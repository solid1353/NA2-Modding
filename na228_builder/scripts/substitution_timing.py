from __future__ import annotations

import struct
from typing import TYPE_CHECKING

from ..payload_builder.operations import PayloadFragment

if TYPE_CHECKING:
    from .catalog import CatalogSelection


SUBSTITUTION_FRAMES_AFTER_PATH = (
    "features",
    "battle",
    "substitution",
    "frames_after",
)


def substitution_frames_after_fragment(
    selection: CatalogSelection,
    *,
    owner: str,
    symbol: str = "battle_logic_substitution_frames_after",
) -> PayloadFragment | None:
    """Encode the selected post-impact substitution window in game frames."""

    matches = [
        node
        for node in selection.nodes
        if node.path == SUBSTITUTION_FRAMES_AFTER_PATH
    ]
    if len(matches) != 1:
        raise ValueError(
            "Catalog selection has no unique substitution frames-after node"
        )
    node = matches[0]
    if not node.enabled:
        return None
    value = node.configured_value
    if (
        not node.has_configured_value
        or isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 16
    ):
        raise ValueError("Substitution frames after requires 0 through 16")
    return PayloadFragment(
        owner=owner,
        symbol=symbol,
        kind="rodata",
        alignment=4,
        payload=struct.pack("<I", value),
    )
