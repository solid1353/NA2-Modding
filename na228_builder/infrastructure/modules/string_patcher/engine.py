from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path, PurePosixPath

from ..binary_patcher import engine as binary_patcher
from ..translation_importer import engine as translation_importer
from ..payload_builder.operations import ResidentPayloadBuild, ResolvedPatch
from . import linked_strings


@dataclass(frozen=True)
class StringPatchDraft:
    translation_plan: translation_importer.TranslationImportPlan
    external_draft: linked_strings.ExternalStringDraft
    game_title_policy: dict[str, object]


@dataclass(frozen=True)
class StringPatchPlan:
    package: binary_patcher.Package
    summary: dict[str, object]
    external_plan: linked_strings.ExternalStringPlan


@dataclass(frozen=True)
class GameTitlePolicy:
    imported_title: str
    output_title: str
    expected_mapping_count: int
    expected_occurrence_count: int


def _apply_game_title_policy(
    plan: translation_importer.TranslationImportPlan,
    policy: GameTitlePolicy,
) -> translation_importer.TranslationImportPlan:
    """Apply output identity after official strings have been imported."""
    if (
        not policy.imported_title
        or not policy.output_title
        or policy.imported_title == policy.output_title
    ):
        raise ValueError("string-patcher game-title policy must replace distinct text")

    hits: dict[str, int] = {}
    resolved_texts: dict[str, str] = {}
    for mapping_id, text in plan.resolved_texts.items():
        occurrences = text.count(policy.imported_title)
        if occurrences:
            hits[mapping_id] = occurrences
        resolved_texts[mapping_id] = text.replace(
            policy.imported_title, policy.output_title
        )

    resolved_sequences: dict[str, tuple[str, ...]] = {}
    for mapping_id, values in plan.resolved_sequences.items():
        occurrences = sum(value.count(policy.imported_title) for value in values)
        if occurrences:
            hits[mapping_id] = occurrences
        resolved_sequences[mapping_id] = tuple(
            value.replace(policy.imported_title, policy.output_title)
            for value in values
        )

    if (
        len(hits) != policy.expected_mapping_count
        or sum(hits.values()) != policy.expected_occurrence_count
    ):
        raise ValueError(
            "string-patcher game-title coverage differs from the catalog guard: "
            f"{len(hits)} mappings/{sum(hits.values())} occurrences"
        )

    return replace(
        plan,
        resolved_texts=resolved_texts,
        resolved_sequences=resolved_sequences,
    )


def build_binary_package(
    *,
    imported_rows: Sequence[Mapping[str, str]] = (),
    resolved_patches: Sequence[ResolvedPatch] = (),
    imported_targets: Mapping[str, Mapping[str, object]],
) -> binary_patcher.Package:
    """Package inline import rows and resolved external-string pointer writes."""
    targets: dict[str, binary_patcher.Target] = {}
    target_ids: dict[str, str] = {}
    patches: dict[str, binary_patcher.Patch] = {}
    edits: list[binary_patcher.Edit] = []

    def add(
        import_id: str,
        group_id: str,
        path: str,
        offset: int,
        expected_hex: str,
        replacement_hex: str,
        mapping_id: str,
        reason: str,
    ) -> None:
        target_id = target_ids.get(path)
        if target_id is None:
            target_id = f"string_target_{len(target_ids) + 1:03d}"
            target_ids[path] = target_id
            metadata = imported_targets[path]
            targets[target_id] = binary_patcher.Target(
                target_id=target_id,
                root_id=str(metadata["root_id"]),
                path=PurePosixPath(path),
                expected_size=int(metadata["expected_size"]),
                expected_sha256=str(metadata["expected_sha256"]),
            )
        patches[import_id] = binary_patcher.Patch(
            patch_id=import_id,
            group_id=group_id,
            evidence_id=mapping_id,
        )
        edits.append(
            binary_patcher.Edit(
                edit_id=f"{import_id}-string",
                patch_id=import_id,
                order=10,
                destination_target_id=target_id,
                destination_offset=offset,
                operation="replace",
                length=len(expected_hex) // 2,
                expected_hex=expected_hex,
                replacement_hex=replacement_hex,
                reason=reason,
            )
        )

    for row in imported_rows:
        add(
            row["import_id"],
            row["group_id"],
            row["path"],
            int(row["offset"], 0),
            row["expected_hex"],
            row["replacement_hex"],
            row["source_mapping_id"],
            row["reason"],
        )
    for index, patch in enumerate(resolved_patches, 1):
        add(
            f"XT-I{index:04d}",
            "external_strings",
            patch.path,
            patch.offset,
            patch.expected.hex().upper(),
            patch.replacement.hex().upper(),
            patch.mapping_id,
            patch.reason,
        )

    return binary_patcher.Package(
        directory=Path(__file__).resolve().parent,
        package_id="derived.string_patcher",
        targets=targets,
        patches=patches,
        edits=edits,
    )


def build_translation_draft(
    *,
    translation_plan: translation_importer.TranslationImportPlan,
    owner: str,
    title_policy: GameTitlePolicy | None,
) -> StringPatchDraft:
    """Declare external text fragments and symbolic pointer writes."""
    transformed_plan = (
        _apply_game_title_policy(translation_plan, title_policy)
        if title_policy is not None
        else translation_plan
    )
    adapted = translation_importer.AdaptedTexts(transformed_plan)
    external_draft = linked_strings.build_external_string_draft(
        translation_plan=transformed_plan,
        adapted=adapted,
        owner=owner,
    )
    transformed_plan = translation_importer.compile_inline_imports(
        transformed_plan,
        adapted=adapted,
        excluded_mapping_ids=external_draft.excluded_mapping_ids,
    )
    return StringPatchDraft(
        translation_plan=transformed_plan,
        external_draft=external_draft,
        game_title_policy=(
            {
                "applied": True,
                "imported_title": title_policy.imported_title,
                "output_title": title_policy.output_title,
                "mapping_count": title_policy.expected_mapping_count,
                "occurrence_count": title_policy.expected_occurrence_count,
            }
            if title_policy is not None
            else {"applied": False}
        ),
    )


def finalize_translation_plan(
    *,
    draft: StringPatchDraft,
    build: ResidentPayloadBuild | None,
    resolved_patches: tuple[ResolvedPatch, ...],
) -> StringPatchPlan:
    """Compile inline imports and linker-resolved pointer redirects."""
    translation_plan = draft.translation_plan
    external_plan = linked_strings.finalize_external_string_plan(
        draft.external_draft,
        build=build,
        resolved_patches=resolved_patches,
    )
    package = build_binary_package(
        imported_rows=translation_plan.import_rows,
        resolved_patches=external_plan.resolved_patches,
        imported_targets=translation_plan.targets,
    )
    summary = dict(external_plan.summary)
    summary["inline_import_rows"] = len(translation_plan.import_rows)
    summary["external_binary_edits"] = len(external_plan.resolved_patches)
    summary["compiled_binary_edits"] = len(package.edits)
    summary["game_title_policy"] = draft.game_title_policy
    return StringPatchPlan(
        package=package,
        summary=summary,
        external_plan=external_plan,
    )


def external_patch_log_rows(plan: StringPatchPlan) -> list[dict[str, object]]:
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
        for patch in plan.external_plan.resolved_patches
    ]
