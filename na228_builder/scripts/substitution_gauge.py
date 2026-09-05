from __future__ import annotations

import struct
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import TYPE_CHECKING

from ..payload_builder.operations import PayloadFragment, PayloadRelocation
from .battle_settings_runtime import PRACTICE_SETTINGS_PATH, battle_mechanic_path

if TYPE_CHECKING:
    from .catalog import CatalogSelection


CHARACTER_OVERRIDES_PATH = (
    "features",
    "settings",
    "character_overrides",
)
DEFAULT_RECOVERY_DELAY_SECONDS = Decimal("14.0")
DEFAULT_REFILL_SECONDS_PER_STOCK = Decimal("1.0")
DEFAULT_DAMAGE_PERCENT_PER_STOCK = Decimal("31.25")
DEFAULT_DAMAGE_RECOVERY = True
COUNTS_PER_SECOND = Decimal(60)
STOCK_COUNT = 4
Q16_ONE = Decimal(65536)
SUBSTITUTION_MODE_VALUES = {
    "chakra": 0,
    "gauge": 1,
    "free": 2,
}


def _selected_node(selection: CatalogSelection, path: tuple[str, ...]):
    matches = [node for node in selection.nodes if node.path == path]
    if len(matches) != 1:
        raise ValueError(
            f"Catalog selection has no unique {'.'.join(path)} node"
        )
    return matches[0]


def _decimal(value: object, label: str) -> Decimal:
    if isinstance(value, Decimal):
        parsed = value
    elif isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a decimal number")
    else:
        try:
            parsed = Decimal(str(value))
        except InvalidOperation as exc:
            raise ValueError(f"{label} must be a finite decimal number") from exc
    if not parsed.is_finite():
        raise ValueError(f"{label} must be a finite decimal number")
    return parsed


def _integral_counts(value: Decimal, label: str) -> int:
    counts = value * COUNTS_PER_SECOND
    integral = counts.to_integral_value()
    if counts != integral:
        raise ValueError(f"{label} must resolve to whole native display counts")
    return int(integral)


def _require_step(value: Decimal, step: Decimal, label: str) -> None:
    if value % step != 0:
        raise ValueError(f"{label} must use increments of {step}")


def substitution_gauge_fragment(
    selection: CatalogSelection,
    *,
    owner: str,
    symbol: str = "substitution_gauge_config",
) -> PayloadFragment | None:
    """Encode the selected native-30-FPS substitution-gauge configuration."""

    node = _selected_node(selection, battle_mechanic_path("substitution"))
    if not node.enabled:
        return None
    character_overrides = _selected_node(selection, CHARACTER_OVERRIDES_PATH)
    practice_settings = _selected_node(selection, PRACTICE_SETTINGS_PATH)
    if not practice_settings.enabled:
        raise ValueError(
            "features.settings.ingame.battle_mechanics.substitution requires "
            "features.settings.ingame.practice_mode"
        )

    substitution = node.configured_value
    if not node.has_configured_value or not isinstance(substitution, dict):
        raise ValueError("Mod settings substitution requires an object value")
    mode = substitution.get("value")
    if mode not in SUBSTITUTION_MODE_VALUES:
        raise ValueError(
            "Substitution-gauge value must be 'chakra', 'gauge', or 'free'"
        )
    stock_counts, capacity_counts, delay_counts, damage_threshold_q16, damage_recovery = gauge_config_values(selection)

    return PayloadFragment(
        owner=owner,
        symbol=symbol,
        kind="rodata",
        alignment=4,
        payload=struct.pack(
            "<9I",
            stock_counts,
            capacity_counts,
            delay_counts,
            damage_threshold_q16,
            int(damage_recovery),
            SUBSTITUTION_MODE_VALUES[mode],
            chakra_minimum_option_default(selection),
            0,
            0,
        ),
        relocations=(
            PayloadRelocation(offset=28, kind="abs32", symbol="substitution_cost_for_fighter"),
            PayloadRelocation(offset=32, kind="abs32", symbol="substitution_cost_fraction_for_fighter"),
        ) if character_overrides.enabled else (),
    )


def chakra_minimum_option_default(selection: CatalogSelection) -> int:
    substitution = _selected_node(selection, battle_mechanic_path("substitution")).configured_value
    value = substitution.get("chakra", {}).get("minimum_chakra", "match_cost")
    if value == "match_cost":
        return 0
    if (
        isinstance(value, bool) or not isinstance(value, int)
        or not 5 <= value <= 100 or value % 5 != 0
    ):
        raise ValueError("Minimum Chakra must be 'match_cost' or 5 through 100 in steps of 5")
    return value // 5


def gauge_config_values(selection: CatalogSelection) -> tuple[int, int, int, int, bool]:
    substitution = _selected_node(selection, battle_mechanic_path("substitution")).configured_value
    gauge = substitution.get("gauge", {})
    recovery_delay = _decimal(
        gauge.get(
            "recovery_delay_seconds", DEFAULT_RECOVERY_DELAY_SECONDS
        ),
        "Substitution-gauge recovery delay",
    )
    refill_seconds = _decimal(
        gauge.get(
            "refill_seconds_per_stock", DEFAULT_REFILL_SECONDS_PER_STOCK
        ),
        "Substitution-gauge refill time",
    )
    damage_percent = _decimal(
        gauge.get(
            "damage_percent_per_stock", DEFAULT_DAMAGE_PERCENT_PER_STOCK
        ),
        "Substitution-gauge damage threshold",
    )
    damage_recovery = gauge.get(
        "damage_recovery", DEFAULT_DAMAGE_RECOVERY
    )
    if not isinstance(damage_recovery, bool):
        raise ValueError("Substitution-gauge damage recovery must be Boolean")

    if not Decimal(0) <= recovery_delay <= Decimal(60):
        raise ValueError("Substitution-gauge recovery delay must be from 0 through 60")
    if not Decimal(0) < refill_seconds <= Decimal(10):
        raise ValueError("Substitution-gauge refill time must be above 0 through 10")
    if not Decimal(0) < damage_percent <= Decimal(100):
        raise ValueError(
            "Substitution-gauge damage threshold must be above 0 through 100"
        )
    _require_step(recovery_delay, Decimal("0.25"), "Recovery delay")
    _require_step(refill_seconds, Decimal("0.05"), "Refill time")
    _require_step(damage_percent, Decimal("0.25"), "Damage threshold")

    stock_counts = _integral_counts(refill_seconds, "Refill time")
    delay_counts = _integral_counts(recovery_delay, "Recovery delay")
    capacity_counts = stock_counts * STOCK_COUNT
    damage_threshold_q16 = int(
        (
            damage_percent * Q16_ONE / Decimal(100)
        ).to_integral_value(rounding=ROUND_HALF_UP)
    )
    if damage_threshold_q16 <= 0 or damage_threshold_q16 > int(Q16_ONE):
        raise ValueError("Substitution-gauge damage threshold is outside Q16 range")

    return stock_counts, capacity_counts, delay_counts, damage_threshold_q16, damage_recovery


def gauge_option_defaults(selection: CatalogSelection) -> tuple[int, ...]:
    stock, _capacity, delay, threshold, damage = gauge_config_values(selection)
    return delay // 15, stock // 3 - 1, int(damage), (threshold * 400 + 32768) // 65536 - 1
