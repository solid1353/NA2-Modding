"""Adapters for concrete guarded binary replacements."""

from __future__ import annotations

import codecs
import math
import struct


ADAPTER_NAMES = frozenset(
    {
        "ascii_fixed",
        "mips_lui_float32",
        "mips_simple_display_default",
        "mips_substitution_frames_before",
        "nul_padded_text",
    }
)
FIXED_VALUE_ADAPTER_NAMES = frozenset({"ascii_fixed", "nul_padded_text"})


def validate_adapter_name(name: object) -> str:
    if not isinstance(name, str) or name not in ADAPTER_NAMES:
        raise ValueError(f"Unsupported binary edit adapter: {name!r}")
    return name


def is_fixed_value_adapter(name: object) -> bool:
    return validate_adapter_name(name) in FIXED_VALUE_ADAPTER_NAMES


def apply_fixed_adapter(
    name: object,
    expected_value: object,
    replacement_value: object,
    *,
    encoding: object = None,
    length: object = None,
) -> tuple[str, str]:
    name = validate_adapter_name(name)
    if name not in FIXED_VALUE_ADAPTER_NAMES:
        raise ValueError(f"Binary edit adapter does not accept fixed values: {name!r}")
    if name == "ascii_fixed" and (encoding is not None or length is not None):
        raise ValueError("ascii_fixed does not accept encoding or length")
    if name == "nul_padded_text":
        if not isinstance(encoding, str) or not encoding:
            raise ValueError("nul_padded_text encoding must be non-empty text")
        try:
            encoding = codecs.lookup(encoding).name
        except LookupError as exc:
            raise ValueError(
                f"nul_padded_text encoding is unknown: {encoding!r}"
            ) from exc
        if isinstance(length, bool) or not isinstance(length, int) or length <= 0:
            raise ValueError("nul_padded_text length must be a positive integer")
    encoded: list[bytes] = []
    for label, value in (
        ("expected_value", expected_value),
        ("replacement_value", replacement_value),
    ):
        if not isinstance(value, str) or not value or "\0" in value:
            raise ValueError(f"{name} {label} must be non-empty text without a NUL")
        try:
            encoded.append(value.encode("ascii" if name == "ascii_fixed" else encoding))
        except UnicodeEncodeError as exc:
            if name == "ascii_fixed":
                raise ValueError(f"ascii_fixed {label} must be ASCII") from exc
            raise ValueError(
                f"nul_padded_text {label} is not encodable as {encoding}"
            ) from exc
    if name == "ascii_fixed" and len(encoded[0]) != len(encoded[1]):
        raise ValueError("ascii_fixed values must have equal encoded lengths")
    if name == "nul_padded_text":
        assert isinstance(length, int)
        for label, value in zip(("expected_value", "replacement_value"), encoded):
            if len(value) >= length:
                raise ValueError(
                    f"nul_padded_text {label} does not fit its NUL-padded length"
                )
        encoded = [value + bytes(length - len(value)) for value in encoded]
    return encoded[0].hex().upper(), encoded[1].hex().upper()


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


def _mips_substitution_frames_before(expected: bytes, value: object) -> bytes:
    native_timing_branch = bytes.fromhex("1100010600000000")
    if expected != native_timing_branch:
        raise ValueError(
            "mips_substitution_frames_before requires the native "
            "bgez s0,+17; nop instruction pair"
        )
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("mips_substitution_frames_before requires an integer value")
    if not 0 <= value <= 16:
        raise ValueError("mips_substitution_frames_before requires 0 through 16 frames")

    # Branch from 0x002295C8 to 0x00229620, past both the negative-timing RNG
    # path and the native nonnegative clamp. The delay slot supplies the
    # history helper's literal number of prior records. The current record is
    # checked separately by the helper, so N means exactly N pre-impact frames.
    branch_past_timing_policy = 0x10000015
    load_prior_record_count = 0x24100000 | value
    return struct.pack("<II", branch_past_timing_policy, load_prior_record_count)


def _mips_simple_display_default(expected: bytes, value: object) -> bytes:
    native_simple_display_default = bytes.fromhex("25186600")
    if expected != native_simple_display_default:
        raise ValueError(
            "mips_simple_display_default requires the native or v1,v1,a2 instruction"
        )
    if value == "on":
        return expected
    if value == "off":
        return bytes(4)
    raise ValueError("mips_simple_display_default requires 'off' or 'on'")


def apply_adapter(name: object, expected_hex: str, value: object) -> str:
    name = validate_adapter_name(name)
    expected = bytes.fromhex(expected_hex)
    if name == "mips_lui_float32":
        return _mips_lui_float32(expected, value).hex().upper()
    if name == "mips_simple_display_default":
        return _mips_simple_display_default(expected, value).hex().upper()
    if name == "mips_substitution_frames_before":
        return _mips_substitution_frames_before(expected, value).hex().upper()
    raise AssertionError(name)
