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
LEGACY_BLOB_RELATIVE = Path("assets") / "font_renderer_resident.bin"
LEGACY_BLOB_OUTPUT = MODULE / LEGACY_BLOB_RELATIVE
V2_BLOB_RELATIVE = Path("assets") / "font_renderer_v2_resident.bin"
V2_BLOB_OUTPUT = MODULE / V2_BLOB_RELATIVE
FRAGMENTS_OUTPUT = MODULE / "fragments.tsv"
RELOCATIONS_OUTPUT = MODULE / "relocations.tsv"
PACKED_METRICS_INPUT = load_project_paths(REPOSITORY).path(
    "features",
    "localization",
    "binary_patcher",
    "assets",
    "nun5_semantic_14x20_packed_map.bin",
)

PREFIX = "localization.font"
PLAIN_SPACE = f"{PREFIX}.plain_space"
NEWLINE_ADVANCE = f"{PREFIX}.newline_advance"
MEASURE = f"{PREFIX}.measure"
ASCII_WIDTHS = f"{PREFIX}.ascii_widths"
CONTROLS_FIT = f"{PREFIX}.controls_fit"
SCALE_ADVANCE = f"{PREFIX}.scale_advance"
SELECTED_HELPER = f"{PREFIX}.selected_helper"
SELECTED_TRAMPOLINE = f"{PREFIX}.selected_trampoline"
UI_HELPER = f"{PREFIX}.ui_helper"
UI_TRAMPOLINE = f"{PREFIX}.ui_trampoline"

V2_PREFIX = f"{PREFIX}.v2"
V2_SESSION_POINTER = f"{V2_PREFIX}.session_pointer"
V2_ASCII_WIDTHS = f"{V2_PREFIX}.ascii_widths"
V2_MEASURE = f"{V2_PREFIX}.measure"
V2_PREPARE = f"{V2_PREFIX}.prepare"
V2_ADAPTER_CALL = f"{V2_PREFIX}.adapter_call"
V2_CONTROLS_ADAPTER = f"{V2_PREFIX}.controls_adapter"
V2_CONTROLS_CALLBACK = f"{V2_PREFIX}.controls_callback"
V2_PLAIN_SPACE = f"{V2_PREFIX}.plain_space"
V2_NEWLINE_ADVANCE = f"{V2_PREFIX}.newline_advance"
V2_RIGHT_EDGE = f"{V2_PREFIX}.right_edge"
V2_HALF_SPACE = f"{V2_PREFIX}.half_space"
V2_GLYPH_ADVANCE = f"{V2_PREFIX}.glyph_advance"

SCALE_ADDRESS = 0x0060737C
FONT_RENDERER_POINTER = 0x00607470
FONT_INITIALIZE = 0x00186510
FONT_SET_CONTEXT = 0x001866D0
FONT_MEASURE = 0x003798E0
FONT_CENTER = 0x00379240
PACKED_METRICS_SHA256 = (
    "6F691015E5BA54EA87B2976970D828863E274BB543CC3D531D93800018EB7A5E"
)
ASCII_WIDTHS_SHA256 = (
    "4F4F960D71A6ED85354603D8E39962D971A5DA45095FFEBC01B976BA16105568"
)
ASCII_FIRST = 0x20
ASCII_LAST = 0x7E
SECONDARY_CELL_WIDTH = 14
NUN5_SPACE_WIDTH = 8
NUN5_SPACE_CORRECTION = 6

PLAIN_SPACE_RETURN = 0x00189300
NEWLINE_ADVANCE_RETURN = 0x00188670
V2_PLAIN_SPACE_RESUME = 0x001892F4
V2_NEWLINE_ORIGINAL_RESUME = 0x0018860C
V2_RIGHT_EDGE_RESUME = 0x00187F78
V2_HALF_SPACE_RESUME = 0x00188A84
V2_GLYPH_ADVANCE_RESUME = 0x001896E0
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
COMMAND_CHART_TITLE_OUTER = 0x0087A930
PRACTICE_COMMAND_TITLE_OUTER = 0x00878AA0

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
COMMAND_CHART_TITLE_BOX_X = 27.2
COMMAND_CHART_TITLE_BOX_WIDTH = 288
COMMAND_CHART_TITLE_Y_OFFSET = -3.8
PRACTICE_COMMAND_TITLE_BOX_X = 31.2
PRACTICE_COMMAND_TITLE_BOX_WIDTH = 352
PRACTICE_COMMAND_TITLE_Y_OFFSET = -6.8

V2_SESSION_PREVIOUS = 0x00
V2_SESSION_TEXT = 0x04
V2_SESSION_BOX_X = 0x08
V2_SESSION_BOX_Y = 0x0C
V2_SESSION_BOX_WIDTH = 0x10
V2_SESSION_BOX_HEIGHT = 0x14
V2_SESSION_HORIZONTAL_ALIGNMENT = 0x18
V2_SESSION_VERTICAL_ALIGNMENT = 0x1C
V2_SESSION_FLAGS = 0x20
V2_SESSION_LINE_LIMIT = 0x24
V2_SESSION_LINE_HEIGHT = 0x28
V2_SESSION_CALLBACK = 0x2C
V2_SESSION_MEASURED_WIDTH = 0x30
V2_SESSION_LINE_COUNT = 0x34
V2_SESSION_SCALE_X = 0x38
V2_SESSION_SCALE_Y = 0x3C
V2_SESSION_RENDERED_WIDTH = 0x40
V2_SESSION_RENDERED_HEIGHT = 0x44
V2_SESSION_DRAW_X = 0x48
V2_SESSION_DRAW_Y = 0x4C
V2_SESSION_CALLBACK_ARG0 = 0x50
V2_SESSION_CALLBACK_ARG1 = 0x54
V2_SESSION_CALLBACK_ARG2 = 0x58
V2_SESSION_CALLBACK_ARG3 = 0x5C
V2_SESSION_SAVED_TRACKING = 0x60
V2_SESSION_SAVED_SCALE = 0x64
V2_SESSION_SIZE = 0x68

V2_FLAG_SHRINK_X = 0x01
V2_FLAG_BR_TAGS = 0x02
V2_FLAG_NEWLINE_BYTES = 0x04

CONTROLS_BOX_WIDTH = 128
CONTROLS_BOX_HEIGHT = 20
CONTROLS_LINE_HEIGHT = 20.0
CONTROLS_LABEL_X_CORRECTION = -2.0

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


def build_ascii_widths() -> bytes:
    packed_map = PACKED_METRICS_INPUT.read_bytes()
    actual_hash = hashlib.sha256(packed_map).hexdigest().upper()
    if actual_hash != PACKED_METRICS_SHA256:
        raise ValueError(
            f"packed metric map hash {actual_hash} != "
            f"{PACKED_METRICS_SHA256}"
        )
    rows = [
        value
        for key, value in struct.iter_unpack("<HH", packed_map)
        if key == 0xFFFF
    ]
    count = ASCII_LAST - ASCII_FIRST + 1
    if len(rows) < count:
        raise ValueError(
            f"packed metric map has {len(rows)} empty rows; need {count}"
        )
    widths = bytearray()
    for cell, value in enumerate(rows[:count]):
        left = value & 0x0F
        right = (value >> 8) & 0x0F
        width = SECONDARY_CELL_WIDTH - left - right
        if cell == 0:
            width = NUN5_SPACE_WIDTH
        if not 0 <= width <= 0xFF:
            raise ValueError(f"invalid ASCII width at cell {cell}: {width}")
        widths.append(width)
    result = bytes(widths)
    result_hash = hashlib.sha256(result).hexdigest().upper()
    if result_hash != ASCII_WIDTHS_SHA256:
        raise ValueError(
            f"ASCII width table hash {result_hash} != "
            f"{ASCII_WIDTHS_SHA256}"
        )
    return result


def build_measure() -> Fragment:
    zero, v0, v1, a0 = 0, 2, 3, 4
    t0, t1, t2, t3 = 8, 9, 10, 11
    s0, s1 = 16, 17
    sp, ra = 29, 31
    frame_size = 0x20
    saved_s1 = 0x14
    saved_s0 = 0x18
    saved_ra = 0x1C

    assembler = mips.Assembler()
    assembler.emit(mips.i_type(0x09, sp, sp, -frame_size))
    assembler.emit(mips.i_type(0x2B, sp, ra, saved_ra))
    assembler.emit(mips.i_type(0x2B, sp, s0, saved_s0))
    assembler.emit(mips.i_type(0x2B, sp, s1, saved_s1))
    assembler.emit(mips.r_type(a0, zero, s0, 0x21))
    assembler.emit(mips.jump(0x03, FONT_MEASURE))
    assembler.emit(0)
    assembler.emit(mips.r_type(v0, zero, s1, 0x21))
    assembler.emit(mips.r_type(v0, zero, v1, 0x21))
    assembler.emit(mips.r_type(s0, zero, t0, 0x21))

    assembler.label("validate_ascii")
    assembler.emit(mips.i_type(0x24, t0, t1, 0))
    assembler.branch(0x04, t1, zero, "measure_ascii")
    assembler.emit(0)
    assembler.emit(mips.i_type(0x0B, t1, t2, ASCII_FIRST))
    assembler.branch(0x05, t2, zero, "legacy_space_correction")
    assembler.emit(0)
    assembler.emit(mips.i_type(0x0B, t1, t2, ASCII_LAST + 1))
    assembler.branch(0x04, t2, zero, "legacy_space_correction")
    assembler.emit(mips.i_type(0x09, t0, t0, 1))
    assembler.branch(0x04, zero, zero, "validate_ascii")
    assembler.emit(0)

    assembler.label("measure_ascii")
    assembler.load_symbol_word(t0, t0, 0x09, ASCII_WIDTHS)
    assembler.emit(mips.r_type(s0, zero, t1, 0x21))
    assembler.emit(mips.r_type(zero, zero, t2, 0x21))
    assembler.label("ascii_loop")
    assembler.emit(mips.i_type(0x24, t1, t3, 0))
    assembler.branch(0x04, t3, zero, "return_ascii")
    assembler.emit(mips.i_type(0x09, t1, t1, 1))
    assembler.emit(mips.i_type(0x09, t3, t3, -ASCII_FIRST))
    assembler.emit(mips.r_type(t0, t3, t3, 0x21))
    assembler.emit(mips.i_type(0x24, t3, t3, 0))
    assembler.branch(0x04, zero, zero, "ascii_loop")
    assembler.emit(mips.r_type(t2, t3, t2, 0x21))

    assembler.label("return_ascii")
    assembler.emit(mips.r_type(t2, zero, v0, 0x21))
    assembler.branch(0x04, zero, zero, "restore_return")
    assembler.emit(mips.r_type(s1, zero, v1, 0x21))

    assembler.label("legacy_space_correction")
    assembler.emit(mips.r_type(s0, zero, t0, 0x21))
    assembler.emit(mips.r_type(s1, zero, t1, 0x21))
    assembler.label("legacy_loop")
    assembler.emit(mips.i_type(0x24, t0, t2, 0))
    assembler.branch(0x04, t2, zero, "return_legacy")
    assembler.emit(mips.i_type(0x09, t0, t0, 1))
    assembler.emit(mips.i_type(0x09, zero, t3, ASCII_FIRST))
    assembler.branch(0x05, t2, t3, "legacy_loop")
    assembler.emit(0)
    assembler.emit(
        mips.i_type(0x09, t1, t1, -NUN5_SPACE_CORRECTION)
    )
    assembler.branch(0x04, zero, zero, "legacy_loop")
    assembler.emit(0)

    assembler.label("return_legacy")
    assembler.emit(mips.r_type(t1, zero, v0, 0x21))
    assembler.emit(mips.r_type(s1, zero, v1, 0x21))

    assembler.label("restore_return")
    assembler.emit(mips.i_type(0x23, sp, s1, saved_s1))
    assembler.emit(mips.i_type(0x23, sp, s0, saved_s0))
    assembler.emit(mips.i_type(0x23, sp, ra, saved_ra))
    assembler.emit(mips.r_type(ra, zero, zero, 0x08))
    assembler.emit(mips.i_type(0x09, sp, sp, frame_size))
    payload, relocations = assembler.build()
    return Fragment(MEASURE, payload, relocations)


def build_v2_measure() -> Fragment:
    zero, v0, v1, a0, a1 = 0, 2, 3, 4, 5
    t0, t1, t2, t3 = 8, 9, 10, 11
    t4, t5, t6, t7 = 12, 13, 14, 15
    ra = 31

    assembler = mips.Assembler()
    assembler.emit(mips.r_type(a0, zero, t0, 0x21))
    assembler.emit(mips.r_type(a1, zero, t7, 0x21))
    assembler.load_symbol_word(t2, t2, 0x09, V2_ASCII_WIDTHS)
    assembler.emit(mips.r_type(zero, zero, t3, 0x21))
    assembler.emit(mips.r_type(zero, zero, t4, 0x21))
    assembler.emit(mips.i_type(0x09, zero, t5, 1))

    assembler.label("loop")
    assembler.emit(mips.i_type(0x24, t0, t1, 0))
    assembler.branch(0x04, t1, zero, "finish")
    assembler.emit(0)

    assembler.emit(mips.i_type(0x0C, t7, t6, V2_FLAG_BR_TAGS))
    assembler.branch(0x04, t6, zero, "check_newline")
    assembler.emit(mips.i_type(0x09, zero, t6, ord("<")))
    assembler.branch(0x05, t1, t6, "check_newline")
    assembler.emit(0)
    assembler.emit(mips.i_type(0x24, t0, t6, 1))
    assembler.emit(mips.i_type(0x09, zero, v0, ord("b")))
    assembler.branch(0x05, t6, v0, "check_newline")
    assembler.emit(0)
    assembler.emit(mips.i_type(0x24, t0, t6, 2))
    assembler.emit(mips.i_type(0x09, zero, v0, ord("r")))
    assembler.branch(0x05, t6, v0, "check_newline")
    assembler.emit(0)
    assembler.emit(mips.i_type(0x24, t0, t6, 3))
    assembler.emit(mips.i_type(0x09, zero, v0, ord(">")))
    assembler.branch(0x05, t6, v0, "check_newline")
    assembler.emit(0)
    assembler.emit(mips.i_type(0x09, t0, t0, 4))
    assembler.branch(0x04, zero, zero, "line_break")
    assembler.emit(0)

    assembler.label("check_newline")
    assembler.emit(mips.i_type(0x0C, t7, t6, V2_FLAG_NEWLINE_BYTES))
    assembler.branch(0x04, t6, zero, "check_printable")
    assembler.emit(mips.i_type(0x09, zero, t6, 0x0A))
    assembler.branch(0x05, t1, t6, "check_printable")
    assembler.emit(0)
    assembler.emit(mips.i_type(0x09, t0, t0, 1))

    assembler.label("line_break")
    assembler.emit(mips.r_type(t4, t3, t6, 0x2B))
    assembler.branch(0x04, t6, zero, "line_break_reset")
    assembler.emit(0)
    assembler.emit(mips.r_type(t3, zero, t4, 0x21))
    assembler.label("line_break_reset")
    assembler.emit(mips.r_type(zero, zero, t3, 0x21))
    assembler.emit(mips.i_type(0x09, t5, t5, 1))
    assembler.branch(0x04, zero, zero, "loop")
    assembler.emit(0)

    assembler.label("check_printable")
    assembler.emit(mips.i_type(0x0B, t1, t6, ASCII_FIRST))
    assembler.branch(0x05, t6, zero, "error")
    assembler.emit(0)
    assembler.emit(mips.i_type(0x0B, t1, t6, ASCII_LAST + 1))
    assembler.branch(0x04, t6, zero, "error")
    assembler.emit(mips.i_type(0x09, t0, t0, 1))
    assembler.emit(mips.i_type(0x09, t1, t1, -ASCII_FIRST))
    assembler.emit(mips.r_type(t2, t1, t6, 0x21))
    assembler.emit(mips.i_type(0x24, t6, t6, 0))
    assembler.emit(mips.r_type(t3, t6, t3, 0x21))
    assembler.branch(0x04, zero, zero, "loop")
    assembler.emit(0)

    assembler.label("finish")
    assembler.emit(mips.r_type(t4, t3, t6, 0x2B))
    assembler.branch(0x04, t6, zero, "return_measurement")
    assembler.emit(0)
    assembler.emit(mips.r_type(t3, zero, t4, 0x21))
    assembler.label("return_measurement")
    assembler.emit(mips.r_type(t4, zero, v0, 0x21))
    assembler.emit(mips.r_type(t5, zero, v1, 0x21))
    assembler.emit(mips.r_type(ra, zero, zero, 0x08))
    assembler.emit(0)

    assembler.label("error")
    assembler.emit(mips.i_type(0x09, zero, v0, -1))
    assembler.emit(mips.r_type(zero, zero, v1, 0x21))
    assembler.emit(mips.r_type(ra, zero, zero, 0x08))
    assembler.emit(0)
    payload, relocations = assembler.build()
    return Fragment(V2_MEASURE, payload, relocations)


def build_v2_prepare() -> Fragment:
    zero, v0, v1, a0, a1 = 0, 2, 3, 4, 5
    t0, t1, t2, t3 = 8, 9, 10, 11
    s0, sp, ra = 16, 29, 31
    frame_size = 0x20
    saved_s0 = 0x18
    saved_ra = 0x1C

    assembler = mips.Assembler()
    assembler.emit(mips.i_type(0x09, sp, sp, -frame_size))
    assembler.emit(mips.i_type(0x2B, sp, ra, saved_ra))
    assembler.emit(mips.i_type(0x2B, sp, s0, saved_s0))
    assembler.branch(0x04, a0, zero, "error")
    assembler.emit(mips.r_type(a0, zero, s0, 0x21))
    assembler.emit(mips.i_type(0x23, s0, a0, V2_SESSION_TEXT))
    assembler.branch(0x04, a0, zero, "error")
    assembler.emit(mips.i_type(0x23, s0, a1, V2_SESSION_FLAGS))
    assembler.jump_symbol(0x03, V2_MEASURE)
    assembler.emit(0)
    assembler.branch(0x01, v0, zero, "error")
    assembler.emit(0)

    assembler.emit(
        mips.i_type(0x2B, s0, v0, V2_SESSION_MEASURED_WIDTH)
    )
    assembler.emit(mips.i_type(0x2B, s0, v1, V2_SESSION_LINE_COUNT))
    assembler.emit(mips.i_type(0x23, s0, t0, V2_SESSION_LINE_LIMIT))
    assembler.branch(0x04, t0, zero, "line_limit_ok")
    assembler.emit(mips.r_type(t0, v1, t1, 0x2B))
    assembler.branch(0x05, t1, zero, "error")
    assembler.emit(0)
    assembler.label("line_limit_ok")

    assembler.emit(mips.i_type(0x23, s0, t0, V2_SESSION_BOX_WIDTH))
    assembler.branch(0x04, t0, zero, "error")
    assembler.emit(mips.i_type(0x23, s0, t1, V2_SESSION_BOX_HEIGHT))
    assembler.branch(0x04, t1, zero, "error")
    assembler.emit(0)

    mips.load_u32(assembler, t2, float_bits(1.0))
    assembler.emit(mips.mtc1(t2, 2))
    assembler.emit(
        mips.i_type(0x39, s0, 2, V2_SESSION_SCALE_X)
    )
    assembler.emit(
        mips.i_type(0x39, s0, 2, V2_SESSION_SCALE_Y)
    )
    assembler.emit(mips.mtc1(v0, 0))
    assembler.emit(mips.cop1(0x20, 0, 0, fmt=20))
    assembler.emit(mips.i_type(0x23, s0, t2, V2_SESSION_FLAGS))
    assembler.emit(mips.i_type(0x0C, t2, t2, V2_FLAG_SHRINK_X))
    assembler.branch(0x04, t2, zero, "scale_ready")
    assembler.emit(mips.r_type(t0, v0, t3, 0x2B))
    assembler.branch(0x04, t3, zero, "scale_ready")
    assembler.emit(mips.mtc1(t0, 1))
    assembler.emit(mips.cop1(0x20, 1, 1, fmt=20))
    assembler.emit(mips.cop1(0x03, 2, 1, 0))
    assembler.emit(
        mips.i_type(0x39, s0, 2, V2_SESSION_SCALE_X)
    )

    assembler.label("scale_ready")
    assembler.emit(mips.cop1(0x02, 3, 0, 2))
    assembler.emit(
        mips.i_type(0x39, s0, 3, V2_SESSION_RENDERED_WIDTH)
    )
    assembler.emit(mips.mtc1(v1, 4))
    assembler.emit(mips.cop1(0x20, 4, 4, fmt=20))
    assembler.emit(
        mips.i_type(0x31, s0, 5, V2_SESSION_LINE_HEIGHT)
    )
    assembler.emit(mips.cop1(0x02, 4, 4, 5))
    assembler.emit(
        mips.i_type(0x39, s0, 4, V2_SESSION_RENDERED_HEIGHT)
    )

    assembler.emit(mips.i_type(0x31, s0, 0, V2_SESSION_BOX_X))
    assembler.emit(
        mips.i_type(
            0x23,
            s0,
            t2,
            V2_SESSION_HORIZONTAL_ALIGNMENT,
        )
    )
    assembler.branch(0x04, t2, zero, "store_x")
    assembler.emit(0)
    assembler.emit(mips.i_type(0x09, zero, t3, 1))
    assembler.branch(0x04, t2, t3, "center_x")
    assembler.emit(0)
    assembler.emit(mips.i_type(0x09, zero, t3, 2))
    assembler.branch(0x05, t2, t3, "error")
    assembler.emit(0)
    assembler.emit(mips.mtc1(t0, 1))
    assembler.emit(mips.cop1(0x20, 1, 1, fmt=20))
    assembler.emit(mips.cop1(0x00, 0, 0, 1))
    assembler.emit(mips.i_type(0x31, s0, 2, V2_SESSION_RENDERED_WIDTH))
    assembler.emit(mips.cop1(0x01, 0, 0, 2))
    assembler.branch(0x04, zero, zero, "store_x")
    assembler.emit(0)

    assembler.label("center_x")
    assembler.emit(mips.mtc1(t0, 1))
    assembler.emit(mips.cop1(0x20, 1, 1, fmt=20))
    assembler.emit(mips.i_type(0x31, s0, 2, V2_SESSION_RENDERED_WIDTH))
    assembler.emit(mips.cop1(0x01, 1, 1, 2))
    emit_load_float(assembler, t3, 3, 0.5)
    assembler.emit(mips.cop1(0x02, 1, 1, 3))
    assembler.emit(mips.cop1(0x00, 0, 0, 1))
    assembler.label("store_x")
    assembler.emit(mips.i_type(0x39, s0, 0, V2_SESSION_DRAW_X))

    assembler.emit(mips.i_type(0x31, s0, 0, V2_SESSION_BOX_Y))
    assembler.emit(
        mips.i_type(
            0x23,
            s0,
            t2,
            V2_SESSION_VERTICAL_ALIGNMENT,
        )
    )
    assembler.branch(0x04, t2, zero, "store_y")
    assembler.emit(0)
    assembler.emit(mips.i_type(0x09, zero, t3, 1))
    assembler.branch(0x04, t2, t3, "center_y")
    assembler.emit(0)
    assembler.emit(mips.i_type(0x09, zero, t3, 2))
    assembler.branch(0x05, t2, t3, "error")
    assembler.emit(0)
    assembler.emit(mips.mtc1(t1, 1))
    assembler.emit(mips.cop1(0x20, 1, 1, fmt=20))
    assembler.emit(mips.cop1(0x00, 0, 0, 1))
    assembler.emit(mips.i_type(0x31, s0, 2, V2_SESSION_RENDERED_HEIGHT))
    assembler.emit(mips.cop1(0x01, 0, 0, 2))
    assembler.branch(0x04, zero, zero, "store_y")
    assembler.emit(0)

    assembler.label("center_y")
    assembler.emit(mips.mtc1(t1, 1))
    assembler.emit(mips.cop1(0x20, 1, 1, fmt=20))
    assembler.emit(mips.i_type(0x31, s0, 2, V2_SESSION_RENDERED_HEIGHT))
    assembler.emit(mips.cop1(0x01, 1, 1, 2))
    emit_load_float(assembler, t3, 3, 0.5)
    assembler.emit(mips.cop1(0x02, 1, 1, 3))
    assembler.emit(mips.cop1(0x00, 0, 0, 1))
    assembler.label("store_y")
    assembler.emit(mips.i_type(0x39, s0, 0, V2_SESSION_DRAW_Y))
    assembler.emit(mips.r_type(zero, zero, v0, 0x21))
    assembler.branch(0x04, zero, zero, "restore")
    assembler.emit(0)

    assembler.label("error")
    assembler.emit(mips.i_type(0x09, zero, v0, -1))
    assembler.label("restore")
    assembler.emit(mips.i_type(0x23, sp, s0, saved_s0))
    assembler.emit(mips.i_type(0x23, sp, ra, saved_ra))
    assembler.emit(mips.r_type(ra, zero, zero, 0x08))
    assembler.emit(mips.i_type(0x09, sp, sp, frame_size))
    payload, relocations = assembler.build()
    return Fragment(V2_PREPARE, payload, relocations)


def build_v2_adapter_call() -> Fragment:
    """Prepare and publish one layout session around an existing draw call."""

    zero, v0, a0, a1, a2, a3 = 0, 2, 4, 5, 6, 7
    t0, t1, t9 = 8, 9, 25
    s0, s1, s2, s3 = 16, 17, 18, 19
    sp, ra = 29, 31
    frame_size = 0x30
    saved_s3 = 0x1C
    saved_s2 = 0x20
    saved_s1 = 0x24
    saved_s0 = 0x28
    saved_ra = 0x2C

    assembler = mips.Assembler()
    assembler.emit(mips.i_type(0x09, sp, sp, -frame_size))
    assembler.emit(mips.i_type(0x2B, sp, ra, saved_ra))
    assembler.emit(mips.i_type(0x2B, sp, s0, saved_s0))
    assembler.emit(mips.i_type(0x2B, sp, s1, saved_s1))
    assembler.emit(mips.i_type(0x2B, sp, s2, saved_s2))
    assembler.emit(mips.i_type(0x2B, sp, s3, saved_s3))
    assembler.branch(0x04, a0, zero, "error")
    assembler.emit(mips.r_type(a0, zero, s0, 0x21))
    assembler.emit(mips.i_type(0x23, s0, t0, V2_SESSION_CALLBACK))
    assembler.branch(0x04, t0, zero, "error")
    assembler.emit(mips.r_type(s0, zero, a0, 0x21))
    assembler.jump_symbol(0x03, V2_PREPARE)
    assembler.emit(0)
    assembler.branch(0x05, v0, zero, "error")
    assembler.emit(0)

    mips.load_u32(assembler, t0, FONT_RENDERER_POINTER)
    assembler.emit(mips.i_type(0x23, t0, s2, 0))
    assembler.branch(0x04, s2, zero, "error")
    assembler.emit(0)
    assembler.load_symbol_word(
        t0,
        s1,
        0x09,
        V2_SESSION_POINTER,
    )
    assembler.emit(mips.i_type(0x23, s1, t1, 0))
    assembler.emit(
        mips.i_type(0x2B, s0, t1, V2_SESSION_PREVIOUS)
    )
    assembler.emit(mips.i_type(0x23, s2, t1, 0x3C))
    assembler.emit(
        mips.i_type(0x2B, s0, t1, V2_SESSION_SAVED_TRACKING)
    )
    mips.load_u32(assembler, t0, SCALE_ADDRESS)
    assembler.emit(mips.i_type(0x23, t0, t1, 0))
    assembler.emit(
        mips.i_type(0x2B, s0, t1, V2_SESSION_SAVED_SCALE)
    )

    assembler.emit(mips.i_type(0x2B, s2, zero, 0x3C))
    assembler.emit(
        mips.i_type(0x23, s0, t1, V2_SESSION_SCALE_X)
    )
    assembler.emit(mips.i_type(0x2B, t0, t1, 0))
    assembler.emit(mips.i_type(0x2B, s1, s0, 0))

    assembler.emit(
        mips.i_type(0x23, s0, a0, V2_SESSION_CALLBACK_ARG0)
    )
    assembler.emit(
        mips.i_type(0x23, s0, a1, V2_SESSION_CALLBACK_ARG1)
    )
    assembler.emit(
        mips.i_type(0x23, s0, a2, V2_SESSION_CALLBACK_ARG2)
    )
    assembler.emit(
        mips.i_type(0x23, s0, a3, V2_SESSION_CALLBACK_ARG3)
    )
    assembler.emit(mips.i_type(0x23, s0, t9, V2_SESSION_CALLBACK))
    assembler.emit(mips.r_type(t9, zero, ra, 0x09))
    assembler.emit(0)
    assembler.emit(mips.r_type(v0, zero, s3, 0x21))

    mips.load_u32(assembler, t0, SCALE_ADDRESS)
    assembler.emit(
        mips.i_type(0x23, s0, t1, V2_SESSION_SAVED_SCALE)
    )
    assembler.emit(mips.i_type(0x2B, t0, t1, 0))
    assembler.emit(
        mips.i_type(0x23, s0, t1, V2_SESSION_SAVED_TRACKING)
    )
    assembler.emit(mips.i_type(0x2B, s2, t1, 0x3C))
    assembler.emit(
        mips.i_type(0x23, s0, t1, V2_SESSION_PREVIOUS)
    )
    assembler.emit(mips.i_type(0x2B, s1, t1, 0))
    assembler.emit(mips.r_type(s3, zero, v0, 0x21))
    assembler.branch(0x04, zero, zero, "restore")
    assembler.emit(0)

    assembler.label("error")
    assembler.emit(mips.i_type(0x09, zero, v0, -1))
    assembler.label("restore")
    assembler.emit(mips.i_type(0x23, sp, s3, saved_s3))
    assembler.emit(mips.i_type(0x23, sp, s2, saved_s2))
    assembler.emit(mips.i_type(0x23, sp, s1, saved_s1))
    assembler.emit(mips.i_type(0x23, sp, s0, saved_s0))
    assembler.emit(mips.i_type(0x23, sp, ra, saved_ra))
    assembler.emit(mips.r_type(ra, zero, zero, 0x08))
    assembler.emit(mips.i_type(0x09, sp, sp, frame_size))
    payload, relocations = assembler.build()
    return Fragment(V2_ADAPTER_CALL, payload, relocations)


def build_v2_controls_callback() -> Fragment:
    """Draw one prepared Controls label through NA2's centered renderer."""

    zero, v0, a0, a1, a2 = 0, 2, 4, 5, 6
    t0 = 8
    s0, s1, s2 = 16, 17, 18
    sp, ra = 29, 31
    frame_size = 0x20
    saved_s2 = 0x10
    saved_s1 = 0x14
    saved_s0 = 0x18
    saved_ra = 0x1C

    assembler = mips.Assembler()
    assembler.emit(mips.i_type(0x09, sp, sp, -frame_size))
    assembler.emit(mips.i_type(0x2B, sp, ra, saved_ra))
    assembler.emit(mips.i_type(0x2B, sp, s0, saved_s0))
    assembler.emit(mips.i_type(0x2B, sp, s1, saved_s1))
    assembler.emit(mips.i_type(0x2B, sp, s2, saved_s2))
    assembler.emit(mips.r_type(a0, zero, s0, 0x21))
    assembler.emit(mips.r_type(a1, zero, s1, 0x21))
    assembler.emit(mips.r_type(a2, zero, s2, 0x21))

    assembler.emit(mips.r_type(zero, zero, a1, 0x21))
    assembler.emit(mips.jump(0x03, FONT_MEASURE))
    assembler.emit(0)
    assembler.emit(mips.r_type(zero, v0, t0, 0x03, shift=1))
    assembler.emit(mips.mtc1(t0, 0))
    assembler.emit(mips.cop1(0x20, 0, 0, fmt=20))
    assembler.emit(mips.i_type(0x31, s2, 12, V2_SESSION_DRAW_X))
    assembler.emit(mips.cop1(0x00, 12, 12, 0))
    assembler.emit(mips.i_type(0x31, s2, 13, V2_SESSION_DRAW_Y))
    assembler.emit(mips.r_type(s0, zero, a0, 0x21))
    assembler.emit(mips.r_type(s1, zero, a1, 0x21))
    assembler.emit(mips.jump(0x03, FONT_CENTER))
    assembler.emit(0)

    assembler.emit(mips.i_type(0x23, sp, s2, saved_s2))
    assembler.emit(mips.i_type(0x23, sp, s1, saved_s1))
    assembler.emit(mips.i_type(0x23, sp, s0, saved_s0))
    assembler.emit(mips.i_type(0x23, sp, ra, saved_ra))
    assembler.emit(mips.r_type(ra, zero, zero, 0x08))
    assembler.emit(mips.i_type(0x09, sp, sp, frame_size))
    payload, relocations = assembler.build()
    return Fragment(V2_CONTROLS_CALLBACK, payload, relocations)


def build_v2_controls_adapter() -> Fragment:
    """Prepare the first eight Controls labels in NUN5's 128-unit box."""

    zero, a0, a1 = 0, 4, 5
    t0, t1 = 8, 9
    sp, ra = 29, 31
    frame_size = 0x80
    saved_ra = 0x7C

    assembler = mips.Assembler()
    assembler.emit(mips.i_type(0x09, sp, sp, -frame_size))
    assembler.emit(mips.i_type(0x2B, sp, ra, saved_ra))
    assembler.emit(mips.i_type(0x2B, sp, a0, V2_SESSION_TEXT))
    assembler.emit(mips.i_type(0x2B, sp, a0, V2_SESSION_CALLBACK_ARG0))
    assembler.emit(mips.i_type(0x2B, sp, a1, V2_SESSION_CALLBACK_ARG1))

    emit_load_float(
        assembler,
        t0,
        0,
        CONTROLS_BOX_WIDTH / 2.0 - CONTROLS_LABEL_X_CORRECTION,
    )
    assembler.emit(mips.cop1(0x01, 0, 12, 0))
    assembler.emit(mips.i_type(0x39, sp, 0, V2_SESSION_BOX_X))
    assembler.emit(mips.i_type(0x39, sp, 13, V2_SESSION_BOX_Y))
    mips.load_u32(assembler, t0, CONTROLS_BOX_WIDTH)
    assembler.emit(mips.i_type(0x2B, sp, t0, V2_SESSION_BOX_WIDTH))
    mips.load_u32(assembler, t0, CONTROLS_BOX_HEIGHT)
    assembler.emit(mips.i_type(0x2B, sp, t0, V2_SESSION_BOX_HEIGHT))
    assembler.emit(mips.i_type(0x09, zero, t0, 1))
    assembler.emit(
        mips.i_type(
            0x2B,
            sp,
            t0,
            V2_SESSION_HORIZONTAL_ALIGNMENT,
        )
    )
    assembler.emit(
        mips.i_type(0x2B, sp, zero, V2_SESSION_VERTICAL_ALIGNMENT)
    )
    assembler.emit(mips.i_type(0x2B, sp, t0, V2_SESSION_FLAGS))
    assembler.emit(mips.i_type(0x2B, sp, t0, V2_SESSION_LINE_LIMIT))
    emit_load_float(assembler, t0, 0, CONTROLS_LINE_HEIGHT)
    assembler.emit(mips.i_type(0x39, sp, 0, V2_SESSION_LINE_HEIGHT))
    assembler.load_symbol_word(
        t0,
        t0,
        0x09,
        V2_CONTROLS_CALLBACK,
    )
    assembler.emit(mips.i_type(0x2B, sp, t0, V2_SESSION_CALLBACK))
    assembler.emit(mips.r_type(sp, zero, t1, 0x21))
    assembler.emit(
        mips.i_type(0x2B, sp, t1, V2_SESSION_CALLBACK_ARG2)
    )
    assembler.emit(
        mips.i_type(0x2B, sp, zero, V2_SESSION_CALLBACK_ARG3)
    )

    assembler.emit(mips.r_type(sp, zero, a0, 0x21))
    assembler.jump_symbol(0x03, V2_ADAPTER_CALL)
    assembler.emit(0)
    assembler.emit(mips.i_type(0x23, sp, ra, saved_ra))
    assembler.emit(mips.r_type(ra, zero, zero, 0x08))
    assembler.emit(mips.i_type(0x09, sp, sp, frame_size))
    payload, relocations = assembler.build()
    return Fragment(V2_CONTROLS_ADAPTER, payload, relocations)


def load_v2_session(
    assembler: mips.Assembler,
    address_register: int,
    pointer_register: int,
) -> None:
    assembler.load_symbol_word(
        address_register,
        pointer_register,
        0x23,
        V2_SESSION_POINTER,
    )


def begin_v2_hook(
    assembler: mips.Assembler,
    address_register: int,
    pointer_register: int,
) -> None:
    sp = 29
    assembler.emit(mips.i_type(0x09, sp, sp, -0x10))
    assembler.emit(mips.i_type(0x2B, sp, address_register, 0))
    assembler.emit(mips.i_type(0x2B, sp, pointer_register, 4))
    load_v2_session(assembler, address_register, pointer_register)


def finish_v2_hook(
    assembler: mips.Assembler,
    address_register: int,
    pointer_register: int,
    resume_address: int,
) -> None:
    sp = 29
    assembler.emit(mips.i_type(0x23, sp, address_register, 0))
    assembler.emit(mips.i_type(0x23, sp, pointer_register, 4))
    assembler.emit(mips.i_type(0x09, sp, sp, 0x10))
    assembler.emit(mips.jump(0x02, resume_address))
    assembler.emit(0)


def build_v2_plain_space() -> Fragment:
    zero, v0, v1, s3 = 0, 2, 3, 19
    assembler = mips.Assembler()
    begin_v2_hook(assembler, v0, v1)
    assembler.branch(0x04, v1, zero, "original")
    assembler.emit(mips.i_type(0x31, s3, 0, 4))
    assembler.emit(mips.cop1(0x00, 1, 0, 1))
    emit_load_float(assembler, v0, 2, -6.0)
    assembler.emit(mips.cop1(0x00, 1, 1, 2))
    assembler.emit(
        mips.i_type(0x31, v1, 2, V2_SESSION_SCALE_X)
    )
    assembler.emit(mips.cop1(0x02, 1, 1, 2))
    finish_v2_hook(
        assembler, v0, v1, V2_PLAIN_SPACE_RESUME
    )
    assembler.label("original")
    assembler.emit(mips.cop1(0x00, 1, 0, 1))
    finish_v2_hook(
        assembler, v0, v1, V2_PLAIN_SPACE_RESUME
    )
    payload, relocations = assembler.build()
    return Fragment(V2_PLAIN_SPACE, payload, relocations)


def build_v2_newline_advance() -> Fragment:
    zero, v0, v1, s3 = 0, 2, 3, 19
    assembler = mips.Assembler()
    begin_v2_hook(assembler, v0, v1)
    assembler.branch(0x04, v1, zero, "original")
    assembler.emit(mips.i_type(0x31, s3, 0, 0x40))
    assembler.emit(mips.cop1(0x00, 1, 1, 0))
    emit_load_float(assembler, v0, 0, -4.0)
    assembler.emit(mips.cop1(0x00, 1, 1, 0))
    assembler.emit(
        mips.i_type(0x31, v1, 2, V2_SESSION_SCALE_Y)
    )
    assembler.emit(mips.cop1(0x02, 1, 1, 2))
    assembler.emit(mips.i_type(0x31, s3, 0, 0x20))
    assembler.emit(mips.cop1(0x00, 0, 0, 1))
    assembler.emit(mips.i_type(0x39, s3, 0, 0x20))
    finish_v2_hook(
        assembler, v0, v1, NEWLINE_ADVANCE_RETURN
    )
    assembler.label("original")
    assembler.emit(mips.cop1(0x00, 1, 1, 0))
    finish_v2_hook(
        assembler, v0, v1, V2_NEWLINE_ORIGINAL_RESUME
    )
    payload, relocations = assembler.build()
    return Fragment(V2_NEWLINE_ADVANCE, payload, relocations)


def build_v2_right_edge() -> Fragment:
    zero, v0, v1, s1 = 0, 2, 3, 17
    assembler = mips.Assembler()
    begin_v2_hook(assembler, v0, v1)
    assembler.branch(0x04, v1, zero, "original")
    assembler.emit(mips.cop1(0x00, 21, 1, 0))
    assembler.emit(
        mips.i_type(0x31, v1, 2, V2_SESSION_SCALE_X)
    )
    assembler.emit(mips.cop1(0x02, 2, 1, 2))
    assembler.emit(mips.cop1(0x00, 21, 2, 0))
    assembler.emit(mips.i_type(0x31, s1, 0, 0x20))
    finish_v2_hook(
        assembler, v0, v1, V2_RIGHT_EDGE_RESUME
    )
    assembler.label("original")
    assembler.emit(mips.i_type(0x31, s1, 0, 0x20))
    finish_v2_hook(
        assembler, v0, v1, V2_RIGHT_EDGE_RESUME
    )
    payload, relocations = assembler.build()
    return Fragment(V2_RIGHT_EDGE, payload, relocations)


def build_v2_half_space() -> Fragment:
    zero, v0, v1, s3 = 0, 2, 3, 19
    assembler = mips.Assembler()
    begin_v2_hook(assembler, v0, v1)
    assembler.branch(0x04, v1, zero, "original")
    assembler.emit(0)
    assembler.emit(
        mips.i_type(0x31, v1, 4, V2_SESSION_SCALE_X)
    )
    assembler.emit(mips.cop1(0x02, 4, 3, 4))
    assembler.emit(mips.cop1(0x1C, 0, 2, 4))
    assembler.emit(mips.i_type(0x39, s3, 0, 0x1C))
    finish_v2_hook(
        assembler, v0, v1, V2_HALF_SPACE_RESUME
    )
    assembler.label("original")
    assembler.emit(mips.cop1(0x1C, 0, 2, 3))
    assembler.emit(mips.i_type(0x39, s3, 0, 0x1C))
    finish_v2_hook(
        assembler, v0, v1, V2_HALF_SPACE_RESUME
    )
    payload, relocations = assembler.build()
    return Fragment(V2_HALF_SPACE, payload, relocations)


def build_v2_glyph_advance() -> Fragment:
    zero, v0, v1, s3 = 0, 2, 3, 19
    assembler = mips.Assembler()
    begin_v2_hook(assembler, v0, v1)
    assembler.branch(0x04, v1, zero, "original")
    assembler.emit(mips.cop1(0x00, 1, 0, 2))
    assembler.emit(
        mips.i_type(0x31, v1, 3, V2_SESSION_SCALE_X)
    )
    assembler.emit(mips.cop1(0x02, 1, 1, 3))
    assembler.emit(mips.i_type(0x31, s3, 0, 0x1C))
    finish_v2_hook(
        assembler, v0, v1, V2_GLYPH_ADVANCE_RESUME
    )
    assembler.label("original")
    assembler.emit(mips.i_type(0x31, s3, 0, 0x1C))
    finish_v2_hook(
        assembler, v0, v1, V2_GLYPH_ADVANCE_RESUME
    )
    payload, relocations = assembler.build()
    return Fragment(V2_GLYPH_ADVANCE, payload, relocations)


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
    saved_command_width = 0x30
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
    assembler.branch(0x05, ra, t2, "check_command_title_or_character_body")
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
    assembler.branch(
        0x05,
        t2,
        t3,
        "check_command_title_or_character_body",
    )
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

    assembler.label("check_command_title_or_character_body")
    mips.load_u32(assembler, t2, CHARACTER_BODY_CALLER)
    assembler.branch(0x05, ra, t2, "call_original")
    assembler.emit(0)
    assembler.emit(mips.i_type(0x23, sp, t2, saved_outer_ra))
    mips.load_u32(assembler, t3, COMMAND_CHART_TITLE_OUTER)
    assembler.branch(0x04, t2, t3, "command_chart_title")
    assembler.emit(0)
    mips.load_u32(assembler, t3, PRACTICE_COMMAND_TITLE_OUTER)
    assembler.branch(0x04, t2, t3, "practice_command_title")
    assembler.emit(0)
    mips.load_u32(assembler, t3, CHARACTER_BODY_OUTER)
    assembler.branch(0x05, t2, t3, "call_original")
    assembler.emit(0)
    assembler.branch(0x04, zero, zero, "character_body")
    assembler.emit(0)

    assembler.label("command_chart_title")
    mips.load_u32(
        assembler,
        t2,
        float_bits(COMMAND_CHART_TITLE_BOX_X),
    )
    assembler.emit(mips.i_type(0x2B, a1, t2, 0))
    assembler.emit(mips.i_type(0x31, a1, 0, 4))
    emit_load_float(
        assembler,
        t3,
        1,
        abs(COMMAND_CHART_TITLE_Y_OFFSET),
    )
    assembler.emit(mips.cop1(0x01, 0, 0, 1))
    assembler.emit(mips.i_type(0x39, a1, 0, 4))
    mips.load_u32(assembler, t2, COMMAND_CHART_TITLE_BOX_WIDTH)
    assembler.emit(mips.i_type(0x2B, sp, t2, saved_command_width))
    assembler.branch(0x04, zero, zero, "command_title_fit")
    assembler.emit(0)

    assembler.label("practice_command_title")
    mips.load_u32(
        assembler,
        t2,
        float_bits(PRACTICE_COMMAND_TITLE_BOX_X),
    )
    assembler.emit(mips.i_type(0x2B, a1, t2, 0))
    assembler.emit(mips.i_type(0x31, a1, 0, 4))
    emit_load_float(
        assembler,
        t3,
        1,
        abs(PRACTICE_COMMAND_TITLE_Y_OFFSET),
    )
    assembler.emit(mips.cop1(0x01, 0, 0, 1))
    assembler.emit(mips.i_type(0x39, a1, 0, 4))
    mips.load_u32(assembler, t2, PRACTICE_COMMAND_TITLE_BOX_WIDTH)
    assembler.emit(mips.i_type(0x2B, sp, t2, saved_command_width))

    assembler.label("command_title_fit")
    assembler.emit(mips.i_type(0x09, zero, t2, 1))
    assembler.emit(mips.i_type(0x2B, sp, t2, scale_modified))
    emit_scale_one(assembler, t1, t2)
    assembler.emit(mips.i_type(0x23, sp, t1, saved_a1))
    assembler.emit(mips.i_type(0x23, t1, a0, 8))
    assembler.emit(mips.r_type(zero, zero, a1, 0x21))
    assembler.jump_symbol(0x03, MEASURE)
    assembler.emit(0)
    assembler.emit(mips.r_type(v0, zero, t3, 0x21))
    assembler.emit(mips.i_type(0x23, sp, t0, saved_command_width))
    assembler.emit(mips.r_type(t0, t3, t2, 0x2B))
    assembler.branch(0x04, t2, zero, "command_title_draw")
    assembler.emit(0)
    assembler.emit(mips.mtc1(t3, 0))
    assembler.emit(mips.cop1(0x20, 0, 0, fmt=20))
    assembler.emit(mips.mtc1(t0, 1))
    assembler.emit(mips.cop1(0x20, 1, 1, fmt=20))
    assembler.emit(mips.cop1(0x03, 2, 1, 0))
    assembler.emit(mips.i_type(0x0F, zero, t2, SCALE_ADDRESS >> 16))
    assembler.emit(
        mips.i_type(0x39, t2, 2, SCALE_ADDRESS & 0xFFFF)
    )

    assembler.label("command_title_draw")
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

    assembler.label("character_body")
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


def legacy_fragments() -> tuple[Fragment, ...]:
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
        build_measure(),
        build_controls_fit(),
        Fragment(SCALE_ADVANCE, SCALE_ADVANCE_BYTES),
        build_selected_helper(),
        Fragment(SELECTED_TRAMPOLINE, selected_trampoline),
        build_ui_helper(),
        Fragment(UI_TRAMPOLINE, ui_trampoline),
        Fragment(
            ASCII_WIDTHS,
            build_ascii_widths(),
            kind="rodata",
            alignment=1,
        ),
    )
    symbols = [fragment.symbol for fragment in result]
    if len(symbols) != len(set(symbols)):
        raise ValueError("generated resident fragments export duplicate symbols")
    return result


def v2_fragments() -> tuple[Fragment, ...]:
    result = (
        Fragment(
            V2_SESSION_POINTER,
            b"\0" * 4,
            kind="data",
            alignment=4,
        ),
        Fragment(
            V2_ASCII_WIDTHS,
            build_ascii_widths(),
            kind="rodata",
            alignment=1,
        ),
        build_v2_measure(),
        build_v2_prepare(),
        build_v2_adapter_call(),
        build_v2_controls_callback(),
        build_v2_controls_adapter(),
        build_v2_plain_space(),
        build_v2_newline_advance(),
        build_v2_right_edge(),
        build_v2_half_space(),
        build_v2_glyph_advance(),
    )
    symbols = [fragment.symbol for fragment in result]
    if len(symbols) != len(set(symbols)):
        raise ValueError("generated v2 fragments export duplicate symbols")
    return result


def fragments() -> tuple[Fragment, ...]:
    result = legacy_fragments() + v2_fragments()
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


def pack_blob(
    generated: tuple[Fragment, ...],
) -> tuple[bytes, dict[str, int]]:
    blob = bytearray()
    offsets: dict[str, int] = {}
    for fragment in generated:
        while len(blob) % 4:
            blob.append(0)
        offsets[fragment.symbol] = len(blob)
        blob.extend(fragment.payload)
    return bytes(blob), offsets


def make_fragment_rows(
    generated: tuple[Fragment, ...],
    blob_relative: Path,
    blob: bytes,
    offsets: dict[str, int],
) -> list[dict[str, object]]:
    blob_hash = hashlib.sha256(blob).hexdigest().upper()
    return [
        {
            "fragment_id": fragment.symbol,
            "kind": fragment.kind,
            "alignment": fragment.alignment,
            "blob_path": blob_relative.as_posix(),
            "blob_offset": f"0x{offsets[fragment.symbol]:X}",
            "length": len(fragment.payload),
            "blob_sha256": blob_hash,
            "init": int(fragment.init),
        }
        for fragment in generated
    ]


def relocation_rows(
    generated: tuple[Fragment, ...],
    id_prefix: str,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    relocation_index = 1
    for fragment in generated:
        for order, relocation in enumerate(fragment.relocations, 1):
            rows.append(
                {
                    "relocation_id": (
                        f"{id_prefix}{relocation_index:03d}"
                    ),
                    "fragment_id": fragment.symbol,
                    "order": order * 10,
                    "offset": f"0x{relocation.offset:X}",
                    "kind": relocation.kind,
                    "symbol": relocation.symbol,
                    "addend": relocation.addend,
                }
            )
            relocation_index += 1
    return rows


def generated_outputs() -> tuple[bytes, bytes, bytes, bytes]:
    legacy = legacy_fragments()
    v2 = v2_fragments()
    legacy_blob, legacy_offsets = pack_blob(legacy)
    v2_blob, v2_offsets = pack_blob(v2)
    fragment_rows = [
        *make_fragment_rows(
            legacy,
            LEGACY_BLOB_RELATIVE,
            legacy_blob,
            legacy_offsets,
        ),
        *make_fragment_rows(
            v2,
            V2_BLOB_RELATIVE,
            v2_blob,
            v2_offsets,
        ),
    ]
    generated_relocations = [
        *relocation_rows(legacy, "FR-R"),
        *relocation_rows(v2, "FR-V2-R"),
    ]
    return (
        legacy_blob,
        v2_blob,
        tsv_bytes(engine.FRAGMENT_FIELDS, fragment_rows),
        tsv_bytes(engine.RELOCATION_FIELDS, generated_relocations),
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
        (
            LEGACY_BLOB_OUTPUT,
            V2_BLOB_OUTPUT,
            FRAGMENTS_OUTPUT,
            RELOCATIONS_OUTPUT,
        ),
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
