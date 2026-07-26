from __future__ import annotations

import codecs
import csv
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path, PurePosixPath

from ..binary_patcher import engine as binary_patcher
from ..translation_importer import engine as translation_importer
from ...payload_builder.operations import ResidentPayloadBuild, ResolvedPatch
from . import external as external_strings


STRING_FIELDS = [
    "string_id",
    "group_id",
    "default_enabled",
    "status",
    "confidence",
    "root_id",
    "path",
    "expected_size",
    "expected_sha256",
    "offset",
    "capacity",
    "encoding",
    "storage",
    "expected_text",
    "replacement_text",
    "reason",
    "review_notes",
]
STORAGE_MODES = {"fixed", "nul_padded"}
TRANSLATION_DISPLAY_MODES = {"translation", "mapping_ids"}


@dataclass(frozen=True)
class StringSpec:
    string_id: str
    group_id: str
    default_enabled: bool
    status: str
    confidence: str
    root_id: str
    path: str
    expected_size: int
    expected_sha256: str
    offset: int
    capacity: int
    encoding: str
    storage: str
    expected_text: str
    replacement_text: str
    reason: str
    review_notes: str


@dataclass(frozen=True)
class StringPatchDraft:
    translation_plan: translation_importer.TranslationImportPlan
    external_draft: external_strings.ExternalStringDraft
    game_title_policy: dict[str, object]


@dataclass(frozen=True)
class StringPatchPlan:
    package: binary_patcher.Package
    summary: dict[str, object]
    external_plan: external_strings.ExternalStringPlan


@dataclass(frozen=True)
class GameTitlePolicy:
    imported_title: str
    output_title: str
    expected_mapping_count: int
    expected_occurrence_count: int


def _mapping_id_token(mapping_id: str, capacity: int) -> str:
    """Return the clearest identifier that fits one NUL-terminated slot."""
    try:
        encoded = mapping_id.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError(
            f"{mapping_id}: diagnostic mapping IDs must be ASCII"
        ) from exc
    if len(encoded) < capacity:
        return mapping_id
    raise ValueError(
        f"{mapping_id}: cannot fit a diagnostic identifier in "
        f"{capacity - 1} display bytes"
    )


def _sequence_id_tokens(
    mapping_id: str,
    fragment_count: int,
    capacity: int,
) -> tuple[str, ...]:
    tokens = tuple(
        f"{mapping_id}.{index}" for index in range(1, fragment_count + 1)
    )
    encoded_size = sum(len(token.encode("ascii")) + 1 for token in tokens) + 1
    if encoded_size > capacity:
        raise ValueError(
            f"{mapping_id}: diagnostic sequence identifiers require "
            f"{encoded_size} bytes but the block allows {capacity}"
        )
    return tokens


def _apply_mapping_id_display(
    plan: translation_importer.TranslationImportPlan,
) -> translation_importer.TranslationImportPlan:
    resolved_texts = dict(plan.resolved_texts)
    resolved_sequences = dict(plan.resolved_sequences)
    materialized_templates = dict(plan.materialized_templates)
    rows: list[dict[str, object]] = []
    for mapping in plan.text_mappings:
        mapping_id = str(mapping["id"])
        capacity = int(mapping["capacity"])
        if mapping["mode"] == "sequence":
            current = resolved_sequences.get(mapping_id)
            if current is None:
                continue
            tokens = _sequence_id_tokens(mapping_id, len(current), capacity)
            resolved_sequences[mapping_id] = tokens
            materialized_templates[mapping_id] = "<NUL>".join(tokens)
            rows.append(
                {
                    "mapping_id": mapping_id,
                    "display": "<NUL>".join(tokens),
                }
            )
            continue
        if mapping_id not in resolved_texts:
            continue
        token = _mapping_id_token(mapping_id, capacity)
        resolved_texts[mapping_id] = token
        materialized_templates[mapping_id] = token
        rows.append({"mapping_id": mapping_id, "display": token})

    summary = dict(plan.summary)
    summary["diagnostic_display"] = {
        "mode": "mapping_ids",
        "mapping_count": len(rows),
        "rows": rows,
    }
    return replace(
        plan,
        resolved_texts=resolved_texts,
        resolved_sequences=resolved_sequences,
        materialized_templates=materialized_templates,
        summary=summary,
        display_mode="mapping_ids",
    )


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
            "string-patcher game-title policy coverage differs from profile identity: "
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


def _encode_slot(text: str, spec: StringSpec, label: str) -> bytes:
    if "\x00" in text:
        raise binary_patcher.PatchError(
            f"{spec.string_id} {label} contains an embedded NUL"
        )
    try:
        encoded = text.encode(spec.encoding)
    except UnicodeEncodeError as exc:
        raise binary_patcher.PatchError(
            f"{spec.string_id} {label} is not encodable as {spec.encoding}"
        ) from exc
    if spec.storage == "fixed":
        if len(encoded) != spec.capacity:
            raise binary_patcher.PatchError(
                f"{spec.string_id} {label} encodes to {len(encoded)} bytes, "
                f"expected exactly {spec.capacity}"
            )
        return encoded
    if len(encoded) >= spec.capacity:
        raise binary_patcher.PatchError(
            f"{spec.string_id} {label} encodes to {len(encoded)} bytes and "
            f"does not fit a NUL-terminated {spec.capacity}-byte slot"
        )
    return encoded + bytes(spec.capacity - len(encoded))


def load_specs(directory: Path) -> tuple[StringSpec, ...]:
    directory = directory.resolve()
    path = directory / "strings.tsv"
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != STRING_FIELDS:
            raise binary_patcher.PatchError(
                f"{path}: expected columns {STRING_FIELDS}, found {reader.fieldnames}"
            )
        rows = list(reader)
    specs: list[StringSpec] = []
    seen: set[str] = set()
    for row_number, row in enumerate(rows, 2):
        string_id = row["string_id"].strip()
        if not string_id or string_id in seen:
            raise binary_patcher.PatchError(
                f"{path} row {row_number}: missing or duplicate string_id {string_id!r}"
            )
        seen.add(string_id)
        group_id = row["group_id"].strip()
        if not group_id:
            raise binary_patcher.PatchError(
                f"{path} row {row_number}: group_id is empty"
            )
        status = row["status"].strip()
        if status not in binary_patcher.PATCH_STATUSES:
            raise binary_patcher.PatchError(
                f"{path} row {row_number}: invalid status {status!r}"
            )
        confidence = row["confidence"].strip()
        if confidence not in binary_patcher.CONFIDENCE_VALUES:
            raise binary_patcher.PatchError(
                f"{path} row {row_number}: invalid confidence {confidence!r}"
            )
        root_id = row["root_id"].strip()
        if not root_id:
            raise binary_patcher.PatchError(
                f"{path} row {row_number}: root_id is empty"
            )
        target_path = binary_patcher.relative_posix(
            row["path"], f"{path} row {row_number} path"
        ).as_posix()
        expected_size = binary_patcher.parse_int(
            row["expected_size"], f"{path} row {row_number} expected_size"
        )
        offset = binary_patcher.parse_int(
            row["offset"], f"{path} row {row_number} offset"
        )
        capacity = binary_patcher.parse_int(
            row["capacity"], f"{path} row {row_number} capacity"
        )
        if expected_size <= 0 or offset < 0 or capacity <= 0:
            raise binary_patcher.PatchError(
                f"{path} row {row_number}: sizes must be positive and offset non-negative"
            )
        if offset + capacity > expected_size:
            raise binary_patcher.PatchError(
                f"{path} row {row_number}: string slot exceeds target size"
            )
        encoding = row["encoding"].strip()
        try:
            encoding = codecs.lookup(encoding).name
        except LookupError as exc:
            raise binary_patcher.PatchError(
                f"{path} row {row_number}: unknown encoding {encoding!r}"
            ) from exc
        storage = row["storage"].strip()
        if storage not in STORAGE_MODES:
            raise binary_patcher.PatchError(
                f"{path} row {row_number}: invalid storage mode {storage!r}"
            )
        spec = StringSpec(
            string_id=string_id,
            group_id=group_id,
            default_enabled=binary_patcher.parse_bool(
                row["default_enabled"],
                f"{path} row {row_number} default_enabled",
            ),
            status=status,
            confidence=confidence,
            root_id=root_id,
            path=target_path,
            expected_size=expected_size,
            expected_sha256=binary_patcher.normalized_sha256(
                row["expected_sha256"],
                f"{path} row {row_number} expected_sha256",
            ),
            offset=offset,
            capacity=capacity,
            encoding=encoding,
            storage=storage,
            expected_text=row["expected_text"],
            replacement_text=row["replacement_text"],
            reason=row["reason"].strip(),
            review_notes=row["review_notes"].strip(),
        )
        if (
            spec.default_enabled
            and spec.status not in binary_patcher.APPLICABLE_STATUSES
        ):
            raise binary_patcher.PatchError(
                f"{path} row {row_number}: default-enabled strings must be applicable"
            )
        if not spec.reason:
            raise binary_patcher.PatchError(
                f"{path} row {row_number}: reason is empty"
            )
        _encode_slot(spec.expected_text, spec, "expected_text")
        _encode_slot(spec.replacement_text, spec, "replacement_text")
        specs.append(spec)
    return tuple(specs)


def build_binary_package(
    directory: Path | None,
    *,
    imported_rows: Sequence[Mapping[str, str]] = (),
    imported_targets: Mapping[str, Mapping[str, object]] | None = None,
) -> binary_patcher.Package:
    package_directory = (
        directory.resolve() if directory is not None else Path(__file__).resolve().parent
    )
    specs = load_specs(package_directory) if directory is not None else ()
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

    for spec in specs:
        target_id = ensure_target(
            root_id=spec.root_id,
            path=spec.path,
            expected_size=spec.expected_size,
            expected_sha256=spec.expected_sha256,
            label=spec.string_id,
        )
        groups.setdefault(
            spec.group_id,
            binary_patcher.Group(
                group_id=spec.group_id,
                name=spec.group_id.replace("_", " ").title(),
                description="String patch selection group.",
                review_notes="",
            ),
        )
        patches[spec.string_id] = binary_patcher.Patch(
            patch_id=spec.string_id,
            group_id=spec.group_id,
            default_enabled=spec.default_enabled,
            status=spec.status,
            confidence=spec.confidence,
            name=spec.string_id,
            description=spec.reason,
            source_mapping_id="",
            runtime_classification="",
            review_notes=spec.review_notes,
        )
        edits.append(
            binary_patcher.Edit(
                edit_id=f"{spec.string_id}-string",
                patch_id=spec.string_id,
                order=10,
                destination_target_id=target_id,
                destination_offset=spec.offset,
                operation="replace",
                length=spec.capacity,
                expected_hex=_encode_slot(
                    spec.expected_text, spec, "expected_text"
                ).hex().upper(),
                expected_sha256="",
                replacement_hex=_encode_slot(
                    spec.replacement_text, spec, "replacement_text"
                ).hex().upper(),
                source_target_id="",
                source_offset=None,
                source_expected_hex="",
                source_expected_sha256="",
                blob_path=None,
                blob_offset=None,
                blob_sha256="",
                fill_hex="",
                reason=spec.reason,
            )
        )

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
                name=group_id,
                description="Imported string patch selection group.",
                review_notes="",
            ),
        )
        patches[import_id] = binary_patcher.Patch(
            patch_id=import_id,
            group_id=group_id,
            default_enabled=True,
            status="approved_for_test",
            confidence="verified",
            name=import_id,
            description=reason,
            source_mapping_id=source_mapping_id,
            runtime_classification="",
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
        package_id=(
            f"{package_directory.parent.name}.{package_directory.name}"
            if directory is not None and package_directory.name == "string_patcher"
            else (
                package_directory.name
                if directory is not None
                else "derived.string_patcher"
            )
        ),
        targets=targets,
        groups=groups,
        patches=patches,
        edits=edits,
    )


def build_translation_draft(
    *,
    translation_plan: translation_importer.TranslationImportPlan,
    owner: str,
    title_policy: GameTitlePolicy,
    translation_display: str = "translation",
) -> StringPatchDraft:
    """Declare external text fragments and symbolic pointer writes."""
    if translation_display not in TRANSLATION_DISPLAY_MODES:
        raise ValueError(
            "unsupported translation display mode: "
            f"{translation_display!r}"
        )
    if translation_display == "mapping_ids":
        transformed_plan = _apply_mapping_id_display(translation_plan)
    else:
        transformed_plan = _apply_game_title_policy(
            translation_plan,
            title_policy,
        )
    external_draft = external_strings.build_external_string_draft(
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
        game_title_policy={
            "applied": translation_display == "translation",
            "imported_title": title_policy.imported_title,
            "output_title": title_policy.output_title,
            "mapping_count": title_policy.expected_mapping_count,
            "occurrence_count": title_policy.expected_occurrence_count,
        },
    )


def finalize_translation_plan(
    directory: Path | None,
    *,
    draft: StringPatchDraft,
    build: ResidentPayloadBuild | None,
    resolved_patches: tuple[ResolvedPatch, ...],
) -> StringPatchPlan:
    """Compile inline imports and linker-resolved pointer redirects."""
    translation_plan = draft.translation_plan
    external_plan = external_strings.finalize_external_string_plan(
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
        directory,
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
    return external_strings.patch_log_rows(plan.external_plan)
