#!/usr/bin/env python3
"""Generate relocatable resident code for the accepted NA2 font renderer."""

from __future__ import annotations

import argparse
import csv
import hashlib
import struct
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

from na2_patcher.modules.resident_patcher import engine  # noqa: E402
from na2_patcher.project_paths import load_project_paths  # noqa: E402
from scripts.research.localization import mips  # noqa: E402


MODULE = load_project_paths(REPOSITORY).path(
    "features", "localization", "resident_patcher"
)
BLOB_RELATIVE = Path("assets") / "font_renderer_resident.bin"
BLOB_OUTPUT = MODULE / BLOB_RELATIVE
FRAGMENTS_OUTPUT = MODULE / "fragments.tsv"
RELOCATIONS_OUTPUT = MODULE / "relocations.tsv"

PREFIX = "localization.font"
PLAIN_SPACE = f"{PREFIX}.plain_space"
NEWLINE_ADVANCE = f"{PREFIX}.newline_advance"
MEASURE = f"{PREFIX}.measure"
CONTROLS_FIT = f"{PREFIX}.controls_fit"
SCALE_ADVANCE = f"{PREFIX}.scale_advance"
SELECTED_HELPER = f"{PREFIX}.selected_helper"
SELECTED_TRAMPOLINE = f"{PREFIX}.selected_trampoline"
UI_HELPER = f"{PREFIX}.ui_helper"
UI_TRAMPOLINE = f"{PREFIX}.ui_trampoline"

SCALE_ADDRESS = 0x0060737C
FONT_RENDERER_POINTER = 0x00607470
FONT_INITIALIZE = 0x00186510
FONT_SET_CONTEXT = 0x001866D0
FONT_MEASURE = 0x003798E0
FONT_CENTER = 0x00379240

PLAIN_SPACE_RETURN = 0x00189300
NEWLINE_ADVANCE_RETURN = 0x00188670
UI_ORIGINAL_BODY = 0x00379A28
SELECTED_ORIGINAL_BODY = 0x00379158

UI_CALLER = 0x00383968
SELECTED_CALLER = 0x0038381C
PRACTICE_PAUSE_LIST_CALLER = 0x00382598
PRACTICE_PAUSE_LIST_OUTER = 0x0087D6E0
COLLECTION_BODY_CALLER = 0x003825F8
COLLECTION_BODY_OUTER = 0x006C87D0
PRACTICE_BODY_CALLER = 0x003825F8
PRACTICE_BODY_OUTER = 0x00877F84
CHARACTER_BODY_CALLER = 0x00382454
CHARACTER_BODY_OUTER = 0x003BCA5C

YES_SOURCE = (50.0, 24.0)
NO_SOURCE = (50.0, 56.0)
YES_TARGET = (64.5, 31.5)
NO_TARGET = (68.5, 49.0)
PRACTICE_PAUSE_LIST_Y_OFFSET = -4.0
PRACTICE_PAUSE_LIST_BOX_WIDTH = 216
COLLECTION_BODY_TARGET_Y = 12.0
PRACTICE_BODY_TARGET_Y = 12.0
CHARACTER_BODY_BOX_X = 8.0
CHARACTER_BODY_BOX_WIDTH = 368
CHARACTER_BODY_DRAW_Y = 10.0

TEXT_METRICS_HELPERS = bytes.fromhex(
    "040060C640000146C0C0033C0000834400000000400001466000033C7C7362C4"
    "420802461C0060C6000001461C0060E6C0240608000000000000000000000000"
    "400060C64008004680C0033C000083440000000040000146200060C600000146"
    "200060E69C2106080000000000000000E0FFBD270000BFAF0400A4AF38E60D0C"
    "000000000400A88F211840002148400000000A91070040110100082520000B24"
    "FBFF4B1500000000FAFF2925F8FF001000000000211020010000BF8F2000BD27"
    "0800E00300000000"
)
CONTROLS_FIT_HELPER = bytes.fromhex(
    "E0FFBD271C00BFAF1800A4AF1400A5AF1000ACE70C00ADE721280000CC500F0C"
    "0000000021404000214860001800A48F1400A58F1000ACC70C00ADC781000A29"
    "0D00401500000000000088442000804600430A3C00088A448308004660000A3C"
    "7C7342E543500900C1FF4A2500008A442000804600630046D641083C66660835"
    "0018884400A503461C00BF8F0800E0032000BD27"
)
SELECTED_HELPER_BYTES = bytes.fromhex(
    "3800083C1C3808351300E81700680944C041083C06002811000000006042083C"
    "09002811000000000B000010000000008142083C00608844FC41083C00688844"
    "05000010000000008942083C006088444442083C00688844A8500F0800000000"
)
SCALE_ADVANCE_BYTES = bytes.fromhex(
    "7C7342C4820802461C0020C640150046DE1F0608200020C67C7344C402190446"
    "1C100446A12206081C0060E67C7343C44000024642080346B82506081C0060C6"
)


@dataclass(frozen=True)
class Fragment:
    symbol: str
    payload: bytes
    relocations: tuple[mips.Relocation, ...] = ()
    kind: str = "code"
    alignment: int = 4
    init: bool = False


def float_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def emit_load_float(
    assembler: mips.Assembler,
    integer_register: int,
    float_register: int,
    value: float,
) -> None:
    mips.load_u32(assembler, integer_register, float_bits(value))
    assembler.emit(mips.mtc1(integer_register, float_register))


def emit_scale_one(
    assembler: mips.Assembler,
    address_register: int,
    value_register: int,
) -> None:
    assembler.emit(
        mips.i_type(0x0F, 0, address_register, SCALE_ADDRESS >> 16)
    )
    mips.load_u32(assembler, value_register, float_bits(1.0))
    assembler.emit(
        mips.i_type(
            0x2B,
            address_register,
            value_register,
            SCALE_ADDRESS & 0xFFFF,
        )
    )


def relocatable(
    symbol: str,
    payload: bytes,
    relocations: tuple[mips.Relocation, ...],
) -> Fragment:
    result = bytearray(payload)
    for relocation in relocations:
        width = 2 if relocation.kind in {"hi16", "lo16"} else 4
        result[relocation.offset:relocation.offset + width] = bytes(width)
    return Fragment(symbol, bytes(result), relocations)


def build_selected_helper() -> Fragment:
    return relocatable(
        SELECTED_HELPER,
        SELECTED_HELPER_BYTES,
        (mips.Relocation(0x58, "j26", SELECTED_TRAMPOLINE),),
    )


def build_controls_fit() -> Fragment:
    return relocatable(
        CONTROLS_FIT,
        CONTROLS_FIT_HELPER,
        (mips.Relocation(0x1C, "jal26", MEASURE),),
    )


def build_ui_helper() -> Fragment:
    zero, v0, a0, a1, a2, a3 = 0, 2, 4, 5, 6, 7
    t0, t1, t2, t3 = 8, 9, 10, 11
    sp, ra = 29, 31
    frame_size = 0x40
    saved_a0 = 0x00
    saved_a1 = 0x04
    saved_a2 = 0x08
    saved_a3 = 0x0C
    saved_record_x = 0x10
    saved_record_y = 0x14
    scale_modified = 0x18
    saved_object_font = 0x1C
    saved_font_28 = 0x20
    saved_font_2c = 0x24
    saved_outer_ra = 0x28
    saved_font_6c = 0x2C
    saved_ra = 0x3C

    assembler = mips.Assembler()
    assembler.emit(mips.i_type(0x09, sp, sp, -frame_size))
    assembler.emit(mips.i_type(0x2B, sp, ra, saved_ra))
    for register, offset in (
        (a0, saved_a0),
        (a1, saved_a1),
        (a2, saved_a2),
        (a3, saved_a3),
    ):
        assembler.emit(mips.i_type(0x2B, sp, register, offset))
    assembler.emit(mips.i_type(0x23, a1, t1, 0))
    assembler.emit(mips.i_type(0x2B, sp, t1, saved_record_x))
    assembler.emit(mips.i_type(0x23, a1, t1, 4))
    assembler.emit(mips.i_type(0x2B, sp, t1, saved_record_y))
    assembler.emit(mips.i_type(0x2B, sp, zero, scale_modified))
    assembler.emit(mips.i_type(0x23, sp, t2, frame_size))
    assembler.emit(mips.i_type(0x2B, sp, t2, saved_outer_ra))

    mips.load_u32(assembler, t2, UI_CALLER)
    assembler.branch(0x05, ra, t2, "check_practice_pause_list")
    assembler.emit(0)
    mips.load_u32(assembler, t2, float_bits(YES_SOURCE[1]))
    assembler.branch(0x04, t1, t2, "map_yes")
    assembler.emit(0)
    mips.load_u32(assembler, t2, float_bits(NO_SOURCE[1]))
    assembler.branch(0x04, t1, t2, "map_no")
    assembler.emit(0)
    assembler.branch(0x04, zero, zero, "call_original")
    assembler.emit(0)

    assembler.label("map_yes")
    mips.load_u32(assembler, t2, float_bits(YES_TARGET[0]))
    assembler.emit(mips.i_type(0x2B, a1, t2, 0))
    mips.load_u32(assembler, t2, float_bits(YES_TARGET[1]))
    assembler.emit(mips.i_type(0x2B, a1, t2, 4))
    assembler.branch(0x04, zero, zero, "call_original")
    assembler.emit(0)

    assembler.label("map_no")
    mips.load_u32(assembler, t2, float_bits(NO_TARGET[0]))
    assembler.emit(mips.i_type(0x2B, a1, t2, 0))
    mips.load_u32(assembler, t2, float_bits(NO_TARGET[1]))
    assembler.emit(mips.i_type(0x2B, a1, t2, 4))
    assembler.branch(0x04, zero, zero, "call_original")
    assembler.emit(0)

    assembler.label("check_practice_pause_list")
    mips.load_u32(assembler, t2, PRACTICE_PAUSE_LIST_CALLER)
    assembler.branch(0x05, ra, t2, "check_confirmation_body")
    assembler.emit(0)
    assembler.emit(mips.i_type(0x23, sp, t2, saved_outer_ra))
    mips.load_u32(assembler, t3, PRACTICE_PAUSE_LIST_OUTER)
    assembler.branch(0x05, t2, t3, "check_confirmation_body")
    assembler.emit(0)
    assembler.emit(mips.i_type(0x31, a1, 0, 4))
    emit_load_float(
        assembler, t3, 1, abs(PRACTICE_PAUSE_LIST_Y_OFFSET)
    )
    assembler.emit(mips.cop1(0x01, 0, 0, 1))
    assembler.emit(mips.i_type(0x39, a1, 0, 4))
    assembler.emit(mips.i_type(0x09, zero, t2, 1))
    assembler.emit(mips.i_type(0x2B, sp, t2, scale_modified))
    emit_scale_one(assembler, t1, t2)
    assembler.emit(mips.i_type(0x23, sp, t1, saved_a1))
    assembler.emit(mips.i_type(0x23, t1, a0, 8))
    assembler.emit(mips.r_type(zero, zero, a1, 0x21))
    assembler.jump_symbol(0x03, MEASURE)
    assembler.emit(0)
    assembler.emit(mips.r_type(v0, zero, t3, 0x21))
    assembler.emit(
        mips.i_type(
            0x0A,
            t3,
            t2,
            PRACTICE_PAUSE_LIST_BOX_WIDTH + 1,
        )
    )
    assembler.branch(0x05, t2, zero, "pause_list_draw")
    assembler.emit(0)
    assembler.emit(mips.mtc1(t3, 0))
    assembler.emit(mips.cop1(0x20, 0, 0, fmt=20))
    mips.load_u32(
        assembler,
        t2,
        float_bits(float(PRACTICE_PAUSE_LIST_BOX_WIDTH)),
    )
    assembler.emit(mips.mtc1(t2, 1))
    assembler.emit(mips.cop1(0x03, 2, 1, 0))
    assembler.emit(mips.i_type(0x0F, zero, t2, SCALE_ADDRESS >> 16))
    assembler.emit(
        mips.i_type(0x39, t2, 2, SCALE_ADDRESS & 0xFFFF)
    )

    assembler.label("pause_list_draw")
    for register, offset in (
        (a0, saved_a0),
        (a1, saved_a1),
        (a2, saved_a2),
        (a3, saved_a3),
    ):
        assembler.emit(mips.i_type(0x23, sp, register, offset))
    assembler.jump_symbol(0x03, UI_TRAMPOLINE)
    assembler.emit(0)
    assembler.branch(0x04, zero, zero, "restore_record")
    assembler.emit(0)

    assembler.label("check_confirmation_body")
    mips.load_u32(assembler, t2, COLLECTION_BODY_CALLER)
    assembler.branch(0x05, ra, t2, "check_character_body")
    assembler.emit(0)
    assembler.emit(mips.i_type(0x23, sp, t2, saved_outer_ra))
    mips.load_u32(assembler, t3, COLLECTION_BODY_OUTER)
    assembler.branch(0x05, t2, t3, "check_practice_body")
    assembler.emit(0)
    mips.load_u32(
        assembler, t2, float_bits(COLLECTION_BODY_TARGET_Y)
    )
    assembler.emit(mips.i_type(0x2B, a1, t2, 4))
    assembler.branch(0x04, zero, zero, "call_original")
    assembler.emit(0)

    assembler.label("check_practice_body")
    mips.load_u32(assembler, t3, PRACTICE_BODY_OUTER)
    assembler.branch(0x05, t2, t3, "check_character_body")
    assembler.emit(0)
    mips.load_u32(
        assembler, t2, float_bits(PRACTICE_BODY_TARGET_Y)
    )
    assembler.emit(mips.i_type(0x2B, a1, t2, 4))
    mips.load_u32(assembler, a0, FONT_RENDERER_POINTER)
    assembler.emit(mips.i_type(0x23, a0, a0, 0))
    assembler.emit(mips.i_type(0x09, zero, a1, 1))
    assembler.emit(mips.jump(0x03, FONT_INITIALIZE))
    assembler.emit(0)
    emit_scale_one(assembler, t0, t2)
    assembler.branch(0x04, zero, zero, "call_original")
    assembler.emit(0)

    assembler.label("check_character_body")
    mips.load_u32(assembler, t2, CHARACTER_BODY_CALLER)
    assembler.branch(0x05, ra, t2, "call_original")
    assembler.emit(0)
    assembler.emit(mips.i_type(0x23, sp, t2, saved_outer_ra))
    mips.load_u32(assembler, t3, CHARACTER_BODY_OUTER)
    assembler.branch(0x05, t2, t3, "call_original")
    assembler.emit(0)
    assembler.emit(mips.i_type(0x09, zero, t2, 1))
    assembler.emit(mips.i_type(0x2B, sp, t2, scale_modified))
    assembler.emit(mips.i_type(0x23, sp, t1, saved_a0))
    assembler.emit(mips.i_type(0x23, t1, t2, 0x1C))
    assembler.emit(mips.i_type(0x2B, sp, t2, saved_object_font))
    mips.load_u32(assembler, t1, FONT_RENDERER_POINTER)
    assembler.emit(mips.i_type(0x23, t1, t1, 0))
    assembler.emit(mips.i_type(0x23, t1, t2, 0x28))
    assembler.emit(mips.i_type(0x2B, sp, t2, saved_font_28))
    assembler.emit(mips.i_type(0x23, t1, t2, 0x2C))
    assembler.emit(mips.i_type(0x2B, sp, t2, saved_font_2c))
    mips.load_u32(assembler, a0, FONT_RENDERER_POINTER)
    assembler.emit(mips.i_type(0x23, a0, a0, 0))
    assembler.emit(mips.i_type(0x09, zero, a1, 1))
    assembler.emit(mips.jump(0x03, FONT_INITIALIZE))
    assembler.emit(0)
    mips.load_u32(assembler, t1, FONT_RENDERER_POINTER)
    assembler.emit(mips.i_type(0x23, t1, t1, 0))
    assembler.emit(mips.i_type(0x23, sp, t2, saved_font_28))
    assembler.emit(mips.i_type(0x2B, t1, t2, 0x28))
    assembler.emit(mips.i_type(0x23, sp, t2, saved_font_2c))
    assembler.emit(mips.i_type(0x2B, t1, t2, 0x2C))
    assembler.emit(mips.i_type(0x23, t1, t2, 0x6C))
    assembler.emit(mips.i_type(0x2B, sp, t2, saved_font_6c))
    assembler.emit(mips.r_type(t1, zero, a0, 0x21))
    assembler.emit(mips.i_type(0x23, sp, a1, saved_a2))
    assembler.emit(mips.jump(0x03, FONT_SET_CONTEXT))
    assembler.emit(0)
    emit_scale_one(assembler, t0, t2)
    assembler.emit(mips.i_type(0x23, sp, t1, saved_a1))
    assembler.emit(mips.i_type(0x23, t1, a0, 8))
    assembler.emit(mips.r_type(zero, zero, a1, 0x21))
    assembler.jump_symbol(0x03, MEASURE)
    assembler.emit(0)
    assembler.emit(mips.r_type(v0, zero, t3, 0x21))
    assembler.emit(
        mips.i_type(0x0A, t3, t2, CHARACTER_BODY_BOX_WIDTH + 1)
    )
    assembler.branch(0x05, t2, zero, "character_draw")
    assembler.emit(0)
    assembler.emit(mips.mtc1(t3, 0))
    assembler.emit(mips.cop1(0x20, 0, 0, fmt=20))
    mips.load_u32(
        assembler, t2, float_bits(float(CHARACTER_BODY_BOX_WIDTH))
    )
    assembler.emit(mips.mtc1(t2, 1))
    assembler.emit(mips.cop1(0x03, 2, 1, 0))
    assembler.emit(mips.i_type(0x0F, zero, t2, SCALE_ADDRESS >> 16))
    assembler.emit(
        mips.i_type(0x39, t2, 2, SCALE_ADDRESS & 0xFFFF)
    )

    assembler.label("character_draw")
    emit_load_float(
        assembler,
        t2,
        12,
        CHARACTER_BODY_BOX_X + CHARACTER_BODY_BOX_WIDTH / 2.0,
    )
    emit_load_float(assembler, t2, 13, CHARACTER_BODY_DRAW_Y)
    assembler.emit(mips.i_type(0x23, sp, t1, saved_a1))
    assembler.emit(mips.i_type(0x23, t1, a0, 8))
    mips.load_u32(assembler, a1, 0xFF000000)
    assembler.emit(mips.jump(0x03, FONT_CENTER))
    assembler.emit(0)
    mips.load_u32(assembler, t1, FONT_RENDERER_POINTER)
    assembler.emit(mips.i_type(0x23, t1, t1, 0))
    assembler.emit(mips.i_type(0x23, sp, t2, saved_font_6c))
    assembler.emit(mips.i_type(0x2B, t1, t2, 0x6C))
    assembler.branch(0x04, zero, zero, "restore_record")
    assembler.emit(0)

    assembler.label("call_original")
    for register, offset in (
        (a0, saved_a0),
        (a1, saved_a1),
        (a2, saved_a2),
        (a3, saved_a3),
    ):
        assembler.emit(mips.i_type(0x23, sp, register, offset))
    assembler.jump_symbol(0x03, UI_TRAMPOLINE)
    assembler.emit(0)

    assembler.label("restore_record")
    assembler.emit(mips.i_type(0x23, sp, t1, saved_a1))
    assembler.emit(mips.i_type(0x23, sp, t2, saved_record_x))
    assembler.emit(mips.i_type(0x2B, t1, t2, 0))
    assembler.emit(mips.i_type(0x23, sp, t2, saved_record_y))
    assembler.emit(mips.i_type(0x2B, t1, t2, 4))
    assembler.emit(mips.i_type(0x23, sp, t2, scale_modified))
    assembler.branch(0x04, t2, zero, "restore_return")
    assembler.emit(0)
    emit_scale_one(assembler, t1, t2)
    assembler.label("restore_return")
    assembler.emit(mips.i_type(0x23, sp, ra, saved_ra))
    assembler.emit(mips.r_type(ra, zero, zero, 0x08))
    assembler.emit(mips.i_type(0x09, sp, sp, frame_size))
    payload, relocations = assembler.build()
    return Fragment(UI_HELPER, payload, relocations)


def fragments() -> tuple[Fragment, ...]:
    selected_trampoline = struct.pack(
        "<4I",
        mips.i_type(0x09, 29, 29, -0x40),
        mips.i_type(0x3F, 29, 31, 0x30),
        mips.jump(0x02, SELECTED_ORIGINAL_BODY),
        0,
    )
    ui_trampoline = struct.pack(
        "<4I",
        mips.i_type(0x09, 29, 29, -0x60),
        mips.i_type(0x3F, 29, 31, 0x40),
        mips.jump(0x02, UI_ORIGINAL_BODY),
        0,
    )
    result = (
        Fragment(PLAIN_SPACE, TEXT_METRICS_HELPERS[0x00:0x40]),
        Fragment(NEWLINE_ADVANCE, TEXT_METRICS_HELPERS[0x40:0x70]),
        Fragment(MEASURE, TEXT_METRICS_HELPERS[0x70:0xC8]),
        build_controls_fit(),
        Fragment(SCALE_ADVANCE, SCALE_ADVANCE_BYTES),
        build_selected_helper(),
        Fragment(SELECTED_TRAMPOLINE, selected_trampoline),
        build_ui_helper(),
        Fragment(UI_TRAMPOLINE, ui_trampoline),
    )
    symbols = [fragment.symbol for fragment in result]
    if len(symbols) != len(set(symbols)):
        raise ValueError("generated resident fragments export duplicate symbols")
    return result


def tsv_bytes(fields: list[str], rows: list[dict[str, object]]) -> bytes:
    from io import StringIO

    stream = StringIO(newline="")
    writer = csv.DictWriter(
        stream, fieldnames=fields, delimiter="\t", lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def generated_outputs() -> tuple[bytes, bytes, bytes]:
    generated = fragments()
    blob = bytearray()
    offsets: dict[str, int] = {}
    for fragment in generated:
        while len(blob) % 4:
            blob.append(0)
        offsets[fragment.symbol] = len(blob)
        blob.extend(fragment.payload)
    blob_bytes = bytes(blob)
    blob_hash = hashlib.sha256(blob_bytes).hexdigest().upper()
    fragment_rows = [
        {
            "fragment_id": fragment.symbol,
            "kind": fragment.kind,
            "alignment": fragment.alignment,
            "blob_path": BLOB_RELATIVE.as_posix(),
            "blob_offset": f"0x{offsets[fragment.symbol]:X}",
            "length": len(fragment.payload),
            "blob_sha256": blob_hash,
            "init": int(fragment.init),
        }
        for fragment in generated
    ]
    relocation_rows: list[dict[str, object]] = []
    relocation_index = 1
    for fragment in generated:
        for order, relocation in enumerate(fragment.relocations, 1):
            relocation_rows.append(
                {
                    "relocation_id": f"FR-R{relocation_index:03d}",
                    "fragment_id": fragment.symbol,
                    "order": order * 10,
                    "offset": f"0x{relocation.offset:X}",
                    "kind": relocation.kind,
                    "symbol": relocation.symbol,
                    "addend": relocation.addend,
                }
            )
            relocation_index += 1
    return (
        blob_bytes,
        tsv_bytes(engine.FRAGMENT_FIELDS, fragment_rows),
        tsv_bytes(engine.RELOCATION_FIELDS, relocation_rows),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        action="store_true",
        help="write the verified resident blob and declarative tables",
    )
    args = parser.parse_args()
    outputs = zip(
        (BLOB_OUTPUT, FRAGMENTS_OUTPUT, RELOCATIONS_OUTPUT),
        generated_outputs(),
        strict=True,
    )
    action = "verified"
    for path, payload in outputs:
        if args.write:
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.is_file() or path.read_bytes() != payload:
                path.write_bytes(payload)
            action = "wrote"
        elif not path.is_file():
            raise FileNotFoundError(path)
        elif path.read_bytes() != payload:
            raise ValueError(f"generated output differs: {path}")
        print(f"{action}\t{path.relative_to(REPOSITORY).as_posix()}")
        print(f"size\t{len(payload)}")
        print(f"sha256\t{hashlib.sha256(payload).hexdigest().upper()}")


if __name__ == "__main__":
    main()
