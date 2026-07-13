#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional, Sequence

SECTOR = 2048
UTC_PLUS_3 = dt.timezone(dt.timedelta(hours=3))

TARGET_SPECS = {
    "BTL": ("PRG/BTL.BIN", ["PRG/BTL.BIN", "BTL.BIN"]),
    "ETC": ("PRG/ETC.BIN", ["PRG/ETC.BIN", "ETC.BIN"]),
    "SLPS": ("SLPS_258.37", ["SLPS_258.37"]),
}

SOURCE_SPECS = {
    "UN5_BTL": ["PRG/BTL.BIN", "BTL.BIN"],
    "UN5_ETC": ["PRG/ETC.BIN", "ETC.BIN"],
    "UN5_TEXTENG": ["PRG/TEXTENG.BIN", "TEXTENG.BIN"],
    "UN5_SLES": ["SLES_556.05"],
}

MAPPING_FIELDS = [
    "mode",
    "target",
    "target_offset",
    "capacity",
    "source",
    "source_offset",
    "pool_offset",
    "pool_capacity",
    "runtime_base",
    "pointer_offsets",
    "reason",
]

EXPECTED_SHA1 = {
    "NA2_BTL": "bf7fc7331a2a4f34fc90b84b45772ae1f6bcab03",
    "NA2_ETC": "dcfffd7eb14e484a4c0fbc195599a0b45a9a11c1",
    "NA2_SLPS": "bbe206bbf4da0ee815b437226ceb6a533c95833e",
    "UN5_BTL": "874b9d64ddec7f9f742a08831505155001adb863",
    "UN5_ETC": "1c9b05bc501cac21b7da17c5fc6c99dd3869f3be",
    "UN5_TEXTENG": "77fafba95157e44ccd61783a04aba87c4b98b1fb",
    "UN5_SLES": "fe54357b016bc579b435a593e330d2d0ff822cdf",
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
    def _record(buf: bytes, offset: int) -> tuple[Optional[tuple[int, int, int, bytes]], int]:
        if offset >= len(buf) or buf[offset] == 0:
            return None, 0
        length = buf[offset]
        record = buf[offset : offset + length]
        if len(record) < 34:
            raise ValueError(f"Invalid ISO directory record at 0x{offset:X}")
        extent = int.from_bytes(record[2:6], "little")
        size = int.from_bytes(record[10:14], "little")
        flags = record[25]
        name_length = record[32]
        return (extent, size, flags, record[33 : 33 + name_length]), length

    def _walk(self, record: IsoRecord, prefix: str) -> None:
        directory = self.data[
            record.extent * SECTOR : record.extent * SECTOR + record.size
        ]
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
        pvd: Optional[bytes] = None
        for sector in range(16, min(128, len(self.data) // SECTOR)):
            offset = sector * SECTOR
            if self.data[offset] == 1 and self.data[offset + 1 : offset + 6] == b"CD001":
                pvd = self.data[offset : offset + SECTOR]
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
                return self.data[
                    record.extent * SECTOR : record.extent * SECTOR + record.size
                ]
        basenames = {value.rsplit("/", 1)[-1] for value in normalized}
        matches = [
            record
            for path, record in self.records.items()
            if not record.is_dir and path.rsplit("/", 1)[-1] in basenames
        ]
        if len(matches) == 1:
            record = matches[0]
            return self.data[
                record.extent * SECTOR : record.extent * SECTOR + record.size
            ]
        raise FileNotFoundError(f"Could not uniquely locate {label} in {self.path}")


class FolderSource:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        if not self.root.is_dir():
            raise FileNotFoundError(self.root)
        self.files = {
            normalize_path(path.relative_to(self.root).as_posix()): path
            for path in self.root.rglob("*")
            if path.is_file()
        }

    def read(self, candidates: Sequence[str], label: str) -> bytes:
        normalized = [normalize_path(value) for value in candidates]
        for candidate in normalized:
            path = self.files.get(candidate)
            if path:
                return path.read_bytes()
        basenames = {value.rsplit("/", 1)[-1] for value in normalized}
        matches = [
            path
            for name, path in self.files.items()
            if name.rsplit("/", 1)[-1] in basenames
        ]
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
    selected: list[str] = []
    for part in value.replace(";", ",").split(","):
        item = part.strip().upper()
        if not item or item in {"NONE", "NO", "OFF"}:
            continue
        if item == "ALL":
            selected.extend(TARGET_SPECS)
            continue
        selected.append(aliases.get(item, item))
    unknown = sorted(set(selected) - set(TARGET_SPECS))
    if unknown:
        raise ValueError("Unsupported target(s): " + ", ".join(unknown))
    selected = list(dict.fromkeys(selected))
    if not selected:
        raise ValueError("No translation targets selected")
    return selected


def parse_mapping_int(value: str, label: str) -> int:
    text = value.strip()
    if not text:
        raise ValueError(f"{label}: missing integer value")
    try:
        number = int(text, 0)
    except ValueError as exc:
        raise ValueError(f"{label}: invalid integer {text!r}") from exc
    if number < 0:
        raise ValueError(f"{label}: negative integer {number}")
    return number


def load_mappings_tsv(path: Path) -> dict[str, object]:
    slots: list[dict[str, object]] = []
    pools: list[dict[str, object]] = []
    pools_by_key: dict[tuple[str, int, int, int], dict[str, object]] = {}
    unresolved: list[dict[str, object]] = []

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != MAPPING_FIELDS:
            raise ValueError(
                "mappings.tsv must contain exactly these columns in this order: "
                + "\t".join(MAPPING_FIELDS)
            )
        for line_number, raw in enumerate(reader, 2):
            row = {key: (value or "").strip() for key, value in raw.items()}
            mode = row["mode"].lower()
            target = row["target"].upper()
            label = f"mappings.tsv line {line_number}"
            if target not in TARGET_SPECS:
                raise ValueError(f"{label}: unsupported target {target!r}")

            if mode == "slot":
                source = row["source"].upper()
                if source not in SOURCE_SPECS:
                    raise ValueError(f"{label}: unsupported source {source!r}")
                slots.append({
                    "mode": "slot",
                    "target": target,
                    "target_offset": parse_mapping_int(row["target_offset"], label),
                    "capacity": parse_mapping_int(row["capacity"], label),
                    "source": source,
                    "source_offset": parse_mapping_int(row["source_offset"], label),
                })
                continue

            if mode == "pool":
                source = row["source"].upper()
                if source not in SOURCE_SPECS:
                    raise ValueError(f"{label}: unsupported source {source!r}")
                pool_offset = parse_mapping_int(row["pool_offset"], label)
                pool_capacity = parse_mapping_int(row["pool_capacity"], label)
                runtime_base = parse_mapping_int(row["runtime_base"], label)
                pointer_values = [
                    value.strip()
                    for value in row["pointer_offsets"].split(",")
                    if value.strip()
                ]
                if not pointer_values:
                    raise ValueError(f"{label}: pool row has no pointer offsets")
                key = (target, pool_offset, pool_capacity, runtime_base)
                pool = pools_by_key.get(key)
                if pool is None:
                    pool = {
                        "mode": "pool",
                        "target": target,
                        "pool_offset": pool_offset,
                        "pool_capacity": pool_capacity,
                        "runtime_base": runtime_base,
                        "entries": [],
                    }
                    pools_by_key[key] = pool
                    pools.append(pool)
                pool["entries"].append({
                    "source": source,
                    "source_offset": parse_mapping_int(row["source_offset"], label),
                    "pointer_offsets": [
                        parse_mapping_int(value, label) for value in pointer_values
                    ],
                })
                continue

            if mode == "unresolved":
                reason = row["reason"]
                if not reason:
                    raise ValueError(f"{label}: unresolved row has no reason")
                unresolved.append({
                    "target": target,
                    "target_offset": parse_mapping_int(row["target_offset"], label),
                    "capacity": parse_mapping_int(row["capacity"], label),
                    "reason": reason,
                })
                continue

            raise ValueError(f"{label}: unsupported mode {mode!r}")

    if not slots and not pools:
        raise ValueError("mappings.tsv contains no resolved mappings")
    return {"slots": slots, "pools": pools, "unresolved": unresolved}


def read_ascii_z(data: bytes, offset: int, label: str) -> tuple[str, bytes]:
    if offset < 0 or offset >= len(data):
        raise ValueError(f"{label}: source offset 0x{offset:X} is outside the file")
    end = data.find(b"\x00", offset)
    if end < 0:
        raise ValueError(f"{label}: unterminated source string at 0x{offset:X}")
    raw = data[offset:end]
    if not raw:
        raise ValueError(f"{label}: empty source string at 0x{offset:X}")
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{label}: source string is not ASCII") from exc
    if any(ord(char) < 0x20 and char not in "\t\r\n" for char in text):
        raise ValueError(f"{label}: source string contains unsupported control bytes")
    return text, raw


def read_target_slot(data: bytes, offset: int, capacity: int, label: str) -> tuple[str, bytes]:
    if capacity <= 0:
        raise ValueError(f"{label}: non-positive capacity")
    if offset < 0 or offset + capacity > len(data):
        raise ValueError(f"{label}: target range 0x{offset:X}+{capacity} is outside the file")
    slot = data[offset : offset + capacity]
    end = slot.find(b"\x00")
    if end < 0:
        raise ValueError(f"{label}: target slot has no NUL terminator")
    raw = slot[:end]
    try:
        text = raw.decode("cp932")
    except UnicodeDecodeError:
        text = ""
    return text, raw


NAMED_COLOR_TAG_EQUIVALENTS = {
    "<WHITE>": ("<WHITE>", "<colorFFFFFF>"),
    "<BLACK>": ("<BLACK>", "<color000000>"),
    "<RED>": ("<RED>",),
}


def adapt_source_markup(source_text: str, target_text: str, label: str) -> str:
    """Translate UN5 named color tags into the verified local NA2 tag dialect.

    NA2 and UN5 share generic <colorRRGGBB>, icon, line-break, and other
    markup. Their named color aliases are not identical in every renderer.
    The target slot itself is the authority: a named UN5 color token is
    rewritten only to an equivalent token already used by that NA2 string.
    """
    adapted = source_text
    for source_tag, target_candidates in NAMED_COLOR_TAG_EQUIVALENTS.items():
        if source_tag not in adapted:
            continue
        replacement = next(
            (candidate for candidate in target_candidates if candidate in target_text),
            None,
        )
        if replacement is None:
            raise ValueError(
                f"{label}: cannot verify an NA2 equivalent for source tag {source_tag}"
            )
        adapted = adapted.replace(source_tag, replacement)
    return adapted


def read_pointer_target_text(data: bytes, pointer_offset: int, runtime_base: int) -> str:
    if pointer_offset < 0 or pointer_offset + 4 > len(data):
        return ""
    pointer = int.from_bytes(data[pointer_offset : pointer_offset + 4], "little")
    offset = pointer - runtime_base
    if offset < 0 or offset >= len(data):
        return ""
    end = data.find(b"\x00", offset)
    if end < 0:
        return ""
    try:
        return data[offset:end].decode("cp932")
    except UnicodeDecodeError:
        return ""


def write_slot(output: bytearray, offset: int, capacity: int, replacement: bytes) -> None:
    if len(replacement) > capacity - 1:
        raise ValueError("replacement does not fit target slot")
    output[offset : offset + capacity] = (
        replacement + b"\x00" + b"\x00" * (capacity - len(replacement) - 1)
    )


def apply_slot_mappings(
    mappings: Sequence[dict],
    selected: set[str],
    clean_targets: dict[str, bytes],
    output_targets: dict[str, bytearray],
    official_sources: dict[str, bytes],
) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, int]]:
    annotations: list[dict[str, object]] = []
    skipped: list[dict[str, object]] = []
    stats = {"mapped": 0, "changed": 0, "skipped_too_long": 0, "skipped_invalid": 0}

    occupied: dict[str, list[tuple[int, int]]] = {target: [] for target in selected}
    for index, row in enumerate(mappings, 1):
        target = str(row["target"]).upper()
        if target not in selected:
            continue
        offset = int(row["target_offset"])
        capacity = int(row["capacity"])
        source_key = str(row["source"])
        source_offset = int(row["source_offset"])
        label = f"slot mapping #{index} {target} 0x{offset:X}"
        try:
            official_text, _ = read_ascii_z(
                official_sources[source_key], source_offset, label
            )
            target_text, _ = read_target_slot(
                clean_targets[target], offset, capacity, label
            )
            source_text = adapt_source_markup(official_text, target_text, label)
            source_bytes = source_text.encode("ascii")
            if len(source_bytes) > capacity - 1:
                skipped.append({
                    "target": target,
                    "target_offset": f"0x{offset:X}",
                    "capacity": capacity,
                    "source": source_key,
                    "source_offset": f"0x{source_offset:X}",
                    "reason": "SOURCE_TEXT_TOO_LONG",
                    "source_bytes": len(source_bytes),
                })
                stats["skipped_too_long"] += 1
                continue
            for start, end in occupied[target]:
                if offset < end and start < offset + capacity:
                    raise ValueError(f"{label}: overlaps another slot mapping")
            occupied[target].append((offset, offset + capacity))
            before = bytes(output_targets[target][offset : offset + capacity])
            write_slot(output_targets[target], offset, capacity, source_bytes)
            after = bytes(output_targets[target][offset : offset + capacity])
            annotations.append({
                "path": TARGET_SPECS[target][0],
                "start": offset,
                "end": offset + capacity,
                "source_text": target_text,
                "replacement_text": source_text,
            })
            stats["mapped"] += 1
            if before != after:
                stats["changed"] += 1
        except Exception as exc:
            skipped.append({
                "target": target,
                "target_offset": f"0x{offset:X}",
                "capacity": capacity,
                "source": source_key,
                "source_offset": f"0x{source_offset:X}",
                "reason": "INVALID_MAPPING",
                "detail": str(exc),
            })
            stats["skipped_invalid"] += 1
    return annotations, skipped, stats


def apply_pool_mappings(
    pools: Sequence[dict],
    selected: set[str],
    clean_targets: dict[str, bytes],
    output_targets: dict[str, bytearray],
    official_sources: dict[str, bytes],
) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, int]]:
    annotations: list[dict[str, object]] = []
    skipped: list[dict[str, object]] = []
    stats = {"pools": 0, "entries": 0, "pointer_writes": 0}

    for pool_index, pool in enumerate(pools, 1):
        target = str(pool["target"]).upper()
        if target not in selected:
            continue
        pool_offset = int(pool["pool_offset"])
        pool_capacity = int(pool["pool_capacity"])
        runtime_base = int(pool["runtime_base"])
        entries = list(pool.get("entries", []))
        label = f"pool mapping #{pool_index} {target} 0x{pool_offset:X}"
        if pool_offset < 0 or pool_offset + pool_capacity > len(clean_targets[target]):
            raise ValueError(f"{label}: pool is outside the target file")

        resolved = []
        total = 0
        for entry_index, entry in enumerate(entries, 1):
            source_key = str(entry["source"])
            source_offset = int(entry["source_offset"])
            entry_label = f"{label} entry #{entry_index}"
            official_text, _ = read_ascii_z(
                official_sources[source_key], source_offset, entry_label
            )
            pointer_offsets = [int(value) for value in entry["pointer_offsets"]]
            if not pointer_offsets:
                raise ValueError(f"{entry_label}: no pointer offsets")
            for pointer_offset in pointer_offsets:
                if pointer_offset < 0 or pointer_offset + 4 > len(clean_targets[target]):
                    raise ValueError(f"{entry_label}: pointer offset is outside the file")
            source_target_text = read_pointer_target_text(
                clean_targets[target], pointer_offsets[0], runtime_base
            )
            source_text = adapt_source_markup(
                official_text, source_target_text, entry_label
            )
            payload = source_text.encode("ascii") + b"\x00"
            total += len(payload)
            resolved.append((entry, source_target_text, source_text, payload, pointer_offsets))

        if total > pool_capacity:
            skipped.append({
                "target": target,
                "pool_offset": f"0x{pool_offset:X}",
                "pool_capacity": pool_capacity,
                "required": total,
                "reason": "POOL_TOO_SMALL",
            })
            continue

        output_targets[target][pool_offset : pool_offset + pool_capacity] = b"\x00" * pool_capacity
        cursor = pool_offset
        for _entry, source_target_text, source_text, payload, pointer_offsets in resolved:
            output_targets[target][cursor : cursor + len(payload)] = payload
            pointer_value = runtime_base + cursor
            for pointer_offset in pointer_offsets:
                output_targets[target][pointer_offset : pointer_offset + 4] = pointer_value.to_bytes(4, "little")
                stats["pointer_writes"] += 1
            annotations.append({
                "path": TARGET_SPECS[target][0],
                "start": cursor,
                "end": cursor + len(payload),
                "source_text": source_target_text,
                "replacement_text": source_text,
            })
            cursor += len(payload)
            stats["entries"] += 1
        stats["pools"] += 1

    return annotations, skipped, stats


def diff_rows(
    path: str,
    clean: bytes,
    output: bytes,
    annotations: Sequence[dict[str, object]],
) -> list[dict[str, str]]:
    if len(clean) != len(output):
        raise ValueError(f"Cannot emit fixed-offset patches for size-changed file: {path}")

    normalized = normalize_path(path)
    relevant = [
        item for item in annotations
        if normalize_path(str(item["path"])) == normalized
    ]

    ranges: list[tuple[int, int]] = []
    start: Optional[int] = None
    for index, (before, after) in enumerate(zip(clean, output)):
        if before != after and start is None:
            start = index
        elif before == after and start is not None:
            ranges.append((start, index))
            start = None
    if start is not None:
        ranges.append((start, len(clean)))

    rows: list[dict[str, str]] = []
    for range_start, range_end in ranges:
        boundaries = {range_start, range_end}
        for annotation in relevant:
            annotation_start = int(annotation["start"])
            annotation_end = int(annotation["end"])
            if range_start < annotation_end and annotation_start < range_end:
                boundaries.add(max(range_start, annotation_start))
                boundaries.add(min(range_end, annotation_end))
        ordered = sorted(boundaries)
        for segment_start, segment_end in zip(ordered, ordered[1:]):
            if segment_start >= segment_end:
                continue
            matching = [
                item for item in relevant
                if segment_start < int(item["end"])
                and int(item["start"]) < segment_end
            ]
            if matching:
                annotation = matching[-1]
                source_text = str(annotation["source_text"])
                replacement_text = str(annotation["replacement_text"])
            else:
                source_text = ""
                replacement_text = ""
            rows.append({
                "path": path,
                "offset": f"0x{segment_start:X}",
                "expected_hex": clean[segment_start:segment_end].hex().upper(),
                "replacement_hex": output[segment_start:segment_end].hex().upper(),
                "source_text": source_text,
                "replacement_text": replacement_text,
            })
    return rows


def write_translation_tsv(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        raise ValueError("No translation patches were generated")
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    fields = [
        "path",
        "offset",
        "expected_hex",
        "replacement_hex",
        "source_text",
        "replacement_text",
    ]
    try:
        with temporary.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build one NA2 post-composition translation TSV from official UN5 sources"
    )
    parser.add_argument("--na2-iso", type=Path)
    parser.add_argument("--na2-folder", type=Path)
    parser.add_argument("--un5-iso", type=Path)
    parser.add_argument("--un5-folder", type=Path)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--apply", default="BTL,ETC,SLPS")
    parser.add_argument("--no-strict-hash", action="store_true")
    args = parser.parse_args()

    selected_list = parse_apply(args.apply)
    selected = set(selected_list)
    na2 = source_from(args.na2_folder, args.na2_iso, "NA2")
    un5 = source_from(args.un5_folder, args.un5_iso, "UN5")

    clean_targets = {
        target: na2.read(TARGET_SPECS[target][1], f"NA2 {TARGET_SPECS[target][0]}")
        for target in selected_list
    }
    official_sources = {
        key: un5.read(candidates, key)
        for key, candidates in SOURCE_SPECS.items()
    }

    actual_hashes = {
        **{f"NA2_{target}": sha1(data) for target, data in clean_targets.items()},
        **{key: sha1(data) for key, data in official_sources.items()},
    }
    if not args.no_strict_hash:
        for key, expected in EXPECTED_SHA1.items():
            actual = actual_hashes.get(key)
            if actual is not None and actual != expected:
                raise ValueError(f"Unexpected {key} SHA-1: {actual}; expected {expected}")

    mapping_path = args.data_root / "mappings.tsv"
    mapping_data = load_mappings_tsv(mapping_path)

    output_targets = {
        target: bytearray(clean_targets[target])
        for target in selected_list
    }

    slot_annotations, slot_skipped, slot_stats = apply_slot_mappings(
        mapping_data.get("slots", []),
        selected,
        clean_targets,
        output_targets,
        official_sources,
    )
    pool_annotations, pool_skipped, pool_stats = apply_pool_mappings(
        mapping_data.get("pools", []),
        selected,
        clean_targets,
        output_targets,
        official_sources,
    )
    annotations = slot_annotations + pool_annotations

    rows: list[dict[str, str]] = []
    translated_hashes = {}
    for target in selected_list:
        path = TARGET_SPECS[target][0]
        output = bytes(output_targets[target])
        rows.extend(diff_rows(path, clean_targets[target], output, annotations))
        translated_hashes[path] = {
            "source_sha1": sha1(clean_targets[target]),
            "translated_sha1": sha1(output),
            "size": len(output),
        }

    now = dt.datetime.now(UTC_PLUS_3)
    run_id = now.strftime("%Y%m%d_%H%M%S_%f")[:-3] + f"_pid{os.getpid()}"
    run_root = args.work_root.resolve() / "runs" / run_id
    run_root.mkdir(parents=True, exist_ok=False)
    final_path = run_root / f"NA2_APPLY__TRANSLATION__{run_id}.tsv"
    write_translation_tsv(final_path, rows)

    selected_unresolved = [
        row for row in mapping_data.get("unresolved", [])
        if str(row.get("target", "")).upper() in selected
    ]
    summary = {
        "mode": "official-source post-composition TSV",
        "run_id": run_id,
        "timezone": "UTC+03:00",
        "translation_tsv": str(final_path),
        "patch_rows": len(rows),
        "targets": selected_list,
        "source_hashes": actual_hashes,
        "translated_file_hashes": translated_hashes,
        "slot_stats": slot_stats,
        "pool_stats": pool_stats,
        "skipped_runtime": slot_skipped + pool_skipped,
        "unresolved_mappings": selected_unresolved,
    }
    write_json(run_root / "build_summary.json", summary)

    print("Built NA2 translation TSV:")
    print(f"  {final_path}")
    print(f"  patch rows: {len(rows)}")
    print(f"  mapped text slots: {slot_stats['mapped']}")
    print(f"  relocated official strings: {pool_stats['entries']}")
    print(f"  runtime skips: {len(slot_skipped) + len(pool_skipped)}")
    print(f"  unresolved numeric mappings: {len(selected_unresolved)}")
    for path, info in translated_hashes.items():
        print(f"  {path}: {info['size']} bytes, translated SHA-1 {info['translated_sha1']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
