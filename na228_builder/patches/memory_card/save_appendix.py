from __future__ import annotations

import csv
import re
import struct
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Callable

from na228_builder.infrastructure.modules.payload_builder.operations import (
    PayloadFragment,
    PayloadRelocation,
)
from ..settings.ingame.battle_mechanics.battle_settings_runtime import (
    chakra_default,
    extra_hit_default,
    shadowblur_default,
    sub_active_frames_default,
    substitution_default,
    support_default,
    ultimate_jutsu_default,
    xdash_chakra_cost_option_default,
)
from ..settings.ingame.battle_mechanics.items.items_settings import (
    FIELD_ITEMS,
    items_option_defaults,
)
from ..settings.ingame.battle_mechanics.substitution.substitution_gauge import (
    chakra_minimum_option_default,
    gauge_option_defaults,
)
from ..settings.ingame.shared.menu_options import MOD_SETTINGS_PATH
from ..settings.ingame.shared.native_settings_defaults import (
    BATTLE_ROW_IDS,
    PRACTICE_GENERAL_ROW_IDS,
    PRACTICE_OPPONENT_ROW_IDS,
    battle_configured_row_defaults,
    practice_configured_row_defaults,
)


APPENDIX_SIZE = 0x200
APPENDIX_HEADER_SIZE = 0x10
APPENDIX_ENTRY_SIZE = 4
SCHEMA_HEADER_SIZE = 8
DESCRIPTOR_SIZE = 24
CALL_WITH_ARGUMENT = 0
CALL_WITH_VALUE = 1
RANGE_PATTERN = re.compile(
    r"^(.*?)(-?\d+(?:\.\d+)?)([^\d]*) to "
    r"(-?\d+(?:\.\d+)?)([^\d]*) by "
    r"(-?\d+(?:\.\d+)?)([^\d]*)$"
)


@dataclass(frozen=True)
class AppendixRow:
    setting_id: int
    key: str
    label: str
    option_count: int


@dataclass(frozen=True)
class SettingBinding:
    getter: str
    setter: str
    argument: int
    call_kind: int
    default: int


def _range_count(value: str) -> int | None:
    match = RANGE_PATTERN.fullmatch(value)
    if match is None:
        return None
    prefix, start_text, start_suffix, end_text, end_suffix, step_text, step_suffix = (
        match.groups()
    )
    del prefix
    def normalized_unit(suffix: str) -> str:
        return " frame" if suffix in {" frame", " frames"} else suffix

    if (
        normalized_unit(start_suffix) != normalized_unit(end_suffix)
        or normalized_unit(start_suffix) != normalized_unit(step_suffix)
    ):
        raise ValueError(f"Save appendix range uses inconsistent units: {value!r}")
    try:
        start = Decimal(start_text)
        end = Decimal(end_text)
        step = Decimal(step_text)
    except InvalidOperation as error:
        raise ValueError(f"Save appendix range is invalid: {value!r}") from error
    if step == 0 or (end - start) * step < 0:
        raise ValueError(f"Save appendix range has an invalid direction: {value!r}")
    intervals = (end - start) / step
    if intervals != intervals.to_integral_value() or intervals < 0:
        raise ValueError(f"Save appendix range does not end on its step: {value!r}")
    return int(intervals) + 1


def _option_count(value: str) -> int:
    alternatives = value.split(" | ")
    if not alternatives or any(not alternative for alternative in alternatives):
        raise ValueError(f"Save appendix values are invalid: {value!r}")
    count = 0
    for alternative in alternatives:
        range_count = _range_count(alternative)
        count += 1 if range_count is None else range_count
    if not 1 <= count <= 0x10000:
        raise ValueError(f"Save appendix option count is invalid: {count}")
    return count


def load_save_appendix(path: Path) -> tuple[int, tuple[AppendixRow, ...]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or not lines[0].startswith("# schema_version: "):
        raise ValueError("save_appendix.tsv must start with '# schema_version: <number>'")
    try:
        schema_version = int(lines[0].removeprefix("# schema_version: "))
    except ValueError as error:
        raise ValueError("save_appendix.tsv has an invalid schema_version") from error
    if not 1 <= schema_version <= 0xFFFF:
        raise ValueError("save_appendix.tsv schema_version must be 1 through 65535")
    reader = csv.DictReader(lines[1:], delimiter="\t")
    if reader.fieldnames != ["id", "key", "label", "values"]:
        raise ValueError("save_appendix.tsv columns must be id, key, label, values")
    rows: list[AppendixRow] = []
    identifiers: set[int] = set()
    keys: set[str] = set()
    for line_number, raw in enumerate(reader, start=3):
        if None in raw or any(value is None for value in raw.values()):
            raise ValueError(f"save_appendix.tsv line {line_number} is malformed")
        identifier_text = raw["id"]
        if not re.fullmatch(r"[0-9A-F]{4}", identifier_text):
            raise ValueError(
                f"save_appendix.tsv line {line_number} id must be four uppercase hex digits"
            )
        setting_id = int(identifier_text, 16)
        key = raw["key"]
        label = raw["label"]
        if setting_id == 0 or setting_id in identifiers:
            raise ValueError(f"Duplicate or zero save appendix id: {identifier_text}")
        if not key or key in keys:
            raise ValueError(f"Duplicate or empty save appendix key: {key!r}")
        if not label:
            raise ValueError(f"Save appendix label is empty for {key}")
        identifiers.add(setting_id)
        keys.add(key)
        rows.append(
            AppendixRow(setting_id, key, label, _option_count(raw["values"]))
        )
    if APPENDIX_HEADER_SIZE + len(rows) * APPENDIX_ENTRY_SIZE > APPENDIX_SIZE:
        raise ValueError("save_appendix.tsv exceeds the 0x200-byte appendix capacity")
    return schema_version, tuple(rows)


def _selected_values(selection) -> dict[tuple[str, ...], object]:
    return {
        node.path: node.configured_value
        for node in selection.nodes
        if node.has_configured_value
    }


def _bindings(selection) -> dict[str, SettingBinding]:
    selected = _selected_values(selection)
    mod_values = (
        int(bool(selected[MOD_SETTINGS_PATH + ("new_controls",)])),
        int(selected[MOD_SETTINGS_PATH + ("simple_display",)] == "on"),
        int(bool(selected[MOD_SETTINGS_PATH + ("character_overrides",)])),
        int(bool(selected[MOD_SETTINGS_PATH + ("balance_overlay",)])),
        {"none": 0, "relevant": 1, "all": 2}[
            selected[MOD_SETTINGS_PATH + ("support_selection",)]
        ],
    )
    bindings = {
        key: SettingBinding(
            "mod_settings_option_get",
            "mod_settings_option_set",
            argument,
            CALL_WITH_ARGUMENT,
            mod_values[argument],
        )
        for argument, key in enumerate(
            (
                "mod.new_controls",
                "mod.simple_display",
                "mod.character_overrides",
                "mod.balance_overlay",
                "mod.support_selection",
            )
        )
    }

    battle_defaults = battle_configured_row_defaults(selection)
    for key, row_id in (
        ("battle.time", BATTLE_ROW_IDS["time"]),
        ("battle.difficulty", BATTLE_ROW_IDS["difficulty"]),
        ("battle.handicap", BATTLE_ROW_IDS["handicap"]),
    ):
        bindings[key] = SettingBinding(
            "save_native_setting_get",
            "save_native_setting_set",
            0x100 | row_id,
            CALL_WITH_ARGUMENT,
            battle_defaults[row_id],
        )

    practice_defaults = practice_configured_row_defaults(selection)
    practice_rows = (
        ("practice.health", PRACTICE_GENERAL_ROW_IDS["health"]),
        ("practice.commands", PRACTICE_GENERAL_ROW_IDS["commands"]),
        ("practice.damage", PRACTICE_GENERAL_ROW_IDS["damage"]),
        ("practice.opponent.status", PRACTICE_OPPONENT_ROW_IDS["status"]),
        ("practice.opponent.strength", PRACTICE_OPPONENT_ROW_IDS["strength"]),
        ("practice.opponent.attack", PRACTICE_OPPONENT_ROW_IDS["attack"]),
        ("practice.opponent.guard", PRACTICE_OPPONENT_ROW_IDS["guard"]),
        ("practice.opponent.move", PRACTICE_OPPONENT_ROW_IDS["move"]),
        (
            "practice.opponent.substitution_jutsu",
            PRACTICE_OPPONENT_ROW_IDS["substitution_jutsu"],
        ),
        ("practice.opponent.linked_attack", PRACTICE_OPPONENT_ROW_IDS["linked_attack"]),
        (
            "practice.opponent.extra_hit_counter",
            PRACTICE_OPPONENT_ROW_IDS["extra_hit_counter"],
        ),
    )
    for key, row_id in practice_rows:
        bindings[key] = SettingBinding(
            "save_native_setting_get",
            "save_native_setting_set",
            0x200 | row_id,
            CALL_WITH_ARGUMENT,
            practice_defaults[row_id],
        )

    value_only: tuple[tuple[str, str, str, Callable, int], ...] = (
        ("mechanics.chakra", "chakra_mode_get", "chakra_mode_set", chakra_default, 0),
        (
            "mechanics.ultimate_jutsu",
            "ultimate_jutsu_mode_get",
            "ultimate_jutsu_mode_set",
            ultimate_jutsu_default,
            0,
        ),
        ("mechanics.shadowblur", "shadowblur_get", "shadowblur_set", shadowblur_default, 0),
        ("mechanics.extra_hit", "extra_hit_get", "extra_hit_set", extra_hit_default, 0),
        (
            "mechanics.sub_active_frames",
            "sub_active_frames_get",
            "sub_active_frames_set",
            sub_active_frames_default,
            0,
        ),
        (
            "mechanics.xdash_chakra_cost",
            "xdash_chakra_cost_option_get",
            "xdash_chakra_cost_option_set",
            xdash_chakra_cost_option_default,
            0,
        ),
        ("mechanics.support", "support_get", "support_set", support_default, 0),
        (
            "mechanics.substitution",
            "substitution_gauge_mode_get",
            "substitution_gauge_mode_set",
            substitution_default,
            0,
        ),
    )
    for key, getter, setter, resolver, argument in value_only:
        bindings[key] = SettingBinding(
            getter,
            setter,
            argument,
            CALL_WITH_VALUE,
            resolver(selection),
        )

    item_defaults = items_option_defaults(selection)
    bindings["mechanics.items"] = SettingBinding(
        "items_settings_option_get",
        "items_settings_option_set",
        0,
        CALL_WITH_ARGUMENT,
        item_defaults[0],
    )
    gauge_defaults = gauge_option_defaults(selection)
    substitution_children = (
        (
            "mechanics.substitution.chakra.minimum_chakra",
            4,
            chakra_minimum_option_default(selection),
        ),
        ("mechanics.substitution.gauge.recovery_delay_seconds", 0, gauge_defaults[0]),
        (
            "mechanics.substitution.gauge.refill_seconds_per_stock",
            1,
            gauge_defaults[1],
        ),
        ("mechanics.substitution.gauge.damage_recovery", 2, gauge_defaults[2]),
        (
            "mechanics.substitution.gauge.damage_percent_per_stock",
            3,
            gauge_defaults[3],
        ),
    )
    for key, argument, default in substitution_children:
        bindings[key] = SettingBinding(
            "substitution_gauge_option_get",
            "substitution_gauge_option_set",
            argument,
            CALL_WITH_ARGUMENT,
            default,
        )

    bindings["mechanics.items.custom.availability"] = SettingBinding(
        "items_settings_option_get",
        "items_settings_option_set",
        1,
        CALL_WITH_ARGUMENT,
        item_defaults[1],
    )
    for argument, (_code, key, _label) in enumerate(FIELD_ITEMS, start=2):
        bindings[f"mechanics.items.custom.{key}"] = SettingBinding(
            "items_settings_option_get",
            "items_settings_option_set",
            argument,
            CALL_WITH_ARGUMENT,
            item_defaults[argument],
        )
    return bindings


def save_appendix_schema_fragment(
    selection,
    *,
    owner: str,
    path: Path | None = None,
) -> PayloadFragment:
    source = path if path is not None else Path(__file__).resolve().parents[2] / "save_appendix.tsv"
    schema_version, rows = load_save_appendix(source)
    bindings = _bindings(selection)
    row_keys = {row.key for row in rows}
    unresolved = sorted(row_keys - bindings.keys())
    missing = sorted(bindings.keys() - row_keys)
    if unresolved:
        raise ValueError(f"Unresolved save appendix keys: {', '.join(unresolved)}")
    if missing:
        raise ValueError(f"Save appendix omits settings: {', '.join(missing)}")

    payload = bytearray(struct.pack("<HHI", schema_version, len(rows), 0))
    relocations: list[PayloadRelocation] = []
    for row in rows:
        binding = bindings[row.key]
        maximum = row.option_count - 1
        if not 0 <= binding.default <= maximum:
            raise ValueError(
                f"Save appendix default for {row.key} is {binding.default}, maximum is {maximum}"
            )
        descriptor_offset = len(payload)
        payload.extend(
            struct.pack(
                "<HHHHIIII",
                row.setting_id,
                maximum,
                binding.call_kind,
                0,
                binding.argument,
                binding.default,
                0,
                0,
            )
        )
        relocations.extend(
            (
                PayloadRelocation(
                    offset=descriptor_offset + 16,
                    kind="abs32",
                    symbol=binding.getter,
                ),
                PayloadRelocation(
                    offset=descriptor_offset + 20,
                    kind="abs32",
                    symbol=binding.setter,
                ),
            )
        )
    expected_size = SCHEMA_HEADER_SIZE + len(rows) * DESCRIPTOR_SIZE
    if len(payload) != expected_size:
        raise AssertionError("Save appendix descriptor layout changed unexpectedly")
    return PayloadFragment(
        owner=owner,
        symbol="save_appendix_schema",
        kind="rodata",
        alignment=4,
        payload=bytes(payload),
        relocations=tuple(relocations),
    )


def save_appendix_load_status_fragment(*, owner: str) -> PayloadFragment:
    return PayloadFragment(
        owner=owner,
        symbol="save_appendix_load_status",
        kind="data",
        alignment=4,
        payload=bytes(8),
    )


def save_appendix_next_update_fragment(selection, *, owner: str) -> PayloadFragment:
    first_save_only = any(
        node.path == ("features", "memory_card", "display_only_first_save")
        and node.enabled
        for node in selection.nodes
    )
    return PayloadFragment(
        owner=owner,
        symbol="save_appendix_next_update",
        kind="rodata",
        alignment=4,
        payload=struct.pack("<I", 0 if first_save_only else 0x001E3F20),
        relocations=(
            PayloadRelocation(
                offset=0,
                kind="abs32",
                symbol="display_only_first_save_update",
            ),
        ) if first_save_only else (),
    )
