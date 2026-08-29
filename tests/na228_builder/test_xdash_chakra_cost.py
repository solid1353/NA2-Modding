from __future__ import annotations

import json
import struct
import tempfile
import unittest
from pathlib import Path

from na228_builder.scripts import catalog
from na228_builder.scripts.battle_settings_runtime import (
    battle_settings_runtime_fragment,
)
from scripts.lib.paths import load_local_paths


class XdashChakraCostTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.paths = load_local_paths(Path(__file__).resolve(), allow_missing=True)
        cls.repository = cls.paths.repository
        cls.builder = cls.paths.path("builder")
        cls.catalog_path = cls.builder / "catalog"
        cls.configurations = cls.builder / "configurations"

    def test_base_runtime_default_is_five_percent(self) -> None:
        selection = catalog.load_selection(
            self.catalog_path,
            self.configurations / "base.json",
        )
        fragment = battle_settings_runtime_fragment(
            selection,
            owner="settings.runtime_injector",
        )
        self.assertIsNotNone(fragment)
        assert fragment is not None
        self.assertEqual(struct.unpack("<6I", fragment.payload)[4], 5)

    def test_runtime_default_preserves_configured_percent(self) -> None:
        base = json.loads(
            (self.configurations / "base.json").read_text(encoding="utf-8")
        )
        with tempfile.TemporaryDirectory() as directory:
            configuration_path = Path(directory) / "normalized.json"
            for percent in (0, 50, 100):
                with self.subTest(percent=percent):
                    base["features"]["settings"]["shared"][
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
                    fragment = battle_settings_runtime_fragment(
                        selection,
                        owner="settings.runtime_injector",
                    )
                    self.assertIsNotNone(fragment)
                    assert fragment is not None
                    self.assertEqual(
                        struct.unpack("<6I", fragment.payload)[4],
                        percent,
                    )

    def test_false_disables_the_shared_runtime_fragment(self) -> None:
        base = json.loads(
            (self.configurations / "base.json").read_text(encoding="utf-8")
        )
        base["features"]["settings"]["shared"] = False
        with tempfile.TemporaryDirectory() as directory:
            configuration_path = Path(directory) / "disabled.json"
            configuration_path.write_text(
                json.dumps(base, indent=2) + "\n",
                encoding="utf-8",
            )
            selection = catalog.load_selection(
                self.catalog_path,
                configuration_path,
            )
        self.assertIsNone(
            battle_settings_runtime_fragment(
                selection,
                owner="settings.runtime_injector",
            )
        )

    def test_catalog_rejects_cost_outside_normalized_gauge(self) -> None:
        base = json.loads(
            (self.configurations / "base.json").read_text(encoding="utf-8")
        )
        with tempfile.TemporaryDirectory() as directory:
            configuration_path = Path(directory) / "invalid.json"
            for value in (-5, 4, 105):
                with self.subTest(value=value):
                    base["features"]["settings"]["shared"][
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
            self.configurations / "base.json",
        )
        injection = selection.injections[
            "i__battle_logic__xdash_chakra_cost"
        ]
        hooks = injection["hooks"]
        self.assertEqual(
            set(hooks),
            {"charge_noncancellable_xdash_before_interrupts"},
        )
        hook = hooks["charge_noncancellable_xdash_before_interrupts"]
        self.assertEqual(hook["target_id"], "na2_elf")
        self.assertEqual(hook["offset"], "0x14DB80")
        self.assertEqual(hook["expected_hex"], "A038080C")
        self.assertEqual(hook["symbol"], "xdash_pre_update_shim")

        source = injection["payload"]["xdash_chakra_cost"]
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

        self.assertIn("xdash_pre_update_shim", source["fragments"])
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
        shim = compiled["xdash_pre_update_shim"]
        self.assertEqual(
            shim.payload.hex().upper(),
            "E0FFBD270000B0FF1000BFFF0000000C2D8080002000013C"
            "80E2213409F820002D2000020000B0DF1000BFDF0800E003"
            "2000BD2700000000",
        )
        self.assertEqual(
            [(0xC, "jal26", "battle_logic_xdash_pre_fighter_update", 0)],
            [
                (item.offset, item.kind, item.symbol, item.addend)
                for item in shim.relocations
            ],
        )
        self.assertEqual(
            injection["payload"]["battle_logic_xdash_charge_state"]["value"],
            "0000000000000000",
        )


if __name__ == "__main__":
    unittest.main()
