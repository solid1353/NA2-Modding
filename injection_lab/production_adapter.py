#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
from dataclasses import replace
from pathlib import Path


LAB_ROOT = Path(__file__).resolve().parent
REPOSITORY = LAB_ROOT.parent
sys.path.insert(0, str(REPOSITORY))

from na228_builder.payload_builder import ee_c_fragments
from na228_builder.payload_builder.operations import (
    PayloadFragment,
    PayloadRelocation,
    encode_symbol_reference,
)


CRC_PATTERN = re.compile(r"[0-9A-F]{8}\Z")
SYMBOL_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*\Z")
SOURCE_FIELDS = ["source_id", "language", "path", "namespace"]
IMPORT_FIELDS = ["source_id", "name", "symbol", "addend"]
FRAGMENT_FIELDS = ["source_id", "order", "object_fragment", "fragment_id"]
ENTRY_FIELDS = ["source_id", "entry_symbol", "abi", "purpose"]
SYMBOL_MAP_FIELDS = [
    "owner",
    "symbol",
    "kind",
    "file_offset",
    "runtime_address",
    "size",
    "sha256",
    "init",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compile one canonical runtime-injector C source into an Injection "
            "Lab bank and redirect one production entry through the lab dispatcher."
        )
    )
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--entry", required=True)
    return parser.parse_args()


def environment_int(name: str) -> int:
    value = os.environ.get(name, "")
    try:
        result = int(value, 0)
    except ValueError as exc:
        raise ValueError(f"{name} is not a valid integer: {value!r}") from exc
    if not 0 < result <= 0xFFFFFFFF:
        raise ValueError(f"{name} is outside the unsigned 32-bit range")
    return result


def read_tsv(path: Path, fields: list[str]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != fields:
            raise ValueError(f"{path}: expected columns {' '.join(fields)}")
        return [
            {key: (value or "").strip() for key, value in row.items()}
            for row in reader
            if any((value or "").strip() for value in row.values())
        ]


def identifier(value: str, label: str) -> str:
    if not SYMBOL_PATTERN.fullmatch(value):
        raise ValueError(f"{label}: invalid identifier {value!r}")
    return value


def integer(value: str, label: str) -> int:
    try:
        return int(value, 0)
    except ValueError as exc:
        raise ValueError(f"{label}: invalid integer {value!r}") from exc


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def align(value: int, alignment: int) -> int:
    return (value + alignment - 1) & -alignment


def locate_build_record(payload_sha256: str) -> tuple[Path, dict[str, object]]:
    matches: list[tuple[Path, dict[str, object]]] = []
    builds_root = REPOSITORY / "logs" / "na2" / "builds"
    for summary_path in builds_root.glob("*/payload_builder/payload_summary.json"):
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        if str(summary.get("sha256", "")).upper() == payload_sha256:
            matches.append((summary_path.parents[1], summary))
    if not matches:
        raise ValueError(
            "No retained NA2 build record matches the exact Current 228.BIN "
            f"SHA-256 {payload_sha256}"
        )
    matches.sort(key=lambda item: item[0].name)
    selected = matches[-1]
    selected_map = selected[0] / "payload_builder" / "symbol_map.tsv"
    selected_map_sha = sha256(selected_map.read_bytes())
    for record, _summary in matches[:-1]:
        candidate_map = record / "payload_builder" / "symbol_map.tsv"
        if not candidate_map.is_file() or sha256(candidate_map.read_bytes()) != selected_map_sha:
            raise ValueError(
                "Matching 228.BIN build records disagree on their symbol maps: "
                + ", ".join(record.name for record, _ in matches)
            )
    return selected


def load_symbol_map(
    build_record: Path, payload: bytes
) -> dict[str, dict[str, object]]:
    rows = read_tsv(
        build_record / "payload_builder" / "symbol_map.tsv",
        SYMBOL_MAP_FIELDS,
    )
    result: dict[str, dict[str, object]] = {}
    for line, row in enumerate(rows, 2):
        symbol = identifier(row["symbol"], f"symbol_map.tsv:{line} symbol")
        if symbol in result:
            raise ValueError(f"symbol_map.tsv:{line}: duplicate symbol {symbol}")
        offset = integer(row["file_offset"], f"symbol_map.tsv:{line} file_offset")
        address = integer(
            row["runtime_address"], f"symbol_map.tsv:{line} runtime_address"
        )
        size = integer(row["size"], f"symbol_map.tsv:{line} size")
        if offset < 0 or size <= 0 or offset + size > len(payload):
            raise ValueError(
                f"symbol_map.tsv:{line}: {symbol} exceeds exact Current 228.BIN"
            )
        actual_sha = sha256(payload[offset : offset + size])
        expected_sha = row["sha256"].upper()
        if actual_sha != expected_sha:
            raise ValueError(
                f"symbol_map.tsv:{line}: exact Current bytes do not match {symbol}"
            )
        result[symbol] = {
            "offset": offset,
            "address": address,
            "size": size,
            "kind": row["kind"],
            "sha256": actual_sha,
        }
    return result


def load_source(
    source_id: str,
) -> tuple[
    Path,
    str,
    dict[str, ee_c_fragments.SymbolReference],
    list[tuple[int, str, str]],
]:
    package_root = (
        REPOSITORY / "na228_builder" / "features" / "localization" / "runtime_injector"
    )
    source_rows = read_tsv(package_root / "c_sources.tsv", SOURCE_FIELDS)
    selected = [row for row in source_rows if row["source_id"] == source_id]
    if len(selected) != 1:
        raise ValueError(
            f"Production source {source_id!r} must match exactly one c_sources.tsv row"
        )
    row = selected[0]
    if row["language"] != "c":
        raise ValueError(f"Production source {source_id!r} is not C")
    relative_source = Path(row["path"])
    if relative_source.is_absolute() or ".." in relative_source.parts:
        raise ValueError(f"Production source path escapes its package: {row['path']}")
    source_path = (package_root / relative_source).resolve()
    if package_root.resolve() not in source_path.parents or not source_path.is_file():
        raise ValueError(f"Production source was not found in its package: {source_path}")
    namespace = identifier(row["namespace"], "c_sources.tsv namespace")

    imports: dict[str, ee_c_fragments.SymbolReference] = {}
    for line, import_row in enumerate(
        read_tsv(package_root / "c_imports.tsv", IMPORT_FIELDS), 2
    ):
        if import_row["source_id"] != source_id:
            continue
        name = identifier(import_row["name"], f"c_imports.tsv:{line} name")
        if name in imports:
            raise ValueError(f"c_imports.tsv:{line}: duplicate import {name}")
        imports[name] = ee_c_fragments.SymbolReference(
            symbol=identifier(
                import_row["symbol"], f"c_imports.tsv:{line} symbol"
            ),
            addend=integer(import_row["addend"], f"c_imports.tsv:{line} addend"),
        )

    mappings: list[tuple[int, str, str]] = []
    seen_objects: set[str] = set()
    seen_final: set[str] = set()
    for line, fragment_row in enumerate(
        read_tsv(package_root / "c_fragments.tsv", FRAGMENT_FIELDS), 2
    ):
        if fragment_row["source_id"] != source_id:
            continue
        order = integer(fragment_row["order"], f"c_fragments.tsv:{line} order")
        object_fragment = identifier(
            fragment_row["object_fragment"],
            f"c_fragments.tsv:{line} object_fragment",
        )
        fragment_id = identifier(
            fragment_row["fragment_id"], f"c_fragments.tsv:{line} fragment_id"
        )
        if object_fragment in seen_objects or fragment_id in seen_final:
            raise ValueError(
                f"c_fragments.tsv:{line}: duplicate production fragment mapping"
            )
        seen_objects.add(object_fragment)
        seen_final.add(fragment_id)
        mappings.append((order, object_fragment, fragment_id))
    if not mappings:
        raise ValueError(f"Production source {source_id!r} has no fragments")
    mappings.sort()
    return source_path, namespace, imports, mappings


def load_entry(source_id: str, entry_symbol: str) -> dict[str, str]:
    entries = read_tsv(LAB_ROOT / "production_entries.tsv", ENTRY_FIELDS)
    selected = [
        row
        for row in entries
        if row["source_id"] == source_id and row["entry_symbol"] == entry_symbol
    ]
    if len(selected) != 1:
        raise ValueError(
            "The selected production source/entry is not an explicitly "
            "declared Injection Lab ABI boundary"
        )
    entry = selected[0]
    identifier(entry["abi"], "production_entries.tsv abi")
    if not entry["purpose"]:
        raise ValueError("production_entries.tsv purpose must not be empty")
    return entry


def compile_fragments(
    source_id: str,
    source_path: Path,
    namespace: str,
    imports: dict[str, ee_c_fragments.SymbolReference],
    mappings: list[tuple[int, str, str]],
) -> list[PayloadFragment]:
    object_path = LAB_ROOT / "obj" / "production" / f"{source_id}.o"
    object_path.parent.mkdir(parents=True, exist_ok=True)
    extracted = ee_c_fragments.compile_and_extract(
        source_path,
        object_path,
        namespace=namespace,
        toolchain_bin=ee_c_fragments.default_toolchain_bin(REPOSITORY),
        owner="localization.runtime_injector",
        external_symbols=imports,
    )
    aliases = {
        object_fragment: fragment_id
        for _order, object_fragment, fragment_id in mappings
    }
    actual = {fragment.symbol for fragment in extracted.fragments}
    declared = set(aliases)
    if actual != declared:
        raise ValueError(
            f"Production source {source_id}: extracted fragments differ from "
            f"canonical declarations; missing={sorted(declared - actual)}, "
            f"extra={sorted(actual - declared)}"
        )
    by_symbol = {fragment.symbol: fragment for fragment in extracted.fragments}
    result: list[PayloadFragment] = []
    for _order, object_fragment, fragment_id in mappings:
        fragment = by_symbol[object_fragment]
        result.append(
            replace(
                fragment,
                symbol=fragment_id,
                relocations=tuple(
                    PayloadRelocation(
                        offset=relocation.offset,
                        kind=relocation.kind,
                        symbol=aliases.get(relocation.symbol, relocation.symbol),
                        addend=relocation.addend,
                    )
                    for relocation in fragment.relocations
                ),
            )
        )
    return result


def link_bank(
    fragments: list[PayloadFragment],
    *,
    code_base: int,
    code_end: int,
    external_addresses: dict[str, int],
) -> tuple[bytes, dict[str, int]]:
    cursor = code_base
    addresses: dict[str, int] = {}
    for fragment in fragments:
        cursor = align(cursor, fragment.alignment)
        addresses[fragment.symbol] = cursor
        cursor += len(fragment.payload)
    used_end = align(cursor, 4)
    if used_end > code_end:
        raise ValueError(
            "Production C closure exceeds the selected Injection Lab bank: "
            f"0x{used_end:X} > 0x{code_end:X}"
        )

    image = bytearray(used_end - code_base)
    resolved = {**external_addresses, **addresses}
    for fragment in fragments:
        payload = bytearray(fragment.payload)
        for relocation in fragment.relocations:
            target = resolved.get(relocation.symbol)
            if target is None:
                raise ValueError(
                    f"{fragment.symbol}: unresolved production symbol "
                    f"{relocation.symbol!r}"
                )
            replacement = encode_symbol_reference(
                relocation.kind, target + relocation.addend
            )
            end = relocation.offset + len(replacement)
            if relocation.offset < 0 or end > len(payload):
                raise ValueError(
                    f"{fragment.symbol}: relocation exceeds its fragment"
                )
            payload[relocation.offset:end] = replacement
        offset = addresses[fragment.symbol] - code_base
        image[offset : offset + len(payload)] = payload
    return bytes(image), addresses


def word_patch(address: int, value: int) -> str:
    return f"patch=1,EE,{address + 0x20000000:08X},extended,{value:08X}"


def main() -> int:
    args = parse_args()
    source_id = identifier(args.source_id, "source-id")
    entry_symbol = identifier(args.entry, "entry")
    crc = os.environ.get("NA2_INJECTION_CRC", "").upper()
    if not CRC_PATTERN.fullmatch(crc):
        raise ValueError("NA2_INJECTION_CRC must be eight hexadecimal digits")
    injection_base = environment_int("NA2_INJECTION_BASE")
    injection_end = environment_int("NA2_INJECTION_END")
    code_base = environment_int("NA2_INJECTION_CODE_BASE")
    code_end = environment_int("NA2_INJECTION_CODE_END")
    build_id = environment_int("NA2_INJECTION_BUILD_ID")
    if not injection_base < code_base < code_end <= injection_end:
        raise ValueError("Invalid Injection Lab bank reservation")

    payload_path = LAB_ROOT / "data" / "FILES" / "228.BIN"
    payload = payload_path.read_bytes()
    payload_sha256 = sha256(payload)
    build_record, payload_summary = locate_build_record(payload_sha256)
    symbol_map = load_symbol_map(build_record, payload)
    if str(payload_summary.get("load_base", "")).lower() != "0x8f3d00":
        raise ValueError("Matching build record has an unexpected 228.BIN load base")

    source_path, namespace, imports, mappings = load_source(source_id)
    entry_declaration = load_entry(source_id, entry_symbol)
    fragments = compile_fragments(
        source_id, source_path, namespace, imports, mappings
    )
    fragment_ids = {fragment.symbol for fragment in fragments}
    if entry_symbol not in fragment_ids:
        raise ValueError(
            f"Entry {entry_symbol!r} is not a fragment of source {source_id!r}"
        )
    entry_fragment = next(
        fragment for fragment in fragments if fragment.symbol == entry_symbol
    )
    if entry_fragment.kind != "code":
        raise ValueError(f"Entry {entry_symbol!r} is not executable code")

    canonical_imports = {reference.symbol for reference in imports.values()}
    external_addresses: dict[str, int] = {}
    for symbol in canonical_imports:
        row = symbol_map.get(symbol)
        if row is None:
            raise ValueError(
                f"Exact Current symbol map does not resolve import {symbol!r}"
            )
        external_addresses[symbol] = int(row["address"])
    for fragment in fragments:
        for relocation in fragment.relocations:
            if (
                relocation.symbol not in fragment_ids
                and relocation.symbol not in canonical_imports
            ):
                raise ValueError(
                    f"{fragment.symbol}: dependency {relocation.symbol!r} is not "
                    "declared by the selected production source"
                )

    image, addresses = link_bank(
        fragments,
        code_base=code_base,
        code_end=code_end,
        external_addresses=external_addresses,
    )
    resident_entry = symbol_map.get(entry_symbol)
    if resident_entry is None:
        raise ValueError(
            f"Exact Current symbol map does not contain entry {entry_symbol!r}"
        )
    if int(resident_entry["size"]) < 8:
        raise ValueError(f"Production entry {entry_symbol!r} is smaller than 8 bytes")
    resident_address = int(resident_entry["address"])
    resident_offset = int(resident_entry["offset"])
    expected_entry = payload[resident_offset : resident_offset + 8]

    dispatcher = injection_base
    active_pointer = injection_base + 0x10
    hi = (active_pointer + 0x8000) >> 16
    lo = active_pointer & 0xFFFF
    dispatcher_words = (
        0x3C190000 | hi,
        0x8F390000 | lo,
        0x03200008,
        0,
    )
    entry_address = addresses[entry_symbol]
    redirect_words = (
        int.from_bytes(encode_symbol_reference("j26", dispatcher), "little"),
        0,
    )

    output_path = LAB_ROOT / "build" / f"{crc}.pnach"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "// Auto-generated production-aware Injection Lab PNACH",
        "gametitle=Narutimate Accel v2.28 injection lab",
        f"// Current CRC: {crc}",
        f"// Current 228.BIN SHA-256: {payload_sha256}",
        f"// Build record: {build_record.relative_to(REPOSITORY).as_posix()}",
        f"// Production source: {source_id}",
        f"// Production entry: {entry_symbol}",
        f"// Code bank: 0x{code_base:08X}-0x{code_end:08X}",
        f"// Used bank bytes: {len(image)}",
        f"// Build ID: 0x{build_id:08X}",
        "",
        "; selected production C closure",
    ]
    for offset in range(0, len(image), 4):
        value = int.from_bytes(image[offset : offset + 4], "little")
        lines.append(word_patch(code_base + offset, value))
    lines.extend(("", "; fixed tail dispatcher"))
    for index, value in enumerate(dispatcher_words):
        lines.append(word_patch(dispatcher + index * 4, value))
    lines.append(word_patch(active_pointer, entry_address))
    lines.extend(("", "; guarded production resident-entry redirect"))
    for index, value in enumerate(redirect_words):
        lines.append(word_patch(resident_address + index * 4, value))
    lines.append("")
    output_path.write_text("\n".join(lines), encoding="ascii")

    manifest = {
        "schema_version": 1,
        "mode": "production_c",
        "current_crc": crc,
        "payload_sha256": payload_sha256,
        "build_record": build_record.relative_to(REPOSITORY).as_posix(),
        "source_id": source_id,
        "entry_symbol": entry_symbol,
        "entry_abi": entry_declaration["abi"],
        "entry_purpose": entry_declaration["purpose"],
        "entry_resident_address": f"0x{resident_address:08X}",
        "entry_resident_expected_hex": expected_entry.hex().upper(),
        "entry_bank_address": f"0x{entry_address:08X}",
        "dispatcher_address": f"0x{dispatcher:08X}",
        "active_pointer_address": f"0x{active_pointer:08X}",
        "code_base": f"0x{code_base:08X}",
        "code_end": f"0x{code_end:08X}",
        "used_end": f"0x{code_base + len(image):08X}",
        "used_bytes": len(image),
        "fragment_count": len(fragments),
        "import_count": len(canonical_imports),
        "build_id": f"0x{build_id:08X}",
        "pnach": output_path.relative_to(LAB_ROOT).as_posix(),
        "pnach_sha256": sha256(output_path.read_bytes()),
    }
    manifest_path = LAB_ROOT / "build" / "production-adapter.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"Linked {len(fragments)} fragments and {len(canonical_imports)} "
        f"Current imports into 0x{code_base:08X}-0x{code_base + len(image):08X}"
    )
    print(f"Production entry {entry_symbol} -> 0x{entry_address:08X}")
    print(f"PNACH generated at {output_path}")
    print(f"Manifest generated at {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
