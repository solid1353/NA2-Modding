#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import os
import re
import shutil
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from na2_patcher.project_paths import load_project_paths, resolve_alias
from na2_patcher.source_media import read_root_file

PROJECT_PATHS = load_project_paths(REPOSITORY_ROOT, allow_missing=True)

BINARY_PATCHER_SCHEMA_VERSION = 3
TARGET_FIELDS = [
    "target_id",
    "root_id",
    "role",
    "path",
    "expected_size",
    "expected_sha256",
]
GROUP_FIELDS = [
    "group_id",
    "enabled",
    "name",
    "description",
    "review_notes",
]
PATCH_FIELDS = [
    "patch_id",
    "group_id",
    "enabled",
    "status",
    "confidence",
    "name",
    "description",
    "source_mapping_id",
    "runtime_classification",
    "review_notes",
]
EDIT_FIELDS = [
    "edit_id",
    "patch_id",
    "order",
    "destination_target_id",
    "destination_offset",
    "operation",
    "length",
    "expected_hex",
    "expected_sha256",
    "replacement_hex",
    "source_target_id",
    "source_offset",
    "source_expected_hex",
    "source_expected_sha256",
    "blob_path",
    "blob_offset",
    "blob_sha256",
    "fill_hex",
    "reason",
]

PATCH_STATUSES = {
    "pending",
    "approved_for_test",
    "runtime_proven",
    "runtime_failed",
    "deprecated",
}
APPLICABLE_STATUSES = {"approved_for_test", "runtime_proven"}
CONFIDENCE_VALUES = {"high", "medium", "low", "verified"}
ROLES = {"destination", "source", "both"}
OPERATIONS = {"replace", "copy", "blob", "fill"}


class PatchError(RuntimeError):
    pass


@dataclass(frozen=True)
class Target:
    target_id: str
    root_id: str
    role: str
    path: PurePosixPath
    expected_size: int
    expected_sha256: str


@dataclass(frozen=True)
class Group:
    group_id: str
    enabled: bool
    name: str
    description: str
    review_notes: str


@dataclass(frozen=True)
class Patch:
    patch_id: str
    group_id: str
    enabled: bool
    status: str
    confidence: str
    name: str
    description: str
    source_mapping_id: str
    runtime_classification: str
    review_notes: str


@dataclass(frozen=True)
class Edit:
    edit_id: str
    patch_id: str
    order: int
    destination_target_id: str
    destination_offset: int
    operation: str
    length: int
    expected_hex: str
    expected_sha256: str
    replacement_hex: str
    source_target_id: str
    source_offset: int | None
    source_expected_hex: str
    source_expected_sha256: str
    blob_path: PurePosixPath | None
    blob_offset: int | None
    blob_sha256: str
    fill_hex: str
    reason: str


@dataclass
class Package:
    directory: Path
    package_id: str
    targets: dict[str, Target]
    groups: dict[str, Group]
    patches: dict[str, Patch]
    edits: list[Edit]


def parse_bool(value: str, label: str) -> bool:
    if value == "0":
        return False
    if value == "1":
        return True
    raise PatchError(f"{label} must be 0 or 1")


def parse_int(value: str, label: str) -> int:
    try:
        return int(value, 0)
    except ValueError as exc:
        raise PatchError(f"{label} is not an integer: {value!r}") from exc


def normalized_hex(value: str, label: str, *, allow_empty: bool = True) -> str:
    compact = "".join(value.split()).upper()
    if not compact and allow_empty:
        return ""
    if not compact:
        raise PatchError(f"{label} is empty")
    if len(compact) % 2 or not re.fullmatch(r"[0-9A-F]+", compact):
        raise PatchError(f"{label} is not even-length hexadecimal data")
    return compact


def normalized_sha256(value: str, label: str, *, allow_empty: bool = False) -> str:
    result = value.strip().upper()
    if not result and allow_empty:
        return ""
    if not re.fullmatch(r"[0-9A-F]{64}", result):
        raise PatchError(f"{label} is not a SHA-256 value")
    return result


def data_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def relative_posix(value: str, label: str) -> PurePosixPath:
    text = value.strip().replace("\\", "/")
    if not text or re.match(r"^[A-Za-z]:", text):
        raise PatchError(f"{label} must be a non-empty relative path")
    path = PurePosixPath(text)
    if (
        path.is_absolute()
        or any(part in {"", ".", ".."} for part in path.parts)
        or path.as_posix() != text
    ):
        raise PatchError(f"{label} must be a normalized relative path: {value!r}")
    return path


def command_relative_path(value: str, label: str, workspace: Path) -> Path:
    raw = Path(value)
    if raw.is_absolute():
        raise PatchError(f"{label} must be repository-relative: {value}")
    resolved = (workspace / raw).resolve()
    try:
        resolved.relative_to(workspace)
    except ValueError as exc:
        raise PatchError(f"{label} escapes the repository: {value}") from exc
    return resolved


def read_tsv(path: Path, expected_fields: list[str]) -> list[dict[str, str]]:
    if not path.is_file():
        raise PatchError(f"Required TSV is missing: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != expected_fields:
            actual = "\t".join(reader.fieldnames or [])
            expected = "\t".join(expected_fields)
            raise PatchError(
                f"Unexpected columns in {path.name}\nExpected: {expected}\nActual:   {actual}"
            )
        rows = []
        for row_number, row in enumerate(reader, 2):
            if None in row:
                raise PatchError(f"{path.name} row {row_number} has extra columns")
            if any(value is None for value in row.values()):
                raise PatchError(f"{path.name} row {row_number} has missing columns")
            if not any(value.strip() for value in row.values()):
                continue
            rows.append({key: value.strip() for key, value in row.items()})
        return rows


def unique_id(value: str, label: str, seen: set[str]) -> str:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", value):
        raise PatchError(f"{label} has an invalid identifier: {value!r}")
    if value in seen:
        raise PatchError(f"Duplicate {label}: {value}")
    seen.add(value)
    return value


def load_package(directory: Path) -> Package:
    directory = directory.resolve()
    if (directory / "manifest.tsv").exists():
        raise PatchError("binary_patcher manifest.tsv is obsolete and must be removed")
    package_id = (
        f"{directory.parent.name}.{directory.name}"
        if directory.name == "binary_patcher"
        else directory.name
    )
    unique_id(package_id, "package_id", set())

    targets: dict[str, Target] = {}
    seen: set[str] = set()
    for row_number, row in enumerate(
        read_tsv(directory / "targets.tsv", TARGET_FIELDS), 2
    ):
        target_id = unique_id(row["target_id"], "target_id", seen)
        root_id = row["root_id"]
        if not re.fullmatch(r"[a-z][a-z0-9_-]*", root_id):
            raise PatchError(f"targets.tsv row {row_number}: invalid root_id")
        if row["role"] not in ROLES:
            raise PatchError(f"targets.tsv row {row_number}: invalid role")
        expected_size = parse_int(
            row["expected_size"], f"targets.tsv row {row_number} expected_size"
        )
        if expected_size < 0:
            raise PatchError(f"targets.tsv row {row_number}: negative expected_size")
        targets[target_id] = Target(
            target_id=target_id,
            root_id=root_id,
            role=row["role"],
            path=relative_posix(row["path"], f"target {target_id} path"),
            expected_size=expected_size,
            expected_sha256=normalized_sha256(
                row["expected_sha256"], f"target {target_id} expected_sha256"
            ),
        )

    groups: dict[str, Group] = {}
    seen = set()
    for row_number, row in enumerate(
        read_tsv(directory / "groups.tsv", GROUP_FIELDS), 2
    ):
        group_id = unique_id(row["group_id"], "group_id", seen)
        if not row["name"]:
            raise PatchError(f"groups.tsv row {row_number}: name is empty")
        groups[group_id] = Group(
            group_id=group_id,
            enabled=parse_bool(
                row["enabled"], f"groups.tsv row {row_number} enabled"
            ),
            name=row["name"],
            description=row["description"],
            review_notes=row["review_notes"],
        )

    patches: dict[str, Patch] = {}
    seen = set()
    for row_number, row in enumerate(
        read_tsv(directory / "patches.tsv", PATCH_FIELDS), 2
    ):
        patch_id = unique_id(row["patch_id"], "patch_id", seen)
        group_id = row["group_id"]
        if group_id not in groups:
            raise PatchError(
                f"patches.tsv row {row_number}: unknown group_id {group_id!r}"
            )
        status = row["status"]
        if status not in PATCH_STATUSES:
            raise PatchError(f"patches.tsv row {row_number}: invalid status {status!r}")
        confidence = row["confidence"]
        if confidence not in CONFIDENCE_VALUES:
            raise PatchError(
                f"patches.tsv row {row_number}: invalid confidence {confidence!r}"
            )
        enabled = parse_bool(
            row["enabled"],
            f"patches.tsv row {row_number} enabled",
        )
        if enabled and status not in APPLICABLE_STATUSES:
            raise PatchError(
                f"patch {patch_id}: enabled patches must be applicable"
            )
        patches[patch_id] = Patch(
            patch_id=patch_id,
            group_id=group_id,
            enabled=enabled,
            status=status,
            confidence=confidence,
            name=row["name"],
            description=row["description"],
            source_mapping_id=row["source_mapping_id"],
            runtime_classification=row["runtime_classification"],
            review_notes=row["review_notes"],
        )
    edits: list[Edit] = []
    seen = set()
    patch_edit_counts = {patch_id: 0 for patch_id in patches}
    for row_number, row in enumerate(
        read_tsv(directory / "edits.tsv", EDIT_FIELDS), 2
    ):
        edit_id = unique_id(row["edit_id"], "edit_id", seen)
        patch_id = row["patch_id"]
        if patch_id not in patches:
            raise PatchError(f"edits.tsv row {row_number}: unknown patch_id")
        destination_id = row["destination_target_id"]
        if destination_id not in targets:
            raise PatchError(f"edits.tsv row {row_number}: unknown destination target")
        if targets[destination_id].role not in {"destination", "both"}:
            raise PatchError(f"edit {edit_id}: target is not a destination")
        operation = row["operation"]
        if operation not in OPERATIONS:
            raise PatchError(f"edit {edit_id}: unsupported operation {operation!r}")
        order = parse_int(row["order"], f"edit {edit_id} order")
        offset = parse_int(
            row["destination_offset"], f"edit {edit_id} destination_offset"
        )
        length = parse_int(row["length"], f"edit {edit_id} length")
        if order < 0 or offset < 0 or length <= 0:
            raise PatchError(f"edit {edit_id}: invalid order, offset, or length")
        expected_hex = normalized_hex(
            row["expected_hex"], f"edit {edit_id} expected_hex"
        )
        expected_sha = normalized_sha256(
            row["expected_sha256"],
            f"edit {edit_id} expected_sha256",
            allow_empty=True,
        )
        if bool(expected_hex) == bool(expected_sha):
            raise PatchError(
                f"edit {edit_id}: provide exactly one of expected_hex/expected_sha256"
            )
        if expected_hex and len(bytes.fromhex(expected_hex)) != length:
            raise PatchError(f"edit {edit_id}: expected_hex length mismatch")

        replacement_hex = normalized_hex(
            row["replacement_hex"], f"edit {edit_id} replacement_hex"
        )
        source_id = row["source_target_id"]
        source_offset = (
            parse_int(row["source_offset"], f"edit {edit_id} source_offset")
            if row["source_offset"]
            else None
        )
        source_expected_hex = normalized_hex(
            row["source_expected_hex"], f"edit {edit_id} source_expected_hex"
        )
        source_expected_sha = normalized_sha256(
            row["source_expected_sha256"],
            f"edit {edit_id} source_expected_sha256",
            allow_empty=True,
        )
        blob_path = (
            relative_posix(row["blob_path"], f"edit {edit_id} blob_path")
            if row["blob_path"]
            else None
        )
        blob_offset = (
            parse_int(row["blob_offset"], f"edit {edit_id} blob_offset")
            if row["blob_offset"]
            else None
        )
        blob_sha = normalized_sha256(
            row["blob_sha256"], f"edit {edit_id} blob_sha256", allow_empty=True
        )
        fill_hex = normalized_hex(row["fill_hex"], f"edit {edit_id} fill_hex")

        if operation == "replace":
            if len(bytes.fromhex(replacement_hex)) != length:
                raise PatchError(f"edit {edit_id}: replacement_hex length mismatch")
            if (
                source_id
                or source_offset is not None
                or source_expected_hex
                or source_expected_sha
                or blob_path
                or blob_offset is not None
                or blob_sha
                or fill_hex
            ):
                raise PatchError(f"edit {edit_id}: replace has unrelated source fields")
        elif operation == "copy":
            if (
                replacement_hex
                or blob_path
                or blob_offset is not None
                or blob_sha
                or fill_hex
            ):
                raise PatchError(f"edit {edit_id}: copy has unrelated data fields")
            if source_id not in targets or source_offset is None or source_offset < 0:
                raise PatchError(f"edit {edit_id}: copy source is incomplete")
            if targets[source_id].role not in {"source", "both"}:
                raise PatchError(f"edit {edit_id}: copy target is not a source")
            if bool(source_expected_hex) == bool(source_expected_sha):
                raise PatchError(
                    f"edit {edit_id}: provide exactly one source expectation"
                )
            if source_expected_hex and len(bytes.fromhex(source_expected_hex)) != length:
                raise PatchError(f"edit {edit_id}: source_expected_hex length mismatch")
        elif operation == "blob":
            if (
                replacement_hex
                or source_id
                or source_offset is not None
                or source_expected_hex
                or source_expected_sha
                or fill_hex
            ):
                raise PatchError(f"edit {edit_id}: blob has unrelated data fields")
            if blob_path is None or blob_offset is None or blob_offset < 0 or not blob_sha:
                raise PatchError(f"edit {edit_id}: blob source is incomplete")
        elif operation == "fill":
            if (
                replacement_hex
                or source_id
                or source_offset is not None
                or source_expected_hex
                or source_expected_sha
                or blob_path
                or blob_offset is not None
                or blob_sha
            ):
                raise PatchError(f"edit {edit_id}: fill has unrelated data fields")
            if len(bytes.fromhex(fill_hex)) != 1:
                raise PatchError(f"edit {edit_id}: fill_hex must be exactly one byte")
        edits.append(
            Edit(
                edit_id=edit_id,
                patch_id=patch_id,
                order=order,
                destination_target_id=destination_id,
                destination_offset=offset,
                operation=operation,
                length=length,
                expected_hex=expected_hex,
                expected_sha256=expected_sha,
                replacement_hex=replacement_hex,
                source_target_id=source_id,
                source_offset=source_offset,
                source_expected_hex=source_expected_hex,
                source_expected_sha256=source_expected_sha,
                blob_path=blob_path,
                blob_offset=blob_offset,
                blob_sha256=blob_sha,
                fill_hex=fill_hex,
                reason=row["reason"],
            )
        )
        patch_edit_counts[patch_id] += 1
    for patch_id, count in patch_edit_counts.items():
        if count == 0:
            raise PatchError(f"patch {patch_id} has no edits")

    group_patch_counts = {group_id: 0 for group_id in groups}
    for patch in patches.values():
        group_patch_counts[patch.group_id] += 1
    for group_id, count in group_patch_counts.items():
        if count == 0:
            raise PatchError(f"group {group_id} has no patches")

    return Package(directory, package_id, targets, groups, patches, edits)


def parse_roots(values: list[str], workspace: Path) -> dict[str, Path]:
    roots: dict[str, Path] = {}
    for value in values:
        root_id, separator, path_text = value.partition("=")
        if not separator or not re.fullmatch(r"[a-z][a-z0-9_-]*", root_id):
            raise PatchError(f"Invalid --root binding: {value!r}")
        if root_id in roots:
            raise PatchError(f"Duplicate --root binding: {root_id}")
        if path_text.startswith("@"):
            try:
                path = resolve_alias(path_text, PROJECT_PATHS)
            except (KeyError, ValueError) as exc:
                raise PatchError(
                    f"Invalid project-root alias for root {root_id}: {path_text!r}"
                ) from exc
        else:
            path = command_relative_path(path_text, f"root {root_id}", workspace)
        if not (path.is_dir() or path.is_file()):
            raise PatchError(f"Root is not an extraction or ISO: {path_text}")
        roots[root_id] = path
    return roots


def target_file(target: Target, roots: dict[str, Path]) -> Path:
    if target.root_id not in roots:
        raise PatchError(f"Missing --root binding for {target.root_id}")
    path = roots[target.root_id].joinpath(*target.path.parts)
    if not path.is_file():
        raise PatchError(f"Target file is missing: {target.root_id}/{target.path}")
    return path


def verify_target(target: Target, roots: dict[str, Path]) -> bytes:
    if target.root_id not in roots:
        raise PatchError(f"Missing root binding for {target.root_id}")
    try:
        data = read_root_file(roots[target.root_id], target.path)
    except FileNotFoundError as exc:
        raise PatchError(
            f"Target file is missing: {target.root_id}/{target.path}"
        ) from exc
    if len(data) != target.expected_size:
        raise PatchError(
            f"Target size mismatch for {target.target_id}: "
            f"expected {target.expected_size}, found {len(data)}"
        )
    actual_hash = data_sha256(data)
    if actual_hash != target.expected_sha256:
        raise PatchError(
            f"Target SHA-256 mismatch for {target.target_id}: "
            f"expected {target.expected_sha256}, found {actual_hash}"
        )
    return data


def verify_range(data: bytes, offset: int, length: int, label: str) -> bytes:
    end = offset + length
    if offset < 0 or end > len(data):
        raise PatchError(
            f"{label} range 0x{offset:X}-0x{end:X} is outside {len(data)} bytes"
        )
    return data[offset:end]


def verify_expectation(data: bytes, expected_hex: str, expected_sha: str, label: str) -> None:
    if expected_hex and data != bytes.fromhex(expected_hex):
        raise PatchError(
            f"{label} expected {expected_hex}, found {data.hex().upper()}"
        )
    if expected_sha and data_sha256(data) != expected_sha:
        raise PatchError(
            f"{label} SHA-256 expected {expected_sha}, found {data_sha256(data)}"
        )


def replacement_for_edit(
    edit: Edit,
    package: Package,
    target_data: dict[str, bytes],
) -> bytes:
    if edit.operation == "replace":
        return bytes.fromhex(edit.replacement_hex)
    if edit.operation == "fill":
        return bytes.fromhex(edit.fill_hex) * edit.length
    if edit.operation == "copy":
        assert edit.source_offset is not None
        source = target_data[edit.source_target_id]
        data = verify_range(
            source,
            edit.source_offset,
            edit.length,
            f"edit {edit.edit_id} source",
        )
        verify_expectation(
            data,
            edit.source_expected_hex,
            edit.source_expected_sha256,
            f"edit {edit.edit_id} source",
        )
        return data
    assert edit.blob_path is not None and edit.blob_offset is not None
    blob_file = package.directory.joinpath(*edit.blob_path.parts)
    if not blob_file.is_file():
        raise PatchError(f"edit {edit.edit_id}: blob is missing: {edit.blob_path}")
    blob = blob_file.read_bytes()
    if file_sha256(blob_file) != edit.blob_sha256:
        raise PatchError(f"edit {edit.edit_id}: blob SHA-256 mismatch")
    return verify_range(blob, edit.blob_offset, edit.length, f"edit {edit.edit_id} blob")


def verify_package_data(package: Package, roots: dict[str, Path]) -> dict[str, bytes]:
    used_roots = {target.root_id for target in package.targets.values()}
    missing = sorted(used_roots - roots.keys())
    if missing:
        raise PatchError("Missing root bindings: " + ", ".join(missing))
    target_data = {
        target_id: verify_target(target, roots)
        for target_id, target in package.targets.items()
    }
    for edit in package.edits:
        destination = target_data[edit.destination_target_id]
        verify_range(
            destination,
            edit.destination_offset,
            edit.length,
            f"edit {edit.edit_id} destination",
        )
        replacement = replacement_for_edit(edit, package, target_data)
        if len(replacement) != edit.length:
            raise PatchError(f"edit {edit.edit_id}: replacement length mismatch")
    return target_data


def patch_is_enabled(package: Package, patch: Patch) -> bool:
    return package.groups[patch.group_id].enabled and patch.enabled


def selected_patch_ids(package: Package, requested: list[str], enabled: bool) -> list[str]:
    if requested and enabled:
        raise PatchError("Use explicit --patch selections or --enabled, not both")
    if enabled:
        selected = [
            patch.patch_id
            for patch in package.patches.values()
            if patch_is_enabled(package, patch)
        ]
    else:
        selected = []
        for patch_id in requested:
            if patch_id not in package.patches:
                raise PatchError(f"Unknown patch ID: {patch_id}")
            selected.append(patch_id)
    if not selected and not enabled:
        raise PatchError("No patches selected")
    return selected


def validate_selection(package: Package, selected: list[str], *, for_apply: bool) -> list[Edit]:
    if not selected:
        raise PatchError("No patches selected")
    for patch_id in selected:
        if patch_id not in package.patches:
            raise PatchError(f"Unknown patch ID: {patch_id}")
    if for_apply:
        blocked = [
            patch_id
            for patch_id in selected
            if package.patches[patch_id].status not in APPLICABLE_STATUSES
        ]
        if blocked:
            details = ", ".join(
                f"{patch_id} ({package.patches[patch_id].status})"
                for patch_id in blocked
            )
            raise PatchError(f"Selected patches are not approved for application: {details}")
    edits_by_patch: dict[str, list[Edit]] = {}
    for edit in package.edits:
        edits_by_patch.setdefault(edit.patch_id, []).append(edit)
    occurrences = {patch_id: index for index, patch_id in enumerate(selected)}
    result: list[Edit] = [
        edit
        for patch_id in selected
        for edit in sorted(
            edits_by_patch[patch_id],
            key=lambda item: (item.order, item.edit_id),
        )
    ]
    return sorted(
        result,
        key=lambda item: (
            item.destination_target_id,
            item.destination_offset,
            occurrences[item.patch_id],
            item.order,
            item.edit_id,
        ),
    )


def write_tsv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def patch_selection_rows(
    package: Package,
    selected: list[str],
    *,
    selection_mode: str,
) -> list[dict[str, object]]:
    selected_ids = set(selected)
    return [
        {
            "group_id": patch.group_id,
            "group_name": package.groups[patch.group_id].name,
            "group_enabled": int(package.groups[patch.group_id].enabled),
            "patch_id": patch.patch_id,
            "patch_enabled": int(patch.enabled),
            "effective_selected": int(patch.patch_id in selected_ids),
            "selection_mode": selection_mode,
            "source_mapping_id": patch.source_mapping_id,
            "status": patch.status,
            "confidence": patch.confidence,
            "name": patch.name,
        }
        for patch in package.patches.values()
    ]


def compose_edits(
    package: Package,
    target_data: dict[str, bytes],
    edits: list[Edit],
    initial_buffers: dict[str, bytes | bytearray] | None = None,
    *,
    feature_id: str = "",
) -> tuple[dict[str, bytearray], list[dict[str, object]], dict[str, str]]:
    """Apply already validated edits to in-memory buffers.

    `target_data` is the verified clean baseline and remains the source for copy
    operations. `initial_buffers` may contain outputs from an earlier compositor
    stage, such as a font package. Every destination expectation is checked again
    against that staged state before any edit is accepted.
    """
    staged = initial_buffers or {}
    destination_ids = {
        item.destination_target_id for item in edits
    }
    mutable: dict[str, bytearray] = {}
    before_hashes: dict[str, str] = {}
    for target_id in destination_ids:
        target = package.targets[target_id]
        initial = bytes(staged.get(target_id, target_data[target_id]))
        if len(initial) != target.expected_size:
            raise PatchError(
                f"Staged size mismatch for {target_id}: "
                f"expected {target.expected_size}, found {len(initial)}"
            )
        mutable[target_id] = bytearray(initial)
        before_hashes[target_id] = data_sha256(initial)

    patch_rows: list[dict[str, object]] = []
    for edit in edits:
        data = mutable[edit.destination_target_id]
        old = verify_range(
            bytes(data),
            edit.destination_offset,
            edit.length,
            f"edit {edit.edit_id} staged destination",
        )
        replacement = replacement_for_edit(edit, package, target_data)
        if old == replacement:
            outcome = "already_satisfied"
        else:
            try:
                verify_expectation(
                    old,
                    edit.expected_hex,
                    edit.expected_sha256,
                    f"edit {edit.edit_id} staged destination",
                )
            except PatchError as exc:
                origin = f"feature {feature_id}, " if feature_id else ""
                raise PatchError(
                    f"Conflicting edit {edit.edit_id} "
                    f"({origin}patch {edit.patch_id}): {exc}"
                ) from exc
            data[edit.destination_offset : edit.destination_offset + edit.length] = replacement
            outcome = "applied"
        target = package.targets[edit.destination_target_id]
        patch = package.patches[edit.patch_id]
        group = package.groups[patch.group_id]
        patch_rows.append(
            {
                "package_id": package.package_id,
                "feature_id": feature_id,
                "group_id": group.group_id,
                "group_name": group.name,
                "patch_id": edit.patch_id,
                "source_mapping_id": patch.source_mapping_id,
                "edit_id": edit.edit_id,
                "target_id": target.target_id,
                "path": target.path.as_posix(),
                "offset": f"0x{edit.destination_offset:X}",
                "length": edit.length,
                "original_hex": old.hex().upper(),
                "new_hex": replacement.hex().upper(),
                "operation": edit.operation,
                "outcome": outcome,
                "reason": edit.reason,
            }
        )
    return mutable, patch_rows, before_hashes


def apply_package(
    package: Package,
    roots: dict[str, Path],
    target_data: dict[str, bytes],
    selected: list[str],
    edits: list[Edit],
    output_root: Path,
    output_root_text: str,
    log_directory: Path,
    log_directory_text: str,
    *,
    selection_mode: str,
) -> None:
    if output_root.exists():
        raise PatchError(f"Output root already exists: {output_root_text}")
    if log_directory.exists():
        raise PatchError(f"Log directory already exists: {log_directory_text}")
    for root_id, root in roots.items():
        try:
            output_root.relative_to(root)
        except ValueError:
            pass
        else:
            raise PatchError(f"Output root must not be inside input root {root_id}")

    mutable, patch_rows, before_hashes = compose_edits(
        package,
        target_data,
        edits,
    )

    stage = output_root.parent / f".{output_root.name}.staging_{uuid.uuid4().hex}"
    log_stage = log_directory.parent / f".{log_directory.name}.staging_{uuid.uuid4().hex}"
    if stage.exists() or log_stage.exists():
        raise PatchError("Unexpected staging collision")
    hash_rows: list[dict[str, object]] = []
    try:
        for target_id, data in mutable.items():
            target = package.targets[target_id]
            if len(data) != target.expected_size:
                raise PatchError(f"Size changed for {target_id}")
            destination = stage.joinpath(*target.path.parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
            hash_rows.append(
                {
                    "target_id": target_id,
                    "path": target.path.as_posix(),
                    "size": len(data),
                    "before_sha256": before_hashes[target_id],
                    "after_sha256": data_sha256(data),
                }
            )
        write_tsv(
            log_stage / "patch_log.tsv",
            [
                "package_id",
                "feature_id",
                "group_id",
                "group_name",
                "patch_id",
                "source_mapping_id",
                "edit_id",
                "target_id",
                "path",
                "offset",
                "length",
                "original_hex",
                "new_hex",
                "operation",
                "outcome",
                "reason",
            ],
            patch_rows,
        )
        write_tsv(
            log_stage / "patch_selection.tsv",
            [
                "group_id",
                "group_name",
                "group_enabled",
                "patch_id",
                "patch_enabled",
                "effective_selected",
                "selection_mode",
                "source_mapping_id",
                "status",
                "confidence",
                "name",
            ],
            patch_selection_rows(
                package,
                selected,
                selection_mode=selection_mode,
            ),
        )
        write_tsv(
            log_stage / "file_hashes.tsv",
            ["target_id", "path", "size", "before_sha256", "after_sha256"],
            hash_rows,
        )
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        write_tsv(
            log_stage / "run_summary.tsv",
            [
                "timestamp_utc",
                "schema_version",
                "package_id",
                "output_root",
                "log_directory",
                "group_count",
                "patch_count",
                "edit_count",
            ],
            [
                {
                    "timestamp_utc": timestamp,
                    "schema_version": BINARY_PATCHER_SCHEMA_VERSION,
                    "package_id": package.package_id,
                    "output_root": output_root_text.replace("\\", "/"),
                    "log_directory": log_directory_text.replace("\\", "/"),
                    "group_count": len(
                        {package.patches[patch_id].group_id for patch_id in selected}
                    ),
                    "patch_count": len(selected),
                    "edit_count": len(edits),
                }
            ],
        )
        os.replace(stage, output_root)
        try:
            os.replace(log_stage, log_directory)
        except Exception:
            shutil.rmtree(output_root)
            raise
    except Exception:
        if stage.exists():
            shutil.rmtree(stage)
        if log_stage.exists():
            shutil.rmtree(log_stage)
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate and apply declarative binary patcher patches.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("validate", "plan", "apply"):
        sub = subparsers.add_parser(command)
        sub.add_argument("--package", required=True)
        sub.add_argument("--root", action="append", default=[], metavar="ID=PATH")
        if command in {"plan", "apply"}:
            sub.add_argument("--patch", action="append", default=[])
            sub.add_argument("--enabled", action="store_true")
        if command == "apply":
            sub.add_argument("--output-root", required=True)
            sub.add_argument("--log-directory")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    workspace = PROJECT_PATHS.repository
    package_path = command_relative_path(args.package, "--package", workspace)
    if not package_path.is_dir():
        raise PatchError(f"Package directory does not exist: {args.package}")
    roots = parse_roots(args.root, workspace)
    package = load_package(package_path)
    target_data = verify_package_data(package, roots)

    if args.command == "validate":
        print(
            f"Validated {package.package_id}: "
            f"{len(package.targets)} targets, {len(package.groups)} groups, "
            f"{len(package.patches)} patches, "
            f"{len(package.edits)} edits"
        )
        return 0

    selected = selected_patch_ids(package, args.patch, args.enabled)
    edits = validate_selection(package, selected, for_apply=args.command == "apply")
    if args.command == "plan":
        compose_edits(package, target_data, edits)
        for row in patch_selection_rows(
            package,
            selected,
            selection_mode="enabled" if args.enabled else "explicit",
        ):
            print(
                f"{row['group_id']}\t{row['patch_id']}\t"
                f"group_enabled={row['group_enabled']}\t"
                f"patch_enabled={row['patch_enabled']}\t"
                f"effective_selected={row['effective_selected']}\t"
                f"{row['status']}\t{row['confidence']}\t{row['name']}"
            )
        print(f"Plan: {len(selected)} atomic patches, {len(edits)} edits; no files written")
        return 0

    output_root = command_relative_path(args.output_root, "--output-root", workspace)
    if args.log_directory:
        log_text = args.log_directory
    else:
        run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        logs_relative = PROJECT_PATHS.path("logs").relative_to(workspace).as_posix()
        log_text = f"{logs_relative}/na2_patcher/binary_patcher/{run_id}"
    log_directory = command_relative_path(log_text, "--log-directory", workspace)
    apply_package(
        package,
        roots,
        target_data,
        selected,
        edits,
        output_root,
        args.output_root,
        log_directory,
        log_text,
        selection_mode="enabled" if args.enabled else "explicit",
    )
    print(f"Applied {len(selected)} atomic patches ({len(edits)} edits)")
    print(f"Output: {args.output_root}")
    print(f"Log: {log_text}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PatchError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
