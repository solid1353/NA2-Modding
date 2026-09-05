from __future__ import annotations

import hashlib
import struct
from pathlib import Path, PurePosixPath

from ..modules.binary_patcher import engine as binary_patcher
from .builder import ResidentPayloadConfig
from .operations import ResidentPayloadBuild, ResolvedPatch


def _encode_i(opcode: int, rs: int, rt: int, immediate: int) -> int:
    if not -0x8000 <= immediate <= 0xFFFF:
        raise ValueError(f"MIPS immediate is out of range: 0x{immediate:X}")
    return (opcode << 26) | (rs << 21) | (rt << 16) | (immediate & 0xFFFF)


def _addiu(rt: int, rs: int, immediate: int) -> int:
    return _encode_i(0x09, rs, rt, immediate)


def _lui(rt: int, immediate: int) -> int:
    return _encode_i(0x0F, 0, rt, immediate)


def _sd(rt: int, base: int, offset: int) -> int:
    return _encode_i(0x3F, base, rt, offset)


def _ld(rt: int, base: int, offset: int) -> int:
    return _encode_i(0x37, base, rt, offset)


def _jal(address: int) -> int:
    if address & 3 or not 0 <= address < 0x10000000:
        raise ValueError(f"MIPS JAL target is not encodable: 0x{address:X}")
    return 0x0C000000 | (address >> 2)


def _words(values: tuple[int, ...]) -> bytes:
    return struct.pack("<" + "I" * len(values), *values)


def _guarded_patch(
    clean: bytes,
    *,
    path: str,
    offset: int,
    expected: bytes,
    replacement: bytes,
    mapping_id: str,
    kind: str,
    reason: str,
) -> ResolvedPatch:
    if not expected or len(expected) != len(replacement):
        raise ValueError(f"{mapping_id}: resident integration changes file size")
    actual = clean[offset:offset + len(expected)]
    if actual != expected:
        raise RuntimeError(
            f"{mapping_id}: unexpected clean ELF bytes at 0x{offset:X}: "
            f"{actual.hex().upper()}"
        )
    return ResolvedPatch(
        owner="payload_builder",
        path=path,
        offset=offset,
        expected=expected,
        replacement=replacement,
        mapping_id=mapping_id,
        kind=kind,
        reason=reason,
    )


def build_integration_patches(
    build: ResidentPayloadBuild,
    *,
    config: ResidentPayloadConfig,
    boot_path: str,
    clean_boot: bytes,
) -> tuple[ResolvedPatch, ...]:
    if build.output_path != config.output_path or build.load_base != config.load_base:
        raise ValueError("Resident build does not match its integration configuration")
    if (
        build.memory_end != config.reservation_end
        or build.used_end > config.reservation_end
    ):
        raise ValueError("Resident build exceeds the configured integration envelope")
    filename = Path(build.output_path).name.encode("ascii") + b"\0"
    if len(filename) != 8:
        raise ValueError("Resident-payload loader filename must be seven ASCII bytes")

    patches: list[ResolvedPatch] = []
    patches.append(
        _guarded_patch(
            clean_boot,
            path=boot_path,
            offset=0x2C,
            expected=struct.pack("<H", 5),
            replacement=struct.pack("<H", 6),
            mapping_id="ELF-RP-PHNUM",
            kind="memory_layout",
            reason="Declare the shared resident-payload reservation program header.",
        )
    )
    old_final = struct.pack(
        "<8I",
        1,
        0x507480,
        config.old_memory_boundary,
        config.old_memory_boundary,
        0,
        0,
        6,
        0x10,
    )
    reservation = struct.pack(
        "<8I",
        1,
        0x507480,
        build.load_base,
        build.load_base,
        0,
        config.reservation_end - build.load_base,
        7,
        0x80,
    )
    new_final = struct.pack(
        "<8I",
        1,
        0x507480,
        config.reservation_end,
        config.reservation_end,
        0,
        0,
        6,
        0x10,
    )
    patches.append(
        _guarded_patch(
            clean_boot,
            path=boot_path,
            offset=0xB4,
            expected=old_final + b"\0" * 32,
            replacement=reservation + new_final,
            mapping_id="ELF-RP-PHEADERS",
            kind="memory_layout",
            reason="Reserve the stable resident-payload envelope.",
        )
    )

    high = (config.reservation_end + 0x8000) >> 16
    low = config.reservation_end & 0xFFFF
    boundary_words = (
        (0x220, 0x3C03008E, _lui(3, high), "ELF-RP-BOUNDARY-1H"),
        (0x228, 0x2463D080, _addiu(3, 3, low), "ELF-RP-BOUNDARY-1L"),
        (0x2D0, 0x3C04008E, _lui(4, high), "ELF-RP-BOUNDARY-2H"),
        (0x2D8, 0x2484D080, _addiu(4, 4, low), "ELF-RP-BOUNDARY-2L"),
        (0x1885C, 0x3C17008E, _lui(23, high), "ELF-RP-BOUNDARY-3H"),
        (0x18860, 0x26F7D080, _addiu(23, 23, low), "ELF-RP-BOUNDARY-3L"),
        (0x4D6908, 0x3C03008E, _lui(3, high), "ELF-RP-BOUNDARY-4H"),
        (0x4D690C, 0x2463D080, _addiu(3, 3, low), "ELF-RP-BOUNDARY-4L"),
    )
    for offset, expected_word, replacement_word, mapping_id in boundary_words:
        patches.append(
            _guarded_patch(
                clean_boot,
                path=boot_path,
                offset=offset,
                expected=struct.pack("<I", expected_word),
                replacement=struct.pack("<I", replacement_word),
                mapping_id=mapping_id,
                kind="memory_layout",
                reason="Move a hardcoded resident-memory boundary to the stable reservation end.",
            )
        )
    for offset, mapping_id, reason in (
        (0x2F79F4, "ELF-RP-BOUNDARY-LITERAL", "Move the literal final memory-boundary pointer."),
        (0x50763C, "ELF-RP-SECTION-END", "Move the zero-size final section marker."),
    ):
        patches.append(
            _guarded_patch(
                clean_boot,
                path=boot_path,
                offset=offset,
                expected=struct.pack("<I", config.old_memory_boundary),
                replacement=struct.pack("<I", config.reservation_end),
                mapping_id=mapping_id,
                kind="memory_layout",
                reason=reason,
            )
        )

    patches.append(
        _guarded_patch(
            clean_boot,
            path=boot_path,
            offset=config.destination_table_file_offset + 8,
            expected=b"\0" * 4,
            replacement=struct.pack("<I", build.load_base),
            mapping_id="ELF-RP-LOAD-SLOT",
            kind="loader",
            reason="Assign generic PRG loader slot 2 to the shared resident payload.",
        )
    )

    cave_string_address = config.cave_runtime_address + 17 * 4
    cave_code = _words(
        (
            _addiu(29, 29, -0x20),
            _sd(31, 29, 0x10),
            _sd(4, 29, 0),
            _addiu(4, 0, 2),
            _lui(5, cave_string_address >> 16),
            _addiu(5, 5, cave_string_address & 0xFFFF),
            _jal(config.loader_function),
            0,
            _jal(build.entrypoint),
            0,
            _ld(4, 29, 0),
            _jal(config.original_constructor_function),
            0,
            _ld(31, 29, 0x10),
            _addiu(29, 29, 0x20),
            0x03E00008,
            0,
        )
    )
    cave_payload = cave_code + filename
    patches.append(
        _guarded_patch(
            clean_boot,
            path=boot_path,
            offset=config.cave_file_offset,
            expected=b"\0" * len(cave_payload),
            replacement=cave_payload,
            mapping_id="ELF-RP-BOOTSTRAP",
            kind="loader",
            reason=(
                f"Load {filename[:-1].decode('ascii')}, invoke the shared resident "
                "entrypoint, then preserve the original constructor call."
            ),
        )
    )
    patches.append(
        _guarded_patch(
            clean_boot,
            path=boot_path,
            offset=config.hook_file_offset,
            expected=struct.pack("<I", _jal(config.original_constructor_function)),
            replacement=struct.pack("<I", _jal(config.cave_runtime_address)),
            mapping_id="ELF-RP-HOOK",
            kind="loader",
            reason="Redirect the constructor through the shared resident-payload bootstrap.",
        )
    )
    return tuple(sorted(patches, key=lambda item: (item.path, item.offset, item.mapping_id)))


def build_integration_package(
    patches: tuple[ResolvedPatch, ...],
    *,
    boot_path: str,
    clean_boot: bytes,
) -> binary_patcher.Package:
    target_id = "resident_boot_elf"
    target = binary_patcher.Target(
        target_id=target_id,
        root_id="na2",
        role="destination",
        path=PurePosixPath(boot_path),
        expected_size=len(clean_boot),
        expected_sha256=hashlib.sha256(clean_boot).hexdigest().upper(),
    )
    package_patches: dict[str, binary_patcher.Patch] = {}
    edits: list[binary_patcher.Edit] = []
    for index, patch in enumerate(patches, 1):
        group_id = patch.kind
        patch_id = patch.mapping_id
        package_patches[patch_id] = binary_patcher.Patch(
            patch_id=patch_id,
            group_id=group_id,
            evidence_id=patch.mapping_id,
        )
        edits.append(
            binary_patcher.Edit(
                edit_id=f"PB-E{index:03d}",
                patch_id=patch_id,
                order=10,
                destination_target_id=target_id,
                destination_offset=patch.offset,
                operation="replace",
                length=len(patch.expected),
                expected_hex=patch.expected.hex().upper(),
                expected_sha256="",
                replacement_hex=patch.replacement.hex().upper(),
                source_target_id="",
                source_offset=None,
                source_expected_hex="",
                source_expected_sha256="",
                blob_path=None,
                blob_offset=None,
                blob_sha256="",
                fill_hex="",
                reason=patch.reason,
            )
        )
    return binary_patcher.Package(
        directory=Path(__file__).resolve().parent,
        package_id="payload_builder",
        targets={target_id: target},
        patches=package_patches,
        edits=edits,
    )
