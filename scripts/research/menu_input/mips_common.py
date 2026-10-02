"""Shared MIPS word and face-button helpers for the menu-input tools."""

from __future__ import annotations

import re

FACE_MASKS = {0x10: "triangle", 0x20: "circle", 0x40: "cross", 0x80: "square"}
# Group 1 is the Ghidra function name; group 2 is its hexadecimal address.
FUNCTION_RE = re.compile(r"(?m)^(?:[\w *]+)\s+(FUN_([0-9a-f]{8}))\([^\n]*\)\s*\n\s*\{")


def little_endian_words(data: bytes) -> list[int]:
    usable = len(data) - len(data) % 4
    return [int.from_bytes(data[offset : offset + 4], "little") for offset in range(0, usable, 4)]


def is_face_mask_andi(word: int) -> bool:
    return word >> 26 == 0x0C and (word & 0xFFFF) in FACE_MASKS
