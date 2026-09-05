"""Presentation and runtime bindings for configurable menu values."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .battle_settings_runtime import BATTLE_MECHANICS_PATH, battle_mechanic_enabled
from .substitution_gauge import gauge_option_defaults, chakra_minimum_option_default
from .items_settings import FIELD_ITEMS, ITEM_VALUE_LABELS, items_configuration, items_option_defaults


@dataclass(frozen=True)
class MenuOption:
    label: str
    help: str
    values: tuple[str, ...]
    default: int
    getter: str
    setter: str
    argument: int


PAGE_TITLES = {
    BATTLE_MECHANICS_PATH + ("substitution", "chakra"): "Chakra Settings",
    BATTLE_MECHANICS_PATH + ("substitution", "gauge"): "Gauge Settings",
    BATTLE_MECHANICS_PATH + ("items", "custom"): "Items Settings",
}


def items_mode_option(selection):
    return MenuOption("Items", "Choose item availability. Square opens Custom settings.",
                      ITEM_VALUE_LABELS, items_option_defaults(selection)[0],
                      "items_settings_option_get", "items_settings_option_set", 0)


def menu_option_bindings(selection):
    """Bind leaf paths to existing gameplay handlers; page topology lives in the catalog."""
    options = {}
    if battle_mechanic_enabled(selection, "substitution"):
        options[BATTLE_MECHANICS_PATH + ("substitution", "chakra", "minimum_chakra")] = MenuOption(
            "Minimum Chakra", "Required chakra to substitute. Match Cost follows the actual cost.",
            ("Match Cost", *(f"{value}%" for value in range(5, 101, 5))),
            chakra_minimum_option_default(selection),
            "substitution_gauge_option_get", "substitution_gauge_option_set", 4)
        defaults = gauge_option_defaults(selection)
        rows = (
            ("recovery_delay_seconds", "Recovery Delay", "Delay after substitution before automatic recovery.",
             tuple(f"{Decimal(i) / 4:.2f}s" for i in range(241))),
            ("refill_seconds_per_stock", "Refill Time per Stock", "Automatic recovery time for one stock.",
             tuple(f"{Decimal(i) / 20:.2f}s" for i in range(1, 201))),
            ("damage_recovery", "Damage Recovery", "Recover gauge when taking damage.", ("Off", "On")),
            ("damage_percent_per_stock", "Damage Percent per Stock", "Damage required to recover one stock.",
             tuple(f"{Decimal(i) / 4:.2f}%" for i in range(1, 401))),
        )
        for index, (key, label, help_text, values) in enumerate(rows):
            options[BATTLE_MECHANICS_PATH + ("substitution", "gauge", key)] = MenuOption(
                label, help_text, values, defaults[index],
                "substitution_gauge_option_get", "substitution_gauge_option_set", index)
    if items_configuration(selection) is not None:
        defaults = items_option_defaults(selection)
        custom_path = BATTLE_MECHANICS_PATH + ("items", "custom")
        options[custom_path + ("availability",)] = MenuOption(
            "Availability", "Choose the amount of items in Custom mode.",
            ITEM_VALUE_LABELS[:4], defaults[1],
            "items_settings_option_get", "items_settings_option_set", 1)
        for index, (_code, key, label) in enumerate(FIELD_ITEMS):
            options[custom_path + (key,)] = MenuOption(
                label, f"Allow {label} in Custom mode.", ("Off", "On"), defaults[index + 2],
                "items_settings_option_get", "items_settings_option_set", index + 2)
    return options
