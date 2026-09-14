from __future__ import annotations

import struct
from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image

from na228_builder.infrastructure.modules.payload_builder.operations import PayloadFragment
from ..ingame.practice_mode.practice_settings import (
    PracticePage,
    PracticeRow,
    practice_settings_row_bindings,
    settings_menu_schema_fragment,
)
from ..ingame.shared.menu_options import MOD_SETTINGS_PATH
from ..ingame.shared.menu_pages import build_menu_pages, page_resource_fragments

if TYPE_CHECKING:
    from na228_builder.infrastructure.orchestration.catalog import CatalogSelection


def _pages(selection: CatalogSelection) -> tuple[PracticePage, ...]:
    return build_menu_pages(
        selection,
        MOD_SETTINGS_PATH,
        practice_settings_row_bindings(selection, include_native_rows=False),
        PracticeRow,
        PracticePage,
        ("player_row_count", "opponent_row_count"),
        "mod_settings_schema",
        0,
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
