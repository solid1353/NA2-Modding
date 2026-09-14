from __future__ import annotations

import json
import struct
import tempfile
import unittest
from pathlib import Path

from na228_builder.infrastructure.orchestration import catalog, jsonc
from na228_builder.patches.settings.mod_settings.mod_settings import (
    mod_settings_state_fragment,
)
from scripts.lib.paths import load_local_paths


class SupportSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.paths = load_local_paths(Path(__file__).resolve(), allow_missing=True)
        cls.repository = cls.paths.repository
        cls.builder = cls.paths.path("builder")
        cls.catalog_path = cls.builder / "catalog.modcat"
        cls.configurations = cls.builder / "configurations"
        cls.targets = cls.builder / "infrastructure" / "modules" / "targets.tsv"

    def _selection(self, mode: str) -> catalog.CatalogSelection:
        base = jsonc.loads(
            (self.configurations / "base.jsonc").read_text(encoding="utf-8")
        )
        base["features"]["settings"]["mod_settings"][
            "support_selection"
        ] = mode
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "configuration.jsonc"
        path.write_text(json.dumps(base, indent=2) + "\n", encoding="utf-8")
        return catalog.load_selection(self.catalog_path, path)

    def test_modes_emit_their_runtime_value_for_character_select(self) -> None:
        for mode, encoded in {"none": 0, "relevant": 1, "all": 2}.items():
            with self.subTest(mode=mode):
                selection = self._selection(mode)
                state = mod_settings_state_fragment(
                    selection,
                    owner="settings.runtime_injector",
                )
                values = struct.unpack("<10I", state.payload)
                self.assertEqual(values[4], encoded)
                self.assertEqual(values[9], encoded)

                declaration = selection.injections[
                    "character_select.support_selection"
                ]["payload"]["character_select_support_selection"]
                self.assertEqual(
                    declaration["imports"]["mod_settings_option_get"],
                    "mod_settings_option_get",
                )


if __name__ == "__main__":
    unittest.main()
