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
from ..shared.native_settings_defaults import (
    BATTLE_SETTINGS_PATH,
    BATTLE_ROW_IDS,
    battle_configured_row_defaults,
)

if TYPE_CHECKING:
    from na228_builder.infrastructure.orchestration.catalog import CatalogSelection


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
ROW_FLAG_CUSTOM_SUBSTITUTION_INPUT = 0x800
ROW_FLAG_CUSTOM_XDASH_CHAKRA_COST = 0x1000
ROW_FLAG_CUSTOM_SUPPORT = 0x2000
ROW_FLAG_CUSTOM_CHAKRA = 0x8000

NATIVE_LABEL_TABLE = 0x008BE160
NATIVE_HELP_TABLE = 0x008BE560
NATIVE_VALUE_TABLE = 0x008BE5C0


@dataclass(frozen=True)
class BattleRow:
    row_id: int
    local_offset: int
    option_count: int
    flags: int
    default_value: int = 0

    value_pages: tuple[tuple[int, int, Message | str | None], ...] = ()
    runtime_option: MenuOption | None = None
    label: Message | str | None = None
    help: Message | str | None = None

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


LAYOUT = RowLayout(
    row_type=BattleRow,
    field_count=10,
    references=2,
    first_custom_row_id=6,
    items_row_id=2,
    chakra_row_id=3,
    ultimate_jutsu_row_id=4,
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


def _active_pages(selection: CatalogSelection) -> tuple[MenuPage, ...]:
    native_row = native_rows(NATIVE_ROWS, battle_configured_row_defaults(selection))
    row_bindings = {
        BATTLE_SETTINGS_PATH + (field,): (lambda row_id=row_id: native_row(row_id))
        for field, row_id in BATTLE_ROW_IDS.items()
    }
    row_bindings.update(mechanic_row_bindings(selection, LAYOUT, native_row))
    return build_menu_pages(selection, BATTLE_SETTINGS_PATH, row_bindings, LAYOUT,
                            "battle_settings_schema")


def battle_settings_fragments(
    selection: CatalogSelection,
    *,
    owner: str,
) -> tuple[PayloadFragment, ...]:
    """The schema, its page resources, and the active help table."""
    pages = _active_pages(selection)
    table_size = max(1, *(len(page.rows) for page in pages)) * 4
    return (
        settings_schema_fragment(selection, pages, LAYOUT, owner=owner,
                                 symbol="battle_settings_schema"),
        *page_resource_fragments(pages, owner, "battle_settings_schema", selection),
        PayloadFragment(
            owner=owner,
            symbol="battle_settings_active_help",
            kind="data",
            alignment=4,
            payload=b"\0" * table_size,
        ),
    )
