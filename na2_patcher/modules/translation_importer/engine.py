#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Sequence

SECTOR = 2048

TARGET_SPECS = {
    "BTL": ("PRG/BTL.BIN", ["PRG/BTL.BIN", "BTL.BIN"]),
    "ETC": ("PRG/ETC.BIN", ["PRG/ETC.BIN", "ETC.BIN"]),
    "SLPS": ("SLPS_258.37", ["SLPS_258.37"]),
}
SOURCE_SPECS = {
    "NUN5_BTL": ["PRG/BTL.BIN", "BTL.BIN"],
    "NUN5_ETC": ["PRG/ETC.BIN", "ETC.BIN"],
    "NUN5_TEXTENG": ["PRG/TEXTENG.BIN", "TEXTENG.BIN"],
    "NUN5_SLES": ["SLES_556.05"],
}
MAPPING_FIELDS = [
    "id", "enabled", "section", "mode", "target", "target_offset", "capacity",
    "source_ref", "transform", "arguments", "value", "reason",
]
REFERENCE_FIELDS = [
    "mapping_id",
    "target",
    "target_file_offset",
    "target_runtime_address",
    "resolution",
    "reference_binary",
    "reference_file_offsets",
    "parent_mapping_id",
    "parent_file_offset",
    "parent_runtime_address",
]
METADATA_FIELDS = ["key", "value"]
EXPECTED_SHA1 = {
    "NA2_BTL": "bf7fc7331a2a4f34fc90b84b45772ae1f6bcab03",
    "NA2_ETC": "dcfffd7eb14e484a4c0fbc195599a0b45a9a11c1",
    "NA2_SLPS": "bbe206bbf4da0ee815b437226ceb6a533c95833e",
    "NUN5_BTL": "874b9d64ddec7f9f742a08831505155001adb863",
    "NUN5_ETC": "1c9b05bc501cac21b7da17c5fc6c99dd3869f3be",
    "NUN5_TEXTENG": "77fafba95157e44ccd61783a04aba87c4b98b1fb",
    "NUN5_SLES": "fe54357b016bc579b435a593e330d2d0ff822cdf",
}
VALID_MODES = {"slot", "sequence", "shorten", "bytes"}
PLACEHOLDER_TEXT = frozenset({"unknown", "placeholder", "dummy", "test", "todo", "temp"})
IDENTIFIER_TEXT = re.compile(r"[a-z][a-z0-9_./-]{3,}\Z")
VALID_TRANSFORMS = {
    "", "empty", "format_arg1", "format_args", "format_prefix_arg2",
    "format_suffix_arg2", "between_placeholders", "after_placeholder2",
    "split_br", "split_br_sequence", "join_br_parts", "insert_br_after_words",
    "append_space", "flatten_br_slice", "uppercase",
}
TARGET_RUNTIME_BASES = {
    "SLPS": 0x000FFF00,
    "BTL": 0x006B3F00,
    "ETC": 0x006B3F00,
}
VALID_REFERENCE_RESOLUTIONS = frozenset({"direct", "parent_message"})
NAMED_COLOR_TAG_EQUIVALENTS = {
    "<WHITE>": ("<WHITE>", "<colorFFFFFF>"),
    "<BLACK>": ("<BLACK>", "<color000000>"),
    "<RED>": ("<RED>",),
}


@dataclass(frozen=True)
class IsoRecord:
    path: str
    extent: int
    size: int
    flags: int

    @property
    def is_dir(self) -> bool:
        return bool(self.flags & 2)


@dataclass(frozen=True)
class TranslationImportPlan:
    mapping_version: int
    packaged_mappings_sha256: str
    import_rows: list[dict[str, str]]
    targets: dict[str, dict[str, object]]
    text_mappings: tuple[dict[str, object], ...]
    references: tuple["Reference", ...]
    resolved_texts: dict[str, str]
    resolved_sequences: dict[str, tuple[str, ...]]
    source_templates: dict[str, str]
    materialized_templates: dict[str, str]
    clean_targets: dict[str, bytes]
    official_sources: dict[str, bytes]
    summary: dict[str, object]


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


@dataclass(frozen=True)
class GameTitlePolicy:
    donor_title: str
    output_title: str
    target: str
    expected_mapping_count: int
    expected_occurrence_count: int


class Iso9660:
    def __init__(self, path: Path) -> None:
        self.path = path.resolve()
        self.data = self.path.read_bytes()
        self.records: Dict[str, IsoRecord] = {}
        self._parse()

    @staticmethod
    def _decode_name(raw: bytes) -> str:
        if raw in (b"\x00", b"\x01"):
            return ""
        return raw.decode("ascii", "replace").split(";", 1)[0].upper()

    @staticmethod
    def _record(buf: bytes, offset: int):
        if offset >= len(buf) or buf[offset] == 0:
            return None, 0
        length = buf[offset]
        record = buf[offset:offset + length]
        if len(record) < 34:
            raise ValueError(f"Invalid ISO directory record at 0x{offset:X}")
        extent = int.from_bytes(record[2:6], "little")
        size = int.from_bytes(record[10:14], "little")
        flags = record[25]
        name_length = record[32]
        return (extent, size, flags, record[33:33 + name_length]), length

    def _walk(self, record: IsoRecord, prefix: str) -> None:
        directory = self.data[record.extent * SECTOR:record.extent * SECTOR + record.size]
        offset = 0
        while offset < len(directory):
            if directory[offset] == 0:
                offset = ((offset // SECTOR) + 1) * SECTOR
                continue
            parsed, used = self._record(directory, offset)
            if parsed is None:
                break
            offset += used
            extent, size, flags, raw_name = parsed
            name = self._decode_name(raw_name)
            if not name:
                continue
            path = f"{prefix}/{name}" if prefix else name
            child = IsoRecord(path, extent, size, flags)
            self.records[path] = child
            if child.is_dir:
                self._walk(child, path)

    def _parse(self) -> None:
        pvd = None
        for sector in range(16, min(128, len(self.data) // SECTOR)):
            offset = sector * SECTOR
            if self.data[offset] == 1 and self.data[offset + 1:offset + 6] == b"CD001":
                pvd = self.data[offset:offset + SECTOR]
                break
        if pvd is None:
            raise ValueError(f"No ISO9660 primary volume descriptor: {self.path}")
        parsed, _ = self._record(pvd, 156)
        if parsed is None:
            raise ValueError("Invalid ISO root record")
        extent, size, flags, _ = parsed
        self._walk(IsoRecord("", extent, size, flags), "")

    def read(self, candidates: Sequence[str], label: str) -> bytes:
        normalized = [normalize_path(value) for value in candidates]
        for candidate in normalized:
            record = self.records.get(candidate)
            if record and not record.is_dir:
                return self.data[record.extent * SECTOR:record.extent * SECTOR + record.size]
        basenames = {value.rsplit("/", 1)[-1] for value in normalized}
        matches = [record for path, record in self.records.items()
                   if not record.is_dir and path.rsplit("/", 1)[-1] in basenames]
        if len(matches) == 1:
            record = matches[0]
            return self.data[record.extent * SECTOR:record.extent * SECTOR + record.size]
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


def source_from(folder: Optional[Path], iso: Optional[Path], label: str):
    if folder is not None and folder.is_dir():
        return FolderSource(folder)
    if iso is not None and iso.is_file():
        return Iso9660(iso)
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


def parse_hex(value: str, label: str) -> bytes:
    text = value.strip().replace(" ", "")
    if not text or len(text) % 2:
        raise ValueError(f"{label}: invalid hexadecimal byte sequence")
    try:
        return bytes.fromhex(text)
    except ValueError as exc:
        raise ValueError(f"{label}: invalid hexadecimal byte sequence") from exc


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


def parse_source_ref(value: str, label: str) -> tuple[str, int]:
    match = re.fullmatch(r"([A-Za-z0-9_]+)@(0[xX][0-9A-Fa-f]+|[0-9]+)", value.strip())
    if not match:
        raise ValueError(f"{label}: malformed source reference {value!r}")
    source = match.group(1).upper()
    if source not in SOURCE_SPECS:
        raise ValueError(f"{label}: unsupported source {source!r}")
    return source, int(match.group(2), 0)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != MAPPING_FIELDS:
            raise ValueError("mappings.tsv must contain exactly these columns in this order: " + "\t".join(MAPPING_FIELDS))
        rows = [{key: (value or "").strip() for key, value in raw.items()} for raw in reader]
    ids = [row["id"] for row in rows]
    if any(not value for value in ids) or len(ids) != len(set(ids)):
        raise ValueError("mappings.tsv contains empty or duplicate ids")
    return rows


def read_references(path: Path) -> tuple[Reference, ...]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != REFERENCE_FIELDS:
            raise ValueError(
                f"{path}: expected columns " + "\t".join(REFERENCE_FIELDS)
            )
        rows = [
            {key: (value or "").strip() for key, value in row.items()}
            for row in reader
            if any((value or "").strip() for value in row.values())
        ]
    references: list[Reference] = []
    seen: set[str] = set()
    for line, row in enumerate(rows, 2):
        mapping_id = row["mapping_id"]
        label = f"{path.name} line {line} ({mapping_id})"
        if not mapping_id or mapping_id in seen:
            raise ValueError(f"{label}: duplicate or empty mapping_id")
        seen.add(mapping_id)
        target = row["target"].upper()
        reference_binary = row["reference_binary"].upper()
        if target not in TARGET_SPECS or reference_binary not in TARGET_SPECS:
            raise ValueError(f"{label}: unsupported target/reference binary")
        resolution = row["resolution"]
        if resolution not in VALID_REFERENCE_RESOLUTIONS:
            raise ValueError(f"{label}: unsupported resolution {resolution!r}")
        reference_offsets = tuple(
            parse_int(value.strip(), label)
            for value in row["reference_file_offsets"].split(",")
            if value.strip()
        )
        if not reference_offsets or len(set(reference_offsets)) != len(reference_offsets):
            raise ValueError(f"{label}: empty or duplicate reference offsets")
        parent_id = row["parent_mapping_id"]
        parent_offset = row["parent_file_offset"]
        parent_runtime = row["parent_runtime_address"]
        if resolution == "direct":
            if (parent_id, parent_offset, parent_runtime) != ("-", "-", "-"):
                raise ValueError(f"{label}: direct rows must not declare a parent")
            parent_id_value = None
            parent_offset_value = None
            parent_runtime_value = None
        else:
            if not parent_id or "-" in (parent_id, parent_offset, parent_runtime):
                raise ValueError(f"{label}: parent_message row requires a complete parent")
            parent_id_value = parent_id
            parent_offset_value = parse_int(parent_offset, label)
            parent_runtime_value = parse_int(parent_runtime, label)
        references.append(
            Reference(
                mapping_id=mapping_id,
                target=target,
                target_file_offset=parse_int(row["target_file_offset"], label),
                target_runtime_address=parse_int(row["target_runtime_address"], label),
                resolution=resolution,
                reference_binary=reference_binary,
                reference_file_offsets=reference_offsets,
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
    shortening_ids = {
        mapping_id
        for mapping_id, row in text_by_id.items()
        if row["mode"] == "shorten"
    }
    reference_ids = {row.mapping_id for row in references}
    if reference_ids != shortening_ids:
        raise ValueError(
            "reference coverage differs from enabled shortening mappings: "
            f"missing={sorted(shortening_ids - reference_ids)}, "
            f"extra={sorted(reference_ids - shortening_ids)}"
        )
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


def read_mapping_metadata(data_root: Path) -> tuple[int, str, GameTitlePolicy]:
    """Read canonical mapping metadata from the feature-owned config."""
    config_path = data_root / "config.tsv"
    with config_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != METADATA_FIELDS:
            raise ValueError(
                "translation importer config.tsv must contain exactly: "
                + "\t".join(METADATA_FIELDS)
            )
        rows = [
            {key: (value or "").strip() for key, value in row.items()}
            for row in reader
            if any((value or "").strip() for value in row.values())
        ]
    metadata = {row["key"]: row["value"] for row in rows}
    if len(metadata) != len(rows):
        raise ValueError("translation importer config.tsv contains duplicate keys")
    expected_keys = {
        "schema_version",
        "mapping_version",
        "mappings_sha256",
        "donor_game_title",
        "output_game_title",
        "game_title_target",
        "game_title_mapping_count",
        "game_title_occurrence_count",
    }
    if set(metadata) != expected_keys:
        raise ValueError(
            "translation importer config.tsv keys must be exactly: "
            + ", ".join(sorted(expected_keys))
        )
    if metadata["schema_version"] != "1":
        raise ValueError("Unsupported translation importer schema_version")
    version = parse_int(metadata["mapping_version"], "mapping_version")
    if version <= 0:
        raise ValueError("translation importer mapping_version must be positive")
    packaged_hash = metadata["mappings_sha256"].lower()
    if not re.fullmatch(r"[0-9a-f]{64}", packaged_hash):
        raise ValueError("translation importer mappings_sha256 must be SHA-256")
    donor_title = metadata["donor_game_title"]
    output_title = metadata["output_game_title"]
    title_target = metadata["game_title_target"]
    if not donor_title or not output_title or donor_title == output_title:
        raise ValueError("translation importer game-title policy must replace distinct text")
    if "\0" in donor_title or "\0" in output_title:
        raise ValueError("translation importer game-title policy contains an embedded NUL")
    try:
        donor_title.encode("cp1252")
        output_title.encode("cp1252")
    except UnicodeEncodeError as exc:
        raise ValueError("translation importer game-title policy must be CP1252") from exc
    if title_target not in TARGET_SPECS:
        raise ValueError("translation importer game-title policy has invalid target")
    mapping_count = parse_int(
        metadata["game_title_mapping_count"], "game_title_mapping_count"
    )
    occurrence_count = parse_int(
        metadata["game_title_occurrence_count"], "game_title_occurrence_count"
    )
    if mapping_count <= 0 or occurrence_count < mapping_count:
        raise ValueError("translation importer game-title policy has invalid counts")
    return version, packaged_hash, GameTitlePolicy(
        donor_title=donor_title,
        output_title=output_title,
        target=title_target,
        expected_mapping_count=mapping_count,
        expected_occurrence_count=occurrence_count,
    )


def read_official_z(data: bytes, offset: int, label: str) -> str:
    if offset < 0 or offset >= len(data):
        raise ValueError(f"{label}: source offset 0x{offset:X} is outside the file")
    end = data.find(b"\x00", offset)
    if end < 0:
        raise ValueError(f"{label}: unterminated source string at 0x{offset:X}")
    raw = data[offset:end]
    if not raw:
        raise ValueError(f"{label}: empty source string at 0x{offset:X}")
    text = raw.decode("cp1252")
    if any(ord(char) < 0x20 and char not in "\t\r\n" for char in text):
        raise ValueError(f"{label}: source string contains unsupported control bytes")
    return text


def resolve_source_text(row: dict[str, object], sources: dict[str, bytes], label: str) -> str:
    source = str(row["source"])
    offset = int(row["source_offset"])
    template = read_official_z(sources[source], offset, label)
    transform = str(row.get("transform", ""))
    arguments = dict(row.get("arguments", {}))

    def arg(name: str) -> str:
        if name not in arguments:
            raise ValueError(f"{label}: transform {transform!r} requires {name}")
        src, off = parse_source_ref(arguments[name], label)
        return read_official_z(sources[src], off, f"{label} {name}")

    if transform == "":
        return template
    if transform == "empty":
        return ""
    if transform == "format_arg1":
        if "%1" not in template:
            raise ValueError(f"{label}: template has no %1")
        return template.replace("%1", arg("arg1"))
    if transform == "format_args":
        if "%1" not in template or "%2" not in template:
            raise ValueError(f"{label}: template lacks placeholders")
        return template.replace("%1", arg("arg1")).replace("%2", arg("arg2"))
    if transform == "format_prefix_arg2":
        if "%1" not in template or "%2" not in template:
            raise ValueError(f"{label}: template lacks placeholders")
        return template.replace("%1", arg("arg1")).split("%2", 1)[0]
    if transform in {"format_suffix_arg2", "after_placeholder2"}:
        if "%2" not in template:
            raise ValueError(f"{label}: template has no %2")
        return template.split("%2", 1)[1]
    if transform == "between_placeholders":
        if "%1" not in template or "%2" not in template:
            raise ValueError(f"{label}: template lacks placeholders")
        return template.split("%1", 1)[1].split("%2", 1)[0]
    if transform == "split_br":
        part = parse_int(arguments.get("part", ""), label)
        pieces = template.split("<br>")
        if part >= len(pieces):
            raise ValueError(f"{label}: split part {part} is outside {len(pieces)} parts")
        return pieces[part]
    if transform == "join_br_parts":
        values = [parse_int(value, label) for value in arguments.get("parts", "").split(",") if value.strip()]
        if not values:
            raise ValueError(f"{label}: join_br_parts has no parts")
        pieces = template.split("<br>")
        if max(values) >= len(pieces):
            raise ValueError(f"{label}: join part is outside {len(pieces)} parts")
        return arguments.get("join", "<br>").join(pieces[value] for value in values)
    if transform == "insert_br_after_words":
        count = parse_int(arguments.get("words", ""), label)
        pieces = template.split(" ")
        if any(not piece for piece in pieces):
            raise ValueError(f"{label}: source text does not use single-space word boundaries")
        if count <= 0 or count >= len(pieces):
            raise ValueError(
                f"{label}: word break {count} is outside 1..{len(pieces) - 1}"
            )
        return " ".join(pieces[:count]) + "<br>" + " ".join(pieces[count:])
    if transform == "append_space":
        return template + " "
    if transform == "flatten_br_slice":
        flattened = template.replace("<br>", " ")
        start = parse_int(arguments.get("start", ""), label)
        end = parse_int(arguments.get("end", ""), label)
        if start > end or end > len(flattened):
            raise ValueError(
                f"{label}: slice {start}:{end} is outside flattened text length {len(flattened)}"
            )
        return flattened[start:end]
    if transform == "uppercase":
        return template.upper()
    raise ValueError(f"{label}: unsupported transform {transform!r}")


def resolve_source_sequence(row: dict[str, object], sources: dict[str, bytes], label: str) -> list[str]:
    source = str(row["source"])
    offset = int(row["source_offset"])
    template = read_official_z(sources[source], offset, label)
    transform = str(row.get("transform", ""))
    arguments = dict(row.get("arguments", {}))
    if transform != "split_br_sequence":
        raise ValueError(f"{label}: sequence mode requires split_br_sequence")
    values = [parse_int(value, label) for value in arguments.get("parts", "").split(",") if value.strip()]
    if not values:
        raise ValueError(f"{label}: split_br_sequence has no parts")
    pieces = template.split("<br>")
    if max(values) >= len(pieces):
        raise ValueError(f"{label}: sequence part is outside {len(pieces)} parts")
    return [pieces[value] for value in values]


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


def write_slot(output: bytearray, offset: int, capacity: int, replacement: bytes) -> None:
    if len(replacement) > capacity - 1:
        raise ValueError(f"replacement is {len(replacement)} bytes but slot allows {capacity - 1}")
    output[offset:offset + capacity] = replacement + b"\x00" + b"\x00" * (capacity - len(replacement) - 1)


def parse_mappings(rows: list[dict[str, str]]) -> dict[str, list[dict[str, object]]]:
    result = {"text": [], "bytes": [], "inactive": []}
    for line, row in enumerate(rows, 2):
        label = f"mappings.tsv line {line} ({row['id']})"
        if row["enabled"] not in {"0", "1"}:
            raise ValueError(f"{label}: enabled must be 0 or 1")
        mode = row["mode"].lower()
        if mode not in VALID_MODES:
            raise ValueError(f"{label}: unsupported mode {mode!r}")
        target = row["target"].upper()
        if target not in TARGET_SPECS:
            raise ValueError(f"{label}: unsupported target {target!r}")
        if row["enabled"] == "0":
            result["inactive"].append(row)
            continue
        common = {"id": row["id"], "section": row["section"] or "unclassified", "mode": mode,
                  "target": target, "reason": row["reason"]}
        if mode in {"slot", "sequence", "shorten"}:
            source, source_offset = parse_source_ref(row["source_ref"], label)
            transform = row["transform"].lower()
            if transform not in VALID_TRANSFORMS:
                raise ValueError(f"{label}: unsupported transform {transform!r}")
            short_text = row["value"]
            if mode == "shorten" and (not short_text.startswith("[S]") or not short_text):
                raise ValueError(f"{label}: shorten rows require [S]-prefixed value")
            if mode in {"slot", "sequence"} and short_text:
                raise ValueError(f"{label}: {mode} rows require an empty value")
            if mode == "sequence" and transform != "split_br_sequence":
                raise ValueError(f"{label}: sequence rows require split_br_sequence")
            result["text"].append({
                **common,
                "target_offset": parse_int(row["target_offset"], label),
                "capacity": parse_int(row["capacity"], label),
                "source": source,
                "source_offset": source_offset,
                "transform": transform,
                "arguments": parse_arguments(row["arguments"], label),
                "short_text": short_text,
            })
        elif mode == "bytes":
            if "=>" not in row["value"]:
                raise ValueError(f"{label}: bytes value must be EXPECTED=>REPLACEMENT")
            expected_text, replacement_text = row["value"].split("=>", 1)
            expected = parse_hex(expected_text, label)
            replacement = parse_hex(replacement_text, label)
            if len(expected) != len(replacement):
                raise ValueError(f"{label}: byte patch changes file size")
            result["bytes"].append({**common, "target_offset": parse_int(row["target_offset"], label),
                                    "expected": expected, "replacement": replacement})
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
    official_sources: dict[str, bytes],
    title_policy: GameTitlePolicy,
) -> tuple[
    dict[str, str],
    dict[str, tuple[str, ...]],
    dict[str, str],
    dict[str, str],
]:
    """Resolve official templates and transforms once for downstream consumers."""
    source_templates: dict[str, str] = {}
    resolved_texts: dict[str, str] = {}
    resolved_sequences: dict[str, tuple[str, ...]] = {}
    materialized_templates: dict[str, str] = {}
    policy_hits: dict[str, int] = {}

    for row in mappings:
        if str(row["target"]) not in selected:
            continue
        mapping_id = str(row["id"])
        source = str(row["source"])
        source_offset = int(row["source_offset"])
        template = read_official_z(
            official_sources[source], source_offset, f"{mapping_id} source template"
        )
        source_templates[mapping_id] = template
        materialized_templates[mapping_id] = template.replace(
            title_policy.donor_title, title_policy.output_title
        )
        if row["mode"] == "sequence":
            sequence = tuple(
                resolve_source_sequence(row, official_sources, mapping_id)
            )
            occurrences = sum(
                value.count(title_policy.donor_title) for value in sequence
            )
            if occurrences:
                policy_hits[mapping_id] = occurrences
            resolved_sequences[mapping_id] = tuple(
                value.replace(title_policy.donor_title, title_policy.output_title)
                for value in sequence
            )
        else:
            resolved = resolve_source_text(
                row, official_sources, mapping_id
            )
            occurrences = resolved.count(title_policy.donor_title)
            if occurrences:
                policy_hits[mapping_id] = occurrences
            resolved_texts[mapping_id] = resolved.replace(
                title_policy.donor_title, title_policy.output_title
            )

    if title_policy.target in selected and (
        len(policy_hits) != title_policy.expected_mapping_count
        or sum(policy_hits.values()) != title_policy.expected_occurrence_count
    ):
        raise ValueError(
            "translation importer game-title policy coverage differs from config.tsv: "
            f"{len(policy_hits)} mappings/{sum(policy_hits.values())} occurrences"
        )
    return (
        resolved_texts,
        resolved_sequences,
        source_templates,
        materialized_templates,
    )


def apply_text_mappings(
    mappings,
    selected,
    clean_targets,
    output_targets,
    resolved_texts,
    resolved_sequences,
):
    annotations = []
    occupied: dict[str, list[tuple[int, int, str]]] = defaultdict(list)
    stats = Counter()
    sections = Counter()
    for row in mappings:
        target = str(row["target"])
        if target not in selected:
            continue
        offset = int(row["target_offset"])
        capacity = int(row["capacity"])
        label = f"{row['id']} {target} 0x{offset:X}"
        for start, end, prior in occupied[target]:
            if offset < end and start < offset + capacity:
                raise ValueError(f"{label}: overlaps {prior} at 0x{start:X}-0x{end:X}")
        if row["mode"] == "sequence":
            target_fragments, _ = read_target_sequence(clean_targets[target], offset, capacity, label)
            official_fragments = resolved_sequences[str(row["id"])]
            target_context = "<NUL>".join(target_fragments)
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
            official = resolved_texts[str(row["id"])]
            target_text, _ = read_target_slot(clean_targets[target], offset, capacity, label)
            validate_semantic_replacement(official, target_text, label)
            if row["mode"] == "shorten":
                replacement_text = str(row["short_text"])
                stats["shortened"] += 1
            else:
                replacement_text = adapt_source_markup(official, target_text, label)
            replacement = replacement_text.encode("cp1252")
            write_slot(output_targets[target], offset, capacity, replacement)
        occupied[target].append((offset, offset + capacity, str(row["id"])))
        annotations.append({"path": TARGET_SPECS[target][0], "start": offset, "end": offset + capacity,
                            "source_text": target_text, "replacement_text": replacement_text,
                            "mapping_id": str(row["id"]), "reason": str(row["reason"])})
        stats["mapped"] += 1
        if clean_targets[target][offset:offset + capacity] != bytes(output_targets[target][offset:offset + capacity]):
            stats["changed"] += 1
        sections[str(row["section"])] += 1
    return annotations, dict(stats), dict(sorted(sections.items()))


def apply_byte_mappings(mappings, selected, output_targets):
    annotations = []
    occupied: dict[str, list[tuple[int, int, str]]] = defaultdict(list)
    stats = Counter()
    sections = Counter()
    for row in mappings:
        target = str(row["target"])
        if target not in selected:
            continue
        offset = int(row["target_offset"])
        expected = bytes(row["expected"])
        replacement = bytes(row["replacement"])
        label = f"{row['id']} {target} 0x{offset:X}"
        if offset < 0 or offset + len(expected) > len(output_targets[target]):
            raise ValueError(f"{label}: patch outside file")
        for start, end, prior in occupied[target]:
            if offset < end and start < offset + len(expected):
                raise ValueError(f"{label}: overlaps {prior}")
        actual = bytes(output_targets[target][offset:offset + len(expected)])
        if actual != expected:
            raise ValueError(f"{label}: expected {expected.hex().upper()}, found {actual.hex().upper()}")
        output_targets[target][offset:offset + len(expected)] = replacement
        occupied[target].append((offset, offset + len(expected), str(row["id"])))
        annotations.append({"path": TARGET_SPECS[target][0], "start": offset, "end": offset + len(expected),
                            "source_text": "", "replacement_text": "",
                            "mapping_id": str(row["id"]), "reason": str(row["reason"])})
        stats["mapped"] += 1
        if expected != replacement:
            stats["changed"] += 1
        sections[str(row["section"])] += 1
    return annotations, dict(stats), dict(sorted(sections.items()))


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
    nun5_iso: Optional[Path] = None,
    nun5_folder: Optional[Path] = None,
    data_root: Path,
    apply: str = "BTL,ETC,SLPS",
) -> TranslationImportPlan:
    """Import and validate strings without writing them into game payloads."""
    selected_list = parse_apply(apply)
    selected = set(selected_list)
    na2 = source_from(na2_folder, na2_iso, "NA2")
    nun5 = source_from(nun5_folder, nun5_iso, "NUN5")
    clean_targets = {
        target: na2.read(TARGET_SPECS[target][1], f"NA2 {TARGET_SPECS[target][0]}")
        for target in selected_list
    }
    official_sources = {
        key: nun5.read(candidates, key) for key, candidates in SOURCE_SPECS.items()
    }
    actual_hashes = {
        **{f"NA2_{target}": sha1(data) for target, data in clean_targets.items()},
        **{key: sha1(data) for key, data in official_sources.items()},
    }
    for key, expected in EXPECTED_SHA1.items():
        actual = actual_hashes.get(key)
        if actual is not None and actual != expected:
            raise ValueError(f"Unexpected {key} SHA-1: {actual}; expected {expected}")

    data_root = data_root.resolve()
    mapping_version, packaged_hash, title_policy = read_mapping_metadata(data_root)
    mapping_path = data_root / "mappings.tsv"
    actual_mapping_hash = hashlib.sha256(mapping_path.read_bytes()).hexdigest()
    if actual_mapping_hash != packaged_hash:
        raise ValueError(
            "translation importer mappings.tsv SHA-256 does not match config.tsv: "
            f"{actual_mapping_hash} != {packaged_hash}"
        )
    rows_raw = read_rows(mapping_path)
    mappings = parse_mappings(rows_raw)
    references = read_references(data_root / "references.tsv")
    reference_counts = validate_references(
        references, mappings["text"], clean_targets
    )
    resolved_texts, resolved_sequences, source_templates, materialized_templates = (
        resolve_text_materializations(
            mappings["text"], selected, official_sources, title_policy
        )
    )
    output_targets = {
        target: bytearray(clean_targets[target]) for target in selected_list
    }

    text_annotations, text_stats, text_sections = apply_text_mappings(
        mappings["text"],
        selected,
        clean_targets,
        output_targets,
        resolved_texts,
        resolved_sequences,
    )
    byte_annotations, byte_stats, byte_sections = apply_byte_mappings(
        mappings["bytes"], selected, output_targets
    )
    annotations = text_annotations + byte_annotations

    import_rows: list[dict[str, str]] = []
    import_targets: dict[str, dict[str, object]] = {}
    translated_hashes: dict[str, dict[str, object]] = {}
    for target in selected_list:
        path = TARGET_SPECS[target][0]
        output = bytes(output_targets[target])
        rows = diff_rows(path, clean_targets[target], output, annotations)
        for row in rows:
            row["import_id"] = f"{target}-I{len(import_rows) + 1:04d}"
            row["group_id"] = target
            import_rows.append(row)
        import_targets[path] = {
            "root_id": "na2",
            "path": path,
            "expected_size": len(clean_targets[target]),
            "expected_sha256": hashlib.sha256(clean_targets[target]).hexdigest().upper(),
        }
        translated_hashes[path] = {
            "source_sha1": sha1(clean_targets[target]),
            "translated_sha1": sha1(output),
            "size": len(output),
        }

    active_by_mode = Counter(
        row["mode"] for row in mappings["text"] if row["target"] in selected
    )
    active_by_mode.update(
        row["mode"] for row in mappings["bytes"] if row["target"] in selected
    )
    active_sections = Counter(text_sections)
    active_sections.update(byte_sections)
    summary: dict[str, object] = {
        "mapping_version": mapping_version,
        "mode": "official-source translation importer",
        "targets": selected_list,
        "output": {
            "import_rows": len(import_rows),
            "text_mappings_applied": text_stats.get("mapped", 0),
            "text_mappings_changed": text_stats.get("changed", 0),
            "shortened_mappings_applied": text_stats.get("shortened", 0),
            "structural_patches_applied": byte_stats.get("mapped", 0),
        },
        "active_mapping_coverage": {
            "by_mode": dict(sorted(active_by_mode.items())),
            "by_section": dict(sorted(active_sections.items())),
        },
        "source_hashes": actual_hashes,
        "translated_file_hashes": translated_hashes,
        "reference_inventory": reference_counts,
        "game_title_policy": {
            "donor_title": title_policy.donor_title,
            "output_title": title_policy.output_title,
            "target": title_policy.target,
            "mapping_count": title_policy.expected_mapping_count,
            "occurrence_count": title_policy.expected_occurrence_count,
        },
    }
    return TranslationImportPlan(
        mapping_version=mapping_version,
        packaged_mappings_sha256=packaged_hash,
        import_rows=import_rows,
        targets=import_targets,
        text_mappings=tuple(mappings["text"]),
        references=references,
        resolved_texts=resolved_texts,
        resolved_sequences=resolved_sequences,
        source_templates=source_templates,
        materialized_templates=materialized_templates,
        clean_targets=clean_targets,
        official_sources=official_sources,
        summary=summary,
    )
