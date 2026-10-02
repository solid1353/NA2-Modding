from __future__ import annotations

import csv
import re
import struct
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

from na228_builder.infrastructure.modules.payload_builder.operations import (
    PayloadFragment,
    PayloadRelocation,
)
from ..settings.ingame.battle_mechanics.battle_settings_runtime import (
    BATTLE_MECHANICS_PATH,
    EXTENDED_ITEMS_PATH,
    MATCH_SETUP_PATH,
    chakra_default,
    extra_hit_default,
    shadowblur_default,
    substitution_input_default,
    substitution_default,
    support_default,
    ultimate_jutsu_default,
    xdash_chakra_cost_option_default,
)
from ..general.controls.control_defaults import (
    added_binding_save_defaults,
    controls_layout,
)
from ..settings.ingame.shared.menu_options import (
    MOD_SETTINGS_PATH,
    items_mode_option,
    menu_option_bindings,
)
from ..settings.ingame.shared.native_settings_defaults import (
    BATTLE_ROW_IDS,
    PRACTICE_GENERAL_ROW_IDS,
    PRACTICE_OPPONENT_ROW_IDS,
    battle_configured_row_defaults,
    practice_configured_row_defaults,
)


TABLE_PATH = Path(__file__).resolve().parents[2] / "resources" / "save_appendix.tsv"
APPENDIX_SIZE = 0x1000
APPENDIX_HEADER_SIZE = 0x10
APPENDIX_ENTRY_SIZE = 4
CALL_WITH_ARGUMENT = 0
CALL_WITH_VALUE = 1
EXTRA_CONTROL_KEYS = (
    "controls.p1.guard",
    "controls.p1.substitution",
    "controls.p1.item_select_l",
    "controls.p1.item_select_r",
    "controls.p2.guard",
    "controls.p2.substitution",
    "controls.p2.item_select_l",
    "controls.p2.item_select_r",
)
# Save keys of the menu options outside Battle Mechanics, whose keys follow their paths.
MOD_KEYS = {
    MOD_SETTINGS_PATH + ("simple_display",): "mod.simple_display",
    MATCH_SETUP_PATH + ("character_balance",): "mod.character_overrides",
    MATCH_SETUP_PATH + ("balance_overlay",): "mod.balance_overlay",
    MATCH_SETUP_PATH + ("support_selection",): "mod.support_selection",
    EXTENDED_ITEMS_PATH: "mod.extended_items",
}
# Settings saved through their value getter and setter.
VALUE_SETTINGS = (
    ("mechanics.chakra", "chakra_mode_get", "chakra_mode_set", chakra_default),
    ("mechanics.ultimate_jutsu", "ultimate_jutsu_mode_get", "ultimate_jutsu_mode_set",
     ultimate_jutsu_default),
    ("mechanics.shadowblur", "shadowblur_get", "shadowblur_set", shadowblur_default),
    ("mechanics.extra_hit", "extra_hit_get", "extra_hit_set", extra_hit_default),
    ("mechanics.substitution_input", "substitution_input_get", "substitution_input_set",
     substitution_input_default),
    ("mechanics.xdash_chakra_cost", "xdash_chakra_cost_option_get",
     "xdash_chakra_cost_option_set", xdash_chakra_cost_option_default),
    ("mechanics.support", "support_get", "support_set", support_default),
    ("mechanics.substitution_resource", "substitution_gauge_mode_get",
     "substitution_gauge_mode_set", substitution_default),
)
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
    _, start_text, start_suffix, end_text, end_suffix, step_text, step_suffix = (
        match.groups()
    )
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
    if any(not alternative for alternative in alternatives):
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
    # Type rows name a value list that later rows use by name; they are not saved.
    types: dict[str, str] = {}
    for line_number, raw in enumerate(reader, start=3):
        if None in raw or any(value is None for value in raw.values()):
            raise ValueError(f"save_appendix.tsv line {line_number} is malformed")
        identifier_text = raw["id"]
        if identifier_text == "type":
            name = raw["key"]
            if rows or not re.fullmatch(r"[a-z_]+", name) or name in types:
                raise ValueError(
                    f"save_appendix.tsv line {line_number} must be a uniquely named type "
                    "before the settings"
                )
            _option_count(raw["values"])
            types[name] = raw["values"]
            continue
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
            AppendixRow(
                setting_id, key, label, _option_count(types.get(raw["values"], raw["values"]))
            )
        )
    if APPENDIX_HEADER_SIZE + len(rows) * APPENDIX_ENTRY_SIZE > APPENDIX_SIZE:
        raise ValueError("save_appendix.tsv exceeds the 0x1000-byte appendix capacity")
    return schema_version, tuple(rows)


def _bindings(selection) -> dict[str, SettingBinding]:
    options = {
        MOD_KEYS.get(path) or "mechanics." + ".".join(path[len(BATTLE_MECHANICS_PATH):]):
            option
        for path, option in menu_option_bindings(selection).items()
    }
    options["mechanics.items"] = items_mode_option(selection)
    bindings = {
        key: SettingBinding(option.getter, option.setter, option.argument,
                            CALL_WITH_ARGUMENT, option.default)
        for key, option in options.items()
    }
    control_defaults = added_binding_save_defaults(controls_layout(selection))
    for argument, key in enumerate(EXTRA_CONTROL_KEYS):
        bindings[key] = SettingBinding(
            "control_settings_extra_get",
            "control_settings_extra_set",
            argument,
            CALL_WITH_ARGUMENT,
            control_defaults[argument],
        )
    battle_defaults = battle_configured_row_defaults(selection)
    practice_defaults = practice_configured_row_defaults(selection)
    for prefix, kind, row_ids, defaults in (
        ("battle.", 0x100, BATTLE_ROW_IDS, battle_defaults),
        ("practice.", 0x200, PRACTICE_GENERAL_ROW_IDS, practice_defaults),
        ("practice.opponent.", 0x200, PRACTICE_OPPONENT_ROW_IDS, practice_defaults),
    ):
        for key, row_id in row_ids.items():
            bindings[prefix + key] = SettingBinding(
                "save_native_setting_get",
                "save_native_setting_set",
                kind | row_id,
                CALL_WITH_ARGUMENT,
                defaults[row_id],
            )
    for key, getter, setter, resolver in VALUE_SETTINGS:
        bindings[key] = SettingBinding(getter, setter, 0, CALL_WITH_VALUE, resolver(selection))
    return bindings


def save_appendix_schema_fragment(selection, *, owner: str) -> PayloadFragment:
    schema_version, rows = load_save_appendix(TABLE_PATH)
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
        payload=bytes(4),
    )
