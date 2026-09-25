from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from na228_builder.infrastructure.orchestration import catalog, jsonc
from na228_builder.patches.localization.mod_strings import ModStrings
from scripts.lib.paths import load_local_paths


class ControlSettingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.paths = load_local_paths(Path(__file__).resolve(), allow_missing=True)
        cls.builder = cls.paths.path("builder")
        cls.catalog_path = cls.builder / "catalog.modcat"
        cls.configurations = cls.builder / "configurations"

    def _base_features(self) -> dict[str, object]:
        base = jsonc.loads(
            (self.configurations / "base.jsonc").read_text(encoding="utf-8")
        )
        return base["features"]

    def _write_full_configuration(self, features: dict[str, object]) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "configuration.jsonc"
        path.write_text(
            json.dumps({"features": features}, indent=2) + "\n",
            encoding="utf-8",
        )
        return path

    def test_controls_and_substitution_settings_are_independently_selectable(
        self,
    ) -> None:
        for controls_enabled, substitution_enabled in (
            (False, False),
            (False, True),
            (True, False),
            (True, True),
        ):
            with self.subTest(
                controls=controls_enabled,
                substitution=substitution_enabled,
            ):
                features = self._base_features()
                features["settings"]["mod_settings"][
                    "new_controls"
                ] = controls_enabled
                mechanics = features["settings"]["battle_mechanics"]
                substitution = mechanics["substitution"]
                mechanics["substitution"] = (
                    substitution if substitution_enabled else False
                )
                selection = catalog.load_selection(
                    self.catalog_path,
                    self._write_full_configuration(features),
                )
                controls = next(
                    node
                    for node in selection.nodes
                    if node.path
                    == (
                        "features", "settings", "mod_settings", "new_controls"
                    )
                )
                substitution = next(
                    node
                    for node in selection.nodes
                    if node.path
                    == (
                        "features", "settings", "battle_mechanics",
                        "substitution",
                    )
                )
                self.assertTrue(controls.enabled)
                self.assertEqual(controls.configured_value, controls_enabled)
                self.assertEqual(substitution.enabled, substitution_enabled)
                active_edits = {
                    node.patch
                    for node in selection.feature_nodes("settings")
                    if node.enabled and node.patch in selection.edits
                }
                active_injections = {
                    node.patch
                    for node in selection.feature_nodes("settings")
                    if node.enabled and node.patch in selection.injections
                }
                self.assertEqual(
                    "settings.new_controls" in active_edits,
                    True,
                )
                self.assertEqual(
                    "settings.new_controls" in active_injections,
                    True,
                )
                self.assertEqual(
                    "settings.battle_mechanics.substitution"
                    in active_injections,
                    substitution_enabled,
                )

    def test_control_settings_owns_substitution_label(self) -> None:
        selection = catalog.load_selection(
            self.catalog_path,
            self.configurations / "base.jsonc",
        )
        controls = selection.injections["settings.new_controls"]
        self.assertIn("label_substitution_action", controls["hooks"])
        self.assertEqual(
            ModStrings(selection).native_payload(
                controls["hooks"]["label_substitution_action"]["symbol"]),
            b"Substitution\0",
        )

        gauge = selection.injections[
            "settings.battle_mechanics.substitution"
        ]
        self.assertNotIn("label_substitution_action", gauge["hooks"])


if __name__ == "__main__":
    unittest.main()
