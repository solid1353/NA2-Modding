#!/usr/bin/env python3
"""Generate and verify the Ninja Song ASCII-number call redirects."""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
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

from scripts.lib.paths import load_paths  # noqa: E402


PATCH_ID = "font_numeric_ninja_song"
SYMBOL = "localization.font.ninja_song_ascii_number"
FORMATTER_JAL_HEX = "44E10D0C"


@dataclass(frozen=True)
class CallSite:
    name: str
    offset: int
    context_offset: int
    context_hex: str
    width: int
    mode: int
    reason: str


CALLS = (
    CallSite(
        "factor",
        0x64B28,
        0x64B10,
        "0000028E000045842D200000030006244000A7272D40000044E10D0C00000000",
        3,
        0,
        "Render the left Ninja Song arithmetic factor as right-aligned ASCII width 3.",
    ),
    CallSite(
        "multiplier",
        0x64BA8,
        0x64B94,
        "2D2000000400058E030006244000A7272D40000044E10D0C00000000",
        3,
        0,
        "Render the right Ninja Song arithmetic factor as right-aligned ASCII width 3.",
    ),
    CallSite(
        "total",
        0x64CE4,
        0x64CD0,
        "2D2000000800058E050006244000A7272D40000044E10D0C00000000",
        5,
        0,
        "Render the Ninja Song arithmetic total as right-aligned ASCII width 5.",
    ),
    CallSite(
        "inline",
        0x64E4C,
        0x64E38,
        "2D2000000400058E040006244000A7270100082444E10D0C00000000",
        4,
        1,
        "Render the Ninja Song label placeholder as unpadded ASCII decimal.",
    ),
    CallSite(
        "score",
        0x64ED4,
        0x64EC0,
        "2D2000000800058E040006246000A7272D40000044E10D0C00000000",
        4,
        0,
        "Render the Ninja Song detail score as right-aligned ASCII width 4.",
    ),
)


def format_ascii_number(value: int, width: int, mode: int) -> str:
    """Reference the NUN5 formatter's modes for focused tests."""

    text = str(value)
    if mode == 1:
        return text
    if mode == 0:
        return text.rjust(width, " ")
    if mode == 2:
        return text.rjust(width, "0")
    raise ValueError(f"unsupported numeric formatter mode: {mode}")


def generated_edits() -> list[dict[str, object]]:
    return [
        {
            "edit_id": f"{PATCH_ID}_{index:02d}",
            "patch_id": PATCH_ID,
            "order": index * 10,
            "target_id": "na2_btl",
            "offset": call.offset,
            "expected_hex": FORMATTER_JAL_HEX,
            "replacement_hex": "00000000",
            "relocation_offset": 0,
            "symbol": SYMBOL,
            "encoding": "jal26",
            "addend": 0,
            "reason": call.reason,
        }
        for index, call in enumerate(CALLS, 1)
    ]


def verify_source() -> Path:
    btl = (
        load_paths(REPOSITORY).path("source_na2")
        / "PRG"
        / "BTL.BIN"
    )
    data = btl.read_bytes()
    for call in CALLS:
        expected_context = bytes.fromhex(call.context_hex)
        actual_context = data[
            call.context_offset : call.context_offset
            + len(expected_context)
        ]
        if actual_context != expected_context:
            raise ValueError(
                f"{call.name} context mismatch at "
                f"{call.context_offset:#x}: "
                f"{actual_context.hex().upper()} != {call.context_hex}"
            )
        expected_jal = bytes.fromhex(FORMATTER_JAL_HEX)
        actual_jal = data[call.offset : call.offset + len(expected_jal)]
        if actual_jal != expected_jal:
            raise ValueError(
                f"{call.name} formatter mismatch at {call.offset:#x}: "
                f"{actual_jal.hex().upper()} != {FORMATTER_JAL_HEX}"
            )
    return btl


def verify_multiplication_mapping() -> Path:
    mappings = (
        REPOSITORY
        / "na228_builder"
        / "features"
        / "localization"
        / "translation_importer"
        / "mappings.tsv"
    )
    with mappings.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    matches = [row for row in rows if row["id"] == "T2195"]
    if len(matches) != 1:
        raise ValueError(
            f"expected one T2195 multiplication mapping, found {len(matches)}"
        )
    row = matches[0]
    expected = {
        "enabled": "1",
        "source": " × ",
        "donor": " * ",
        "source_ref": "NA2_SLPS@0x504DA0",
    }
    actual = {field: row[field] for field in expected}
    if actual != expected:
        raise ValueError(
            f"T2195 multiplication mapping mismatch: {actual!r} != {expected!r}"
        )
    return mappings


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tsv",
        action="store_true",
        help="emit the generated runtime-injector edit fields as TSV",
    )
    args = parser.parse_args()
    btl = verify_source()
    mappings = verify_multiplication_mapping()
    edits = generated_edits()
    print(f"verified\t{btl.relative_to(REPOSITORY).as_posix()}")
    print(f"verified\t{mappings.relative_to(REPOSITORY).as_posix()}")
    print(f"edits\t{len(edits)}")
    if args.tsv:
        fields = (
            "edit_id",
            "patch_id",
            "order",
            "target_id",
            "offset",
            "expected_hex",
            "replacement_hex",
            "relocation_offset",
            "symbol",
            "encoding",
            "addend",
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
            row["offset"] = f"0x{int(row['offset']):X}"
            writer.writerow(row)


if __name__ == "__main__":
    main()
