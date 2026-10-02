"""Adapters for concrete guarded binary replacements."""

from __future__ import annotations

import codecs


ADAPTER_NAMES = frozenset({"ascii_fixed", "nul_padded_text"})


def validate_adapter_name(name: object) -> str:
    if not isinstance(name, str) or name not in ADAPTER_NAMES:
        raise ValueError(f"Unsupported binary edit adapter: {name!r}")
    return name



def apply_fixed_adapter(
    name: object,
    expected_value: object,
    replacement_value: object,
    *,
    encoding: object = None,
    length: object = None,
) -> tuple[str, str]:
    name = validate_adapter_name(name)
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
        for label, value in zip(("expected_value", "replacement_value"), encoded):
            if len(value) >= length:
                raise ValueError(
                    f"nul_padded_text {label} does not fit its NUL-padded length"
                )
        encoded = [value + bytes(length - len(value)) for value in encoded]
    return encoded[0].hex().upper(), encoded[1].hex().upper()
