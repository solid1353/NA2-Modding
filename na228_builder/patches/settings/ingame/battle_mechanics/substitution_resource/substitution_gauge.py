from __future__ import annotations

import struct
from decimal import Decimal, ROUND_HALF_UP
from typing import TYPE_CHECKING

from na228_builder.infrastructure.modules.payload_builder.operations import PayloadFragment, PayloadRelocation
from ..battle_settings_runtime import BATTLE_MECHANICS_PATH, substitution_default

if TYPE_CHECKING:
    from na228_builder.infrastructure.orchestration.catalog import CatalogSelection


DEFAULT_RECOVERY_DELAY_SECONDS = Decimal("14.0")
DEFAULT_REFILL_SECONDS_PER_STOCK = Decimal("1.0")
DEFAULT_DAMAGE_PERCENT_FOR_FULL_REFILL = Decimal("125")
DEFAULT_DAMAGE_RECOVERY = "on"
COUNTS_PER_SECOND = Decimal(60)
STOCK_COUNT = 4
Q16_ONE = Decimal(65536)


def _substitution(selection: CatalogSelection) -> dict[str, object]:
    return selection.node(*BATTLE_MECHANICS_PATH, "substitution_resource").configured_value


def substitution_gauge_fragment(
    selection: CatalogSelection,
    *,
    owner: str,
) -> PayloadFragment:
    """Encode the selected native-30-FPS substitution-gauge configuration."""

    stock_counts, capacity_counts, delay_counts, damage_full_refill_q16, damage_recovery = gauge_config_values(selection)

    return PayloadFragment(
        owner=owner,
        symbol="substitution_gauge_config",
        kind="rodata",
        alignment=4,
        payload=struct.pack(
            "<9I",
            stock_counts,
            capacity_counts,
            delay_counts,
            damage_full_refill_q16,
            int(damage_recovery),
            substitution_default(selection),
            chakra_minimum_option_default(selection),
            0,
            0,
        ),
        relocations=(
            PayloadRelocation(offset=28, kind="abs32", symbol="substitution_cost_for_fighter"),
            PayloadRelocation(offset=32, kind="abs32", symbol="substitution_cost_fraction_for_fighter"),
        ),
    )


def chakra_minimum_option_default(selection: CatalogSelection) -> int:
    value = _substitution(selection).get("chakra", {}).get("minimum_chakra", "match_cost")
    if value == "match_cost":
        return 0
    if not isinstance(value, int):
        raise ValueError("Minimum Chakra must be 'match_cost' or 5 through 100 in steps of 5")
    return value // 5


def gauge_config_values(selection: CatalogSelection) -> tuple[int, int, int, int, bool]:
    gauge = _substitution(selection).get("gauge", {})
    recovery_delay = Decimal(str(gauge.get(
        "recovery_delay_seconds", DEFAULT_RECOVERY_DELAY_SECONDS
    )))
    refill_seconds = Decimal(str(gauge.get(
        "refill_seconds_per_stock", DEFAULT_REFILL_SECONDS_PER_STOCK
    )))
    damage_percent = Decimal(str(gauge.get(
        "damage_percent_for_full_refill", DEFAULT_DAMAGE_PERCENT_FOR_FULL_REFILL
    )))
    damage_recovery = gauge.get("damage_recovery", DEFAULT_DAMAGE_RECOVERY)

    stock_counts = int(refill_seconds * COUNTS_PER_SECOND)
    delay_counts = int(recovery_delay * COUNTS_PER_SECOND)
    capacity_counts = stock_counts * STOCK_COUNT
    damage_full_refill_q16 = int(
        (
            damage_percent * Q16_ONE / Decimal(100)
        ).to_integral_value(rounding=ROUND_HALF_UP)
    )
    return stock_counts, capacity_counts, delay_counts, damage_full_refill_q16, damage_recovery == "on"


def gauge_option_defaults(selection: CatalogSelection) -> tuple[int, ...]:
    stock, _capacity, delay, threshold, damage = gauge_config_values(selection)
    return delay // 15, stock // 3 - 1, int(damage), (threshold * 20 + 32768) // 65536 - 1
