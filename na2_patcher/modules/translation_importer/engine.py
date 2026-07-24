#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Optional, Sequence

from ...image_assembler.iso9660 import Iso9660

TARGET_SPECS = {
    "BTL": ("PRG/BTL.BIN", ["PRG/BTL.BIN", "BTL.BIN"]),
    "ETC": ("PRG/ETC.BIN", ["PRG/ETC.BIN", "ETC.BIN"]),
    "SLPS": ("SLPS_258.37", ["SLPS_258.37"]),
}
DONOR_IDS = frozenset(
    {"NUN5_BTL", "NUN5_ETC", "NUN5_TEXTENG", "NUN5_SLES"}
)
SOURCE_IDS = {
    "NA2_BTL": "BTL",
    "NA2_ETC": "ETC",
    "NA2_SLPS": "SLPS",
}
MAPPING_FIELDS = [
    "id", "enabled", "display_context", "source", "donor", "prefix",
    "replacement", "display_basis", "source_ref", "donor_ref", "mode",
    "capacity", "transform", "arguments", "reference_refs",
    "parent_mapping_id",
]
EXPECTED_SHA1 = {
    "NA2_BTL": "bf7fc7331a2a4f34fc90b84b45772ae1f6bcab03",
    "NA2_ETC": "dcfffd7eb14e484a4c0fbc195599a0b45a9a11c1",
    "NA2_SLPS": "bbe206bbf4da0ee815b437226ceb6a533c95833e",
}
VALID_MODES = {"slot", "sequence"}
DISPLAY_BASIS_PREFIXES = ("seen:", "inferred:", "character:")
PLACEHOLDER_TEXT = frozenset({"unknown", "placeholder", "dummy", "test", "todo", "temp"})
IDENTIFIER_TEXT = re.compile(r"[a-z][a-z0-9_./-]{3,}\Z")
VALID_TRANSFORMS = {
    "",
    "empty",
    "format_arg1",
    "format_args",
    "format_literal_arg1",
    "format_literal_prefix_arg2",
    "format_prefix_arg2",
    "format_suffix_arg2",
    "between_placeholders",
    "after_placeholder2",
    "split_br",
    "split_br_sequence",
    "join_br_parts",
    "insert_br_after_words",
    "append_space",
    "flatten_br_slice",
}
TARGET_RUNTIME_BASES = {
    "SLPS": 0x000FFF00,
    "BTL": 0x006B3F00,
    "ETC": 0x006B3F00,
}
NAMED_COLOR_TAG_EQUIVALENTS = {
    "<WHITE>": ("<WHITE>", "<colorFFFFFF>"),
    "<BLACK>": ("<BLACK>", "<color000000>"),
    "<RED>": ("<RED>",),
}


@dataclass(frozen=True)
class TranslationImportPlan:
    import_rows: list[dict[str, str]]
    targets: dict[str, dict[str, object]]
    text_mappings: tuple[dict[str, object], ...]
    references: tuple["Reference", ...]
    resolved_texts: dict[str, str]
    resolved_sequences: dict[str, tuple[str, ...]]
    source_texts: dict[str, str]
    donor_texts: dict[str, str]
    materialized_templates: dict[str, str]
    clean_targets: dict[str, bytes]
    summary: dict[str, object]
    display_mode: str = "translation"


@dataclass(frozen=True)
class Reference:
    mapping_id: str
    target: str
    target_file_offset: int
    target_runtime_address: int
    resolution: str
    reference_binary: str
    reference_file_offsets: tuple[int, ...]
    parent_mapping_id: str | None
    parent_file_offset: int | None
    parent_runtime_address: int | None


class IsoSource:
    def __init__(self, path: Path) -> None:
        self.path = path.resolve()
        self.image = Iso9660(self.path)

    def read(self, candidates: Sequence[str], label: str) -> bytes:
        normalized = [normalize_path(value) for value in candidates]
        for candidate in normalized:
            record = self.image.by_path.get(candidate)
            if record and not record.is_dir:
                return self.image.read_file(record)
        basenames = {value.rsplit("/", 1)[-1] for value in normalized}
        matches = [
            record
            for path, record in self.image.by_path.items()
            if not record.is_dir and path.rsplit("/", 1)[-1] in basenames
        ]
        if len(matches) == 1:
            return self.image.read_file(matches[0])
        raise FileNotFoundError(f"Could not uniquely locate {label} in {self.path}")


class FolderSource:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        if not self.root.is_dir():
            raise FileNotFoundError(self.root)
        self.files = {normalize_path(path.relative_to(self.root).as_posix()): path
                      for path in self.root.rglob("*") if path.is_file()}

    def read(self, candidates: Sequence[str], label: str) -> bytes:
        normalized = [normalize_path(value) for value in candidates]
        for candidate in normalized:
            path = self.files.get(candidate)
            if path:
                return path.read_bytes()
        basenames = {value.rsplit("/", 1)[-1] for value in normalized}
        matches = [path for name, path in self.files.items()
                   if name.rsplit("/", 1)[-1] in basenames]
        if len(matches) == 1:
            return matches[0].read_bytes()
        raise FileNotFoundError(f"Could not uniquely locate {label} under {self.root}")


def normalize_path(value: str) -> str:
    return value.strip("/\\").replace("\\", "/").upper()


def sha1(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()


def normalize_fullwidth_ascii(text: str) -> str:
    """Normalize fullwidth ASCII-compatible characters in translated output."""
    result: list[str] = []
    for character in text:
        codepoint = ord(character)
        if character == "\u3000":
            result.append(" ")
        elif 0xFF01 <= codepoint <= 0xFF5E:
            result.append(chr(codepoint - 0xFEE0))
        else:
            result.append(character)
    return "".join(result)


def source_from(folder: Optional[Path], iso: Optional[Path], label: str):
    if folder is not None and folder.is_dir():
        return FolderSource(folder)
    if iso is not None and iso.is_file():
        return IsoSource(iso)
    supplied = []
    if folder is not None:
        supplied.append(f"folder={folder}")
    if iso is not None:
        supplied.append(f"iso={iso}")
    raise FileNotFoundError(f"{label} source not found ({', '.join(supplied) or 'no path supplied'})")


def parse_apply(value: str) -> list[str]:
    aliases = {"ELF": "SLPS", "SLES": "SLPS", "EXE": "SLPS"}
    selected = []
    for part in value.replace(";", ",").split(","):
        item = part.strip().upper()
        if not item or item in {"NONE", "NO", "OFF"}:
            continue
        if item == "ALL":
            selected.extend(TARGET_SPECS)
        else:
            selected.append(aliases.get(item, item))
    unknown = sorted(set(selected) - set(TARGET_SPECS))
    if unknown:
        raise ValueError("Unsupported target(s): " + ", ".join(unknown))
    selected = list(dict.fromkeys(selected))
    if not selected:
        raise ValueError("No translation targets selected")
    return selected


def parse_int(value: str, label: str) -> int:
    text = value.strip()
    if not text:
        raise ValueError(f"{label}: missing integer")
    try:
        result = int(text, 0)
    except ValueError as exc:
        raise ValueError(f"{label}: invalid integer {text!r}") from exc
    if result < 0:
        raise ValueError(f"{label}: negative integer")
    return result


def parse_arguments(value: str, label: str) -> dict[str, str]:
    result = {}
    if not value.strip():
        return result
    for item in value.split(";"):
        if "=" not in item:
            raise ValueError(f"{label}: malformed argument {item!r}")
        key, val = item.split("=", 1)
        key = key.strip().lower()
        if not key or key in result:
            raise ValueError(f"{label}: duplicate/empty argument key")
        result[key] = val.strip()
    return result


def parse_ref(
    value: str,
    label: str,
    *,
    allowed: frozenset[str] | set[str],
) -> tuple[str, int]:
    match = re.fullmatch(r"([A-Za-z0-9_]+)@(0[xX][0-9A-Fa-f]+|[0-9]+)", value.strip())
    if not match:
        raise ValueError(f"{label}: malformed reference {value!r}")
    source = match.group(1).upper()
    if source not in allowed:
        raise ValueError(f"{label}: unsupported reference source {source!r}")
    return source, int(match.group(2), 0)


def parse_source_ref(value: str, label: str) -> tuple[str, int]:
    source, offset = parse_ref(
        value,
        label,
        allowed=frozenset(SOURCE_IDS),
    )
    return SOURCE_IDS[source], offset


def parse_donor_ref(value: str, label: str) -> tuple[str, int]:
    return parse_ref(value, label, allowed=DONOR_IDS)


def parse_reference_refs(
    value: str,
    label: str,
) -> tuple[tuple[str, int], ...]:
    refs = tuple(
        parse_source_ref(item.strip(), label)
        for item in value.split(",")
        if item.strip()
    )
    if len(refs) != len(set(refs)):
        raise ValueError(f"{label}: duplicate pointer references")
    return refs


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != MAPPING_FIELDS:
            raise ValueError("mappings.tsv must contain exactly these columns in this order: " + "\t".join(MAPPING_FIELDS))
        verbatim_fields = {"source", "donor", "prefix", "replacement"}
        rows = [
            {
                key: (
                    value or ""
                    if key in verbatim_fields
                    else (value or "").strip()
                )
                for key, value in raw.items()
            }
            for raw in reader
        ]
    ids = [row["id"] for row in rows]
    if any(not value for value in ids) or len(ids) != len(set(ids)):
        raise ValueError("mappings.tsv contains empty or duplicate ids")
    return rows


def references_from_mappings(
    mappings: Sequence[dict[str, object]],
) -> tuple[Reference, ...]:
    by_id = {str(row["id"]): row for row in mappings}
    references: list[Reference] = []
    for row in mappings:
        mapping_id = str(row["id"])
        reference_refs = tuple(row["reference_refs"])
        parent_id_value = str(row["parent_mapping_id"]) or None
        if not reference_refs and parent_id_value is None:
            continue
        label = f"{mapping_id} reference inventory"
        if not reference_refs:
            raise ValueError(f"{label}: parent mappings require reference_refs")
        parent_offset_value: int | None = None
        parent_runtime_value: int | None = None
        if parent_id_value is not None:
            parent = by_id.get(parent_id_value)
            if parent is None:
                raise ValueError(f"{label}: missing parent {parent_id_value}")
            if parent["target"] != row["target"]:
                raise ValueError(f"{label}: parent target differs")
            parent_offset_value = int(parent["target_offset"])
            parent_runtime_value = (
                TARGET_RUNTIME_BASES[str(row["target"])] + parent_offset_value
            )
        grouped: dict[str, list[int]] = defaultdict(list)
        for reference_binary, reference_offset in reference_refs:
            grouped[reference_binary].append(reference_offset)
        for reference_binary in sorted(grouped):
            references.append(
                Reference(
                    mapping_id=mapping_id,
                    target=str(row["target"]),
                    target_file_offset=int(row["target_offset"]),
                    target_runtime_address=(
                        TARGET_RUNTIME_BASES[str(row["target"])]
                        + int(row["target_offset"])
                    ),
                    resolution=(
                        "parent_message"
                        if parent_id_value is not None
                        else "direct"
                    ),
                    reference_binary=reference_binary,
                    reference_file_offsets=tuple(grouped[reference_binary]),
                    parent_mapping_id=parent_id_value,
                    parent_file_offset=parent_offset_value,
                    parent_runtime_address=parent_runtime_value,
                )
            )
    return tuple(references)


def validate_references(
    references: tuple[Reference, ...],
    mappings: Sequence[dict[str, object]],
    clean_targets: dict[str, bytes],
) -> dict[str, int]:
    text_by_id = {str(row["id"]): row for row in mappings}
    pointer_sites: set[tuple[str, int]] = set()
    for row in references:
        mapping = text_by_id[row.mapping_id]
        if mapping["target"] != row.target:
            raise ValueError(f"{row.mapping_id}: target differs from reference inventory")
        if int(mapping["target_offset"]) != row.target_file_offset:
            raise ValueError(
                f"{row.mapping_id}: target offset differs from reference inventory"
            )
        expected_runtime = TARGET_RUNTIME_BASES[row.target] + row.target_file_offset
        if expected_runtime != row.target_runtime_address:
            raise ValueError(f"{row.mapping_id}: target runtime address is inconsistent")
        expected_pointer = row.parent_runtime_address or row.target_runtime_address
        if row.resolution == "parent_message":
            assert row.parent_mapping_id is not None
            assert row.parent_file_offset is not None
            assert row.parent_runtime_address is not None
            parent = text_by_id.get(row.parent_mapping_id)
            if parent is None:
                raise ValueError(
                    f"{row.mapping_id}: missing parent {row.parent_mapping_id}"
                )
            if parent["target"] != row.target:
                raise ValueError(f"{row.mapping_id}: parent target differs")
            if int(parent["target_offset"]) != row.parent_file_offset:
                raise ValueError(f"{row.mapping_id}: parent offset differs")
            if (
                TARGET_RUNTIME_BASES[row.target] + row.parent_file_offset
                != row.parent_runtime_address
            ):
                raise ValueError(
                    f"{row.mapping_id}: parent runtime address is inconsistent"
                )
        clean = clean_targets[row.reference_binary]
        for offset in row.reference_file_offsets:
            if offset + 4 > len(clean):
                raise ValueError(
                    f"{row.mapping_id}: pointer offset is outside "
                    f"{TARGET_SPECS[row.reference_binary][0]}"
                )
            actual = int.from_bytes(clean[offset:offset + 4], "little")
            if actual != expected_pointer:
                raise ValueError(
                    f"{row.mapping_id}: pointer at 0x{offset:X} is 0x{actual:X}, "
                    f"expected 0x{expected_pointer:X}"
                )
            pointer_sites.add((row.reference_binary, offset))
    counts = Counter(row.resolution for row in references)
    return {
        "rows": len(references),
        "direct": counts["direct"],
        "parent_message": counts["parent_message"],
        "pointer_sites": sum(len(row.reference_file_offsets) for row in references),
        "redirect_edits": len(pointer_sites),
    }


def resolve_replacement_text(
    row: dict[str, object],
    label: str,
    donor_by_ref: dict[str, str] | None = None,
) -> str:
    override = str(row["replacement"])
    template = normalize_fullwidth_ascii(
        override if override else str(row["donor"])
    )
    prefix = normalize_fullwidth_ascii(str(row.get("prefix", "")))
    transform = str(row.get("transform", ""))
    arguments = dict(row.get("arguments", {}))

    def argument(name: str) -> str:
        value = arguments.get(name, "")
        if not value:
            raise ValueError(f"{label}: transform {transform!r} requires {name}")
        if donor_by_ref is None:
            raise ValueError(f"{label}: donor reference lookup is unavailable")
        parse_donor_ref(value, label)
        try:
            return donor_by_ref[value]
        except KeyError as exc:
            raise ValueError(
                f"{label}: donor reference {value!r} has no canonical donor text"
            ) from exc

    if transform == "":
        resolved = template
    elif transform == "empty":
        resolved = ""
    elif transform == "format_arg1":
        if "%1" not in template:
            raise ValueError(f"{label}: template has no %1")
        resolved = template.replace("%1", argument("arg1"))
    elif transform == "format_args":
        if "%1" not in template or "%2" not in template:
            raise ValueError(f"{label}: template lacks placeholders")
        resolved = (
            template.replace("%1", argument("arg1"))
            .replace("%2", argument("arg2"))
        )
    elif transform == "format_literal_arg1":
        if "%1" not in template:
            raise ValueError(f"{label}: template has no %1")
        resolved = template.replace(
            "%1",
            normalize_fullwidth_ascii(arguments.get("arg1", "")),
        )
    elif transform == "format_literal_prefix_arg2":
        if "%1" not in template or "%2" not in template:
            raise ValueError(f"{label}: template lacks placeholders")
        resolved = template.replace(
            "%1",
            normalize_fullwidth_ascii(arguments.get("arg1", "")),
        ).split("%2", 1)[0]
    elif transform == "format_prefix_arg2":
        if "%1" not in template or "%2" not in template:
            raise ValueError(f"{label}: template lacks placeholders")
        resolved = template.replace("%1", argument("arg1")).split("%2", 1)[0]
    elif transform in {"format_suffix_arg2", "after_placeholder2"}:
        if "%2" not in template:
            raise ValueError(f"{label}: template has no %2")
        resolved = template.split("%2", 1)[1]
    elif transform == "between_placeholders":
        if "%1" not in template or "%2" not in template:
            raise ValueError(f"{label}: template lacks placeholders")
        resolved = template.split("%1", 1)[1].split("%2", 1)[0]
    elif transform == "split_br":
        part = parse_int(arguments.get("part", ""), label)
        pieces = template.split("<br>")
        if part >= len(pieces):
            raise ValueError(f"{label}: split part {part} is outside {len(pieces)} parts")
        resolved = pieces[part]
    elif transform == "join_br_parts":
        parts = [
            parse_int(value, label)
            for value in arguments.get("parts", "").split(",")
            if value.strip()
        ]
        if not parts:
            raise ValueError(f"{label}: join_br_parts has no parts")
        pieces = template.split("<br>")
        if max(parts) >= len(pieces):
            raise ValueError(f"{label}: join part is outside {len(pieces)} parts")
        resolved = arguments.get("join", "<br>").join(pieces[index] for index in parts)
    elif transform == "insert_br_after_words":
        count = parse_int(arguments.get("words", ""), label)
        words = template.split(" ")
        if any(not word for word in words):
            raise ValueError(
                f"{label}: donor text does not use single-space word boundaries"
            )
        if count <= 0 or count >= len(words):
            raise ValueError(
                f"{label}: word break {count} is outside 1..{len(words) - 1}"
            )
        resolved = " ".join(words[:count]) + "<br>" + " ".join(words[count:])
    elif transform == "append_space":
        resolved = template + " "
    elif transform == "flatten_br_slice":
        flattened = template.replace("<br>", " ")
        start = parse_int(arguments.get("start", ""), label)
        end = parse_int(arguments.get("end", ""), label)
        if start > end or end > len(flattened):
            raise ValueError(
                f"{label}: slice {start}:{end} is outside flattened text length "
                f"{len(flattened)}"
            )
        resolved = flattened[start:end]
    else:
        raise ValueError(f"{label}: unsupported transform {transform!r}")
    return normalize_fullwidth_ascii(prefix + resolved)


def read_target_sequence(data: bytes, offset: int, capacity: int, label: str) -> tuple[list[str], bytes]:
    if capacity <= 0 or offset < 0 or offset + capacity > len(data):
        raise ValueError(f"{label}: invalid target range 0x{offset:X}+{capacity}")
    region = data[offset:offset + capacity]
    fragments: list[str] = []
    cursor = 0
    while cursor < len(region):
        if all(value == 0 for value in region[cursor:]):
            break
        end = region.find(b"\x00", cursor)
        if end < 0:
            raise ValueError(f"{label}: target sequence has no terminating NUL")
        raw = region[cursor:end]
        if not raw:
            raise ValueError(f"{label}: target sequence contains an empty fragment before its zero-padded tail")
        try:
            fragments.append(raw.decode("cp932"))
        except UnicodeDecodeError:
            fragments.append("")
        cursor = end + 1
    if not fragments:
        raise ValueError(f"{label}: target sequence is empty")
    return fragments, region[:cursor]


def write_sequence(output: bytearray, offset: int, capacity: int, fragments: list[bytes]) -> None:
    payload = b"".join(fragment + b"\x00" for fragment in fragments) + b"\x00"
    if len(payload) > capacity:
        raise ValueError(f"replacement sequence is {len(payload)} bytes but block allows {capacity}")
    output[offset:offset + capacity] = payload + b"\x00" * (capacity - len(payload))


def read_target_slot(data: bytes, offset: int, capacity: int, label: str) -> tuple[str, bytes]:
    if capacity <= 0 or offset < 0 or offset + capacity > len(data):
        raise ValueError(f"{label}: invalid target range 0x{offset:X}+{capacity}")
    slot = data[offset:offset + capacity]
    end = slot.find(b"\x00")
    if end < 0:
        raise ValueError(f"{label}: target slot has no NUL terminator")
    raw = slot[:end]
    padding = slot[end + 1:]
    first_structural = next((index for index, value in enumerate(padding, end + 1) if value != 0), None)
    if first_structural is not None:
        raise ValueError(
            f"{label}: declared slot crosses nonzero data at 0x{offset + first_structural:X}; "
            "reduce capacity to the actual zero-padded string boundary"
        )
    try:
        text = raw.decode("cp932")
    except UnicodeDecodeError:
        text = ""
    return text, raw


def adapt_source_markup(source_text: str, target_text: str, label: str) -> str:
    adapted = source_text
    for source_tag, candidates in NAMED_COLOR_TAG_EQUIVALENTS.items():
        if source_tag not in adapted:
            continue
        replacement = next((candidate for candidate in candidates if candidate in target_text), None)
        if replacement is None:
            raise ValueError(f"{label}: cannot verify an NA2 equivalent for {source_tag}")
        adapted = adapted.replace(source_tag, replacement)
    return adapted


def validate_declared_source(
    declared_text: str,
    actual_text: str,
    label: str,
) -> None:
    if declared_text != actual_text:
        raise ValueError(
            f"{label}: declared source text {declared_text!r} does not match "
            f"clean target text {actual_text!r}"
        )


def write_slot(output: bytearray, offset: int, capacity: int, replacement: bytes) -> None:
    if len(replacement) > capacity - 1:
        raise ValueError(f"replacement is {len(replacement)} bytes but slot allows {capacity - 1}")
    output[offset:offset + capacity] = replacement + b"\x00" + b"\x00" * (capacity - len(replacement) - 1)


def parse_mappings(rows: list[dict[str, str]]) -> dict[str, list[dict[str, object]]]:
    result = {"text": [], "inactive": []}
    for line, row in enumerate(rows, 2):
        label = f"mappings.tsv line {line} ({row['id']})"
        if row["enabled"] not in {"0", "1"}:
            raise ValueError(f"{label}: enabled must be 0 or 1")
        if not row["display_context"]:
            raise ValueError(f"{label}: display_context is required")
        if not row["display_basis"].startswith(DISPLAY_BASIS_PREFIXES):
            raise ValueError(
                f"{label}: display_basis must begin with "
                + ", ".join(DISPLAY_BASIS_PREFIXES)
            )
        mode = row["mode"].lower()
        if mode not in VALID_MODES:
            raise ValueError(f"{label}: unsupported mode {mode!r}")
        target, target_offset = parse_source_ref(row["source_ref"], label)
        transform = row["transform"].lower()
        if transform not in VALID_TRANSFORMS:
            raise ValueError(f"{label}: unsupported transform {transform!r}")
        arguments = parse_arguments(row["arguments"], label)
        if transform == "":
            if arguments:
                raise ValueError(f"{label}: arguments require a transform")
        elif transform == "split_br":
            if set(arguments) != {"part"}:
                raise ValueError(f"{label}: split_br requires only part=<index>")
            parse_int(arguments["part"], label)
        elif transform == "split_br_sequence":
            if set(arguments) != {"parts"}:
                raise ValueError(
                    f"{label}: split_br_sequence requires only parts=<indexes>"
                )
            parts = [
                parse_int(value, label)
                for value in arguments["parts"].split(",")
                if value.strip()
            ]
            if not parts:
                raise ValueError(f"{label}: split_br_sequence has no parts")
        elif transform == "empty":
            if arguments:
                raise ValueError(f"{label}: empty does not accept arguments")
        elif transform in {
            "format_literal_arg1",
            "format_literal_prefix_arg2",
        }:
            if set(arguments) != {"arg1"} or not arguments["arg1"]:
                raise ValueError(
                    f"{label}: {transform} requires only nonempty arg1=<text>"
                )
        elif transform in {"format_arg1", "format_prefix_arg2"}:
            if set(arguments) != {"arg1"}:
                raise ValueError(f"{label}: {transform} requires only arg1=<ref>")
            parse_donor_ref(arguments["arg1"], label)
        elif transform == "format_args":
            if set(arguments) != {"arg1", "arg2"}:
                raise ValueError(
                    f"{label}: format_args requires arg1=<ref>;arg2=<ref>"
                )
            parse_donor_ref(arguments["arg1"], label)
            parse_donor_ref(arguments["arg2"], label)
        elif transform in {
            "format_suffix_arg2",
            "between_placeholders",
            "after_placeholder2",
            "append_space",
        }:
            if arguments:
                raise ValueError(f"{label}: {transform} does not accept arguments")
        elif transform == "join_br_parts":
            if not set(arguments).issubset({"parts", "join"}) or "parts" not in arguments:
                raise ValueError(
                    f"{label}: join_br_parts requires parts=<indexes> and optional join"
                )
            for value in arguments["parts"].split(","):
                if value.strip():
                    parse_int(value, label)
        elif transform == "insert_br_after_words":
            if set(arguments) != {"words"}:
                raise ValueError(
                    f"{label}: insert_br_after_words requires only words=<count>"
                )
            parse_int(arguments["words"], label)
        elif transform == "flatten_br_slice":
            if set(arguments) != {"start", "end"}:
                raise ValueError(
                    f"{label}: flatten_br_slice requires start=<index>;end=<index>"
                )
            parse_int(arguments["start"], label)
            parse_int(arguments["end"], label)
        if mode == "sequence" and transform not in {"", "split_br_sequence"}:
            raise ValueError(
                f"{label}: sequence mappings require blank or split_br_sequence transform"
            )
        donor_ref = row["donor_ref"]
        if donor_ref:
            parse_donor_ref(donor_ref, label)
        reference_refs = parse_reference_refs(row["reference_refs"], label)
        parsed = {
            "id": row["id"],
            "display_context": row["display_context"],
            "display_basis": row["display_basis"],
            "mode": mode,
            "target": target,
            "target_offset": target_offset,
            "source_ref": row["source_ref"],
            "capacity": parse_int(row["capacity"], label),
            "source": row["source"],
            "donor_ref": donor_ref,
            "donor": row["donor"],
            "prefix": row["prefix"],
            "replacement": row["replacement"],
            "transform": transform,
            "arguments": arguments,
            "reference_refs": reference_refs,
            "parent_mapping_id": row["parent_mapping_id"],
        }
        result["inactive" if row["enabled"] == "0" else "text"].append(parsed)
    return result


def validate_semantic_replacement(source_text: str, target_text: str, label: str) -> None:
    """Reject donor sentinels that would overwrite identifier-like NA2 data."""
    if (
        IDENTIFIER_TEXT.fullmatch(target_text)
        and source_text.strip().casefold() in PLACEHOLDER_TEXT
    ):
        raise ValueError(
            f"{label}: refuses placeholder donor text {source_text!r} for "
            f"identifier-like target {target_text!r}"
        )


def resolve_text_materializations(
    mappings: Sequence[dict[str, object]],
    selected: set[str],
    donor_catalog: Sequence[dict[str, object]] | None = None,
) -> tuple[
    dict[str, str],
    dict[str, tuple[str, ...]],
    dict[str, str],
    dict[str, str],
    dict[str, str],
]:
    """Resolve canonical replacement templates for downstream consumers."""
    donor_by_ref: dict[str, str] = {}
    for row in donor_catalog if donor_catalog is not None else mappings:
        donor_ref = str(row["donor_ref"])
        donor = str(row["donor"])
        if not donor_ref:
            continue
        prior = donor_by_ref.setdefault(donor_ref, donor)
        if prior != donor:
            raise ValueError(
                f"{row['id']}: donor reference {donor_ref!r} has conflicting text"
            )
    source_texts: dict[str, str] = {}
    donor_texts: dict[str, str] = {}
    resolved_texts: dict[str, str] = {}
    resolved_sequences: dict[str, tuple[str, ...]] = {}
    materialized_templates: dict[str, str] = {}
    for row in mappings:
        if str(row["target"]) not in selected:
            continue
        mapping_id = str(row["id"])
        override = str(row["replacement"])
        template = normalize_fullwidth_ascii(
            override if override else str(row["donor"])
        )
        prefix = normalize_fullwidth_ascii(str(row["prefix"]))
        materialized = prefix + template
        source_texts[mapping_id] = str(row["source"])
        donor_texts[mapping_id] = str(row["donor"])
        materialized_templates[mapping_id] = materialized
        if row["mode"] == "sequence":
            if row["transform"] == "split_br_sequence":
                arguments = dict(row["arguments"])
                parts = [
                    parse_int(value, mapping_id)
                    for value in arguments["parts"].split(",")
                    if value.strip()
                ]
                pieces = template.split("<br>")
                if max(parts) >= len(pieces):
                    raise ValueError(
                        f"{mapping_id}: sequence part is outside {len(pieces)} parts"
                    )
                sequence = tuple(pieces[index] for index in parts)
                if sequence:
                    sequence = (prefix + sequence[0], *sequence[1:])
            else:
                sequence = tuple(materialized.split("<NUL>"))
            if not sequence or any(not value for value in sequence):
                raise ValueError(f"{mapping_id}: sequence contains an empty fragment")
            resolved_sequences[mapping_id] = sequence
        else:
            resolved = resolve_replacement_text(row, mapping_id, donor_by_ref)
            resolved_texts[mapping_id] = resolved
    return (
        resolved_texts,
        resolved_sequences,
        source_texts,
        donor_texts,
        materialized_templates,
    )


def apply_text_mappings(
    mappings,
    selected,
    clean_targets,
    output_targets,
    resolved_texts,
    resolved_sequences,
    excluded_mapping_ids: frozenset[str] = frozenset(),
    display_mode: str = "translation",
):
    annotations = []
    occupied: dict[str, list[tuple[int, int, str]]] = defaultdict(list)
    stats = Counter()
    display_contexts = Counter()
    for row in mappings:
        target = str(row["target"])
        mapping_id = str(row["id"])
        if target not in selected or mapping_id in excluded_mapping_ids:
            continue
        offset = int(row["target_offset"])
        capacity = int(row["capacity"])
        label = f"{row['id']} {target} 0x{offset:X}"
        for start, end, prior in occupied[target]:
            if offset < end and start < offset + capacity:
                raise ValueError(f"{label}: overlaps {prior} at 0x{start:X}-0x{end:X}")
        if row["mode"] == "sequence":
            target_fragments, _ = read_target_sequence(clean_targets[target], offset, capacity, label)
            official_fragments = resolved_sequences[mapping_id]
            target_context = "<NUL>".join(target_fragments)
            validate_declared_source(str(row["source"]), target_context, label)
            replacement_fragments = [
                adapt_source_markup(fragment, target_context, label) for fragment in official_fragments
            ]
            write_sequence(
                output_targets[target],
                offset,
                capacity,
                [fragment.encode("cp1252") for fragment in replacement_fragments],
            )
            target_text = target_context
            replacement_text = "<NUL>".join(replacement_fragments)
        else:
            official = resolved_texts[mapping_id]
            target_text, _ = read_target_slot(clean_targets[target], offset, capacity, label)
            validate_declared_source(str(row["source"]), target_text, label)
            validate_semantic_replacement(official, target_text, label)
            replacement_text = adapt_source_markup(official, target_text, label)
            replacement = replacement_text.encode("cp1252")
            write_slot(output_targets[target], offset, capacity, replacement)
        occupied[target].append((offset, offset + capacity, str(row["id"])))
        if display_mode == "mapping_ids":
            mapping_kind = "diagnostic mapping identifier"
        else:
            mapping_kind = (
                "override"
                if str(row["replacement"])
                else "official donor translation"
            )
            if str(row["prefix"]):
                mapping_kind = f"prefixed {mapping_kind}"
        annotations.append({"path": TARGET_SPECS[target][0], "start": offset, "end": offset + capacity,
                            "source_text": target_text, "replacement_text": replacement_text,
                            "mapping_id": str(row["id"]),
                            "reason": f"Apply {mapping_kind} for {row['id']}."})
        stats["mapped"] += 1
        if clean_targets[target][offset:offset + capacity] != bytes(output_targets[target][offset:offset + capacity]):
            stats["changed"] += 1
        display_contexts[str(row["display_context"])] += 1
    return annotations, dict(stats), dict(sorted(display_contexts.items()))


def diff_rows(path: str, clean: bytes, output: bytes, annotations) -> list[dict[str, str]]:
    if len(clean) != len(output):
        raise ValueError(f"Cannot emit fixed-offset patches for size-changed file: {path}")
    normalized = normalize_path(path)
    relevant = [item for item in annotations if normalize_path(str(item["path"])) == normalized]
    ranges = []
    start = None
    for index, (before, after) in enumerate(zip(clean, output)):
        if before != after and start is None:
            start = index
        elif before == after and start is not None:
            ranges.append((start, index)); start = None
    if start is not None:
        ranges.append((start, len(clean)))
    rows = []
    for range_start, range_end in ranges:
        boundaries = {range_start, range_end}
        for annotation in relevant:
            a, b = int(annotation["start"]), int(annotation["end"])
            if range_start < b and a < range_end:
                boundaries.add(max(range_start, a)); boundaries.add(min(range_end, b))
        ordered = sorted(boundaries)
        for a, b in zip(ordered, ordered[1:]):
            if a >= b:
                continue
            matching = [item for item in relevant if a < int(item["end"]) and int(item["start"]) < b]
            annotation = matching[-1] if matching else None
            rows.append({
                "path": path,
                "offset": f"0x{a:X}",
                "expected_hex": clean[a:b].hex().upper(),
                "replacement_hex": output[a:b].hex().upper(),
                "source_text": str(annotation["source_text"]) if annotation else "",
                "replacement_text": str(annotation["replacement_text"]) if annotation else "",
                "source_mapping_id": str(annotation["mapping_id"]) if annotation else "",
                "reason": str(annotation["reason"]) if annotation else "Imported translation string.",
            })
    return rows


def write_import_tsv(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        raise ValueError("No translation imports were generated")
    fields = [
        "import_id", "group_id", "path", "offset", "expected_hex",
        "replacement_hex", "source_text", "replacement_text",
        "source_mapping_id", "reason",
    ]
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
            writer.writeheader(); writer.writerows(rows); handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_translation_import_plan(
    *,
    na2_iso: Optional[Path] = None,
    na2_folder: Optional[Path] = None,
    data_root: Path,
    apply: str = "BTL,ETC,SLPS",
) -> TranslationImportPlan:
    """Load canonical translation declarations without choosing placement."""
    selected_list = parse_apply(apply)
    selected = set(selected_list)
    na2 = source_from(na2_folder, na2_iso, "NA2")
    clean_targets = {
        target: na2.read(TARGET_SPECS[target][1], f"NA2 {TARGET_SPECS[target][0]}")
        for target in selected_list
    }
    actual_hashes = {
        f"NA2_{target}": sha1(data) for target, data in clean_targets.items()
    }
    for key, expected in EXPECTED_SHA1.items():
        actual = actual_hashes.get(key)
        if actual is not None and actual != expected:
            raise ValueError(f"Unexpected {key} SHA-1: {actual}; expected {expected}")

    data_root = data_root.resolve()
    mapping_path = data_root / "mappings.tsv"
    actual_mapping_hash = hashlib.sha256(mapping_path.read_bytes()).hexdigest().upper()
    rows_raw = read_rows(mapping_path)
    mappings = parse_mappings(rows_raw)
    references = tuple(
        reference
        for reference in references_from_mappings(mappings["text"])
        if reference.target in selected
    )
    reference_counts = validate_references(
        references, mappings["text"], clean_targets
    )
    (
        resolved_texts,
        resolved_sequences,
        source_texts,
        donor_texts,
        materialized_templates,
    ) = resolve_text_materializations(
        mappings["text"],
        selected,
        donor_catalog=tuple(mappings["text"]) + tuple(mappings["inactive"]),
    )
    import_targets: dict[str, dict[str, object]] = {}
    for target in selected_list:
        path = TARGET_SPECS[target][0]
        import_targets[path] = {
            "root_id": "na2",
            "path": path,
            "expected_size": len(clean_targets[target]),
            "expected_sha256": hashlib.sha256(clean_targets[target]).hexdigest().upper(),
        }

    active_by_mode = Counter(
        row["mode"] for row in mappings["text"] if row["target"] in selected
    )
    active_display_contexts = Counter(
        str(row["display_context"])
        for row in mappings["text"]
        if row["target"] in selected
    )
    active_display_bases = Counter(
        str(row["display_basis"])
        for row in mappings["text"]
        if row["target"] in selected
    )
    summary: dict[str, object] = {
        "mode": "canonical translation declarations",
        "mappings_sha256": actual_mapping_hash,
        "targets": selected_list,
        "output": {
            "import_rows": 0,
            "text_mappings_applied": 0,
            "text_mappings_changed": 0,
        },
        "active_mapping_coverage": {
            "by_mode": dict(sorted(active_by_mode.items())),
            "by_display_context": dict(sorted(active_display_contexts.items())),
            "by_display_basis": dict(sorted(active_display_bases.items())),
        },
        "source_hashes": actual_hashes,
        "reference_inventory": reference_counts,
    }
    return TranslationImportPlan(
        import_rows=[],
        targets=import_targets,
        text_mappings=tuple(mappings["text"]),
        references=references,
        resolved_texts=resolved_texts,
        resolved_sequences=resolved_sequences,
        source_texts=source_texts,
        donor_texts=donor_texts,
        materialized_templates=materialized_templates,
        clean_targets=clean_targets,
        summary=summary,
    )


def compile_inline_imports(
    plan: TranslationImportPlan,
    *,
    excluded_mapping_ids: frozenset[str] = frozenset(),
) -> TranslationImportPlan:
    """Compile every selected mapping not assigned to external storage."""
    selected_list = [
        target for target in TARGET_SPECS if target in plan.clean_targets
    ]
    selected = set(selected_list)
    unknown = excluded_mapping_ids - {
        str(row["id"]) for row in plan.text_mappings
    }
    if unknown:
        raise ValueError(
            "unknown externally placed mapping ids: " + ", ".join(sorted(unknown))
        )
    output_targets = {
        target: bytearray(plan.clean_targets[target]) for target in selected_list
    }
    annotations, text_stats, text_contexts = apply_text_mappings(
        plan.text_mappings,
        selected,
        plan.clean_targets,
        output_targets,
        plan.resolved_texts,
        plan.resolved_sequences,
        excluded_mapping_ids,
        plan.display_mode,
    )
    import_rows: list[dict[str, str]] = []
    translated_hashes: dict[str, dict[str, object]] = {}
    for target in selected_list:
        path = TARGET_SPECS[target][0]
        output = bytes(output_targets[target])
        rows = diff_rows(
            path, plan.clean_targets[target], output, annotations
        )
        for row in rows:
            row["import_id"] = f"{target}-I{len(import_rows) + 1:04d}"
            row["group_id"] = target
            import_rows.append(row)
        translated_hashes[path] = {
            "source_sha1": sha1(plan.clean_targets[target]),
            "translated_sha1": sha1(output),
            "size": len(output),
        }
    summary = dict(plan.summary)
    summary["output"] = {
        "import_rows": len(import_rows),
        "text_mappings_applied": text_stats.get("mapped", 0),
        "text_mappings_changed": text_stats.get("changed", 0),
        "external_mappings_omitted": len(excluded_mapping_ids),
    }
    coverage = dict(summary["active_mapping_coverage"])
    coverage["inline_by_display_context"] = text_contexts
    summary["active_mapping_coverage"] = coverage
    summary["translated_file_hashes"] = translated_hashes
    return replace(plan, import_rows=import_rows, summary=summary)
