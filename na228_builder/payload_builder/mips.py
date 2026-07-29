"""Small deterministic MIPS encoder used by localization asset generators."""

from __future__ import annotations

import struct
from dataclasses import dataclass


@dataclass(frozen=True)
class Relocation:
    offset: int
    kind: str
    symbol: str
    addend: int = 0


def i_type(opcode: int, rs: int, rt: int, immediate: int) -> int:
    return (
        (opcode << 26)
        | (rs << 21)
        | (rt << 16)
        | (immediate & 0xFFFF)
    )


def r_type(
    rs: int,
    rt: int,
    rd: int,
    function: int,
    *,
    shift: int = 0,
) -> int:
    return (
        (rs << 21)
        | (rt << 16)
        | (rd << 11)
        | (shift << 6)
        | function
    )


def cop1(
    function: int,
    fd: int,
    fs: int,
    ft: int = 0,
    *,
    fmt: int = 16,
) -> int:
    return (
        (0x11 << 26)
        | (fmt << 21)
        | (ft << 16)
        | (fs << 11)
        | (fd << 6)
        | function
    )


def mtc1(rt: int, fs: int) -> int:
    return (0x11 << 26) | (4 << 21) | (rt << 16) | (fs << 11)


def mfc1(rt: int, fs: int) -> int:
    return (0x11 << 26) | (rt << 16) | (fs << 11)


def jump(opcode: int, address: int) -> int:
    if opcode not in (0x02, 0x03) or address & 3:
        raise ValueError(f"invalid MIPS jump: opcode={opcode}, target={address:#x}")
    return (opcode << 26) | ((address >> 2) & 0x03FFFFFF)


def load_u32(assembler: "Assembler", register: int, value: int) -> None:
    assembler.emit(i_type(0x0F, 0, register, value >> 16))
    if value & 0xFFFF:
        assembler.emit(i_type(0x0D, register, register, value & 0xFFFF))


class Assembler:
    def __init__(self) -> None:
        self.words: list[int] = []
        self.labels: dict[str, int] = {}
        self.branch_fixups: list[tuple[int, int, int, int, str]] = []
        self.relocations: list[Relocation] = []

    @property
    def offset(self) -> int:
        return len(self.words) * 4

    def emit(self, value: int) -> None:
        self.words.append(value & 0xFFFFFFFF)

    def label(self, name: str) -> None:
        if name in self.labels:
            raise ValueError(f"duplicate label: {name}")
        self.labels[name] = len(self.words)

    def branch(self, opcode: int, rs: int, rt: int, label: str) -> None:
        index = len(self.words)
        self.branch_fixups.append((index, opcode, rs, rt, label))
        self.words.append(0)

    def relocate(
        self,
        value: int,
        kind: str,
        symbol: str,
        *,
        addend: int = 0,
    ) -> None:
        offset = self.offset
        self.emit(value)
        self.relocations.append(Relocation(offset, kind, symbol, addend))

    def jump_symbol(
        self,
        opcode: int,
        symbol: str,
        *,
        addend: int = 0,
    ) -> None:
        if opcode not in (0x02, 0x03):
            raise ValueError(f"unsupported symbolic jump opcode: {opcode}")
        self.relocate(
            opcode << 26,
            "j26" if opcode == 0x02 else "jal26",
            symbol,
            addend=addend,
        )

    def load_symbol_word(
        self,
        address_register: int,
        value_register: int,
        opcode: int,
        symbol: str,
        *,
        addend: int = 0,
    ) -> None:
        self.relocate(
            i_type(0x0F, 0, address_register, 0),
            "hi16",
            symbol,
            addend=addend,
        )
        self.relocate(
            i_type(opcode, address_register, value_register, 0),
            "lo16",
            symbol,
            addend=addend,
        )

    def build(self) -> tuple[bytes, tuple[Relocation, ...]]:
        for index, opcode, rs, rt, label in self.branch_fixups:
            if label not in self.labels:
                raise ValueError(f"undefined branch label: {label}")
            target = self.labels[label]
            immediate = target - (index + 1)
            if not -0x8000 <= immediate <= 0x7FFF:
                raise ValueError(f"branch to {label} is out of range")
            self.words[index] = i_type(opcode, rs, rt, immediate)
        return (
            struct.pack(f"<{len(self.words)}I", *self.words),
            tuple(self.relocations),
        )
