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
EXPECTED_SHA1 = {
    "NA2_BTL": "bf7fc7331a2a4f34fc90b84b45772ae1f6bcab03",
    "NA2_ETC": "dcfffd7eb14e484a4c0fbc195599a0b45a9a11c1",
    "NA2_SLPS": "bbe206bbf4da0ee815b437226ceb6a533c95833e",
    "NUN5_BTL": "874b9d64ddec7f9f742a08831505155001adb863",
    "NUN5_ETC": "1c9b05bc501cac21b7da17c5fc6c99dd3869f3be",
    "NUN5_TEXTENG": "77fafba95157e44ccd61783a04aba87c4b98b1fb",
    "NUN5_SLES": "fe54357b016bc579b435a593e330d2d0ff822cdf",
}
VALID_MODES = {"slot", "sequence", "shorten", "bytes", "unresolved"}
VALID_TRANSFORMS = {
    "", "empty", "format_arg1", "format_args", "format_prefix_arg2",
    "format_suffix_arg2", "between_placeholders", "after_placeholder2",
    "split_br", "split_br_sequence", "join_br_parts", "append_space", "flatten_br_slice",
}
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
class TranslationPlan:
    mapping_version: int
    packaged_mappings_sha256: str
    patch_rows: list[dict[str, str]]
    summary: dict[str, object]


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


def read_mapping_metadata(data_root: Path) -> tuple[int, str]:
    """Read the canonical mapping version and packaged mappings hash from README."""
    readme_path = data_root / "README.md"
    try:
        text = readme_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"Could not read mapping metadata from {readme_path}") from exc

    version_match = re.search(r"(?mi)^- Version:\s*`([0-9]+)`\s*$", text)
    hash_match = re.search(
        r"(?mi)^- Packaged `mappings\.tsv` SHA-256:\s*`([0-9a-f]{64})`\s*$",
        text,
    )
    if version_match is None or hash_match is None:
        raise ValueError(
            "README.md must contain mapping metadata entries for Version and "
            "Packaged `mappings.tsv` SHA-256"
        )
    version = int(version_match.group(1))
    if version <= 0:
        raise ValueError("README.md mapping Version must be positive")
    return version, hash_match.group(1).lower()


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
    result = {"text": [], "bytes": [], "unresolved": [], "inactive": []}
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
        else:
            result["unresolved"].append({**common, "target_offset": parse_int(row["target_offset"], label),
                                         "capacity": parse_int(row["capacity"], label)})
    return result


def apply_text_mappings(mappings, selected, clean_targets, output_targets, official_sources):
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
            official_fragments = resolve_source_sequence(row, official_sources, label)
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
            official = resolve_source_text(row, official_sources, label)
            target_text, _ = read_target_slot(clean_targets[target], offset, capacity, label)
            if row["mode"] == "shorten":
                replacement_text = str(row["short_text"])
                stats["shortened"] += 1
            else:
                replacement_text = adapt_source_markup(official, target_text, label)
            replacement = replacement_text.encode("cp1252")
            write_slot(output_targets[target], offset, capacity, replacement)
        occupied[target].append((offset, offset + capacity, str(row["id"])))
        annotations.append({"path": TARGET_SPECS[target][0], "start": offset, "end": offset + capacity,
                            "source_text": target_text, "replacement_text": replacement_text})
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
                            "source_text": "", "replacement_text": ""})
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
            })
    return rows


def write_translation_tsv(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        raise ValueError("No translation patches were generated")
    fields = ["path", "offset", "expected_hex", "replacement_hex", "source_text", "replacement_text"]
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


def build_translation_plan(
    *,
    na2_iso: Optional[Path] = None,
    na2_folder: Optional[Path] = None,
    nun5_iso: Optional[Path] = None,
    nun5_folder: Optional[Path] = None,
    data_root: Path,
    apply: str = "BTL,ETC,SLPS",
) -> TranslationPlan:
    """Build a validated in-memory translation plan for another orchestrator."""
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
    mapping_version, packaged_hash = read_mapping_metadata(data_root)
    mapping_path = data_root / "mappings.tsv"
    rows_raw = read_rows(mapping_path)
    mappings = parse_mappings(rows_raw)
    output_targets = {
        target: bytearray(clean_targets[target]) for target in selected_list
    }

    text_annotations, text_stats, text_sections = apply_text_mappings(
        mappings["text"], selected, clean_targets, output_targets, official_sources
    )
    byte_annotations, byte_stats, byte_sections = apply_byte_mappings(
        mappings["bytes"], selected, output_targets
    )
    annotations = text_annotations + byte_annotations

    patch_rows: list[dict[str, str]] = []
    translated_hashes: dict[str, dict[str, object]] = {}
    for target in selected_list:
        path = TARGET_SPECS[target][0]
        output = bytes(output_targets[target])
        patch_rows.extend(diff_rows(path, clean_targets[target], output, annotations))
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
        "mode": "official-source translation module",
        "targets": selected_list,
        "output": {
            "patch_rows": len(patch_rows),
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
    }
    return TranslationPlan(
        mapping_version=mapping_version,
        packaged_mappings_sha256=packaged_hash,
        patch_rows=patch_rows,
        summary=summary,
    )
