#!/usr/bin/env python3
"""Find direct JAL call sites to a MIPS runtime address in a binary patcher."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[3]
if str(REPOSITORY) not in sys.path:
    sys.path.insert(0, str(REPOSITORY))

from scripts.research.menu_input.mips_common import little_endian_words  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("target", type=lambda value: int(value, 0))
    parser.add_argument("--address-delta", type=lambda value: int(value, 0), default=0)
    args = parser.parse_args()
    wanted = (3 << 26) | ((args.target >> 2) & 0x03FFFFFF)
    for index, word in enumerate(little_endian_words(args.binary.read_bytes())):
        if word == wanted:
            offset = index * 4
            print(f"0x{offset:08X}\truntime=0x{offset + args.address_delta:08X}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
