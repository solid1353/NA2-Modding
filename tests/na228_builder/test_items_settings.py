from __future__ import annotations

import json
import struct
import tempfile
import unittest
from pathlib import Path

from na228_builder.infrastructure.orchestration import catalog
from na228_builder.patches.defaults.battle_mechanics.items.items_settings import (
    FIELD_ITEMS,
    items_settings_fragment,
)
from scripts.lib.paths import load_local_paths
from tests.na228_builder._fixtures import test_features


class ItemsSettingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.paths = load_local_paths(Path(__file__).resolve(), allow_missing=True)
        cls.builder = cls.paths.path("builder")
        cls.catalog_path = cls.builder / "catalog.modcat"

    def _selection(self, mutate) -> catalog.CatalogSelection:
        base = {"features": test_features()}
        mutate(base["features"]["defaults"]["battle_mechanics"])
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "configuration.jsonc"
        path.write_text(json.dumps(base, indent=2) + "\n", encoding="utf-8")
        return catalog.load_selection(self.catalog_path, path)

    def test_custom_item_mask_preserves_field_identity_order(self) -> None:
        def configure(mechanics) -> None:
            items = mechanics["items"]
            items["value"] = "custom"
            items["custom"]["availability"] = "less"
            for _code, key, _label in FIELD_ITEMS:
                items["custom"][key] = "off"
            items["custom"][FIELD_ITEMS[0][1]] = "on"
            items["custom"][FIELD_ITEMS[-1][1]] = "on"

        selection = self._selection(configure)
        fragment = items_settings_fragment(
            selection,
            owner="settings.runtime_injector",
        )
        self.assertIsNotNone(fragment)
        assert fragment is not None
        self.assertEqual(
            struct.unpack_from("<3I", fragment.payload),
            (4, 1, 1 | (1 << (len(FIELD_ITEMS) - 1))),
        )

if __name__ == "__main__":
    unittest.main()
