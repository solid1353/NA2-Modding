from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path, PurePosixPath

from ..binary_patcher import engine as binary_patcher
from ..translation_importer import engine as translation_importer
from ...payload_builder.operations import ResidentPayloadBuild, ResolvedPatch
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

    materialized_templates = {
        mapping_id: text.replace(policy.imported_title, policy.output_title)
        for mapping_id, text in plan.materialized_templates.items()
    }
    return replace(
        plan,
        resolved_texts=resolved_texts,
        resolved_sequences=resolved_sequences,
        materialized_templates=materialized_templates,
    )


def build_binary_package(
    *,
    imported_rows: Sequence[Mapping[str, str]] = (),
    imported_targets: Mapping[str, Mapping[str, object]] | None = None,
) -> binary_patcher.Package:
    package_directory = Path(__file__).resolve().parent
    imported_targets = imported_targets or {}
    targets: dict[str, binary_patcher.Target] = {}
    target_ids: dict[tuple[str, str], str] = {}
    groups: dict[str, binary_patcher.Group] = {}
    patches: dict[str, binary_patcher.Patch] = {}
    edits: list[binary_patcher.Edit] = []

    def ensure_target(
        *,
        root_id: str,
        path: str,
        expected_size: int,
        expected_sha256: str,
        label: str,
    ) -> str:
        normalized_path = binary_patcher.relative_posix(
            path, f"{label} path"
        ).as_posix()
        target_key = (root_id, normalized_path)
        target_id = target_ids.get(target_key)
        if target_id is None:
            target_id = f"string_target_{len(target_ids) + 1:03d}"
            target_ids[target_key] = target_id
            targets[target_id] = binary_patcher.Target(
                target_id=target_id,
                root_id=root_id,
                role="destination",
                path=PurePosixPath(normalized_path),
                expected_size=expected_size,
                expected_sha256=expected_sha256,
            )
            return target_id
        target = targets[target_id]
        if (
            target.expected_size != expected_size
            or target.expected_sha256 != expected_sha256
        ):
            raise binary_patcher.PatchError(
                f"{label}: inconsistent identity for target "
                f"{root_id}:{normalized_path}"
            )
        return target_id

    for row_number, row in enumerate(imported_rows, 1):
        label = f"translation import row {row_number}"
        source_mapping_id = str(row.get("source_mapping_id", "")).strip()
        import_id = str(row.get("import_id", "")).strip()
        group_id = str(row.get("group_id", "")).strip()
        path = binary_patcher.relative_posix(
            str(row.get("path", "")), f"{label} path"
        ).as_posix()
        if not import_id or import_id in patches:
            raise binary_patcher.PatchError(
                f"{label}: missing or duplicate import_id {import_id!r}"
            )
        if not group_id:
            raise binary_patcher.PatchError(f"{label}: group_id is empty")
        metadata = imported_targets.get(path)
        if metadata is None:
            raise binary_patcher.PatchError(
                f"{label}: missing imported target metadata for {path}"
            )
        root_id = str(metadata.get("root_id", "")).strip()
        if not root_id:
            raise binary_patcher.PatchError(f"{label}: imported root_id is empty")
        try:
            expected_size = int(metadata.get("expected_size", 0))
        except (TypeError, ValueError) as exc:
            raise binary_patcher.PatchError(
                f"{label}: invalid imported expected_size"
            ) from exc
        expected_sha256 = binary_patcher.normalized_sha256(
            str(metadata.get("expected_sha256", "")),
            f"{label} expected_sha256",
        )
        offset = binary_patcher.parse_int(
            str(row.get("offset", "")), f"{label} offset"
        )
        try:
            expected = bytes.fromhex(str(row.get("expected_hex", "")))
            replacement = bytes.fromhex(str(row.get("replacement_hex", "")))
        except ValueError as exc:
            raise binary_patcher.PatchError(
                f"{label}: invalid expected/replacement hexadecimal bytes"
            ) from exc
        if not expected or len(expected) != len(replacement):
            raise binary_patcher.PatchError(
                f"{label}: imported edit must be nonempty and fixed-length"
            )
        if offset < 0 or offset + len(expected) > expected_size:
            raise binary_patcher.PatchError(
                f"{label}: imported edit exceeds target size"
            )
        target_id = ensure_target(
            root_id=root_id,
            path=path,
            expected_size=expected_size,
            expected_sha256=expected_sha256,
            label=label,
        )
        reason = (
            str(row.get("reason", "")).strip()
            or "Import official translation text."
        )
        groups.setdefault(
            group_id,
            binary_patcher.Group(
                group_id=group_id,
                enabled=True,
                name=group_id,
                description="Imported string patch selection group.",
                review_notes="",
            ),
        )
        patches[import_id] = binary_patcher.Patch(
            patch_id=import_id,
            group_id=group_id,
            enabled=True,
            status="approved_for_test",
            confidence="verified",
            name=import_id,
            description=reason,
            evidence_id=source_mapping_id,
            review_notes="",
        )
        edits.append(
            binary_patcher.Edit(
                edit_id=f"{import_id}-string",
                patch_id=import_id,
                order=10,
                destination_target_id=target_id,
                destination_offset=offset,
                operation="replace",
                length=len(expected),
                expected_hex=expected.hex().upper(),
                expected_sha256="",
                replacement_hex=replacement.hex().upper(),
                source_target_id="",
                source_offset=None,
                source_expected_hex="",
                source_expected_sha256="",
                blob_path=None,
                blob_offset=None,
                blob_sha256="",
                fill_hex="",
                reason=reason,
            )
        )

    return binary_patcher.Package(
        directory=package_directory,
        package_id="derived.string_patcher",
        targets=targets,
        groups=groups,
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
    external_draft = linked_strings.build_external_string_draft(
        translation_plan=transformed_plan,
        owner=owner,
    )
    transformed_plan = translation_importer.compile_inline_imports(
        transformed_plan,
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
    external_rows = tuple(
        {
            "import_id": f"XT-I{index:04d}",
            "group_id": "external_strings",
            "path": edit.path,
            "offset": f"0x{edit.offset:X}",
            "expected_hex": edit.expected.hex().upper(),
            "replacement_hex": edit.replacement.hex().upper(),
            "source_mapping_id": edit.mapping_id,
            "reason": edit.reason,
        }
        for index, edit in enumerate(external_plan.resolved_patches, 1)
    )
    inline_rows = tuple(translation_plan.import_rows)
    package = build_binary_package(
        imported_rows=inline_rows + external_rows,
        imported_targets=translation_plan.targets,
    )
    summary = dict(external_plan.summary)
    summary["inline_import_rows"] = len(inline_rows)
    summary["external_binary_edits"] = len(external_plan.resolved_patches)
    summary["compiled_binary_edits"] = len(package.edits)
    summary["game_title_policy"] = draft.game_title_policy
    return StringPatchPlan(
        package=package,
        summary=summary,
        external_plan=external_plan,
    )


def external_patch_log_rows(plan: StringPatchPlan) -> list[dict[str, object]]:
    return linked_strings.patch_log_rows(plan.external_plan)
