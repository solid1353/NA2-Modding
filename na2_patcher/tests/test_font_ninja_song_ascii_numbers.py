from __future__ import annotations

import unittest

from na2_patcher.payload_builder import mips
from scripts.localization import generate_font_renderer
from scripts.research.localization import (
    generate_ninja_song_ascii_numbers,
)


class NinjaSongAsciiNumbersTests(unittest.TestCase):
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

if __name__ == "__main__":
    unittest.main()
