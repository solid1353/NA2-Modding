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

from na2_patcher.modules.runtime_injector import engine  # noqa: E402
from na2_patcher.project_paths import load_project_paths  # noqa: E402
from scripts.research.localization import mips  # noqa: E402


MODULE = load_project_paths(REPOSITORY).path(
    "features", "localization", "runtime_injector"
)
LEGACY_BLOB_RELATIVE = Path("assets") / "font_renderer_resident.bin"
LEGACY_BLOB_OUTPUT = MODULE / LEGACY_BLOB_RELATIVE
V2_BLOB_RELATIVE = Path("assets") / "font_renderer_v2_resident.bin"
V2_BLOB_OUTPUT = MODULE / V2_BLOB_RELATIVE
NUMERIC_BLOB_RELATIVE = Path("assets") / "font_numeric_resident.bin"
NUMERIC_BLOB_OUTPUT = MODULE / NUMERIC_BLOB_RELATIVE
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
NINJA_SONG_ASCII_NUMBER = f"{PREFIX}.ninja_song_ascii_number"

V2_PREFIX = f"{PREFIX}.v2"
V2_SESSION_POINTER = f"{V2_PREFIX}.session_pointer"
V2_ASCII_WIDTHS = f"{V2_PREFIX}.ascii_widths"
V2_MEASURE = f"{V2_PREFIX}.measure"
V2_PREPARE = f"{V2_PREFIX}.prepare"
V2_ADAPTER_CALL = f"{V2_PREFIX}.adapter_call"
V2_CONTROLS_ADAPTER = f"{V2_PREFIX}.controls_adapter"
V2_CONTROLS_CALLBACK = f"{V2_PREFIX}.controls_callback"
V2_TITLE_ADAPTER = f"{V2_PREFIX}.title_adapter"
V2_TITLE_CALLBACK = f"{V2_PREFIX}.title_callback"
V2_COMMAND_TITLE_ENTRY = f"{V2_PREFIX}.command_title_entry"
V2_PRACTICE_TITLE_ENTRY = f"{V2_PREFIX}.practice_title_entry"
V2_PAUSE_LIST_CALLBACK = f"{V2_PREFIX}.pause_list_callback"
V2_PAUSE_LIST_ADAPTER = f"{V2_PREFIX}.pause_list_adapter"
V2_PAUSE_LIST_SELECTED_CALLBACK = (
    f"{V2_PREFIX}.pause_list_selected_callback"
)
V2_PAUSE_LIST_SELECTED_ADAPTER = (
    f"{V2_PREFIX}.pause_list_selected_adapter"
)
V2_QUIT_ACTIVE = f"{V2_PREFIX}.quit_active"
V2_QUIT_CHOICES_SCOPE = f"{V2_PREFIX}.quit_choices_scope"
V2_QUIT_SELECTED_ADAPTER = f"{V2_PREFIX}.quit_selected_adapter"
V2_QUIT_UNSELECTED_ADAPTER = f"{V2_PREFIX}.quit_unselected_adapter"
V2_QUIT_BODY_CALLBACK = f"{V2_PREFIX}.quit_body_callback"
V2_QUIT_BODY_ADAPTER = f"{V2_PREFIX}.quit_body_adapter"
V2_NATIVE_MEASURE = f"{V2_PREFIX}.native_measure"
V2_WRAP_NATIVE = f"{V2_PREFIX}.wrap_native"
V2_PRACTICE_TOKENS = f"{V2_PREFIX}.practice_tokens"
V2_PRACTICE_APPEND = f"{V2_PREFIX}.practice_append"
V2_PRACTICE_ICON_MAP = f"{V2_PREFIX}.practice_icon_map"
V2_PRACTICE_ICON_METRIC = f"{V2_PREFIX}.practice_icon_metric"
V2_PRACTICE_ICON_DRAW = f"{V2_PREFIX}.practice_icon_draw"
V2_PRACTICE_CALLBACK = f"{V2_PREFIX}.practice_callback"
V2_PRACTICE_ADAPTER = f"{V2_PREFIX}.practice_adapter"
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
FONT_BOX_DRAW = 0x00382310
FONT_PAUSE_LIST_DRAW = 0x00382470
FONT_PAUSE_LIST_SELECTED_DRAW = 0x003827A0
FONT_UI_DRAW = 0x00379A20
FONT_SELECTED_DRAW = 0x00379150
FONT_CHOICE_LIST_DRAW = 0x00383600
FONT_ICON_DRAW = 0x0037BB40
SPRINTF = 0x0017BCA0
FORMAT_D = 0x006042D3
PRACTICE_ICON_TABLE = 0x008D14C0
PRACTICE_EXPLANATION_TEXT_TABLE = 0x008BD510
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
SPECIAL_CONTROLS_ON_TEXT = 0x006059F0
SPECIAL_CONTROLS_OFF_TEXT = 0x006059F8
SPECIAL_CONTROLS_ON_TARGET = (66.0, 31.0)
SPECIAL_CONTROLS_OFF_TARGET = (59.0, 49.0)
PRACTICE_PAUSE_LIST_Y_OFFSET = -4.0
PRACTICE_PAUSE_LIST_SELECTED_X_OFFSET = 2.0
PRACTICE_PAUSE_LIST_BOX_WIDTH = 216
PRACTICE_PAUSE_LIST_BOX_HEIGHT = 20
PRACTICE_PAUSE_LIST_LINE_HEIGHT = 20.0
QUIT_BODY_BOX_X = 19.0
QUIT_BODY_BOX_Y = 12.0
QUIT_BODY_BOX_WIDTH = 420
QUIT_BODY_BOX_HEIGHT = 40
QUIT_BODY_LINE_HEIGHT = 20.0
QUIT_BODY_LINE_LIMIT = 2
QUIT_BODY_BUFFER = 0x80
QUIT_BODY_BUFFER_SIZE = 0x100
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
COMMAND_TITLE_MODE = 0
PRACTICE_TITLE_MODE = 1
TITLE_BOX_HEIGHT = 20
TITLE_LINE_HEIGHT = 20.0

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
V2_SESSION_GLYPH_HEIGHT = 0x68
V2_PAUSE_LIST_SELECTED_COLOR = V2_SESSION_SIZE

V2_PRACTICE_OBJECT_PRIMARY = 0x6C
V2_PRACTICE_OBJECT_SECONDARY = 0x70
V2_PRACTICE_SAVED_METRIC_CALLBACK = 0x74
V2_PRACTICE_SAVED_DRAW_CALLBACK = 0x78
V2_PRACTICE_BUFFER = 0x80
V2_PRACTICE_BUFFER_SIZE = 0x200

V2_FLAG_SHRINK_X = 0x01
V2_FLAG_BR_TAGS = 0x02
V2_FLAG_NEWLINE_BYTES = 0x04
V2_FLAG_SEPARATE_LINE_ADVANCE = 0x08
V2_FLAG_PREMEASURED = 0x10

CONTROLS_BOX_WIDTH = 128
CONTROLS_BOX_HEIGHT = 20
CONTROLS_LINE_HEIGHT = 20.0

PRACTICE_EXPLANATION_BOX_X = 39.2
PRACTICE_EXPLANATION_BOX_Y_OFFSET = 21.2
PRACTICE_EXPLANATION_BOX_WIDTH = 364
PRACTICE_EXPLANATION_BOX_HEIGHT = 48
PRACTICE_EXPLANATION_GLYPH_HEIGHT = 28.0
PRACTICE_EXPLANATION_LINE_ADVANCE = 14.0
PRACTICE_EXPLANATION_LINE_LIMIT = 0
PRACTICE_EXPLANATION_TOKEN_COUNT = 13
PRACTICE_EXPLANATION_TOKEN_STRIDE = 16

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
    assembler.emit(
        mips.i_type(0x0C, a1, t0, V2_FLAG_PREMEASURED)
    )
    assembler.branch(0x04, t0, zero, "measure")
    assembler.emit(0)
    assembler.emit(
        mips.i_type(0x23, s0, v0, V2_SESSION_MEASURED_WIDTH)
    )
    assembler.emit(mips.i_type(0x23, s0, v1, V2_SESSION_LINE_COUNT))
    assembler.branch(0x04, zero, zero, "measurement_ready")
    assembler.emit(0)

    assembler.label("measure")
    assembler.jump_symbol(0x03, V2_MEASURE)
    assembler.emit(0)
    assembler.branch(0x01, v0, zero, "error")
    assembler.emit(0)

    assembler.emit(
        mips.i_type(0x2B, s0, v0, V2_SESSION_MEASURED_WIDTH)
    )
    assembler.emit(mips.i_type(0x2B, s0, v1, V2_SESSION_LINE_COUNT))
    assembler.label("measurement_ready")
    assembler.branch(0x01, v0, zero, "error")
    assembler.emit(0)
    assembler.branch(0x04, v1, zero, "error")
    assembler.emit(0)
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
    assembler.emit(mips.i_type(0x23, s0, t2, V2_SESSION_FLAGS))
    assembler.emit(
        mips.i_type(
            0x0C,
            t2,
            t2,
            V2_FLAG_SEPARATE_LINE_ADVANCE,
        )
    )
    assembler.branch(0x04, t2, zero, "uniform_line_height")
    assembler.emit(mips.i_type(0x09, v1, t3, -1))
    assembler.emit(mips.mtc1(t3, 4))
    assembler.emit(mips.cop1(0x20, 4, 4, fmt=20))
    assembler.emit(
        mips.i_type(0x31, s0, 5, V2_SESSION_LINE_HEIGHT)
    )
    assembler.emit(mips.cop1(0x02, 4, 4, 5))
    assembler.emit(
        mips.i_type(0x31, s0, 5, V2_SESSION_GLYPH_HEIGHT)
    )
    assembler.emit(mips.cop1(0x00, 4, 4, 5))
    assembler.branch(0x04, zero, zero, "store_rendered_height")
    assembler.emit(0)

    assembler.label("uniform_line_height")
    assembler.emit(mips.mtc1(v1, 4))
    assembler.emit(mips.cop1(0x20, 4, 4, fmt=20))
    assembler.emit(
        mips.i_type(0x31, s0, 5, V2_SESSION_LINE_HEIGHT)
    )
    assembler.emit(mips.cop1(0x02, 4, 4, 5))
    assembler.label("store_rendered_height")
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
        CONTROLS_BOX_WIDTH / 2.0,
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


def build_v2_title_callback() -> Fragment:
    """Draw one prepared title through NA2's boxed UI entrypoint."""

    a3 = 7
    assembler = mips.Assembler()
    assembler.emit(
        mips.i_type(0x31, a3, 12, V2_SESSION_DRAW_X)
    )
    assembler.emit(
        mips.i_type(0x31, a3, 13, V2_SESSION_DRAW_Y)
    )
    assembler.emit(mips.jump(0x02, FONT_BOX_DRAW))
    assembler.emit(0)
    payload, relocations = assembler.build()
    return Fragment(V2_TITLE_CALLBACK, payload, relocations)


def build_v2_title_adapter() -> Fragment:
    """Fit one Command Chart or Practice title in its NUN5 box."""

    zero, a0, a1, a2, a3 = 0, 4, 5, 6, 7
    t0, t1 = 8, 9
    sp, ra = 29, 31
    frame_size = 0x80
    saved_ra = 0x7C

    assembler = mips.Assembler()
    assembler.emit(mips.i_type(0x09, sp, sp, -frame_size))
    assembler.emit(mips.i_type(0x2B, sp, ra, saved_ra))
    assembler.emit(mips.i_type(0x2B, sp, a1, V2_SESSION_TEXT))
    assembler.emit(
        mips.i_type(0x2B, sp, a0, V2_SESSION_CALLBACK_ARG0)
    )
    assembler.emit(
        mips.i_type(0x2B, sp, a1, V2_SESSION_CALLBACK_ARG1)
    )
    assembler.emit(
        mips.i_type(0x2B, sp, a2, V2_SESSION_CALLBACK_ARG2)
    )

    assembler.branch(0x04, a3, zero, "command_chart")
    assembler.emit(0)
    emit_load_float(
        assembler,
        t0,
        0,
        PRACTICE_COMMAND_TITLE_BOX_X,
    )
    assembler.emit(mips.i_type(0x39, sp, 0, V2_SESSION_BOX_X))
    emit_load_float(
        assembler,
        t0,
        0,
        PRACTICE_COMMAND_TITLE_Y_OFFSET,
    )
    assembler.emit(mips.cop1(0x00, 0, 13, 0))
    assembler.emit(mips.i_type(0x39, sp, 0, V2_SESSION_BOX_Y))
    mips.load_u32(
        assembler,
        t0,
        PRACTICE_COMMAND_TITLE_BOX_WIDTH,
    )
    assembler.branch(0x04, zero, zero, "configure")
    assembler.emit(0)

    assembler.label("command_chart")
    emit_load_float(
        assembler,
        t0,
        0,
        COMMAND_CHART_TITLE_BOX_X,
    )
    assembler.emit(mips.i_type(0x39, sp, 0, V2_SESSION_BOX_X))
    emit_load_float(
        assembler,
        t0,
        0,
        COMMAND_CHART_TITLE_Y_OFFSET,
    )
    assembler.emit(mips.cop1(0x00, 0, 13, 0))
    assembler.emit(mips.i_type(0x39, sp, 0, V2_SESSION_BOX_Y))
    mips.load_u32(
        assembler,
        t0,
        COMMAND_CHART_TITLE_BOX_WIDTH,
    )

    assembler.label("configure")
    assembler.emit(
        mips.i_type(0x2B, sp, t0, V2_SESSION_BOX_WIDTH)
    )
    mips.load_u32(assembler, t0, TITLE_BOX_HEIGHT)
    assembler.emit(
        mips.i_type(0x2B, sp, t0, V2_SESSION_BOX_HEIGHT)
    )
    assembler.emit(
        mips.i_type(
            0x2B,
            sp,
            zero,
            V2_SESSION_HORIZONTAL_ALIGNMENT,
        )
    )
    assembler.emit(
        mips.i_type(
            0x2B,
            sp,
            zero,
            V2_SESSION_VERTICAL_ALIGNMENT,
        )
    )
    assembler.emit(mips.i_type(0x09, zero, t0, V2_FLAG_SHRINK_X))
    assembler.emit(
        mips.i_type(0x2B, sp, t0, V2_SESSION_FLAGS)
    )
    assembler.emit(
        mips.i_type(0x2B, sp, t0, V2_SESSION_LINE_LIMIT)
    )
    emit_load_float(assembler, t0, 0, TITLE_LINE_HEIGHT)
    assembler.emit(
        mips.i_type(0x39, sp, 0, V2_SESSION_LINE_HEIGHT)
    )
    assembler.load_symbol_word(
        t0,
        t0,
        0x09,
        V2_TITLE_CALLBACK,
    )
    assembler.emit(
        mips.i_type(0x2B, sp, t0, V2_SESSION_CALLBACK)
    )
    assembler.emit(mips.r_type(sp, zero, t1, 0x21))
    assembler.emit(
        mips.i_type(0x2B, sp, t1, V2_SESSION_CALLBACK_ARG3)
    )

    assembler.emit(mips.r_type(sp, zero, a0, 0x21))
    assembler.jump_symbol(0x03, V2_ADAPTER_CALL)
    assembler.emit(0)
    assembler.emit(mips.i_type(0x23, sp, ra, saved_ra))
    assembler.emit(mips.r_type(ra, zero, zero, 0x08))
    assembler.emit(mips.i_type(0x09, sp, sp, frame_size))
    payload, relocations = assembler.build()
    return Fragment(V2_TITLE_ADAPTER, payload, relocations)


def build_v2_title_entry(symbol: str, mode: int) -> Fragment:
    """Tail-call the shared title adapter with one explicit geometry mode."""

    zero, a3 = 0, 7
    assembler = mips.Assembler()
    assembler.emit(mips.i_type(0x09, zero, a3, mode))
    assembler.jump_symbol(0x02, V2_TITLE_ADAPTER)
    assembler.emit(0)
    payload, relocations = assembler.build()
    return Fragment(symbol, payload, relocations)


def build_v2_pause_list_callback() -> Fragment:
    """Draw one prepared Pause Controls row through its native list helper."""

    a3 = 7
    assembler = mips.Assembler()
    assembler.emit(
        mips.i_type(0x31, a3, 12, V2_SESSION_DRAW_X)
    )
    assembler.emit(
        mips.i_type(0x31, a3, 13, V2_SESSION_DRAW_Y)
    )
    assembler.emit(mips.jump(0x02, FONT_PAUSE_LIST_DRAW))
    assembler.emit(0)
    payload, relocations = assembler.build()
    return Fragment(V2_PAUSE_LIST_CALLBACK, payload, relocations)


def build_v2_pause_list_adapter() -> Fragment:
    """Fit one Pause Controls row in NUN5's 216-unit list box."""

    zero, a0, a1, a2 = 0, 4, 5, 6
    t0, t1 = 8, 9
    sp, ra = 29, 31
    frame_size = 0x80
    saved_ra = 0x7C

    assembler = mips.Assembler()
    assembler.emit(mips.i_type(0x09, sp, sp, -frame_size))
    assembler.emit(mips.i_type(0x2B, sp, ra, saved_ra))
    assembler.emit(mips.i_type(0x2B, sp, a1, V2_SESSION_TEXT))
    assembler.emit(
        mips.i_type(0x2B, sp, a0, V2_SESSION_CALLBACK_ARG0)
    )
    assembler.emit(
        mips.i_type(0x2B, sp, a1, V2_SESSION_CALLBACK_ARG1)
    )
    assembler.emit(
        mips.i_type(0x2B, sp, a2, V2_SESSION_CALLBACK_ARG2)
    )

    assembler.emit(mips.i_type(0x39, sp, 12, V2_SESSION_BOX_X))
    emit_load_float(
        assembler,
        t0,
        0,
        abs(PRACTICE_PAUSE_LIST_Y_OFFSET),
    )
    assembler.emit(mips.cop1(0x01, 0, 13, 0))
    assembler.emit(mips.i_type(0x39, sp, 0, V2_SESSION_BOX_Y))
    mips.load_u32(assembler, t0, PRACTICE_PAUSE_LIST_BOX_WIDTH)
    assembler.emit(
        mips.i_type(0x2B, sp, t0, V2_SESSION_BOX_WIDTH)
    )
    mips.load_u32(assembler, t0, PRACTICE_PAUSE_LIST_BOX_HEIGHT)
    assembler.emit(
        mips.i_type(0x2B, sp, t0, V2_SESSION_BOX_HEIGHT)
    )
    assembler.emit(
        mips.i_type(
            0x2B,
            sp,
            zero,
            V2_SESSION_HORIZONTAL_ALIGNMENT,
        )
    )
    assembler.emit(
        mips.i_type(
            0x2B,
            sp,
            zero,
            V2_SESSION_VERTICAL_ALIGNMENT,
        )
    )
    assembler.emit(mips.i_type(0x09, zero, t0, V2_FLAG_SHRINK_X))
    assembler.emit(mips.i_type(0x2B, sp, t0, V2_SESSION_FLAGS))
    assembler.emit(
        mips.i_type(0x2B, sp, t0, V2_SESSION_LINE_LIMIT)
    )
    emit_load_float(
        assembler,
        t0,
        0,
        PRACTICE_PAUSE_LIST_LINE_HEIGHT,
    )
    assembler.emit(
        mips.i_type(0x39, sp, 0, V2_SESSION_LINE_HEIGHT)
    )
    assembler.load_symbol_word(
        t0,
        t0,
        0x09,
        V2_PAUSE_LIST_CALLBACK,
    )
    assembler.emit(
        mips.i_type(0x2B, sp, t0, V2_SESSION_CALLBACK)
    )
    assembler.emit(mips.r_type(sp, zero, t1, 0x21))
    assembler.emit(
        mips.i_type(0x2B, sp, t1, V2_SESSION_CALLBACK_ARG3)
    )

    assembler.emit(mips.r_type(sp, zero, a0, 0x21))
    assembler.jump_symbol(0x03, V2_ADAPTER_CALL)
    assembler.emit(0)
    assembler.emit(mips.i_type(0x23, sp, ra, saved_ra))
    assembler.emit(mips.r_type(ra, zero, zero, 0x08))
    assembler.emit(mips.i_type(0x09, sp, sp, frame_size))
    payload, relocations = assembler.build()
    return Fragment(V2_PAUSE_LIST_ADAPTER, payload, relocations)


def build_v2_pause_list_selected_callback() -> Fragment:
    """Draw one prepared selected Pause Controls row through its native helper."""

    a1, a2, a3, t0 = 5, 6, 7, 8
    assembler = mips.Assembler()
    assembler.emit(
        mips.i_type(0x31, a3, 0, V2_SESSION_DRAW_X)
    )
    assembler.emit(mips.cop1(0x24, 0, 0))
    assembler.emit(mips.mfc1(a1, 0))
    assembler.emit(
        mips.i_type(0x31, a3, 1, V2_SESSION_DRAW_Y)
    )
    assembler.emit(mips.cop1(0x24, 1, 1))
    assembler.emit(mips.mfc1(a2, 1))
    assembler.emit(
        mips.i_type(0x23, a3, t0, V2_PAUSE_LIST_SELECTED_COLOR)
    )
    assembler.emit(mips.i_type(0x23, a3, a3, V2_SESSION_TEXT))
    assembler.emit(mips.jump(0x02, FONT_PAUSE_LIST_SELECTED_DRAW))
    assembler.emit(0)
    payload, relocations = assembler.build()
    return Fragment(
        V2_PAUSE_LIST_SELECTED_CALLBACK,
        payload,
        relocations,
    )


def build_v2_pause_list_selected_adapter() -> Fragment:
    """Fit a selected Pause Controls row without changing its visual origin."""

    zero, a0, a1, a2, a3 = 0, 4, 5, 6, 7
    t0, t1 = 8, 9
    sp, ra = 29, 31
    frame_size = 0x80
    saved_ra = 0x7C

    assembler = mips.Assembler()
    assembler.emit(mips.i_type(0x09, sp, sp, -frame_size))
    assembler.emit(mips.i_type(0x2B, sp, ra, saved_ra))
    assembler.emit(mips.i_type(0x2B, sp, a3, V2_SESSION_TEXT))
    assembler.emit(
        mips.i_type(0x2B, sp, a0, V2_SESSION_CALLBACK_ARG0)
    )
    assembler.emit(
        mips.i_type(0x2B, sp, a1, V2_SESSION_CALLBACK_ARG1)
    )
    assembler.emit(
        mips.i_type(0x2B, sp, a2, V2_SESSION_CALLBACK_ARG2)
    )
    assembler.emit(
        mips.i_type(0x2B, sp, t0, V2_PAUSE_LIST_SELECTED_COLOR)
    )

    assembler.emit(mips.mtc1(a1, 0))
    assembler.emit(mips.cop1(0x20, 0, 0, fmt=20))
    emit_load_float(
        assembler,
        t0,
        1,
        PRACTICE_PAUSE_LIST_SELECTED_X_OFFSET,
    )
    assembler.emit(mips.cop1(0x00, 0, 0, 1))
    assembler.emit(mips.i_type(0x39, sp, 0, V2_SESSION_BOX_X))

    assembler.emit(mips.mtc1(a2, 0))
    assembler.emit(mips.cop1(0x20, 0, 0, fmt=20))
    emit_load_float(
        assembler,
        t0,
        1,
        abs(PRACTICE_PAUSE_LIST_Y_OFFSET),
    )
    assembler.emit(mips.cop1(0x01, 0, 0, 1))
    assembler.emit(mips.i_type(0x39, sp, 0, V2_SESSION_BOX_Y))

    mips.load_u32(assembler, t0, PRACTICE_PAUSE_LIST_BOX_WIDTH)
    assembler.emit(
        mips.i_type(0x2B, sp, t0, V2_SESSION_BOX_WIDTH)
    )
    mips.load_u32(assembler, t0, PRACTICE_PAUSE_LIST_BOX_HEIGHT)
    assembler.emit(
        mips.i_type(0x2B, sp, t0, V2_SESSION_BOX_HEIGHT)
    )
    assembler.emit(
        mips.i_type(
            0x2B,
            sp,
            zero,
            V2_SESSION_HORIZONTAL_ALIGNMENT,
        )
    )
    assembler.emit(
        mips.i_type(
            0x2B,
            sp,
            zero,
            V2_SESSION_VERTICAL_ALIGNMENT,
        )
    )
    assembler.emit(mips.i_type(0x09, zero, t0, V2_FLAG_SHRINK_X))
    assembler.emit(mips.i_type(0x2B, sp, t0, V2_SESSION_FLAGS))
    assembler.emit(
        mips.i_type(0x2B, sp, t0, V2_SESSION_LINE_LIMIT)
    )
    emit_load_float(
        assembler,
        t0,
        0,
        PRACTICE_PAUSE_LIST_LINE_HEIGHT,
    )
    assembler.emit(
        mips.i_type(0x39, sp, 0, V2_SESSION_LINE_HEIGHT)
    )
    assembler.load_symbol_word(
        t0,
        t0,
        0x09,
        V2_PAUSE_LIST_SELECTED_CALLBACK,
    )
    assembler.emit(
        mips.i_type(0x2B, sp, t0, V2_SESSION_CALLBACK)
    )
    assembler.emit(mips.r_type(sp, zero, t1, 0x21))
    assembler.emit(
        mips.i_type(0x2B, sp, t1, V2_SESSION_CALLBACK_ARG3)
    )

    assembler.emit(mips.r_type(sp, zero, a0, 0x21))
    assembler.jump_symbol(0x03, V2_ADAPTER_CALL)
    assembler.emit(0)
    assembler.emit(mips.i_type(0x23, sp, ra, saved_ra))
    assembler.emit(mips.r_type(ra, zero, zero, 0x08))
    assembler.emit(mips.i_type(0x09, sp, sp, frame_size))
    payload, relocations = assembler.build()
    return Fragment(
        V2_PAUSE_LIST_SELECTED_ADAPTER,
        payload,
        relocations,
    )


def build_v2_quit_choices_scope() -> Fragment:
    """Publish ss4 scope only while its native Yes/No list is drawing."""

    zero, a0 = 0, 4
    t0 = 8
    s0 = 16
    sp, ra = 29, 31
    frame_size = 0x20
    saved_active = 0x10
    saved_s0 = 0x18
    saved_ra = 0x1C

    assembler = mips.Assembler()
    assembler.emit(mips.i_type(0x09, sp, sp, -frame_size))
    assembler.emit(mips.i_type(0x2B, sp, ra, saved_ra))
    assembler.emit(mips.i_type(0x2B, sp, s0, saved_s0))
    assembler.load_symbol_word(t0, s0, 0x09, V2_QUIT_ACTIVE)
    assembler.emit(mips.i_type(0x23, s0, t0, 0))
    assembler.emit(mips.i_type(0x2B, sp, t0, saved_active))
    assembler.emit(mips.i_type(0x09, zero, t0, 1))
    assembler.emit(mips.i_type(0x2B, s0, t0, 0))
    assembler.emit(mips.jump(0x03, FONT_CHOICE_LIST_DRAW))
    assembler.emit(0)
    assembler.emit(mips.i_type(0x23, sp, t0, saved_active))
    assembler.emit(mips.i_type(0x2B, s0, t0, 0))
    assembler.emit(mips.i_type(0x23, sp, s0, saved_s0))
    assembler.emit(mips.i_type(0x23, sp, ra, saved_ra))
    assembler.emit(mips.r_type(ra, zero, zero, 0x08))
    assembler.emit(mips.i_type(0x09, sp, sp, frame_size))
    payload, relocations = assembler.build()
    return Fragment(V2_QUIT_CHOICES_SCOPE, payload, relocations)


def build_v2_quit_selected_adapter() -> Fragment:
    """Map scoped ss4 or exact ss1 selected rows to NUN5 coordinates."""

    zero, a0 = 0, 4
    t0, t1 = 8, 9
    assembler = mips.Assembler()
    assembler.load_symbol_word(t0, t0, 0x23, V2_QUIT_ACTIVE)
    assembler.branch(0x05, t0, zero, "quit_scope")
    assembler.emit(0)
    mips.load_u32(assembler, t0, SPECIAL_CONTROLS_ON_TEXT)
    assembler.branch(0x05, a0, t0, "original")
    assembler.emit(0)
    emit_load_float(
        assembler, t0, 12, SPECIAL_CONTROLS_ON_TARGET[0]
    )
    emit_load_float(
        assembler, t0, 13, SPECIAL_CONTROLS_ON_TARGET[1]
    )
    assembler.branch(0x04, zero, zero, "original")
    assembler.emit(0)

    assembler.label("quit_scope")
    assembler.emit(mips.mfc1(t1, 13))
    mips.load_u32(assembler, t0, float_bits(YES_SOURCE[1]))
    assembler.branch(0x04, t1, t0, "map_yes")
    assembler.emit(0)
    mips.load_u32(assembler, t0, float_bits(NO_SOURCE[1]))
    assembler.branch(0x04, t1, t0, "map_no")
    assembler.emit(0)
    assembler.branch(0x04, zero, zero, "original")
    assembler.emit(0)

    assembler.label("map_yes")
    emit_load_float(assembler, t0, 12, YES_TARGET[0])
    emit_load_float(assembler, t0, 13, YES_TARGET[1])
    assembler.branch(0x04, zero, zero, "original")
    assembler.emit(0)

    assembler.label("map_no")
    emit_load_float(assembler, t0, 12, NO_TARGET[0])
    emit_load_float(assembler, t0, 13, NO_TARGET[1])

    assembler.label("original")
    assembler.emit(mips.jump(0x02, FONT_SELECTED_DRAW))
    assembler.emit(0)
    payload, relocations = assembler.build()
    return Fragment(V2_QUIT_SELECTED_ADAPTER, payload, relocations)


def build_v2_quit_unselected_adapter() -> Fragment:
    """Temporarily map scoped ss4 or exact ss1 rows, then restore them."""

    zero, a1 = 0, 5
    t0, t1 = 8, 9
    s0 = 16
    sp, ra = 29, 31
    frame_size = 0x30
    saved_x = 0x10
    saved_y = 0x14
    saved_s0 = 0x28
    saved_ra = 0x2C

    assembler = mips.Assembler()
    assembler.load_symbol_word(t0, t0, 0x23, V2_QUIT_ACTIVE)
    assembler.branch(0x05, t0, zero, "quit_scope")
    assembler.emit(0)
    assembler.emit(mips.i_type(0x23, a1, t1, 8))
    mips.load_u32(assembler, t0, SPECIAL_CONTROLS_OFF_TEXT)
    assembler.branch(0x05, t1, t0, "original")
    assembler.emit(0)
    mips.load_u32(
        assembler, t0, float_bits(SPECIAL_CONTROLS_OFF_TARGET[0])
    )
    mips.load_u32(
        assembler, t1, float_bits(SPECIAL_CONTROLS_OFF_TARGET[1])
    )
    assembler.branch(0x04, zero, zero, "mapped")
    assembler.emit(0)

    assembler.label("quit_scope")
    assembler.emit(mips.i_type(0x23, a1, t1, 4))
    mips.load_u32(assembler, t0, float_bits(YES_SOURCE[1]))
    assembler.branch(0x04, t1, t0, "map_yes")
    assembler.emit(0)
    mips.load_u32(assembler, t0, float_bits(NO_SOURCE[1]))
    assembler.branch(0x04, t1, t0, "map_no")
    assembler.emit(0)
    assembler.branch(0x04, zero, zero, "original")
    assembler.emit(0)

    assembler.label("map_yes")
    mips.load_u32(assembler, t0, float_bits(YES_TARGET[0]))
    mips.load_u32(assembler, t1, float_bits(YES_TARGET[1]))
    assembler.branch(0x04, zero, zero, "mapped")
    assembler.emit(0)

    assembler.label("map_no")
    mips.load_u32(assembler, t0, float_bits(NO_TARGET[0]))
    mips.load_u32(assembler, t1, float_bits(NO_TARGET[1]))

    assembler.label("mapped")
    assembler.emit(mips.i_type(0x09, sp, sp, -frame_size))
    assembler.emit(mips.i_type(0x2B, sp, ra, saved_ra))
    assembler.emit(mips.i_type(0x2B, sp, s0, saved_s0))
    assembler.emit(mips.r_type(a1, zero, s0, 0x21))
    assembler.emit(mips.i_type(0x23, s0, a1, 0))
    assembler.emit(mips.i_type(0x2B, sp, a1, saved_x))
    assembler.emit(mips.i_type(0x23, s0, a1, 4))
    assembler.emit(mips.i_type(0x2B, sp, a1, saved_y))
    assembler.emit(mips.i_type(0x2B, s0, t0, 0))
    assembler.emit(mips.i_type(0x2B, s0, t1, 4))
    assembler.emit(mips.r_type(s0, zero, a1, 0x21))
    assembler.emit(mips.jump(0x03, FONT_UI_DRAW))
    assembler.emit(0)
    assembler.emit(mips.i_type(0x23, sp, t0, saved_x))
    assembler.emit(mips.i_type(0x2B, s0, t0, 0))
    assembler.emit(mips.i_type(0x23, sp, t0, saved_y))
    assembler.emit(mips.i_type(0x2B, s0, t0, 4))
    assembler.emit(mips.i_type(0x23, sp, s0, saved_s0))
    assembler.emit(mips.i_type(0x23, sp, ra, saved_ra))
    assembler.emit(mips.r_type(ra, zero, zero, 0x08))
    assembler.emit(mips.i_type(0x09, sp, sp, frame_size))

    assembler.label("original")
    assembler.emit(mips.jump(0x02, FONT_UI_DRAW))
    assembler.emit(0)
    payload, relocations = assembler.build()
    return Fragment(V2_QUIT_UNSELECTED_ADAPTER, payload, relocations)


def build_v2_quit_body_callback() -> Fragment:
    """Draw the wrapped ss4 body with its NUN5-local record coordinates."""

    zero, a0, a1, a2, a3 = 0, 4, 5, 6, 7
    t0 = 8
    sp, ra = 29, 31
    frame_size = 0x30
    saved_ra = 0x2C

    assembler = mips.Assembler()
    assembler.emit(mips.i_type(0x09, sp, sp, -frame_size))
    assembler.emit(mips.i_type(0x2B, sp, ra, saved_ra))
    mips.load_u32(assembler, t0, float_bits(QUIT_BODY_BOX_X))
    assembler.emit(mips.i_type(0x2B, sp, t0, 0))
    mips.load_u32(assembler, t0, float_bits(QUIT_BODY_BOX_Y))
    assembler.emit(mips.i_type(0x2B, sp, t0, 4))
    assembler.emit(mips.i_type(0x2B, sp, a1, 8))
    assembler.emit(mips.i_type(0x2B, sp, a2, 12))
    assembler.emit(mips.i_type(0x24, a0, t0, 0x62))
    assembler.branch(0x04, t0, zero, "return")
    assembler.emit(mips.i_type(0x23, a0, a2, 0x74))
    assembler.emit(mips.i_type(0x23, a0, a0, 0x78))
    assembler.emit(mips.i_type(0x09, sp, a1, 0))
    assembler.emit(mips.i_type(0x09, zero, a3, -1))
    assembler.emit(mips.jump(0x03, FONT_UI_DRAW))
    assembler.emit(0)

    assembler.label("return")
    assembler.emit(mips.i_type(0x23, sp, ra, saved_ra))
    assembler.emit(mips.r_type(ra, zero, zero, 0x08))
    assembler.emit(mips.i_type(0x09, sp, sp, frame_size))
    payload, relocations = assembler.build()
    return Fragment(V2_QUIT_BODY_CALLBACK, payload, relocations)


def build_v2_quit_body_adapter() -> Fragment:
    """Copy and greedily wrap the ss4 body only for its exact draw call."""

    zero, v0, v1, a0, a1, a2 = 0, 2, 3, 4, 5, 6
    t0, t1 = 8, 9
    s0, s1, s2, s3, s4 = 16, 17, 18, 19, 20
    sp, ra = 29, 31
    frame_size = 0x1C0
    saved_s4 = 0x1A8
    saved_s3 = 0x1AC
    saved_s2 = 0x1B0
    saved_s1 = 0x1B4
    saved_s0 = 0x1B8
    saved_ra = 0x1BC

    assembler = mips.Assembler()
    assembler.emit(mips.i_type(0x09, sp, sp, -frame_size))
    assembler.emit(mips.i_type(0x2B, sp, ra, saved_ra))
    assembler.emit(mips.i_type(0x2B, sp, s0, saved_s0))
    assembler.emit(mips.i_type(0x2B, sp, s1, saved_s1))
    assembler.emit(mips.i_type(0x2B, sp, s2, saved_s2))
    assembler.emit(mips.i_type(0x2B, sp, s3, saved_s3))
    assembler.emit(mips.i_type(0x2B, sp, s4, saved_s4))
    assembler.emit(mips.r_type(a0, zero, s0, 0x21))
    assembler.emit(mips.r_type(a1, zero, s1, 0x21))
    assembler.emit(mips.r_type(a2, zero, s2, 0x21))
    assembler.emit(mips.i_type(0x09, sp, s3, QUIT_BODY_BUFFER))
    assembler.emit(mips.r_type(s3, zero, s4, 0x21))
    assembler.emit(
        mips.i_type(0x09, zero, t0, QUIT_BODY_BUFFER_SIZE - 1)
    )

    assembler.label("copy")
    assembler.emit(mips.i_type(0x24, s1, t1, 0))
    assembler.emit(mips.i_type(0x28, s4, t1, 0))
    assembler.branch(0x04, t1, zero, "copied")
    assembler.emit(0)
    assembler.emit(mips.i_type(0x09, s1, s1, 1))
    assembler.emit(mips.i_type(0x09, s4, s4, 1))
    assembler.emit(mips.i_type(0x09, t0, t0, -1))
    assembler.branch(0x05, t0, zero, "copy")
    assembler.emit(0)
    assembler.emit(mips.i_type(0x28, s4, zero, 0))

    assembler.label("copied")
    assembler.emit(mips.r_type(s3, zero, a0, 0x21))
    assembler.emit(
        mips.i_type(0x09, zero, a1, QUIT_BODY_BOX_WIDTH)
    )
    assembler.emit(
        mips.i_type(0x09, zero, a2, QUIT_BODY_LINE_LIMIT)
    )
    assembler.jump_symbol(0x03, V2_WRAP_NATIVE)
    assembler.emit(0)
    assembler.emit(
        mips.i_type(0x2B, sp, v0, V2_SESSION_MEASURED_WIDTH)
    )
    assembler.emit(
        mips.i_type(0x2B, sp, v1, V2_SESSION_LINE_COUNT)
    )
    assembler.emit(mips.i_type(0x2B, sp, s3, V2_SESSION_TEXT))
    mips.load_u32(assembler, t0, float_bits(QUIT_BODY_BOX_X))
    assembler.emit(mips.i_type(0x2B, sp, t0, V2_SESSION_BOX_X))
    mips.load_u32(assembler, t0, float_bits(QUIT_BODY_BOX_Y))
    assembler.emit(mips.i_type(0x2B, sp, t0, V2_SESSION_BOX_Y))
    mips.load_u32(assembler, t0, QUIT_BODY_BOX_WIDTH)
    assembler.emit(mips.i_type(0x2B, sp, t0, V2_SESSION_BOX_WIDTH))
    mips.load_u32(assembler, t0, QUIT_BODY_BOX_HEIGHT)
    assembler.emit(mips.i_type(0x2B, sp, t0, V2_SESSION_BOX_HEIGHT))
    assembler.emit(
        mips.i_type(
            0x2B, sp, zero, V2_SESSION_HORIZONTAL_ALIGNMENT
        )
    )
    assembler.emit(
        mips.i_type(0x2B, sp, zero, V2_SESSION_VERTICAL_ALIGNMENT)
    )
    assembler.emit(
        mips.i_type(
            0x09,
            zero,
            t0,
            V2_FLAG_NEWLINE_BYTES | V2_FLAG_PREMEASURED,
        )
    )
    assembler.emit(mips.i_type(0x2B, sp, t0, V2_SESSION_FLAGS))
    assembler.emit(
        mips.i_type(
            0x09, zero, t0, QUIT_BODY_LINE_LIMIT
        )
    )
    assembler.emit(mips.i_type(0x2B, sp, t0, V2_SESSION_LINE_LIMIT))
    emit_load_float(
        assembler, t0, 0, QUIT_BODY_LINE_HEIGHT
    )
    assembler.emit(mips.i_type(0x39, sp, 0, V2_SESSION_LINE_HEIGHT))
    assembler.load_symbol_word(
        t0, t0, 0x09, V2_QUIT_BODY_CALLBACK
    )
    assembler.emit(mips.i_type(0x2B, sp, t0, V2_SESSION_CALLBACK))
    assembler.emit(
        mips.i_type(0x2B, sp, s0, V2_SESSION_CALLBACK_ARG0)
    )
    assembler.emit(
        mips.i_type(0x2B, sp, s3, V2_SESSION_CALLBACK_ARG1)
    )
    assembler.emit(
        mips.i_type(0x2B, sp, s2, V2_SESSION_CALLBACK_ARG2)
    )
    assembler.emit(
        mips.r_type(sp, zero, t0, 0x21)
    )
    assembler.emit(
        mips.i_type(0x2B, sp, t0, V2_SESSION_CALLBACK_ARG3)
    )
    assembler.emit(mips.r_type(sp, zero, a0, 0x21))
    assembler.jump_symbol(0x03, V2_ADAPTER_CALL)
    assembler.emit(0)

    assembler.emit(mips.i_type(0x23, sp, s4, saved_s4))
    assembler.emit(mips.i_type(0x23, sp, s3, saved_s3))
    assembler.emit(mips.i_type(0x23, sp, s2, saved_s2))
    assembler.emit(mips.i_type(0x23, sp, s1, saved_s1))
    assembler.emit(mips.i_type(0x23, sp, s0, saved_s0))
    assembler.emit(mips.i_type(0x23, sp, ra, saved_ra))
    assembler.emit(mips.r_type(ra, zero, zero, 0x08))
    assembler.emit(mips.i_type(0x09, sp, sp, frame_size))
    payload, relocations = assembler.build()
    return Fragment(V2_QUIT_BODY_ADAPTER, payload, relocations)


def build_v2_native_measure() -> Fragment:
    """Measure tagged native text with the shared NUN5 space correction."""

    zero, v0, a0 = 0, 2, 4
    t0, t1, t2 = 8, 9, 10
    s0, s1 = 16, 17
    sp, ra = 29, 31
    frame_size = 0x20
    saved_s0 = 0x10
    saved_s1 = 0x14
    saved_ra = 0x1C

    assembler = mips.Assembler()
    assembler.emit(mips.i_type(0x09, sp, sp, -frame_size))
    assembler.emit(mips.i_type(0x2B, sp, ra, saved_ra))
    assembler.emit(mips.i_type(0x2B, sp, s0, saved_s0))
    assembler.emit(mips.i_type(0x2B, sp, s1, saved_s1))
    assembler.emit(mips.r_type(a0, zero, s0, 0x21))
    assembler.emit(mips.jump(0x03, FONT_MEASURE))
    assembler.emit(mips.r_type(zero, zero, 5, 0x21))
    assembler.emit(mips.r_type(v0, zero, s1, 0x21))
    assembler.emit(mips.r_type(s0, zero, t0, 0x21))

    assembler.label("scan")
    assembler.emit(mips.i_type(0x24, t0, t1, 0))
    assembler.branch(0x04, t1, zero, "return")
    assembler.emit(mips.i_type(0x09, t0, t0, 1))
    assembler.emit(mips.i_type(0x09, zero, t2, ASCII_FIRST))
    assembler.branch(0x05, t1, t2, "scan")
    assembler.emit(0)
    assembler.emit(
        mips.i_type(0x09, s1, s1, -NUN5_SPACE_CORRECTION)
    )
    assembler.branch(0x04, zero, zero, "scan")
    assembler.emit(0)

    assembler.label("return")
    assembler.emit(mips.r_type(s1, zero, v0, 0x21))
    assembler.emit(mips.i_type(0x23, sp, s1, saved_s1))
    assembler.emit(mips.i_type(0x23, sp, s0, saved_s0))
    assembler.emit(mips.i_type(0x23, sp, ra, saved_ra))
    assembler.emit(mips.r_type(ra, zero, zero, 0x08))
    assembler.emit(mips.i_type(0x09, sp, sp, frame_size))
    payload, relocations = assembler.build()
    return Fragment(V2_NATIVE_MEASURE, payload, relocations)


def build_v2_wrap_native() -> Fragment:
    """Greedily wrap one mutable tagged string and return max width/lines."""

    zero, v0, v1, a0, a1, a2 = 0, 2, 3, 4, 5, 6
    t0, t1, t2, t3 = 8, 9, 10, 11
    s0, s1, s2, s3 = 16, 17, 18, 19
    s4, s5, s6, s7 = 20, 21, 22, 23
    sp, ra = 29, 31
    frame_size = 0x60
    saved_registers = (
        (s0, 0x00),
        (s1, 0x04),
        (s2, 0x08),
        (s3, 0x0C),
        (s4, 0x10),
        (s5, 0x14),
        (s6, 0x18),
        (s7, 0x1C),
    )
    saved_manager = 0x40
    saved_tracking = 0x44
    saved_ra = 0x5C

    assembler = mips.Assembler()
    assembler.emit(mips.i_type(0x09, sp, sp, -frame_size))
    assembler.emit(mips.i_type(0x2B, sp, ra, saved_ra))
    for register, offset in saved_registers:
        assembler.emit(mips.i_type(0x2B, sp, register, offset))
    assembler.emit(mips.r_type(a0, zero, s0, 0x21))
    assembler.emit(mips.r_type(a1, zero, s1, 0x21))
    assembler.emit(mips.r_type(a2, zero, s2, 0x21))

    mips.load_u32(assembler, t0, FONT_RENDERER_POINTER)
    assembler.emit(mips.i_type(0x23, t0, t0, 0))
    assembler.emit(mips.i_type(0x2B, sp, t0, saved_manager))
    assembler.branch(0x04, t0, zero, "tracking_ready")
    assembler.emit(0)
    assembler.emit(mips.i_type(0x23, t0, t1, 0x3C))
    assembler.emit(mips.i_type(0x2B, sp, t1, saved_tracking))
    assembler.emit(mips.i_type(0x2B, t0, zero, 0x3C))
    assembler.label("tracking_ready")

    assembler.emit(mips.r_type(s0, zero, s3, 0x21))
    assembler.emit(mips.r_type(s0, zero, s4, 0x21))
    assembler.emit(mips.r_type(zero, zero, s5, 0x21))
    assembler.emit(mips.i_type(0x09, zero, s6, 1))

    assembler.label("wrap_scan")
    assembler.emit(mips.i_type(0x24, s3, t0, 0))
    assembler.branch(0x04, t0, zero, "wrap_end")
    assembler.emit(mips.i_type(0x09, zero, t1, 0x0A))
    assembler.branch(0x04, t0, t1, "existing_newline")
    assembler.emit(mips.i_type(0x09, zero, t1, ASCII_FIRST))
    assembler.branch(0x05, t0, t1, "wrap_next")
    assembler.emit(0)

    assembler.emit(mips.i_type(0x28, s3, zero, 0))
    assembler.emit(mips.r_type(s4, zero, a0, 0x21))
    assembler.jump_symbol(0x03, V2_NATIVE_MEASURE)
    assembler.emit(0)
    assembler.emit(mips.i_type(0x09, zero, t0, ASCII_FIRST))
    assembler.emit(mips.i_type(0x28, s3, t0, 0))
    assembler.emit(mips.r_type(s1, v0, t1, 0x2B))
    assembler.branch(0x04, t1, zero, "space_candidate")
    assembler.emit(0)
    assembler.branch(0x04, s2, zero, "line_room")
    assembler.emit(0)
    assembler.emit(mips.r_type(s6, s2, t1, 0x2B))
    assembler.branch(0x04, t1, zero, "space_candidate")
    assembler.emit(0)
    assembler.label("line_room")
    assembler.branch(0x04, s5, zero, "use_current_space")
    assembler.emit(0)
    assembler.emit(mips.r_type(s5, zero, t2, 0x21))
    assembler.branch(0x04, zero, zero, "wrap_at_space")
    assembler.emit(0)
    assembler.label("use_current_space")
    assembler.emit(mips.r_type(s3, zero, t2, 0x21))
    assembler.label("wrap_at_space")
    assembler.emit(mips.i_type(0x09, zero, t0, 0x0A))
    assembler.emit(mips.i_type(0x28, t2, t0, 0))
    assembler.emit(mips.i_type(0x09, t2, s4, 1))
    assembler.emit(mips.i_type(0x09, s6, s6, 1))

    assembler.label("space_candidate")
    assembler.emit(mips.r_type(s3, zero, s5, 0x21))
    assembler.branch(0x04, zero, zero, "wrap_next")
    assembler.emit(0)

    assembler.label("existing_newline")
    assembler.emit(mips.i_type(0x09, s3, s4, 1))
    assembler.emit(mips.r_type(zero, zero, s5, 0x21))
    assembler.emit(mips.i_type(0x09, s6, s6, 1))

    assembler.label("wrap_next")
    assembler.emit(mips.i_type(0x09, s3, s3, 1))
    assembler.branch(0x04, zero, zero, "wrap_scan")
    assembler.emit(0)

    assembler.label("wrap_end")
    assembler.emit(mips.r_type(s4, zero, a0, 0x21))
    assembler.jump_symbol(0x03, V2_NATIVE_MEASURE)
    assembler.emit(0)
    assembler.emit(mips.r_type(s1, v0, t0, 0x2B))
    assembler.branch(0x04, t0, zero, "measure_lines")
    assembler.emit(0)
    assembler.branch(0x04, s5, zero, "measure_lines")
    assembler.emit(0)
    assembler.branch(0x04, s2, zero, "final_line_room")
    assembler.emit(0)
    assembler.emit(mips.r_type(s6, s2, t0, 0x2B))
    assembler.branch(0x04, t0, zero, "measure_lines")
    assembler.emit(0)
    assembler.label("final_line_room")
    assembler.emit(mips.i_type(0x09, zero, t0, 0x0A))
    assembler.emit(mips.i_type(0x28, s5, t0, 0))
    assembler.emit(mips.i_type(0x09, s6, s6, 1))

    assembler.label("measure_lines")
    assembler.emit(mips.r_type(s6, zero, s2, 0x21))
    assembler.emit(mips.r_type(s0, zero, s3, 0x21))
    assembler.emit(mips.r_type(s0, zero, s4, 0x21))
    assembler.emit(mips.r_type(zero, zero, s7, 0x21))

    assembler.label("measure_scan")
    assembler.emit(mips.i_type(0x24, s3, t0, 0))
    assembler.branch(0x04, t0, zero, "measure_segment")
    assembler.emit(mips.i_type(0x09, zero, t1, 0x0A))
    assembler.branch(0x04, t0, t1, "measure_segment")
    assembler.emit(0)
    assembler.emit(mips.i_type(0x09, s3, s3, 1))
    assembler.branch(0x04, zero, zero, "measure_scan")
    assembler.emit(0)

    assembler.label("measure_segment")
    assembler.emit(mips.r_type(t0, zero, s5, 0x21))
    assembler.emit(mips.i_type(0x28, s3, zero, 0))
    assembler.emit(mips.r_type(s4, zero, a0, 0x21))
    assembler.jump_symbol(0x03, V2_NATIVE_MEASURE)
    assembler.emit(0)
    assembler.emit(mips.r_type(s7, v0, t3, 0x2B))
    assembler.branch(0x04, t3, zero, "max_ready")
    assembler.emit(0)
    assembler.emit(mips.r_type(v0, zero, s7, 0x21))
    assembler.label("max_ready")
    assembler.branch(0x04, s5, zero, "finish")
    assembler.emit(0)
    assembler.emit(mips.i_type(0x09, zero, t0, 0x0A))
    assembler.emit(mips.i_type(0x28, s3, t0, 0))
    assembler.emit(mips.i_type(0x09, s3, s3, 1))
    assembler.emit(mips.r_type(s3, zero, s4, 0x21))
    assembler.branch(0x04, zero, zero, "measure_scan")
    assembler.emit(0)

    assembler.label("finish")
    assembler.emit(mips.i_type(0x23, sp, t0, saved_manager))
    assembler.branch(0x04, t0, zero, "return")
    assembler.emit(0)
    assembler.emit(mips.i_type(0x23, sp, t1, saved_tracking))
    assembler.emit(mips.i_type(0x2B, t0, t1, 0x3C))

    assembler.label("return")
    assembler.emit(mips.r_type(s7, zero, v0, 0x21))
    assembler.emit(mips.r_type(s2, zero, v1, 0x21))
    for register, offset in saved_registers:
        assembler.emit(mips.i_type(0x23, sp, register, offset))
    assembler.emit(mips.i_type(0x23, sp, ra, saved_ra))
    assembler.emit(mips.r_type(ra, zero, zero, 0x08))
    assembler.emit(mips.i_type(0x09, sp, sp, frame_size))
    payload, relocations = assembler.build()
    return Fragment(V2_WRAP_NATIVE, payload, relocations)


def build_v2_practice_tokens() -> bytes:
    tokens = (
        "<iconUP>",
        "<iconDOWN>",
        "<iconRIGHT>",
        "<iconLEFT>",
        "<iconCIRCLE>",
        "<iconTRIANGLE>",
        "<iconSQUARE>",
        "<iconCROSS>",
        "<iconETC0>",
        "<iconL1>",
        "<iconR1>",
        "<iconL2>",
        "<iconR2>",
    )
    if len(tokens) != PRACTICE_EXPLANATION_TOKEN_COUNT:
        raise ValueError("Practice token table has the wrong entry count")
    result = bytearray()
    for token in tokens:
        encoded = token.encode("ascii") + b"\0"
        if len(encoded) > PRACTICE_EXPLANATION_TOKEN_STRIDE:
            raise ValueError(f"Practice token is too long: {token}")
        result.extend(
            encoded.ljust(PRACTICE_EXPLANATION_TOKEN_STRIDE, b"\0")
        )
    result.extend(b" \0")
    return bytes(result)


def build_v2_practice_icon_map() -> bytes:
    return bytes(
        (
            5,
            4,
            7,
            6,
            9,
            11,
            10,
            12,
            0xFF,
            0xFF,
            0xFF,
            0,
            1,
            3,
            2,
            0xFF,
            0xFF,
            8,
        )
    )


def build_v2_practice_append() -> Fragment:
    zero, v0, a0, a1, a2 = 0, 2, 4, 5, 6
    t0, t1 = 8, 9
    ra = 31

    assembler = mips.Assembler()
    assembler.label("copy")
    assembler.emit(mips.i_type(0x24, a1, t0, 0))
    assembler.branch(0x04, t0, zero, "finish")
    assembler.emit(0)
    assembler.emit(mips.r_type(a0, a2, t1, 0x2B))
    assembler.branch(0x04, t1, zero, "finish")
    assembler.emit(0)
    assembler.emit(mips.i_type(0x28, a0, t0, 0))
    assembler.emit(mips.i_type(0x09, a1, a1, 1))
    assembler.emit(mips.i_type(0x09, a0, a0, 1))
    assembler.branch(0x04, zero, zero, "copy")
    assembler.emit(0)
    assembler.label("finish")
    assembler.emit(mips.i_type(0x28, a0, zero, 0))
    assembler.emit(mips.r_type(a0, zero, v0, 0x21))
    assembler.emit(mips.r_type(ra, zero, zero, 0x08))
    assembler.emit(0)
    payload, relocations = assembler.build()
    return Fragment(V2_PRACTICE_APPEND, payload, relocations)


def build_v2_practice_icon_metric() -> Fragment:
    zero, a0, a1, a2 = 0, 4, 5, 6
    t0, t1, t2 = 8, 9, 10
    ra = 31

    assembler = mips.Assembler()
    assembler.emit(
        mips.i_type(0x0B, a2, t0, PRACTICE_EXPLANATION_TOKEN_COUNT + 5)
    )
    assembler.branch(0x04, t0, zero, "return")
    assembler.emit(0)
    assembler.load_symbol_word(t0, t0, 0x09, V2_PRACTICE_ICON_MAP)
    assembler.emit(mips.r_type(t0, a2, t0, 0x21))
    assembler.emit(mips.i_type(0x24, t0, t0, 0))
    assembler.emit(mips.i_type(0x09, zero, t1, 0xFF))
    assembler.branch(0x04, t0, t1, "return")
    assembler.emit(mips.r_type(zero, t0, t0, 0x00, shift=3))
    mips.load_u32(assembler, t1, PRACTICE_ICON_TABLE)
    assembler.emit(mips.r_type(t1, t0, t1, 0x21))
    assembler.emit(mips.i_type(0x21, t1, t2, 4))
    assembler.emit(mips.mtc1(t2, 0))
    assembler.emit(mips.cop1(0x20, 0, 0, fmt=20))
    assembler.emit(mips.i_type(0x39, a0, 0, 0))
    assembler.emit(mips.i_type(0x21, t1, t2, 6))
    assembler.emit(mips.mtc1(t2, 0))
    assembler.emit(mips.cop1(0x20, 0, 0, fmt=20))
    assembler.emit(mips.i_type(0x39, a1, 0, 0))
    assembler.label("return")
    assembler.emit(mips.r_type(ra, zero, zero, 0x08))
    assembler.emit(0)
    payload, relocations = assembler.build()
    return Fragment(V2_PRACTICE_ICON_METRIC, payload, relocations)


def build_v2_practice_icon_draw() -> Fragment:
    zero, a0, a1, a2 = 0, 4, 5, 6
    t0, t1, t2, t3 = 8, 9, 10, 11
    s0, s1, s2, s3 = 16, 17, 18, 19
    sp, ra = 29, 31
    frame_size = 0x50
    saved_registers = (
        (s0, 0x00),
        (s1, 0x04),
        (s2, 0x08),
        (s3, 0x0C),
    )
    saved_ra = 0x4C

    assembler = mips.Assembler()
    assembler.emit(mips.i_type(0x09, sp, sp, -frame_size))
    assembler.emit(mips.i_type(0x2B, sp, ra, saved_ra))
    for register, offset in saved_registers:
        assembler.emit(mips.i_type(0x2B, sp, register, offset))
    assembler.emit(mips.r_type(a0, zero, s0, 0x21))
    assembler.emit(mips.r_type(a1, zero, s1, 0x21))
    assembler.emit(mips.r_type(a2, zero, s2, 0x21))
    assembler.emit(mips.i_type(0x0B, s2, t0, 18))
    assembler.branch(0x04, t0, zero, "restore")
    assembler.emit(0)
    assembler.load_symbol_word(t0, t0, 0x09, V2_PRACTICE_ICON_MAP)
    assembler.emit(mips.r_type(t0, s2, t0, 0x21))
    assembler.emit(mips.i_type(0x24, t0, t0, 0))
    assembler.emit(mips.i_type(0x09, zero, t1, 0xFF))
    assembler.branch(0x04, t0, t1, "restore")
    assembler.emit(mips.r_type(zero, t0, t0, 0x00, shift=3))
    mips.load_u32(assembler, t1, PRACTICE_ICON_TABLE)
    assembler.emit(mips.r_type(t1, t0, s3, 0x21))

    assembler.load_symbol_word(
        t0,
        t0,
        0x23,
        V2_SESSION_POINTER,
    )
    assembler.branch(0x04, t0, zero, "restore")
    assembler.emit(0)
    assembler.emit(
        mips.i_type(0x23, t0, a0, V2_PRACTICE_OBJECT_PRIMARY)
    )
    assembler.emit(mips.i_type(0x0B, s2, t1, 4))
    assembler.branch(0x05, t1, zero, "object_ready")
    assembler.emit(0)
    assembler.emit(mips.i_type(0x0B, s2, t1, 8))
    assembler.branch(0x04, t1, zero, "object_ready")
    assembler.emit(0)
    assembler.emit(
        mips.i_type(0x23, t0, a0, V2_PRACTICE_OBJECT_SECONDARY)
    )
    assembler.label("object_ready")
    assembler.emit(mips.r_type(s3, zero, a1, 0x21))
    assembler.emit(mips.i_type(0x31, s0, 12, 0))
    assembler.emit(mips.i_type(0x31, s1, 13, 0))
    assembler.emit(mips.i_type(0x0B, s2, t1, 11))
    assembler.branch(0x05, t1, zero, "check_direction_end")
    assembler.emit(0)
    assembler.emit(mips.i_type(0x0B, s2, t1, 15))
    assembler.branch(0x04, t1, zero, "check_etc")
    emit_load_float(assembler, t2, 0, -3.0)
    assembler.emit(mips.cop1(0x00, 13, 13, 0))
    assembler.branch(0x04, zero, zero, "draw")
    assembler.emit(0)
    assembler.label("check_direction_end")
    assembler.label("check_etc")
    assembler.emit(mips.i_type(0x09, zero, t1, 17))
    assembler.branch(0x05, s2, t1, "draw")
    assembler.emit(0)
    emit_load_float(assembler, t2, 0, 1.0)
    assembler.emit(mips.cop1(0x00, 13, 13, 0))

    assembler.label("draw")
    assembler.emit(mips.jump(0x03, FONT_ICON_DRAW))
    assembler.emit(0)
    assembler.emit(mips.i_type(0x21, s3, t0, 4))
    assembler.emit(mips.mtc1(t0, 0))
    assembler.emit(mips.cop1(0x20, 0, 0, fmt=20))
    assembler.emit(mips.i_type(0x31, s0, 1, 0))
    assembler.emit(mips.cop1(0x00, 1, 1, 0))
    assembler.emit(mips.i_type(0x39, s0, 1, 0))

    assembler.label("restore")
    for register, offset in saved_registers:
        assembler.emit(mips.i_type(0x23, sp, register, offset))
    assembler.emit(mips.i_type(0x23, sp, ra, saved_ra))
    assembler.emit(mips.r_type(ra, zero, zero, 0x08))
    assembler.emit(mips.i_type(0x09, sp, sp, frame_size))
    payload, relocations = assembler.build()
    return Fragment(V2_PRACTICE_ICON_DRAW, payload, relocations)


def build_v2_practice_callback() -> Fragment:
    a3 = 7
    assembler = mips.Assembler()
    assembler.emit(
        mips.i_type(0x31, a3, 12, V2_SESSION_DRAW_X)
    )
    assembler.emit(
        mips.i_type(0x31, a3, 13, V2_SESSION_DRAW_Y)
    )
    assembler.emit(mips.jump(0x02, FONT_BOX_DRAW))
    assembler.emit(0)
    payload, relocations = assembler.build()
    return Fragment(V2_PRACTICE_CALLBACK, payload, relocations)


def build_v2_practice_adapter() -> Fragment:
    zero, v0, v1, a0, a1, a2 = 0, 2, 3, 4, 5, 6
    t0, t1, t2, t3 = 8, 9, 10, 11
    s0, s1, s2, s3 = 16, 17, 18, 19
    s4, s5, s6, s7 = 20, 21, 22, 23
    sp, ra = 29, 31
    frame_size = 0x300
    saved_registers = (
        (s0, 0x2C0),
        (s1, 0x2C4),
        (s2, 0x2C8),
        (s3, 0x2CC),
        (s4, 0x2D0),
        (s5, 0x2D4),
        (s6, 0x2D8),
        (s7, 0x2DC),
    )
    saved_y = 0x2E0
    saved_ra = 0x2FC
    buffer_limit = V2_PRACTICE_BUFFER_SIZE - 1
    space_offset = (
        PRACTICE_EXPLANATION_TOKEN_COUNT
        * PRACTICE_EXPLANATION_TOKEN_STRIDE
    )

    assembler = mips.Assembler()

    def emit_append() -> None:
        assembler.emit(mips.r_type(s4, zero, a0, 0x21))
        assembler.emit(mips.i_type(0x09, s3, a2, buffer_limit))
        assembler.jump_symbol(0x03, V2_PRACTICE_APPEND)
        assembler.emit(0)
        assembler.emit(mips.r_type(v0, zero, s4, 0x21))

    def emit_append_space() -> None:
        assembler.load_symbol_word(
            a1,
            a1,
            0x09,
            V2_PRACTICE_TOKENS,
            addend=space_offset,
        )
        emit_append()

    assembler.emit(mips.i_type(0x09, sp, sp, -frame_size))
    assembler.emit(mips.i_type(0x2B, sp, ra, saved_ra))
    for register, offset in saved_registers:
        assembler.emit(mips.i_type(0x2B, sp, register, offset))
    assembler.emit(mips.i_type(0x39, sp, 12, saved_y))
    assembler.emit(
        mips.i_type(0x2B, sp, s3, V2_PRACTICE_OBJECT_PRIMARY)
    )
    assembler.emit(
        mips.i_type(0x2B, sp, s2, V2_PRACTICE_OBJECT_SECONDARY)
    )
    assembler.emit(mips.r_type(a0, zero, s0, 0x21))
    assembler.emit(mips.r_type(a1, zero, s1, 0x21))
    assembler.emit(mips.r_type(a2, zero, s2, 0x21))
    assembler.emit(mips.i_type(0x09, sp, s3, V2_PRACTICE_BUFFER))
    assembler.emit(mips.r_type(s3, zero, s4, 0x21))
    assembler.emit(mips.i_type(0x28, s4, zero, 0))
    assembler.emit(mips.r_type(zero, zero, s5, 0x21))
    assembler.emit(mips.r_type(zero, zero, s6, 0x21))
    assembler.emit(mips.r_type(s0, s1, t0, 0x21))
    assembler.emit(mips.i_type(0x23, t0, s7, 0x68))

    assembler.label("token_loop")
    assembler.emit(mips.r_type(s5, s7, t0, 0x2A))
    assembler.branch(0x04, t0, zero, "install_callbacks")
    assembler.emit(0)
    assembler.emit(mips.r_type(zero, s5, t0, 0x00, shift=2))
    assembler.emit(mips.r_type(s0, s1, t1, 0x21))
    assembler.emit(mips.i_type(0x09, t1, t1, 0x40))
    assembler.emit(mips.r_type(t1, t0, t1, 0x21))
    assembler.emit(mips.i_type(0x23, t1, t2, 0))
    assembler.branch(0x01, t2, zero, "token_next")
    assembler.emit(0)
    assembler.emit(mips.i_type(0x0A, t2, t3, 26))
    assembler.branch(0x04, t3, zero, "token_next")
    assembler.emit(0)
    assembler.emit(
        mips.i_type(
            0x0A,
            t2,
            t3,
            PRACTICE_EXPLANATION_TOKEN_COUNT,
        )
    )
    assembler.branch(0x05, t3, zero, "icon_token")
    assembler.emit(0)

    assembler.branch(0x04, s5, zero, "text_payload")
    assembler.emit(0)
    emit_append_space()
    assembler.label("text_payload")
    assembler.emit(
        mips.i_type(
            0x09,
            t2,
            t2,
            -PRACTICE_EXPLANATION_TOKEN_COUNT,
        )
    )
    assembler.emit(mips.r_type(zero, t2, t2, 0x00, shift=2))
    mips.load_u32(assembler, t0, PRACTICE_EXPLANATION_TEXT_TABLE)
    assembler.emit(mips.r_type(t0, t2, t0, 0x21))
    assembler.emit(mips.i_type(0x23, t0, a1, 0))
    emit_append()
    assembler.emit(mips.i_type(0x09, zero, s6, 1))
    assembler.branch(0x04, zero, zero, "token_next")
    assembler.emit(0)

    assembler.label("icon_token")
    assembler.branch(0x04, s5, zero, "icon_payload")
    assembler.emit(0)
    assembler.branch(0x04, s6, zero, "icon_payload")
    assembler.emit(0)
    emit_append_space()
    assembler.label("icon_payload")
    assembler.load_symbol_word(
        t0,
        t0,
        0x09,
        V2_PRACTICE_TOKENS,
    )
    assembler.emit(mips.r_type(zero, t2, t1, 0x00, shift=4))
    assembler.emit(mips.r_type(t0, t1, a1, 0x21))
    emit_append()
    assembler.emit(mips.r_type(zero, zero, s6, 0x21))

    assembler.label("token_next")
    assembler.emit(mips.i_type(0x09, s5, s5, 1))
    assembler.branch(0x04, zero, zero, "token_loop")
    assembler.emit(0)

    assembler.label("install_callbacks")
    mips.load_u32(assembler, t0, FONT_RENDERER_POINTER)
    assembler.emit(mips.i_type(0x23, t0, t0, 0))
    assembler.branch(0x04, t0, zero, "restore")
    assembler.emit(0)
    assembler.emit(mips.i_type(0x23, t0, t1, 0x7C))
    assembler.emit(
        mips.i_type(
            0x2B,
            sp,
            t1,
            V2_PRACTICE_SAVED_METRIC_CALLBACK,
        )
    )
    assembler.emit(mips.i_type(0x23, t0, t1, 0x78))
    assembler.emit(
        mips.i_type(
            0x2B,
            sp,
            t1,
            V2_PRACTICE_SAVED_DRAW_CALLBACK,
        )
    )
    assembler.load_symbol_word(
        t1,
        t1,
        0x09,
        V2_PRACTICE_ICON_METRIC,
    )
    assembler.emit(mips.i_type(0x2B, t0, t1, 0x7C))
    assembler.load_symbol_word(
        t1,
        t1,
        0x09,
        V2_PRACTICE_ICON_DRAW,
    )
    assembler.emit(mips.i_type(0x2B, t0, t1, 0x78))

    assembler.emit(mips.r_type(s3, zero, a0, 0x21))
    mips.load_u32(assembler, a1, PRACTICE_EXPLANATION_BOX_WIDTH)
    mips.load_u32(assembler, a2, PRACTICE_EXPLANATION_LINE_LIMIT)
    assembler.jump_symbol(0x03, V2_WRAP_NATIVE)
    assembler.emit(0)
    assembler.emit(
        mips.i_type(0x2B, sp, v0, V2_SESSION_MEASURED_WIDTH)
    )
    assembler.emit(
        mips.i_type(0x2B, sp, v1, V2_SESSION_LINE_COUNT)
    )

    assembler.emit(mips.i_type(0x2B, sp, s3, V2_SESSION_TEXT))
    emit_load_float(
        assembler,
        t0,
        0,
        PRACTICE_EXPLANATION_BOX_X,
    )
    assembler.emit(mips.i_type(0x39, sp, 0, V2_SESSION_BOX_X))
    assembler.emit(mips.i_type(0x31, sp, 0, saved_y))
    emit_load_float(
        assembler,
        t0,
        1,
        PRACTICE_EXPLANATION_BOX_Y_OFFSET,
    )
    assembler.emit(mips.cop1(0x00, 0, 0, 1))
    assembler.emit(mips.i_type(0x39, sp, 0, V2_SESSION_BOX_Y))
    mips.load_u32(assembler, t0, PRACTICE_EXPLANATION_BOX_WIDTH)
    assembler.emit(
        mips.i_type(0x2B, sp, t0, V2_SESSION_BOX_WIDTH)
    )
    mips.load_u32(assembler, t0, PRACTICE_EXPLANATION_BOX_HEIGHT)
    assembler.emit(
        mips.i_type(0x2B, sp, t0, V2_SESSION_BOX_HEIGHT)
    )
    assembler.emit(
        mips.i_type(
            0x2B,
            sp,
            zero,
            V2_SESSION_HORIZONTAL_ALIGNMENT,
        )
    )
    assembler.emit(mips.i_type(0x09, zero, t0, 1))
    assembler.emit(
        mips.i_type(
            0x2B,
            sp,
            t0,
            V2_SESSION_VERTICAL_ALIGNMENT,
        )
    )
    mips.load_u32(
        assembler,
        t0,
        V2_FLAG_SHRINK_X
        | V2_FLAG_NEWLINE_BYTES
        | V2_FLAG_SEPARATE_LINE_ADVANCE
        | V2_FLAG_PREMEASURED,
    )
    assembler.emit(mips.i_type(0x2B, sp, t0, V2_SESSION_FLAGS))
    mips.load_u32(assembler, t0, PRACTICE_EXPLANATION_LINE_LIMIT)
    assembler.emit(
        mips.i_type(0x2B, sp, t0, V2_SESSION_LINE_LIMIT)
    )
    emit_load_float(
        assembler,
        t0,
        0,
        PRACTICE_EXPLANATION_LINE_ADVANCE,
    )
    assembler.emit(
        mips.i_type(0x39, sp, 0, V2_SESSION_LINE_HEIGHT)
    )
    emit_load_float(
        assembler,
        t0,
        0,
        PRACTICE_EXPLANATION_GLYPH_HEIGHT,
    )
    assembler.emit(
        mips.i_type(0x39, sp, 0, V2_SESSION_GLYPH_HEIGHT)
    )
    assembler.load_symbol_word(
        t0,
        t0,
        0x09,
        V2_PRACTICE_CALLBACK,
    )
    assembler.emit(
        mips.i_type(0x2B, sp, t0, V2_SESSION_CALLBACK)
    )
    assembler.emit(
        mips.i_type(0x2B, sp, s2, V2_SESSION_CALLBACK_ARG0)
    )
    assembler.emit(
        mips.i_type(0x2B, sp, s3, V2_SESSION_CALLBACK_ARG1)
    )
    assembler.emit(mips.i_type(0x09, zero, t0, 0x0F))
    assembler.emit(
        mips.i_type(0x2B, sp, t0, V2_SESSION_CALLBACK_ARG2)
    )
    assembler.emit(mips.r_type(sp, zero, t0, 0x21))
    assembler.emit(
        mips.i_type(0x2B, sp, t0, V2_SESSION_CALLBACK_ARG3)
    )
    assembler.emit(mips.r_type(sp, zero, a0, 0x21))
    assembler.jump_symbol(0x03, V2_ADAPTER_CALL)
    assembler.emit(0)

    mips.load_u32(assembler, t0, FONT_RENDERER_POINTER)
    assembler.emit(mips.i_type(0x23, t0, t0, 0))
    assembler.branch(0x04, t0, zero, "restore")
    assembler.emit(0)
    assembler.emit(
        mips.i_type(
            0x23,
            sp,
            t1,
            V2_PRACTICE_SAVED_METRIC_CALLBACK,
        )
    )
    assembler.emit(mips.i_type(0x2B, t0, t1, 0x7C))
    assembler.emit(
        mips.i_type(
            0x23,
            sp,
            t1,
            V2_PRACTICE_SAVED_DRAW_CALLBACK,
        )
    )
    assembler.emit(mips.i_type(0x2B, t0, t1, 0x78))

    assembler.label("restore")
    for register, offset in saved_registers:
        assembler.emit(mips.i_type(0x23, sp, register, offset))
    assembler.emit(mips.i_type(0x23, sp, ra, saved_ra))
    assembler.emit(mips.r_type(ra, zero, zero, 0x08))
    assembler.emit(mips.i_type(0x09, sp, sp, frame_size))
    payload, relocations = assembler.build()
    return Fragment(V2_PRACTICE_ADAPTER, payload, relocations)


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


def build_ninja_song_ascii_number() -> Fragment:
    """Reproduce NUN5's ASCII decimal padding behind NA2's formatter ABI."""

    zero, v0, a0, a1, a2, a3 = 0, 2, 4, 5, 6, 7
    t0, t1, t2 = 8, 9, 10
    s0, s1, s2, s3 = 16, 17, 18, 19
    sp, ra = 29, 31
    frame_size = 0x50
    temporary = 0x00
    saved_s0 = 0x30
    saved_s1 = 0x34
    saved_s2 = 0x38
    saved_s3 = 0x3C
    saved_ra = 0x4C

    assembler = mips.Assembler()
    assembler.emit(mips.i_type(0x09, sp, sp, -frame_size))
    assembler.emit(mips.i_type(0x2B, sp, ra, saved_ra))
    assembler.emit(mips.i_type(0x2B, sp, s0, saved_s0))
    assembler.emit(mips.i_type(0x2B, sp, s1, saved_s1))
    assembler.emit(mips.i_type(0x2B, sp, s2, saved_s2))
    assembler.emit(mips.i_type(0x2B, sp, s3, saved_s3))
    assembler.emit(mips.r_type(a3, zero, s0, 0x21))
    assembler.emit(mips.r_type(a2, zero, s1, 0x21))
    assembler.emit(mips.r_type(t0, zero, s2, 0x21))
    assembler.emit(mips.r_type(a1, zero, s3, 0x21))

    assembler.emit(mips.i_type(0x09, sp, a0, temporary))
    mips.load_u32(assembler, a1, FORMAT_D)
    assembler.emit(mips.r_type(s3, zero, a2, 0x21))
    assembler.emit(mips.jump(0x03, SPRINTF))
    assembler.emit(0)

    assembler.emit(mips.r_type(zero, zero, t0, 0x21))
    assembler.emit(mips.i_type(0x09, zero, t1, 0x20))
    assembler.emit(mips.i_type(0x09, zero, t2, 1))
    assembler.branch(0x04, s2, t2, "copy")
    assembler.emit(0)
    assembler.emit(mips.r_type(s1, v0, t0, 0x23))
    assembler.branch(0x06, t0, zero, "copy")
    assembler.emit(mips.i_type(0x09, zero, t2, 2))
    assembler.branch(0x05, s2, t2, "pad")
    assembler.emit(0)
    assembler.emit(mips.i_type(0x09, zero, t1, 0x30))

    assembler.label("pad")
    assembler.emit(mips.i_type(0x28, s0, t1, 0))
    assembler.emit(mips.i_type(0x09, s0, s0, 1))
    assembler.emit(mips.i_type(0x09, t0, t0, -1))
    assembler.branch(0x07, t0, zero, "pad")
    assembler.emit(0)

    assembler.label("copy")
    assembler.emit(mips.r_type(sp, zero, t0, 0x21))
    assembler.label("copy_next")
    assembler.emit(mips.i_type(0x24, t0, t1, 0))
    assembler.emit(mips.i_type(0x28, s0, t1, 0))
    assembler.branch(0x04, t1, zero, "restore")
    assembler.emit(mips.i_type(0x09, t0, t0, 1))
    assembler.emit(mips.i_type(0x09, s0, s0, 1))
    assembler.branch(0x04, zero, zero, "copy_next")
    assembler.emit(0)

    assembler.label("restore")
    assembler.emit(mips.i_type(0x23, sp, s3, saved_s3))
    assembler.emit(mips.i_type(0x23, sp, s2, saved_s2))
    assembler.emit(mips.i_type(0x23, sp, s1, saved_s1))
    assembler.emit(mips.i_type(0x23, sp, s0, saved_s0))
    assembler.emit(mips.i_type(0x23, sp, ra, saved_ra))
    assembler.emit(mips.r_type(ra, zero, zero, 0x08))
    assembler.emit(mips.i_type(0x09, sp, sp, frame_size))
    payload, relocations = assembler.build()
    return Fragment(NINJA_SONG_ASCII_NUMBER, payload, relocations)


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
            V2_QUIT_ACTIVE,
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
        Fragment(
            V2_PRACTICE_TOKENS,
            build_v2_practice_tokens(),
            kind="rodata",
            alignment=1,
        ),
        Fragment(
            V2_PRACTICE_ICON_MAP,
            build_v2_practice_icon_map(),
            kind="rodata",
            alignment=1,
        ),
        build_v2_measure(),
        build_v2_prepare(),
        build_v2_adapter_call(),
        build_v2_controls_callback(),
        build_v2_controls_adapter(),
        build_v2_title_callback(),
        build_v2_title_adapter(),
        build_v2_title_entry(
            V2_COMMAND_TITLE_ENTRY,
            COMMAND_TITLE_MODE,
        ),
        build_v2_title_entry(
            V2_PRACTICE_TITLE_ENTRY,
            PRACTICE_TITLE_MODE,
        ),
        build_v2_pause_list_callback(),
        build_v2_pause_list_adapter(),
        build_v2_pause_list_selected_callback(),
        build_v2_pause_list_selected_adapter(),
        build_v2_quit_choices_scope(),
        build_v2_quit_selected_adapter(),
        build_v2_quit_unselected_adapter(),
        build_v2_quit_body_callback(),
        build_v2_quit_body_adapter(),
        build_v2_native_measure(),
        build_v2_wrap_native(),
        build_v2_practice_append(),
        build_v2_practice_icon_metric(),
        build_v2_practice_icon_draw(),
        build_v2_practice_callback(),
        build_v2_practice_adapter(),
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


def numeric_fragments() -> tuple[Fragment, ...]:
    result = (build_ninja_song_ascii_number(),)
    symbols = [fragment.symbol for fragment in result]
    if len(symbols) != len(set(symbols)):
        raise ValueError("generated numeric fragments export duplicate symbols")
    return result


def fragments() -> tuple[Fragment, ...]:
    result = legacy_fragments() + v2_fragments() + numeric_fragments()
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


def generated_outputs() -> tuple[bytes, bytes, bytes, bytes, bytes]:
    legacy = legacy_fragments()
    v2 = v2_fragments()
    numeric = numeric_fragments()
    legacy_blob, legacy_offsets = pack_blob(legacy)
    v2_blob, v2_offsets = pack_blob(v2)
    numeric_blob, numeric_offsets = pack_blob(numeric)
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
        *make_fragment_rows(
            numeric,
            NUMERIC_BLOB_RELATIVE,
            numeric_blob,
            numeric_offsets,
        ),
    ]
    generated_relocations = [
        *relocation_rows(legacy, "FR-R"),
        *relocation_rows(v2, "FR-V2-R"),
        *relocation_rows(numeric, "FR-NUM-R"),
    ]
    return (
        legacy_blob,
        v2_blob,
        numeric_blob,
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
            NUMERIC_BLOB_OUTPUT,
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
