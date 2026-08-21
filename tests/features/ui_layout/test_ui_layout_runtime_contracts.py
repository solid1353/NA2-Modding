"""Focused source and ABI contracts for localized UI-layout injections."""

from __future__ import annotations

import struct
import tempfile
import unittest
from pathlib import Path

from na228_builder.payload_builder import ee_c_fragments


REPOSITORY = Path(__file__).resolve().parents[3]
TOOLCHAIN_BIN = ee_c_fragments.default_toolchain_bin(REPOSITORY)
COMPILER = TOOLCHAIN_BIN / "ee-gcc.exe"
SOURCE_ROOT = REPOSITORY / "src" / "localization" / "ui"
STAGE_WIDTH_SCALE_BITS = (
    (232, 0x3F6C234F),
    (232, 0x3F6C234F),
    (272, 0x3F496969),
    (208, 0x3F800000),
    (344, 0x3F1F417D),
    (160, 0x3F800000),
    (168, 0x3F800000),
    (240, 0x3F644444),
    (288, 0x3F3E38E4),
    (200, 0x3F800000),
    (216, 0x3F7DA12F),
    (216, 0x3F7DA12F),
    (256, 0x3F560000),
    (256, 0x3F560000),
    (304, 0x3F3435E5),
    (152, 0x3F800000),
    (168, 0x3F800000),
    (176, 0x3F800000),
    (264, 0x3F4F83E1),
    (256, 0x3F560000),
    (192, 0x3F800000),
    (168, 0x3F800000),
    (280, 0x3F43A83B),
    (184, 0x3F800000),
)


def words(payload: bytes) -> tuple[int, ...]:
    return tuple(
        int.from_bytes(payload[offset : offset + 4], "little")
        for offset in range(0, len(payload), 4)
    )


class UiLayoutRuntimeContractTests(unittest.TestCase):
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

    def test_ui_c_entries_compile_as_independent_fragments(self) -> None:
        battle = self.compile_source(
            "battle_hud_names.c",
            "test.ui.battle.hud",
        )
        stage = self.compile_source(
            "stage_select.c",
            "test.ui.stage.select",
        )

        self.assertEqual(
            "test.ui.battle.hud.text.localization.ui.battle.hud.fit.width",
            battle.symbols["localization_ui_battle_hud_fit_width"].symbol,
        )
        self.assertEqual(
            "test.ui.stage.select.text.localization.ui.stage.select.name.draw",
            stage.symbols["localization_ui_stage_select_name_draw"].symbol,
        )

        battle_words = words(battle.fragments[0].payload)
        self.assertEqual(
            (
                0x3C014320,  # 160.0f high word
                0x44811000,
                0x00000000,
                0x460C1034,
                0x00000000,
                0x45000002,
                0x46006806,
                0x46001306,
                0x03E00008,
                0x46006002,  # mul.s f0,f12,f13
            ),
            battle_words,
        )

        stage_words = words(stage.fragments[0].payload)
        self.assertEqual(
            (
                0x27BDFFF0,
                0x3C014356,  # 214.0f
                0x44811000,
                0xFFBF0000,
                0x3C020037,
                0x3C013F80,  # 1.0f
                0x44817000,
                0x84A30004,  # rectangle->width from sixth argument a1
                0x44830000,
                0x00000000,
                0x46800020,
                0x46001034,
                0x00000000,
                0x45000002,
                0x3442BD00,  # native draw 0x0037BD00
                0x46001383,  # div.s f14,f2,f0
                0x0040F809,  # jalr ra,v0 with a NOP delay slot
                0x00000000,
                0xDFBF0000,
                0x03E00008,
                0x27BD0010,
                0x00000000,
            ),
            stage_words,
        )

    def test_exact_ui_abi_shims_and_battle_helper_bridge(self) -> None:
        battle_symbol = "test.ui.battle.hud.fit.width"
        assembly = self.compile_source(
            "ui_layout_abi.S",
            "test.ui.layout.abi",
            language="asm",
            external_symbols={
                "localization_ui_battle_hud_fit_width":
                    ee_c_fragments.SymbolReference(battle_symbol),
            },
        )
        fragments = {fragment.symbol: fragment for fragment in assembly.fragments}

        common = fragments[
            "test.ui.layout.abi.text.localization.ui.common.prompt.x.offset"
        ]
        self.assertEqual(
            bytes.fromhex("000083440063004660F20D0800000000"),
            common.payload,
        )

        versus = fragments[
            "test.ui.layout.abi.text.localization.ui.vs.confirmation.jutsu.label.place"
        ]
        self.assertEqual(
            bytes.fromhex("D041023C000082440800E00300031546"),
            versus.payload,
        )

        bridge = fragments[
            "test.ui.layout.abi.text.localization.ui.battle.hud.fit.width.adapter"
        ]
        self.assertEqual(
            [(0x18, "jal26", battle_symbol)],
            [
                (item.offset, item.kind, item.symbol)
                for item in bridge.relocations
            ],
        )
        bridge_words = words(bridge.payload)
        self.assertEqual(
            (
                0x27BDFFE0,  # 16-byte-aligned frame
                0xFFBF0000,  # preserve caller return address
                0xAFA30008,  # preserve live rectangle destination (v1)
                0xAFA5000C,  # preserve live layout record (a1)
                0xE7A10010,  # preserve live layout scale (f1)
                0x46000306,  # source width f0 -> C argument f12
                0x0C000000,  # relocated C-helper call
                0x46000B46,  # layout scale f1 -> C argument f13
                0x46000146,  # helper result f0 -> native result f5
                0xC7A10010,
                0x8FA5000C,
                0x8FA30008,
                0xDFBF0000,
                0x27BD0020,
                0x03E00008,
                0xC4600064,  # displaced native height load
            ),
            bridge_words,
        )

    def test_stage_formula_matches_every_committed_scale_bit_pattern(self) -> None:
        observed = tuple(
            (
                width,
                expected_bits,
                struct.unpack("<I", struct.pack("<f", min(1.0, 214.0 / width)))[0],
            )
            for width, expected_bits in STAGE_WIDTH_SCALE_BITS
        )

        self.assertEqual(len(observed), 24)
        self.assertTrue(
            all(expected == calculated for _, expected, calculated in observed)
        )


if __name__ == "__main__":
    unittest.main()
