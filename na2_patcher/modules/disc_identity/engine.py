from __future__ import annotations

import csv
import os
import re
from dataclasses import dataclass
from pathlib import Path

from ...iso9660 import Iso9660


IDENTITY_FIELDS = ["source_boot_path", "replacement_boot_path", "reason"]
BOOT_PATH_PATTERN = re.compile(
    r"^(?P<prefix>[A-Z]{4})_(?P<first>[0-9]{3})\.(?P<last>[0-9]{2})$"
)


@dataclass(frozen=True)
class DiscIdentity:
    source_boot_path: str
    replacement_boot_path: str
    reason: str

    @property
    def source_serial(self) -> str:
        return serial_from_boot_path(self.source_boot_path)

    @property
    def replacement_serial(self) -> str:
        return serial_from_boot_path(self.replacement_boot_path)


def serial_from_boot_path(path: str) -> str:
    match = BOOT_PATH_PATTERN.fullmatch(path)
    if match is None:
        raise ValueError(f"Invalid PS2 boot executable name: {path!r}")
    return f"{match.group('prefix')}-{match.group('first')}{match.group('last')}"


def load_identity(path: Path) -> DiscIdentity:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != IDENTITY_FIELDS:
            raise ValueError(
                f"{path}: expected columns " + "\t".join(IDENTITY_FIELDS)
            )
        rows = [
            {key: (value or "").strip() for key, value in row.items()}
            for row in reader
            if any((value or "").strip() for value in row.values())
        ]
    if len(rows) != 1:
        raise ValueError(f"{path}: expected exactly one disc-identity row")

    identity = DiscIdentity(**rows[0])
    serial_from_boot_path(identity.source_boot_path)
    serial_from_boot_path(identity.replacement_boot_path)
    if identity.source_boot_path == identity.replacement_boot_path:
        raise ValueError(f"{path}: source and replacement boot paths are identical")
    if len(identity.source_boot_path.encode("ascii")) != len(
        identity.replacement_boot_path.encode("ascii")
    ):
        raise ValueError(f"{path}: boot executable names must have equal byte lengths")
    if not identity.reason:
        raise ValueError(f"{path}: reason is required")
    return identity


def apply_system_cnf(
    identity: DiscIdentity,
    data: bytes | bytearray,
) -> tuple[bytearray, dict[str, object]]:
    source = identity.source_boot_path.encode("ascii")
    replacement = identity.replacement_boot_path.encode("ascii")
    current = bytes(data)
    if current.count(source) != 1:
        raise RuntimeError(
            "SYSTEM.CNF must contain the source boot executable exactly once: "
            f"{identity.source_boot_path}"
        )
    offset = current.index(source)
    updated = bytearray(current)
    updated[offset:offset + len(source)] = replacement
    if len(updated) != len(current):
        raise AssertionError("Disc-identity SYSTEM.CNF edit changed the file size")
    return updated, {
        "target": "SYSTEM.CNF",
        "offset": f"0x{offset:X}",
        "length": len(source),
        "original_hex": source.hex().upper(),
        "new_hex": replacement.hex().upper(),
        "reason": identity.reason,
    }


def apply_iso_directory_identifier(
    identity: DiscIdentity,
    iso: Iso9660,
) -> dict[str, object]:
    source_record = iso.by_path.get(identity.source_boot_path)
    if source_record is None or source_record.is_dir:
        raise RuntimeError(
            f"Source boot executable is not in the ISO: {identity.source_boot_path}"
        )
    if identity.replacement_boot_path in iso.by_path:
        raise RuntimeError(
            f"Replacement boot executable already exists: {identity.replacement_boot_path}"
        )
    if source_record.directory_record_offset is None:
        raise RuntimeError("Boot executable lacks an ISO directory-record offset")

    record_offset = source_record.directory_record_offset
    source = f"{identity.source_boot_path};1".encode("ascii")
    replacement = f"{identity.replacement_boot_path};1".encode("ascii")
    if len(source) != len(replacement):
        raise AssertionError("ISO directory identifiers differ in length")

    with iso.path.open("r+b") as handle:
        handle.seek(record_offset)
        header = handle.read(33)
        if len(header) != 33 or header[0] < 34:
            raise RuntimeError("Invalid boot executable ISO directory record")
        name_length = header[32]
        if name_length != len(source):
            raise RuntimeError(
                "Unexpected boot executable ISO identifier length: "
                f"expected {len(source)}, found {name_length}"
            )
        actual = handle.read(name_length)
        if actual != source:
            raise RuntimeError(
                "Boot executable ISO identifier mismatch: "
                f"expected {source!r}, found {actual!r}"
            )
        identifier_offset = record_offset + 33
        handle.seek(identifier_offset)
        handle.write(replacement)
        handle.flush()
        os.fsync(handle.fileno())

    return {
        "target": "<ISO9660 root directory>",
        "offset": f"0x{identifier_offset:X}",
        "length": len(source),
        "original_hex": source.hex().upper(),
        "new_hex": replacement.hex().upper(),
        "reason": identity.reason,
    }
