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
CHAKRA_REGEN_MIN = Decimal("0.1")
CHAKRA_REGEN_MAX = Decimal("10.0")
CHAKRA_REGEN_STEP = Decimal("0.1")
CHAKRA_REGEN_OPTION_OFFSET = 1
CHAKRA_OPTION_COUNT = 102
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


def battle_mechanic_path(field: str) -> tuple[str, ...]:
    return (*BATTLE_MECHANICS_PATH, field)


def _battle_mechanic_value(selection: CatalogSelection, field: str) -> object:
    return _selected_node(selection, battle_mechanic_path(field)).configured_value


def ultimate_jutsu_default(selection: CatalogSelection) -> int:
    value = _battle_mechanic_value(selection, "ultimate_jutsu")
    if value not in ULTIMATE_JUTSU_MODE_VALUES:
        raise ValueError("Mod settings requires an Ultimate Jutsu default")
    return ULTIMATE_JUTSU_MODE_VALUES[value]


def chakra_default(selection: CatalogSelection) -> int:
    value = _battle_mechanic_value(selection, "chakra")
    if isinstance(value, str) and value in CHAKRA_MODE_VALUES:
        return CHAKRA_MODE_VALUES[value]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(
            "Mod settings chakra default must be 'normal', 'unlimited', or "
            "0.1 through 10.0 in steps of 0.1"
        )
    rate = Decimal(str(value))
    if (
        not CHAKRA_REGEN_MIN <= rate <= CHAKRA_REGEN_MAX
        or rate % CHAKRA_REGEN_STEP != 0
    ):
        raise ValueError(
            "Mod settings chakra default must be 'normal', 'unlimited', or "
            "0.1 through 10.0 in steps of 0.1"
        )
    return int(rate / CHAKRA_REGEN_STEP) + CHAKRA_REGEN_OPTION_OFFSET


def _toggle_default(selection: CatalogSelection, field: str) -> int:
    value = _battle_mechanic_value(selection, field)
    if value not in TOGGLE_MODE_VALUES:
        raise ValueError(
            f"Mod settings {field} default must be 'off' or 'on'"
        )
    return TOGGLE_MODE_VALUES[value]


def shadowblur_default(selection: CatalogSelection) -> int:
    return _toggle_default(selection, "shadowblur")


def extra_hit_default(selection: CatalogSelection) -> int:
    value = _battle_mechanic_value(selection, "extra_hit")
    if isinstance(value, str) and value in TOGGLE_MODE_VALUES:
        return TOGGLE_MODE_VALUES[value]
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not -100 <= value <= -5
        or value % 5 != 0
    ):
        raise ValueError(
            "Extra Hit must be 'off', 'on', or -5 through -100 in steps of 5"
        )
    return 1 - value // 5


def substitution_input_default(selection: CatalogSelection) -> int:
    value = _battle_mechanic_value(selection, "substitution_input")
    if value == "default":
        return 0
    if value == "hold":
        return 1
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 15:
        raise ValueError(
            "Mod settings substitution_input must be 'default', 'hold', or 1 through 15"
        )
    return value + 1


def substitution_default(selection: CatalogSelection) -> int:
    value = _battle_mechanic_value(selection, "substitution_resource")
    if not isinstance(value, dict):
        raise ValueError("Mod settings substitution requires an object value")
    mode = value.get("value")
    if mode not in SUBSTITUTION_MODE_VALUES:
        raise ValueError(
            "Mod settings substitution value must be 'chakra', 'gauge', "
            "or 'free'"
        )
    return SUBSTITUTION_MODE_VALUES[mode]


def xdash_chakra_cost_default(selection: CatalogSelection) -> int:
    value = _battle_mechanic_value(selection, "xdash_chakra_cost")
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 100
        or value % 5 != 0
    ):
        raise ValueError(
            "Mod settings xdash_chakra_cost default must be 0 through 100 "
            "in steps of 5"
        )
    return value


def xdash_chakra_cost_option_default(selection: CatalogSelection) -> int:
    return xdash_chakra_cost_default(selection) // 5


def support_default(selection: CatalogSelection) -> int:
    value = _battle_mechanic_value(selection, "support")
    return SUPPORT_MODE_VALUES[value]


def extended_items_option_default(selection: CatalogSelection) -> int:
    return int(_selected_node(selection, EXTENDED_ITEMS_PATH).configured_value == "on")


def battle_settings_runtime_fragments(
    selection: CatalogSelection,
    *,
    owner: str,
) -> tuple[PayloadFragment, ...]:
    definitions = (
        ("chakra", "battle_settings_chakra_default", chakra_default),
        (
            "ultimate_jutsu",
            "battle_settings_ultimate_jutsu_default",
            ultimate_jutsu_default,
        ),
        ("shadowblur", "battle_settings_shadowblur_default", shadowblur_default),
        ("extra_hit", "battle_settings_extra_hit_default", extra_hit_default),
        (
            "substitution_input",
            "battle_settings_substitution_input_default",
            substitution_input_default,
        ),
        (
            "xdash_chakra_cost",
            "battle_settings_xdash_chakra_cost_default",
            xdash_chakra_cost_default,
        ),
        ("support", "battle_settings_support_default", support_default),
    )
    return tuple(
        PayloadFragment(
            owner=owner,
            symbol=symbol,
            kind="rodata",
            alignment=4,
            payload=struct.pack("<I", resolver(selection)),
        )
        for _field, symbol, resolver in definitions
    ) + (
        PayloadFragment(
            owner=owner,
            symbol="extended_items_default",
            kind="rodata",
            alignment=4,
            payload=struct.pack("<I", extended_items_option_default(selection)),
        ),
    )
