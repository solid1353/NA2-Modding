from __future__ import annotations

import math
import struct
from typing import TYPE_CHECKING

from ..payload_builder.operations import PayloadFragment

if TYPE_CHECKING:
    from .catalog import CatalogSelection


XDASH_CHAKRA_COST_PATH = (
    "features",
    "battle_logic",
    "xdash_chakra_cost",
)


def xdash_chakra_cost_fragment(
    selection: CatalogSelection,
    *,
    owner: str,
    symbol: str = "battle_logic_xdash_chakra_cost",
) -> PayloadFragment | None:
    """Encode the configured X-dash chakra cost for the resident hook."""

    matches = [
        node for node in selection.nodes if node.path == XDASH_CHAKRA_COST_PATH
    ]
    if len(matches) != 1:
        raise ValueError("Catalog selection has no unique X-dash chakra-cost node")
    node = matches[0]
    if not node.enabled:
        return None
    value = node.configured_value
    if (
        not node.has_configured_value
        or isinstance(value, bool)
        or not isinstance(value, (int, float))
    ):
        raise ValueError("X-dash chakra cost requires a configured number")
    cost = float(value)
    if not math.isfinite(cost) or not 0.0 <= cost <= 15.0:
        raise ValueError("X-dash chakra cost must be from 0 through 15")

    return PayloadFragment(
        owner=owner,
        symbol=symbol,
        kind="rodata",
        alignment=4,
        payload=struct.pack("<f", cost),
    )
