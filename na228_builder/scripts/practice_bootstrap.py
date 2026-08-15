from __future__ import annotations

import struct
from typing import TYPE_CHECKING, Mapping

from ..payload_builder.operations import PayloadFragment

if TYPE_CHECKING:
    from .catalog import CatalogSelection


PRACTICE_BOOTSTRAP_PATH = ("features", "qol", "practice", "bootstrap")
PRACTICE_BOOTSTRAP_VERSION = 1
PRACTICE_BOOTSTRAP_NO_AWAKENING = 0xFFFFFFFF


def _hexadecimal_id(
    value: object,
    *,
    field: str,
    label: str,
    maximum: int,
) -> int:
    expectation = (
        f"Practice bootstrap {field} must be a hexadecimal {label} ID "
        f"from 0x00 through 0x{maximum:02X}"
    )
    if not isinstance(value, str) or not value.startswith(("0x", "0X")):
        raise ValueError(expectation)
    try:
        result = int(value, 16)
    except ValueError as exc:
        raise ValueError(expectation) from exc
    if not 0 <= result <= maximum:
        raise ValueError(expectation)
    return result


def practice_bootstrap_fragment(
    selection: CatalogSelection,
    *,
    owner: str,
    awakening_ids_by_character: Mapping[int, tuple[int, ...]],
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
    valid_awakening_ids = awakening_ids_by_character.get(p1)
    if valid_awakening_ids is None:
        raise ValueError(f"Practice bootstrap p1 character ID {p1} is unknown")
    support_id = _hexadecimal_id(
        support,
        field="support",
        label="support",
        maximum=0x25,
    )
    if awakening == "none":
        awakening_id = PRACTICE_BOOTSTRAP_NO_AWAKENING
    else:
        awakening_id = _hexadecimal_id(
            awakening,
            field="awakening",
            label="awakening",
            maximum=0x89,
        )
        if awakening_id not in valid_awakening_ids:
            valid_text = ", ".join(
                f"0x{value:02X}" for value in valid_awakening_ids
            ) or "none"
            raise ValueError(
                f"Practice bootstrap awakening ID 0x{awakening_id:02X} "
                f"is not valid for p1 character ID {p1}; "
                f"valid awakening IDs: {valid_text}"
            )

    return PayloadFragment(
        owner=owner,
        symbol=symbol,
        kind="rodata",
        alignment=4,
        payload=struct.pack(
            "<4I",
            PRACTICE_BOOTSTRAP_VERSION,
            p1,
            support_id,
            awakening_id,
        ),
    )
