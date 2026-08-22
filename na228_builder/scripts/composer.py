from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from ..image_assembler.iso9660 import Iso9660, normalize_iso_path
from ..image_assembler.operations import (
    AssemblyPlan,
    FileInsertion,
    FileRename,
    FileReplacement,
)
from .configuration import SOURCE_BOOT_PATH, SYSTEM_CNF_PATH
from ..payload_builder.operations import (
    ResidentPayloadBuild,
    ResolvedPatch,
    SymbolicPatch,
    encode_symbol_reference,
)


@dataclass(frozen=True)
class CompositionResult:
    plan: AssemblyPlan
    identity_edits: tuple[dict[str, object], ...]


def resolve_symbolic_patches(
    build: ResidentPayloadBuild,
    patches: Sequence[SymbolicPatch],
) -> tuple[ResolvedPatch, ...]:
    """Materialize module-declared game-file writes after payload linking."""
    result: list[ResolvedPatch] = []
    for patch in patches:
        symbol = build.symbols.get(patch.symbol)
        if symbol is None:
            raise ValueError(
                f"{patch.mapping_id}: unknown resident-payload symbol {patch.symbol!r}"
            )
        replacement = encode_symbol_reference(
            patch.encoding, symbol.runtime_address + patch.addend
        )
        if patch.replacement_template:
            if (
                not patch.expected
                or len(patch.expected) != len(patch.replacement_template)
                or patch.relocation_offset < 0
                or patch.relocation_offset + len(replacement)
                > len(patch.replacement_template)
            ):
                raise ValueError(
                    f"{patch.mapping_id}: symbolic patch template or guard width "
                    "is invalid"
                )
            materialized = bytearray(patch.replacement_template)
            start = patch.relocation_offset
            materialized[start:start + len(replacement)] = replacement
            replacement = bytes(materialized)
        elif (
            patch.relocation_offset != 0
            or not patch.expected
            or len(patch.expected) != len(replacement)
        ):
            raise ValueError(
                f"{patch.mapping_id}: symbolic patch width differs from its guard"
            )
        result.append(
            ResolvedPatch(
                owner=patch.owner,
                path=patch.path,
                offset=patch.offset,
                expected=patch.expected,
                replacement=replacement,
                mapping_id=patch.mapping_id,
                kind=patch.kind,
                reason=patch.reason,
            )
        )
    return tuple(
        sorted(result, key=lambda item: (item.owner, item.path, item.offset, item.mapping_id))
    )


def compose_assembly_plan(
    *,
    source: Iso9660,
    output_boot_path: str,
    payloads: Mapping[str, bytes | bytearray],
    owners: Mapping[str, str],
    insertions: Mapping[str, bytes],
    insertion_owners: Mapping[str, str],
) -> CompositionResult:
    """Close composed module payloads plus the product output identity."""
    composed_payloads = {
        normalize_iso_path(path): bytearray(data) for path, data in payloads.items()
    }
    identity_edits: list[dict[str, object]] = []
    system_path = SYSTEM_CNF_PATH
    system_record = source.by_path.get(system_path)
    if system_record is None or system_record.is_dir:
        raise RuntimeError(f"Product composition requires source file: {system_path}")
    system_data = composed_payloads.get(
        system_path,
        bytearray(source.read_file(system_record)),
    )
    source_boot = SOURCE_BOOT_PATH.encode("ascii")
    output_boot = output_boot_path.encode("ascii")
    if len(source_boot) != len(output_boot):
        raise ValueError("Output boot path must preserve the source boot-path length")
    if bytes(system_data).count(source_boot) != 1:
        raise RuntimeError(
            f"{system_path} must contain {SOURCE_BOOT_PATH} exactly once"
        )
    offset = bytes(system_data).index(source_boot)
    system_data[offset:offset + len(source_boot)] = output_boot
    composed_payloads[system_path] = system_data

    boot_reason = "Apply the product's declared output boot path"
    identity_edits.append({
        "target": system_path,
        "offset": f"0x{offset:X}",
        "length": len(source_boot),
        "original_hex": source_boot.hex().upper(),
        "new_hex": output_boot.hex().upper(),
        "reason": boot_reason,
        "owner": "settings.output_boot_path",
    })

    replacements = tuple(
        FileReplacement(
            path=path,
            expected=source.read_file(source.by_path[path]),
            replacement=bytes(composed_payloads[path]),
            owner=owners.get(path, "settings.output_boot_path"),
            reason=(
                boot_reason
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
        source_path=SOURCE_BOOT_PATH,
        replacement_path=output_boot_path,
        owner="settings.output_boot_path",
        reason=boot_reason,
    )
    return CompositionResult(
        plan=AssemblyPlan(replacements, insertion_operations, (rename,)),
        identity_edits=tuple(identity_edits),
    )
