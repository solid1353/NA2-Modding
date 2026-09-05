from __future__ import annotations

import json
import struct
import tempfile
import unittest
from pathlib import Path

from na228_builder.scripts import catalog, jsonc
from na228_builder.scripts.battle_settings_runtime import (
    battle_settings_runtime_fragments,
)
from scripts.lib.paths import load_local_paths


class XdashChakraCostTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.paths = load_local_paths(Path(__file__).resolve(), allow_missing=True)
        cls.repository = cls.paths.repository
        cls.builder = cls.paths.path("builder")
        cls.catalog_path = cls.builder / "catalog.modcat"
        cls.configurations = cls.builder / "configurations"

    def test_base_runtime_default_is_five_percent(self) -> None:
        selection = catalog.load_selection(
            self.catalog_path,
            self.configurations / "base.jsonc",
        )
        fragments = battle_settings_runtime_fragments(
            selection, owner="settings.runtime_injector"
        )
        fragment = next(
            item
            for item in fragments
            if item.symbol == "battle_settings_xdash_chakra_cost_default"
        )
        self.assertEqual(struct.unpack("<I", fragment.payload)[0], 5)

    def test_runtime_default_preserves_configured_percent(self) -> None:
        base = jsonc.loads(
            (self.configurations / "base.jsonc").read_text(encoding="utf-8")
        )
        with tempfile.TemporaryDirectory() as directory:
            configuration_path = Path(directory) / "normalized.jsonc"
            for percent in (0, 50, 100):
                with self.subTest(percent=percent):
                    base["features"]["settings"]["ingame"]["battle_mechanics"][
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
        base["features"]["settings"]["ingame"]["battle_mechanics"][
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
                    base["features"]["settings"]["ingame"]["battle_mechanics"][
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

    def test_hook_charges_the_first_persisted_movement_update(self) -> None:
        selection = catalog.load_selection(
            self.catalog_path,
            self.configurations / "base.jsonc",
        )
        injection = selection.injections["settings.ingame"]
        hooks = injection["hooks"]
        self.assertEqual(
            hooks["update_shared_fighter_settings"],
            {
                "description": (
                    "Preserve the native per-fighter update while applying "
                    "shared X-dash charging before it and the selected Chakra "
                    "behavior after it."
                ),
                "target_id": "na2_elf",
                "offset": "0x14DB80",
                "expected_hex": "A038080C",
                "symbol": "settings_fighter_update_shim",
                "encoding": "jal26",
            },
        )

        shared_update = injection["payload"]["fighter_update"]
        self.assertEqual(
            shared_update["imports"]["battle_logic_xdash_pre_fighter_update"],
            "battle_logic_xdash_pre_fighter_update",
        )

        xdash = selection.injections[
            "settings.battle_mechanics.xdash_chakra_cost"
        ]
        source = xdash["payload"]["xdash_chakra_cost"]
        self.assertEqual(
            source["path"],
            "src/battle_logic/xdash_chakra_cost.c",
        )
        self.assertEqual(
            source["imports"]["xdash_chakra_cost_get"],
            "xdash_chakra_cost_get",
        )
        self.assertEqual(
            source["imports"]["battle_logic_xdash_charge_state"],
            "battle_logic_xdash_charge_state",
        )

        self.assertIn("battle_logic_xdash_pre_fighter_update", source["fragments"])
        compiled = {
            fragment.symbol: fragment
            for fragment in catalog._compile_source(
                self.repository,
                "battle.runtime_injector",
                "xdash_chakra_cost",
                source,
                "xdash_chakra_cost",
            )
        }
        function = compiled["battle_logic_xdash_pre_fighter_update"]
        self.assertGreater(len(function.payload), 0)
        self.assertEqual(
            xdash["payload"]["battle_logic_xdash_charge_state"]["value"],
            "0000000000000000",
        )


if __name__ == "__main__":
    unittest.main()
