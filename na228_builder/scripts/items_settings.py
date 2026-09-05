"""Shared Items configuration and field-item identities."""
from __future__ import annotations

import struct

from ..payload_builder.operations import PayloadFragment
from .battle_settings_runtime import battle_mechanic_path


ITEM_AVAILABILITY = ("none", "less", "normal", "more")
ITEM_MODES = (*ITEM_AVAILABILITY, "custom")
ITEM_VALUE_LABELS = ("None", "Less", "Normal", "More", "Custom")
FIELD_ITEMS = (
    (0x02, "health_recovery", "Health Recovery"),
    (0x03, "chakra_ball", "Chakra Ball"),
    (0x06, "shoes_of_jonin", "Shoes of Jonin"),
    (0x07, "food_pills", "Food Pills"),
    (0x08, "scroll_of_hidden_cloud", "Scroll of Hidden Cloud"),
    (0x09, "scroll_of_teleportation", "Scroll of Teleportation"),
    (0x0A, "scarecrow", "Scarecrow"),
    (0x0B, "tortoiseshell_pills", "Tortoiseshell Pills"),
    (0x0C, "energy_pills", "Energy Pills"),
    (0x0D, "medical_pack", "Medical Pack"),
    (0x0E, "item_pouch", "Item Pouch"),
    (0x23, "demon_wind_shuriken", "Demon Wind Shuriken"),
    (0x24, "weight_of_determination", "Weight of Determination"),
    (0x25, "exploding_kunai", "Exploding Kunai"),
    (0x26, "poison_smoke_bomb", "Poison Smoke Bomb"),
    (0x27, "makibishi_spikes", "Makibishi Spikes"),
    (0x28, "paper_bomb", "Paper Bomb"),
    (0x29, "curse_tag_chakra_points_seal", "Curse Tag: Chakra Points Seal"),
    (0x2A, "curse_tag_armor_break", "Curse Tag: Armor Break"),
    (0x2B, "thousand_shadow_shuriken", "1000-Shadow Shuriken"),
    (0x2C, "burst_kunai", "Burst Kunai"),
    (0x2E, "exploding_seal", "Exploding Seal"),
    (0x2F, "toad_oil", "Toad Oil"),
    (0x30, "random_ball", "Random Ball"),
    (0x31, "stun_ball", "Stun Ball"),
)


def items_configuration(selection):
    node = next(node for node in selection.nodes
                if node.path == battle_mechanic_path("items"))
    return node.configured_value if node.enabled else None


def items_option_defaults(selection):
    config = items_configuration(selection)
    custom = config["custom"]
    return (ITEM_MODES.index(config["value"]),
            ITEM_AVAILABILITY.index(custom["availability"]),
            *(int(custom[key]) for _code, key, _label in FIELD_ITEMS))


def items_settings_fragment(selection, *, owner):
    if items_configuration(selection) is None:
        return None
    mode, availability, *enabled = items_option_defaults(selection)
    mask = sum(value << index for index, value in enumerate(enabled))
    return PayloadFragment(owner=owner, symbol="items_settings_config",
        kind="rodata", alignment=4,
        payload=struct.pack("<3I", mode, availability, mask)
                + bytes(code for code, _key, _label in FIELD_ITEMS))
