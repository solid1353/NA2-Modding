from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass

from ...payload_builder.operations import (
    PayloadFragment,
    ResidentPayloadBuild,
    ResolvedPatch,
    SymbolicPatch,
)
from ..translation_importer import engine as translation_importer


TARGET_PATHS = {
    target: values[0] for target, values in translation_importer.TARGET_SPECS.items()
}


@dataclass(frozen=True)
class ExternalStringDraft:
    fragments: tuple[PayloadFragment, ...]
    symbolic_patches: tuple[SymbolicPatch, ...]
    rows: tuple[dict[str, object], ...]
    summary: dict[str, object]
    excluded_mapping_ids: frozenset[str]


@dataclass(frozen=True)
class ExternalStringPlan:
    resolved_patches: tuple[ResolvedPatch, ...]
    rows: tuple[dict[str, object], ...]
    summary: dict[str, object]
    excluded_mapping_ids: frozenset[str]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def _materialized_strings(
    translation_plan: translation_importer.TranslationImportPlan,
) -> tuple[
    dict[str, bytes],
    dict[str, str],
    list[dict[str, object]],
    frozenset[str],
]:
    text_by_id = {str(row["id"]): row for row in translation_plan.text_mappings}
    shortening_ids = frozenset(
        mapping_id
        for mapping_id, row in text_by_id.items()
        if row["mode"] == "shorten"
    )
    reference_ids = frozenset(row.mapping_id for row in translation_plan.references)
    if reference_ids != shortening_ids:
        raise ValueError(
            "external string reference coverage differs from shortening mappings"
        )
    parent_ids = {
        row.parent_mapping_id
        for row in translation_plan.references
        if row.parent_mapping_id is not None
    }
    effective_ids = {
        row.parent_mapping_id or row.mapping_id for row in translation_plan.references
    }

    encoded_by_symbol: dict[str, bytes] = {}
    symbol_by_mapping: dict[str, str] = {}
    symbol_by_payload: dict[bytes, str] = {}
    rows: list[dict[str, object]] = []
    for mapping_id in sorted(effective_ids):
        mapping = text_by_id[mapping_id]
        if mapping_id in parent_ids:
            text = translation_plan.source_templates[mapping_id]
            materialization = "packed_donor"
        else:
            text = translation_plan.resolved_texts[mapping_id]
            materialization = (
                "packed_derived" if str(mapping["transform"]) else "packed_donor"
            )
        encoded = text.encode("cp1252") + b"\0"
        symbol = symbol_by_payload.get(encoded)
        if symbol is None:
            symbol = f"localization.string.{mapping_id}"
            symbol_by_payload[encoded] = symbol
            encoded_by_symbol[symbol] = encoded
        else:
            materialization = "deduplicated"
        symbol_by_mapping[mapping_id] = symbol
        rows.append(
            {
                "mapping_id": mapping_id,
                "symbol": symbol,
                "materialization": materialization,
                "encoded_bytes": len(encoded),
                "text_sha256": sha256(encoded[:-1]),
            }
        )
    return encoded_by_symbol, symbol_by_mapping, rows, shortening_ids


def _symbolic_pointer_patches(
    translation_plan: translation_importer.TranslationImportPlan,
    symbol_by_mapping: dict[str, str],
    *,
    owner: str,
) -> tuple[SymbolicPatch, ...]:
    patches: dict[tuple[str, int], SymbolicPatch] = {}
    for reference in translation_plan.references:
        effective_id = reference.parent_mapping_id or reference.mapping_id
        symbol = symbol_by_mapping[effective_id]
        expected_address = (
            reference.parent_runtime_address
            if reference.parent_runtime_address is not None
            else reference.target_runtime_address
        )
        expected = expected_address.to_bytes(4, "little")
        clean = translation_plan.clean_targets[reference.reference_binary]
        path = TARGET_PATHS[reference.reference_binary]
        for offset in reference.reference_file_offsets:
            actual = clean[offset:offset + 4]
            if actual != expected:
                raise ValueError(
                    f"{reference.mapping_id}: pointer guard at {path} "
                    f"0x{offset:X} differs from the importer-validated value"
                )
            patch = SymbolicPatch(
                owner=owner,
                path=path,
                offset=offset,
                expected=expected,
                symbol=symbol,
                encoding="abs32",
                mapping_id=reference.mapping_id,
                kind="redirect_pointer",
                reason=(
                    f"Redirect {reference.mapping_id} to linked official text "
                    f"{effective_id}."
                ),
            )
            key = (path, offset)
            prior = patches.get(key)
            if prior is not None:
                if prior.expected != patch.expected or prior.symbol != patch.symbol:
                    raise ValueError(
                        f"conflicting symbolic string pointers at {path} 0x{offset:X}"
                    )
                continue
            patches[key] = patch
    return tuple(patches[key] for key in sorted(patches))


def build_external_string_draft(
    *,
    translation_plan: translation_importer.TranslationImportPlan,
    owner: str,
) -> ExternalStringDraft:
    encoded, symbol_by_mapping, rows, shortening_ids = _materialized_strings(
        translation_plan
    )
    fragments = tuple(
        PayloadFragment(
            owner=owner,
            symbol=symbol,
            kind="rodata",
            alignment=4,
            payload=payload,
        )
        for symbol, payload in sorted(encoded.items())
    )
    symbolic_patches = _symbolic_pointer_patches(
        translation_plan, symbol_by_mapping, owner=owner
    )
    counts = Counter(
        row["materialization"] for row in rows
    )
    summary: dict[str, object] = {
        "external_strings": {
            "count": len(rows),
            "distinct": len(fragments),
            "encoded_bytes": sum(len(fragment.payload) for fragment in fragments),
            "derived": counts["packed_derived"],
        },
        "symbolic_pointer_edits": len(symbolic_patches),
        "inline_shortening_imports_omitted": len(shortening_ids),
    }
    return ExternalStringDraft(
        fragments=fragments,
        symbolic_patches=symbolic_patches,
        rows=tuple(rows),
        summary=summary,
        excluded_mapping_ids=shortening_ids,
    )


def finalize_external_string_plan(
    draft: ExternalStringDraft,
    *,
    build: ResidentPayloadBuild,
    resolved_patches: tuple[ResolvedPatch, ...],
) -> ExternalStringPlan:
    rows: list[dict[str, object]] = []
    for draft_row in draft.rows:
        row = dict(draft_row)
        symbol = build.symbols[str(row["symbol"])]
        row["file_offset"] = f"0x{symbol.file_offset:X}"
        row["runtime_address"] = f"0x{symbol.runtime_address:X}"
        rows.append(row)
    summary = dict(draft.summary)
    external = dict(summary["external_strings"])
    external["rows"] = rows
    summary["external_strings"] = external
    summary["resolved_pointer_edits"] = len(resolved_patches)
    return ExternalStringPlan(
        resolved_patches=resolved_patches,
        rows=tuple(rows),
        summary=summary,
        excluded_mapping_ids=draft.excluded_mapping_ids,
    )


def patch_log_rows(plan: ExternalStringPlan) -> list[dict[str, object]]:
    return [
        {
            "target": patch.path,
            "offset": f"0x{patch.offset:X}",
            "length": len(patch.expected),
            "original_hex": patch.expected.hex().upper(),
            "new_hex": patch.replacement.hex().upper(),
            "mapping_id": patch.mapping_id,
            "kind": patch.kind,
            "reason": patch.reason,
        }
        for patch in plan.resolved_patches
    ]
