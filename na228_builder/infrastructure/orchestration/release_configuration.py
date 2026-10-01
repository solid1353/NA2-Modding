from __future__ import annotations

import re
from pathlib import Path

from . import catalog_format, jsonc


def load_release_definition(path: Path) -> tuple[dict[str, object], dict[str, str]]:
    from .catalog import _read_jsonc

    definition = _read_jsonc(path, "Release configuration")
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
    if not isinstance(mapping, dict):
        raise ValueError("configuration_mapping must be an object")
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
    from .catalog import _validate_configuration_value

    _validate_configuration_value(schema, values, ())
    return schema, paths


def _set_value(result, path, value):
    for part in path[:-1]:
        result = result.setdefault(part, {})
    result[path[-1]] = value


def expand_configuration(features, values, defaults, release_values, mapping):
    from .catalog import _feature_root, _merge_configuration_value, _validate_configuration_value

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
    effective = _merge_configuration_value(
        _feature_root(features), defaults, overrides, ("features",)
    )
    _validate_configuration_value(_feature_root(features), effective, ("features",))
    return effective
