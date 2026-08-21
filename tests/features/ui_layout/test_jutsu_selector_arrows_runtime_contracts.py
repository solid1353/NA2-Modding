"""Focused source contracts for localized Jutsu-selector arrows."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from na228_builder.payload_builder import ee_c_fragments


REPOSITORY = Path(__file__).resolve().parents[3]
TOOLCHAIN_BIN = ee_c_fragments.default_toolchain_bin(REPOSITORY)
COMPILER = TOOLCHAIN_BIN / "ee-gcc.exe"
SOURCE_ROOT = REPOSITORY / "src" / "localization" / "ui"


def words(payload: bytes) -> tuple[int, ...]:
    return tuple(
        int.from_bytes(payload[offset : offset + 4], "little")
        for offset in range(0, len(payload), 4)
    )


def sequence_index(
    payload_words: tuple[int, ...],
    sequence: tuple[int, ...],
) -> int:
    for index in range(len(payload_words) - len(sequence) + 1):
        if payload_words[index : index + len(sequence)] == sequence:
            return index
    raise AssertionError(
        "compiled fragment lacks instruction sequence "
        + ", ".join(f"0x{word:08X}" for word in sequence)
    )


class JutsuSelectorArrowRuntimeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not COMPILER.is_file():
            raise unittest.SkipTest(
                f"local EE compiler is unavailable: {COMPILER}"
            )

    def compile_source(
        self,
        source_name: str,
        namespace: str,
        *,
        language: str = "c",
    ) -> ee_c_fragments.ExtractedEeObject:
        with tempfile.TemporaryDirectory() as temporary:
            return ee_c_fragments.compile_and_extract(
                SOURCE_ROOT / source_name,
                Path(temporary) / f"{source_name}.o",
                namespace=namespace,
                language=language,
                toolchain_bin=TOOLCHAIN_BIN,
            )

    def test_horizontal_arrow_suppression_rejoins_accepted_native_path(self) -> None:
        assembly = self.compile_source(
            "jutsu_selector_arrows_abi.S",
            "test.ui.jutsu.selector.arrows.abi",
            language="asm",
        )

        self.assertEqual(len(assembly.fragments), 1)
        self.assertEqual(
            "test.ui.jutsu.selector.arrows.abi.text."
            "localization.ui.jutsu.selector.arrows.suppress.horizontal",
            assembly.fragments[0].symbol,
        )
        self.assertEqual(
            bytes.fromhex("8EF61A0800000000"),
            assembly.fragments[0].payload,
        )
        self.assertEqual(assembly.fragments[0].relocations, ())

    def test_upper_and_lower_draw_entries_keep_exact_scoped_order(self) -> None:
        compiled = self.compile_source(
            "jutsu_selector_arrows.c",
            "test.ui.jutsu.selector.arrows",
        )
        fragments = {fragment.symbol: fragment for fragment in compiled.fragments}
        upper = fragments[
            "test.ui.jutsu.selector.arrows.text."
            "localization.ui.jutsu.selector.arrow.draw.upper"
        ]
        lower = fragments[
            "test.ui.jutsu.selector.arrows.text."
            "localization.ui.jutsu.selector.arrow.draw.lower"
        ]

        self.assertEqual(upper.relocations, ())
        self.assertEqual(lower.relocations, ())

        upper_words = words(upper.payload)
        lower_words = words(lower.payload)
        self.assertIn(0x3C023FC9, upper_words)
        self.assertIn(0x34420FDB, upper_words)
        self.assertNotIn(0x34420040, upper_words)
        self.assertIn(0x3C02BFC9, lower_words)
        self.assertIn(0x34420FDB, lower_words)
        self.assertIn(0x34420040, lower_words)

        for payload_words, rotation_high in (
            (upper_words, 0x3C023FC9),
            (lower_words, 0x3C02BFC9),
        ):
            mode_calls = tuple(
                index
                for index, word in enumerate(payload_words)
                if word == 0x0220F809
            )
            self.assertEqual(len(mode_calls), 2)
            rotation = payload_words.index(rotation_high)
            rotation_store = payload_words.index(0xAE02004C)
            draw = sequence_index(
                payload_words,
                (0x3C010037, 0x3421BC40, 0x0020F809),
            ) + 2
            flush = sequence_index(
                payload_words,
                (0x3C01001C, 0x3421C070, 0x0020F809),
            ) + 2
            self.assertLess(mode_calls[0], rotation)
            self.assertLess(rotation, rotation_store)
            self.assertLess(rotation_store, draw)
            self.assertLess(draw, flush)
            self.assertLess(flush, mode_calls[1])

        lower_flip = sequence_index(
            lower_words,
            (0x8E020004, 0x34420040, 0xAE020004),
        )
        self.assertLess(lower_words.index(0xAE02004C), lower_flip)
        self.assertLess(
            lower_flip,
            sequence_index(
                lower_words,
                (0x3C010037, 0x3421BC40, 0x0020F809),
            ),
        )


if __name__ == "__main__":
    unittest.main()
