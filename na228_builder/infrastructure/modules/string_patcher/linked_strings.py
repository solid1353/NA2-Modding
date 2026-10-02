"""Materialize linked strings and their symbolic pointer patches."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from ...common import sha256_hex
from ..payload_builder.operations import (
    PayloadFragment,
    ResidentPayloadBuild,
    ResolvedPatch,
    SymbolicPatch,
)
from ..translation_importer import engine as translation_importer


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
    summary: dict[str, object]


def _external_mapping_ids(
    translation_plan: translation_importer.TranslationImportPlan,
    adapted: translation_importer.AdaptedTexts,
) -> frozenset[str]:
    reference_ids = {row.mapping_id for row in translation_plan.references}
    mappings_by_slot: dict[tuple[str, int], list[dict[str, object]]] = {}
    for row in translation_plan.text_mappings:
        key = (str(row["target"]), int(row["target_offset"]))
        mappings_by_slot.setdefault(key, []).append(row)

    forced_external: set[str] = set()
    for (target, offset), mappings in mappings_by_slot.items():
        if len(mappings) == 1:
            continue
        label = f"{target} 0x{offset:X} shared source slot"
        if any(row["mode"] != "slot" for row in mappings):
            raise ValueError(f"{label}: aliases require slot mappings")
        capacities = {int(row["capacity"]) for row in mappings}
        sources = {str(row["source"]) for row in mappings}
        if len(capacities) != 1 or len(sources) != 1:
            raise ValueError(
                f"{label}: aliases must declare the same source and capacity"
            )
        inline = [
            str(row["id"])
            for row in mappings
            if str(row["id"]) not in reference_ids
        ]
        aliases = [
            str(row["id"])
            for row in mappings
            if str(row["id"]) in reference_ids
        ]
        alias_only_empty_slot = (
            not inline
            and len(aliases) == len(mappings)
            and sources == {""}
        )
        if not (
            (len(inline) == 1 and len(aliases) == len(mappings) - 1)
            or alias_only_empty_slot
        ):
            raise ValueError(
                f"{label}: requires one unreferenced inline mapping and "
                "pointer-referenced aliases, or only pointer-referenced "
                "aliases for an empty slot"
            )
        if any(
            reference.mapping_id in aliases
            and reference.reference_binary == target
            and offset in reference.reference_file_offsets
            for reference in translation_plan.references
        ):
            raise ValueError(
                f"{label}: an alias cannot redirect the shared source slot itself"
            )
        forced_external.update(aliases)

    external: set[str] = set(forced_external)
    for row in translation_plan.text_mappings:
        mapping_id = str(row["id"])
        capacity = int(row["capacity"])
        label = f"{mapping_id} {row['target']} 0x{int(row['target_offset']):X}"
        encoded = adapted[mapping_id].encoded
        if row["mode"] == "sequence":
            encoded_size = sum(len(fragment) + 1 for fragment in encoded) + 1
            if encoded_size > capacity:
                if mapping_id not in reference_ids:
                    raise ValueError(
                        f"{label}: replacement sequence is {encoded_size} bytes "
                        f"but inline block allows {capacity}, and no pointer reference is declared"
                    )
                external.add(mapping_id)
            continue
        encoded_size = len(encoded[0])
        if mapping_id in forced_external:
            continue
        if encoded_size <= capacity - 1:
            continue
        if mapping_id not in reference_ids:
            raise ValueError(
                f"{label}: replacement is {encoded_size} bytes but slot allows "
                f"{capacity - 1}, and no pointer reference is declared"
            )
        external.add(mapping_id)
    return frozenset(external)


def _materialized_strings(
    translation_plan: translation_importer.TranslationImportPlan,
    adapted: translation_importer.AdaptedTexts,
    *,
    owner: str,
) -> tuple[
    dict[str, bytes],
    dict[str, str],
    list[dict[str, object]],
    frozenset[str],
]:
    text_by_id = {str(row["id"]): row for row in translation_plan.text_mappings}
    external_ids = _external_mapping_ids(translation_plan, adapted)
    active_references = tuple(
        row
        for row in translation_plan.references
        if row.mapping_id in external_ids
    )
    parent_ids = {
        row.parent_mapping_id
        for row in active_references
        if row.parent_mapping_id is not None
    }
    effective_ids = {
        row.parent_mapping_id or row.mapping_id for row in active_references
    }

    def packed(fragments: list[bytes] | tuple[bytes, ...]) -> bytes:
        return b"".join(fragment + b"\0" for fragment in fragments) + b"\0"

    def structured_family_payload(parent_id: str) -> bytes:
        parent = text_by_id[parent_id]
        donor_ref = str(parent["donor_ref"])
        target = str(parent["target"])
        family = sorted(
            (
                row
                for row in translation_plan.text_mappings
                if str(row["donor_ref"]) == donor_ref
                and str(row["target"]) == target
                and str(row["transform"]) in {
                    "split_br", "join_br_parts", "flatten_br_slice",
                }
            ),
            key=lambda row: int(row["target_offset"]),
        )
        if not family or str(family[0]["id"]) != parent_id:
            raise ValueError(
                f"{parent_id}: parent must be the first structured-message slot"
            )
        expected_offset = int(parent["target_offset"])
        fragments: list[bytes] = []
        for member in family:
            member_id = str(member["id"])
            offset = int(member["target_offset"])
            if offset != expected_offset:
                raise ValueError(
                    f"{parent_id}: structured-message slots are not contiguous "
                    f"at {member_id}"
                )
            fragments.append(adapted[member_id].encoded[0])
            expected_offset = offset + int(member["capacity"])
        return packed(fragments)

    encoded_by_symbol: dict[str, bytes] = {}
    symbol_by_mapping: dict[str, str] = {}
    symbol_by_payload: dict[bytes, str] = {}
    rows: list[dict[str, object]] = []
    for mapping_id in sorted(effective_ids):
        mapping = text_by_id[mapping_id]
        if mapping["mode"] == "sequence":
            encoded = packed(adapted[mapping_id].encoded)
            materialization = "packed_sequence"
        elif mapping_id in parent_ids:
            encoded = structured_family_payload(mapping_id)
            materialization = "packed_structured_family"
        else:
            encoded = adapted[mapping_id].encoded[0] + b"\0"
            materialization = (
                "packed_derived" if str(mapping["transform"]) else "packed_replacement"
            )
        symbol = symbol_by_payload.get(encoded)
        if symbol is None:
            symbol = f"{owner}.string.{mapping_id}"
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
                "text_sha256": sha256_hex(encoded[:-1]),
            }
        )
    return encoded_by_symbol, symbol_by_mapping, rows, external_ids


def _symbolic_pointer_patches(
    translation_plan: translation_importer.TranslationImportPlan,
    symbol_by_mapping: dict[str, str],
    *,
    owner: str,
    external_mapping_ids: frozenset[str],
) -> tuple[SymbolicPatch, ...]:
    patches: dict[tuple[str, int], SymbolicPatch] = {}
    for reference in translation_plan.references:
        if reference.mapping_id not in external_mapping_ids:
            continue
        effective_id = reference.parent_mapping_id or reference.mapping_id
        symbol = symbol_by_mapping[effective_id]
        path = translation_importer.TARGET_SPECS[reference.reference_binary]
        for offset in reference.reference_file_offsets:
            patch = SymbolicPatch(
                owner=owner,
                path=path,
                offset=offset,
                expected=reference.pointer.to_bytes(4, "little"),
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
    adapted: translation_importer.AdaptedTexts,
    owner: str,
) -> ExternalStringDraft:
    encoded, symbol_by_mapping, rows, external_ids = _materialized_strings(
        translation_plan,
        adapted,
        owner=owner,
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
        translation_plan,
        symbol_by_mapping,
        owner=owner,
        external_mapping_ids=external_ids,
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
        "external_mappings": len(external_ids),
    }
    return ExternalStringDraft(
        fragments=fragments,
        symbolic_patches=symbolic_patches,
        rows=tuple(rows),
        summary=summary,
        excluded_mapping_ids=external_ids,
    )


def finalize_external_string_plan(
    draft: ExternalStringDraft,
    *,
    build: ResidentPayloadBuild | None,
    resolved_patches: tuple[ResolvedPatch, ...],
) -> ExternalStringPlan:
    if draft.rows and build is None:
        raise ValueError("External strings require a linked payload build")
    rows: list[dict[str, object]] = []
    for draft_row in draft.rows:
        row = dict(draft_row)
        assert build is not None
        symbol = build.symbols[str(row["symbol"])]
        row["file_offset"] = f"0x{symbol.file_offset:X}"
        row["runtime_address"] = f"0x{symbol.runtime_address:X}"
        rows.append(row)
    summary = dict(draft.summary)
    external = dict(summary["external_strings"])
    external["rows"] = rows
    summary["external_strings"] = external
    summary["resolved_pointer_edits"] = len(resolved_patches)
    return ExternalStringPlan(resolved_patches=resolved_patches, summary=summary)
