from __future__ import annotations

import struct
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image

from na228_builder.infrastructure.modules.payload_builder.operations import PayloadFragment
from ..ingame.battle_mode.battle_settings import NATIVE_ROWS as BATTLE_NATIVE_ROWS
from ..ingame.practice_mode.practice_settings import (
    NATIVE_ROWS as PRACTICE_NATIVE_ROWS,
    ROW_FLAG_HELP_SLOT,
    ROW_FLAG_LABEL_SLOT,
    ROW_FLAG_VALUES_SLOT,
    ROW_LOCAL_CUSTOM,
    PracticePage,
    PracticeRow,
    practice_settings_row_bindings,
    settings_menu_schema_fragment,
)
from ..ingame.battle_mechanics.battle_settings_runtime import PRACTICE_SETTINGS_PATH
from ..ingame.shared.menu_options import MOD_SETTINGS_PATH, MenuOption
from ..ingame.shared.menu_pages import build_menu_pages, page_resource_fragments
from ..ingame.shared.native_settings_defaults import (
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
    *,
    default: int,
    argument: int,
    reference_fields: slice,
    values: tuple[str, ...] = (),
) -> MenuOption:
    label_reference, help_reference, values_reference = (
        row.encoded_fields()[reference_fields]
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
    bindings = practice_settings_row_bindings(selection, include_native_rows=False)
    battle_defaults = battle_configured_row_defaults(selection)
    for key, row_id in BATTLE_ROW_IDS.items():
        source = BATTLE_NATIVE_ROWS[row_id]
        default = battle_defaults.get(row_id, source.default_value)
        values = (
            tuple(str(value) for value in range(10, 100, 10))
            + ("99", "Unlimited")
            if key == "time"
            else tuple(f"{value}-{10 - value}" for value in range(11))
            if key == "handicap"
            else ()
        )
        option = _native_option(
            source,
            default=default,
            argument=0x100 | row_id,
            reference_fields=slice(2, 5),
            values=values,
        )
        flags = ROW_FLAG_LABEL_SLOT | ROW_FLAG_HELP_SLOT
        if not values:
            flags |= ROW_FLAG_VALUES_SLOT
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
                default=default,
                argument=0x200 | row_id,
                reference_fields=slice(3, 6),
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


def _pages(selection: CatalogSelection) -> tuple[PracticePage, ...]:
    return build_menu_pages(
        selection,
        MOD_SETTINGS_PATH,
        _native_row_bindings(selection),
        PracticeRow,
        PracticePage,
        ("player_row_count", "opponent_row_count"),
        "mod_settings_schema",
        0,
        excluded_paths=(
            BATTLE_SETTINGS_PATH + ("battle_mechanics_submenu",),
            PRACTICE_SETTINGS_PATH + ("battle_mechanics_submenu",),
        ),
    )


def mod_settings_schema_fragment(
    selection: CatalogSelection,
    *,
    owner: str,
    symbol: str = "mod_settings_schema",
) -> PayloadFragment:
    return settings_menu_schema_fragment(
        selection,
        _pages(selection),
        owner=owner,
        symbol=symbol,
    )


def mod_settings_resource_fragments(
    selection: CatalogSelection,
    *,
    owner: str,
) -> tuple[PayloadFragment, ...]:
    return page_resource_fragments(_pages(selection), owner, "mod_settings_schema")


def mod_settings_state_fragment(
    selection: CatalogSelection,
    *,
    owner: str,
) -> PayloadFragment:
    selected = {node.path: node for node in selection.nodes}
    values = (
        int(bool(selected[MOD_SETTINGS_PATH + ("new_controls",)].configured_value)),
        int(selected[MOD_SETTINGS_PATH + ("simple_display",)].configured_value == "on"),
        int(bool(selected[MOD_SETTINGS_PATH + ("character_overrides",)].configured_value)),
        int(bool(selected[MOD_SETTINGS_PATH + ("balance_overlay",)].configured_value)),
        {"none": 0, "relevant": 1, "all": 2}[
            selected[MOD_SETTINGS_PATH + ("support_selection",)].configured_value
        ],
    )
    return PayloadFragment(
        owner=owner,
        symbol="mod_settings_state",
        kind="data",
        alignment=4,
        payload=struct.pack("<10I", *values, *values),
    )


def _indexed_texture_fragment(
    filename: str,
    size: tuple[int, int],
    symbol: str,
    *,
    owner: str,
) -> PayloadFragment:
    source = Path(__file__).with_name(filename)
    with Image.open(source) as image:
        if image.size != size or image.mode != "P":
            raise ValueError(
                f"{filename} must be a {size[0]}x{size[1]} indexed PNG"
            )
        payload = image.transpose(Image.Transpose.FLIP_TOP_BOTTOM).tobytes()
    expected_size = size[0] * size[1]
    if len(payload) != expected_size:
        raise ValueError(f"{filename} must contain exactly {expected_size} indexed pixels")
    return PayloadFragment(
        owner=owner,
        symbol=symbol,
        kind="rodata",
        alignment=16,
        payload=payload,
    )


def mod_settings_graphics_fragments(*, owner: str) -> tuple[PayloadFragment, ...]:
    return (
        _indexed_texture_fragment(
            "mod_settings_title.png",
            (128, 32),
            "mod_settings_title_pixels",
            owner=owner,
        ),
        _indexed_texture_fragment(
            "mod_settings_prompt_label.png",
            (48, 24),
            "mod_settings_prompt_label_pixels",
            owner=owner,
        ),
    )
