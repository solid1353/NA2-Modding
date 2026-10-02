from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from ...common import SYMBOL_PATTERN, parse_int, read_tsv, sha256_hex
from ...orchestration.source_media import read_root_file

TARGET_FIELDS = [
    "target_id",
    "root_id",
    "path",
    "expected_size",
    "expected_sha256",
]


class PatchError(RuntimeError):
    pass


@dataclass(frozen=True)
class Target:
    target_id: str
    root_id: str
    path: PurePosixPath
    expected_size: int
    expected_sha256: str


@dataclass(frozen=True)
class Patch:
    patch_id: str
    group_id: str
    evidence_id: str


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
    reason: str
    expected_sha256: str = ""
    replacement_hex: str = ""
    source_target_id: str = ""
    source_offset: int | None = None
    blob_path: PurePosixPath | None = None
    blob_offset: int | None = None
    blob_sha256: str = ""
    fill_hex: str = ""


@dataclass
class Package:
    directory: Path
    package_id: str
    targets: dict[str, Target]
    patches: dict[str, Patch]
    edits: list[Edit]


def normalized_hex(value: str, label: str, *, allow_empty: bool = True) -> str:
    compact = "".join(value.split()).upper()
    if not compact and allow_empty:
        return ""
    if not compact:
        raise PatchError(f"{label} is empty")
    if len(compact) % 2 or not re.fullmatch(r"[0-9A-F]+", compact):
        raise PatchError(f"{label} is not even-length hexadecimal data")
    return compact


def normalized_sha256(value: str, label: str) -> str:
    result = value.strip().upper()
    if not re.fullmatch(r"[0-9A-F]{64}", result):
        raise PatchError(f"{label} is not a SHA-256 value")
    return result


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


def load_targets(path: Path) -> dict[str, Target]:
    targets: dict[str, Target] = {}
    for row_number, row in enumerate(read_tsv(path.resolve(), TARGET_FIELDS), 2):
        label = f"targets.tsv row {row_number}"
        target_id = row["target_id"]
        if not SYMBOL_PATTERN.fullmatch(target_id) or target_id in targets:
            raise PatchError(f"{label}: invalid or duplicate target_id {target_id!r}")
        root_id = row["root_id"]
        if not re.fullmatch(r"[a-z][a-z0-9_-]*", root_id):
            raise PatchError(f"{label}: invalid root_id")
        targets[target_id] = Target(
            target_id=target_id,
            root_id=root_id,
            path=relative_posix(row["path"], f"target {target_id} path"),
            expected_size=parse_int(row["expected_size"], f"{label} expected_size"),
            expected_sha256=normalized_sha256(
                row["expected_sha256"], f"target {target_id} expected_sha256"
            ),
        )
    return targets


def verify_target(target: Target, roots: dict[str, Path]) -> bytes:
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
    actual_hash = sha256_hex(data)
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
    if expected_sha and sha256_hex(data) != expected_sha:
        raise PatchError(
            f"{label} SHA-256 expected {expected_sha}, found {sha256_hex(data)}"
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
        return verify_range(
            source,
            edit.source_offset,
            edit.length,
            f"edit {edit.edit_id} source",
        )
    assert edit.blob_path is not None and edit.blob_offset is not None
    blob_file = package.directory.joinpath(*edit.blob_path.parts)
    if not blob_file.is_file():
        raise PatchError(f"edit {edit.edit_id}: blob is missing: {edit.blob_path}")
    blob = blob_file.read_bytes()
    if sha256_hex(blob) != edit.blob_sha256:
        raise PatchError(f"edit {edit.edit_id}: blob SHA-256 mismatch")
    return verify_range(blob, edit.blob_offset, edit.length, f"edit {edit.edit_id} blob")


def verify_package_data(package: Package, roots: dict[str, Path]) -> dict[str, bytes]:
    used_roots = {target.root_id for target in package.targets.values()}
    missing = sorted(used_roots - roots.keys())
    if missing:
        raise PatchError("Missing root bindings: " + ", ".join(missing))
    return {
        target_id: verify_target(target, roots)
        for target_id, target in package.targets.items()
    }


def ordered_edits(package: Package) -> list[Edit]:
    if not package.patches:
        raise PatchError("Package contains no patches")
    unknown = sorted({edit.patch_id for edit in package.edits} - package.patches.keys())
    if unknown:
        raise PatchError("Edits reference unknown patches: " + ", ".join(unknown))
    patch_order = {
        patch_id: index for index, patch_id in enumerate(package.patches)
    }
    return sorted(
        package.edits,
        key=lambda item: (
            item.destination_target_id,
            item.destination_offset,
            patch_order[item.patch_id],
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


def patch_inventory_rows(package: Package) -> list[dict[str, object]]:
    return [
        {
            "group_id": patch.group_id,
            "patch_id": patch.patch_id,
            "evidence_id": patch.evidence_id,
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
    """Apply edits to in-memory buffers.

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
        before_hashes[target_id] = sha256_hex(initial)

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
        if len(replacement) != edit.length:
            raise PatchError(f"edit {edit.edit_id}: replacement length mismatch")
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
        patch_rows.append(
            {
                "package_id": package.package_id,
                "feature_id": feature_id,
                "group_id": patch.group_id,
                "patch_id": edit.patch_id,
                "evidence_id": patch.evidence_id,
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
