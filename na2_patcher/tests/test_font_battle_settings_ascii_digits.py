from __future__ import annotations

import unittest
from pathlib import Path

from na2_patcher.modules.binary_patcher import engine
from scripts.research.localization import generate_battle_settings_ascii_digits


class BattleSettingsAsciiDigitsTests(unittest.TestCase):
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
            generate_battle_settings_ascii_digits.PATCH_ID
        ]
        self.assertTrue(patch.enabled)
        self.assertEqual(patch.status, "approved_for_test")
        self.assertEqual(patch.confidence, "verified")
        self.assertEqual(patch.group_id, "battle_ui")

        canonical = [
            edit
            for edit in package.edits
            if edit.patch_id
            == generate_battle_settings_ascii_digits.PATCH_ID
        ]
        generated = generate_battle_settings_ascii_digits.generated_edits()
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

    def test_clean_btl_guard_and_ascii_format_are_exact(self) -> None:
        btl, elf = generate_battle_settings_ascii_digits.verify_source()
        self.assertTrue(btl.is_file())
        self.assertTrue(elf.is_file())

    def test_replacement_is_call_local_and_preserves_infinity_branch(self) -> None:
        replacement = generate_battle_settings_ascii_digits.build_call()
        self.assertEqual(len(replacement), 24)
        words = [
            int.from_bytes(replacement[index : index + 4], "little")
            for index in range(0, len(replacement), 4)
        ]
        self.assertEqual(
            words,
            [
                generate_battle_settings_ascii_digits.mips.r_type(
                    generate_battle_settings_ascii_digits.A1,
                    generate_battle_settings_ascii_digits.ZERO,
                    generate_battle_settings_ascii_digits.A2,
                    0x2D,
                ),
                generate_battle_settings_ascii_digits.mips.i_type(
                    0x09,
                    generate_battle_settings_ascii_digits.SP,
                    generate_battle_settings_ascii_digits.A0,
                    generate_battle_settings_ascii_digits.BUFFER_OFFSET,
                ),
                generate_battle_settings_ascii_digits.mips.i_type(
                    0x0F,
                    generate_battle_settings_ascii_digits.ZERO,
                    generate_battle_settings_ascii_digits.A1,
                    generate_battle_settings_ascii_digits.FORMAT_D >> 16,
                ),
                generate_battle_settings_ascii_digits.mips.jump(
                    0x03,
                    generate_battle_settings_ascii_digits.SPRINTF,
                ),
                generate_battle_settings_ascii_digits.mips.i_type(
                    0x09,
                    generate_battle_settings_ascii_digits.A1,
                    generate_battle_settings_ascii_digits.A1,
                    generate_battle_settings_ascii_digits.FORMAT_D & 0xFFFF,
                ),
                0,
            ],
        )
        self.assertEqual(
            generate_battle_settings_ascii_digits.SPECIAL_BRANCH_OFFSET
            + len(
                bytes.fromhex(
                    generate_battle_settings_ascii_digits
                    .SPECIAL_BRANCH_EXPECTED_HEX
                )
            ),
            generate_battle_settings_ascii_digits.DESTINATION_OFFSET,
        )


if __name__ == "__main__":
    unittest.main()
