from __future__ import annotations

import struct
from typing import TYPE_CHECKING

from ..payload_builder.operations import PayloadFragment

if TYPE_CHECKING:
    from .catalog import CatalogSelection


UNLOCK_ALL_PATH = ("features", "general", "unlock_all")


def unlock_all_configuration_fragment(
    selection: CatalogSelection,
    *,
    owner: str,
    symbol: str = "unlock_all_demon_wind_bomb_enabled",
) -> PayloadFragment | None:
    matches = [node for node in selection.nodes if node.path == UNLOCK_ALL_PATH]
    if len(matches) != 1:
        raise ValueError("Catalog selection has no unique general.unlock_all node")
    node = matches[0]
    if not node.enabled:
        return None
    if not node.has_configured_value or not isinstance(node.configured_value, dict):
        raise ValueError("General unlock_all requires an object value")
    enabled = node.configured_value.get("demon_wind_bomb", False)
    if not isinstance(enabled, bool):
        raise ValueError("General unlock_all.demon_wind_bomb must be boolean")
    return PayloadFragment(
        owner=owner,
        symbol=symbol,
        kind="rodata",
        alignment=4,
        payload=struct.pack("<I", int(enabled)),
    )
