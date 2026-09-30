from __future__ import annotations

import json
import struct
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from na228_builder.infrastructure.orchestration import catalog
from na228_builder.patches.localization.mod_strings import ModStrings
from na228_builder.patches.settings.ingame.battle_mode.battle_settings import (
    _active_pages,
    battle_settings_fragment,
)
from scripts.lib.paths import load_local_paths
from na228_builder.patches.settings.ingame.shared.menu_options import MenuOption
from na228_builder.patches.settings.ingame.shared.menu_pages import page_resource_fragments
from tests.na228_builder._fixtures import test_features


class BattleSettingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.paths = load_local_paths(Path(__file__).resolve(), allow_missing=True)
        cls.repository = cls.paths.repository
        cls.builder = cls.paths.path("builder")
        cls.catalog_path = cls.builder / "catalog.modcat"
        directory = tempfile.TemporaryDirectory()
        cls.addClassCleanup(directory.cleanup)
        configuration = Path(directory.name) / "configuration.jsonc"
        configuration.write_text(
            json.dumps({"features": test_features()}), encoding="utf-8"
        )
        cls.selection = catalog.load_selection(
            cls.catalog_path,
            configuration,
        )

    def _selection(self, mutate) -> catalog.CatalogSelection:
        base = {"features": test_features()}
        mutate(base["features"])
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "configuration.jsonc"
        path.write_text(json.dumps(base, indent=2) + "\n", encoding="utf-8")
        return catalog.load_selection(self.catalog_path, path)

    def test_base_schema_links_runtime_providers_and_help(self) -> None:
        fragment = battle_settings_fragment(
            self.selection,
            owner="settings.runtime_injector",
        )
        self.assertIsNotNone(fragment)
        assert fragment is not None
        relocation_symbols = {item.symbol for item in fragment.relocations}
        self.assertTrue(
            {
                "substitution_gauge_mode_get",
                "ultimate_jutsu_mode_get",
                "shadowblur_get",
                "extra_hit_get",
                "substitution_input_get",
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

    def test_japanese_uses_the_native_help_setter(self) -> None:
        selection = self._selection(
            lambda features: features.__setitem__("localization", "jp")
        )
        fragment = battle_settings_fragment(
            selection,
            owner="settings.runtime_injector",
        )
        self.assertIsNotNone(fragment)
        assert fragment is not None
        self.assertNotIn(
            "v2_help_set",
            {item.symbol for item in fragment.relocations},
        )
        self.assertEqual(struct.unpack_from("<I", fragment.payload, 80)[0], 0x0037F760)

    def test_shared_defaults_drive_the_selectable_values(self) -> None:
        def configure(features) -> None:
            mechanics = features["default_settings"]["battle_mechanics"]
            mechanics["ultimate_jutsu"] = "no_contest"
            mechanics["shadowblur"] = "on"
            mechanics["extra_hit"] = "on"
            mechanics["substitution_input"] = 15
            mechanics["xdash_chakra_cost"] = 100
            mechanics["support"] = "normal"
            mechanics["substitution_resource"]["value"] = "free"

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
            {6: 2, 9: 16, 10: 20, 11: 2, 4: 6, 7: 1, 8: 1},
        )

    def test_disabling_battle_mechanics_launcher_keeps_native_root_rows(self) -> None:
        selection = self._selection(
            lambda features: features["menu_composition"]["battle_settings"].__setitem__(
                "battle_mechanics", False
            )
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

    def test_select_reset_rejoins_the_native_sound_path(self) -> None:
        manifest = json.loads(
            (self.builder / "patches/settings/settings.json").read_text(encoding="utf-8")
        )
        edit = manifest["settings.ingame"]["edits"]["skip_native_battle_select_defaults"]
        self.assertEqual(int(edit["destination_offset"], 16), 0x1CBD08)
        jump, delay_slot = struct.unpack("<II", bytes.fromhex(edit["replacement_hex"]))
        self.assertEqual(jump >> 26, 2)
        self.assertEqual((jump & 0x03FFFFFF) << 2, 0x0087FC70)
        self.assertEqual(delay_slot, 0)

    def test_config_key_order_controls_root_and_battle_mechanics_pages(self) -> None:
        def configure(features) -> None:
            settings = features["default_settings"]
            battle = settings["battle_settings"]
            settings["battle_settings"] = {
                key: battle[key]
                for key in (
                    "handicap",
                    "difficulty",
                    "time",
                )
            }
            mechanics = settings["battle_mechanics"]
            settings["battle_mechanics"] = {
                key: mechanics[key]
                for key in (
                    "items",
                    "substitution_resource",
                    "support",
                    "xdash_chakra_cost",
                    "substitution_input",
                    "extra_hit",
                    "shadowblur",
                    "ultimate_jutsu",
                    "chakra",
                )
            }

        pages = _active_pages(self._selection(configure))
        self.assertEqual(
            [ModStrings(self.selection).resolve(row.label) if row.label else row.row_id
             for row in pages[0].rows],
            ["Battle Mechanics", 5, 1, 0],
        )
        self.assertEqual(
            [row.row_id for row in pages[1].rows],
            [2, 6, 11, 10, 9, 8, 7, 4, 3],
        )

    def test_dependent_option_keeps_its_controller_when_rows_move(self) -> None:
        controller = MenuOption(None, None, ("off", "on"), 1, "get", "set", 2)
        dependent = MenuOption(None, None, ("low", "high"), 0, "get", "set", 3,
                               enabled_by=("get", 2))
        for options in ((controller, dependent), (dependent, controller)):
            with self.subTest(controller_index=options.index(controller)):
                page = SimpleNamespace(
                    heading_text=None,
                    reset_symbol="menu_reset",
                    reset_text="Defaults restored.",
                    rows=tuple(SimpleNamespace(runtime_option=option) for option in options),
                )
                fragments = page_resource_fragments((page,), "settings", "menu", self.selection)
                by_symbol = {fragment.symbol: fragment for fragment in fragments}
                dependent_fragment = by_symbol[f"menu_option_{options.index(dependent)}"]
                controller_fragment = by_symbol[f"menu_option_{options.index(controller)}"]
                link = next(relocation for relocation in dependent_fragment.relocations
                            if relocation.offset == 16)
                self.assertEqual(link.symbol, controller_fragment.symbol)

    def test_handicap_text_values(self) -> None:
        values = ModStrings(self.selection).native_payload(
            "mod_number_handicap"
        ).rstrip(b"\0").split(b"\0")
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

if __name__ == "__main__":
    unittest.main()
