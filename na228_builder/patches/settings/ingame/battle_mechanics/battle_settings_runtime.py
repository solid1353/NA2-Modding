from __future__ import annotations

from na228_builder.patches.localization.mod_strings import message

import struct
from decimal import Decimal
from typing import TYPE_CHECKING

from na228_builder.infrastructure.modules.payload_builder.operations import PayloadFragment

if TYPE_CHECKING:
    from na228_builder.infrastructure.orchestration.catalog import CatalogSelection


BATTLE_MECHANICS_PATH = ("features", "defaults", "battle_mechanics")
PRACTICE_SETTINGS_PATH = ("features", "defaults", "practice_settings")
MATCH_SETUP_PATH = ("features", "defaults", "match_setup")
EXTENDED_ITEMS_PATH = MATCH_SETUP_PATH + ("extended_items",)
SUBSTITUTION_INPUT_LABELS = (
    message("common.default"),
    message("settings.substitution_input.hold"),
    message("settings.frame", frames=1),
    *(message("settings.frames", frames=value) for value in range(2, 16)),
)

CHAKRA_MODE_VALUES = {
    "normal": 0,
    "unlimited": 1,
}
CHAKRA_REGEN_OPTION_OFFSET = 1
CHAKRA_STATIC_LABELS = (
    "mod_text_common__normal",
    "mod_text_common__unlimited",
)
CHAKRA_REGEN_LABELS = tuple(
    message("settings.chakra.regen", rate=f"{tenths // 10}.{tenths % 10}")
    for tenths in range(1, 101)
)

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

SUPPORT_MODE_VALUES = {"off": 0, "nerfed": 1, "normal": 2, "unlimited": 3}
SUPPORT_LABELS = (message("common.off"), message("common.nerfed"), message("common.normal"), message("common.unlimited"))
EXTRA_HIT_LABELS = (message("common.off"), message("common.on"), *(message("settings.extra_hit.cost", cost=value) for value in range(5, 101, 5)))
XDASH_CHAKRA_COST_LABELS = tuple(f"{value}%" for value in range(0, 101, 5))

TOGGLE_MODE_VALUES = {
    "off": 0,
    "on": 1,
}
SUBSTITUTION_MODE_VALUES = {
    "chakra": 0,
    "gauge": 1,
    "free": 2,
}


def _mechanic(selection: CatalogSelection, field: str) -> object:
    return selection.node(*BATTLE_MECHANICS_PATH, field).configured_value


def ultimate_jutsu_default(selection: CatalogSelection) -> int:
    return ULTIMATE_JUTSU_MODE_VALUES[_mechanic(selection, "ultimate_jutsu")]


def chakra_default(selection: CatalogSelection) -> int:
    value = _mechanic(selection, "chakra")
    if value in CHAKRA_MODE_VALUES:
        return CHAKRA_MODE_VALUES[value]
    return int(Decimal(str(value)) * 10) + CHAKRA_REGEN_OPTION_OFFSET


def shadowblur_default(selection: CatalogSelection) -> int:
    return TOGGLE_MODE_VALUES[_mechanic(selection, "shadowblur")]


def extra_hit_default(selection: CatalogSelection) -> int:
    value = _mechanic(selection, "extra_hit")
    if value in TOGGLE_MODE_VALUES:
        return TOGGLE_MODE_VALUES[value]
    if not isinstance(value, int):
        raise ValueError(
            "Extra Hit must be 'off', 'on', or -5 through -100 in steps of 5"
        )
    return 1 - value // 5


def substitution_input_default(selection: CatalogSelection) -> int:
    value = _mechanic(selection, "substitution_input")
    if value == "default":
        return 0
    if value == "hold":
        return 1
    if not isinstance(value, int):
        raise ValueError(
            "Mod settings substitution_input must be 'default', 'hold', or 1 through 15"
        )
    return value + 1


def substitution_default(selection: CatalogSelection) -> int:
    return SUBSTITUTION_MODE_VALUES[_mechanic(selection, "substitution_resource")["value"]]


def xdash_chakra_cost_default(selection: CatalogSelection) -> int:
    value = _mechanic(selection, "xdash_chakra_cost")
    if not isinstance(value, int):
        raise ValueError(
            "Mod settings xdash_chakra_cost default must be 0 through 100 "
            "in steps of 5"
        )
    return value


def xdash_chakra_cost_option_default(selection: CatalogSelection) -> int:
    return xdash_chakra_cost_default(selection) // 5


def support_default(selection: CatalogSelection) -> int:
    return SUPPORT_MODE_VALUES[_mechanic(selection, "support")]


def extended_items_option_default(selection: CatalogSelection) -> int:
    return int(selection.node(*EXTENDED_ITEMS_PATH).configured_value == "on")


def battle_settings_runtime_fragments(
    selection: CatalogSelection,
    *,
    owner: str,
) -> tuple[PayloadFragment, ...]:
    defaults = (
        ("battle_settings_chakra_default", chakra_default),
        ("battle_settings_ultimate_jutsu_default", ultimate_jutsu_default),
        ("battle_settings_shadowblur_default", shadowblur_default),
        ("battle_settings_extra_hit_default", extra_hit_default),
        ("battle_settings_substitution_input_default", substitution_input_default),
        ("battle_settings_xdash_chakra_cost_default", xdash_chakra_cost_default),
        ("battle_settings_support_default", support_default),
        ("extended_items_default", extended_items_option_default),
    )
    return tuple(
        PayloadFragment(
            owner=owner,
            symbol=symbol,
            kind="rodata",
            alignment=4,
            payload=struct.pack("<I", resolver(selection)),
        )
        for symbol, resolver in defaults
    )
