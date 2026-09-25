"""Presentation and runtime bindings for configurable menu values."""
from __future__ import annotations

from na228_builder.patches.localization.mod_strings import Message, message

from dataclasses import dataclass
from decimal import Decimal

from ..battle_mechanics.battle_settings_runtime import (
    BATTLE_MECHANICS_PATH,
    battle_mechanic_enabled,
)
from ..battle_mechanics.substitution.substitution_gauge import gauge_option_defaults, chakra_minimum_option_default
from ..battle_mechanics.items.items_settings import FIELD_ITEMS, ITEM_VALUE_LABELS, items_configuration, items_option_defaults


MOD_SETTINGS_PATH = ("features", "default_settings", "mod_settings")


@dataclass(frozen=True)
class MenuOption:
    label: Message | str | None
    help: Message | str | None
    values: tuple[Message | str, ...]
    default: int
    getter: str
    setter: str
    argument: int
    availability: int = 0
    flags: int = 0
    label_reference: int | None = None
    help_reference: int | None = None
    values_reference: int | None = None
    option_count: int | None = None
    enabled_by: tuple[str, int] | None = None

    @property
    def count(self) -> int:
        return self.option_count if self.option_count is not None else len(self.values)


PAGE_TITLES = {
    BATTLE_MECHANICS_PATH + ("substitution", "chakra"): message("page.chakra.heading"),
    BATTLE_MECHANICS_PATH + ("substitution", "gauge"): message("page.gauge.heading"),
    BATTLE_MECHANICS_PATH + ("items", "custom"): message("page.items.heading"),
}


def items_mode_option(selection):
    return MenuOption(message("settings.items.label"), message("settings.items.help"),
                      ITEM_VALUE_LABELS, items_option_defaults(selection)[0],
                      "items_settings_option_get", "items_settings_option_set", 0)


def menu_option_bindings(selection):
    """Bind leaf paths to existing gameplay handlers; page topology lives in the catalog."""
    options = {}
    selected = {node.path: node for node in selection.nodes}

    def configured_index(path, values):
        value = selected[path].configured_value
        try:
            return values.index(value)
        except ValueError as error:
            raise ValueError(
                f"Invalid Mod Settings value for {'.'.join(path)}: {value!r}"
            ) from error

    mod_rows = (
        ("controls", message("settings.control_scheme.label"),
         message("settings.control_scheme.help"),
         ("classic", "updated"), (message("common.classic"), message("common.updated"))),
        ("simple_display", message("settings.simple_display.label"),
         message("settings.simple_display.help"),
         ("off", "on"), (message("common.off"), message("common.on"))),
        ("character_balance", message("settings.character_balance.label"),
         message("settings.character_balance.help"),
         ("original", "overrides"), (message("common.original"), message("common.overrides"))),
        ("balance_overlay", message("settings.balance_overlay.label"),
         message("settings.balance_overlay.help"),
         ("off", "on"), (message("common.off"), message("common.on"))),
        ("support_selection", message("settings.support_selection.label"),
         message("settings.support_selection.help"),
         ("none", "relevant", "all"), (message("common.none"), message("common.relevant"), message("common.all"))),
    )
    for argument, (key, label, help_text, values, labels) in enumerate(mod_rows):
        path = MOD_SETTINGS_PATH + (key,)
        options[path] = MenuOption(
            label, help_text, labels, configured_index(path, values),
            "mod_settings_option_get", "mod_settings_option_set", argument,
        )

    if battle_mechanic_enabled(selection, "substitution"):
        options[BATTLE_MECHANICS_PATH + ("substitution", "chakra", "minimum_chakra")] = MenuOption(
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
            ("damage_percent_per_stock", message("settings.damage_percent.label"), message("settings.damage_percent.help"),
             tuple(f"{Decimal(i) / 4:.2f}%" for i in range(1, 401))),
        )
        for index, (key, label, help_text, values) in enumerate(rows):
            options[BATTLE_MECHANICS_PATH + ("substitution", "gauge", key)] = MenuOption(
                label, help_text, values, defaults[index],
                "substitution_gauge_option_get", "substitution_gauge_option_set", index,
                enabled_by=("substitution_gauge_option_get", 2)
                if key == "damage_percent_per_stock" else None)
    if items_configuration(selection) is not None:
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
