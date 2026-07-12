#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import fnmatch
import os
import re
import shutil
import sys
import zipfile
from pathlib import Path

from iso9660_tools import Iso9660, SECTOR


def normalize(path: str) -> str:
    return path.replace("\\", "/").strip("/").upper()


def normalize_category(value: str) -> str:
    category = "".join(char if char.isalnum() else "_" for char in value.strip().upper())
    category = "_".join(part for part in category.split("_") if part)
    if not category:
        raise ValueError("Empty package category")
    return category


def filename_release_key(path: Path) -> tuple[int, str, int, str]:
    name = path.name.upper()
    timestamp_match = re.search(r"(?<!\d)(20\d{6})[_-](\d{6})(?!\d)", name)
    version_match = re.search(r"(?:^|[_-])V(\d+)(?:[_-]|\.|$)", name)
    timestamp = "" if timestamp_match is None else "".join(timestamp_match.groups())
    version = -1 if version_match is None else int(version_match.group(1))
    return (int(bool(timestamp)), timestamp, version, name)


def latest_file(directory: Path, pattern: str) -> Path:
    pattern_upper = pattern.upper()
    matches = [
        path
        for path in directory.iterdir()
        if path.is_file() and fnmatch.fnmatch(path.name.upper(), pattern_upper)
    ]
    if not matches:
        raise FileNotFoundError(f"No file matches {directory / pattern}")
    return max(matches, key=filename_release_key)


def initialize(source_iso: Path, output_iso: Path) -> None:
    temporary = output_iso.with_suffix(output_iso.suffix + ".initializing")
    if temporary.exists():
        temporary.unlink()
    print("Initializing output with one full source ISO copy...")
    shutil.copyfile(source_iso, temporary)
    os.replace(temporary, output_iso)


def directory_record_offset(iso: Iso9660, path: str) -> int:
    parent_path, _, leaf = path.rpartition("/")
    parent = iso.by_path.get(parent_path)
    if parent is None or not parent.is_dir:
        raise RuntimeError(f"Parent directory not found for {path}")
    data = iso.read_file(parent)
    offset = 0
    while offset < len(data):
        length = data[offset]
        if length == 0:
            offset = ((offset // SECTOR) + 1) * SECTOR
            continue
        raw = data[offset : offset + length]
        name_length = raw[32]
        name_bytes = raw[33 : 33 + name_length]
        if name_bytes not in (b"\x00", b"\x01"):
            name = name_bytes.decode("ascii").split(";", 1)[0].upper()
            if name == leaf:
                return parent.byte_offset + offset
        offset += length
    raise RuntimeError(f"Directory record not found for {path}")


def write_both_endian_32(output, offset: int, value: int) -> None:
    output.seek(offset)
    output.write(value.to_bytes(4, "little"))
    output.write(value.to_bytes(4, "big"))


def update_volume_space_size(output, sectors: int) -> None:
    for sector in range(16, 128):
        offset = sector * SECTOR
        output.seek(offset)
        descriptor = output.read(SECTOR)
        if len(descriptor) != SECTOR or descriptor[1:6] != b"CD001":
            continue
        if descriptor[0] == 1:
            write_both_endian_32(output, offset + 80, sectors)
        if descriptor[0] == 255:
            break


def load_zip_payloads(
    package: Path,
    *,
    source: Iso9660,
    payloads: dict[str, bytearray],
    owners: dict[str, str],
) -> list[str]:
    applied: list[str] = []
    seen: set[str] = set()
    with zipfile.ZipFile(package) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            path = normalize(info.filename)
            if path in seen:
                raise RuntimeError(f"Duplicate ZIP path in {package.name}: {path}")
            seen.add(path)
            if path in owners:
                raise RuntimeError(
                    f"Selected ZIP packages replace the same ISO path: {path} "
                    f"({owners[path]} and {package.name})"
                )
            record = source.by_path.get(path)
            if record is None or record.is_dir:
                raise RuntimeError(f"ZIP path is not in the clean source ISO: {path}")
            payloads[path] = bytearray(archive.read(info))
            owners[path] = package.name
            applied.append(path)
    if not applied:
        raise RuntimeError(f"Package contains no files: {package}")
    return applied


def parse_offset(value: str, *, row_number: int) -> int:
    text = value.strip()
    if not text:
        raise ValueError(f"Translation TSV row {row_number}: empty offset")
    try:
        return int(text, 0)
    except ValueError as exc:
        raise ValueError(
            f"Translation TSV row {row_number}: invalid offset {value!r}"
        ) from exc


def parse_hex(value: str, *, field: str, row_number: int) -> bytes:
    compact = "".join(value.split())
    if not compact:
        raise ValueError(f"Translation TSV row {row_number}: empty {field}")
    if len(compact) % 2:
        raise ValueError(f"Translation TSV row {row_number}: odd-length {field}")
    try:
        return bytes.fromhex(compact)
    except ValueError as exc:
        raise ValueError(
            f"Translation TSV row {row_number}: invalid {field}"
        ) from exc


def apply_translation_tsv(
    table: Path,
    *,
    source: Iso9660,
    payloads: dict[str, bytearray],
    owners: dict[str, str],
) -> tuple[int, list[str]]:
    patch_fields = ["path", "offset", "expected_hex", "replacement_hex"]
    descriptive_fields = patch_fields + ["source_text", "replacement_text"]
    patched_paths: list[str] = []
    patched_set: set[str] = set()
    row_count = 0

    with table.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fields = reader.fieldnames or []
        if fields not in (patch_fields, descriptive_fields):
            raise ValueError(
                "Translation TSV columns must be either: "
                + "\t".join(patch_fields)
                + " or "
                + "\t".join(descriptive_fields)
            )

        for row_number, row in enumerate(reader, 2):
            if not any((value or "").strip() for value in row.values()):
                continue
            path = normalize(row["path"])
            record = source.by_path.get(path)
            if record is None or record.is_dir:
                raise RuntimeError(
                    f"Translation TSV row {row_number}: path is not in the clean source ISO: {path}"
                )
            if path not in payloads:
                payloads[path] = bytearray(source.read_file(record))
                owners[path] = table.name

            offset = parse_offset(row["offset"], row_number=row_number)
            expected = parse_hex(
                row["expected_hex"], field="expected_hex", row_number=row_number
            )
            replacement = parse_hex(
                row["replacement_hex"], field="replacement_hex", row_number=row_number
            )
            if len(expected) != len(replacement):
                raise ValueError(
                    f"Translation TSV row {row_number}: expected/replacement lengths differ "
                    f"({len(expected)} != {len(replacement)})"
                )

            data = payloads[path]
            end = offset + len(expected)
            if offset < 0 or end > len(data):
                raise ValueError(
                    f"Translation TSV row {row_number}: range 0x{offset:X}-0x{end:X} "
                    f"is outside {path} ({len(data)} bytes)"
                )
            actual = bytes(data[offset:end])
            if actual != expected:
                raise RuntimeError(
                    f"Translation conflict in {table.name}, row {row_number}, {path} "
                    f"at 0x{offset:X}: expected {expected.hex().upper()}, "
                    f"found {actual.hex().upper()}"
                )
            data[offset:end] = replacement
            owners[path] = table.name
            row_count += 1
            if path not in patched_set:
                patched_set.add(path)
                patched_paths.append(path)

    if row_count == 0:
        raise RuntimeError(f"Translation TSV contains no patch rows: {table}")
    return row_count, patched_paths


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Recreate the output ISO, compose the newest selected NA2 ZIP packages, "
            "then apply the newest translation TSV last."
        )
    )
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--downloads", required=True, type=Path)
    parser.add_argument("--package", action="append", default=[])
    args = parser.parse_args()

    source_iso = args.source.resolve()
    output_iso = args.output.resolve()
    downloads = args.downloads.resolve()
    if not source_iso.is_file():
        raise FileNotFoundError(source_iso)
    if not downloads.is_dir():
        raise FileNotFoundError(downloads)
    if source_iso == output_iso:
        raise ValueError("Source and output ISO paths must differ")

    requested = args.package or ["Font", "Translation"]
    categories: list[str] = []
    for value in requested:
        category = normalize_category(value)
        if category not in categories:
            categories.append(category)

    zip_categories = [category for category in categories if category != "TRANSLATION"]
    translation_selected = "TRANSLATION" in categories

    packages: list[tuple[str, Path]] = []
    for category in zip_categories:
        package = latest_file(downloads, f"NA2_APPLY__{category}__*.zip")
        packages.append((category, package))

    translation_table = None
    if translation_selected:
        translation_table = latest_file(
            downloads, "NA2_APPLY__TRANSLATION__*.tsv"
        )

    source = Iso9660(source_iso)
    payloads: dict[str, bytearray] = {}
    owners: dict[str, str] = {}
    package_paths: dict[str, list[str]] = {}

    for category, package in packages:
        package_paths[category] = load_zip_payloads(
            package,
            source=source,
            payloads=payloads,
            owners=owners,
        )

    translated_rows = 0
    translated_paths: list[str] = []
    if translation_table is not None:
        translated_rows, translated_paths = apply_translation_tsv(
            translation_table,
            source=source,
            payloads=payloads,
            owners=owners,
        )

    if not payloads:
        raise RuntimeError("No package files or translation patches were selected")

    output_iso.parent.mkdir(parents=True, exist_ok=True)
    initialize(source_iso, output_iso)
    current = Iso9660(output_iso)
    with output_iso.open("r+b") as output:
        for path, data in payloads.items():
            record = current.by_path[path]
            payload = bytes(data)
            if len(payload) == record.size:
                output.seek(record.byte_offset)
                output.write(payload)
                continue

            output.seek(0, os.SEEK_END)
            extent = (output.tell() + SECTOR - 1) // SECTOR
            output.seek(extent * SECTOR)
            output.write(payload)
            padding = (-len(payload)) % SECTOR
            if padding:
                output.write(b"\x00" * padding)

            record_offset = directory_record_offset(current, path)
            write_both_endian_32(output, record_offset + 2, extent)
            write_both_endian_32(output, record_offset + 10, len(payload))

        output.seek(0, os.SEEK_END)
        sectors = (output.tell() + SECTOR - 1) // SECTOR
        output.truncate(sectors * SECTOR)
        update_volume_space_size(output, sectors)
        output.flush()
        os.fsync(output.fileno())

    result = Iso9660(output_iso)
    source_tree = {(record.path, record.is_dir) for record in source.records}
    result_tree = {(record.path, record.is_dir) for record in result.records}
    if result_tree != source_tree:
        raise RuntimeError("Final ISO file tree differs from the source tree")

    for source_record in source.records:
        if source_record.is_dir:
            continue
        result_record = result.by_path.get(source_record.path)
        if result_record is None or result_record.is_dir:
            raise RuntimeError(f"Final ISO is missing source file: {source_record.path}")
        expected = bytes(payloads[source_record.path]) if source_record.path in payloads else source.read_file(source_record)
        if result.read_file(result_record) != expected:
            raise RuntimeError(f"Final ISO file verification failed: {source_record.path}")

    green = "\033[32m"
    reset = "\033[0m"
    for category, package in packages:
        print(f"Applied {category} package: {package.name}")
        for path in sorted(package_paths[category]):
            print(f"  {green}{path}{reset}")
    if translation_table is not None:
        print(f"Applied translation table: {translation_table.name}")
        print(f"  rows: {translated_rows}")
        for path in sorted(translated_paths):
            print(f"  {green}{path}{reset}")
    print(f"ISO: {output_iso}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
