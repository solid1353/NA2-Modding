from __future__ import annotations

import csv
import hashlib
import struct
import zlib
from dataclasses import dataclass
from pathlib import Path


ASSET_FIELDS = [
    "container_id",
    "path",
    "asset_sha256",
    "payload_sha256",
]
EXTERNAL_PACK_MAGIC = b"NA228UIP"
EXTERNAL_PACK_PATH = "PRG/228_UI.BIN"
EXTERNAL_PACK_SECTOR_SIZE = 0x800
EXTERNAL_PACK_ENTRY_SIZE = 0x10


def sha256(data: bytes | bytearray) -> str:
    return hashlib.sha256(data).hexdigest().upper()


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
class AssetSpec:
    container_id: str
    path: str
    asset_sha256: str
    payload_sha256: str


@dataclass(frozen=True)
class ExternalTextureResult:
    spec: AssetSpec
    replacement: bytes
    payload_sha256: str
    decompressed_size: int
    compressed_stream_size: int
    padding_size: int
    pack_sector: int
    pack_sector_count: int
    path_hash: int


@dataclass(frozen=True)
class ExternalTexturePackPlan:
    containers: tuple[ExternalTextureResult, ...]
    payload: bytes


def load_assets(directory: Path) -> tuple[AssetSpec, ...]:
    manifest = directory.resolve() / "assets.tsv"
    with manifest.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != ASSET_FIELDS:
            raise ValueError(
                f"{manifest}: expected columns " + "\t".join(ASSET_FIELDS)
            )
        rows = [
            {key: (value or "").strip() for key, value in row.items()}
            for row in reader
            if any((value or "").strip() for value in row.values())
        ]

    assets: list[AssetSpec] = []
    container_ids: set[str] = set()
    paths: set[str] = set()
    for line, row in enumerate(rows, 2):
        label = f"assets.tsv line {line}"
        container_id = row["container_id"]
        if not container_id or container_id in container_ids:
            raise ValueError(f"{label}: duplicate or empty container_id")
        container_ids.add(container_id)
        path = checked_relative_path(row["path"], label)
        if path.casefold() in paths:
            raise ValueError(f"{label}: duplicate path {path!r}")
        paths.add(path.casefold())
        assets.append(
            AssetSpec(
                container_id=container_id,
                path=path,
                asset_sha256=checked_hash(row["asset_sha256"], label),
                payload_sha256=checked_hash(row["payload_sha256"], label),
            )
        )
    if not assets:
        raise ValueError("assets.tsv contains no localized UI assets")
    asset_root = directory.resolve() / "assets"
    expected_files = {f"{asset.container_id}.ccs.gz" for asset in assets}
    present_files = {
        path.name for path in asset_root.glob("*.ccs.gz") if path.is_file()
    }
    missing_files = sorted(expected_files - present_files)
    unexpected_files = sorted(present_files - expected_files)
    if missing_files or unexpected_files:
        details: list[str] = []
        if missing_files:
            details.append("missing " + ", ".join(missing_files))
        if unexpected_files:
            details.append("unlisted " + ", ".join(unexpected_files))
        raise ValueError("Localized texture asset inventory mismatch: " + "; ".join(details))
    return tuple(sorted(assets, key=lambda asset: asset.container_id))


def runtime_path_hash(path: str) -> int:
    value = 0x811C9DC5
    normalized = path.replace("\\", "/").lstrip("/").upper()
    for byte in normalized.encode("ascii"):
        value ^= byte
        value = (value * 0x01000193) & 0xFFFFFFFF
    return value


def gzip_stream(payload: bytes, label: str) -> tuple[bytes, int, int]:
    decoder = zlib.decompressobj(16 + zlib.MAX_WBITS)
    decoded = decoder.decompress(payload) + decoder.flush()
    if not decoder.eof:
        raise ValueError(f"{label}: localized asset is not a complete gzip stream")
    stream_size = len(payload) - len(decoder.unused_data)
    padding_size = len(payload) - stream_size
    if payload[stream_size:] != b"\0" * padding_size:
        raise ValueError(f"{label}: localized asset has nonzero trailing bytes")
    return decoded, stream_size, padding_size


def build_external_texture_pack(data_root: Path) -> ExternalTexturePackPlan:
    results: list[ExternalTextureResult] = []
    body = bytearray(EXTERNAL_PACK_SECTOR_SIZE)
    hashes: dict[int, str] = {}
    for spec in load_assets(data_root):
        asset_path = data_root / "assets" / f"{spec.container_id}.ccs.gz"
        if not asset_path.is_file():
            raise FileNotFoundError(
                f"Localized texture asset is missing: {asset_path.relative_to(data_root)}"
            )
        replacement = asset_path.read_bytes()
        replacement_hash = sha256(replacement)
        if replacement_hash != spec.asset_sha256:
            raise ValueError(
                f"{spec.container_id}: localized asset SHA-256 {replacement_hash} "
                f"does not match {spec.asset_sha256}"
            )
        decoded, stream_size, padding_size = gzip_stream(
            replacement, spec.container_id
        )
        payload_hash = sha256(decoded)
        if payload_hash != spec.payload_sha256:
            raise ValueError(
                f"{spec.container_id}: localized CCS SHA-256 {payload_hash} does "
                f"not match {spec.payload_sha256}"
            )
        path_hash = runtime_path_hash(spec.path)
        collision = hashes.get(path_hash)
        if collision is not None:
            raise ValueError(
                f"Localized texture path hash collision: {collision} and {spec.path}"
            )
        hashes[path_hash] = spec.path
        pack_sector = len(body) // EXTERNAL_PACK_SECTOR_SIZE
        body.extend(replacement)
        body.extend(b"\0" * (-len(body) % EXTERNAL_PACK_SECTOR_SIZE))
        results.append(
            ExternalTextureResult(
                spec=spec,
                replacement=replacement,
                payload_sha256=payload_hash,
                decompressed_size=len(decoded),
                compressed_stream_size=stream_size,
                padding_size=padding_size,
                pack_sector=pack_sector,
                pack_sector_count=(
                    (len(replacement) + EXTERNAL_PACK_SECTOR_SIZE - 1)
                    // EXTERNAL_PACK_SECTOR_SIZE
                ),
                path_hash=path_hash,
            )
        )

    header_size = 16 + len(results) * EXTERNAL_PACK_ENTRY_SIZE
    if header_size > EXTERNAL_PACK_SECTOR_SIZE:
        raise ValueError("Localized texture pack index exceeds one sector")
    body[0:8] = EXTERNAL_PACK_MAGIC
    struct.pack_into(
        "<II", body, 8, len(results), EXTERNAL_PACK_ENTRY_SIZE
    )
    for index, result in enumerate(results):
        struct.pack_into(
            "<IIII",
            body,
            16 + index * EXTERNAL_PACK_ENTRY_SIZE,
            result.path_hash,
            result.pack_sector,
            result.pack_sector_count,
            result.decompressed_size,
        )
    return ExternalTexturePackPlan(tuple(results), bytes(body))


def result_rows(plan: ExternalTexturePackPlan) -> list[dict[str, object]]:
    return [
        {
            "container_id": result.spec.container_id,
            "path": result.spec.path,
            "fixed_size": len(result.replacement),
            "compressed_stream_size": result.compressed_stream_size,
            "zero_padding": result.padding_size,
            "asset_sha256": sha256(result.replacement),
            "payload_sha256": result.payload_sha256,
            "pack_sector": result.pack_sector,
            "pack_sectors": result.pack_sector_count,
        }
        for result in plan.containers
    ]
