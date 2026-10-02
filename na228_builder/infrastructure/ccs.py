"""Decompressed CCS section walking and texture lookup."""

from __future__ import annotations

import struct
from collections import defaultdict
from dataclasses import dataclass


SECTION_TOC = 0xCCCC0002
SECTION_TEXTURE = 0xCCCC0300
SECTION_PALETTE = 0xCCCC0400
SECTION_MODEL = 0xCCCC0800
KNOWN_SECTION_TYPES = {
    0xCCCC0001, 0xCCCC0002, 0xCCCC0003, 0xCCCC0005,
    0xCCCC0100, 0xCCCC0102, 0xCCCC0108, 0xCCCC0200,
    0xCCCC0202, 0xCCCC0300, 0xCCCC0400, 0xCCCC0500,
    0xCCCC0502, 0xCCCC0600, 0xCCCC0601, 0xCCCC0603,
    0xCCCC0609, 0xCCCC0700, 0xCCCC0800, 0xCCCC0900,
    0xCCCC0A00, 0xCCCC0B00, 0xCCCC0C00, 0xCCCC0D00,
    0xCCCC0E00, 0xCCCC1000, 0xCCCC1100, 0xCCCC1200,
    0xCCCC1300, 0xCCCC1400, 0xCCCC1700, 0xCCCC1800,
    0xCCCC1900, 0xCCCC1901, 0xCCCC2000, 0xCCCC2200,
    0xCCCC2400, 0xCCCCFF01,
}


@dataclass(frozen=True)
class Section:
    section_type: int
    offset: int
    total_size: int
    object_id: int | None
    object_name: str | None

    @property
    def data_offset(self) -> int:
        return self.offset + 12

    @property
    def data_size(self) -> int:
        return self.total_size - 12


@dataclass(frozen=True)
class TextureEntry:
    name: str
    textures: tuple[Section, ...]
    palettes: tuple[Section, ...]


def read_u32(data: bytes | bytearray, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def read_c_string(data: bytes, offset: int, size: int) -> str:
    return data[offset : offset + size].split(b"\0", 1)[0].decode("ascii", "replace")


def parse_toc(data: bytes, offset: int) -> tuple[int, list[str], list[str], list[int]]:
    size_words = read_u32(data, offset + 4)
    file_count = read_u32(data, offset + 8) - 1
    object_count = read_u32(data, offset + 12) - 1
    toc_data = data[offset + 16 : offset + 16 + size_words * 4]
    cursor = 0x20
    filenames = []
    for _ in range(file_count):
        filenames.append(read_c_string(toc_data, cursor, 0x20).strip())
        cursor += 0x20
    cursor += 0x20
    object_names = []
    file_indexes = []
    for _ in range(object_count):
        object_names.append(read_c_string(toc_data, cursor, 0x1E).strip())
        file_indexes.append(struct.unpack_from("<H", toc_data, cursor + 0x1E)[0])
        cursor += 0x20
    return 16 + size_words * 4, filenames, object_names, file_indexes


def section_total_size(data: bytes, offset: int, section_type: int, size_words: int) -> int:
    if section_type == SECTION_TOC:
        return 16 + size_words * 4
    if section_type == SECTION_TEXTURE:
        if size_words < 51:
            raise ValueError(f"Texture section at 0x{offset:X} is smaller than 51 words")
        return 12 + (size_words - 51) * 4
    if section_type == SECTION_MODEL:
        cursor = offset + 12
        while cursor + 4 <= len(data):
            if read_u32(data, cursor) in KNOWN_SECTION_TYPES:
                return cursor - offset
            cursor += 4
        raise ValueError(f"Could not locate the section after model at 0x{offset:X}")
    return 8 + size_words * 4


def parse_ccs(payload: bytes | bytearray) -> dict[str, TextureEntry]:
    """Map each casefolded `.bmp` filename to its TEX and CLT sections."""
    data = bytes(payload)
    filenames: list[str] | None = None
    object_names: list[str] = []
    file_indexes: list[int] = []
    cursor = 0
    while cursor + 8 <= len(data):
        section_type = read_u32(data, cursor)
        size_words = read_u32(data, cursor + 4)
        if section_type == SECTION_TOC:
            _, filenames, object_names, file_indexes = parse_toc(data, cursor)
            break
        cursor += section_total_size(data, cursor, section_type, size_words)
    if filenames is None:
        raise ValueError("CCS has no TOC section")

    sections_by_object: dict[int, list[Section]] = defaultdict(list)
    cursor = 0
    while cursor + 8 <= len(data):
        section_type = read_u32(data, cursor)
        size_words = read_u32(data, cursor + 4)
        total_size = section_total_size(data, cursor, section_type, size_words)
        if total_size <= 0 or cursor + total_size > len(data):
            raise ValueError(f"Invalid CCS section at 0x{cursor:X}")
        object_id = None if section_type == SECTION_TOC or not size_words else read_u32(data, cursor + 8)
        object_name = None
        if object_id is not None and 1 <= object_id <= len(object_names):
            object_name = object_names[object_id - 1]
            sections_by_object[object_id].append(
                Section(section_type, cursor, total_size, object_id, object_name)
            )
        cursor += total_size
    if cursor != len(data):
        raise ValueError(f"CCS section walk ended at 0x{cursor:X}, expected 0x{len(data):X}")

    object_ids_by_file: dict[int, list[int]] = defaultdict(list)
    for object_id, file_index in enumerate(file_indexes, 1):
        object_ids_by_file[file_index].append(object_id)
    result: dict[str, TextureEntry] = {}
    for file_index, filename in enumerate(filenames, 1):
        if not filename.casefold().endswith(".bmp"):
            continue
        textures = []
        palettes = []
        for object_id in object_ids_by_file[file_index]:
            for section in sections_by_object.get(object_id, []):
                if section.section_type == SECTION_TEXTURE:
                    textures.append(section)
                elif section.section_type == SECTION_PALETTE:
                    palettes.append(section)
        key = filename.casefold()
        if key in result:
            raise ValueError(f"Duplicate CCS texture filename {filename!r}")
        result[key] = TextureEntry(filename, tuple(textures), tuple(palettes))
    return result
