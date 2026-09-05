from __future__ import annotations

import json
import struct
import tempfile
import unittest
from pathlib import Path

from na228_builder.scripts import catalog, jsonc
from na228_builder.scripts.substitution_gauge import substitution_gauge_fragment
from scripts.lib.paths import load_local_paths


class SubstitutionGaugeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.paths = load_local_paths(Path(__file__).resolve(), allow_missing=True)
        cls.builder = cls.paths.path("builder")
        cls.catalog_path = cls.builder / "catalog.modcat"
        cls.configurations = cls.builder / "configurations"

    def _write_full_configuration(self, features: dict[str, object]) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "configuration.jsonc"
        path.write_text(
            json.dumps({"features": features}, indent=2) + "\n",
            encoding="utf-8",
        )
        return path

    def _base_features(self) -> dict[str, object]:
        base = jsonc.loads(
            (self.configurations / "base.jsonc").read_text(encoding="utf-8")
        )
        return base["features"]

    def test_base_configuration_encodes_parity_defaults(self) -> None:
        selection = catalog.load_selection(
            self.catalog_path,
            self.configurations / "base.jsonc",
        )
        gauge = substitution_gauge_fragment(
            selection,
            owner="battle.runtime_injector",
        )
        gauge_node = next(
            node
            for node in selection.nodes
            if node.path == (
                "features", "settings", "ingame",
                "battle_mechanics", "substitution",
            )
        )
        self.assertEqual(
            gauge_node.configured_value["value"],
            "gauge",
        )
        self.assertIsNotNone(gauge)
        assert gauge is not None
        self.assertEqual(
            struct.unpack("<9I", gauge.payload),
            (60, 240, 840, 20480, 1, 1, 0, 0, 0),
        )

    def test_false_disables_gauge(self) -> None:
        features = self._base_features()
        features["settings"]["ingame"]["battle_mechanics"][
            "substitution"
        ] = False
        selection = catalog.load_selection(
            self.catalog_path,
            self._write_full_configuration(features),
        )
        self.assertIsNone(
            substitution_gauge_fragment(
                selection,
                owner="battle.runtime_injector",
            )
        )

    def test_true_is_invalid_when_default_is_mandatory(self) -> None:
        features = self._base_features()
        features["settings"]["ingame"]["battle_mechanics"][
            "substitution"
        ] = True
        with self.assertRaisesRegex(
            catalog.ConfigurationError,
            "features.settings.ingame.battle_mechanics.substitution",
        ):
            catalog.load_selection(
                self.catalog_path,
                self._write_full_configuration(features),
            )
    def test_advanced_configuration_encodes_exact_integer_counts(self) -> None:
        features = self._base_features()
        features["settings"]["ingame"]["battle_mechanics"]["substitution"] = {
            "value": "chakra",
            "gauge": {
                "recovery_delay_seconds": 0.25,
                "refill_seconds_per_stock": 0.05,
                "damage_recovery": False,
                "damage_percent_per_stock": 31.25,
            },
        }
        selection = catalog.load_selection(
            self.catalog_path,
            self._write_full_configuration(features),
        )
        gauge = substitution_gauge_fragment(
            selection,
            owner="battle.runtime_injector",
        )
        self.assertIsNotNone(gauge)
        assert gauge is not None
        self.assertEqual(
            struct.unpack("<9I", gauge.payload),
            (3, 12, 15, 20480, 0, 0, 0, 0, 0),
        )

    def test_partial_configuration_inherits_omitted_defaults(self) -> None:
        features = self._base_features()
        features["settings"]["ingame"]["battle_mechanics"]["substitution"] = {
            "value": "free",
            "gauge": {
                "recovery_delay_seconds": 10,
                "damage_recovery": False,
            },
        }
        selection = catalog.load_selection(
            self.catalog_path,
            self._write_full_configuration(features),
        )
        gauge = substitution_gauge_fragment(
            selection,
            owner="battle.runtime_injector",
        )
        self.assertIsNotNone(gauge)
        assert gauge is not None
        self.assertEqual(
            struct.unpack("<9I", gauge.payload),
            (60, 240, 600, 20480, 0, 2, 0, 0, 0),
        )

    def test_gauge_can_coexist_with_support_on(self) -> None:
        features = self._base_features()
        features["settings"]["ingame"]["battle_mechanics"]["substitution"][
            "value"
        ] = "gauge"
        features["settings"]["ingame"]["battle_mechanics"]["support"] = "normal"
        selection = catalog.load_selection(
            self.catalog_path,
            self._write_full_configuration(features),
        )
        support = next(
            node
            for node in selection.nodes
            if node.path == (
                "features", "settings", "ingame",
                "battle_mechanics", "support",
            )
        )
        self.assertEqual(support.configured_value, "normal")
        gauge = substitution_gauge_fragment(
            selection,
            owner="battle.runtime_injector",
        )
        self.assertIsNotNone(gauge)
        assert gauge is not None
        self.assertEqual(
            struct.unpack("<9I", gauge.payload),
            (60, 240, 840, 20480, 1, 1, 0, 0, 0),
        )

    def test_charged_spend_precedes_native_chakra_suppression(self) -> None:
        selection = catalog.load_selection(
            self.catalog_path,
            self.configurations / "base.jsonc",
        )
        injection = selection.injections[
            "settings.battle_mechanics.substitution"
        ]
        hook = injection["hooks"]["spend_stock_without_chakra"]
        self.assertEqual(
            hook,
            {
                "description": (
                    "After native charged-transition setup, retain the complete "
                    "native chakra path in Chakra mode, spend the resolved gauge "
                    "cost in Gauge mode, or spend nothing in Free mode."
                ),
                "target_id": "na2_elf",
                "offset": "0x129984",
                "expected_hex": "3C1D0C0C00000000",
                "symbol": "substitution_gauge_spend_shim",
                "encoding": "jal26",
            },
        )
        payload = injection["payload"]
        self.assertEqual(
            payload["substitution_gauge_abi"]["imports"][
                "substitution_gauge_route_spend"
            ],
            "substitution_gauge_route_spend",
        )
        assembly = (
            self.builder.parent
            / "src"
            / "battle_logic"
            / "substitution_gauge_abi.S"
        ).read_text(encoding="utf-8")
        start = assembly.index("substitution_gauge_spend_shim:")
        end = assembly.index(
            ".size substitution_gauge_spend_shim",
            start,
        )
        shim = assembly[start:end]
        self.assertIn("jal substitution_gauge_route_spend", shim)
        self.assertIn("beqz $v0", shim)
        self.assertIn("ori $t9, $t9, 0x74f0", shim)
        self.assertIn("ori $t9, $t9, 0x988c", shim)
        self.assertIn("ori $t9, $t9, 0x98f0", shim)

    def test_gauge_without_character_overrides_uses_native_cost(self) -> None:
        features = self._base_features()
        features["settings"]["ingame"]["battle_mechanics"]["substitution"][
            "value"
        ] = "gauge"
        features["settings"]["character_overrides"] = False
        selection = catalog.load_selection(
            self.catalog_path,
            self._write_full_configuration(features),
        )
        fragment = substitution_gauge_fragment(
            selection,
            owner="battle.runtime_injector",
        )
        self.assertIsNotNone(fragment)
        assert fragment is not None
        self.assertEqual(fragment.relocations, ())

    def test_gauge_offsets_only_resolved_name_y_while_localization_owns_x(
        self,
    ) -> None:
        selection = catalog.load_selection(
            self.catalog_path,
            self.configurations / "base.jsonc",
        )
        gauge = selection.injections[
            "settings.battle_mechanics.substitution"
        ]
        self.assertNotIn(
            "load_battle_hud_character_name_x_anchor",
            gauge["hooks"],
        )
        hook = gauge["hooks"]["adjust_battle_hud_character_name_y"]
        self.assertEqual(hook["target_id"], "na2_btl")
        self.assertEqual(hook["offset"], "0x67F68")
        self.assertEqual(hook["expected_hex"], "820001460C00A290")

        adjuster = "substitution_gauge_adjust_battle_hud_character_name_y"
        gauge_c = gauge["payload"]["substitution_gauge"]
        self.assertIn(adjuster, gauge_c["fragments"])
        self.assertFalse(
            any("character_name_x" in name for name in gauge_c["fragments"])
        )

        gauge_abi = gauge["payload"]["substitution_gauge_abi"]
        shim = f"{adjuster}_shim"
        self.assertEqual(gauge_abi["imports"][adjuster], adjuster)
        self.assertIn(shim, gauge_abi["fragments"])
        self.assertFalse(
            any("character_name_x" in name for name in gauge_abi["fragments"])
        )

        localization_name_edit = selection.edits[
            "localization.ui"
        ]["edits"]["battle_hud_names__mirrored_x_anchor_74"]
        self.assertEqual(localization_name_edit["destination_target_id"], "na2_btl")
        self.assertEqual(localization_name_edit["destination_offset"], "0x2103D8")
        self.assertEqual(
            struct.unpack("<f", bytes.fromhex(localization_name_edit["expected_hex"]))[0],
            90.0,
        )
        self.assertEqual(
            struct.unpack(
                "<f", bytes.fromhex(localization_name_edit["replacement_hex"])
            )[0],
            74.0,
        )

        assembly = (
            self.builder.parent
            / "src"
            / "battle_logic"
            / "substitution_gauge_abi.S"
        ).read_text(encoding="utf-8")
        start = assembly.index(f"{shim}:")
        end = assembly.index(f".size {shim}", start)
        body = assembly[start:end]
        for instruction in (
            "sw $v1, 16($sp)",
            "sw $a1, 20($sp)",
            "swc1 $f1, 24($sp)",
            "swc1 $f3, 28($sp)",
            "swc1 $f4, 32($sp)",
            "swc1 $f5, 36($sp)",
            "mov.s $f12, $f0",
            f"jal {adjuster}",
            "mul.s $f2, $f0, $f1",
            "lw $a1, 20($sp)",
            "lw $v1, 16($sp)",
            "lbu $v0, 12($a1)",
        ):
            self.assertIn(instruction, body)

        source = (
            self.builder.parent
            / "src"
            / "battle_logic"
            / "substitution_gauge.c"
        ).read_text(encoding="utf-8")
        self.assertIn("BATTLE_HUD_CHARACTER_NAME_Y_OFFSET 11.0f", source)
        self.assertNotIn("NATIVE_BATTLE_HUD_CHARACTER_NAME", source)
        self.assertNotIn("BATTLE_HUD_CHARACTER_NAME_X", source)

    def test_independent_renderer_uses_native_battle_hud_visibility(self) -> None:
        selection = catalog.load_selection(
            self.catalog_path,
            self.configurations / "base.jsonc",
        )
        injection = selection.injections[
            "settings.battle_mechanics.substitution"
        ]
        cache_hook = injection["hooks"][
            "cache_substitution_gauge_render_source"
        ]
        self.assertEqual(
            cache_hook,
            {
                "description": (
                    "Retain the native support-controller update, then cache "
                    "its initialized per-side sprite and BTL rendering context "
                    "without drawing through the support-controller lifecycle."
                ),
                "target_id": "na2_btl",
                "offset": "0x69380",
                "expected_hex": "04721C0C",
                "symbol": "substitution_gauge_update_and_cache",
                "encoding": "jal26",
            },
        )
        draw_hook = injection["hooks"][
            "draw_independent_substitution_gauge_with_battle_hud"
        ]
        self.assertEqual(
            draw_hook,
            {
                "description": (
                    "Retain the primary per-side Battle HUD draw, then draw "
                    "the independent substitution bar only after the native "
                    "parent visibility gate accepts that HUD side, using the "
                    "same live layout transform and primary-sprite alpha."
                ),
                "target_id": "na2_btl",
                "offset": "0x67434",
                "expected_hex": "C86D1C0C",
                "symbol": "substitution_gauge_draw_with_battle_hud",
                "encoding": "jal26",
            },
        )
        gauge_payload = injection["payload"]["substitution_gauge"]
        self.assertEqual(
            gauge_payload["imports"],
            {"substitution_gauge_config": "substitution_gauge_config"},
        )
        self.assertEqual(
            gauge_payload["fragments"]["substitution_gauge_fill_fraction"],
            {
                "object": (
                    "battle.logic.substitution.gauge.c.bss."
                    "substitution.gauge.fill.fraction"
                ),
            },
        )
        self.assertEqual(
            gauge_payload["fragments"]["substitution_gauge_update_and_cache"],
            {
                "object": (
                    "battle.logic.substitution.gauge.c.text."
                    "substitution.gauge.update.and.cache"
                ),
            },
        )
        self.assertEqual(
            gauge_payload["fragments"][
                "substitution_gauge_draw_with_battle_hud"
            ],
            {
                "object": (
                    "battle.logic.substitution.gauge.c.text."
                    "substitution.gauge.draw.with.battle.hud"
                ),
            },
        )
        self.assertEqual(
            gauge_payload["fragments"]["substitution_gauge_runtime_state"],
            {
                "object": (
                    "battle.logic.substitution.gauge.c.bss."
                    "substitution.gauge.runtime.state"
                ),
            },
        )

    def test_battle_support_and_character_select_support_are_independent(self) -> None:
        cases = (
            (True, True),
            (True, False),
            (False, True),
            (False, False),
        )
        for battle_support_enabled, selection_enabled in cases:
            with self.subTest(
                battle_support=battle_support_enabled,
                support_selection=selection_enabled,
            ):
                features = self._base_features()
                support = features["settings"]["ingame"][
                    "battle_mechanics"
                ]["support"]
                features["settings"]["ingame"]["battle_mechanics"][
                    "support"
                ] = (
                    support if battle_support_enabled else False
                )
                support_selection = features["character_select"][
                    "support_selection"
                ]
                features["character_select"]["support_selection"] = (
                    support_selection if selection_enabled else False
                )
                selection = catalog.load_selection(
                    self.catalog_path,
                    self._write_full_configuration(features),
                )
                settings_injections = {
                    node.patch
                    for node in selection.feature_nodes("settings")
                    if node.enabled and node.patch in selection.injections
                }
                character_select_injections = {
                    node.patch
                    for node in selection.feature_nodes("character_select")
                    if node.enabled and node.patch in selection.injections
                }
                self.assertEqual(
                    "settings.battle_mechanics.support" in settings_injections,
                    battle_support_enabled,
                )
                self.assertEqual(
                    "character_select.support_selection"
                    in character_select_injections,
                    selection_enabled,
                )

    def test_support_selector_owns_only_battle_routing(self) -> None:
        selection = catalog.load_selection(
            self.catalog_path,
            self.configurations / "base.jsonc",
        )
        injection = selection.injections["settings.battle_mechanics.support"]
        self.assertEqual(
            set(injection["hooks"]),
            {
                "route_free_field_support_call",
                "route_support_gauge_drain",
                "route_support_gauge_draw",
                "route_support_gauge_update",
                "support_gauge_marker",
                "support_gauge_readiness",
            },
        )
        self.assertEqual(
            injection["hooks"]["route_support_gauge_draw"],
            {
                "description": (
                    "Suppress the dedicated native support gauge only while Off."
                ),
                "target_id": "na2_btl",
                "offset": "0x69398",
                "expected_hex": "BC721C0C",
                "symbol": "battle_support_route_gauge_draw",
                "encoding": "jal26",
            },
        )
        support_payload = injection["payload"]["battle_support"]
        self.assertEqual(support_payload["imports"], {"support_get": "support_get"})

        support_selection = selection.injections[
            "character_select.support_selection"
        ]
        self.assertNotIn(
            "route_free_field_support_call", support_selection["hooks"]
        )
        self.assertNotIn("route_support_gauge_draw", support_selection["hooks"])
        self.assertEqual(
            set(support_selection["payload"]),
            {"character_select_support_selection"},
        )


if __name__ == "__main__":
    unittest.main()
