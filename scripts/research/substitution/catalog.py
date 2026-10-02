#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import struct
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable, Mapping, Sequence, TextIO


REPOSITORY = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPOSITORY))

from na228_builder.infrastructure.common import sha256_hex
from scripts.lib.paths import load_paths


EXPECTED_ELF_SHA256 = (
    "20C0A40D70EA412CD431993A2E189B37ECB6054D63AE93BE545470016E1627AF"
)
VIRTUAL_TO_FILE_DELTA = 0x0FFF00
ACTION_RECORD_SIZE = 0x54
TIMING_OFFSET = 0x1A
RESPONSE_SELECTOR_OFFSET = 0x2C
TIMING_FLAG_MASK = 0x000C0000
SUBSTITUTION_BLOCK_FLAG_MASK = 0x02008000
COMMAND_CONTEXT = "Command Chart > character move name"
NA2_SLPS_REF = re.compile(r"^NA2_SLPS@0x([0-9A-Fa-f]+)$")
AUXILIARY_CHARACTER_RECORDS = (
    ("0x1A", "0x0059C7A0"),
    ("0x1D", "0x0059CF80"),
    ("0x1E", "0x0059D750"),
    ("0x1F", "0x0059DF20"),
)
RUNTIME_TIMING_MUTATIONS: Mapping[tuple[int, int], Mapping[str, object]] = {
    (0x40, 0x2B): {
        "writers": "FUN_002B5250@0x002B5250",
        "values": "template_byte|-1|0",
        "block_mutated": True,
        "summary": (
            "state 0x2B can select a template byte and set +0x14:0x00008000, "
            "or write -1/0 and clear that block bit"
        ),
    },
    (0x40, 0x2C): {
        "writers": (
            "FUN_002B5250@0x002B5250;FUN_002B68F0@0x002B68F0"
        ),
        "values": "template_byte|-1|-2|0|2|retained",
        "block_mutated": True,
        "summary": (
            "state 0x2C can select a template byte/-1/retained and toggle "
            "+0x14:0x00008000; the hit callback then selects -2/0/2 from "
            "the other fighter's +0xB64 tier"
        ),
    },
    (0x40, 0x2D): {
        "writers": "FUN_002B5250@0x002B5250",
        "values": "template_byte|-1|0",
        "block_mutated": True,
        "summary": (
            "state 0x2D can select a template byte and set +0x14:0x00008000, "
            "or write -1/0 and clear that block bit"
        ),
    },
    (0x43, 0x27): {
        "writers": "FUN_002BDF80@0x002BDF80",
        "values": "template_byte|0",
        "block_mutated": True,
        "summary": (
            "state 0x27 can select a template byte and set +0x14:0x00008000, "
            "or write 0 and clear that block bit"
        ),
    },
    (0x45, 0x2A): {
        "writers": "FUN_002C55B0@0x002C55B0",
        "values": "stock|1|2|3",
        "block_mutated": False,
        "summary": (
            "state 0x2A retains stock timing at tier <=1 and writes 1/2/3 "
            "when fighter +0x69B0 reaches tiers 2/3/4+"
        ),
    },
    (0x4C, 0x1E): {
        "writers": "FUN_002D5320@0x002D5320",
        "values": "template_byte|template_byte+1|template_byte+2",
        "block_mutated": False,
        "summary": (
            "state 0x1E writes a template timing plus 0/1/2 according to "
            "fighter +0x4E3E tier"
        ),
    },
}


def _require_range(data: bytes, offset: int, size: int, label: str) -> None:
    if offset < 0 or offset + size > len(data):
        raise ValueError(
            f"{label} range 0x{offset:X}..0x{offset + size:X} "
            f"is outside the clean ELF size 0x{len(data):X}"
        )


def _is_exceptional(record: Mapping[str, object]) -> bool:
    return record["raw_timing"] != 0 or record["effective_timing"] != 0


def _is_blocked(record: Mapping[str, object]) -> bool:
    return record["substitution_block_flags"] != "0x00000000"


def _parse_virtual(value: str, label: str) -> int:
    try:
        result = int(value, 0)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} has an invalid address: {value!r}") from exc
    if result < VIRTUAL_TO_FILE_DELTA:
        raise ValueError(f"{label} is below the boot-ELF load mapping: {value!r}")
    return result


def _parse_source_ref(value: str) -> int | None:
    match = NA2_SLPS_REF.fullmatch(value)
    return int(match.group(1), 16) if match else None


def _mapping_indexes(
    mapping_rows: Iterable[Mapping[str, str]],
) -> tuple[dict[int, Mapping[str, str]], dict[int, Mapping[str, str]], int]:
    by_source: dict[int, Mapping[str, str]] = {}
    by_reference: dict[int, Mapping[str, str]] = {}
    admitted = 0
    for row in mapping_rows:
        if row.get("display_context") != COMMAND_CONTEXT:
            continue
        admitted += 1
        source = _parse_source_ref(row.get("source_ref", ""))
        if source is None:
            raise ValueError(
                f"Command mapping {row.get('id')!r} has no NA2_SLPS source_ref"
            )
        reference_text = row.get("reference_refs", "")
        if reference_text:
            reference = _parse_source_ref(reference_text)
            if reference is None:
                raise ValueError(
                    f"Command mapping {row.get('id')!r} has an unsupported "
                    "reference_refs value"
                )
            if reference in by_reference:
                raise ValueError(
                    f"duplicate Command mapping reference 0x{reference:X}"
                )
            by_reference[reference] = row
        else:
            if source in by_source:
                raise ValueError(f"duplicate direct Command source 0x{source:X}")
            by_source[source] = row
    return by_source, by_reference, admitted


def _timing_policy(raw_timing: int, flags_10: int) -> tuple[int, str]:
    effective = raw_timing
    if raw_timing == 0 and flags_10 & TIMING_FLAG_MASK:
        effective = -1
    if effective < 0:
        denominator = -effective * 2 + 1
        return effective, f"mt_modulo_1_of_{denominator}_current_record"
    distance = min(effective, 3)
    return effective, f"deterministic_current_plus_{distance}_earlier"


def _negative_rng_policy(effective_timing: int) -> tuple[int | None, int | None]:
    if effective_timing >= 0:
        return None, None
    modulus = -effective_timing * 2 + 1
    return modulus, (1 << 32) // modulus


def scan_action_catalog(
    elf: bytes,
    character_rows: Iterable[Mapping[str, str]],
    mapping_rows: Iterable[Mapping[str, str]],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    by_source, by_reference, command_mapping_count = _mapping_indexes(mapping_rows)
    records: list[dict[str, object]] = []
    optional_bases = 0

    for character in character_rows:
        character_name = character.get("character", "")
        if not character_name:
            raise ValueError("character catalog row has no character name")
        catalog_scope = character.get("catalog_scope", "primary")
        try:
            character_id = int(character.get("id", ""), 0)
        except ValueError as exc:
            raise ValueError(
                f"{character_name} has an invalid character id"
            ) from exc
        metadata_address = _parse_virtual(
            character.get("record_address", ""),
            f"{character_name} metadata",
        )
        metadata_offset = metadata_address - VIRTUAL_TO_FILE_DELTA
        _require_range(elf, metadata_offset + 0x28, 0x0C, f"{character_name} metadata")
        count, _, primary_base, optional_base = struct.unpack_from(
            "<HHII", elf, metadata_offset + 0x28
        )
        if not count:
            raise ValueError(f"{character_name} has an empty action table")
        if optional_base:
            optional_bases += 1
        action_base = optional_base or primary_base

        for index in range(count):
            record_address = action_base + index * ACTION_RECORD_SIZE
            record_offset = record_address - VIRTUAL_TO_FILE_DELTA
            _require_range(
                elf,
                record_offset,
                ACTION_RECORD_SIZE,
                f"{character_name} action {index}",
            )
            name_field_offset = record_offset + 0x08
            (name_pointer,) = struct.unpack_from("<I", elf, name_field_offset)
            name_source_offset = name_pointer - VIRTUAL_TO_FILE_DELTA
            flags_10, flags_14 = struct.unpack_from("<II", elf, record_offset + 0x10)
            (raw_timing,) = struct.unpack_from(
                "<b", elf, record_offset + TIMING_OFFSET
            )
            effective_timing, policy = _timing_policy(raw_timing, flags_10)
            rng_modulus, rng_passing_words = _negative_rng_policy(effective_timing)
            response_selector = elf[record_offset + RESPONSE_SELECTOR_OFFSET]
            substitution_block_flags = flags_14 & SUBSTITUTION_BLOCK_FLAG_MASK
            runtime_mutation = RUNTIME_TIMING_MUTATIONS.get(
                (character_id, index), {}
            )

            mapping = by_reference.get(name_field_offset)
            mapping_join = "reference" if mapping is not None else ""
            if mapping is None:
                mapping = by_source.get(name_source_offset)
                if mapping is not None:
                    mapping_join = "source"

            records.append(
                {
                    "character": character_name,
                    "character_id": character_id,
                    "catalog_scope": catalog_scope,
                    "metadata_address": f"0x{metadata_address:08X}",
                    "record_index": index,
                    "record_index_hex": f"0x{index:02X}",
                    "record_address": f"0x{record_address:08X}",
                    "record_file_offset": f"0x{record_offset:X}",
                    "timing_address": f"0x{record_address + TIMING_OFFSET:08X}",
                    "timing_file_offset": f"0x{record_offset + TIMING_OFFSET:X}",
                    "flags_10": f"0x{flags_10:08X}",
                    "flags_14": f"0x{flags_14:08X}",
                    "substitution_block_flags": f"0x{substitution_block_flags:08X}",
                    "raw_timing": raw_timing,
                    "effective_timing": effective_timing,
                    "policy": policy,
                    "negative_rng_modulus": rng_modulus,
                    "negative_rng_passing_u32_words": rng_passing_words,
                    "negative_rng_total_u32_words": (
                        1 << 32 if rng_modulus is not None else None
                    ),
                    "response_selector_2c": f"0x{response_selector:02X}",
                    "runtime_timing_mutated": bool(runtime_mutation),
                    "runtime_timing_writers": runtime_mutation.get("writers", ""),
                    "runtime_timing_values": runtime_mutation.get("values", ""),
                    "runtime_substitution_block_mutated": runtime_mutation.get(
                        "block_mutated", False
                    ),
                    "runtime_mutation_summary": runtime_mutation.get("summary", ""),
                    "command_mapping_id": mapping.get("id", "") if mapping else "",
                    "command_name": mapping.get("donor", "") if mapping else "",
                    "mapping_join": mapping_join,
                    "name_pointer": f"0x{name_pointer:08X}",
                    "name_source_offset": f"0x{name_source_offset:X}",
                    "name_field_offset": f"0x{name_field_offset:X}",
                }
            )

    raw_counts = Counter(record["raw_timing"] for record in records)
    effective_counts = Counter(record["effective_timing"] for record in records)
    exceptional = [record for record in records if _is_exceptional(record)]
    named = [record for record in records if record["command_mapping_id"]]
    mapping_groups: dict[object, list[dict[str, object]]] = {}
    for record in named:
        mapping_groups.setdefault(record["command_mapping_id"], []).append(record)
    named_mapping_ids = set(mapping_groups)
    mixed_mapping_profiles: list[dict[str, object]] = []
    mixed_timing_mapping_ids = 0
    mixed_block_mapping_ids = 0
    for mapping_id, group in mapping_groups.items():
        profiles = {
            (record["effective_timing"], record["substitution_block_flags"])
            for record in group
        }
        timings = {record["effective_timing"] for record in group}
        blocks = {record["substitution_block_flags"] for record in group}
        if len(timings) > 1:
            mixed_timing_mapping_ids += 1
        if len(blocks) > 1:
            mixed_block_mapping_ids += 1
        if len(profiles) > 1:
            mixed_mapping_profiles.append(
                {
                    "command_mapping_id": mapping_id,
                    "command_name": group[0]["command_name"],
                    "instances": [
                        {
                            "character": record["character"],
                            "character_id": record["character_id"],
                            "record_index": record["record_index"],
                            "record_address": record["record_address"],
                            "raw_timing": record["raw_timing"],
                            "effective_timing": record["effective_timing"],
                            "substitution_block_flags": record[
                                "substitution_block_flags"
                            ],
                        }
                        for record in group
                    ],
                }
            )
        for record in group:
            record["command_mapping_instances"] = len(group)
            record["command_mapping_policy_variants"] = len(profiles)
    for record in records:
        if not record["command_mapping_id"]:
            record["command_mapping_instances"] = 0
            record["command_mapping_policy_variants"] = 0
    primary_records = [
        record for record in records if record["catalog_scope"] == "primary"
    ]
    auxiliary_records = [
        record for record in records if record["catalog_scope"] == "auxiliary"
    ]
    primary_named = [
        record for record in named if record["catalog_scope"] == "primary"
    ]
    auxiliary_named = [
        record for record in named if record["catalog_scope"] == "auxiliary"
    ]
    primary_mapping_ids = {
        record["command_mapping_id"] for record in primary_named
    }
    auxiliary_mapping_ids = {
        record["command_mapping_id"] for record in auxiliary_named
    }
    blocked = [record for record in records if _is_blocked(record)]
    blocked_flag_counts = Counter(
        str(record["substitution_block_flags"]) for record in blocked
    )
    response_selector_counts = Counter(
        str(record["response_selector_2c"]) for record in records
    )
    runtime_mutated = [
        record for record in records if record["runtime_timing_mutated"]
    ]
    summary: dict[str, object] = {
        "characters": len({record["character_id"] for record in records}),
        "records": len(records),
        "scope_counts": {
            "primary": {
                "characters": len(
                    {record["character_id"] for record in primary_records}
                ),
                "records": len(primary_records),
            },
            "auxiliary": {
                "characters": len(
                    {record["character_id"] for record in auxiliary_records}
                ),
                "records": len(auxiliary_records),
            },
        },
        "optional_action_bases": optional_bases,
        "raw_timing_counts": {
            str(key): raw_counts[key] for key in sorted(raw_counts)
        },
        "effective_timing_counts": {
            str(key): effective_counts[key] for key in sorted(effective_counts)
        },
        "flagged_zero_to_negative_one": sum(
            record["raw_timing"] == 0 and record["effective_timing"] == -1
            for record in records
        ),
        "exceptional_records": len(exceptional),
        "exceptional_named": sum(
            bool(record["command_mapping_id"]) for record in exceptional
        ),
        "exceptional_unnamed": sum(
            not record["command_mapping_id"] for record in exceptional
        ),
        "substitution_block_flagged_records": len(blocked),
        "substitution_block_flag_counts": {
            key: blocked_flag_counts[key] for key in sorted(blocked_flag_counts)
        },
        "substitution_block_flagged_named": sum(
            bool(record["command_mapping_id"]) for record in blocked
        ),
        "substitution_block_flagged_exceptional": sum(
            _is_exceptional(record) for record in blocked
        ),
        "response_selector_counts": {
            key: response_selector_counts[key]
            for key in sorted(response_selector_counts)
        },
        "runtime_timing_mutated_records": len(runtime_mutated),
        "runtime_timing_mutated_named": sum(
            bool(record["command_mapping_id"]) for record in runtime_mutated
        ),
        "runtime_substitution_block_mutated_records": sum(
            bool(record["runtime_substitution_block_mutated"])
            for record in runtime_mutated
        ),
        "runtime_timing_mutations": [
            {
                key: record[key]
                for key in (
                    "character",
                    "character_id",
                    "record_index",
                    "record_address",
                    "timing_address",
                    "raw_timing",
                    "effective_timing",
                    "substitution_block_flags",
                    "command_mapping_id",
                    "command_name",
                    "runtime_timing_writers",
                    "runtime_timing_values",
                    "runtime_substitution_block_mutated",
                    "runtime_mutation_summary",
                )
            }
            for record in runtime_mutated
        ],
        "command_mapping_rows": command_mapping_count,
        "mapping_ids_in_primary_tables": len(primary_mapping_ids),
        "mapping_ids_in_auxiliary_tables": len(auxiliary_mapping_ids),
        "mapping_ids_in_all_tables": len(named_mapping_ids),
        "command_mapping_rows_unmatched": (
            command_mapping_count - len(named_mapping_ids)
        ),
        "command_mapping_instance_count_distribution": {
            str(key): value
            for key, value in sorted(
                Counter(len(group) for group in mapping_groups.values()).items()
            )
        },
        "command_mapping_ids_with_multiple_instances": sum(
            len(group) > 1 for group in mapping_groups.values()
        ),
        "command_mapping_ids_with_mixed_reliability": len(
            mixed_mapping_profiles
        ),
        "command_mapping_ids_with_mixed_timing": mixed_timing_mapping_ids,
        "command_mapping_ids_with_mixed_block_flags": mixed_block_mapping_ids,
        "mixed_command_mapping_reliability": sorted(
            mixed_mapping_profiles,
            key=lambda item: str(item["command_mapping_id"]),
        ),
        "mapped_record_instances_in_primary_tables": len(primary_named),
        "mapped_record_instances_in_auxiliary_tables": len(auxiliary_named),
        "mapped_record_instances": len(named),
    }
    return records, summary


def _read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def load_clean_catalog() -> tuple[list[dict[str, object]], dict[str, object], Path]:
    paths = load_paths(REPOSITORY)
    elf_path = paths.path("source_na2", "SLPS_258.37")
    elf = elf_path.read_bytes()
    digest = sha256_hex(elf)
    if digest != EXPECTED_ELF_SHA256:
        raise ValueError(
            f"clean ELF SHA-256 mismatch: expected {EXPECTED_ELF_SHA256}, "
            f"got {digest}"
        )
    characters: list[Mapping[str, str]] = [
        {**row, "catalog_scope": "primary"}
        for row in _read_tsv(paths.path("resources", "character_data.tsv"))
    ]
    characters.extend(
        {
            "character": f"Auxiliary fighter {character_id}",
            "id": character_id,
            "record_address": record_address,
            "catalog_scope": "auxiliary",
        }
        for character_id, record_address in AUXILIARY_CHARACTER_RECORDS
    )
    mappings = _read_tsv(
        paths.path(
            "builder", "patches", "localization", "strings", "mappings.tsv"
        )
    )
    records, summary = scan_action_catalog(elf, characters, mappings)
    summary["elf_sha256"] = digest
    return records, summary, elf_path


def _character_filter(value: str, records: Sequence[Mapping[str, object]]) -> set[int]:
    try:
        selected_id = int(value, 0)
    except ValueError:
        selected_id = -1
    if selected_id >= 0:
        matches = {
            int(record["character_id"])
            for record in records
            if int(record["character_id"]) == selected_id
        }
    else:
        folded = value.casefold()
        matches = {
            int(record["character_id"])
            for record in records
            if str(record["character"]).casefold() == folded
        }
    if not matches:
        raise ValueError(f"unknown character selector: {value!r}")
    return matches


def _mapping_filter(
    value: str, records: Sequence[Mapping[str, object]]
) -> set[str]:
    folded = value.casefold()
    matches = {
        str(record["command_mapping_id"])
        for record in records
        if record["command_mapping_id"]
        and (
            str(record["command_mapping_id"]).casefold() == folded
            or str(record["command_name"]).casefold() == folded
        )
    }
    if not matches:
        raise ValueError(f"unknown Command Chart mapping or title: {value!r}")
    return matches


def _write_tsv(records: Sequence[Mapping[str, object]], stream: TextIO) -> None:
    if not records:
        return
    fieldnames = list(records[0])
    writer = csv.DictWriter(
        stream,
        fieldnames=fieldnames,
        delimiter="\t",
        lineterminator="\n",
        extrasaction="raise",
    )
    writer.writeheader()
    writer.writerows(records)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Enumerate NA2 substitution timing policy from clean character "
            "action records without changing the source ELF."
        )
    )
    parser.add_argument(
        "--character",
        help="Exact character name or decimal/0x-prefixed character ID.",
    )
    parser.add_argument(
        "--scope",
        choices=("primary", "auxiliary"),
        help="Keep only primary-roster or auxiliary-fighter record rows.",
    )
    parser.add_argument(
        "--mapping",
        help="Exact Command Chart mapping ID or case-insensitive exact title.",
    )
    parser.add_argument(
        "--exceptional-only",
        action="store_true",
        help="Keep nonzero raw timing and zero records converted by flags.",
    )
    parser.add_argument(
        "--named-only",
        action="store_true",
        help="Keep records with an admitted Command Chart title.",
    )
    parser.add_argument(
        "--blocked-only",
        action="store_true",
        help="Keep records rejected by either predicate-level +0x14 flag.",
    )
    parser.add_argument(
        "--runtime-mutated-only",
        action="store_true",
        help="Keep records whose live timing is changed by a known callback.",
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Emit the complete clean-source summary without record rows.",
    )
    parser.add_argument("--format", choices=("json", "tsv"), default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    records, summary, elf_path = load_clean_catalog()
    selected: Sequence[Mapping[str, object]] = records
    if args.scope:
        selected = [
            record for record in selected if record["catalog_scope"] == args.scope
        ]
    if args.character:
        ids = _character_filter(args.character, records)
        selected = [record for record in selected if record["character_id"] in ids]
    if args.mapping:
        mapping_ids = _mapping_filter(args.mapping, records)
        selected = [
            record
            for record in selected
            if record["command_mapping_id"] in mapping_ids
        ]
    if args.exceptional_only:
        selected = [record for record in selected if _is_exceptional(record)]
    if args.named_only:
        selected = [record for record in selected if record["command_mapping_id"]]
    if args.blocked_only:
        selected = [record for record in selected if _is_blocked(record)]
    if args.runtime_mutated_only:
        selected = [
            record for record in selected if record["runtime_timing_mutated"]
        ]

    if args.summary_only:
        if args.format != "json":
            raise ValueError("--summary-only requires --format json")
        output = {
            "source_elf": str(elf_path),
            "summary": summary,
        }
        print(json.dumps(output, indent=2, sort_keys=True))
    elif args.format == "json":
        output = {
            "source_elf": str(elf_path),
            "summary": summary,
            "selected_records": len(selected),
            "records": selected,
        }
        print(json.dumps(output, indent=2, sort_keys=True))
    else:
        _write_tsv(selected, sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
