from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from na228_builder.infrastructure.orchestration import catalog
from na228_builder.patches.localization.mod_strings import ModStrings
from na228_builder.patches.settings.mod_settings.mod_settings import _pages
from scripts.lib.paths import load_local_paths
from tests.na228_builder._fixtures import test_features


class ModSettingsMenuTests(unittest.TestCase):
    def test_character_selection_follows_battle_mechanics(self) -> None:
        builder = load_local_paths(Path(__file__).resolve(), allow_missing=True).path("builder")
        with tempfile.TemporaryDirectory() as directory:
            configuration = Path(directory) / "configuration.jsonc"
            configuration.write_text(
                json.dumps({"features": test_features()}), encoding="utf-8"
            )
            selection = catalog.load_selection(builder / "catalog.modcat", configuration)

        pages = _pages(selection)
        strings = ModStrings(selection)

        def labels(page):
            return [
                strings.resolve(row.label if row.label is not None else row.runtime_option.label)
                for row in page.rows
            ]

        self.assertEqual(
            labels(pages[0]),
            [
                "Battle Mechanics",
                "Character Selection",
                "Battle Settings",
                "Practice Settings",
                "Control Settings",
                "Simple Display",
            ],
        )
        character_page = pages[pages[0].rows[1].value_pages[0][1]]
        self.assertEqual((character_page.parent_page, character_page.parent_row), (0, 1))
        self.assertEqual(
            labels(character_page),
            ["Support Selection", "Character Balance", "Balance Overlay"],
        )


if __name__ == "__main__":
    unittest.main()
