from __future__ import annotations

import argparse
import difflib
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


FUNCTION = re.compile(r";undefined (?P<name>FUN_[0-9a-fA-F]{8})\(")
INSTRUCTION = re.compile(
    r"^text:(?P<address>[0-9a-fA-F]{8})\s+"
    r"(?P<bytes>[0-9a-fA-F]{8})\s+"
    r"(?P<body>.*?)(?:\s*;.*)?$"
)
SYMBOL = re.compile(r"\b(?:FUN|SUB|LAB)_[0-9a-fA-F]{8}\b")
DATA_SUFFIX = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*_[0-9a-fA-F]{8}\b")
NUMBER = re.compile(r"(?<![A-Za-z_])(?:-?0x[0-9a-fA-F]+|-?\d+)(?![A-Za-z_])")


@dataclass(frozen=True)
class Function:
    name: str
    address: int
    signatures: tuple[str, ...]


def normalized_instruction(body: str) -> str:
    body = SYMBOL.sub("SYMBOL", body)
    body = DATA_SUFFIX.sub("DATA", body)
    return NUMBER.sub("#", body).strip()


def parse_functions(path: Path) -> dict[str, Function]:
    functions: dict[str, Function] = {}
    current_name: str | None = None
    current_address: int | None = None
    signatures: list[str] = []

    def finish() -> None:
        nonlocal current_name, current_address, signatures
        if current_name is not None and current_address is not None and signatures:
            functions[current_name] = Function(
                current_name,
                current_address,
                tuple(signatures),
            )
        current_name = None
        current_address = None
        signatures = []

    for line in path.read_text(encoding="utf-8").splitlines():
        function_match = FUNCTION.search(line)
        if function_match:
            finish()
            current_name = function_match.group("name")
            continue
        if current_name is None:
            continue
        instruction_match = INSTRUCTION.match(line)
        if instruction_match is None:
            continue
        address = int(instruction_match.group("address"), 16)
        if current_address is None:
            current_address = address
        signatures.append(normalized_instruction(instruction_match.group("body")))
    finish()
    return functions


def ngrams(values: tuple[str, ...], width: int = 2) -> Counter[tuple[str, ...]]:
    return Counter(tuple(values[index : index + width]) for index in range(len(values) - width + 1))


def overlap(left: Counter[tuple[str, ...]], right: Counter[tuple[str, ...]]) -> float:
    total = sum((left | right).values())
    return sum((left & right).values()) / total if total else 0.0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Find structural cross-build matches for one Ghidra assembly function"
    )
    parser.add_argument("source", type=Path)
    parser.add_argument("function")
    parser.add_argument("candidates", type=Path)
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    source_functions = parse_functions(args.source)
    target = source_functions.get(args.function)
    if target is None:
        raise ValueError(f"Function not found: {args.function}")
    target_ngrams = ngrams(target.signatures)

    shortlist: list[tuple[float, Function]] = []
    for candidate in parse_functions(args.candidates).values():
        ratio = len(candidate.signatures) / len(target.signatures)
        if not 0.5 <= ratio <= 2.0:
            continue
        shortlist.append((overlap(target_ngrams, ngrams(candidate.signatures)), candidate))
    shortlist.sort(key=lambda item: item[0], reverse=True)

    ranked = []
    for quick_score, candidate in shortlist[:250]:
        similarity = difflib.SequenceMatcher(
            None,
            target.signatures,
            candidate.signatures,
            autojunk=False,
        ).ratio()
        ranked.append((similarity, quick_score, candidate))
    ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)

    print("function\taddress\tinstructions\tsimilarity\tbigram_overlap")
    for similarity, quick_score, candidate in ranked[: args.limit]:
        print(
            f"{candidate.name}\t0x{candidate.address:08X}\t{len(candidate.signatures)}\t"
            f"{similarity:.6f}\t{quick_score:.6f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
