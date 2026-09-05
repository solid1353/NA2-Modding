from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..payload_builder.operations import PayloadFragment
from .battle_settings_runtime import (
    PRACTICE_SETTINGS_PATH,
    ULTIMATE_JUTSU_NATIVE_DEFAULT,
    ULTIMATE_JUTSU_NATIVE_MODE_COUNT,
    battle_mechanic_enabled,
    ultimate_jutsu_default,
)

if TYPE_CHECKING:
    from .catalog import CatalogSelection


BATTLE_SETTINGS_PATH = ("features", "settings", "ingame", "battle_mode")

BATTLE_ROW_VALUE_MAPS: dict[str, dict[object, int]] = {
    "time": {
        10: 0,
        20: 1,
        30: 2,
        40: 3,
        50: 4,
        60: 5,
        70: 6,
        80: 7,
        90: 8,
        99: 9,
        "unlimited": 10,
    },
    "difficulty": {
        "simple": 0,
        "easy": 1,
        "normal": 2,
        "hard": 3,
        "insane": 4,
        "ultimate": 5,
    },
    "handicap": {value: value for value in range(11)},
}
BATTLE_ROW_IDS = {
    "time": 0,
    "difficulty": 1,
    "handicap": 5,
}

PRACTICE_GENERAL_ROW_VALUE_MAPS: dict[str, dict[object, int]] = {
    "health": {"normal": 0, "half": 1, "almost": 2},
    "commands": {"off": 0, "on": 1},
    "damage": {"off": 0, "on": 1},
}
PRACTICE_OPPONENT_ROW_VALUE_MAPS: dict[str, dict[object, int]] = {
    "status": {
        "manual": 0,
        "com": 1,
        "stand": 2,
        "jump": 3,
        "double_jump": 4,
    },
    "strength": BATTLE_ROW_VALUE_MAPS["difficulty"],
    "attack": {
        "no": 0,
        "single": 1,
        "combo": 2,
        "projectile": 3,
        "high_speed_move": 4,
        "ultimate_jutsu": 5,
        "jutsu": 6,
    },
    "guard": {"no": 0, "yes": 1},
    "move": {"stay": 0, "follow": 1},
    "substitution_jutsu": {"normal": 0, "no": 1},
    "linked_attack": {"dont_use": 0, "normal": 1, "random": 2},
    "extra_hit_counter": {"normal": 0, "return": 1},
}
PRACTICE_GENERAL_ROW_IDS = {
    "health": 0,
    "commands": 6,
    "damage": 7,
}
PRACTICE_OPPONENT_ROW_IDS = {
    "status": 9,
    "strength": 10,
    "attack": 11,
    "guard": 12,
    "move": 13,
    "substitution_jutsu": 14,
    "linked_attack": 15,
    "extra_hit_counter": 16,
}


@dataclass(frozen=True)
class _StorageField:
    offset: int
    mask: int
    shift: int = 0


BATTLE_STORAGE_FIELDS = {
    "time": _StorageField(3, 0xFF),
    "difficulty": _StorageField(7, 0xFF),
    "handicap": _StorageField(5, 0xFF),
}
PRACTICE_GENERAL_STORAGE_FIELDS = {
    "health": _StorageField(1, 0xFF),
    "commands": _StorageField(0, 0x01),
    "damage": _StorageField(0, 0x10, 4),
}
PRACTICE_OPPONENT_STORAGE_FIELDS = {
    "status": _StorageField(6, 0xFF),
    "strength": _StorageField(7, 0xFF),
    "attack": _StorageField(8, 0xFF),
    "guard": _StorageField(9, 0xFF),
    "move": _StorageField(10, 0xFF),
    "substitution_jutsu": _StorageField(0, 0x80, 7),
    "linked_attack": _StorageField(11, 0xFF),
    "extra_hit_counter": _StorageField(0, 0x40, 6),
}


def _selected_node(selection: CatalogSelection, path: tuple[str, ...]):
    matches = [node for node in selection.nodes if node.path == path]
    if len(matches) != 1:
        raise ValueError(f"Catalog selection has no unique {'.'.join(path)} node")
    return matches[0]


def _configured_object(
    selection: CatalogSelection,
    path: tuple[str, ...],
    label: str,
) -> dict[str, object]:
    node = _selected_node(selection, path)
    if not node.enabled:
        return {}
    configured = node.configured_value if node.has_configured_value else {}
    if not isinstance(configured, dict):
        raise ValueError(f"{label} settings requires an object value")
    return configured


def battle_configured_row_defaults(
    selection: CatalogSelection,
) -> dict[int, int]:
    configured = _configured_object(
        selection, BATTLE_SETTINGS_PATH, "Battle"
    )
    return {
        BATTLE_ROW_IDS[name]: BATTLE_ROW_VALUE_MAPS[name][value]
        for name, value in configured.items()
        if name in BATTLE_ROW_VALUE_MAPS
    }


def practice_configured_row_defaults(
    selection: CatalogSelection,
) -> dict[int, int]:
    configured = _configured_object(selection, PRACTICE_SETTINGS_PATH, "Practice")
    defaults: dict[int, int] = {}
    for values, row_maps, row_ids in (
        (
            configured,
            PRACTICE_GENERAL_ROW_VALUE_MAPS,
            PRACTICE_GENERAL_ROW_IDS,
        ),
        (
            configured.get("opponent_settings", {}),
            PRACTICE_OPPONENT_ROW_VALUE_MAPS,
            PRACTICE_OPPONENT_ROW_IDS,
        ),
    ):
        defaults.update(
            {
                row_ids[name]: row_maps[name][value]
                for name, value in values.items()
                if name in row_maps
            }
        )
    return defaults


def _encode_storage(
    configured: dict[str, object],
    row_value_maps: dict[str, dict[object, int]],
    fields: dict[str, _StorageField],
) -> tuple[bytearray, bytearray]:
    values = bytearray(12)
    masks = bytearray(12)
    for name, raw_value in configured.items():
        if name not in fields:
            continue
        field = fields[name]
        encoded = (
            100
            if name == "time" and raw_value == "unlimited"
            else int(raw_value)
            if name == "time"
            else row_value_maps[name][raw_value]
        )
        values[field.offset] = (
            values[field.offset]
            | ((encoded << field.shift) & field.mask)
        )
        masks[field.offset] |= field.mask
    return values, masks


def native_settings_defaults_fragment(
    selection: CatalogSelection,
    *,
    owner: str,
    symbol: str = "native_settings_defaults",
) -> PayloadFragment | None:
    battle_node = _selected_node(selection, BATTLE_SETTINGS_PATH)
    practice_node = _selected_node(selection, PRACTICE_SETTINGS_PATH)
    ultimate_jutsu_enabled = battle_mechanic_enabled(
        selection, "ultimate_jutsu"
    )
    if not (battle_node.enabled or practice_node.enabled or ultimate_jutsu_enabled):
        return None

    battle_configured = _configured_object(
        selection, BATTLE_SETTINGS_PATH, "Battle"
    )
    practice_configured = _configured_object(selection, PRACTICE_SETTINGS_PATH, "Practice")
    battle_values, battle_masks = _encode_storage(
        battle_configured, BATTLE_ROW_VALUE_MAPS, BATTLE_STORAGE_FIELDS
    )
    general_values, general_masks = _encode_storage(
        practice_configured,
        PRACTICE_GENERAL_ROW_VALUE_MAPS,
        PRACTICE_GENERAL_STORAGE_FIELDS,
    )
    opponent_values, opponent_masks = _encode_storage(
        practice_configured.get("opponent_settings", {}),
        PRACTICE_OPPONENT_ROW_VALUE_MAPS,
        PRACTICE_OPPONENT_STORAGE_FIELDS,
    )
    practice_values = bytearray(
        left | right for left, right in zip(general_values, opponent_values)
    )
    practice_masks = bytearray(
        left | right for left, right in zip(general_masks, opponent_masks)
    )
    battle_values[0] &= ~0x04
    battle_masks[0] |= 0x04
    practice_values[0] &= ~0x04
    practice_masks[0] |= 0x04
    practice_values[0] &= ~0x20
    practice_masks[0] |= 0x20

    if ultimate_jutsu_enabled:
        ultimate_jutsu = ultimate_jutsu_default(selection)
        native_ultimate_jutsu = (
            ultimate_jutsu
            if ultimate_jutsu < ULTIMATE_JUTSU_NATIVE_MODE_COUNT
            else ULTIMATE_JUTSU_NATIVE_DEFAULT
        )
        battle_values[2] = native_ultimate_jutsu
        battle_masks[2] = 0xFF
        practice_values[2] = native_ultimate_jutsu
        practice_masks[2] = 0xFF

    payload = bytes(
        battle_values
        + battle_masks
        + practice_values
        + practice_masks
    )
    return PayloadFragment(
        owner=owner,
        symbol=symbol,
        kind="rodata",
        alignment=4,
        payload=payload,
    )
