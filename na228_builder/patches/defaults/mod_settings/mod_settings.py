from __future__ import annotations

from na228_builder.patches.localization.mod_strings import message

import struct
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING

from na228_builder.infrastructure.common import indexed_png_pixels
from na228_builder.infrastructure.modules.payload_builder.operations import PayloadFragment
from ..battle_settings.battle_settings import (
    LAYOUT as BATTLE_LAYOUT,
    NATIVE_ROWS as BATTLE_NATIVE_ROWS,
)
from ..practice_settings.practice_settings import (
    LAYOUT as PRACTICE_LAYOUT,
    NATIVE_ROWS as PRACTICE_NATIVE_ROWS,
    ROW_FLAG_HANDICAP,
    ROW_FLAG_HELP_SLOT,
    ROW_FLAG_LABEL_SLOT,
    ROW_FLAG_VALUES_SLOT,
    PracticeRow,
    practice_native_row,
)
from ..battle_mechanics.battle_settings_runtime import PRACTICE_SETTINGS_PATH
from ..menu_options import MOD_SETTINGS_PATH, MenuOption, mod_setting_values
from ..menu_pages import (
    ROW_LOCAL_CUSTOM,
    MenuPage,
    build_menu_pages,
    mechanic_row_bindings,
    page_resource_fragments,
    settings_schema_fragment,
)
from ..native_settings_defaults import (
    BATTLE_ROW_IDS,
    BATTLE_SETTINGS_PATH,
    PRACTICE_GENERAL_ROW_IDS,
    PRACTICE_OPPONENT_ROW_IDS,
    battle_configured_row_defaults,
    practice_configured_row_defaults,
)

if TYPE_CHECKING:
    from na228_builder.infrastructure.orchestration.catalog import CatalogSelection


def _native_option(
    row,
    layout,
    *,
    default: int,
    argument: int,
    values: tuple[str, ...] = (),
) -> MenuOption:
    label_reference, help_reference, values_reference = (
        row.encoded_fields()[layout.references:layout.references + 3]
    )
    return MenuOption(
        None,
        None,
        values,
        default,
        "save_native_setting_get",
        "save_native_setting_set",
        argument,
        label_reference=label_reference,
        help_reference=help_reference,
        values_reference=None if values else values_reference,
        option_count=row.option_count,
    )


def _native_row_bindings(selection: CatalogSelection):
    bindings = mechanic_row_bindings(selection, PRACTICE_LAYOUT, practice_native_row(selection))
    battle_defaults = battle_configured_row_defaults(selection)
    for key, row_id in BATTLE_ROW_IDS.items():
        source = BATTLE_NATIVE_ROWS[row_id]
        default = battle_defaults.get(row_id, source.default_value)
        values = (
            tuple(str(value) for value in range(10, 100, 10))
            + ("99", message("common.unlimited"))
            if key == "time"
            else ()
        )
        option = _native_option(
            source,
            BATTLE_LAYOUT,
            default=default,
            argument=0x100 | row_id,
            values=values,
        )
        flags = ROW_FLAG_LABEL_SLOT | ROW_FLAG_HELP_SLOT
        if not values:
            flags |= ROW_FLAG_VALUES_SLOT
        if key == "handicap":
            flags |= ROW_FLAG_HANDICAP
        row = PracticeRow(
            row_id,
            1,
            ROW_LOCAL_CUSTOM,
            source.option_count,
            default,
            flags=flags,
            runtime_option=option,
        )
        bindings[BATTLE_SETTINGS_PATH + (key,)] = lambda row=row: row

    practice_defaults = practice_configured_row_defaults(selection)
    for parent, row_ids in (
        ((), PRACTICE_GENERAL_ROW_IDS),
        (("opponent_settings",), PRACTICE_OPPONENT_ROW_IDS),
    ):
        for key, row_id in row_ids.items():
            source = PRACTICE_NATIVE_ROWS[row_id]
            default = practice_defaults.get(row_id, source.default_value)
            option = _native_option(
                source,
                PRACTICE_LAYOUT,
                default=default,
                argument=0x200 | row_id,
            )
            row = replace(
                source,
                section=1,
                local_offset=ROW_LOCAL_CUSTOM,
                default_value=default,
                runtime_option=option,
            )
            bindings[PRACTICE_SETTINGS_PATH + parent + (key,)] = (
                lambda row=row: row
            )
    return bindings


def _pages(selection: CatalogSelection) -> tuple[MenuPage, ...]:
    pages = build_menu_pages(
        selection,
        MOD_SETTINGS_PATH,
        _native_row_bindings(selection),
        PRACTICE_LAYOUT,
        "mod_settings_schema",
        external_launchers={"control_settings": 0x8000},
    )
    for page in pages:
        handicap_rows = [
            index for index, row in enumerate(page.rows)
            if row.flags & ROW_FLAG_HANDICAP
        ]
        # The double-height Handicap panel has no room for a following row.
        if handicap_rows and handicap_rows != [len(page.rows) - 1]:
            raise ValueError("Handicap must be the last row on its Mod Settings page")
    return pages


def mod_settings_menu_fragments(
    selection: CatalogSelection,
    *,
    owner: str,
) -> tuple[PayloadFragment, ...]:
    """The schema and its page resources."""
    pages = _pages(selection)
    return (
        settings_schema_fragment(selection, pages, PRACTICE_LAYOUT, owner=owner,
                                 symbol="mod_settings_schema"),
        *page_resource_fragments(pages, owner, "mod_settings_schema", selection),
    )


def mod_settings_state_fragment(
    selection: CatalogSelection,
    *,
    owner: str,
) -> PayloadFragment:
    values = mod_setting_values(selection)
    return PayloadFragment(
        owner=owner,
        symbol="mod_settings_state",
        kind="data",
        alignment=4,
        payload=struct.pack("<8I", *values, *values),
    )


def mod_settings_graphics_fragments(*, owner: str) -> tuple[PayloadFragment, ...]:
    return tuple(
        PayloadFragment(
            owner=owner,
            symbol=symbol,
            kind="rodata",
            alignment=16,
            payload=indexed_png_pixels(Path(__file__).with_name(filename), size, flip=True),
        )
        for filename, size, symbol in (
            ("mod_settings_title.png", (128, 32), "mod_settings_title_pixels"),
            ("mod_settings_prompt_label.png", (48, 24), "mod_settings_prompt_label_pixels"),
        )
    )
