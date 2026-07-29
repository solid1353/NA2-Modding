#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import socket
import struct
from pathlib import Path


READ32 = 0x02
WRITE32 = 0x06
CRC = 0x0D


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Apply exact-guarded Injection Lab overlay caller writes."
    )
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--port", required=True, type=int)
    return parser.parse_args()


class PineClient:
    def __init__(self, port: int) -> None:
        self.socket = socket.create_connection(("127.0.0.1", port), timeout=3)
        self.socket.settimeout(3)

    def close(self) -> None:
        self.socket.close()

    def __enter__(self) -> "PineClient":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def receive(self, size: int) -> bytes:
        result = bytearray()
        while len(result) < size:
            chunk = self.socket.recv(size - len(result))
            if not chunk:
                raise RuntimeError("PCSX2 closed the PINE connection")
            result.extend(chunk)
        return bytes(result)

    def exchange(self, payload: bytes) -> bytes:
        self.socket.sendall(struct.pack("<I", len(payload) + 4) + payload)
        reply_size = struct.unpack("<I", self.receive(4))[0]
        if reply_size < 5:
            raise RuntimeError(f"PINE returned invalid reply size {reply_size}")
        reply = self.receive(reply_size - 4)
        if reply[0] != 0:
            raise RuntimeError("PCSX2 rejected the PINE request")
        return reply[1:]

    def string_query(self, opcode: int) -> str:
        reply = self.exchange(bytes([opcode]))
        if len(reply) < 5:
            raise RuntimeError("PINE returned a malformed string")
        size = struct.unpack_from("<I", reply)[0]
        raw = reply[4:]
        if size != len(raw) or not raw or raw[-1] != 0:
            raise RuntimeError("PINE returned a malformed string")
        return raw[:-1].decode("utf-8", errors="replace")

    def read32(self, address: int) -> int:
        reply = self.exchange(bytes([READ32]) + struct.pack("<I", address))
        if len(reply) != 4:
            raise RuntimeError("PINE Read32 returned a malformed reply")
        return struct.unpack("<I", reply)[0]

    def write32(self, address: int, value: int) -> None:
        reply = self.exchange(
            bytes([WRITE32]) + struct.pack("<II", address, value)
        )
        if reply:
            raise RuntimeError("PINE Write32 returned unexpected data")

    def read(self, address: int, length: int) -> bytes:
        return b"".join(
            struct.pack("<I", self.read32(address + offset))
            for offset in range(0, length, 4)
        )

    def write(self, address: int, value: bytes) -> None:
        for offset in range(0, len(value), 4):
            self.write32(
                address + offset,
                int.from_bytes(value[offset : offset + 4], "little"),
            )


def load_manifest(path: Path) -> tuple[str, list[dict[str, object]]]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("mode") != "production_c":
        raise ValueError("Manifest is not an Injection Lab production build")
    if manifest.get("redirect_mode") != "overlay":
        raise ValueError("Manifest does not declare guarded overlay writes")
    crc = str(manifest.get("current_crc", "")).upper()
    if len(crc) != 8 or any(character not in "0123456789ABCDEF" for character in crc):
        raise ValueError("Manifest current_crc is invalid")
    rows = manifest.get("overlay_writes")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Manifest overlay_writes is empty")
    parsed: list[dict[str, object]] = []
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            raise ValueError(f"overlay_writes[{index}] is not an object")
        address = int(str(row["runtime_address"]), 0)
        expected = bytes.fromhex(str(row["expected_hex"]))
        replacement = bytes.fromhex(str(row["replacement_hex"]))
        if (
            address % 4
            or not expected
            or len(expected) % 4
            or len(expected) != len(replacement)
        ):
            raise ValueError(f"overlay_writes[{index}] has invalid word ranges")
        parsed.append(
            {
                "id": str(row["id"]),
                "address": address,
                "expected": expected,
                "replacement": replacement,
            }
        )
    return crc, parsed


def main() -> int:
    args = parse_args()
    if not 1 <= args.port <= 65535:
        raise ValueError("PINE port is outside 1..65535")
    expected_crc, writes = load_manifest(args.manifest)
    with PineClient(args.port) as client:
        live_crc = client.string_query(CRC).upper()
        if live_crc != expected_crc:
            raise RuntimeError(
                f"Live CRC {live_crc!r} does not match Current {expected_crc}"
            )
        pending: list[dict[str, object]] = []
        for row in writes:
            live = client.read(int(row["address"]), len(row["expected"]))
            if live == row["replacement"]:
                continue
            if live != row["expected"]:
                raise RuntimeError(
                    f"{row['id']}: live guard mismatch at "
                    f"0x{int(row['address']):08X}: {live.hex().upper()}"
                )
            pending.append(row)
        for row in pending:
            client.write(int(row["address"]), row["replacement"])
        for row in writes:
            live = client.read(int(row["address"]), len(row["replacement"]))
            if live != row["replacement"]:
                raise RuntimeError(
                    f"{row['id']}: overlay write readback mismatch at "
                    f"0x{int(row['address']):08X}"
                )
    print(
        f"Applied {len(pending)} guarded overlay writes; "
        f"{len(writes) - len(pending)} already active"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
