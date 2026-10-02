from __future__ import annotations

from pathlib import Path

from ..modules.image_assembler.iso9660 import Iso9660, IsoRecord, SECTOR


ROFS_PASSWORD = "cc2fuku"
_ROFS_PRIME_START = 16411
_ROFS_PRIME_COUNT = 1024
_ROFS_TOC_ENCRYPTED = 0x10


class CvmError(RuntimeError):
    """Raised when a CVM/ROFS image cannot be read safely."""


def _is_prime(value: int) -> bool:
    if value < 2:
        return False
    if value % 2 == 0:
        return value == 2
    divisor = 3
    while divisor * divisor <= value:
        if value % divisor == 0:
            return False
        divisor += 2
    return True


def _make_rofs_primes() -> tuple[int, ...]:
    # The ROFS table is exactly the first 1024 consecutive primes beginning at
    # 16411. Generating it keeps the reader self-contained and avoids a runtime
    # dependency on the historical CVM utility source tree.
    result: list[int] = []
    candidate = _ROFS_PRIME_START
    while len(result) < _ROFS_PRIME_COUNT:
        if _is_prime(candidate):
            result.append(candidate)
        candidate += 1
    return tuple(result)


_ROFS_PRIMES = _make_rofs_primes()

_SCRAMBLE_SPECS = (
    "^03 .0 37 .4 .1 26 .2 15",
    "^12 .7 .5 23 00 .6 .4 31",
    "^.1 27 .6 12 35 .3 00 .4",
    "+23 .6 .0 .2 04 11 .7 35",
    "+.7 30 02 16 .4 .3 .5 21",
    "+.2 23 .6 07 .0 11 .4 35",
    "+03 .7^12 .6 .1 25 .0+34",
    " .7^34 .3+21 .0 .2 15^06",
    " .3^10 .6+04^32 .7 .1+25",
)


def _compile_scramble(spec: str) -> tuple[tuple[str, int | None, int], ...]:
    result: list[tuple[str, int | None, int]] = []
    offset = 0
    operation = "^"
    for _ in range(8):
        while offset < len(spec) and spec[offset] == " ":
            offset += 1
        if offset < len(spec) and spec[offset] in "^+":
            operation = spec[offset]
            offset += 1
        if offset + 2 > len(spec):
            raise AssertionError(f"Invalid ROFS scramble specification: {spec!r}")
        hash_character = spec[offset]
        key_character = spec[offset + 1]
        offset += 2
        hash_index = None if hash_character == "." else int(hash_character)
        result.append((operation, hash_index, int(key_character)))
    return tuple(result)


_SCRAMBLES = tuple(_compile_scramble(spec) for spec in _SCRAMBLE_SPECS)


def _hash_values(data: bytes) -> tuple[int, int, int]:
    values = []
    for initial in (18973, 21503, 24001):
        value = initial
        for item in data:
            product = _ROFS_PRIMES[(item + 128) & 0xFF] * value
            value = _ROFS_PRIMES[product & 0x3FF]
        values.append(value)
    return values[0], values[1], values[2]


def _rofs_key(password: str) -> bytes:
    try:
        characters = password.encode("ascii")
    except UnicodeEncodeError as error:
        raise ValueError("ROFS password must contain only ASCII characters") from error

    total = 0
    for index, character in enumerate(characters):
        total = character * (character + total) & 0xFFFFFFFF
        for following in characters[index + 1 :]:
            total = (total + following) & 0xFFFFFFFF

    seed = 0x100001 * total & 0xFFFFFFFF
    seed_bytes = seed.to_bytes(4, "big")
    key = bytearray(8)
    for index in range(4):
        key[index * 2] = seed_bytes[index]
        key[index * 2 + 1] = seed_bytes[3 - index]

    for index in range(4):
        value, _, _ = _hash_values(bytes(key[index * 2 : index * 2 + 2]))
        key[index * 2 : index * 2 + 2] = value.to_bytes(2, "big")
    return bytes(key)


def _sector_hash(seed: int) -> tuple[int, bytes]:
    value = 0x100001 * (seed & 0xFFFFFFFF) & 0xFFFFFFFF
    first, second, third = _hash_values(value.to_bytes(4, "big"))
    return first % len(_SCRAMBLES), second.to_bytes(2, "big") + third.to_bytes(2, "big")


def _local_key(key: bytes, hash_bytes: bytes, index: int) -> bytes:
    result = bytearray(8)
    for output, (operation, hash_index, key_index) in enumerate(_SCRAMBLES[index]):
        value = key[key_index]
        if hash_index is not None:
            if operation == "^":
                value ^= hash_bytes[hash_index]
            else:
                value = (value + hash_bytes[hash_index]) & 0xFF
        result[output] = value
    return bytes(result)


def _crypt_sector(data: bytes, logical_sector: int, key: bytes) -> bytes:
    if len(data) != SECTOR:
        raise ValueError(f"ROFS sectors must be exactly {SECTOR} bytes")
    result = bytearray(data)
    seed = key[5]
    for offset in range(0, SECTOR, 8):
        scramble_index, hash_bytes = _sector_hash(logical_sector * seed)
        local_key = _local_key(key, hash_bytes, scramble_index)
        seed = scramble_index + offset
        for index, key_byte in enumerate(local_key):
            result[offset + index] ^= key_byte
            seed = seed * key_byte & 0xFFFFFFFF
    return bytes(result)


_ROFS_KEY = _rofs_key(ROFS_PASSWORD)


class CvmIso(Iso9660):
    """Read the ISO9660 image stored in a CVM/ROFS container without extraction.

    ``path`` may name a standalone CVM or a larger image containing one. In the
    latter case, ``cvm_offset`` and ``cvm_size`` bound every read to that member.
    The public ISO view matches the maintained splitter: encrypted volume and
    directory sectors are decrypted, while ordinary member payloads remain
    byte-for-byte views into the container. Record extents include the
    extended-attribute length, and ``file_size`` bounds records to the inner ISO.
    """

    def __init__(
        self,
        path: Path,
        *,
        cvm_offset: int = 0,
        cvm_size: int | None = None,
    ) -> None:
        self.path = Path(path)
        if not self.path.is_file():
            raise FileNotFoundError(self.path)

        image_size = self.path.stat().st_size
        if cvm_offset < 0 or cvm_offset > image_size:
            raise ValueError(f"CVM offset is outside the image: {cvm_offset}")
        if cvm_size is None:
            cvm_size = image_size - cvm_offset
        if cvm_size < 0 or cvm_size > image_size - cvm_offset:
            raise ValueError(
                "CVM range is outside the image: "
                f"offset={cvm_offset}, size={cvm_size}"
            )

        self.cvm_offset = cvm_offset
        self.cvm_size = cvm_size
        self.end_toc_sector = 0

        chunk = self._read_cvm_bytes(0, 12, "CVMH chunk header")
        if chunk[:4] != b"CVMH":
            raise CvmError("CVMH chunk not found at the start of the CVM")
        cvmh_length = int.from_bytes(chunk[4:12], "big")
        if cvmh_length < 0x80:
            raise CvmError(f"CVMH payload is too short: {cvmh_length}")
        cvmh = self._read_cvm_bytes(12, cvmh_length, "CVMH payload")
        self.iso_start_sector = int.from_bytes(cvmh[0x7C:0x80], "big")
        self.toc_encrypted = bool(
            int.from_bytes(cvmh[0x24:0x28], "big") & _ROFS_TOC_ENCRYPTED
        )

        zone_header_offset = 12 + cvmh_length
        zone_header = self._read_cvm_bytes(zone_header_offset, 12, "ZONE chunk header")
        if zone_header[:4] != b"ZONE":
            raise CvmError("ZONE chunk not found after the CVMH chunk")
        zone_length = int.from_bytes(zone_header[4:12], "big")
        zone_payload_offset = zone_header_offset + 12
        if zone_length < 0x2C:
            raise CvmError(f"ZONE payload is too short: {zone_length}")
        if zone_length > self.cvm_size - zone_payload_offset:
            raise CvmError("ZONE chunk extends outside the CVM")
        zone = self._read_cvm_bytes(zone_payload_offset, 0x2C, "ZONE fixed header")
        self.iso_zone_sector = int.from_bytes(zone[0x20:0x24], "big")
        self.iso_length = int.from_bytes(zone[0x24:0x2C], "big")
        self.sector_count, remainder = divmod(self.iso_length, SECTOR)
        if self.sector_count <= 16 or remainder:
            raise CvmError(f"Invalid inner ISO length: {self.iso_length}")

        self.header_size = self.iso_start_sector * SECTOR
        iso_end = self.header_size + self.iso_length
        zone_end = zone_payload_offset + zone_length
        if self.header_size < zone_payload_offset or iso_end > zone_end or iso_end > self.cvm_size:
            raise CvmError("Inner ISO range extends outside the CVM ZONE chunk")
        self.file_size = self.iso_length
        self.header = self._read_cvm_bytes(0, self.header_size, "CVM header")

        primary, primary_offset = self._read_primary_volume_descriptor()
        self.end_toc_sector = primary_offset // SECTOR + 1
        self._read_tree(primary, None)

    @classmethod
    def from_iso(cls, iso: Iso9660) -> CvmIso:
        """Open DATA/DATA.CVM directly from an already parsed outer ISO."""
        record = iso.by_path.get("DATA/DATA.CVM")
        if record is None or record.is_dir:
            raise FileNotFoundError("Outer ISO has no CVM file DATA/DATA.CVM")
        return cls(iso.path, cvm_offset=record.byte_offset, cvm_size=record.size)

    def _read_cvm_bytes(self, offset: int, size: int, context: str) -> bytes:
        if offset < 0 or size < 0 or offset > self.cvm_size or size > self.cvm_size - offset:
            raise CvmError(f"{context} is outside the CVM")
        with self.path.open("rb") as handle:
            handle.seek(self.cvm_offset + offset)
            data = handle.read(size)
        if len(data) != size:
            raise CvmError(f"Unexpected EOF while reading {context}")
        return data

    def _transform_iso_bytes(self, offset: int, size: int, *, toc_only: bool) -> bytes:
        if offset < 0 or size < 0 or offset > self.iso_length or size > self.iso_length - offset:
            raise CvmError(f"Inner ISO range is outside the image: offset={offset}, size={size}")
        if size == 0:
            return b""

        first_sector = offset // SECTOR
        final_sector = (offset + size + SECTOR - 1) // SECTOR
        aligned_offset = first_sector * SECTOR
        data = bytearray(
            self._read_cvm_bytes(
                self.header_size + aligned_offset,
                (final_sector - first_sector) * SECTOR,
                "inner ISO data",
            )
        )
        if self.toc_encrypted:
            for sector in range(first_sector, final_sector):
                if toc_only or 16 <= sector < self.end_toc_sector:
                    local_offset = (sector - first_sector) * SECTOR
                    logical_sector = sector + self.iso_zone_sector - self.iso_start_sector
                    data[local_offset : local_offset + SECTOR] = _crypt_sector(
                        bytes(data[local_offset : local_offset + SECTOR]),
                        logical_sector,
                        _ROFS_KEY,
                    )

        start = offset - aligned_offset
        return bytes(data[start : start + size])

    def _read_toc_bytes(self, offset: int, size: int) -> bytes:
        return self._transform_iso_bytes(offset, size, toc_only=True)

    def _read_primary_volume_descriptor(self) -> tuple[bytes, int]:
        for sector in range(16, min(128, self.sector_count)):
            descriptor = self._read_toc_bytes(sector * SECTOR, SECTOR)
            if descriptor[1:6] != b"CD001" or descriptor[6] != 1:
                continue
            if descriptor[0] == 1:
                return descriptor, sector * SECTOR
            if descriptor[0] == 255:
                break
        suffix = "; the password may be wrong" if self.toc_encrypted else ""
        raise CvmError(f"Inner ISO9660 primary volume descriptor not found{suffix}")

    def _record_extent(self, raw: bytes, context: str) -> int:
        return super()._record_extent(raw, context) + raw[1]

    def _directory_data(self, directory: IsoRecord) -> bytes:
        data = self._read_toc_bytes(directory.byte_offset, directory.size)
        self.end_toc_sector = max(
            self.end_toc_sector,
            (directory.byte_offset + directory.size + SECTOR - 1) // SECTOR,
        )
        return data

    def read_iso_bytes(self, offset: int, size: int) -> bytes:
        """Read bytes from the logical, TOC-decrypted inner ISO image."""
        return self._transform_iso_bytes(offset, size, toc_only=False)

    def read_file(self, record: IsoRecord) -> bytes:
        return self.read_iso_bytes(record.byte_offset, record.size)
