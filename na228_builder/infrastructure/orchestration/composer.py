from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from ..common import sha256_hex
from ..modules.image_assembler.iso9660 import Iso9660, normalize_iso_path
from ..modules.image_assembler.operations import (
    AssemblyPlan,
    FileInsertion,
    FileRename,
    FileReplacement,
)
from .configuration import SOURCE_BOOT_PATH, SYSTEM_CNF_PATH
from ..modules.payload_builder.operations import (
    ResidentPayloadBuild,
    ResolvedPatch,
    SymbolicPatch,
    encode_symbol_reference,
)


# Files the build adds live in this disc directory, with a manifest of changed source files.
MOD_DIRECTORY = "228"
MANIFEST_PATH = f"{MOD_DIRECTORY}/MANIFEST.TSV"


def changed_source_manifest(
    replacements: Sequence[FileReplacement],
    renames: Sequence[FileRename],
) -> bytes:
    """Tab-separated list of changed source files with their source and output hashes."""
    output_paths = {rename.source_path: rename.replacement_path for rename in renames}
    lines = ["source_path\toutput_path\tsource_sha256\toutput_sha256"]
    for replacement in sorted(replacements, key=lambda item: item.path):
        lines.append("\t".join((
            replacement.path,
            output_paths.get(replacement.path, replacement.path),
            sha256_hex(replacement.expected),
            sha256_hex(replacement.replacement),
        )))
    return ("\r\n".join(lines) + "\r\n").encode("ascii")


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
    identity_owner: str,
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
    renames: tuple[FileRename, ...] = ()
    boot_reason = "Apply the selected disc identity"
    if output_boot_path != SOURCE_BOOT_PATH:
        system_record = source.by_path.get(SYSTEM_CNF_PATH)
        if system_record is None or system_record.is_dir:
            raise RuntimeError(f"Disc identity patch requires source file: {SYSTEM_CNF_PATH}")
        system_data = composed_payloads.get(
            SYSTEM_CNF_PATH,
            bytearray(source.read_file(system_record)),
        )
        source_boot = SOURCE_BOOT_PATH.encode("ascii")
        output_boot = output_boot_path.encode("ascii")
        if len(source_boot) != len(output_boot):
            raise ValueError("Output boot path must preserve the source boot-path length")
        if bytes(system_data).count(source_boot) != 1:
            raise RuntimeError(
                f"{SYSTEM_CNF_PATH} must contain {SOURCE_BOOT_PATH} exactly once"
            )
        offset = bytes(system_data).index(source_boot)
        system_data[offset:offset + len(source_boot)] = output_boot
        composed_payloads[SYSTEM_CNF_PATH] = system_data
        identity_edits.append({
            "target": SYSTEM_CNF_PATH,
            "offset": f"0x{offset:X}",
            "length": len(source_boot),
            "original_hex": source_boot.hex().upper(),
            "new_hex": output_boot.hex().upper(),
            "reason": boot_reason,
            "owner": identity_owner,
        })
        renames = (FileRename(
            source_path=SOURCE_BOOT_PATH,
            replacement_path=output_boot_path,
            owner=identity_owner,
            reason=boot_reason,
        ),)

    replacements = tuple(
        FileReplacement(
            path=path,
            expected=source.read_file(source.by_path[path]),
            replacement=bytes(composed_payloads[path]),
            owner=owners.get(path, identity_owner),
            reason=(
                boot_reason
                if path == SYSTEM_CNF_PATH and path not in payloads
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
    ) + (
        FileInsertion(
            path=MANIFEST_PATH,
            payload=changed_source_manifest(replacements, renames),
            owner=identity_owner,
            reason="List the changed source files",
        ),
    )
    return CompositionResult(
        plan=AssemblyPlan(replacements, insertion_operations, renames),
        identity_edits=tuple(identity_edits),
    )
