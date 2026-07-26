from __future__ import annotations

import unittest
from pathlib import Path

from na2_patcher.modules.binary_patcher import engine
from scripts.research.localization import generate_save_load_ascii_digits


class SaveLoadAsciiDigitsTests(unittest.TestCase):
    def test_canonical_patch_matches_the_generator(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        package = engine.load_package(
            repository
            / "na2_patcher"
            / "features"
            / "localization"
            / "binary_patcher"
        )
        patch = package.patches[
            generate_save_load_ascii_digits.PATCH_ID
        ]
        self.assertTrue(patch.default_enabled)
        self.assertEqual(patch.status, "runtime_proven")
        self.assertEqual(patch.confidence, "verified")
        self.assertEqual(patch.group_id, "front_end")

        canonical = [
            edit
            for edit in package.edits
            if edit.patch_id == generate_save_load_ascii_digits.PATCH_ID
        ]
        generated = generate_save_load_ascii_digits.generated_edits()
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

    def test_clean_elf_guards_and_ascii_formats_are_exact(self) -> None:
        elf = generate_save_load_ascii_digits.verify_source()
        self.assertTrue(elf.is_file())
        for site in generate_save_load_ascii_digits.CALL_SITES:
            replacement = generate_save_load_ascii_digits.build_call(site)
            self.assertEqual(len(replacement), 28)
            jal = int.from_bytes(replacement[20:24], "little")
            self.assertEqual(
                jal,
                generate_save_load_ascii_digits.mips.jump(
                    0x03,
                    generate_save_load_ascii_digits.SPRINTF,
                ),
            )


if __name__ == "__main__":
    unittest.main()
