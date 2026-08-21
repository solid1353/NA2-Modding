from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ...payload_builder.operations import (
    PayloadFragment,
    ResolvedPatch,
    SymbolicPatch,
)
from ..binary_patcher import engine as binary_patcher


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
