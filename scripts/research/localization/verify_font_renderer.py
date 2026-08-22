#!/usr/bin/env python3
"""Verify reconstructed resident fragments for the accepted NA2 font renderer."""

from __future__ import annotations

import hashlib
import struct
import sys
import tempfile
from dataclasses import dataclass
from functools import lru_cache
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

from na228_builder.scripts import catalog  # noqa: E402
from na228_builder.payload_builder import mips  # noqa: E402
from scripts.lib.paths import load_paths  # noqa: E402
from na228_builder.payload_builder import ee_c_fragments  # noqa: E402


PACKED_METRICS_INPUT = load_paths(REPOSITORY).path(
    "builder",
    "localization",
    "assets",
    "nun5_semantic_14x20_packed_map.bin",
)
C_CORE_SOURCE = REPOSITORY / "src" / "localization" / "font" / "font_v2_core.c"
C_V2_SOURCES = {
    "core": C_CORE_SOURCE,
    "menus": C_CORE_SOURCE.with_name("font_v2_menus.c"),
    "bodies": C_CORE_SOURCE.with_name("font_v2_bodies.c"),
    "mixed_text": C_CORE_SOURCE.with_name("font_v2_mixed_text.c"),
    "lists": C_CORE_SOURCE.with_name("font_v2_lists.c"),
    "settings": C_CORE_SOURCE.with_name("font_v2_settings.c"),
    "ninja_song": C_CORE_SOURCE.with_name("font_v2_ninja_song.c"),
    "selected_style": C_CORE_SOURCE.with_name("font_v2_selected_style.c"),
}
C_NUMERIC_SOURCE = C_CORE_SOURCE.with_name("font_numeric.c")
C_TOOLCHAIN_BIN = ee_c_fragments.default_toolchain_bin(REPOSITORY)

PREFIX = "localization.font"


def _concise_payload_symbol(symbol: str) -> str:
    v2_prefix = f"{PREFIX}.v2."
    if symbol.startswith(v2_prefix):
        return "v2_" + symbol.removeprefix(v2_prefix).replace(".", "_")
    font_prefix = f"{PREFIX}."
    if symbol.startswith(font_prefix):
        return symbol.removeprefix(font_prefix).replace(".", "_")
    return symbol


NINJA_SONG_ASCII_NUMBER = _concise_payload_symbol(
    f"{PREFIX}.ninja_song_ascii_number"
)
NUMERIC_FORMAT_DECIMAL = _concise_payload_symbol(
    f"{PREFIX}.c.numeric_format_decimal"
)
NUMERIC_FORMAT_TWO_DECIMAL = _concise_payload_symbol(
    f"{PREFIX}.c.numeric_format_two_decimal"
)
NINJA_SONG_FORMAT_DECIMAL = NUMERIC_FORMAT_DECIMAL
SAVE_LOAD_DAY = _concise_payload_symbol(f"{PREFIX}.save_load_day")
SAVE_LOAD_TWO = _concise_payload_symbol(f"{PREFIX}.save_load_two")
SAVE_LOAD_YEAR = _concise_payload_symbol(f"{PREFIX}.save_load_year")
SAVE_LOAD_HOUR = _concise_payload_symbol(f"{PREFIX}.save_load_hour")
BATTLE_SETTINGS_TIME = _concise_payload_symbol(f"{PREFIX}.battle_settings_time")

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
V2_PAUSE_LIST_SELECTED_IMPL = (
    f"{V2_PREFIX}.c.pause_list_selected_impl"
)
V2_LINKED_CHOICE_SELECTED_ADAPTER = (
    f"{V2_PREFIX}.linked_choice_selected_adapter"
)
V2_LINKED_CHOICE_SELECTED_IMPL = (
    f"{V2_PREFIX}.c.linked_choice_selected_impl"
)
V2_LINKED_CHOICE_UNSELECTED_ADAPTER = (
    f"{V2_PREFIX}.linked_choice_unselected_adapter"
)
V2_QUIT_ACTIVE = f"{V2_PREFIX}.quit_active"
V2_QUIT_CHOICES_SCOPE = f"{V2_PREFIX}.quit_choices_scope"
V2_CHARACTER_CHOICES_SCOPE = f"{V2_PREFIX}.character_choices_scope"
V2_QUIT_SCOPE_ENTER = f"{V2_PREFIX}.c.quit_scope_enter"
V2_CHARACTER_SCOPE_ENTER = f"{V2_PREFIX}.c.character_scope_enter"
V2_QUIT_SCOPE_LEAVE = f"{V2_PREFIX}.c.quit_scope_leave"
V2_QUIT_SELECTED_ADAPTER = f"{V2_PREFIX}.quit_selected_adapter"
V2_QUIT_SELECTED_MAP = f"{V2_PREFIX}.c.quit_selected_map"
V2_SPECIAL_CHOICE_SELECTED_ADAPTER = (
    f"{V2_PREFIX}.c.special_choice_selected_adapter"
)
V2_SPECIAL_CHOICE_SELECTED_CALLBACK = (
    f"{V2_PREFIX}.special_choice_selected_callback"
)
V2_GLOBAL_SELECTED_STYLE = f"{V2_PREFIX}.global_selected_style"
V2_GLOBAL_SELECTED_RECORD_DRAW = (
    f"{V2_PREFIX}.global_selected_record_draw"
)
V2_GLOBAL_TWO_CHOICE_DRAW = f"{V2_PREFIX}.global_two_choice_draw"
V2_QUIT_UNSELECTED_ADAPTER = f"{V2_PREFIX}.quit_unselected_adapter"
V2_QUIT_UNSELECTED_CALLBACK = (
    f"{V2_PREFIX}.c.quit_unselected_callback"
)
V2_QUIT_BODY_CALLBACK = f"{V2_PREFIX}.quit_body_callback"
V2_QUIT_BODY_ADAPTER = f"{V2_PREFIX}.quit_body_adapter"
V2_SPECIAL_CONTROLS_BODY_CALLBACK = (
    f"{V2_PREFIX}.special_controls_body_callback"
)
V2_SPECIAL_CONTROLS_BODY_ADAPTER = (
    f"{V2_PREFIX}.special_controls_body_adapter"
)
V2_COLLECTION_BODY_ADAPTER = f"{V2_PREFIX}.collection_body_adapter"
V2_NATIVE_MEASURE = f"{V2_PREFIX}.native_measure"
V2_NATIVE_MEASURE_CALLBACK = f"{V2_PREFIX}.c.native_measure_callback"
V2_WRAP_NATIVE = f"{V2_PREFIX}.wrap_native"
V2_WRAP_RETRY = f"{V2_PREFIX}.c.wrap_retry"
V2_PRACTICE_TOKENS = f"{V2_PREFIX}.practice_tokens"
V2_PRACTICE_APPEND = f"{V2_PREFIX}.practice_append"
V2_COMMAND_RELATIONSHIP_IMPL = (
    f"{V2_PREFIX}.c.command_relationship_impl"
)
V2_COMMAND_ICON_OFFSET = f"{V2_PREFIX}.c.command_icon_offset"
V2_CHARACTER_CONFIRMATION_BODY_ADAPTER = (
    f"{V2_PREFIX}.character_confirmation_body_adapter"
)
V2_CHARACTER_SELECTED_ADAPTER = (
    f"{V2_PREFIX}.character_selected_adapter"
)
V2_CHARACTER_UNSELECTED_ADAPTER = (
    f"{V2_PREFIX}.character_unselected_adapter"
)
V2_JUTSU_DRAW_CALLBACK = f"{V2_PREFIX}.c.jutsu_draw_callback"
V2_JUTSU_DRAW_ENTRY = f"{V2_PREFIX}.jutsu_draw_entry"
V2_COLLECTION_LIST_CALLBACK = f"{V2_PREFIX}.c.collection_list_callback"
V2_COLLECTION_LIST_ENTRY = f"{V2_PREFIX}.collection_list_entry"
V2_COLLECTION_PLAQUE_CALLBACK = (
    f"{V2_PREFIX}.c.collection_plaque_callback"
)
V2_COLLECTION_PLAQUE_DRAW = f"{V2_PREFIX}.c.collection_plaque_draw"
V2_COLLECTION_PLAQUE_ADAPTER = (
    f"{V2_PREFIX}.collection_plaque_adapter"
)
V2_COLLECTION_DIORAMA_TITLE_CALLBACK = (
    f"{V2_PREFIX}.c.collection_diorama_title_callback"
)
V2_COLLECTION_DIORAMA_TITLE_ADAPTER = (
    f"{V2_PREFIX}.collection_diorama_title_adapter"
)
V2_COLLECTION_DIORAMA_PROMPT_ADAPTER = (
    f"{V2_PREFIX}.collection_diorama_prompt_adapter"
)
V2_COLLECTION_DIORAMA_DISPLAY_PROMPT_ADAPTER = (
    f"{V2_PREFIX}.collection_diorama_display_prompt_adapter"
)
V2_COLLECTION_DIORAMA_PROMPT_RECORDS = (
    f"{V2_PREFIX}.collection_diorama_prompt_records"
)
V2_CHARACTER_CONFIRMATION_BODY_CALLBACK = (
    f"{V2_PREFIX}.c.character_confirmation_body_callback"
)
V2_PRACTICE_ICON_MAP = f"{V2_PREFIX}.practice_icon_map"
V2_PRACTICE_ICON_METRIC = f"{V2_PREFIX}.practice_icon_metric"
V2_PRACTICE_ICON_DRAW = f"{V2_PREFIX}.practice_icon_draw"
V2_PRACTICE_ICON_DRAW_CALLBACK = (
    f"{V2_PREFIX}.c.practice_icon_draw_callback"
)
V2_PRACTICE_CALLBACK = f"{V2_PREFIX}.practice_callback"
V2_PRACTICE_ADAPTER = f"{V2_PREFIX}.practice_adapter"
V2_PRACTICE_ADAPTER_IMPL = f"{V2_PREFIX}.c.practice_adapter_impl"
V2_SETTINGS_LABEL_CALLBACK = f"{V2_PREFIX}.c.settings_label_callback"
V2_SETTINGS_HEADING_CALLBACK = f"{V2_PREFIX}.c.settings_heading_callback"
V2_SETTINGS_VALUE_CALLBACK = f"{V2_PREFIX}.c.settings_value_callback"
V2_SETTINGS_ROW_COMMON = f"{V2_PREFIX}.c.settings_row_common"
V2_BATTLE_SETTINGS_LABEL_ADAPTER = (
    f"{V2_PREFIX}.battle_settings_label_adapter"
)
V2_PRACTICE_SETTINGS_LABEL_ADAPTER = (
    f"{V2_PREFIX}.practice_settings_label_adapter"
)
V2_SETTINGS_VALUE_ADAPTER = f"{V2_PREFIX}.settings_value_adapter"
V2_BATTLE_SETTINGS_VALUE_ADAPTER = (
    f"{V2_PREFIX}.battle_settings_value_adapter"
)
V2_PRACTICE_SETTINGS_HEADING_ADAPTER = (
    f"{V2_PREFIX}.practice_settings_heading_adapter"
)
V2_NINJA_TEXT_CALLBACK = f"{V2_PREFIX}.c.ninja_text_callback"
V2_NINJA_TEXT_COMMON = f"{V2_PREFIX}.c.ninja_text_common"
V2_NINJA_COMPACT_ADAPTER = f"{V2_PREFIX}.ninja_compact_adapter"
V2_NINJA_UNIT_ADAPTER = f"{V2_PREFIX}.ninja_unit_adapter"
V2_NINJA_EQUALS_ADAPTER = f"{V2_PREFIX}.ninja_equals_adapter"
V2_NINJA_TOTAL_ADAPTER = f"{V2_PREFIX}.ninja_total_adapter"
V2_NINJA_EMPTY_ADAPTER = f"{V2_PREFIX}.ninja_empty_adapter"
V2_NINJA_ARITHMETIC_TEMPLATE = (
    f"{V2_PREFIX}.ninja_arithmetic_template"
)
V2_NINJA_BONUS_LABEL_DRAW = f"{V2_PREFIX}.c.ninja_bonus_label_draw"
V2_NINJA_BONUS_TOTAL_DRAW = f"{V2_PREFIX}.c.ninja_bonus_total_draw"
V2_NINJA_BONUS_TEMPLATE = f"{V2_PREFIX}.ninja_bonus_template"
V2_NINJA_OBJECTIVE_CALLBACK = f"{V2_PREFIX}.c.ninja_objective_callback"
V2_NINJA_OBJECTIVE_DRAW = f"{V2_PREFIX}.c.ninja_objective_draw"
V2_NINJA_OBJECTIVE_ROW_ADAPTER = (
    f"{V2_PREFIX}.ninja_objective_row_adapter"
)
V2_PLAIN_SPACE = f"{V2_PREFIX}.plain_space"
V2_NEWLINE_ADVANCE = f"{V2_PREFIX}.newline_advance"
V2_RIGHT_EDGE = f"{V2_PREFIX}.right_edge"
V2_HALF_SPACE = f"{V2_PREFIX}.half_space"
V2_GLYPH_ADVANCE = f"{V2_PREFIX}.glyph_advance"

for _constant_name, _constant_value in tuple(globals().items()):
    if (
        _constant_name.startswith("V2_")
        and _constant_name != "V2_PREFIX"
        and isinstance(_constant_value, str)
    ):
        globals()[_constant_name] = _concise_payload_symbol(_constant_value)
del _constant_name, _constant_value

SCALE_ADDRESS = 0x0060737C
FONT_RENDERER_POINTER = 0x00607470
FONT_MEASURE = 0x003798E0
FONT_CENTER = 0x00379240
FONT_PLAIN_DRAW = 0x00378F50
FONT_BOX_DRAW = 0x00382310
FONT_PAUSE_LIST_DRAW = 0x00382470
FONT_PAUSE_LIST_SELECTED_DRAW = 0x003827A0
FONT_UI_DRAW = 0x00379A20
FONT_SELECTED_DRAW = 0x00379150
FONT_RECORD_DRAW = 0x003821D0
FONT_SET_CONTEXT = 0x001866D0
FONT_CHOICE_LIST_DRAW = 0x00383600
FONT_ICON_DRAW = 0x0037BB40
FONT_TWO_CHOICE_RECORDS = 0x005B1280
SPRINTF = 0x0017BCA0
FORMAT_D = 0x006042D3
FORMAT_02D = 0x00605C20
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

NEWLINE_ADVANCE_RETURN = 0x00188670
V2_PLAIN_SPACE_RESUME = 0x001892F4
V2_NEWLINE_ORIGINAL_RESUME = 0x0018860C
V2_RIGHT_EDGE_RESUME = 0x00187F78
V2_GLYPH_BOTTOM_RESUME = 0x00187F80
V2_GLYPH_BOTTOM_DELAY = 0x8F84CA6C
V2_HALF_SPACE_RESUME = 0x00188A84
V2_GLYPH_ADVANCE_RESUME = 0x001896E0
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
SPECIAL_CONTROLS_BODY_BOX_X = 24.0
SPECIAL_CONTROLS_BODY_BOX_Y = 12.0
SPECIAL_CONTROLS_BODY_BOX_WIDTH = 400
SPECIAL_CONTROLS_BODY_BOX_HEIGHT = 60
SPECIAL_CONTROLS_BODY_LINE_HEIGHT = 20.0
SPECIAL_CONTROLS_BODY_LINE_LIMIT = 2
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
V2_SPECIAL_CHOICE_NATIVE_ARG3 = 0x6C

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
V2_FLAG_GLYPH_HEIGHT = 0x40

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

@dataclass(frozen=True)
class Fragment:
    symbol: str
    payload: bytes
    relocations: tuple[mips.Relocation, ...] = ()
    kind: str = "code"
    alignment: int = 4
    init: bool = False


@dataclass(frozen=True)
class NumericHook:
    edit_id: str
    patch_id: str
    order: int
    target_id: str
    offset: int
    expected_hex: str
    replacement_hex: str
    relocation_offset: int
    symbol: str
    reason: str
    encoding: str = "jal26"


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




@lru_cache(maxsize=1)
def build_v2_c_sources() -> tuple[Fragment, ...]:
    shared_fragments: dict[str, ee_c_fragments.PayloadFragment] = {}
    shared_symbols: dict[str, ee_c_fragments.SymbolReference] = {}

    source_symbols = {
        "font_v2_measure": V2_MEASURE,
        "font_v2_adapter_call": V2_ADAPTER_CALL,
        "font_v2_native_measure": V2_NATIVE_MEASURE,
        "font_v2_wrap_native": V2_WRAP_NATIVE,
        "font_v2_wrap_retry": V2_WRAP_RETRY,
        "font_v2_is_mode_select_body": ee_c_fragments.SymbolReference(
            f"{V2_PREFIX}.c.text", 72
        ),
    }
    with tempfile.TemporaryDirectory(prefix="na2-font-v2-c-") as temporary:
        common_external_symbols = {
            "font_v2_ascii_widths": ee_c_fragments.SymbolReference(
                V2_ASCII_WIDTHS
            ),
            "font_v2_active_session": ee_c_fragments.SymbolReference(
                V2_SESSION_POINTER
            ),
            "font_v2_controls_callback": ee_c_fragments.SymbolReference(
                V2_CONTROLS_CALLBACK
            ),
            "font_v2_title_callback": ee_c_fragments.SymbolReference(
                V2_TITLE_CALLBACK
            ),
            "font_v2_pause_list_callback": ee_c_fragments.SymbolReference(
                V2_PAUSE_LIST_CALLBACK
            ),
            "font_v2_pause_list_selected_callback": (
                ee_c_fragments.SymbolReference(
                    V2_PAUSE_LIST_SELECTED_CALLBACK
                )
            ),
            "font_v2_quit_active": ee_c_fragments.SymbolReference(
                V2_QUIT_ACTIVE
            ),
            "font_v2_quit_unselected_callback": (
                ee_c_fragments.SymbolReference(V2_QUIT_UNSELECTED_CALLBACK)
            ),
            "font_v2_special_choice_selected_callback": (
                ee_c_fragments.SymbolReference(
                    V2_SPECIAL_CHOICE_SELECTED_CALLBACK
                )
            ),
            "font_v2_quit_body_callback": ee_c_fragments.SymbolReference(
                V2_QUIT_BODY_CALLBACK
            ),
            "font_v2_special_controls_body_callback": (
                ee_c_fragments.SymbolReference(
                    V2_SPECIAL_CONTROLS_BODY_CALLBACK
                )
            ),
            "font_v2_native_measure_callback": (
                ee_c_fragments.SymbolReference(V2_NATIVE_MEASURE_CALLBACK)
            ),
            "font_v2_practice_tokens": ee_c_fragments.SymbolReference(
                V2_PRACTICE_TOKENS
            ),
            "font_v2_practice_icon_map": ee_c_fragments.SymbolReference(
                V2_PRACTICE_ICON_MAP
            ),
            "font_v2_practice_icon_draw_callback": (
                ee_c_fragments.SymbolReference(
                    V2_PRACTICE_ICON_DRAW_CALLBACK
                )
            ),
            "font_v2_practice_callback": ee_c_fragments.SymbolReference(
                V2_PRACTICE_CALLBACK
            ),
            "font_ninja_song_ascii_number": ee_c_fragments.SymbolReference(
                NINJA_SONG_ASCII_NUMBER
            ),
        }
        for source_name, source_path in C_V2_SOURCES.items():
            external_symbols = dict(common_external_symbols)
            for c_name, target in source_symbols.items():
                if isinstance(target, str):
                    external_symbols[c_name] = ee_c_fragments.SymbolReference(
                        target
                    )
                else:
                    external_symbols[c_name] = target
            compiled = ee_c_fragments.compile_and_extract(
                source_path,
                Path(temporary) / f"font_v2_{source_name}.o",
                namespace=f"{V2_PREFIX}.c",
                toolchain_bin=C_TOOLCHAIN_BIN,
                external_symbols=external_symbols,
            )
            for fragment in compiled.fragments:
                if fragment.symbol in shared_fragments:
                    raise ValueError(
                        "Font v2 C sources export duplicate fragment "
                        f"{fragment.symbol!r}"
                    )
                shared_fragments[fragment.symbol] = fragment
            for name, reference in compiled.symbols.items():
                if name in shared_symbols:
                    raise ValueError(
                        f"Font v2 C sources export duplicate symbol {name!r}"
                    )
                shared_symbols[name] = reference

    extracted = ee_c_fragments.ExtractedEeObject(
        fragments=tuple(shared_fragments.values()),
        symbols=shared_symbols,
    )

    expected_exports = {
        "font_v2_measure",
        "font_v2_prepare",
        "font_v2_adapter_call",
        "font_v2_wrap_retry",
        "font_v2_controls_callback",
        "font_v2_controls_adapter",
        "font_v2_command_title_entry",
        "font_v2_practice_title_entry",
        "font_v2_pause_list_adapter",
        "font_v2_pause_list_selected_impl",
        "font_v2_quit_scope_enter",
        "font_v2_character_scope_enter",
        "font_v2_quit_scope_leave",
        "font_v2_quit_selected_map",
        "font_v2_special_choice_selected_adapter",
        "font_v2_quit_unselected_adapter",
        "font_v2_native_measure",
        "font_v2_wrap_native",
        "font_v2_quit_body_adapter",
        "font_v2_special_controls_body_adapter",
        "font_v2_collection_body_adapter",
        "font_v2_practice_append",
        "font_v2_command_relationship_impl",
        "font_v2_command_icon_offset",
        "font_v2_character_confirmation_body_adapter",
        "font_v2_character_selected_adapter",
        "font_v2_character_unselected_adapter",
        "font_v2_jutsu_draw_entry",
        "font_v2_collection_list_entry",
        "font_v2_collection_plaque_adapter",
        "font_v2_collection_diorama_title_adapter",
        "font_v2_collection_diorama_prompt_adapter",
        "font_v2_collection_diorama_display_prompt_adapter",
        "font_v2_practice_icon_metric",
        "font_v2_practice_icon_draw",
        "font_v2_practice_adapter_impl",
        "font_v2_battle_settings_label_adapter",
        "font_v2_practice_settings_label_adapter",
        "font_v2_settings_value_adapter",
        "font_v2_battle_settings_value_adapter",
        "font_v2_practice_settings_heading_adapter",
        "font_v2_ninja_arithmetic_template",
        "font_v2_ninja_bonus_template",
        "font_v2_ninja_objective_row_adapter",
        "font_v2_global_two_choice_draw",
    }
    if set(extracted.symbols) != expected_exports:
        raise ValueError(
            "Font v2 C exports differ: "
            f"expected={sorted(expected_exports)}, "
            f"actual={sorted(extracted.symbols)}"
        )
    aliases = {
        extracted.symbols["font_v2_measure"].symbol: V2_MEASURE,
        extracted.symbols["font_v2_prepare"].symbol: V2_PREPARE,
        extracted.symbols["font_v2_adapter_call"].symbol: V2_ADAPTER_CALL,
        extracted.symbols["font_v2_controls_callback"].symbol: (
            V2_CONTROLS_CALLBACK
        ),
        extracted.symbols["font_v2_controls_adapter"].symbol: (
            V2_CONTROLS_ADAPTER
        ),
        extracted.symbols["font_v2_command_title_entry"].symbol: (
            V2_COMMAND_TITLE_ENTRY
        ),
        extracted.symbols["font_v2_practice_title_entry"].symbol: (
            V2_PRACTICE_TITLE_ENTRY
        ),
        extracted.symbols["font_v2_pause_list_adapter"].symbol: (
            V2_PAUSE_LIST_ADAPTER
        ),
        extracted.symbols["font_v2_pause_list_selected_impl"].symbol: (
            V2_PAUSE_LIST_SELECTED_IMPL
        ),
        extracted.symbols["font_v2_quit_scope_enter"].symbol: (
            V2_QUIT_SCOPE_ENTER
        ),
        extracted.symbols["font_v2_character_scope_enter"].symbol: (
            V2_CHARACTER_SCOPE_ENTER
        ),
        extracted.symbols["font_v2_quit_scope_leave"].symbol: (
            V2_QUIT_SCOPE_LEAVE
        ),
        extracted.symbols["font_v2_quit_selected_map"].symbol: (
            V2_QUIT_SELECTED_MAP
        ),
        extracted.symbols[
            "font_v2_special_choice_selected_adapter"
        ].symbol: V2_SPECIAL_CHOICE_SELECTED_ADAPTER,
        extracted.symbols["font_v2_quit_unselected_adapter"].symbol: (
            V2_QUIT_UNSELECTED_ADAPTER
        ),
        extracted.symbols["font_v2_native_measure"].symbol: (
            V2_NATIVE_MEASURE
        ),
        extracted.symbols["font_v2_wrap_native"].symbol: V2_WRAP_NATIVE,
        extracted.symbols["font_v2_quit_body_adapter"].symbol: (
            V2_QUIT_BODY_ADAPTER
        ),
        extracted.symbols[
            "font_v2_special_controls_body_adapter"
        ].symbol: V2_SPECIAL_CONTROLS_BODY_ADAPTER,
        extracted.symbols["font_v2_collection_body_adapter"].symbol: (
            V2_COLLECTION_BODY_ADAPTER
        ),
        extracted.symbols["font_v2_practice_append"].symbol: (
            V2_PRACTICE_APPEND
        ),
        extracted.symbols["font_v2_command_relationship_impl"].symbol: (
            V2_COMMAND_RELATIONSHIP_IMPL
        ),
        extracted.symbols["font_v2_command_icon_offset"].symbol: (
            V2_COMMAND_ICON_OFFSET
        ),
        extracted.symbols[
            "font_v2_character_confirmation_body_adapter"
        ].symbol: V2_CHARACTER_CONFIRMATION_BODY_ADAPTER,
        extracted.symbols["font_v2_character_selected_adapter"].symbol: (
            V2_CHARACTER_SELECTED_ADAPTER
        ),
        extracted.symbols["font_v2_character_unselected_adapter"].symbol: (
            V2_CHARACTER_UNSELECTED_ADAPTER
        ),
        extracted.symbols["font_v2_jutsu_draw_entry"].symbol: (
            V2_JUTSU_DRAW_ENTRY
        ),
        extracted.symbols["font_v2_collection_list_entry"].symbol: (
            V2_COLLECTION_LIST_ENTRY
        ),
        extracted.symbols["font_v2_collection_plaque_adapter"].symbol: (
            V2_COLLECTION_PLAQUE_ADAPTER
        ),
        extracted.symbols[
            "font_v2_collection_diorama_title_adapter"
        ].symbol: V2_COLLECTION_DIORAMA_TITLE_ADAPTER,
        extracted.symbols[
            "font_v2_collection_diorama_prompt_adapter"
        ].symbol: V2_COLLECTION_DIORAMA_PROMPT_ADAPTER,
        extracted.symbols[
            "font_v2_collection_diorama_display_prompt_adapter"
        ].symbol: V2_COLLECTION_DIORAMA_DISPLAY_PROMPT_ADAPTER,
        extracted.symbols["font_v2_practice_icon_metric"].symbol: (
            V2_PRACTICE_ICON_METRIC
        ),
        extracted.symbols["font_v2_practice_icon_draw"].symbol: (
            V2_PRACTICE_ICON_DRAW
        ),
        extracted.symbols["font_v2_practice_adapter_impl"].symbol: (
            V2_PRACTICE_ADAPTER_IMPL
        ),
        extracted.symbols[
            "font_v2_battle_settings_label_adapter"
        ].symbol: V2_BATTLE_SETTINGS_LABEL_ADAPTER,
        extracted.symbols[
            "font_v2_practice_settings_label_adapter"
        ].symbol: V2_PRACTICE_SETTINGS_LABEL_ADAPTER,
        extracted.symbols["font_v2_settings_value_adapter"].symbol: (
            V2_SETTINGS_VALUE_ADAPTER
        ),
        extracted.symbols[
            "font_v2_battle_settings_value_adapter"
        ].symbol: V2_BATTLE_SETTINGS_VALUE_ADAPTER,
        extracted.symbols[
            "font_v2_practice_settings_heading_adapter"
        ].symbol: V2_PRACTICE_SETTINGS_HEADING_ADAPTER,
        extracted.symbols["font_v2_ninja_arithmetic_template"].symbol: (
            V2_NINJA_ARITHMETIC_TEMPLATE
        ),
        extracted.symbols["font_v2_ninja_bonus_template"].symbol: (
            V2_NINJA_BONUS_TEMPLATE
        ),
        extracted.symbols[
            "font_v2_ninja_objective_row_adapter"
        ].symbol: V2_NINJA_OBJECTIVE_ROW_ADAPTER,
        extracted.symbols["font_v2_global_two_choice_draw"].symbol: (
            V2_GLOBAL_TWO_CHOICE_DRAW
        ),
    }
    helper_symbols = {
        fragment.symbol
        for fragment in extracted.fragments
        if fragment.symbol not in aliases
    }
    helper_aliases = {
        f"{V2_PREFIX}.c.text": f"{V2_PREFIX}.c.is_br",
        f"{V2_PREFIX}.c.text.font.v2.title.adapter.common": (
            V2_TITLE_ADAPTER
        ),
        f"{V2_PREFIX}.c.text.font.v2.map.choice": (
            f"{V2_PREFIX}.c.map_choice"
        ),
        f"{V2_PREFIX}.c.text.font.v2.wrapped.body.common": (
            f"{V2_PREFIX}.c.wrapped_body_common"
        ),
        f"{V2_PREFIX}.c.text.font.v2.wrap.retry": V2_WRAP_RETRY,
        f"{V2_PREFIX}.c.text.font.v2.icon.record": (
            f"{V2_PREFIX}.c.icon_record"
        ),
        (
            f"{V2_PREFIX}.c.text.font.v2.character."
            "confirmation.body.callback"
        ): V2_CHARACTER_CONFIRMATION_BODY_CALLBACK,
        f"{V2_PREFIX}.c.text.font.v2.jutsu.draw.callback": (
            V2_JUTSU_DRAW_CALLBACK
        ),
        f"{V2_PREFIX}.c.text.font.v2.collection.list.callback": (
            V2_COLLECTION_LIST_CALLBACK
        ),
        f"{V2_PREFIX}.c.text.font.v2.collection.plaque.callback": (
            V2_COLLECTION_PLAQUE_CALLBACK
        ),
        f"{V2_PREFIX}.c.text.font.v2.collection.plaque.draw": (
            V2_COLLECTION_PLAQUE_DRAW
        ),
        f"{V2_PREFIX}.c.text.font.v2.collection.diorama.title.callback": (
            V2_COLLECTION_DIORAMA_TITLE_CALLBACK
        ),
        f"{V2_PREFIX}.c.rodata.font.v2.collection.diorama.prompt.records": (
            V2_COLLECTION_DIORAMA_PROMPT_RECORDS
        ),
        f"{V2_PREFIX}.c.text.font.v2.collection.body.callback": (
            f"{V2_PREFIX}.c.collection_body_callback"
        ),
        f"{V2_PREFIX}.c.text.font.v2.settings.label.callback": (
            V2_SETTINGS_LABEL_CALLBACK
        ),
        f"{V2_PREFIX}.c.text.font.v2.settings.heading.callback": (
            V2_SETTINGS_HEADING_CALLBACK
        ),
        f"{V2_PREFIX}.c.text.font.v2.settings.value.callback": (
            V2_SETTINGS_VALUE_CALLBACK
        ),
        f"{V2_PREFIX}.c.text.font.v2.settings.row.common": (
            V2_SETTINGS_ROW_COMMON
        ),
        f"{V2_PREFIX}.c.text.font.v2.special.choice.session.init": (
            f"{V2_PREFIX}.c.special_choice_session_init"
        ),
        f"{V2_PREFIX}.c.text.font.v2.ninja.text.callback": (
            V2_NINJA_TEXT_CALLBACK
        ),
        f"{V2_PREFIX}.c.text.font.v2.ninja.text.common": (
            V2_NINJA_TEXT_COMMON
        ),
        f"{V2_PREFIX}.c.text.font.v2.ninja.compact.adapter": (
            V2_NINJA_COMPACT_ADAPTER
        ),
        f"{V2_PREFIX}.c.text.font.v2.ninja.unit.adapter": (
            V2_NINJA_UNIT_ADAPTER
        ),
        f"{V2_PREFIX}.c.text.font.v2.ninja.equals.adapter": (
            V2_NINJA_EQUALS_ADAPTER
        ),
        f"{V2_PREFIX}.c.text.font.v2.ninja.total.adapter": (
            V2_NINJA_TOTAL_ADAPTER
        ),
        f"{V2_PREFIX}.c.text.font.v2.ninja.empty.adapter": (
            V2_NINJA_EMPTY_ADAPTER
        ),
        f"{V2_PREFIX}.c.text.font.v2.ninja.objective.callback": (
            V2_NINJA_OBJECTIVE_CALLBACK
        ),
        f"{V2_PREFIX}.c.text.font.v2.ninja.objective.draw": (
            V2_NINJA_OBJECTIVE_DRAW
        ),
        f"{V2_PREFIX}.c.text.font.v2.ninja.bonus.label.draw": (
            V2_NINJA_BONUS_LABEL_DRAW
        ),
        f"{V2_PREFIX}.c.text.font.v2.ninja.bonus.total.draw": (
            V2_NINJA_BONUS_TOTAL_DRAW
        ),
    }
    if helper_symbols != set(helper_aliases):
        raise ValueError(
            "Font v2 C private helper fragments differ: "
            f"expected={sorted(helper_aliases)}, "
            f"actual={sorted(helper_symbols)}"
        )
    aliases.update(
        {
            source: _concise_payload_symbol(target)
            for source, target in helper_aliases.items()
        }
    )

    result = tuple(
        Fragment(
            symbol=aliases[fragment.symbol],
            payload=fragment.payload,
            relocations=tuple(
                mips.Relocation(
                    offset=relocation.offset,
                    kind=relocation.kind,
                    symbol=aliases.get(
                        relocation.symbol,
                        relocation.symbol,
                    ),
                    addend=relocation.addend,
                )
                for relocation in fragment.relocations
            ),
            kind=fragment.kind,
            alignment=fragment.alignment,
            init=fragment.init,
        )
        for fragment in extracted.fragments
    )
    if {fragment.symbol for fragment in result} != {
        _concise_payload_symbol(f"{V2_PREFIX}.c.is_br"),
        V2_MEASURE,
        V2_PREPARE,
        V2_ADAPTER_CALL,
        V2_CONTROLS_CALLBACK,
        V2_CONTROLS_ADAPTER,
        V2_TITLE_ADAPTER,
        V2_COMMAND_TITLE_ENTRY,
        V2_PRACTICE_TITLE_ENTRY,
        V2_PAUSE_LIST_ADAPTER,
        V2_PAUSE_LIST_SELECTED_IMPL,
        V2_QUIT_SCOPE_ENTER,
        V2_CHARACTER_SCOPE_ENTER,
        V2_QUIT_SCOPE_LEAVE,
        _concise_payload_symbol(f"{V2_PREFIX}.c.map_choice"),
        _concise_payload_symbol(f"{V2_PREFIX}.c.special_choice_session_init"),
        V2_QUIT_SELECTED_MAP,
        V2_SPECIAL_CHOICE_SELECTED_ADAPTER,
        V2_QUIT_UNSELECTED_ADAPTER,
        V2_NATIVE_MEASURE,
        V2_WRAP_NATIVE,
        V2_WRAP_RETRY,
        _concise_payload_symbol(f"{V2_PREFIX}.c.wrapped_body_common"),
        V2_QUIT_BODY_ADAPTER,
        V2_SPECIAL_CONTROLS_BODY_ADAPTER,
        V2_COLLECTION_BODY_ADAPTER,
        V2_PRACTICE_APPEND,
        V2_COMMAND_RELATIONSHIP_IMPL,
        V2_COMMAND_ICON_OFFSET,
        V2_CHARACTER_CONFIRMATION_BODY_ADAPTER,
        V2_CHARACTER_SELECTED_ADAPTER,
        V2_CHARACTER_UNSELECTED_ADAPTER,
        V2_CHARACTER_CONFIRMATION_BODY_CALLBACK,
        V2_JUTSU_DRAW_CALLBACK,
        V2_JUTSU_DRAW_ENTRY,
        V2_COLLECTION_LIST_CALLBACK,
        V2_COLLECTION_LIST_ENTRY,
        V2_COLLECTION_PLAQUE_CALLBACK,
        V2_COLLECTION_PLAQUE_DRAW,
        V2_COLLECTION_PLAQUE_ADAPTER,
        V2_COLLECTION_DIORAMA_TITLE_CALLBACK,
        V2_COLLECTION_DIORAMA_TITLE_ADAPTER,
        V2_COLLECTION_DIORAMA_PROMPT_ADAPTER,
        V2_COLLECTION_DIORAMA_DISPLAY_PROMPT_ADAPTER,
        V2_COLLECTION_DIORAMA_PROMPT_RECORDS,
        _concise_payload_symbol(f"{V2_PREFIX}.c.collection_body_callback"),
        _concise_payload_symbol(f"{V2_PREFIX}.c.icon_record"),
        V2_PRACTICE_ICON_METRIC,
        V2_PRACTICE_ICON_DRAW,
        V2_PRACTICE_ADAPTER_IMPL,
        V2_SETTINGS_LABEL_CALLBACK,
        V2_SETTINGS_HEADING_CALLBACK,
        V2_SETTINGS_VALUE_CALLBACK,
        V2_SETTINGS_ROW_COMMON,
        V2_BATTLE_SETTINGS_LABEL_ADAPTER,
        V2_PRACTICE_SETTINGS_LABEL_ADAPTER,
        V2_SETTINGS_VALUE_ADAPTER,
        V2_BATTLE_SETTINGS_VALUE_ADAPTER,
        V2_PRACTICE_SETTINGS_HEADING_ADAPTER,
        V2_NINJA_TEXT_CALLBACK,
        V2_NINJA_TEXT_COMMON,
        V2_NINJA_COMPACT_ADAPTER,
        V2_NINJA_UNIT_ADAPTER,
        V2_NINJA_EQUALS_ADAPTER,
        V2_NINJA_TOTAL_ADAPTER,
        V2_NINJA_EMPTY_ADAPTER,
        V2_NINJA_ARITHMETIC_TEMPLATE,
        V2_NINJA_BONUS_LABEL_DRAW,
        V2_NINJA_BONUS_TOTAL_DRAW,
        V2_NINJA_BONUS_TEMPLATE,
        V2_NINJA_OBJECTIVE_CALLBACK,
        V2_NINJA_OBJECTIVE_DRAW,
        V2_NINJA_OBJECTIVE_ROW_ADAPTER,
        V2_GLOBAL_TWO_CHOICE_DRAW,
    }:
        raise ValueError("Font v2 C fragment aliases are incomplete")
    return result


@lru_cache(maxsize=1)
def build_numeric_c_core() -> tuple[Fragment, ...]:
    with tempfile.TemporaryDirectory(prefix="na2-font-numeric-c-") as temporary:
        extracted = ee_c_fragments.compile_and_extract(
            C_NUMERIC_SOURCE,
            Path(temporary) / "font_numeric.o",
            namespace=f"{PREFIX}.numeric.c",
            toolchain_bin=C_TOOLCHAIN_BIN,
            external_symbols={
                "font_numeric_format_decimal": (
                    ee_c_fragments.SymbolReference(
                        NUMERIC_FORMAT_DECIMAL
                    )
                ),
                "font_numeric_format_two_decimal": (
                    ee_c_fragments.SymbolReference(
                        NUMERIC_FORMAT_TWO_DECIMAL
                    )
                ),
            },
        )

    expected_exports = {
        "font_ninja_song_ascii_number": NINJA_SONG_ASCII_NUMBER,
        "font_save_load_day": SAVE_LOAD_DAY,
        "font_save_load_two": SAVE_LOAD_TWO,
        "font_save_load_year": SAVE_LOAD_YEAR,
        "font_save_load_hour": SAVE_LOAD_HOUR,
        "font_battle_settings_time": BATTLE_SETTINGS_TIME,
    }
    if set(extracted.symbols) != set(expected_exports):
        raise ValueError(
            "Font numeric C exports differ: "
            f"actual={sorted(extracted.symbols)}"
        )
    aliases = {
        extracted.symbols[name].symbol: symbol
        for name, symbol in expected_exports.items()
    }
    if {fragment.symbol for fragment in extracted.fragments} != set(aliases):
        raise ValueError(
            "Font numeric C fragments differ: "
            f"actual={sorted(fragment.symbol for fragment in extracted.fragments)}"
        )
    return tuple(
        Fragment(
            symbol=aliases[fragment.symbol],
            payload=fragment.payload,
            relocations=tuple(
                mips.Relocation(
                    offset=relocation.offset,
                    kind=relocation.kind,
                    symbol=aliases.get(
                        relocation.symbol,
                        relocation.symbol,
                    ),
                    addend=relocation.addend,
                )
                for relocation in fragment.relocations
            ),
            kind=fragment.kind,
            alignment=fragment.alignment,
            init=fragment.init,
        )
        for fragment in extracted.fragments
    )


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


def build_v2_pause_list_selected_entry(
    fragment_symbol: str = V2_PAUSE_LIST_SELECTED_ADAPTER,
    implementation_symbol: str = V2_PAUSE_LIST_SELECTED_IMPL,
) -> Fragment:
    """Capture live selected-row color in t0 for a typed C implementation."""

    t0 = 8
    sp, ra = 29, 31
    frame_size = 0x20
    saved_ra = 0x1C

    assembler = mips.Assembler()
    assembler.emit(mips.i_type(0x09, sp, sp, -frame_size))
    assembler.emit(mips.i_type(0x2B, sp, ra, saved_ra))
    # The PS2 EE EABI passes the fifth integer argument in t0.  The native
    # selected-row caller already has the required live color in that register.
    assembler.jump_symbol(0x03, implementation_symbol)
    assembler.emit(0)
    assembler.emit(mips.i_type(0x23, sp, ra, saved_ra))
    assembler.emit(mips.r_type(ra, 0, 0, 0x08))
    assembler.emit(mips.i_type(0x09, sp, sp, frame_size))
    payload, relocations = assembler.build()
    return Fragment(
        fragment_symbol,
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


def build_v2_quit_choices_scope_entry(
    fragment_symbol: str = V2_QUIT_CHOICES_SCOPE,
    enter_symbol: str = V2_QUIT_SCOPE_ENTER,
) -> Fragment:
    """Bridge the native list ABI around a C-owned nested scope state."""

    v0, a0, a1, a2, a3 = 2, 4, 5, 6, 7
    sp, ra = 29, 31
    frame_size = 0x40
    saved_arg0 = 0x10
    saved_arg1 = 0x14
    saved_arg2 = 0x18
    saved_arg3 = 0x1C
    saved_f12 = 0x20
    saved_f13 = 0x24
    saved_active = 0x28
    saved_result = 0x2C
    saved_ra = 0x3C

    assembler = mips.Assembler()
    assembler.emit(mips.i_type(0x09, sp, sp, -frame_size))
    assembler.emit(mips.i_type(0x2B, sp, ra, saved_ra))
    for register, offset in (
        (a0, saved_arg0),
        (a1, saved_arg1),
        (a2, saved_arg2),
        (a3, saved_arg3),
    ):
        assembler.emit(mips.i_type(0x2B, sp, register, offset))
    assembler.emit(mips.i_type(0x39, sp, 12, saved_f12))
    assembler.emit(mips.i_type(0x39, sp, 13, saved_f13))
    assembler.jump_symbol(0x03, enter_symbol)
    assembler.emit(0)
    assembler.emit(mips.i_type(0x2B, sp, v0, saved_active))
    for register, offset in (
        (a0, saved_arg0),
        (a1, saved_arg1),
        (a2, saved_arg2),
        (a3, saved_arg3),
    ):
        assembler.emit(mips.i_type(0x23, sp, register, offset))
    assembler.emit(mips.i_type(0x31, sp, 12, saved_f12))
    assembler.emit(mips.i_type(0x31, sp, 13, saved_f13))
    assembler.emit(mips.jump(0x03, FONT_CHOICE_LIST_DRAW))
    assembler.emit(0)
    assembler.emit(mips.i_type(0x2B, sp, v0, saved_result))
    assembler.emit(mips.i_type(0x23, sp, a0, saved_active))
    assembler.jump_symbol(0x03, V2_QUIT_SCOPE_LEAVE)
    assembler.emit(0)
    assembler.emit(mips.i_type(0x23, sp, v0, saved_result))
    assembler.emit(mips.i_type(0x23, sp, ra, saved_ra))
    assembler.emit(mips.r_type(ra, 0, 0, 0x08))
    assembler.emit(mips.i_type(0x09, sp, sp, frame_size))
    payload, relocations = assembler.build()
    return Fragment(fragment_symbol, payload, relocations)


def build_v2_quit_selected_adapter() -> Fragment:
    """Map scoped ss4 or exact ss1 selected rows to NUN5 coordinates."""

    zero, a0 = 0, 4
    t0, t1 = 8, 9
    assembler = mips.Assembler()
    assembler.load_symbol_word(t0, t0, 0x23, V2_QUIT_ACTIVE)
    assembler.branch(0x05, t0, zero, "quit_scope")
    assembler.emit(0)
    mips.load_u32(assembler, t0, SPECIAL_CONTROLS_ON_TEXT)
    assembler.branch(0x04, a0, t0, "special_on")
    assembler.emit(0)
    mips.load_u32(assembler, t0, SPECIAL_CONTROLS_OFF_TEXT)
    assembler.branch(0x05, a0, t0, "original")
    assembler.emit(0)
    emit_load_float(
        assembler, t0, 12, SPECIAL_CONTROLS_OFF_TARGET[0]
    )
    emit_load_float(
        assembler, t0, 13, SPECIAL_CONTROLS_OFF_TARGET[1]
    )
    assembler.branch(0x04, zero, zero, "original")
    assembler.emit(0)

    assembler.label("special_on")
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


def build_v2_quit_selected_entry() -> Fragment:
    """Bridge native float coordinates through the C choice mapper."""

    v0, a0, a1, a2, a3 = 2, 4, 5, 6, 7
    t0, t1 = 8, 9
    sp, ra = 29, 31
    frame_size = 0x30
    saved_arg0 = 0x10
    saved_arg1 = 0x14
    saved_arg2 = 0x18
    saved_arg3 = 0x1C
    mapped_y = 0x20
    saved_ra = 0x2C

    assembler = mips.Assembler()
    assembler.emit(mips.i_type(0x09, sp, sp, -frame_size))
    assembler.emit(mips.i_type(0x2B, sp, ra, saved_ra))
    for register, offset in (
        (a0, saved_arg0),
        (a1, saved_arg1),
        (a2, saved_arg2),
        (a3, saved_arg3),
    ):
        assembler.emit(mips.i_type(0x2B, sp, register, offset))
    mips.load_u32(assembler, t0, SPECIAL_CONTROLS_ON_TEXT)
    assembler.branch(0x04, a0, t0, "special_choice")
    assembler.emit(0)
    mips.load_u32(assembler, t0, SPECIAL_CONTROLS_OFF_TEXT)
    assembler.branch(0x05, a0, t0, "mapped_choice")
    assembler.emit(0)

    assembler.label("special_choice")
    assembler.emit(mips.mfc1(t0, 12))
    assembler.emit(mips.mfc1(t1, 13))
    assembler.jump_symbol(0x03, V2_SPECIAL_CHOICE_SELECTED_ADAPTER)
    assembler.emit(0)
    assembler.emit(mips.i_type(0x23, sp, ra, saved_ra))
    assembler.emit(mips.r_type(ra, 0, 0, 0x08))
    assembler.emit(mips.i_type(0x09, sp, sp, frame_size))

    assembler.label("mapped_choice")
    assembler.emit(mips.mfc1(a1, 13))
    assembler.emit(mips.mfc1(a2, 12))
    assembler.emit(mips.i_type(0x09, sp, a3, mapped_y))
    assembler.jump_symbol(0x03, V2_QUIT_SELECTED_MAP)
    assembler.emit(0)
    assembler.emit(mips.mtc1(v0, 12))
    assembler.emit(mips.i_type(0x23, sp, t0, mapped_y))
    assembler.emit(mips.mtc1(t0, 13))
    for register, offset in (
        (a0, saved_arg0),
        (a1, saved_arg1),
        (a2, saved_arg2),
        (a3, saved_arg3),
    ):
        assembler.emit(mips.i_type(0x23, sp, register, offset))
    assembler.emit(mips.i_type(0x23, sp, ra, saved_ra))
    assembler.emit(mips.i_type(0x09, sp, sp, frame_size))
    assembler.emit(mips.jump(0x02, FONT_SELECTED_DRAW))
    assembler.emit(0)
    payload, relocations = assembler.build()
    return Fragment(V2_QUIT_SELECTED_ADAPTER, payload, relocations)


def build_v2_special_choice_selected_callback() -> Fragment:
    """Draw one prepared selected Special Controls choice natively."""

    a3 = 7
    assembler = mips.Assembler()
    assembler.emit(mips.i_type(0x31, a3, 12, V2_SESSION_DRAW_X))
    assembler.emit(mips.i_type(0x31, a3, 13, V2_SESSION_DRAW_Y))
    assembler.emit(
        mips.i_type(0x23, a3, a3, V2_SPECIAL_CHOICE_NATIVE_ARG3)
    )
    assembler.emit(mips.jump(0x02, FONT_SELECTED_DRAW))
    assembler.emit(0)
    payload, relocations = assembler.build()
    return Fragment(
        V2_SPECIAL_CHOICE_SELECTED_CALLBACK,
        payload,
        relocations,
    )


def build_v2_global_selected_style() -> Fragment:
    """Shift register coordinates before a native selected two-pass body."""

    zero, v0, a0, t0, gp, ra = 0, 2, 4, 8, 28, 31
    assembler = mips.Assembler()
    emit_load_float(assembler, t0, 0, 1.0)
    assembler.emit(0)
    assembler.emit(mips.cop1(0x00, 21, 21, 0))
    emit_load_float(assembler, t0, 0, 2.0)
    assembler.emit(0)
    assembler.emit(mips.cop1(0x00, 20, 20, 0))
    assembler.emit(mips.i_type(0x23, gp, a0, -13696))
    assembler.emit(mips.i_type(0x0D, zero, v0, 0xFF80))
    assembler.emit(mips.r_type(ra, zero, zero, 0x08))
    assembler.emit(0)
    payload, relocations = assembler.build()
    return Fragment(V2_GLOBAL_SELECTED_STYLE, payload, relocations)


def build_v2_global_selected_record_draw() -> Fragment:
    """Move one inline selected shadow record below/right, then draw it."""

    a1, t0 = 5, 8
    assembler = mips.Assembler()
    emit_load_float(assembler, t0, 0, 1.0)
    assembler.emit(mips.i_type(0x31, a1, 1, 0))
    assembler.emit(0)
    assembler.emit(mips.cop1(0x00, 1, 1, 0))
    assembler.emit(mips.i_type(0x39, a1, 1, 0))
    emit_load_float(assembler, t0, 0, 2.0)
    assembler.emit(mips.i_type(0x31, a1, 1, 4))
    assembler.emit(0)
    assembler.emit(mips.cop1(0x00, 1, 1, 0))
    assembler.emit(mips.i_type(0x39, a1, 1, 4))
    assembler.emit(mips.jump(0x02, FONT_RECORD_DRAW))
    assembler.emit(0)
    payload, relocations = assembler.build()
    return Fragment(V2_GLOBAL_SELECTED_RECORD_DRAW, payload, relocations)


def build_v2_global_two_choice_draw() -> Fragment:
    """Route the fixed two-choice primitive through ordinary/selected draws."""

    zero, a0, a1 = 0, 4, 5
    t0 = 8
    s0, s1, s2 = 16, 17, 18
    gp, sp, ra = 28, 29, 31
    frame_size = 0x40
    saved_s2 = 0x30
    saved_s1 = 0x34
    saved_s0 = 0x38
    saved_ra = 0x3C

    assembler = mips.Assembler()
    assembler.emit(mips.i_type(0x09, sp, sp, -frame_size))
    assembler.emit(mips.i_type(0x2B, sp, s2, saved_s2))
    assembler.emit(mips.i_type(0x2B, sp, s1, saved_s1))
    assembler.emit(mips.i_type(0x2B, sp, s0, saved_s0))
    assembler.emit(mips.i_type(0x2B, sp, ra, saved_ra))
    assembler.emit(mips.r_type(a0, zero, s0, 0x21))
    assembler.emit(mips.r_type(a1, zero, s1, 0x21))
    mips.load_u32(assembler, s2, FONT_TWO_CHOICE_RECORDS)

    assembler.emit(mips.i_type(0x23, gp, a0, -13696))
    assembler.emit(mips.i_type(0x23, s0, a1, 0x1C))
    assembler.emit(mips.jump(0x03, FONT_SET_CONTEXT))
    assembler.emit(0)

    # Preserve the native order: record 1 at +0x10, then record 0 at +0x00.
    assembler.emit(mips.i_type(0x31, s2, 12, 0x10))
    assembler.emit(mips.i_type(0x31, s2, 13, 0x14))
    assembler.emit(mips.i_type(0x23, s2, a0, 0x18))
    assembler.emit(mips.i_type(0x09, zero, t0, 1))
    assembler.branch(0x04, s1, t0, "record_1_selected")
    assembler.emit(0)
    mips.load_u32(assembler, a1, 0xFF000000)
    assembler.emit(mips.jump(0x03, FONT_PLAIN_DRAW))
    assembler.emit(0)
    assembler.branch(0x04, zero, zero, "record_0")
    assembler.emit(0)

    assembler.label("record_1_selected")
    mips.load_u32(assembler, a1, 0xFF0000D4)
    assembler.emit(mips.jump(0x03, FONT_SELECTED_DRAW))
    assembler.emit(0)

    assembler.label("record_0")
    assembler.emit(mips.i_type(0x31, s2, 12, 0x00))
    assembler.emit(mips.i_type(0x31, s2, 13, 0x04))
    assembler.emit(mips.i_type(0x23, s2, a0, 0x08))
    assembler.branch(0x04, s1, zero, "record_0_selected")
    assembler.emit(0)
    mips.load_u32(assembler, a1, 0xFF000000)
    assembler.emit(mips.jump(0x03, FONT_PLAIN_DRAW))
    assembler.emit(0)
    assembler.branch(0x04, zero, zero, "restore")
    assembler.emit(0)

    assembler.label("record_0_selected")
    mips.load_u32(assembler, a1, 0xFF0000D4)
    assembler.emit(mips.jump(0x03, FONT_SELECTED_DRAW))
    assembler.emit(0)

    assembler.label("restore")
    assembler.emit(mips.i_type(0x23, gp, a0, -13696))
    assembler.emit(mips.i_type(0x23, gp, a1, -13692))
    assembler.emit(mips.jump(0x03, FONT_SET_CONTEXT))
    assembler.emit(0)
    assembler.emit(mips.i_type(0x23, sp, s2, saved_s2))
    assembler.emit(mips.i_type(0x23, sp, s1, saved_s1))
    assembler.emit(mips.i_type(0x23, sp, s0, saved_s0))
    assembler.emit(mips.i_type(0x23, sp, ra, saved_ra))
    assembler.emit(mips.r_type(ra, zero, zero, 0x08))
    assembler.emit(mips.i_type(0x09, sp, sp, frame_size))
    payload, relocations = assembler.build()
    return Fragment(V2_GLOBAL_TWO_CHOICE_DRAW, payload, relocations)


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
    mips.load_u32(assembler, t0, SPECIAL_CONTROLS_ON_TEXT)
    assembler.branch(0x04, t1, t0, "special_on")
    assembler.emit(0)
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

    assembler.label("special_on")
    mips.load_u32(
        assembler, t0, float_bits(SPECIAL_CONTROLS_ON_TARGET[0])
    )
    mips.load_u32(
        assembler, t1, float_bits(SPECIAL_CONTROLS_ON_TARGET[1])
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


def build_v2_quit_unselected_callback() -> Fragment:
    """Tail-call the original ordinary UI renderer for the C adapter."""

    assembler = mips.Assembler()
    assembler.emit(mips.jump(0x02, FONT_UI_DRAW))
    assembler.emit(0)
    payload, relocations = assembler.build()
    return Fragment(V2_QUIT_UNSELECTED_CALLBACK, payload, relocations)


def build_v2_wrapped_body_callback(
    symbol: str,
    box_x: float,
    box_y: float,
) -> Fragment:
    """Draw one wrapped body with caller-specific local coordinates."""

    zero, a0, a1, a2, a3 = 0, 4, 5, 6, 7
    t0 = 8
    sp, ra = 29, 31
    frame_size = 0x30
    saved_ra = 0x2C

    assembler = mips.Assembler()
    assembler.emit(mips.i_type(0x09, sp, sp, -frame_size))
    assembler.emit(mips.i_type(0x2B, sp, ra, saved_ra))
    mips.load_u32(assembler, t0, float_bits(box_x))
    assembler.emit(mips.i_type(0x2B, sp, t0, 0))
    mips.load_u32(assembler, t0, float_bits(box_y))
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
    return Fragment(symbol, payload, relocations)


def build_v2_wrapped_body_adapter(
    symbol: str,
    callback_symbol: str,
    box_x: float,
    box_y: float,
    box_width: int,
    box_height: int,
    line_height: float,
    line_limit: int,
) -> Fragment:
    """Copy and greedily wrap one exact caller's body at draw time."""

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
        mips.i_type(0x09, zero, a1, box_width)
    )
    assembler.emit(
        mips.i_type(0x09, zero, a2, line_limit)
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
    mips.load_u32(assembler, t0, float_bits(box_x))
    assembler.emit(mips.i_type(0x2B, sp, t0, V2_SESSION_BOX_X))
    mips.load_u32(assembler, t0, float_bits(box_y))
    assembler.emit(mips.i_type(0x2B, sp, t0, V2_SESSION_BOX_Y))
    mips.load_u32(assembler, t0, box_width)
    assembler.emit(mips.i_type(0x2B, sp, t0, V2_SESSION_BOX_WIDTH))
    mips.load_u32(assembler, t0, box_height)
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
            0x09, zero, t0, line_limit
        )
    )
    assembler.emit(mips.i_type(0x2B, sp, t0, V2_SESSION_LINE_LIMIT))
    emit_load_float(
        assembler, t0, 0, line_height
    )
    assembler.emit(mips.i_type(0x39, sp, 0, V2_SESSION_LINE_HEIGHT))
    assembler.load_symbol_word(
        t0, t0, 0x09, callback_symbol
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
    return Fragment(symbol, payload, relocations)


def build_v2_quit_body_callback() -> Fragment:
    """Draw the wrapped ss4 body with its NUN5-local record coordinates."""

    return build_v2_wrapped_body_callback(
        V2_QUIT_BODY_CALLBACK,
        QUIT_BODY_BOX_X,
        QUIT_BODY_BOX_Y,
    )


def build_v2_quit_body_adapter() -> Fragment:
    """Copy and greedily wrap the ss4 body only for its exact draw call."""

    return build_v2_wrapped_body_adapter(
        V2_QUIT_BODY_ADAPTER,
        V2_QUIT_BODY_CALLBACK,
        QUIT_BODY_BOX_X,
        QUIT_BODY_BOX_Y,
        QUIT_BODY_BOX_WIDTH,
        QUIT_BODY_BOX_HEIGHT,
        QUIT_BODY_LINE_HEIGHT,
        QUIT_BODY_LINE_LIMIT,
    )


def build_v2_special_controls_body_callback() -> Fragment:
    """Draw the wrapped ss1 body with its NUN5-local record coordinates."""

    return build_v2_wrapped_body_callback(
        V2_SPECIAL_CONTROLS_BODY_CALLBACK,
        SPECIAL_CONTROLS_BODY_BOX_X,
        SPECIAL_CONTROLS_BODY_BOX_Y,
    )


def build_v2_special_controls_body_adapter() -> Fragment:
    """Copy and wrap only the exact ss1 Special Controls body draw."""

    return build_v2_wrapped_body_adapter(
        V2_SPECIAL_CONTROLS_BODY_ADAPTER,
        V2_SPECIAL_CONTROLS_BODY_CALLBACK,
        SPECIAL_CONTROLS_BODY_BOX_X,
        SPECIAL_CONTROLS_BODY_BOX_Y,
        SPECIAL_CONTROLS_BODY_BOX_WIDTH,
        SPECIAL_CONTROLS_BODY_BOX_HEIGHT,
        SPECIAL_CONTROLS_BODY_LINE_HEIGHT,
        SPECIAL_CONTROLS_BODY_LINE_LIMIT,
    )


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


def build_v2_native_measure_callback() -> Fragment:
    """Call NA2's native tagged-text metric ABI from compiled C."""

    zero, a1 = 0, 5
    assembler = mips.Assembler()
    assembler.emit(mips.r_type(zero, zero, a1, 0x21))
    assembler.emit(mips.jump(0x02, FONT_MEASURE))
    assembler.emit(0)
    payload, relocations = assembler.build()
    return Fragment(V2_NATIVE_MEASURE_CALLBACK, payload, relocations)


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


def build_v2_practice_icon_draw_callback() -> Fragment:
    """Tail-call NA2's icon renderer with C-prepared integer/float arguments."""

    assembler = mips.Assembler()
    assembler.emit(mips.jump(0x02, FONT_ICON_DRAW))
    assembler.emit(0)
    payload, relocations = assembler.build()
    return Fragment(V2_PRACTICE_ICON_DRAW_CALLBACK, payload, relocations)


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


def build_v2_practice_adapter_entry() -> Fragment:
    """Capture Practice's live s3/s2 objects and f12 Y for compiled C."""

    a3, t0, t1 = 7, 8, 9
    s2, s3 = 18, 19
    sp, ra = 29, 31
    frame_size = 0x30
    saved_ra = 0x2C

    assembler = mips.Assembler()
    assembler.emit(mips.i_type(0x09, sp, sp, -frame_size))
    assembler.emit(mips.i_type(0x2B, sp, ra, saved_ra))
    assembler.emit(mips.r_type(s3, 0, a3, 0x21))
    # The PS2 EE EABI carries integer arguments five and six in t0/t1.
    assembler.emit(mips.r_type(s2, 0, t0, 0x21))
    assembler.emit(mips.mfc1(t1, 12))
    assembler.jump_symbol(0x03, V2_PRACTICE_ADAPTER_IMPL)
    assembler.emit(0)
    assembler.emit(mips.i_type(0x23, sp, ra, saved_ra))
    assembler.emit(mips.r_type(ra, 0, 0, 0x08))
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
    *,
    delay_word: int = 0,
) -> None:
    sp = 29
    assembler.emit(mips.i_type(0x23, sp, address_register, 0))
    assembler.emit(mips.i_type(0x23, sp, pointer_register, 4))
    assembler.emit(mips.i_type(0x09, sp, sp, 0x10))
    assembler.emit(mips.jump(0x02, resume_address))
    assembler.emit(delay_word)


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
    assembler.emit(
        mips.i_type(0x23, v1, v0, V2_SESSION_FLAGS)
    )
    assembler.emit(
        mips.i_type(0x0C, v0, v0, V2_FLAG_GLYPH_HEIGHT)
    )
    assembler.branch(0x04, v0, zero, "native_bottom")
    assembler.emit(0)
    assembler.emit(
        mips.i_type(0x31, v1, 1, V2_SESSION_GLYPH_HEIGHT)
    )
    assembler.emit(mips.cop1(0x00, 20, 0, 1))
    finish_v2_hook(
        assembler,
        v0,
        v1,
        V2_GLYPH_BOTTOM_RESUME,
        delay_word=V2_GLYPH_BOTTOM_DELAY,
    )
    assembler.label("native_bottom")
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


def build_numeric_format_bridge(symbol: str, format_address: int) -> Fragment:
    """Bridge typed C calls to NA2's native variadic ``sprintf`` ABI."""

    zero, a1, a2 = 0, 5, 6
    assembler = mips.Assembler()
    assembler.emit(mips.r_type(a1, zero, a2, 0x21))
    mips.load_u32(assembler, a1, format_address)
    assembler.emit(mips.jump(0x02, SPRINTF))
    assembler.emit(0)
    payload, relocations = assembler.build()
    return Fragment(symbol, payload, relocations)


def build_ninja_song_format_decimal() -> Fragment:
    """Retain the public helper used by accepted Ninja Song coverage."""

    return build_numeric_format_bridge(NUMERIC_FORMAT_DECIMAL, FORMAT_D)


def build_numeric_format_two_decimal() -> Fragment:
    return build_numeric_format_bridge(
        NUMERIC_FORMAT_TWO_DECIMAL,
        FORMAT_02D,
    )


def _hook_payload(
    value_register: int,
    buffer_offset: int,
    word_count: int,
    *,
    preserve_year: bool = False,
) -> bytes:
    zero, v0, a0, a1, s6, sp = 0, 2, 4, 5, 22, 29
    assembler = mips.Assembler()
    assembler.emit(mips.r_type(value_register, zero, a0, 0x2D))
    assembler.emit(mips.i_type(0x09, sp, a1, buffer_offset))
    assembler.emit(0)
    assembler.emit(0)
    if preserve_year:
        assembler.emit(mips.r_type(v0, zero, s6, 0x2D))
    while len(assembler.words) < word_count:
        assembler.emit(0)
    payload, relocations = assembler.build()
    if relocations:
        raise AssertionError("numeric hook unexpectedly emitted relocations")
    return payload


def numeric_hooks() -> tuple[NumericHook, ...]:
    save_specs = (
        (
            "call_eu_day_c_formatter_resume",
            10,
            0x0E660C,
            "0E0065942D200000040006249000A7270100082444E10D0C00000000",
            3,
            SAVE_LOAD_DAY,
            True,
            "Format the EU day in C and return the loaded year for s6.",
        ),
        (
            "call_shared_c_two_digit_month",
            20,
            0x0E6650,
            "2D2000002D282002020006249000A7272D40C00044E10D0C00000000",
            17,
            SAVE_LOAD_TWO,
            False,
            "Format the EU month through the shared C two-digit entry.",
        ),
        (
            "call_c_four_digit_year_formatter",
            30,
            0x0E6694,
            "2D2000002D28A002020006249000A7272D40C00044E10D0C00000000",
            22,
            SAVE_LOAD_YEAR,
            False,
            "Format the preserved four-digit year through C.",
        ),
        (
            "call_accepted_signed_99_hour_c",
            40,
            0x0E67A4,
            "2D2000002D28A002030006249000A7270200082444E10D0C00000000",
            21,
            SAVE_LOAD_HOUR,
            False,
            "Apply the accepted signed 99-hour cap and two-digit format in C.",
        ),
        (
            "call_shared_c_two_digit_minute",
            50,
            0x0E67E8,
            "2D2000002D282002020006249000A7272D40C00044E10D0C00000000",
            17,
            SAVE_LOAD_TWO,
            False,
            "Format minutes through the shared C two-digit entry.",
        ),
        (
            "call_shared_c_two_digit_second",
            60,
            0x0E682C,
            "2D2000002D28C002020006249000A7272D40C00044E10D0C00000000",
            22,
            SAVE_LOAD_TWO,
            False,
            "Format seconds through the shared C two-digit entry.",
        ),
    )
    hooks = [
        NumericHook(
            edit_id=edit_id,
            patch_id="i__localization__font__numeric_formatting__save_load",
            order=order,
            target_id="na2_elf",
            offset=offset,
            expected_hex=expected,
            replacement_hex=_hook_payload(
                value_register,
                0x90,
                7,
                preserve_year=preserve_year,
            ).hex().upper(),
            relocation_offset=8,
            symbol=symbol,
            reason=reason,
        )
        for (
            edit_id,
            order,
            offset,
            expected,
            value_register,
            symbol,
            preserve_year,
            reason,
        ) in save_specs
    ]
    hooks.append(
        NumericHook(
            edit_id="call_ordinary_battle_settings_time_c",
            patch_id="i__localization__font__numeric_formatting__battle_settings",
            order=10,
            target_id="na2_btl",
            offset=0x1CC3D8,
            expected_hex=(
                "2D200000030006246000A7270100082444E10D0C00000000"
            ),
            replacement_hex=_hook_payload(5, 0x60, 6).hex().upper(),
            relocation_offset=8,
            symbol=BATTLE_SETTINGS_TIME,
            reason=(
                "Route only ordinary Battle Settings Time through C while "
                "preserving the separate 100/infinity branch."
            ),
        )
    )
    return tuple(hooks)






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
        *build_v2_c_sources(),
        build_v2_title_callback(),
        build_v2_pause_list_callback(),
        build_v2_pause_list_selected_callback(),
        build_v2_quit_choices_scope_entry(),
        build_v2_quit_choices_scope_entry(
            V2_CHARACTER_CHOICES_SCOPE,
            V2_CHARACTER_SCOPE_ENTER,
        ),
        build_v2_quit_selected_entry(),
        build_v2_plain_space(),
        build_v2_newline_advance(),
        build_v2_right_edge(),
        build_v2_half_space(),
        build_v2_special_choice_selected_callback(),
        build_v2_global_selected_style(),
        build_v2_global_selected_record_draw(),
        build_v2_glyph_advance(),
    )
    symbols = [fragment.symbol for fragment in result]
    if len(symbols) != len(set(symbols)):
        raise ValueError("generated v2 fragments export duplicate symbols")
    return result


def numeric_fragments() -> tuple[Fragment, ...]:
    result = (
        *build_numeric_c_core(),
        build_ninja_song_format_decimal(),
        build_numeric_format_two_decimal(),
    )
    symbols = [fragment.symbol for fragment in result]
    if len(symbols) != len(set(symbols)):
        raise ValueError("generated numeric fragments export duplicate symbols")
    return result




def main() -> None:
    paths = load_paths(REPOSITORY)
    selection = catalog.load_selection(
        paths.path("builder", "catalog"),
        paths.path("builder", "configurations", "dev.json"),
    )
    declaration = catalog.load_runtime_package(
        selection,
        "localization",
        paths.path("builder", "catalog", "targets.tsv"),
        REPOSITORY,
        "localization.runtime_injector",
    )
    v2 = v2_fragments()
    expected = (*v2[:-2], *numeric_fragments(), *v2[-2:])
    actual_by_symbol = {
        fragment.symbol: fragment for fragment in declaration.fragments
    }
    missing = [
        fragment.symbol
        for fragment in expected
        if fragment.symbol not in actual_by_symbol
    ]
    if missing:
        raise ValueError(f"runtime-injector is missing Font fragments: {missing}")
    for generated in expected:
        actual = actual_by_symbol[generated.symbol]
        actual_relocations = tuple(
            sorted(
                (
                    relocation.offset,
                    relocation.kind,
                    relocation.symbol,
                    relocation.addend,
                )
                for relocation in actual.relocations
            )
        )
        generated_relocations = tuple(
            sorted(
                (
                    relocation.offset,
                    relocation.kind,
                    relocation.symbol,
                    relocation.addend,
                )
                for relocation in generated.relocations
            )
        )
        if (
            actual.kind != generated.kind
            or actual.alignment != generated.alignment
            or actual.payload != generated.payload
            or actual_relocations != generated_relocations
            or actual.init != generated.init
        ):
            raise ValueError(
                f"runtime-injector fragment differs: {actual.symbol}"
            )
    print(
        f"verified\t{len(expected)} reconstructed Font fragments "
        f"within {len(declaration.fragments)} compiled/static declarations"
    )


if __name__ == "__main__":
    main()
