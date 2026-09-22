from __future__ import annotations

import json
import struct
import tempfile
import unittest
from pathlib import Path

from na228_builder.infrastructure.orchestration import catalog, jsonc
from na228_builder.patches.settings.ingame.battle_mechanics.substitution.substitution_gauge import substitution_gauge_fragment
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

    def test_false_disables_gauge(self) -> None:
        features = self._base_features()
        features["settings"]["battle_mechanics"][
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
        features["settings"]["battle_mechanics"][
            "substitution"
        ] = True
        with self.assertRaisesRegex(
            catalog.ConfigurationError,
            "features.settings.battle_mechanics.substitution",
        ):
            catalog.load_selection(
                self.catalog_path,
                self._write_full_configuration(features),
            )

    def test_advanced_configuration_encodes_exact_integer_counts(self) -> None:
        features = self._base_features()
        features["settings"]["battle_mechanics"][
            "substitution"
        ] = {
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
        base_selection = catalog.load_selection(
            self.catalog_path,
            self._write_full_configuration(features),
        )
        base_gauge = substitution_gauge_fragment(
            base_selection,
            owner="battle.runtime_injector",
        )
        assert base_gauge is not None
        features["settings"]["battle_mechanics"][
            "substitution"
        ] = {
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
        actual = struct.unpack("<9I", gauge.payload)
        base = struct.unpack("<9I", base_gauge.payload)
        self.assertEqual((actual[2], actual[4], actual[5]), (600, 0, 2))
        self.assertEqual(
            (actual[0], actual[1], actual[3], actual[6:]),
            (base[0], base[1], base[3], base[6:]),
        )

    def test_gauge_can_coexist_with_support_on(self) -> None:
        features = self._base_features()
        base_selection = catalog.load_selection(
            self.catalog_path,
            self._write_full_configuration(features),
        )
        base_gauge = substitution_gauge_fragment(
            base_selection,
            owner="battle.runtime_injector",
        )
        assert base_gauge is not None
        mechanics = features["settings"]["battle_mechanics"]
        mechanics["substitution"]["value"] = "gauge"
        mechanics["support"] = "normal"
        selection = catalog.load_selection(
            self.catalog_path,
            self._write_full_configuration(features),
        )
        support = next(
            node
            for node in selection.nodes
            if node.path == (
                "features", "settings", "battle_mechanics", "support",
            )
        )
        self.assertEqual(support.configured_value, "normal")
        gauge = substitution_gauge_fragment(
            selection,
            owner="battle.runtime_injector",
        )
        self.assertIsNotNone(gauge)
        assert gauge is not None
        self.assertEqual(gauge.payload, base_gauge.payload)

    def test_gauge_always_links_runtime_cost_providers(self) -> None:
        features = self._base_features()
        features["settings"]["battle_mechanics"][
            "substitution"
        ]["value"] = "gauge"
        features["settings"]["mod_settings"]["character_overrides"] = False
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
        self.assertEqual(
            tuple(relocation.symbol for relocation in fragment.relocations),
            (
                "substitution_cost_for_fighter",
                "substitution_cost_fraction_for_fighter",
            ),
        )

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
                mechanics = features["settings"]["battle_mechanics"]
                support = mechanics["support"]
                mechanics["support"] = (
                    support if battle_support_enabled else False
                )
                mod_settings = features["settings"]["mod_settings"]
                support_selection = mod_settings[
                    "support_selection"
                ]
                mod_settings["support_selection"] = (
                    support_selection if selection_enabled else False
                )
                selection = catalog.load_selection(
                    self.catalog_path,
                    self._write_full_configuration(features),
                )
                injections = {
                    node.patch
                    for node in selection.feature_nodes("settings")
                    if node.enabled and node.patch in selection.injections
                }
                self.assertEqual(
                    "settings.battle_mechanics.support" in injections,
                    battle_support_enabled,
                )
                self.assertEqual(
                    "character_select.support_selection"
                    in injections,
                    selection_enabled,
                )


if __name__ == "__main__":
    unittest.main()
