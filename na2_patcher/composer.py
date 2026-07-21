from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from .image_assembler.iso9660 import Iso9660, normalize_iso_path
from .image_assembler.operations import (
    AssemblyPlan,
    FileInsertion,
    FileRename,
    FileReplacement,
    IsoFileRef,
    IsoRangeRef,
)
from .profile import ProfileImage, ProfileModule


TRANSLATION_IMPORT_ARTIFACT = "translation_imports"


@dataclass(frozen=True)
class ModuleArtifactContract:
    provides: tuple[str, ...] = ()
    requires: tuple[str, ...] = ()
    consumes_if_available: tuple[str, ...] = ()
    require_consumers: tuple[str, ...] = ()


MODULE_ARTIFACT_CONTRACTS = {
    "translation_importer": ModuleArtifactContract(
        provides=(TRANSLATION_IMPORT_ARTIFACT,),
        require_consumers=(TRANSLATION_IMPORT_ARTIFACT,),
    ),
    "string_patcher": ModuleArtifactContract(
        consumes_if_available=(TRANSLATION_IMPORT_ARTIFACT,),
    ),
    "texture_patcher": ModuleArtifactContract(),
    "binary_patcher": ModuleArtifactContract(),
    "external_translation": ModuleArtifactContract(),
}


@dataclass(frozen=True)
class CompositionResult:
    plan: AssemblyPlan
    image_edits: tuple[dict[str, object], ...]


def resolve_module_order(
    modules: Sequence[ProfileModule],
) -> tuple[ProfileModule, ...]:
    """Resolve declared module-artifact dependencies with stable peer ordering."""
    by_feature: dict[str, list[ProfileModule]] = {}
    for module in modules:
        if module.module not in MODULE_ARTIFACT_CONTRACTS:
            raise ValueError(f"No artifact contract for module type: {module.module}")
        by_feature.setdefault(module.feature_id, []).append(module)

    edges: dict[str, set[str]] = {module.module_id: set() for module in modules}
    indegree = {module.module_id: 0 for module in modules}
    by_id = {module.module_id: module for module in modules}
    for feature_id, feature_modules in by_feature.items():
        providers: dict[str, ProfileModule] = {}
        consumers: dict[str, list[ProfileModule]] = {}
        for module in feature_modules:
            contract = MODULE_ARTIFACT_CONTRACTS[module.module]
            for artifact in contract.provides:
                previous = providers.get(artifact)
                if previous is not None:
                    raise ValueError(
                        f"Feature {feature_id}: ambiguous providers for {artifact}: "
                        f"{previous.module_id}, {module.module_id}"
                    )
                providers[artifact] = module
            for artifact in contract.requires + contract.consumes_if_available:
                consumers.setdefault(artifact, []).append(module)

        for module in feature_modules:
            contract = MODULE_ARTIFACT_CONTRACTS[module.module]
            for artifact in contract.requires:
                if artifact not in providers:
                    raise ValueError(
                        f"Feature {feature_id}: {module.module_id} requires missing "
                        f"artifact {artifact}"
                    )
            for artifact in contract.require_consumers:
                if not consumers.get(artifact):
                    raise ValueError(
                        f"Feature {feature_id}: {module.module} provides {artifact} "
                        "but no string_patcher consumes it"
                    )

        for artifact, provider in providers.items():
            for consumer in consumers.get(artifact, ()):
                if consumer.module_id == provider.module_id:
                    continue
                edges[provider.module_id].add(consumer.module_id)
                indegree[consumer.module_id] += 1

    order_index = {module.module_id: index for index, module in enumerate(modules)}
    ready = sorted(
        (module_id for module_id, degree in indegree.items() if degree == 0),
        key=order_index.__getitem__,
    )
    resolved: list[ProfileModule] = []
    while ready:
        module_id = ready.pop(0)
        resolved.append(by_id[module_id])
        for dependent in sorted(edges[module_id], key=order_index.__getitem__):
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                ready.append(dependent)
                ready.sort(key=order_index.__getitem__)
    if len(resolved) != len(modules):
        unresolved = sorted(module_id for module_id, degree in indegree.items() if degree)
        raise ValueError(f"Module artifact dependency cycle: {', '.join(unresolved)}")
    return tuple(resolved)


def _verify_source_hash(data: bytes, expected: str | None, label: str) -> None:
    if expected is None:
        return
    normalized = expected.upper()
    if len(normalized) != 64 or any(char not in "0123456789ABCDEF" for char in normalized):
        raise ValueError(f"{label}: expected SHA-256 must be 64 hex digits")
    actual = hashlib.sha256(data).hexdigest().upper()
    if actual != normalized:
        raise RuntimeError(f"{label}: SHA-256 {actual} does not match {normalized}")


def resolve_source_ref(
    reference: IsoFileRef | IsoRangeRef,
    roots: Mapping[str, Path],
) -> bytes:
    """Resolve a whole file or byte range from an extraction or source ISO."""
    root = roots.get(reference.root_id)
    if root is None:
        raise KeyError(f"Unknown source root: {reference.root_id}")
    path = normalize_iso_path(reference.path)
    if root.is_dir():
        candidate = (root / Path(path)).resolve()
        try:
            candidate.relative_to(root.resolve())
        except ValueError as exc:
            raise ValueError(f"Source reference escapes root: {path}") from exc
        if not candidate.is_file():
            raise FileNotFoundError(candidate)
        data = candidate.read_bytes()
    elif root.is_file():
        iso = Iso9660(root)
        record = iso.by_path.get(path)
        if record is None or record.is_dir:
            raise FileNotFoundError(f"{root}: {path}")
        data = iso.read_file(record)
    else:
        raise FileNotFoundError(root)

    if isinstance(reference, IsoRangeRef):
        if reference.offset < 0 or reference.length <= 0:
            raise ValueError("ISO range references require a non-negative offset and length")
        end = reference.offset + reference.length
        if end > len(data):
            raise ValueError(f"Source range exceeds {path}: 0x{end:X} > 0x{len(data):X}")
        data = data[reference.offset:end]
    _verify_source_hash(data, reference.expected_sha256, f"{reference.root_id}:{path}")
    return data


def compose_assembly_plan(
    *,
    source: Iso9660,
    image: ProfileImage,
    payloads: Mapping[str, bytes | bytearray],
    owners: Mapping[str, str],
    insertions: Mapping[str, bytes],
    insertion_owners: Mapping[str, str],
) -> CompositionResult:
    """Close composed module payloads plus profile image identity into one plan."""
    composed_payloads = {
        normalize_iso_path(path): bytearray(data) for path, data in payloads.items()
    }
    system_path = normalize_iso_path(image.system_cnf_path)
    system_record = source.by_path.get(system_path)
    if system_record is None or system_record.is_dir:
        raise RuntimeError(f"Profile image requires source file: {system_path}")
    system_data = composed_payloads.get(
        system_path,
        bytearray(source.read_file(system_record)),
    )
    source_boot = image.source_boot_path.encode("ascii")
    output_boot = image.output_boot_path.encode("ascii")
    if bytes(system_data).count(source_boot) != 1:
        raise RuntimeError(
            f"{system_path} must contain {image.source_boot_path} exactly once"
        )
    offset = bytes(system_data).index(source_boot)
    system_data[offset:offset + len(source_boot)] = output_boot
    composed_payloads[system_path] = system_data

    reason = "Apply the profile's declared output boot identity"
    image_edit = {
        "target": system_path,
        "offset": f"0x{offset:X}",
        "length": len(source_boot),
        "original_hex": source_boot.hex().upper(),
        "new_hex": output_boot.hex().upper(),
        "reason": reason,
        "owner": "profile.image",
    }
    replacements = tuple(
        FileReplacement(
            path=path,
            expected=source.read_file(source.by_path[path]),
            replacement=bytes(composed_payloads[path]),
            owner=owners.get(path, "profile.image"),
            reason=(
                reason
                if path == system_path and path not in payloads
                else "Apply the final composed module payload"
            ),
        )
        for path in sorted(composed_payloads)
    )
    insertion_operations = tuple(
        FileInsertion(
            path=normalize_iso_path(path),
            payload=bytes(payload),
            owner=insertion_owners[path],
            reason="Insert a module-declared image file",
        )
        for path, payload in sorted(insertions.items())
    )
    rename = FileRename(
        source_path=image.source_boot_path,
        replacement_path=image.output_boot_path,
        owner="profile.image",
        reason=reason,
    )
    return CompositionResult(
        plan=AssemblyPlan(replacements, insertion_operations, (rename,)),
        image_edits=(image_edit,),
    )
