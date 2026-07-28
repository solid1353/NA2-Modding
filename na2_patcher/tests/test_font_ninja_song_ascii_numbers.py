from __future__ import annotations

import unittest
from pathlib import Path

from na2_patcher.composer import resolve_symbolic_patches
from na2_patcher.modules.runtime_injector import engine
from na2_patcher.payload_builder import mips
from na2_patcher.payload_builder.builder import build_resident_payload
from scripts.localization import generate_font_renderer
from scripts.research.localization import (
    generate_ninja_song_ascii_numbers,
)


class NinjaSongAsciiNumbersTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repository = Path(__file__).resolve().parents[2]
        cls.declaration = engine.load_package(
            cls.repository
            / "na2_patcher"
            / "features"
            / "localization"
            / "runtime_injector",
            owner="localization.runtime_injector",
        )

    def test_canonical_patch_matches_generated_five_call_redirects(self) -> None:
        patch_id = generate_ninja_song_ascii_numbers.PATCH_ID
        patch = self.declaration.patches[patch_id]
        self.assertTrue(patch.enabled)
        self.assertEqual(patch.group_id, "battle_ui")
        self.assertEqual(patch.status, "runtime_proven")
        self.assertEqual(patch.confidence, "high")

        canonical = [
            edit
            for edit in self.declaration.active_edits
            if edit.patch_id == patch_id
        ]
        generated = generate_ninja_song_ascii_numbers.generated_edits()
        self.assertEqual(len(canonical), 5)
        self.assertEqual(len(canonical), len(generated))
        for edit, expected in zip(canonical, generated, strict=True):
            self.assertEqual(edit.edit_id, expected["edit_id"])
            self.assertEqual(edit.order, expected["order"])
            self.assertEqual(edit.target_id, expected["target_id"])
            symbolic = edit.symbolic_patch
            self.assertEqual(symbolic.offset, expected["offset"])
            self.assertEqual(
                symbolic.expected.hex().upper(),
                expected["expected_hex"],
            )
            self.assertEqual(
                symbolic.replacement_template.hex().upper(),
                expected["replacement_hex"],
            )
            self.assertEqual(symbolic.relocation_offset, 0)
            self.assertEqual(symbolic.symbol, expected["symbol"])
            self.assertEqual(symbolic.encoding, "jal26")
            self.assertEqual(symbolic.addend, 0)

        build = build_resident_payload(self.declaration.fragments)
        resolved = resolve_symbolic_patches(
            build, self.declaration.symbolic_patches
        )
        package = engine.build_binary_package(self.declaration, resolved)
        canonical_edits = {
            edit.edit_id: edit
            for edit in package.edits
            if edit.patch_id == patch_id
        }
        self.assertEqual(set(canonical_edits), {
            row["edit_id"] for row in generated
        })
        helper = build.symbols[
            generate_ninja_song_ascii_numbers.SYMBOL
        ]
        for edit in canonical_edits.values():
            hook = bytes.fromhex(edit.replacement_hex)
            self.assertEqual(len(hook), 4)
            jump = int.from_bytes(hook, "little")
            self.assertEqual(jump >> 26, 0x03)
            self.assertEqual(
                (jump & 0x03FFFFFF) << 2,
                helper.runtime_address,
            )

    def test_clean_btl_contexts_and_multiplication_mapping_are_exact(self) -> None:
        self.assertTrue(
            generate_ninja_song_ascii_numbers.verify_source().is_file()
        )
        self.assertTrue(
            generate_ninja_song_ascii_numbers
            .verify_multiplication_mapping()
            .is_file()
        )

    def test_nun5_padding_modes_are_preserved(self) -> None:
        format_number = (
            generate_ninja_song_ascii_numbers.format_ascii_number
        )
        self.assertEqual(format_number(1, 3, 0), "  1")
        self.assertEqual(format_number(100, 3, 0), "100")
        self.assertEqual(format_number(300, 5, 0), "  300")
        self.assertEqual(format_number(7, 4, 1), "7")
        self.assertEqual(format_number(1200, 4, 0), "1200")
        self.assertEqual(format_number(7, 4, 2), "0007")
        with self.assertRaisesRegex(ValueError, "unsupported"):
            format_number(7, 4, 3)

    def test_accepted_c_helper_keeps_public_symbol_and_native_abi(self) -> None:
        first = generate_font_renderer.build_numeric_c_core()
        generate_font_renderer.build_numeric_c_core.cache_clear()
        second = generate_font_renderer.build_numeric_c_core()
        self.assertEqual(first, second)

        fragment = next(
            item
            for item in first
            if item.symbol == generate_ninja_song_ascii_numbers.SYMBOL
        )
        self.assertEqual(
            fragment.symbol,
            generate_ninja_song_ascii_numbers.SYMBOL,
        )
        self.assertEqual(len(fragment.relocations), 1)
        relocation = fragment.relocations[0]
        self.assertEqual(relocation.kind, "jal26")
        self.assertEqual(
            relocation.symbol,
            generate_font_renderer.NINJA_SONG_FORMAT_DECIMAL,
        )
        self.assertEqual(relocation.addend, 0)

        words = [
            int.from_bytes(fragment.payload[offset:offset + 4], "little")
            for offset in range(0, len(fragment.payload), 4)
        ]
        self.assertTrue(
            any(
                word >> 26 == 0
                and (word >> 21) & 0x1F == 8
                and (word >> 16) & 0x1F == 0
                and word & 0x3F in {0x21, 0x2D}
                for word in words
            ),
            "compiled helper must consume the fifth EE EABI argument from t0",
        )

        bridge = generate_font_renderer.build_ninja_song_format_decimal()
        self.assertEqual(
            bridge.symbol,
            generate_font_renderer.NINJA_SONG_FORMAT_DECIMAL,
        )
        self.assertEqual(bridge.relocations, ())
        bridge_words = [
            int.from_bytes(bridge.payload[offset:offset + 4], "little")
            for offset in range(0, len(bridge.payload), 4)
        ]
        self.assertEqual(
            bridge_words,
            [
                mips.r_type(5, 0, 6, 0x21),
                mips.i_type(0x0F, 0, 5, 0x60),
                mips.i_type(0x0D, 5, 5, 0x42D3),
                mips.jump(0x02, generate_font_renderer.SPRINTF),
                0,
            ],
        )

        numeric_fragments = generate_font_renderer.numeric_fragments()
        self.assertIn(fragment, numeric_fragments)
        self.assertIn(bridge, numeric_fragments)
        rows = {
            row.symbol: row
            for row in self.declaration.fragments
            if row.symbol in {fragment.symbol, bridge.symbol}
        }
        self.assertEqual(set(rows), {fragment.symbol, bridge.symbol})
        self.assertEqual(rows[fragment.symbol].payload, fragment.payload)
        self.assertEqual(rows[bridge.symbol].payload, bridge.payload)
        self.assertEqual(
            [
                (
                    item.offset,
                    item.kind,
                    item.symbol,
                    item.addend,
                )
                for item in rows[fragment.symbol].relocations
            ],
            [
                (
                    item.offset,
                    item.kind,
                    item.symbol,
                    item.addend,
                )
                for item in fragment.relocations
            ],
        )
        self.assertEqual(rows[fragment.symbol].kind, "code")
        self.assertEqual(rows[bridge.symbol].kind, "code")


if __name__ == "__main__":
    unittest.main()
