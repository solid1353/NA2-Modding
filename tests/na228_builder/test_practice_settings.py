from __future__ import annotations

import json
import struct
import tempfile
import unittest
from pathlib import Path

from na228_builder.scripts import catalog, jsonc
from na228_builder.scripts.practice_settings import (
    ROW_SIZE,
    SCHEMA_HEADER_SIZE,
    practice_settings_fragment,
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

    @staticmethod
    def _rows(fragment) -> list[tuple[int, ...]]:
        row_count = struct.unpack_from("<I", fragment.payload)[0]
        return [
            struct.unpack_from(
                "<10I",
                fragment.payload,
                SCHEMA_HEADER_SIZE + index * ROW_SIZE,
            )
            for index in range(row_count)
        ]

    def test_base_schema_includes_every_shared_selector(self) -> None:
        fragment = practice_settings_fragment(
            self.selection,
            owner="settings.runtime_injector",
        )
        self.assertIsNotNone(fragment)
        assert fragment is not None
        row_count, player_count, opponent_count = struct.unpack_from(
            "<3I", fragment.payload
        )
        self.assertEqual((row_count, player_count, opponent_count), (20, 13, 7))
        self.assertEqual(
            struct.unpack_from("<4B", fragment.payload, 12),
            (0, 0, 0, 0),
        )

        rows = self._rows(fragment)
        self.assertEqual(
            [row[0] for row in rows],
            [
                0,
                1,
                2,
                5,
                6,
                7,
                3,
                18,
                19,
                20,
                21,
                22,
                17,
                9,
                10,
                11,
                12,
                13,
                14,
                15,
            ],
        )
        by_id = {row[0]: row for row in rows}
        self.assertEqual((by_id[17][6], by_id[17][7]), (3, 1))
        self.assertEqual((by_id[20][6], by_id[20][7]), (17, 4))
        self.assertEqual((by_id[21][6], by_id[21][7]), (21, 1))
        self.assertEqual((by_id[22][6], by_id[22][7]), (2, 0))
        self.assertEqual((by_id[3][6], by_id[3][7]), (8, 7))

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

    def test_configured_defaults_use_native_enum_values(self) -> None:
        selection = self._selection(
            lambda features: features["settings"]["in_game"].__setitem__(
                "practice",
                {
                    "general_settings": {
                        "health": "almost",
                        "chakra": "unlimited",
                        "linked_attack": "normal",
                        "linked_mode": False,
                        "items": "normal",
                        "commands": "on",
                        "damage": "on",
                        "guide_ninja_sound": "on",
                    },
                    "opponent_settings": {
                        "status": "com",
                        "strength": "normal",
                        "attack": "no",
                        "guard": "no",
                        "move": "stay",
                        "substitution_jutsu": "normal",
                        "linked_attack": "random",
                        "extra_hit_counter": False,
                    },
                },
            )
        )
        fragment = practice_settings_fragment(
            selection,
            owner="settings.runtime_injector",
        )
        self.assertIsNotNone(fragment)
        assert fragment is not None
        defaults = {row[0]: row[7] for row in self._rows(fragment)}
        self.assertEqual(defaults[0], 2)
        self.assertEqual(defaults[6], 1)
        self.assertEqual(defaults[8], 1)
        self.assertEqual(defaults[15], 2)

    def test_disabling_shared_settings_keeps_the_native_practice_rows(self) -> None:
        selection = self._selection(
            lambda features: features["settings"]["in_game"].__setitem__(
                "shared", False
            )
        )
        fragment = practice_settings_fragment(
            selection,
            owner="settings.runtime_injector",
        )
        self.assertIsNotNone(fragment)
        assert fragment is not None
        rows = self._rows(fragment)
        self.assertEqual(
            [row[0] for row in rows],
            [0, 1, 2, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15],
        )
        self.assertEqual(struct.unpack_from("<3I", fragment.payload), (13, 6, 7))
        self.assertEqual(fragment.relocations, ())

    def test_backing_repeats_for_every_player_row_beyond_native_capacity(self) -> None:
        injection = self.selection.injections["settings.in_game"]
        self.assertEqual(
            injection["hooks"]["practice_draw_compact_backing"],
            {
                "description": (
                    "Run the native backing renderer and repeat the final "
                    "native player-row backing for each compact row beyond "
                    "the animation's nine-row capacity."
                ),
                "target_id": "na2_btl",
                "offset": "0x1CE4D0",
                "expected_hex": "E4ED060C",
                "symbol": "practice_settings_draw_backing",
                "encoding": "jal26",
            },
        )
        source = injection["payload"]["practice_settings"]
        compiled = {
            fragment.symbol: fragment
            for fragment in catalog._compile_source(
                self.repository,
                "settings.runtime_injector",
                "practice_settings",
                source,
                "practice_settings",
            )
        }
        self.assertIn("practice_settings_backing_layout", compiled)
        self.assertIn("practice_settings_prepare_backing_and_compose", compiled)
        self.assertIn("practice_settings_draw_backing", compiled)

    def test_scroll_flag_bridge_can_skip_the_native_up_arrow(self) -> None:
        injection = self.selection.injections["settings.in_game"]
        source = injection["payload"]["practice_settings_abi"]
        compiled = {
            fragment.symbol: fragment
            for fragment in catalog._compile_source(
                self.repository,
                "settings.runtime_injector",
                "practice_settings_abi",
                source,
                "practice_settings_abi",
            )
        }
        bridge = compiled["practice_settings_scroll_flags_bridge"]
        self.assertTrue(
            bridge.payload.hex().upper().endswith(
                "8800193C802039370800200300000000"
                "8800193CFC2039370800200300000000"
            )
        )


if __name__ == "__main__":
    unittest.main()
