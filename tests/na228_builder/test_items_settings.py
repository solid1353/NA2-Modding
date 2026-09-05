from __future__ import annotations

import json
import struct
import tempfile
import unittest
from pathlib import Path

from na228_builder.scripts import catalog, jsonc
from na228_builder.scripts.items_settings import (
    FIELD_ITEMS,
    items_option_defaults,
    items_settings_fragment,
)
from scripts.lib.paths import load_local_paths


class ItemsSettingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.paths = load_local_paths(Path(__file__).resolve(), allow_missing=True)
        cls.builder = cls.paths.path("builder")
        cls.catalog_path = cls.builder / "catalog.modcat"
        cls.configurations = cls.builder / "configurations"

    def _selection(self, mutate) -> catalog.CatalogSelection:
        base = jsonc.loads(
            (self.configurations / "base.jsonc").read_text(encoding="utf-8")
        )
        mutate(base["features"]["settings"]["ingame"]["battle_mechanics"])
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "configuration.jsonc"
        path.write_text(json.dumps(base, indent=2) + "\n", encoding="utf-8")
        return catalog.load_selection(self.catalog_path, path)

    def test_base_custom_mode_encodes_all_field_items(self) -> None:
        selection = catalog.load_selection(
            self.catalog_path,
            self.configurations / "base.jsonc",
        )
        defaults = items_option_defaults(selection)
        self.assertEqual(defaults[:2], (4, 2))
        self.assertEqual(defaults[2:], (1,) * len(FIELD_ITEMS))

        fragment = items_settings_fragment(
            selection,
            owner="settings.runtime_injector",
        )
        self.assertIsNotNone(fragment)
        assert fragment is not None
        mode, availability, enabled_mask = struct.unpack_from("<3I", fragment.payload)
        self.assertEqual((mode, availability), (4, 2))
        self.assertEqual(enabled_mask, (1 << len(FIELD_ITEMS)) - 1)
        self.assertEqual(
            fragment.payload[12:],
            bytes(code for code, _key, _label in FIELD_ITEMS),
        )

    def test_custom_item_mask_preserves_field_identity_order(self) -> None:
        def configure(mechanics) -> None:
            items = mechanics["items"]
            items["value"] = "custom"
            items["custom"]["availability"] = "less"
            for _code, key, _label in FIELD_ITEMS:
                items["custom"][key] = False
            items["custom"][FIELD_ITEMS[0][1]] = True
            items["custom"][FIELD_ITEMS[-1][1]] = True

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

    def test_disabling_items_removes_its_runtime_fragment(self) -> None:
        selection = self._selection(
            lambda mechanics: mechanics.__setitem__("items", False)
        )
        self.assertIsNone(
            items_settings_fragment(
                selection,
                owner="settings.runtime_injector",
            )
        )


if __name__ == "__main__":
    unittest.main()
