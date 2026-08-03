from __future__ import annotations

import dataclasses
import struct
import tempfile
import unittest
from pathlib import Path

from na228_builder.composer import resolve_symbolic_patches
from na228_builder.payload_builder.builder import build_resident_payload, load_config
from na228_builder.payload_builder.integration import build_integration_patches
from na228_builder.payload_builder.operations import (
    PayloadFragment,
    PayloadRelocation,
    SymbolicPatch,
)


class PayloadBuilderTests(unittest.TestCase):
    def test_links_fragments_deterministically_and_resolves_relocations(self) -> None:
        fragments = (
            PayloadFragment("feature.data", "shared.data", "data", 16, b"DATA"),
            PayloadFragment(
                "feature.code",
                "shared.code",
                "code",
                4,
                b"\0" * 4,
                (PayloadRelocation(0, "abs32", "shared.data"),),
            ),
        )
        first = build_resident_payload(fragments)
        second = build_resident_payload(tuple(reversed(fragments)))
        self.assertEqual(first.payload, second.payload)
        code = first.symbols["shared.code"]
        data = first.symbols["shared.data"]
        self.assertEqual(data.file_offset, 0x100)
        self.assertEqual(
            first.payload[code.file_offset:code.file_offset + 4],
            data.runtime_address.to_bytes(4, "little"),
        )

    def test_composer_resolves_external_symbolic_patch(self) -> None:
        build = build_resident_payload(
            (PayloadFragment("feature.data", "shared.text", "rodata", 4, b"Text\0"),)
        )
        patch = SymbolicPatch(
            owner="feature.data",
            path="SLPS_258.37",
            offset=0x20,
            expected=b"\0" * 4,
            symbol="shared.text",
            encoding="abs32",
            mapping_id="TEST-PTR",
            kind="redirect_pointer",
            reason="Test symbolic resolution.",
        )
        resolved = resolve_symbolic_patches(build, (patch,))[0]
        self.assertEqual(
            resolved.replacement,
            build.symbols["shared.text"].runtime_address.to_bytes(4, "little"),
        )

    def test_resolves_jump_template_without_losing_delay_slot(self) -> None:
        build = build_resident_payload(
            (PayloadFragment("feature.code", "shared.helper", "code", 4, b"\0" * 4),)
        )
        patch = SymbolicPatch(
            owner="feature.code",
            path="SLPS_258.37",
            offset=0x20,
            expected=b"\x11" * 8,
            symbol="shared.helper",
            encoding="j26",
            mapping_id="TEST-JUMP",
            kind="redirect_code",
            reason="Test a symbolic jump plus an explicit delay slot.",
            replacement_template=b"\0" * 8,
        )
        resolved = resolve_symbolic_patches(build, (patch,))[0]
        expected_jump = (
            0x08000000 | (build.symbols["shared.helper"].runtime_address >> 2)
        ).to_bytes(4, "little")
        self.assertEqual(resolved.replacement, expected_jump + b"\0" * 4)

    def test_rejects_duplicate_and_unresolved_symbols(self) -> None:
        duplicate = PayloadFragment("a", "same", "data", 4, b"a")
        with self.assertRaisesRegex(ValueError, "duplicate symbols"):
            build_resident_payload((duplicate, dataclasses.replace(duplicate, owner="b")))
        unresolved = PayloadFragment(
            "a",
            "code",
            "code",
            4,
            b"\0" * 4,
            (PayloadRelocation(0, "abs32", "missing"),),
        )
        with self.assertRaisesRegex(ValueError, "unresolved symbol"):
            build_resident_payload((unresolved,))

    def test_rejects_payload_beyond_the_proven_envelope(self) -> None:
        config = load_config()
        constrained = dataclasses.replace(
            config,
            maximum_end=config.load_base + config.minimum_data_offset + 8,
            reservation_end=config.load_base + config.minimum_data_offset + 8,
        )
        with self.assertRaisesRegex(ValueError, "reservation envelope"):
            build_resident_payload(
                (PayloadFragment("a", "large", "data", 4, b"x" * 32),),
                config=constrained,
            )

    def test_integration_boundary_is_independent_of_payload_size(self) -> None:
        config = load_config()
        small = build_resident_payload(
            (PayloadFragment("a", "small", "data", 4, b"x" * 16),),
            config=config,
        )
        large = build_resident_payload(
            (PayloadFragment("a", "large", "data", 4, b"x" * 48),),
            config=config,
        )
        self.assertNotEqual(small.memory_end, large.memory_end)

        clean = bytearray(0x507640)
        struct.pack_into("<H", clean, 0x2C, 5)
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
        clean[0xB4:0xF4] = old_final + b"\0" * 32
        for offset, word in (
            (0x220, 0x3C03008E),
            (0x228, 0x2463D080),
            (0x2D0, 0x3C04008E),
            (0x2D8, 0x2484D080),
            (0x1885C, 0x3C17008E),
            (0x18860, 0x26F7D080),
            (0x4D6908, 0x3C03008E),
            (0x4D690C, 0x2463D080),
        ):
            struct.pack_into("<I", clean, offset, word)
        struct.pack_into("<I", clean, 0x2F79F4, config.old_memory_boundary)
        struct.pack_into("<I", clean, 0x50763C, config.old_memory_boundary)
        struct.pack_into(
            "<I",
            clean,
            config.hook_file_offset,
            0x0C000000 | (config.original_constructor_function >> 2),
        )

        small_patches = build_integration_patches(
            small,
            config=config,
            boot_path="SLPS_258.37",
            clean_boot=bytes(clean),
        )
        large_patches = build_integration_patches(
            large,
            config=config,
            boot_path="SLPS_258.37",
            clean_boot=bytes(clean),
        )
        self.assertEqual(
            [(patch.mapping_id, patch.replacement) for patch in small_patches],
            [(patch.mapping_id, patch.replacement) for patch in large_patches],
        )

    def test_development_injection_range_is_reserved_before_payload(self) -> None:
        config = load_config()
        self.assertEqual(config.development_injection_base, 0x008F0000)
        self.assertEqual(config.development_injection_end, config.load_base)
        self.assertEqual(
            config.development_injection_end - config.development_injection_base,
            0x3D00,
        )

    def test_rejects_development_injection_range_outside_protected_gap(self) -> None:
        source = Path("na228_builder/payload_builder/config.tsv").read_text(
            encoding="utf-8"
        )
        invalid = source.replace(
            "development_injection_end\t0x008F3D00",
            "development_injection_end\t0x008F3D10",
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "config.tsv"
            path.write_text(invalid, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "pre-payload gap"):
                load_config(path)


if __name__ == "__main__":
    unittest.main()
