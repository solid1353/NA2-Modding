#!/usr/bin/env python3
"""Build one NA2 translation patch TSV.

The builder derives all BTL, ETC, and executable translation edits from the clean
NA2/UN5 sources, but emits no replacement binaries. The resulting TSV is applied
after all selected binary packages have been composed.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import shutil
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional, Sequence

SECTOR = 2048
EXPECTED_SHA1 = {
    "NA2_BTL": "bf7fc7331a2a4f34fc90b84b45772ae1f6bcab03",
    "NA2_ETC": "dcfffd7eb14e484a4c0fbc195599a0b45a9a11c1",
    "NA2_SLPS": "bbe206bbf4da0ee815b437226ceb6a533c95833e",
    "UN5_TEXTENG": "77fafba95157e44ccd61783a04aba87c4b98b1fb",
}
FILE_SPECS = {
    "BTL": ("PRG/BTL.BIN", ["PRG/BTL.BIN", "BTL.BIN"]),
    "ETC": ("PRG/ETC.BIN", ["PRG/ETC.BIN", "ETC.BIN"]),
}
TEXTENG_CANDIDATES = ["PRG/TEXTENG.BIN", "TEXTENG.BIN"]
SLPS_CANDIDATES = ["SLPS_258.37"]
BTL_RUNTIME_BASE = 0x6B3F00


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
        rec = buf[offset : offset + length]
        if len(rec) < 34:
            raise ValueError(f"Invalid ISO directory record at 0x{offset:X}")
        extent = int.from_bytes(rec[2:6], "little")
        size = int.from_bytes(rec[10:14], "little")
        flags = rec[25]
        name_length = rec[32]
        return (extent, size, flags, rec[33 : 33 + name_length]), length

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
        normalized = [normalize_path(x) for x in candidates]
        for candidate in normalized:
            record = self.records.get(candidate)
            if record and not record.is_dir:
                return self.data[
                    record.extent * SECTOR : record.extent * SECTOR + record.size
                ]
        basenames = {x.rsplit("/", 1)[-1] for x in normalized}
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
        normalized = [normalize_path(x) for x in candidates]
        for candidate in normalized:
            path = self.files.get(candidate)
            if path:
                return path.read_bytes()
        basenames = {x.rsplit("/", 1)[-1] for x in normalized}
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


def parse_apply(value: str) -> list[str]:
    selected = [
        part.strip().upper()
        for part in value.replace(";", ",").split(",")
        if part.strip()
    ]
    selected = [part for part in selected if part not in {"NONE", "NO", "OFF"}]
    unknown = sorted(set(selected) - set(FILE_SPECS))
    if unknown:
        raise ValueError("Unsupported target(s): " + ", ".join(unknown))
    if not selected:
        raise ValueError("No translation targets selected")
    return list(dict.fromkeys(selected))


def source_from(folder: Optional[Path], iso: Optional[Path], label: str):
    if folder is not None and folder.is_dir():
        return FolderSource(folder)
    if iso is not None and iso.is_file():
        return Iso9660(iso)
    details = []
    if folder is not None:
        details.append(f"folder={folder}")
    if iso is not None:
        details.append(f"iso={iso}")
    suffix = ", ".join(details) if details else "no path supplied"
    raise FileNotFoundError(f"{label} source not found ({suffix})")


def read_ascii_z(data: bytes, offset: int, label: str) -> str:
    if offset < 0 or offset >= len(data):
        raise ValueError(f"{label}: TEXTENG offset 0x{offset:X} is outside the file")
    end = data.find(b"\x00", offset)
    if end < 0:
        raise ValueError(f"{label}: unterminated TEXTENG string at 0x{offset:X}")
    raw = data[offset:end]
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{label}: non-ASCII TEXTENG string at 0x{offset:X}") from exc
    if not text:
        raise ValueError(f"{label}: empty TEXTENG string at 0x{offset:X}")
    if any(ord(char) < 0x20 and char not in "\t\r\n" for char in text):
        raise ValueError(f"{label}: unsupported control character in TEXTENG string")
    return text


def verify_source_literal(
    clean: bytes,
    *,
    offset: int,
    source_text: str,
    capacity: int,
    label: str,
) -> bytes:
    try:
        source_bytes = source_text.encode("cp932")
    except UnicodeEncodeError as exc:
        raise ValueError(f"{label}: source text is not CP932-encodable") from exc
    if capacity < len(source_bytes) + 1:
        raise ValueError(
            f"{label}: capacity {capacity} is smaller than source literal plus NUL "
            f"({len(source_bytes) + 1})"
        )
    if offset < 0 or offset + capacity > len(clean):
        raise ValueError(f"{label}: slot 0x{offset:X}+{capacity} is outside the file")
    actual = clean[offset : offset + len(source_bytes)]
    actual_nul = clean[offset + len(source_bytes)]
    if actual != source_bytes or actual_nul != 0:
        raise ValueError(
            f"{label}: clean-source mismatch at 0x{offset:X}; expected "
            f"{source_bytes.hex()}, got {actual.hex()} and NUL=0x{actual_nul:02X}"
        )
    return source_bytes


def write_slot(output: bytearray, offset: int, capacity: int, replacement: bytes) -> None:
    if len(replacement) > capacity - 1:
        raise ValueError(
            f"replacement length {len(replacement)} exceeds slot payload {capacity - 1}"
        )
    output[offset : offset + capacity] = (
        replacement + b"\x00" + b"\x00" * (capacity - len(replacement) - 1)
    )




def patch_exact_slot(
    clean: bytes,
    output: bytearray,
    *,
    offset: int,
    capacity: int,
    source_text: str,
    replacement_text: str,
    label: str,
) -> None:
    verify_source_literal(
        clean,
        offset=offset,
        source_text=source_text,
        capacity=capacity,
        label=label,
    )
    try:
        replacement = replacement_text.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError(f"{label}: replacement is not ASCII") from exc
    write_slot(output, offset, capacity, replacement)


def patch_exact_bytes(
    clean: bytes,
    output: bytearray,
    *,
    offset: int,
    source_text: str,
    replacement_text: str,
    label: str,
) -> None:
    source = source_text.encode("cp932") + b"\x00"
    replacement = replacement_text.encode("ascii") + b"\x00"
    if len(replacement) > len(source):
        raise ValueError(f"{label}: replacement is longer than source storage")
    actual = clean[offset : offset + len(source)]
    if actual != source:
        raise ValueError(
            f"{label}: clean-source mismatch at 0x{offset:X}; "
            f"expected {source.hex()}, got {actual.hex()}"
        )
    output[offset : offset + len(source)] = replacement + b"\x00" * (
        len(source) - len(replacement)
    )


def apply_runtime_ui_fixes(
    *,
    clean_btl: bytes,
    output_btl: bytearray,
    clean_etc: bytes,
    output_etc: bytearray,
    clean_slps: bytes,
    output_slps: bytearray,
) -> tuple[dict[str, int], list[dict[str, object]]]:
    text_annotations: list[dict[str, object]] = []

    def annotate(
        path: str,
        offset: int,
        length: int,
        source_text: str,
        replacement_text: str,
    ) -> None:
        text_annotations.append(
            {
                "path": path,
                "start": offset,
                "end": offset + length,
                "source_text": source_text,
                "replacement_text": replacement_text,
            }
        )
    # Direct BTL strings missed by the legacy baseline.
    btl_slots = [
        (0x209CD0, 16, "使用不可", "No Use"),
        (0x209D98, 16, "飛び道具", "Projectile"),
        (0x209DA8, 16, "高速移動", "High Speed"),
        (0x209DE0, 16, "動かない", "Don't Move"),
        (0x209DF0, 16, "必ず返す", "Always"),
        (0x20A210, 16, "対戦時間", "Battle Time"),
        (0x20A748, 16, "連係攻撃", "Linked Attack"),
        (0x20A768, 16, "コマンド表示", "Command Display"),
        (0x20A788, 16, "案内忍音声", "Guide Sound"),
        (0x20A7A8, 16, "追い討ち返し", "Extra Counter"),
    ]
    for offset, capacity, source, replacement in btl_slots:
        patch_exact_slot(
            clean_btl,
            output_btl,
            offset=offset,
            capacity=capacity,
            source_text=source,
            replacement_text=replacement,
            label=f"BTL UI fix at 0x{offset:X}",
        )
        annotate("PRG/BTL.BIN", offset, capacity, source, replacement)

    # Shop help strings visible in the reported shop screen.
    etc_slots = [
        (
            0x2F230,
            112,
            "<r購入|こうにゅう>する<r商品|しょうひん>を<r選|えら>び、<iconCIRCLE>ボタンを<r押|お>してください。",
            "Press <iconCIRCLE> to choose item.",
        ),
        (
            0x2F3F0,
            112,
            "<r購入|こうにゅう>する<r商品|しょうひん>にカーソルを<r合|あ>わせ、<iconCIRCLE>ボタンを<r押|お>してください。",
            "Select an item and press <iconCIRCLE> to buy.",
        ),
        (
            0x2F460,
            160,
            "<iconSQUARE>ボタンを<r押|お>すとポイントを<r使|つか>ってボーナスゲームを<r行|おこな>うことができます。",
            "Press <iconSQUARE> to use points to play a bonus game.",
        ),
    ]
    for offset, capacity, source, replacement in etc_slots:
        patch_exact_slot(
            clean_etc,
            output_etc,
            offset=offset,
            capacity=capacity,
            source_text=source,
            replacement_text=replacement,
            label=f"ETC shop UI fix at 0x{offset:X}",
        )
        annotate("PRG/ETC.BIN", offset, capacity, source, replacement)

    # Executable-resident practice values and labels. Each entry is an exact
    # fixed slot in the clean SLPS executable.
    slps_slots = [
        (0x505B48, 8, "楽々", "V.Easy"),
        (0x505B50, 8, "ふつう", "Normal"),
        (0x505B58, 8, "激むず", "V.Hard"),
        (0x505B60, 8, "究極", "Max"),
        (0x505B68, 8, "なし", "None"),
        (0x505B70, 8, "少なめ", "Low"),
        (0x505B78, 8, "多め", "High"),
        (0x505B80, 8, "通常", "Normal"),
        (0x505B98, 8, "回転", "Turn"),
        (0x505BA0, 8, "連打", "Combo"),
        (0x505BB0, 8, "オフ", "Off"),
        (0x505BB8, 8, "オン", "On"),
        (0x505BC8, 8, "半分", "Half"),
        (0x505BE0, 16, "オート", "Auto"),
        (0x505BF0, 8, "手動", "Manual"),
        (0x505BF8, 8, "ＣＯＭ", "COM"),
        (0x505C00, 8, "立ち", "Stand"),
        (0x505C08, 8, "しない", "None"),
        (0x505C10, 8, "単発", "Single"),
        (0x505C18, 8, "コンボ", "Combo"),
        (0x505C20, 8, "奥義", "Ult."),
        (0x505C28, 8, "忍術", "Jutsu"),
        (0x505C30, 8, "する", "Use"),
        (0x505C40, 8, "追う", "Chase"),
        (0x505C60, 16, "乱発", "Frequent"),
        (0x505C70, 8, "難易度", "Level"),
        (0x505CA0, 8, "体力", "Health"),
        (0x505CA8, 8, "状態", "Status"),
        (0x505CB0, 8, "強さ", "Power"),
        (0x505CB8, 8, "攻撃", "Attack"),
        (0x505CC0, 8, "ガード", "Guard"),
        (0x505CC8, 8, "行動", "Action"),
    ]
    for offset, capacity, source, replacement in slps_slots:
        patch_exact_slot(
            clean_slps,
            output_slps,
            offset=offset,
            capacity=capacity,
            source_text=source,
            replacement_text=replacement,
            label=f"SLPS UI fix at 0x{offset:X}",
        )
        annotate("SLPS_258.37", offset, capacity, source, replacement)

    # Common short character-name tables used by shop/collection UI.
    name_slots = [
        (0x506450, "ナルト", "Naruto"),
        (0x506458, "サクラ", "Sakura"),
        (0x506460, "カカシ", "Kakashi"),
        (0x506468, "ネジ", "Neji"),
        (0x506470, "サイ", "Sai"),
        (0x506478, "サスケ", "Sasuke"),
        (0x506480, "シズネ", "Shizune"),
        (0x506488, "アスマ", "Asuma"),
        (0x506490, "テマリ", "Temari"),
        (0x506498, "ヤマト", "Yamato"),
        (0x5064A0, "リー", "Lee"),
        (0x5064A8, "ガイ", "Guy"),
        (0x5064B0, "いの", "Ino"),
        (0x5064B8, "キバ", "Kiba"),
        (0x5064C0, "シノ", "Shino"),
        (0x5064C8, "ヒナタ", "Hinata"),
        (0x506648, "クナイ", "Kunai"),
        (0x506650, "サイ", "Sai"),
        (0x506658, "テマリ", "Temari"),
        (0x506660, "サソリ", "Sasori"),
        (0x506668, "シズネ", "Shizune"),
        (0x506670, "ヤマト", "Yamato"),
    ]
    for offset, source, replacement in name_slots:
        patch_exact_slot(
            clean_slps,
            output_slps,
            offset=offset,
            capacity=8,
            source_text=source,
            replacement_text=replacement,
            label=f"SLPS name fix at 0x{offset:X}",
        )
        annotate("SLPS_258.37", offset, 8, source, replacement)

    # Confirmation choices, including the shop quit prompt shown in the report.
    yes_offsets = [
        0x503110, 0x5031A0, 0x506760, 0x506FA8,
    ]
    no_offsets = [
        0x503118, 0x5031A8, 0x504668, 0x505AD8,
        0x5066A8, 0x506768, 0x506FB0,
    ]
    for offset in yes_offsets:
        patch_exact_bytes(
            clean_slps,
            output_slps,
            offset=offset,
            source_text="はい",
            replacement_text="Yes",
            label=f"SLPS Yes fix at 0x{offset:X}",
        )
        annotate(
            "SLPS_258.37",
            offset,
            len("はい".encode("cp932")) + 1,
            "はい",
            "Yes",
        )
    for offset in no_offsets:
        patch_exact_bytes(
            clean_slps,
            output_slps,
            offset=offset,
            source_text="いいえ",
            replacement_text="No",
            label=f"SLPS No fix at 0x{offset:X}",
        )
        annotate(
            "SLPS_258.37",
            offset,
            len("いいえ".encode("cp932")) + 1,
            "いいえ",
            "No",
        )

    # Exact long official labels do not fit their original 8/16-byte slots.
    # Store them in the unused tail of the translated item-spawn help slot and
    # redirect only the BTL pointers that need them.
    pool_host_offset = 0x20A340
    pool_host_capacity = 240
    host = output_btl[pool_host_offset : pool_host_offset + pool_host_capacity]
    first_nul = host.find(0)
    if first_nul < 0:
        raise ValueError("BTL string-pool host has no NUL terminator")
    cursor = pool_host_offset + first_nul + 1
    pool_limit = pool_host_offset + pool_host_capacity
    pool_offsets: dict[str, int] = {}
    for text in [
        "Difficulty",
        "Ultimate Jutsu",
        "Strength",
        "Guide Ninja Sound",
        "Extra Hit Counter",
        "Ultimate",
    ]:
        payload = text.encode("ascii") + b"\x00"
        if cursor + len(payload) > pool_limit:
            raise ValueError("BTL UI string pool does not fit in host slot")
        output_btl[cursor : cursor + len(payload)] = payload
        pool_offsets[text] = cursor
        annotate("PRG/BTL.BIN", cursor, len(payload), "", text)
        cursor += len(payload)

    pointer_rewrites = {
        0x20A264: "Difficulty",
        0x20A270: "Ultimate Jutsu",
        0x20A7CC: "Ultimate Jutsu",
        0x20A7E0: "Guide Ninja Sound",
        0x20A7E8: "Strength",
        0x20A800: "Extra Hit Counter",
        0x209DD4: "Ultimate",
    }
    for pointer_offset, text in pointer_rewrites.items():
        runtime_pointer = BTL_RUNTIME_BASE + pool_offsets[text]
        output_btl[pointer_offset : pointer_offset + 4] = runtime_pointer.to_bytes(
            4, "little"
        )

    return (
        {
            "btl_direct_slots": len(btl_slots),
            "etc_direct_slots": len(etc_slots),
            "slps_ui_slots": len(slps_slots),
            "slps_name_slots": len(name_slots),
            "slps_yes_no_slots": len(yes_offsets) + len(no_offsets),
            "btl_pointer_rewrites": len(pointer_rewrites),
            "btl_pool_strings": len(pool_offsets),
        },
        text_annotations,
    )


def patch_rows(
    *,
    selected: set[str],
    clean_files: dict[str, bytes],
    output_files: dict[str, bytearray],
    baseline_rows: list[dict],
    official_rows: list[dict],
    texteng: bytes,
) -> tuple[list[dict], dict[str, dict[str, int]]]:
    log: list[dict] = []
    stats = {
        target: {"baseline": 0, "official": 0, "official_changed": 0}
        for target in selected
    }

    for row in baseline_rows:
        target = str(row["file"]).upper()
        if target not in selected:
            continue
        offset = int(row["offset"])
        capacity = int(row["capacity"])
        source_text = str(row["source"])
        translation = str(row["translation"])
        row_id = str(row.get("id", ""))
        label = f"baseline {target} {row_id or hex(offset)}"
        source_bytes = verify_source_literal(
            clean_files[target],
            offset=offset,
            source_text=source_text,
            capacity=capacity,
            label=label,
        )
        try:
            replacement = translation.encode("cp932")
        except UnicodeEncodeError as exc:
            raise ValueError(f"{label}: translation is not CP932-encodable") from exc
        write_slot(output_files[target], offset, capacity, replacement)
        stats[target]["baseline"] += 1
        log.append(
            {
                "phase": "baseline",
                "file": target,
                "id": row_id,
                "offset_hex": f"0x{offset:X}",
                "capacity": capacity,
                "source": source_text,
                "translation": translation,
                "source_bytes": len(source_bytes),
                "replacement_bytes": len(replacement),
                "texteng_offset_hex": "",
            }
        )

    for index, row in enumerate(official_rows, 1):
        target = str(row["file"]).upper()
        if target not in selected:
            continue
        offset = int(row["offset"])
        capacity = int(row["capacity"])
        source_text = str(row["source"])
        texteng_offset = int(row["texteng_offset"])
        label = f"official {target} #{index} at 0x{offset:X}"
        source_bytes = verify_source_literal(
            clean_files[target],
            offset=offset,
            source_text=source_text,
            capacity=capacity,
            label=label,
        )
        official_text = read_ascii_z(texteng, texteng_offset, label)
        replacement = official_text.encode("ascii")
        before = bytes(output_files[target][offset : offset + capacity])
        write_slot(output_files[target], offset, capacity, replacement)
        after = bytes(output_files[target][offset : offset + capacity])
        stats[target]["official"] += 1
        if after != before:
            stats[target]["official_changed"] += 1
        log.append(
            {
                "phase": "official_texteng",
                "file": target,
                "id": "",
                "offset_hex": f"0x{offset:X}",
                "capacity": capacity,
                "source": source_text,
                "translation": official_text,
                "source_bytes": len(source_bytes),
                "replacement_bytes": len(replacement),
                "texteng_offset_hex": f"0x{texteng_offset:X}",
            }
        )

    return log, stats


def write_csv(path: Path, rows: Iterable[dict]) -> None:
    rows = list(rows)
    if not rows:
        path.write_text("", encoding="utf-8-sig")
        return
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def diff_rows(
    path: str,
    clean: bytes,
    output: bytes,
    text_annotations: Sequence[dict[str, object]] = (),
) -> list[dict[str, str]]:
    if len(clean) != len(output):
        raise ValueError(f"Cannot emit fixed-offset patches for size-changed file: {path}")

    normalized_path = normalize_path(path)
    annotations = [
        annotation
        for annotation in text_annotations
        if normalize_path(str(annotation["path"])) == normalized_path
    ]

    changed_ranges: list[tuple[int, int]] = []
    start: Optional[int] = None
    for index, (before, after) in enumerate(zip(clean, output)):
        if before != after and start is None:
            start = index
        elif before == after and start is not None:
            changed_ranges.append((start, index))
            start = None
    if start is not None:
        changed_ranges.append((start, len(clean)))

    rows: list[dict[str, str]] = []
    for range_start, range_end in changed_ranges:
        boundaries = {range_start, range_end}
        for annotation in annotations:
            annotation_start = int(annotation["start"])
            annotation_end = int(annotation["end"])
            if range_start < annotation_end and range_end > annotation_start:
                boundaries.add(max(range_start, annotation_start))
                boundaries.add(min(range_end, annotation_end))

        ordered = sorted(boundaries)
        for segment_start, segment_end in zip(ordered, ordered[1:]):
            if segment_start >= segment_end:
                continue
            matching = [
                annotation
                for annotation in annotations
                if segment_start < int(annotation["end"])
                and segment_end > int(annotation["start"])
            ]
            if matching:
                # Later operations override earlier ones at the same location.
                annotation = matching[-1]
                source_text = str(annotation["source_text"])
                replacement_text = str(annotation["replacement_text"])
            else:
                source_text = ""
                replacement_text = ""

            rows.append(
                {
                    "path": path,
                    "offset": f"0x{segment_start:X}",
                    "expected_hex": clean[segment_start:segment_end].hex().upper(),
                    "replacement_hex": output[segment_start:segment_end].hex().upper(),
                    "source_text": source_text,
                    "replacement_text": replacement_text,
                }
            )
    return rows


def write_translation_tsv(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        raise ValueError("No translation patches were generated")
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "path",
                    "offset",
                    "expected_hex",
                    "replacement_hex",
                    "source_text",
                    "replacement_text",
                ],
                delimiter="\t",
                lineterminator="\n",
            )
            writer.writeheader()
            writer.writerows(rows)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build one NA2 translation TSV from clean NA2 and official UN5 sources"
    )
    parser.add_argument("--na2-iso", type=Path)
    parser.add_argument("--na2-folder", type=Path)
    parser.add_argument("--un5-iso", type=Path)
    parser.add_argument("--un5-folder", type=Path)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--apply", default="BTL,ETC")
    parser.add_argument("--no-strict-hash", action="store_true")
    args = parser.parse_args()

    selected_list = parse_apply(args.apply)
    selected = set(selected_list)
    na2 = source_from(args.na2_folder, args.na2_iso, "NA2")
    un5 = source_from(args.un5_folder, args.un5_iso, "UN5")

    clean_files = {
        target: na2.read(FILE_SPECS[target][1], f"NA2 {FILE_SPECS[target][0]}")
        for target in selected
    }
    clean_slps = na2.read(SLPS_CANDIDATES, "NA2 SLPS_258.37")
    texteng = un5.read(TEXTENG_CANDIDATES, "UN5 PRG/TEXTENG.BIN")

    actual_hashes = {
        "NA2_BTL": sha1(clean_files["BTL"]) if "BTL" in selected else None,
        "NA2_ETC": sha1(clean_files["ETC"]) if "ETC" in selected else None,
        "NA2_SLPS": sha1(clean_slps),
        "UN5_TEXTENG": sha1(texteng),
    }
    if not args.no_strict_hash:
        for key, expected in EXPECTED_SHA1.items():
            actual = actual_hashes.get(key)
            if actual is not None and actual != expected:
                raise ValueError(f"Unexpected {key} SHA-1: {actual}; expected {expected}")

    baseline_rows = json.loads(
        (args.data_root / "baseline.json").read_text(encoding="utf-8")
    )
    official_rows = json.loads(
        (args.data_root / "texteng_map.json").read_text(encoding="utf-8")
    )

    output_files = {target: bytearray(clean_files[target]) for target in selected}
    output_slps = bytearray(clean_slps)
    patch_log, stats = patch_rows(
        selected=selected,
        clean_files=clean_files,
        output_files=output_files,
        baseline_rows=baseline_rows,
        official_rows=official_rows,
        texteng=texteng,
    )
    text_annotations: list[dict[str, object]] = [
        {
            "path": FILE_SPECS[str(entry["file"]).upper()][0],
            "start": int(str(entry["offset_hex"]), 16),
            "end": int(str(entry["offset_hex"]), 16) + int(entry["capacity"]),
            "source_text": str(entry["source"]),
            "replacement_text": str(entry["translation"]),
        }
        for entry in patch_log
    ]

    runtime_stats: dict[str, int] = {}
    if {"BTL", "ETC"}.issubset(selected):
        runtime_stats, runtime_annotations = apply_runtime_ui_fixes(
            clean_btl=clean_files["BTL"],
            output_btl=output_files["BTL"],
            clean_etc=clean_files["ETC"],
            output_etc=output_files["ETC"],
            clean_slps=clean_slps,
            output_slps=output_slps,
        )
        text_annotations.extend(runtime_annotations)

    rows: list[dict[str, str]] = []
    for target in selected_list:
        rows.extend(
            diff_rows(
                FILE_SPECS[target][0],
                clean_files[target],
                bytes(output_files[target]),
                text_annotations,
            )
        )
    if runtime_stats:
        rows.extend(
            diff_rows(
                "SLPS_258.37",
                clean_slps,
                bytes(output_slps),
                text_annotations,
            )
        )

    run_id = dt.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3] + f"_pid{os.getpid()}"
    output_dir = args.output_directory.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    final_path = output_dir / f"NA2_APPLY__TRANSLATION__{run_id}.tsv"
    if final_path.exists():
        raise FileExistsError(final_path)
    write_translation_tsv(final_path, rows)

    run_root = args.work_root / "runs" / run_id
    run_root.mkdir(parents=True, exist_ok=False)
    hashes = {
        FILE_SPECS[target][0]: {
            "source_sha1": sha1(clean_files[target]),
            "translated_sha1": sha1(bytes(output_files[target])),
            "size": len(output_files[target]),
        }
        for target in selected_list
    }
    if runtime_stats:
        hashes["SLPS_258.37"] = {
            "source_sha1": sha1(clean_slps),
            "translated_sha1": sha1(bytes(output_slps)),
            "size": len(output_slps),
        }
    summary = {
        "mode": "single post-composition translation TSV",
        "run_id": run_id,
        "translation_tsv": str(final_path),
        "patch_rows": len(rows),
        "targets": selected_list,
        "source_hashes": actual_hashes,
        "translated_file_hashes": hashes,
        "stats": stats,
        "runtime_ui_fixes": runtime_stats,
    }
    (run_root / "build_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print("Built NA2 translation TSV:")
    print(f"  {final_path}")
    print(f"  patch rows: {len(rows)}")
    for path, info in hashes.items():
        print(
            f"  {path}: {info['size']} bytes, translated SHA-1 "
            f"{info['translated_sha1']}"
        )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
