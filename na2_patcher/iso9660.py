from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

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
