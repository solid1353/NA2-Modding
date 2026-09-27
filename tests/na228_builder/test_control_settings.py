from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from na228_builder.infrastructure.orchestration import catalog
from scripts.lib.paths import load_local_paths
from tests.na228_builder._fixtures import test_features


class ControlSettingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.paths = load_local_paths(Path(__file__).resolve(), allow_missing=True)
        cls.builder = cls.paths.path("builder")
        cls.catalog_path = cls.builder / "catalog.modcat"
    def _base_features(self) -> dict[str, object]:
        return test_features()

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
                features["general"]["new_controls"] = controls_enabled
                mechanics = features["default_settings"]["battle_mechanics"]
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
                        "features", "general", "new_controls"
                    )
                )
                substitution = next(
                    node
                    for node in selection.nodes
                    if node.path
                    == (
                        "features", "default_settings", "battle_mechanics",
                        "substitution",
                    )
                )
                self.assertEqual(controls.enabled, controls_enabled)
                self.assertEqual(substitution.enabled, substitution_enabled)
                active_edits = {
                    node.patch
                    for node in selection.nodes
                    if node.enabled and node.patch in selection.edits
                }
                active_injections = {
                    node.patch
                    for node in selection.nodes
                    if node.enabled and node.patch in selection.injections
                }
                self.assertEqual(
                    "general.new_controls" in active_edits,
                    controls_enabled,
                )
                self.assertEqual(
                    "general.new_controls" in active_injections,
                    controls_enabled,
                )
                self.assertEqual(
                    "settings.battle_mechanics.substitution"
                    in active_injections,
                    substitution_enabled,
                )


if __name__ == "__main__":
    unittest.main()
