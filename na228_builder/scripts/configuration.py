from __future__ import annotations

import codecs
import csv
import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import TYPE_CHECKING

from scripts.lib.paths import Paths, load_paths, resolve_alias

if TYPE_CHECKING:
    from .catalog import CatalogSelection


BUILDER_TARGETS_FILE = Path("catalog") / "implementation" / "targets.tsv"
MODULE_TYPE_ORDER = (
    "translation_importer",
    "string_patcher",
    "runtime_injector",
    "texture_patcher",
    "binary_patcher",
)
MODULE_TYPES = frozenset(MODULE_TYPE_ORDER)
FEATURE_MODULE_INPUTS = {
    "localization": (
        ("translation_importer", ("localization", "translation_importer")),
        ("texture_patcher", ("localization", "texture_patcher")),
    ),
}
BINARY_PATCHER_CONTROL_FILES = (
    "groups.tsv",
    "patches.tsv",
    "edits.tsv",
)
STRING_PATCHER_CONTROL_FILES = ("strings.tsv",)
RUNTIME_INJECTOR_CONTROL_FILES = (
    "groups.tsv",
    "patches.tsv",
    "fragments.tsv",
    "c_sources.tsv",
    "c_imports.tsv",
    "c_fragments.tsv",
    "relocations.tsv",
    "edits.tsv",
)
TRANSLATION_IMPORTER_CONTROL_FILES = (
    "mappings.tsv",
)
TEXTURE_PATCHER_CONTROL_FILES = (
    "containers.tsv",
    "mappings.tsv",
    "strategies.tsv",
)


@dataclass(frozen=True)
class ProductIdentity:
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
class SelectedFeature:
    feature_id: str
    input_sha256: str
    module_ids: tuple[str, ...]


@dataclass(frozen=True)
class ModuleInvocation:
    module_id: str
    order: int
    module: str
    input_path: Path
    input_sha256: str
    feature_id: str


@dataclass(frozen=True)
class BuildConfiguration:
    definition_path: Path
    configuration_id: str
    product_path: Path
    targets_path: Path
    roots: dict[str, Path]
    identity: ProductIdentity
    features: tuple[SelectedFeature, ...]
    modules: tuple[ModuleInvocation, ...]
    selection: CatalogSelection


def _identity_object(value: object, keys: set[str], label: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != keys:
        expected = ", ".join(sorted(keys))
        raise ValueError(f"Product {label} keys must be: {expected}")
    return value


def _identity_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"Product identity {label} must be non-empty text")
    return value


def _identity_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"Product identity {label} must be an integer")
    return value


def _read_product(path: Path) -> tuple[ProductIdentity, dict[str, str]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Product config is not valid JSON: {path}") from exc
    product = _identity_object(
        data,
        {"schema_version", "title", "serial", "inputs", "identity", "builds"},
        "product",
    )
    if product["schema_version"] != 1:
        raise ValueError("Unsupported product schema_version")
    root = _identity_object(
        product["identity"], {"image", "memory_card", "game_title"}, "identity"
    )
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
    inputs = product["inputs"]
    if not isinstance(inputs, dict) or not inputs:
        raise ValueError("Product inputs must be a non-empty object")
    normalized_inputs: dict[str, str] = {}
    for root_id, value in inputs.items():
        if (
            not isinstance(root_id, str)
            or not re.fullmatch(r"[a-z][a-z0-9_]*", root_id)
            or root_id in normalized_inputs
            or not isinstance(value, str)
            or not value
        ):
            raise ValueError(f"Invalid product input: {root_id!r}")
        normalized_inputs[root_id] = value
    identity = ProductIdentity(
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
    return identity, normalized_inputs


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


def _product_input_path(
    value: str, label: str, workspace: Path, paths: Paths
) -> Path:
    if value.startswith("@"):
        try:
            resolved = resolve_alias(value, paths)
        except (KeyError, ValueError) as exc:
            raise ValueError(
                f"{label} has an invalid project-root alias: {value!r}"
            ) from exc
        if not resolved.exists():
            raise FileNotFoundError(resolved)
        return resolved
    return _workspace_path(value, label, workspace)


def _tree_digest(
    path: Path,
    files: list[Path],
    *,
    external_labels: Mapping[Path, str] | None = None,
) -> str:
    labels = {
        item.resolve(): label
        for item, label in (external_labels or {}).items()
    }

    def digest_path(item: Path) -> str:
        resolved = item.resolve()
        if resolved in labels:
            return labels[resolved]
        try:
            return resolved.relative_to(path).as_posix()
        except ValueError:
            repository = load_paths(path, allow_missing=True).repository
            return "@repository/" + resolved.relative_to(repository).as_posix()

    digest = hashlib.sha256()
    for item in sorted(files, key=digest_path):
        relative = digest_path(item).encode("utf-8")
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


def _builder_targets_file(module_path: Path) -> Path:
    for parent in (module_path.resolve(), *module_path.resolve().parents):
        targets_path = parent / BUILDER_TARGETS_FILE
        if targets_path.is_file():
            return targets_path
    raise FileNotFoundError(
        f"Builder target registry is missing above: {module_path.resolve()}"
    )


def _binary_patcher_content_files(path: Path) -> list[Path]:
    path = path.resolve()
    files = _required_files(
        path, BINARY_PATCHER_CONTROL_FILES, "Binary-patcher module"
    )
    files.append(_builder_targets_file(path))
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


def _runtime_injector_content_files(path: Path) -> list[Path]:
    path = path.resolve()
    files = _required_files(
        path, RUNTIME_INJECTOR_CONTROL_FILES, "runtime_injector module"
    )
    files.append(_builder_targets_file(path))
    fragments_path = path / "fragments.tsv"
    with fragments_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fields = reader.fieldnames or []
        if "blob_path" not in fields:
            raise ValueError(f"{fragments_path}: missing blob_path column")
        blob_paths = {
            (row.get("blob_path") or "").strip()
            for row in reader
            if (row.get("blob_path") or "").strip()
        }
    for value in sorted(blob_paths):
        candidate = Path(value.replace("\\", "/"))
        if candidate.is_absolute() or ".." in candidate.parts:
            raise ValueError(
                f"{fragments_path}: blob_path must be module-relative: {value!r}"
            )
        blob = (path / candidate).resolve()
        try:
            blob.relative_to(path)
        except ValueError as exc:
            raise ValueError(
                f"{fragments_path}: blob_path escapes module: {value!r}"
            ) from exc
        if not blob.is_file():
            raise FileNotFoundError(blob)
        files.append(blob)
    sources_path = path / "c_sources.tsv"
    with sources_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fields = reader.fieldnames or []
        if "path" not in fields:
            raise ValueError(f"{sources_path}: missing path column")
        source_paths = {
            (row.get("path") or "").strip()
            for row in reader
            if (row.get("path") or "").strip()
        }
    for value in sorted(source_paths):
        candidate = Path(value.replace("\\", "/"))
        if candidate.is_absolute() or ".." in candidate.parts:
            raise ValueError(
                f"{sources_path}: path must be relative: {value!r}"
            )
        if candidate.parts and candidate.parts[0] == "src":
            repository = load_paths(path, allow_missing=True).repository
            source_root = (repository / "src").resolve()
            source = (repository / candidate).resolve()
            try:
                source.relative_to(source_root)
            except ValueError as exc:
                raise ValueError(
                    f"{sources_path}: path escapes src: {value!r}"
                ) from exc
        else:
            source = (path / candidate).resolve()
            try:
                source.relative_to(path)
            except ValueError as exc:
                raise ValueError(
                    f"{sources_path}: path escapes module: {value!r}"
                ) from exc
        if not source.is_file():
            raise FileNotFoundError(source)
        files.append(source)
    return files


def _module_content_files(path: Path, module_type: str) -> list[Path]:
    path = path.resolve()
    if module_type == "binary_patcher":
        return _binary_patcher_content_files(path)
    if module_type == "runtime_injector":
        return _runtime_injector_content_files(path)
    if module_type == "string_patcher":
        return _required_files(
            path, STRING_PATCHER_CONTROL_FILES, "string_patcher module"
        )
    names = {
        "translation_importer": TRANSLATION_IMPORTER_CONTROL_FILES,
        "texture_patcher": TEXTURE_PATCHER_CONTROL_FILES,
    }[module_type]
    return _required_files(path, names, f"{module_type} module")


def module_content_sha256(path: Path, module_type: str) -> str:
    """Hash one module's canonical executable inputs."""
    path = path.resolve()
    if module_type not in MODULE_TYPES:
        raise ValueError(f"Unsupported module type: {module_type!r}")
    if not path.is_dir():
        raise FileNotFoundError(path)
    files = _module_content_files(path, module_type)
    external_labels = (
        {
            _builder_targets_file(path): "@builder/catalog/implementation/targets.tsv"
        }
        if module_type in {"binary_patcher", "runtime_injector"}
        else None
    )
    return _tree_digest(path, files, external_labels=external_labels)


def _validated_identity(product_path: Path) -> tuple[ProductIdentity, dict[str, str]]:
    identity, product_inputs = _read_product(product_path)
    if identity.memory_card_title_offset < 0 or identity.memory_card_title_capacity <= 0:
        raise ValueError(
            "Product identity title offset must be non-negative and capacity positive"
        )
    if (
        identity.game_title_mapping_count <= 0
        or identity.game_title_occurrence_count < identity.game_title_mapping_count
    ):
        raise ValueError("Product identity game-title coverage is invalid")
    try:
        encoding = codecs.lookup(identity.memory_card_title_encoding).name
    except LookupError as exc:
        raise ValueError("Product identity has an unknown title encoding") from exc
    identity = replace(identity, memory_card_title_encoding=encoding)
    from ..image_assembler.iso9660 import normalize_iso_path

    for label, value in (
        ("source_boot_path", identity.source_boot_path),
        ("output_boot_path", identity.output_boot_path),
        ("system_cnf_path", identity.system_cnf_path),
    ):
        if normalize_iso_path(value) != value:
            raise ValueError(f"Product identity {label} must be normalized: {value!r}")
    if identity.source_boot_path == identity.output_boot_path:
        raise ValueError("Product identity boot paths must differ")
    if len(identity.source_boot_path.encode("ascii")) != len(
        identity.output_boot_path.encode("ascii")
    ):
        raise ValueError("Product identity boot paths must have equal byte lengths")
    for label, text in (
        ("source_memory_card_title", identity.source_memory_card_title),
        ("output_memory_card_title", identity.output_memory_card_title),
    ):
        if "\0" in text:
            raise ValueError(f"Product identity {label} contains an embedded NUL")
        try:
            encoded = text.encode(identity.memory_card_title_encoding)
        except UnicodeEncodeError as exc:
            raise ValueError(
                f"Product identity {label} is not encodable as "
                f"{identity.memory_card_title_encoding}"
            ) from exc
        if len(encoded) >= identity.memory_card_title_capacity:
            raise ValueError(
                f"Product identity {label} does not fit its NUL-padded capacity"
            )
    if (
        not identity.imported_game_title
        or not identity.output_game_title
        or identity.imported_game_title == identity.output_game_title
    ):
        raise ValueError("Product identity must replace one non-empty game title")
    for label, text in (
        ("imported_game_title", identity.imported_game_title),
        ("output_game_title", identity.output_game_title),
    ):
        if "\0" in text:
            raise ValueError(f"Product identity {label} contains an embedded NUL")
        try:
            text.encode("cp1252")
        except UnicodeEncodeError as exc:
            raise ValueError(f"Product identity {label} must be CP1252") from exc
    return identity, product_inputs


def _resolved_roots(
    product_inputs: dict[str, str],
    workspace: Path,
    paths: Paths,
    root_overrides: Mapping[str, Path] | None,
) -> dict[str, Path]:
    overrides = {
        key: Path(value).resolve() for key, value in (root_overrides or {}).items()
    }
    roots: dict[str, Path] = {}
    for root_id, value in product_inputs.items():
        root = overrides.get(root_id)
        if root is None:
            root = _product_input_path(
                value, f"product input {root_id}", workspace, paths
            )
        if not root.exists():
            raise FileNotFoundError(root)
        roots[root_id] = root
    unknown_overrides = sorted(overrides.keys() - roots.keys())
    if unknown_overrides:
        raise ValueError(
            "Configuration root overrides contain unknown IDs: "
            + ", ".join(unknown_overrides)
        )
    return roots


def _feature_module_inputs(
    builder_root: Path,
    feature_id: str,
) -> list[tuple[str, Path]]:
    inputs: list[tuple[str, Path]] = []
    for module_type, relative_path in FEATURE_MODULE_INPUTS.get(feature_id, ()):
        module_path = builder_root.joinpath(*relative_path).resolve()
        if not module_path.is_dir():
            raise FileNotFoundError(module_path)
        inputs.append((module_type, module_path))
    return sorted(inputs, key=lambda item: MODULE_TYPE_ORDER.index(item[0]))


def _catalog_feature_sha256(
    selection: CatalogSelection,
    feature_id: str,
    repository: Path,
    module_inputs: list[tuple[str, Path]],
    targets_path: Path,
) -> str:
    from . import catalog as catalog_module

    raw_features = selection.catalog.get("features")
    if not isinstance(raw_features, dict):
        raise ValueError("Catalog root must contain a features object")
    feature_value = raw_features[feature_id]
    entries: list[tuple[str, bytes]] = [
        (
            f"catalog/{feature_id}.json",
            json.dumps(feature_value, ensure_ascii=False, separators=(",", ":")).encode("utf-8"),
        )
    ]
    for edit_id in catalog_module.feature_reference_ids(
        selection, feature_id, "edits"
    ):
        entries.append(
            (
                f"edits/{edit_id}.json",
                json.dumps(
                    selection.edits[edit_id],
                    ensure_ascii=False,
                    separators=(",", ":"),
                ).encode("utf-8"),
            )
        )
    for injection_id in catalog_module.feature_reference_ids(
        selection, feature_id, "injections"
    ):
        entries.append(
            (
                f"injections/{injection_id}.json",
                json.dumps(
                    selection.injections[injection_id],
                    ensure_ascii=False,
                    separators=(",", ":"),
                ).encode("utf-8"),
            )
        )
    for module_type, module_path in module_inputs:
        for file in _module_content_files(module_path, module_type):
            entries.append((file.relative_to(repository).as_posix(), file.read_bytes()))
    if catalog_module.feature_has(selection, feature_id, "edits") or catalog_module.feature_has(
        selection, feature_id, "injections"
    ):
        entries.append((targets_path.relative_to(repository).as_posix(), targets_path.read_bytes()))
    if catalog_module.feature_has(selection, feature_id, "edits"):
        operations = repository / "na228_builder" / "modules" / "binary_patcher" / "operations"
        for file in sorted(operations.glob("*.tsv")):
            entries.append((file.relative_to(repository).as_posix(), file.read_bytes()))
    for file in catalog_module.referenced_files(selection, repository, feature_id):
        entries.append((file.relative_to(repository).as_posix(), file.read_bytes()))
    digest = hashlib.sha256()
    for label, payload in sorted(entries):
        digest.update(label.encode("utf-8"))
        digest.update(b"\0")
        digest.update(payload)
        digest.update(b"\0")
    return digest.hexdigest().upper()


def _load_configuration(
    definition_path: Path,
    workspace: Path,
    builder_root: Path,
    *,
    project_paths: Paths | None,
    root_overrides: Mapping[str, Path] | None,
) -> BuildConfiguration:
    from . import catalog as catalog_module

    configuration_id = definition_path.stem
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_. -]*", configuration_id):
        raise ValueError(f"Invalid configuration name: {configuration_id!r}")
    catalog_path = builder_root / "catalog"
    selection = catalog_module.load_selection(catalog_path, definition_path)
    paths = project_paths or load_paths(workspace, allow_missing=True)
    product_path = paths.file("product_config").resolve()
    identity, product_inputs = _validated_identity(product_path)
    roots = _resolved_roots(product_inputs, workspace, paths, root_overrides)
    targets_path = builder_root / BUILDER_TARGETS_FILE
    if not targets_path.is_file():
        raise FileNotFoundError(targets_path)
    features: list[SelectedFeature] = []
    modules: list[ModuleInvocation] = []
    for feature_id in selection.feature_ids:
        module_inputs = _feature_module_inputs(builder_root, feature_id)
        actual = _catalog_feature_sha256(
            selection,
            feature_id,
            workspace,
            module_inputs,
            targets_path,
        )
        available: dict[str, Path] = {}
        for module_type, module_path in module_inputs:
            if selection.node_enabled("features", feature_id):
                available[module_type] = module_path
        if catalog_module.feature_has(
            selection,
            feature_id,
            "injections",
            enabled_only=True,
        ):
            available["runtime_injector"] = builder_root
        if catalog_module.feature_has(
            selection,
            feature_id,
            "edits",
            enabled_only=True,
        ):
            available["binary_patcher"] = builder_root
        module_ids: list[str] = []
        for module_type in MODULE_TYPE_ORDER:
            module_path = available.get(module_type)
            if module_path is None:
                continue
            module_id = f"{feature_id}.{module_type}"
            module_ids.append(module_id)
            module_hash = (
                actual
                if module_type in {"binary_patcher", "runtime_injector"}
                else module_content_sha256(module_path, module_type)
            )
            modules.append(
                ModuleInvocation(
                    module_id=module_id,
                    order=len(modules) + 1,
                    module=module_type,
                    input_path=module_path,
                    input_sha256=module_hash,
                    feature_id=feature_id,
                )
            )
        if selection.node_enabled("features", feature_id) and not module_ids:
            raise ValueError(f"Catalog feature owns no executable data: {feature_id}")
        features.append(
            SelectedFeature(
                feature_id=feature_id,
                input_sha256=actual,
                module_ids=tuple(module_ids),
            )
        )
    return BuildConfiguration(
        definition_path=definition_path,
        configuration_id=configuration_id,
        product_path=product_path,
        targets_path=targets_path,
        roots=roots,
        identity=identity,
        features=tuple(features),
        modules=tuple(modules),
        selection=selection,
    )


def configuration_resource_files(
    configuration: BuildConfiguration,
    *,
    include_disabled: bool = False,
) -> tuple[Path, ...]:
    """Return structural and hash-covered files needed to load a configuration."""
    from . import catalog as catalog_module

    files = [
        configuration.definition_path,
        configuration.product_path,
        *configuration.selection.catalog_files,
        configuration.selection.edits_path,
        configuration.selection.injections_path,
        configuration.targets_path,
    ]
    if configuration.selection.base_configuration_path is not None:
        files.append(configuration.selection.base_configuration_path)
    if include_disabled or any(
        module.module == "binary_patcher" for module in configuration.modules
    ):
        operations = (
            configuration.selection.catalog_path.parent
            / "modules"
            / "binary_patcher"
            / "operations"
        )
        files.extend(sorted(operations.glob("*.tsv")))
    for feature in configuration.features:
        files.extend(
            catalog_module.referenced_files(
                configuration.selection,
                configuration.selection.catalog_path.parent.parent,
                feature.feature_id,
            )
        )
    if include_disabled:
        builder_root = configuration.selection.catalog_path.parent
        for feature in configuration.features:
            for module_type, module_path in _feature_module_inputs(
                builder_root, feature.feature_id
            ):
                files.extend(_module_content_files(module_path, module_type))
    else:
        for module in configuration.modules:
            if module.module not in {"binary_patcher", "runtime_injector"}:
                files.extend(_module_content_files(module.input_path, module.module))
    return tuple(sorted(set(files), key=lambda path: path.as_posix()))


def load_configuration(
    definition_path: Path,
    workspace: Path,
    builder_root: Path,
    *,
    project_paths: Paths | None = None,
    root_overrides: Mapping[str, Path] | None = None,
) -> BuildConfiguration:
    workspace = workspace.resolve()
    definition_path = definition_path.resolve()
    builder_root = builder_root.resolve()
    try:
        builder_root.relative_to(workspace)
    except ValueError as exc:
        raise ValueError(
            f"Configuration builder root must be inside the workspace: {builder_root}"
        ) from exc
    if not definition_path.is_file() or definition_path.suffix.lower() != ".json":
        raise FileNotFoundError(
            f"Configuration definition is not a JSON file: {definition_path}"
        )
    return _load_configuration(
        definition_path,
        workspace,
        builder_root,
        project_paths=project_paths,
        root_overrides=root_overrides,
    )
