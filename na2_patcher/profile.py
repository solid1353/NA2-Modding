from __future__ import annotations

import csv
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from .project_paths import ProjectPaths, load_project_paths, resolve_alias


ROOT_FIELDS = ["root_id", "path"]
FEATURE_FIELDS = ["feature_id", "expected_sha256"]
IMAGE_FIELDS = ["source_boot_path", "output_boot_path", "system_cnf_path"]
MODULE_TYPE_ORDER = (
    "translation_importer",
    "string_patcher",
    "texture_patcher",
    "binary_patcher",
)
MODULE_TYPES = frozenset(MODULE_TYPE_ORDER)
BINARY_PATCHER_CONTROL_FILES = (
    "targets.tsv",
    "groups.tsv",
    "patches.tsv",
    "edits.tsv",
)
STRING_PATCHER_CONTROL_FILES = ("strings.tsv",)
STRING_PATCHER_EXTERNAL_FILES = ("config.tsv", "pointer_refs.tsv")
TRANSLATION_IMPORTER_CONTROL_FILES = ("config.tsv", "mappings.tsv")
TEXTURE_PATCHER_CONTROL_FILES = (
    "containers.tsv",
    "mappings.tsv",
    "strategies.tsv",
)


@dataclass(frozen=True)
class ProfileImage:
    source_boot_path: str
    output_boot_path: str
    system_cnf_path: str


@dataclass(frozen=True)
class ProfileFeature:
    feature_id: str
    input_path: Path
    expected_sha256: str
    module_ids: tuple[str, ...]


@dataclass(frozen=True)
class ProfileModule:
    module_id: str
    order: int
    module: str
    input_path: Path
    input_sha256: str
    feature_id: str


@dataclass(frozen=True)
class Profile:
    directory: Path
    profile_id: str
    roots: dict[str, Path]
    image: ProfileImage
    features: tuple[ProfileFeature, ...]
    modules: tuple[ProfileModule, ...]


def _read_tsv(path: Path, fields: list[str]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != fields:
            raise ValueError(f"{path}: expected columns " + "\t".join(fields))
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
            raise ValueError(
                f"{label} has an invalid project-root alias: {value!r}"
            ) from exc
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


def _required_files(path: Path, names: tuple[str, ...], label: str) -> list[Path]:
    files = [path / name for name in names]
    missing = [item.name for item in files if not item.is_file()]
    if missing:
        raise FileNotFoundError(f"{label} is missing canonical inputs: {', '.join(missing)}")
    return files


def _binary_patcher_content_files(path: Path) -> list[Path]:
    path = path.resolve()
    files = _required_files(
        path, BINARY_PATCHER_CONTROL_FILES, "Binary-patcher module"
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
    for value in sorted(blob_paths):
        candidate = Path(value.replace("\\", "/"))
        if candidate.is_absolute() or ".." in candidate.parts:
            raise ValueError(
                f"{edits_path}: blob_path must be package-relative: {value!r}"
            )
        blob = (path / candidate).resolve()
        try:
            blob.relative_to(path)
        except ValueError as exc:
            raise ValueError(f"{edits_path}: blob_path escapes package: {value!r}") from exc
        if not blob.is_file():
            raise FileNotFoundError(blob)
        files.append(blob)
    return files


def _module_content_files(path: Path, module_type: str) -> list[Path]:
    path = path.resolve()
    if module_type == "binary_patcher":
        return _binary_patcher_content_files(path)
    if module_type == "string_patcher":
        files = _required_files(
            path, STRING_PATCHER_CONTROL_FILES, "string_patcher module"
        )
        external = [path / name for name in STRING_PATCHER_EXTERNAL_FILES]
        if any(item.exists() for item in external):
            missing = [item.name for item in external if not item.is_file()]
            if missing:
                raise FileNotFoundError(
                    "string_patcher module has an incomplete external-string "
                    f"declaration: {', '.join(missing)}"
                )
            files.extend(external)
        return files
    names = {
        "translation_importer": TRANSLATION_IMPORTER_CONTROL_FILES,
        "texture_patcher": TEXTURE_PATCHER_CONTROL_FILES,
    }[module_type]
    return _required_files(path, names, f"{module_type} module")


def _discover_module_directories(path: Path) -> list[tuple[str, Path]]:
    path = path.resolve()
    if not path.is_dir():
        raise FileNotFoundError(path)
    readme = path / "README.md"
    if not readme.is_file():
        raise FileNotFoundError(f"Feature package is missing README.md: {path}")
    unexpected_files = sorted(
        item.name for item in path.iterdir() if item.is_file() and item.name != "README.md"
    )
    if unexpected_files:
        raise ValueError(
            f"Feature root contains unsupported files: {', '.join(unexpected_files)}"
        )
    directories = {item.name: item for item in path.iterdir() if item.is_dir()}
    unknown = sorted(directories.keys() - MODULE_TYPES)
    if unknown:
        raise ValueError(f"Feature contains unknown module directories: {', '.join(unknown)}")
    result = [
        (module_type, directories[module_type])
        for module_type in MODULE_TYPE_ORDER
        if module_type in directories
    ]
    if not result:
        raise ValueError(f"Feature owns no module directories: {path}")
    return result


def module_content_sha256(path: Path, module_type: str) -> str:
    """Hash one module's canonical executable inputs."""
    path = path.resolve()
    if module_type not in MODULE_TYPES:
        raise ValueError(f"Unsupported module type: {module_type!r}")
    if not path.is_dir():
        raise FileNotFoundError(path)
    return _tree_digest(path, _module_content_files(path, module_type))


def feature_content_sha256(path: Path) -> str:
    """Hash every canonical executable input owned by one feature."""
    path = path.resolve()
    files: list[Path] = []
    for module_type, module_path in _discover_module_directories(path):
        files.extend(_module_content_files(module_path, module_type))
    return _tree_digest(path, files)


def load_profile(directory: Path, workspace: Path) -> Profile:
    workspace = workspace.resolve()
    directory = directory.resolve()
    try:
        directory.relative_to(workspace)
    except ValueError as exc:
        raise ValueError(f"Profile must be inside the repository: {directory}") from exc
    profile_id = directory.name
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", profile_id):
        raise ValueError(f"Invalid profile directory name: {profile_id!r}")

    project_paths = load_project_paths(workspace)
    image_rows = _read_tsv(directory / "image.tsv", IMAGE_FIELDS)
    if len(image_rows) != 1:
        raise ValueError("Profile image.tsv must contain exactly one image row")
    image_row = image_rows[0]
    image = ProfileImage(
        source_boot_path=image_row["source_boot_path"],
        output_boot_path=image_row["output_boot_path"],
        system_cnf_path=image_row["system_cnf_path"],
    )
    from .image_assembler.iso9660 import normalize_iso_path

    for label, value in (
        ("source_boot_path", image.source_boot_path),
        ("output_boot_path", image.output_boot_path),
        ("system_cnf_path", image.system_cnf_path),
    ):
        if normalize_iso_path(value) != value:
            raise ValueError(f"Profile image {label} must be normalized: {value!r}")
    if image.source_boot_path == image.output_boot_path:
        raise ValueError("Profile image boot paths must differ")
    if len(image.source_boot_path.encode("ascii")) != len(
        image.output_boot_path.encode("ascii")
    ):
        raise ValueError("Profile image boot paths must have equal byte lengths")

    roots: dict[str, Path] = {}
    for row in _read_tsv(directory / "roots.tsv", ROOT_FIELDS):
        root_id = row["root_id"]
        if not root_id or root_id in roots:
            raise ValueError(f"Duplicate or empty profile root_id: {root_id!r}")
        root = _profile_root_path(
            row["path"], f"root {root_id}", workspace, project_paths
        )
        if not root.exists():
            raise FileNotFoundError(root)
        roots[root_id] = root

    feature_rows = _read_tsv(directory / "features.tsv", FEATURE_FIELDS)
    if not feature_rows:
        raise ValueError("Profile has no enabled features")
    features_root = project_paths.path("features").resolve()
    features: list[ProfileFeature] = []
    modules: list[ProfileModule] = []
    seen_features: set[str] = set()
    for row in feature_rows:
        feature_id = row["feature_id"]
        if (
            not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", feature_id)
            or feature_id in seen_features
        ):
            raise ValueError(f"Duplicate or invalid feature_id: {feature_id!r}")
        seen_features.add(feature_id)
        feature_path = (features_root / feature_id).resolve()
        try:
            feature_path.relative_to(features_root)
        except ValueError as exc:
            raise ValueError(f"Feature path escapes configured root: {feature_id}") from exc
        expected = row["expected_sha256"].upper()
        if len(expected) != 64 or any(char not in "0123456789ABCDEF" for char in expected):
            raise ValueError(f"Feature {feature_id}: expected_sha256 must be 64 hex digits")
        actual = feature_content_sha256(feature_path)
        if actual != expected:
            raise ValueError(
                f"Feature {feature_id}: input SHA-256 {actual} does not match {expected}"
            )

        module_ids: list[str] = []
        for module_type, module_path in _discover_module_directories(feature_path):
            module_id = f"{feature_id}.{module_type}"
            module_ids.append(module_id)
            modules.append(
                ProfileModule(
                    module_id=module_id,
                    order=len(modules) + 1,
                    module=module_type,
                    input_path=module_path,
                    input_sha256=module_content_sha256(module_path, module_type),
                    feature_id=feature_id,
                )
            )
        features.append(
            ProfileFeature(
                feature_id=feature_id,
                input_path=feature_path,
                expected_sha256=expected,
                module_ids=tuple(module_ids),
            )
        )

    return Profile(
        directory=directory,
        profile_id=profile_id,
        roots=roots,
        image=image,
        features=tuple(features),
        modules=tuple(modules),
    )
