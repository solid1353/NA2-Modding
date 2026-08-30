from __future__ import annotations

import struct
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from ..payload_builder.operations import PayloadFragment, PayloadRelocation
from .battle_settings_runtime import (
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
from .native_settings_defaults import (
    BATTLE_SETTINGS_PATH,
    battle_configured_row_defaults,
)

if TYPE_CHECKING:
    from .catalog import CatalogSelection


ROW_LOCAL_CUSTOM = 0xFFFFFFFF
ROW_FLAG_LABEL_SLOT = 0x01
ROW_FLAG_HELP_SLOT = 0x02
ROW_FLAG_VALUES_SLOT = 0x04
ROW_FLAG_CUSTOM_SUBSTITUTION = 0x08
ROW_FLAG_DIFFICULTY_LIMIT = 0x10
ROW_FLAG_TIME = 0x20
ROW_FLAG_HANDICAP = 0x40
ROW_FLAG_ULTIMATE_JUTSU = 0x80
ROW_FLAG_CUSTOM_ULTIMATE_JUTSU = 0x100
ROW_FLAG_CUSTOM_SHADOWBLUR = 0x200
ROW_FLAG_CUSTOM_EXTRA_HIT = 0x400
ROW_FLAG_CUSTOM_SUB_ACTIVE_FRAMES = 0x800
ROW_FLAG_CUSTOM_XDASH_CHAKRA_COST = 0x1000
ROW_FLAG_CUSTOM_SUPPORT = 0x2000

NATIVE_LABEL_TABLE = 0x008BE160
NATIVE_HELP_TABLE = 0x008BE560
NATIVE_VALUE_TABLE = 0x008BE5C0
SUBSTITUTION_ROW_ID = 6
SHADOWBLUR_ROW_ID = 7
EXTRA_HIT_ROW_ID = 8
SUB_ACTIVE_FRAMES_ROW_ID = 9
XDASH_CHAKRA_COST_ROW_ID = 10
SUPPORT_ROW_ID = 11
SCHEMA_HEADER_SIZE = 68
ROW_FIELD_COUNT = 8
ROW_SIZE = ROW_FIELD_COUNT * 4
LABEL_REFERENCE_FIELD = 2
HELP_REFERENCE_FIELD = 3
VALUE_REFERENCE_FIELD = 4
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
class BattleRow:
    row_id: int
    local_offset: int
    option_count: int
    flags: int
    default_value: int = 0

    def encoded_fields(self) -> tuple[int, ...]:
        return (
            self.row_id,
            self.local_offset,
            NATIVE_LABEL_TABLE + self.row_id * 4,
            NATIVE_HELP_TABLE + self.row_id * 4,
            NATIVE_VALUE_TABLE + self.row_id * 4,
            self.option_count,
            self.default_value,
            self.flags,
        )


NATIVE_ROWS = {
    0: BattleRow(
        0,
        0x30,
        11,
        ROW_FLAG_LABEL_SLOT | ROW_FLAG_HELP_SLOT | ROW_FLAG_TIME,
        9,
    ),
    1: BattleRow(
        1,
        0x34,
        6,
        ROW_FLAG_LABEL_SLOT
        | ROW_FLAG_HELP_SLOT
        | ROW_FLAG_VALUES_SLOT
        | ROW_FLAG_DIFFICULTY_LIMIT,
        2,
    ),
    2: BattleRow(
        2,
        0x38,
        4,
        ROW_FLAG_LABEL_SLOT | ROW_FLAG_HELP_SLOT | ROW_FLAG_VALUES_SLOT,
        2,
    ),
    3: BattleRow(
        3,
        0x3C,
        2,
        ROW_FLAG_LABEL_SLOT | ROW_FLAG_HELP_SLOT | ROW_FLAG_VALUES_SLOT,
    ),
    4: BattleRow(
        4,
        0x40,
        6,
        ROW_FLAG_LABEL_SLOT
        | ROW_FLAG_HELP_SLOT
        | ROW_FLAG_VALUES_SLOT
        | ROW_FLAG_ULTIMATE_JUTSU,
        2,
    ),
    5: BattleRow(
        5,
        0x44,
        11,
        ROW_FLAG_LABEL_SLOT | ROW_FLAG_HELP_SLOT | ROW_FLAG_HANDICAP,
        5,
    ),
}


def _selected_node(selection: CatalogSelection, path: tuple[str, ...]):
    matches = [node for node in selection.nodes if node.path == path]
    if len(matches) != 1:
        raise ValueError(f"Catalog selection has no unique {'.'.join(path)} node")
    return matches[0]


def _configured_value(selection: CatalogSelection, path: tuple[str, ...]):
    node = _selected_node(selection, path)
    return node.configured_value if node.has_configured_value else None


def _active_rows(selection: CatalogSelection) -> tuple[BattleRow, ...]:
    configured_defaults = battle_configured_row_defaults(selection)

    def native_row(row_id: int) -> BattleRow:
        row = NATIVE_ROWS[row_id]
        if row_id not in configured_defaults:
            return row
        return replace(row, default_value=configured_defaults[row_id])

    native_fields = (
        (0, "time"),
        (1, "difficulty"),
        (2, "items"),
        (3, "chakra"),
        (5, "handicap"),
    )
    rows = [
        native_row(row_id)
        for row_id, field in native_fields
        if _configured_value(selection, BATTLE_SETTINGS_PATH + (field,))
        is not False
    ]
    custom_rows = {
        "ultimate_jutsu": lambda: replace(
            native_row(4),
            option_count=ULTIMATE_JUTSU_NATIVE_MODE_COUNT + 2,
            default_value=ultimate_jutsu_default(selection),
            flags=native_row(4).flags | ROW_FLAG_CUSTOM_ULTIMATE_JUTSU,
        ),
        "shadowblur": lambda: BattleRow(
            SHADOWBLUR_ROW_ID, ROW_LOCAL_CUSTOM, 2,
            ROW_FLAG_CUSTOM_SHADOWBLUR, shadowblur_default(selection),
        ),
        "extra_hit": lambda: BattleRow(
            EXTRA_HIT_ROW_ID, ROW_LOCAL_CUSTOM, 2,
            ROW_FLAG_CUSTOM_EXTRA_HIT, extra_hit_default(selection),
        ),
        "sub_active_frames": lambda: BattleRow(
            SUB_ACTIVE_FRAMES_ROW_ID, ROW_LOCAL_CUSTOM, 17,
            ROW_FLAG_CUSTOM_SUB_ACTIVE_FRAMES,
            sub_active_frames_default(selection),
        ),
        "xdash_chakra_cost": lambda: BattleRow(
            XDASH_CHAKRA_COST_ROW_ID, ROW_LOCAL_CUSTOM, 21,
            ROW_FLAG_CUSTOM_XDASH_CHAKRA_COST,
            xdash_chakra_cost_option_default(selection),
        ),
        "support": lambda: BattleRow(
            SUPPORT_ROW_ID, ROW_LOCAL_CUSTOM, 2,
            ROW_FLAG_CUSTOM_SUPPORT, support_default(selection),
        ),
        "substitution": lambda: BattleRow(
            SUBSTITUTION_ROW_ID, ROW_LOCAL_CUSTOM, 3,
            ROW_FLAG_CUSTOM_SUBSTITUTION, substitution_default(selection),
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
    return tuple(rows)


def battle_settings_fragment(
    selection: CatalogSelection,
    *,
    owner: str,
    symbol: str = "battle_settings_schema",
) -> PayloadFragment | None:
    battle_settings = _selected_node(selection, BATTLE_SETTINGS_PATH)
    if not battle_settings.enabled:
        return None

    rows = _active_rows(selection)
    payload = bytearray(struct.pack("<17I", len(rows), *([0] * 16)))
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
            (4, "substitution_gauge_mode_get"),
            (8, "substitution_gauge_mode_set"),
        ),
        "ultimate_jutsu": (
            (12, "ultimate_jutsu_mode_get"),
            (16, "ultimate_jutsu_mode_set"),
            (20, "ultimate_jutsu_no_contest_label"),
            (24, "ultimate_jutsu_no_hud_label"),
        ),
        "shadowblur": ((28, "shadowblur_get"), (32, "shadowblur_set")),
        "extra_hit": ((36, "extra_hit_get"), (40, "extra_hit_set")),
        "sub_active_frames": (
            (44, "sub_active_frames_get"),
            (48, "sub_active_frames_set"),
        ),
        "xdash_chakra_cost": (
            (52, "xdash_chakra_cost_option_get"),
            (56, "xdash_chakra_cost_option_set"),
        ),
        "support": ((60, "support_get"), (64, "support_set")),
    }
    for field, symbols in header_symbols.items():
        if shared_setting_enabled(selection, field):
            relocations.extend(
                PayloadRelocation(offset=offset, kind="abs32", symbol=name)
                for offset, name in symbols
            )
    for index, row in enumerate(rows):
        fields = list(row.encoded_fields())
        if row.row_id in CUSTOM_ROW_RESOURCES:
            fields[LABEL_REFERENCE_FIELD] = 0
            fields[HELP_REFERENCE_FIELD] = 0
            fields[VALUE_REFERENCE_FIELD] = 0
            row_offset = SCHEMA_HEADER_SIZE + index * ROW_SIZE
            label_symbol, help_symbol, value_table = CUSTOM_ROW_RESOURCES[
                row.row_id
            ]
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
        payload.extend(struct.pack("<8I", *fields))

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
