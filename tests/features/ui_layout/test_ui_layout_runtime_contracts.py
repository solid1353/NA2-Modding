"""Focused source and ABI contracts for localized UI-layout injections."""

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

    def test_ui_c_entries_export_expected_fragments(self) -> None:
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


if __name__ == "__main__":
    unittest.main()
