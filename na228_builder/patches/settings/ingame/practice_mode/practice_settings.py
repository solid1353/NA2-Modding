from __future__ import annotations

from na228_builder.patches.localization.mod_strings import Message
from dataclasses import dataclass
from typing import TYPE_CHECKING

from na228_builder.infrastructure.modules.payload_builder.operations import PayloadFragment
from ..shared.menu_options import MenuOption
from ..shared.menu_pages import (
    MenuPage,
    RowLayout,
    build_menu_pages,
    mechanic_row_bindings,
    native_rows,
    page_resource_fragments,
    settings_schema_fragment,
)
from ..battle_mechanics.battle_settings_runtime import PRACTICE_SETTINGS_PATH
from ..shared.native_settings_defaults import (
    PRACTICE_GENERAL_ROW_IDS,
    PRACTICE_OPPONENT_ROW_IDS,
    practice_configured_row_defaults,
)

if TYPE_CHECKING:
    from na228_builder.infrastructure.orchestration.catalog import CatalogSelection


ROW_SECTION_PLAYER = 0
ROW_SECTION_OPPONENT = 1

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
ROW_FLAG_CUSTOM_SUBSTITUTION_INPUT = 0x200
ROW_FLAG_CUSTOM_XDASH_CHAKRA_COST = 0x400
ROW_FLAG_CUSTOM_SUPPORT = 0x800
ROW_FLAG_CUSTOM_CHAKRA = 0x1000
ROW_FLAG_STATUS_SOURCE = 0x2000
ROW_FLAG_HANDICAP = 0x10000

NATIVE_LABEL_TABLE = 0x008BE6C0
NATIVE_HELP_TABLE = 0x008BEF70
NATIVE_STATUS_HELP_TABLE = 0x008BF350
NATIVE_VALUE_TABLE = 0x008BF380


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

    value_pages: tuple[tuple[int, int, Message | str | None], ...] = ()
    runtime_option: MenuOption | None = None
    label: Message | str | None = None
    help: Message | str | None = None

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


LAYOUT = RowLayout(
    row_type=PracticeRow,
    field_count=12,
    references=3,
    first_custom_row_id=17,
    items_row_id=5,
    chakra_row_id=1,
    ultimate_jutsu_row_id=3,
    values_slot_flag=ROW_FLAG_VALUES_SLOT,
    custom_flags={
        "chakra": ROW_FLAG_CUSTOM_CHAKRA,
        "ultimate_jutsu": ROW_FLAG_CUSTOM_ULTIMATE_JUTSU,
        "substitution_resource": ROW_FLAG_CUSTOM_SUBSTITUTION,
        "shadowblur": ROW_FLAG_CUSTOM_SHADOWBLUR,
        "extra_hit": ROW_FLAG_CUSTOM_EXTRA_HIT,
        "substitution_input": ROW_FLAG_CUSTOM_SUBSTITUTION_INPUT,
        "xdash_chakra_cost": ROW_FLAG_CUSTOM_XDASH_CHAKRA_COST,
        "support": ROW_FLAG_CUSTOM_SUPPORT,
    },
)

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
            | ROW_FLAG_STATUS_SOURCE
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


def practice_native_row(selection: CatalogSelection):
    return native_rows(NATIVE_ROWS, practice_configured_row_defaults(selection))


def _active_pages(selection: CatalogSelection) -> tuple[MenuPage, ...]:
    native_row = practice_native_row(selection)
    row_bindings = mechanic_row_bindings(selection, LAYOUT, native_row)
    for parent, row_ids in (
        ((), PRACTICE_GENERAL_ROW_IDS),
        (("opponent_settings",), PRACTICE_OPPONENT_ROW_IDS),
    ):
        row_bindings.update({
            PRACTICE_SETTINGS_PATH + parent + (field,):
                (lambda row_id=row_id: native_row(row_id))
            for field, row_id in row_ids.items()
        })
    return build_menu_pages(selection, PRACTICE_SETTINGS_PATH, row_bindings, LAYOUT,
                            "practice_settings_schema")


def practice_settings_fragments(
    selection: CatalogSelection,
    *,
    owner: str,
) -> tuple[PayloadFragment, ...]:
    """The schema, its page resources, and the active label and value tables."""
    pages = _active_pages(selection)
    table_size = max(1, *(len(page.rows) for page in pages)) * 4
    return (
        settings_schema_fragment(selection, pages, LAYOUT, owner=owner,
                                 symbol="practice_settings_schema"),
        *page_resource_fragments(pages, owner, "practice_settings_schema", selection),
        *(
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
        ),
    )
