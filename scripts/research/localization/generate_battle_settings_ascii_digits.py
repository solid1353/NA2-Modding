#!/usr/bin/env python3
"""Generate and verify the Battle Settings ASCII-time patch."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


def find_repository(start: Path) -> Path:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / "project-paths.json").is_file():
            return candidate
    raise FileNotFoundError("project-paths.json was not found")


REPOSITORY = find_repository(Path(__file__))
if str(REPOSITORY) not in sys.path:
    sys.path.insert(0, str(REPOSITORY))

from na2_patcher.project_paths import load_project_paths  # noqa: E402
from scripts.research.localization import mips  # noqa: E402


PATCH_ID = "font_battle_settings_ascii_digits"
EDIT_ID = f"{PATCH_ID}_01"
DESTINATION_OFFSET = 0x1CC3D8
EXPECTED_HEX = "2D200000030006246000A7270100082444E10D0C00000000"

SPECIAL_BRANCH_OFFSET = 0x1CC3B0
SPECIAL_BRANCH_EXPECTED_HEX = (
    "640002240800A214000000006000A42778B1858FE0F0050C00000000"
    "080000100000000000000000"
)

SPRINTF = 0x0017BCA0
FORMAT_D = 0x006042D3
ELF_FILE_BIAS = 0x000FFF00
BUFFER_OFFSET = 0x60

ZERO = 0
A0 = 4
A1 = 5
A2 = 6
SP = 29


def build_call() -> bytes:
    assembler = mips.Assembler()
    assembler.emit(mips.r_type(A1, ZERO, A2, 0x2D))
    assembler.emit(mips.i_type(0x09, SP, A0, BUFFER_OFFSET))
    assembler.emit(mips.i_type(0x0F, ZERO, A1, FORMAT_D >> 16))
    assembler.emit(mips.jump(0x03, SPRINTF))
    assembler.emit(mips.i_type(0x09, A1, A1, FORMAT_D & 0xFFFF))
    assembler.emit(0)
    payload, relocations = assembler.build()
    if relocations:
        raise AssertionError("fixed-address Battle Settings call emitted relocations")
    return payload


def generated_edits() -> list[dict[str, object]]:
    return [
        {
            "edit_id": EDIT_ID,
            "patch_id": PATCH_ID,
            "order": 10,
            "destination_target_id": "na2_btl",
            "destination_offset": DESTINATION_OFFSET,
            "operation": "replace",
            "length": 24,
            "expected_hex": EXPECTED_HEX,
            "replacement_hex": build_call().hex().upper(),
            "reason": (
                "Route only ordinary Battle Settings Time values through "
                "NA2's existing ASCII sprintf while preserving the separate "
                "100/infinity branch and every other fullwidth formatter caller."
            ),
        }
    ]


def verify_source() -> tuple[Path, Path]:
    paths = load_project_paths(REPOSITORY)
    btl = paths.path("source_na2") / "PRG" / "BTL.BIN"
    btl_data = btl.read_bytes()

    expected = bytes.fromhex(EXPECTED_HEX)
    actual = btl_data[DESTINATION_OFFSET : DESTINATION_OFFSET + len(expected)]
    if actual != expected:
        raise ValueError(
            f"{EDIT_ID} source mismatch at {DESTINATION_OFFSET:#x}: "
            f"{actual.hex().upper()} != {expected.hex().upper()}"
        )

    special_expected = bytes.fromhex(SPECIAL_BRANCH_EXPECTED_HEX)
    special_actual = btl_data[
        SPECIAL_BRANCH_OFFSET : SPECIAL_BRANCH_OFFSET + len(special_expected)
    ]
    if special_actual != special_expected:
        raise ValueError(
            f"Battle Settings infinity branch mismatch at "
            f"{SPECIAL_BRANCH_OFFSET:#x}: "
            f"{special_actual.hex().upper()} != {special_expected.hex().upper()}"
        )
    if SPECIAL_BRANCH_OFFSET + len(special_expected) != DESTINATION_OFFSET:
        raise AssertionError("infinity guard no longer ends at the numeric block")

    elf = paths.path("source_na2") / "SLPS_258.37"
    elf_data = elf.read_bytes()
    format_offset = FORMAT_D - ELF_FILE_BIAS
    expected_format = b"%d\0"
    actual_format = elf_data[format_offset : format_offset + 3]
    if actual_format != expected_format:
        raise ValueError(
            f"format string mismatch at {FORMAT_D:#x}: "
            f"{actual_format!r} != {expected_format!r}"
        )
    return btl, elf


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tsv",
        action="store_true",
        help="emit the generated edit fields as TSV after verification",
    )
    args = parser.parse_args()
    btl, elf = verify_source()
    edits = generated_edits()
    print(f"verified\t{btl.relative_to(REPOSITORY).as_posix()}")
    print(f"verified\t{elf.relative_to(REPOSITORY).as_posix()}")
    print(f"edits\t{len(edits)}")
    if args.tsv:
        fields = (
            "edit_id",
            "patch_id",
            "order",
            "destination_target_id",
            "destination_offset",
            "operation",
            "length",
            "expected_hex",
            "replacement_hex",
            "reason",
        )
        writer = csv.DictWriter(
            sys.stdout,
            fieldnames=fields,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        for edit in edits:
            row = dict(edit)
            row["destination_offset"] = (
                f"0x{int(row['destination_offset']):X}"
            )
            writer.writerow(row)


if __name__ == "__main__":
    main()
