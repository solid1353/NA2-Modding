from __future__ import annotations

import struct
from dataclasses import dataclass


ELF32_HEADER_SIZE = 52
ELF32_PROGRAM_HEADER_SIZE = 32
ELF32_SECTION_HEADER_SIZE = 40
SHT_NOBITS = 8


@dataclass(frozen=True)
class ElfCrcDiscriminatorEdit:
    offset: int
    original: bytes
    replacement: bytes


def _checked_range(offset: int, size: int, length: int, label: str) -> tuple[int, int]:
    if offset < 0 or size < 0 or offset + size > length:
        raise ValueError(f"Boot ELF {label} exceeds the file")
    return offset, offset + size


def _overlaps(start: int, end: int, occupied: list[tuple[int, int]]) -> bool:
    return any(start < occupied_end and occupied_start < end for occupied_start, occupied_end in occupied)


def apply_elf_crc_discriminator(
    data: bytes | bytearray,
    discriminator: int,
) -> tuple[bytearray, ElfCrcDiscriminatorEdit | None]:
    """Change one runtime-unloaded zero word so PCSX2 assigns a distinct ELF CRC."""

    if discriminator < 0 or discriminator > 0xFFFFFFFF:
        raise ValueError("Boot ELF CRC discriminator must fit in an unsigned 32-bit word")
    result = bytearray(data)
    if discriminator == 0:
        return result, None
    if len(result) < ELF32_HEADER_SIZE or result[:7] != b"\x7fELF\x01\x01\x01":
        raise ValueError("Boot ELF must be ELF32 little-endian")

    (
        _ident,
        _type,
        _machine,
        _version,
        _entry,
        program_offset,
        section_offset,
        _flags,
        header_size,
        program_entry_size,
        program_count,
        section_entry_size,
        section_count,
        _section_names,
    ) = struct.unpack_from("<16sHHIIIIIHHHHHH", result, 0)
    if header_size != ELF32_HEADER_SIZE:
        raise ValueError(f"Unexpected boot ELF header size: {header_size}")
    if program_count and program_entry_size != ELF32_PROGRAM_HEADER_SIZE:
        raise ValueError(f"Unexpected boot ELF program-header size: {program_entry_size}")
    if section_count and section_entry_size != ELF32_SECTION_HEADER_SIZE:
        raise ValueError(f"Unexpected boot ELF section-header size: {section_entry_size}")

    occupied = [_checked_range(0, header_size, len(result), "header")]
    if program_count:
        occupied.append(
            _checked_range(
                program_offset,
                program_entry_size * program_count,
                len(result),
                "program-header table",
            )
        )
        for index in range(program_count):
            fields = struct.unpack_from(
                "<IIIIIIII",
                result,
                program_offset + index * program_entry_size,
            )
            file_offset = fields[1]
            file_size = fields[4]
            if file_size:
                occupied.append(
                    _checked_range(
                        file_offset,
                        file_size,
                        len(result),
                        f"program segment {index}",
                    )
                )
    if section_count:
        occupied.append(
            _checked_range(
                section_offset,
                section_entry_size * section_count,
                len(result),
                "section-header table",
            )
        )
        for index in range(section_count):
            fields = struct.unpack_from(
                "<IIIIIIIIII",
                result,
                section_offset + index * section_entry_size,
            )
            section_type = fields[1]
            file_offset = fields[4]
            file_size = fields[5]
            if file_size and section_type != SHT_NOBITS:
                occupied.append(
                    _checked_range(
                        file_offset,
                        file_size,
                        len(result),
                        f"section {index}",
                    )
                )

    replacement = discriminator.to_bytes(4, "little")
    for offset in range((len(result) - 4) & ~3, -1, -4):
        end = offset + 4
        if _overlaps(offset, end, occupied) or result[offset:end] != b"\0\0\0\0":
            continue
        original = bytes(result[offset:end])
        result[offset:end] = replacement
        return result, ElfCrcDiscriminatorEdit(
            offset=offset,
            original=original,
            replacement=replacement,
        )

    raise ValueError("Boot ELF has no aligned runtime-unloaded zero word for a CRC discriminator")
