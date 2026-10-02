from __future__ import annotations

import json
import struct
import tempfile
import unittest
from pathlib import Path

from na228_builder.infrastructure.orchestration import catalog
from na228_builder.patches.defaults.battle_mechanics.battle_settings_runtime import (
    battle_settings_runtime_fragments,
)
from scripts.lib.paths import load_local_paths
from tests.na228_builder._fixtures import test_features


class SubstitutionInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.paths = load_local_paths(Path(__file__).resolve(), allow_missing=True)
        cls.builder = cls.paths.path("builder")
        cls.catalog_path = cls.builder / "catalog.modcat"

    def _selection_with(self, value: object) -> catalog.CatalogSelection:
        base = {"features": test_features()}
        base["features"]["defaults"]["battle_mechanics"][
            "substitution_input"
        ] = value
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "configuration.jsonc"
        path.write_text(json.dumps(base, indent=2) + "\n", encoding="utf-8")
        return catalog.load_selection(self.catalog_path, path)

    def test_values_encode_default_hold_and_frame_windows(self) -> None:
        for value, expected in (("default", 0), ("hold", 1), (1, 2), (15, 16)):
            with self.subTest(value=value):
                fragments = battle_settings_runtime_fragments(
                    self._selection_with(value),
                    owner="settings.runtime_injector",
                )
                fragment = next(
                    item
                    for item in fragments
                    if item.symbol == "battle_settings_substitution_input_default"
                )
                self.assertEqual(struct.unpack("<I", fragment.payload)[0], expected)

    def test_catalog_rejects_frame_windows_outside_1_to_15(self) -> None:
        for value in (0, 16):
            with self.subTest(value=value):
                with self.assertRaises(catalog.ConfigurationError):
                    self._selection_with(value)


if __name__ == "__main__":
    unittest.main()
