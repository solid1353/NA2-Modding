#!/usr/bin/env python3
"""Verify a worker ISO against its exact retained build and symbol bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[3]
if str(REPOSITORY) not in sys.path:
    sys.path.insert(0, str(REPOSITORY))

from na228_builder.image_assembler.iso9660 import Iso9660  # noqa: E402
from scripts.injection.build import load_symbol_map  # noqa: E402


RESIDENT_PATHS = (
    "PRG/228.BIN",
    "PRG/BTL.BIN",
    "PRG/ETC.BIN",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", required=True, type=Path)
    parser.add_argument("--build-record", required=True, type=Path)
    parser.add_argument("--boot-elf", required=True)
    parser.add_argument("--serial", required=True)
    parser.add_argument("--crc", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--required-symbol", action="append", default=[])
    return parser.parse_args()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def read_member(image: Iso9660, path: str) -> bytes:
    try:
        record = image.by_path[path]
    except KeyError as exc:
        raise ValueError(f"worker ISO has no required file {path}") from exc
    if record.is_dir:
        raise ValueError(f"worker ISO path is a directory: {path}")
    return image.read_file(record)


def main() -> int:
    args = parse_args()
    iso = args.iso.resolve(strict=True)
    build_record = args.build_record.resolve(strict=True)
    if not build_record.is_dir():
        raise ValueError(f"build record is not a directory: {build_record}")

    image = Iso9660(iso)
    artifacts: list[dict[str, object]] = []
    contents: dict[str, bytes] = {}
    for path in (args.boot_elf, *RESIDENT_PATHS):
        data = read_member(image, path)
        contents[path] = data
        artifacts.append(
            {"path": path, "size": len(data), "sha256": sha256(data)}
        )

    payload = contents["PRG/228.BIN"]
    payload_summary_path = (
        build_record / "payload_builder" / "payload_summary.json"
    )
    payload_summary = json.loads(payload_summary_path.read_text("utf-8"))
    payload_hash = sha256(payload)
    if payload_summary.get("sha256", "").upper() != payload_hash:
        raise ValueError(
            "worker ISO 228.BIN does not match the retained build record"
        )
    if int(payload_summary.get("size", -1)) != len(payload):
        raise ValueError(
            "worker ISO 228.BIN size does not match the retained build record"
        )

    symbols = load_symbol_map(build_record, payload)
    missing = [name for name in args.required_symbol if name not in symbols]
    if missing:
        raise ValueError(
            "retained build record lacks required symbols: " + ", ".join(missing)
        )

    result = {
        "schema_version": 1,
        "iso": str(iso),
        "serial": args.serial,
        "crc": args.crc.upper(),
        "boot_elf": args.boot_elf,
        "payload_sha256": payload_hash,
        "build_record": str(build_record),
        "symbol_count": len(symbols),
        "required_symbols": args.required_symbol,
        "artifacts": artifacts,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
