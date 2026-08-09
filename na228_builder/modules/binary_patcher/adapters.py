"""Catalog-value adapters for concrete guarded binary replacements."""

from __future__ import annotations

import math
import struct


ADAPTER_NAMES = frozenset({"mips_lui_float32"})


def validate_adapter_name(name: object) -> str:
    if not isinstance(name, str) or name not in ADAPTER_NAMES:
        raise ValueError(f"Unsupported binary edit adapter: {name!r}")
    return name


def _mips_lui_float32(expected: bytes, value: object) -> bytes:
    if len(expected) != 4:
        raise ValueError("mips_lui_float32 requires a four-byte expected_hex guard")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("mips_lui_float32 requires an int or decimal setting value")
    numeric = float(value)
    if not math.isfinite(numeric):
        raise ValueError("mips_lui_float32 requires a finite setting value")

    instruction = int.from_bytes(expected, "little")
    if instruction >> 26 != 0x0F:
        raise ValueError("mips_lui_float32 expected_hex is not a MIPS LUI instruction")

    encoded = struct.pack(">f", numeric)
    upper, lower = struct.unpack(">HH", encoded)
    if lower != 0:
        raise ValueError(
            "mips_lui_float32 cannot encode this value with one LUI instruction"
        )
    replacement = (instruction & 0xFFFF0000) | upper
    return replacement.to_bytes(4, "little")


def apply_adapter(name: object, expected_hex: str, value: object) -> str:
    name = validate_adapter_name(name)
    expected = bytes.fromhex(expected_hex)
    if name == "mips_lui_float32":
        return _mips_lui_float32(expected, value).hex().upper()
    raise AssertionError(name)
