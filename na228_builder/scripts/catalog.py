from __future__ import annotations

import csv
import hashlib
import json
import re
import tempfile
from dataclasses import dataclass, replace
from pathlib import Path, PurePosixPath

from ..modules.binary_patcher import adapters as binary_adapters
from ..modules.binary_patcher import engine as binary_patcher
from ..modules.runtime_injector import engine as runtime_injector
from ..payload_builder import ee_c_fragments
from . import catalog_format
from ..payload_builder.operations import (
    FRAGMENT_KINDS,
    RELOCATION_KINDS,
    PayloadFragment,
    PayloadRelocation,
    SymbolicPatch,
)


IDENTIFIER = re.compile(r"[a-z][a-z0-9_]*\Z")
OPERATION_FIELDS = ["field", "required", "type"]
FIELD_TYPES = {"hex", "integer", "integer_list", "path", "sha256", "text"}


class ConfigurationError(ValueError):
    """A user-supplied configuration does not satisfy the catalog contract."""


@dataclass(frozen=True)
class CatalogNode:
    path: tuple[str, ...]
    enabled: bool
    patches: tuple[str, ...] = ()
    description: str = ""
    configured_value: object = None
    has_configured_value: bool = False

    @property
    def feature_id(self) -> str:
        if len(self.path) < 2 or self.path[0] != "features":
            raise ValueError(f"Catalog node is outside the features root: {self.node_id}")
        return self.path[1]

    @property
    def node_id(self) -> str:
        if len(self.path) > 1 and self.path[0] == "features":
            return ".".join(self.path[1:])
        return ".".join(self.path)

    @property
    def edit_ids(self) -> tuple[str, ...]:
        return tuple(item for item in self.patches if item.startswith("e__"))

    @property
    def injection_ids(self) -> tuple[str, ...]:
        return tuple(item for item in self.patches if item.startswith("i__"))

    @property
    def string_patch_ids(self) -> tuple[str, ...]:
        return tuple(item for item in self.patches if item.startswith("s__"))


@dataclass(frozen=True)
class CatalogSelection:
    catalog_path: Path
    catalog_files: tuple[Path, ...]
    edits_path: Path
    injections_path: Path
    string_patches_path: Path
    base_configuration_path: Path | None
    configuration_path: Path
    catalog: dict[str, catalog_format.ContainerNode]
    edits: dict[str, dict[str, object]]
    injections: dict[str, dict[str, object]]
    string_patches: dict[str, dict[str, object]]
    nodes: tuple[CatalogNode, ...]

    @property
    def configuration_id(self) -> str:
        return self.configuration_path.stem

    @property
    def feature_ids(self) -> tuple[str, ...]:
        return tuple(
            node.path[1]
            for node in self.nodes
            if len(node.path) == 2 and node.path[0] == "features"
        )

    def feature_nodes(self, feature_id: str) -> tuple[CatalogNode, ...]:
        return tuple(
            node
            for node in self.nodes
            if len(node.path) >= 2
            and node.path[0] == "features"
            and node.path[1] == feature_id
        )

    def node_enabled(self, *path: str) -> bool:
        matches = [node for node in self.nodes if node.path == path]
        if len(matches) != 1:
            raise ValueError(f"Catalog selection has no unique node: {'.'.join(path)}")
        return matches[0].enabled


@dataclass(frozen=True)
class OperationField:
    name: str
    required: bool
    type: str


def _read_json(
    path: Path,
    label: str,
    *,
    allow_empty: bool = False,
) -> dict[str, object]:
    def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
        value: dict[str, object] = {}
        for key, item in pairs:
            if key in value:
                raise ValueError(f"{label} contains duplicate key {key!r}")
            value[key] = item
        return value

    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} is not valid JSON: {path}") from exc
    if not isinstance(value, dict) or (not value and not allow_empty):
        qualifier = "an object" if allow_empty else "a non-empty object"
        raise ValueError(f"{label} root must be {qualifier}")
    return value


def _read_catalog(
    path: Path,
) -> tuple[dict[str, catalog_format.ContainerNode], tuple[Path, ...]]:
    path = path.resolve()
    if not path.is_dir():
        raise FileNotFoundError(path)
    feature_paths: dict[str, Path] = {
        item.stem: item.resolve()
        for item in path.glob("*.modcat")
    }
    if not feature_paths:
        raise ValueError(f"Catalog contains no feature files: {path}")
    feature_ids = sorted(feature_paths)
    features: dict[str, catalog_format.ContainerNode] = {}
    files: list[Path] = []
    for feature_id in feature_ids:
        _identifier(feature_id, "Catalog feature filename")
        feature_path = feature_paths[feature_id]
        features[feature_id] = catalog_format.parse_catalog(feature_path)
        files.append(feature_path)
    return features, tuple(files)


def _identifier(value: str, label: str) -> str:
    if not IDENTIFIER.fullmatch(value):
        raise ValueError(f"{label} must be a meaningful snake_case key: {value!r}")
    return value


def _description(value: object, label: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError(f"{label} description must be text")
    if not value.strip():
        raise ValueError(f"{label} description must be nonempty")
    return value


def _container_fields(
    node: catalog_format.ContainerNode,
) -> dict[str, catalog_format.CatalogNodeExpression]:
    return {field.name: field.node for field in node.fields}


def _feature_root(
    features: dict[str, catalog_format.ContainerNode],
) -> catalog_format.ContainerNode:
    return catalog_format.ContainerNode(
        tuple(
            catalog_format.ContainerField(feature_id, features[feature_id])
            for feature_id in sorted(features)
        )
    )


def _catalog_patches(
    node: catalog_format.CatalogNodeExpression,
) -> tuple[str, ...]:
    if isinstance(node, catalog_format.SettingNode):
        return node.patches
    if isinstance(node, catalog_format.ContainerNode):
        return tuple(
            patch
            for field in node.fields
            for patch in _catalog_patches(field.node)
        )
    if isinstance(node, catalog_format.UnionNode):
        return tuple(
            patch
            for branch in node.branches
            for patch in _catalog_patches(branch)
        )
    raise TypeError(type(node))


def _configured_value_text(value: object, *, limit: int = 160) -> str:
    try:
        text = json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError):
        text = repr(value)
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _invalid_configuration_value(
    path: tuple[str, ...],
    value: object,
    expected: str,
) -> ConfigurationError:
    return ConfigurationError(
        f"Invalid config value at {'.'.join(path)}: "
        f"got {_configured_value_text(value)}; expected {expected}"
    )


def _validate_configuration_value(
    node: catalog_format.CatalogNodeExpression,
    value: object,
    path: tuple[str, ...],
) -> None:
    label = ".".join(path)
    if value is False:
        return
    if isinstance(node, catalog_format.SettingNode):
        if node.value_type is None:
            if value is not True:
                raise _invalid_configuration_value(path, value, "true or false")
        elif not catalog_format.matches_type(node.value_type, value):
            expected = " ".join(catalog_format.type_text(node.value_type).split())
            raise _invalid_configuration_value(
                path,
                value,
                f"{expected}, or false to disable it",
            )
        return
    if isinstance(node, catalog_format.ContainerNode):
        if not isinstance(value, dict):
            raise _invalid_configuration_value(
                path, value, "an object, or false to disable it"
            )
        fields = _container_fields(node)
        if set(value) != set(fields):
            missing = sorted(set(fields) - set(value))
            extra = sorted(set(value) - set(fields))
            problems: list[str] = []
            if missing:
                problems.append("missing keys: " + ", ".join(missing))
            if extra:
                problems.append("unknown keys: " + ", ".join(extra))
            raise ConfigurationError(
                f"Invalid config object at {label}: {'; '.join(problems)}"
            )
        for key, child in fields.items():
            _validate_configuration_value(child, value[key], (*path, key))
        return
    if isinstance(node, catalog_format.UnionNode):
        matches = [
            branch
            for branch in node.branches
            if catalog_format.matches_type(catalog_format.active_type(branch), value)
        ]
        if len(matches) != 1:
            expected = " ".join(
                catalog_format.type_text(catalog_format.active_type(node)).split()
            )
            raise _invalid_configuration_value(
                path,
                value,
                f"exactly one of {expected}, or false to disable it",
            )
        _validate_configuration_value(matches[0], value, path)
        return
    raise TypeError(type(node))


def _merge_configuration_value(
    node: catalog_format.CatalogNodeExpression,
    base: object,
    override: object,
    path: tuple[str, ...],
) -> object:
    label = ".".join(path)
    if override is False:
        return False
    if isinstance(node, (catalog_format.SettingNode, catalog_format.UnionNode)):
        _validate_configuration_value(node, override, path)
        return override
    if not isinstance(node, catalog_format.ContainerNode):
        raise TypeError(type(node))
    if not isinstance(override, dict):
        raise _invalid_configuration_value(
            path, override, "an object override, or false to disable it"
        )
    fields = _container_fields(node)
    extra = sorted(set(override) - set(fields))
    if extra:
        raise ConfigurationError(
            f"Invalid config override at {label}: unknown keys: {', '.join(extra)}"
        )
    if base is False:
        merged: dict[str, object] = {key: False for key in fields}
    elif isinstance(base, dict):
        if set(base) != set(fields):
            missing = sorted(set(fields) - set(base))
            extra_base = sorted(set(base) - set(fields))
            problems: list[str] = []
            if missing:
                problems.append("missing keys: " + ", ".join(missing))
            if extra_base:
                problems.append("unknown keys: " + ", ".join(extra_base))
            raise ConfigurationError(
                f"Invalid config object at {label}: {'; '.join(problems)}"
            )
        merged = dict(base)
    else:
        raise _invalid_configuration_value(
            path, base, "an object, or false to disable it"
        )
    for key, child_override in override.items():
        merged[key] = _merge_configuration_value(
            fields[key], merged[key], child_override, (*path, key)
        )
    return merged


def _selected_nodes(
    root: catalog_format.ContainerNode,
    value: object,
) -> tuple[CatalogNode, ...]:
    nodes: list[CatalogNode] = []

    def visit(
        node: catalog_format.CatalogNodeExpression,
        configured: object,
        path: tuple[str, ...],
    ) -> bool:
        if configured is False:
            description = (
                node.description
                if isinstance(
                    node, (catalog_format.ContainerNode, catalog_format.SettingNode)
                )
                else ""
            )
            patches = node.patches if isinstance(node, catalog_format.SettingNode) else ()
            nodes.append(CatalogNode(path, False, patches, description))
            if isinstance(node, catalog_format.ContainerNode):
                for field in node.fields:
                    visit(field.node, False, (*path, field.name))
            return False
        if isinstance(node, catalog_format.SettingNode):
            has_value = node.value_type is not None
            nodes.append(
                CatalogNode(
                    path,
                    True,
                    node.patches,
                    node.description,
                    configured if has_value else None,
                    has_value,
                )
            )
            return True
        if isinstance(node, catalog_format.UnionNode):
            matches = [
                branch
                for branch in node.branches
                if catalog_format.matches_type(
                    catalog_format.active_type(branch), configured
                )
            ]
            if len(matches) != 1:
                expected = " ".join(
                    catalog_format.type_text(catalog_format.active_type(node)).split()
                )
                raise _invalid_configuration_value(
                    path,
                    configured,
                    f"exactly one of {expected}, or false to disable it",
                )
            return visit(matches[0], configured, path)
        if not isinstance(node, catalog_format.ContainerNode):
            raise TypeError(type(node))
        if not isinstance(configured, dict):
            raise _invalid_configuration_value(path, configured, "an object")
        insertion = len(nodes)
        nodes.append(CatalogNode(path, False, (), node.description))
        enabled = False
        for field in node.fields:
            enabled = visit(field.node, configured[field.name], (*path, field.name)) or enabled
        nodes[insertion] = CatalogNode(path, enabled, (), node.description)
        return enabled

    visit(root, value, ("features",))
    return tuple(nodes)


def _load_implementation(
    catalog_path: Path,
    features: dict[str, catalog_format.ContainerNode],
) -> tuple[
    Path,
    Path,
    Path,
    dict[str, dict[str, object]],
    dict[str, dict[str, object]],
    dict[str, dict[str, object]],
]:
    implementation_path = catalog_path / "implementation"
    edits_path = implementation_path / "edits.json"
    injections_path = implementation_path / "injections.json"
    string_patches_path = implementation_path / "string_patches.json"
    raw_edits = _read_json(edits_path, "Edits", allow_empty=True)
    raw_injections = _read_json(injections_path, "Injections", allow_empty=True)
    raw_string_patches = _read_json(
        string_patches_path, "String patches", allow_empty=True
    )
    edits: dict[str, dict[str, object]] = {}
    injections: dict[str, dict[str, object]] = {}
    string_patches: dict[str, dict[str, object]] = {}
    for edit_id, edit in raw_edits.items():
        _identifier(edit_id, "Edit ID")
        if not edit_id.startswith("e__"):
            raise ValueError(f"Edit ID must start with 'e__': {edit_id!r}")
        if not isinstance(edit, dict):
            raise ValueError(f"Edit {edit_id!r} must be an object")
        _description(edit.get("description"), f"Edit {edit_id!r}")
        if "adapter" in edit:
            binary_adapters.validate_adapter_name(edit["adapter"])
        edits[edit_id] = edit
    for injection_id, injection in raw_injections.items():
        _identifier(injection_id, "Injection ID")
        if not injection_id.startswith("i__"):
            raise ValueError(
                f"Injection ID must start with 'i__': {injection_id!r}"
            )
        if not isinstance(injection, dict):
            raise ValueError(f"Injection {injection_id!r} must be an object")
        extra = sorted(set(injection) - {"description", "hooks", "payload"})
        if extra:
            raise ValueError(
                f"Injection {injection_id!r} has unknown fields: {extra}"
            )
        if not injection:
            raise ValueError(f"Injection {injection_id!r} must not be empty")
        _description(injection.get("description"), f"Injection {injection_id!r}")
        for field in ("hooks", "payload"):
            if field in injection and not isinstance(injection[field], dict):
                raise ValueError(f"Injection {injection_id!r}.{field} must be an object")
        hooks = injection.get("hooks", {})
        if isinstance(hooks, dict):
            for hook_id, hook in hooks.items():
                _identifier(hook_id, f"Injection {injection_id!r} hook ID")
                if not isinstance(hook, dict):
                    raise ValueError(
                        f"Injection {injection_id!r} hook {hook_id!r} must be an object"
                    )
                _description(
                    hook.get("description"),
                    f"Injection {injection_id!r} hook {hook_id!r}",
                )
        injections[injection_id] = injection
    required_string_patch_fields = {
        "description",
        "operation",
        "expected_value",
        "expected_mapping_count",
        "expected_occurrence_count",
    }
    for patch_id, patch in raw_string_patches.items():
        _identifier(patch_id, "String patch ID")
        if not patch_id.startswith("s__"):
            raise ValueError(f"String patch ID must start with 's__': {patch_id!r}")
        if not isinstance(patch, dict):
            raise ValueError(f"String patch {patch_id!r} must be an object")
        if set(patch) != required_string_patch_fields:
            missing = sorted(required_string_patch_fields - set(patch))
            extra = sorted(set(patch) - required_string_patch_fields)
            problems = []
            if missing:
                problems.append("missing fields: " + ", ".join(missing))
            if extra:
                problems.append("unknown fields: " + ", ".join(extra))
            raise ValueError(
                f"String patch {patch_id!r} is invalid: {'; '.join(problems)}"
            )
        _description(patch["description"], f"String patch {patch_id!r}")
        if patch["operation"] != "replace_imported_game_title":
            raise ValueError(
                f"String patch {patch_id!r} has unsupported operation: "
                f"{patch['operation']!r}"
            )
        expected_value = patch["expected_value"]
        if (
            not isinstance(expected_value, str)
            or not expected_value
            or "\0" in expected_value
        ):
            raise ValueError(
                f"String patch {patch_id!r}.expected_value must be non-empty text "
                "without an embedded NUL"
            )
        mapping_count = patch["expected_mapping_count"]
        occurrence_count = patch["expected_occurrence_count"]
        if (
            isinstance(mapping_count, bool)
            or not isinstance(mapping_count, int)
            or mapping_count <= 0
            or isinstance(occurrence_count, bool)
            or not isinstance(occurrence_count, int)
            or occurrence_count < mapping_count
        ):
            raise ValueError(
                f"String patch {patch_id!r} has invalid expected coverage"
            )
        string_patches[patch_id] = patch
    references = [
        patch
        for feature in features.values()
        for patch in _catalog_patches(feature)
    ]
    referenced = set(references)
    for patch in references:
        _identifier(patch, "Catalog patch ID")
        if patch.startswith("e__"):
            if patch not in edits:
                raise ValueError(f"Catalog references unknown edit: {patch}")
        elif patch.startswith("i__"):
            if patch not in injections:
                raise ValueError(f"Catalog references unknown injection: {patch}")
        elif patch.startswith("s__"):
            if patch not in string_patches:
                raise ValueError(f"Catalog references unknown string patch: {patch}")
        else:
            raise ValueError(f"Catalog patch ID has invalid prefix: {patch!r}")
    orphaned = sorted(
        (set(edits) | set(injections) | set(string_patches)) - referenced
    )
    if orphaned:
        raise ValueError(f"Implementation definitions are not catalog-referenced: {orphaned}")
    return (
        edits_path,
        injections_path,
        string_patches_path,
        edits,
        injections,
        string_patches,
    )


def _effective_configuration(
    catalog_path: Path,
    configuration_path: Path,
    features: dict[str, catalog_format.ContainerNode],
) -> tuple[Path | None, object, dict[str, object]]:
    try:
        configuration = _read_json(configuration_path, "Configuration")
    except ValueError as exc:
        raise ConfigurationError(str(exc)) from exc
    root = _feature_root(features)
    repository_configuration_root = (catalog_path.parent / "configurations").resolve()
    if (
        configuration_path.parent == repository_configuration_root
        and configuration_path.name != "base.json"
        and set(configuration) != {"overrides"}
    ):
        raise ConfigurationError(
            "Repository configurations must contain only the overrides root key"
        )
    if set(configuration) == {"overrides"}:
        base_path = (repository_configuration_root / "base.json").resolve()
        try:
            base = _read_json(base_path, "Base configuration")
        except ValueError as exc:
            raise ConfigurationError(str(exc)) from exc
        if set(base) != {"features", "overrides"}:
            raise ConfigurationError(
                "Base configuration root keys must be features and overrides"
            )
        if not isinstance(base["overrides"], dict):
            raise ConfigurationError("Base configuration overrides must be an object")
        if not isinstance(configuration["overrides"], dict):
            raise _invalid_configuration_value(
                ("overrides",), configuration["overrides"], "an object"
            )
        _validate_configuration_value(root, base["features"], ("features",))
        base_effective = _merge_configuration_value(
            root, base["features"], base["overrides"], ("features",)
        )
        effective = _merge_configuration_value(
            root, base_effective, configuration["overrides"], ("features",)
        )
        overrides = configuration["overrides"]
    elif set(configuration) == {"features", "overrides"}:
        base_path = None
        if not isinstance(configuration["overrides"], dict):
            raise _invalid_configuration_value(
                ("overrides",), configuration["overrides"], "an object"
            )
        _validate_configuration_value(root, configuration["features"], ("features",))
        effective = _merge_configuration_value(
            root,
            configuration["features"],
            configuration["overrides"],
            ("features",),
        )
        overrides = configuration["overrides"]
    else:
        expected = {"features", "overrides"}
        actual = set(configuration)
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        problems: list[str] = []
        if missing:
            problems.append("missing keys: " + ", ".join(missing))
        if extra:
            problems.append("unknown keys: " + ", ".join(extra))
        raise ConfigurationError(f"Invalid config root: {'; '.join(problems)}")
    _validate_configuration_value(root, effective, ("features",))
    assert isinstance(overrides, dict)
    return base_path, effective, overrides


def load_selection(catalog_path: Path, configuration_path: Path) -> CatalogSelection:
    catalog_path = catalog_path.resolve()
    configuration_path = configuration_path.resolve()
    features, catalog_files = _read_catalog(catalog_path)
    (
        edits_path,
        injections_path,
        string_patches_path,
        edits,
        injections,
        string_patches,
    ) = _load_implementation(catalog_path, features)
    base_path, effective, _overrides = _effective_configuration(
        catalog_path, configuration_path, features
    )
    nodes = _selected_nodes(_feature_root(features), effective)
    return CatalogSelection(
        catalog_path=catalog_path,
        catalog_files=catalog_files,
        edits_path=edits_path,
        injections_path=injections_path,
        string_patches_path=string_patches_path,
        base_configuration_path=base_path,
        configuration_path=configuration_path,
        catalog=features,
        edits=edits,
        injections=injections,
        string_patches=string_patches,
        nodes=nodes,
    )


def materialized_configuration(
    catalog_path: Path,
    configuration_path: Path,
) -> dict[str, object]:
    """Return one self-contained JSON configuration with base values applied."""
    catalog_path = catalog_path.resolve()
    configuration_path = configuration_path.resolve()
    features, _catalog_files = _read_catalog(catalog_path)
    _base_path, effective, _overrides = _effective_configuration(
        catalog_path, configuration_path, features
    )
    return {"features": effective, "overrides": {}}


def public_catalog(catalog_path: Path) -> str:
    """Return the consolidated inert release reference without implementation data."""
    features, _catalog_files = _read_catalog(catalog_path)
    return catalog_format.serialize_catalog(features, include_patches=False)


def _parse_int(value: object, label: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be an integer")
    try:
        parsed = int(value, 0) if isinstance(value, str) else int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be an integer") from exc
    if parsed < minimum:
        raise ValueError(f"{label} must be at least {minimum}")
    return parsed


def _hex(value: object, label: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be hexadecimal text")
    return binary_patcher.normalized_hex(value, label, allow_empty=allow_empty)


def _sha256(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be SHA-256 text")
    return binary_patcher.normalized_sha256(value, label)


def _relative_path(value: object, label: str) -> PurePosixPath:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be path text")
    return binary_patcher.relative_posix(value, label)


def _parse_int_list(value: object, label: str) -> tuple[int, ...]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label} must be a non-empty integer list")
    parsed = tuple(
        _parse_int(item, f"{label}[{index}]")
        for index, item in enumerate(value)
    )
    if len(set(parsed)) != len(parsed):
        raise ValueError(f"{label} must contain unique offsets")
    return parsed


def load_operation_contracts(directory: Path) -> dict[str, tuple[OperationField, ...]]:
    contracts: dict[str, tuple[OperationField, ...]] = {}
    for path in sorted(directory.glob("*.tsv")):
        operation = _identifier(path.stem, f"operation filename {path.name}")
        fields: list[OperationField] = []
        seen: set[str] = set()
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            if reader.fieldnames != OPERATION_FIELDS:
                raise ValueError(f"{path}: expected columns " + "\t".join(OPERATION_FIELDS))
            for line, row in enumerate(reader, 2):
                name = _identifier(row["field"].strip(), f"{path}:{line} field")
                if name in seen:
                    raise ValueError(f"{path}:{line}: duplicate field {name}")
                seen.add(name)
                required = row["required"].strip()
                if required not in {"0", "1"}:
                    raise ValueError(f"{path}:{line}: required must be 0 or 1")
                field_type = row["type"].strip()
                if field_type not in FIELD_TYPES:
                    raise ValueError(f"{path}:{line}: unsupported type {field_type!r}")
                fields.append(OperationField(name, required == "1", field_type))
        if not fields:
            raise ValueError(f"{path}: empty operation contract")
        contracts[operation] = tuple(fields)
    if not contracts:
        raise ValueError(f"{directory}: no operation contracts")
    return contracts


def _validate_operation(
    edit: dict[str, object],
    label: str,
    contracts: dict[str, tuple[OperationField, ...]],
) -> str:
    operation = edit.get("operation")
    if not isinstance(operation, str) or operation not in contracts:
        raise ValueError(f"{label}.operation is unsupported: {operation!r}")
    contract = contracts[operation]
    allowed = {field.name for field in contract}
    if set(edit) - allowed:
        raise ValueError(f"{label} has unknown fields: {sorted(set(edit) - allowed)}")
    missing = sorted(field.name for field in contract if field.required and field.name not in edit)
    if missing:
        raise ValueError(f"{label} is missing required fields: {missing}")
    expectation_fields = [
        field.name for field in contract if field.name.startswith("expected_")
    ]
    if len(expectation_fields) > 1:
        present = [field for field in expectation_fields if field in edit]
        if len(present) != 1:
            raise ValueError(
                f"{label} requires exactly one destination expectation: "
                f"{expectation_fields}"
            )
    for field in contract:
        if field.name not in edit:
            continue
        value = edit[field.name]
        field_label = f"{label}.{field.name}"
        if field.type == "integer":
            _parse_int(value, field_label)
        elif field.type == "integer_list":
            _parse_int_list(value, field_label)
        elif field.type == "hex":
            _hex(value, field_label)
        elif field.type == "sha256":
            _sha256(value, field_label)
        elif field.type == "path":
            _relative_path(value, field_label)
        elif not isinstance(value, str):
            raise ValueError(f"{field_label} must be text")
    if operation == "replace":
        replacements = [
            field for field in ("replacement_hex", "adapter") if field in edit
        ]
        if len(replacements) != 1:
            raise ValueError(
                f"{label} requires exactly one of replacement_hex or adapter"
            )
        fixed_fields = {
            field for field in ("expected_value", "replacement_value")
            if field in edit
        }
        if "adapter" in edit:
            fixed_adapter = binary_adapters.is_fixed_value_adapter(edit["adapter"])
            if fixed_adapter and fixed_fields != {
                "expected_value", "replacement_value"
            }:
                raise ValueError(
                    f"{label}.adapter requires expected_value and replacement_value"
                )
            if not fixed_adapter and fixed_fields:
                raise ValueError(
                    f"{label}.adapter does not accept fixed value fields"
                )
        elif fixed_fields:
            raise ValueError(f"{label} fixed value fields require an adapter")
    return operation


def _group_id(node: CatalogNode) -> str:
    path = node.path[1:] if node.path[:1] == ("features",) else node.path
    return ".".join(path[:-1]) or node.feature_id


def _internal_patch(node: CatalogNode) -> binary_patcher.Patch:
    return binary_patcher.Patch(
        patch_id=node.node_id,
        group_id=_group_id(node),
        enabled=node.enabled,
        status="approved_for_test",
        confidence="verified",
        name=node.path[-1],
        description=_description(node.description, node.node_id),
        evidence_id="",
        review_notes="",
    )


def _groups(nodes: list[CatalogNode]) -> dict[str, binary_patcher.Group]:
    groups: dict[str, binary_patcher.Group] = {}
    for node in nodes:
        group_id = _group_id(node)
        if group_id in groups:
            continue
        groups[group_id] = binary_patcher.Group(
            group_id=group_id,
            enabled=True,
            name=node.path[-2] if len(node.path) > 1 else node.feature_id,
            description="",
            review_notes="",
        )
    return groups


def load_binary_package(
    selection: CatalogSelection,
    feature_id: str,
    targets_path: Path,
    repository: Path,
    operations_path: Path,
) -> binary_patcher.Package:
    nodes = [
        node
        for node in selection.feature_nodes(feature_id)
        if node.enabled and node.edit_ids
    ]
    targets = binary_patcher.load_targets(targets_path)
    contracts = load_operation_contracts(operations_path)
    patches = {node.node_id: _internal_patch(node) for node in nodes}
    edits: list[binary_patcher.Edit] = []
    used_targets: set[str] = set()
    order = 0
    for node in nodes:
        for edit_key in node.edit_ids:
            raw_edit = selection.edits[edit_key]
            label = f"edits.{edit_key}"
            operation = _validate_operation(raw_edit, label, contracts)
            destination_id = str(raw_edit["destination_target_id"])
            if destination_id not in targets:
                raise ValueError(f"{label}: unknown destination target {destination_id!r}")
            expected_hex = ""
            expected_sha256 = ""
            if "expected_hex" in raw_edit:
                expected_hex = _hex(raw_edit["expected_hex"], f"{label}.expected_hex")
            if "expected_sha256" in raw_edit:
                expected_sha256 = _sha256(raw_edit["expected_sha256"], f"{label}.expected_sha256")
            destination_offsets = _parse_int_list(
                raw_edit["destination_offsets"],
                f"{label}.destination_offsets",
            )
            replacement_hex = ""
            source_id = ""
            source_offset: int | None = None
            blob_path: PurePosixPath | None = None
            blob_sha256 = ""
            fill_hex = ""
            if operation == "replace":
                if "adapter" in raw_edit:
                    if binary_adapters.is_fixed_value_adapter(raw_edit["adapter"]):
                        if node.has_configured_value:
                            raise ValueError(
                                f"{label}.adapter requires a bare catalog setting"
                            )
                        expected_hex, replacement_hex = (
                            binary_adapters.apply_fixed_adapter(
                                raw_edit["adapter"],
                                raw_edit["expected_value"],
                                raw_edit["replacement_value"],
                                encoding=raw_edit.get("encoding"),
                                length=raw_edit.get("length"),
                            )
                        )
                    else:
                        if not node.has_configured_value:
                            raise ValueError(
                                f"{label}.adapter requires a typed catalog setting"
                            )
                        if not expected_hex or "expected_sha256" in raw_edit:
                            raise ValueError(
                                f"{label}.adapter requires expected_hex, not expected_sha256"
                            )
                        replacement_hex = binary_adapters.apply_adapter(
                            raw_edit["adapter"], expected_hex, node.configured_value
                        )
                else:
                    replacement_hex = _hex(
                        raw_edit["replacement_hex"], f"{label}.replacement_hex"
                    )
                length = len(bytes.fromhex(replacement_hex))
            elif operation == "copy":
                length = _parse_int(raw_edit["length"], f"{label}.length", minimum=1)
                source_id = str(raw_edit["source_target_id"])
                source_offset = _parse_int(raw_edit["source_offset"], f"{label}.source_offset")
                if source_id not in targets:
                    raise ValueError(f"{label}: unknown source target {source_id!r}")
                used_targets.add(source_id)
            elif operation == "blob":
                blob_path = _relative_path(raw_edit["blob_path"], f"{label}.blob_path")
                blob_sha256 = _sha256(raw_edit["blob_sha256"], f"{label}.blob_sha256")
                blob_file = repository.joinpath(*blob_path.parts)
                if not blob_file.is_file():
                    raise FileNotFoundError(blob_file)
                length = blob_file.stat().st_size
            else:
                length = _parse_int(raw_edit["length"], f"{label}.length", minimum=1)
                fill_hex = _hex(raw_edit["fill_hex"], f"{label}.fill_hex")
                if len(bytes.fromhex(fill_hex)) != 1:
                    raise ValueError(f"{label}.fill_hex must be exactly one byte")
            if expected_hex and len(bytes.fromhex(expected_hex)) != length:
                raise ValueError(f"{label}.expected_hex length mismatch")
            used_targets.add(destination_id)
            reason = _description(raw_edit.get("description"), label)
            multiple_destinations = len(destination_offsets) > 1
            for destination_offset in destination_offsets:
                order += 1
                edit_id = f"{node.node_id}.{edit_key}"
                if multiple_destinations:
                    edit_id += f".at_{destination_offset:08x}"
                edits.append(
                    binary_patcher.Edit(
                        edit_id=edit_id,
                        patch_id=node.node_id,
                        order=order,
                        destination_target_id=destination_id,
                        destination_offset=destination_offset,
                        operation=operation,
                        length=length,
                        expected_hex=expected_hex,
                        expected_sha256=expected_sha256,
                        replacement_hex=replacement_hex,
                        source_target_id=source_id,
                        source_offset=source_offset,
                        source_expected_hex="",
                        source_expected_sha256="",
                        blob_path=blob_path,
                        blob_offset=0 if blob_path is not None else None,
                        blob_sha256=blob_sha256,
                        fill_hex=fill_hex,
                        reason=reason,
                    )
                )
    return binary_patcher.Package(
        directory=repository,
        package_id=f"{feature_id}.binary_patcher",
        targets={key: value for key, value in targets.items() if key in used_targets},
        groups=_groups(nodes),
        patches=patches,
        edits=edits,
    )


def payload_entries(
    selection: CatalogSelection,
    feature_id: str,
) -> list[tuple[CatalogNode, str, str, dict[str, object]]]:
    entries: list[tuple[CatalogNode, str, str, dict[str, object]]] = []
    seen_payloads: set[str] = set()
    for node, injection_id, injection in injection_entries(selection, feature_id):
        if not node.enabled:
            continue
        payload = injection.get("payload")
        if not isinstance(payload, dict):
            continue
        for payload_id, value in payload.items():
            if not runtime_injector.IDENTIFIER.fullmatch(payload_id):
                raise ValueError(
                    f"injections.{injection_id}.payload key is invalid: "
                    f"{payload_id!r}"
                )
            if payload_id in seen_payloads:
                raise ValueError(
                    f"Duplicate payload declaration {payload_id!r} in {feature_id}"
                )
            seen_payloads.add(payload_id)
            if not isinstance(value, dict):
                raise ValueError(
                    f"injections.{injection_id}.payload.{payload_id} must be an object"
                )
            entries.append((node, injection_id, payload_id, value))
    return entries


def injection_entries(
    selection: CatalogSelection,
    feature_id: str,
) -> list[tuple[CatalogNode, str, dict[str, object]]]:
    entries: list[tuple[CatalogNode, str, dict[str, object]]] = []
    references: dict[str, list[CatalogNode]] = {}
    for node in selection.feature_nodes(feature_id):
        for injection_id in node.injection_ids:
            references.setdefault(injection_id, []).append(node)
    for injection_id, nodes in references.items():
        representative = replace(
            nodes[0],
            enabled=any(node.enabled for node in nodes),
        )
        entries.append(
            (representative, injection_id, selection.injections[injection_id])
        )
    return entries


def _source_path(repository: Path, value: object, label: str) -> Path:
    relative = _relative_path(value, label)
    path = repository.joinpath(*relative.parts).resolve()
    try:
        path.relative_to(repository.resolve())
    except ValueError as exc:
        raise ValueError(f"{label} escapes the repository") from exc
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def load_static_fragment(
    repository: Path,
    owner: str,
    fragment_id: str,
    value: dict[str, object],
    label: str,
) -> tuple[int, PayloadFragment]:
    kind = value.get("kind")
    if kind not in FRAGMENT_KINDS:
        raise ValueError(f"{label}.kind is invalid: {kind!r}")
    order = _parse_int(value.get("order"), f"{label}.order", minimum=1)
    alignment = _parse_int(value.get("alignment"), f"{label}.alignment", minimum=1)
    if alignment & (alignment - 1):
        raise ValueError(f"{label}.alignment must be a power of two")
    has_value = "value" in value
    has_blob = "blob_path" in value
    if has_value == has_blob:
        raise ValueError(f"{label} requires exactly one of value or blob_path")
    if has_value:
        payload = bytes.fromhex(_hex(value["value"], f"{label}.value"))
    else:
        blob = _source_path(repository, value["blob_path"], f"{label}.blob_path")
        if hashlib.sha256(blob.read_bytes()).hexdigest().upper() != _sha256(
            value.get("blob_sha256"), f"{label}.blob_sha256"
        ):
            raise ValueError(f"{label}: blob SHA-256 mismatch")
        blob_offset = _parse_int(value.get("blob_offset", 0), f"{label}.blob_offset")
        length = _parse_int(value.get("length"), f"{label}.length", minimum=1)
        payload = blob.read_bytes()[blob_offset:blob_offset + length]
        if len(payload) != length:
            raise ValueError(f"{label}: blob range is incomplete")
    relocations: list[PayloadRelocation] = []
    raw_relocations = value.get("relocations", {})
    if not isinstance(raw_relocations, dict):
        raise ValueError(f"{label}.relocations must be an object")
    for relocation_id, raw in raw_relocations.items():
        _identifier(relocation_id, f"{label}.relocations key")
        if not isinstance(raw, dict):
            raise ValueError(f"{label}.relocations.{relocation_id} must be an object")
        encoding = raw.get("encoding")
        if encoding not in RELOCATION_KINDS:
            raise ValueError(f"{label}.relocations.{relocation_id}.encoding is invalid")
        symbol = raw.get("symbol")
        if not isinstance(symbol, str) or not runtime_injector.IDENTIFIER.fullmatch(symbol):
            raise ValueError(f"{label}.relocations.{relocation_id}.symbol is invalid")
        relocations.append(
            PayloadRelocation(
                offset=_parse_int(raw.get("offset"), f"{label}.relocations.{relocation_id}.offset"),
                kind=encoding,
                symbol=symbol,
                addend=_parse_int(raw.get("addend", 0), f"{label}.relocations.{relocation_id}.addend", minimum=-0x80000000),
            )
        )
    return order, PayloadFragment(
        owner=owner,
        symbol=fragment_id,
        kind=str(kind),
        alignment=alignment,
        payload=payload,
        relocations=tuple(relocations),
        init=value.get("init", False) is True,
    )


def _compile_source(
    repository: Path,
    owner: str,
    source_id: str,
    value: dict[str, object],
    label: str,
) -> list[tuple[int, PayloadFragment]]:
    source_path = _source_path(repository, value.get("path"), f"{label}.path")
    namespace = value.get("namespace")
    if not isinstance(namespace, str) or not runtime_injector.IDENTIFIER.fullmatch(namespace):
        raise ValueError(f"{label}.namespace is invalid")
    raw_imports = value.get("imports", {})
    if not isinstance(raw_imports, dict):
        raise ValueError(f"{label}.imports must be an object")
    imports: dict[str, ee_c_fragments.SymbolReference] = {}
    for name, raw in raw_imports.items():
        if not runtime_injector.IDENTIFIER.fullmatch(name):
            raise ValueError(f"{label}.imports key is invalid: {name!r}")
        if isinstance(raw, str):
            symbol = raw
            addend = 0
        elif isinstance(raw, dict):
            symbol = raw.get("symbol")
            addend = _parse_int(raw.get("addend", 0), f"{label}.imports.{name}.addend", minimum=-0x80000000)
        else:
            raise ValueError(f"{label}.imports.{name} must be text or an object")
        if not isinstance(symbol, str) or not runtime_injector.IDENTIFIER.fullmatch(symbol):
            raise ValueError(f"{label}.imports.{name}.symbol is invalid")
        imports[name] = ee_c_fragments.SymbolReference(symbol, addend)
    raw_fragments = value.get("fragments")
    if not isinstance(raw_fragments, dict) or not raw_fragments:
        raise ValueError(f"{label}.fragments must be a non-empty object")
    aliases: dict[str, tuple[int, str]] = {}
    for fragment_id, raw in raw_fragments.items():
        if not runtime_injector.IDENTIFIER.fullmatch(fragment_id) or not isinstance(raw, dict):
            raise ValueError(f"{label}.fragments.{fragment_id} is invalid")
        object_fragment = raw.get("object")
        if not isinstance(object_fragment, str) or not runtime_injector.IDENTIFIER.fullmatch(object_fragment):
            raise ValueError(f"{label}.fragments.{fragment_id}.object is invalid")
        aliases[object_fragment] = (
            _parse_int(raw.get("order"), f"{label}.fragments.{fragment_id}.order", minimum=1),
            fragment_id,
        )
    packaged_object = source_path.with_name(source_path.name + ".o")
    if packaged_object.is_file():
        extracted = ee_c_fragments.extract_ee_object(
            packaged_object,
            namespace=namespace,
            owner=owner,
            external_symbols=imports,
        )
    else:
        toolchain = ee_c_fragments.default_toolchain_bin(repository)
        with tempfile.TemporaryDirectory(prefix="na2-catalog-c-") as temporary:
            extracted = ee_c_fragments.compile_and_extract(
                source_path,
                Path(temporary) / f"{source_id}.o",
                namespace=namespace,
                toolchain_bin=toolchain,
                owner=owner,
                external_symbols=imports,
            )
    actual = {fragment.symbol for fragment in extracted.fragments}
    if actual != set(aliases):
        raise ValueError(
            f"{label}: extracted fragments differ from declarations; "
            f"missing={sorted(set(aliases) - actual)}, extra={sorted(actual - set(aliases))}"
        )
    result: list[tuple[int, PayloadFragment]] = []
    symbol_aliases = {source: target[1] for source, target in aliases.items()}
    for fragment in extracted.fragments:
        order, fragment_id = aliases[fragment.symbol]
        result.append(
            (
                order,
                PayloadFragment(
                    owner=owner,
                    symbol=fragment_id,
                    kind=fragment.kind,
                    alignment=fragment.alignment,
                    payload=fragment.payload,
                    relocations=tuple(
                        PayloadRelocation(
                            offset=item.offset,
                            kind=item.kind,
                            symbol=symbol_aliases.get(item.symbol, item.symbol),
                            addend=item.addend,
                        )
                        for item in fragment.relocations
                    ),
                    init=fragment.init,
                ),
            )
        )
    return result


def load_runtime_package(
    selection: CatalogSelection,
    feature_id: str,
    targets_path: Path,
    repository: Path,
    owner: str,
) -> runtime_injector.RuntimeInjectionPackage:
    runtime_entries = injection_entries(selection, feature_id)
    hook_entries = [
        (node, injection_id, injection)
        for node, injection_id, injection in runtime_entries
        if node.enabled
        and isinstance(injection.get("hooks"), dict)
        and injection["hooks"]
    ]
    hook_nodes = [node for node, _, _ in hook_entries]
    targets = binary_patcher.load_targets(targets_path)
    patches = {node.node_id: _internal_patch(node) for node in hook_nodes}
    edits: list[runtime_injector.RuntimeSymbolicEdit] = []
    used_targets: set[str] = set()
    order = 0
    for node, injection_id, injection in hook_entries:
        raw_hooks = injection["hooks"]
        assert isinstance(raw_hooks, dict)
        for hook_key, raw in raw_hooks.items():
            _identifier(hook_key, f"injections.{injection_id}.hooks key")
            if not isinstance(raw, dict):
                raise ValueError(
                    f"injections.{injection_id}.hooks.{hook_key} must be an object"
                )
            label = f"injections.{injection_id}.hooks.{hook_key}"
            allowed = {
                "description", "target_id", "offset", "expected_hex",
                "replacement_hex", "relocation_offset", "symbol", "encoding", "addend",
            }
            if set(raw) - allowed:
                raise ValueError(f"{label} has unknown fields: {sorted(set(raw) - allowed)}")
            target_id = raw.get("target_id")
            if not isinstance(target_id, str) or target_id not in targets:
                raise ValueError(f"{label}.target_id is invalid")
            expected = bytes.fromhex(_hex(raw.get("expected_hex"), f"{label}.expected_hex"))
            template_hex = _hex(raw.get("replacement_hex", ""), f"{label}.replacement_hex", allow_empty=True)
            template = bytes.fromhex(template_hex) if template_hex else bytes(len(expected))
            if len(template) != len(expected):
                raise ValueError(f"{label}.replacement_hex length mismatch")
            symbol = raw.get("symbol")
            encoding = raw.get("encoding")
            if not isinstance(symbol, str) or not runtime_injector.IDENTIFIER.fullmatch(symbol):
                raise ValueError(f"{label}.symbol is invalid")
            if encoding not in RELOCATION_KINDS:
                raise ValueError(f"{label}.encoding is invalid")
            order += 1
            used_targets.add(target_id)
            mapping_id = f"{node.node_id}.{hook_key}"
            edits.append(
                runtime_injector.RuntimeSymbolicEdit(
                    edit_id=mapping_id,
                    patch_id=node.node_id,
                    order=order,
                    target_id=target_id,
                    symbolic_patch=SymbolicPatch(
                        owner=owner,
                        path=targets[target_id].path.as_posix(),
                        offset=_parse_int(raw.get("offset"), f"{label}.offset"),
                        expected=expected,
                        symbol=symbol,
                        encoding=str(encoding),
                        mapping_id=mapping_id,
                        kind=_group_id(node),
                        reason=_description(raw.get("description"), label),
                        addend=_parse_int(raw.get("addend", 0), f"{label}.addend", minimum=-0x80000000),
                        replacement_template=template,
                        relocation_offset=_parse_int(raw.get("relocation_offset", 0), f"{label}.relocation_offset"),
                    ),
                )
            )
    declared: list[tuple[int, PayloadFragment]] = []
    for _, injection_id, payload_id, raw in payload_entries(selection, feature_id):
        label = f"injections.{injection_id}.payload.{payload_id}"
        if raw.get("kind") == "c":
            declared.extend(_compile_source(repository, owner, payload_id, raw, label))
        else:
            declared.append(
                load_static_fragment(repository, owner, payload_id, raw, label)
            )
    orders = [item[0] for item in declared]
    symbols = [item[1].symbol for item in declared]
    if len(orders) != len(set(orders)):
        raise ValueError(f"{feature_id}: payload orders must be unique")
    if len(symbols) != len(set(symbols)):
        raise ValueError(f"{feature_id}: payload symbols must be unique")
    return runtime_injector.RuntimeInjectionPackage(
        directory=repository,
        owner=owner,
        targets={key: value for key, value in targets.items() if key in used_targets},
        groups=_groups(hook_nodes),
        patches=patches,
        fragments=tuple(item[1] for item in sorted(declared, key=lambda item: item[0])),
        edits=tuple(edits),
    )


def feature_reference_ids(
    selection: CatalogSelection,
    feature_id: str,
    field: str,
) -> tuple[str, ...]:
    prefixes = {"edits": "e__", "injections": "i__", "string_patches": "s__"}
    if field not in prefixes:
        raise ValueError(f"Unsupported catalog implementation field: {field}")
    if feature_id not in selection.catalog:
        raise ValueError(f"Unknown catalog feature: {feature_id}")
    prefix = prefixes[field]
    return tuple(
        dict.fromkeys(
            patch
            for patch in _catalog_patches(selection.catalog[feature_id])
            if patch.startswith(prefix)
        )
    )


def feature_has(
    selection: CatalogSelection,
    feature_id: str,
    field: str,
    *,
    enabled_only: bool = False,
) -> bool:
    if field == "edits":
        references = (
            tuple(
                edit_id
                for node in selection.feature_nodes(feature_id)
                if node.enabled
                for edit_id in node.edit_ids
            )
            if enabled_only
            else feature_reference_ids(selection, feature_id, "edits")
        )
        return bool(references)
    if field == "injections":
        references = (
            tuple(
                injection_id
                for node in selection.feature_nodes(feature_id)
                if node.enabled
                for injection_id in node.injection_ids
            )
            if enabled_only
            else feature_reference_ids(selection, feature_id, "injections")
        )
        return any(
            isinstance(selection.injections[injection_id].get("hooks"), dict)
            and selection.injections[injection_id]["hooks"]
            for injection_id in references
        )
    if field == "string_patches":
        references = (
            tuple(
                patch_id
                for node in selection.feature_nodes(feature_id)
                if node.enabled
                for patch_id in node.string_patch_ids
            )
            if enabled_only
            else feature_reference_ids(selection, feature_id, "string_patches")
        )
        return bool(references)
    raise ValueError(f"Unsupported catalog implementation field: {field}")


def selected_string_patches(
    selection: CatalogSelection,
    operation: str,
) -> tuple[tuple[CatalogNode, str, dict[str, object]], ...]:
    """Return enabled semantic string patches for one supported operation."""
    return tuple(
        (node, patch_id, selection.string_patches[patch_id])
        for node in selection.nodes
        if node.enabled
        for patch_id in node.string_patch_ids
        if selection.string_patches[patch_id]["operation"] == operation
    )


def referenced_files(selection: CatalogSelection, repository: Path, feature_id: str) -> tuple[Path, ...]:
    files: set[Path] = set()
    for edit_id in feature_reference_ids(selection, feature_id, "edits"):
        raw = selection.edits[edit_id]
        if "blob_path" in raw:
            files.add(
                _source_path(
                    repository,
                    raw["blob_path"],
                    f"edits.{edit_id}.blob_path",
                )
            )
    for injection_id in feature_reference_ids(selection, feature_id, "injections"):
        injection = selection.injections[injection_id]
        payload = injection.get("payload")
        if not isinstance(payload, dict):
            continue
        for payload_id, raw in payload.items():
            if not isinstance(raw, dict):
                continue
            if raw.get("kind") == "c":
                files.add(
                    _source_path(
                        repository,
                        raw.get("path"),
                        f"injections.{injection_id}.payload.{payload_id}.path",
                    )
                )
            elif "blob_path" in raw:
                files.add(
                    _source_path(
                        repository,
                        raw["blob_path"],
                        f"injections.{injection_id}.payload.{payload_id}.blob_path",
                    )
                )
    return tuple(sorted(files, key=lambda path: path.as_posix()))
