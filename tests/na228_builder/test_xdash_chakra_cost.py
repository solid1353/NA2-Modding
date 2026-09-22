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


class XdashChakraCostTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.paths = load_local_paths(Path(__file__).resolve(), allow_missing=True)
        cls.builder = cls.paths.path("builder")
        cls.catalog_path = cls.builder / "catalog.modcat"
        cls.configurations = cls.builder / "configurations"

    def test_runtime_default_preserves_configured_percent(self) -> None:
        base = jsonc.loads(
            (self.configurations / "base.jsonc").read_text(encoding="utf-8")
        )
        with tempfile.TemporaryDirectory() as directory:
            configuration_path = Path(directory) / "normalized.jsonc"
            for percent in (0, 50, 100):
                with self.subTest(percent=percent):
                    base["features"]["settings"]["battle_mechanics"][
                        "xdash_chakra_cost"
                    ] = percent
                    configuration_path.write_text(
                        json.dumps(base, indent=2) + "\n",
                        encoding="utf-8",
                    )
                    selection = catalog.load_selection(
                        self.catalog_path,
                        configuration_path,
                    )
                    fragments = battle_settings_runtime_fragments(
                        selection, owner="settings.runtime_injector"
                    )
                    fragment = next(
                        item
                        for item in fragments
                        if item.symbol
                        == "battle_settings_xdash_chakra_cost_default"
                    )
                    self.assertEqual(struct.unpack("<I", fragment.payload)[0], percent)

    def test_false_disables_the_xdash_runtime_fragment(self) -> None:
        base = jsonc.loads(
            (self.configurations / "base.jsonc").read_text(encoding="utf-8")
        )
        base["features"]["settings"]["battle_mechanics"][
            "xdash_chakra_cost"
        ] = False
        with tempfile.TemporaryDirectory() as directory:
            configuration_path = Path(directory) / "disabled.jsonc"
            configuration_path.write_text(
                json.dumps(base, indent=2) + "\n",
                encoding="utf-8",
            )
            selection = catalog.load_selection(
                self.catalog_path,
                configuration_path,
            )
        self.assertNotIn(
            "battle_settings_xdash_chakra_cost_default",
            {
                fragment.symbol
                for fragment in battle_settings_runtime_fragments(
                    selection, owner="settings.runtime_injector"
                )
            },
        )

    def test_catalog_rejects_cost_outside_normalized_gauge(self) -> None:
        base = jsonc.loads(
            (self.configurations / "base.jsonc").read_text(encoding="utf-8")
        )
        with tempfile.TemporaryDirectory() as directory:
            configuration_path = Path(directory) / "invalid.jsonc"
            for value in (-5, 4, 105):
                with self.subTest(value=value):
                    base["features"]["settings"]["battle_mechanics"][
                        "xdash_chakra_cost"
                    ] = value
                    configuration_path.write_text(
                        json.dumps(base, indent=2) + "\n",
                        encoding="utf-8",
                    )
                    with self.assertRaises(catalog.ConfigurationError):
                        catalog.load_selection(
                            self.catalog_path,
                            configuration_path,
                        )


if __name__ == "__main__":
    unittest.main()
