from __future__ import annotations

import argparse
import mmap
import struct
from pathlib import Path


def parse_pattern(args: argparse.Namespace) -> tuple[str, bytes]:
    choices = [args.ascii is not None, args.hex is not None, args.u32 is not None, args.f32 is not None]
    if sum(choices) != 1:
        raise ValueError("specify exactly one of --ascii, --hex, --u32, or --f32")
    if args.ascii is not None:
        return repr(args.ascii), args.ascii.encode("ascii")
    if args.hex is not None:
        return args.hex, bytes.fromhex(args.hex)
    if args.u32 is not None:
        value = int(args.u32, 0)
        return f"0x{value:08X}", struct.pack("<I", value)
    value = float(args.f32)
    return repr(value), struct.pack("<f", value)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Find byte, pointer, or float patterns in an extracted EE RAM snapshot"
    )
    parser.add_argument("memory", type=Path)
    parser.add_argument("--ascii")
    parser.add_argument("--hex")
    parser.add_argument("--u32")
    parser.add_argument("--f32")
    parser.add_argument("--alignment", type=lambda value: int(value, 0), default=1)
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()
    if args.alignment < 1:
        raise ValueError("alignment must be positive")
    if args.limit < 1:
        raise ValueError("limit must be positive")

    label, pattern = parse_pattern(args)
    count = 0
    with args.memory.open("rb") as handle, mmap.mmap(
        handle.fileno(), 0, access=mmap.ACCESS_READ
    ) as memory:
        cursor = 0
        while count < args.limit:
            offset = memory.find(pattern, cursor)
            if offset < 0:
                break
            cursor = offset + 1
            if offset % args.alignment:
                continue
            print(f"0x{offset:08X}\t{label}")
            count += 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
