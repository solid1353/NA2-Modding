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
    PRACTICE_SETTINGS_PATH,
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
    PRACTICE_GENERAL_ROW_IDS,
    PRACTICE_OPPONENT_ROW_IDS,
    practice_configured_row_defaults,
)

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
ROW_FLAG_CUSTOM_CHAKRA = 0x1000

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
SCHEMA_HEADER_SIZE = 80
PAGE_FIELD_COUNT = 7
PAGE_SIZE = PAGE_FIELD_COUNT * 4
ROW_FIELD_COUNT = 12
ROW_SIZE = ROW_FIELD_COUNT * 4
LABEL_REFERENCE_FIELD = 3
HELP_REFERENCE_FIELD = 4
VALUE_REFERENCE_FIELD = 5
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

    value_pages: tuple[tuple[int, int, str | None], ...] = ()
    runtime_option: MenuOption | None = None
    label: str | None = None
    help: str | None = None

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
            0,
            0,
        )


@dataclass(frozen=True)
class PracticePage:
    rows: tuple[PracticeRow, ...]
    player_row_count: int
    opponent_row_count: int
    parent_page: int = 0
    parent_row: int = 0
    heading_symbol: str | None = None
    heading_text: str | None = None


NATIVE_ROWS = {
    0: PracticeRow(0, ROW_SECTION_PLAYER, 0x6C, 3, 0),
    1: PracticeRow(1, ROW_SECTION_PLAYER, 0x70, 2, 0),
    3: PracticeRow(3, ROW_SECTION_PLAYER, 0x78, 6, 2),
    6: PracticeRow(6, ROW_SECTION_PLAYER, 0x84, 2, 1),
    7: PracticeRow(7, ROW_SECTION_PLAYER, 0x88, 2, 1),
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


def _active_pages(selection: CatalogSelection) -> tuple[PracticePage, ...]:
    configured_defaults = practice_configured_row_defaults(selection)

    def native_row(row_id: int) -> PracticeRow:
        row = NATIVE_ROWS[row_id]
        if row_id not in configured_defaults:
            return row
        return replace(row, default_value=configured_defaults[row_id])

    custom_rows = {
        "items": lambda: PracticeRow(
            5, ROW_SECTION_PLAYER, ROW_LOCAL_CUSTOM, 5, items_mode_option(selection).default,
            flags=0, runtime_option=items_mode_option(selection),
        ),
        "chakra": lambda: replace(
            native_row(1),
            local_offset=ROW_LOCAL_CUSTOM,
            option_count=CHAKRA_OPTION_COUNT,
            default_value=chakra_default(selection),
            flags=(native_row(1).flags & ~ROW_FLAG_VALUES_SLOT)
            | ROW_FLAG_CUSTOM_CHAKRA,
        ),
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
            EXTRA_HIT_ROW_ID, ROW_SECTION_PLAYER, ROW_LOCAL_CUSTOM, len(EXTRA_HIT_LABELS),
            extra_hit_default(selection), flags=ROW_FLAG_CUSTOM_EXTRA_HIT,
        ),
        "sub_active_frames": lambda: PracticeRow(
            SUB_ACTIVE_FRAMES_ROW_ID, ROW_SECTION_PLAYER, ROW_LOCAL_CUSTOM, len(SUB_ACTIVE_FRAMES_LABELS),
            sub_active_frames_default(selection),
            flags=ROW_FLAG_CUSTOM_SUB_ACTIVE_FRAMES,
        ),
        "xdash_chakra_cost": lambda: PracticeRow(
            XDASH_CHAKRA_COST_ROW_ID, ROW_SECTION_PLAYER, ROW_LOCAL_CUSTOM, 21,
            xdash_chakra_cost_option_default(selection),
            flags=ROW_FLAG_CUSTOM_XDASH_CHAKRA_COST,
        ),
        "support": lambda: PracticeRow(
            SUPPORT_ROW_ID, ROW_SECTION_PLAYER, ROW_LOCAL_CUSTOM, len(SUPPORT_LABELS),
            support_default(selection), flags=ROW_FLAG_CUSTOM_SUPPORT,
        ),
        "substitution": lambda: PracticeRow(
            SUBSTITUTION_ROW_ID, ROW_SECTION_PLAYER, ROW_LOCAL_CUSTOM, 3,
            substitution_default(selection),
            flags=ROW_FLAG_CUSTOM_SUBSTITUTION,
        ),
    }
    row_bindings = {
        PRACTICE_SETTINGS_PATH + (field,): (lambda row_id=row_id: native_row(row_id))
        for field, row_id in PRACTICE_GENERAL_ROW_IDS.items()
    }
    row_bindings.update({
        PRACTICE_SETTINGS_PATH + ("opponent_settings", field):
            (lambda row_id=row_id: native_row(row_id))
        for field, row_id in PRACTICE_OPPONENT_ROW_IDS.items()
    })
    row_bindings.update({BATTLE_MECHANICS_PATH + (field,): factory
                         for field, factory in custom_rows.items()})
    return build_menu_pages(selection, PRACTICE_SETTINGS_PATH, row_bindings,
                            PracticeRow, PracticePage, ("player_row_count", "opponent_row_count"),
                            "practice_settings_schema", SUPPORT_ROW_ID + 1)


def practice_settings_fragment(
    selection: CatalogSelection,
    *,
    owner: str,
    symbol: str = "practice_settings_schema",
) -> PayloadFragment | None:
    if not _node_enabled(selection, PRACTICE_SETTINGS_PATH):
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
                page.player_row_count,
                page.opponent_row_count,
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
        row_offset = rows_offset + index * ROW_SIZE
        if row.runtime_option is not None or row.label is not None:
            fields = list(row.encoded_fields())
            fields[LABEL_REFERENCE_FIELD] = 0
            fields[HELP_REFERENCE_FIELD] = 0
            fields[VALUE_REFERENCE_FIELD] = 0
            payload.extend(struct.pack("<12I", *fields))
        elif (row.flags & ROW_FLAG_CUSTOM_CHAKRA) != 0:
            fields = list(row.encoded_fields())
            fields[VALUE_REFERENCE_FIELD] = 0
            payload.extend(struct.pack("<12I", *fields))
            relocations.append(
                PayloadRelocation(
                    offset=row_offset + VALUE_REFERENCE_FIELD * 4,
                    kind="abs32",
                    symbol=symbol,
                    addend=value_table_offsets["chakra"],
                )
            )
        elif row.row_id in CUSTOM_ROW_RESOURCES:
            fields = list(row.encoded_fields())
            fields[LABEL_REFERENCE_FIELD] = 0
            fields[HELP_REFERENCE_FIELD] = 0
            fields[VALUE_REFERENCE_FIELD] = 0
            label_symbol, help_symbol, value_table = CUSTOM_ROW_RESOURCES[
                row.row_id
            ]
            payload.extend(struct.pack("<12I", *fields))
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
            payload.extend(struct.pack("<12I", *row.encoded_fields()))

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
                          3, 4, 5, symbol)

    return PayloadFragment(
        owner=owner,
        symbol=symbol,
        kind="rodata",
        alignment=4,
        payload=bytes(payload),
        relocations=tuple(relocations),
    )


def practice_settings_table_fragments(
    selection: CatalogSelection,
    *,
    owner: str,
) -> tuple[PayloadFragment, ...]:
    if not _node_enabled(selection, PRACTICE_SETTINGS_PATH):
        return ()

    pages = _active_pages(selection)
    table_size = max(1, *(len(page.rows) for page in pages)) * 4
    return page_resource_fragments(pages, owner, "practice_settings_schema") + tuple(
        PayloadFragment(
            owner=owner,
            symbol=symbol,
            kind="data",
            alignment=4,
            payload=b"\0" * table_size,
        )
        for symbol in (
            "practice_settings_active_labels",
            "practice_settings_active_value_tables",
        )
    )
