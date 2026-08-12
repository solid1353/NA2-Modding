"""Specific accepted ABI and instruction contracts in the release font package."""

from __future__ import annotations

import unittest
from pathlib import Path

from na228_builder.payload_builder import build_resident_payload
from na228_builder.scripts import catalog
from na228_builder.scripts.composer import resolve_symbolic_patches
from tests.na228_builder._fixtures import resident_payload_config


REPOSITORY = Path(__file__).resolve().parents[3]


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


class FontRuntimeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        builder = REPOSITORY / "na228_builder"
        selection = catalog.load_selection(
            builder / "catalog",
            builder / "configurations" / "release.json",
        )
        cls.package = catalog.load_runtime_package(
            selection,
            "localization",
            builder / "catalog" / "implementation" / "targets.tsv",
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
        self.assertTrue(is_register_move(practice[2], source=19, destination=7))
        self.assertTrue(is_register_move(practice[3], source=18, destination=8))
        mfc1 = practice[4]
        self.assertEqual(mfc1 >> 26, 0x11)
        self.assertEqual((mfc1 >> 21) & 0x1F, 0)
        self.assertEqual((mfc1 >> 16) & 0x1F, 9)
        self.assertEqual((mfc1 >> 11) & 0x1F, 12)


if __name__ == "__main__":
    unittest.main()
