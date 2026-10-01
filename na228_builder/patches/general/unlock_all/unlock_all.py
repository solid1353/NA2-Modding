from __future__ import annotations

import struct
from typing import TYPE_CHECKING

from na228_builder.infrastructure.modules.payload_builder.operations import PayloadFragment

if TYPE_CHECKING:
    from na228_builder.infrastructure.orchestration.catalog import CatalogSelection


UNLOCK_ALL_PATH = ("features", "general", "unlock_all")


def unlock_all_configuration_fragment(
    selection: CatalogSelection,
    *,
    owner: str,
    symbol: str = "unlock_all_demon_wind_bomb_enabled",
) -> PayloadFragment | None:
    nodes = {node.path: node for node in selection.nodes}
    if not nodes[UNLOCK_ALL_PATH].enabled:
        return None
    enabled = nodes[UNLOCK_ALL_PATH + ("demon_wind_bomb",)].configured_value
    return PayloadFragment(
        owner=owner,
        symbol=symbol,
        kind="rodata",
        alignment=4,
        payload=struct.pack("<I", int(enabled)),
    )
