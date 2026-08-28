from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..payload_builder.operations import PayloadFragment, PayloadRelocation

if TYPE_CHECKING:
    from .catalog import CatalogSelection


SUBSTITUTION_GAUGE_PATH = (
    "features",
    "battle",
    "substitution",
    "gauge",
)
ULTIMATE_JUTSU_CONTEST_DISABLED_PATH = (
    "features",
    "battle",
    "ultimate_jutsu",
    "contest_disabled",
)

ROW_LOCAL_CUSTOM = 0xFFFFFFFF
ROW_FLAG_LABEL_SLOT = 0x01
ROW_FLAG_HELP_SLOT = 0x02
ROW_FLAG_VALUES_SLOT = 0x04
ROW_FLAG_CUSTOM_SUBSTITUTION = 0x08
ROW_FLAG_DIFFICULTY_LIMIT = 0x10
ROW_FLAG_TIME = 0x20
ROW_FLAG_HANDICAP = 0x40
ROW_FLAG_ULTIMATE_JUTSU = 0x80

NATIVE_LABEL_TABLE = 0x008BE160
NATIVE_HELP_TABLE = 0x008BE560
NATIVE_VALUE_TABLE = 0x008BE5C0
SUBSTITUTION_ROW_ID = 6
SCHEMA_HEADER_SIZE = 12
ROW_FIELD_COUNT = 8
ROW_SIZE = ROW_FIELD_COUNT * 4
LABEL_REFERENCE_FIELD = 2
HELP_REFERENCE_FIELD = 3
VALUE_REFERENCE_FIELD = 4
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


@dataclass(frozen=True)
class BattleRow:
    row_id: int
    local_offset: int
    option_count: int
    flags: int
    default_value: int = 0

    def encoded_fields(self) -> tuple[int, ...]:
        return (
            self.row_id,
            self.local_offset,
            NATIVE_LABEL_TABLE + self.row_id * 4,
            NATIVE_HELP_TABLE + self.row_id * 4,
            NATIVE_VALUE_TABLE + self.row_id * 4,
            self.option_count,
            self.default_value,
            self.flags,
        )


NATIVE_ROWS = {
    0: BattleRow(
        0,
        0x30,
        11,
        ROW_FLAG_LABEL_SLOT | ROW_FLAG_HELP_SLOT | ROW_FLAG_TIME,
    ),
    1: BattleRow(
        1,
        0x34,
        6,
        ROW_FLAG_LABEL_SLOT
        | ROW_FLAG_HELP_SLOT
        | ROW_FLAG_VALUES_SLOT
        | ROW_FLAG_DIFFICULTY_LIMIT,
    ),
    2: BattleRow(
        2,
        0x38,
        4,
        ROW_FLAG_LABEL_SLOT | ROW_FLAG_HELP_SLOT | ROW_FLAG_VALUES_SLOT,
    ),
    3: BattleRow(
        3,
        0x3C,
        2,
        ROW_FLAG_LABEL_SLOT | ROW_FLAG_HELP_SLOT | ROW_FLAG_VALUES_SLOT,
    ),
    4: BattleRow(
        4,
        0x40,
        6,
        ROW_FLAG_LABEL_SLOT
        | ROW_FLAG_HELP_SLOT
        | ROW_FLAG_VALUES_SLOT
        | ROW_FLAG_ULTIMATE_JUTSU,
    ),
    5: BattleRow(
        5,
        0x44,
        11,
        ROW_FLAG_LABEL_SLOT | ROW_FLAG_HELP_SLOT | ROW_FLAG_HANDICAP,
    ),
}


def _selected_node(selection: CatalogSelection, path: tuple[str, ...]):
    matches = [node for node in selection.nodes if node.path == path]
    if len(matches) != 1:
        raise ValueError(f"Catalog selection has no unique {'.'.join(path)} node")
    return matches[0]


def _substitution_default(selection: CatalogSelection) -> int:
    node = _selected_node(selection, SUBSTITUTION_GAUGE_PATH)
    if not node.enabled:
        return 0
    value = node.configured_value
    if not node.has_configured_value or not isinstance(value, dict):
        raise ValueError("Substitution gauge requires a settings object")
    default = value.get("default")
    if default not in SUBSTITUTION_MODE_VALUES:
        raise ValueError(
            "Substitution gauge default must be 'chakra', 'gauge', or 'free'"
        )
    return SUBSTITUTION_MODE_VALUES[default]


def _active_rows(selection: CatalogSelection) -> tuple[BattleRow, ...]:
    gauge = _selected_node(selection, SUBSTITUTION_GAUGE_PATH)
    contest_disabled = _selected_node(
        selection,
        ULTIMATE_JUTSU_CONTEST_DISABLED_PATH,
    )
    rows = [NATIVE_ROWS[index] for index in range(4)]
    if gauge.enabled:
        rows.append(
            BattleRow(
                SUBSTITUTION_ROW_ID,
                ROW_LOCAL_CUSTOM,
                3,
                ROW_FLAG_CUSTOM_SUBSTITUTION,
                _substitution_default(selection),
            )
        )
    if not contest_disabled.enabled:
        rows.append(NATIVE_ROWS[4])
    rows.append(NATIVE_ROWS[5])
    return tuple(rows)


def battle_settings_fragment(
    selection: CatalogSelection,
    *,
    owner: str,
    symbol: str = "battle_settings_schema",
) -> PayloadFragment | None:
    gauge = _selected_node(selection, SUBSTITUTION_GAUGE_PATH)
    contest_disabled = _selected_node(
        selection,
        ULTIMATE_JUTSU_CONTEST_DISABLED_PATH,
    )
    if not gauge.enabled and not contest_disabled.enabled:
        return None

    rows = _active_rows(selection)
    payload = bytearray(struct.pack("<3I", len(rows), 0, 0))
    relocations: list[PayloadRelocation] = []
    value_table_offset = SCHEMA_HEADER_SIZE + len(rows) * ROW_SIZE
    if gauge.enabled:
        relocations.extend(
            (
                PayloadRelocation(
                    offset=4,
                    kind="abs32",
                    symbol="substitution_gauge_mode_get",
                ),
                PayloadRelocation(
                    offset=8,
                    kind="abs32",
                    symbol="substitution_gauge_mode_set",
                ),
            )
        )
    for index, row in enumerate(rows):
        fields = list(row.encoded_fields())
        if row.row_id == SUBSTITUTION_ROW_ID:
            fields[LABEL_REFERENCE_FIELD] = 0
            fields[HELP_REFERENCE_FIELD] = 0
            fields[VALUE_REFERENCE_FIELD] = 0
            row_offset = SCHEMA_HEADER_SIZE + index * ROW_SIZE
            relocations.extend(
                (
                    PayloadRelocation(
                        offset=row_offset + LABEL_REFERENCE_FIELD * 4,
                        kind="abs32",
                        symbol="battle_settings_substitution_label",
                    ),
                    PayloadRelocation(
                        offset=row_offset + HELP_REFERENCE_FIELD * 4,
                        kind="abs32",
                        symbol="battle_settings_substitution_help",
                    ),
                    PayloadRelocation(
                        offset=row_offset + VALUE_REFERENCE_FIELD * 4,
                        kind="abs32",
                        symbol=symbol,
                        addend=value_table_offset,
                    ),
                )
            )
        payload.extend(struct.pack("<8I", *fields))

    if gauge.enabled:
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
