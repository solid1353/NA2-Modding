#!/usr/bin/env python3
"""Pair likely controller-mask functions across preserved Ghidra C exports.

This is a read-only analysis helper.  It does not patch binaries.  Function bodies
are compared after normalizing generated symbol addresses and the four face-button
mask literals; the report retains the original mask counts for classification.
"""

from __future__ import annotations

import argparse
import difflib
import re
from dataclasses import dataclass
from pathlib import Path

from paths import PATHS


FUNCTION_RE = re.compile(r"(?m)^(?:[\w *]+)\s+(FUN_[0-9a-f]{8})\([^\n]*\)\s*\n\s*\{")
MASK_RE = re.compile(r"&\s*(0x10|0x20|0x40|0x80)(?:[uUlL]+)?\b")
MASKS = ("0x10", "0x20", "0x40", "0x80")


@dataclass(frozen=True)
class Function:
    name: str
    ordinal: int
    start_line: int
    text: str
    normalized: str
    masks: tuple[int, int, int, int]


def normalize(text: str) -> str:
    text = re.sub(r"FUN_[0-9a-f]{8}", "FUN_ADDR", text)
    text = re.sub(r"(?:PTR_)?DAT_[0-9a-f]{8}", "DATA_ADDR", text)
    text = re.sub(r"[iu]Ram[0-9a-f]{8}", "RAM_ADDR", text)
    text = re.sub(r"[iu]Gp[0-9a-f]+", "GP_ADDR", text)
    text = re.sub(r"\b0x(?:10|20|40|80)(?:[uUlL]+)?\b", "FACE_BUTTON", text)
    text = re.sub(r"\s+", "", text)
    return text


def parse_functions(path: Path) -> list[Function]:
    source = path.read_text(encoding="utf-8", errors="replace")
    matches = list(FUNCTION_RE.finditer(source))
    functions: list[Function] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(source)
        text = source[match.start():end]
        mask_values = MASK_RE.findall(text)
        if not mask_values:
            continue
        masks = tuple(mask_values.count(mask) for mask in MASKS)
        functions.append(
            Function(
                name=match.group(1),
                ordinal=index,
                start_line=source.count("\n", 0, match.start()) + 1,
                text=text,
                normalized=normalize(text),
                masks=masks,
            )
        )
    return functions


def score(left: Function, right: Function) -> float:
    length_ratio = min(len(left.normalized), len(right.normalized)) / max(
        len(left.normalized), len(right.normalized)
    )
    if length_ratio < 0.55:
        return 0.0
    return difflib.SequenceMatcher(None, left.normalized, right.normalized, autojunk=False).ratio()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("na2", type=Path)
    parser.add_argument("nun5", type=Path)
    parser.add_argument("--minimum-score", type=float, default=0.82)
    parser.add_argument("--minimum-address", type=lambda value: int(value, 0), default=0)
    parser.add_argument("--ordinal-window", type=int, default=80)
    parser.add_argument("--changed-masks-only", action="store_true")
    args = parser.parse_args()

    na2 = [f for f in parse_functions(args.na2) if int(f.name[4:], 16) >= args.minimum_address]
    nun5 = parse_functions(args.nun5)
    print("na2_function\tna2_line\tna2_masks_10_20_40_80\tnun5_function\tnun5_line\tnun5_masks_10_20_40_80\tscore\tsecond_score")
    for left in na2:
        nearby = [right for right in nun5 if abs(left.ordinal - right.ordinal) <= args.ordinal_window]
        ranked = sorted(((score(left, right), right) for right in nearby), reverse=True, key=lambda item: item[0])
        if len(ranked) < 2:
            continue
        best_score, best = ranked[0]
        second_score = ranked[1][0]
        if best_score < args.minimum_score:
            continue
        if args.changed_masks_only and left.masks == best.masks:
            continue
        print(
            f"{left.name}\t{left.start_line}\t{','.join(map(str, left.masks))}\t"
            f"{best.name}\t{best.start_line}\t{','.join(map(str, best.masks))}\t"
            f"{best_score:.4f}\t{second_score:.4f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
