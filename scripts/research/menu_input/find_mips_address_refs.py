#!/usr/bin/env python3
"""Find LUI plus ADDIU/ORI references to a raw-module runtime address."""

from __future__ import annotations

import argparse
from pathlib import Path

from paths import PATHS


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("address", type=lambda value: int(value, 0))
    parser.add_argument("--address-delta", type=lambda value: int(value, 0), default=0)
    parser.add_argument("--window", type=int, default=12)
    args = parser.parse_args()

    data = args.binary.read_bytes()
    words = [int.from_bytes(data[i : i + 4], "little") for i in range(0, len(data) - 3, 4)]
    low = args.address & 0xFFFF
    hi_addiu = ((args.address + 0x8000) >> 16) & 0xFFFF
    hi_ori = (args.address >> 16) & 0xFFFF
    for index, first in enumerate(words):
        if first >> 26 != 0x0F:
            continue
        reg = (first >> 16) & 31
        hi = first & 0xFFFF
        for second_index in range(index + 1, min(index + args.window + 1, len(words))):
            second = words[second_index]
            op = second >> 26
            rs = (second >> 21) & 31
            rt = (second >> 16) & 31
            if rs != reg or rt != reg or (second & 0xFFFF) != low:
                continue
            if (op == 0x09 and hi == hi_addiu) or (op == 0x0D and hi == hi_ori):
                first_offset = index * 4
                second_offset = second_index * 4
                print(
                    f"0x{first_offset:08X}\t0x{second_offset:08X}\t"
                    f"runtime=0x{first_offset + args.address_delta:08X}"
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
