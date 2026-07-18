from __future__ import annotations

import argparse
import math
import mmap
import struct
from pathlib import Path


def u32(memory: mmap.mmap, offset: int) -> int:
    return struct.unpack_from("<I", memory, offset)[0]


def i32(memory: mmap.mmap, offset: int) -> int:
    return struct.unpack_from("<i", memory, offset)[0]


def f32(memory: mmap.mmap, offset: int) -> float:
    return struct.unpack_from("<f", memory, offset)[0]


def resource_name(memory: mmap.mmap, resource: int, size: int) -> str | None:
    if not resource or resource + 4 > size:
        return None
    pointer = u32(memory, resource)
    if not pointer or pointer >= size:
        return None
    end = memory.find(b"\0", pointer, min(pointer + 96, size))
    if end < 0:
        return None
    try:
        value = memory[pointer:end].decode("ascii")
    except UnicodeDecodeError:
        return None
    return value if value.startswith(("TEX_", "CLT_")) else None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="List likely 0xF8-byte CC2 sprite objects in an extracted EE RAM snapshot"
    )
    parser.add_argument("memory", type=Path)
    parser.add_argument("--source-width", type=int)
    parser.add_argument("--source-height", type=int)
    parser.add_argument("--min-source-width", type=int, default=1)
    parser.add_argument("--max-source-width", type=int, default=1024)
    parser.add_argument("--min-source-height", type=int, default=1)
    parser.add_argument("--max-source-height", type=int, default=1024)
    parser.add_argument("--alignment", type=lambda value: int(value, 0), default=8)
    parser.add_argument("--name", help="case-insensitive substring required in the resource name")
    parser.add_argument("--limit", type=int, default=500)
    args = parser.parse_args()

    size = args.memory.stat().st_size
    found = 0
    print(
        "address\tx\ty\tdisplay_width\tdisplay_height\tu_fixed\tv_fixed\t"
        "source_width\tsource_height\tresource\tname"
    )
    with args.memory.open("rb") as handle, mmap.mmap(
        handle.fileno(), 0, access=mmap.ACCESS_READ
    ) as memory:
        for base in range(0, size - 0xF8, args.alignment):
            if u32(memory, base + 0x70) != 1:
                continue
            source_width = i32(memory, base + 0x60)
            source_height = i32(memory, base + 0x64)
            if args.source_width is not None and source_width != args.source_width:
                continue
            if args.source_height is not None and source_height != args.source_height:
                continue
            if not args.min_source_width <= source_width <= args.max_source_width:
                continue
            if not args.min_source_height <= source_height <= args.max_source_height:
                continue
            values = [f32(memory, base + offset) for offset in (0x50, 0x54, 0x58, 0x5C)]
            if not all(math.isfinite(value) and abs(value) <= 4096 for value in values):
                continue
            resource = u32(memory, base + 0xEC)
            if resource and resource >= size:
                continue
            name = resource_name(memory, resource, size)
            if name is None:
                continue
            if args.name is not None and args.name.casefold() not in name.casefold():
                continue
            print(
                f"0x{base:08X}\t{values[0]:.3f}\t{values[1]:.3f}\t"
                f"{values[2]:.3f}\t{values[3]:.3f}\t"
                f"{i32(memory, base + 0x68)}\t{i32(memory, base + 0x6C)}\t"
                f"{source_width}\t{source_height}\t0x{resource:08X}\t{name}"
            )
            found += 1
            if found >= args.limit:
                break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
