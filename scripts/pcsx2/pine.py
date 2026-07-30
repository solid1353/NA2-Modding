#!/usr/bin/env python3
from __future__ import annotations

import argparse
import socket
import struct


READ32 = 0x02
WRITE32 = 0x06
LOAD_STATE = 0x0A
STATUS = 0x0F
SCREENSHOT = 0x11
PAUSE = 0x12
RESUME = 0x13
CLEAR_EXECUTION_CACHES = 0x14
PAD_PULSE = 0x15

PAD_BUTTONS = {
    "up": 0,
    "right": 1,
    "down": 2,
    "left": 3,
    "triangle": 4,
    "circle": 5,
    "cross": 6,
    "square": 7,
    "select": 8,
    "start": 9,
    "l1": 10,
    "l2": 11,
    "r1": 12,
    "r2": 13,
    "l3": 14,
    "r3": 15,
}

STATUS_NAMES = {
    0: "running",
    1: "paused",
    2: "shutdown",
}


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

    def _receive(self, size: int) -> bytes:
        result = bytearray()
        while len(result) < size:
            chunk = self.socket.recv(size - len(result))
            if not chunk:
                raise RuntimeError("PCSX2 closed the PINE connection")
            result.extend(chunk)
        return bytes(result)

    def exchange(self, payload: bytes) -> bytes:
        self.socket.sendall(struct.pack("<I", len(payload) + 4) + payload)
        reply_size = struct.unpack("<I", self._receive(4))[0]
        if reply_size < 5:
            raise RuntimeError(f"PINE returned invalid reply size {reply_size}")
        reply = self._receive(reply_size - 4)
        if reply[0] != 0:
            raise RuntimeError("PCSX2 rejected the PINE request")
        return reply[1:]

    def command(self, opcode: int) -> None:
        if self.exchange(bytes([opcode])):
            raise RuntimeError(f"PINE opcode 0x{opcode:02X} returned unexpected data")

    def status(self) -> str:
        reply = self.exchange(bytes([STATUS]))
        if len(reply) != 4:
            raise RuntimeError("PINE Status returned a malformed reply")
        value = struct.unpack("<I", reply)[0]
        try:
            return STATUS_NAMES[value]
        except KeyError as exc:
            raise RuntimeError(f"PINE returned unknown status {value}") from exc

    def pause(self) -> None:
        self.command(PAUSE)

    def load_state(self, slot: int) -> None:
        if not 0 <= slot <= 255:
            raise ValueError("savestate slot is outside 0..255")
        if self.exchange(bytes([LOAD_STATE, slot])):
            raise RuntimeError("PINE LoadState returned unexpected data")
        # LoadState is queued by PCSX2. The synchronous pause is a barrier:
        # its CPU-thread callback runs only after the queued load completes.
        self.pause()

    def resume(self) -> None:
        self.command(RESUME)

    def clear_execution_caches(self) -> None:
        self.command(CLEAR_EXECUTION_CACHES)

    def screenshot(self) -> None:
        self.command(SCREENSHOT)

    def pad_pulse(
        self, button: int, duration_ms: int, controller: int = 0
    ) -> None:
        if not 0 <= controller <= 7:
            raise ValueError("controller is outside 0..7")
        if not 0 <= button <= 15:
            raise ValueError("button is outside 0..15")
        if not 1 <= duration_ms <= 1000:
            raise ValueError("pulse duration is outside 1..1000 ms")
        reply = self.exchange(
            bytes([PAD_PULSE, controller, button])
            + struct.pack("<H", duration_ms)
        )
        if reply:
            raise RuntimeError("PINE PadPulse returned unexpected data")

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
        if address % 4 or length < 0 or length % 4:
            raise ValueError("PINE memory ranges must contain aligned EE words")
        return b"".join(
            struct.pack("<I", self.read32(address + offset))
            for offset in range(0, length, 4)
        )

    def write(self, address: int, value: bytes) -> None:
        if address % 4 or len(value) % 4:
            raise ValueError("PINE memory ranges must contain aligned EE words")
        for offset in range(0, len(value), 4):
            self.write32(
                address + offset,
                int.from_bytes(value[offset : offset + 4], "little"),
            )


def integer(value: str) -> int:
    try:
        return int(value, 0)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid integer: {value!r}") from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Direct PCSX2 PINE client.")
    parser.add_argument("--port", required=True, type=int)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status")
    commands.add_parser("pause")
    commands.add_parser("resume")
    commands.add_parser("refresh")
    commands.add_parser("screenshot")
    pad_pulse = commands.add_parser("pad-pulse")
    pad_pulse.add_argument("button", choices=sorted(PAD_BUTTONS))
    pad_pulse.add_argument("--controller", type=integer, default=0)
    pad_pulse.add_argument("--milliseconds", type=integer, default=100)
    load_state = commands.add_parser("load-state")
    load_state.add_argument("slot", type=integer)
    read = commands.add_parser("read")
    read.add_argument("address", type=integer)
    read.add_argument("length", type=integer)
    write = commands.add_parser("write")
    write.add_argument("address", type=integer)
    write.add_argument("hex_bytes")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not 1 <= args.port <= 65535:
        raise ValueError("PINE port is outside 1..65535")
    with PineClient(args.port) as client:
        if args.command == "status":
            print(client.status())
        elif args.command == "pause":
            client.pause()
            print(client.status())
        elif args.command == "load-state":
            client.load_state(args.slot)
            print(f"savestate slot {args.slot} loaded; paused")
        elif args.command == "resume":
            client.resume()
            print(client.status())
        elif args.command == "refresh":
            client.clear_execution_caches()
            print("execution caches cleared")
        elif args.command == "screenshot":
            client.screenshot()
            print("screenshot queued")
        elif args.command == "pad-pulse":
            client.pad_pulse(
                PAD_BUTTONS[args.button],
                args.milliseconds,
                args.controller,
            )
            print(
                f"controller {args.controller} {args.button} pulsed for "
                f"{args.milliseconds} ms"
            )
        elif args.command == "read":
            print(client.read(args.address, args.length).hex().upper())
        elif args.command == "write":
            value = bytes.fromhex(args.hex_bytes)
            client.write(args.address, value)
            print(f"wrote {len(value)} bytes")
        else:
            raise AssertionError(args.command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
