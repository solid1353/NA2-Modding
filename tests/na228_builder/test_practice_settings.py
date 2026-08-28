from __future__ import annotations

import json
import struct
import tempfile
import unittest
from pathlib import Path

from na228_builder.scripts import catalog
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
        cls.selection = catalog.load_selection(
            cls.builder / "catalog",
            cls.builder / "configurations" / "base.json",
        )

    def test_base_schema_compacts_enabled_rows_without_empty_slots(self) -> None:
        fragment = practice_settings_fragment(
            self.selection,
            owner="battle.runtime_injector",
        )
        self.assertIsNotNone(fragment)
        assert fragment is not None
        (
            row_count,
            player_count,
            opponent_count,
            health,
            commands,
            guide_ninja_sound,
            linked_attack,
        ) = struct.unpack_from("<3I4B", fragment.payload)
        self.assertEqual((row_count, player_count, opponent_count), (13, 7, 6))
        self.assertEqual(
            (
                health,
                commands,
                guide_ninja_sound,
                linked_attack,
            ),
            (0, 0, 0, 0),
        )
        self.assertEqual(
            [
                struct.unpack_from(
                    "<I",
                    fragment.payload,
                    SCHEMA_HEADER_SIZE + index * ROW_SIZE,
                )[0]
                for index in range(row_count)
            ],
            [0, 1, 17, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14],
        )
        substitution = struct.unpack_from(
            "<10I",
            fragment.payload,
            SCHEMA_HEADER_SIZE + 2 * ROW_SIZE,
        )
        self.assertEqual(substitution[6:8], (3, 1))
        self.assertEqual(
            [relocation.symbol for relocation in fragment.relocations],
            [
                "substitution_gauge_mode_get",
                "substitution_gauge_mode_set",
                "practice_settings_substitution_label",
                "practice_settings_substitution_help",
                "practice_settings_schema",
                "substitution_gauge_mode_chakra_label",
                "substitution_gauge_mode_gauge_label",
                "substitution_gauge_mode_free_label",
            ],
        )

    def test_omitted_defaults_preserve_native_values(self) -> None:
        base = json.loads(
            (self.builder / "configurations" / "base.json").read_text(
                encoding="utf-8"
            )
        )
        base["features"]["practice"]["settings_rework"] = {}
        with tempfile.TemporaryDirectory() as directory:
            configuration = Path(directory) / "configuration.json"
            configuration.write_text(json.dumps(base), encoding="utf-8")
            selection = catalog.load_selection(
                self.builder / "catalog", configuration
            )
            fragment = practice_settings_fragment(
                selection,
                owner="battle.runtime_injector",
            )

        self.assertIsNotNone(fragment)
        assert fragment is not None
        self.assertEqual(
            struct.unpack_from("<4B", fragment.payload, 12),
            (255,) * 4,
        )

    def test_configured_defaults_use_native_enum_values(self) -> None:
        base = json.loads(
            (self.builder / "configurations" / "base.json").read_text(
                encoding="utf-8"
            )
        )
        base["features"]["practice"]["settings_rework"] = {
            "health": "critical",
            "commands": "on",
            "guide_ninja_sound": "on",
            "linked_attack": "random",
        }
        with tempfile.TemporaryDirectory() as directory:
            configuration = Path(directory) / "configuration.json"
            configuration.write_text(json.dumps(base), encoding="utf-8")
            selection = catalog.load_selection(
                self.builder / "catalog", configuration
            )
            fragment = practice_settings_fragment(
                selection,
                owner="battle.runtime_injector",
            )

        self.assertIsNotNone(fragment)
        assert fragment is not None
        self.assertEqual(
            struct.unpack_from("<4B", fragment.payload, 12),
            (2, 1, 1, 2),
        )
        row_count = struct.unpack_from("<I", fragment.payload)[0]
        defaults = {}
        for index in range(row_count):
            fields = struct.unpack_from(
                "<10I",
                fragment.payload,
                SCHEMA_HEADER_SIZE + index * ROW_SIZE,
            )
            defaults[fields[0]] = fields[7]
        self.assertEqual(defaults[0], 2)
        self.assertEqual(defaults[6], 1)
        self.assertEqual(defaults[8], 1)

    def test_linked_attack_configured_default_reaches_select_reset(self) -> None:
        base = json.loads(
            (self.builder / "configurations" / "base.json").read_text(
                encoding="utf-8"
            )
        )
        base["features"]["battle"]["support_disabled"] = False
        base["features"]["practice"]["settings_rework"] = {
            "linked_attack": "random"
        }
        with tempfile.TemporaryDirectory() as directory:
            configuration = Path(directory) / "configuration.json"
            configuration.write_text(json.dumps(base), encoding="utf-8")
            selection = catalog.load_selection(
                self.builder / "catalog", configuration
            )
            fragment = practice_settings_fragment(
                selection,
                owner="battle.runtime_injector",
            )

        self.assertIsNotNone(fragment)
        assert fragment is not None
        row_count = struct.unpack_from("<I", fragment.payload)[0]
        defaults = {}
        for index in range(row_count):
            fields = struct.unpack_from(
                "<10I",
                fragment.payload,
                SCHEMA_HEADER_SIZE + index * ROW_SIZE,
            )
            defaults[fields[0]] = fields[7]
        self.assertEqual(defaults[15], 2)

    def test_ultimate_jutsu_row_follows_contest_disabled_only(self) -> None:
        base = json.loads(
            (self.builder / "configurations" / "base.json").read_text(
                encoding="utf-8"
            )
        )
        base["features"]["battle"]["ultimate_jutsu"]["contest_disabled"] = False
        base["features"]["battle"]["ultimate_jutsu"]["hud_hidden"] = True
        with tempfile.TemporaryDirectory() as directory:
            configuration = Path(directory) / "configuration.json"
            configuration.write_text(json.dumps(base), encoding="utf-8")
            selection = catalog.load_selection(
                self.builder / "catalog", configuration
            )
            fragment = practice_settings_fragment(
                selection,
                owner="battle.runtime_injector",
            )

        self.assertIsNotNone(fragment)
        assert fragment is not None
        row_count = struct.unpack_from("<I", fragment.payload)[0]
        row_ids = [
            struct.unpack_from(
                "<I",
                fragment.payload,
                SCHEMA_HEADER_SIZE + index * ROW_SIZE,
            )[0]
            for index in range(row_count)
        ]
        self.assertIn(3, row_ids)

    def test_backing_layout_runs_between_native_animation_and_draw(self) -> None:
        injection = self.selection.injections["i__practice__settings_rework"]
        self.assertEqual(
            injection["hooks"]["prepare_compact_backing_layout"],
            {
                "description": (
                    "After native animation advance and before native hierarchy "
                    "composition, place the Opponent heading and row backings "
                    "at the compact section boundary and suppress unused native "
                    "records."
                ),
                "target_id": "na2_btl",
                "offset": "0x1CDBEC",
                "expected_hex": "BCED060C",
                "symbol": "practice_settings_prepare_backing_and_compose",
                "encoding": "jal26",
            },
        )
        self.assertEqual(
            injection["hooks"]["draw_compact_backing"],
            {
                "description": (
                    "Run the native backing renderer and draw the single "
                    "additional native player-row backing only when the compact "
                    "player section exceeds the animation's nine-row capacity."
                ),
                "target_id": "na2_btl",
                "offset": "0x1CE4D0",
                "expected_hex": "E4ED060C",
                "symbol": "practice_settings_draw_backing",
                "encoding": "jal26",
            },
        )

        c_source = injection["payload"]["practice_settings"]
        compiled_c = dict(
            catalog._compile_source(
                self.repository,
                "battle.runtime_injector",
                "practice_settings",
                c_source,
                "practice_settings",
            )
        )
        self.assertEqual(compiled_c[228].symbol, "practice_settings_backing_layout")
        self.assertEqual(
            compiled_c[230].symbol,
            "practice_settings_prepare_backing_and_compose",
        )
        self.assertEqual(compiled_c[231].symbol, "practice_settings_draw_backing")

    def test_scroll_flag_bridge_can_skip_the_native_up_arrow(self) -> None:
        injection = self.selection.injections["i__practice__settings_rework"]
        source = injection["payload"]["practice_settings_abi"]
        compiled = dict(
            catalog._compile_source(
                self.repository,
                "battle.runtime_injector",
                "practice_settings_abi",
                source,
                "practice_settings_abi",
            )
        )
        bridge = compiled[225]
        self.assertEqual(bridge.symbol, "practice_settings_scroll_flags_bridge")
        self.assertTrue(
            bridge.payload.hex().upper().endswith(
                "8800193C802039370800200300000000"
                "8800193CFC2039370800200300000000"
            )
        )


if __name__ == "__main__":
    unittest.main()
