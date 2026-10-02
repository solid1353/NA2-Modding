from __future__ import annotations

import struct
from pathlib import Path, PurePosixPath

from ...common import sha256_hex
from ..binary_patcher import engine as binary_patcher
from .builder import ResidentPayloadConfig
from .operations import ResidentPayloadBuild, ResolvedPatch, mips_jump


def _encode_i(opcode: int, rs: int, rt: int, immediate: int) -> int:
    if not -0x8000 <= immediate <= 0xFFFF:
        raise ValueError(f"MIPS immediate is out of range: 0x{immediate:X}")
    return (opcode << 26) | (rs << 21) | (rt << 16) | (immediate & 0xFFFF)


def _addiu(rt: int, rs: int, immediate: int) -> int:
    return _encode_i(0x09, rs, rt, immediate)


def _lui(rt: int, immediate: int) -> int:
    return _encode_i(0x0F, 0, rt, immediate)


def _ori(rt: int, rs: int, immediate: int) -> int:
    return _encode_i(0x0D, rs, rt, immediate)


def _sw(rt: int, base: int, offset: int) -> int:
    return _encode_i(0x2B, base, rt, offset)


def _sd(rt: int, base: int, offset: int) -> int:
    return _encode_i(0x3F, base, rt, offset)


def _ld(rt: int, base: int, offset: int) -> int:
    return _encode_i(0x37, base, rt, offset)


def _jal(address: int) -> int:
    return mips_jump(address, link=True)


def _words(*values: int) -> bytes:
    return struct.pack("<" + "I" * len(values), *values)


def _load_program_header(address: int, memory_size: int, flags: int, alignment: int) -> bytes:
    """ELF PT_LOAD header at the boot ELF's final file offset with no file data."""
    return struct.pack(
        "<8I", 1, 0x507480, address, address, 0, memory_size, flags, alignment
    )


def build_integration_patches(
    build: ResidentPayloadBuild,
    *,
    config: ResidentPayloadConfig,
    boot_path: str,
    clean_boot: bytes,
) -> tuple[ResolvedPatch, ...]:
    patches: list[ResolvedPatch] = []

    def patch(
        offset: int,
        expected: bytes,
        replacement: bytes,
        mapping_id: str,
        kind: str,
        reason: str,
    ) -> None:
        patches.append(
            ResolvedPatch(
                owner="payload_builder",
                path=boot_path,
                offset=offset,
                expected=expected,
                replacement=replacement,
                mapping_id=mapping_id,
                kind=kind,
                reason=reason,
            )
        )

    patch(
        0x2C,
        struct.pack("<H", 5),
        struct.pack("<H", 6),
        "ELF-RP-PHNUM",
        "memory_layout",
        "Declare the shared resident-payload reservation program header.",
    )
    patch(
        0xB4,
        _load_program_header(config.old_memory_boundary, 0, 6, 0x10) + b"\0" * 32,
        _load_program_header(
            build.load_base, config.reservation_end - build.load_base, 7, 0x80
        )
        + _load_program_header(config.reservation_end, 0, 6, 0x10),
        "ELF-RP-PHEADERS",
        "memory_layout",
        "Reserve the stable resident-payload envelope.",
    )

    high = (config.reservation_end + 0x8000) >> 16
    low = config.reservation_end & 0xFFFF
    for offset, expected_word, replacement_word, mapping_id in (
        (0x220, 0x3C03008E, _lui(3, high), "ELF-RP-BOUNDARY-1H"),
        (0x228, 0x2463D080, _addiu(3, 3, low), "ELF-RP-BOUNDARY-1L"),
        (0x2D0, 0x3C04008E, _lui(4, high), "ELF-RP-BOUNDARY-2H"),
        (0x2D8, 0x2484D080, _addiu(4, 4, low), "ELF-RP-BOUNDARY-2L"),
        (0x1885C, 0x3C17008E, _lui(23, high), "ELF-RP-BOUNDARY-3H"),
        (0x18860, 0x26F7D080, _addiu(23, 23, low), "ELF-RP-BOUNDARY-3L"),
        (0x4D6908, 0x3C03008E, _lui(3, high), "ELF-RP-BOUNDARY-4H"),
        (0x4D690C, 0x2463D080, _addiu(3, 3, low), "ELF-RP-BOUNDARY-4L"),
    ):
        patch(
            offset,
            _words(expected_word),
            _words(replacement_word),
            mapping_id,
            "memory_layout",
            "Move a hardcoded resident-memory boundary to the stable reservation end.",
        )
    for offset, mapping_id, reason in (
        (0x2F79F4, "ELF-RP-BOUNDARY-LITERAL", "Move the literal final memory-boundary pointer."),
        (0x50763C, "ELF-RP-SECTION-END", "Move the zero-size final section marker."),
    ):
        patch(
            offset,
            _words(config.old_memory_boundary),
            _words(config.reservation_end),
            mapping_id,
            "memory_layout",
            reason,
        )

    patch(
        config.destination_table_file_offset + 8,
        b"\0" * 4,
        _words(build.load_base),
        "ELF-RP-LOAD-SLOT",
        "loader",
        "Assign generic PRG loader slot 2 to the shared resident payload.",
    )

    # The generic loader prefixes cdrom0:\PRG\. Swap its PRG\ for the payload's
    # directory while it loads, and restore it before the payload entrypoint runs.
    directory_offset = config.loader_directory_address - (
        config.cave_runtime_address - config.cave_file_offset
    )
    original_directory = clean_boot[directory_offset:directory_offset + 4]
    if original_directory != b"PRG\\":
        raise ValueError(
            f"Loader directory text is not PRG\\ at 0x{config.loader_directory_address:X}"
        )
    payload_directory = PurePosixPath(build.output_path).parent.name.encode("ascii") + b"\\"
    directory_high = (config.loader_directory_address + 0x8000) >> 16
    directory_low = config.loader_directory_address - (directory_high << 16)

    def directory_word(text: bytes) -> tuple[int, int]:
        value = int.from_bytes(text, "little")
        return value >> 16, value & 0xFFFF

    payload_high, payload_low = directory_word(payload_directory)
    original_high, original_low = directory_word(original_directory)
    cave_string_address = config.cave_runtime_address + 21 * 4
    cave_code = _words(
        _addiu(29, 29, -0x20),
        _sd(31, 29, 0x10),
        _sd(4, 29, 0),
        _lui(8, directory_high),
        _lui(9, payload_high),
        _ori(9, 9, payload_low),
        _addiu(4, 0, 2),
        _lui(5, cave_string_address >> 16),
        _addiu(5, 5, cave_string_address & 0xFFFF),
        _jal(config.loader_function),
        _sw(9, 8, directory_low),
        _lui(8, directory_high),
        _lui(9, original_high),
        _ori(9, 9, original_low),
        _jal(build.entrypoint),
        _sw(9, 8, directory_low),
        _jal(config.original_constructor_function),
        _ld(4, 29, 0),
        _ld(31, 29, 0x10),
        0x03E00008,
        _addiu(29, 29, 0x20),
    )
    cave_payload = cave_code + Path(build.output_path).name.encode("ascii") + b"\0"
    patch(
        config.cave_file_offset,
        b"\0" * len(cave_payload),
        cave_payload,
        "ELF-RP-BOOTSTRAP",
        "loader",
        f"Load {build.output_path} through the PRG loader, invoke the shared "
        "resident entrypoint, then preserve the original constructor call.",
    )
    patch(
        config.hook_file_offset,
        _words(_jal(config.original_constructor_function)),
        _words(_jal(config.cave_runtime_address)),
        "ELF-RP-HOOK",
        "loader",
        "Redirect the constructor through the shared resident-payload bootstrap.",
    )
    return tuple(sorted(patches, key=lambda item: (item.path, item.offset, item.mapping_id)))


def build_integration_package(
    build: ResidentPayloadBuild,
    *,
    config: ResidentPayloadConfig,
    boot_path: str,
    clean_boot: bytes,
) -> binary_patcher.Package:
    patches = build_integration_patches(
        build, config=config, boot_path=boot_path, clean_boot=clean_boot
    )
    target_id = "resident_boot_elf"
    target = binary_patcher.Target(
        target_id=target_id,
        root_id="na2",
        path=PurePosixPath(boot_path),
        expected_size=len(clean_boot),
        expected_sha256=sha256_hex(clean_boot),
    )
    return binary_patcher.Package(
        directory=Path(__file__).resolve().parent,
        package_id="payload_builder",
        targets={target_id: target},
        patches={
            patch.mapping_id: binary_patcher.Patch(
                patch_id=patch.mapping_id,
                group_id=patch.kind,
                evidence_id=patch.mapping_id,
            )
            for patch in patches
        },
        edits=[
            binary_patcher.Edit(
                edit_id=f"PB-E{index:03d}",
                patch_id=patch.mapping_id,
                order=10,
                destination_target_id=target_id,
                destination_offset=patch.offset,
                operation="replace",
                length=len(patch.expected),
                expected_hex=patch.expected.hex().upper(),
                replacement_hex=patch.replacement.hex().upper(),
                reason=patch.reason,
            )
            for index, patch in enumerate(patches, 1)
        ],
    )
