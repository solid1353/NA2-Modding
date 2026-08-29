from __future__ import annotations

import struct
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import TYPE_CHECKING

from ..payload_builder.operations import PayloadFragment
from .battle_settings_runtime import PRACTICE_SETTINGS_PATH, SHARED_SETTINGS_PATH

if TYPE_CHECKING:
    from .catalog import CatalogSelection


CHARACTER_OVERRIDES_PATH = (
    "features",
    "general",
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

    node = _selected_node(selection, SHARED_SETTINGS_PATH)
    if not node.enabled:
        return None
    character_overrides = _selected_node(selection, CHARACTER_OVERRIDES_PATH)
    if not character_overrides.enabled:
        raise ValueError(
            "features.settings.shared.substitution requires "
            "features.general.character_overrides"
        )
    practice_settings = _selected_node(selection, PRACTICE_SETTINGS_PATH)
    if not practice_settings.enabled:
        raise ValueError(
            "features.settings.shared.substitution requires "
            "features.settings.practice"
        )

    value = node.configured_value
    if not node.has_configured_value or not isinstance(value, dict):
        raise ValueError("Shared settings requires an object value")
    substitution = value.get("substitution")
    if not isinstance(substitution, dict):
        raise ValueError("Shared settings substitution requires an object value")
    default = substitution.get("default")
    if default not in SUBSTITUTION_MODE_VALUES:
        raise ValueError(
            "Substitution-gauge default must be 'chakra', 'gauge', or 'free'"
        )
    recovery_delay = _decimal(
        substitution.get(
            "recovery_delay_seconds", DEFAULT_RECOVERY_DELAY_SECONDS
        ),
        "Substitution-gauge recovery delay",
    )
    refill_seconds = _decimal(
        substitution.get(
            "refill_seconds_per_stock", DEFAULT_REFILL_SECONDS_PER_STOCK
        ),
        "Substitution-gauge refill time",
    )
    damage_percent = _decimal(
        substitution.get(
            "damage_percent_per_stock", DEFAULT_DAMAGE_PERCENT_PER_STOCK
        ),
        "Substitution-gauge damage threshold",
    )
    damage_recovery = substitution.get(
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

    return PayloadFragment(
        owner=owner,
        symbol=symbol,
        kind="rodata",
        alignment=4,
        payload=struct.pack(
            "<6I",
            stock_counts,
            capacity_counts,
            delay_counts,
            damage_threshold_q16,
            int(damage_recovery),
            SUBSTITUTION_MODE_VALUES[default],
        ),
    )
