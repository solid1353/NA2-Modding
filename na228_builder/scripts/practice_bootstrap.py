from __future__ import annotations

import struct
from typing import TYPE_CHECKING

from ..payload_builder.operations import PayloadFragment

if TYPE_CHECKING:
    from .catalog import CatalogSelection


PRACTICE_BOOTSTRAP_PATH = ("features", "qol", "practice", "bootstrap")
PRACTICE_BOOTSTRAP_VERSION = 1
PRACTICE_BOOTSTRAP_NO_AWAKENING = 0xFFFFFFFF
PRACTICE_BOOTSTRAP_MAX_AWAKENING_ID = 0x89


def practice_bootstrap_fragment(
    selection: CatalogSelection,
    *,
    owner: str,
    symbol: str = "practice_bootstrap_configuration",
) -> PayloadFragment | None:
    """Encode the selected Practice bootstrap inputs for the resident hook."""

    matches = [
        node for node in selection.nodes if node.path == PRACTICE_BOOTSTRAP_PATH
    ]
    if len(matches) != 1:
        raise ValueError("Catalog selection has no unique Practice bootstrap node")
    node = matches[0]
    if not node.enabled:
        return None
    if not node.has_configured_value or not isinstance(node.configured_value, dict):
        raise ValueError("Practice bootstrap requires a configured object value")

    value = node.configured_value
    expected_keys = {"p1", "support", "awakening"}
    if set(value) != expected_keys:
        raise ValueError(
            "Practice bootstrap keys must be: awakening, p1, support"
        )
    p1 = value["p1"]
    support = value["support"]
    awakening = value["awakening"]
    if isinstance(p1, bool) or not isinstance(p1, int) or not 1 <= p1 <= 93:
        raise ValueError("Practice bootstrap p1 must be a character ID from 1 through 93")
    if (
        isinstance(support, bool)
        or not isinstance(support, int)
        or not 0 <= support <= 0x25
    ):
        raise ValueError("Practice bootstrap support must be a support ID from 0 through 37")
    if awakening == "none":
        awakening_id = PRACTICE_BOOTSTRAP_NO_AWAKENING
    elif (
        isinstance(awakening, bool)
        or not isinstance(awakening, int)
        or not 0 <= awakening <= PRACTICE_BOOTSTRAP_MAX_AWAKENING_ID
    ):
        raise ValueError(
            "Practice bootstrap awakening must be none or an awakening ID from 0 through 137"
        )
    else:
        awakening_id = awakening

    return PayloadFragment(
        owner=owner,
        symbol=symbol,
        kind="rodata",
        alignment=4,
        payload=struct.pack(
            "<4I",
            PRACTICE_BOOTSTRAP_VERSION,
            p1,
            support,
            awakening_id,
        ),
    )
