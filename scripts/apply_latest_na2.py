#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import stat
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path

sys.dont_write_bytecode = True

SECTOR = 2048


@dataclass(frozen=True)
class IsoRecord:
    path: str
    is_dir: bool
    extent: int
    size: int

    @property
    def byte_offset(self) -> int:
        return self.extent * SECTOR


class Iso9660:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.file_size = path.stat().st_size
        self.records: list[IsoRecord] = []
        self.by_path: dict[str, IsoRecord] = {}

        primary = self._read_primary_volume_descriptor()
        root_length = primary[156]
        if root_length < 34:
            raise RuntimeError(f"Invalid ISO root directory record: {path}")

        root = self._parse_record(primary[156:156 + root_length], "")
        if not root.is_dir:
            raise RuntimeError(f"ISO root record is not a directory: {path}")

        self._add_record(root)
        self._read_directory(root, set())

    def _read_primary_volume_descriptor(self) -> bytes:
        with self.path.open("rb") as handle:
            primary: bytes | None = None
            for sector in range(16, 128):
                handle.seek(sector * SECTOR)
                descriptor = handle.read(SECTOR)
                if len(descriptor) != SECTOR:
                    break
                if descriptor[1:6] != b"CD001" or descriptor[6] != 1:
                    continue
                if descriptor[0] == 1 and primary is None:
                    primary = descriptor
                if descriptor[0] == 255:
                    break

        if primary is None:
            raise RuntimeError(f"ISO9660 primary volume descriptor not found: {self.path}")
        return primary

    @staticmethod
    def _both_endian_u32(raw: bytes, offset: int, context: str) -> int:
        little = int.from_bytes(raw[offset:offset + 4], "little")
        big = int.from_bytes(raw[offset + 4:offset + 8], "big")
        if little != big:
            raise RuntimeError(f"Invalid both-endian ISO field in {context}")
        return little

    def _parse_record(self, raw: bytes, path: str) -> IsoRecord:
        if len(raw) < 34 or raw[0] != len(raw):
            raise RuntimeError(f"Invalid ISO directory record for {path or '/'}")

        extent = self._both_endian_u32(raw, 2, path or "/")
        size = self._both_endian_u32(raw, 10, path or "/")
        flags = raw[25]
        if flags & 0x80:
            raise RuntimeError(f"Multi-extent ISO file is unsupported: {path or '/'}")

        byte_offset = extent * SECTOR
        if byte_offset > self.file_size or size > self.file_size - byte_offset:
            raise RuntimeError(f"ISO record points outside the image: {path or '/'}")

        return IsoRecord(
            path=path,
            is_dir=bool(flags & 0x02),
            extent=extent,
            size=size,
        )

    @staticmethod
    def _decode_name(raw: bytes, parent: str) -> str:
        try:
            name = raw.decode("ascii")
        except UnicodeDecodeError as error:
            raise RuntimeError(
                f"Non-ASCII ISO9660 identifier under {parent or '/'}"
            ) from error

        name = name.split(";", 1)[0].rstrip(".").upper()
        if not name or "/" in name or "\\" in name:
            raise RuntimeError(f"Invalid ISO9660 identifier under {parent or '/'}")
        return name

    def _add_record(self, record: IsoRecord) -> None:
        if record.path in self.by_path:
            raise RuntimeError(f"Duplicate ISO path: {record.path or '/'}")
        self.records.append(record)
        self.by_path[record.path] = record

    def _read_directory(
        self,
        directory: IsoRecord,
        active_directories: set[tuple[int, int]],
    ) -> None:
        identity = (directory.extent, directory.size)
        if identity in active_directories:
            raise RuntimeError(f"Recursive ISO directory reference: {directory.path or '/'}")

        active_directories.add(identity)
        try:
            data = self.read_file(directory)
            offset = 0
            while offset < len(data):
                length = data[offset]
                if length == 0:
                    offset = ((offset // SECTOR) + 1) * SECTOR
                    continue
                if length < 34 or offset + length > len(data):
                    raise RuntimeError(
                        f"Invalid directory data in {directory.path or '/'}"
                    )

                raw = data[offset:offset + length]
                name_length = raw[32]
                if 33 + name_length > len(raw):
                    raise RuntimeError(
                        f"Invalid file identifier in {directory.path or '/'}"
                    )
                identifier = raw[33:33 + name_length]
                offset += length

                if identifier in (b"\x00", b"\x01"):
                    continue

                name = self._decode_name(identifier, directory.path)
                path = f"{directory.path}/{name}" if directory.path else name
                record = self._parse_record(raw, path)
                self._add_record(record)
                if record.is_dir:
                    self._read_directory(record, active_directories)
        finally:
            active_directories.remove(identity)

    def read_file(self, record: IsoRecord) -> bytes:
        with self.path.open("rb") as handle:
            handle.seek(record.byte_offset)
            data = handle.read(record.size)
        if len(data) != record.size:
            raise RuntimeError(f"Failed to read ISO record: {record.path or '/'}")
        return data


@dataclass(frozen=True)
class Package:
    source: str
    path: Path
    payloads: dict[str, bytes]


def normalize_source(value: str) -> str:
    source = value.strip().upper()
    if not source:
        raise argparse.ArgumentTypeError("Package source cannot be empty")
    if any(character not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_" for character in source):
        raise argparse.ArgumentTypeError(
            f"Invalid package source {value!r}; use only letters, digits, and underscores"
        )
    return source


def normalize_zip_path(raw_path: str, *, is_directory: bool) -> str:
    if not raw_path or "\x00" in raw_path:
        raise RuntimeError(f"Unsafe ZIP path: {raw_path!r}")

    path = raw_path.replace("\\", "/")
    if path.startswith("/"):
        raise RuntimeError(f"Unsafe ZIP path: {raw_path!r}")
    if is_directory:
        path = path.removesuffix("/")
    elif path.endswith("/"):
        raise RuntimeError(f"Unsafe ZIP file path: {raw_path!r}")

    parts = path.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise RuntimeError(f"Unsafe ZIP path: {raw_path!r}")
    if ":" in parts[0]:
        raise RuntimeError(f"Unsafe ZIP path: {raw_path!r}")

    return "/".join(parts).upper()


def latest_package(directory: Path, source: str) -> Path:
    prefix = f"NA2_APPLY__{source}__"
    matches = [
        path
        for path in directory.iterdir()
        if path.is_file()
        and path.name.upper().startswith(prefix)
        and path.name.upper().endswith(".ZIP")
    ]
    if not matches:
        pattern = f"NA2_APPLY__{source}__*.zip"
        raise FileNotFoundError(
            f"No package exists for source {source}: {directory / pattern}"
        )
    return max(matches, key=lambda path: (path.stat().st_mtime_ns, path.name.upper()))


def validate_package(package_path: Path, source_name: str, source_iso: Iso9660) -> Package:
    payloads: dict[str, bytes] = {}
    seen_paths: set[str] = set()

    try:
        archive = zipfile.ZipFile(package_path)
    except zipfile.BadZipFile as error:
        raise RuntimeError(f"Invalid ZIP for source {source_name}: {package_path}") from error

    with archive:
        for info in archive.infolist():
            is_directory = info.is_dir()
            path = normalize_zip_path(info.filename, is_directory=is_directory)
            if path in seen_paths:
                raise RuntimeError(
                    f"Duplicate normalized ZIP path in {package_path.name}: {path}"
                )
            seen_paths.add(path)

            record = source_iso.by_path.get(path)
            if record is None or record.is_dir != is_directory:
                entry_kind = "directory" if is_directory else "file"
                raise RuntimeError(
                    f"Unexpected {entry_kind} in {package_path.name}; "
                    f"path does not match the source ISO: {path}"
                )
            if is_directory:
                continue

            unix_mode = info.external_attr >> 16
            unix_type = stat.S_IFMT(unix_mode)
            if info.create_system == 3 and unix_type not in (0, stat.S_IFREG):
                raise RuntimeError(
                    f"Unsupported non-regular ZIP entry in {package_path.name}: "
                    f"{info.filename!r}"
                )
            if info.flag_bits & 0x1:
                raise RuntimeError(
                    f"Encrypted ZIP entry is not supported in {package_path.name}: "
                    f"{info.filename!r}"
                )
            if info.file_size != record.size:
                raise RuntimeError(
                    f"Replacement size differs in {package_path.name} for {path}: "
                    f"expected {record.size} bytes, got {info.file_size}"
                )

            try:
                payloads[path] = archive.read(info)
            except (zipfile.BadZipFile, RuntimeError, NotImplementedError) as error:
                raise RuntimeError(
                    f"Failed to validate ZIP entry in {package_path.name}: "
                    f"{info.filename!r}: {error}"
                ) from error

    if not payloads:
        raise RuntimeError(f"Package contains no replacement files: {package_path.name}")

    return Package(source=source_name, path=package_path, payloads=payloads)


def find_conflicts(packages: list[Package]) -> dict[str, list[Package]]:
    owners: dict[str, list[Package]] = {}
    for package in packages:
        for path in package.payloads:
            owners.setdefault(path, []).append(package)
    return {path: items for path, items in owners.items() if len(items) > 1}


def recreate_output(source_iso: Path, output_iso: Path) -> None:
    temporary = output_iso.with_suffix(output_iso.suffix + ".initializing")
    temporary.unlink(missing_ok=True)
    print("Recreating output with a complete source ISO copy...")
    try:
        shutil.copyfile(source_iso, temporary)
        os.replace(temporary, output_iso)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Compose explicitly selected NA2 apply-package sources onto a fresh "
            "complete copy of the clean source ISO."
        )
    )
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--downloads", required=True, type=Path)
    parser.add_argument(
        "--package",
        required=True,
        action="append",
        type=normalize_source,
        dest="package_sources",
        help=(
            "Package source label, repeated as needed; selects the newest "
            "NA2_APPLY__<SOURCE>__*.zip"
        ),
    )
    args = parser.parse_args()

    source_iso_path = args.source.resolve()
    output_iso_path = args.output.resolve()
    downloads = args.downloads.resolve()

    if not source_iso_path.is_file():
        raise FileNotFoundError(f"Source ISO does not exist: {source_iso_path}")
    if not downloads.is_dir():
        raise NotADirectoryError(f"Package directory does not exist: {downloads}")
    if source_iso_path == output_iso_path:
        raise ValueError("Source and output ISO paths must differ")

    duplicate_sources = sorted(
        source
        for source in set(args.package_sources)
        if args.package_sources.count(source) > 1
    )
    if duplicate_sources:
        raise RuntimeError(
            "Package source selected more than once: " + ", ".join(duplicate_sources)
        )

    package_sources = args.package_sources

    print("SELECTED NA2 APPLY PACKAGES:")
    selected_paths: list[Path] = []
    for source in package_sources:
        package_path = latest_package(downloads, source)
        selected_paths.append(package_path)
        print(f"  [{source}] {package_path}")

    source_iso = Iso9660(source_iso_path)
    packages = [
        validate_package(package_path, source, source_iso)
        for source, package_path in zip(package_sources, selected_paths, strict=True)
    ]

    conflicts = find_conflicts(packages)
    if conflicts:
        lines = ["Selected packages replace the same ISO path(s):"]
        for path in sorted(conflicts):
            labels = ", ".join(
                f"{package.source} ({package.path.name})"
                for package in conflicts[path]
            )
            lines.append(f"  {path}: {labels}")
        raise RuntimeError("\n".join(lines))

    output_iso_path.parent.mkdir(parents=True, exist_ok=True)
    recreate_output(source_iso_path, output_iso_path)

    with output_iso_path.open("r+b") as output:
        for package in packages:
            for path in sorted(package.payloads):
                output.seek(source_iso.by_path[path].byte_offset)
                output.write(package.payloads[path])
        output.flush()
        os.fsync(output.fileno())

    result = Iso9660(output_iso_path)
    if output_iso_path.stat().st_size != source_iso_path.stat().st_size:
        raise RuntimeError("Final ISO size differs from the source ISO")

    source_tree = {(record.path, record.is_dir) for record in source_iso.records}
    result_tree = {(record.path, record.is_dir) for record in result.records}
    if result_tree != source_tree:
        raise RuntimeError("Final ISO file tree differs from the source tree")

    expected_replacements = {
        path: data
        for package in packages
        for path, data in package.payloads.items()
    }
    for source_record in source_iso.records:
        if source_record.is_dir:
            continue

        result_record = result.by_path.get(source_record.path)
        if result_record is None or result_record.is_dir:
            raise RuntimeError(f"Final ISO is missing source file: {source_record.path}")

        expected = expected_replacements.get(source_record.path)
        if expected is None:
            expected = source_iso.read_file(source_record)
        if result.read_file(result_record) != expected:
            raise RuntimeError(
                f"Final ISO file verification failed: {source_record.path}"
            )

    green = "\033[32m"
    reset = "\033[0m"
    print("Applied files:")
    for package in packages:
        print(f"  [{package.source}] {package.path.name}")
        for path in sorted(package.payloads):
            print(f"    {green}{path}{reset}")
    print(f"ISO: {output_iso_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
