"""Default controller layout from the controls setting's layout."""
from __future__ import annotations

import struct
from pathlib import Path

from PIL import Image

from na228_builder.infrastructure.modules.payload_builder.operations import (
    PayloadFragment,
    PayloadRelocation,
)


CONTROLS_PATH = ("features", "defaults", "control_settings")

BUTTON_MASKS = {
    "circle": 0x20,
    "triangle": 0x10,
    "square": 0x80,
    "cross": 0x40,
    "select": 0x100,
    "l1": 0x04,
    "r1": 0x08,
    "l2": 0x01,
    "r2": 0x02,
    "l3": 0x200,
    "r3": 0x400,
}
# Control Settings button rows, in row order.
EDITOR_BUTTONS = ("circle", "triangle", "square", "cross", "select", "l1", "r1", "l2", "r2", "l3", "r3")
# L3, R3, and Select cells on the 16-color TEX_xcommand02 palette, written into
# free texels of the Control Settings textures.
ADDED_ICONS = ("l3_icon.png", "r3_icon.png", "select_icon.png")
ACTIONS = {
    "ultimate_jutsu_prep": 0,
    "attack": 1,
    "jump": 2,
    "item_use": 3,
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
# Saved button choices for the added actions; matches save_appendix.tsv.
SAVED_BUTTON_MASKS = (0x000, 0x001, 0x002, 0x004, 0x008, 0x010, 0x020, 0x040, 0x080, 0x100, 0x200, 0x400)


def controls_layout(selection) -> dict[str, int]:
    """Return button -> action ID; unbound buttons are omitted."""
    nodes = {node.path: node for node in selection.nodes}
    layout: dict[str, int] = {}
    for button in BUTTON_MASKS:
        value = nodes[CONTROLS_PATH + (button,)].configured_value
        if value == "unbound":
            continue
        action = ACTIONS[value]
        if action in layout.values():
            raise ValueError(
                f"defaults.control_settings: {value!r} is assigned twice"
            )
        layout[button] = action
    return layout


def controls_vibration(selection) -> int:
    """Return the default vibration choice: 1 for on, 0 for off."""
    node = next(node for node in selection.nodes if node.path == CONTROLS_PATH + ("vibration",))
    return int(node.configured_value == "on")


def _mask_of(layout: dict[str, int], action: int) -> int:
    return next((BUTTON_MASKS[button] for button, bound in layout.items() if bound == action), 0)


def added_binding_masks(layout: dict[str, int]) -> tuple[int, ...]:
    """Guard, Substitution, Item Select L, Item Select R masks for P1, then P2."""
    return tuple(_mask_of(layout, action) for _side in range(SIDES) for action in ADDED_ACTIONS)


def added_binding_save_defaults(layout: dict[str, int]) -> tuple[int, ...]:
    return tuple(SAVED_BUTTON_MASKS.index(mask) for mask in added_binding_masks(layout))


# Native Control Settings label draw and running-help setter, used when the
# localized font layout is off.
NATIVE_LABEL_DRAW = 0x00379240
NATIVE_HELP_SET = 0x0037F760


def control_default_fragments(
    *, owner: str, layout: dict[str, int], vibration: int, font_layout: bool
) -> tuple[PayloadFragment, ...]:
    native = struct.pack("<8H", *(_mask_of(layout, action) for action in range(NATIVE_ACTIONS)))
    reset = struct.pack(
        f"<{len(EDITOR_BUTTONS) + 1}I",
        *(layout.get(button, UNBOUND) for button in EDITOR_BUTTONS),
        vibration,
    )
    added = struct.pack(f"<{SIDES * len(ADDED_ACTIONS)}H", *added_binding_masks(layout))
    return (
        PayloadFragment(owner=owner, symbol="control_default_native_bindings",
                        kind="rodata", alignment=4, payload=native),
        PayloadFragment(owner=owner, symbol="control_default_reset_actions",
                        kind="rodata", alignment=4, payload=reset),
        PayloadFragment(owner=owner, symbol="control_settings_extra_bindings",
                        kind="data", alignment=4, payload=added),
        # Cold start sets both ports' vibration from this byte, like the retail 0x005C06B0.
        PayloadFragment(owner=owner, symbol="control_default_vibration",
                        kind="rodata", alignment=4, payload=struct.pack("<I", vibration)),
        PayloadFragment(owner=owner, symbol="control_settings_button_icons",
                        kind="rodata", alignment=4, payload=_added_icon_pixels()),
        _font_routine(owner, "control_settings_label_draw", font_layout,
                      "v2_controls_adapter", NATIVE_LABEL_DRAW),
        _font_routine(owner, "control_settings_help_set", font_layout,
                      "v2_help_set", NATIVE_HELP_SET),
    )


def _font_routine(
    owner: str, symbol: str, font_layout: bool, localized: str, native: int
) -> PayloadFragment:
    """Point at the localized font routine when its layout is built, else the native one."""
    return PayloadFragment(
        owner=owner,
        symbol=symbol,
        kind="rodata",
        alignment=4,
        payload=struct.pack("<I", 0 if font_layout else native),
        relocations=(
            (PayloadRelocation(offset=0, kind="abs32", symbol=localized),)
            if font_layout
            else ()
        ),
    )


def _added_icon_pixels() -> bytes:
    """Palette indices of the L3, R3, and Select cells, 30x16 each, top row first."""
    payload = bytearray()
    for filename in ADDED_ICONS:
        with Image.open(Path(__file__).with_name(filename)) as image:
            if image.size != (30, 16) or image.mode != "P":
                raise ValueError(f"{filename} must be a 30x16 indexed PNG")
            pixels = image.tobytes()
        if max(pixels) >= 16:
            raise ValueError(f"{filename} must use the 16-color TEX_xcommand02 palette")
        payload += pixels
    return bytes(payload)
