from __future__ import annotations

from . import catalog_format


def validate_layout(layout: object) -> dict[str, object]:
    """Validate public names, groups, and non-overlapping internal paths."""
    paths: list[tuple[str, ...]] = []

    def visit(group, public_path):
        if not isinstance(group, dict) or not group:
            raise ValueError(f"{public_path} must be a nonempty layout object")
        for name, entry in group.items():
            if (not isinstance(name, str) or not catalog_format.IDENTIFIER.fullmatch(name)
                    or name in {"description", "patch"}):
                raise ValueError(f"{public_path}: invalid public setting name {name!r}")
            label = f"{public_path}.{name}"
            if isinstance(entry, dict):
                visit(entry, label)
                continue
            if not isinstance(entry, str):
                raise ValueError(f"{label} must be a catalog path or layout object")
            path = tuple(entry.split("."))
            if (len(path) < 2 or path[0] != "features"
                    or any(not catalog_format.IDENTIFIER.fullmatch(part) for part in path)):
                raise ValueError(f"{label}: invalid catalog path {entry!r}")
            for previous in paths:
                common = min(len(path), len(previous))
                if path[:common] == previous[:common]:
                    raise ValueError(
                        f"Overlapping release mappings: {'.'.join(previous)} and {entry}"
                    )
            paths.append(path)

    visit(layout, "configuration_layout")
    return layout


def resolve_layout(features, layout):
    """Return the public schema and ordered public-to-internal path mappings."""
    validate_layout(layout)
    root = catalog_format.ContainerNode(tuple(
        catalog_format.ContainerField(name, node) for name, node in features.items()
    ))
    mappings = []

    def resolve(path):
        node = root
        for part in path[1:]:
            expanded = catalog_format.expand_node(node)
            if not isinstance(expanded, catalog_format.ContainerNode):
                raise ValueError(f"Release path crosses a setting or union: {'.'.join(path)}")
            fields = {field.name: field.node for field in expanded.fields}
            if part not in fields:
                raise ValueError(f"Unknown release catalog path: {'.'.join(path)}")
            node = fields[part]
        return node

    def collect(group, public_path):
        fields = []
        for name, entry in group.items():
            path = (*public_path, name)
            if isinstance(entry, dict):
                node = collect(entry, path)
            else:
                internal_path = tuple(entry.split("."))
                node = resolve(internal_path)
                mappings.append((path, internal_path[1:]))
            fields.append(catalog_format.ContainerField(name, node))
        return catalog_format.ContainerNode(tuple(fields))

    return collect(layout, ()), tuple(mappings)


def _value_at(value, path):
    for part in path:
        if value is False:
            return False
        value = value[part]
    return value


def _set_value(result, path, value):
    for part in path[:-1]:
        result = result.setdefault(part, {})
    result[path[-1]] = value


def project_configuration(features, values, layout):
    from .catalog import _validate_configuration_value

    schema, mappings = resolve_layout(features, layout)
    result = {}
    for public_path, internal_path in mappings:
        _set_value(result, public_path, _value_at(values, internal_path))
    _validate_configuration_value(schema, result, ())
    return result


def expand_configuration(features, values, defaults, layout):
    from .catalog import _feature_root, _merge_configuration_value, _validate_configuration_value

    schema, mappings = resolve_layout(features, layout)
    _validate_configuration_value(schema, values, ())
    overrides = {}
    for public_path, internal_path in mappings:
        _set_value(overrides, internal_path, _value_at(values, public_path))
    return _merge_configuration_value(_feature_root(features), defaults, overrides, ("features",))
