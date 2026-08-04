from __future__ import annotations

from dataclasses import dataclass


RELOCATION_KINDS = frozenset({"abs32", "hi16", "lo16", "j26", "jal26"})
FRAGMENT_KINDS = frozenset({"code", "rodata", "data"})


@dataclass(frozen=True)
class PayloadRelocation:
    offset: int
    kind: str
    symbol: str
    addend: int = 0


@dataclass(frozen=True)
class PayloadFragment:
    owner: str
    symbol: str
    kind: str
    alignment: int
    payload: bytes
    relocations: tuple[PayloadRelocation, ...] = ()
    init: bool = False


@dataclass(frozen=True)
class SymbolicPatch:
    owner: str
    path: str
    offset: int
    expected: bytes
    symbol: str
    encoding: str
    mapping_id: str
    kind: str
    reason: str
    addend: int = 0
    replacement_template: bytes = b""
    relocation_offset: int = 0


@dataclass(frozen=True)
class ResolvedPatch:
    owner: str
    path: str
    offset: int
    expected: bytes
    replacement: bytes
    mapping_id: str
    kind: str
    reason: str


@dataclass(frozen=True)
class LinkedSymbol:
    owner: str
    symbol: str
    kind: str
    file_offset: int
    runtime_address: int
    size: int
    sha256: str


@dataclass(frozen=True)
class ResidentPayloadBuild:
    output_path: str
    payload: bytes
    load_base: int
    entrypoint: int
    memory_end: int
    used_end: int
    symbols: dict[str, LinkedSymbol]
    map_rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


def encode_symbol_reference(kind: str, address: int) -> bytes:
    if kind not in RELOCATION_KINDS:
        raise ValueError(f"Unsupported resident-payload relocation: {kind!r}")
    if not 0 <= address <= 0xFFFFFFFF:
        raise ValueError(f"Resident-payload address is outside 32 bits: 0x{address:X}")
    if kind == "abs32":
        return address.to_bytes(4, "little")
    if kind == "hi16":
        return ((address + 0x8000) >> 16).to_bytes(2, "little")
    if kind == "lo16":
        return (address & 0xFFFF).to_bytes(2, "little")
    if address & 3 or address >= 0x10000000:
        raise ValueError(f"MIPS jump target is not encodable: 0x{address:X}")
    opcode = 0x08000000 if kind == "j26" else 0x0C000000
    return (opcode | (address >> 2)).to_bytes(4, "little")
