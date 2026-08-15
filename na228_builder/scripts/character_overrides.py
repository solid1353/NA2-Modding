from __future__ import annotations

import csv
import math
import struct
from dataclasses import dataclass
from pathlib import Path

from ..payload_builder.operations import PayloadFragment


REFERENCE_FIELDS = (
    "character",
    "id",
    "support_id",
    "awakening_ids",
    "linked_uj",
    "linked_jutsu",
    "record_address",
    "default_hp",
    "durability_parameter",
    "incoming_damage_multiplier",
    "offense_multiplier",
    "health_recovery_multiplier",
    "chakra_recovery_multiplier",
)
VALUE_FIELDS = (
    "substitution_cost",
    "hp",
    "damage_multiplier",
    "health_recovery_multiplier",
    "chakra_recovery_multiplier",
)
OVERRIDE_FIELDS = ("id", "base_id", "character", "tier", *VALUE_FIELDS)
TABLE_VERSION = 3
TIER_WIDTH = 4
SUBSTITUTION_COST_INDEX = VALUE_FIELDS.index("substitution_cost")
SUBSTITUTION_COST_DELTA_FLAG = 1 << 16
MAX_AWAKENING_ID = 0x89
MAX_NATIVE_SUPPORT_ID = 0x21


@dataclass(frozen=True)
class CharacterOverrideRow:
    character_id: int | None
    base_id: int | None
    character: str
    tier: str
    values: tuple[float | None, ...]
    substitution_cost_is_delta: bool = False


@dataclass(frozen=True)
class CharacterOverrideConfiguration:
    base: CharacterOverrideRow
    characters: tuple[CharacterOverrideRow, ...]
    reference_characters: tuple[tuple[int, str], ...]
    reference_support_ids: tuple[tuple[int, int | None], ...]
    reference_awakening_ids: tuple[tuple[int, tuple[int, ...]], ...]
    reference_linked_uj: tuple[tuple[int, tuple[int, ...]], ...]
    reference_linked_jutsu: tuple[tuple[int, tuple[int, ...]], ...]
    character_count: int
    resource_files: tuple[Path, ...]

    def row_by_id(self) -> dict[int, CharacterOverrideRow]:
        return {
            row.character_id: row
            for row in self.characters
            if row.character_id is not None
        }

    def support_id_by_character(self) -> dict[int, int | None]:
        return dict(self.reference_support_ids)

    def awakening_ids_by_character(self) -> dict[int, tuple[int, ...]]:
        return dict(self.reference_awakening_ids)

    def linked_uj_by_character(self) -> dict[int, tuple[int, ...]]:
        return dict(self.reference_linked_uj)

    def linked_jutsu_by_character(self) -> dict[int, tuple[int, ...]]:
        return dict(self.reference_linked_jutsu)


def _read_rows(path: Path, fields: tuple[str, ...]) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if tuple(reader.fieldnames or ()) != fields:
            raise ValueError(f"{path}: expected columns " + "\t".join(fields))
        return [
            {key: (value or "").strip() for key, value in row.items()}
            for row in reader
            if any((value or "").strip() for value in row.values())
        ]


def _reference_ids(
    path: Path,
    line: int,
    value: str,
    *,
    field: str,
    label: str,
    maximum: int,
) -> tuple[int, ...]:
    if not value:
        return ()
    result: list[int] = []
    for token in value.split(","):
        token = token.strip()
        if not token:
            raise ValueError(
                f"{path}:{line}: {field} must be comma-separated IDs"
            )
        try:
            reference_id = int(token, 0)
        except ValueError as exc:
            raise ValueError(
                f"{path}:{line}: invalid {label} ID {token!r}"
            ) from exc
        if not 0 <= reference_id <= maximum:
            raise ValueError(
                f"{path}:{line}: {label} ID must be from 0 through {maximum}"
            )
        if reference_id in result:
            raise ValueError(
                f"{path}:{line}: duplicate {label} ID {reference_id}"
            )
        result.append(reference_id)
    return tuple(result)


def _awakening_ids(path: Path, line: int, value: str) -> tuple[int, ...]:
    return _reference_ids(
        path,
        line,
        value,
        field="awakening_ids",
        label="awakening",
        maximum=MAX_AWAKENING_ID,
    )


def _support_id(path: Path, line: int, value: str) -> int | None:
    if not value:
        return None
    try:
        support_id = int(value, 0)
    except ValueError as exc:
        raise ValueError(
            f"{path}:{line}: invalid support ID {value!r}"
        ) from exc
    if not 0 <= support_id <= MAX_NATIVE_SUPPORT_ID:
        raise ValueError(
            f"{path}:{line}: support ID must be from 0 through "
            f"{MAX_NATIVE_SUPPORT_ID}"
        )
    return support_id


def _linked_support_ids(
    path: Path,
    line: int,
    field: str,
    value: str,
) -> tuple[int, ...]:
    return _reference_ids(
        path,
        line,
        value,
        field=field,
        label="support",
        maximum=MAX_NATIVE_SUPPORT_ID,
    )


def _reference_characters(
    path: Path,
) -> tuple[
    dict[int, str],
    dict[int, int | None],
    dict[int, tuple[int, ...]],
    dict[int, tuple[int, ...]],
    dict[int, tuple[int, ...]],
]:
    by_id: dict[int, str] = {}
    by_name: dict[str, int] = {}
    support_id_by_character: dict[int, int | None] = {}
    character_by_support_id: dict[int, int] = {}
    awakening_ids_by_character: dict[int, tuple[int, ...]] = {}
    linked_uj_by_character: dict[int, tuple[int, ...]] = {}
    linked_jutsu_by_character: dict[int, tuple[int, ...]] = {}
    for line, row in enumerate(_read_rows(path, REFERENCE_FIELDS), 2):
        try:
            character_id = int(row["id"], 10)
        except ValueError as exc:
            raise ValueError(f"{path}:{line}: invalid character ID {row['id']!r}") from exc
        character = row["character"]
        if character_id < 0:
            raise ValueError(f"{path}:{line}: character ID must be nonnegative")
        if not character:
            raise ValueError(f"{path}:{line}: character name must not be empty")
        if character_id in by_id:
            raise ValueError(f"{path}:{line}: duplicate character ID {character_id}")
        if character in by_name:
            raise ValueError(f"{path}:{line}: duplicate character name {character!r}")
        by_id[character_id] = character
        by_name[character] = character_id
        support_id = _support_id(path, line, row["support_id"])
        if support_id is not None:
            existing_character_id = character_by_support_id.get(support_id)
            if existing_character_id is not None:
                raise ValueError(
                    f"{path}:{line}: duplicate support ID {support_id}; "
                    f"already assigned to character ID {existing_character_id}"
                )
            character_by_support_id[support_id] = character_id
        support_id_by_character[character_id] = support_id
        awakening_ids_by_character[character_id] = _awakening_ids(
            path,
            line,
            row["awakening_ids"],
        )
        linked_uj_by_character[character_id] = _linked_support_ids(
            path,
            line,
            "linked_uj",
            row["linked_uj"],
        )
        linked_jutsu_by_character[character_id] = _linked_support_ids(
            path,
            line,
            "linked_jutsu",
            row["linked_jutsu"],
        )
    if not by_id:
        raise ValueError(f"{path}: character reference is empty")
    return (
        by_id,
        support_id_by_character,
        awakening_ids_by_character,
        linked_uj_by_character,
        linked_jutsu_by_character,
    )


def _number(
    path: Path,
    line: int,
    field: str,
    value: str,
    *,
    allow_negative: bool = False,
) -> float | None:
    if not value:
        return None
    try:
        result = float(value)
    except ValueError as exc:
        raise ValueError(f"{path}:{line}: {field} must be a number") from exc
    if not math.isfinite(result):
        raise ValueError(f"{path}:{line}: {field} must be finite")
    if not allow_negative and result < 0:
        raise ValueError(f"{path}:{line}: {field} must be nonnegative")
    try:
        encoded = struct.pack("<f", result)
    except OverflowError as exc:
        raise ValueError(f"{path}:{line}: {field} is outside float32 range") from exc
    decoded = struct.unpack("<f", encoded)[0]
    if not math.isfinite(decoded):
        raise ValueError(f"{path}:{line}: {field} is outside float32 range")
    return decoded


def _substitution_cost(
    path: Path,
    line: int,
    value: str,
) -> tuple[float | None, bool]:
    if not value:
        return None, False
    is_delta = value.startswith(("+", "-"))
    return (
        _number(
            path,
            line,
            "substitution_cost",
            value,
            allow_negative=is_delta,
        ),
        is_delta,
    )


def _tier(path: Path, line: int, value: str) -> str:
    try:
        encoded = value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError(f"{path}:{line}: tier must contain only ASCII characters") from exc
    if len(encoded) > TIER_WIDTH:
        raise ValueError(
            f"{path}:{line}: tier must fit within {TIER_WIDTH} ASCII characters"
        )
    return value


def _base_id(
    path: Path,
    line: int,
    character_id: int,
    raw_base_id: str,
    reference_by_id: dict[int, str],
) -> int | None:
    if not raw_base_id:
        return None
    try:
        base_id = int(raw_base_id, 10)
    except ValueError as exc:
        raise ValueError(
            f"{path}:{line}: invalid base character ID {raw_base_id!r}"
        ) from exc
    if base_id not in reference_by_id:
        raise ValueError(f"{path}:{line}: unknown base character ID {base_id}")
    if character_id == base_id:
        raise ValueError(f"{path}:{line}: character cannot be its own base form")
    return base_id


def _override_rows(
    path: Path,
    reference_by_id: dict[int, str],
) -> tuple[CharacterOverrideRow | None, dict[int, CharacterOverrideRow]]:
    base: CharacterOverrideRow | None = None
    characters: dict[int, CharacterOverrideRow] = {}
    for line, raw in enumerate(_read_rows(path, OVERRIDE_FIELDS), 2):
        raw_id = raw["id"]
        raw_base_id = raw["base_id"]
        character = raw["character"]
        tier = _tier(path, line, raw["tier"])
        substitution_cost, substitution_cost_is_delta = _substitution_cost(
            path,
            line,
            raw["substitution_cost"],
        )
        values = (
            substitution_cost,
            *(
                _number(path, line, field, raw[field])
                for field in VALUE_FIELDS[1:]
            ),
        )
        if raw_id == "base":
            if base is not None:
                raise ValueError(f"{path}:{line}: duplicate base row")
            if character != "Base":
                raise ValueError(f"{path}:{line}: base row character must be 'Base'")
            if raw_base_id:
                raise ValueError(f"{path}:{line}: base row base_id must be empty")
            if tier:
                raise ValueError(f"{path}:{line}: base row tier must be empty")
            if substitution_cost_is_delta:
                raise ValueError(
                    f"{path}:{line}: base substitution_cost must be a literal value"
                )
            base = CharacterOverrideRow(None, None, character, tier, values)
            continue
        try:
            character_id = int(raw_id, 10)
        except ValueError as exc:
            raise ValueError(f"{path}:{line}: invalid character ID {raw_id!r}") from exc
        expected = reference_by_id.get(character_id)
        if expected is None:
            raise ValueError(f"{path}:{line}: unknown character ID {character_id}")
        if character != expected:
            raise ValueError(
                f"{path}:{line}: character ID {character_id} must be named {expected!r}"
            )
        if character_id in characters:
            raise ValueError(f"{path}:{line}: duplicate character ID {character_id}")
        characters[character_id] = CharacterOverrideRow(
            character_id,
            _base_id(path, line, character_id, raw_base_id, reference_by_id),
            character,
            tier,
            values,
            substitution_cost_is_delta,
        )
    return base, characters


def _merge_values(
    inherited: tuple[float | None, ...],
    override: tuple[float | None, ...],
) -> tuple[float | None, ...]:
    return tuple(
        replacement if replacement is not None else original
        for original, replacement in zip(inherited, override, strict=True)
    )


def _merge_rows(
    inherited: CharacterOverrideRow,
    override: CharacterOverrideRow,
) -> CharacterOverrideRow:
    return CharacterOverrideRow(
        character_id=inherited.character_id,
        base_id=(
            override.base_id
            if override.base_id is not None
            else inherited.base_id
        ),
        character=override.character,
        tier=override.tier or inherited.tier,
        values=_merge_values(inherited.values, override.values),
        substitution_cost_is_delta=(
            override.substitution_cost_is_delta
            if override.values[SUBSTITUTION_COST_INDEX] is not None
            else inherited.substitution_cost_is_delta
        ),
    )


def load_character_overrides(
    definition_path: Path,
    builder_root: Path,
) -> CharacterOverrideConfiguration:
    configuration_root = (builder_root / "configurations").resolve()
    reference_path = (builder_root.parent / "resources" / "character_data.tsv").resolve()
    (
        reference_by_id,
        support_id_by_character,
        awakening_ids_by_character,
        linked_uj_by_character,
        linked_jutsu_by_character,
    ) = _reference_characters(reference_path)
    definition_path = definition_path.resolve()
    if definition_path.parent == configuration_root:
        override_root = configuration_root / "overrides"
        base_path = override_root / "base.character_overrides.tsv"
        profile_path = override_root / (
            definition_path.stem + ".character_overrides.tsv"
        )
        paths = (base_path.resolve(), profile_path.resolve())
    else:
        paths = (definition_path.with_name("character_overrides.tsv").resolve(),)

    base, merged = _override_rows(paths[0], reference_by_id)
    if base is None:
        raise ValueError(f"{paths[0]}: missing required base row")
    character_order = list(merged)
    for path in paths[1:]:
        profile_base, profile_rows = _override_rows(path, reference_by_id)
        if profile_base is not None:
            base = _merge_rows(base, profile_base)
        for character_id, row in profile_rows.items():
            inherited = merged.get(character_id)
            if inherited is None:
                merged[character_id] = row
                character_order.append(character_id)
            else:
                merged[character_id] = _merge_rows(inherited, row)
    return CharacterOverrideConfiguration(
        base=base,
        characters=tuple(merged[key] for key in character_order),
        reference_characters=tuple(reference_by_id.items()),
        reference_support_ids=tuple(
            (character_id, support_id_by_character[character_id])
            for character_id in reference_by_id
        ),
        reference_awakening_ids=tuple(
            (character_id, awakening_ids_by_character[character_id])
            for character_id in reference_by_id
        ),
        reference_linked_uj=tuple(
            (character_id, linked_uj_by_character[character_id])
            for character_id in reference_by_id
        ),
        reference_linked_jutsu=tuple(
            (character_id, linked_jutsu_by_character[character_id])
            for character_id in reference_by_id
        ),
        character_count=max(reference_by_id) + 1,
        resource_files=(reference_path, *paths),
    )


def _format_number(value: float | None) -> str:
    if value is None:
        return ""
    result = format(value, ".9g")
    if "." not in result and "e" not in result.lower():
        result += ".0"
    return result


def _format_substitution_cost(row: CharacterOverrideRow) -> str:
    value = row.values[SUBSTITUTION_COST_INDEX]
    result = _format_number(value)
    if result and row.substitution_cost_is_delta and not result.startswith("-"):
        return "+" + result
    return result


def render_character_overrides(configuration: CharacterOverrideConfiguration) -> str:
    lines = ["\t".join(OVERRIDE_FIELDS)]
    configured = configuration.row_by_id()
    configured_ids = set(configured)
    rows = (
        configuration.base,
        *configuration.characters,
        *(
            CharacterOverrideRow(
                character_id=character_id,
                base_id=None,
                character=character,
                tier="",
                values=(None,) * len(VALUE_FIELDS),
            )
            for character_id, character in configuration.reference_characters
            if character_id not in configured_ids
        ),
    )
    for row in rows:
        identity = "base" if row.character_id is None else str(row.character_id)
        lines.append(
            "\t".join(
                (
                    identity,
                    "" if row.base_id is None else str(row.base_id),
                    row.character,
                    row.tier,
                    _format_substitution_cost(row),
                    *(_format_number(value) for value in row.values[1:]),
                )
            )
        )
    return "\n".join(lines) + "\n"


def character_override_fragment(
    configuration: CharacterOverrideConfiguration,
    *,
    owner: str,
    symbol: str = "character_overrides",
) -> PayloadFragment:
    row_by_id = configuration.row_by_id()

    def encode_row(row: CharacterOverrideRow | None) -> bytes:
        values = row.values if row is not None else (None,) * len(VALUE_FIELDS)
        flags = sum(
            1 << index
            for index, value in enumerate(values)
            if value is not None
        )
        if row is not None and row.substitution_cost_is_delta:
            flags |= SUBSTITUTION_COST_DELTA_FLAG
        tier = (
            row.tier.encode("ascii").ljust(TIER_WIDTH, b"\0")
            if row is not None
            else b"\0" * TIER_WIDTH
        )
        encoded_values = tuple(value if value is not None else 0.0 for value in values)
        return struct.pack("<I4s5f", flags, tier, *encoded_values)

    payload = struct.pack(
        "<4I",
        TABLE_VERSION,
        configuration.character_count,
        len(VALUE_FIELDS),
        0,
    )
    payload += encode_row(configuration.base)
    payload += b"".join(
        encode_row(row_by_id.get(character_id))
        for character_id in range(configuration.character_count)
    )
    return PayloadFragment(
        owner=owner,
        symbol=symbol,
        kind="rodata",
        alignment=4,
        payload=payload,
    )
