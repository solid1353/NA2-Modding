#!/usr/bin/env python3
"""Generate and verify the contextual Special/Practice ON/OFF split."""

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
        if (candidate / "paths.json").is_file():
            return candidate
    raise FileNotFoundError("paths.json was not found")


REPOSITORY = find_repository(Path(__file__))
if str(REPOSITORY) not in sys.path:
    sys.path.insert(0, str(REPOSITORY))

from scripts.lib.project_paths import load_project_paths  # noqa: E402


PATCH_ID = "font_layout_on_off_context"

TITLECASE_TABLE_ADDRESS = 0x00604658
TITLECASE_TABLE_OFFSET = 0x504758
TITLECASE_TABLE_POINTER_HEX = "58466000"
PRACTICE_ROW_POINTERS = (
    (0x20B498, "C05A6000", "Commands"),
    (0x20B49C, "D05A6000", "Damage"),
    (0x20B4A0, "D85A6000", "Guide Ninja Sound"),
)


def generated_edits() -> list[dict[str, object]]:
    edits: list[dict[str, object]] = []
    for index, (offset, expected_hex, label) in enumerate(
        PRACTICE_ROW_POINTERS,
        start=1,
    ):
        edits.append(
            {
                "edit_id": f"{PATCH_ID}_{index:02d}",
                "patch_id": PATCH_ID,
                "order": index * 10,
                "destination_target_id": "na2_btl",
                "destination_offset": offset,
                "operation": "replace",
                "length": 4,
                "expected_hex": expected_hex,
                "replacement_hex": TITLECASE_TABLE_POINTER_HEX,
                "reason": (
                    f"Point the Practice Settings {label} row at the "
                    "existing title-case Off/On selector table."
                ),
            }
        )
    return edits


def verify_source() -> tuple[Path, Path]:
    paths = load_project_paths(REPOSITORY)
    btl = paths.path("source_na2") / "PRG" / "BTL.BIN"
    btl_data = btl.read_bytes()
    elf = paths.path("source_na2") / "SLPS_258.37"
    elf_data = elf.read_bytes()

    for edit in generated_edits():
        offset = int(edit["destination_offset"])
        expected = bytes.fromhex(str(edit["expected_hex"]))
        actual = btl_data[offset : offset + len(expected)]
        if actual != expected:
            raise ValueError(
                f"{edit['edit_id']} source mismatch at {offset:#x}: "
                f"{actual.hex().upper()} != {expected.hex().upper()}"
            )

    expected_titlecase_table = bytes.fromhex("4846600050466000")
    actual_titlecase_table = elf_data[
        TITLECASE_TABLE_OFFSET
        : TITLECASE_TABLE_OFFSET + len(expected_titlecase_table)
    ]
    if actual_titlecase_table != expected_titlecase_table:
        raise ValueError(
            f"title-case table mismatch at {TITLECASE_TABLE_OFFSET:#x}: "
            f"{actual_titlecase_table.hex().upper()} != "
            f"{expected_titlecase_table.hex().upper()}"
        )
    return btl, elf


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tsv",
        action="store_true",
        help="emit the generated binary-patcher edit fields as TSV",
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
