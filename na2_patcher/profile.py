from __future__ import annotations

import codecs
import csv
import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path

from .project_paths import ProjectPaths, load_project_paths, resolve_alias


ROOT_FIELDS = ["root_id", "path"]
FEATURE_FIELDS = ["feature_id", "expected_sha256", "bypass_check"]
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
TRANSLATION_IMPORTER_CONTROL_FILES = ("mappings.tsv",)
TEXTURE_PATCHER_CONTROL_FILES = (
    "containers.tsv",
    "mappings.tsv",
    "strategies.tsv",
)


@dataclass(frozen=True)
class ProfileIdentity:
    source_boot_path: str
    output_boot_path: str
    system_cnf_path: str
    memory_card_title_offset: int
    memory_card_title_capacity: int
    memory_card_title_encoding: str
    source_memory_card_title: str
    output_memory_card_title: str
    imported_game_title: str
    output_game_title: str
    game_title_mapping_count: int
    game_title_occurrence_count: int


@dataclass(frozen=True)
class ProfileFeature:
    feature_id: str
    input_path: Path
    expected_sha256: str
    actual_sha256: str
    bypass_check: bool
    module_ids: tuple[str, ...]

    @property
    def hash_check_bypassed(self) -> bool:
        return self.bypass_check


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
    identity: ProfileIdentity
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


def _identity_object(value: object, keys: set[str], label: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != keys:
        expected = ", ".join(sorted(keys))
        raise ValueError(f"Profile identity {label} keys must be: {expected}")
    return value


def _identity_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"Profile identity {label} must be non-empty text")
    return value


def _identity_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"Profile identity {label} must be an integer")
    return value


def _read_identity(path: Path) -> ProfileIdentity:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Profile identity is not valid JSON: {path}") from exc
    root = _identity_object(
        data, {"schema_version", "image", "memory_card", "game_title"}, "root"
    )
    if root["schema_version"] != 1:
        raise ValueError("Unsupported profile identity schema_version")
    image = _identity_object(
        root["image"],
        {"source_boot_path", "output_boot_path", "system_cnf_path"},
        "image",
    )
    memory = _identity_object(
        root["memory_card"],
        {"title_offset", "title_capacity", "title_encoding", "source_title", "output_title"},
        "memory_card",
    )
    title = _identity_object(
        root["game_title"],
        {"imported", "output", "expected_mapping_count", "expected_occurrence_count"},
        "game_title",
    )
    return ProfileIdentity(
        source_boot_path=_identity_text(image["source_boot_path"], "image.source_boot_path"),
        output_boot_path=_identity_text(image["output_boot_path"], "image.output_boot_path"),
        system_cnf_path=_identity_text(image["system_cnf_path"], "image.system_cnf_path"),
        memory_card_title_offset=_identity_int(
            memory["title_offset"], "memory_card.title_offset"
        ),
        memory_card_title_capacity=_identity_int(
            memory["title_capacity"], "memory_card.title_capacity"
        ),
        memory_card_title_encoding=_identity_text(
            memory["title_encoding"], "memory_card.title_encoding"
        ),
        source_memory_card_title=_identity_text(
            memory["source_title"], "memory_card.source_title"
        ),
        output_memory_card_title=_identity_text(
            memory["output_title"], "memory_card.output_title"
        ),
        imported_game_title=_identity_text(title["imported"], "game_title.imported"),
        output_game_title=_identity_text(title["output"], "game_title.output"),
        game_title_mapping_count=_identity_int(
            title["expected_mapping_count"], "game_title.expected_mapping_count"
        ),
        game_title_occurrence_count=_identity_int(
            title["expected_occurrence_count"], "game_title.expected_occurrence_count"
        ),
    )


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
        return _required_files(
            path, STRING_PATCHER_CONTROL_FILES, "string_patcher module"
        )
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


def profile_resource_files(profile: Profile) -> tuple[Path, ...]:
    """Return the exact structural and hash-covered files needed to load a profile."""
    files = [
        profile.directory / "roots.tsv",
        profile.directory / "features.tsv",
        profile.directory / "identity.json",
    ]
    files.extend(feature.input_path / "README.md" for feature in profile.features)
    for module in profile.modules:
        files.extend(_module_content_files(module.input_path, module.module))
    return tuple(sorted(set(files), key=lambda path: path.as_posix()))


def profile_resource_files(profile: Profile) -> tuple[Path, ...]:
    """Return the exact structural and hash-covered files needed to load a profile."""
    files = [
        profile.directory / "roots.tsv",
        profile.directory / "features.tsv",
        profile.directory / "identity.json",
    ]
    files.extend(feature.input_path / "README.md" for feature in profile.features)
    for module in profile.modules:
        files.extend(_module_content_files(module.input_path, module.module))
    return tuple(sorted(set(files), key=lambda path: path.as_posix()))


def load_profile(
    directory: Path,
    workspace: Path,
    *,
    root_overrides: Mapping[str, Path] | None = None,
) -> Profile:
    workspace = workspace.resolve()
    directory = directory.resolve()
    try:
        directory.relative_to(workspace)
    except ValueError as exc:
        raise ValueError(f"Profile must be inside the repository: {directory}") from exc
    profile_id = directory.name
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", profile_id):
        raise ValueError(f"Invalid profile directory name: {profile_id!r}")

    project_paths = load_project_paths(workspace, allow_missing=True)
    identity = _read_identity(directory / "identity.json")
    memory_card_title_offset = identity.memory_card_title_offset
    memory_card_title_capacity = identity.memory_card_title_capacity
    game_title_mapping_count = identity.game_title_mapping_count
    game_title_occurrence_count = identity.game_title_occurrence_count
    if memory_card_title_offset < 0 or memory_card_title_capacity <= 0:
        raise ValueError(
            "Profile identity title offset must be non-negative and capacity positive"
        )
    if (
        game_title_mapping_count <= 0
        or game_title_occurrence_count < game_title_mapping_count
    ):
        raise ValueError("Profile identity game-title coverage is invalid")
    try:
        memory_card_title_encoding = codecs.lookup(identity.memory_card_title_encoding).name
    except LookupError as exc:
        raise ValueError("Profile identity has an unknown title encoding") from exc
    identity = replace(
        identity,
        memory_card_title_encoding=memory_card_title_encoding,
    )
    from .image_assembler.iso9660 import normalize_iso_path

    for label, value in (
        ("source_boot_path", identity.source_boot_path),
        ("output_boot_path", identity.output_boot_path),
        ("system_cnf_path", identity.system_cnf_path),
    ):
        if normalize_iso_path(value) != value:
            raise ValueError(f"Profile identity {label} must be normalized: {value!r}")
    if identity.source_boot_path == identity.output_boot_path:
        raise ValueError("Profile identity boot paths must differ")
    if len(identity.source_boot_path.encode("ascii")) != len(
        identity.output_boot_path.encode("ascii")
    ):
        raise ValueError("Profile identity boot paths must have equal byte lengths")
    for label, text in (
        ("source_memory_card_title", identity.source_memory_card_title),
        ("output_memory_card_title", identity.output_memory_card_title),
    ):
        if "\0" in text:
            raise ValueError(f"Profile identity {label} contains an embedded NUL")
        try:
            encoded = text.encode(identity.memory_card_title_encoding)
        except UnicodeEncodeError as exc:
            raise ValueError(
                f"Profile identity {label} is not encodable as "
                f"{identity.memory_card_title_encoding}"
            ) from exc
        if len(encoded) >= identity.memory_card_title_capacity:
            raise ValueError(
                f"Profile identity {label} does not fit its NUL-padded capacity"
            )
    if (
        not identity.imported_game_title
        or not identity.output_game_title
        or identity.imported_game_title == identity.output_game_title
    ):
        raise ValueError("Profile identity must replace one non-empty game title")
    for label, text in (
        ("imported_game_title", identity.imported_game_title),
        ("output_game_title", identity.output_game_title),
    ):
        if "\0" in text:
            raise ValueError(f"Profile identity {label} contains an embedded NUL")
        try:
            text.encode("cp1252")
        except UnicodeEncodeError as exc:
            raise ValueError(f"Profile identity {label} must be CP1252") from exc

    roots: dict[str, Path] = {}
    overrides = {
        key: Path(value).resolve() for key, value in (root_overrides or {}).items()
    }
    for row in _read_tsv(directory / "roots.tsv", ROOT_FIELDS):
        root_id = row["root_id"]
        if not root_id or root_id in roots:
            raise ValueError(f"Duplicate or empty profile root_id: {root_id!r}")
        root = overrides.get(root_id)
        if root is None:
            root = _profile_root_path(
                row["path"], f"root {root_id}", workspace, project_paths
            )
        if not root.exists():
            raise FileNotFoundError(root)
        roots[root_id] = root
    unknown_overrides = sorted(overrides.keys() - roots.keys())
    if unknown_overrides:
        raise ValueError(
            "Profile root overrides contain unknown IDs: "
            + ", ".join(unknown_overrides)
        )

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
        bypass_value = row["bypass_check"]
        if bypass_value not in ("0", "1"):
            raise ValueError(
                f"Feature {feature_id}: bypass_check must be 0 or 1"
            )
        bypass_check = bypass_value == "1"
        actual = feature_content_sha256(feature_path)
        if len(expected) != 64 or any(
            char not in "0123456789ABCDEF" for char in expected
        ):
            raise ValueError(
                f"Feature {feature_id}: expected_sha256 must be 64 hex digits"
            )
        if not bypass_check and actual != expected:
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
                actual_sha256=actual,
                bypass_check=bypass_check,
                module_ids=tuple(module_ids),
            )
        )

    return Profile(
        directory=directory,
        profile_id=profile_id,
        roots=roots,
        identity=identity,
        features=tuple(features),
        modules=tuple(modules),
    )
