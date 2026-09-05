from __future__ import annotations

import json
import struct
import tempfile
import unittest
from pathlib import Path

from na228_builder.scripts import catalog, jsonc
from na228_builder.scripts.battle_settings import (
    _active_pages,
    battle_settings_fragment,
)
from scripts.lib.paths import load_local_paths


class BattleSettingsTests(unittest.TestCase):
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

    def test_base_schema_follows_configured_page_order(self) -> None:
        fragment = battle_settings_fragment(
            self.selection,
            owner="settings.runtime_injector",
        )
        self.assertIsNotNone(fragment)
        assert fragment is not None
        pages = _active_pages(self.selection)
        self.assertEqual(len(pages), 5)
        self.assertEqual(pages[0].rows[0].label, "Battle Mechanics")
        self.assertEqual(
            [row.row_id for row in pages[0].rows[1:]],
            [0, 1, 5],
        )
        self.assertEqual(
            [row.row_id for row in pages[1].rows],
            [3, 4, 7, 8, 9, 10, 11, 6, 2],
        )
        self.assertEqual(
            [page.heading_text for page in pages[1:]],
            ["Battle Mechanics", "Chakra Settings", "Gauge Settings", "Items Settings"],
        )
        by_id = {row.row_id: row for page in pages for row in page.rows}
        self.assertEqual((by_id[6].option_count, by_id[6].default_value), (3, 1))
        self.assertEqual((by_id[9].option_count, by_id[9].default_value), (16, 5))
        self.assertEqual((by_id[10].option_count, by_id[10].default_value), (21, 1))
        self.assertEqual((by_id[11].option_count, by_id[11].default_value), (4, 0))
        self.assertEqual((by_id[4].option_count, by_id[4].default_value), (8, 7))
        self.assertEqual((by_id[5].option_count, by_id[5].default_value), (11, 0))

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
            }.issubset(relocation_symbols)
        )

    def test_shared_defaults_drive_the_selectable_values(self) -> None:
        def configure(features) -> None:
            mechanics = features["settings"]["ingame"]["battle_mechanics"]
            mechanics["ultimate_jutsu"] = "no_contest"
            mechanics["shadowblur"] = "on"
            mechanics["extra_hit"] = "on"
            mechanics["sub_active_frames"] = 15
            mechanics["xdash_chakra_cost"] = 100
            mechanics["support"] = "normal"
            mechanics["substitution"]["value"] = "free"

        selection = self._selection(configure)
        fragment = battle_settings_fragment(
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
        self.assertEqual(
            {row_id: defaults[row_id] for row_id in (6, 9, 10, 11, 4, 7, 8)},
            {6: 2, 9: 15, 10: 20, 11: 2, 4: 6, 7: 1, 8: 1},
        )

    def test_disabling_battle_mechanics_launcher_keeps_native_root_rows(self) -> None:
        selection = self._selection(
            lambda features: features["settings"]["ingame"][
                "battle_mode"
            ].__setitem__("battle_mechanics", False)
        )
        fragment = battle_settings_fragment(
            selection,
            owner="settings.runtime_injector",
        )
        self.assertIsNotNone(fragment)
        assert fragment is not None
        pages = _active_pages(selection)
        self.assertEqual(len(pages), 1)
        self.assertEqual([row.row_id for row in pages[0].rows], [0, 1, 5])

    def test_config_key_order_controls_root_and_battle_mechanics_pages(self) -> None:
        def configure(features) -> None:
            ingame = features["settings"]["ingame"]
            battle = ingame["battle_mode"]
            ingame["battle_mode"] = {
                key: battle[key]
                for key in ("handicap", "difficulty", "battle_mechanics", "time")
            }
            mechanics = ingame["battle_mechanics"]
            ingame["battle_mechanics"] = {
                key: mechanics[key]
                for key in (
                    "items",
                    "substitution",
                    "support",
                    "xdash_chakra_cost",
                    "sub_active_frames",
                    "extra_hit",
                    "shadowblur",
                    "ultimate_jutsu",
                    "chakra",
                )
            }

        pages = _active_pages(self._selection(configure))
        self.assertEqual(
            [row.label or row.row_id for row in pages[0].rows],
            [5, 1, "Battle Mechanics", 0],
        )
        self.assertEqual(
            [row.row_id for row in pages[1].rows],
            [2, 6, 11, 10, 9, 8, 7, 4, 3],
        )

    def test_handicap_is_an_ordinary_final_row_with_text_values(self) -> None:
        injection = self.selection.injections["settings.ingame"]
        self.assertEqual(
            injection["hooks"]["battle_route_visible_handicap_draw"]["symbol"],
            "battle_settings_draw_ordinary_bridge",
        )
        self.assertEqual(
            injection["hooks"]["battle_select_page_appropriate_cursor"]["symbol"],
            "battle_settings_cursor_ordinary_bridge",
        )
        source = injection["payload"]["battle_settings"]
        compiled = {
            fragment.symbol: fragment
            for fragment in catalog._compile_source(
                self.repository,
                "settings.runtime_injector",
                "battle_settings",
                source,
                "battle_settings",
            )
        }
        values = compiled["battle_settings_handicap_text"].payload.rstrip(
            b"\0"
        ).split(b"\0")
        self.assertEqual(
            values,
            [
                b"0-10",
                b"1-9",
                b"2-8",
                b"3-7",
                b"4-6",
                b"5-5",
                b"6-4",
                b"7-3",
                b"8-2",
                b"9-1",
                b"10-0",
            ],
        )

    def test_scrolling_uses_seven_physical_rows_for_any_logical_count(self) -> None:
        injection = self.selection.injections["settings.ingame"]
        hooks = injection["hooks"]
        self.assertEqual(hooks["battle_draw_visible_label_rows"]["symbol"], "battle_settings_label_loop_bridge")
        self.assertEqual(hooks["battle_draw_visible_value_rows"]["symbol"], "battle_settings_value_loop_bridge")
        self.assertEqual(hooks["battle_draw_visible_rows"]["symbol"], "battle_settings_draw_rows")
        self.assertEqual(hooks["battle_draw_visible_cursor"]["symbol"], "battle_settings_draw_cursor")

    def test_sources_compile_with_the_selected_runtime_package(self) -> None:
        injection = self.selection.injections["settings.ingame"]
        c_fragments = catalog._compile_source(
            self.repository,
            "settings.runtime_injector",
            "battle_settings",
            injection["payload"]["battle_settings"],
            "battle_settings",
        )
        asm_fragments = catalog._compile_source(
            self.repository,
            "settings.runtime_injector",
            "battle_settings_abi",
            injection["payload"]["battle_settings_abi"],
            "battle_settings_abi",
        )
        self.assertIn(
            "battle_settings_draw_backing",
            {fragment.symbol for fragment in c_fragments},
        )
        self.assertIn(
            "battle_settings_value_loop_bridge",
            {fragment.symbol for fragment in asm_fragments},
        )


if __name__ == "__main__":
    unittest.main()
