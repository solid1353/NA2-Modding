from __future__ import annotations

import csv
import hashlib
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from ...payload_builder import ee_c_fragments
from ...payload_builder.operations import (
    FRAGMENT_KINDS,
    RELOCATION_KINDS,
    PayloadFragment,
    PayloadRelocation,
    ResolvedPatch,
    SymbolicPatch,
)
from ..binary_patcher import engine as binary_patcher


TARGET_FIELDS = binary_patcher.TARGET_FIELDS
GROUP_FIELDS = binary_patcher.GROUP_FIELDS
PATCH_FIELDS = binary_patcher.PATCH_FIELDS
FRAGMENT_FIELDS = [
    "fragment_id",
    "order",
    "kind",
    "alignment",
    "payload_hex",
    "blob_path",
    "blob_offset",
    "length",
    "blob_sha256",
    "init",
]
C_SOURCE_FIELDS = [
    "source_id",
    "language",
    "path",
    "namespace",
]
C_IMPORT_FIELDS = [
    "source_id",
    "name",
    "symbol",
    "addend",
]
C_FRAGMENT_FIELDS = [
    "source_id",
    "order",
    "object_fragment",
    "fragment_id",
]
RELOCATION_FIELDS = [
    "relocation_id",
    "fragment_id",
    "order",
    "offset",
    "kind",
    "symbol",
    "addend",
]
EDIT_FIELDS = [
    "edit_id",
    "patch_id",
    "order",
    "target_id",
    "offset",
    "expected_hex",
    "replacement_hex",
    "relocation_offset",
    "symbol",
    "encoding",
    "addend",
    "reason",
]
CONTROL_FILES = (
    "targets.tsv",
    "groups.tsv",
    "patches.tsv",
    "fragments.tsv",
    "c_sources.tsv",
    "c_imports.tsv",
    "c_fragments.tsv",
    "relocations.tsv",
    "edits.tsv",
)
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*\Z")


@dataclass(frozen=True)
class RuntimeSymbolicEdit:
    edit_id: str
    patch_id: str
    order: int
    target_id: str
    symbolic_patch: SymbolicPatch


@dataclass(frozen=True)
class RuntimeInjectionPackage:
    directory: Path
    owner: str
    targets: dict[str, binary_patcher.Target]
    groups: dict[str, binary_patcher.Group]
    patches: dict[str, binary_patcher.Patch]
    fragments: tuple[PayloadFragment, ...]
    edits: tuple[RuntimeSymbolicEdit, ...]

    @property
    def active_edits(self) -> tuple[RuntimeSymbolicEdit, ...]:
        return tuple(
            edit
            for edit in self.edits
            if self.patches[edit.patch_id].enabled
            and self.groups[self.patches[edit.patch_id].group_id].enabled
        )

    @property
    def symbolic_patches(self) -> tuple[SymbolicPatch, ...]:
        return tuple(edit.symbolic_patch for edit in self.active_edits)

    @property
    def payload_fragments(self) -> tuple[PayloadFragment, ...]:
        # Fragments have package-wide symbolic dependencies. Retain and validate
        # every declaration, but contribute none when every owning patch is off.
        return self.fragments if self.active_edits else ()


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


def _identifier(value: str, label: str) -> str:
    if not IDENTIFIER.fullmatch(value):
        raise ValueError(f"{label}: invalid identifier {value!r}")
    return value


def _integer(value: str, label: str, *, minimum: int = 0) -> int:
    try:
        result = int(value, 0)
    except ValueError as exc:
        raise ValueError(f"{label}: invalid integer {value!r}") from exc
    if result < minimum:
        raise ValueError(f"{label}: value must be at least {minimum}")
    return result


def _hex(value: str, label: str, *, allow_empty: bool = False) -> bytes:
    compact = "".join(value.split()).upper()
    if not compact and allow_empty:
        return b""
    if not compact or len(compact) % 2 or not re.fullmatch(r"[0-9A-F]+", compact):
        raise ValueError(f"{label}: invalid hexadecimal data")
    return bytes.fromhex(compact)


def _sha256(value: str, label: str) -> str:
    normalized = value.upper()
    if len(normalized) != 64 or not re.fullmatch(r"[0-9A-F]{64}", normalized):
        raise ValueError(f"{label}: SHA-256 must be 64 hex digits")
    return normalized


def _relative_path(value: str, label: str) -> PurePosixPath:
    normalized = value.replace("\\", "/")
    path = PurePosixPath(normalized)
    if not normalized or path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{label}: path must be package-relative")
    return path


def _load_targets(directory: Path) -> dict[str, binary_patcher.Target]:
    targets: dict[str, binary_patcher.Target] = {}
    for line, row in enumerate(
        _read_tsv(directory / "targets.tsv", TARGET_FIELDS), 2
    ):
        target_id = _identifier(row["target_id"], f"targets.tsv:{line} target_id")
        if target_id in targets:
            raise ValueError(f"targets.tsv:{line}: duplicate target {target_id}")
        role = row["role"]
        if role != "destination":
            raise ValueError(
                f"targets.tsv:{line}: runtime-injector symbolic targets must be destinations"
            )
        path = _relative_path(row["path"], f"targets.tsv:{line} path")
        targets[target_id] = binary_patcher.Target(
            target_id=target_id,
            root_id=_identifier(
                row["root_id"], f"targets.tsv:{line} root_id"
            ),
            role=role,
            path=path,
            expected_size=_integer(
                row["expected_size"], f"targets.tsv:{line} expected_size", minimum=1
            ),
            expected_sha256=_sha256(
                row["expected_sha256"], f"targets.tsv:{line} expected_sha256"
            ),
        )
    if not targets:
        raise ValueError("runtime_injector requires at least one target")
    return targets


def _load_groups(directory: Path) -> dict[str, binary_patcher.Group]:
    groups: dict[str, binary_patcher.Group] = {}
    for line, row in enumerate(
        _read_tsv(directory / "groups.tsv", GROUP_FIELDS), 2
    ):
        group_id = _identifier(row["group_id"], f"groups.tsv:{line} group_id")
        if group_id in groups:
            raise ValueError(f"groups.tsv:{line}: duplicate group {group_id}")
        if not row["name"] or not row["description"]:
            raise ValueError(f"groups.tsv:{line}: name and description are required")
        groups[group_id] = binary_patcher.Group(
            group_id=group_id,
            enabled=binary_patcher.parse_bool(
                row["enabled"], f"groups.tsv:{line} enabled"
            ),
            name=row["name"],
            description=row["description"],
            review_notes=row["review_notes"],
        )
    if not groups:
        raise ValueError("runtime_injector requires at least one group")
    return groups


def _load_patches(
    directory: Path, groups: dict[str, binary_patcher.Group]
) -> dict[str, binary_patcher.Patch]:
    patches: dict[str, binary_patcher.Patch] = {}
    for line, row in enumerate(
        _read_tsv(directory / "patches.tsv", PATCH_FIELDS), 2
    ):
        patch_id = _identifier(row["patch_id"], f"patches.tsv:{line} patch_id")
        if patch_id in patches:
            raise ValueError(f"patches.tsv:{line}: duplicate patch {patch_id}")
        group_id = row["group_id"]
        if group_id not in groups:
            raise ValueError(f"patches.tsv:{line}: unknown group {group_id!r}")
        enabled = binary_patcher.parse_bool(
            row["enabled"], f"patches.tsv:{line} enabled"
        )
        status = row["status"]
        confidence = row["confidence"]
        if status not in binary_patcher.PATCH_STATUSES:
            raise ValueError(
                f"patches.tsv:{line}: invalid status {status!r}"
            )
        if enabled and status not in binary_patcher.APPLICABLE_STATUSES:
            raise ValueError(
                f"patches.tsv:{line}: enabled runtime-injector patches "
                "must be applicable"
            )
        if confidence not in binary_patcher.CONFIDENCE_VALUES:
            raise ValueError(f"patches.tsv:{line}: invalid confidence {confidence!r}")
        if not row["name"] or not row["description"] or not row["evidence_id"]:
            raise ValueError(
                f"patches.tsv:{line}: name, description, and evidence_id "
                "are required"
            )
        patches[patch_id] = binary_patcher.Patch(
            patch_id=patch_id,
            group_id=group_id,
            enabled=enabled,
            status=status,
            confidence=confidence,
            name=row["name"],
            description=row["description"],
            evidence_id=row["evidence_id"],
            review_notes=row["review_notes"],
        )
    if not patches:
        raise ValueError("runtime_injector requires at least one patch")
    return patches


def _module_file(directory: Path, value: str, label: str) -> Path:
    relative = _relative_path(value, label)
    path = (directory / Path(relative.as_posix())).resolve()
    try:
        path.relative_to(directory.resolve())
    except ValueError as exc:
        raise ValueError(f"{label}: path escapes module") from exc
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def _repository_root(directory: Path) -> Path:
    for candidate in (directory.resolve(), *directory.resolve().parents):
        if (candidate / "paths.json").is_file():
            return candidate
    raise FileNotFoundError("paths.json was not found")


def _source_file(directory: Path, value: str, label: str) -> Path:
    relative = _relative_path(value, label)
    if relative.parts and relative.parts[0] == "src":
        repository = _repository_root(directory)
        source_root = (repository / "src").resolve()
        path = (repository / Path(relative.as_posix())).resolve()
        try:
            path.relative_to(source_root)
        except ValueError as exc:
            raise ValueError(f"{label}: path escapes src") from exc
        if not path.is_file():
            raise FileNotFoundError(path)
        return path
    return _module_file(directory, value, label)


def _load_static_fragments(
    directory: Path, owner: str
) -> list[tuple[int, int, PayloadFragment]]:
    fragment_rows = _read_tsv(directory / "fragments.tsv", FRAGMENT_FIELDS)
    relocation_rows = _read_tsv(
        directory / "relocations.tsv", RELOCATION_FIELDS
    )
    rows_by_id: dict[str, tuple[int, dict[str, str]]] = {}
    for line, row in enumerate(fragment_rows, 2):
        fragment_id = _identifier(
            row["fragment_id"], f"fragments.tsv:{line} fragment_id"
        )
        if fragment_id in rows_by_id:
            raise ValueError(f"fragments.tsv:{line}: duplicate fragment {fragment_id}")
        rows_by_id[fragment_id] = (line, row)
    relocations: dict[str, list[tuple[int, int, PayloadRelocation]]] = {
        fragment_id: [] for fragment_id in rows_by_id
    }
    relocation_ids: set[str] = set()
    for line, row in enumerate(relocation_rows, 2):
        relocation_id = _identifier(
            row["relocation_id"], f"relocations.tsv:{line} relocation_id"
        )
        if relocation_id in relocation_ids:
            raise ValueError(
                f"relocations.tsv:{line}: duplicate relocation {relocation_id}"
            )
        relocation_ids.add(relocation_id)
        fragment_id = row["fragment_id"]
        if fragment_id not in rows_by_id:
            raise ValueError(
                f"relocations.tsv:{line}: unknown fragment {fragment_id!r}"
            )
        kind = row["kind"]
        if kind not in RELOCATION_KINDS:
            raise ValueError(f"relocations.tsv:{line}: invalid kind {kind!r}")
        order = _integer(row["order"], f"relocations.tsv:{line} order", minimum=1)
        relocation = PayloadRelocation(
            offset=_integer(row["offset"], f"relocations.tsv:{line} offset"),
            kind=kind,
            symbol=_identifier(
                row["symbol"], f"relocations.tsv:{line} symbol"
            ),
            addend=_integer(
                row["addend"], f"relocations.tsv:{line} addend", minimum=-0x80000000
            ),
        )
        relocations[fragment_id].append((order, line, relocation))

    fragments: list[tuple[int, int, PayloadFragment]] = []
    blob_cache: dict[Path, bytes] = {}
    for fragment_id, (line, row) in rows_by_id.items():
        order = _integer(
            row["order"], f"fragments.tsv:{line} order", minimum=1
        )
        kind = row["kind"]
        if kind not in FRAGMENT_KINDS:
            raise ValueError(f"fragments.tsv:{line}: invalid kind {kind!r}")
        alignment = _integer(
            row["alignment"], f"fragments.tsv:{line} alignment", minimum=1
        )
        if alignment & (alignment - 1):
            raise ValueError(
                f"fragments.tsv:{line}: alignment must be a power of two"
            )
        length = _integer(
            row["length"], f"fragments.tsv:{line} length", minimum=1
        )
        has_inline = bool(row["payload_hex"])
        has_blob = bool(row["blob_path"])
        if has_inline == has_blob:
            raise ValueError(
                f"fragments.tsv:{line}: exactly one of payload_hex or "
                "blob_path is required"
            )
        if has_inline:
            if row["blob_offset"] or row["blob_sha256"]:
                raise ValueError(
                    f"fragments.tsv:{line}: inline payload cannot declare "
                    "blob_offset or blob_sha256"
                )
            payload = _hex(
                row["payload_hex"], f"fragments.tsv:{line} payload_hex"
            )
            if len(payload) != length:
                raise ValueError(
                    f"fragments.tsv:{line}: inline payload length "
                    f"{len(payload)} does not match {length}"
                )
        else:
            blob_path = _module_file(
                directory,
                row["blob_path"],
                f"fragments.tsv:{line} blob_path",
            )
            blob = blob_cache.setdefault(blob_path, blob_path.read_bytes())
            expected_blob_hash = _sha256(
                row["blob_sha256"], f"fragments.tsv:{line} blob_sha256"
            )
            actual_blob_hash = hashlib.sha256(blob).hexdigest().upper()
            if actual_blob_hash != expected_blob_hash:
                raise ValueError(
                    f"fragments.tsv:{line}: blob SHA-256 {actual_blob_hash} "
                    f"does not match {expected_blob_hash}"
                )
            blob_offset = _integer(
                row["blob_offset"], f"fragments.tsv:{line} blob_offset"
            )
            payload = blob[blob_offset:blob_offset + length]
            if len(payload) != length:
                raise ValueError(f"fragments.tsv:{line}: fragment exceeds blob")
        ordered_relocations = sorted(
            relocations[fragment_id], key=lambda item: (item[0], item[1])
        )
        if len({item[0] for item in ordered_relocations}) != len(
            ordered_relocations
        ):
            raise ValueError(
                f"fragments.tsv:{line}: relocation order values must be unique"
            )
        fragments.append(
            (
                order,
                line,
                PayloadFragment(
                    owner=owner,
                    symbol=fragment_id,
                    kind=kind,
                    alignment=alignment,
                    payload=payload,
                    relocations=tuple(item[2] for item in ordered_relocations),
                    init=binary_patcher.parse_bool(
                        row["init"], f"fragments.tsv:{line} init"
                    ),
                ),
            )
        )
    return fragments


def _load_c_fragments(
    directory: Path, owner: str
) -> list[tuple[int, int, PayloadFragment]]:
    source_rows = _read_tsv(directory / "c_sources.tsv", C_SOURCE_FIELDS)
    import_rows = _read_tsv(directory / "c_imports.tsv", C_IMPORT_FIELDS)
    fragment_rows = _read_tsv(
        directory / "c_fragments.tsv", C_FRAGMENT_FIELDS
    )
    sources: dict[str, tuple[int, Path, str]] = {}
    for line, row in enumerate(source_rows, 2):
        source_id = _identifier(
            row["source_id"], f"c_sources.tsv:{line} source_id"
        )
        if source_id in sources:
            raise ValueError(
                f"c_sources.tsv:{line}: duplicate source {source_id}"
            )
        if row["language"] != "c":
            raise ValueError(
                f"c_sources.tsv:{line}: unsupported language "
                f"{row['language']!r}"
            )
        source_path = _source_file(
            directory, row["path"], f"c_sources.tsv:{line} path"
        )
        namespace = _identifier(
            row["namespace"], f"c_sources.tsv:{line} namespace"
        )
        sources[source_id] = (line, source_path, namespace)

    imports: dict[str, dict[str, ee_c_fragments.SymbolReference]] = {
        source_id: {} for source_id in sources
    }
    for line, row in enumerate(import_rows, 2):
        source_id = row["source_id"]
        if source_id not in sources:
            raise ValueError(
                f"c_imports.tsv:{line}: unknown source {source_id!r}"
            )
        name = _identifier(row["name"], f"c_imports.tsv:{line} name")
        if name in imports[source_id]:
            raise ValueError(
                f"c_imports.tsv:{line}: duplicate import {name!r} "
                f"for {source_id}"
            )
        imports[source_id][name] = ee_c_fragments.SymbolReference(
            symbol=_identifier(
                row["symbol"], f"c_imports.tsv:{line} symbol"
            ),
            addend=_integer(
                row["addend"],
                f"c_imports.tsv:{line} addend",
                minimum=-0x80000000,
            ),
        )

    mappings: dict[
        str, dict[str, tuple[int, int, str]]
    ] = {source_id: {} for source_id in sources}
    final_ids: set[str] = set()
    for line, row in enumerate(fragment_rows, 2):
        source_id = row["source_id"]
        if source_id not in sources:
            raise ValueError(
                f"c_fragments.tsv:{line}: unknown source {source_id!r}"
            )
        object_fragment = _identifier(
            row["object_fragment"],
            f"c_fragments.tsv:{line} object_fragment",
        )
        if object_fragment in mappings[source_id]:
            raise ValueError(
                f"c_fragments.tsv:{line}: duplicate object fragment "
                f"{object_fragment!r} for {source_id}"
            )
        fragment_id = _identifier(
            row["fragment_id"], f"c_fragments.tsv:{line} fragment_id"
        )
        if fragment_id in final_ids:
            raise ValueError(
                f"c_fragments.tsv:{line}: duplicate output fragment "
                f"{fragment_id!r}"
            )
        final_ids.add(fragment_id)
        mappings[source_id][object_fragment] = (
            _integer(
                row["order"],
                f"c_fragments.tsv:{line} order",
                minimum=1,
            ),
            line,
            fragment_id,
        )

    if not sources and fragment_rows:
        raise ValueError("c_fragments.tsv declares fragments without sources")
    if not sources:
        return []

    result: list[tuple[int, int, PayloadFragment]] = []
    repository = _repository_root(directory)
    toolchain = ee_c_fragments.default_toolchain_bin(repository)
    with tempfile.TemporaryDirectory(prefix="na2-runtime-c-") as temporary:
        output_root = Path(temporary)
        for source_id, (_line, source_path, namespace) in sources.items():
            extracted = ee_c_fragments.compile_and_extract(
                source_path,
                output_root / f"{source_id}.o",
                namespace=namespace,
                toolchain_bin=toolchain,
                owner=owner,
                external_symbols=imports[source_id],
            )
            aliases = {
                object_fragment: mapping[2]
                for object_fragment, mapping in mappings[source_id].items()
            }
            actual = {fragment.symbol for fragment in extracted.fragments}
            declared = set(aliases)
            if actual != declared:
                raise ValueError(
                    f"C source {source_id}: extracted fragments differ from "
                    f"declarations; missing={sorted(declared - actual)}, "
                    f"extra={sorted(actual - declared)}"
                )
            for fragment in extracted.fragments:
                order, line, fragment_id = mappings[source_id][fragment.symbol]
                result.append(
                    (
                        order,
                        line,
                        PayloadFragment(
                            owner=owner,
                            symbol=fragment_id,
                            kind=fragment.kind,
                            alignment=fragment.alignment,
                            payload=fragment.payload,
                            relocations=tuple(
                                PayloadRelocation(
                                    offset=relocation.offset,
                                    kind=relocation.kind,
                                    symbol=aliases.get(
                                        relocation.symbol,
                                        relocation.symbol,
                                    ),
                                    addend=relocation.addend,
                                )
                                for relocation in fragment.relocations
                            ),
                            init=fragment.init,
                        ),
                    )
                )
    return result


def _load_fragments(
    directory: Path, owner: str
) -> tuple[PayloadFragment, ...]:
    declared = [
        *_load_static_fragments(directory, owner),
        *_load_c_fragments(directory, owner),
    ]
    if not declared:
        raise ValueError("runtime_injector requires at least one fragment")
    orders = [item[0] for item in declared]
    if len(orders) != len(set(orders)):
        raise ValueError("runtime_injector fragment orders must be unique")
    symbols = [item[2].symbol for item in declared]
    if len(symbols) != len(set(symbols)):
        raise ValueError("runtime_injector fragment symbols must be unique")
    return tuple(item[2] for item in sorted(declared, key=lambda item: item[:2]))


def _load_edits(
    directory: Path,
    owner: str,
    targets: dict[str, binary_patcher.Target],
    patches: dict[str, binary_patcher.Patch],
) -> tuple[RuntimeSymbolicEdit, ...]:
    edits: list[RuntimeSymbolicEdit] = []
    edit_ids: set[str] = set()
    patch_orders: dict[str, set[int]] = {patch_id: set() for patch_id in patches}
    for line, row in enumerate(
        _read_tsv(directory / "edits.tsv", EDIT_FIELDS), 2
    ):
        edit_id = _identifier(row["edit_id"], f"edits.tsv:{line} edit_id")
        if edit_id in edit_ids:
            raise ValueError(f"edits.tsv:{line}: duplicate edit {edit_id}")
        edit_ids.add(edit_id)
        patch_id = row["patch_id"]
        target_id = row["target_id"]
        if patch_id not in patches:
            raise ValueError(f"edits.tsv:{line}: unknown patch {patch_id!r}")
        if target_id not in targets:
            raise ValueError(f"edits.tsv:{line}: unknown target {target_id!r}")
        order = _integer(row["order"], f"edits.tsv:{line} order", minimum=1)
        if order in patch_orders[patch_id]:
            raise ValueError(
                f"edits.tsv:{line}: duplicate order {order} in {patch_id}"
            )
        patch_orders[patch_id].add(order)
        expected = _hex(row["expected_hex"], f"edits.tsv:{line} expected_hex")
        template = _hex(
            row["replacement_hex"],
            f"edits.tsv:{line} replacement_hex",
            allow_empty=True,
        )
        encoding = row["encoding"]
        if encoding not in RELOCATION_KINDS:
            raise ValueError(f"edits.tsv:{line}: invalid encoding {encoding!r}")
        edits.append(
            RuntimeSymbolicEdit(
                edit_id=edit_id,
                patch_id=patch_id,
                order=order,
                target_id=target_id,
                symbolic_patch=SymbolicPatch(
                    owner=owner,
                    path=targets[target_id].path.as_posix(),
                    offset=_integer(row["offset"], f"edits.tsv:{line} offset"),
                    expected=expected,
                    symbol=_identifier(
                        row["symbol"], f"edits.tsv:{line} symbol"
                    ),
                    encoding=encoding,
                    mapping_id=edit_id,
                    kind=patches[patch_id].group_id,
                    reason=row["reason"],
                    addend=_integer(
                        row["addend"],
                        f"edits.tsv:{line} addend",
                        minimum=-0x80000000,
                    ),
                    replacement_template=template,
                    relocation_offset=_integer(
                        row["relocation_offset"],
                        f"edits.tsv:{line} relocation_offset",
                    ),
                ),
            )
        )
    missing = sorted(
        patch_id for patch_id, orders in patch_orders.items() if not orders
    )
    if missing:
        raise ValueError(
            "runtime-injector patches without symbolic edits: " + ", ".join(missing)
        )
    return tuple(
        sorted(edits, key=lambda item: (item.patch_id, item.order, item.edit_id))
    )


def load_package(directory: Path, *, owner: str) -> RuntimeInjectionPackage:
    directory = directory.resolve()
    if not directory.is_dir():
        raise FileNotFoundError(directory)
    _identifier(owner, "runtime-injector owner")
    missing = [name for name in CONTROL_FILES if not (directory / name).is_file()]
    if missing:
        raise FileNotFoundError(
            f"runtime_injector is missing canonical inputs: {', '.join(missing)}"
        )
    targets = _load_targets(directory)
    groups = _load_groups(directory)
    patches = _load_patches(directory, groups)
    fragments = _load_fragments(directory, owner)
    edits = _load_edits(directory, owner, targets, patches)
    return RuntimeInjectionPackage(
        directory=directory,
        owner=owner,
        targets=targets,
        groups=groups,
        patches=patches,
        fragments=fragments,
        edits=edits,
    )


def build_binary_package(
    package: RuntimeInjectionPackage,
    resolved_patches: tuple[ResolvedPatch, ...],
) -> binary_patcher.Package:
    resolved_by_id = {patch.mapping_id: patch for patch in resolved_patches}
    if len(resolved_by_id) != len(resolved_patches):
        raise ValueError(
            "resolved runtime-injector patches contain duplicate mapping IDs"
        )
    active_edits = package.active_edits
    expected_ids = {edit.edit_id for edit in active_edits}
    if set(resolved_by_id) != expected_ids:
        raise ValueError(
            "resolved runtime-injector patch set differs from its declarations; "
            f"missing={sorted(expected_ids - resolved_by_id.keys())}, "
            f"extra={sorted(resolved_by_id.keys() - expected_ids)}"
        )
    edits: list[binary_patcher.Edit] = []
    for declaration in active_edits:
        resolved = resolved_by_id[declaration.edit_id]
        target = package.targets[declaration.target_id]
        if resolved.owner != package.owner or resolved.path != target.path.as_posix():
            raise ValueError(
                f"{declaration.edit_id}: resolved owner or target differs"
            )
        edits.append(
            binary_patcher.Edit(
                edit_id=declaration.edit_id,
                patch_id=declaration.patch_id,
                order=declaration.order,
                destination_target_id=declaration.target_id,
                destination_offset=resolved.offset,
                operation="replace",
                length=len(resolved.expected),
                expected_hex=resolved.expected.hex().upper(),
                expected_sha256="",
                replacement_hex=resolved.replacement.hex().upper(),
                source_target_id="",
                source_offset=None,
                source_expected_hex="",
                source_expected_sha256="",
                blob_path=None,
                blob_offset=None,
                blob_sha256="",
                fill_hex="",
                reason=resolved.reason,
            )
        )
    return binary_patcher.Package(
        directory=package.directory,
        package_id=package.owner,
        targets=package.targets,
        groups=package.groups,
        patches=package.patches,
        edits=edits,
    )
