from __future__ import annotations

import unittest
from pathlib import Path

from na2_patcher.composer import resolve_symbolic_patches
from na2_patcher.modules.runtime_injector import engine
from na2_patcher.payload_builder.builder import build_resident_payload
from scripts.research.localization import (
    generate_font_renderer,
    generate_ninja_song_ascii_numbers,
    mips,
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
        self.assertEqual(patch.status, "approved_for_test")
        self.assertEqual(patch.confidence, "verified")

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

    def test_generated_helper_has_same_abi_and_ascii_primitives(self) -> None:
        fragment = generate_font_renderer.build_ninja_song_ascii_number()
        self.assertEqual(
            fragment.symbol,
            generate_ninja_song_ascii_numbers.SYMBOL,
        )
        self.assertEqual(fragment.relocations, ())
        self.assertEqual(len(fragment.payload), 188)
        words = {
            int.from_bytes(fragment.payload[offset:offset + 4], "little")
            for offset in range(0, len(fragment.payload), 4)
        }
        for expected_word in (
            mips.jump(0x03, generate_font_renderer.SPRINTF),
            mips.i_type(0x0F, 0, 5, 0x60),
            mips.i_type(0x0D, 5, 5, 0x42D3),
            mips.i_type(0x09, 0, 9, 0x20),
            mips.i_type(0x09, 0, 9, 0x30),
            mips.i_type(0x2B, 29, 31, 0x4C),
            mips.i_type(0x23, 29, 31, 0x4C),
            mips.r_type(31, 0, 0, 0x08),
        ):
            self.assertIn(expected_word, words)

        numeric_fragments = generate_font_renderer.numeric_fragments()
        self.assertEqual(numeric_fragments, (fragment,))
        rows = [
            row
            for row in self.declaration.fragments
            if row.symbol == fragment.symbol
        ]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].payload, fragment.payload)
        self.assertEqual(len(rows[0].payload), 188)
        self.assertEqual(rows[0].kind, "code")
        self.assertEqual(rows[0].alignment, 4)


if __name__ == "__main__":
    unittest.main()
