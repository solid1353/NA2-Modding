from __future__ import annotations

import csv
import hashlib
import json
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from .modules.binary_patcher import engine as binary_patcher
from .modules.runtime_injector import engine as runtime_injector
from .payload_builder import ee_c_fragments
from .payload_builder.operations import (
    FRAGMENT_KINDS,
    RELOCATION_KINDS,
    PayloadFragment,
    PayloadRelocation,
    SymbolicPatch,
)


IDENTIFIER = re.compile(r"[a-z][a-z0-9_]*\Z")
RESERVED_NODE_FIELDS = frozenset(
    {"description", "proven", "edits", "hooks", "payload"}
)
PIN_FIELDS = ["feature_id", "expected_sha256", "bypass_check"]
LEGACY_PIN_FIELDS = ["feature_id", "enabled", "expected_sha256", "bypass_check"]
OPERATION_FIELDS = ["field", "required", "type"]
FIELD_TYPES = {"hex", "integer", "path", "sha256", "text"}


@dataclass(frozen=True)
class CatalogNode:
    path: tuple[str, ...]
    value: dict[str, object]
    enabled: bool

    @property
    def feature_id(self) -> str:
        return self.path[0]

    @property
    def node_id(self) -> str:
        return ".".join(self.path)


@dataclass(frozen=True)
class CatalogSelection:
    catalog_path: Path
    configuration_path: Path
    nodes: tuple[CatalogNode, ...]

    @property
    def configuration_id(self) -> str:
        return self.configuration_path.stem

    @property
    def feature_ids(self) -> tuple[str, ...]:
        return tuple(node.path[0] for node in self.nodes if len(node.path) == 1)

    def feature_nodes(self, feature_id: str) -> tuple[CatalogNode, ...]:
        return tuple(node for node in self.nodes if node.feature_id == feature_id)

    def node_enabled(self, *path: str) -> bool:
        matches = [node for node in self.nodes if node.path == path]
        if len(matches) != 1:
            raise ValueError(f"Catalog selection has no unique node: {'.'.join(path)}")
        return matches[0].enabled


@dataclass(frozen=True)
class FeaturePin:
    feature_id: str
    expected_sha256: str
    bypass_check: bool


@dataclass(frozen=True)
class OperationField:
    name: str
    required: bool
    type: str


def _read_json(path: Path, label: str) -> dict[str, object]:
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
    if not isinstance(value, dict) or not value:
        raise ValueError(f"{label} root must be a non-empty object")
    return value


def _identifier(value: str, label: str) -> str:
    if not IDENTIFIER.fullmatch(value):
        raise ValueError(f"{label} must be a meaningful snake_case key: {value!r}")
    return value


def _description(value: object, label: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError(f"{label} description must be text")
    return value


def _selectable_children(value: dict[str, object], label: str) -> dict[str, dict[str, object]]:
    children: dict[str, dict[str, object]] = {}
    for key, child in value.items():
        if key in RESERVED_NODE_FIELDS:
            continue
        _identifier(key, f"{label} key")
        if not isinstance(child, dict):
            raise ValueError(f"{label}.{key} must be an object")
        children[key] = child
    return children


def load_selection(catalog_path: Path, configuration_path: Path) -> CatalogSelection:
    catalog_path = catalog_path.resolve()
    configuration_path = configuration_path.resolve()
    catalog = _read_json(catalog_path, "Catalog")
    configuration = _read_json(configuration_path, "Configuration")
    nodes: list[CatalogNode] = []

    def setting_enabled(setting: object) -> bool:
        if isinstance(setting, bool):
            return setting
        if isinstance(setting, dict):
            return any(setting_enabled(child) for child in setting.values())
        return False

    def visit(
        value: dict[str, object],
        setting: object,
        path: tuple[str, ...],
        inherited_enabled: bool,
    ) -> None:
        label = ".".join(path)
        _description(value.get("description"), label)
        if "proven" in value and value["proven"] is not False:
            raise ValueError(f"{label}.proven must be false when present")
        for field in ("edits", "hooks", "payload"):
            if field in value and not isinstance(value[field], dict):
                raise ValueError(f"{label}.{field} must be an object")
        children = _selectable_children(value, label)
        if isinstance(setting, bool):
            enabled = inherited_enabled and setting
            nodes.append(CatalogNode(path, value, enabled))
            for key, child in children.items():
                visit(child, setting, (*path, key), enabled)
            return
        if not isinstance(setting, dict):
            raise ValueError(f"Configuration {label} must be true, false, or an object")
        if not children:
            raise ValueError(f"Configuration leaf {label} must be true or false")
        if set(setting) != set(children):
            missing = sorted(set(children) - set(setting))
            extra = sorted(set(setting) - set(children))
            raise ValueError(
                f"Configuration {label} children differ from catalog; "
                f"missing={missing}, extra={extra}"
            )
        enabled = inherited_enabled and setting_enabled(setting)
        nodes.append(CatalogNode(path, value, enabled))
        for key, child in children.items():
            visit(child, setting[key], (*path, key), enabled)

    catalog_children = _selectable_children(catalog, "catalog")
    if set(configuration) != set(catalog_children):
        missing = sorted(set(catalog_children) - set(configuration))
        extra = sorted(set(configuration) - set(catalog_children))
        raise ValueError(
            "Configuration root differs from catalog; "
            f"missing={missing}, extra={extra}"
        )
    for key, value in catalog_children.items():
        visit(value, configuration[key], (key,), True)
    return CatalogSelection(catalog_path, configuration_path, tuple(nodes))


def all_enabled_configuration(catalog_path: Path) -> dict[str, object]:
    """Return a structurally complete configuration with every leaf enabled."""
    catalog = _read_json(catalog_path.resolve(), "Catalog")

    def enabled_node(value: dict[str, object], label: str) -> object:
        children = _selectable_children(value, label)
        if not children:
            return True
        return {
            key: enabled_node(child, f"{label}.{key}")
            for key, child in children.items()
        }

    return {
        key: enabled_node(value, key)
        for key, value in _selectable_children(catalog, "catalog").items()
    }


def read_pins(path: Path) -> tuple[FeaturePin, ...]:
    pins: list[FeaturePin] = []
    seen: set[str] = set()
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames not in (PIN_FIELDS, LEGACY_PIN_FIELDS):
            raise ValueError(
                f"{path}: expected pin columns " + "\t".join(PIN_FIELDS)
            )
        for line, row in enumerate(reader, 2):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"{path}:{line}: malformed row")
            if not any(value.strip() for value in row.values()):
                continue
            feature_id = _identifier(row["feature_id"].strip(), f"{path}:{line} feature_id")
            if feature_id in seen:
                raise ValueError(f"{path}:{line}: duplicate feature {feature_id}")
            seen.add(feature_id)
            digest = row["expected_sha256"].strip().upper()
            if not re.fullmatch(r"[0-9A-F]{64}", digest):
                raise ValueError(f"{path}:{line}: invalid expected_sha256")
            bypass = row["bypass_check"].strip()
            if bypass not in {"0", "1"}:
                raise ValueError(f"{path}:{line}: bypass_check must be 0 or 1")
            pins.append(FeaturePin(feature_id, digest, bypass == "1"))
    if not pins:
        raise ValueError(f"{path}: no feature pins")
    return tuple(pins)


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
        elif field.type == "hex":
            _hex(value, field_label)
        elif field.type == "sha256":
            _sha256(value, field_label)
        elif field.type == "path":
            _relative_path(value, field_label)
        elif not isinstance(value, str):
            raise ValueError(f"{field_label} must be text")
    return operation


def _group_id(node: CatalogNode) -> str:
    return ".".join(node.path[:-1]) or node.feature_id


def _internal_patch(node: CatalogNode) -> binary_patcher.Patch:
    description = _description(node.value.get("description"), node.node_id)
    return binary_patcher.Patch(
        patch_id=node.node_id,
        group_id=_group_id(node),
        enabled=node.enabled,
        status="approved_for_test",
        confidence="verified",
        name=node.path[-1],
        description=description,
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
        if isinstance(node.value.get("edits"), dict) and node.value["edits"]
    ]
    targets = binary_patcher.load_targets(targets_path)
    contracts = load_operation_contracts(operations_path)
    patches = {node.node_id: _internal_patch(node) for node in nodes}
    edits: list[binary_patcher.Edit] = []
    used_targets: set[str] = set()
    order = 0
    for node in nodes:
        raw_edits = node.value["edits"]
        assert isinstance(raw_edits, dict)
        for edit_key, raw_edit in raw_edits.items():
            _identifier(edit_key, f"{node.node_id}.edits key")
            if not isinstance(raw_edit, dict):
                raise ValueError(f"{node.node_id}.edits.{edit_key} must be an object")
            label = f"{node.node_id}.edits.{edit_key}"
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
            destination_offset = _parse_int(raw_edit["destination_offset"], f"{label}.destination_offset")
            replacement_hex = ""
            source_id = ""
            source_offset: int | None = None
            blob_path: PurePosixPath | None = None
            blob_sha256 = ""
            fill_hex = ""
            if operation == "replace":
                replacement_hex = _hex(raw_edit["replacement_hex"], f"{label}.replacement_hex")
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
            order += 1
            used_targets.add(destination_id)
            edits.append(
                binary_patcher.Edit(
                    edit_id=f"{node.node_id}.{edit_key}",
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
                    reason="",
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
) -> list[tuple[CatalogNode, str, dict[str, object]]]:
    entries: list[tuple[CatalogNode, str, dict[str, object]]] = []
    seen: set[str] = set()
    for node in selection.feature_nodes(feature_id):
        payload = node.value.get("payload")
        if not isinstance(payload, dict):
            continue
        for key, value in payload.items():
            if not runtime_injector.IDENTIFIER.fullmatch(key):
                raise ValueError(f"{node.node_id}.payload key is invalid: {key!r}")
            if key in seen:
                raise ValueError(f"Duplicate payload declaration {key!r} in {feature_id}")
            seen.add(key)
            if not isinstance(value, dict):
                raise ValueError(f"{node.node_id}.payload.{key} must be an object")
            if node.enabled:
                entries.append((node, key, value))
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
    hook_nodes = [
        node
        for node in selection.feature_nodes(feature_id)
        if isinstance(node.value.get("hooks"), dict) and node.value["hooks"]
    ]
    targets = binary_patcher.load_targets(targets_path)
    patches = {node.node_id: _internal_patch(node) for node in hook_nodes}
    edits: list[runtime_injector.RuntimeSymbolicEdit] = []
    used_targets: set[str] = set()
    order = 0
    for node in hook_nodes:
        raw_hooks = node.value["hooks"]
        assert isinstance(raw_hooks, dict)
        for hook_key, raw in raw_hooks.items():
            _identifier(hook_key, f"{node.node_id}.hooks key")
            if not isinstance(raw, dict):
                raise ValueError(f"{node.node_id}.hooks.{hook_key} must be an object")
            label = f"{node.node_id}.hooks.{hook_key}"
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
                        reason="",
                        addend=_parse_int(raw.get("addend", 0), f"{label}.addend", minimum=-0x80000000),
                        replacement_template=template,
                        relocation_offset=_parse_int(raw.get("relocation_offset", 0), f"{label}.relocation_offset"),
                    ),
                )
            )
    declared: list[tuple[int, PayloadFragment]] = []
    for node, payload_id, raw in payload_entries(selection, feature_id):
        label = f"{node.node_id}.payload.{payload_id}"
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


def feature_has(
    selection: CatalogSelection,
    feature_id: str,
    field: str,
    *,
    enabled_only: bool = False,
) -> bool:
    return any(
        (not enabled_only or node.enabled)
        and isinstance(node.value.get(field), dict)
        and node.value[field]
        for node in selection.feature_nodes(feature_id)
    )


def referenced_files(selection: CatalogSelection, repository: Path, feature_id: str) -> tuple[Path, ...]:
    files: set[Path] = set()
    for node in selection.feature_nodes(feature_id):
        edits = node.value.get("edits")
        if isinstance(edits, dict):
            for raw in edits.values():
                if isinstance(raw, dict) and "blob_path" in raw:
                    files.add(_source_path(repository, raw["blob_path"], f"{node.node_id}.blob_path"))
        payload = node.value.get("payload")
        if not isinstance(payload, dict):
            continue
        for payload_id, raw in payload.items():
            if not isinstance(raw, dict):
                continue
            if raw.get("kind") == "c":
                files.add(_source_path(repository, raw.get("path"), f"{node.node_id}.payload.{payload_id}.path"))
            elif "blob_path" in raw:
                files.add(_source_path(repository, raw["blob_path"], f"{node.node_id}.payload.{payload_id}.blob_path"))
    return tuple(sorted(files, key=lambda path: path.as_posix()))
