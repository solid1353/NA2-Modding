from __future__ import annotations

import csv
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from .project_paths import ProjectPaths, load_project_paths, resolve_alias


MANIFEST_FIELDS = ["key", "value"]
ROOT_FIELDS = ["root_id", "path"]
FEATURE_FIELDS = [
    "feature_id",
    "enabled",
    "input",
    "expected_sha256",
    "reason",
]
MODULE_FIELDS = [
    "module_id",
    "order",
    "module",
    "input",
    "expected_sha256",
    "reason",
]
MODULE_TYPES = {
    "disc_identity",
    "external_translation",
    "binary_patcher",
    "string_patcher",
    "translation_importer",
    "texture_patcher",
}
BINARY_PATCHER_CONTROL_FILES = (
    "manifest.tsv",
    "targets.tsv",
    "groups.tsv",
    "patches.tsv",
    "edits.tsv",
)
STRING_PATCHER_CONTROL_FILES = ("strings.tsv",)
TRANSLATION_IMPORTER_CONTROL_FILES = ("manifest.tsv", "mappings.tsv")
TEXTURE_PATCHER_CONTROL_FILES = (
    "containers.tsv",
    "mappings.tsv",
    "strategies.tsv",
)
EXTERNAL_TRANSLATION_CONTROL_FILES = (
    "manifest.tsv",
    "pointer_refs.tsv",
)
FEATURE_CONTROL_FILES = (
    "manifest.tsv",
)


@dataclass(frozen=True)
class ProfileFeature:
    feature_id: str
    enabled: bool
    input_path: Path
    expected_sha256: str
    name: str
    description: str
    reason: str
    module_ids: tuple[str, ...]


@dataclass(frozen=True)
class ProfileModule:
    module_id: str
    order: int
    module: str
    input_path: Path
    expected_sha256: str
    reason: str
    feature_id: str
    enabled: bool


@dataclass(frozen=True)
class Profile:
    directory: Path
    manifest: dict[str, str]
    roots: dict[str, Path]
    features: tuple[ProfileFeature, ...]
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


def _profile_root_path(
    value: str, label: str, workspace: Path, project_paths: ProjectPaths
) -> Path:
    if value.startswith("@"):
        try:
            resolved = resolve_alias(value, project_paths)
        except (KeyError, ValueError) as exc:
            raise ValueError(f"{label} has an invalid project-root alias: {value!r}") from exc
        if not resolved.exists():
            raise FileNotFoundError(resolved)
        return resolved
    return _workspace_path(value, label, workspace)


def _tree_digest(path: Path, files: list[Path]) -> str:
    digest = hashlib.sha256()
    for item in sorted(files, key=lambda value: value.relative_to(path).as_posix()):
        relative = item.relative_to(path).as_posix().encode("utf-8")
        data_hash = hashlib.sha256(item.read_bytes()).hexdigest().upper().encode("ascii")
        digest.update(relative)
        digest.update(b"\0")
        digest.update(data_hash)
        digest.update(b"\n")
    return digest.hexdigest().upper()


def content_sha256(path: Path) -> str:
    """Hash one file or a complete directory tree deterministically."""
    if path.is_file():
        return hashlib.sha256(path.read_bytes()).hexdigest().upper()
    if not path.is_dir():
        raise FileNotFoundError(path)
    files = [item for item in path.rglob("*") if item.is_file()]
    if not files:
        raise ValueError(f"Cannot hash empty directory: {path}")
    return _tree_digest(path, files)


def _binary_patcher_content_files(path: Path) -> list[Path]:
    # Normalize once so Windows short/long path aliases cannot make blob paths
    # appear to sit outside the same package during digest calculation.
    path = path.resolve()
    files = [path / name for name in BINARY_PATCHER_CONTROL_FILES]
    missing = [item.name for item in files if not item.is_file()]
    if missing:
        raise FileNotFoundError(
            f"Binary-patcher module is missing canonical input files: {', '.join(missing)}"
        )

    edits_path = path / "edits.tsv"
    with edits_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fields = reader.fieldnames or []
        if "blob_path" not in fields:
            raise ValueError(f"{edits_path}: missing blob_path column")
        blob_paths = {
            (row.get("blob_path") or "").strip()
            for row in reader
            if (row.get("blob_path") or "").strip()
        }

    root = path
    for value in sorted(blob_paths):
        candidate = Path(value.replace("\\", "/"))
        if candidate.is_absolute() or ".." in candidate.parts:
            raise ValueError(
                f"{edits_path}: blob_path must be package-relative: {value!r}"
            )
        blob = (path / candidate).resolve()
        try:
            blob.relative_to(root)
        except ValueError as exc:
            raise ValueError(f"{edits_path}: blob_path escapes package: {value!r}") from exc
        if not blob.is_file():
            raise FileNotFoundError(blob)
        files.append(blob)
    return files


def _texture_patcher_content_files(path: Path) -> list[Path]:
    path = path.resolve()
    files = [path / name for name in TEXTURE_PATCHER_CONTROL_FILES]
    missing = [item.name for item in files if not item.is_file()]
    if missing:
        raise FileNotFoundError(
            f"Texture-patcher module is missing canonical input files: {', '.join(missing)}"
        )
    return files


def _string_patcher_content_files(path: Path) -> list[Path]:
    path = path.resolve()
    files = [path / name for name in STRING_PATCHER_CONTROL_FILES]
    missing = [item.name for item in files if not item.is_file()]
    if missing:
        raise FileNotFoundError(
            f"String-patcher module is missing canonical input files: {', '.join(missing)}"
        )
    return files


def _translation_importer_content_files(path: Path) -> list[Path]:
    path = path.resolve()
    files = [path / name for name in TRANSLATION_IMPORTER_CONTROL_FILES]
    missing = [item.name for item in files if not item.is_file()]
    if missing:
        raise FileNotFoundError(
            "Translation-importer package is missing canonical input files: "
            + ", ".join(missing)
        )
    return files


def _external_translation_content_files(path: Path) -> list[Path]:
    path = path.resolve()
    files = [path / name for name in EXTERNAL_TRANSLATION_CONTROL_FILES]
    missing = [item.name for item in files if not item.is_file()]
    if missing:
        raise FileNotFoundError(
            "External-translation module is missing canonical input files: "
            + ", ".join(missing)
        )
    return files


def feature_content_sha256(path: Path) -> str:
    """Hash one reusable feature package's declarative inputs."""
    path = path.resolve()
    if not path.is_dir():
        raise FileNotFoundError(path)
    files = [path / name for name in FEATURE_CONTROL_FILES]
    missing = [item.name for item in files if not item.is_file()]
    if missing:
        raise FileNotFoundError(
            f"Feature package is missing canonical input files: {', '.join(missing)}"
        )
    return _tree_digest(path, files)


def module_content_sha256(path: Path, module_type: str) -> str:
    """Hash only executable module inputs, excluding adjacent documentation."""
    path = path.resolve()
    if module_type not in MODULE_TYPES:
        raise ValueError(f"Unsupported module type: {module_type!r}")
    if path.is_file():
        return content_sha256(path)
    if not path.is_dir():
        raise FileNotFoundError(path)
    if module_type == "binary_patcher":
        return _tree_digest(path, _binary_patcher_content_files(path))
    if module_type == "string_patcher":
        return _tree_digest(path, _string_patcher_content_files(path))
    if module_type == "translation_importer":
        return _tree_digest(path, _translation_importer_content_files(path))
    if module_type == "external_translation":
        return _tree_digest(path, _external_translation_content_files(path))
    if module_type == "texture_patcher":
        return _tree_digest(path, _texture_patcher_content_files(path))
    return content_sha256(path)


def load_profile(directory: Path, workspace: Path) -> Profile:
    workspace = workspace.resolve()
    directory = directory.resolve()
    try:
        directory.relative_to(workspace)
    except ValueError as exc:
        raise ValueError(f"Profile must be inside the repository: {directory}") from exc

    manifest_rows = _read_tsv(directory / "manifest.tsv", MANIFEST_FIELDS)
    profile_manifest = {row["key"]: row["value"] for row in manifest_rows}
    if len(profile_manifest) != len(manifest_rows):
        raise ValueError("manifest.tsv contains duplicate keys")
    if profile_manifest.get("schema_version") != "2":
        raise ValueError("Profile schema_version must be 2")
    if not profile_manifest.get("profile_id"):
        raise ValueError("Profile manifest requires profile_id")

    root_rows = _read_tsv(directory / "roots.tsv", ROOT_FIELDS)
    roots: dict[str, Path] = {}
    project_paths: ProjectPaths | None = None
    for row in root_rows:
        root_id = row["root_id"]
        if not root_id or root_id in roots:
            raise ValueError(f"Duplicate or empty profile root_id: {root_id!r}")
        if row["path"].startswith("@"):
            if project_paths is None:
                project_paths = load_project_paths(workspace)
            root = _profile_root_path(
                row["path"], f"root {root_id}", workspace, project_paths
            )
        else:
            root = _workspace_path(row["path"], f"root {root_id}", workspace)
        if not root.exists():
            raise FileNotFoundError(root)
        roots[root_id] = root

    feature_rows = _read_tsv(directory / "features.tsv", FEATURE_FIELDS)
    feature_definitions: list[dict[str, object]] = []
    feature_ids: set[str] = set()
    for row in feature_rows:
        feature_id = row["feature_id"]
        if (
            not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", feature_id)
            or feature_id in feature_ids
        ):
            raise ValueError(f"Duplicate or invalid feature_id: {feature_id!r}")
        feature_ids.add(feature_id)
        if row["enabled"] not in {"0", "1"}:
            raise ValueError(f"Feature {feature_id}: enabled must be 0 or 1")
        input_path = _workspace_path(
            row["input"], f"feature {feature_id} input", workspace
        )
        if not input_path.is_dir():
            raise FileNotFoundError(input_path)
        expected = row["expected_sha256"].upper()
        if len(expected) != 64 or any(char not in "0123456789ABCDEF" for char in expected):
            raise ValueError(
                f"Feature {feature_id}: expected_sha256 must be 64 hex digits"
            )
        feature_definitions.append(
            {
                "feature_id": feature_id,
                "enabled": row["enabled"] == "1",
                "input_path": input_path,
                "expected_sha256": expected,
                "reason": row["reason"],
            }
        )
    if not feature_definitions:
        raise ValueError("Profile has no features")
    if not any(bool(feature["enabled"]) for feature in feature_definitions):
        raise ValueError("Profile has no enabled features")

    module_rows = _read_tsv(directory / "modules.tsv", MODULE_FIELDS)
    module_definitions: dict[str, dict[str, object]] = {}
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
        module_definitions[module_id] = {
            "module_id": module_id,
            "order": order,
            "module": module_type,
            "input_path": input_path,
            "expected_sha256": expected,
            "reason": row["reason"],
        }

    feature_packages: dict[str, dict[str, object]] = {}
    for definition in feature_definitions:
        feature_id = str(definition["feature_id"])
        input_path = definition["input_path"]
        assert isinstance(input_path, Path)
        manifest_rows = _read_tsv(input_path / "manifest.tsv", MANIFEST_FIELDS)
        feature_manifest = {row["key"]: row["value"] for row in manifest_rows}
        if len(feature_manifest) != len(manifest_rows):
            raise ValueError(f"Feature {feature_id}: manifest.tsv has duplicate keys")
        if feature_manifest.get("schema_version") != "1":
            raise ValueError(f"Feature {feature_id}: schema_version must be 1")
        if feature_manifest.get("feature_id") != feature_id:
            raise ValueError(
                f"Feature package ID {feature_manifest.get('feature_id')!r} does not match "
                f"profile feature {feature_id!r}"
            )
        if not feature_manifest.get("name"):
            raise ValueError(f"Feature {feature_id}: name is empty")
        if bool(definition["enabled"]):
            actual = feature_content_sha256(input_path)
            expected = str(definition["expected_sha256"])
            if actual != expected:
                raise ValueError(
                    f"Feature {feature_id}: input SHA-256 {actual} does not match {expected}"
                )
        feature_packages[feature_id] = {
            **definition,
            "name": feature_manifest["name"],
            "description": feature_manifest.get("description", ""),
        }

    modules: list[ProfileModule] = []
    module_ids_by_feature: dict[str, list[str]] = {
        feature_id: [] for feature_id in feature_packages
    }
    for module_id, definition in module_definitions.items():
        module_input = definition["input_path"]
        assert isinstance(module_input, Path)
        owners: list[tuple[str, Path]] = []
        for feature_id, feature in feature_packages.items():
            feature_input = feature["input_path"]
            assert isinstance(feature_input, Path)
            try:
                relative = module_input.relative_to(feature_input)
            except ValueError:
                continue
            if relative.parts:
                owners.append((feature_id, relative))
        if len(owners) != 1:
            raise ValueError(
                f"Module {module_id}: input must belong to exactly one feature directory"
            )
        feature_id, relative = owners[0]
        module_type = str(definition["module"])
        if relative.parts[0] != module_type:
            raise ValueError(
                f"Module {module_id}: first feature subfolder must match module type "
                f"{module_type!r}, found {relative.parts[0]!r}"
            )
        enabled = bool(feature_packages[feature_id]["enabled"])
        if enabled:
            actual = module_content_sha256(
                definition["input_path"],  # type: ignore[arg-type]
                module_type,
            )
            expected = str(definition["expected_sha256"])
            if actual != expected:
                raise ValueError(
                    f"Module {module_id}: input SHA-256 {actual} does not match {expected}"
                )
        module_ids_by_feature[feature_id].append(module_id)
        modules.append(
            ProfileModule(
                **definition,  # type: ignore[arg-type]
                feature_id=feature_id,
                enabled=enabled,
            )
        )

    features: list[ProfileFeature] = []
    for feature_id, definition in feature_packages.items():
        module_ids = tuple(module_ids_by_feature[feature_id])
        if not module_ids:
            raise ValueError(f"Feature {feature_id} owns no profile modules")
        features.append(
            ProfileFeature(
                feature_id=feature_id,
                enabled=bool(definition["enabled"]),
                input_path=definition["input_path"],  # type: ignore[arg-type]
                expected_sha256=str(definition["expected_sha256"]),
                name=str(definition["name"]),
                description=str(definition["description"]),
                reason=str(definition["reason"]),
                module_ids=module_ids,
            )
        )

    if not any(module.enabled for module in modules):
        raise ValueError("Profile has no enabled modules")
    return Profile(
        directory=directory,
        manifest=profile_manifest,
        roots=roots,
        features=tuple(features),
        modules=tuple(sorted(modules, key=lambda item: item.order)),
    )
