from __future__ import annotations

import struct
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from ..payload_builder.operations import PayloadFragment, PayloadRelocation
from .menu_options import items_mode_option, MenuOption
from .menu_pages import build_menu_pages, append_row_extensions, page_resource_fragments
from .battle_settings_runtime import (
    BATTLE_MECHANICS_PATH,
    CHAKRA_OPTION_COUNT,
    CHAKRA_REGEN_LABELS,
    CHAKRA_STATIC_LABELS,
    SUB_ACTIVE_FRAMES_LABELS,
    SUPPORT_LABELS,
    ULTIMATE_JUTSU_NATIVE_MODE_COUNT,
    chakra_default,
    EXTRA_HIT_LABELS,
    extra_hit_default,
    shadowblur_default,
    sub_active_frames_default,
    substitution_default,
    support_default,
    battle_mechanic_enabled,
    ultimate_jutsu_default,
    xdash_chakra_cost_option_default,
)
from .native_settings_defaults import (
    BATTLE_SETTINGS_PATH,
    BATTLE_ROW_IDS,
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
ROW_FLAG_CUSTOM_CHAKRA = 0x8000

NATIVE_LABEL_TABLE = 0x008BE160
NATIVE_HELP_TABLE = 0x008BE560
NATIVE_VALUE_TABLE = 0x008BE5C0
SUBSTITUTION_ROW_ID = 6
SHADOWBLUR_ROW_ID = 7
EXTRA_HIT_ROW_ID = 8
SUB_ACTIVE_FRAMES_ROW_ID = 9
XDASH_CHAKRA_COST_ROW_ID = 10
SUPPORT_ROW_ID = 11
SCHEMA_HEADER_SIZE = 80
PAGE_FIELD_COUNT = 7
PAGE_SIZE = PAGE_FIELD_COUNT * 4
ROW_FIELD_COUNT = 10
ROW_SIZE = ROW_FIELD_COUNT * 4
LABEL_REFERENCE_FIELD = 2
HELP_REFERENCE_FIELD = 3
VALUE_REFERENCE_FIELD = 4
SUBSTITUTION_MODE_LABELS = (
    None,  # Supplied by the value-linked child page.
    None,  # Supplied by the value-linked child page.
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
        "extra_hit",
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
        "support",
    ),
}

@dataclass(frozen=True)
class BattleRow:
    row_id: int
    local_offset: int
    option_count: int
    flags: int
    default_value: int = 0

    value_pages: tuple[tuple[int, int, str | None], ...] = ()
    runtime_option: MenuOption | None = None
    label: str | None = None
    help: str | None = None

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
            0,
            0,
        )


@dataclass(frozen=True)
class BattlePage:
    rows: tuple[BattleRow, ...]
    primary_row_count: int
    secondary_row_count: int
    parent_page: int = 0
    parent_row: int = 0
    heading_symbol: str | None = None
    heading_text: str | None = None


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


def _active_pages(selection: CatalogSelection) -> tuple[BattlePage, ...]:
    configured_defaults = battle_configured_row_defaults(selection)

    def native_row(row_id: int) -> BattleRow:
        row = NATIVE_ROWS[row_id]
        if row_id not in configured_defaults:
            return row
        return replace(row, default_value=configured_defaults[row_id])

    custom_rows = {
        "items": lambda: BattleRow(
            2, ROW_LOCAL_CUSTOM, 5, 0, items_mode_option(selection).default,
            runtime_option=items_mode_option(selection),
        ),
        "chakra": lambda: replace(
            native_row(3),
            local_offset=ROW_LOCAL_CUSTOM,
            option_count=CHAKRA_OPTION_COUNT,
            default_value=chakra_default(selection),
            flags=(native_row(3).flags & ~ROW_FLAG_VALUES_SLOT)
            | ROW_FLAG_CUSTOM_CHAKRA,
        ),
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
            EXTRA_HIT_ROW_ID, ROW_LOCAL_CUSTOM, len(EXTRA_HIT_LABELS),
            ROW_FLAG_CUSTOM_EXTRA_HIT, extra_hit_default(selection),
        ),
        "sub_active_frames": lambda: BattleRow(
            SUB_ACTIVE_FRAMES_ROW_ID, ROW_LOCAL_CUSTOM, len(SUB_ACTIVE_FRAMES_LABELS),
            ROW_FLAG_CUSTOM_SUB_ACTIVE_FRAMES,
            sub_active_frames_default(selection),
        ),
        "xdash_chakra_cost": lambda: BattleRow(
            XDASH_CHAKRA_COST_ROW_ID, ROW_LOCAL_CUSTOM, 21,
            ROW_FLAG_CUSTOM_XDASH_CHAKRA_COST,
            xdash_chakra_cost_option_default(selection),
        ),
        "support": lambda: BattleRow(
            SUPPORT_ROW_ID, ROW_LOCAL_CUSTOM, len(SUPPORT_LABELS),
            ROW_FLAG_CUSTOM_SUPPORT, support_default(selection),
        ),
        "substitution": lambda: BattleRow(
            SUBSTITUTION_ROW_ID, ROW_LOCAL_CUSTOM, 3,
            ROW_FLAG_CUSTOM_SUBSTITUTION, substitution_default(selection),
        ),
    }
    row_bindings = {
        BATTLE_SETTINGS_PATH + (field,): (lambda row_id=row_id: native_row(row_id))
        for field, row_id in BATTLE_ROW_IDS.items()
    }
    row_bindings.update({BATTLE_MECHANICS_PATH + (field,): factory
                         for field, factory in custom_rows.items()})
    return build_menu_pages(selection, BATTLE_SETTINGS_PATH, row_bindings,
                            BattleRow, BattlePage, ("primary_row_count", "secondary_row_count"),
                            "battle_settings_schema", SUPPORT_ROW_ID + 1)


def battle_settings_fragment(
    selection: CatalogSelection,
    *,
    owner: str,
    symbol: str = "battle_settings_schema",
) -> PayloadFragment | None:
    battle_settings = _selected_node(selection, BATTLE_SETTINGS_PATH)
    if not battle_settings.enabled:
        return None

    pages = _active_pages(selection)
    rows = tuple(row for page in pages for row in page.rows)
    payload = bytearray(
        struct.pack(
            "<20I",
            len(rows),
            len(pages),
            0,
            0,
            *([0] * 16),
        )
    )
    relocations: list[PayloadRelocation] = [
        PayloadRelocation(
            offset=8,
            kind="abs32",
            symbol=symbol,
            addend=SCHEMA_HEADER_SIZE,
        ),
        PayloadRelocation(
            offset=12,
            kind="abs32",
            symbol=symbol,
            addend=SCHEMA_HEADER_SIZE + len(pages) * PAGE_SIZE,
        ),
    ]
    row_start = 0
    for page in pages:
        page_offset = len(payload)
        payload.extend(
            struct.pack(
                "<7I",
                row_start,
                len(page.rows),
                page.primary_row_count,
                page.secondary_row_count,
                page.parent_page,
                page.parent_row,
                0,
            )
        )
        if page.heading_symbol is not None:
            relocations.append(
                PayloadRelocation(
                    offset=page_offset + 6 * 4,
                    kind="abs32",
                    symbol=page.heading_symbol,
                )
            )
        row_start += len(page.rows)

    rows_offset = SCHEMA_HEADER_SIZE + len(pages) * PAGE_SIZE
    appended_tables_offset = rows_offset + len(rows) * ROW_SIZE
    chakra_value_table_offset = appended_tables_offset
    substitution_value_table_offset = (
        chakra_value_table_offset + CHAKRA_OPTION_COUNT * 4
    )
    toggle_value_table_offset = substitution_value_table_offset + (
        len(SUBSTITUTION_MODE_LABELS) * 4
    )
    sub_active_frames_value_table_offset = toggle_value_table_offset + (
        len(TOGGLE_LABELS) * 4
    )
    xdash_chakra_cost_value_table_offset = (
        sub_active_frames_value_table_offset + len(SUB_ACTIVE_FRAMES_LABELS) * 4
    )
    support_value_table_offset = xdash_chakra_cost_value_table_offset + 21 * 4
    extra_hit_value_table_offset = support_value_table_offset + len(SUPPORT_LABELS) * 4
    text_pool_offset = extra_hit_value_table_offset + len(EXTRA_HIT_LABELS) * 4
    value_table_offsets = {
        "chakra": chakra_value_table_offset,
        "substitution": substitution_value_table_offset,
        "toggle": toggle_value_table_offset,
        "sub_active_frames": sub_active_frames_value_table_offset,
        "xdash_chakra_cost": xdash_chakra_cost_value_table_offset,
        "support": support_value_table_offset,
        "extra_hit": extra_hit_value_table_offset,
    }
    header_symbols = {
        "substitution": (
            (16, "substitution_gauge_mode_get"),
            (20, "substitution_gauge_mode_set"),
        ),
        "ultimate_jutsu": (
            (24, "ultimate_jutsu_mode_get"),
            (28, "ultimate_jutsu_mode_set"),
            (32, "ultimate_jutsu_no_contest_label"),
            (36, "ultimate_jutsu_no_hud_label"),
        ),
        "shadowblur": ((40, "shadowblur_get"), (44, "shadowblur_set")),
        "extra_hit": ((48, "extra_hit_get"), (52, "extra_hit_set")),
        "sub_active_frames": (
            (56, "sub_active_frames_get"),
            (60, "sub_active_frames_set"),
        ),
        "xdash_chakra_cost": (
            (64, "xdash_chakra_cost_option_get"),
            (68, "xdash_chakra_cost_option_set"),
        ),
        "support": ((72, "support_get"), (76, "support_set")),
    }
    for field, symbols in header_symbols.items():
        if battle_mechanic_enabled(selection, field):
            relocations.extend(
                PayloadRelocation(offset=offset, kind="abs32", symbol=name)
                for offset, name in symbols
            )
    for index, row in enumerate(rows):
        fields = list(row.encoded_fields())
        row_offset = rows_offset + index * ROW_SIZE
        if row.runtime_option is not None or row.label is not None:
            fields[LABEL_REFERENCE_FIELD] = 0
            fields[HELP_REFERENCE_FIELD] = 0
            fields[VALUE_REFERENCE_FIELD] = 0
        elif (row.flags & ROW_FLAG_CUSTOM_CHAKRA) != 0:
            fields[VALUE_REFERENCE_FIELD] = 0
            relocations.append(
                PayloadRelocation(
                    offset=row_offset + VALUE_REFERENCE_FIELD * 4,
                    kind="abs32",
                    symbol=symbol,
                    addend=value_table_offsets["chakra"],
                )
            )
        elif row.row_id in CUSTOM_ROW_RESOURCES:
            fields[LABEL_REFERENCE_FIELD] = 0
            fields[HELP_REFERENCE_FIELD] = 0
            fields[VALUE_REFERENCE_FIELD] = 0
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
        payload.extend(struct.pack("<10I", *fields))

    if any(
        row.row_id in CUSTOM_ROW_RESOURCES
        or (row.flags & ROW_FLAG_CUSTOM_CHAKRA) != 0
        for row in rows
    ):
        text_pool = bytearray()
        next_text_offset = text_pool_offset
        for label in CHAKRA_STATIC_LABELS:
            relocations.append(
                PayloadRelocation(
                    offset=len(payload),
                    kind="abs32",
                    symbol=label,
                )
            )
            payload.extend(b"\0" * 4)

        for text_value in CHAKRA_REGEN_LABELS:
            relocations.append(
                PayloadRelocation(
                    offset=len(payload),
                    kind="abs32",
                    symbol=symbol,
                    addend=next_text_offset,
                )
            )
            payload.extend(b"\0" * 4)
            text = text_value.encode("ascii") + b"\0"
            text_pool.extend(text)
            next_text_offset += len(text)

        for label in SUBSTITUTION_MODE_LABELS:
            if label is not None and battle_mechanic_enabled(selection, "substitution"):
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

        for label in SUB_ACTIVE_FRAMES_LABELS:
            text = label.encode("ascii") + b"\0"
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
        for label in (*SUPPORT_LABELS, *EXTRA_HIT_LABELS):
            text = label.encode("ascii") + b"\0"
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

    append_row_extensions(payload, relocations, rows, rows_offset, ROW_SIZE,
                          2, 3, 4, symbol)

    return PayloadFragment(
        owner=owner,
        symbol=symbol,
        kind="rodata",
        alignment=4,
        payload=bytes(payload),
        relocations=tuple(relocations),
    )


def battle_settings_table_fragments(
    selection: CatalogSelection,
    *,
    owner: str,
) -> tuple[PayloadFragment, ...]:
    battle_settings = _selected_node(selection, BATTLE_SETTINGS_PATH)
    if not battle_settings.enabled:
        return ()

    pages = _active_pages(selection)
    table_size = max(1, *(len(page.rows) for page in pages)) * 4
    return page_resource_fragments(pages, owner, "battle_settings_schema") + (
        PayloadFragment(
            owner=owner,
            symbol="battle_settings_active_help",
            kind="data",
            alignment=4,
            payload=b"\0" * table_size,
        ),
    )
