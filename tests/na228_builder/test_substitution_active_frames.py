from __future__ import annotations

import json
import struct
import tempfile
import unittest
from pathlib import Path

from na228_builder.infrastructure.orchestration import catalog, jsonc
from na228_builder.patches.settings.ingame.battle_mechanics.battle_settings_runtime import (
    battle_settings_runtime_fragments,
)
from scripts.lib.paths import load_local_paths


class SubstitutionActiveFramesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.paths = load_local_paths(Path(__file__).resolve(), allow_missing=True)
        cls.builder = cls.paths.path("builder")
        cls.catalog_path = cls.builder / "catalog.modcat"
        cls.configurations = cls.builder / "configurations"

    def _selection_with(self, value: object) -> catalog.CatalogSelection:
        base = jsonc.loads(
            (self.configurations / "base.jsonc").read_text(encoding="utf-8")
        )
        base["features"]["default_settings"]["battle_mechanics"][
            "sub_active_frames"
        ] = value
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "configuration.jsonc"
        path.write_text(json.dumps(base, indent=2) + "\n", encoding="utf-8")
        return catalog.load_selection(self.catalog_path, path)

    def test_catalog_accepts_the_active_frame_boundaries(self) -> None:
        for value in ("default", 1, 15):
            with self.subTest(value=value):
                fragments = battle_settings_runtime_fragments(
                    self._selection_with(value),
                    owner="settings.runtime_injector",
                )
                fragment = next(
                    item
                    for item in fragments
                    if item.symbol == "battle_settings_sub_active_frames_default"
                )
                expected = 0 if value == "default" else value
                self.assertEqual(struct.unpack("<I", fragment.payload)[0], expected)

    def test_catalog_rejects_values_outside_the_active_frame_range(self) -> None:
        for value in (0, 16):
            with self.subTest(value=value):
                with self.assertRaises(catalog.ConfigurationError):
                    self._selection_with(value)


if __name__ == "__main__":
    unittest.main()
