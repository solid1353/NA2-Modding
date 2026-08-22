"""Specific accepted ABI and instruction contracts in the release font package."""

from __future__ import annotations

import csv
import unittest
from pathlib import Path

from na228_builder.payload_builder import build_resident_payload
from na228_builder.payload_builder import mips
from na228_builder.scripts import catalog
from na228_builder.scripts.composer import resolve_symbolic_patches
from scripts.research.localization.verify_font_renderer import (
    ASCII_FIRST,
    build_ascii_widths,
)
from scripts.lib.paths import load_paths
from tests.na228_builder._fixtures import resident_payload_config


REPOSITORY = Path(__file__).resolve().parents[3]
PATHS = load_paths(REPOSITORY)


def words(payload: bytes) -> tuple[int, ...]:
    if len(payload) % 4:
        raise AssertionError("MIPS payload is not word aligned")
    return tuple(
        int.from_bytes(payload[offset : offset + 4], "little")
        for offset in range(0, len(payload), 4)
    )


def is_register_move(word: int, *, source: int, destination: int) -> bool:
    return (
        word >> 26 == 0
        and (word >> 21) & 0x1F == source
        and (word >> 16) & 0x1F == 0
        and (word >> 11) & 0x1F == destination
        and word & 0x3F in {0x21, 0x2D}
    )


def loads_u32(words_: tuple[int, ...], value: int) -> bool:
    """Return whether a compiled fragment materializes one exact 32-bit value."""
    upper = value >> 16
    lower = value & 0xFFFF
    for index, word in enumerate(words_):
        if word >> 26 != 0x0F or word & 0xFFFF != upper:
            continue
        register = (word >> 16) & 0x1F
        if lower == 0:
            return True
        if index + 1 >= len(words_):
            continue
        following = words_[index + 1]
        if (
            following >> 26 == 0x0D
            and (following >> 21) & 0x1F == register
            and (following >> 16) & 0x1F == register
            and following & 0xFFFF == lower
        ):
            return True
    return False


class FontRuntimeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        builder = PATHS.path("builder")
        selection = catalog.load_selection(
            builder / "catalog",
            builder / "configurations" / "release.json",
        )
        cls.package = catalog.load_runtime_package(
            selection,
            "localization",
            builder / "catalog" / "targets.tsv",
            REPOSITORY,
            "localization.runtime_injector",
        )
        cls.build = build_resident_payload(
            cls.package.payload_fragments,
            config=resident_payload_config(
                reservation_end=0x00A00000,
                maximum_end=0x00B00000,
            ),
        )

    def test_numeric_hooks_link_and_save_load_day_preserves_year(self) -> None:
        symbols = {
            "save_load_hour",
            "save_load_year",
            "save_load_day",
            "save_load_two",
            "battle_settings_time",
        }
        edits = tuple(
            edit
            for edit in self.package.active_edits
            if edit.symbolic_patch.symbol in symbols
        )
        self.assertEqual(len(edits), 7)
        resolved = {
            patch.mapping_id: patch
            for patch in resolve_symbolic_patches(
                self.build,
                tuple(edit.symbolic_patch for edit in edits),
            )
        }
        for edit in edits:
            patch = resolved[edit.symbolic_patch.mapping_id]
            offset = edit.symbolic_patch.relocation_offset
            instruction = int.from_bytes(
                patch.replacement[offset : offset + 4], "little"
            )
            self.assertEqual(
                instruction >> 26,
                0x03,
                f"{patch.mapping_id} must link with JAL",
            )

        day = next(
            resolved[edit.symbolic_patch.mapping_id]
            for edit in edits
            if edit.symbolic_patch.symbol == "save_load_day"
        )
        self.assertTrue(
            any(
                is_register_move(word, source=2, destination=22)
                for word in words(day.replacement)
            ),
            "Save/Load day hook must preserve the returned year from v0 in s6",
        )

    def test_c_and_native_bridges_preserve_ee_eabi_arguments(self) -> None:
        fragments = {fragment.symbol: fragment for fragment in self.package.fragments}
        ninja = words(fragments["ninja_song_ascii_number"].payload)
        self.assertTrue(
            any(
                word >> 26 == 0
                and (word >> 21) & 0x1F == 8
                and (word >> 16) & 0x1F == 0
                and word & 0x3F in {0x21, 0x2D}
                for word in ninja
            ),
            "Ninja Song C entry must consume its fifth integer argument from t0",
        )

        practice = words(fragments["v2_practice_adapter"].payload)
        self.assertEqual(len(practice), 5)
        self.assertTrue(is_register_move(practice[0], source=19, destination=7))
        self.assertTrue(is_register_move(practice[1], source=18, destination=8))
        mfc1 = practice[2]
        self.assertEqual(mfc1 >> 26, 0x11)
        self.assertEqual((mfc1 >> 21) & 0x1F, 0)
        self.assertEqual((mfc1 >> 16) & 0x1F, 9)
        self.assertEqual((mfc1 >> 11) & 0x1F, 12)
        self.assertEqual(practice[3] >> 26, 0x02)
        self.assertEqual(practice[4], 0)

        command = words(fragments["v2_command_relationship_adapter"].payload)
        self.assertEqual(len(command), 4)
        self.assertTrue(is_register_move(command[0], source=17, destination=5))
        mfc1 = command[1]
        self.assertEqual(mfc1 >> 26, 0x11)
        self.assertEqual((mfc1 >> 21) & 0x1F, 0)
        self.assertEqual((mfc1 >> 16) & 0x1F, 7)
        self.assertEqual((mfc1 >> 11) & 0x1F, 13)
        self.assertEqual(command[2] >> 26, 0x02)
        self.assertEqual(command[3], 0)

    def test_glyph_geometry_shims_preserve_accepted_instruction_bodies(
        self,
    ) -> None:
        accepted_bodies = {
            "glyph_secondary_cell_guard": bytes.fromhex(
                "7B00412C0A1001000600A3941F1C060800000000"
            ),
            "glyph_normal_bottom_edge": bytes.fromhex(
                "08006330020060100C0021C6100021C660088046"
                "000D0046E01F06086CCA848F"
            ),
        }
        fragments = {
            fragment.symbol: fragment for fragment in self.package.fragments
        }
        for symbol, accepted in accepted_bodies.items():
            self.assertEqual(fragments[symbol].payload, accepted)

        accepted_hooks = {
            "glyph_secondary_cell_guard": (
                0x87174,
                bytes.fromhex("6800658E0600A394"),
                bytes.fromhex("000000006800658E"),
            ),
            "glyph_normal_bottom_edge": (
                0x88078,
                bytes.fromhex("000D00466CCA848F"),
                bytes.fromhex("0000000070002392"),
            ),
        }
        edits = tuple(
            edit
            for edit in self.package.active_edits
            if edit.symbolic_patch.symbol in accepted_hooks
        )
        self.assertEqual(len(edits), len(accepted_hooks))
        resolved = {
            patch.mapping_id: patch
            for patch in resolve_symbolic_patches(
                self.build,
                tuple(edit.symbolic_patch for edit in edits),
            )
        }
        for edit in edits:
            symbolic = edit.symbolic_patch
            offset, expected, template = accepted_hooks[symbolic.symbol]
            self.assertEqual(symbolic.offset, offset)
            self.assertEqual(symbolic.expected, expected)
            self.assertEqual(symbolic.replacement_template, template)
            self.assertEqual(symbolic.encoding, "j26")
            self.assertEqual(symbolic.relocation_offset, 0)

            replacement = resolved[symbolic.mapping_id].replacement
            self.assertEqual(replacement[4:], template[4:])
            self.assertEqual(int.from_bytes(replacement[:4], "little") >> 26, 0x02)

    def test_character_modal_rows_share_centered_box_and_structural_y(self) -> None:
        fragments = {
            fragment.symbol: fragment for fragment in self.package.fragments
        }
        accepted_coordinates = (
            0x41000000,  # shared box X and first-row Y: 8
            0x42000000,  # 32
            0x42600000,  # 56
            0x42A00000,  # 80
            0x42E40000,  # shared footer Y: 114
        )
        for symbol in (
            "v2_character_selected_adapter",
            "v2_character_unselected_adapter",
        ):
            payload_words = words(fragments[symbol].payload)
            missing = tuple(
                value
                for value in accepted_coordinates
                if not loads_u32(payload_words, value)
            )
            self.assertEqual(
                missing,
                (),
                f"{symbol} lost the centered Character-modal contract",
            )
    def test_pause_selected_hook_targets_c_without_forwarding_wrapper(self) -> None:
        hook_symbols = {
            edit.symbolic_patch.symbol for edit in self.package.active_edits
        }
        self.assertIn("v2_c_pause_list_selected_impl", hook_symbols)
        self.assertNotIn("v2_pause_list_selected_adapter", hook_symbols)

        fragment_symbols = {
            fragment.symbol for fragment in self.package.fragments
        }
        self.assertNotIn("v2_pause_list_selected_adapter", fragment_symbols)

    def test_command_relationship_uses_live_nun5_wrap_width(self) -> None:
        fragments = {
            fragment.symbol: fragment for fragment in self.package.fragments
        }
        relationship = words(
            fragments["v2_c_command_relationship_impl"].payload
        )
        self.assertIn(mips.i_type(0x09, 0, 5, 272), relationship)
        self.assertIn(mips.i_type(0x09, 0, 2, 272), relationship)

        widths = build_ascii_widths()

        def measure(text: str) -> int:
            return sum(
                widths[ord(character) - ASCII_FIRST]
                for character in text
            )

        def wrap(text: str) -> list[str]:
            lines: list[str] = []
            current = ""
            for word in text.split(" "):
                candidate = f"{current} {word}" if current else word
                if current and measure(candidate) > 272:
                    lines.append(current)
                    current = word
                else:
                    current = candidate
            lines.append(current)
            return lines

        self.assertEqual(
            wrap("Consume Chakra/Charge/Jump OK"),
            ["Consume Chakra/Charge/Jump", "OK"],
        )
        self.assertEqual(
            wrap("Chakra Gauge 1+/Nor. Ultimate Jutsu"),
            ["Chakra Gauge 1+/Nor.", "Ultimate Jutsu"],
        )
        self.assertEqual(
            wrap("Chakra Gauge 2+/Awk. Ultimate Jutsu"),
            ["Chakra Gauge 2+/Awk.", "Ultimate Jutsu"],
        )
        self.assertEqual(
            wrap("Chakra Gauge 3/Rev. Ultimate Jutsu"),
            ["Chakra Gauge 3/Rev. Ultimate", "Jutsu"],
        )

    def test_title_fit_preserves_nun5_quote_delimiter_width(self) -> None:
        fragments = {
            fragment.symbol: fragment for fragment in self.package.fragments
        }
        measure = words(fragments["v2_measure"].payload)
        title = words(fragments["v2_title_adapter"].payload)
        self.assertTrue(
            any(
                word >> 26 == 0x0C and word & 0xFFFF == 0x100
                for word in measure
            ),
            "v2 measurement must test the NUN5 quote-width flag",
        )
        self.assertTrue(
            any(
                word >> 26 in {0x09, 0x0D} and word & 0xFFFF == 0x301
                for word in title
            ),
            "the shared title adapter must request shrink, NUN5 quote width, "
            "and color-tag measurement",
        )
        self.assertTrue(
            any(
                word >> 26 == 0x0C and word & 0xFFFF == 0x200
                for word in measure
            ),
            "v2 measurement must test the color-tag flag",
        )

        widths = build_ascii_widths()
        self.assertEqual(widths[ord('"') - ASCII_FIRST], 9)
        self.assertEqual(widths[ord("@") - ASCII_FIRST], 14)

        title_text = 'Ninja Art: Beast Scroll Replicas "Wild Dog" '
        ordinary_width = sum(
            widths[ord(character) - ASCII_FIRST]
            for character in title_text
        )
        nun5_width = sum(
            widths[ord("@" if character == '"' else character) - ASCII_FIRST]
            for character in title_text
        )
        self.assertEqual(ordinary_width, 391)
        self.assertEqual(nun5_width, 401)

    def test_command_title_ignores_only_the_terminal_nun5_lf(self) -> None:
        fragments = {
            fragment.symbol: fragment for fragment in self.package.fragments
        }
        command = words(fragments["v2_command_title_entry"].payload)
        self.assertTrue(
            any(
                word >> 26 == 0x0B and word & 0xFFFF == 0xFF
                for word in command
            ),
            "the Command title copy must remain bounded to 255 text bytes",
        )
        self.assertTrue(
            any(
                word >> 26 == 0x0E and word & 0xFFFF == 0x0A
                for word in command
            ),
            "the Command title entry must test its final byte for LF",
        )
        self.assertTrue(
            any(
                word >> 26 == 0x28 and (word >> 16) & 0x1F == 0
                for word in command
            ),
            "the transient Command title copy must receive a NUL terminator",
        )

        mapping_path = PATHS.path(
            "builder", "localization", "translation_importer", "mappings.tsv"
        )
        with mapping_path.open("r", encoding="utf-8-sig", newline="") as handle:
            mapping = next(
                row
                for row in csv.DictReader(handle, delimiter="\t")
                if row["id"] == "T1486"
            )
        self.assertEqual(mapping["donor_ref"], "NUN5_TEXTENG@0xB9A0")
        self.assertEqual(mapping["donor"], "Air Strike Palm\n")
        self.assertEqual(mapping["replacement"], "")


if __name__ == "__main__":
    unittest.main()
