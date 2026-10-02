"""Retail strings owned by mod strings: every build points the string's references at
the mod string in its own language, and the translation importer skips the mapping."""
from __future__ import annotations

import struct
from dataclasses import dataclass, replace
from pathlib import Path

from ...infrastructure.common import parse_int
from ...infrastructure.modules.binary_patcher import engine as binary_patcher
from ...infrastructure.modules.payload_builder.operations import SymbolicPatch
from ...infrastructure.modules.runtime_injector.engine import (
    RuntimeInjectionPackage,
    RuntimeSymbolicEdit,
)
from ...infrastructure.modules.translation_importer import engine as importer


MAPPINGS_PATH = Path(__file__).resolve().parent / "strings" / "mappings.tsv"
PATCH_ID = "localization.retail_strings"
TARGET_IDS = {"SLPS": "na2_elf", "BTL": "na2_btl", "ETC": "na2_etc"}


@dataclass(frozen=True)
class OwnedRetailString:
    mapping_id: str
    string_id: str
    target: str
    offset: int
    mode: str
    capacity: int
    source: str
    reference_refs: tuple[tuple[str, int], ...]


def mod_text_symbol(string_id: str) -> str:
    return "mod_text_" + string_id.replace(".", "__")


def owned_retail_strings() -> tuple[OwnedRetailString, ...]:
    owned = []
    for row in importer.read_rows(MAPPINGS_PATH):
        if not row["mod_string"]:
            continue
        label = f"mappings.tsv ({row['id']})"
        target, offset = importer.parse_source_ref(row["source_ref"], label)
        owned.append(OwnedRetailString(
            mapping_id=row["id"],
            string_id=row["mod_string"],
            target=target,
            offset=offset,
            mode=row["mode"].lower(),
            capacity=parse_int(row["capacity"], label),
            source=row["source"],
            reference_refs=importer.parse_reference_refs(row["reference_refs"], label),
        ))
    return tuple(owned)



def _references(entry: OwnedRetailString, clean: dict[str, bytes], address: int,
                label: str) -> tuple[tuple[str, int], ...]:
    """The declared pointer references, or every aligned pointer word to the string."""
    if entry.reference_refs:
        return entry.reference_refs
    word = struct.pack("<I", address)
    found = []
    for binary, data in clean.items():
        start = data.find(word)
        while start >= 0:
            if start % 4 == 0:
                found.append((binary, start))
            start = data.find(word, start + 1)
    if not found:
        raise ValueError(f"{label}: no pointer references the retail string; list them in reference_refs")
    return tuple(found)


def retail_string_package(
    declaration: RuntimeInjectionPackage,
    source_root: Path,
    targets_path: Path,
) -> RuntimeInjectionPackage:
    """Add guarded redirects from each owned retail string to its mod string."""
    owned = owned_retail_strings()
    if not owned:
        return declaration
    clean = importer.read_clean_targets(source_root)
    targets = binary_patcher.load_targets(targets_path)
    used_targets = dict(declaration.targets)
    edits = list(declaration.edits)
    order = max((edit.order for edit in edits), default=0)
    for entry in owned:
        label = f"{PATCH_ID} ({entry.mapping_id})"
        data = clean[entry.target]
        if entry.mode == "sequence":
            fragments, _ = importer.read_target_sequence(data, entry.offset, entry.capacity, label)
            actual = "<NUL>".join(fragments)
        else:
            actual, _ = importer.read_target_slot(data, entry.offset, entry.capacity, label)
        importer.validate_declared_source(entry.source, actual, label)
        address = importer.TARGET_RUNTIME_BASES[entry.target] + entry.offset
        expected = struct.pack("<I", address)
        for binary, offset in _references(entry, clean, address, label):
            if clean[binary][offset:offset + 4] != expected:
                raise ValueError(f"{label}: {binary} 0x{offset:X} does not point at the retail string")
            target_id = TARGET_IDS[binary]
            used_targets[target_id] = targets[target_id]
            order += 1
            edit_id = f"{PATCH_ID}.{entry.mapping_id}.{binary.lower()}_{offset:X}"
            edits.append(RuntimeSymbolicEdit(
                edit_id=edit_id,
                patch_id=PATCH_ID,
                order=order,
                target_id=target_id,
                symbolic_patch=SymbolicPatch(
                    owner=declaration.owner,
                    path=targets[target_id].path.as_posix(),
                    offset=offset,
                    expected=expected,
                    symbol=mod_text_symbol(entry.string_id),
                    encoding="abs32",
                    mapping_id=edit_id,
                    kind="localization",
                    reason=f"Point {entry.mapping_id} at mod string {entry.string_id}.",
                ),
            ))
    return replace(
        declaration,
        targets=used_targets,
        patches={
            **declaration.patches,
            PATCH_ID: binary_patcher.Patch(patch_id=PATCH_ID, group_id="localization", evidence_id=""),
        },
        edits=tuple(edits),
    )
