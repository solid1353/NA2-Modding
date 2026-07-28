#!/usr/bin/env python3
"""Generate the native NUN5-derived NA2 font data assets."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys


def find_repository(start: Path) -> Path:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / "project-paths.json").is_file():
            return candidate
    raise FileNotFoundError("project-paths.json was not found")


REPOSITORY = find_repository(Path(__file__))
if str(REPOSITORY) not in sys.path:
    sys.path.insert(0, str(REPOSITORY))

from na2_patcher.project_paths import load_project_paths  # noqa: E402


PACKAGE = load_project_paths(REPOSITORY).path(
    "features", "localization", "binary_patcher"
)
ATLAS_OUTPUT = PACKAGE / "assets" / "nun5_semantic_14x20.bin"
PACKED_MAP_OUTPUT = PACKAGE / "assets" / "nun5_semantic_14x20_packed_map.bin"

NA2_GF4_SHA256 = "472E297E6B7B158232CD0BCD87941079D51885D65AEF5CFE7052CBE8D88FC4F5"
NA2_GF4C_SHA256 = "5A811B40E328F236A739A8F51CCDC61B52FD409420712F2D2BC02E087ACBC3BE"
NUN5_GF4_SHA256 = "129BAFD7F0FF5896F20F48B0AB603EA4362774CED017F7EB327D96D7B0EFC847"
NUN5_GF4C_SHA256 = "C6C889B795BB6137120252FAE887B48CB4304A0854A761F5942B50818D9D2FBD"

PALETTE_OFFSET = 0x28
PALETTE_COUNT = 16
PALETTE_ENTRY_SIZE = 4

NA2_DESCRIPTOR_OFFSET = 0x4E
NA2_DESCRIPTOR_EXPECTED = bytes.fromhex("0A1600006E009D")
NA2_DESCRIPTOR_REPLACEMENT = bytes.fromhex("0E1400008C007B")
NA2_MAP_OFFSET = 0xD5318
NA2_MAP_ENTRY_SIZE = 4
NA2_MAP_COUNT = 434
NA2_MAP_SIZE = NA2_MAP_ENTRY_SIZE * NA2_MAP_COUNT
NA2_METRICS_OFFSET = 0xD59E0
NA2_RASTER_OFFSET = 0xD9240
NA2_WIDTH = 10
NA2_HEIGHT = 22
NA2_STRIDE = 110

NUN5_METRICS_OFFSET = 0x7BE8
NUN5_RASTER_OFFSET = 0x4C
NUN5_WIDTH = 14
NUN5_HEIGHT = 20
NUN5_STRIDE = 140
NUN5_CELL_COUNT = 223

OUTPUT_CELL_COUNT = 123
OUTPUT_ATLAS_SIZE = OUTPUT_CELL_COUNT * NUN5_STRIDE
OUTPUT_METRICS_SIZE = OUTPUT_CELL_COUNT * 4
EXPECTED_CLEAN_ATLAS_SHA256 = "0246A8275782ADFEEF80C7C88CD5B912741A7787F3519FFDD6A6AA60F6DE9810"
EXPECTED_CLEAN_METRICS_SHA256 = "423D859444D28C397E52215376E3701472EB6F493995C66BD45FEFC1FE1C5090"
EXPECTED_CLEAN_MAP_SHA256 = "26563C6C773B372CB0DE4845FFBE83023DAD94526AB2990B72C55EF39A7D18EF"
OUTPUT_ATLAS_SHA256 = "6E4B988E512568F0A91E0226A8A4046362C1A4EF078E50BBF630BEEF90333736"
OUTPUT_METRICS_SHA256 = "CE51A6033E1CF199E2B78D57F8A714FD83BA9251B19A2969B201C6C84FCA6B59"
OUTPUT_PACKED_PAYLOAD_SHA256 = "19EDB008C3EB164117A461E75317BF7885890C72122599C4AE45344FB53761CB"
OUTPUT_PACKED_MAP_SHA256 = "6F691015E5BA54EA87B2976970D828863E274BB543CC3D531D93800018EB7A5E"
RESULT_GF4_SHA256 = "79BA614746E667A70A068A0A889085D028D8019884182E78041026A77971AA25"

# NUN5 lacks several ASCII punctuation slots used by translated NA2. Import
# only exact same-semantic cells and reconstruct every other reachable cell
# from clean NA2. The at-sign is stored at NUN5 cell 63.
DONOR_RANGES = ((0, 31), (33, 58), (65, 90))


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def checked_read(path: Path, expected_hash: str) -> bytes:
    data = path.read_bytes()
    actual = sha256(data)
    if actual != expected_hash:
        raise ValueError(f"hash mismatch for {path.name}: {actual} != {expected_hash}")
    return data


def palette(data: bytes) -> tuple[tuple[int, int, int, int], ...]:
    entries = []
    for index in range(PALETTE_COUNT):
        offset = PALETTE_OFFSET + index * PALETTE_ENTRY_SIZE
        entries.append(tuple(data[offset : offset + PALETTE_ENTRY_SIZE]))
    return tuple(entries)  # type: ignore[return-value]


def nearest_palette_index(
    color: tuple[int, int, int, int],
    destination: tuple[tuple[int, int, int, int], ...],
) -> int:
    if color[3] == 0:
        return min(
            range(len(destination)),
            key=lambda index: (destination[index][3], index),
        )
    return min(
        range(len(destination)),
        key=lambda index: (
            sum((source - target) ** 2 for source, target in zip(color, destination[index])),
            index,
        ),
    )


def unpack_cell(data: bytes, offset: int, stride: int, width: int, height: int) -> list[int]:
    packed = data[offset : offset + stride]
    if len(packed) != stride:
        raise ValueError("cell exceeds source data")
    pixels: list[int] = []
    for value in packed:
        pixels.extend((value & 0x0F, value >> 4))
    return pixels[: width * height]


def pack_cell(pixels: list[int]) -> bytes:
    if len(pixels) % 2:
        pixels = [*pixels, 0]
    return bytes(
        pixels[index] | (pixels[index + 1] << 4)
        for index in range(0, len(pixels), 2)
    )


def nun5_source_cell(destination_cell: int) -> int | None:
    if destination_cell == 32:
        return 63
    for first, last in DONOR_RANGES:
        if first <= destination_cell <= last:
            return destination_cell
    return None


def convert_nun5_cell(
    data: bytes,
    source_cell: int,
    source_palette: tuple[tuple[int, int, int, int], ...],
    destination_palette: tuple[tuple[int, int, int, int], ...],
) -> bytes:
    if not 0 <= source_cell < NUN5_CELL_COUNT:
        raise ValueError(f"invalid NUN5 cell {source_cell}")
    pixels = unpack_cell(
        data,
        NUN5_RASTER_OFFSET + source_cell * NUN5_STRIDE,
        NUN5_STRIDE,
        NUN5_WIDTH,
        NUN5_HEIGHT,
    )
    converted = [
        nearest_palette_index(source_palette[index], destination_palette)
        for index in pixels
    ]
    return pack_cell(converted)


def resample_clean_cell(data: bytes, source_cell: int) -> bytes:
    source = unpack_cell(
        data,
        NA2_RASTER_OFFSET + source_cell * NA2_STRIDE,
        NA2_STRIDE,
        NA2_WIDTH,
        NA2_HEIGHT,
    )
    converted: list[int] = []
    for destination_y in range(NUN5_HEIGHT):
        source_y = ((2 * destination_y + 1) * NA2_HEIGHT) // (2 * NUN5_HEIGHT)
        for destination_x in range(NUN5_WIDTH):
            source_x = ((2 * destination_x + 1) * NA2_WIDTH) // (2 * NUN5_WIDTH)
            converted.append(source[source_y * NA2_WIDTH + source_x])
    return pack_cell(converted)


def build_atlas(
    clean_na2: bytes,
    official_nun5: bytes,
    clean_palette: tuple[tuple[int, int, int, int], ...],
    donor_palette: tuple[tuple[int, int, int, int], ...],
) -> bytes:
    cells: list[bytes] = []
    for destination_cell in range(OUTPUT_CELL_COUNT):
        source_cell = nun5_source_cell(destination_cell)
        if source_cell is None:
            cell = resample_clean_cell(clean_na2, destination_cell)
        else:
            cell = convert_nun5_cell(
                official_nun5,
                source_cell,
                donor_palette,
                clean_palette,
            )
        if len(cell) != NUN5_STRIDE:
            raise ValueError(f"invalid generated cell length at {destination_cell}")
        cells.append(cell)
    result = b"".join(cells)
    if len(result) != OUTPUT_ATLAS_SIZE or sha256(result) != OUTPUT_ATLAS_SHA256:
        raise ValueError(f"atlas mismatch: {len(result)} bytes, {sha256(result)}")
    return result


def metric_from_cell(
    cell: bytes,
    destination_palette: tuple[tuple[int, int, int, int], ...],
) -> bytes:
    pixels = unpack_cell(cell, 0, NUN5_STRIDE, NUN5_WIDTH, NUN5_HEIGHT)
    ink = [
        (x, y)
        for y in range(NUN5_HEIGHT)
        for x in range(NUN5_WIDTH)
        if destination_palette[pixels[y * NUN5_WIDTH + x]][3] > 0
    ]
    if not ink:
        return bytes(4)
    xs = [x for x, _ in ink]
    ys = [y for _, y in ink]
    # NUN5 stores each transparent-side margin minus one, clamped to zero.
    return bytes(
        (
            max(min(xs) - 1, 0),
            max(min(ys) - 1, 0),
            max(NUN5_WIDTH - 1 - max(xs) - 1, 0),
            max(NUN5_HEIGHT - 1 - max(ys) - 1, 0),
        )
    )


def build_metrics(
    clean_na2: bytes,
    official_nun5: bytes,
    atlas: bytes,
    clean_palette: tuple[tuple[int, int, int, int], ...],
) -> bytes:
    clean_block = clean_na2[
        NA2_METRICS_OFFSET : NA2_METRICS_OFFSET + OUTPUT_METRICS_SIZE
    ]
    if sha256(clean_block) != EXPECTED_CLEAN_METRICS_SHA256:
        raise ValueError("clean NA2 metric block does not match")
    result = bytearray()
    for destination_cell in range(OUTPUT_CELL_COUNT):
        source_cell = nun5_source_cell(destination_cell)
        if source_cell is not None:
            source_offset = NUN5_METRICS_OFFSET + source_cell * 4
            result.extend(official_nun5[source_offset : source_offset + 4])
            continue
        cell_offset = destination_cell * NUN5_STRIDE
        result.extend(
            metric_from_cell(
                atlas[cell_offset : cell_offset + NUN5_STRIDE],
                clean_palette,
            )
        )
    metrics = bytes(result)
    if sha256(metrics) != OUTPUT_METRICS_SHA256:
        raise ValueError(f"metrics hash {sha256(metrics)} != {OUTPUT_METRICS_SHA256}")
    return metrics


def build_packed_map(clean_na2: bytes, metrics: bytes) -> tuple[bytes, bytes]:
    clean_map = clean_na2[NA2_MAP_OFFSET : NA2_MAP_OFFSET + NA2_MAP_SIZE]
    if len(clean_map) != NA2_MAP_SIZE or sha256(clean_map) != EXPECTED_CLEAN_MAP_SHA256:
        raise ValueError("clean NA2 primary hash map does not match")

    rows = [metrics[offset : offset + 4] for offset in range(0, len(metrics), 4)]
    if len(rows) != OUTPUT_CELL_COUNT or any(len(row) != 4 for row in rows):
        raise ValueError("metric row count does not match the secondary cell count")
    if any(value > 0x0F for row in rows for value in row):
        raise ValueError("a metric cannot be represented in four bits")

    packed_payload = b"".join(
        (
            row[0]
            | (row[1] << 4)
            | (row[2] << 8)
            | (row[3] << 12)
        ).to_bytes(2, "little")
        for row in rows
    )
    if sha256(packed_payload) != OUTPUT_PACKED_PAYLOAD_SHA256:
        raise ValueError("packed metric payload does not match")

    result = bytearray(clean_map)
    payload_offset = 0
    for entry_offset in range(0, len(result), NA2_MAP_ENTRY_SIZE):
        if result[entry_offset : entry_offset + 2] != b"\xFF\xFF":
            continue
        if payload_offset < len(packed_payload):
            result[entry_offset + 2 : entry_offset + 4] = packed_payload[
                payload_offset : payload_offset + 2
            ]
            payload_offset += 2
    if payload_offset != len(packed_payload):
        raise ValueError("primary hash map has too few empty entries for packed metrics")

    packed_map = bytes(result)
    if sha256(packed_map) != OUTPUT_PACKED_MAP_SHA256:
        raise ValueError("packed primary hash map does not match")
    for entry_offset in range(0, len(clean_map), NA2_MAP_ENTRY_SIZE):
        if packed_map[entry_offset : entry_offset + 2] != clean_map[
            entry_offset : entry_offset + 2
        ]:
            raise ValueError("packed map changed a primary hash key")
        if clean_map[entry_offset : entry_offset + 2] != b"\xFF\xFF" and packed_map[
            entry_offset : entry_offset + 4
        ] != clean_map[entry_offset : entry_offset + 4]:
            raise ValueError("packed map changed an occupied primary entry")
    return packed_map, packed_payload


def verify_result(clean_na2: bytes, atlas: bytes, packed_map: bytes) -> None:
    if clean_na2[NA2_DESCRIPTOR_OFFSET : NA2_DESCRIPTOR_OFFSET + 7] != NA2_DESCRIPTOR_EXPECTED:
        raise ValueError("clean secondary descriptor does not match")
    clean_atlas = clean_na2[NA2_RASTER_OFFSET : NA2_RASTER_OFFSET + OUTPUT_ATLAS_SIZE]
    if sha256(clean_atlas) != EXPECTED_CLEAN_ATLAS_SHA256:
        raise ValueError("clean NA2 raster destination does not match")

    result = bytearray(clean_na2)
    result[
        NA2_DESCRIPTOR_OFFSET : NA2_DESCRIPTOR_OFFSET + 7
    ] = NA2_DESCRIPTOR_REPLACEMENT
    result[NA2_MAP_OFFSET : NA2_MAP_OFFSET + len(packed_map)] = packed_map
    result[NA2_RASTER_OFFSET : NA2_RASTER_OFFSET + len(atlas)] = atlas
    actual = sha256(bytes(result))
    if actual != RESULT_GF4_SHA256:
        raise ValueError(f"result GF4 hash {actual} != {RESULT_GF4_SHA256}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        action="store_true",
        help="write the verified atlas and metric blobs into the package assets directory",
    )
    args = parser.parse_args()

    paths = load_project_paths(REPOSITORY)
    clean_na2_root = paths.path("source_na2")
    nun5_root = paths.path("source_nun5")
    clean_na2 = checked_read(clean_na2_root / "DATA" / "GF4.BIN", NA2_GF4_SHA256)
    clean_gf4c = checked_read(
        clean_na2_root / "DATA" / "GF4C.BIN", NA2_GF4C_SHA256
    )
    official_nun5 = checked_read(
        nun5_root / "DATA" / "GF4.BIN", NUN5_GF4_SHA256
    )
    nun5_gf4c = checked_read(
        nun5_root / "DATA" / "GF4C.BIN", NUN5_GF4C_SHA256
    )

    clean_palette = palette(clean_gf4c)
    donor_palette = palette(nun5_gf4c)
    palette_map = tuple(
        nearest_palette_index(color, clean_palette) for color in donor_palette
    )
    expected_map = (0, 1, 1, 2, 3, 4, 4, 5, 7, 8, 8, 9, 10, 11, 15, 12)
    if palette_map != expected_map:
        raise ValueError(f"unexpected palette map {palette_map} != {expected_map}")

    atlas = build_atlas(clean_na2, official_nun5, clean_palette, donor_palette)
    metrics = build_metrics(
        clean_na2,
        official_nun5,
        atlas,
        clean_palette,
    )
    packed_map, packed_payload = build_packed_map(clean_na2, metrics)
    verify_result(clean_na2, atlas, packed_map)

    outputs = (
        (ATLAS_OUTPUT, atlas),
        (PACKED_MAP_OUTPUT, packed_map),
    )
    if args.write:
        for path, payload in outputs:
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.is_file() or path.read_bytes() != payload:
                path.write_bytes(payload)
        action = "wrote"
    else:
        for path, payload in outputs:
            if not path.is_file():
                raise FileNotFoundError(
                    f"generated asset is missing: {path.relative_to(REPOSITORY)}"
                )
            if path.read_bytes() != payload:
                raise ValueError(f"persisted asset differs from deterministic output: {path.name}")
        action = "verified"

    print(f"{action}\t{ATLAS_OUTPUT.relative_to(REPOSITORY).as_posix()}")
    print(f"atlas_size\t{len(atlas)}")
    print(f"atlas_sha256\t{sha256(atlas)}")
    print(f"{action}\t{PACKED_MAP_OUTPUT.relative_to(REPOSITORY).as_posix()}")
    print(f"packed_map_size\t{len(packed_map)}")
    print(f"packed_map_sha256\t{sha256(packed_map)}")
    print(f"packed_payload_size\t{len(packed_payload)}")
    print(f"packed_payload_sha256\t{sha256(packed_payload)}")
    print(f"metrics_size\t{len(metrics)}")
    print(f"metrics_sha256\t{sha256(metrics)}")
    print(f"result_gf4_sha256\t{RESULT_GF4_SHA256}")
    print(f"palette_map\t{','.join(str(index) for index in palette_map)}")


if __name__ == "__main__":
    main()
