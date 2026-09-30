from __future__ import annotations

import hashlib
import io
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Mapping

from .udf import Udf, UdfPlan

SECTOR = 2048
_ZERO_SECTOR = b"\0" * SECTOR
_ISO_FILE_NAME = re.compile(r"[A-Z0-9_]+(?:\.[A-Z0-9_]+)?")
_ISO_DIRECTORY_NAME = re.compile(r"[A-Z0-9_]{1,8}")


def _flush_image(handle: object) -> None:
    handle.flush()
    try:
        descriptor = handle.fileno()
    except (AttributeError, OSError, io.UnsupportedOperation):
        return
    os.fsync(descriptor)


@dataclass(frozen=True)
class IsoRecord:
    path: str
    is_dir: bool
    extent: int
    size: int
    recorded_at: datetime | None
    directory_record_offset: int | None = None

    @property
    def byte_offset(self) -> int:
        return self.extent * SECTOR


@dataclass(frozen=True)
class IsoInsertion:
    path: str
    extent: int
    size: int
    sha256: str
    directory_record_offset: int
    udf_file_entry_offset: int | None = None
    udf_directory_record_offset: int | None = None

    @property
    def byte_offset(self) -> int:
        return self.extent * SECTOR


@dataclass(frozen=True)
class IsoUdfRename:
    source_path: str
    replacement_path: str
    identifier_offset: int
    original_identifier: bytes
    replacement_identifier: bytes


@dataclass(frozen=True)
class IsoComposition:
    insertions: tuple[IsoInsertion, ...]
    udf_renames: tuple[IsoUdfRename, ...]


@dataclass(frozen=True)
class _PlannedWrite:
    offset: int
    expected: bytes
    replacement: bytes
    reason: str


class Iso9660:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.file_size = path.stat().st_size
        self.records: list[IsoRecord] = []
        self.by_path: dict[str, IsoRecord] = {}

        primary, primary_offset = self._read_primary_volume_descriptor()
        self.primary_volume_descriptor_offset = primary_offset
        self.volume_space_size = self._both_endian_u32(
            primary, 80, "primary volume descriptor"
        )
        image_sectors = self.file_size // SECTOR
        if self.volume_space_size > image_sectors:
            raise RuntimeError(
                f"ISO volume space exceeds the image: {self.volume_space_size} > "
                f"{image_sectors} sectors"
            )
        root_length = primary[156]
        if root_length < 34:
            raise RuntimeError(f"Invalid ISO root directory record: {path}")

        root = self._parse_record(
            primary[156:156 + root_length],
            "",
            primary_offset + 156,
        )
        if not root.is_dir:
            raise RuntimeError(f"ISO root record is not a directory: {path}")

        self._add_record(root)
        self._read_directory(root, set())

    def _read_primary_volume_descriptor(self) -> tuple[bytes, int]:
        with self.path.open("rb") as handle:
            primary: bytes | None = None
            primary_offset: int | None = None
            for sector in range(16, 128):
                handle.seek(sector * SECTOR)
                descriptor = handle.read(SECTOR)
                if len(descriptor) != SECTOR:
                    break
                if descriptor[1:6] != b"CD001" or descriptor[6] != 1:
                    continue
                if descriptor[0] == 1 and primary is None:
                    primary = descriptor
                    primary_offset = sector * SECTOR
                if descriptor[0] == 255:
                    break

        if primary is None or primary_offset is None:
            raise RuntimeError(f"ISO9660 primary volume descriptor not found: {self.path}")
        return primary, primary_offset

    @staticmethod
    def _both_endian_u32(raw: bytes, offset: int, context: str) -> int:
        little = int.from_bytes(raw[offset:offset + 4], "little")
        big = int.from_bytes(raw[offset + 4:offset + 8], "big")
        if little != big:
            raise RuntimeError(f"Invalid both-endian ISO field in {context}")
        return little

    def _parse_record(
        self,
        raw: bytes,
        path: str,
        directory_record_offset: int | None = None,
    ) -> IsoRecord:
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

        date = raw[18:25]
        recorded_at: datetime | None
        if date == b"\0" * 7:
            recorded_at = None
        else:
            offset_quarters = date[6] - 256 if date[6] >= 128 else date[6]
            if not -48 <= offset_quarters <= 52:
                raise RuntimeError(
                    f"Invalid ISO timezone offset for {path or '/'}: {offset_quarters}"
                )
            try:
                recorded_at = datetime(
                    1900 + date[0],
                    date[1],
                    date[2],
                    date[3],
                    date[4],
                    date[5],
                    tzinfo=timezone(timedelta(minutes=offset_quarters * 15)),
                )
            except ValueError as error:
                raise RuntimeError(
                    f"Invalid ISO recording time for {path or '/'}"
                ) from error

        return IsoRecord(
            path=path,
            is_dir=bool(flags & 0x02),
            extent=extent,
            size=size,
            recorded_at=recorded_at,
            directory_record_offset=directory_record_offset,
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

                record_offset = offset
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
                record = self._parse_record(
                    raw,
                    path,
                    directory.byte_offset + record_offset,
                )
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


def normalize_iso_path(path: str) -> str:
    normalized = path.replace("\\", "/").strip("/").upper()
    if not normalized or "//" in normalized:
        raise ValueError(f"Invalid ISO path: {path!r}")
    parts = normalized.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError(f"Invalid ISO path: {path!r}")
    return normalized


def _identifier_for_path(path: str, *, is_dir: bool = False) -> bytes:
    name = path.rsplit("/", 1)[-1]
    if is_dir:
        if not _ISO_DIRECTORY_NAME.fullmatch(name):
            raise ValueError(f"Unsupported ISO9660 directory name: {name!r}")
        return name.encode("ascii")
    if not _ISO_FILE_NAME.fullmatch(name):
        raise ValueError(f"Unsupported ISO9660 file name: {name!r}")
    identifier = f"{name};1".encode("ascii")
    if len(identifier) > 31:
        raise ValueError(f"ISO9660 file identifier is longer than 31 bytes: {name!r}")
    return identifier


def _both_endian_u32(raw: bytes, offset: int, context: str) -> int:
    return Iso9660._both_endian_u32(raw, offset, context)


def _both_endian_u16(raw: bytes, offset: int, context: str) -> int:
    little = int.from_bytes(raw[offset:offset + 2], "little")
    big = int.from_bytes(raw[offset + 2:offset + 4], "big")
    if little != big:
        raise RuntimeError(f"Invalid both-endian ISO field in {context}")
    return little


def _set_both_endian_u32(raw: bytearray, offset: int, value: int) -> None:
    if not 0 <= value <= 0xFFFFFFFF:
        raise ValueError(f"ISO field is outside the 32-bit range: {value}")
    raw[offset:offset + 4] = value.to_bytes(4, "little")
    raw[offset + 4:offset + 8] = value.to_bytes(4, "big")


def _read_record_at(handle, offset: int, context: str) -> bytearray:
    handle.seek(offset)
    length_raw = handle.read(1)
    if len(length_raw) != 1 or length_raw[0] < 34:
        raise RuntimeError(f"Invalid ISO directory record for {context}")
    handle.seek(offset)
    raw = bytearray(handle.read(length_raw[0]))
    if len(raw) != length_raw[0] or raw[0] != len(raw):
        raise RuntimeError(f"Invalid ISO directory record for {context}")
    name_length = raw[32]
    if 33 + name_length > len(raw):
        raise RuntimeError(f"Invalid ISO file identifier for {context}")
    return raw


def _record_identifier(raw: bytes) -> bytes:
    return bytes(raw[33:33 + raw[32]])


def _updated_record_size(
    raw: bytearray,
    *,
    expected_size: int,
    new_size: int,
    context: str,
) -> bytes:
    actual = _both_endian_u32(raw, 10, context)
    if actual != expected_size:
        raise RuntimeError(
            f"Unexpected ISO directory size for {context}: {actual} != {expected_size}"
        )
    _set_both_endian_u32(raw, 10, new_size)
    return bytes(raw)


def _file_record(
    *,
    identifier: bytes,
    extent: int,
    size: int,
    recorded_at: bytes,
    volume_sequence: bytes,
    is_dir: bool = False,
) -> bytes:
    padding = 1 if len(identifier) % 2 == 0 else 0
    length = 33 + len(identifier) + padding
    if length > 255:
        raise ValueError("ISO9660 directory record is longer than 255 bytes")
    raw = bytearray(length)
    raw[0] = length
    _set_both_endian_u32(raw, 2, extent)
    _set_both_endian_u32(raw, 10, size)
    raw[18:25] = recorded_at
    raw[25] = 0x02 if is_dir else 0
    raw[28:32] = volume_sequence
    raw[32] = len(identifier)
    raw[33:33 + len(identifier)] = identifier
    return bytes(raw)


def _find_zero_extent(
    handle,
    *,
    start_sector: int,
    sector_count: int,
    volume_space_size: int,
    path: str,
) -> int:
    run_start = start_sector
    run_length = 0
    for sector in range(start_sector, volume_space_size):
        handle.seek(sector * SECTOR)
        block = handle.read(SECTOR)
        if len(block) != SECTOR:
            raise RuntimeError(f"Failed to scan ISO tail sector {sector}")
        if block == _ZERO_SECTOR:
            if run_length == 0:
                run_start = sector
            run_length += 1
            if run_length == sector_count:
                return run_start
        else:
            run_length = 0
    raise RuntimeError(
        f"No verified-zero tail extent can hold {path} "
        f"({sector_count} sector{'s' if sector_count != 1 else ''})"
    )


def _directory_metadata_writes(
    source: Iso9660,
    handle,
    *,
    parent: IsoRecord,
    entries: list[tuple[str, int, int, bool]],
) -> tuple[list[tuple[int, bytes]], dict[str, int], int]:
    if parent.size <= 0:
        raise RuntimeError(f"Cannot append to empty ISO directory: {parent.path or '/'}")
    allocated_size = ((parent.size + SECTOR - 1) // SECTOR) * SECTOR
    handle.seek(parent.byte_offset)
    directory_data = bytearray(handle.read(allocated_size))
    if len(directory_data) != allocated_size:
        raise RuntimeError(f"Failed to read ISO directory: {parent.path or '/'}")

    self_length = directory_data[0]
    if self_length < 34 or self_length > parent.size:
        raise RuntimeError(f"Invalid self record in ISO directory: {parent.path or '/'}")
    self_record = bytearray(directory_data[:self_length])
    if _record_identifier(self_record) != b"\x00":
        raise RuntimeError(f"Missing self record in ISO directory: {parent.path or '/'}")
    if _both_endian_u32(self_record, 2, parent.path or "/") != parent.extent:
        raise RuntimeError(f"Self record extent mismatch in {parent.path or '/'}")
    if _both_endian_u16(self_record, 28, parent.path or "/") <= 0:
        raise RuntimeError(f"Invalid volume sequence in {parent.path or '/'}")

    cursor = parent.size
    entry_offsets: dict[str, int] = {}
    appended: list[tuple[int, bytes]] = []
    for path, extent, size, is_dir in entries:
        identifier = _identifier_for_path(path, is_dir=is_dir)
        record = _file_record(
            identifier=identifier,
            extent=extent,
            size=size,
            recorded_at=bytes(self_record[18:25]),
            volume_sequence=bytes(self_record[28:32]),
            is_dir=is_dir,
        )
        sector_remaining = SECTOR - (cursor % SECTOR)
        if len(record) > sector_remaining:
            cursor += sector_remaining
        end = cursor + len(record)
        if end > allocated_size:
            raise RuntimeError(
                f"ISO directory has no record capacity for {path}: "
                f"{parent.path or '/'} uses {parent.size}/{allocated_size} bytes"
            )
        if any(directory_data[cursor:end]):
            raise RuntimeError(
                f"ISO directory append area is not zero for {path} at "
                f"0x{parent.byte_offset + cursor:X}"
            )
        entry_offsets[path] = parent.byte_offset + cursor
        appended.append((parent.byte_offset + cursor, record))
        cursor = end

    new_size = cursor
    writes = list(appended)

    self_updated = _updated_record_size(
        self_record,
        expected_size=parent.size,
        new_size=new_size,
        context=f"{parent.path or '/'} self record",
    )
    writes.append((parent.byte_offset, self_updated))

    if parent.directory_record_offset is None:
        raise RuntimeError(f"Missing parent record offset for {parent.path or '/'}")
    parent_entry = _read_record_at(
        handle,
        parent.directory_record_offset,
        f"{parent.path or '/'} parent entry",
    )
    writes.append(
        (
            parent.directory_record_offset,
            _updated_record_size(
                parent_entry,
                expected_size=parent.size,
                new_size=new_size,
                context=f"{parent.path or '/'} parent entry",
            ),
        )
    )

    direct_children = [
        record
        for record in source.records
        if record.is_dir
        and record.path
        and record.path.rpartition("/")[0] == parent.path
    ]
    for child in direct_children:
        child_self = _read_record_at(
            handle, child.byte_offset, f"{child.path} self record"
        )
        parent_offset = child.byte_offset + len(child_self)
        child_parent = _read_record_at(
            handle, parent_offset, f"{child.path} parent record"
        )
        if _record_identifier(child_parent) != b"\x01":
            raise RuntimeError(f"Missing parent record in ISO directory: {child.path}")
        writes.append(
            (
                parent_offset,
                _updated_record_size(
                    child_parent,
                    expected_size=parent.size,
                    new_size=new_size,
                    context=f"{child.path} parent record",
                ),
            )
        )

    if parent.path == "":
        parent_record_offset = parent.byte_offset + len(self_record)
        root_parent = _read_record_at(
            handle, parent_record_offset, "/ parent record"
        )
        if _record_identifier(root_parent) != b"\x01":
            raise RuntimeError("Missing root parent record in ISO directory")
        writes.append(
            (
                parent_record_offset,
                _updated_record_size(
                    root_parent,
                    expected_size=parent.size,
                    new_size=new_size,
                    context="/ parent record",
                ),
            )
        )

    return writes, entry_offsets, new_size


def _new_directory_data(
    *,
    extent: int,
    parent: IsoRecord,
    parent_size: int,
    handle,
    entries: list[tuple[str, int, int]],
) -> tuple[bytes, dict[str, int]]:
    """One-sector directory: self and parent records, then its file records."""
    handle.seek(parent.byte_offset)
    parent_self = _read_record_at(handle, parent.byte_offset, f"{parent.path or '/'} self record")
    recorded_at = bytes(parent_self[18:25])
    volume_sequence = bytes(parent_self[28:32])
    records = [
        _file_record(identifier=b"\x00", extent=extent, size=0, recorded_at=recorded_at,
                     volume_sequence=volume_sequence, is_dir=True),
        _file_record(identifier=b"\x01", extent=parent.extent, size=parent_size,
                     recorded_at=recorded_at, volume_sequence=volume_sequence, is_dir=True),
    ]
    offsets: dict[str, int] = {}
    cursor = sum(len(record) for record in records)
    for path, file_extent, size in entries:
        record = _file_record(identifier=_identifier_for_path(path), extent=file_extent,
                              size=size, recorded_at=recorded_at,
                              volume_sequence=volume_sequence)
        offsets[path] = extent * SECTOR + cursor
        records.append(record)
        cursor += len(record)
    if cursor > SECTOR:
        raise RuntimeError(f"New ISO directory does not fit one sector: {entries}")
    data = bytearray(b"".join(records))
    _set_both_endian_u32(data, 10, len(data))
    return bytes(data), offsets


def _path_table_order(table: bytes) -> dict[str, int]:
    """Rank each directory path by its row in an existing little-endian path table."""
    paths = [""]
    ranks: dict[str, int] = {}
    offset = 0
    while offset < len(table) and table[offset]:
        length = table[offset]
        parent = int.from_bytes(table[offset + 6:offset + 8], "little")
        identifier = table[offset + 8:offset + 8 + length]
        if paths[1:] or identifier != b"\x00":
            if not 1 <= parent <= len(paths):
                raise RuntimeError("ISO path table has an invalid parent number")
            name = identifier.decode("ascii").upper()
            parent_path = paths[parent - 1]
            path = f"{parent_path}/{name}" if parent_path else name
            paths.append(path)
        ranks[paths[-1]] = len(ranks)
        offset += 8 + length + (length & 1)
    return ranks


def _path_table(
    directories: Mapping[str, int],
    *,
    big_endian: bool,
    ranks: Mapping[str, int],
) -> bytes:
    """ISO9660 path table by depth and parent, keeping existing rows in their order.

    Directories without a rank follow the existing ones at their level, by name.
    """
    order = "big" if big_endian else "little"
    numbers: dict[str, int] = {"": 1}
    rows = [("", b"\x00", 1)]
    depth = 0
    while True:
        level = [path for path in directories if path and path.count("/") == depth]
        if not level:
            break
        level.sort(key=lambda path: (
            numbers[path.rpartition("/")[0]],
            ranks.get(path, len(ranks)),
            path.rpartition("/")[2].encode("ascii"),
        ))
        for path in level:
            rows.append((path, path.rpartition("/")[2].encode("ascii"),
                         numbers[path.rpartition("/")[0]]))
            numbers[path] = len(rows)
        depth += 1
    table = bytearray()
    for path, identifier, parent_number in rows:
        table += bytes((len(identifier), 0))
        table += directories[path].to_bytes(4, order)
        table += parent_number.to_bytes(2, order)
        table += identifier
        if len(identifier) % 2:
            table.append(0)
    return bytes(table)


def _path_table_writes(
    image: Iso9660,
    handle,
    directories: Mapping[str, int],
) -> list[_PlannedWrite]:
    """Rewrite every path table copy and the table size for a changed directory set."""
    handle.seek(image.primary_volume_descriptor_offset)
    primary = handle.read(SECTOR)
    old_size = _both_endian_u32(primary, 132, "path table size")
    current = {record.path: record.extent for record in image.records if record.is_dir}
    handle.seek(int.from_bytes(primary[140:144], "little") * SECTOR)
    ranks = _path_table_order(handle.read(old_size))
    new_size = len(_path_table(directories, big_endian=False, ranks=ranks))
    writes: list[_PlannedWrite] = []
    for field, big_endian in ((140, False), (144, False), (148, True), (152, True)):
        location = int.from_bytes(primary[field:field + 4], "big" if big_endian else "little")
        if location == 0:
            continue
        handle.seek(location * SECTOR)
        existing = handle.read(max(old_size, new_size))
        if existing[:old_size] != _path_table(current, big_endian=big_endian, ranks=ranks):
            raise RuntimeError(f"ISO path table at sector {location} does not match its tree")
        capacity = ((old_size + SECTOR - 1) // SECTOR) * SECTOR
        if new_size > capacity or any(existing[old_size:]):
            raise RuntimeError(f"ISO path table at sector {location} has no room to grow")
        replacement = _path_table(directories, big_endian=big_endian, ranks=ranks)
        if replacement != existing:
            writes.append(_PlannedWrite(
                location * SECTOR, existing, replacement.ljust(len(existing), b"\0"),
                f"ISO9660 path table at sector {location}",
            ))
    size_field = bytearray(8)
    _set_both_endian_u32(size_field, 0, new_size)
    if bytes(size_field) != primary[132:140]:
        writes.append(_PlannedWrite(
            image.primary_volume_descriptor_offset + 132, bytes(primary[132:140]),
            bytes(size_field), "ISO9660 path table size",
        ))
    return writes


def _normalized_renames(renames: Mapping[str, str]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    replacements: set[str] = set()
    for supplied_source, supplied_replacement in renames.items():
        source = normalize_iso_path(supplied_source)
        replacement = normalize_iso_path(supplied_replacement)
        if source in normalized:
            raise ValueError(f"Duplicate normalized ISO rename source: {source}")
        if replacement in replacements:
            raise ValueError(f"Duplicate normalized ISO rename target: {replacement}")
        if source.rpartition("/")[0] != replacement.rpartition("/")[0]:
            raise ValueError("UDF mirror renames cannot move files between directories")
        normalized[source] = replacement
        replacements.add(replacement)
    return normalized


def _validate_bridge_before_composition(
    iso: Iso9660,
    udf: Udf,
    renames: Mapping[str, str],
) -> None:
    udf_tree = {
        (renames.get(record.path, record.path), record.is_dir)
        for record in udf.records
    }
    iso_tree = {(record.path, record.is_dir) for record in iso.records}
    if udf_tree != iso_tree:
        missing = sorted(iso_tree - udf_tree)
        extra = sorted(udf_tree - iso_tree)
        raise RuntimeError(
            "ISO9660/UDF bridge tree mismatch before composition: "
            f"missing={missing}, extra={extra}"
        )
    for udf_record in udf.records:
        if udf_record.is_dir:
            continue
        iso_path = renames.get(udf_record.path, udf_record.path)
        iso_record = iso.by_path[iso_path]
        if (
            iso_record.size != udf_record.information_length
            or iso_record.extent != udf.absolute_extent(udf_record)
        ):
            raise RuntimeError(
                f"ISO9660/UDF file mapping mismatch before composition: {iso_path}"
            )


def _validate_planned_writes(
    image: Path,
    writes: list[_PlannedWrite],
    image_size: int,
) -> list[_PlannedWrite]:
    ordered = sorted(writes, key=lambda item: item.offset)
    previous_end = 0
    for index, write in enumerate(ordered):
        if not write.expected or len(write.expected) != len(write.replacement):
            raise RuntimeError(f"Invalid planned ISO write: {write.reason}")
        end = write.offset + len(write.expected)
        if write.offset < 0 or end > image_size:
            raise RuntimeError(f"Planned ISO write is outside the image: {write.reason}")
        if index and write.offset < previous_end:
            raise RuntimeError(f"Overlapping planned ISO write: {write.reason}")
        previous_end = end

    with image.open("rb") as handle:
        for write in ordered:
            handle.seek(write.offset)
            actual = handle.read(len(write.expected))
            if actual != write.expected:
                raise RuntimeError(
                    f"ISO changed before planned write at 0x{write.offset:X}: "
                    f"{write.reason}"
                )
    return ordered


def compose_filesystems(
    image: Path,
    payloads: Mapping[str, bytes | bytearray],
    *,
    udf_renames: Mapping[str, str] | None = None,
) -> IsoComposition:
    """Compose ISO9660 insertions and mirror them into an existing UDF bridge."""
    if not payloads and not udf_renames:
        return IsoComposition((), ())

    image = image.resolve()
    source = Iso9660(image)
    original_size = source.file_size
    if original_size % SECTOR:
        raise RuntimeError(f"ISO size is not sector-aligned: {original_size}")
    renames = _normalized_renames(udf_renames or {})
    udf = Udf(image) if Udf.is_present(image) else None
    if udf is not None:
        _validate_bridge_before_composition(source, udf, renames)

    normalized_payloads: dict[str, bytes] = {}
    parents: dict[str, IsoRecord] = {}
    new_directories: set[str] = set()
    for supplied_path, supplied_data in payloads.items():
        path = normalize_iso_path(supplied_path)
        if path in normalized_payloads:
            raise ValueError(f"Duplicate normalized ISO insertion path: {path}")
        if path in source.by_path:
            raise RuntimeError(f"ISO insertion path already exists: {path}")
        if not isinstance(supplied_data, (bytes, bytearray, memoryview)):
            raise TypeError(f"ISO insertion payload must be bytes: {path}")
        data = bytes(supplied_data)
        if not data:
            raise ValueError(f"ISO insertion payload is empty: {path}")
        _identifier_for_path(path)
        parent_path = path.rpartition("/")[0]
        parent = source.by_path.get(parent_path)
        if parent is None:
            # A missing parent becomes one new directory under an existing directory.
            grandparent_path = parent_path.rpartition("/")[0]
            grandparent = source.by_path.get(grandparent_path)
            if grandparent is None or not grandparent.is_dir:
                raise RuntimeError(
                    f"ISO insertion parent directory does not exist: {parent_path or '/'}"
                )
            _identifier_for_path(parent_path, is_dir=True)
            new_directories.add(parent_path)
            parents[grandparent_path] = grandparent
        elif not parent.is_dir:
            raise RuntimeError(f"ISO insertion parent is not a directory: {parent_path}")
        else:
            parents[parent_path] = parent
        normalized_payloads[path] = data

    occupied_end = max(
        record.extent + ((record.size + SECTOR - 1) // SECTOR)
        for record in source.records
    )
    allocation: dict[str, int] = {}
    udf_file_entry_sectors: dict[str, int] = {}
    planned_writes: list[_PlannedWrite] = []
    directory_offsets: dict[str, int] = {}
    udf_plan: UdfPlan | None = None
    with image.open("rb") as handle:
        search_sector = occupied_end
        for path in sorted(normalized_payloads):
            sector_count = (len(normalized_payloads[path]) + SECTOR - 1) // SECTOR
            extent = _find_zero_extent(
                handle,
                start_sector=search_sector,
                sector_count=sector_count,
                volume_space_size=source.volume_space_size,
                path=path,
            )
            allocation[path] = extent
            search_sector = extent + sector_count

        directory_extents: dict[str, int] = {}
        for directory_path in sorted(new_directories):
            extent = _find_zero_extent(
                handle,
                start_sector=search_sector,
                sector_count=1,
                volume_space_size=source.volume_space_size,
                path=f"ISO directory {directory_path}",
            )
            directory_extents[directory_path] = extent
            search_sector = extent + 1

        udf_directory_sectors: dict[str, tuple[int, int]] = {}
        if udf is not None:
            for directory_path in sorted(new_directories):
                entry_sector = _find_zero_extent(
                    handle,
                    start_sector=search_sector,
                    sector_count=2,
                    volume_space_size=source.volume_space_size,
                    path=f"UDF directory {directory_path}",
                )
                udf_directory_sectors[directory_path] = (entry_sector, entry_sector + 1)
                search_sector = entry_sector + 2
            for path in sorted(normalized_payloads):
                sector = _find_zero_extent(
                    handle,
                    start_sector=search_sector,
                    sector_count=1,
                    volume_space_size=source.volume_space_size,
                    path=f"UDF File Entry for {path}",
                )
                udf_file_entry_sectors[path] = sector
                search_sector = sector + 1

        def files_in(directory_path: str) -> list[tuple[str, int, int]]:
            return [
                (path, allocation[path], len(normalized_payloads[path]))
                for path in sorted(normalized_payloads)
                if path.rpartition("/")[0] == directory_path
            ]

        # A new directory's length depends only on its entries, not its parent's size.
        new_directory_sizes = {
            directory_path: len(_new_directory_data(
                extent=directory_extents[directory_path],
                parent=parents[directory_path.rpartition("/")[0]],
                parent_size=0,
                handle=handle,
                entries=files_in(directory_path),
            )[0])
            for directory_path in new_directories
        }
        metadata_writes: list[tuple[int, bytes]] = []
        parent_sizes: dict[str, int] = {}
        for parent_path in sorted(parents):
            entries = [
                (path, directory_extents[path], new_directory_sizes[path], True)
                for path in sorted(new_directories)
                if path.rpartition("/")[0] == parent_path
            ] + [
                (path, extent, size, False) for path, extent, size in files_in(parent_path)
            ]
            writes, offsets, parent_sizes[parent_path] = _directory_metadata_writes(
                source,
                handle,
                parent=parents[parent_path],
                entries=entries,
            )
            metadata_writes.extend(writes)
            directory_offsets.update(offsets)

        for directory_path in sorted(new_directories):
            parent_path = directory_path.rpartition("/")[0]
            data, offsets = _new_directory_data(
                extent=directory_extents[directory_path],
                parent=parents[parent_path],
                parent_size=parent_sizes[parent_path],
                handle=handle,
                entries=files_in(directory_path),
            )
            directory_offsets.update(offsets)
            extent = directory_extents[directory_path]
            handle.seek(extent * SECTOR)
            if handle.read(SECTOR) != _ZERO_SECTOR:
                raise RuntimeError(f"ISO directory extent changed: {directory_path}")
            planned_writes.append(_PlannedWrite(
                extent * SECTOR,
                _ZERO_SECTOR,
                data + b"\0" * (SECTOR - len(data)),
                f"ISO9660 directory {directory_path}",
            ))

        if new_directories:
            directories = {
                record.path: record.extent for record in source.records if record.is_dir
            }
            directories.update(directory_extents)
            planned_writes.extend(_path_table_writes(source, handle, directories))

        for path in sorted(normalized_payloads):
            extent = allocation[path]
            payload = normalized_payloads[path]
            sector_count = (len(payload) + SECTOR - 1) // SECTOR
            handle.seek(extent * SECTOR)
            expected = handle.read(sector_count * SECTOR)
            if expected != _ZERO_SECTOR * sector_count:
                raise RuntimeError(f"ISO tail extent changed before insertion: {path}")
            replacement = payload + b"\0" * (len(expected) - len(payload))
            planned_writes.append(
                _PlannedWrite(
                    extent * SECTOR,
                    expected,
                    replacement,
                    f"inserted payload {path}",
                )
            )

        for offset, replacement in metadata_writes:
            handle.seek(offset)
            expected = handle.read(len(replacement))
            if len(expected) != len(replacement):
                raise RuntimeError(f"Failed to read ISO metadata at 0x{offset:X}")
            planned_writes.append(
                _PlannedWrite(offset, expected, replacement, "ISO9660 directory metadata")
            )

    if udf is not None:
        udf_plan = udf.plan_updates(
            insertion_extents={
                path: (allocation[path], len(normalized_payloads[path]))
                for path in normalized_payloads
            },
            file_entry_sectors=udf_file_entry_sectors,
            renames=renames,
            new_directories=udf_directory_sectors,
        )
        planned_writes.extend(
            _PlannedWrite(write.offset, write.expected, write.replacement, write.reason)
            for write in udf_plan.writes
        )

    ordered_writes = _validate_planned_writes(image, planned_writes, original_size)
    with image.open("r+b") as output:
        for write in ordered_writes:
            output.seek(write.offset)
            output.write(write.replacement)
        _flush_image(output)

    if image.stat().st_size != original_size:
        raise RuntimeError("ISO composition changed the image size")

    result = Iso9660(image)
    expected_tree = {(record.path, record.is_dir) for record in source.records}
    expected_tree.update((path, False) for path in normalized_payloads)
    expected_tree.update((path, True) for path in new_directories)
    result_tree = {(record.path, record.is_dir) for record in result.records}
    if result_tree != expected_tree:
        raise RuntimeError("ISO composition changed the file tree beyond declared additions")
    if new_directories:
        with image.open("rb") as handle:
            if _path_table_writes(result, handle, {
                record.path: record.extent for record in result.records if record.is_dir
            }):
                raise RuntimeError("Final ISO path tables do not match the directory tree")

    result_udf: Udf | None = None
    udf_insertions = {}
    if udf is not None:
        assert udf_plan is not None
        result_udf = Udf(image)
        result_udf_tree = {
            (record.path, record.is_dir) for record in result_udf.records
        }
        if result_udf_tree != result_tree:
            raise RuntimeError("Final ISO9660 and UDF file trees differ")
        for path, iso_record in result.by_path.items():
            udf_record = result_udf.by_path[path]
            if iso_record.is_dir:
                if not udf_record.is_dir:
                    raise RuntimeError(f"Final ISO9660/UDF type mismatch: {path or '/'}")
                continue
            if (
                udf_record.is_dir
                or udf_record.information_length != iso_record.size
                or result_udf.absolute_extent(udf_record) != iso_record.extent
            ):
                raise RuntimeError(f"Final ISO9660/UDF file mapping mismatch: {path}")
        udf_insertions = {item.path: item for item in udf_plan.insertions}
        if set(udf_insertions) != set(normalized_payloads):
            raise RuntimeError("Final UDF insertion result set is incomplete")

    insertions: list[IsoInsertion] = []
    for path in sorted(normalized_payloads):
        record = result.by_path.get(path)
        payload = normalized_payloads[path]
        if (
            record is None
            or record.is_dir
            or record.extent != allocation[path]
            or record.size != len(payload)
            or record.directory_record_offset != directory_offsets[path]
            or result.read_file(record) != payload
        ):
            raise RuntimeError(f"Inserted ISO file verification failed: {path}")
        udf_insertion = udf_insertions.get(path)
        if result_udf is not None:
            udf_record = result_udf.by_path[path]
            if result_udf.read_file(udf_record) != payload:
                raise RuntimeError(f"Inserted UDF file verification failed: {path}")
        insertions.append(
            IsoInsertion(
                path=path,
                extent=record.extent,
                size=record.size,
                sha256=hashlib.sha256(payload).hexdigest().upper(),
                directory_record_offset=directory_offsets[path],
                udf_file_entry_offset=(
                    udf_insertion.file_entry_offset if udf_insertion else None
                ),
                udf_directory_record_offset=(
                    udf_insertion.directory_record_offset if udf_insertion else None
                ),
            )
        )

    rename_results = tuple(
        IsoUdfRename(
            source_path=item.source_path,
            replacement_path=item.replacement_path,
            identifier_offset=item.identifier_offset,
            original_identifier=item.original_identifier,
            replacement_identifier=item.replacement_identifier,
        )
        for item in (udf_plan.renames if udf_plan is not None else ())
    )
    return IsoComposition(tuple(insertions), rename_results)
