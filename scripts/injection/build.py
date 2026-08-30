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
sys.path.insert(0, str(REPOSITORY))

from na228_builder.scripts import catalog as catalog_module
from na228_builder.payload_builder import ee_c_fragments
from na228_builder.payload_builder.operations import (
    PayloadFragment,
    PayloadRelocation,
    encode_symbol_reference,
)
from na228_builder.image_assembler.iso9660 import Iso9660
from scripts.lib.paths import load_paths


PATHS = load_paths(REPOSITORY)
CATALOG_PATH = PATHS.path("builder", "catalog.modcat")
CONFIGURATION_PATH = PATHS.path("builder", "configurations", "base.jsonc")

SYMBOL_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*\Z")
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
CATALOG_SELECTION = catalog_module.load_selection(
    CATALOG_PATH,
    CONFIGURATION_PATH,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compile and link runtime-injector EE source fragments."
    )
    parser.add_argument("--source-id")
    parser.add_argument("--entry")
    parser.add_argument(
        "--source-path",
        type=Path,
        help="Compile every registered EE C/assembly source selected by this file or folder.",
    )
    parser.add_argument("--overlay-plan")
    parser.add_argument(
        "--hot-reload-label",
        help="Compile the development marker with this display text.",
    )
    parser.add_argument(
        "--iso",
        type=Path,
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
    work_root = PATHS.path("work").resolve()
    try:
        relative = plan_path.relative_to(work_root)
    except ValueError:
        relative = Path()
    if len(relative.parts) < 2 or not plan_path.is_file():
        raise ValueError("Overlay plan must be task-owned under work/<task>/")
    raw = json.loads(plan_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Overlay plan root must be a JSON object")
    expected_fields = {
        "source_id",
        "entry_symbols",
        "purpose",
        "writes",
    }
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
    if raw["source_id"] != source_id:
        raise ValueError("Overlay plan source_id does not match selection")
    if not isinstance(raw["purpose"], str) or not raw["purpose"].strip():
        raise ValueError("Overlay plan purpose must be non-empty text")
    if not isinstance(raw["writes"], list) or not raw["writes"]:
        raise ValueError("Task-owned overlay plan writes must be a non-empty array")

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


def newest_cached_iso(configuration: str = "base") -> Path:
    registry_path = PATHS.path("logs", "na228", "preflight", "registry.json")
    if not registry_path.is_file():
        raise ValueError(f"No cached {configuration} build exists")
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    entries = registry.get("entries")
    images = registry.get("images")
    if not isinstance(entries, dict) or not isinstance(images, dict):
        raise ValueError(f"Invalid build registry: {registry_path}")
    candidates = sorted(
        (
            entry
            for entry in entries.values()
            if isinstance(entry, dict)
            and entry.get("configuration") == configuration
        ),
        key=lambda entry: str(entry.get("verified_utc", "")),
        reverse=True,
    )
    for entry in candidates:
        image = images.get(entry.get("sha256"))
        if not isinstance(image, dict) or not isinstance(image.get("path"), str):
            continue
        path = (REPOSITORY / image["path"]).resolve()
        if path.is_file():
            return path
    raise ValueError(f"No cached {configuration} build exists")


def align(value: int, alignment: int) -> int:
    return (value + alignment - 1) & -alignment


def locate_build_record(
    payload_sha256: str,
    *,
    required: bool = True,
) -> tuple[Path, dict[str, object]] | None:
    matches: list[tuple[Path, dict[str, object]]] = []
    builds_root = PATHS.path("logs", "na228", "preflight", "records")
    for summary_path in builds_root.glob("*/payload_builder/payload_summary.json"):
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        if str(summary.get("sha256", "")).upper() == payload_sha256:
            matches.append((summary_path.parents[1], summary))
    if not matches:
        if not required:
            return None
        raise ValueError(
            "No retained NA2 build record matches the cached 228.BIN "
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
                f"symbol_map.tsv:{line}: {symbol} exceeds the cached 228.BIN"
            )
        actual_sha = sha256(payload[offset : offset + size])
        expected_sha = row["sha256"].upper()
        if actual_sha != expected_sha:
            raise ValueError(
                f"symbol_map.tsv:{line}: cached bytes do not match {symbol}"
            )
        result[symbol] = {
            "offset": offset,
            "address": address,
            "size": size,
            "kind": row["kind"],
            "sha256": actual_sha,
        }
    return result


def configured_payload() -> dict[str, tuple[object, str, dict[str, object]]]:
    result: dict[str, tuple[object, str, dict[str, object]]] = {}
    for feature_id in CATALOG_SELECTION.feature_ids:
        for node, injection_id, payload_id, value in catalog_module.payload_entries(
            CATALOG_SELECTION,
            feature_id,
        ):
            if payload_id in result:
                raise ValueError(f"Duplicate configured payload ID: {payload_id}")
            result[payload_id] = (node, injection_id, value)
    return result


def production_sources() -> dict[str, dict[str, object]]:
    return {
        payload_id: value
        for payload_id, (_node, _injection_id, value) in configured_payload().items()
        if value.get("kind") in {"c", "asm"}
    }


def production_source_owner(source_id: str) -> str:
    selected = configured_payload().get(source_id)
    if selected is None or selected[2].get("kind") not in {"c", "asm"}:
        raise ValueError(f"Unknown production EE source: {source_id!r}")
    node = selected[0]
    return f"{node.feature_id}.runtime_injector"


def fragment_declaration_positions() -> dict[str, int]:
    positions: dict[str, int] = {}
    for payload_id, (_node, _injection_id, value) in configured_payload().items():
        if value.get("kind") in {"c", "asm"}:
            fragments = value.get("fragments")
            if not isinstance(fragments, dict):
                continue
            symbols = fragments
        else:
            symbols = (payload_id,)
        for symbol in symbols:
            if symbol in positions:
                raise ValueError(f"Duplicate configured fragment: {symbol}")
            positions[symbol] = len(positions)
    return positions


def _load_static_fragments() -> list[PayloadFragment]:
    result: list[PayloadFragment] = []
    for payload_id, (node, injection_id, value) in configured_payload().items():
        if value.get("kind") == "c":
            continue
        if value.get("kind") == "asm":
            compiled = catalog_module._compile_source(
                REPOSITORY,
                f"{node.feature_id}.runtime_injector",
                payload_id,
                value,
                f"injections.{injection_id}.payload.{payload_id}",
            )
            result.extend(compiled)
            continue
        result.append(
            catalog_module.load_static_fragment(
                REPOSITORY,
                f"{node.feature_id}.runtime_injector",
                payload_id,
                value,
                f"injections.{injection_id}.payload.{payload_id}",
            )
        )
    return result


def load_source(
    source_id: str,
) -> tuple[
    Path,
    str,
    str,
    dict[str, ee_c_fragments.SymbolReference],
    list[tuple[str, str]],
]:
    if source_id == HOT_RELOAD_SOURCE:
        return (
            REPOSITORY / "src" / "hot_reload_message.c",
            "c",
            "project.hot_reload",
            {},
            [
                ("project.hot_reload.text", HOT_RELOAD_ENTRY),
                ("project.hot_reload.rodata", "project.hot_reload.rodata"),
                ("project.hot_reload.bss", "project.hot_reload.bss"),
            ],
        )

    row = production_sources().get(source_id)
    if row is None:
        raise ValueError(f"Unknown production EE source: {source_id!r}")
    source_value = row.get("path")
    if not isinstance(source_value, str):
        raise ValueError(f"Catalog EE source {source_id!r} has no path")
    relative_source = Path(source_value.replace("\\", "/"))
    if relative_source.is_absolute() or ".." in relative_source.parts:
        raise ValueError(f"Production source path is invalid: {source_value}")
    source_path = (REPOSITORY / relative_source).resolve()
    if REPOSITORY not in source_path.parents or not source_path.is_file():
        raise ValueError(f"Production source was not found: {source_path}")
    language_value = row.get("kind")
    if language_value not in {"c", "asm"}:
        raise ValueError(f"Catalog EE source {source_id!r} has invalid kind")
    language = str(language_value)
    ee_c_fragments.validate_source_language(source_path, language)
    namespace_value = row.get("namespace")
    if not isinstance(namespace_value, str):
        raise ValueError(f"Catalog EE source {source_id!r} has no namespace")
    namespace = identifier(namespace_value, "catalog namespace")

    imports: dict[str, ee_c_fragments.SymbolReference] = {}
    raw_imports = row.get("imports", {})
    if not isinstance(raw_imports, dict):
        raise ValueError(f"Catalog EE source {source_id!r} imports must be an object")
    for name, import_value in raw_imports.items():
        name = identifier(name, f"catalog source {source_id} import name")
        if name in imports:
            raise ValueError(f"Catalog source {source_id}: duplicate import {name}")
        if isinstance(import_value, str):
            symbol = import_value
            addend = 0
        elif isinstance(import_value, dict):
            symbol = import_value.get("symbol")
            addend_value = import_value.get("addend", 0)
            if isinstance(addend_value, bool) or not isinstance(addend_value, int):
                raise ValueError(f"Catalog source {source_id} import {name} addend is invalid")
            addend = addend_value
        else:
            raise ValueError(f"Catalog source {source_id} import {name} is invalid")
        if not isinstance(symbol, str):
            raise ValueError(f"Catalog source {source_id} import {name} has no symbol")
        imports[name] = ee_c_fragments.SymbolReference(
            symbol=identifier(symbol, f"catalog source {source_id} import symbol"),
            addend=addend,
        )

    mappings: list[tuple[str, str]] = []
    seen_objects: set[str] = set()
    seen_final: set[str] = set()
    raw_fragments = row.get("fragments")
    if not isinstance(raw_fragments, dict):
        raise ValueError(f"Catalog EE source {source_id!r} fragments must be an object")
    for fragment_id, fragment_row in raw_fragments.items():
        if not isinstance(fragment_row, dict):
            raise ValueError(f"Catalog source {source_id} fragment {fragment_id} is invalid")
        object_fragment = identifier(
            str(fragment_row.get("object", "")),
            f"catalog source {source_id} fragment object",
        )
        fragment_id = identifier(
            fragment_id, f"catalog source {source_id} fragment ID"
        )
        if object_fragment in seen_objects or fragment_id in seen_final:
            raise ValueError(
                f"Catalog source {source_id}: duplicate production fragment mapping"
            )
        seen_objects.add(object_fragment)
        seen_final.add(fragment_id)
        mappings.append((object_fragment, fragment_id))
    if not mappings:
        raise ValueError(f"Production EE source {source_id!r} has no fragments")
    return source_path, language, namespace, imports, mappings


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

    source = production_sources().get(source_id)
    payload = {
        key: value
        for key, (_node, _injection_id, value) in configured_payload().items()
    }
    fragment: object = None
    if source is not None and isinstance(source.get("fragments"), dict):
        fragment = source["fragments"].get(entry_symbol)
    if not isinstance(fragment, dict):
        fragment = next(
            (
                source_fragment
                for value in payload.values()
                if isinstance(value, dict)
                and isinstance(value.get("fragments"), dict)
                and isinstance(
                    source_fragment := value["fragments"].get(entry_symbol),
                    dict,
                )
                and source_fragment.get("source", source_id) == source_id
            ),
            payload.get(entry_symbol),
        )
    if not isinstance(fragment, dict):
        raise ValueError(
            "The selected production source/entry is not an explicitly "
            "declared catalog ABI boundary"
        )
    abi = fragment.get("abi")
    purpose = fragment.get("description")
    if not isinstance(abi, str):
        raise ValueError(f"Catalog entry {entry_symbol} has no ABI")
    identifier(abi, "catalog entry ABI")
    if not isinstance(purpose, str) or not purpose:
        raise ValueError(f"Catalog entry {entry_symbol} has no description")
    return {
        "symbol": entry_symbol,
        "abi": abi,
        "purpose": purpose,
    }


def compile_fragments(
    source_id: str,
    source_path: Path,
    source_language: str,
    namespace: str,
    imports: dict[str, ee_c_fragments.SymbolReference],
    mappings: list[tuple[str, str]],
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
        language=source_language,
        toolchain_bin=ee_c_fragments.default_toolchain_bin(REPOSITORY),
        owner=(
            "localization.runtime_injector"
            if source_id == HOT_RELOAD_SOURCE
            else production_source_owner(source_id)
        ),
        defines=defines,
        external_symbols=imports,
    )
    aliases = {
        object_fragment: fragment_id
        for object_fragment, fragment_id in mappings
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
    for object_fragment, fragment_id in mappings:
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
    mappings: list[tuple[str, str]],
    symbol_map: dict[str, dict[str, object]],
    current_payload: bytes,
    resident_symbol_overrides: dict[str, int],
    forced_symbols: set[str] | None = None,
) -> tuple[list[PayloadFragment], set[str]]:
    declaration_positions = fragment_declaration_positions()
    next_position = len(declaration_positions)
    mapping_positions: dict[str, int] = {}
    for _object_fragment, fragment_id in mappings:
        position = declaration_positions.get(fragment_id)
        if position is None:
            position = next_position
            next_position += 1
        mapping_positions[fragment_id] = position
    catalog: dict[str, tuple[int, PayloadFragment]] = {}
    for fragment in c_fragments:
        catalog[fragment.symbol] = (
            mapping_positions[fragment.symbol],
            fragment,
        )
    for fragment in _load_static_fragments():
        if fragment.symbol in catalog:
            if catalog[fragment.symbol][1] != fragment:
                raise ValueError(
                    f"Conflicting canonical fragment symbol {fragment.symbol!r}"
                )
            continue
        catalog[fragment.symbol] = (
            declaration_positions[fragment.symbol],
            fragment,
        )
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
        fragment = catalog[symbol][1]
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
        fragment = catalog[symbol][1]
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
        key=lambda item: (item[0], item[1].symbol),
    )
    return [item[1] for item in ordered], external_symbols


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
                f"Cached-build symbol map does not resolve import {symbol!r}"
            )
        result[symbol] = int(row["address"])
    return result


def resolved_path(value: Path) -> Path:
    return value.resolve() if value.is_absolute() else (REPOSITORY / value).resolve()


def source_ids_for_path(value: Path) -> tuple[Path, list[str]]:
    scope = resolved_path(value)
    source_root = (REPOSITORY / "src").resolve()
    try:
        scope.relative_to(source_root)
    except ValueError as exc:
        raise ValueError(f"Source scope must be inside {source_root}: {scope}") from exc
    if not scope.exists():
        raise ValueError(f"Source scope was not found: {scope}")
    if not scope.is_dir() and scope.suffix not in {".c", ".S"}:
        raise ValueError(f"Source scope must be an EE C/.S file or folder: {scope}")

    registered: list[tuple[str, Path]] = [
        (HOT_RELOAD_SOURCE, (source_root / "hot_reload_message.c").resolve())
    ]
    for source_id in production_sources():
        source_id = identifier(source_id, "catalog EE source ID")
        source_path, _language, _namespace, _imports, _mappings = load_source(source_id)
        registered.append((source_id, source_path.resolve()))

    selected = [
        source_id
        for source_id, source_path in registered
        if source_path == scope
        or (scope.is_dir() and source_path.is_relative_to(scope))
    ]
    if not selected:
        raise ValueError(f"Source scope contains no registered EE sources: {scope}")

    selected_paths = {
        source_path
        for source_id, source_path in registered
        if source_id in selected
    }
    discovered = (
        {
            path.resolve()
            for pattern in ("*.c", "*.S")
            for path in scope.rglob(pattern)
        }
        if scope.is_dir()
        else {scope}
    )
    unregistered = sorted(discovered - selected_paths)
    if unregistered:
        relative = [path.relative_to(REPOSITORY).as_posix() for path in unregistered]
        raise ValueError(
            "Source scope contains unregistered EE source files: "
            + ", ".join(relative)
        )
    return scope, selected


def main() -> int:
    args = parse_args()
    direct_scope = args.source_path is not None
    if direct_scope:
        if args.source_id or args.entry or args.overlay_plan:
            raise ValueError(
                "--source-path cannot be combined with --source-id, --entry, "
                "or --overlay-plan"
            )
        source_scope, source_ids = source_ids_for_path(args.source_path)
        source_id = source_ids[0]
        entry_symbol = ""
        output_name = (
            "all"
            if source_scope == (REPOSITORY / "src").resolve()
            else source_scope.stem
        )
    else:
        if not args.source_id or not args.entry:
            raise ValueError(
                "--source-id and --entry are required unless --source-path is used"
            )
        source_id = identifier(args.source_id, "source-id")
        source_ids = [source_id]
        entry_symbol = identifier(args.entry, "entry")
        output_name = source_id
    iso_path = resolved_path(args.iso) if args.iso is not None else newest_cached_iso()
    output = resolved_path(
        args.output or PATHS.path("build", "injection", output_name)
    )
    code_base = 0x008F0000
    code_end = 0x008F3D00

    if direct_scope:
        overlay_plan_path = None
        overlay_plan = None
        overlay_entries: list[dict[str, str]] = []
        unresolved_overlay_writes: list[dict[str, object]] = []
        resident_symbol_overrides: dict[str, int] = {}
    else:
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

    if direct_scope:
        entry_declarations: list[dict[str, str]] = []
    else:
        entry_declarations = (
            overlay_entries
            if overlay_plan is not None
            else [load_declared_entry(source_id, entry_symbol)]
        )
    entry_symbols = [entry["symbol"] for entry in entry_declarations]

    mappings: list[tuple[str, str]] = []
    compiled_c_fragments: list[PayloadFragment] = []
    with tempfile.TemporaryDirectory(prefix="na228-injection-") as temporary:
        temporary_path = Path(temporary)
        compiled_source_ids = list(source_ids)
        if HOT_RELOAD_SOURCE not in compiled_source_ids:
            compiled_source_ids.append(HOT_RELOAD_SOURCE)
        for selected_source_id in compiled_source_ids:
            (
                selected_source_path,
                source_language,
                namespace,
                imports,
                source_mappings,
            ) = load_source(selected_source_id)
            mappings.extend(source_mappings)
            compiled_c_fragments.extend(
                compile_fragments(
                    selected_source_id,
                    selected_source_path,
                    source_language,
                    namespace,
                    imports,
                    source_mappings,
                    temporary_path / f"{selected_source_id}.o",
                    args.hot_reload_label,
                )
            )
    if direct_scope:
        root_symbols = [
            fragment.symbol
            for fragment in compiled_c_fragments
            if fragment.kind == "code"
        ]
        declared_entries: dict[str, dict[str, str]] = {}
        for selected_source_id in source_ids:
            source = production_sources()[selected_source_id]
            fragments = source.get("fragments", {})
            if not isinstance(fragments, dict):
                continue
            for symbol, value in fragments.items():
                if not isinstance(value, dict):
                    continue
                abi = value.get("abi")
                purpose = value.get("description")
                if isinstance(abi, str) and isinstance(purpose, str):
                    declared_entries[symbol] = {
                        "symbol": symbol,
                        "abi": abi,
                        "purpose": purpose,
                    }
        entry_symbols = [
            symbol
            for symbol in root_symbols
            if symbol != HOT_RELOAD_ENTRY and symbol in symbol_map
        ]
        entry_declarations = [
            declared_entries.get(
                symbol,
                {
                    "symbol": symbol,
                    "abi": "resident_symbol",
                    "purpose": "Direct registered EE-source attachment.",
                },
            )
            for symbol in entry_symbols
        ]
    else:
        root_symbols = [*entry_symbols, HOT_RELOAD_ENTRY]
    fragments, external_symbols = select_fragment_closure(
        root_symbols,
        compiled_c_fragments,
        mappings,
        symbol_map,
        payload,
        resident_symbol_overrides,
        forced_symbols=(
            {fragment.symbol for fragment in compiled_c_fragments}
            if direct_scope
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
    overlay_writes = (
        []
        if direct_scope
        else resolve_overlay_writes(
            unresolved_overlay_writes,
            entry_addresses=addresses,
            primary_entry=addresses[entry_symbol],
        )
    )

    writes = list(overlay_writes)
    if direct_scope:
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
                        "Redirect the cached-build resident entry to the selected "
                        "development EE sources."
                    ),
                }
            )
            occupied_addresses.add(resident_address)
    elif overlay_plan is None and source_id != HOT_RELOAD_SOURCE:
        resident_entry = symbol_map.get(entry_symbol)
        if resident_entry is None:
            raise ValueError(
                f"Cached-build symbol map does not contain entry {entry_symbol!r}; "
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
                "reason": "Redirect the cached-build resident entry to the fragment.",
            }
        )
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
        "source_id": source_id,
        "source_ids": source_ids,
        "source_scope": (
            source_scope.relative_to(REPOSITORY).as_posix()
            if direct_scope
            else None
        ),
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
