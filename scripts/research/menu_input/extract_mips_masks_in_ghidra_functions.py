#!/usr/bin/env python3
"""List face-button ANDI instructions inside named Ghidra-exported functions."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

FUNCTION_RE = re.compile(r"(?m)^(?:[\w *]+)\s+(FUN_([0-9a-f]{8}))\([^\n]*\)\s*\n\s*\{")
FACE_MASKS = {0x10: "triangle", 0x20: "circle", 0x40: "cross", 0x80: "square"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("c_export", type=Path)
    parser.add_argument("--file-to-runtime-delta", type=lambda value: int(value, 0), required=True)
    parser.add_argument("functions", nargs="+")
    args = parser.parse_args()

    source = args.c_export.read_text(encoding="utf-8", errors="replace")
    addresses = sorted(int(match.group(2), 16) for match in FUNCTION_RE.finditer(source))
    data = args.binary.read_bytes()

    print("function\truntime_address\tfile_offset\tregisters\tmask\tbytes")
    for requested in args.functions:
        name = requested if requested.startswith("FUN_") else f"FUN_{requested.lower()}"
        start = int(name[4:], 16)
        if start not in addresses:
            raise SystemExit(f"Function not found in export: {name}")
        index = addresses.index(start)
        end = addresses[index + 1] if index + 1 < len(addresses) else start + 0x10000
        start_offset = start - args.file_to_runtime_delta
        end_offset = min(end - args.file_to_runtime_delta, len(data))
        for offset in range(start_offset, end_offset, 4):
            word = int.from_bytes(data[offset : offset + 4], "little")
            if word >> 26 != 0x0C or (word & 0xFFFF) not in FACE_MASKS:
                continue
            rs = (word >> 21) & 0x1F
            rt = (word >> 16) & 0x1F
            mask = word & 0xFFFF
            print(
                f"{name}\t0x{offset + args.file_to_runtime_delta:08X}\t0x{offset:08X}\t"
                f"r{rs}->r{rt}\t{FACE_MASKS[mask]}(0x{mask:02X})\t{data[offset:offset+4].hex().upper()}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
