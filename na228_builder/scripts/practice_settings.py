from __future__ import annotations

import struct
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from ..payload_builder.operations import PayloadFragment, PayloadRelocation

if TYPE_CHECKING:
    from .catalog import CatalogSelection


PRACTICE_SETTINGS_PATH = ("features", "practice", "settings_rework")
SUBSTITUTION_GAUGE_PATH = (
    "features",
    "battle",
    "substitution",
    "gauge",
)
SUPPORT_DISABLED_PATH = ("features", "battle", "support_disabled")
ULTIMATE_JUTSU_CONTEST_DISABLED_PATH = (
    "features",
    "battle",
    "ultimate_jutsu",
    "contest_disabled",
)
EXTRA_HIT_DISABLED_PATH = (
    "features",
    "battle",
    "extra_hit_disabled_with_aura_punishment_for_initiator",
)

ROW_SECTION_PLAYER = 0
ROW_SECTION_OPPONENT = 1
ROW_LOCAL_CUSTOM = 0xFFFFFFFF

ROW_AVAILABLE_ALWAYS = 0
ROW_AVAILABLE_STATUS_COM = 1
ROW_AVAILABLE_STATUS_ACTION = 2
ROW_AVAILABLE_STATUS_NOT_MANUAL = 3

ROW_FLAG_LABEL_SLOT = 0x01
ROW_FLAG_HELP_SLOT = 0x02
ROW_FLAG_HELP_BY_VALUE = 0x04
ROW_FLAG_VALUES_SLOT = 0x08
ROW_FLAG_STRENGTH_LIMIT = 0x10
ROW_FLAG_CUSTOM_SUBSTITUTION = 0x20

NATIVE_LABEL_TABLE = 0x008BE6C0
NATIVE_HELP_TABLE = 0x008BEF70
NATIVE_STATUS_HELP_TABLE = 0x008BF350
NATIVE_VALUE_TABLE = 0x008BF380

SUBSTITUTION_ROW_ID = 17
SCHEMA_HEADER_SIZE = 24
ROW_FIELD_COUNT = 10
ROW_SIZE = ROW_FIELD_COUNT * 4
LABEL_REFERENCE_FIELD = 3
HELP_REFERENCE_FIELD = 4
VALUE_REFERENCE_FIELD = 5
SUBSTITUTION_MODE_LABELS = (
    "substitution_gauge_mode_chakra_label",
    "substitution_gauge_mode_gauge_label",
    "substitution_gauge_mode_free_label",
)
SUBSTITUTION_MODE_VALUES = {
    "chakra": 0,
    "gauge": 1,
    "free": 2,
}

DEFAULT_PRESERVE_NATIVE = 0xFF
DEFAULT_VALUE_MAPS = {
    "health": {"full": 0, "half": 1, "critical": 2},
    "commands": {"off": 0, "on": 1},
    "guide_ninja_sound": {"off": 0, "on": 1},
    "linked_attack": {"off": 0, "on": 1, "random": 2},
}


@dataclass(frozen=True)
class PracticeRow:
    row_id: int
    section: int
    local_offset: int
    option_count: int
    default_value: int
    availability: int = ROW_AVAILABLE_ALWAYS
    flags: int = (
        ROW_FLAG_LABEL_SLOT | ROW_FLAG_HELP_SLOT | ROW_FLAG_VALUES_SLOT
    )

    def encoded_fields(self) -> tuple[int, ...]:
        help_reference = (
            NATIVE_STATUS_HELP_TABLE
            if self.flags & ROW_FLAG_HELP_BY_VALUE
            else NATIVE_HELP_TABLE + self.row_id * 4
        )
        return (
            self.row_id,
            self.section,
            self.local_offset,
            NATIVE_LABEL_TABLE + self.row_id * 4,
            help_reference,
            NATIVE_VALUE_TABLE + self.row_id * 4,
            self.option_count,
            self.default_value,
            self.availability,
            self.flags,
        )


NATIVE_ROWS = {
    0: PracticeRow(0, ROW_SECTION_PLAYER, 0x6C, 3, 0),
    1: PracticeRow(1, ROW_SECTION_PLAYER, 0x70, 2, 0),
    2: PracticeRow(2, ROW_SECTION_PLAYER, 0x74, 2, 0),
    3: PracticeRow(3, ROW_SECTION_PLAYER, 0x78, 6, 2),
    4: PracticeRow(4, ROW_SECTION_PLAYER, 0x7C, 2, 1),
    5: PracticeRow(5, ROW_SECTION_PLAYER, 0x80, 4, 2),
    6: PracticeRow(6, ROW_SECTION_PLAYER, 0x84, 2, 1),
    7: PracticeRow(7, ROW_SECTION_PLAYER, 0x88, 2, 1),
    8: PracticeRow(8, ROW_SECTION_PLAYER, 0x8C, 2, 1),
    9: PracticeRow(
        9,
        ROW_SECTION_OPPONENT,
        0x90,
        5,
        2,
        flags=(
            ROW_FLAG_LABEL_SLOT
            | ROW_FLAG_HELP_BY_VALUE
            | ROW_FLAG_VALUES_SLOT
        ),
    ),
    10: PracticeRow(
        10,
        ROW_SECTION_OPPONENT,
        0x94,
        6,
        2,
        availability=ROW_AVAILABLE_STATUS_COM,
        flags=(
            ROW_FLAG_LABEL_SLOT
            | ROW_FLAG_HELP_SLOT
            | ROW_FLAG_VALUES_SLOT
            | ROW_FLAG_STRENGTH_LIMIT
        ),
    ),
    11: PracticeRow(
        11,
        ROW_SECTION_OPPONENT,
        0x98,
        7,
        0,
        availability=ROW_AVAILABLE_STATUS_ACTION,
    ),
    12: PracticeRow(
        12,
        ROW_SECTION_OPPONENT,
        0x9C,
        2,
        0,
        availability=ROW_AVAILABLE_STATUS_ACTION,
    ),
    13: PracticeRow(
        13,
        ROW_SECTION_OPPONENT,
        0xA0,
        2,
        0,
        availability=ROW_AVAILABLE_STATUS_ACTION,
    ),
    14: PracticeRow(
        14,
        ROW_SECTION_OPPONENT,
        0xA4,
        2,
        0,
        availability=ROW_AVAILABLE_STATUS_COM,
    ),
    15: PracticeRow(
        15,
        ROW_SECTION_OPPONENT,
        0xA8,
        3,
        1,
        availability=ROW_AVAILABLE_STATUS_NOT_MANUAL,
    ),
    16: PracticeRow(
        16,
        ROW_SECTION_OPPONENT,
        0xAC,
        2,
        0,
        availability=ROW_AVAILABLE_STATUS_NOT_MANUAL,
    ),
}


def _node_enabled(selection: CatalogSelection, path: tuple[str, ...]) -> bool:
    matches = [node for node in selection.nodes if node.path == path]
    if len(matches) != 1:
        raise ValueError(f"Catalog selection has no unique {'.'.join(path)} node")
    return matches[0].enabled


def _selected_node(selection: CatalogSelection, path: tuple[str, ...]):
    matches = [node for node in selection.nodes if node.path == path]
    if len(matches) != 1:
        raise ValueError(f"Catalog selection has no unique {'.'.join(path)} node")
    return matches[0]


def _configured_defaults(
    selection: CatalogSelection,
) -> tuple[int, int, int, int]:
    node = _selected_node(selection, PRACTICE_SETTINGS_PATH)
    configured = node.configured_value if node.has_configured_value else {}
    if not isinstance(configured, dict):
        raise ValueError("Practice Settings Rework requires an object value")
    return tuple(
        DEFAULT_PRESERVE_NATIVE
        if name not in configured
        else DEFAULT_VALUE_MAPS[name][configured[name]]
        for name in DEFAULT_VALUE_MAPS
    )


def _active_rows(selection: CatalogSelection) -> tuple[PracticeRow, ...]:
    substitution_gauge = _node_enabled(selection, SUBSTITUTION_GAUGE_PATH)
    support_disabled = _node_enabled(selection, SUPPORT_DISABLED_PATH)
    ultimate_jutsu_contest_disabled = _node_enabled(
        selection, ULTIMATE_JUTSU_CONTEST_DISABLED_PATH
    )
    extra_hit_disabled = _node_enabled(selection, EXTRA_HIT_DISABLED_PATH)
    health, commands, guide_ninja_sound, linked_attack = _configured_defaults(
        selection
    )
    configured_defaults = {
        0: health,
        6: commands,
        8: guide_ninja_sound,
        15: linked_attack,
    }

    def native_row(row_id: int) -> PracticeRow:
        row = NATIVE_ROWS[row_id]
        default_value = configured_defaults.get(row_id, DEFAULT_PRESERVE_NATIVE)
        if default_value == DEFAULT_PRESERVE_NATIVE:
            return row
        return replace(row, default_value=default_value)

    rows = [native_row(0), native_row(1)]
    if substitution_gauge:
        gauge_node = _selected_node(selection, SUBSTITUTION_GAUGE_PATH)
        gauge_value = gauge_node.configured_value
        if not isinstance(gauge_value, dict):
            raise ValueError("Substitution gauge requires a settings object")
        gauge_default = gauge_value.get("default")
        if gauge_default not in SUBSTITUTION_MODE_VALUES:
            raise ValueError(
                "Substitution-gauge default must be 'chakra', 'gauge', or 'free'"
            )
        rows.append(
            PracticeRow(
                SUBSTITUTION_ROW_ID,
                ROW_SECTION_PLAYER,
                ROW_LOCAL_CUSTOM,
                3,
                SUBSTITUTION_MODE_VALUES[gauge_default],
                flags=ROW_FLAG_CUSTOM_SUBSTITUTION,
            )
        )
    if not support_disabled:
        rows.append(native_row(2))
    if not ultimate_jutsu_contest_disabled:
        rows.append(native_row(3))
    if not support_disabled:
        rows.append(native_row(4))
    rows.extend(native_row(index) for index in range(5, 9))
    rows.extend(native_row(index) for index in range(9, 15))
    if not support_disabled:
        rows.append(native_row(15))
    if not extra_hit_disabled:
        rows.append(native_row(16))
    return tuple(rows)


def practice_settings_fragment(
    selection: CatalogSelection,
    *,
    owner: str,
    symbol: str = "practice_settings_schema",
) -> PayloadFragment | None:
    if not _node_enabled(selection, PRACTICE_SETTINGS_PATH):
        return None

    rows = _active_rows(selection)
    player_count = sum(row.section == ROW_SECTION_PLAYER for row in rows)
    opponent_count = sum(row.section == ROW_SECTION_OPPONENT for row in rows)
    configured_defaults = _configured_defaults(selection)
    payload = bytearray(
        struct.pack(
            "<3I4B2I",
            len(rows),
            player_count,
            opponent_count,
            *configured_defaults,
            0,
            0,
        )
    )
    relocations: list[PayloadRelocation] = []
    value_table_offset = SCHEMA_HEADER_SIZE + len(rows) * ROW_SIZE
    if _node_enabled(selection, SUBSTITUTION_GAUGE_PATH):
        relocations.extend(
            (
                PayloadRelocation(
                    offset=16,
                    kind="abs32",
                    symbol="substitution_gauge_mode_get",
                ),
                PayloadRelocation(
                    offset=20,
                    kind="abs32",
                    symbol="substitution_gauge_mode_set",
                ),
            )
        )

    for index, row in enumerate(rows):
        row_offset = SCHEMA_HEADER_SIZE + index * ROW_SIZE
        if row.row_id == SUBSTITUTION_ROW_ID:
            fields = list(row.encoded_fields())
            fields[LABEL_REFERENCE_FIELD] = 0
            fields[HELP_REFERENCE_FIELD] = 0
            fields[VALUE_REFERENCE_FIELD] = 0
            payload.extend(struct.pack("<10I", *fields))
            relocations.extend(
                (
                    PayloadRelocation(
                        offset=row_offset + LABEL_REFERENCE_FIELD * 4,
                        kind="abs32",
                        symbol="practice_settings_substitution_label",
                    ),
                    PayloadRelocation(
                        offset=row_offset + HELP_REFERENCE_FIELD * 4,
                        kind="abs32",
                        symbol="practice_settings_substitution_help",
                    ),
                    PayloadRelocation(
                        offset=row_offset + VALUE_REFERENCE_FIELD * 4,
                        kind="abs32",
                        symbol=symbol,
                        addend=value_table_offset,
                    ),
                )
            )
        else:
            payload.extend(struct.pack("<10I", *row.encoded_fields()))

    if _node_enabled(selection, SUBSTITUTION_GAUGE_PATH):
        for label in SUBSTITUTION_MODE_LABELS:
            relocations.append(
                PayloadRelocation(
                    offset=len(payload),
                    kind="abs32",
                    symbol=label,
                )
            )
            payload.extend(b"\0" * 4)

    return PayloadFragment(
        owner=owner,
        symbol=symbol,
        kind="rodata",
        alignment=4,
        payload=bytes(payload),
        relocations=tuple(relocations),
    )
