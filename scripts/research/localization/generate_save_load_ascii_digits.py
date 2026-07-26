#!/usr/bin/env python3
"""Generate and verify the call-local Save/Load ASCII-number patch."""

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
        if (candidate / "project-paths.json").is_file():
            return candidate
    raise FileNotFoundError("project-paths.json was not found")


REPOSITORY = find_repository(Path(__file__))
if str(REPOSITORY) not in sys.path:
    sys.path.insert(0, str(REPOSITORY))

from na2_patcher.project_paths import load_project_paths  # noqa: E402
from scripts.research.localization import mips  # noqa: E402


PATCH_ID = "font_save_load_ascii_digits"
SPRINTF = 0x0017BCA0
BUFFER_OFFSET = 0x90

ZERO = 0
AT = 1
V1 = 3
A0 = 4
A1 = 5
A2 = 6
S1 = 17
S5 = 21
S6 = 22
SP = 29

FORMAT_D = 0x006042D3
FORMAT_02D = 0x00605C20
NUN5_MAX_HOURS = 99


@dataclass(frozen=True)
class CallSite:
    edit_id: str
    order: int
    offset: int
    expected_hex: str
    value_word: int
    format_address: int
    label: str
    maximum: int | None = None


CALL_SITES = (
    CallSite(
        "font_save_load_ascii_digits_01",
        10,
        0x0E660C,
        "0E0065942D200000040006249000A7270100082444E10D0C00000000",
        mips.i_type(0x25, V1, A2, 0x0E),
        FORMAT_D,
        "year",
    ),
    CallSite(
        "font_save_load_ascii_digits_02",
        20,
        0x0E6650,
        "2D2000002D282002020006249000A7272D40C00044E10D0C00000000",
        mips.r_type(S1, ZERO, A2, 0x2D),
        FORMAT_02D,
        "month",
    ),
    CallSite(
        "font_save_load_ascii_digits_03",
        30,
        0x0E6694,
        "2D2000002D28A002020006249000A7272D40C00044E10D0C00000000",
        mips.r_type(S5, ZERO, A2, 0x2D),
        FORMAT_02D,
        "day",
    ),
    CallSite(
        "font_save_load_ascii_digits_04",
        40,
        0x0E67A4,
        "2D2000002D28A002030006249000A7270200082444E10D0C00000000",
        mips.r_type(S5, ZERO, A2, 0x2D),
        FORMAT_02D,
        "hour",
        NUN5_MAX_HOURS,
    ),
    CallSite(
        "font_save_load_ascii_digits_05",
        50,
        0x0E67E8,
        "2D2000002D282002020006249000A7272D40C00044E10D0C00000000",
        mips.r_type(S1, ZERO, A2, 0x2D),
        FORMAT_02D,
        "minute",
    ),
    CallSite(
        "font_save_load_ascii_digits_06",
        60,
        0x0E682C,
        "2D2000002D28C002020006249000A7272D40C00044E10D0C00000000",
        mips.r_type(S6, ZERO, A2, 0x2D),
        FORMAT_02D,
        "second",
    ),
)


def build_call(site: CallSite) -> bytes:
    high = site.format_address >> 16
    low = site.format_address & 0xFFFF
    assembler = mips.Assembler()
    if site.maximum is None:
        assembler.emit(site.value_word)
        assembler.emit(mips.i_type(0x09, SP, A0, BUFFER_OFFSET))
        assembler.emit(mips.i_type(0x0F, ZERO, A1, high))
        assembler.emit(mips.i_type(0x09, A1, A1, low))
        assembler.emit(0)
        assembler.emit(mips.jump(0x03, SPRINTF))
        assembler.emit(0)
    else:
        if site.maximum != NUN5_MAX_HOURS:
            raise AssertionError(f"unsupported Save/Load cap: {site.maximum}")
        # Match NUN5's signed `hour < 100 ? hour : 99` behavior without
        # growing the guarded 28-byte call block.
        assembler.emit(mips.i_type(0x0A, S5, AT, site.maximum + 1))
        assembler.emit(mips.i_type(0x09, ZERO, A2, site.maximum))
        assembler.emit(mips.r_type(S5, AT, A2, 0x0B))
        assembler.emit(mips.i_type(0x09, SP, A0, BUFFER_OFFSET))
        assembler.emit(mips.i_type(0x0F, ZERO, A1, high))
        assembler.emit(mips.jump(0x03, SPRINTF))
        assembler.emit(mips.i_type(0x09, A1, A1, low))
    payload, relocations = assembler.build()
    if relocations:
        raise AssertionError("fixed-address Save/Load call emitted relocations")
    return payload


def generated_edits() -> list[dict[str, object]]:
    edits = [
        {
            "edit_id": site.edit_id,
            "patch_id": PATCH_ID,
            "order": site.order,
            "destination_target_id": "na2_elf",
            "destination_offset": site.offset,
            "operation": "replace",
            "length": 28,
            "expected_hex": site.expected_hex,
            "replacement_hex": build_call(site).hex().upper(),
            "reason": (
                (
                    "Format the Save/Load hour through NA2's existing ASCII "
                    "sprintf with NUN5's two-digit field and 99-hour cap while "
                    "preserving field order and timer math."
                )
                if site.maximum is not None
                else (
                    f"Format the Save/Load {site.label} through NA2's existing "
                    "ASCII sprintf while preserving the original field width, "
                    "value, order, and timer math."
                )
            ),
        }
        for site in CALL_SITES
    ]
    edits.append(
        {
            "edit_id": "font_save_load_ascii_digits_07",
            "patch_id": PATCH_ID,
            "order": 70,
            "destination_target_id": "na2_elf",
            "destination_offset": 0x503134,
            "operation": "replace",
            "length": 4,
            "expected_hex": "81460000",
            "replacement_hex": "3A000000",
            "reason": (
                "Replace the Save/Load-only fullwidth colon constant with "
                "ASCII colon for the now-ASCII time fields."
            ),
        }
    )
    return edits


def verify_source() -> Path:
    paths = load_project_paths(REPOSITORY)
    elf = paths.path("source_na2") / "SLPS_258.37"
    data = elf.read_bytes()
    for edit in generated_edits():
        offset = int(edit["destination_offset"])
        expected = bytes.fromhex(str(edit["expected_hex"]))
        actual = data[offset : offset + len(expected)]
        if actual != expected:
            raise ValueError(
                f"{edit['edit_id']} source mismatch at {offset:#x}: "
                f"{actual.hex().upper()} != {expected.hex().upper()}"
            )
    for address, expected in (
        (FORMAT_D, b"%d\0"),
        (FORMAT_02D, b"%02d\0"),
    ):
        offset = address - 0x000FFF00
        actual = data[offset : offset + len(expected)]
        if actual != expected:
            raise ValueError(
                f"format string mismatch at {address:#x}: {actual!r} != "
                f"{expected!r}"
            )
    return elf


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tsv",
        action="store_true",
        help="emit the generated edit fields as TSV after verification",
    )
    args = parser.parse_args()
    elf = verify_source()
    edits = generated_edits()
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
