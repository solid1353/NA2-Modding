from __future__ import annotations

import csv
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from na228_builder.scripts.source_media import read_root_file

TARGET_FIELDS = [
    "target_id",
    "root_id",
    "role",
    "path",
    "expected_size",
    "expected_sha256",
]
ROLES = {"destination", "source", "both"}


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
    patches: dict[str, Patch]
    edits: list[Edit]


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


def load_targets(path: Path) -> dict[str, Target]:
    path = path.resolve()
    targets: dict[str, Target] = {}
    seen: set[str] = set()
    for row_number, row in enumerate(read_tsv(path, TARGET_FIELDS), 2):
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
    return targets


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
