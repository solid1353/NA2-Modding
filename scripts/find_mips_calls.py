#!/usr/bin/env python3
"""Find direct JAL call sites to a MIPS runtime address in a raw binary."""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("target", type=lambda value: int(value, 0))
    parser.add_argument("--address-delta", type=lambda value: int(value, 0), default=0)
    args = parser.parse_args()
    wanted = (3 << 26) | ((args.target >> 2) & 0x03FFFFFF)
    data = args.binary.read_bytes()
    for offset in range(0, len(data) - 3, 4):
        if int.from_bytes(data[offset : offset + 4], "little") == wanted:
            print(f"0x{offset:08X}\truntime=0x{offset + args.address_delta:08X}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
