from __future__ import annotations

import unittest
from pathlib import Path

from na2_patcher.modules.binary_patcher import engine as binary_engine
from na2_patcher.modules.runtime_injector import engine as runtime_engine
from scripts.research.localization import generate_font_renderer
from scripts.research.localization import generate_on_off_context_split


class OnOffContextSplitTests(unittest.TestCase):
    def test_canonical_pointer_patch_matches_the_generator(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        package = binary_engine.load_package(
            repository
            / "na2_patcher"
            / "features"
            / "localization"
            / "binary_patcher"
        )
        patch = package.patches[
            generate_on_off_context_split.PATCH_ID
        ]
        self.assertTrue(patch.enabled)
        self.assertEqual(patch.status, "approved_for_test")
        self.assertEqual(patch.confidence, "verified")
        self.assertEqual(patch.group_id, "auto_fit")

        canonical = [
            edit
            for edit in package.edits
            if edit.patch_id == generate_on_off_context_split.PATCH_ID
        ]
        generated = generate_on_off_context_split.generated_edits()
        self.assertEqual(len(canonical), len(generated))
        for edit, expected in zip(canonical, generated, strict=True):
            self.assertEqual(edit.edit_id, expected["edit_id"])
            self.assertEqual(edit.order, expected["order"])
            self.assertEqual(
                edit.destination_target_id,
                expected["destination_target_id"],
            )
            self.assertEqual(
                edit.destination_offset,
                expected["destination_offset"],
            )
            self.assertEqual(edit.operation, expected["operation"])
            self.assertEqual(edit.length, expected["length"])
            self.assertEqual(edit.expected_hex, expected["expected_hex"])
            self.assertEqual(
                edit.replacement_hex,
                expected["replacement_hex"],
            )

    def test_clean_elf_guards_are_exact(self) -> None:
        btl, elf = generate_on_off_context_split.verify_source()
        self.assertTrue(btl.is_file())
        self.assertTrue(elf.is_file())

    def test_special_controls_uses_the_existing_boxed_adapter(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        package = runtime_engine.load_package(
            repository
            / "na2_patcher"
            / "features"
            / "localization"
            / "runtime_injector",
            owner="localization.runtime_injector",
        )
        patch = package.patches["font_v2_controls"]
        self.assertTrue(patch.enabled)
        self.assertEqual(patch.status, "approved_for_test")

        matching = [
            edit
            for edit in package.edits
            if edit.patch_id == "font_v2_controls"
            and edit.symbolic_patch.offset
            == generate_on_off_context_split.SPECIAL_CALL_OFFSET
        ]
        self.assertEqual(len(matching), 1)
        edit = matching[0].symbolic_patch
        self.assertEqual(
            edit.expected,
            bytes.fromhex(
                generate_on_off_context_split.SPECIAL_CALL_EXPECTED_HEX
            ),
        )
        self.assertEqual(
            edit.symbol,
            generate_on_off_context_split.SPECIAL_CALL_SYMBOL,
        )
        self.assertEqual(edit.encoding, "jal26")

        widths = generate_font_renderer.build_ascii_widths()
        for value in ("Off", "On"):
            measured = sum(
                widths[ord(character) - generate_font_renderer.ASCII_FIRST]
                for character in value
            )
            self.assertLess(
                measured,
                generate_font_renderer.CONTROLS_BOX_WIDTH,
            )

    def test_practice_rows_share_the_existing_titlecase_table(self) -> None:
        edits = generate_on_off_context_split.generated_edits()
        self.assertEqual(len(edits), 3)
        for edit in edits:
            self.assertEqual(
                edit["replacement_hex"],
                generate_on_off_context_split.TITLECASE_TABLE_POINTER_HEX,
            )


if __name__ == "__main__":
    unittest.main()
