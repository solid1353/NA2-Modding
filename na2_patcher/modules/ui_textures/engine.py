from __future__ import annotations

import argparse
import binascii
import csv
import gzip
import hashlib
import json
import re
import struct
import zlib
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from ...iso9660 import Iso9660
from ...project_paths import load_project_paths, resolve_alias

try:
    import zopfli.gzip as zopfli_gzip
except ImportError:
    zopfli_gzip = None


CONTAINER_FIELDS = [
    "container_id",
    "path",
    "target_sha256",
    "donor_sha256",
]
MAPPING_FIELDS = [
    "mapping_id",
    "enabled",
    "container_id",
    "target_texture",
    "donor_texture",
    "transform",
    "reason",
]
STRATEGY_FIELDS = [
    "container_id",
    "strategy",
    "replacement_sha256",
    "payload_sha256",
    "reason",
]
SECTION_TOC = 0xCCCC0002
SECTION_TEXTURE = 0xCCCC0300
SECTION_PALETTE = 0xCCCC0400
SECTION_MODEL = 0xCCCC0800
VALID_STRATEGIES = {"whole", "mapped"}
VALID_TRANSFORMS = {"copy", "split_left", "split_right", "indexed_top_rows_64"}
INDEXED_TOP_ROWS = re.compile(r"indexed_top_rows_([1-9][0-9]*)")
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


def sha256(data: bytes | bytearray) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def read_u32(data: bytes | bytearray, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def read_c_string(data: bytes, offset: int, size: int) -> str:
    return data[offset : offset + size].split(b"\0", 1)[0].decode("ascii", "replace")


def read_tsv(path: Path, fields: list[str]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != fields:
            raise ValueError(f"{path}: expected columns " + "\t".join(fields))
        return [
            {key: (value or "").strip() for key, value in row.items()}
            for row in reader
            if any((value or "").strip() for value in row.values())
        ]


def checked_relative_path(value: str, label: str) -> str:
    candidate = Path(value.replace("\\", "/"))
    if not value or candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"{label} must be a relative path: {value!r}")
    return candidate.as_posix()


def checked_hash(value: str, label: str) -> str:
    result = value.upper()
    if len(result) != 64 or any(char not in "0123456789ABCDEF" for char in result):
        raise ValueError(f"{label} must be 64 hexadecimal digits")
    return result


@dataclass(frozen=True)
class ContainerSpec:
    container_id: str
    path: str
    target_sha256: str
    donor_sha256: str


@dataclass(frozen=True)
class Mapping:
    mapping_id: str
    container_id: str
    target_texture: str
    donor_texture: str
    transform: str
    reason: str


@dataclass(frozen=True)
class Strategy:
    container_id: str
    strategy: str
    replacement_sha256: str
    payload_sha256: str
    reason: str


@dataclass(frozen=True)
class Package:
    directory: Path
    containers: dict[str, ContainerSpec]
    mappings: tuple[Mapping, ...]
    strategies: dict[str, Strategy]


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


@dataclass(frozen=True)
class ContainerResult:
    spec: ContainerSpec
    strategy: Strategy
    original: bytes
    donor: bytes
    replacement: bytes
    payload_sha256: str
    compressed_stream_size: int
    padding_size: int
    outer_cvm_offset: int
    mapping_ids: tuple[str, ...]


@dataclass(frozen=True)
class UiTexturePlan:
    package: Package
    containers: tuple[ContainerResult, ...]
    target_header: bytes

    def apply_to_cvm(self, cvm: bytearray) -> None:
        if bytes(cvm[: len(self.target_header)]) != self.target_header:
            raise RuntimeError("DATA.CVM header does not match the pinned NA2 extraction")
        for result in self.containers:
            start = result.outer_cvm_offset
            end = start + len(result.original)
            actual = bytes(cvm[start:end])
            if actual != result.original:
                raise RuntimeError(
                    f"DATA.CVM conflict for {result.spec.path} at 0x{start:X}: "
                    f"found SHA-256 {sha256(actual)}, expected {sha256(result.original)}"
                )
            cvm[start:end] = result.replacement

    @property
    def mapping_count(self) -> int:
        return sum(len(result.mapping_ids) for result in self.containers)


def load_package(directory: Path) -> Package:
    directory = directory.resolve()
    container_rows = read_tsv(directory / "containers.tsv", CONTAINER_FIELDS)
    mapping_rows = read_tsv(directory / "mappings.tsv", MAPPING_FIELDS)
    strategy_rows = read_tsv(directory / "strategies.tsv", STRATEGY_FIELDS)

    containers: dict[str, ContainerSpec] = {}
    paths: set[str] = set()
    for line, row in enumerate(container_rows, 2):
        label = f"containers.tsv line {line}"
        container_id = row["container_id"]
        if not container_id or container_id in containers:
            raise ValueError(f"{label}: duplicate or empty container_id")
        path = checked_relative_path(row["path"], label)
        if path.casefold() in paths:
            raise ValueError(f"{label}: duplicate path {path!r}")
        paths.add(path.casefold())
        containers[container_id] = ContainerSpec(
            container_id=container_id,
            path=path,
            target_sha256=checked_hash(row["target_sha256"], label),
            donor_sha256=checked_hash(row["donor_sha256"], label),
        )

    strategies: dict[str, Strategy] = {}
    for line, row in enumerate(strategy_rows, 2):
        label = f"strategies.tsv line {line}"
        container_id = row["container_id"]
        if container_id not in containers:
            raise ValueError(f"{label}: unknown container_id {container_id!r}")
        if container_id in strategies:
            raise ValueError(f"{label}: duplicate container_id {container_id!r}")
        strategy = row["strategy"]
        if strategy not in VALID_STRATEGIES:
            raise ValueError(f"{label}: unsupported strategy {strategy!r}")
        strategies[container_id] = Strategy(
            container_id=container_id,
            strategy=strategy,
            replacement_sha256=checked_hash(row["replacement_sha256"], label),
            payload_sha256=checked_hash(row["payload_sha256"], label),
            reason=row["reason"],
        )
    missing_strategies = containers.keys() - strategies.keys()
    if missing_strategies:
        raise ValueError("Missing strategies for: " + ", ".join(sorted(missing_strategies)))

    mappings: list[Mapping] = []
    mapping_ids: set[str] = set()
    targets: set[tuple[str, str]] = set()
    for line, row in enumerate(mapping_rows, 2):
        label = f"mappings.tsv line {line}"
        if row["enabled"] not in {"0", "1"}:
            raise ValueError(f"{label}: enabled must be 0 or 1")
        mapping_id = row["mapping_id"]
        if not mapping_id or mapping_id in mapping_ids:
            raise ValueError(f"{label}: duplicate or empty mapping_id")
        mapping_ids.add(mapping_id)
        if row["enabled"] == "0":
            continue
        container_id = row["container_id"]
        if container_id not in containers:
            raise ValueError(f"{label}: unknown container_id {container_id!r}")
        transform = row["transform"]
        if transform not in VALID_TRANSFORMS:
            raise ValueError(f"{label}: unsupported transform {transform!r}")
        target_key = (container_id, row["target_texture"].casefold())
        if target_key in targets:
            raise ValueError(f"{label}: target texture is mapped more than once")
        targets.add(target_key)
        mappings.append(
            Mapping(
                mapping_id=mapping_id,
                container_id=container_id,
                target_texture=row["target_texture"],
                donor_texture=row["donor_texture"],
                transform=transform,
                reason=row["reason"],
            )
        )
    mapped_containers = {mapping.container_id for mapping in mappings}
    missing_mappings = containers.keys() - mapped_containers
    if missing_mappings:
        raise ValueError("Containers without enabled mappings: " + ", ".join(sorted(missing_mappings)))
    return Package(directory, containers, tuple(mappings), strategies)


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


def texture_dimensions(payload: bytes, section: Section) -> tuple[int, int]:
    data = payload[section.data_offset : section.data_offset + section.data_size]
    if len(data) < 0x18:
        raise ValueError(f"Truncated TEX section {section.object_name!r}")
    return 1 << data[0xC], 1 << data[0xD]


def component_signature(payload: bytes, entry: TextureEntry) -> tuple[object, ...]:
    return (
        tuple((*texture_dimensions(payload, part), part.data_size) for part in entry.textures),
        tuple(part.data_size for part in entry.palettes),
    )


def validate_mapping(
    mapping: Mapping,
    target_payload: bytes,
    donor_payload: bytes,
    target_entries: dict[str, TextureEntry],
    donor_entries: dict[str, TextureEntry],
) -> None:
    target = target_entries.get(mapping.target_texture.casefold())
    donor = donor_entries.get(mapping.donor_texture.casefold())
    if target is None:
        raise ValueError(f"{mapping.mapping_id}: target texture not found: {mapping.target_texture}")
    if donor is None:
        raise ValueError(f"{mapping.mapping_id}: donor texture not found: {mapping.donor_texture}")
    if mapping.transform in {"copy", "indexed_top_rows_64"}:
        if component_signature(target_payload, target) != component_signature(donor_payload, donor):
            raise ValueError(f"{mapping.mapping_id}: target and donor component layouts differ")
        return
    if len(target.textures) != 1 or len(donor.textures) != 1:
        raise ValueError(f"{mapping.mapping_id}: split relationship requires one TEX section")
    target_width, target_height = texture_dimensions(target_payload, target.textures[0])
    donor_width, donor_height = texture_dimensions(donor_payload, donor.textures[0])
    if donor_width != target_width * 2 or donor_height != target_height:
        raise ValueError(
            f"{mapping.mapping_id}: expected donor {target_width * 2}x{target_height}, "
            f"found {donor_width}x{donor_height}"
        )


def decoded_rgba(payload: bytes, entry: TextureEntry) -> tuple[int, int, bytes] | None:
    if len(entry.textures) != 1 or len(entry.palettes) != 1:
        return None
    texture = entry.textures[0]
    palette = entry.palettes[0]
    tex = payload[texture.data_offset : texture.data_offset + texture.data_size]
    clt = payload[palette.data_offset : palette.data_offset + palette.data_size]
    if len(tex) < 0x18 or len(clt) < 0x14 or (len(clt) - 0x10) % 4:
        return None
    colors = []
    for offset in range(0x10, len(clt), 4):
        red, green, blue, alpha = clt[offset : offset + 4]
        colors.append((red, green, blue, min(255, alpha * 255 // 128) if alpha <= 128 else alpha))
    width, height = 1 << tex[0xC], 1 << tex[0xD]
    encoded = tex[0x18:]
    indices: list[int]
    if len(encoded) * 2 == width * height:
        indices = [index for value in encoded for index in (value & 0x0F, value >> 4)]
    elif len(encoded) == width * height:
        indices = list(encoded)
    else:
        return None
    if indices and max(indices) >= len(colors):
        return None
    rgba = bytes(channel for index in indices for channel in colors[index])
    return width, height, rgba


def validate_visual_coverage(
    strategy: Strategy,
    mappings: list[Mapping],
    target_payload: bytes,
    donor_payload: bytes,
    target_entries: dict[str, TextureEntry],
    donor_entries: dict[str, TextureEntry],
) -> None:
    # A mapped container deliberately preserves every target visual that is not
    # named by a mapping. Whole-container imports still require declarations for
    # every decoded donor difference because they import the complete payload.
    if strategy.strategy == "mapped":
        return

    covered = {mapping.target_texture.casefold() for mapping in mappings}
    uncovered = []
    for name in sorted(target_entries.keys() & donor_entries.keys()):
        target = decoded_rgba(target_payload, target_entries[name])
        donor = decoded_rgba(donor_payload, donor_entries[name])
        if target is None or donor is None or target[:2] != donor[:2]:
            continue
        if target[2] != donor[2] and name not in covered:
            uncovered.append(target_entries[name].name)
    if uncovered:
        raise ValueError(
            f"{strategy.container_id}: donor contains uncovered decoded visual changes: "
            + ", ".join(uncovered)
        )


def palette_distance(left: tuple[int, int, int, int], right: tuple[int, int, int, int]) -> int:
    if left[3] == 0 and right[3] == 0:
        return 0
    return sum((left[index] - right[index]) ** 2 for index in range(4))


def indexed_top_rows_payload(
    target_payload: bytes,
    donor_payload: bytes,
    mapping: Mapping,
) -> bytes:
    match = INDEXED_TOP_ROWS.fullmatch(mapping.transform)
    if match is None:
        raise ValueError(f"{mapping.mapping_id}: invalid indexed-row transform")
    top_rows = int(match.group(1))
    target_entries = parse_ccs(target_payload)
    donor_entries = parse_ccs(donor_payload)
    target = target_entries[mapping.target_texture.casefold()]
    donor = donor_entries[mapping.donor_texture.casefold()]
    if len(target.textures) != 1 or len(target.palettes) != 1:
        raise ValueError(f"{mapping.mapping_id}: target requires one TEX and one CLT")
    if len(donor.textures) != 1 or len(donor.palettes) != 1:
        raise ValueError(f"{mapping.mapping_id}: donor requires one TEX and one CLT")

    target_tex_section = target.textures[0]
    donor_tex_section = donor.textures[0]
    target_clt_section = target.palettes[0]
    donor_clt_section = donor.palettes[0]
    target_tex = bytearray(
        target_payload[
            target_tex_section.data_offset : target_tex_section.data_offset + target_tex_section.data_size
        ]
    )
    donor_tex = donor_payload[
        donor_tex_section.data_offset : donor_tex_section.data_offset + donor_tex_section.data_size
    ]
    target_clt = target_payload[
        target_clt_section.data_offset : target_clt_section.data_offset + target_clt_section.data_size
    ]
    donor_clt = donor_payload[
        donor_clt_section.data_offset : donor_clt_section.data_offset + donor_clt_section.data_size
    ]
    width, height = 1 << target_tex[0xC], 1 << target_tex[0xD]
    donor_width, donor_height = 1 << donor_tex[0xC], 1 << donor_tex[0xD]
    if (width, height) != (donor_width, donor_height) or not (0 < top_rows <= height):
        raise ValueError(f"{mapping.mapping_id}: incompatible indexed-row dimensions")
    if len(target_tex) - 0x18 != width * height or len(donor_tex) - 0x18 != width * height:
        raise ValueError(f"{mapping.mapping_id}: indexed-row import requires 8-bit textures")
    if len(target_clt) != len(donor_clt) or (len(target_clt) - 0x10) % 4:
        raise ValueError(f"{mapping.mapping_id}: incompatible palettes")

    target_palette = [
        tuple(target_clt[offset : offset + 4])
        for offset in range(0x10, len(target_clt), 4)
    ]
    donor_palette = [
        tuple(donor_clt[offset : offset + 4])
        for offset in range(0x10, len(donor_clt), 4)
    ]
    palette_map = [
        min(
            range(len(target_palette)),
            key=lambda index: palette_distance(color, target_palette[index]),
        )
        for color in donor_palette
    ]
    first_raw_row = height - top_rows  # CCS TEX rows are stored bottom-to-top.
    for row in range(first_raw_row, height):
        start = 0x18 + row * width
        for index in range(start, start + width):
            target_tex[index] = palette_map[donor_tex[index]]

    result = bytearray(target_payload)
    result[
        target_tex_section.data_offset : target_tex_section.data_offset + target_tex_section.data_size
    ] = target_tex
    return bytes(result)


def copy_mapping_payload(
    target_payload: bytes,
    donor_payload: bytes,
    mapping: Mapping,
) -> bytes:
    """Copy one mapped texture's TEX/CLT data into the target CCS layout."""
    if mapping.transform != "copy":
        raise ValueError(f"{mapping.mapping_id}: copy payload requires transform=copy")

    target_entries = parse_ccs(target_payload)
    donor_entries = parse_ccs(donor_payload)
    validate_mapping(
        mapping,
        target_payload,
        donor_payload,
        target_entries,
        donor_entries,
    )
    target = target_entries[mapping.target_texture.casefold()]
    donor = donor_entries[mapping.donor_texture.casefold()]
    result = bytearray(target_payload)
    component_pairs = zip(
        target.textures + target.palettes,
        donor.textures + donor.palettes,
        strict=True,
    )
    for target_section, donor_section in component_pairs:
        target_start = target_section.data_offset
        target_end = target_start + target_section.data_size
        donor_start = donor_section.data_offset
        donor_end = donor_start + donor_section.data_size
        result[target_start:target_end] = donor_payload[donor_start:donor_end]
    if len(result) != len(target_payload):
        raise AssertionError(f"{mapping.mapping_id}: mapped copy changed CCS size")
    return bytes(result)


def gzip_header_end(data: bytes) -> int:
    if len(data) < 18 or data[:3] != b"\x1f\x8b\x08":
        raise ValueError("CCS is not a gzip stream")
    flags = data[3]
    if flags & 0xE0:
        raise ValueError("gzip stream uses reserved flags")
    cursor = 10
    if flags & 0x04:
        if cursor + 2 > len(data):
            raise ValueError("truncated gzip extra header")
        extra_length = struct.unpack_from("<H", data, cursor)[0]
        cursor += 2 + extra_length
    for flag in (0x08, 0x10):
        if flags & flag:
            end = data.find(b"\0", cursor)
            if end < 0:
                raise ValueError("unterminated gzip string header")
            cursor = end + 1
    if flags & 0x02:
        cursor += 2
    if cursor > len(data) - 8:
        raise ValueError("truncated gzip header")
    return cursor


def repack_gzip_exact(original: bytes, payload: bytes) -> tuple[bytes, int, int]:
    header_end = gzip_header_end(original)
    candidates = []
    for strategy in (zlib.Z_DEFAULT_STRATEGY, zlib.Z_FILTERED, zlib.Z_RLE):
        for level in range(6, 10):
            for memory_level in range(1, 10):
                compressor = zlib.compressobj(
                    level=level,
                    method=zlib.DEFLATED,
                    wbits=-15,
                    memLevel=memory_level,
                    strategy=strategy,
                )
                encoded = compressor.compress(payload) + compressor.flush()
                candidates.append((len(encoded), strategy, level, memory_level, encoded))
    _, _, _, _, deflate = min(candidates, key=lambda item: item[:4])
    trailer = struct.pack("<II", binascii.crc32(payload) & 0xFFFFFFFF, len(payload) & 0xFFFFFFFF)
    header = original[:header_end]
    stream = header + deflate + trailer
    if len(stream) > len(original) and len(header) > 10:
        header = original[:3] + b"\0" + original[4:10]
        stream = header + deflate + trailer
    if len(stream) > len(original) and zopfli_gzip is not None:
        for iterations, split_last in ((15, 0), (15, 1), (50, 0), (50, 1)):
            optimized = zopfli_gzip.compress(
                payload,
                numiterations=iterations,
                blocksplittinglast=split_last,
            )
            if len(optimized) < len(stream):
                stream = optimized
    if len(stream) > len(original):
        if zopfli_gzip is None:
            raise RuntimeError(
                "Fixed-capacity CCS derivation requires zopfli==0.4.3; "
                "install na2_patcher/requirements.txt"
            )
        raise RuntimeError(
            f"Recompressed CCS is {len(stream) - len(original)} bytes larger than its fixed capacity"
        )
    padding = len(original) - len(stream)
    result = stream + b"\0" * padding
    if len(result) != len(original) or gzip.decompress(result) != payload:
        raise AssertionError("Exact-size gzip verification failed")
    return result, len(stream), padding


def selected_container_ids(package: Package, selection: tuple[str, ...]) -> list[str]:
    selected = set(selection)
    unknown = selected - package.containers.keys()
    if unknown:
        raise ValueError("Unknown UI container IDs: " + ", ".join(sorted(unknown)))
    return sorted(selected or package.containers.keys())


def expected_payload(
    strategy: Strategy,
    target_payload: bytes,
    donor_payload: bytes,
    mappings: list[Mapping],
) -> bytes:
    if strategy.strategy == "whole":
        if any(INDEXED_TOP_ROWS.fullmatch(mapping.transform) for mapping in mappings):
            raise ValueError(f"{strategy.container_id}: whole strategy cannot use indexed-row transforms")
        return donor_payload
    indexed = [mapping for mapping in mappings if INDEXED_TOP_ROWS.fullmatch(mapping.transform)]
    if indexed:
        if len(indexed) != 1 or len(mappings) != 1:
            raise ValueError(
                f"{strategy.container_id}: mapped indexed-row strategy requires exactly one mapping"
            )
        return indexed_top_rows_payload(target_payload, donor_payload, indexed[0])

    copied = [mapping for mapping in mappings if mapping.transform == "copy"]
    if not copied or len(copied) != len(mappings):
        raise ValueError(
            f"{strategy.container_id}: mapped strategy requires one indexed-row mapping "
            "or one or more copy mappings"
        )
    payload = target_payload
    for mapping in copied:
        payload = copy_mapping_payload(payload, donor_payload, mapping)
    return payload


def source_members(
    na2_root: Path,
    nun5_root: Path,
) -> tuple[Iso9660, Iso9660, bytes]:
    target_cvm_root = na2_root / "DATA" / "DATA.CVM.files"
    donor_cvm_root = nun5_root / "DATA" / "DATA.CVM.files"
    return (
        Iso9660(target_cvm_root / "DATA.CVM.iso"),
        Iso9660(donor_cvm_root / "DATA.CVM.iso"),
        (target_cvm_root / "DATA.CVM.hdr").read_bytes(),
    )


def build_plan(
    *,
    na2_root: Path,
    nun5_root: Path,
    data_root: Path,
    selection: tuple[str, ...] = (),
) -> UiTexturePlan:
    package = load_package(data_root)
    target_iso, donor_iso, target_header = source_members(na2_root, nun5_root)
    mappings_by_container: dict[str, list[Mapping]] = defaultdict(list)
    for mapping in package.mappings:
        mappings_by_container[mapping.container_id].append(mapping)

    results = []
    for container_id in selected_container_ids(package, selection):
        spec = package.containers[container_id]
        strategy = package.strategies[container_id]
        iso_path = spec.path.upper()
        target_record = target_iso.by_path.get(iso_path)
        donor_record = donor_iso.by_path.get(iso_path)
        if target_record is None or target_record.is_dir:
            raise FileNotFoundError(f"NA2 DATA.CVM has no file {spec.path}")
        if donor_record is None or donor_record.is_dir:
            raise FileNotFoundError(f"NUN5 DATA.CVM has no file {spec.path}")
        original = target_iso.read_file(target_record)
        donor = donor_iso.read_file(donor_record)
        if sha256(original) != spec.target_sha256:
            raise RuntimeError(f"Unexpected NA2 SHA-256 for {spec.path}: {sha256(original)}")
        if sha256(donor) != spec.donor_sha256:
            raise RuntimeError(f"Unexpected NUN5 SHA-256 for {spec.path}: {sha256(donor)}")
        target_payload = gzip.decompress(original)
        donor_payload = gzip.decompress(donor)
        target_entries = parse_ccs(target_payload)
        donor_entries = parse_ccs(donor_payload)
        mappings = mappings_by_container[container_id]
        for mapping in mappings:
            validate_mapping(mapping, target_payload, donor_payload, target_entries, donor_entries)
        validate_visual_coverage(
            strategy,
            mappings,
            target_payload,
            donor_payload,
            target_entries,
            donor_entries,
        )
        payload = expected_payload(strategy, target_payload, donor_payload, mappings)
        payload_hash = sha256(payload)

        replacement, stream_size, padding = repack_gzip_exact(original, payload)
        replacement_hash = sha256(replacement)
        if payload_hash != strategy.payload_sha256:
            raise RuntimeError(
                f"Unexpected derived payload SHA-256 for {spec.path}: {payload_hash}"
            )
        if replacement_hash != strategy.replacement_sha256:
            raise RuntimeError(
                f"Unexpected derived replacement SHA-256 for {spec.path}: "
                f"{replacement_hash}"
            )

        results.append(
            ContainerResult(
                spec=spec,
                strategy=strategy,
                original=original,
                donor=donor,
                replacement=replacement,
                payload_sha256=payload_hash,
                compressed_stream_size=stream_size,
                padding_size=padding,
                outer_cvm_offset=len(target_header) + target_record.byte_offset,
                mapping_ids=tuple(mapping.mapping_id for mapping in mappings),
            )
        )
    return UiTexturePlan(package, tuple(results), target_header)


def build_ui_texture_plan(
    *,
    na2_root: Path,
    nun5_root: Path,
    data_root: Path,
    selection: tuple[str, ...] = (),
) -> UiTexturePlan:
    return build_plan(
        na2_root=na2_root,
        nun5_root=nun5_root,
        data_root=data_root,
        selection=selection,
    )


def result_rows(plan: UiTexturePlan) -> list[dict[str, object]]:
    return [
        {
            "container_id": result.spec.container_id,
            "path": result.spec.path,
            "strategy": result.strategy.strategy,
            "mapping_count": len(result.mapping_ids),
            "fixed_size": len(result.replacement),
            "compressed_stream_size": result.compressed_stream_size,
            "zero_padding": result.padding_size,
            "target_sha256": sha256(result.original),
            "donor_sha256": sha256(result.donor),
            "replacement_sha256": sha256(result.replacement),
            "payload_sha256": result.payload_sha256,
            "outer_cvm_offset": f"0x{result.outer_cvm_offset:X}",
        }
        for result in plan.containers
    ]


def write_preview(plan: UiTexturePlan, output: Path) -> None:
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    for result in plan.containers:
        path = output / Path(result.spec.path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(result.replacement)
    (output / "summary.json").write_text(
        json.dumps(
            {
                "container_count": len(plan.containers),
                "mapping_count": plan.mapping_count,
                "containers": result_rows(plan),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def parse_selection(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


def default_roots() -> tuple[Path, Path, Path]:
    repository = Path(__file__).resolve().parents[3]
    paths = load_project_paths(repository)
    return (
        resolve_alias("@source/NA2.iso.files", paths),
        resolve_alias("@source/NUN5.iso.files", paths),
        Path(__file__).resolve().parent,
    )


def print_results(plan: UiTexturePlan) -> None:
    print(
        "container_id\tstrategy\tfixed_size\tcompressed_stream_size\tzero_padding\t"
        "replacement_sha256\tpayload_sha256"
    )
    for row in result_rows(plan):
        print(
            "\t".join(
                str(row[field])
                for field in (
                    "container_id",
                    "strategy",
                    "fixed_size",
                    "compressed_stream_size",
                    "zero_padding",
                    "replacement_sha256",
                    "payload_sha256",
                )
            )
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Derive fixed-size NUN5-to-NA2 UI CCS imports"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    verify_parser = subparsers.add_parser(
        "verify", help="derive and verify pinned replacements from both games"
    )
    verify_parser.add_argument("--selection", default="")
    preview_parser = subparsers.add_parser("preview", help="write verified CCS members for review")
    preview_parser.add_argument("--output", required=True)
    preview_parser.add_argument("--selection", default="")
    args = parser.parse_args()

    na2_root, nun5_root, data_root = default_roots()
    selection = parse_selection(args.selection)
    plan = build_ui_texture_plan(
        na2_root=na2_root,
        nun5_root=nun5_root,
        data_root=data_root,
        selection=selection,
    )
    if args.command == "preview":
        output = Path(args.output)
        if not output.is_absolute():
            output = Path(__file__).resolve().parents[3] / output
        write_preview(plan, output.resolve())
    print_results(plan)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
