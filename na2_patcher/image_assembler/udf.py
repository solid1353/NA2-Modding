from __future__ import annotations

import binascii
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


BLOCK_SIZE = 2048
_TAG_SIZE = 16
_SHORT_AD_SIZE = 8
_LONG_AD_SIZE = 16
_EXTENT_LENGTH_MASK = 0x3FFFFFFF


@dataclass(frozen=True)
class UdfRecord:
    path: str
    display_path: str
    is_dir: bool
    file_type: int
    icb_lbn: int
    icb_length: int
    information_length: int
    logical_blocks_recorded: int
    data_lbn: int
    unique_id: int
    file_entry_offset: int
    file_entry_length: int
    fid_offset: int | None
    fid_length: int | None
    parent_path: str


@dataclass(frozen=True)
class UdfWrite:
    offset: int
    expected: bytes
    replacement: bytes
    reason: str


@dataclass(frozen=True)
class UdfInsertion:
    path: str
    file_entry_offset: int
    directory_record_offset: int


@dataclass(frozen=True)
class UdfRename:
    source_path: str
    replacement_path: str
    identifier_offset: int
    original_identifier: bytes
    replacement_identifier: bytes


@dataclass(frozen=True)
class UdfPlan:
    writes: tuple[UdfWrite, ...]
    insertions: tuple[UdfInsertion, ...]
    renames: tuple[UdfRename, ...]


def _u16(raw: bytes | bytearray, offset: int) -> int:
    return struct.unpack_from("<H", raw, offset)[0]


def _u32(raw: bytes | bytearray, offset: int) -> int:
    return struct.unpack_from("<I", raw, offset)[0]


def _u64(raw: bytes | bytearray, offset: int) -> int:
    return struct.unpack_from("<Q", raw, offset)[0]


def _set_u16(raw: bytearray, offset: int, value: int) -> None:
    struct.pack_into("<H", raw, offset, value)


def _set_u32(raw: bytearray, offset: int, value: int) -> None:
    struct.pack_into("<I", raw, offset, value)


def _set_u64(raw: bytearray, offset: int, value: int) -> None:
    struct.pack_into("<Q", raw, offset, value)


def _allocated_length(raw: bytes | bytearray, offset: int, context: str) -> int:
    value = _u32(raw, offset)
    if value >> 30:
        raise RuntimeError(f"Unsupported UDF extent type in {context}")
    return value & _EXTENT_LENGTH_MASK


def _normalize_path(path: str) -> str:
    normalized = path.replace("\\", "/").strip("/").upper()
    if not normalized or "//" in normalized:
        raise ValueError(f"Invalid UDF path: {path!r}")
    if any(part in {"", ".", ".."} for part in normalized.split("/")):
        raise ValueError(f"Invalid UDF path: {path!r}")
    return normalized


def _decode_cs0(raw: bytes, context: str) -> str:
    if not raw:
        raise RuntimeError(f"Empty UDF file identifier in {context}")
    try:
        if raw[0] == 8:
            return raw[1:].decode("latin-1")
        if raw[0] == 16:
            if len(raw) % 2 == 0:
                raise UnicodeDecodeError("utf-16-be", raw, 1, len(raw), "odd payload")
            return raw[1:].decode("utf-16-be")
    except UnicodeDecodeError as error:
        raise RuntimeError(f"Invalid UDF CS0 identifier in {context}") from error
    raise RuntimeError(
        f"Unsupported UDF CS0 compression id {raw[0]} in {context}"
    )


def _encode_cs0(name: str) -> bytes:
    encoded = b"\x10" + name.encode("utf-16-be")
    if len(encoded) > 255:
        raise ValueError(f"UDF file identifier is longer than 255 bytes: {name!r}")
    return encoded


def _validate_tag(
    raw: bytes | bytearray,
    offset: int,
    *,
    expected_identifier: int,
    expected_location: int,
    context: str,
) -> int:
    if offset < 0 or offset + _TAG_SIZE > len(raw):
        raise RuntimeError(f"Truncated UDF descriptor tag in {context}")
    identifier = _u16(raw, offset)
    if identifier != expected_identifier:
        raise RuntimeError(
            f"Unexpected UDF tag in {context}: {identifier} != {expected_identifier}"
        )
    if _u16(raw, offset + 2) != 2 or raw[offset + 5] != 0:
        raise RuntimeError(f"Unsupported UDF descriptor tag version in {context}")
    checksum = (sum(raw[offset:offset + 4]) + sum(raw[offset + 5:offset + 16])) & 0xFF
    if raw[offset + 4] != checksum:
        raise RuntimeError(f"Invalid UDF descriptor tag checksum in {context}")
    crc_length = _u16(raw, offset + 10)
    if offset + _TAG_SIZE + crc_length > len(raw):
        raise RuntimeError(f"Invalid UDF descriptor CRC length in {context}")
    crc = binascii.crc_hqx(
        bytes(raw[offset + _TAG_SIZE:offset + _TAG_SIZE + crc_length]), 0
    )
    if _u16(raw, offset + 8) != crc:
        raise RuntimeError(f"Invalid UDF descriptor CRC in {context}")
    location = _u32(raw, offset + 12)
    if location != expected_location:
        raise RuntimeError(
            f"Unexpected UDF tag location in {context}: {location} != "
            f"{expected_location}"
        )
    return _TAG_SIZE + crc_length


def _refresh_tag(raw: bytearray, offset: int, *, location: int | None = None) -> None:
    if location is not None:
        _set_u32(raw, offset + 12, location)
    crc_length = _u16(raw, offset + 10)
    if offset + _TAG_SIZE + crc_length > len(raw):
        raise RuntimeError("Cannot refresh truncated UDF descriptor tag")
    _set_u16(
        raw,
        offset + 8,
        binascii.crc_hqx(
            bytes(raw[offset + _TAG_SIZE:offset + _TAG_SIZE + crc_length]), 0
        ),
    )
    raw[offset + 4] = 0
    raw[offset + 4] = (
        sum(raw[offset:offset + 4]) + sum(raw[offset + 5:offset + 16])
    ) & 0xFF


def _long_ad(raw: bytes | bytearray, offset: int, context: str) -> tuple[int, int, int]:
    length = _allocated_length(raw, offset, context)
    location = _u32(raw, offset + 4)
    partition = _u16(raw, offset + 8)
    return length, location, partition


class Udf:
    """Restricted validating reader/writer for NA2's UDF 1.02 bridge."""

    @staticmethod
    def is_present(path: Path) -> bool:
        with path.open("rb") as handle:
            for sector in range(16, 32):
                handle.seek(sector * BLOCK_SIZE)
                descriptor = handle.read(BLOCK_SIZE)
                if len(descriptor) != BLOCK_SIZE:
                    break
                if descriptor[1:6] == b"NSR02":
                    return True
        return False

    def __init__(self, path: Path) -> None:
        self.path = path.resolve()
        self.file_size = self.path.stat().st_size
        if self.file_size % BLOCK_SIZE:
            raise RuntimeError(f"UDF image is not block-aligned: {self.path}")
        self.image_blocks = self.file_size // BLOCK_SIZE
        if self.image_blocks <= 257 or not self.is_present(self.path):
            raise RuntimeError(f"UDF 1.02 bridge is not present: {self.path}")

        main_extent, reserve_extent = self._read_anchor(256)
        final_main, final_reserve = self._read_anchor(self.image_blocks - 1)
        if (main_extent, reserve_extent) != (final_main, final_reserve):
            raise RuntimeError("UDF anchor descriptor extents disagree")

        main = self._read_descriptor_sequence(*main_extent, "main")
        reserve = self._read_descriptor_sequence(*reserve_extent, "reserve")
        main_partition = self._only_descriptor(main, 5, "Partition Descriptor")
        reserve_partition = self._only_descriptor(reserve, 5, "Partition Descriptor")
        main_logical = self._only_descriptor(main, 6, "Logical Volume Descriptor")
        reserve_logical = self._only_descriptor(reserve, 6, "Logical Volume Descriptor")
        if main_partition[16:] != reserve_partition[16:]:
            raise RuntimeError("UDF main/reserve Partition Descriptors disagree")
        if main_logical[16:] != reserve_logical[16:]:
            raise RuntimeError("UDF main/reserve Logical Volume Descriptors disagree")

        if _u16(main_partition, 22) != 0 or main_partition[25:31] != b"+NSR02":
            raise RuntimeError("Unsupported UDF partition descriptor")
        self.partition_start = _u32(main_partition, 188)
        self.partition_length = _u32(main_partition, 192)
        if (
            self.partition_start <= 0
            or self.partition_length <= 0
            or self.partition_start + self.partition_length > self.image_blocks
        ):
            raise RuntimeError("UDF partition lies outside the image")

        if _u32(main_logical, 212) != BLOCK_SIZE:
            raise RuntimeError("Unsupported UDF logical block size")
        if _u32(main_logical, 264) != 6 or _u32(main_logical, 268) != 1:
            raise RuntimeError("Unsupported UDF partition-map count")
        if bytes(main_logical[440:446]) != b"\x01\x06\x01\x00\x00\x00":
            raise RuntimeError("Unsupported UDF Type 1 partition map")

        file_set_length, file_set_lbn, file_set_partition = _long_ad(
            main_logical, 248, "Logical Volume Contents Use"
        )
        if file_set_partition != 0 or file_set_length < 512:
            raise RuntimeError("Unsupported UDF File Set Descriptor address")
        file_set = self._read_partition_block(file_set_lbn)
        _validate_tag(
            file_set,
            0,
            expected_identifier=256,
            expected_location=file_set_lbn,
            context="File Set Descriptor",
        )
        root_length, root_lbn, root_partition = _long_ad(
            file_set, 400, "root directory ICB"
        )
        if root_partition != 0:
            raise RuntimeError("UDF root directory uses an unsupported partition")

        integrity_length = _allocated_length(
            main_logical, 432, "Logical Volume Integrity extent"
        )
        self.integrity_sector = _u32(main_logical, 436)
        if integrity_length < BLOCK_SIZE:
            raise RuntimeError("UDF Logical Volume Integrity extent is too short")
        self.integrity = self._read_absolute_block(self.integrity_sector)
        _validate_tag(
            self.integrity,
            0,
            expected_identifier=9,
            expected_location=self.integrity_sector,
            context="Logical Volume Integrity Descriptor",
        )
        if _u32(self.integrity, 28) != 1:
            raise RuntimeError("UDF logical volume is not closed")
        self.integrity_partition_count = _u32(self.integrity, 72)
        if self.integrity_partition_count != 1:
            raise RuntimeError("Unsupported UDF integrity partition count")
        self.integrity_implementation_offset = 80 + 8 * self.integrity_partition_count
        implementation_length = _u32(self.integrity, 76)
        if implementation_length < 40:
            raise RuntimeError("UDF integrity implementation data is too short")
        self.recorded_file_count = _u32(
            self.integrity, self.integrity_implementation_offset + 32
        )
        self.recorded_directory_count = _u32(
            self.integrity, self.integrity_implementation_offset + 36
        )

        self.records: list[UdfRecord] = []
        self.by_path: dict[str, UdfRecord] = {}
        self.children: dict[str, list[str]] = {}
        self._active_icbs: set[int] = set()
        self._walk_file_entry(
            root_lbn,
            root_length,
            path="",
            display_path="",
            parent_path="",
            fid_offset=None,
            fid_length=None,
        )

    def _read_absolute_block(self, sector: int) -> bytes:
        if not 0 <= sector < self.image_blocks:
            raise RuntimeError(f"UDF sector is outside the image: {sector}")
        with self.path.open("rb") as handle:
            handle.seek(sector * BLOCK_SIZE)
            data = handle.read(BLOCK_SIZE)
        if len(data) != BLOCK_SIZE:
            raise RuntimeError(f"Failed to read UDF sector {sector}")
        return data

    def _read_partition_block(self, lbn: int) -> bytes:
        if not 0 <= lbn < self.partition_length:
            raise RuntimeError(f"UDF logical block is outside the partition: {lbn}")
        return self._read_absolute_block(self.partition_start + lbn)

    def _read_anchor(self, sector: int) -> tuple[tuple[int, int], tuple[int, int]]:
        anchor = self._read_absolute_block(sector)
        _validate_tag(
            anchor,
            0,
            expected_identifier=2,
            expected_location=sector,
            context=f"Anchor Volume Descriptor Pointer at sector {sector}",
        )
        main = (_allocated_length(anchor, 16, "main descriptor sequence"), _u32(anchor, 20))
        reserve = (
            _allocated_length(anchor, 24, "reserve descriptor sequence"),
            _u32(anchor, 28),
        )
        if not main[0] or not reserve[0]:
            raise RuntimeError("UDF anchor has an empty descriptor sequence")
        return main, reserve

    def _read_descriptor_sequence(
        self, length: int, sector: int, name: str
    ) -> dict[int, list[bytes]]:
        if length % BLOCK_SIZE:
            raise RuntimeError(f"UDF {name} descriptor sequence is not block-aligned")
        descriptors: dict[int, list[bytes]] = {}
        terminated = False
        for index in range(length // BLOCK_SIZE):
            location = sector + index
            block = self._read_absolute_block(location)
            identifier = _u16(block, 0)
            if identifier == 0:
                continue
            _validate_tag(
                block,
                0,
                expected_identifier=identifier,
                expected_location=location,
                context=f"UDF {name} descriptor sector {location}",
            )
            descriptors.setdefault(identifier, []).append(block)
            if identifier == 8:
                terminated = True
                break
        if not terminated:
            raise RuntimeError(f"UDF {name} descriptor sequence is unterminated")
        return descriptors

    @staticmethod
    def _only_descriptor(
        descriptors: dict[int, list[bytes]], identifier: int, name: str
    ) -> bytes:
        matches = descriptors.get(identifier, [])
        if len(matches) != 1:
            raise RuntimeError(f"UDF requires exactly one {name}")
        return matches[0]

    def _walk_file_entry(
        self,
        icb_lbn: int,
        icb_length: int,
        *,
        path: str,
        display_path: str,
        parent_path: str,
        fid_offset: int | None,
        fid_length: int | None,
    ) -> UdfRecord:
        if icb_lbn in self._active_icbs:
            raise RuntimeError(f"Recursive UDF ICB reference: {icb_lbn}")
        block = self._read_partition_block(icb_lbn)
        descriptor_length = _validate_tag(
            block,
            0,
            expected_identifier=261,
            expected_location=icb_lbn,
            context=f"UDF File Entry {path or '/'}",
        )
        if icb_length != descriptor_length:
            raise RuntimeError(
                f"UDF ICB length mismatch for {path or '/'}: "
                f"{icb_length} != {descriptor_length}"
            )
        flags = _u16(block, 34)
        if flags & 7:
            raise RuntimeError(f"Unsupported UDF allocation descriptor type: {path or '/'}")
        file_type = block[27]
        is_dir = file_type == 4
        information_length = _u64(block, 56)
        logical_blocks = _u64(block, 64)
        extended_length = _u32(block, 168)
        allocation_length = _u32(block, 172)
        allocation_offset = 176 + extended_length
        if allocation_length != _SHORT_AD_SIZE or allocation_offset + 8 > descriptor_length:
            raise RuntimeError(f"Unsupported UDF File Entry layout: {path or '/'}")
        data_length = _allocated_length(block, allocation_offset, path or "/")
        data_lbn = _u32(block, allocation_offset + 4)
        if data_length != information_length:
            raise RuntimeError(f"UDF allocation length mismatch: {path or '/'}")
        expected_blocks = (information_length + BLOCK_SIZE - 1) // BLOCK_SIZE
        if logical_blocks != expected_blocks:
            raise RuntimeError(f"UDF recorded-block count mismatch: {path or '/'}")
        if data_lbn + expected_blocks > self.partition_length:
            raise RuntimeError(f"UDF file data is outside the partition: {path or '/'}")
        if path in self.by_path:
            raise RuntimeError(f"Duplicate UDF path: {path or '/'}")

        record = UdfRecord(
            path=path,
            display_path=display_path,
            is_dir=is_dir,
            file_type=file_type,
            icb_lbn=icb_lbn,
            icb_length=icb_length,
            information_length=information_length,
            logical_blocks_recorded=logical_blocks,
            data_lbn=data_lbn,
            unique_id=_u64(block, 160),
            file_entry_offset=(self.partition_start + icb_lbn) * BLOCK_SIZE,
            file_entry_length=descriptor_length,
            fid_offset=fid_offset,
            fid_length=fid_length,
            parent_path=parent_path,
        )
        self.records.append(record)
        self.by_path[path] = record
        self.children.setdefault(path, [])

        if not is_dir:
            return record

        self._active_icbs.add(icb_lbn)
        try:
            directory = self.read_file(record)
            offset = 0
            parent_seen = False
            while offset < len(directory):
                block_location = data_lbn + offset // BLOCK_SIZE
                descriptor_length = _validate_tag(
                    directory,
                    offset,
                    expected_identifier=257,
                    expected_location=block_location,
                    context=f"UDF directory {path or '/'} at 0x{offset:X}",
                )
                total_length = (descriptor_length + 3) & ~3
                if total_length != descriptor_length or offset + total_length > len(directory):
                    raise RuntimeError(f"Invalid UDF FID length in {path or '/'}")
                if _u16(directory, offset + 16) != 1:
                    raise RuntimeError(f"Unsupported UDF file version in {path or '/'}")
                characteristics = directory[offset + 18]
                identifier_length = directory[offset + 19]
                child_icb_length, child_icb_lbn, partition = _long_ad(
                    directory, offset + 20, f"UDF FID in {path or '/'}"
                )
                if partition != 0:
                    raise RuntimeError(f"UDF FID uses an unsupported partition: {path or '/'}")
                implementation_length = _u16(directory, offset + 36)
                if implementation_length % 4:
                    raise RuntimeError(f"Invalid UDF FID implementation length: {path or '/'}")
                identifier_offset = offset + 38 + implementation_length
                identifier_end = identifier_offset + identifier_length
                if identifier_end > offset + total_length:
                    raise RuntimeError(f"Truncated UDF file identifier in {path or '/'}")

                if characteristics & 8:
                    if identifier_length or not (characteristics & 2) or parent_seen:
                        raise RuntimeError(f"Invalid UDF parent FID in {path or '/'}")
                    parent_seen = True
                else:
                    display_name = _decode_cs0(
                        bytes(directory[identifier_offset:identifier_end]), path or "/"
                    )
                    normalized_name = _normalize_path(display_name)
                    child_path = f"{path}/{normalized_name}" if path else normalized_name
                    child_display = (
                        f"{display_path}/{display_name}" if display_path else display_name
                    )
                    child = self._walk_file_entry(
                        child_icb_lbn,
                        child_icb_length,
                        path=child_path,
                        display_path=child_display,
                        parent_path=path,
                        fid_offset=(
                            self.partition_start + data_lbn
                        ) * BLOCK_SIZE + offset,
                        fid_length=total_length,
                    )
                    if bool(characteristics & 2) != child.is_dir:
                        raise RuntimeError(f"UDF FID type mismatch: {child_path}")
                    self.children[path].append(child_path)
                offset += total_length
            if not parent_seen:
                raise RuntimeError(f"UDF directory lacks a parent FID: {path or '/'}")
        finally:
            self._active_icbs.remove(icb_lbn)
        return record

    def read_file(self, record: UdfRecord) -> bytes:
        offset = (self.partition_start + record.data_lbn) * BLOCK_SIZE
        with self.path.open("rb") as handle:
            handle.seek(offset)
            data = handle.read(record.information_length)
        if len(data) != record.information_length:
            raise RuntimeError(f"Failed to read UDF file: {record.path or '/'}")
        return data

    def absolute_extent(self, record: UdfRecord) -> int:
        return self.partition_start + record.data_lbn

    def _read_range(self, offset: int, length: int) -> bytes:
        with self.path.open("rb") as handle:
            handle.seek(offset)
            data = handle.read(length)
        if len(data) != length:
            raise RuntimeError(f"Failed to read UDF range at 0x{offset:X}")
        return data

    @staticmethod
    def _updated_file_entry(
        original: bytes,
        *,
        information_length: int,
        logical_blocks: int,
        data_lbn: int,
        unique_id: int,
        tag_location: int,
    ) -> bytes:
        updated = bytearray(original)
        extended_length = _u32(updated, 168)
        allocation_offset = 176 + extended_length
        if _u32(updated, 172) != 8 or allocation_offset + 8 > len(updated):
            raise RuntimeError("Unsupported UDF File Entry template")
        _set_u64(updated, 56, information_length)
        _set_u64(updated, 64, logical_blocks)
        _set_u64(updated, 160, unique_id)
        _set_u32(updated, allocation_offset, information_length)
        _set_u32(updated, allocation_offset + 4, data_lbn)
        if extended_length >= 16 and _u16(updated, 176) == 262:
            _refresh_tag(updated, 176, location=tag_location)
        _refresh_tag(updated, 0, location=tag_location)
        return bytes(updated)

    @staticmethod
    def _file_identifier(
        *,
        name: str,
        icb_length: int,
        icb_lbn: int,
        tag_location: int,
    ) -> bytes:
        identifier = _encode_cs0(name)
        length = (38 + len(identifier) + 3) & ~3
        raw = bytearray(length)
        _set_u16(raw, 0, 257)
        _set_u16(raw, 2, 2)
        _set_u16(raw, 6, 0)
        _set_u16(raw, 10, length - 16)
        _set_u32(raw, 12, tag_location)
        _set_u16(raw, 16, 1)
        raw[18] = 0
        raw[19] = len(identifier)
        _set_u32(raw, 20, icb_length)
        _set_u32(raw, 24, icb_lbn)
        _set_u16(raw, 28, 0)
        _set_u16(raw, 36, 0)
        raw[38:38 + len(identifier)] = identifier
        _refresh_tag(raw, 0)
        return bytes(raw)

    def plan_updates(
        self,
        *,
        insertion_extents: Mapping[str, tuple[int, int]],
        file_entry_sectors: Mapping[str, int],
        renames: Mapping[str, str],
    ) -> UdfPlan:
        normalized_insertions = {
            _normalize_path(path): value for path, value in insertion_extents.items()
        }
        normalized_entries = {
            _normalize_path(path): sector for path, sector in file_entry_sectors.items()
        }
        if set(normalized_insertions) != set(normalized_entries):
            raise RuntimeError("UDF insertion payload/ICB sets differ")
        normalized_renames = {
            _normalize_path(source): _normalize_path(replacement)
            for source, replacement in renames.items()
        }

        directory_buffers: dict[str, tuple[bytes, bytearray]] = {}
        file_entry_buffers: dict[str, tuple[bytes, bytearray]] = {}

        def directory_buffer(path: str) -> tuple[UdfRecord, bytearray]:
            record = self.by_path[path]
            if not record.is_dir or record.logical_blocks_recorded <= 0:
                raise RuntimeError(f"Cannot update UDF directory: {path or '/'}")
            if path not in directory_buffers:
                length = record.logical_blocks_recorded * BLOCK_SIZE
                offset = (self.partition_start + record.data_lbn) * BLOCK_SIZE
                original = self._read_range(offset, length)
                directory_buffers[path] = (original, bytearray(original))
            return record, directory_buffers[path][1]

        def file_entry_buffer(path: str) -> tuple[UdfRecord, bytearray]:
            record = self.by_path[path]
            if path not in file_entry_buffers:
                original = self._read_range(
                    record.file_entry_offset, record.file_entry_length
                )
                file_entry_buffers[path] = (original, bytearray(original))
            return record, file_entry_buffers[path][1]

        rename_results: list[UdfRename] = []
        for source_path in sorted(normalized_renames):
            replacement_path = normalized_renames[source_path]
            source = self.by_path.get(source_path)
            if source is None or source.fid_offset is None or source.fid_length is None:
                raise RuntimeError(f"UDF rename source does not exist: {source_path}")
            if replacement_path in self.by_path:
                raise RuntimeError(f"UDF rename target already exists: {replacement_path}")
            replacement_parent, _, replacement_name = replacement_path.rpartition("/")
            if replacement_parent != source.parent_path:
                raise RuntimeError("UDF renames cannot move a file between directories")
            parent, data = directory_buffer(source.parent_path)
            relative = source.fid_offset - (
                self.partition_start + parent.data_lbn
            ) * BLOCK_SIZE
            implementation_length = _u16(data, relative + 36)
            identifier_offset = relative + 38 + implementation_length
            original_length = data[relative + 19]
            original_identifier = bytes(
                data[identifier_offset:identifier_offset + original_length]
            )
            replacement_identifier = _encode_cs0(replacement_name)
            capacity = source.fid_length - (38 + implementation_length)
            if len(replacement_identifier) > capacity:
                raise RuntimeError(
                    f"UDF rename identifier does not fit its existing FID: "
                    f"{replacement_path}"
                )
            data[relative + 19] = len(replacement_identifier)
            data[identifier_offset:identifier_offset + capacity] = b"\0" * capacity
            data[
                identifier_offset:identifier_offset + len(replacement_identifier)
            ] = replacement_identifier
            _refresh_tag(data, relative)
            rename_results.append(
                UdfRename(
                    source_path=source_path,
                    replacement_path=replacement_path,
                    identifier_offset=(
                        self.partition_start + parent.data_lbn
                    ) * BLOCK_SIZE + identifier_offset,
                    original_identifier=original_identifier,
                    replacement_identifier=replacement_identifier,
                )
            )

        insertion_results: list[UdfInsertion] = []
        next_unique_id = max(record.unique_id for record in self.records) + 1
        insertions_by_parent: dict[str, list[str]] = {}
        for path in sorted(normalized_insertions):
            if path in self.by_path:
                raise RuntimeError(f"UDF insertion path already exists: {path}")
            parent_path = path.rpartition("/")[0]
            parent = self.by_path.get(parent_path)
            if parent is None or not parent.is_dir:
                raise RuntimeError(f"UDF insertion parent does not exist: {parent_path}")
            insertions_by_parent.setdefault(parent_path, []).append(path)

        new_file_entry_writes: list[UdfWrite] = []
        for parent_path in sorted(insertions_by_parent):
            parent, directory = directory_buffer(parent_path)
            template_candidates = [
                self.by_path[path]
                for path in self.children[parent_path]
                if not self.by_path[path].is_dir
            ]
            if not template_candidates:
                raise RuntimeError(
                    f"UDF insertion directory lacks a file-entry template: {parent_path}"
                )
            template = template_candidates[-1]
            template_data = self._read_range(
                template.file_entry_offset, template.file_entry_length
            )
            cursor = parent.information_length
            for path in insertions_by_parent[parent_path]:
                absolute_extent, size = normalized_insertions[path]
                file_entry_sector = normalized_entries[path]
                payload_blocks = (size + BLOCK_SIZE - 1) // BLOCK_SIZE
                if not (
                    self.partition_start
                    <= absolute_extent
                    and absolute_extent + payload_blocks
                    <= self.partition_start + self.partition_length
                ):
                    raise RuntimeError(f"UDF insertion payload is outside the partition: {path}")
                if not (
                    self.partition_start
                    <= file_entry_sector
                    < self.partition_start + self.partition_length
                ):
                    raise RuntimeError(f"UDF insertion ICB is outside the partition: {path}")
                data_lbn = absolute_extent - self.partition_start
                file_entry_lbn = file_entry_sector - self.partition_start
                file_entry = self._updated_file_entry(
                    template_data,
                    information_length=size,
                    logical_blocks=(size + BLOCK_SIZE - 1) // BLOCK_SIZE,
                    data_lbn=data_lbn,
                    unique_id=next_unique_id,
                    tag_location=file_entry_lbn,
                )
                if len(file_entry) > BLOCK_SIZE:
                    raise RuntimeError(f"UDF File Entry exceeds one block: {path}")
                if any(self._read_absolute_block(file_entry_sector)):
                    raise RuntimeError(f"UDF insertion ICB sector is not zero: {path}")
                block = file_entry + b"\0" * (BLOCK_SIZE - len(file_entry))
                new_file_entry_writes.append(
                    UdfWrite(
                        file_entry_sector * BLOCK_SIZE,
                        b"\0" * BLOCK_SIZE,
                        block,
                        f"UDF File Entry for {path}",
                    )
                )

                identifier = self._file_identifier(
                    name=path.rsplit("/", 1)[-1],
                    icb_length=len(file_entry),
                    icb_lbn=file_entry_lbn,
                    tag_location=parent.data_lbn + cursor // BLOCK_SIZE,
                )
                remaining = BLOCK_SIZE - cursor % BLOCK_SIZE
                if len(identifier) > remaining:
                    cursor += remaining
                end = cursor + len(identifier)
                if end > len(directory):
                    raise RuntimeError(
                        f"UDF directory has no FID capacity for {path}: "
                        f"{parent_path or '/'} uses {parent.information_length}/"
                        f"{len(directory)} bytes"
                    )
                if any(directory[cursor:end]):
                    raise RuntimeError(f"UDF directory append area is not zero: {path}")
                directory[cursor:end] = identifier
                insertion_results.append(
                    UdfInsertion(
                        path=path,
                        file_entry_offset=file_entry_sector * BLOCK_SIZE,
                        directory_record_offset=(
                            self.partition_start + parent.data_lbn
                        ) * BLOCK_SIZE + cursor,
                    )
                )
                cursor = end
                next_unique_id += 1

            _, parent_entry = file_entry_buffer(parent_path)
            updated_parent = self._updated_file_entry(
                bytes(parent_entry),
                information_length=cursor,
                logical_blocks=parent.logical_blocks_recorded,
                data_lbn=parent.data_lbn,
                unique_id=parent.unique_id,
                tag_location=parent.icb_lbn,
            )
            parent_entry[:] = updated_parent

        writes: list[UdfWrite] = []
        for path in sorted(directory_buffers):
            record = self.by_path[path]
            original, replacement = directory_buffers[path]
            if bytes(replacement) != original:
                writes.append(
                    UdfWrite(
                        (self.partition_start + record.data_lbn) * BLOCK_SIZE,
                        original,
                        bytes(replacement),
                        f"UDF directory metadata for {path or '/'}",
                    )
                )
        for path in sorted(file_entry_buffers):
            record = self.by_path[path]
            original, replacement = file_entry_buffers[path]
            if bytes(replacement) != original:
                writes.append(
                    UdfWrite(
                        record.file_entry_offset,
                        original,
                        bytes(replacement),
                        f"UDF File Entry metadata for {path or '/'}",
                    )
                )
        writes.extend(new_file_entry_writes)

        if normalized_insertions:
            actual_file_count = sum(not record.is_dir for record in self.records)
            actual_directory_count = sum(record.is_dir for record in self.records)
            integrity = bytearray(self.integrity)
            if self.recorded_file_count == actual_file_count:
                _set_u32(
                    integrity,
                    self.integrity_implementation_offset + 32,
                    actual_file_count + len(normalized_insertions),
                )
            elif self.recorded_file_count != 0:
                raise RuntimeError("UDF integrity file count is stale")
            if self.recorded_directory_count not in (0, actual_directory_count):
                raise RuntimeError("UDF integrity directory count is stale")
            _refresh_tag(integrity, 0)
            if bytes(integrity) != self.integrity:
                writes.append(
                    UdfWrite(
                        self.integrity_sector * BLOCK_SIZE,
                        self.integrity,
                        bytes(integrity),
                        "UDF Logical Volume Integrity counts",
                    )
                )

        return UdfPlan(
            writes=tuple(writes),
            insertions=tuple(insertion_results),
            renames=tuple(rename_results),
        )
