#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import tempfile
from dataclasses import replace
from pathlib import Path


SCRIPT_ROOT = Path(__file__).resolve().parent
REPOSITORY = SCRIPT_ROOT.parents[1]
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
from na228_builder.image_assembler.iso9660 import Iso9660
from na228_builder.project_paths import load_project_paths


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
HOT_RELOAD_SOURCE = "hot_reload_message"
HOT_RELOAD_ENTRY = "project.hot_reload_message"
FIXED_EXTERNAL_ADDRESSES: dict[str, int] = {}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compile and link a runtime-injector C fragment."
    )
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--entry", required=True)
    parser.add_argument("--overlay-plan")
    parser.add_argument(
        "--whole-source",
        action="store_true",
        help="Link every declared fragment from the selected C source.",
    )
    parser.add_argument(
        "--hot-reload-label",
        help="Compile the development marker with this display text.",
    )
    parser.add_argument(
        "--iso",
        type=Path,
        default=load_project_paths(REPOSITORY).file("latest_iso"),
    )
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


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
) -> tuple[
    Path | None,
    dict[str, object] | None,
    list[dict[str, str]],
    list[dict[str, object]],
    dict[str, int],
]:
    if value is None:
        return None, None, [], [], {}
    plan_path = Path(value)
    if not plan_path.is_absolute():
        plan_path = REPOSITORY / plan_path
    plan_path = plan_path.resolve()
    allowed_roots = (
        ((REPOSITORY / "work").resolve(), 2, False),
        ((SCRIPT_ROOT / "targets").resolve(), 1, True),
    )
    allowed = False
    maintained_target = False
    for root, minimum_parts, root_is_maintained in allowed_roots:
        try:
            relative = plan_path.relative_to(root)
        except ValueError:
            continue
        if len(relative.parts) >= minimum_parts:
            allowed = True
            maintained_target = root_is_maintained
            break
    if not allowed or not plan_path.is_file():
        raise ValueError(
            "Overlay plan must be task-owned under work/<task>/ or a "
            "maintained target under scripts/injection/targets/"
        )
    raw = json.loads(plan_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Overlay plan root must be a JSON object")
    version = raw.get("schema_version")
    expected_fields = (
        {
            "schema_version",
            "source_id",
            "entry_symbol",
            "abi",
            "purpose",
            "writes",
        }
        if version == 1
        else {
            "schema_version",
            "source_id",
            "entry_symbols",
            "purpose",
            "writes",
        }
    )
    optional_fields = {"resident_symbol_overrides"}
    actual_fields = set(raw)
    if not expected_fields.issubset(actual_fields) or (
        actual_fields - expected_fields - optional_fields
    ):
        raise ValueError(
            "Overlay plan fields differ: "
            f"missing={sorted(expected_fields - actual_fields)}, "
            f"extra={sorted(actual_fields - expected_fields - optional_fields)}"
        )
    if version not in (1, 2):
        raise ValueError("Overlay plan schema_version must be 1 or 2")
    if raw["source_id"] != source_id:
        raise ValueError("Overlay plan source_id does not match selection")
    if not isinstance(raw["purpose"], str) or not raw["purpose"].strip():
        raise ValueError("Overlay plan purpose must be non-empty text")
    if not isinstance(raw["writes"], list) or (
        not raw["writes"] and not maintained_target
    ):
        raise ValueError(
            "Task-owned overlay plan writes must be a non-empty array"
        )

    resident_symbol_overrides: dict[str, int] = {}
    raw_overrides = raw.get("resident_symbol_overrides", {})
    if not isinstance(raw_overrides, dict):
        raise ValueError("resident_symbol_overrides must be an object")
    for raw_symbol, raw_address in raw_overrides.items():
        symbol = identifier(
            str(raw_symbol), "resident_symbol_overrides symbol"
        )
        address = integer(
            str(raw_address),
            f"resident_symbol_overrides {symbol} runtime_address",
        )
        if address % 4 or address < 0 or address >= 0x02000000:
            raise ValueError(
                f"resident_symbol_overrides {symbol}: runtime_address must "
                "be aligned EE memory"
            )
        resident_symbol_overrides[symbol] = address

    if version == 1:
        selected_symbol = identifier(
            str(raw["entry_symbol"]), "overlay plan entry_symbol"
        )
        if selected_symbol != entry_symbol:
            raise ValueError("Overlay plan entry_symbol does not match selection")
        entries = [
            {
                "symbol": selected_symbol,
                "abi": identifier(str(raw["abi"]), "overlay plan abi"),
                "purpose": str(raw["purpose"]).strip(),
            }
        ]
    else:
        raw_entries = raw["entry_symbols"]
        if not isinstance(raw_entries, list) or not raw_entries:
            raise ValueError(
                "Overlay plan entry_symbols must be a non-empty array"
            )
        entries: list[dict[str, str]] = []
        seen_symbols: set[str] = set()
        for index, item in enumerate(raw_entries, 1):
            label = f"overlay plan entry_symbols[{index}]"
            if not isinstance(item, dict) or set(item) != {"symbol", "abi"}:
                raise ValueError(
                    f"{label}: expected only symbol and abi"
                )
            symbol = identifier(str(item["symbol"]), f"{label} symbol")
            if symbol in seen_symbols:
                raise ValueError(f"{label}: duplicate symbol {symbol!r}")
            seen_symbols.add(symbol)
            entries.append(
                {
                    "symbol": symbol,
                    "abi": identifier(str(item["abi"]), f"{label} abi"),
                    "purpose": str(raw["purpose"]).strip(),
                }
            )
        if entries[0]["symbol"] != entry_symbol:
            raise ValueError(
                "Overlay plan first entry_symbols item does not match selection"
            )

    selected_symbols = {entry["symbol"] for entry in entries}
    unresolved: list[dict[str, object]] = []
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
            replacement_kind = "entry_call"
            replacement_symbol = None
            replacement = bytes(8)
        elif kind == "symbol_call":
            if set(replacement_spec) != {"kind", "symbol"} or len(expected) != 8:
                raise ValueError(
                    f"{label}: symbol_call requires symbol and exactly eight "
                    "expected bytes"
                )
            replacement_symbol = identifier(
                str(replacement_spec["symbol"]), f"{label} replacement symbol"
            )
            if replacement_symbol not in selected_symbols:
                raise ValueError(
                    f"{label}: symbol_call target {replacement_symbol!r} is "
                    "not selected by entry_symbols"
                )
            replacement_kind = "symbol_call"
            replacement = bytes(8)
        elif kind == "bytes":
            if set(replacement_spec) != {"kind", "hex"}:
                raise ValueError(
                    f"{label}: bytes replacement requires only kind and hex"
                )
            replacement = hex_bytes(
                str(replacement_spec["hex"]), f"{label} replacement hex"
            )
            replacement_kind = "bytes"
            replacement_symbol = None
        else:
            raise ValueError(
                f"{label}: replacement kind must be entry_call, symbol_call, "
                "or bytes"
            )
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
        unresolved.append(
            {
                "id": write_id,
                "runtime_address": f"0x{address:08X}",
                "expected_hex": expected.hex().upper(),
                "replacement_hex": replacement.hex().upper(),
                "replacement_kind": replacement_kind,
                "replacement_symbol": replacement_symbol,
                "reason": item["reason"].strip(),
            }
        )
    return (
        plan_path,
        raw,
        entries,
        unresolved,
        resident_symbol_overrides,
    )


def resolve_overlay_writes(
    writes: list[dict[str, object]],
    *,
    entry_addresses: dict[str, int],
    primary_entry: int,
) -> list[dict[str, object]]:
    resolved: list[dict[str, object]] = []
    for row in writes:
        kind = str(row["replacement_kind"])
        if kind == "entry_call":
            replacement = encode_symbol_reference("jal26", primary_entry) + bytes(4)
        elif kind == "symbol_call":
            symbol = str(row["replacement_symbol"])
            replacement = (
                encode_symbol_reference("jal26", entry_addresses[symbol]) + bytes(4)
            )
        else:
            replacement = bytes.fromhex(str(row["replacement_hex"]))
        resolved.append(
            {
                "id": row["id"],
                "runtime_address": row["runtime_address"],
                "expected_hex": row["expected_hex"],
                "replacement_hex": replacement.hex().upper(),
                "reason": row["reason"],
            }
        )
    return resolved


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def align(value: int, alignment: int) -> int:
    return (value + alignment - 1) & -alignment


def locate_build_record(
    payload_sha256: str,
    *,
    required: bool = True,
) -> tuple[Path, dict[str, object]] | None:
    matches: list[tuple[Path, dict[str, object]]] = []
    builds_root = REPOSITORY / "logs" / "na228" / "builds"
    for summary_path in builds_root.glob("*/payload_builder/payload_summary.json"):
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        if str(summary.get("sha256", "")).upper() == payload_sha256:
            matches.append((summary_path.parents[1], summary))
    if not matches:
        if not required:
            return None
        raise ValueError(
            "No retained NA2 build record matches the exact Latest 228.BIN "
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
                f"symbol_map.tsv:{line}: {symbol} exceeds exact Latest 228.BIN"
            )
        actual_sha = sha256(payload[offset : offset + size])
        expected_sha = row["sha256"].upper()
        if actual_sha != expected_sha:
            raise ValueError(
                f"symbol_map.tsv:{line}: exact Latest bytes do not match {symbol}"
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
    if source_id == HOT_RELOAD_SOURCE:
        return (
            REPOSITORY / "src" / "hot_reload_message.c",
            "project.hot_reload",
            {},
            [
                (1, "project.hot_reload.text", HOT_RELOAD_ENTRY),
                (2, "project.hot_reload.rodata", "project.hot_reload.rodata"),
                (3, "project.hot_reload.bss", "project.hot_reload.bss"),
            ],
        )

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
    relative_source = Path(row["path"].replace("\\", "/"))
    if relative_source.is_absolute() or ".." in relative_source.parts:
        raise ValueError(f"Production source path is invalid: {row['path']}")
    if relative_source.parts and relative_source.parts[0] == "src":
        source_path = (REPOSITORY / relative_source).resolve()
        allowed_root = (REPOSITORY / "src").resolve()
    else:
        source_path = (package_root / relative_source).resolve()
        allowed_root = package_root.resolve()
    if allowed_root not in source_path.parents or not source_path.is_file():
        raise ValueError(f"Production source was not found: {source_path}")
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


def load_declared_entry(
    source_id: str,
    entry_symbol: str,
) -> dict[str, str]:
    if source_id == HOT_RELOAD_SOURCE and entry_symbol == HOT_RELOAD_ENTRY:
        return {
            "symbol": HOT_RELOAD_ENTRY,
            "abi": "void",
            "purpose": "Project C hot-reload smoke entry.",
        }

    entries = read_tsv(PACKAGE_ROOT / "entries.tsv", ENTRY_FIELDS)
    selected = [
        row
        for row in entries
        if row["source_id"] == source_id and row["entry_symbol"] == entry_symbol
    ]
    if len(selected) != 1:
        raise ValueError(
            "The selected production source/entry is not an explicitly "
            "declared runtime-injector ABI boundary"
        )
    entry = selected[0]
    identifier(entry["abi"], "entries.tsv abi")
    if not entry["purpose"]:
        raise ValueError("entries.tsv purpose must not be empty")
    return {
        "symbol": entry["entry_symbol"],
        "abi": entry["abi"],
        "purpose": entry["purpose"],
    }


def load_declared_entries(source_id: str) -> list[dict[str, str]]:
    entries = read_tsv(PACKAGE_ROOT / "entries.tsv", ENTRY_FIELDS)
    result = []
    for entry in entries:
        if entry["source_id"] != source_id:
            continue
        identifier(entry["entry_symbol"], "entries.tsv entry_symbol")
        identifier(entry["abi"], "entries.tsv abi")
        if not entry["purpose"]:
            raise ValueError("entries.tsv purpose must not be empty")
        result.append(
            {
                "symbol": entry["entry_symbol"],
                "abi": entry["abi"],
                "purpose": entry["purpose"],
            }
        )
    if not result:
        raise ValueError(
            f"Production source {source_id!r} has no declared entries"
        )
    return result


def compile_fragments(
    source_id: str,
    source_path: Path,
    namespace: str,
    imports: dict[str, ee_c_fragments.SymbolReference],
    mappings: list[tuple[int, str, str]],
    object_path: Path,
    hot_reload_label: str | None = None,
) -> list[PayloadFragment]:
    object_path.parent.mkdir(parents=True, exist_ok=True)
    defines = None
    if hot_reload_label is not None and source_id == HOT_RELOAD_SOURCE:
        defines = {"HOT_RELOAD_LABEL": json.dumps(hot_reload_label)}
    extracted = ee_c_fragments.compile_and_extract(
        source_path,
        object_path,
        namespace=namespace,
        toolchain_bin=ee_c_fragments.default_toolchain_bin(REPOSITORY),
        owner="localization.runtime_injector",
        defines=defines,
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
    entry_symbols: list[str],
    c_fragments: list[PayloadFragment],
    mappings: list[tuple[int, str, str]],
    symbol_map: dict[str, dict[str, object]],
    current_payload: bytes,
    resident_symbol_overrides: dict[str, int],
    forced_symbols: set[str] | None = None,
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
    for entry_symbol in entry_symbols:
        if entry_symbol not in catalog:
            raise ValueError(
                f"Entry {entry_symbol!r} is not a canonical runtime-injector fragment"
            )

    root_symbols = set(entry_symbols)
    root_symbols.update(forced_symbols or ())
    selected: set[str] = set()
    external_symbols: set[str] = set()
    current_match_cache: dict[str, bool] = {}

    def matches_current(symbol: str, active: set[str] | None = None) -> bool:
        if symbol in root_symbols:
            return False
        if symbol in resident_symbol_overrides:
            return True
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

    for root_symbol in sorted(root_symbols):
        if root_symbol not in catalog:
            raise ValueError(
                f"Selected root {root_symbol!r} is not a canonical "
                "runtime-injector fragment"
            )
        visit(root_symbol)
    ordered = sorted(
        (catalog[symbol] for symbol in selected),
        key=lambda item: (item[0], item[1], item[2].symbol),
    )
    return [item[2] for item in ordered], external_symbols


def link_fragment(
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
            "Production C closure exceeds the development reservation: "
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


def resolve_external_addresses(
    external_symbols: set[str],
    symbol_map: dict[str, dict[str, object]],
    resident_symbol_overrides: dict[str, int],
) -> dict[str, int]:
    unused_overrides = set(resident_symbol_overrides) - external_symbols
    if unused_overrides:
        raise ValueError(
            "Resident symbol overrides are not selected imports: "
            + ", ".join(sorted(unused_overrides))
        )

    result: dict[str, int] = {}
    for symbol in external_symbols:
        if symbol in resident_symbol_overrides:
            result[symbol] = resident_symbol_overrides[symbol]
            continue
        if symbol in FIXED_EXTERNAL_ADDRESSES:
            result[symbol] = FIXED_EXTERNAL_ADDRESSES[symbol]
            continue
        row = symbol_map.get(symbol)
        if row is None:
            raise ValueError(
                f"Exact Latest symbol map does not resolve import {symbol!r}"
            )
        result[symbol] = int(row["address"])
    return result


def resolved_path(value: Path) -> Path:
    return value.resolve() if value.is_absolute() else (REPOSITORY / value).resolve()


def main() -> int:
    args = parse_args()
    source_id = identifier(args.source_id, "source-id")
    entry_symbol = identifier(args.entry, "entry")
    iso_path = resolved_path(args.iso)
    output = resolved_path(
        args.output or Path("build") / "injection" / source_id
    )
    code_base = 0x008F0000
    code_end = 0x008F3D00

    (
        overlay_plan_path,
        overlay_plan,
        overlay_entries,
        unresolved_overlay_writes,
        resident_symbol_overrides,
    ) = load_overlay_plan(
        args.overlay_plan,
        source_id=source_id,
        entry_symbol=entry_symbol,
    )

    iso = Iso9660(iso_path)
    try:
        payload_record = iso.by_path["PRG/228.BIN"]
    except KeyError as exc:
        raise ValueError(f"{iso_path}: PRG/228.BIN was not found") from exc
    payload = iso.read_file(payload_record)
    payload_sha256 = sha256(payload)
    record_match = locate_build_record(
        payload_sha256,
        required=not resident_symbol_overrides,
    )
    if record_match is None:
        build_record = None
        symbol_map: dict[str, dict[str, object]] = {}
    else:
        build_record, payload_summary = record_match
        symbol_map = load_symbol_map(build_record, payload)
        if str(payload_summary.get("load_base", "")).lower() != "0x8f3d00":
            raise ValueError(
                "Matching build record has an unexpected 228.BIN load base"
            )

    source_path, namespace, imports, mappings = load_source(source_id)
    entry_declarations = (
        overlay_entries
        if overlay_plan is not None
        else [load_declared_entry(source_id, entry_symbol)]
    )
    if args.whole_source:
        declared = load_declared_entries(source_id)
        by_symbol = {
            declaration["symbol"]: declaration
            for declaration in entry_declarations
        }
        for declaration in declared:
            by_symbol.setdefault(declaration["symbol"], declaration)
        entry_declarations = [
            by_symbol[entry_symbol],
            *(
                declaration
                for symbol, declaration in by_symbol.items()
                if symbol != entry_symbol
            ),
        ]
    entry_symbols = [entry["symbol"] for entry in entry_declarations]

    include_marker = (
        source_id == HOT_RELOAD_SOURCE or args.hot_reload_label is not None
    )
    root_symbols = list(entry_symbols)
    with tempfile.TemporaryDirectory(prefix="na228-injection-") as temporary:
        temporary_path = Path(temporary)
        compiled_c_fragments = compile_fragments(
            source_id,
            source_path,
            namespace,
            imports,
            mappings,
            temporary_path / f"{source_id}.o",
            args.hot_reload_label,
        )
        if source_id != HOT_RELOAD_SOURCE and include_marker:
            (
                marker_source_path,
                marker_namespace,
                marker_imports,
                marker_mappings,
            ) = load_source(HOT_RELOAD_SOURCE)
            compiled_c_fragments.extend(
                compile_fragments(
                    HOT_RELOAD_SOURCE,
                    marker_source_path,
                    marker_namespace,
                    marker_imports,
                    marker_mappings,
                    temporary_path / f"{HOT_RELOAD_SOURCE}.o",
                    args.hot_reload_label,
                )
            )
            marker_order_base = max(
                (order for order, _object, _fragment in mappings),
                default=0,
            )
            mappings.extend(
                (
                    marker_order_base + order,
                    object_fragment,
                    fragment_id,
                )
                for order, object_fragment, fragment_id in marker_mappings
            )
            root_symbols.append(HOT_RELOAD_ENTRY)
    fragments, external_symbols = select_fragment_closure(
        root_symbols,
        compiled_c_fragments,
        mappings,
        symbol_map,
        payload,
        resident_symbol_overrides,
        forced_symbols=(
            {fragment.symbol for fragment in compiled_c_fragments}
            if args.whole_source
            else None
        ),
    )
    by_symbol = {fragment.symbol: fragment for fragment in fragments}
    for selected_entry in root_symbols:
        if by_symbol[selected_entry].kind != "code":
            raise ValueError(f"Entry {selected_entry!r} is not executable code")

    external_addresses = resolve_external_addresses(
        external_symbols,
        symbol_map,
        resident_symbol_overrides,
    )

    fragment, addresses = link_fragment(
        fragments,
        code_base=code_base,
        code_end=code_end,
        external_addresses=external_addresses,
    )
    overlay_writes = resolve_overlay_writes(
        unresolved_overlay_writes,
        entry_addresses=addresses,
        primary_entry=addresses[entry_symbol],
    )

    writes = list(overlay_writes)
    if args.whole_source:
        occupied_addresses = {
            int(write["runtime_address"], 0)
            for write in writes
        }
        for declaration in entry_declarations:
            selected_entry = declaration["symbol"]
            resident_entry = symbol_map.get(selected_entry)
            if resident_entry is None:
                continue
            resident_address = int(resident_entry["address"])
            if resident_address in occupied_addresses:
                continue
            if int(resident_entry["size"]) < 8:
                raise ValueError(
                    f"Production entry {selected_entry!r} is smaller than 8 bytes"
                )
            resident_offset = int(resident_entry["offset"])
            expected = payload[resident_offset : resident_offset + 8]
            writes.append(
                {
                    "id": (
                        "resident_entry_redirect_"
                        + re.sub(r"[^A-Za-z0-9_.-]", "_", selected_entry)
                    ),
                    "runtime_address": f"0x{resident_address:08X}",
                    "expected_hex": expected.hex().upper(),
                    "replacement_hex": (
                        encode_symbol_reference("j26", addresses[selected_entry])
                        + bytes(4)
                    ).hex().upper(),
                    "reason": (
                        "Redirect the Latest resident entry to the whole-source "
                        "development fragment."
                    ),
                }
            )
            occupied_addresses.add(resident_address)
    elif overlay_plan is None and source_id != HOT_RELOAD_SOURCE:
        resident_entry = symbol_map.get(entry_symbol)
        if resident_entry is None:
            raise ValueError(
                f"Exact Latest symbol map does not contain entry {entry_symbol!r}; "
                "a task-owned overlay plan is required to bootstrap a new entry"
            )
        if int(resident_entry["size"]) < 8:
            raise ValueError(
                f"Production entry {entry_symbol!r} is smaller than 8 bytes"
            )
        resident_offset = int(resident_entry["offset"])
        expected = payload[resident_offset : resident_offset + 8]
        replacement = (
            encode_symbol_reference("j26", addresses[entry_symbol]) + bytes(4)
        )
        writes.append(
            {
                "id": "resident_entry_redirect",
                "runtime_address": (
                    f"0x{int(resident_entry['address']):08X}"
                ),
                "expected_hex": expected.hex().upper(),
                "replacement_hex": replacement.hex().upper(),
                "reason": "Redirect the Latest resident entry to the fragment.",
            }
        )
    if include_marker:
        writes.append(
            {
                "id": "hot_reload_visible_marker_call",
                "runtime_address": "0x001085A0",
                "expected_hex": "A021040C00000000",
                "replacement_hex": (
                    encode_symbol_reference(
                        "jal26", addresses[HOT_RELOAD_ENTRY]
                    )
                    + bytes(4)
                ).hex().upper(),
                "reason": (
                    "Replace an existing no-op end-of-frame call with the "
                    "visible hot-reload marker before renderer flush."
                ),
            }
        )

    output.mkdir(parents=True, exist_ok=True)
    fragment_path = output / "fragment.bin"
    manifest_path = output / "manifest.json"
    fragment_path.write_bytes(fragment)
    manifest = {
        "schema_version": 1,
        "source_id": source_id,
        "whole_source": args.whole_source,
        "entry_symbols": [
            {
                "symbol": selected_entry,
                "abi": declaration["abi"],
                "purpose": declaration["purpose"],
                "runtime_address": f"0x{addresses[selected_entry]:08X}",
            }
            for selected_entry, declaration in zip(
                entry_symbols, entry_declarations, strict=True
            )
        ],
        "fragment_file": "fragment.bin",
        "fragment_sha256": sha256(fragment),
        "segments": [
            {
                "file_offset": 0,
                "runtime_address": f"0x{code_base:08X}",
                "size": len(fragment),
            }
        ],
        "zero_fill": [],
        "writes": writes,
        "used_end": f"0x{code_base + len(fragment):08X}",
        "selected_fragments": [item.symbol for item in fragments],
        "resident_imports": sorted(
            external_symbols - FIXED_EXTERNAL_ADDRESSES.keys()
        ),
        "resident_symbol_overrides": {
            symbol: f"0x{address:08X}"
            for symbol, address in sorted(resident_symbol_overrides.items())
        },
        "resolved_imports": {
            symbol: f"0x{address:08X}"
            for symbol, address in sorted(external_addresses.items())
        },
        "fixed_imports": {
            symbol: f"0x{FIXED_EXTERNAL_ADDRESSES[symbol]:08X}"
            for symbol in sorted(
                external_symbols & FIXED_EXTERNAL_ADDRESSES.keys()
            )
        },
        "payload_sha256": payload_sha256,
        "build_record": (
            build_record.relative_to(REPOSITORY).as_posix()
            if build_record is not None
            else None
        ),
        "overlay_plan": (
            overlay_plan_path.relative_to(REPOSITORY).as_posix()
            if overlay_plan_path is not None
            else None
        ),
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"Linked {len(fragments)} fragments, "
        f"{len(external_symbols - FIXED_EXTERNAL_ADDRESSES.keys())} "
        f"resident imports, and "
        f"{len(external_symbols & FIXED_EXTERNAL_ADDRESSES.keys())} "
        f"fixed imports into "
        f"0x{code_base:08X}-0x{code_base + len(fragment):08X}"
    )
    if build_record is None:
        print(
            "Resident imports resolved from verified overlay-plan overrides; "
            "the exact ISO payload has no retained shared build record."
        )
    for selected_entry in entry_symbols:
        print(
            f"Production entry {selected_entry} -> "
            f"0x{addresses[selected_entry]:08X}"
        )
    print(f"Fragment: {fragment_path}")
    print(f"Manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
