#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY))

from scripts.pcsx2.pine import PineClient


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Apply a compiled EE fragment directly through PINE."
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--port", required=True, type=int)
    return parser.parse_args()


def integer(value: object, label: str) -> int:
    try:
        return int(str(value), 0)
    except ValueError as exc:
        raise ValueError(f"{label}: invalid integer {value!r}") from exc


def encoded_bytes(value: object, label: str, *, empty: bool = False) -> bytes:
    text = str(value)
    if (
        (not text and not empty)
        or len(text) % 2
        or any(character not in "0123456789abcdefABCDEF" for character in text)
    ):
        raise ValueError(f"{label}: invalid hexadecimal bytes")
    return bytes.fromhex(text)


def word_range(address: int, size: int, label: str) -> None:
    if address % 4 or size < 0 or size % 4:
        raise ValueError(f"{label}: expected an aligned EE word range")


def load_candidate(
    directory: Path,
) -> tuple[
    bytes,
    list[tuple[str, int, bytes]],
    list[tuple[str, int, bytes, bytes]],
]:
    directory = directory.resolve()
    manifest_path = directory / "manifest.json"
    fragment_path = directory / "fragment.bin"
    if not manifest_path.is_file() or not fragment_path.is_file():
        raise ValueError(
            f"{directory}: expected fragment.bin and manifest.json"
        )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise ValueError("manifest.json: unsupported injection schema")
    if manifest.get("fragment_file") != "fragment.bin":
        raise ValueError("manifest.json: fragment_file must be fragment.bin")

    fragment = fragment_path.read_bytes()
    actual_hash = hashlib.sha256(fragment).hexdigest().upper()
    if actual_hash != str(manifest.get("fragment_sha256", "")).upper():
        raise ValueError("fragment.bin does not match manifest.json")

    segments_value = manifest.get("segments")
    if not isinstance(segments_value, list) or not segments_value:
        raise ValueError("manifest.json: segments must not be empty")
    memory_chunks: list[tuple[str, int, bytes]] = []
    for index, row in enumerate(segments_value, 1):
        if not isinstance(row, dict):
            raise ValueError(f"segments[{index}]: expected an object")
        offset = integer(row.get("file_offset"), f"segments[{index}].file_offset")
        address = integer(
            row.get("runtime_address"),
            f"segments[{index}].runtime_address",
        )
        size = integer(row.get("size"), f"segments[{index}].size")
        word_range(address, size, f"segments[{index}]")
        if offset < 0 or offset % 4 or offset + size > len(fragment):
            raise ValueError(f"segments[{index}]: invalid fragment range")
        memory_chunks.append(
            (f"segment {index}", address, fragment[offset : offset + size])
        )

    zero_fill_value = manifest.get("zero_fill", [])
    if not isinstance(zero_fill_value, list):
        raise ValueError("manifest.json: zero_fill must be a list")
    for index, row in enumerate(zero_fill_value, 1):
        if not isinstance(row, dict):
            raise ValueError(f"zero_fill[{index}]: expected an object")
        address = integer(
            row.get("runtime_address"),
            f"zero_fill[{index}].runtime_address",
        )
        size = integer(row.get("size"), f"zero_fill[{index}].size")
        word_range(address, size, f"zero_fill[{index}]")
        memory_chunks.append((f"zero fill {index}", address, bytes(size)))

    writes_value = manifest.get("writes", [])
    if not isinstance(writes_value, list):
        raise ValueError("manifest.json: writes must be a list")
    guarded_writes: list[tuple[str, int, bytes, bytes]] = []
    for index, row in enumerate(writes_value, 1):
        if not isinstance(row, dict):
            raise ValueError(f"writes[{index}]: expected an object")
        write_id = str(row.get("id", "")).strip()
        if not write_id:
            raise ValueError(f"writes[{index}].id: expected a value")
        address = integer(
            row.get("runtime_address"),
            f"writes[{index}].runtime_address",
        )
        expected = encoded_bytes(
            row.get("expected_hex", ""),
            f"writes[{index}].expected_hex",
        )
        replacement = encoded_bytes(
            row.get("replacement_hex", ""),
            f"writes[{index}].replacement_hex",
        )
        word_range(address, len(expected), f"writes[{index}]")
        if len(expected) != len(replacement):
            raise ValueError(
                f"writes[{index}]: expected and replacement sizes differ"
            )
        guarded_writes.append((write_id, address, expected, replacement))

    return fragment, memory_chunks, guarded_writes


def main() -> int:
    args = parse_args()
    if not 1 <= args.port <= 65535:
        raise ValueError("PINE port is outside 1..65535")
    _fragment, memory_chunks, guarded_writes = load_candidate(args.input)

    with PineClient(args.port) as client:
        initial_state = client.status()
        if initial_state == "shutdown":
            raise RuntimeError("PCSX2 virtual machine is shut down")
        resume_after = initial_state == "running"
        if resume_after:
            client.pause()
        try:
            pending_writes: list[tuple[str, int, bytes]] = []
            for write_id, address, expected, replacement in guarded_writes:
                live = client.read(address, len(expected))
                if live == replacement:
                    continue
                if live != expected:
                    raise RuntimeError(
                        f"{write_id}: live guard mismatch at "
                        f"0x{address:08X}: {live.hex().upper()}"
                    )
                pending_writes.append((write_id, address, replacement))

            for _label, address, value in memory_chunks:
                client.write(address, value)
            for _write_id, address, replacement in pending_writes:
                client.write(address, replacement)

            for label, address, value in memory_chunks:
                if client.read(address, len(value)) != value:
                    raise RuntimeError(
                        f"{label}: readback mismatch at 0x{address:08X}"
                    )
            for write_id, address, _expected, replacement in guarded_writes:
                if client.read(address, len(replacement)) != replacement:
                    raise RuntimeError(
                        f"{write_id}: readback mismatch at 0x{address:08X}"
                    )

            client.clear_execution_caches()
        finally:
            if resume_after:
                client.resume()

    print(
        f"Applied {len(memory_chunks)} memory ranges and "
        f"{len(pending_writes)} guarded writes; "
        f"{len(guarded_writes) - len(pending_writes)} already active"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
