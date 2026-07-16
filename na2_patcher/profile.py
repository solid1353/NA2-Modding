from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path


MANIFEST_FIELDS = ["key", "value"]
ROOT_FIELDS = ["root_id", "path"]
MODULE_FIELDS = [
    "module_id",
    "order",
    "enabled",
    "module",
    "input",
    "expected_sha256",
    "selection",
    "reason",
]
MODULE_TYPES = {"zip_overlay", "raw_binary", "translation"}


@dataclass(frozen=True)
class ProfileModule:
    module_id: str
    order: int
    enabled: bool
    module: str
    input_path: Path
    expected_sha256: str
    selection: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class Profile:
    directory: Path
    manifest: dict[str, str]
    roots: dict[str, Path]
    modules: tuple[ProfileModule, ...]


def _read_tsv(path: Path, fields: list[str]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != fields:
            raise ValueError(
                f"{path}: expected columns " + "\t".join(fields)
            )
        return [
            {key: (value or "").strip() for key, value in row.items()}
            for row in reader
            if any((value or "").strip() for value in row.values())
        ]


def _workspace_path(value: str, label: str, workspace: Path) -> Path:
    candidate = Path(value)
    if not value or candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"{label} must be a repository-relative path: {value!r}")
    resolved = (workspace / candidate).resolve()
    try:
        resolved.relative_to(workspace)
    except ValueError as exc:
        raise ValueError(f"{label} escapes the repository: {value!r}") from exc
    return resolved


def content_sha256(path: Path) -> str:
    """Hash one file or a directory tree deterministically."""
    if path.is_file():
        return hashlib.sha256(path.read_bytes()).hexdigest().upper()
    if not path.is_dir():
        raise FileNotFoundError(path)
    digest = hashlib.sha256()
    files = sorted(item for item in path.rglob("*") if item.is_file())
    if not files:
        raise ValueError(f"Cannot hash empty directory: {path}")
    for item in files:
        relative = item.relative_to(path).as_posix().encode("utf-8")
        data_hash = hashlib.sha256(item.read_bytes()).hexdigest().upper().encode("ascii")
        digest.update(relative)
        digest.update(b"\0")
        digest.update(data_hash)
        digest.update(b"\n")
    return digest.hexdigest().upper()


def load_profile(directory: Path, workspace: Path) -> Profile:
    workspace = workspace.resolve()
    directory = directory.resolve()
    try:
        directory.relative_to(workspace)
    except ValueError as exc:
        raise ValueError(f"Profile must be inside the repository: {directory}") from exc

    manifest_rows = _read_tsv(directory / "manifest.tsv", MANIFEST_FIELDS)
    manifest = {row["key"]: row["value"] for row in manifest_rows}
    if len(manifest) != len(manifest_rows):
        raise ValueError("manifest.tsv contains duplicate keys")
    if manifest.get("schema_version") != "1":
        raise ValueError("Profile schema_version must be 1")
    if not manifest.get("profile_id"):
        raise ValueError("Profile manifest requires profile_id")

    root_rows = _read_tsv(directory / "roots.tsv", ROOT_FIELDS)
    roots: dict[str, Path] = {}
    for row in root_rows:
        root_id = row["root_id"]
        if not root_id or root_id in roots:
            raise ValueError(f"Duplicate or empty profile root_id: {root_id!r}")
        root = _workspace_path(row["path"], f"root {root_id}", workspace)
        if not root.exists():
            raise FileNotFoundError(root)
        roots[root_id] = root

    module_rows = _read_tsv(directory / "modules.tsv", MODULE_FIELDS)
    modules: list[ProfileModule] = []
    seen_ids: set[str] = set()
    seen_orders: set[int] = set()
    for row in module_rows:
        module_id = row["module_id"]
        if not module_id or module_id in seen_ids:
            raise ValueError(f"Duplicate or empty module_id: {module_id!r}")
        seen_ids.add(module_id)
        try:
            order = int(row["order"], 10)
        except ValueError as exc:
            raise ValueError(f"Module {module_id}: invalid order") from exc
        if order < 0 or order in seen_orders:
            raise ValueError(f"Module {module_id}: order must be unique and nonnegative")
        seen_orders.add(order)
        if row["enabled"] not in {"0", "1"}:
            raise ValueError(f"Module {module_id}: enabled must be 0 or 1")
        module_type = row["module"]
        if module_type not in MODULE_TYPES:
            raise ValueError(f"Module {module_id}: unsupported module {module_type!r}")
        input_path = _workspace_path(
            row["input"], f"module {module_id} input", workspace
        )
        if not input_path.exists():
            raise FileNotFoundError(input_path)
        expected = row["expected_sha256"].upper()
        if len(expected) != 64 or any(char not in "0123456789ABCDEF" for char in expected):
            raise ValueError(f"Module {module_id}: expected_sha256 must be 64 hex digits")
        actual = content_sha256(input_path)
        if actual != expected:
            raise ValueError(
                f"Module {module_id}: input SHA-256 {actual} does not match {expected}"
            )
        selection = tuple(
            item.strip() for item in row["selection"].split(",") if item.strip()
        )
        modules.append(
            ProfileModule(
                module_id=module_id,
                order=order,
                enabled=row["enabled"] == "1",
                module=module_type,
                input_path=input_path,
                expected_sha256=expected,
                selection=selection,
                reason=row["reason"],
            )
        )

    if not any(module.enabled for module in modules):
        raise ValueError("Profile has no enabled modules")
    return Profile(
        directory=directory,
        manifest=manifest,
        roots=roots,
        modules=tuple(sorted(modules, key=lambda item: item.order)),
    )
