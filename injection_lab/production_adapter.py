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
PACKAGE_ROOT = (
    REPOSITORY
    / "na228_builder"
    / "features"
    / "localization"
    / "runtime_injector"
)
sys.path.insert(0, str(REPOSITORY))

from na228_builder.payload_builder import ee_c_fragments
from na228_builder.payload_builder.operations import (
    PayloadFragment,
    PayloadRelocation,
    encode_symbol_reference,
)
from na228_builder.modules.runtime_injector.engine import _load_static_fragments


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
    parser.add_argument("--overlay-plan")
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


def hex_bytes(value: str, label: str) -> bytes:
    if not value or len(value) % 2 or not re.fullmatch(r"[0-9A-Fa-f]+", value):
        raise ValueError(f"{label}: expected non-empty even-length hexadecimal")
    return bytes.fromhex(value)


def load_overlay_plan(
    value: str | None,
    *,
    source_id: str,
    entry_symbol: str,
    dispatcher: int,
) -> tuple[Path | None, dict[str, object] | None, list[dict[str, object]]]:
    if value is None:
        return None, None, []
    plan_path = Path(value)
    if not plan_path.is_absolute():
        plan_path = REPOSITORY / plan_path
    plan_path = plan_path.resolve()
    work_root = (REPOSITORY / "work").resolve()
    try:
        relative = plan_path.relative_to(work_root)
    except ValueError as exc:
        raise ValueError("Overlay plan must be task-owned under work/<task>/") from exc
    if len(relative.parts) < 2 or not plan_path.is_file():
        raise ValueError("Overlay plan must be a file under work/<task>/")
    raw = json.loads(plan_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Overlay plan root must be a JSON object")
    expected_fields = {
        "schema_version",
        "source_id",
        "entry_symbol",
        "abi",
        "purpose",
        "writes",
    }
    if set(raw) != expected_fields:
        raise ValueError(
            "Overlay plan fields differ: "
            f"missing={sorted(expected_fields - set(raw))}, "
            f"extra={sorted(set(raw) - expected_fields)}"
        )
    if raw["schema_version"] != 1:
        raise ValueError("Overlay plan schema_version must be 1")
    if raw["source_id"] != source_id or raw["entry_symbol"] != entry_symbol:
        raise ValueError("Overlay plan source_id/entry_symbol does not match selection")
    identifier(str(raw["abi"]), "overlay plan abi")
    if not isinstance(raw["purpose"], str) or not raw["purpose"].strip():
        raise ValueError("Overlay plan purpose must be non-empty text")
    if not isinstance(raw["writes"], list) or not raw["writes"]:
        raise ValueError("Overlay plan writes must be a non-empty array")

    resolved: list[dict[str, object]] = []
    seen_ids: set[str] = set()
    occupied: list[tuple[int, int]] = []
    for index, item in enumerate(raw["writes"], 1):
        label = f"overlay plan writes[{index}]"
        if not isinstance(item, dict):
            raise ValueError(f"{label}: expected an object")
        required = {
            "id",
            "runtime_address",
            "expected_hex",
            "replacement",
            "reason",
        }
        if set(item) != required:
            raise ValueError(
                f"{label}: fields differ; missing={sorted(required - set(item))}, "
                f"extra={sorted(set(item) - required)}"
            )
        write_id = identifier(str(item["id"]), f"{label} id")
        if write_id in seen_ids:
            raise ValueError(f"{label}: duplicate id {write_id!r}")
        seen_ids.add(write_id)
        address = integer(str(item["runtime_address"]), f"{label} runtime_address")
        if address % 4 or address >= 0x02000000:
            raise ValueError(f"{label}: runtime_address must be aligned EE memory")
        expected = hex_bytes(str(item["expected_hex"]), f"{label} expected_hex")
        if len(expected) % 4:
            raise ValueError(f"{label}: expected bytes must contain whole EE words")
        replacement_spec = item["replacement"]
        if not isinstance(replacement_spec, dict):
            raise ValueError(f"{label}: replacement must be an object")
        kind = replacement_spec.get("kind")
        if kind == "entry_call":
            if set(replacement_spec) != {"kind"} or len(expected) != 8:
                raise ValueError(
                    f"{label}: entry_call requires exactly eight expected bytes"
                )
            replacement = (
                encode_symbol_reference("jal26", dispatcher)
                + bytes(4)
            )
        elif kind == "bytes":
            if set(replacement_spec) != {"kind", "hex"}:
                raise ValueError(
                    f"{label}: bytes replacement requires only kind and hex"
                )
            replacement = hex_bytes(
                str(replacement_spec["hex"]), f"{label} replacement hex"
            )
        else:
            raise ValueError(f"{label}: replacement kind must be entry_call or bytes")
        if len(replacement) != len(expected):
            raise ValueError(f"{label}: replacement length differs from expected")
        end = address + len(expected)
        if any(
            address < prior_end and prior_start < end
            for prior_start, prior_end in occupied
        ):
            raise ValueError(f"{label}: write overlaps another overlay write")
        occupied.append((address, end))
        if not isinstance(item["reason"], str) or not item["reason"].strip():
            raise ValueError(f"{label}: reason must be non-empty text")
        resolved.append(
            {
                "id": write_id,
                "runtime_address": f"0x{address:08X}",
                "expected_hex": expected.hex().upper(),
                "replacement_hex": replacement.hex().upper(),
                "reason": item["reason"].strip(),
            }
        )
    return plan_path, raw, resolved


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def align(value: int, alignment: int) -> int:
    return (value + alignment - 1) & -alignment


def locate_build_record(payload_sha256: str) -> tuple[Path, dict[str, object]]:
    matches: list[tuple[Path, dict[str, object]]] = []
    builds_root = REPOSITORY / "logs" / "na228" / "builds"
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
    package_root = PACKAGE_ROOT
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


def load_entry(
    source_id: str,
    entry_symbol: str,
    overlay_plan: dict[str, object] | None,
) -> dict[str, str]:
    if overlay_plan is not None:
        return {
            "source_id": source_id,
            "entry_symbol": entry_symbol,
            "abi": str(overlay_plan["abi"]),
            "purpose": str(overlay_plan["purpose"]).strip(),
        }
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


def select_fragment_closure(
    entry_symbol: str,
    c_fragments: list[PayloadFragment],
    mappings: list[tuple[int, str, str]],
    symbol_map: dict[str, dict[str, object]],
    current_payload: bytes,
) -> tuple[list[PayloadFragment], set[str]]:
    c_orders = {
        fragment_id: order
        for order, _object_fragment, fragment_id in mappings
    }
    catalog: dict[str, tuple[int, int, PayloadFragment]] = {}
    for fragment in c_fragments:
        catalog[fragment.symbol] = (c_orders[fragment.symbol], 1, fragment)
    for order, line, fragment in _load_static_fragments(
        PACKAGE_ROOT, "localization.runtime_injector"
    ):
        if fragment.symbol in catalog:
            raise ValueError(
                f"Duplicate canonical fragment symbol {fragment.symbol!r}"
            )
        catalog[fragment.symbol] = (order, line, fragment)
    if entry_symbol not in catalog:
        raise ValueError(
            f"Entry {entry_symbol!r} is not a canonical runtime-injector fragment"
        )

    selected: set[str] = set()
    external_symbols: set[str] = set()
    current_match_cache: dict[str, bool] = {}

    def matches_current(symbol: str, active: set[str] | None = None) -> bool:
        if symbol == entry_symbol:
            return False
        cached = current_match_cache.get(symbol)
        if cached is not None:
            return cached
        active = set() if active is None else active
        if symbol in active:
            return False
        active.add(symbol)
        fragment = catalog[symbol][2]
        row = symbol_map.get(fragment.symbol)
        if (
            row is None
            or row["kind"] != fragment.kind
            or int(row["size"]) != len(fragment.payload)
        ):
            active.remove(symbol)
            current_match_cache[symbol] = False
            return False
        resolved = bytearray(fragment.payload)
        for relocation in fragment.relocations:
            target_row = symbol_map.get(relocation.symbol)
            if target_row is None:
                active.remove(symbol)
                current_match_cache[symbol] = False
                return False
            replacement = encode_symbol_reference(
                relocation.kind,
                int(target_row["address"]) + relocation.addend,
            )
            end = relocation.offset + len(replacement)
            if relocation.offset < 0 or end > len(resolved):
                raise ValueError(
                    f"{fragment.symbol}: relocation exceeds its fragment"
                )
            resolved[relocation.offset:end] = replacement
        offset = int(row["offset"])
        matches = (
            bytes(resolved) == current_payload[offset : offset + len(resolved)]
            and all(
                relocation.symbol not in catalog
                or matches_current(relocation.symbol, active)
                for relocation in fragment.relocations
            )
        )
        active.remove(symbol)
        current_match_cache[symbol] = matches
        return matches

    def visit(symbol: str) -> None:
        if symbol in selected:
            return
        selected.add(symbol)
        fragment = catalog[symbol][2]
        for relocation in fragment.relocations:
            if relocation.symbol in catalog:
                if matches_current(relocation.symbol):
                    external_symbols.add(relocation.symbol)
                else:
                    visit(relocation.symbol)
            else:
                external_symbols.add(relocation.symbol)

    visit(entry_symbol)
    ordered = sorted(
        (catalog[symbol] for symbol in selected),
        key=lambda item: (item[0], item[1], item[2].symbol),
    )
    return [item[2] for item in ordered], external_symbols


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
    dispatcher = injection_base
    active_pointer = injection_base + 0x10
    overlay_plan_path, overlay_plan, overlay_writes = load_overlay_plan(
        args.overlay_plan,
        source_id=source_id,
        entry_symbol=entry_symbol,
        dispatcher=dispatcher,
    )

    payload_path = LAB_ROOT / "data" / "FILES" / "228.BIN"
    payload = payload_path.read_bytes()
    payload_sha256 = sha256(payload)
    build_record, payload_summary = locate_build_record(payload_sha256)
    symbol_map = load_symbol_map(build_record, payload)
    if str(payload_summary.get("load_base", "")).lower() != "0x8f3d00":
        raise ValueError("Matching build record has an unexpected 228.BIN load base")

    source_path, namespace, imports, mappings = load_source(source_id)
    entry_declaration = load_entry(source_id, entry_symbol, overlay_plan)
    compiled_c_fragments = compile_fragments(
        source_id, source_path, namespace, imports, mappings
    )
    fragments, external_symbols = select_fragment_closure(
        entry_symbol,
        compiled_c_fragments,
        mappings,
        symbol_map,
        payload,
    )
    entry_fragment = next(
        fragment for fragment in fragments if fragment.symbol == entry_symbol
    )
    if entry_fragment.kind != "code":
        raise ValueError(f"Entry {entry_symbol!r} is not executable code")

    external_addresses: dict[str, int] = {}
    for symbol in external_symbols:
        row = symbol_map.get(symbol)
        if row is None:
            raise ValueError(
                f"Exact Current symbol map does not resolve import {symbol!r}"
            )
        external_addresses[symbol] = int(row["address"])

    image, addresses = link_bank(
        fragments,
        code_base=code_base,
        code_end=code_end,
        external_addresses=external_addresses,
    )
    resident_entry = symbol_map.get(entry_symbol)
    resident_address: int | None = None
    expected_entry = b""
    if overlay_plan is None:
        if resident_entry is None:
            raise ValueError(
                f"Exact Current symbol map does not contain entry {entry_symbol!r}; "
                "a task-owned overlay plan is required to bootstrap a new entry"
            )
        if int(resident_entry["size"]) < 8:
            raise ValueError(
                f"Production entry {entry_symbol!r} is smaller than 8 bytes"
            )
        resident_address = int(resident_entry["address"])
        resident_offset = int(resident_entry["offset"])
        expected_entry = payload[resident_offset : resident_offset + 8]

    hi = (active_pointer + 0x8000) >> 16
    lo = active_pointer & 0xFFFF
    dispatcher_words = (
        0x3C190000 | hi,
        0x8F390000 | lo,
        0x03200008,
        0,
    )
    entry_address = addresses[entry_symbol]
    redirect_words = ()
    if resident_address is not None:
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
        (
            "// Entry redirect: task-owned guarded overlay plan"
            if overlay_plan is not None
            else "// Entry redirect: exact Current resident symbol"
        ),
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
    if resident_address is not None:
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
        "redirect_mode": "overlay" if overlay_plan is not None else "resident",
        "entry_resident_address": (
            f"0x{resident_address:08X}"
            if resident_address is not None
            else None
        ),
        "entry_resident_expected_hex": expected_entry.hex().upper(),
        "entry_bank_address": f"0x{entry_address:08X}",
        "dispatcher_address": f"0x{dispatcher:08X}",
        "active_pointer_address": f"0x{active_pointer:08X}",
        "code_base": f"0x{code_base:08X}",
        "code_end": f"0x{code_end:08X}",
        "used_end": f"0x{code_base + len(image):08X}",
        "used_bytes": len(image),
        "fragment_count": len(fragments),
        "bank_fragments": [fragment.symbol for fragment in fragments],
        "import_count": len(external_symbols),
        "current_imports": sorted(external_symbols),
        "overlay_plan": (
            overlay_plan_path.relative_to(REPOSITORY).as_posix()
            if overlay_plan_path is not None
            else None
        ),
        "overlay_plan_sha256": (
            sha256(overlay_plan_path.read_bytes())
            if overlay_plan_path is not None
            else None
        ),
        "overlay_writes": overlay_writes,
        "build_id": f"0x{build_id:08X}",
        "pnach": output_path.relative_to(LAB_ROOT).as_posix(),
        "pnach_sha256": sha256(output_path.read_bytes()),
    }
    manifest_path = LAB_ROOT / "build" / "production-adapter.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"Linked {len(fragments)} fragments and {len(external_symbols)} "
        f"Current imports into 0x{code_base:08X}-0x{code_base + len(image):08X}"
    )
    print(f"Production entry {entry_symbol} -> 0x{entry_address:08X}")
    if overlay_plan_path is not None:
        print(
            f"Resolved {len(overlay_writes)} guarded overlay writes from "
            f"{overlay_plan_path}"
        )
    print(f"PNACH generated at {output_path}")
    print(f"Manifest generated at {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
