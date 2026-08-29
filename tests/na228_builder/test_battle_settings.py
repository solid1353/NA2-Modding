from __future__ import annotations

import json
import struct
import tempfile
import unittest
from pathlib import Path

from na228_builder.scripts import catalog
from na228_builder.scripts.battle_settings import (
    ROW_SIZE,
    SCHEMA_HEADER_SIZE,
    battle_settings_fragment,
)
from scripts.lib.paths import load_local_paths


class BattleSettingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.paths = load_local_paths(Path(__file__).resolve(), allow_missing=True)
        cls.repository = cls.paths.repository
        cls.builder = cls.paths.path("builder")
        cls.catalog_path = cls.builder / "catalog"
        cls.configurations = cls.builder / "configurations"
        cls.selection = catalog.load_selection(
            cls.catalog_path,
            cls.configurations / "base.json",
        )

    def _selection(self, mutate) -> catalog.CatalogSelection:
        base = json.loads(
            (self.configurations / "base.json").read_text(encoding="utf-8")
        )
        mutate(base["features"])
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "configuration.json"
        path.write_text(json.dumps(base, indent=2) + "\n", encoding="utf-8")
        return catalog.load_selection(self.catalog_path, path)

    @staticmethod
    def _rows(fragment) -> list[tuple[int, ...]]:
        row_count = struct.unpack_from("<I", fragment.payload)[0]
        return [
            struct.unpack_from(
                "<8I",
                fragment.payload,
                SCHEMA_HEADER_SIZE + index * ROW_SIZE,
            )
            for index in range(row_count)
        ]

    def test_base_schema_includes_every_shared_selector_before_handicap(self) -> None:
        fragment = battle_settings_fragment(
            self.selection,
            owner="settings.runtime_injector",
        )
        self.assertIsNotNone(fragment)
        assert fragment is not None
        rows = self._rows(fragment)
        self.assertEqual(
            [row[0] for row in rows],
            [0, 1, 2, 3, 6, 9, 10, 11, 4, 7, 8, 5],
        )
        by_id = {row[0]: row for row in rows}
        self.assertEqual((by_id[6][5], by_id[6][6]), (3, 1))
        self.assertEqual((by_id[9][5], by_id[9][6]), (17, 4))
        self.assertEqual((by_id[10][5], by_id[10][6]), (21, 1))
        self.assertEqual((by_id[11][5], by_id[11][6]), (2, 0))
        self.assertEqual((by_id[4][5], by_id[4][6]), (8, 7))
        self.assertEqual((by_id[5][5], by_id[5][6]), (11, 0))

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
            shared = features["settings"]["shared"]
            shared["ultimate_jutsu"] = "no_contest"
            shared["shadowblur"] = "on"
            shared["extra_hit"] = "on"
            shared["sub_active_frames"] = 16
            shared["xdash_chakra_cost"] = 100
            shared["support"] = "on"
            shared["substitution"]["default"] = "free"

        fragment = battle_settings_fragment(
            self._selection(configure),
            owner="settings.runtime_injector",
        )
        self.assertIsNotNone(fragment)
        assert fragment is not None
        defaults = {row[0]: row[6] for row in self._rows(fragment)}
        self.assertEqual(
            {row_id: defaults[row_id] for row_id in (6, 9, 10, 11, 4, 7, 8)},
            {6: 2, 9: 16, 10: 20, 11: 1, 4: 6, 7: 1, 8: 1},
        )

    def test_disabling_shared_settings_removes_the_extended_battle_schema(self) -> None:
        selection = self._selection(
            lambda features: features["settings"].__setitem__("shared", False)
        )
        self.assertIsNone(
            battle_settings_fragment(
                selection,
                owner="settings.runtime_injector",
            )
        )

    def test_handicap_is_an_ordinary_final_row_with_text_values(self) -> None:
        injection = self.selection.injections["i__battle__settings_rework"]
        self.assertEqual(
            injection["hooks"]["draw_all_rows_as_ordinary"]["symbol"],
            "battle_settings_draw_ordinary_bridge",
        )
        self.assertEqual(
            injection["hooks"]["select_ordinary_cursor_object"]["symbol"],
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
        injection = self.selection.injections["i__battle__settings_rework"]
        hooks = injection["hooks"]
        self.assertEqual(hooks["draw_seven_label_rows"]["symbol"], "battle_settings_label_loop_bridge")
        self.assertEqual(hooks["draw_seven_value_rows"]["symbol"], "battle_settings_value_loop_bridge")
        self.assertEqual(hooks["draw_visible_rows"]["symbol"], "battle_settings_draw_rows")
        self.assertEqual(hooks["draw_visible_cursor"]["symbol"], "battle_settings_draw_cursor")

    def test_sources_compile_with_the_selected_runtime_package(self) -> None:
        injection = self.selection.injections["i__battle__settings_rework"]
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
