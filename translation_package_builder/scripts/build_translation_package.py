#!/usr/bin/env python3
"""Build a self-contained NA2 translation replacement package.

Reads clean PRG/BTL.BIN and PRG/ETC.BIN directly from the authoritative
NA2 ISO, applies the bundled approved TSV rows in place, and writes:

    NA2_APPLY__TRANSLATION__*.zip

The ZIP contains exactly:

    PRG/BTL.BIN
    PRG/ETC.BIN

This tool never writes or patches an ISO.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import re
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

SECTOR = 2048
EXPECTED_SHA1 = {
    "NA2_BTL.BIN": "bf7fc7331a2a4f34fc90b84b45772ae1f6bcab03",
    "NA2_ETC.BIN": "dcfffd7eb14e484a4c0fbc195599a0b45a9a11c1",
}
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BTL_TSV = ROOT / "translations" / "apply" / "btl_apply.tsv"
DEFAULT_ETC_TSV = ROOT / "translations" / "apply" / "etc_apply.tsv"
EXPECTED_ZIP_PATHS = ("PRG/BTL.BIN", "PRG/ETC.BIN")


@dataclass(frozen=True)
class IsoRecord:
    path: str
    raw_name: str
    extent: int
    size: int
    flags: int

    @property
    def is_dir(self) -> bool:
        return (self.flags & 0x02) != 0

    @property
    def byte_offset(self) -> int:
        return self.extent * SECTOR


class Iso9660:
    def __init__(self, iso_path: Path) -> None:
        self.iso_path = iso_path
        self._data = iso_path.read_bytes()
        self.records: Dict[str, IsoRecord] = {}
        self.root_record: Optional[IsoRecord] = None
        self._parse()

    def _parse_dir_record_at(self, data: bytes, off: int) -> Tuple[Optional[IsoRecord], int]:
        if off >= len(data):
            return None, 0
        length = data[off]
        if length == 0:
            return None, 0
        rec = data[off : off + length]
        if len(rec) < 34:
            raise ValueError(f"Bad short directory record at offset {off}")
        extent = int.from_bytes(rec[2:6], "little")
        size = int.from_bytes(rec[10:14], "little")
        flags = rec[25]
        name_len = rec[32]
        name_bytes = rec[33 : 33 + name_len]
        if name_bytes == b"\x00":
            raw_name = "."
        elif name_bytes == b"\x01":
            raw_name = ".."
        else:
            raw_name = name_bytes.decode("ascii", errors="replace")
        return IsoRecord("", raw_name, extent, size, flags), length

    @staticmethod
    def _norm_component(raw: str) -> str:
        return raw.split(";", 1)[0].upper()

    def _parse_directory(self, rec: IsoRecord, prefix: str) -> None:
        start = rec.byte_offset
        end = start + rec.size
        data = self._data[start:end]
        off = 0
        while off < len(data):
            length = data[off]
            if length == 0:
                off = ((off // SECTOR) + 1) * SECTOR
                continue
            child, used = self._parse_dir_record_at(data, off)
            if child is None or used == 0:
                break
            off += used
            if child.raw_name in (".", ".."):
                continue
            component = self._norm_component(child.raw_name)
            path = f"{prefix}/{component}" if prefix else component
            full = IsoRecord(path, child.raw_name, child.extent, child.size, child.flags)
            self.records[path] = full
            if full.is_dir:
                self._parse_directory(full, path)

    def _parse(self) -> None:
        pvd = None
        for sector in range(16, min(128, len(self._data) // SECTOR)):
            off = sector * SECTOR
            if self._data[off] == 1 and self._data[off + 1 : off + 6] == b"CD001":
                pvd = self._data[off : off + SECTOR]
                break
        if pvd is None:
            raise ValueError(f"{self.iso_path}: no ISO9660 Primary Volume Descriptor found")
        root_rec, _ = self._parse_dir_record_at(pvd, 156)
        if root_rec is None:
            raise ValueError("Could not parse ISO root directory record")
        root_rec = IsoRecord("", "/", root_rec.extent, root_rec.size, root_rec.flags)
        self.root_record = root_rec
        self._parse_directory(root_rec, "")

    def read_file(self, rec: IsoRecord) -> bytes:
        if rec.is_dir:
            raise ValueError(f"{rec.path} is a directory")
        start = rec.byte_offset
        return self._data[start : start + rec.size]

    def find_file(self, candidates: Iterable[str], label: str) -> IsoRecord:
        normalized = [c.strip("/").replace("\\", "/").upper() for c in candidates]
        for candidate in normalized:
            rec = self.records.get(candidate)
            if rec is not None and not rec.is_dir:
                return rec
        wanted = {c.rsplit("/", 1)[-1] for c in normalized}
        matches = [r for p, r in self.records.items() if not r.is_dir and p.rsplit("/", 1)[-1] in wanted]
        if len(matches) == 1:
            return matches[0]
        if matches:
            details = "\n".join(f"  {m.path} size=0x{m.size:X}" for m in matches)
            raise FileNotFoundError(f"Ambiguous {label}:\n{details}")
        checked = "\n".join(f"  {c}" for c in normalized)
        raise FileNotFoundError(f"Could not find {label}. Tried:\n{checked}")


def sha1_bytes(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()


def check_sha1(data: bytes, expected: str, label: str, strict: bool) -> str:
    actual = sha1_bytes(data)
    if actual.lower() != expected.lower():
        message = f"SHA-1 mismatch for {label}: expected {expected}, actual {actual}"
        if strict:
            raise RuntimeError(message)
        print("WARNING: " + message, file=sys.stderr)
    return actual


def cp932_bytes(text: str) -> bytes:
    try:
        return text.encode("cp932")
    except UnicodeEncodeError as exc:
        raise ValueError(f"Text is not CP932-encodable: {text!r}: {exc}") from exc


ASSET_TOKEN_RE = re.compile(
    r"(?ix)"
    r"(^|\b)(ANM|OBJ|TEX|CMP|BGM|SE|SND|EFFECT|EFF|MDL|MOT|CHR|STAGE|SPR|GIM|TIM|CCS)_[A-Za-z0-9_%.-]+"
    r"|\b[a-z0-9_./-]+\.ccs\b"
    r"|\b[a-z0-9_./-]+\.(anm|gim|tim|bin|tm2|mdl|mot|seq|vag)\b"
    r"|\bcha\d{2}[a-z]?\b"
    r"|\bton0%d\b"
    r"|\beffect0x\.ccs\b"
    r"|\b(spine|trall)\b"
)


def reject_translation_candidate(text: str, source_text: str = "") -> str:
    value = (text or "").strip()
    if not value:
        return "empty_candidate"
    if ASSET_TOKEN_RE.search(value):
        return "asset_or_internal_identifier"
    if "%" in value and "%" not in (source_text or ""):
        return "unsafe_ascii_percent_added"
    if re.fullmatch(r"[a-z]{2,}\d*[a-z]?", value) and " " not in value:
        return "identifier_like_lowercase_token"
    return ""


def read_tsv(path: Path) -> List[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, rows: List[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: List[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                fields.append(key)
                seen.add(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def common_row_values(row: dict[str, str]) -> tuple[str, str, str, str, str]:
    return (
        row.get("id", ""),
        row.get("offset_hex", "") or row.get("offset", ""),
        row.get("source_japanese") or row.get("source_text") or row.get("ja_text") or row.get("old_text") or "",
        row.get("chosen_translation") or row.get("new_text") or row.get("en_text") or row.get("proposed_translation") or "",
        (row.get("enabled") or row.get("apply") or "yes").strip().lower(),
    )


def patch_btl_inplace(blob: bytearray, rows: List[dict[str, str]]) -> Tuple[List[dict[str, str]], dict[str, int]]:
    log: List[dict[str, str]] = []
    stats = {"rows": 0, "patched": 0, "skipped": 0}
    for row in rows:
        stats["rows"] += 1
        rid, offset_hex, source_text, new_text, enabled = common_row_values(row)
        entry = {
            "id": rid,
            "file_label": "BTL",
            "offset_hex": offset_hex,
            "source_text": source_text,
            "new_text": new_text,
            "status": "",
            "reason": "",
            "source_cp932_bytes": "",
            "new_cp932_bytes": "",
            "old_expected_cp932_hex": "",
            "old_actual_hex": "",
            "old_actual_nul_hex": "",
        }
        if enabled in ("0", "false", "no", "n", "skip", "disabled"):
            entry.update(status="skipped", reason="disabled_by_tsv")
        else:
            reason = reject_translation_candidate(new_text, source_text)
            if reason:
                entry.update(status="skipped", reason=reason)
            else:
                try:
                    offset = int(offset_hex, 16)
                    old_data = cp932_bytes(source_text)
                    new_data = cp932_bytes(new_text)
                    old_len = len(old_data)
                    entry["source_cp932_bytes"] = str(old_len)
                    entry["new_cp932_bytes"] = str(len(new_data))
                    entry["old_expected_cp932_hex"] = old_data.hex(" ")
                    write_len = old_len + 1
                    if offset < 0 or offset + write_len > len(blob):
                        raise ValueError(f"literal_region_outside_btl_size_0x{len(blob):X}")
                    actual_old = bytes(blob[offset : offset + old_len])
                    actual_nul = blob[offset + old_len]
                    entry["old_actual_hex"] = actual_old.hex(" ")
                    entry["old_actual_nul_hex"] = f"0x{actual_nul:02X}"
                    if actual_old != old_data or actual_nul != 0:
                        raise ValueError("original_literal_mismatch_or_missing_nul")
                    if len(new_data) > old_len:
                        raise ValueError("replacement_longer_than_original_literal_under_safe_policy")
                    old_region = bytes(blob[offset : offset + write_len])
                    blob[offset : offset + write_len] = new_data + b"\x00" + b"\x00" * (old_len - len(new_data))
                    entry.update(status="patched", reason="ok", old_region_sha1=sha1_bytes(old_region))
                except Exception as exc:
                    entry.update(status="skipped", reason=str(exc))
        stats[entry["status"]] += 1
        log.append(entry)
    return log, stats


def patch_etc_inplace(blob: bytearray, rows: List[dict[str, str]]) -> Tuple[List[dict[str, str]], dict[str, int]]:
    log: List[dict[str, str]] = []
    stats = {"rows": 0, "patched": 0, "skipped": 0}
    for row in rows:
        stats["rows"] += 1
        rid, offset_hex, source_text, new_text, enabled = common_row_values(row)
        entry = {
            "id": rid,
            "file_label": "ETC",
            "offset_hex": offset_hex,
            "slot_capacity": row.get("slot_capacity", ""),
            "source_text": source_text,
            "new_text": new_text,
            "status": "",
            "reason": "",
            "source_cp932_bytes": "",
            "new_cp932_bytes": "",
            "old_expected_cp932_hex": "",
            "old_actual_hex": "",
            "old_actual_nul_hex": "",
        }
        if enabled in ("0", "false", "no", "n", "skip", "disabled"):
            entry.update(status="skipped", reason="disabled_by_tsv")
        else:
            reason = reject_translation_candidate(new_text, source_text)
            if reason:
                entry.update(status="skipped", reason=reason)
            else:
                try:
                    offset = int(offset_hex, 16)
                    old_data = cp932_bytes(source_text)
                    new_data = cp932_bytes(new_text)
                    old_len = len(old_data)
                    entry["source_cp932_bytes"] = str(old_len)
                    entry["new_cp932_bytes"] = str(len(new_data))
                    entry["old_expected_cp932_hex"] = old_data.hex(" ")
                    raw_capacity = (row.get("slot_capacity") or "").strip()
                    slot_capacity = int(raw_capacity, 0) if raw_capacity else old_len + 1
                    entry["slot_capacity"] = str(slot_capacity)
                    if slot_capacity < old_len + 1:
                        raise ValueError("slot_capacity_smaller_than_original_literal_plus_nul")
                    if offset < 0 or offset + slot_capacity > len(blob):
                        raise ValueError(f"literal_region_outside_ETC_size_0x{len(blob):X}")
                    actual_old = bytes(blob[offset : offset + old_len])
                    actual_nul = blob[offset + old_len]
                    entry["old_actual_hex"] = actual_old.hex(" ")
                    entry["old_actual_nul_hex"] = f"0x{actual_nul:02X}"
                    if actual_old != old_data or actual_nul != 0:
                        raise ValueError("original_literal_mismatch_or_missing_nul")
                    if len(new_data) > slot_capacity - 1:
                        raise ValueError("replacement_longer_than_declared_slot_capacity")
                    old_region = bytes(blob[offset : offset + slot_capacity])
                    blob[offset : offset + slot_capacity] = new_data + b"\x00" + b"\x00" * (slot_capacity - len(new_data) - 1)
                    entry.update(status="patched", reason="ok", old_region_sha1=sha1_bytes(old_region))
                except Exception as exc:
                    entry.update(status="skipped", reason=str(exc))
        stats[entry["status"]] += 1
        log.append(entry)
    return log, stats


def validate_zip(path: Path, expected: Dict[str, bytes]) -> Dict[str, str]:
    with zipfile.ZipFile(path, "r") as archive:
        infos = archive.infolist()
        names = [info.filename.replace("\\", "/") for info in infos]
        if names != list(EXPECTED_ZIP_PATHS):
            raise RuntimeError(f"Unexpected ZIP contents/order: {names}")
        if len({name.upper() for name in names}) != len(names):
            raise RuntimeError("ZIP contains duplicate normalized paths")
        hashes: Dict[str, str] = {}
        for info, name in zip(infos, names):
            if info.is_dir():
                raise RuntimeError(f"Unexpected directory entry in ZIP: {name}")
            data = archive.read(info)
            if data != expected[name]:
                raise RuntimeError(f"ZIP bytes differ from generated file: {name}")
            hashes[name] = sha1_bytes(data)
        return hashes


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build NA2_APPLY__TRANSLATION__*.zip from clean NA2.iso and current BTL/ETC TSVs.")
    parser.add_argument("--na2-iso", required=True, type=Path)
    parser.add_argument("--output-directory", required=True, type=Path)
    parser.add_argument("--btl-tsv", type=Path, default=DEFAULT_BTL_TSV)
    parser.add_argument("--etc-tsv", type=Path, default=DEFAULT_ETC_TSV)
    parser.add_argument("--no-strict-hash", action="store_true")
    args = parser.parse_args(argv)

    na2_iso = args.na2_iso.resolve()
    output_directory = args.output_directory.resolve()
    btl_tsv = args.btl_tsv.resolve()
    etc_tsv = args.etc_tsv.resolve()
    strict = not args.no_strict_hash

    if not na2_iso.is_file():
        raise FileNotFoundError(f"Clean NA2 ISO not found: {na2_iso}")
    if not btl_tsv.is_file():
        raise FileNotFoundError(f"BTL apply TSV not found: {btl_tsv}")
    if not etc_tsv.is_file():
        raise FileNotFoundError(f"ETC apply TSV not found: {etc_tsv}")

    run_id = dt.datetime.now().strftime("%Y%m%d_%H%M%S_%f") + f"_pid{os.getpid()}"
    run_dir = ROOT / "work" / "runs" / run_id
    logs_dir = run_dir / "logs"
    package_root = run_dir / "package"
    prg_dir = package_root / "PRG"
    prg_dir.mkdir(parents=True, exist_ok=False)
    logs_dir.mkdir(parents=True, exist_ok=False)

    print(f"Reading clean NA2 ISO: {na2_iso}")
    iso = Iso9660(na2_iso)
    btl_rec = iso.find_file(["PRG/BTL.BIN"], "NA2 PRG/BTL.BIN")
    etc_rec = iso.find_file(["PRG/ETC.BIN"], "NA2 PRG/ETC.BIN")
    btl_source = iso.read_file(btl_rec)
    etc_source = iso.read_file(etc_rec)

    source_hashes = {
        "PRG/BTL.BIN": check_sha1(btl_source, EXPECTED_SHA1["NA2_BTL.BIN"], "NA2 BTL.BIN", strict),
        "PRG/ETC.BIN": check_sha1(etc_source, EXPECTED_SHA1["NA2_ETC.BIN"], "NA2 ETC.BIN", strict),
    }

    btl_rows = read_tsv(btl_tsv)
    etc_rows = read_tsv(etc_tsv)
    btl_output = bytearray(btl_source)
    etc_output = bytearray(etc_source)
    btl_log, btl_stats = patch_btl_inplace(btl_output, btl_rows)
    etc_log, etc_stats = patch_etc_inplace(etc_output, etc_rows)

    if len(btl_output) != btl_rec.size:
        raise RuntimeError("Generated BTL.BIN size differs from source ISO record size")
    if len(etc_output) != etc_rec.size:
        raise RuntimeError("Generated ETC.BIN size differs from source ISO record size")

    btl_path = prg_dir / "BTL.BIN"
    etc_path = prg_dir / "ETC.BIN"
    btl_path.write_bytes(btl_output)
    etc_path.write_bytes(etc_output)

    expected = {
        "PRG/BTL.BIN": bytes(btl_output),
        "PRG/ETC.BIN": bytes(etc_output),
    }
    generated_hashes = {name: sha1_bytes(data) for name, data in expected.items()}

    write_tsv(logs_dir / "btl_patch_log.tsv", btl_log)
    write_tsv(logs_dir / "btl_skipped_rows.tsv", [row for row in btl_log if row.get("status") == "skipped"])
    write_tsv(logs_dir / "etc_patch_log.tsv", etc_log)
    write_tsv(logs_dir / "etc_skipped_rows.tsv", [row for row in etc_log if row.get("status") == "skipped"])

    output_directory.mkdir(parents=True, exist_ok=True)
    final_name = f"NA2_APPLY__TRANSLATION__{run_id}.zip"
    final_path = output_directory / final_name
    temp_path = output_directory / f".NA2_TRANSLATION_BUILD_{run_id}.tmp.zip"
    if final_path.exists() or temp_path.exists():
        raise FileExistsError(f"Refusing to overwrite existing package path for run {run_id}")

    try:
        with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            archive.writestr("PRG/BTL.BIN", expected["PRG/BTL.BIN"])
            archive.writestr("PRG/ETC.BIN", expected["PRG/ETC.BIN"])
        zip_hashes = validate_zip(temp_path, expected)
        os.replace(temp_path, final_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()

    summary = {
        "tool": "NA2 Translation Package Builder v1",
        "source_iso": str(na2_iso),
        "output_zip": str(final_path),
        "btl_tsv": str(btl_tsv),
        "etc_tsv": str(etc_tsv),
        "source_hashes": source_hashes,
        "generated_hashes": generated_hashes,
        "zip_hashes": zip_hashes,
        "source_record_sizes": {
            "PRG/BTL.BIN": btl_rec.size,
            "PRG/ETC.BIN": etc_rec.size,
        },
        "btl_stats": btl_stats,
        "etc_stats": etc_stats,
        "zip_paths": list(EXPECTED_ZIP_PATHS),
    }
    (logs_dir / "build_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("")
    print("TRANSLATION PACKAGE CREATED")
    print(f"  {final_path}")
    for name in EXPECTED_ZIP_PATHS:
        print(f"  {name}  size={len(expected[name])}  sha1={generated_hashes[name]}")
    print(f"  BTL rows: patched={btl_stats['patched']} skipped={btl_stats['skipped']}")
    print(f"  ETC rows: patched={etc_stats['patched']} skipped={etc_stats['skipped']}")
    print(f"  Logs: {logs_dir}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
