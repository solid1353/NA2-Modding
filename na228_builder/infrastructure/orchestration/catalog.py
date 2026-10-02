from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import dataclass, replace
from functools import cached_property
from pathlib import Path, PurePosixPath

from ..modules.binary_patcher import adapters as binary_adapters
from ..modules.binary_patcher import engine as binary_patcher
from ..modules.runtime_injector import engine as runtime_injector
from ..modules.payload_builder import ee_c_fragments
from ..common import SYMBOL_PATTERN, UINT64_MAX, key_problems, read_tsv, sha256_hex
from . import catalog_format
from . import jsonc
from ..modules.payload_builder.operations import (
    FRAGMENT_KINDS,
    RELOCATION_KINDS,
    PayloadFragment,
    PayloadRelocation,
    SymbolicPatch,
)


PATCH_ID = re.compile(r"[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*\Z")
OPERATION_FIELDS = ["field", "required", "type"]
FIELD_TYPES = {"hex", "integer", "integer_list", "path", "sha256", "text"}
SOURCE_PAYLOAD_FIELDS = {
    "kind",
    "path",
    "namespace",
    "imports",
    "fragments",
    "resources",
}
SOURCE_FRAGMENT_FIELDS = {"object", "abi", "description"}
STATIC_PAYLOAD_FIELDS = {
    "kind",
    "alignment",
    "value",
    "blob_path",
    "blob_sha256",
    "blob_offset",
    "length",
    "relocations",
    "init",
}
IMPORT_FIELDS = {"symbol", "addend"}
RELOCATION_FIELDS = {"offset", "encoding", "symbol", "addend"}


class ConfigurationError(ValueError):
    """A user-supplied configuration does not satisfy the catalog contract."""


def parse_build_overrides(value: str | None) -> dict[str, object] | None:
    if value is None:
        return None
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ConfigurationError("Build overrides must be a JSON object")
    return parsed


@dataclass(frozen=True)
class StartupFastForwardFrames:
    additive: int | None = None
    override: int | None = None


@dataclass(frozen=True)
class CatalogNode:
    path: tuple[str, ...]
    enabled: bool
    patch: str | None = None
    description: str = ""
    configured_value: object = None
    has_configured_value: bool = False
    startup_fast_forward_frames: StartupFastForwardFrames | None = None
    modules: tuple[str, ...] = ()

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

@dataclass(frozen=True)
class CatalogSelection:
    catalog_path: Path
    patch_files: tuple[Path, ...]
    base_configuration_path: Path | None
    configuration_path: Path
    catalog: dict[str, catalog_format.CatalogNodeExpression]
    patches: dict[str, dict[str, object]]
    edits: dict[str, dict[str, object]]
    injections: dict[str, dict[str, object]]
    string_patches: dict[str, dict[str, object]]
    nodes: tuple[CatalogNode, ...]
    effective_configuration: object
    supplied_overrides: dict[str, object] | None

    @cached_property
    def patch_nodes(self) -> tuple[CatalogNode, ...]:
        return _included_patch_nodes(self.nodes, self.patches)

    def feature_patch_nodes(self, feature_id: str) -> tuple[CatalogNode, ...]:
        return tuple(node for node in self.patch_nodes if node.feature_id == feature_id)

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


    @cached_property
    def nodes_by_path(self) -> dict[tuple[str, ...], CatalogNode]:
        return {node.path: node for node in self.nodes}

    def node(self, *path: str) -> CatalogNode:
        try:
            return self.nodes_by_path[path]
        except KeyError:
            raise ValueError(f"Catalog selection has no node: {'.'.join(path)}") from None

    def node_enabled(self, *path: str) -> bool:
        return self.node(*path).enabled


@dataclass(frozen=True)
class OperationField:
    name: str
    required: bool
    type: str


def _read_json(path: Path, label: str, *, comments: bool = False) -> dict[str, object]:
    """Read a non-empty JSON object, or JSONC when comments are allowed."""
    def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
        value: dict[str, object] = {}
        for key, item in pairs:
            if key in value:
                raise ValueError(f"{label} contains duplicate key {key!r}")
            value[key] = item
        return value

    loads = jsonc.loads if comments else json.loads
    try:
        value = loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    except json.JSONDecodeError as exc:
        kind = "JSONC" if comments else "JSON"
        raise ValueError(f"{label} is not valid {kind}: {path}") from exc
    if not isinstance(value, dict) or not value:
        raise ValueError(f"{label} root must be a non-empty object")
    return value



def _read_catalog(path: Path) -> dict[str, catalog_format.CatalogNodeExpression]:
    catalog_file = path.resolve()
    if not catalog_file.is_file():
        raise FileNotFoundError(catalog_file)
    root = catalog_format.parse_catalog(catalog_file)
    root_fields = _container_fields(root)
    if set(root_fields) != {"features"}:
        raise ValueError("Catalog root must contain only the features object")
    feature_root = root_fields["features"]
    if not isinstance(feature_root, catalog_format.ContainerNode):
        raise ValueError("Catalog features must be an object")
    features = _container_fields(feature_root)
    if not features:
        raise ValueError(f"Catalog contains no features: {catalog_file}")
    for feature_id in features:
        _identifier(feature_id, "Catalog feature ID")
    patch_ids = [
        patch_id
        for feature in features.values()
        for patch_id in _catalog_patches(feature)
    ]
    duplicate_patch_ids = sorted(
        patch_id for patch_id in set(patch_ids) if patch_ids.count(patch_id) > 1
    )
    if duplicate_patch_ids:
        raise ValueError(
            "Catalog patch IDs must each be referenced exactly once: "
            + ", ".join(duplicate_patch_ids)
        )
    for feature_id, feature in features.items():
        for patch_id, expected in _catalog_patch_names(feature, (feature_id,)):
            if patch_id != expected:
                raise ValueError(
                    f"Catalog patch {patch_id!r} must be named after its node: {expected!r}"
                )
    return features


def _source_location(patch_id: str, path: str, catalog_path: Path, label: str) -> None:
    """A source under patches/ lives in its patch's directory or in an ancestor's."""
    prefix = f"{catalog_path.parent.name}/patches/"
    if not path.startswith(prefix):
        return
    directory = PurePosixPath(path[len(prefix):]).parent.parts
    owner = tuple(patch_id.split("."))
    if directory[: len(owner)] != owner and owner[: len(directory)] != directory:
        raise ValueError(
            f"{label}.path must be under patches/{'/'.join(owner)}/ or a parent directory: {path}"
        )


def _identifier(value: str, label: str) -> str:
    if not catalog_format.IDENTIFIER.fullmatch(value):
        raise ValueError(f"{label} must be a meaningful snake_case key: {value!r}")
    return value


def _patch_identifier(value: str, label: str) -> str:
    if not PATCH_ID.fullmatch(value):
        raise ValueError(f"{label} must be a dotted meaningful snake_case key: {value!r}")
    return value


def _description(value: object, label: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError(f"{label} description must be text")
    if not value.strip():
        raise ValueError(f"{label} description must be nonempty")
    return value


def _validate_fields(
    value: dict[str, object],
    allowed: set[str],
    label: str,
    *,
    required: set[str] | None = None,
) -> None:
    missing = sorted((required or set()) - set(value))
    extra = sorted(set(value) - allowed)
    if missing:
        raise ValueError(f"{label} is missing fields: {missing}")
    if extra:
        raise ValueError(f"{label} has unknown fields: {extra}")


def _optional_text(value: object, label: str) -> None:
    if value is not None and (not isinstance(value, str) or not value.strip()):
        raise ValueError(f"{label} must be nonempty text")


def _container_fields(
    node: catalog_format.ContainerNode,
) -> dict[str, catalog_format.CatalogNodeExpression]:
    return {field.name: field.node for field in node.fields}


def _feature_root(
    features: dict[str, catalog_format.CatalogNodeExpression],
) -> catalog_format.ContainerNode:
    return catalog_format.ContainerNode(
        tuple(
            catalog_format.ContainerField(feature_id, features[feature_id])
            for feature_id in features
        )
    )


def _catalog_patch_names(
    node: catalog_format.CatalogNodeExpression,
    path: tuple[str, ...],
) -> tuple[tuple[str, str], ...]:
    """Each referenced patch with the ID its node path gives it; a setting branch of a
    union adds its literal value."""
    if isinstance(node, catalog_format.SettingNode):
        return ((node.patch, ".".join(path)),) if node.patch else ()
    if isinstance(node, catalog_format.ContainerNode):
        return (
            *(((node.patch, ".".join(path)),) if node.patch else ()),
            *(
                named
                for field in node.fields
                for named in _catalog_patch_names(field.node, (*path, field.name))
            ),
        )
    if isinstance(node, catalog_format.UnionNode):
        return tuple(
            named
            for branch in node.branches
            for named in _catalog_patch_names(
                branch,
                (*path, branch.value_type.value)
                if isinstance(branch, catalog_format.SettingNode)
                and isinstance(branch.value_type, catalog_format.LiteralType)
                and isinstance(branch.value_type.value, str)
                else path,
            )
        )
    if isinstance(node, catalog_format.IntersectionNode):
        return tuple(
            named
            for operand in node.operands
            for named in _catalog_patch_names(operand, path)
        )
    return ()


def _catalog_patches(
    node: catalog_format.CatalogNodeExpression,
) -> tuple[str, ...]:
    if isinstance(node, catalog_format.SettingNode):
        return (node.patch,) if node.patch else ()
    if isinstance(node, catalog_format.ContainerNode):
        return (
            *((node.patch,) if node.patch else ()),
            *(
                patch
                for field in node.fields
                for patch in _catalog_patches(field.node)
            ),
        )
    if isinstance(node, catalog_format.UnionNode):
        return tuple(
            patch
            for branch in node.branches
            for patch in _catalog_patches(branch)
        )
    if isinstance(node, catalog_format.IntersectionNode):
        return tuple(
            patch
            for operand in node.operands
            for patch in _catalog_patches(operand)
        )
    if isinstance(node, catalog_format.FalseNode):
        return ()
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


def _setting_configured_value(
    node: catalog_format.SettingNode,
    value: object,
) -> object:
    if (
        value is True
        and node.value_type is not None
        and catalog_format.matches_type(node.value_type, {})
    ):
        return {}
    return value


def _matches_configuration_node(
    node: catalog_format.CatalogNodeExpression,
    value: object,
) -> bool:
    if isinstance(node, catalog_format.SettingNode):
        configured = _setting_configured_value(node, value)
        if node.value_type is None:
            return configured is True or configured is False
        return catalog_format.matches_type(node.value_type, configured)
    if isinstance(node, catalog_format.FalseNode):
        return value is False
    return catalog_format.matches_type(catalog_format.active_type(node), value)


def _validate_configuration_value(
    node: catalog_format.CatalogNodeExpression,
    value: object,
    path: tuple[str, ...],
) -> None:
    label = ".".join(path)
    if isinstance(node, catalog_format.SettingNode):
        if node.value_type is None:
            if value is not True and value is not False:
                raise _invalid_configuration_value(path, value, "true or false")
        else:
            configured = _setting_configured_value(node, value)
            if catalog_format.matches_type(node.value_type, configured):
                return
            expected = " ".join(catalog_format.type_text(node.value_type).split())
            if catalog_format.matches_type(node.value_type, {}):
                expected += ", or true for an empty object"
            raise _invalid_configuration_value(path, value, expected)
        return
    if isinstance(node, catalog_format.FalseNode):
        if value is not False:
            raise _invalid_configuration_value(path, value, "false")
        return
    if isinstance(node, catalog_format.ContainerNode):
        if not isinstance(value, dict):
            raise _invalid_configuration_value(path, value, "an object")
        fields = _container_fields(node)
        problems = key_problems(value, fields)
        if problems:
            raise ConfigurationError(f"Invalid config object at {label}: {problems}")
        for key, child in fields.items():
            _validate_configuration_value(child, value[key], (*path, key))
        return
    if isinstance(node, catalog_format.IntersectionNode):
        _validate_configuration_value(catalog_format.expand_node(node), value, path)
        return
    if isinstance(node, catalog_format.UnionNode):
        matches = [
            branch
            for branch in node.branches
            if _matches_configuration_node(branch, value)
        ]
        if len(matches) != 1:
            expected = " ".join(
                catalog_format.type_text(catalog_format.active_type(node)).split()
            )
            raise _invalid_configuration_value(
                path,
                value,
                f"exactly one of {expected}",
            )
        _validate_configuration_value(matches[0], value, path)
        return
    raise TypeError(type(node))


def _intersection_merge_parts(
    node: catalog_format.IntersectionNode,
) -> tuple[
    dict[str, catalog_format.CatalogNodeExpression],
    catalog_format.UnionNode | None,
]:
    shared_fields: dict[str, catalog_format.CatalogNodeExpression] = {}
    branch_operands: list[catalog_format.UnionNode] = []
    for operand in node.operands:
        expanded = (
            operand
            if isinstance(operand, catalog_format.ContainerNode)
            else catalog_format.expand_node(operand)
        )
        if isinstance(expanded, catalog_format.ContainerNode):
            for field in expanded.fields:
                if field.name in shared_fields:
                    raise TypeError(
                        f"duplicate validated intersection field {field.name}"
                    )
                shared_fields[field.name] = field.node
            continue
        if isinstance(expanded, catalog_format.UnionNode):
            branch_operands.append(expanded)
            continue
        raise TypeError(type(expanded))

    if not branch_operands:
        return shared_fields, None
    if len(branch_operands) == 1:
        return shared_fields, branch_operands[0]
    branch_node = catalog_format.expand_node(
        catalog_format.IntersectionNode(tuple(branch_operands))
    )
    if not isinstance(branch_node, catalog_format.UnionNode):
        raise TypeError(type(branch_node))
    return shared_fields, branch_node


def _merge_intersection_configuration_value(
    node: catalog_format.IntersectionNode,
    base: object,
    override: object,
    path: tuple[str, ...],
) -> object:
    if not isinstance(override, dict):
        raise _invalid_configuration_value(path, override, "an object override")

    expanded = catalog_format.expand_node(node)
    shared_fields, branch_node = _intersection_merge_parts(node)
    if not shared_fields:
        return _merge_configuration_value(expanded, base, override, path)

    branch_fields: set[str] = set()
    if branch_node is not None:
        for branch in branch_node.branches:
            if not isinstance(branch, catalog_format.ContainerNode):
                raise TypeError(type(branch))
            branch_fields.update(_container_fields(branch))

    label = ".".join(path)
    extra = sorted(set(override) - set(shared_fields) - branch_fields)
    if extra:
        raise ConfigurationError(
            f"Invalid config override at {label}: unknown keys: {', '.join(extra)}"
        )

    _validate_configuration_value(expanded, base, path)
    if not isinstance(base, dict):
        raise TypeError(type(base))
    merged = {key: base[key] for key in shared_fields}
    base_branch = {
        key: value for key, value in base.items() if key not in shared_fields
    }

    for key in set(override).intersection(shared_fields):
        merged[key] = _merge_configuration_value(
            shared_fields[key], merged[key], override[key], (*path, key)
        )

    if branch_node is None:
        return merged

    branch_override = {
        key: value for key, value in override.items() if key in branch_fields
    }
    if branch_override:
        _validate_configuration_value(branch_node, branch_override, path)
        merged.update(branch_override)
        return merged
    merged.update(base_branch)
    return merged


def _merge_configuration_value(
    node: catalog_format.CatalogNodeExpression,
    base: object,
    override: object,
    path: tuple[str, ...],
) -> object:
    label = ".".join(path)
    if isinstance(node, catalog_format.IntersectionNode):
        return _merge_intersection_configuration_value(node, base, override, path)
    if isinstance(node, catalog_format.UnionNode) and isinstance(override, dict):
        # An object override merges into the object branch selected by the base.
        base_matches = [
            branch
            for branch in node.branches
            if not isinstance(branch, catalog_format.FalseNode)
            and _matches_configuration_node(branch, base)
        ]
        if len(base_matches) == 1 and isinstance(
            base_matches[0],
            (catalog_format.ContainerNode, catalog_format.IntersectionNode),
        ):
            merged = _merge_configuration_value(base_matches[0], base, override, path)
            _validate_configuration_value(node, merged, path)
            return merged
    if isinstance(node, (catalog_format.SettingNode, catalog_format.UnionNode)):
        _validate_configuration_value(node, override, path)
        return override
    if not isinstance(node, catalog_format.ContainerNode):
        raise TypeError(type(node))
    if not isinstance(override, dict):
        raise _invalid_configuration_value(path, override, "an object override")
    fields = _container_fields(node)
    extra = sorted(set(override) - set(fields))
    if extra:
        raise ConfigurationError(
            f"Invalid config override at {label}: unknown keys: {', '.join(extra)}"
        )
    if not isinstance(base, dict):
        raise _invalid_configuration_value(path, base, "an object")
    problems = key_problems(base, fields)
    if problems:
        raise ConfigurationError(f"Invalid config object at {label}: {problems}")
    merged = dict(base)
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

    def disabled(
        node: catalog_format.CatalogNodeExpression,
        path: tuple[str, ...],
    ) -> None:
        """Record a turned-off node and its descendants without values."""
        if isinstance(node, catalog_format.IntersectionNode):
            node = catalog_format.expand_node(node)
        if isinstance(node, (catalog_format.ContainerNode, catalog_format.SettingNode)):
            nodes.append(CatalogNode(path, False, node.patch, node.description))
        else:
            nodes.append(CatalogNode(path, False))
        if isinstance(node, catalog_format.ContainerNode):
            for field in node.fields:
                disabled(field.node, (*path, field.name))

    def visit(
        node: catalog_format.CatalogNodeExpression,
        configured: object,
        path: tuple[str, ...],
    ) -> bool:
        if isinstance(node, catalog_format.SettingNode):
            if node.value_type is None and configured is False:
                nodes.append(CatalogNode(path, False, node.patch, node.description))
                return False
            has_value = node.value_type is not None
            configured = _setting_configured_value(node, configured)
            nodes.append(
                CatalogNode(
                    path,
                    True,
                    node.patch,
                    node.description,
                    configured if has_value else None,
                    has_value,
                )
            )
            return True
        if isinstance(node, catalog_format.IntersectionNode):
            return visit(catalog_format.expand_node(node), configured, path)
        if isinstance(node, catalog_format.UnionNode):
            matches = [
                branch
                for branch in node.branches
                if _matches_configuration_node(branch, configured)
            ]
            if len(matches) != 1:
                expected = " ".join(
                    catalog_format.type_text(catalog_format.active_type(node)).split()
                )
                raise _invalid_configuration_value(
                    path,
                    configured,
                    f"exactly one of {expected}",
                )
            if isinstance(matches[0], catalog_format.FalseNode):
                for branch in node.branches:
                    if not isinstance(branch, catalog_format.FalseNode):
                        disabled(branch, path)
                        break
                return False
            return visit(matches[0], configured, path)
        if not isinstance(node, catalog_format.ContainerNode):
            raise TypeError(type(node))
        if not isinstance(configured, dict):
            raise _invalid_configuration_value(path, configured, "an object")
        insertion = len(nodes)
        nodes.append(
            CatalogNode(
                path,
                False,
                node.patch,
                node.description,
                configured,
                True,
            )
        )
        enabled = False
        for field in node.fields:
            enabled = visit(field.node, configured[field.name], (*path, field.name)) or enabled
        enabled = enabled or bool(node.patch)
        nodes[insertion] = CatalogNode(
            path,
            enabled,
            node.patch,
            node.description,
            configured,
            True,
        )
        return enabled

    visit(root, value, ("features",))
    return tuple(nodes)


def _apply_patch_metadata(
    nodes: tuple[CatalogNode, ...],
    patches: dict[str, dict[str, object]],
) -> tuple[CatalogNode, ...]:
    result: list[CatalogNode] = []
    for node in nodes:
        if node.patch is None:
            result.append(node)
            continue
        definition = patches[node.patch]
        raw_frames = definition.get("startup_fast_forward_frames")
        frames = None
        if isinstance(raw_frames, dict):
            frames = StartupFastForwardFrames(
                additive=raw_frames.get("additive"),
                override=raw_frames.get("override"),
            )
        raw_modules = definition.get("modules", [])
        assert isinstance(raw_modules, list)
        result.append(
            replace(
                node,
                startup_fast_forward_frames=frames,
                modules=tuple(str(module) for module in raw_modules),
            )
        )
    return tuple(result)


def _patch_closure(
    references: tuple[str, ...],
    patches: dict[str, dict[str, object]],
) -> tuple[str, ...]:
    result: list[str] = []
    active: list[str] = []
    seen: set[str] = set()

    def visit(patch_id: str) -> None:
        if patch_id in active:
            raise ValueError("Patch include cycle: " + " -> ".join((*active, patch_id)))
        if patch_id in seen:
            return
        if patch_id not in patches:
            raise ValueError(f"Catalog references unknown patch: {patch_id}")
        active.append(patch_id)
        result.append(patch_id)
        for included in patches[patch_id].get("includes", []):
            visit(included)
        active.pop()
        seen.add(patch_id)

    for reference in references:
        visit(reference)
    return tuple(result)


def _included_patch_nodes(
    nodes: tuple[CatalogNode, ...],
    patches: dict[str, dict[str, object]],
) -> tuple[CatalogNode, ...]:
    selected: dict[str, CatalogNode] = {}
    priorities: dict[str, tuple[bool, bool, bool]] = {}
    for node in nodes:
        if node.patch is None:
            continue
        for patch_id in _patch_closure((node.patch,), patches):
            # Prefer an active direct reference, then the patch's own feature.
            priority = (
                node.enabled,
                patch_id == node.patch,
                node.feature_id == patch_id.split(".", 1)[0],
            )
            if patch_id in priorities and priorities[patch_id] >= priority:
                continue
            priorities[patch_id] = priority
            selected[patch_id] = node if patch_id == node.patch else CatalogNode(
                path=("features", node.feature_id, "includes", *patch_id.split(".")),
                enabled=node.enabled,
                patch=patch_id,
                description=str(patches[patch_id].get("description", "")),
            )
    return _apply_patch_metadata(tuple(selected.values()), patches)


def _startup_frame_settings(
    nodes: tuple[CatalogNode, ...],
) -> list[tuple[CatalogNode, StartupFastForwardFrames]]:
    return [
        (node, node.startup_fast_forward_frames)
        for node in nodes
        if node.enabled and node.startup_fast_forward_frames is not None
    ]


def _startup_fast_forward_override(nodes: tuple[CatalogNode, ...]) -> int | None:
    overrides = [
        (node, frames)
        for node, frames in _startup_frame_settings(nodes)
        if frames.override is not None
    ]
    if len(overrides) > 1:
        raise ConfigurationError(
            "Multiple enabled startup_fast_forward_frames overrides: "
            + ", ".join(node.node_id for node, _frames in overrides)
        )
    return overrides[0][1].override if overrides else None


def _startup_fast_forward_frames(
    nodes: tuple[CatalogNode, ...],
    baseline_frames: int,
) -> int:
    if (
        isinstance(baseline_frames, bool)
        or not isinstance(baseline_frames, int)
        or baseline_frames < 0
        or baseline_frames > UINT64_MAX
    ):
        raise ValueError("Baseline startup fast-forward frames must be a UInt64 integer")
    override = _startup_fast_forward_override(nodes)
    additive = sum(
        frames.additive or 0 for _node, frames in _startup_frame_settings(nodes)
    )
    baseline = override if override is not None else baseline_frames
    result = baseline + additive
    if result < 0 or result > UINT64_MAX:
        raise ConfigurationError(
            "Resolved startup_fast_forward_frames must be a UInt64 integer; "
            f"got {result}"
        )
    return result


def startup_fast_forward_frames(
    selection: CatalogSelection,
    baseline_frames: int,
) -> int:
    """Return the selected startup fast-forward frame count."""

    return _startup_fast_forward_frames(selection.patch_nodes, baseline_frames)


def _load_implementation(
    catalog_path: Path,
    features: dict[str, catalog_format.CatalogNodeExpression],
) -> tuple[
    tuple[Path, ...],
    dict[str, dict[str, object]],
    dict[str, dict[str, object]],
    dict[str, dict[str, object]],
    dict[str, dict[str, object]],
]:
    patches_path = catalog_path.parent / "patches"
    if not patches_path.is_dir():
        raise FileNotFoundError(patches_path)
    patch_files = tuple(sorted(patches_path.glob("*/*.json")))
    if not patch_files:
        raise ValueError(f"Patch directory contains no JSON definitions: {patches_path}")
    patches: dict[str, dict[str, object]] = {}
    for patch_file in patch_files:
        raw = _read_json(patch_file, f"Patches in {patch_file.name}")
        for patch_id, definition in raw.items():
            _patch_identifier(patch_id, "Patch ID")
            patch_root = patch_id.split(".", 1)[0]
            if patch_file.parent.name != patch_root or patch_file.stem != patch_root:
                raise ValueError(
                    f"Patch {patch_id!r} must be stored in "
                    f"patches/{patch_root}/{patch_root}.json"
                )
            if patch_id in patches:
                raise ValueError(f"Duplicate patch definition: {patch_id}")
            if not isinstance(definition, dict):
                raise ValueError(f"Patch {patch_id!r} must be an object")
            patches[patch_id] = definition

    edits: dict[str, dict[str, object]] = {}
    injections: dict[str, dict[str, object]] = {}
    string_patches: dict[str, dict[str, object]] = {}
    required_string_patch_fields = {
        "description",
        "operation",
        "expected_value",
        "expected_mapping_count",
        "expected_occurrence_count",
    }
    allowed_patch_fields = {
        "description",
        "includes",
        "edit",
        "edits",
        "hooks",
        "payload",
        "string_patch",
        "image_patch",
        "image_file",
        "modules",
        "startup_fast_forward_frames",
    }
    for patch_id, patch in patches.items():
        extra = sorted(set(patch) - allowed_patch_fields)
        if extra:
            raise ValueError(f"Patch {patch_id!r} has unknown fields: {extra}")
        description = _description(patch.get("description"), f"Patch {patch_id!r}")
        if "includes" in patch:
            includes = patch["includes"]
            if not isinstance(includes, list) or not includes:
                raise ValueError(f"Patch {patch_id!r}.includes must be a non-empty list")
            for reference in includes:
                if not isinstance(reference, str):
                    raise ValueError(f"Patch {patch_id!r}.includes must contain patch IDs")
                _patch_identifier(reference, f"Patch {patch_id!r}.includes")
            if len(set(includes)) != len(includes):
                raise ValueError(f"Patch {patch_id!r}.includes contains duplicate references")
        if "image_file" in patch:
            image_file = patch["image_file"]
            label = f"Patch {patch_id!r}.image_file"
            if not isinstance(image_file, dict):
                raise ValueError(f"{label} must be an object")
            _validate_fields(image_file, {"path", "asset", "sha256"}, label,
                             required={"path", "asset", "sha256"})
            _relative_path(image_file["path"], f"{label}.path")
            _relative_path(image_file["asset"], f"{label}.asset")
            digest = image_file["sha256"]
            if not isinstance(digest, str) or not re.fullmatch(r"[0-9A-F]{64}", digest):
                raise ValueError(f"{label}.sha256 must be an uppercase SHA-256")
        if not (set(patch) - {"description"}):
            raise ValueError(f"Patch {patch_id!r} owns no implementation data")
        if "edit" in patch and "edits" in patch:
            raise ValueError(f"Patch {patch_id!r} cannot define both edit and edits")

        edit: dict[str, object] | None = None
        if "edit" in patch:
            raw_edit = patch["edit"]
            if not isinstance(raw_edit, dict) or not raw_edit:
                raise ValueError(f"Patch {patch_id!r}.edit must be a non-empty object")
            if "edits" in raw_edit:
                raise ValueError(f"Patch {patch_id!r}.edit must be a primitive edit")
            edit = raw_edit
        elif "edits" in patch:
            members = patch["edits"]
            if not isinstance(members, dict) or not members:
                raise ValueError(f"Patch {patch_id!r}.edits must be a non-empty object")
            edit = {**({"description": description} if description else {}), "edits": members}

        if edit is not None:
            _description(edit.get("description"), f"Patch {patch_id!r} edit")
            if "edits" in edit:
                members = edit["edits"]
                assert isinstance(members, dict)
                for member_id, member in members.items():
                    _identifier(member_id, f"Patch {patch_id!r} edit member ID")
                    if not isinstance(member, dict):
                        raise ValueError(
                            f"Patch {patch_id!r} edit member {member_id!r} "
                            "must be an object"
                        )
                    if "edits" in member:
                        raise ValueError(
                            f"Patch {patch_id!r} edit member {member_id!r} "
                            "must be a primitive edit"
                        )
                    _description(
                        member.get("description"),
                        f"Patch {patch_id!r} edit member {member_id!r}",
                    )
                    if "adapter" in member:
                        binary_adapters.validate_adapter_name(member["adapter"])
            elif "adapter" in edit:
                binary_adapters.validate_adapter_name(edit["adapter"])
            edits[patch_id] = edit

        injection_fields = {field: patch[field] for field in ("hooks", "payload") if field in patch}
        if injection_fields:
            injection: dict[str, object] = {
                **({"description": description} if description else {}),
                **injection_fields,
            }
        for field in ("hooks", "payload"):
            if field in patch and not isinstance(patch[field], dict):
                raise ValueError(f"Patch {patch_id!r}.{field} must be an object")
        for hook_id, hook in patch.get("hooks", {}).items():
            _identifier(hook_id, f"Patch {patch_id!r} hook ID")
            if not isinstance(hook, dict):
                raise ValueError(f"Patch {patch_id!r} hook {hook_id!r} must be an object")
            _description(hook.get("description"), f"Patch {patch_id!r} hook {hook_id!r}")
        if injection_fields:
            injections[patch_id] = injection

        for payload_id, declaration in patch.get("payload", {}).items():
            _identifier(payload_id, f"Patch {patch_id!r} payload ID")
            label = f"Patch {patch_id!r}.payload.{payload_id}"
            if not isinstance(declaration, dict):
                raise ValueError(f"{label} must be an object")
            kind = declaration.get("kind")
            if kind in {"c", "asm"}:
                _validate_fields(
                    declaration,
                    SOURCE_PAYLOAD_FIELDS,
                    label,
                    required={"kind", "path", "namespace", "fragments"},
                )
                if not isinstance(declaration["path"], str):
                    raise ValueError(f"{label}.path must be text")
                _source_location(patch_id, declaration["path"], catalog_path, label)
                namespace = declaration["namespace"]
                if (
                    not isinstance(namespace, str)
                    or not SYMBOL_PATTERN.fullmatch(namespace)
                ):
                    raise ValueError(f"{label}.namespace is invalid")
                imports = declaration.get("imports", {})
                if not isinstance(imports, dict):
                    raise ValueError(f"{label}.imports must be an object")
                for import_id, imported in imports.items():
                    if not SYMBOL_PATTERN.fullmatch(import_id):
                        raise ValueError(f"{label}.imports key is invalid: {import_id!r}")
                    if isinstance(imported, dict):
                        _validate_fields(
                            imported,
                            IMPORT_FIELDS,
                            f"{label}.imports.{import_id}",
                            required={"symbol"},
                        )
                resources = declaration.get("resources", [])
                if (
                    not isinstance(resources, list)
                    or any(
                        not isinstance(resource, str)
                        for resource in resources
                    )
                    or len(resources) != len(set(resources))
                ):
                    raise ValueError(
                        f"{label}.resources must be a list of unique paths"
                    )
                fragments = declaration.get("fragments")
                if not isinstance(fragments, dict) or not fragments:
                    raise ValueError(f"{label}.fragments must be a non-empty object")
                for fragment_id, fragment in fragments.items():
                    if not SYMBOL_PATTERN.fullmatch(fragment_id):
                        raise ValueError(
                            f"{label}.fragments key is invalid: {fragment_id!r}"
                        )
                    fragment_label = f"{label}.fragments.{fragment_id}"
                    if not isinstance(fragment, dict):
                        raise ValueError(f"{fragment_label} must be an object")
                    _validate_fields(
                        fragment,
                        SOURCE_FRAGMENT_FIELDS,
                        fragment_label,
                        required={"object"},
                    )
                    object_fragment = fragment["object"]
                    if (
                        not isinstance(object_fragment, str)
                        or not SYMBOL_PATTERN.fullmatch(object_fragment)
                    ):
                        raise ValueError(f"{fragment_label}.object is invalid")
                    _optional_text(fragment.get("abi"), f"{fragment_label}.abi")
                    _description(fragment.get("description"), fragment_label)
            elif kind in FRAGMENT_KINDS:
                _validate_fields(
                    declaration,
                    STATIC_PAYLOAD_FIELDS,
                    label,
                    required={"kind", "alignment"},
                )
                if ("value" in declaration) == ("blob_path" in declaration):
                    raise ValueError(
                        f"{label} requires exactly one of value or blob_path"
                    )
                relocations = declaration.get("relocations", {})
                if not isinstance(relocations, dict):
                    raise ValueError(f"{label}.relocations must be an object")
                for relocation_id, relocation in relocations.items():
                    if not isinstance(relocation, dict):
                        raise ValueError(
                            f"{label}.relocations.{relocation_id} must be an object"
                        )
                    _validate_fields(
                        relocation,
                        RELOCATION_FIELDS,
                        f"{label}.relocations.{relocation_id}",
                        required={"offset", "encoding", "symbol"},
                    )
                if "init" in declaration and not isinstance(
                    declaration["init"], bool
                ):
                    raise ValueError(f"{label}.init must be boolean")
            else:
                raise ValueError(f"{label}.kind is invalid: {kind!r}")

        if "string_patch" in patch:
            string_patch = patch["string_patch"]
            if not isinstance(string_patch, dict):
                raise ValueError(f"Patch {patch_id!r}.string_patch must be an object")
            problems = key_problems(string_patch, required_string_patch_fields, noun="fields")
            if problems:
                raise ValueError(f"Patch {patch_id!r}.string_patch is invalid: {problems}")
            _description(string_patch["description"], f"Patch {patch_id!r}.string_patch")
            if string_patch["operation"] != "replace_imported_game_title":
                raise ValueError(
                    f"Patch {patch_id!r}.string_patch has unsupported operation: "
                    f"{string_patch['operation']!r}"
                )
            expected_value = string_patch["expected_value"]
            if not isinstance(expected_value, str) or not expected_value or "\0" in expected_value:
                raise ValueError(
                    f"Patch {patch_id!r}.string_patch.expected_value must be non-empty text without an embedded NUL"
                )
            mapping_count = string_patch["expected_mapping_count"]
            occurrence_count = string_patch["expected_occurrence_count"]
            if (
                isinstance(mapping_count, bool)
                or not isinstance(mapping_count, int)
                or mapping_count <= 0
                or isinstance(occurrence_count, bool)
                or not isinstance(occurrence_count, int)
                or occurrence_count < mapping_count
            ):
                raise ValueError(f"Patch {patch_id!r}.string_patch has invalid expected coverage")
            string_patches[patch_id] = string_patch

        if "image_patch" in patch:
            image_patch = patch["image_patch"]
            if image_patch != {"operation": "use_nun5_disc_identity"}:
                raise ValueError(
                    f"Patch {patch_id!r}.image_patch must declare "
                    "operation 'use_nun5_disc_identity'"
                )

        modules = patch.get("modules", [])
        if not isinstance(modules, list) or any(not isinstance(module, str) for module in modules):
            raise ValueError(f"Patch {patch_id!r}.modules must be an array of strings")
        if len(modules) != len(set(modules)):
            raise ValueError(f"Patch {patch_id!r}.modules must be unique")
        for module in modules:
            _identifier(module, f"Patch {patch_id!r} module")

        if "startup_fast_forward_frames" in patch:
            frames = patch["startup_fast_forward_frames"]
            if not isinstance(frames, dict) or not frames:
                raise ValueError(f"Patch {patch_id!r}.startup_fast_forward_frames must be a non-empty object")
            extra_frames = sorted(set(frames) - {"additive", "override"})
            if extra_frames:
                raise ValueError(f"Patch {patch_id!r}.startup_fast_forward_frames has unknown fields: {extra_frames}")
            for key, value in frames.items():
                if isinstance(value, bool) or not isinstance(value, int):
                    raise ValueError(f"Patch {patch_id!r}.startup_fast_forward_frames.{key} must be an integer")
                if key == "override" and (value <= 0 or value > UINT64_MAX):
                    raise ValueError(f"Patch {patch_id!r}.startup_fast_forward_frames.override must be a positive UInt64 integer")

    references = [
        patch
        for feature in features.values()
        for patch in _catalog_patches(feature)
    ]
    for patch_id in references:
        _patch_identifier(patch_id, "Catalog patch ID")
    referenced = set(_patch_closure(tuple(references), patches))
    orphaned = sorted(set(patches) - referenced)
    if orphaned:
        raise ValueError(f"Patch definitions are not catalog-referenced: {orphaned}")
    return (
        patch_files,
        patches,
        edits,
        injections,
        string_patches,
    )


def _effective_configuration(
    catalog_path: Path,
    configuration_path: Path,
    features: dict[str, catalog_format.CatalogNodeExpression],
    *,
    release_defaults_path: Path | None = None,
    release_definition_path: Path | None = None,
    overrides: dict[str, object] | None = None,
) -> tuple[Path | None, object]:
    repository_configuration_root = (catalog_path.parent / "configurations").resolve()
    if (
        release_defaults_path is None
        and configuration_path.parent == repository_configuration_root
    ):
        manifest_path = catalog_path.parent / "release" / "release_manifest.json"
        if manifest_path.is_file():
            manifest = _read_json(manifest_path, "Release manifest")
            release_name = manifest.get("configuration")
            if isinstance(release_name, str):
                release_path = (catalog_path.parent / release_name).resolve()
                if configuration_path == release_path:
                    release_defaults_path = repository_configuration_root / "base.jsonc"
                    release_definition_path = release_path
    try:
        configuration = _read_json(configuration_path, "Configuration", comments=True)
    except ValueError as exc:
        raise ConfigurationError(str(exc)) from exc
    root = _feature_root(features)
    if (
        release_defaults_path is None
        and configuration_path.parent == repository_configuration_root
        and configuration_path.name != "base.jsonc"
        and set(configuration) != {"overrides"}
    ):
        raise ConfigurationError(
            "Repository configurations must contain only the overrides root key"
        )
    if release_defaults_path is not None:
        base_path = release_defaults_path
        defaults = _read_json(release_defaults_path, "Packaged defaults", comments=True)["features"]
        _validate_configuration_value(root, defaults, ("features",))
        release_values, mapping = load_release_definition(release_definition_path)
        if configuration_path == release_definition_path:
            configuration = release_values
        effective = expand_configuration(features, configuration, defaults, release_values, mapping)
    elif set(configuration) == {"overrides"}:
        base_path = (repository_configuration_root / "base.jsonc").resolve()
        try:
            base = _read_json(base_path, "Base configuration", comments=True)
        except ValueError as exc:
            raise ConfigurationError(str(exc)) from exc
        if set(base) != {"features"}:
            raise ConfigurationError(
                "Base configuration root must contain only features"
            )
        if not isinstance(configuration["overrides"], dict):
            raise _invalid_configuration_value(
                ("overrides",), configuration["overrides"], "an object"
            )
        _validate_configuration_value(root, base["features"], ("features",))
        effective = _merge_configuration_value(
            root, base["features"], configuration["overrides"], ("features",)
        )
    elif set(configuration) == {"features"}:
        base_path = None
        effective = configuration["features"]
    else:
        raise ConfigurationError(
            f"Invalid config root: {key_problems(configuration, {'features'})}"
        )
    _validate_configuration_value(root, effective, ("features",))
    if overrides:
        nested: dict[str, object] = {}
        assigned_paths: list[str] = []
        for dotted_path, value in overrides.items():
            if not isinstance(dotted_path, str) or not dotted_path or any(
                not catalog_format.IDENTIFIER.fullmatch(part) for part in dotted_path.split(".")
            ):
                raise ConfigurationError(f"Invalid config override path: {dotted_path!r}")
            if any(
                dotted_path == previous
                or dotted_path.startswith(previous + ".")
                or previous.startswith(dotted_path + ".")
                for previous in assigned_paths
            ):
                raise ConfigurationError(f"Overlapping config override: {dotted_path}")
            assigned_paths.append(dotted_path)
            branch = nested
            parts = dotted_path.split(".")
            for part in parts[:-1]:
                previous = branch.setdefault(part, {})
                if not isinstance(previous, dict):
                    raise ConfigurationError(f"Overlapping config override: {dotted_path}")
                branch = previous
            if parts[-1] in branch:
                raise ConfigurationError(f"Overlapping config override: {dotted_path}")
            branch[parts[-1]] = value
        effective = _merge_configuration_value(root, effective, nested, ("features",))
        _validate_configuration_value(root, effective, ("features",))
    return base_path, effective


def load_selection(catalog_path: Path, configuration_path: Path, *,
                   release_defaults_path: Path | None = None,
                   release_definition_path: Path | None = None,
                   overrides: dict[str, object] | None = None) -> CatalogSelection:
    catalog_path = catalog_path.resolve()
    configuration_path = configuration_path.resolve()
    features = _read_catalog(catalog_path)
    (
        patch_files,
        patches,
        edits,
        injections,
        string_patches,
    ) = _load_implementation(catalog_path, features)
    base_path, effective = _effective_configuration(
        catalog_path, configuration_path, features,
        release_defaults_path=release_defaults_path,
        release_definition_path=release_definition_path,
        overrides=overrides,
    )
    nodes = _apply_patch_metadata(
        _selected_nodes(_feature_root(features), effective),
        patches,
    )
    selection = CatalogSelection(
        catalog_path=catalog_path,
        patch_files=patch_files,
        base_configuration_path=base_path,
        configuration_path=configuration_path,
        catalog=features,
        patches=patches,
        edits=edits,
        injections=injections,
        string_patches=string_patches,
        nodes=nodes,
        effective_configuration=effective,
        supplied_overrides=overrides,
    )
    _startup_fast_forward_override(selection.patch_nodes)
    return selection


def load_startup_fast_forward_frames(
    catalog_path: Path,
    configuration_path: Path,
    baseline_frames: int,
) -> int:
    """Resolve launch metadata from selected unified patches."""
    return startup_fast_forward_frames(
        load_selection(catalog_path, configuration_path), baseline_frames
    )


def materialized_configuration(
    catalog_path: Path,
    configuration_path: Path,
) -> dict[str, object]:
    """Resolve a development configuration's complete feature values."""
    catalog_path = catalog_path.resolve()
    configuration_path = configuration_path.resolve()
    features = _read_catalog(catalog_path)
    _base_path, effective = _effective_configuration(catalog_path, configuration_path, features)
    return {"features": effective}


def load_release_definition(path: Path) -> tuple[dict[str, object], dict[str, str]]:
    definition = _read_json(path, "Release configuration", comments=True)
    mapping = definition.pop("configuration_mapping", None)
    if not definition or not isinstance(mapping, dict):
        raise ValueError("Release configuration needs public settings and a mapping object")
    return definition, mapping


def public_configuration_text(path: Path, values: dict[str, object]) -> str:
    """Keep the release definition's public text and comments without its mapping."""
    source = path.read_text(encoding="utf-8")
    mapping_fields = list(re.finditer(
        r'(?m)^[ \t]*"configuration_mapping"[ \t]*:', source
    ))
    if len(mapping_fields) != 1:
        raise ValueError("Release configuration needs one trailing configuration_mapping")
    public_prefix = source[:mapping_fields[0].start()].rstrip()
    if not public_prefix.endswith(","):
        raise ValueError("Release configuration_mapping must follow the public values")
    public_text = public_prefix[:-1] + "\n}\n"
    if jsonc.loads(public_text) != values:
        raise ValueError("Release configuration_mapping must be the final root field")
    return public_text


def _optional_group(node):
    """Resolve a `{ ... } | false` group to its object branch."""
    if isinstance(node, catalog_format.UnionNode):
        groups = [
            branch for branch in node.branches
            if not isinstance(branch, catalog_format.FalseNode)
        ]
        if len(groups) == 1 and len(node.branches) == 2:
            return groups[0]
    return node


def resolve_layout(features, values, mapping):
    """Derive the public schema and mappings from the release values."""
    root = catalog_format.ContainerNode(tuple(
        catalog_format.ContainerField(name, node) for name, node in features.items()
    ))
    for public, target in mapping.items():
        if (not isinstance(public, str) or not public
                or any(not catalog_format.IDENTIFIER.fullmatch(part)
                       for part in public.split("."))
                or not isinstance(target, str) or not target
                or any(not catalog_format.IDENTIFIER.fullmatch(part)
                       for part in target.split("."))):
            raise ValueError(f"Invalid release mapping: {public!r}: {target!r}")
    mappings = []
    paths = {}
    used_mapping = set()

    def resolve(path):
        node = root
        for part in path:
            expanded = _optional_group(catalog_format.expand_node(node))
            if not isinstance(expanded, catalog_format.ContainerNode):
                raise ValueError(f"Release path crosses a setting or union: {'.'.join(path)}")
            fields = {field.name: field.node for field in expanded.fields}
            if part not in fields:
                raise ValueError(f"Unknown release catalog path: {'.'.join(path)}")
            node = fields[part]
        return node

    def visit(group, public_path, internal_path):
        node = resolve(internal_path)
        paths[public_path] = internal_path
        expanded = catalog_format.expand_node(node)
        if isinstance(expanded, catalog_format.ContainerNode) and isinstance(group, dict):
            if not group:
                raise ValueError(f"{'.'.join(public_path)} must contain public settings")
            fields = []
            for name, value in group.items():
                if (not isinstance(name, str) or not catalog_format.IDENTIFIER.fullmatch(name)
                        or name in {"description", "patch", "configuration_mapping"}):
                    raise ValueError(f"Invalid public setting name: {name!r}")
                path = (*public_path, name)
                mapping_key = ".".join(path)
                target = mapping.get(mapping_key)
                if target is None:
                    child_path = (*internal_path, name)
                else:
                    child_path = tuple(target.split("."))
                    used_mapping.add(mapping_key)
                child = visit(value, path, child_path)
                fields.append(catalog_format.ContainerField(name, child))
            return catalog_format.ContainerNode(tuple(fields), expanded.description)
        mappings.append((public_path, internal_path))
        return node

    schema = visit(values, (), ())
    unused = set(mapping) - used_mapping
    if unused:
        raise ValueError(f"Unused release mappings: {', '.join(sorted(unused))}")
    for index, (_, path) in enumerate(mappings):
        for _, previous in mappings[:index]:
            common = min(len(path), len(previous))
            if path[:common] == previous[:common]:
                raise ValueError(
                    f"Overlapping release mappings: {'.'.join(previous)} and {'.'.join(path)}"
                )
    _validate_configuration_value(schema, values, ())
    return schema, paths


def _set_value(result, path, value):
    for part in path[:-1]:
        result = result.setdefault(part, {})
    result[path[-1]] = value


def expand_configuration(features, values, defaults, release_values, mapping):
    """Merge public release values over the packaged defaults; the caller validates."""
    schema, paths = resolve_layout(features, release_values, mapping)
    _validate_configuration_value(schema, values, ())
    overrides = {}

    def collect(node, value, public_path):
        if isinstance(node, catalog_format.ContainerNode) and isinstance(value, dict):
            for field in node.fields:
                collect(field.node, value[field.name], (*public_path, field.name))
            return
        _set_value(overrides, paths[public_path], value)

    collect(schema, values, ())
    return _merge_configuration_value(
        _feature_root(features), defaults, overrides, ("features",)
    )


def release_configuration_values(catalog_path: Path, release_definition_path: Path) -> dict[str, object]:
    """Return the validated public defaults without release metadata."""
    features = _read_catalog(catalog_path)
    values, mapping = load_release_definition(release_definition_path)
    resolve_layout(features, values, mapping)
    return values


def public_catalog(catalog_path: Path, release_definition_path: Path) -> str:
    """Return the release reference selected by public setting presence."""
    features = _read_catalog(catalog_path)
    values, mapping = load_release_definition(release_definition_path)
    projected, _paths = resolve_layout(features, values, mapping)
    return catalog_format.serialize_feature(projected, include_patches=False)


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
        for line, row in enumerate(read_tsv(path, OPERATION_FIELDS), 2):
            name = _identifier(row["field"], f"{path}:{line} field")
            if name in seen:
                raise ValueError(f"{path}:{line}: duplicate field {name}")
            seen.add(name)
            if row["required"] not in {"0", "1"}:
                raise ValueError(f"{path}:{line}: required must be 0 or 1")
            if row["type"] not in FIELD_TYPES:
                raise ValueError(f"{path}:{line}: unsupported type {row['type']!r}")
            fields.append(OperationField(name, row["required"] == "1", row["type"]))
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
            if fixed_fields != {"expected_value", "replacement_value"}:
                raise ValueError(
                    f"{label}.adapter requires expected_value and replacement_value"
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
        evidence_id="",
    )


def _edit_members(
    edit_id: str,
    definition: dict[str, object],
) -> tuple[tuple[str | None, dict[str, object]], ...]:
    def normalize_destination(
        member_id: str | None,
        edit: dict[str, object],
    ) -> dict[str, object]:
        label = f"edits.{edit_id}"
        if member_id is not None:
            label += f".edits.{member_id}"
        destination_fields = {
            "destination_offset",
            "destination_offsets",
        } & set(edit)
        if len(destination_fields) != 1:
            raise ValueError(
                f"{label} requires exactly one of destination_offset "
                "or destination_offsets"
            )

        normalized = dict(edit)
        if "destination_offset" in edit:
            destination_offset = _parse_int(
                edit["destination_offset"],
                f"{label}.destination_offset",
            )
            del normalized["destination_offset"]
            normalized["destination_offsets"] = [destination_offset]
        else:
            destination_offsets = _parse_int_list(
                edit["destination_offsets"],
                f"{label}.destination_offsets",
            )
            if len(destination_offsets) < 2:
                raise ValueError(
                    f"{label}.destination_offsets must contain at least two "
                    "offsets; use destination_offset for one"
                )
            normalized["destination_offsets"] = list(destination_offsets)
        return normalized

    def expand_table(
        table_id: str | None,
        table: dict[str, object],
    ) -> tuple[tuple[str, dict[str, object]], ...]:
        label = f"edits.{edit_id}"
        if table_id is not None:
            label += f".edits.{table_id}"
        allowed = {
            "description",
            "operation",
            "destination_target_id",
            "table_offset",
            "record_stride",
            "field_offset",
            "record_patches",
        }
        problems = key_problems(table, allowed - {"description"}, allowed, noun="fields")
        if problems:
            raise ValueError(f"{label} is invalid: {problems}")

        table_offset = _parse_int(table["table_offset"], f"{label}.table_offset")
        record_stride = _parse_int(
            table["record_stride"], f"{label}.record_stride", minimum=1
        )
        field_offset = _parse_int(table["field_offset"], f"{label}.field_offset")
        record_patches = table["record_patches"]
        if not isinstance(record_patches, dict) or not record_patches:
            raise ValueError(f"{label}.record_patches must be a non-empty object")

        expanded: list[tuple[str, dict[str, object]]] = []
        used_indices: set[int] = set()
        patch_length: int | None = None
        for record_id, record in sorted(record_patches.items()):
            _identifier(record_id, f"{label}.record_patches record ID")
            record_label = f"{label}.record_patches.{record_id}"
            if not isinstance(record, dict):
                raise ValueError(f"{record_label} must be an object")
            index_fields = {"record_index", "record_indices"} & set(record)
            if len(index_fields) != 1:
                raise ValueError(
                    f"{record_label} requires exactly one of record_index "
                    "or record_indices"
                )
            problems = key_problems(
                record, index_fields | {"expected_hex", "replacement_hex"}, noun="fields"
            )
            if problems:
                raise ValueError(f"{record_label} is invalid: {problems}")

            if "record_index" in record:
                indices = (
                    _parse_int(record["record_index"], f"{record_label}.record_index"),
                )
            else:
                indices = _parse_int_list(
                    record["record_indices"], f"{record_label}.record_indices"
                )
            duplicates = sorted(used_indices.intersection(indices))
            if duplicates:
                raise ValueError(
                    f"{record_label} reuses table record indices: {duplicates}"
                )
            used_indices.update(indices)

            expected_hex = _hex(
                record["expected_hex"], f"{record_label}.expected_hex"
            )
            replacement_hex = _hex(
                record["replacement_hex"], f"{record_label}.replacement_hex"
            )
            expected_length = len(bytes.fromhex(expected_hex))
            replacement_length = len(bytes.fromhex(replacement_hex))
            if expected_length != replacement_length:
                raise ValueError(f"{record_label} expected/replacement length mismatch")
            if patch_length is None:
                patch_length = replacement_length
            elif replacement_length != patch_length:
                raise ValueError(
                    f"{record_label} length differs from other table records"
                )
            if field_offset + replacement_length > record_stride:
                raise ValueError(
                    f"{record_label} field exceeds the {record_stride}-byte record stride"
                )

            member_id = record_id if table_id is None else f"{table_id}__{record_id}"
            expanded.append(
                (
                    member_id,
                    {
                        **(
                            {"description": table["description"]}
                            if "description" in table
                            else {}
                        ),
                        "operation": "replace",
                        "destination_target_id": table["destination_target_id"],
                        "destination_offsets": [
                            table_offset + index * record_stride + field_offset
                            for index in indices
                        ],
                        "expected_hex": expected_hex,
                        "replacement_hex": replacement_hex,
                    },
                )
            )
        return tuple(expanded)

    if "edits" not in definition:
        if definition.get("operation") == "replace_table":
            return expand_table(None, definition)
        return ((None, normalize_destination(None, definition)),)
    result: list[tuple[str | None, dict[str, object]]] = []
    for member_id, member in sorted(definition["edits"].items()):
        if member.get("operation") == "replace_table":
            result.extend(expand_table(member_id, member))
        else:
            result.append((member_id, normalize_destination(member_id, member)))
    return tuple(result)


def load_binary_package(
    selection: CatalogSelection,
    feature_id: str,
    targets_path: Path,
    repository: Path,
    operations_path: Path,
) -> binary_patcher.Package:
    nodes = [
        node
        for node in selection.feature_patch_nodes(feature_id)
        if node.enabled and node.patch in selection.edits
    ]
    targets = binary_patcher.load_targets(targets_path)
    contracts = load_operation_contracts(operations_path)
    patches = {node.node_id: _internal_patch(node) for node in nodes}
    edits: list[binary_patcher.Edit] = []
    used_targets: set[str] = set()
    order = 0
    for node in nodes:
        edit_key = node.patch
        grouped_ranges: dict[str, list[tuple[int, int, str]]] = {}
        for member_id, raw_edit in _edit_members(
            edit_key, selection.edits[edit_key]
        ):
            label = f"edits.{edit_key}"
            if member_id is not None:
                label += f".edits.{member_id}"
            operation = _validate_operation(raw_edit, label, contracts)
            destination_id = str(raw_edit["destination_target_id"])
            if destination_id not in targets:
                raise ValueError(
                    f"{label}: unknown destination target {destination_id!r}"
                )
            expected_hex = ""
            expected_sha256 = ""
            if "expected_hex" in raw_edit:
                expected_hex = _hex(
                    raw_edit["expected_hex"], f"{label}.expected_hex"
                )
            if "expected_sha256" in raw_edit:
                expected_sha256 = _sha256(
                    raw_edit["expected_sha256"], f"{label}.expected_sha256"
                )
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
                    if node.has_configured_value:
                        raise ValueError(
                            f"{label}.adapter requires a bare catalog setting"
                        )
                    expected_hex, replacement_hex = binary_adapters.apply_fixed_adapter(
                        raw_edit["adapter"],
                        raw_edit["expected_value"],
                        raw_edit["replacement_value"],
                        encoding=raw_edit.get("encoding"),
                        length=raw_edit.get("length"),
                    )
                else:
                    replacement_hex = _hex(
                        raw_edit["replacement_hex"],
                        f"{label}.replacement_hex",
                    )
                length = len(bytes.fromhex(replacement_hex))
            elif operation == "copy":
                length = _parse_int(
                    raw_edit["length"], f"{label}.length", minimum=1
                )
                source_id = str(raw_edit["source_target_id"])
                source_offset = _parse_int(
                    raw_edit["source_offset"], f"{label}.source_offset"
                )
                if source_id not in targets:
                    raise ValueError(
                        f"{label}: unknown source target {source_id!r}"
                    )
                used_targets.add(source_id)
            elif operation == "blob":
                blob_path = _relative_path(
                    raw_edit["blob_path"], f"{label}.blob_path"
                )
                blob_sha256 = _sha256(
                    raw_edit["blob_sha256"], f"{label}.blob_sha256"
                )
                blob_file = repository.joinpath(*blob_path.parts)
                if not blob_file.is_file():
                    raise FileNotFoundError(blob_file)
                length = blob_file.stat().st_size
            else:
                length = _parse_int(
                    raw_edit["length"], f"{label}.length", minimum=1
                )
                fill_hex = _hex(raw_edit["fill_hex"], f"{label}.fill_hex")
                if len(bytes.fromhex(fill_hex)) != 1:
                    raise ValueError(f"{label}.fill_hex must be exactly one byte")
            if expected_hex and len(bytes.fromhex(expected_hex)) != length:
                raise ValueError(f"{label}.expected_hex length mismatch")
            if member_id is not None:
                for destination_offset in destination_offsets:
                    destination_end = destination_offset + length
                    for prior_start, prior_end, prior_member_id in grouped_ranges.get(
                        destination_id, []
                    ):
                        if (
                            prior_member_id != member_id
                            and max(prior_start, destination_offset)
                            < min(prior_end, destination_end)
                        ):
                            raise ValueError(
                                f"edits.{edit_key} members {prior_member_id!r} "
                                f"and {member_id!r} have overlapping destination "
                                f"ranges in {destination_id!r}"
                            )
                    grouped_ranges.setdefault(destination_id, []).append(
                        (destination_offset, destination_end, member_id)
                    )
            used_targets.add(destination_id)
            reason = _description(
                raw_edit.get(
                    "description",
                    selection.patches[edit_key].get("description"),
                ),
                label,
            )
            multiple_destinations = len(destination_offsets) > 1
            for destination_offset in destination_offsets:
                order += 1
                edit_id = f"{node.node_id}.{edit_key}"
                if member_id is not None:
                    edit_id += f".{member_id}"
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
        for payload_id, value in injection.get("payload", {}).items():
            if payload_id in seen_payloads:
                raise ValueError(
                    f"Duplicate payload declaration {payload_id!r} in {feature_id}"
                )
            seen_payloads.add(payload_id)
            entries.append((node, injection_id, payload_id, value))
    return entries


def injection_entries(
    selection: CatalogSelection,
    feature_id: str,
) -> list[tuple[CatalogNode, str, dict[str, object]]]:
    entries: list[tuple[CatalogNode, str, dict[str, object]]] = []
    references: dict[str, list[CatalogNode]] = {}
    for node in selection.feature_patch_nodes(feature_id):
        if node.patch in selection.injections:
            assert node.patch is not None
            references.setdefault(node.patch, []).append(node)
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
) -> PayloadFragment:
    alignment = _parse_int(value["alignment"], f"{label}.alignment", minimum=1)
    if alignment & (alignment - 1):
        raise ValueError(f"{label}.alignment must be a power of two")
    if "value" in value:
        payload = bytes.fromhex(_hex(value["value"], f"{label}.value"))
    else:
        blob = _source_path(repository, value["blob_path"], f"{label}.blob_path").read_bytes()
        if sha256_hex(blob) != _sha256(value.get("blob_sha256"), f"{label}.blob_sha256"):
            raise ValueError(f"{label}: blob SHA-256 mismatch")
        blob_offset = _parse_int(value.get("blob_offset", 0), f"{label}.blob_offset")
        length = _parse_int(value.get("length"), f"{label}.length", minimum=1)
        payload = blob[blob_offset:blob_offset + length]
        if len(payload) != length:
            raise ValueError(f"{label}: blob range is incomplete")
    relocations: list[PayloadRelocation] = []
    for relocation_id, raw in value.get("relocations", {}).items():
        _identifier(relocation_id, f"{label}.relocations key")
        encoding = raw["encoding"]
        if encoding not in RELOCATION_KINDS:
            raise ValueError(f"{label}.relocations.{relocation_id}.encoding is invalid")
        symbol = raw["symbol"]
        if not isinstance(symbol, str) or not SYMBOL_PATTERN.fullmatch(symbol):
            raise ValueError(f"{label}.relocations.{relocation_id}.symbol is invalid")
        relocations.append(
            PayloadRelocation(
                offset=_parse_int(raw["offset"], f"{label}.relocations.{relocation_id}.offset"),
                kind=encoding,
                symbol=symbol,
                addend=_parse_int(raw.get("addend", 0), f"{label}.relocations.{relocation_id}.addend", minimum=-0x80000000),
            )
        )
    return PayloadFragment(
        owner=owner,
        symbol=fragment_id,
        kind=str(value["kind"]),
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
) -> list[PayloadFragment]:
    language = str(value["kind"])
    source_path = _source_path(repository, value["path"], f"{label}.path")
    ee_c_fragments.validate_source_language(source_path, language)
    namespace = value["namespace"]
    imports: dict[str, ee_c_fragments.SymbolReference] = {}
    for name, raw in value.get("imports", {}).items():
        if isinstance(raw, str):
            symbol = raw
            addend = 0
        elif isinstance(raw, dict):
            symbol = raw.get("symbol")
            addend = _parse_int(raw.get("addend", 0), f"{label}.imports.{name}.addend", minimum=-0x80000000)
        else:
            raise ValueError(f"{label}.imports.{name} must be text or an object")
        if not isinstance(symbol, str) or not SYMBOL_PATTERN.fullmatch(symbol):
            raise ValueError(f"{label}.imports.{name}.symbol is invalid")
        imports[name] = ee_c_fragments.SymbolReference(symbol, addend)
    aliases = {
        raw["object"]: fragment_id for fragment_id, raw in value["fragments"].items()
    }
    packaged_object = source_path.with_name(source_path.name + ".o")
    if packaged_object.is_file():
        extracted = ee_c_fragments.extract_ee_object(
            packaged_object,
            namespace=namespace,
            owner=owner,
            external_symbols=imports,
        )
    else:
        from scripts.lib.paths import load_paths

        toolchain = ee_c_fragments.default_toolchain_bin(repository)
        build_root = load_paths(repository).path("build")
        root_existed = build_root.is_dir()
        build_root.mkdir(parents=True, exist_ok=True)
        object_path = None
        try:
            handle, object_name = tempfile.mkstemp(
                prefix=f"na2-catalog-ee-{source_id}-", suffix=".o", dir=build_root
            )
            object_path = Path(object_name)
            os.close(handle)
            extracted = ee_c_fragments.compile_and_extract(
                source_path,
                object_path,
                namespace=namespace,
                language=language,
                toolchain_bin=toolchain,
                owner=owner,
                external_symbols=imports,
            )
        finally:
            if object_path is not None:
                object_path.unlink(missing_ok=True)
            if not root_existed and not any(build_root.iterdir()):
                build_root.rmdir()
    actual = {fragment.symbol for fragment in extracted.fragments}
    if actual != set(aliases):
        raise ValueError(
            f"{label}: extracted fragments differ from declarations; "
            f"missing={sorted(set(aliases) - actual)}, extra={sorted(actual - set(aliases))}"
        )
    result: list[PayloadFragment] = []
    symbol_aliases = dict(aliases)
    extracted_by_symbol = {
        fragment.symbol: fragment for fragment in extracted.fragments
    }
    for object_fragment, fragment_id in aliases.items():
        fragment = extracted_by_symbol[object_fragment]
        result.append(
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
        if node.enabled and injection.get("hooks")
    ]
    hook_nodes = [node for node, _, _ in hook_entries]
    targets = binary_patcher.load_targets(targets_path)
    patches = {node.node_id: _internal_patch(node) for node in hook_nodes}
    edits: list[runtime_injector.RuntimeSymbolicEdit] = []
    used_targets: set[str] = set()
    order = 0
    for node, injection_id, injection in hook_entries:
        for hook_key, raw in injection["hooks"].items():
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
            if not isinstance(symbol, str) or not SYMBOL_PATTERN.fullmatch(symbol):
                raise ValueError(f"{label}.symbol is invalid")
            if encoding not in RELOCATION_KINDS:
                raise ValueError(f"{label}.encoding is invalid")
            order += 1
            used_targets.add(target_id)
            mapping_id = f"{node.node_id}.{injection_id}.{hook_key}"
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
    declared: list[PayloadFragment] = []
    for _, injection_id, payload_id, raw in payload_entries(selection, feature_id):
        label = f"injections.{injection_id}.payload.{payload_id}"
        if raw.get("kind") in {"c", "asm"}:
            declared.extend(_compile_source(repository, owner, payload_id, raw, label))
        else:
            declared.append(
                load_static_fragment(repository, owner, payload_id, raw, label)
            )
    symbols = [item.symbol for item in declared]
    if len(symbols) != len(set(symbols)):
        raise ValueError(f"{feature_id}: payload symbols must be unique")
    return runtime_injector.RuntimeInjectionPackage(
        directory=repository,
        owner=owner,
        targets={key: value for key, value in targets.items() if key in used_targets},
        patches=patches,
        fragments=tuple(declared),
        edits=tuple(edits),
    )


def feature_reference_ids(
    selection: CatalogSelection,
    feature_id: str,
    field: str,
) -> tuple[str, ...]:
    implementations = {
        "edits": selection.edits,
        "injections": selection.injections,
        "string_patches": selection.string_patches,
        "image_patches": {
            patch_id: definition["image_patch"]
            for patch_id, definition in selection.patches.items()
            if "image_patch" in definition
        },
    }
    if field not in implementations:
        raise ValueError(f"Unsupported catalog implementation field: {field}")
    if feature_id not in selection.catalog:
        raise ValueError(f"Unknown catalog feature: {feature_id}")
    return tuple(
        dict.fromkeys(
            patch
            for patch in feature_patch_ids(selection, feature_id)
            if patch in implementations[field]
        )
    )


def feature_patch_ids(
    selection: CatalogSelection,
    feature_id: str,
) -> tuple[str, ...]:
    if feature_id not in selection.catalog:
        raise ValueError(f"Unknown catalog feature: {feature_id}")
    return _patch_closure(_catalog_patches(selection.catalog[feature_id]), selection.patches)


def feature_has(
    selection: CatalogSelection,
    feature_id: str,
    field: str,
    *,
    enabled_only: bool = False,
) -> bool:
    references = set(feature_reference_ids(selection, feature_id, field))
    if enabled_only:
        references = {
            node.patch
            for node in selection.feature_patch_nodes(feature_id)
            if node.enabled and node.patch in references
        }
    if field == "injections":
        return any(selection.injections[patch_id].get("hooks") for patch_id in references)
    return bool(references)


def selected_patch_values(
    selection: CatalogSelection,
    field: str,
) -> tuple[tuple[CatalogNode, str, dict[str, object]], ...]:
    """Return each enabled patch's value for one patch field, such as image_file."""
    return tuple(
        (node, node.patch, selection.patches[node.patch][field])
        for node in selection.patch_nodes
        if node.enabled and node.patch is not None
        and field in selection.patches[node.patch]
    )


def selected_string_patches(
    selection: CatalogSelection,
    operation: str,
) -> tuple[tuple[CatalogNode, str, dict[str, object]], ...]:
    """Return enabled semantic string patches for one supported operation."""
    return tuple(
        item
        for item in selected_patch_values(selection, "string_patch")
        if item[2]["operation"] == operation
    )


def referenced_files(selection: CatalogSelection, repository: Path, feature_id: str) -> tuple[Path, ...]:
    files: set[Path] = set()
    for patch_id in feature_patch_ids(selection, feature_id):
        image_file = selection.patches[patch_id].get("image_file")
        if image_file is not None:
            files.add(_source_path(repository, image_file["asset"],
                                   f"patches.{patch_id}.image_file.asset"))
    for edit_id in feature_reference_ids(selection, feature_id, "edits"):
        for member_id, raw in _edit_members(edit_id, selection.edits[edit_id]):
            if "blob_path" in raw:
                label = f"edits.{edit_id}"
                if member_id is not None:
                    label += f".edits.{member_id}"
                files.add(
                    _source_path(
                        repository,
                        raw["blob_path"],
                        f"{label}.blob_path",
                    )
                )
    for injection_id in feature_reference_ids(selection, feature_id, "injections"):
        for payload_id, raw in selection.injections[injection_id].get("payload", {}).items():
            if raw["kind"] in {"c", "asm"}:
                files.add(
                    _source_path(
                        repository,
                        raw["path"],
                        f"injections.{injection_id}.payload.{payload_id}.path",
                    )
                )
                for index, resource in enumerate(raw.get("resources", [])):
                    files.add(
                        _source_path(
                            repository,
                            resource,
                            f"injections.{injection_id}.payload."
                            f"{payload_id}.resources[{index}]",
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
