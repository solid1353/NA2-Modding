from __future__ import annotations

import struct
from typing import TYPE_CHECKING

from ..payload_builder.operations import PayloadFragment

if TYPE_CHECKING:
    from .catalog import CatalogSelection


SHARED_SETTINGS_PATH = ("features", "settings", "shared")
PRACTICE_SETTINGS_PATH = ("features", "settings", "practice")

ULTIMATE_JUTSU_MODE_VALUES = {
    "no_use": 0,
    "random": 1,
    "command": 2,
    "timing": 3,
    "turn": 4,
    "combo": 5,
    "no_contest": 6,
    "no_hud": 7,
}
ULTIMATE_JUTSU_NATIVE_DEFAULT = ULTIMATE_JUTSU_MODE_VALUES["command"]
ULTIMATE_JUTSU_NATIVE_MODE_COUNT = 6

TOGGLE_MODE_VALUES = {
    "off": 0,
    "on": 1,
}
SUBSTITUTION_MODE_VALUES = {
    "chakra": 0,
    "gauge": 1,
    "free": 2,
}


def _selected_node(selection: CatalogSelection, path: tuple[str, ...]):
    matches = [node for node in selection.nodes if node.path == path]
    if len(matches) != 1:
        raise ValueError(f"Catalog selection has no unique {'.'.join(path)} node")
    return matches[0]


def _shared_settings_value(selection: CatalogSelection) -> dict[str, object]:
    node = _selected_node(selection, SHARED_SETTINGS_PATH)
    if not node.enabled:
        return {}
    configured = node.configured_value
    if not node.has_configured_value or not isinstance(configured, dict):
        raise ValueError("Shared settings requires an object value")
    return configured


def ultimate_jutsu_default(selection: CatalogSelection) -> int:
    node = _selected_node(selection, SHARED_SETTINGS_PATH)
    if not node.enabled:
        return ULTIMATE_JUTSU_NATIVE_DEFAULT
    value = _shared_settings_value(selection).get("ultimate_jutsu")
    if value not in ULTIMATE_JUTSU_MODE_VALUES:
        raise ValueError("Shared settings requires an Ultimate Jutsu default")
    return ULTIMATE_JUTSU_MODE_VALUES[value]


def _toggle_default(selection: CatalogSelection, field: str) -> int:
    value = _shared_settings_value(selection).get(field)
    if value not in TOGGLE_MODE_VALUES:
        raise ValueError(
            f"Shared settings {field} default must be 'off' or 'on'"
        )
    return TOGGLE_MODE_VALUES[value]


def shadowblur_default(selection: CatalogSelection) -> int:
    return _toggle_default(selection, "shadowblur")


def extra_hit_default(selection: CatalogSelection) -> int:
    return _toggle_default(selection, "extra_hit")


def sub_active_frames_default(selection: CatalogSelection) -> int:
    value = _shared_settings_value(selection).get("sub_active_frames")
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 16:
        raise ValueError(
            "Shared settings sub_active_frames default must be 0 through 16"
        )
    return value


def substitution_default(selection: CatalogSelection) -> int:
    value = _shared_settings_value(selection).get("substitution")
    if not isinstance(value, dict):
        raise ValueError("Shared settings substitution requires an object value")
    default = value.get("default")
    if default not in SUBSTITUTION_MODE_VALUES:
        raise ValueError(
            "Shared settings substitution default must be 'chakra', 'gauge', "
            "or 'free'"
        )
    return SUBSTITUTION_MODE_VALUES[default]


def xdash_chakra_cost_default(selection: CatalogSelection) -> int:
    value = _shared_settings_value(selection).get("xdash_chakra_cost")
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 100
        or value % 5 != 0
    ):
        raise ValueError(
            "Shared settings xdash_chakra_cost default must be 0 through 100 "
            "in steps of 5"
        )
    return value


def xdash_chakra_cost_option_default(selection: CatalogSelection) -> int:
    return xdash_chakra_cost_default(selection) // 5


def support_default(selection: CatalogSelection) -> int:
    return _toggle_default(selection, "support")


def battle_settings_runtime_fragment(
    selection: CatalogSelection,
    *,
    owner: str,
    symbol: str = "battle_settings_runtime_config",
) -> PayloadFragment | None:
    node = _selected_node(selection, SHARED_SETTINGS_PATH)
    if not node.enabled:
        return None
    practice = _selected_node(selection, PRACTICE_SETTINGS_PATH)
    if not practice.enabled:
        raise ValueError(
            "features.settings.shared requires features.settings.practice"
        )
    return PayloadFragment(
        owner=owner,
        symbol=symbol,
        kind="rodata",
        alignment=4,
        payload=struct.pack(
            "<6I",
            ultimate_jutsu_default(selection),
            shadowblur_default(selection),
            extra_hit_default(selection),
            sub_active_frames_default(selection),
            xdash_chakra_cost_default(selection),
            support_default(selection),
        ),
    )
