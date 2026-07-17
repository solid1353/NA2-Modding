#!/usr/bin/env python3
"""Pair MIPS face-button ANDI instructions between regional raw modules.

The comparison is read-only and independent of the menu patch tables.  It uses
local instruction-shape context, normalizing branch targets, addresses, and
immediates while retaining opcodes and register allocation.
"""

from __future__ import annotations

import argparse
import difflib
from dataclasses import dataclass
from pathlib import Path

from project_paths import PROJECT_PATHS


FACE_MASKS = {0x10: "triangle", 0x20: "circle", 0x40: "cross", 0x80: "square"}


@dataclass(frozen=True)
class Hit:
    offset: int
    word: int
    rs: int
    rt: int
    mask: int


def words(data: bytes) -> list[int]:
    usable = len(data) - len(data) % 4
    return [int.from_bytes(data[offset : offset + 4], "little") for offset in range(0, usable, 4)]


def hits(values: list[int]) -> list[Hit]:
    result: list[Hit] = []
    for index, word in enumerate(values):
        opcode = word >> 26
        immediate = word & 0xFFFF
        if opcode == 0x0C and immediate in FACE_MASKS:
            result.append(
                Hit(
                    offset=index * 4,
                    word=word,
                    rs=(word >> 21) & 0x1F,
                    rt=(word >> 16) & 0x1F,
                    mask=immediate,
                )
            )
    return result


def shape(word: int) -> int:
    opcode = word >> 26
    if opcode == 0:
        # R-type: register allocation and function are strong structural evidence.
        return word
    if opcode in (2, 3):
        # Absolute jump targets shift between regional builds.
        return opcode << 26
    if opcode == 0x0C and (word & 0xFFFF) in FACE_MASKS:
        # Preserve source/destination registers, normalize only the button mask.
        return (word & 0xFFFF0000) | 0xF00D
    # I-type immediates include branches, data addresses, and structure offsets;
    # opcode plus register allocation is the stable regional signature.
    return word & 0xFFFF0000


def context(values: list[int], hit: Hit, radius: int) -> list[int]:
    index = hit.offset // 4
    start = max(0, index - radius)
    end = min(len(values), index + radius + 1)
    return [shape(word) for word in values[start:end]]


def similarity(left: list[int], right: list[int]) -> float:
    return difflib.SequenceMatcher(None, left, right, autojunk=False).ratio()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("na2", type=Path)
    parser.add_argument("nun5", type=Path)
    parser.add_argument("--radius", type=int, default=32)
    parser.add_argument("--minimum-score", type=float, default=0.72)
    parser.add_argument("--minimum-margin", type=float, default=0.04)
    args = parser.parse_args()

    na2_words = words(args.na2.read_bytes())
    nun5_words = words(args.nun5.read_bytes())
    na2_hits = hits(na2_words)
    nun5_hits = hits(nun5_words)

    print(
        "na2_offset\tna2_registers\tna2_mask\tnun5_offset\tnun5_registers\t"
        "nun5_mask\tscore\tsecond_score\tmargin"
    )
    for left in na2_hits:
        left_context = context(na2_words, left, args.radius)
        ranked = sorted(
            (
                (similarity(left_context, context(nun5_words, right, args.radius)), right)
                for right in nun5_hits
            ),
            reverse=True,
            key=lambda item: item[0],
        )
        best_score, best = ranked[0]
        second_score = ranked[1][0]
        margin = best_score - second_score
        if best_score < args.minimum_score or margin < args.minimum_margin:
            continue
        print(
            f"0x{left.offset:08X}\tr{left.rs}->r{left.rt}\t{FACE_MASKS[left.mask]}(0x{left.mask:02X})\t"
            f"0x{best.offset:08X}\tr{best.rs}->r{best.rt}\t{FACE_MASKS[best.mask]}(0x{best.mask:02X})\t"
            f"{best_score:.4f}\t{second_score:.4f}\t{margin:.4f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
