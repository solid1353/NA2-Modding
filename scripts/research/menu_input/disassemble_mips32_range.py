#!/usr/bin/env python3
"""Small dependency-free MIPS32 little-endian range disassembler.

This is intended for raw PS2 modules where a full disassembler project is not
available.  It deliberately covers the integer/control-flow instructions most
useful for locating input handlers and leaves uncommon words as `.word`.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from project_paths import PROJECT_PATHS


REG = (
    "zero", "at", "v0", "v1", "a0", "a1", "a2", "a3",
    "t0", "t1", "t2", "t3", "t4", "t5", "t6", "t7",
    "s0", "s1", "s2", "s3", "s4", "s5", "s6", "s7",
    "t8", "t9", "k0", "k1", "gp", "sp", "fp", "ra",
)
FACE = {0x10: "triangle", 0x20: "circle", 0x40: "cross", 0x80: "square"}


def signed16(value: int) -> int:
    return value - 0x10000 if value & 0x8000 else value


def decode(word: int, address: int) -> str:
    op = word >> 26
    rs = (word >> 21) & 31
    rt = (word >> 16) & 31
    rd = (word >> 11) & 31
    sh = (word >> 6) & 31
    fn = word & 63
    imm = word & 0xFFFF
    simm = signed16(imm)
    target = ((address + 4) & 0xF0000000) | ((word & 0x03FFFFFF) << 2)
    branch = address + 4 + (simm << 2)

    if word == 0:
        return "nop"
    if op == 0:
        r3 = {
            0x20: "add", 0x21: "addu", 0x22: "sub", 0x23: "subu",
            0x24: "and", 0x25: "or", 0x26: "xor", 0x27: "nor",
            0x2A: "slt", 0x2B: "sltu",
        }
        if fn in r3:
            return f"{r3[fn]} {REG[rd]}, {REG[rs]}, {REG[rt]}"
        if fn in (0x00, 0x02, 0x03):
            name = {0x00: "sll", 0x02: "srl", 0x03: "sra"}[fn]
            return f"{name} {REG[rd]}, {REG[rt]}, {sh}"
        if fn == 0x08:
            return f"jr {REG[rs]}"
        if fn == 0x09:
            return f"jalr {REG[rd]}, {REG[rs]}"
        if fn in (0x10, 0x12):
            name = {0x10: "mfhi", 0x12: "mflo"}[fn]
            return f"{name} {REG[rd]}"
        if fn in (0x18, 0x19, 0x1A, 0x1B):
            name = {0x18: "mult", 0x19: "multu", 0x1A: "div", 0x1B: "divu"}[fn]
            return f"{name} {REG[rs]}, {REG[rt]}"
    if op in (2, 3):
        return f"{'j' if op == 2 else 'jal'} 0x{target:08X}"
    if op in (4, 5):
        return f"{'beq' if op == 4 else 'bne'} {REG[rs]}, {REG[rt]}, 0x{branch:08X}"
    if op in (6, 7):
        return f"{'blez' if op == 6 else 'bgtz'} {REG[rs]}, 0x{branch:08X}"
    if op == 1:
        name = {0: "bltz", 1: "bgez", 16: "bltzal", 17: "bgezal"}.get(rt)
        if name:
            return f"{name} {REG[rs]}, 0x{branch:08X}"
    if op in (8, 9, 10, 11):
        name = {8: "addi", 9: "addiu", 10: "slti", 11: "sltiu"}[op]
        return f"{name} {REG[rt]}, {REG[rs]}, {simm}"
    if op in (12, 13, 14):
        name = {12: "andi", 13: "ori", 14: "xori"}[op]
        note = f" ; {FACE[imm]}" if op == 12 and imm in FACE else ""
        return f"{name} {REG[rt]}, {REG[rs]}, 0x{imm:04X}{note}"
    if op == 15:
        return f"lui {REG[rt]}, 0x{imm:04X}"
    memory = {
        0x20: "lb", 0x21: "lh", 0x23: "lw", 0x24: "lbu", 0x25: "lhu",
        0x28: "sb", 0x29: "sh", 0x2B: "sw", 0x31: "lwc1", 0x39: "swc1",
    }
    if op in memory:
        return f"{memory[op]} {REG[rt]}, {simm}({REG[rs]})"
    return f".word 0x{word:08X}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("start", type=lambda value: int(value, 0))
    parser.add_argument("end", type=lambda value: int(value, 0))
    parser.add_argument("--address-delta", type=lambda value: int(value, 0), default=0)
    args = parser.parse_args()

    data = args.binary.read_bytes()
    start = args.start & ~3
    end = min((args.end + 3) & ~3, len(data))
    if start < 0 or start >= end:
        parser.error("range is outside the binary or empty")
    for offset in range(start, end, 4):
        word = int.from_bytes(data[offset : offset + 4], "little")
        address = offset + args.address_delta
        print(f"0x{offset:08X}  0x{address:08X}  {word:08X}  {decode(word, address)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
