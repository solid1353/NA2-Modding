from __future__ import annotations

import json
import struct
import tempfile
import unittest
from pathlib import Path

from na228_builder.scripts import catalog
from na228_builder.scripts.xdash_chakra_cost import (
    xdash_chakra_cost_fragment,
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

    def test_normalized_base_maps_five_percent_to_native_chakra(self) -> None:
        selection = catalog.load_selection(
            self.catalog_path,
            self.configurations / "base.json",
        )
        fragment = xdash_chakra_cost_fragment(
            selection,
            owner="battle.runtime_injector",
        )
        self.assertIsNotNone(fragment)
        assert fragment is not None
        self.assertEqual(struct.unpack("<f", fragment.payload), (0.75,))

    def test_normalized_cost_maps_to_native_fifteen_point_gauge(self) -> None:
        base = json.loads(
            (self.configurations / "base.json").read_text(encoding="utf-8")
        )
        with tempfile.TemporaryDirectory() as directory:
            configuration_path = Path(directory) / "normalized.json"
            for normalized, native in ((0, 0.0), (50, 7.5), (100, 15.0)):
                with self.subTest(normalized=normalized):
                    base["features"]["battle"][
                        "xdash_chakra_cost"
                    ] = normalized
                    configuration_path.write_text(
                        json.dumps(base, indent=2) + "\n",
                        encoding="utf-8",
                    )
                    selection = catalog.load_selection(
                        self.catalog_path,
                        configuration_path,
                    )
                    fragment = xdash_chakra_cost_fragment(
                        selection,
                        owner="battle.runtime_injector",
                    )
                    self.assertIsNotNone(fragment)
                    assert fragment is not None
                    self.assertEqual(
                        struct.unpack("<f", fragment.payload),
                        (native,),
                    )

    def test_false_disables_the_fragment(self) -> None:
        base = json.loads(
            (self.configurations / "base.json").read_text(encoding="utf-8")
        )
        base["features"]["battle"]["xdash_chakra_cost"] = False
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
            xdash_chakra_cost_fragment(
                selection,
                owner="battle.runtime_injector",
            )
        )

    def test_catalog_rejects_cost_outside_normalized_gauge(self) -> None:
        base = json.loads(
            (self.configurations / "base.json").read_text(encoding="utf-8")
        )
        with tempfile.TemporaryDirectory() as directory:
            configuration_path = Path(directory) / "invalid.json"
            for value in (-0.5, 100.5):
                with self.subTest(value=value):
                    base["features"]["battle"]["xdash_chakra_cost"] = value
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
            source["imports"]["battle_logic_xdash_chakra_cost"],
            "battle_logic_xdash_chakra_cost",
        )
        self.assertEqual(
            source["imports"]["battle_logic_xdash_charge_state"],
            "battle_logic_xdash_charge_state",
        )

        self.assertIn("xdash_pre_update_shim", source["fragments"])
        compiled = dict(
            catalog._compile_source(
                self.repository,
                "battle.runtime_injector",
                "xdash_chakra_cost",
                source,
                "xdash_chakra_cost",
            )
        )
        shim = compiled[114]
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
