from __future__ import annotations

import unittest

from na2_patcher.payload_builder import mips
from scripts.research.localization import verify_font_renderer


class SaveLoadAsciiDigitsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.hooks = tuple(
            hook
            for hook in verify_font_renderer.numeric_hooks()
            if hook.patch_id == "font_numeric_save_load"
        )

    def test_date_order_and_year_lifetime_are_explicit(self) -> None:
        self.assertEqual(
            [hook.symbol for hook in self.hooks[:3]],
            [
                verify_font_renderer.SAVE_LOAD_DAY,
                verify_font_renderer.SAVE_LOAD_TWO,
                verify_font_renderer.SAVE_LOAD_YEAR,
            ],
        )
        first_words = [
            int.from_bytes(
                bytes.fromhex(self.hooks[0].replacement_hex)[index : index + 4],
                "little",
            )
            for index in range(0, 28, 4)
        ]
        self.assertEqual(
            first_words[0],
            mips.r_type(3, 0, 4, 0x2D),
        )
        self.assertEqual(first_words[2], 0)
        self.assertEqual(
            first_words[4],
            mips.r_type(2, 0, 22, 0x2D),
        )

    def test_compiled_entries_use_only_native_format_bridges(self) -> None:
        fragments = {
            fragment.symbol: fragment
            for fragment in verify_font_renderer.build_numeric_c_core()
        }
        self.assertEqual(
            {
                relocation.symbol
                for relocation in fragments[
                    verify_font_renderer.SAVE_LOAD_DAY
                ].relocations
            },
            {verify_font_renderer.NUMERIC_FORMAT_TWO_DECIMAL},
        )
        self.assertEqual(
            {
                relocation.symbol
                for relocation in fragments[
                    verify_font_renderer.SAVE_LOAD_HOUR
                ].relocations
            },
            {verify_font_renderer.NUMERIC_FORMAT_TWO_DECIMAL},
        )
        self.assertEqual(
            {
                relocation.symbol
                for relocation in fragments[
                    verify_font_renderer.SAVE_LOAD_YEAR
                ].relocations
            },
            {verify_font_renderer.NUMERIC_FORMAT_DECIMAL},
        )


if __name__ == "__main__":
    unittest.main()
