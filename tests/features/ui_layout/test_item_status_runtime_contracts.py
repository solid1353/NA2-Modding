"""Focused ABI contracts for the accepted item-status renderer conversion."""

from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from na228_builder.payload_builder import ee_c_fragments


REPOSITORY = Path(__file__).resolve().parents[3]
TOOLCHAIN_BIN = ee_c_fragments.default_toolchain_bin(REPOSITORY)
COMPILER = TOOLCHAIN_BIN / "ee-gcc.exe"
SOURCE_ROOT = REPOSITORY / "src" / "localization" / "ui"
RENDERER_REFERENCE = "test.ui.item.status.renderer"
TAIL_REFERENCE = (
    "test.ui.item.status.c.text.localization.item.status.update.tail"
)


def words(payload: bytes) -> tuple[int, ...]:
    return tuple(
        int.from_bytes(payload[offset : offset + 4], "little")
        for offset in range(0, len(payload), 4)
    )


def contains_words(payload: bytes, expected: tuple[int, ...]) -> bool:
    payload_words = words(payload)
    width = len(expected)
    return any(
        payload_words[index : index + width] == expected
        for index in range(len(payload_words) - width + 1)
    )


class ItemStatusRuntimeContractTests(unittest.TestCase):
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
        language: str,
        external_symbols: dict[str, ee_c_fragments.SymbolReference] | None = None,
    ) -> ee_c_fragments.ExtractedEeObject:
        with tempfile.TemporaryDirectory() as temporary:
            return ee_c_fragments.compile_and_extract(
                SOURCE_ROOT / source_name,
                Path(temporary) / f"{source_name}.o",
                namespace=namespace,
                language=language,
                toolchain_bin=TOOLCHAIN_BIN,
                external_symbols=external_symbols,
            )

    def test_resident_renderer_is_the_exact_accepted_boot_elf_body(self) -> None:
        assembly = self.compile_source(
            "item_status_renderer.S",
            "test.ui.item.status.renderer.asm",
            language="asm",
        )
        self.assertEqual(len(assembly.fragments), 1)
        renderer = assembly.fragments[0]

        self.assertEqual(
            "test.ui.item.status.renderer.asm.text."
            "localization.item.status.foreground.draw",
            renderer.symbol,
        )
        self.assertEqual(len(renderer.payload), 500)
        self.assertEqual(renderer.relocations, ())
        self.assertEqual(
            hashlib.sha256(renderer.payload).hexdigest().upper(),
            "A39D248B11539514FA49523952E09755DA57649ED0A03A09CEBA2081C3011A2F",
        )

    def test_common_update_bridge_enters_only_the_tail_and_rejoins_epilogue(
        self,
    ) -> None:
        c_source = self.compile_source(
            "item_status.c",
            "test.ui.item.status.c",
            language="c",
            external_symbols={
                "localization_item_status_foreground_draw":
                    ee_c_fragments.SymbolReference(RENDERER_REFERENCE),
            },
        )
        assembly = self.compile_source(
            "item_status_update_abi.S",
            "test.ui.item.status.update.asm",
            language="asm",
            external_symbols={
                "localization_item_status_update_tail":
                    ee_c_fragments.SymbolReference(TAIL_REFERENCE),
            },
        )

        self.assertNotIn("localization_item_status_update", c_source.symbols)
        self.assertEqual(
            TAIL_REFERENCE,
            c_source.symbols["localization_item_status_update_tail"].symbol,
        )

        bridge = assembly.fragments[0]
        self.assertEqual(
            bytes.fromhex(
                "3000A527"  # addiu a1,sp,0x30: native transformed position
                "0000000C"  # relocated jal to the C tail
                "00000000"
                "E6371C08"  # j 0x0070DF98: native restore/return epilogue
                "00000000"
            ),
            bridge.payload,
        )
        self.assertEqual(
            [(4, "jal26", TAIL_REFERENCE)],
            [
                (item.offset, item.kind, item.symbol)
                for item in bridge.relocations
            ],
        )

    def test_common_tail_preserves_distinct_bubble_and_foreground_abis(
        self,
    ) -> None:
        c_source = self.compile_source(
            "item_status.c",
            "test.ui.item.status.c",
            language="c",
            external_symbols={
                "localization_item_status_foreground_draw":
                    ee_c_fragments.SymbolReference(RENDERER_REFERENCE),
            },
        )
        tail_symbol = c_source.symbols[
            "localization_item_status_update_tail"
        ].symbol
        tail = next(
            fragment
            for fragment in c_source.fragments
            if fragment.symbol == tail_symbol
        )

        # Reuse original sp+0x20 as the foreground (transformed-1), execute the
        # accepted X +0.0 operation, subtract 33 only from Y, then perform the
        # native record-0x80 lookup before choosing its variant.
        self.assertIn(0x24B2FFF0, words(tail.payload))  # foreground = input - 1
        self.assertTrue(
            contains_words(
                tail.payload,
                (
                    0x6A020007,
                    0x6E020000,
                    0x6A03000F,
                    0x6E030008,
                    0xB2420007,
                    0xB6420000,
                    0xB243000F,
                    0xB6430008,
                    0xC6420000,
                    0xC6440004,
                    0x46061080,  # foreground X + volatile 0.0
                    0x46002101,  # foreground Y - 33.0
                    0xE6420000,
                    0x3C010037,
                    0x34217CB0,
                    0x0020F809,
                    0xE6440004,
                ),
            )
        )

        # The bubble draw receives the unshifted native sp+0x30 position. The
        # class callback separately receives the shifted sp+0x20 foreground.
        self.assertTrue(
            contains_words(
                tail.payload,
                (
                    0x00C0202D,
                    0xC62C0034,
                    0x4600A346,
                    0x3C013FC8,
                    0x3421F5C3,
                    0x44817800,
                    0x0200302D,  # a2 = original sp+0x30 transformed position
                    0x3C013F80,
                    0x44817000,
                    0x0260F809,
                    0x24050080,
                ),
            )
        )
        self.assertTrue(
            contains_words(
                tail.payload,
                (
                    0x0220202D,
                    0x8C620008,
                    0x0040F809,
                    0x0240282D,  # class callback receives sp+0x20 foreground
                ),
            )
        )

    def test_each_item_class_keeps_its_accepted_renderer_route(self) -> None:
        c_source = self.compile_source(
            "item_status.c",
            "test.ui.item.status.c",
            language="c",
            external_symbols={
                "localization_item_status_foreground_draw":
                    ee_c_fragments.SymbolReference(RENDERER_REFERENCE),
            },
        )
        expected_calls = {
            "localization_item_status_update_tail": 0,
            "localization_item_status_numeric_draw": 2,
            "localization_item_status_single_draw": 0,
            "localization_item_status_paired_draw": 2,
            "localization_item_status_fixed_draw": 2,
        }

        for source_symbol, call_count in expected_calls.items():
            fragment_symbol = c_source.symbols[source_symbol].symbol
            fragment = next(
                item
                for item in c_source.fragments
                if item.symbol == fragment_symbol
            )
            renderer_calls = [
                relocation
                for relocation in fragment.relocations
                if relocation.symbol == RENDERER_REFERENCE
            ]
            self.assertEqual(
                len(renderer_calls),
                call_count,
                source_symbol,
            )

        single_symbol = c_source.symbols[
            "localization_item_status_single_draw"
        ].symbol
        single = next(
            item
            for item in c_source.fragments
            if item.symbol == single_symbol
        )
        self.assertTrue(
            contains_words(
                single.payload,
                (0x3C120037,),
            )
        )
        self.assertTrue(
            contains_words(
                single.payload,
                (0x36527720,),
            )
        )

    def test_compiled_class_geometry_is_the_accepted_layout(self) -> None:
        c_source = self.compile_source(
            "item_status.c",
            "test.ui.item.status.c",
            language="c",
            external_symbols={
                "localization_item_status_foreground_draw":
                    ee_c_fragments.SymbolReference(RENDERER_REFERENCE),
            },
        )

        def fragment(source_symbol: str) -> bytes:
            fragment_symbol = c_source.symbols[source_symbol].symbol
            return next(
                item.payload
                for item in c_source.fragments
                if item.symbol == fragment_symbol
            )

        numeric = fragment("localization_item_status_numeric_draw")
        self.assertTrue(
            contains_words(
                numeric,
                (
                    0x3C0141A0,  # top Y +20
                    0x44810000,
                    0xB7A40008,
                    0x24120095,
                    0x2402000C,
                    0x4480A000,  # ordinary top rotation = 0
                    0x02222018,
                    0xC7A20004,
                    0x46001180,
                    0x3C0141B0,  # top X +22
                ),
            )
        )
        self.assertTrue(
            contains_words(
                numeric,
                (
                    0x3C014160,  # record 0x82 top X/Y adjustment = -14
                    0x44810000,
                    0x3C013FC9,
                    0x34210FDB,  # quarter turn
                    0x4481A000,
                    0x46003081,
                    0x46002001,
                ),
            )
        )
        self.assertTrue(
            contains_words(
                numeric,
                (
                    0x4480A000,  # record 0x8D rotation = 0
                    0xC7A00004,
                    0x3C01420C,  # record 0x8D Y +35
                ),
            )
        )
        self.assertTrue(
            contains_words(
                numeric,
                (
                    0x3C013FC9,
                    0x34210FDB,  # record 0x95 quarter turn
                    0x4481A000,
                    0x3C014150,  # record 0x95 Y +13
                ),
            )
        )
        self.assertTrue(
            contains_words(
                numeric,
                (
                    0x3C014248,  # digit input X origin -50
                    0x44811000,
                ),
            )
        )

        single = fragment("localization_item_status_single_draw")
        self.assertTrue(
            contains_words(
                single,
                (
                    0x3C014204,  # single-label Y +33
                    0x44811000,
                    0xB7A30008,
                    0x24020082,
                    0x4480A000,
                    0xC7A00004,
                    0x46020000,
                    0x12220027,
                    0xE7A00004,
                    0x24020099,  # both 0x82 and 0x99 rotate
                ),
            )
        )
        self.assertTrue(
            contains_words(
                single,
                (0x3C013FC9, 0x34210FDB, 0x4481A000),
            )
        )

        paired = fragment("localization_item_status_paired_draw")
        self.assertTrue(
            contains_words(
                paired,
                (
                    0x3C014190,  # paired top Y +18
                    0x44810000,
                    0xB7A40008,
                    0x2402000C,
                    0x02222018,
                    0x4480A000,
                ),
            )
        )
        self.assertTrue(
            contains_words(
                paired,
                (
                    0x3C014160,  # record 0x82 top adjustment -14
                    0x44810000,
                    0x3C013FC9,
                    0x34210FDB,
                    0x4481A000,
                    0x46002001,
                ),
            )
        )
        self.assertTrue(
            contains_words(
                paired,
                (
                    0x3C0141A0,  # paired lower Y +20
                    0x44810000,
                ),
            )
        )
        self.assertTrue(
            contains_words(
                paired,
                (
                    0x2402009B,
                    0xE7A40004,
                    0x00031842,
                    0x44831000,
                    0x00000000,
                    0x468010A0,
                    0x46020001,
                    0x12420025,
                ),
            )
        )
        self.assertTrue(
            contains_words(
                paired,
                (
                    0x3C014160,  # record 0x9B lower adjustment +14
                    0x44810000,
                    0x4480A000,  # record 0x9B rotation = 0
                    0x46002000,
                ),
            )
        )

        fixed = fragment("localization_item_status_fixed_draw")
        self.assertTrue(
            contains_words(
                fixed,
                (
                    0x2404008E,
                    0x3C02005B,
                    0x9442110E,
                ),
            )
        )
        self.assertTrue(
            contains_words(
                fixed,
                (
                    0x3C0141A0,  # record 0x8E Y +20
                    0x44811000,
                ),
            )
        )
        self.assertTrue(
            contains_words(
                fixed,
                (
                    0x2404008D,
                    0x3C02005B,
                    0x94421102,
                ),
            )
        )
        self.assertTrue(
            contains_words(
                fixed,
                (
                    0x3C014214,  # record 0x8D Y +37
                    0x44811000,
                ),
            )
        )
        self.assertGreaterEqual(words(fixed).count(0x44807000), 2)

    def test_compiled_bubble_width_scale_table_keeps_every_class_case(
        self,
    ) -> None:
        c_source = self.compile_source(
            "item_status.c",
            "test.ui.item.status.c",
            language="c",
            external_symbols={
                "localization_item_status_foreground_draw":
                    ee_c_fragments.SymbolReference(RENDERER_REFERENCE),
            },
        )
        tail_symbol = c_source.symbols[
            "localization_item_status_update_tail"
        ].symbol
        tail = next(
            item
            for item in c_source.fragments
            if item.symbol == tail_symbol
        )
        tail_words = words(tail.payload)

        # Paired 4/5/6+14/15/17, paired fallback, single 9/default,
        # fixed, and non-paired/single/fixed constants.
        for constant in (
            0x3C013FCC,  # 1.59375
            0x3C013FC4,  # 1.53125
            0x3C013FF4,  # 1.90625
            0x3C013F8C,  # 1.09375
            0x3C013F94,  # 1.15625
            0x3C013F80,  # 1.0
            0x3C013FA0,  # 1.25
        ):
            self.assertIn(constant, tail_words)

        self.assertTrue(
            contains_words(
                tail.payload,
                (
                    0x24020004,
                    0x3C013FCC,
                    0x44810000,
                    0x10820018,
                    0x24020005,
                    0x3C013FC4,
                ),
            )
        )
        for item_code in (0x06, 0x0E, 0x0F, 0x11):
            self.assertIn(0x24020000 | item_code, tail_words)
        self.assertIn(0x2C820012, tail_words)


if __name__ == "__main__":
    unittest.main()
