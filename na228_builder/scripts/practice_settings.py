from __future__ import annotations

import struct
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from ..payload_builder.operations import PayloadFragment, PayloadRelocation
from .battle_settings_runtime import (
    PRACTICE_SETTINGS_PATH,
    ULTIMATE_JUTSU_NATIVE_MODE_COUNT,
    extra_hit_default,
    shadowblur_default,
    sub_active_frames_default,
    substitution_default,
    support_default,
    shared_setting_enabled,
    ultimate_jutsu_default,
    xdash_chakra_cost_option_default,
)
from .native_settings_defaults import practice_configured_row_defaults

if TYPE_CHECKING:
    from .catalog import CatalogSelection


ROW_SECTION_PLAYER = 0
ROW_SECTION_OPPONENT = 1
ROW_LOCAL_CUSTOM = 0xFFFFFFFF

ROW_AVAILABLE_ALWAYS = 0
ROW_AVAILABLE_STATUS_COM = 1
ROW_AVAILABLE_STATUS_ACTION = 2
ROW_AVAILABLE_STATUS_NOT_MANUAL = 3

ROW_FLAG_LABEL_SLOT = 0x01
ROW_FLAG_HELP_SLOT = 0x02
ROW_FLAG_HELP_BY_VALUE = 0x04
ROW_FLAG_VALUES_SLOT = 0x08
ROW_FLAG_STRENGTH_LIMIT = 0x10
ROW_FLAG_CUSTOM_SUBSTITUTION = 0x20
ROW_FLAG_CUSTOM_ULTIMATE_JUTSU = 0x40
ROW_FLAG_CUSTOM_SHADOWBLUR = 0x80
ROW_FLAG_CUSTOM_EXTRA_HIT = 0x100
ROW_FLAG_CUSTOM_SUB_ACTIVE_FRAMES = 0x200
ROW_FLAG_CUSTOM_XDASH_CHAKRA_COST = 0x400
ROW_FLAG_CUSTOM_SUPPORT = 0x800

NATIVE_LABEL_TABLE = 0x008BE6C0
NATIVE_HELP_TABLE = 0x008BEF70
NATIVE_STATUS_HELP_TABLE = 0x008BF350
NATIVE_VALUE_TABLE = 0x008BF380

SUBSTITUTION_ROW_ID = 17
SHADOWBLUR_ROW_ID = 18
EXTRA_HIT_ROW_ID = 19
SUB_ACTIVE_FRAMES_ROW_ID = 20
XDASH_CHAKRA_COST_ROW_ID = 21
SUPPORT_ROW_ID = 22
SCHEMA_HEADER_SIZE = 76
ROW_FIELD_COUNT = 10
ROW_SIZE = ROW_FIELD_COUNT * 4
LABEL_REFERENCE_FIELD = 3
HELP_REFERENCE_FIELD = 4
VALUE_REFERENCE_FIELD = 5
SUBSTITUTION_MODE_LABELS = (
    "substitution_gauge_mode_chakra_label",
    "substitution_gauge_mode_gauge_label",
    "substitution_gauge_mode_free_label",
)
TOGGLE_LABELS = (
    "battle_settings_off_label",
    "battle_settings_on_label",
)
CUSTOM_ROW_RESOURCES = {
    SUBSTITUTION_ROW_ID: (
        "battle_settings_substitution_label",
        "battle_settings_substitution_help",
        "substitution",
    ),
    SHADOWBLUR_ROW_ID: (
        "battle_settings_shadowblur_label",
        "battle_settings_shadowblur_help",
        "toggle",
    ),
    EXTRA_HIT_ROW_ID: (
        "battle_settings_extra_hit_label",
        "battle_settings_extra_hit_help",
        "toggle",
    ),
    SUB_ACTIVE_FRAMES_ROW_ID: (
        "battle_settings_sub_active_frames_label",
        "battle_settings_sub_active_frames_help",
        "sub_active_frames",
    ),
    XDASH_CHAKRA_COST_ROW_ID: (
        "battle_settings_xdash_chakra_cost_label",
        "battle_settings_xdash_chakra_cost_help",
        "xdash_chakra_cost",
    ),
    SUPPORT_ROW_ID: (
        "battle_settings_support_label",
        "battle_settings_support_help",
        "toggle",
    ),
}

@dataclass(frozen=True)
class PracticeRow:
    row_id: int
    section: int
    local_offset: int
    option_count: int
    default_value: int
    availability: int = ROW_AVAILABLE_ALWAYS
    flags: int = (
        ROW_FLAG_LABEL_SLOT | ROW_FLAG_HELP_SLOT | ROW_FLAG_VALUES_SLOT
    )

    def encoded_fields(self) -> tuple[int, ...]:
        help_reference = (
            NATIVE_STATUS_HELP_TABLE
            if self.flags & ROW_FLAG_HELP_BY_VALUE
            else NATIVE_HELP_TABLE + self.row_id * 4
        )
        return (
            self.row_id,
            self.section,
            self.local_offset,
            NATIVE_LABEL_TABLE + self.row_id * 4,
            help_reference,
            NATIVE_VALUE_TABLE + self.row_id * 4,
            self.option_count,
            self.default_value,
            self.availability,
            self.flags,
        )


NATIVE_ROWS = {
    0: PracticeRow(0, ROW_SECTION_PLAYER, 0x6C, 3, 0),
    1: PracticeRow(1, ROW_SECTION_PLAYER, 0x70, 2, 0),
    2: PracticeRow(2, ROW_SECTION_PLAYER, 0x74, 2, 0),
    3: PracticeRow(3, ROW_SECTION_PLAYER, 0x78, 6, 2),
    4: PracticeRow(4, ROW_SECTION_PLAYER, 0x7C, 2, 0),
    5: PracticeRow(5, ROW_SECTION_PLAYER, 0x80, 4, 2),
    6: PracticeRow(6, ROW_SECTION_PLAYER, 0x84, 2, 1),
    7: PracticeRow(7, ROW_SECTION_PLAYER, 0x88, 2, 1),
    8: PracticeRow(8, ROW_SECTION_PLAYER, 0x8C, 2, 1),
    9: PracticeRow(
        9,
        ROW_SECTION_OPPONENT,
        0x90,
        5,
        2,
        flags=(
            ROW_FLAG_LABEL_SLOT
            | ROW_FLAG_HELP_BY_VALUE
            | ROW_FLAG_VALUES_SLOT
        ),
    ),
    10: PracticeRow(
        10,
        ROW_SECTION_OPPONENT,
        0x94,
        6,
        2,
        availability=ROW_AVAILABLE_STATUS_COM,
        flags=(
            ROW_FLAG_LABEL_SLOT
            | ROW_FLAG_HELP_SLOT
            | ROW_FLAG_VALUES_SLOT
            | ROW_FLAG_STRENGTH_LIMIT
        ),
    ),
    11: PracticeRow(
        11,
        ROW_SECTION_OPPONENT,
        0x98,
        7,
        0,
        availability=ROW_AVAILABLE_STATUS_ACTION,
    ),
    12: PracticeRow(
        12,
        ROW_SECTION_OPPONENT,
        0x9C,
        2,
        0,
        availability=ROW_AVAILABLE_STATUS_ACTION,
    ),
    13: PracticeRow(
        13,
        ROW_SECTION_OPPONENT,
        0xA0,
        2,
        0,
        availability=ROW_AVAILABLE_STATUS_ACTION,
    ),
    14: PracticeRow(
        14,
        ROW_SECTION_OPPONENT,
        0xA4,
        2,
        0,
        availability=ROW_AVAILABLE_STATUS_COM,
    ),
    15: PracticeRow(
        15,
        ROW_SECTION_OPPONENT,
        0xA8,
        3,
        1,
        availability=ROW_AVAILABLE_STATUS_NOT_MANUAL,
    ),
    16: PracticeRow(
        16,
        ROW_SECTION_OPPONENT,
        0xAC,
        2,
        0,
        availability=ROW_AVAILABLE_STATUS_NOT_MANUAL,
    ),
}


def _node_enabled(selection: CatalogSelection, path: tuple[str, ...]) -> bool:
    matches = [node for node in selection.nodes if node.path == path]
    if len(matches) != 1:
        raise ValueError(f"Catalog selection has no unique {'.'.join(path)} node")
    return matches[0].enabled


def _configured_value(selection: CatalogSelection, path: tuple[str, ...]):
    matches = [node for node in selection.nodes if node.path == path]
    if len(matches) != 1:
        raise ValueError(f"Catalog selection has no unique {'.'.join(path)} node")
    node = matches[0]
    return node.configured_value if node.has_configured_value else None


def _active_rows(selection: CatalogSelection) -> tuple[PracticeRow, ...]:
    configured_defaults = practice_configured_row_defaults(selection)

    def native_row(row_id: int) -> PracticeRow:
        row = NATIVE_ROWS[row_id]
        if row_id not in configured_defaults:
            return row
        return replace(row, default_value=configured_defaults[row_id])

    general_fields = (
        (0, "health"),
        (1, "chakra"),
        (2, "linked_attack"),
    )
    general_path = PRACTICE_SETTINGS_PATH + ("general_settings",)
    rows = [
        native_row(row_id)
        for row_id, field in general_fields
        if _configured_value(selection, general_path + (field,)) is not False
    ]
    linked_mode_path = PRACTICE_SETTINGS_PATH + (
        "general_settings",
        "linked_mode",
    )
    if _configured_value(selection, linked_mode_path) is not False:
        rows.append(native_row(4))
    trailing_general_fields = (
        (5, "items"),
        (6, "commands"),
        (7, "damage"),
        (8, "guide_ninja_sound"),
    )
    rows.extend(
        native_row(row_id)
        for row_id, field in trailing_general_fields
        if _configured_value(selection, general_path + (field,)) is not False
    )

    custom_rows = {
        "ultimate_jutsu": lambda: replace(
            native_row(3),
            option_count=ULTIMATE_JUTSU_NATIVE_MODE_COUNT + 2,
            default_value=ultimate_jutsu_default(selection),
            flags=native_row(3).flags | ROW_FLAG_CUSTOM_ULTIMATE_JUTSU,
        ),
        "shadowblur": lambda: PracticeRow(
            SHADOWBLUR_ROW_ID, ROW_SECTION_PLAYER, ROW_LOCAL_CUSTOM, 2,
            shadowblur_default(selection), flags=ROW_FLAG_CUSTOM_SHADOWBLUR,
        ),
        "extra_hit": lambda: PracticeRow(
            EXTRA_HIT_ROW_ID, ROW_SECTION_PLAYER, ROW_LOCAL_CUSTOM, 2,
            extra_hit_default(selection), flags=ROW_FLAG_CUSTOM_EXTRA_HIT,
        ),
        "sub_active_frames": lambda: PracticeRow(
            SUB_ACTIVE_FRAMES_ROW_ID, ROW_SECTION_PLAYER, ROW_LOCAL_CUSTOM, 17,
            sub_active_frames_default(selection),
            flags=ROW_FLAG_CUSTOM_SUB_ACTIVE_FRAMES,
        ),
        "xdash_chakra_cost": lambda: PracticeRow(
            XDASH_CHAKRA_COST_ROW_ID, ROW_SECTION_PLAYER, ROW_LOCAL_CUSTOM, 21,
            xdash_chakra_cost_option_default(selection),
            flags=ROW_FLAG_CUSTOM_XDASH_CHAKRA_COST,
        ),
        "support": lambda: PracticeRow(
            SUPPORT_ROW_ID, ROW_SECTION_PLAYER, ROW_LOCAL_CUSTOM, 2,
            support_default(selection), flags=ROW_FLAG_CUSTOM_SUPPORT,
        ),
        "substitution": lambda: PracticeRow(
            SUBSTITUTION_ROW_ID, ROW_SECTION_PLAYER, ROW_LOCAL_CUSTOM, 3,
            substitution_default(selection),
            flags=ROW_FLAG_CUSTOM_SUBSTITUTION,
        ),
    }
    for node in selection.nodes:
        if (
            len(node.path) == 5
            and node.path[:4] == ("features", "settings", "in_game", "shared")
            and node.enabled
            and node.path[4] in custom_rows
        ):
            rows.append(custom_rows[node.path[4]]())
    opponent_fields = (
        (9, "status"),
        (10, "strength"),
        (11, "attack"),
        (12, "guard"),
        (13, "move"),
        (14, "substitution_jutsu"),
        (15, "linked_attack"),
        (16, "extra_hit_counter"),
    )
    opponent_path = PRACTICE_SETTINGS_PATH + ("opponent_settings",)
    rows.extend(
        native_row(row_id)
        for row_id, field in opponent_fields
        if _configured_value(selection, opponent_path + (field,)) is not False
    )
    return tuple(rows)


def practice_settings_fragment(
    selection: CatalogSelection,
    *,
    owner: str,
    symbol: str = "practice_settings_schema",
) -> PayloadFragment | None:
    if not _node_enabled(selection, PRACTICE_SETTINGS_PATH):
        return None

    rows = _active_rows(selection)
    player_count = sum(row.section == ROW_SECTION_PLAYER for row in rows)
    opponent_count = sum(row.section == ROW_SECTION_OPPONENT for row in rows)
    payload = bytearray(
        struct.pack(
            "<19I",
            len(rows),
            player_count,
            opponent_count,
            *([0] * 16),
        )
    )
    relocations: list[PayloadRelocation] = []
    appended_tables_offset = SCHEMA_HEADER_SIZE + len(rows) * ROW_SIZE
    substitution_value_table_offset = appended_tables_offset
    toggle_value_table_offset = substitution_value_table_offset + (
        len(SUBSTITUTION_MODE_LABELS) * 4
    )
    sub_active_frames_value_table_offset = toggle_value_table_offset + (
        len(TOGGLE_LABELS) * 4
    )
    xdash_chakra_cost_value_table_offset = (
        sub_active_frames_value_table_offset + 17 * 4
    )
    text_pool_offset = xdash_chakra_cost_value_table_offset + 21 * 4
    value_table_offsets = {
        "substitution": substitution_value_table_offset,
        "toggle": toggle_value_table_offset,
        "sub_active_frames": sub_active_frames_value_table_offset,
        "xdash_chakra_cost": xdash_chakra_cost_value_table_offset,
    }
    header_symbols = {
        "substitution": (
            (12, "substitution_gauge_mode_get"),
            (16, "substitution_gauge_mode_set"),
        ),
        "ultimate_jutsu": (
            (20, "ultimate_jutsu_mode_get"),
            (24, "ultimate_jutsu_mode_set"),
            (28, "ultimate_jutsu_no_contest_label"),
            (32, "ultimate_jutsu_no_hud_label"),
        ),
        "shadowblur": ((36, "shadowblur_get"), (40, "shadowblur_set")),
        "extra_hit": ((44, "extra_hit_get"), (48, "extra_hit_set")),
        "sub_active_frames": (
            (52, "sub_active_frames_get"),
            (56, "sub_active_frames_set"),
        ),
        "xdash_chakra_cost": (
            (60, "xdash_chakra_cost_option_get"),
            (64, "xdash_chakra_cost_option_set"),
        ),
        "support": ((68, "support_get"), (72, "support_set")),
    }
    for field, symbols in header_symbols.items():
        if shared_setting_enabled(selection, field):
            relocations.extend(
                PayloadRelocation(offset=offset, kind="abs32", symbol=name)
                for offset, name in symbols
            )

    for index, row in enumerate(rows):
        row_offset = SCHEMA_HEADER_SIZE + index * ROW_SIZE
        if row.row_id in CUSTOM_ROW_RESOURCES:
            fields = list(row.encoded_fields())
            fields[LABEL_REFERENCE_FIELD] = 0
            fields[HELP_REFERENCE_FIELD] = 0
            fields[VALUE_REFERENCE_FIELD] = 0
            label_symbol, help_symbol, value_table = CUSTOM_ROW_RESOURCES[
                row.row_id
            ]
            payload.extend(struct.pack("<10I", *fields))
            relocations.extend(
                (
                    PayloadRelocation(
                        offset=row_offset + LABEL_REFERENCE_FIELD * 4,
                        kind="abs32",
                        symbol=label_symbol,
                    ),
                    PayloadRelocation(
                        offset=row_offset + HELP_REFERENCE_FIELD * 4,
                        kind="abs32",
                        symbol=help_symbol,
                    ),
                    PayloadRelocation(
                        offset=row_offset + VALUE_REFERENCE_FIELD * 4,
                        kind="abs32",
                        symbol=symbol,
                        addend=value_table_offsets[value_table],
                    ),
                )
            )
        else:
            payload.extend(struct.pack("<10I", *row.encoded_fields()))

    if any(row.row_id in CUSTOM_ROW_RESOURCES for row in rows):
        for label in SUBSTITUTION_MODE_LABELS:
            if shared_setting_enabled(selection, "substitution"):
                relocations.append(
                    PayloadRelocation(
                        offset=len(payload),
                        kind="abs32",
                        symbol=label,
                    )
                )
            payload.extend(b"\0" * 4)

        for label in TOGGLE_LABELS:
            relocations.append(
                PayloadRelocation(
                    offset=len(payload),
                    kind="abs32",
                    symbol=label,
                )
            )
            payload.extend(b"\0" * 4)

        text_pool = bytearray()
        next_text_offset = text_pool_offset
        for value in range(17):
            text = f"{value}".encode("ascii") + b"\0"
            relocations.append(
                PayloadRelocation(
                    offset=len(payload),
                    kind="abs32",
                    symbol=symbol,
                    addend=next_text_offset,
                )
            )
            payload.extend(b"\0" * 4)
            text_pool.extend(text)
            next_text_offset += len(text)
        for value in range(0, 101, 5):
            text = f"{value}%".encode("ascii") + b"\0"
            relocations.append(
                PayloadRelocation(
                    offset=len(payload),
                    kind="abs32",
                    symbol=symbol,
                    addend=next_text_offset,
                )
            )
            payload.extend(b"\0" * 4)
            text_pool.extend(text)
            next_text_offset += len(text)
        payload.extend(text_pool)

    return PayloadFragment(
        owner=owner,
        symbol=symbol,
        kind="rodata",
        alignment=4,
        payload=bytes(payload),
        relocations=tuple(relocations),
    )
