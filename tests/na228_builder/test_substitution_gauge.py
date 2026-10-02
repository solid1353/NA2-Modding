from __future__ import annotations

import json
import struct
import tempfile
import unittest
from pathlib import Path

from na228_builder.infrastructure.orchestration import catalog
from na228_builder.patches.defaults.battle_mechanics.substitution_resource.substitution_gauge import substitution_gauge_fragment
from scripts.lib.paths import load_local_paths
from tests.na228_builder._fixtures import test_features


class SubstitutionGaugeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.paths = load_local_paths(Path(__file__).resolve(), allow_missing=True)
        cls.builder = cls.paths.path("builder")
        cls.catalog_path = cls.builder / "catalog.modcat"

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
        return test_features()

    def test_true_is_invalid_when_default_is_mandatory(self) -> None:
        features = self._base_features()
        features["defaults"]["battle_mechanics"][
            "substitution_resource"
        ] = True
        with self.assertRaisesRegex(
            catalog.ConfigurationError,
            "features.defaults.battle_mechanics.substitution_resource",
        ):
            catalog.load_selection(
                self.catalog_path,
                self._write_full_configuration(features),
            )

    def test_advanced_configuration_encodes_exact_integer_counts(self) -> None:
        features = self._base_features()
        features["defaults"]["battle_mechanics"][
            "substitution_resource"
        ] = {
            "value": "chakra",
            "gauge": {
                "recovery_delay_seconds": 0.25,
                "refill_seconds_per_stock": 0.05,
                "damage_recovery": "off",
                "damage_percent_for_full_refill": 125,
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
            (3, 12, 15, 81920, 0, 0, 0, 0, 0),
        )

    def test_partial_configuration_uses_omitted_field_defaults(self) -> None:
        features = self._base_features()
        features["defaults"]["battle_mechanics"][
            "substitution_resource"
        ] = {
            "value": "free",
            "gauge": {
                "recovery_delay_seconds": 10,
                "damage_recovery": "off",
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
        self.assertEqual((actual[2], actual[4], actual[5]), (600, 0, 2))
        self.assertGreater(actual[0], 0)
        self.assertEqual(actual[1], 4 * actual[0])
        self.assertGreater(actual[3], 0)
        self.assertLessEqual(actual[3], 4 * 65536)
        self.assertEqual(actual[6:], (0, 0, 0))

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
        mechanics = features["defaults"]["battle_mechanics"]
        mechanics["substitution_resource"]["value"] = "gauge"
        mechanics["support"] = "normal"
        selection = catalog.load_selection(
            self.catalog_path,
            self._write_full_configuration(features),
        )
        support = next(
            node
            for node in selection.nodes
            if node.path == (
                "features", "defaults", "battle_mechanics", "support",
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
        features["defaults"]["battle_mechanics"][
            "substitution_resource"
        ]["value"] = "gauge"
        features["defaults"]["match_setup"]["character_balance"] = "original"
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
            self._write_full_configuration(self._base_features()),
        )
        gauge = selection.injections[
            "defaults.battle_mechanics.substitution_resource"
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

if __name__ == "__main__":
    unittest.main()
