"""Presentation and runtime bindings for configurable menu values."""
from __future__ import annotations

from na228_builder.patches.localization.mod_strings import Message, message

from dataclasses import dataclass
from decimal import Decimal

from ..battle_mechanics.battle_settings_runtime import (
    BATTLE_MECHANICS_PATH,
    EXTENDED_ITEMS_PATH,
    MATCH_SETUP_PATH,
    extended_items_option_default,
)
from ..battle_mechanics.substitution_resource.substitution_gauge import gauge_option_defaults, chakra_minimum_option_default
from ..battle_mechanics.items.items_settings import FIELD_ITEMS, ITEM_VALUE_LABELS, items_option_defaults


MOD_SETTINGS_PATH = ("features", "defaults", "mod_settings")
# Mod Settings values in their runtime argument order, with their choices.
MOD_SETTING_VALUES = (
    (MOD_SETTINGS_PATH + ("simple_display",), ("off", "on")),
    (MATCH_SETUP_PATH + ("character_balance",), ("original", "overrides")),
    (MATCH_SETUP_PATH + ("balance_overlay",), ("off", "on")),
    (MATCH_SETUP_PATH + ("support_selection",), ("none", "relevant", "all")),
)


@dataclass(frozen=True)
class MenuOption:
    label: Message | str | None
    help: Message | str | None
    values: tuple[Message | str, ...]
    default: int
    getter: str
    setter: str
    argument: int
    label_reference: int | None = None
    help_reference: int | None = None
    values_reference: int | None = None
    option_count: int | None = None
    enabled_by: tuple[str, int] | None = None

    @property
    def count(self) -> int:
        return self.option_count if self.option_count is not None else len(self.values)


PAGE_TITLES = {
    BATTLE_MECHANICS_PATH + ("substitution_resource", "chakra"): message("page.chakra.heading"),
    BATTLE_MECHANICS_PATH + ("substitution_resource", "gauge"): message("page.gauge.heading"),
    BATTLE_MECHANICS_PATH + ("items", "custom"): message("page.items.heading"),
}


def mod_setting_values(selection) -> tuple[int, ...]:
    return tuple(choices.index(selection.node(*path).configured_value)
                 for path, choices in MOD_SETTING_VALUES)


def items_mode_option(selection):
    return MenuOption(message("settings.items.label"), message("settings.items.help"),
                      ITEM_VALUE_LABELS, items_option_defaults(selection)[0],
                      "items_settings_option_get", "items_settings_option_set", 0)


def menu_option_bindings(selection):
    """Bind leaf paths to existing gameplay handlers; page topology lives in the catalog."""
    options = {}
    for argument, ((path, choices), default) in enumerate(
            zip(MOD_SETTING_VALUES, mod_setting_values(selection))):
        options[path] = MenuOption(
            message(f"settings.{path[-1]}.label"), message(f"settings.{path[-1]}.help"),
            tuple(message(f"common.{choice}") for choice in choices), default,
            "mod_settings_option_get", "mod_settings_option_set", argument,
        )

    options[BATTLE_MECHANICS_PATH + ("substitution_resource", "chakra", "minimum_chakra")] = MenuOption(
        message("settings.minimum_chakra.label"), message("settings.minimum_chakra.help"),
        (message("settings.minimum_chakra.match_cost"), *(f"{value}%" for value in range(5, 101, 5))),
        chakra_minimum_option_default(selection),
        "substitution_gauge_option_get", "substitution_gauge_option_set", 4)
    defaults = gauge_option_defaults(selection)
    rows = (
        ("recovery_delay_seconds", message("settings.recovery_delay.label"), message("settings.recovery_delay.help"),
         tuple(message("settings.seconds", seconds=f"{Decimal(i) / 4:.2f}") for i in range(241))),
        ("refill_seconds_per_stock", message("settings.refill_time.label"), message("settings.refill_time.help"),
         tuple(message("settings.seconds", seconds=f"{Decimal(i) / 20:.2f}") for i in range(1, 201))),
        ("damage_recovery", message("settings.damage_recovery.label"), message("settings.damage_recovery.help"), (message("common.off"), message("common.on"))),
        ("damage_percent_for_full_refill", message("settings.damage_full_refill.label"), message("settings.damage_full_refill.help"),
         tuple(f"{i * 5}%" for i in range(1, 81))),
    )
    for index, (key, label, help_text, values) in enumerate(rows):
        options[BATTLE_MECHANICS_PATH + ("substitution_resource", "gauge", key)] = MenuOption(
            label, help_text, values, defaults[index],
            "substitution_gauge_option_get", "substitution_gauge_option_set", index,
            enabled_by=("substitution_gauge_option_get", 2)
            if key == "damage_percent_for_full_refill" else None)
    options[EXTENDED_ITEMS_PATH] = MenuOption(
        message("settings.extended_items.label"), message("settings.extended_items.help"),
        (message("common.off"), message("common.on")), extended_items_option_default(selection),
        "extended_items_option_get", "extended_items_option_set", 0)
    defaults = items_option_defaults(selection)
    custom_path = BATTLE_MECHANICS_PATH + ("items", "custom")
    options[custom_path + ("availability",)] = MenuOption(
        message("settings.availability.label"), message("settings.availability.help"),
        ITEM_VALUE_LABELS[:4], defaults[1],
        "items_settings_option_get", "items_settings_option_set", 1)
    for index, (_code, key, label) in enumerate(FIELD_ITEMS):
        options[custom_path + (key,)] = MenuOption(
            label, message("settings.item.help", item=label), (message("common.off"), message("common.on")), defaults[index + 2],
            "items_settings_option_get", "items_settings_option_set", index + 2,
            enabled_by=("items_settings_option_get", 1))
    return options
