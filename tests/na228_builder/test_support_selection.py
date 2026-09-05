from __future__ import annotations

import json
import struct
import tempfile
import unittest
from pathlib import Path

from na228_builder.scripts import catalog, jsonc
from na228_builder.scripts.support_selection import (
    COMPACT_SUPPORT_SYMBOLS,
    SUPPORT_SELECTION_MODES,
    support_selection_runtime_package,
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
        cls.targets = cls.builder / "modules" / "targets.tsv"

    def _selection(self, mode: str) -> catalog.CatalogSelection:
        base = jsonc.loads(
            (self.configurations / "base.jsonc").read_text(encoding="utf-8")
        )
        base["features"]["character_select"]["support_selection"] = mode
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "configuration.jsonc"
        path.write_text(json.dumps(base, indent=2) + "\n", encoding="utf-8")
        return catalog.load_selection(self.catalog_path, path)

    def test_modes_emit_their_runtime_value_and_compact_only_when_needed(self) -> None:
        for mode, encoded in SUPPORT_SELECTION_MODES.items():
            with self.subTest(mode=mode):
                selection = self._selection(mode)
                package = catalog.load_runtime_package(
                    selection,
                    "character_select",
                    self.targets,
                    self.repository,
                    "character_select.runtime_injector",
                )
                transformed = support_selection_runtime_package(selection, package)
                mode_fragment = next(
                    fragment
                    for fragment in transformed.fragments
                    if fragment.symbol == "character_select_support_selection_mode"
                )
                self.assertEqual(struct.unpack("<I", mode_fragment.payload)[0], encoded)

                edit_symbols = {
                    edit.symbolic_patch.symbol for edit in transformed.edits
                }
                fragment_symbols = {
                    fragment.symbol for fragment in transformed.fragments
                }
                if mode == "all":
                    self.assertTrue(COMPACT_SUPPORT_SYMBOLS.isdisjoint(edit_symbols))
                    self.assertTrue(COMPACT_SUPPORT_SYMBOLS.isdisjoint(fragment_symbols))
                else:
                    self.assertTrue(COMPACT_SUPPORT_SYMBOLS.issubset(edit_symbols))
                    self.assertTrue(COMPACT_SUPPORT_SYMBOLS.issubset(fragment_symbols))


if __name__ == "__main__":
    unittest.main()
