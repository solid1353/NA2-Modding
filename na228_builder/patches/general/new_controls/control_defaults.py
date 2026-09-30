"""Default controller layout from resources/default_controls.tsv."""
from __future__ import annotations

import csv
import struct
from pathlib import Path

from na228_builder.infrastructure.modules.payload_builder.operations import (
    PayloadFragment,
    PayloadRelocation,
)


TABLE_PATH = Path(__file__).resolve().parents[3] / "resources" / "default_controls.tsv"

# Editor rows and their button masks, in Control Settings row order.
BUTTON_MASKS = {
    "circle": 0x20,
    "triangle": 0x10,
    "square": 0x80,
    "cross": 0x40,
    "l1": 0x04,
    "r1": 0x08,
    "l2": 0x01,
    "r2": 0x02,
}
FACE_BUTTONS = frozenset({"circle", "triangle", "square", "cross"})
FACE_ACTIONS = {
    "ultimate_jutsu_prep": 0,
    "attack": 1,
    "jump": 2,
    "item_use": 3,
}
SHOULDER_ACTIONS = {
    "linked_attack": 5,
    "guard": 8,
    "substitution": 9,
    "item_select_l": 10,
    "item_select_r": 11,
}
NATIVE_ACTIONS = 8
ADDED_ACTIONS = (8, 9, 10, 11)
UNBOUND = 12
SIDES = 2
# Retail default for the reset table's trailing vibration word.
RESET_VIBRATION = 1
SHOULDER_MASKS = (0x00, 0x01, 0x02, 0x04, 0x08)


def load_default_controls(path: Path = TABLE_PATH) -> dict[str, int]:
    """Return button -> action ID; buttons without a row stay unbound."""
    reader = csv.DictReader(path.read_text(encoding="utf-8").splitlines(), delimiter="\t")
    if reader.fieldnames != ["button", "action"]:
        raise ValueError("default_controls.tsv columns must be button, action")
    layout: dict[str, int] = {}
    for line_number, row in enumerate(reader, start=2):
        button, action = row["button"], row["action"]
        if button not in BUTTON_MASKS or button in layout:
            raise ValueError(f"default_controls.tsv line {line_number}: unknown or repeated button {button!r}")
        actions = FACE_ACTIONS if button in FACE_BUTTONS else SHOULDER_ACTIONS
        if action not in actions:
            raise ValueError(f"default_controls.tsv line {line_number}: {action!r} cannot be on {button}")
        if actions[action] in layout.values():
            raise ValueError(f"default_controls.tsv line {line_number}: {action!r} is assigned twice")
        layout[button] = actions[action]
    return layout


def _mask_of(layout: dict[str, int], action: int) -> int:
    return next((BUTTON_MASKS[button] for button, bound in layout.items() if bound == action), 0)


def added_binding_masks(layout: dict[str, int]) -> tuple[int, ...]:
    """Guard, Substitution, Item Select L, Item Select R masks for P1, then P2."""
    return tuple(_mask_of(layout, action) for _side in range(SIDES) for action in ADDED_ACTIONS)


def added_binding_save_defaults(layout: dict[str, int]) -> tuple[int, ...]:
    return tuple(SHOULDER_MASKS.index(mask) for mask in added_binding_masks(layout))


def control_default_fragments(
    *, owner: str, substitution_input: bool
) -> tuple[PayloadFragment, ...]:
    layout = load_default_controls()
    native = struct.pack("<8H", *(_mask_of(layout, action) for action in range(NATIVE_ACTIONS)))
    reset = struct.pack(
        "<9I",
        *(layout.get(button, UNBOUND) for button in BUTTON_MASKS),
        RESET_VIBRATION,
    )
    added = struct.pack(f"<{SIDES * len(ADDED_ACTIONS)}H", *added_binding_masks(layout))
    return (
        PayloadFragment(owner=owner, symbol="control_default_native_bindings",
                        kind="rodata", alignment=4, payload=native),
        PayloadFragment(owner=owner, symbol="control_default_reset_actions",
                        kind="rodata", alignment=4, payload=reset),
        PayloadFragment(owner=owner, symbol="control_settings_extra_bindings",
                        kind="data", alignment=4, payload=added),
        # The Hold value lives in Substitution Input, which may be left out.
        PayloadFragment(
            owner=owner,
            symbol="control_settings_substitution_input_get",
            kind="rodata",
            alignment=4,
            payload=bytes(4),
            relocations=(
                (PayloadRelocation(offset=0, kind="abs32", symbol="substitution_input_get"),)
                if substitution_input
                else ()
            ),
        ),
    )
