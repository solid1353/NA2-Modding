from __future__ import annotations

import csv
import hashlib
import re
import struct
from dataclasses import dataclass
from pathlib import Path

from .operations import (
    FRAGMENT_KINDS,
    LinkedSymbol,
    PayloadFragment,
    ResidentPayloadBuild,
    encode_symbol_reference,
)


CONFIG_FIELDS = ["key", "value"]
CONFIG_KEYS = {
    "output_path",
    "load_base",
    "entry_offset",
    "minimum_data_offset",
    "maximum_end",
    "reservation_end",
    "loader_function",
    "original_constructor_function",
    "hook_file_offset",
    "cave_file_offset",
    "cave_runtime_address",
    "destination_table_file_offset",
    "old_memory_boundary",
    "development_injection_base",
    "development_injection_end",
}
SYMBOL_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*\Z")
KIND_ORDER = {"code": 0, "rodata": 1, "data": 2}


@dataclass(frozen=True)
class ResidentPayloadConfig:
    output_path: str
    load_base: int
    entry_offset: int
    minimum_data_offset: int
    maximum_end: int
    reservation_end: int
    loader_function: int
    original_constructor_function: int
    hook_file_offset: int
    cave_file_offset: int
    cave_runtime_address: int
    destination_table_file_offset: int
    old_memory_boundary: int
    development_injection_base: int
    development_injection_end: int


def _parse_int(value: str, label: str) -> int:
    try:
        result = int(value, 0)
    except ValueError as exc:
        raise ValueError(f"{label}: invalid integer {value!r}") from exc
    if result < 0:
        raise ValueError(f"{label}: negative integer")
    return result


def _align(value: int, alignment: int) -> int:
    return (value + alignment - 1) & -alignment


def load_config(path: Path | None = None) -> ResidentPayloadConfig:
    path = path or Path(__file__).with_name("config.tsv")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != CONFIG_FIELDS:
            raise ValueError(f"{path}: expected columns " + "\t".join(CONFIG_FIELDS))
        rows = [
            {key: (value or "").strip() for key, value in row.items()}
            for row in reader
            if any((value or "").strip() for value in row.values())
        ]
    values = {row["key"]: row["value"] for row in rows}
    if len(values) != len(rows):
        raise ValueError("resident-payload config contains duplicate keys")
    if set(values) != CONFIG_KEYS:
        raise ValueError(
            "resident-payload config key mismatch; "
            f"missing={sorted(CONFIG_KEYS - values.keys())}, "
            f"extra={sorted(values.keys() - CONFIG_KEYS)}"
        )
    output_path = values["output_path"]
    output_name = Path(output_path).name
    if output_path != f"PRG/{output_name}" or output_name != output_name.upper():
        raise ValueError("resident payload must be an uppercase file directly under PRG")
    if len(output_name.encode("ascii") + b"\0") != 8:
        raise ValueError("resident-payload filename must encode to seven ASCII bytes")
    parsed = {
        key: _parse_int(values[key], key)
        for key in CONFIG_KEYS
        if key != "output_path"
    }
    config = ResidentPayloadConfig(output_path=output_path, **parsed)
    if config.entry_offset != 0x40:
        raise ValueError("resident-payload MWO3 entry offset must be 0x40")
    if config.minimum_data_offset < config.entry_offset + 8:
        raise ValueError("resident-payload minimum data offset overlaps its entrypoint")
    if config.maximum_end <= config.load_base:
        raise ValueError("resident-payload maximum end must exceed its load base")
    if not config.load_base < config.reservation_end <= config.maximum_end:
        raise ValueError(
            "resident-payload reservation end must exceed its load base and "
            "remain inside the proven maximum envelope"
        )
    if not (
        config.old_memory_boundary
        <= config.development_injection_base
        < config.development_injection_end
        <= config.load_base
    ):
        raise ValueError(
            "development injection reservation must be inside the protected "
            "pre-payload gap"
        )
    if config.development_injection_base & 0xF or config.development_injection_end & 0xF:
        raise ValueError("development injection reservation must be 16-byte aligned")
    return config


def _validate_fragment(fragment: PayloadFragment) -> None:
    if not fragment.owner or not SYMBOL_PATTERN.fullmatch(fragment.owner):
        raise ValueError(f"Invalid resident-payload owner: {fragment.owner!r}")
    if not SYMBOL_PATTERN.fullmatch(fragment.symbol):
        raise ValueError(f"Invalid resident-payload symbol: {fragment.symbol!r}")
    if fragment.kind not in FRAGMENT_KINDS:
        raise ValueError(f"Invalid fragment kind for {fragment.symbol}: {fragment.kind!r}")
    if not fragment.payload:
        raise ValueError(f"Resident-payload fragment is empty: {fragment.symbol}")
    if fragment.alignment <= 0 or fragment.alignment & (fragment.alignment - 1):
        raise ValueError(f"Fragment alignment is not a power of two: {fragment.symbol}")
    if fragment.init and fragment.kind != "code":
        raise ValueError(f"Only code fragments may be initialization entries: {fragment.symbol}")
    for relocation in fragment.relocations:
        width = 2 if relocation.kind in {"hi16", "lo16"} else 4
        if relocation.offset < 0 or relocation.offset + width > len(fragment.payload):
            raise ValueError(
                f"Relocation exceeds fragment {fragment.symbol}: 0x{relocation.offset:X}"
            )


def _entry_size(init_count: int) -> int:
    if not init_count:
        return 8
    return (7 + 2 * init_count) * 4


def _entry_payload(init_symbols: list[str], addresses: dict[str, int]) -> bytes:
    if not init_symbols:
        return struct.pack("<II", 0x03E00008, 0)
    words = [0x27BDFFF0, 0xFFBF0000]
    for symbol in init_symbols:
        words.extend((int.from_bytes(encode_symbol_reference("jal26", addresses[symbol]), "little"), 0))
    words.extend((0xDFBF0000, 0x27BD0010, 0x03E00008, 0, 0))
    return struct.pack("<" + "I" * len(words), *words)


def build_resident_payload(
    fragments: tuple[PayloadFragment, ...] | list[PayloadFragment],
    *,
    config: ResidentPayloadConfig | None = None,
    layout_shift: int = 0,
) -> ResidentPayloadBuild:
    config = config or load_config()
    if layout_shift < 0 or layout_shift > 0x10000 or layout_shift & 0xF:
        raise ValueError(
            "Resident-payload layout shift must be a 16-byte multiple "
            "from 0 through 65536"
        )
    ordered = sorted(
        tuple(fragments),
        key=lambda item: (KIND_ORDER.get(item.kind, 99), item.owner, item.symbol),
    )
    if not ordered:
        raise ValueError("Resident payload has no contributed fragments")
    for fragment in ordered:
        _validate_fragment(fragment)
    symbols_by_name = {fragment.symbol: fragment for fragment in ordered}
    if len(symbols_by_name) != len(ordered):
        raise ValueError("Resident-payload fragments export duplicate symbols")

    init_symbols = [fragment.symbol for fragment in ordered if fragment.init]
    cursor = (
        _align(config.entry_offset + _entry_size(len(init_symbols)), 0x10)
        + layout_shift
    )
    offsets: dict[str, int] = {}
    for fragment in ordered:
        if fragment.kind != "code":
            cursor = max(cursor, config.minimum_data_offset + layout_shift)
        cursor = _align(cursor, fragment.alignment)
        offsets[fragment.symbol] = cursor
        cursor += len(fragment.payload)
    used_size = _align(cursor, 0x10)
    used_end = config.load_base + used_size
    if used_end > config.reservation_end:
        raise ValueError(
            "Resident payload exceeds the proven reservation envelope: "
            f"0x{used_end:X} > 0x{config.reservation_end:X}"
        )
    output_size = config.reservation_end - config.load_base
    memory_end = config.reservation_end

    addresses = {
        symbol: config.load_base + offset for symbol, offset in offsets.items()
    }
    result = bytearray(output_size)
    output_name = Path(config.output_path).name
    struct.pack_into(
        "<4s7I",
        result,
        0,
        b"MWo3",
        8,
        config.load_base,
        config.entry_offset,
        output_size - 0x50,
        0,
        memory_end,
        memory_end,
    )
    result[0x20:0x28] = output_name.lower().encode("ascii") + b"\0"
    entry = _entry_payload(init_symbols, addresses)
    result[config.entry_offset:config.entry_offset + len(entry)] = entry

    linked: dict[str, LinkedSymbol] = {}
    map_rows: list[dict[str, object]] = []
    for fragment in ordered:
        offset = offsets[fragment.symbol]
        payload = bytearray(fragment.payload)
        for relocation in fragment.relocations:
            target = addresses.get(relocation.symbol)
            if target is None:
                raise ValueError(
                    f"{fragment.symbol}: unresolved symbol {relocation.symbol!r}"
                )
            replacement = encode_symbol_reference(
                relocation.kind, target + relocation.addend
            )
            end = relocation.offset + len(replacement)
            payload[relocation.offset:end] = replacement
        result[offset:offset + len(payload)] = payload
        digest = hashlib.sha256(bytes(payload)).hexdigest().upper()
        symbol = LinkedSymbol(
            owner=fragment.owner,
            symbol=fragment.symbol,
            kind=fragment.kind,
            file_offset=offset,
            runtime_address=addresses[fragment.symbol],
            size=len(payload),
            sha256=digest,
        )
        linked[fragment.symbol] = symbol
        map_rows.append(
            {
                "owner": symbol.owner,
                "symbol": symbol.symbol,
                "kind": symbol.kind,
                "file_offset": f"0x{symbol.file_offset:X}",
                "runtime_address": f"0x{symbol.runtime_address:X}",
                "size": symbol.size,
                "sha256": symbol.sha256,
                "init": int(fragment.init),
            }
        )

    payload = bytes(result)
    summary: dict[str, object] = {
        "output_path": config.output_path,
        "size": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest().upper(),
        "load_base": f"0x{config.load_base:X}",
        "entrypoint": f"0x{config.load_base + config.entry_offset:X}",
        "memory_end": f"0x{memory_end:X}",
        "used_end": f"0x{used_end:X}",
        "used_size": used_size,
        "layout_shift": layout_shift,
        "reservation_end": f"0x{config.reservation_end:X}",
        "maximum_end": f"0x{config.maximum_end:X}",
        "fragment_count": len(ordered),
        "init_count": len(init_symbols),
        "fragments_by_kind": {
            kind: sum(fragment.kind == kind for fragment in ordered)
            for kind in ("code", "rodata", "data")
        },
    }
    return ResidentPayloadBuild(
        output_path=config.output_path,
        payload=payload,
        load_base=config.load_base,
        entrypoint=config.load_base + config.entry_offset,
        memory_end=memory_end,
        used_end=used_end,
        symbols=linked,
        map_rows=tuple(map_rows),
        summary=summary,
    )
