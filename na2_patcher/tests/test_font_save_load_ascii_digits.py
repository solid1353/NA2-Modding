from __future__ import annotations

import unittest
from pathlib import Path

from na2_patcher.modules.binary_patcher import engine as binary_engine
from na2_patcher.modules.runtime_injector import engine as runtime_engine
from na2_patcher.payload_builder import mips
from na2_patcher.project_paths import load_project_paths
from scripts.localization import generate_font_renderer


class SaveLoadAsciiDigitsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repository = Path(__file__).resolve().parents[2]
        feature = (
            cls.repository
            / "na2_patcher"
            / "features"
            / "localization"
        )
        cls.runtime = runtime_engine.load_package(
            feature / "runtime_injector",
            owner="localization.runtime_injector",
        )
        cls.binary = binary_engine.load_package(feature / "binary_patcher")
        cls.hooks = tuple(
            hook
            for hook in generate_font_renderer.numeric_hooks()
            if hook.patch_id == "font_save_load_ascii_digits"
        )

    def test_canonical_symbolic_hooks_match_the_generator(self) -> None:
        patch = self.runtime.patches["font_save_load_ascii_digits"]
        self.assertTrue(patch.enabled)
        self.assertEqual(patch.status, "runtime_proven")
        self.assertEqual(patch.group_id, "front_end")
        canonical = tuple(
            edit
            for edit in self.runtime.edits
            if edit.patch_id == patch.patch_id
        )
        self.assertEqual(len(canonical), 6)
        for edit, hook in zip(canonical, self.hooks, strict=True):
            self.assertEqual(edit.edit_id, hook.edit_id)
            self.assertEqual(edit.order, hook.order)
            self.assertEqual(edit.target_id, hook.target_id)
            symbolic = edit.symbolic_patch
            self.assertEqual(symbolic.offset, hook.offset)
            self.assertEqual(symbolic.expected.hex().upper(), hook.expected_hex)
            self.assertEqual(
                symbolic.replacement_template.hex().upper(),
                hook.replacement_hex,
            )
            self.assertEqual(
                symbolic.relocation_offset,
                hook.relocation_offset,
            )
            self.assertEqual(symbolic.symbol, hook.symbol)

    def test_clean_elf_guards_and_local_colon_are_exact(self) -> None:
        elf = load_project_paths(self.repository).path("source_na2") / "SLPS_258.37"
        data = elf.read_bytes()
        for hook in self.hooks:
            expected = bytes.fromhex(hook.expected_hex)
            self.assertEqual(
                data[hook.offset : hook.offset + len(expected)],
                expected,
            )
        colon = [
            edit
            for edit in self.binary.edits
            if edit.patch_id == "font_save_load_ascii_digits"
        ]
        self.assertEqual(len(colon), 1)
        self.assertEqual(colon[0].destination_offset, 0x503134)
        self.assertEqual(colon[0].replacement_hex, "3A000000")

    def test_date_order_and_year_lifetime_are_explicit(self) -> None:
        self.assertEqual(
            [hook.symbol for hook in self.hooks[:3]],
            [
                generate_font_renderer.SAVE_LOAD_DAY,
                generate_font_renderer.SAVE_LOAD_TWO,
                generate_font_renderer.SAVE_LOAD_YEAR,
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
            for fragment in generate_font_renderer.build_numeric_c_core()
        }
        self.assertEqual(
            {
                relocation.symbol
                for relocation in fragments[
                    generate_font_renderer.SAVE_LOAD_DAY
                ].relocations
            },
            {generate_font_renderer.NUMERIC_FORMAT_TWO_DECIMAL},
        )
        self.assertEqual(
            {
                relocation.symbol
                for relocation in fragments[
                    generate_font_renderer.SAVE_LOAD_HOUR
                ].relocations
            },
            {generate_font_renderer.NUMERIC_FORMAT_TWO_DECIMAL},
        )
        self.assertEqual(
            {
                relocation.symbol
                for relocation in fragments[
                    generate_font_renderer.SAVE_LOAD_YEAR
                ].relocations
            },
            {generate_font_renderer.NUMERIC_FORMAT_DECIMAL},
        )


if __name__ == "__main__":
    unittest.main()
