from __future__ import annotations

from pathlib import Path

from . import catalog_format


def load_release_definition(path: Path) -> tuple[dict[str, object], dict[str, str]]:
    from .catalog import _read_jsonc

    definition = _read_jsonc(path, "Release configuration")
    layout = definition.pop("configuration_layout", None)
    if not definition or not isinstance(layout, dict):
        raise ValueError("Release configuration needs public settings and a layout object")
    return definition, layout


def resolve_layout(features, values, layout):
    """Derive the public schema and mappings from the release values."""
    root = catalog_format.ContainerNode(tuple(
        catalog_format.ContainerField(name, node) for name, node in features.items()
    ))
    if not isinstance(layout, dict):
        raise ValueError("configuration_layout must be an object")
    for public, target in layout.items():
        if (not isinstance(public, str) or not public
                or any(not catalog_format.IDENTIFIER.fullmatch(part)
                       for part in public.split("."))
                or not isinstance(target, str) or not target
                or any(not catalog_format.IDENTIFIER.fullmatch(part)
                       for part in target.split("."))):
            raise ValueError(f"Invalid release mapping: {public!r}: {target!r}")
    mappings = []
    paths = {}
    used_layout = set()

    def resolve(path):
        node = root
        for part in path:
            expanded = catalog_format.expand_node(node)
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
                        or name in {"description", "patch", "configuration_layout"}):
                    raise ValueError(f"Invalid public setting name: {name!r}")
                path = (*public_path, name)
                layout_key = ".".join(path)
                target = layout.get(layout_key)
                if target is None:
                    child_path = (*internal_path, name)
                else:
                    child_path = tuple(target.split("."))
                    used_layout.add(layout_key)
                child = visit(value, path, child_path)
                fields.append(catalog_format.ContainerField(name, child))
            return catalog_format.ContainerNode(tuple(fields), expanded.description)
        mappings.append((public_path, internal_path))
        return node

    schema = visit(values, (), ())
    unused = set(layout) - used_layout
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


def expand_configuration(features, values, defaults, release_values, layout):
    from .catalog import _feature_root, _merge_configuration_value, _validate_configuration_value

    schema, paths = resolve_layout(features, release_values, layout)
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
