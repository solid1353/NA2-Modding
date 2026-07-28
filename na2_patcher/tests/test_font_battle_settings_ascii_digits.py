from __future__ import annotations

import unittest
from pathlib import Path

from na2_patcher.modules.runtime_injector import engine
from na2_patcher.project_paths import load_project_paths
from scripts.localization import generate_font_renderer


SPECIAL_BRANCH_OFFSET = 0x1CC3B0
SPECIAL_BRANCH_EXPECTED = bytes.fromhex(
    "640002240800A214000000006000A42778B1858FE0F0050C00000000"
    "080000100000000000000000"
)


class BattleSettingsAsciiDigitsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repository = Path(__file__).resolve().parents[2]
        cls.package = engine.load_package(
            cls.repository
            / "na2_patcher"
            / "features"
            / "localization"
            / "runtime_injector",
            owner="localization.runtime_injector",
        )
        cls.hook = next(
            hook
            for hook in generate_font_renderer.numeric_hooks()
            if hook.patch_id == "font_battle_settings_ascii_digits"
        )

    def test_canonical_symbolic_hook_matches_the_generator(self) -> None:
        patch = self.package.patches["font_battle_settings_ascii_digits"]
        self.assertTrue(patch.enabled)
        self.assertEqual(patch.status, "runtime_proven")
        self.assertEqual(patch.group_id, "battle_ui")
        edit = next(
            edit
            for edit in self.package.edits
            if edit.patch_id == patch.patch_id
        )
        symbolic = edit.symbolic_patch
        self.assertEqual(symbolic.offset, self.hook.offset)
        self.assertEqual(
            symbolic.expected.hex().upper(),
            self.hook.expected_hex,
        )
        self.assertEqual(
            symbolic.replacement_template.hex().upper(),
            self.hook.replacement_hex,
        )
        self.assertEqual(symbolic.relocation_offset, 8)
        self.assertEqual(
            symbolic.symbol,
            generate_font_renderer.BATTLE_SETTINGS_TIME,
        )
        self.assertEqual(symbolic.encoding, self.hook.encoding)
        self.assertEqual(symbolic.encoding, "jal26")

    def test_clean_guard_and_infinity_branch_are_untouched(self) -> None:
        btl = (
            load_project_paths(self.repository).path("source_na2")
            / "PRG"
            / "BTL.BIN"
        )
        data = btl.read_bytes()
        expected = bytes.fromhex(self.hook.expected_hex)
        self.assertEqual(
            data[self.hook.offset : self.hook.offset + len(expected)],
            expected,
        )
        self.assertEqual(
            data[
                SPECIAL_BRANCH_OFFSET
                : SPECIAL_BRANCH_OFFSET + len(SPECIAL_BRANCH_EXPECTED)
            ],
            SPECIAL_BRANCH_EXPECTED,
        )
        self.assertEqual(
            SPECIAL_BRANCH_OFFSET + len(SPECIAL_BRANCH_EXPECTED),
            self.hook.offset,
        )

    def test_compiled_entry_uses_only_decimal_bridge(self) -> None:
        fragments = {
            fragment.symbol: fragment
            for fragment in generate_font_renderer.build_numeric_c_core()
        }
        self.assertEqual(
            {
                relocation.symbol
                for relocation in fragments[
                    generate_font_renderer.BATTLE_SETTINGS_TIME
                ].relocations
            },
            {generate_font_renderer.NUMERIC_FORMAT_DECIMAL},
        )


if __name__ == "__main__":
    unittest.main()
