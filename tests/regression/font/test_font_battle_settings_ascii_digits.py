from __future__ import annotations

import unittest

from scripts.research.localization import verify_font_renderer


class BattleSettingsAsciiDigitsTests(unittest.TestCase):
    def test_compiled_entry_uses_the_documented_decimal_bridge(self) -> None:
        fragments = {
            fragment.symbol: fragment
            for fragment in verify_font_renderer.build_numeric_c_core()
        }
        self.assertEqual(
            {
                relocation.symbol
                for relocation in fragments[
                    verify_font_renderer.BATTLE_SETTINGS_TIME
                ].relocations
            },
            {verify_font_renderer.NUMERIC_FORMAT_DECIMAL},
        )


if __name__ == "__main__":
    unittest.main()
