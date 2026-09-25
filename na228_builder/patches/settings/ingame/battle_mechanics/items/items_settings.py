"""Shared Items configuration and field-item identities."""
from __future__ import annotations

from na228_builder.patches.localization.mod_strings import message

import struct

from na228_builder.infrastructure.modules.payload_builder.operations import PayloadFragment
from ..battle_settings_runtime import battle_mechanic_path


ITEM_AVAILABILITY = ("none", "less", "normal", "more")
ITEM_MODES = (*ITEM_AVAILABILITY, "custom")
ITEM_VALUE_LABELS = (message("common.none"), message("common.less"), message("common.normal"), message("common.more"), message("common.custom"))
FIELD_ITEMS = (
    (0x02, "health_recovery", message("item.health_recovery")),
    (0x03, "chakra_ball", message("item.chakra_ball")),
    (0x06, "shoes_of_jonin", message("item.shoes_of_jonin")),
    (0x07, "food_pills", message("item.food_pills")),
    (0x08, "scroll_of_hidden_cloud", message("item.scroll_of_hidden_cloud")),
    (0x09, "scroll_of_teleportation", message("item.scroll_of_teleportation")),
    (0x0A, "scarecrow", message("item.scarecrow")),
    (0x0B, "tortoiseshell_pills", message("item.tortoiseshell_pills")),
    (0x0C, "energy_pills", message("item.energy_pills")),
    (0x0D, "medical_pack", message("item.medical_pack")),
    (0x0E, "item_pouch", message("item.item_pouch")),
    (0x23, "demon_wind_shuriken", message("item.demon_wind_shuriken")),
    (0x24, "weight_of_determination", message("item.weight_of_determination")),
    (0x25, "exploding_kunai", message("item.exploding_kunai")),
    (0x26, "poison_smoke_bomb", message("item.poison_smoke_bomb")),
    (0x27, "makibishi_spikes", message("item.makibishi_spikes")),
    (0x28, "paper_bomb", message("item.paper_bomb")),
    (0x29, "curse_tag_chakra_points_seal", message("item.curse_tag_chakra_points_seal")),
    (0x2A, "curse_tag_armor_break", message("item.curse_tag_armor_break")),
    (0x2B, "thousand_shadow_shuriken", message("item.thousand_shadow_shuriken")),
    (0x2C, "burst_kunai", message("item.burst_kunai")),
    (0x2E, "exploding_seal", message("item.exploding_seal")),
    (0x2F, "toad_oil", message("item.toad_oil")),
    (0x30, "random_ball", message("item.random_ball")),
    (0x31, "stun_ball", message("item.stun_ball")),
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
