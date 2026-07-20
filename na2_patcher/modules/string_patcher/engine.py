from __future__ import annotations

import codecs
import csv
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from ..binary_patcher import engine as binary_patcher


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
    if not rows:
        raise binary_patcher.PatchError(f"{path}: contains no string patches")

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
        if spec.default_enabled and spec.status != "runtime_proven":
            raise binary_patcher.PatchError(
                f"{path} row {row_number}: default-enabled strings must be runtime_proven"
            )
        if not spec.reason:
            raise binary_patcher.PatchError(
                f"{path} row {row_number}: reason is empty"
            )
        _encode_slot(spec.expected_text, spec, "expected_text")
        _encode_slot(spec.replacement_text, spec, "replacement_text")
        specs.append(spec)
    return tuple(specs)


def build_binary_package(directory: Path) -> binary_patcher.Package:
    directory = directory.resolve()
    specs = load_specs(directory)
    targets: dict[str, binary_patcher.Target] = {}
    target_ids: dict[tuple[str, str], str] = {}
    groups: dict[str, binary_patcher.Group] = {}
    patches: dict[str, binary_patcher.Patch] = {}
    edits: list[binary_patcher.Edit] = []

    for spec in specs:
        target_key = (spec.root_id, spec.path)
        target_id = target_ids.get(target_key)
        if target_id is None:
            target_id = f"string_target_{len(target_ids) + 1:03d}"
            target_ids[target_key] = target_id
            targets[target_id] = binary_patcher.Target(
                target_id=target_id,
                root_id=spec.root_id,
                role="destination",
                path=PurePosixPath(spec.path),
                expected_size=spec.expected_size,
                expected_sha256=spec.expected_sha256,
            )
        else:
            target = targets[target_id]
            if (
                target.expected_size != spec.expected_size
                or target.expected_sha256 != spec.expected_sha256
            ):
                raise binary_patcher.PatchError(
                    f"{spec.string_id}: inconsistent identity for target "
                    f"{spec.root_id}:{spec.path}"
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

    try:
        evidence_path = (directory / "README.md").relative_to(
            binary_patcher.PROJECT_PATHS.repository
        ).as_posix()
    except ValueError:
        evidence_path = ""

    return binary_patcher.Package(
        directory=directory,
        manifest={
            "schema_version": "2",
            "package_id": "string_patcher",
            "package_version": "1",
            "game": "NA2",
            "description": "String declarations compiled through binary_patcher.",
            "evidence_path": evidence_path,
        },
        targets=targets,
        groups=groups,
        patches=patches,
        edits=edits,
    )
