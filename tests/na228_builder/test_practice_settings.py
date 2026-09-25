from __future__ import annotations

import json
import struct
import tempfile
import unittest
from pathlib import Path

from na228_builder.infrastructure.orchestration import catalog, jsonc
from na228_builder.patches.localization.mod_strings import ModStrings
from na228_builder.patches.settings.ingame.practice_mode.practice_settings import (
    _active_pages,
    practice_settings_fragment,
    practice_settings_table_fragments,
)
from scripts.lib.paths import load_local_paths


class PracticeSettingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.paths = load_local_paths(Path(__file__).resolve(), allow_missing=True)
        cls.repository = cls.paths.repository
        cls.builder = cls.paths.path("builder")
        cls.catalog_path = cls.builder / "catalog.modcat"
        cls.configurations = cls.builder / "configurations"
        cls.selection = catalog.load_selection(
            cls.catalog_path,
            cls.configurations / "base.jsonc",
        )

    def _selection(self, mutate) -> catalog.CatalogSelection:
        base = jsonc.loads(
            (self.configurations / "base.jsonc").read_text(encoding="utf-8")
        )
        mutate(base["features"])
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "configuration.jsonc"
        path.write_text(json.dumps(base, indent=2) + "\n", encoding="utf-8")
        return catalog.load_selection(self.catalog_path, path)

    def test_base_schema_links_runtime_providers_and_help(self) -> None:
        fragment = practice_settings_fragment(
            self.selection,
            owner="settings.runtime_injector",
        )
        self.assertIsNotNone(fragment)
        assert fragment is not None
        row_count, page_count, active_page = struct.unpack_from(
            "<3I", fragment.payload
        )
        pages = _active_pages(self.selection)
        self.assertEqual(row_count, sum(len(page.rows) for page in pages))
        self.assertEqual(page_count, len(pages))
        self.assertEqual(active_page, 0)

        relocation_symbols = {item.symbol for item in fragment.relocations}
        self.assertTrue(
            {
                "substitution_gauge_mode_get",
                "ultimate_jutsu_mode_get",
                "shadowblur_get",
                "extra_hit_get",
                "sub_active_frames_get",
                "xdash_chakra_cost_option_get",
                "support_get",
                "v2_help_set",
            }.issubset(relocation_symbols)
        )
        help_relocations = [
            item for item in fragment.relocations if item.symbol == "v2_help_set"
        ]
        self.assertEqual(
            [(item.offset, item.kind) for item in help_relocations],
            [(80, "abs32")],
        )

    def test_configured_defaults_use_native_enum_values(self) -> None:
        def configure(features) -> None:
            practice = features["default_settings"]["practice_settings"]
            practice["health"] = "almost"
            practice["commands"] = "on"
            practice["damage"] = "on"
            practice["opponent_settings"]["status"] = "com"
            practice["opponent_settings"]["linked_attack"] = "random"
            practice["opponent_settings"]["extra_hit_counter"] = "return"

        selection = self._selection(configure)
        fragment = practice_settings_fragment(
            selection,
            owner="settings.runtime_injector",
        )
        self.assertIsNotNone(fragment)
        assert fragment is not None
        defaults = {
            row.row_id: row.default_value
            for page in _active_pages(selection)
            for row in page.rows
        }
        self.assertEqual(defaults[0], 2)
        self.assertEqual(defaults[6], 1)
        self.assertEqual(defaults[7], 1)
        self.assertEqual(defaults[15], 2)
        self.assertEqual(defaults[16], 1)

    def test_disabling_battle_mechanics_launcher_keeps_native_and_opponent_rows(self) -> None:
        selection = self._selection(
            lambda features: features["menu_composition"]["practice_settings"].__setitem__(
                "battle_mechanics", False
            )
        )
        fragment = practice_settings_fragment(
            selection,
            owner="settings.runtime_injector",
        )
        self.assertIsNotNone(fragment)
        assert fragment is not None
        pages = _active_pages(selection)
        self.assertEqual(len(pages), 2)
        self.assertEqual(ModStrings(selection).resolve(pages[0].rows[0].label), "Opponent Settings")
        self.assertEqual(
            [row.row_id for row in pages[0].rows[1:]],
            [0, 6, 7],
        )
        self.assertEqual([row.row_id for row in pages[1].rows], list(range(9, 17)))
        self.assertEqual(struct.unpack_from("<2I", fragment.payload), (12, 2))

    def test_runtime_tables_match_the_generated_schema_size(self) -> None:
        fragment = practice_settings_fragment(
            self.selection,
            owner="settings.runtime_injector",
        )
        self.assertIsNotNone(fragment)
        assert fragment is not None
        largest_page = max(len(page.rows) for page in _active_pages(self.selection))
        tables = practice_settings_table_fragments(
            self.selection,
            owner="settings.runtime_injector",
        )
        by_symbol = {
            table.symbol: (table.kind, len(table.payload))
            for table in tables
        }
        self.assertEqual(
            by_symbol["practice_settings_active_labels"],
            ("data", largest_page * 4),
        )
        self.assertEqual(
            by_symbol["practice_settings_active_value_tables"],
            ("data", largest_page * 4),
        )
        self.assertIn("practice_settings_schema_page_1_heading", by_symbol)
        self.assertTrue(
            any(symbol.startswith("practice_settings_schema_option_") for symbol in by_symbol)
        )

    def test_scroll_flag_bridge_can_skip_the_native_up_arrow(self) -> None:
        injection = self.selection.injections["settings.ingame"]
        source = injection["payload"]["settings_menu_presentation_abi"]
        compiled = {
            fragment.symbol: fragment
            for fragment in catalog._compile_source(
                self.repository,
                "settings.runtime_injector",
                "settings_menu_presentation_abi",
                source,
                "settings_menu_presentation_abi",
            )
        }
        bridge = compiled["settings_menu_scroll_flags_bridge"]
        self.assertTrue(
            bridge.payload.hex().upper().endswith(
                "8800193C802039370800200300000000"
                "8800193CFC2039370800200300000000"
            )
        )


if __name__ == "__main__":
    unittest.main()
