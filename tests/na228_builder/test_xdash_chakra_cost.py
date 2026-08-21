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


class XdashChakraCostTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repository = Path(__file__).resolve().parents[2]
        cls.builder = cls.repository / "na228_builder"
        cls.catalog_path = cls.builder / "catalog"
        cls.configurations = cls.builder / "configurations"

    def test_base_configuration_encodes_one_chakra(self) -> None:
        selection = catalog.load_selection(
            self.catalog_path,
            self.configurations / "base.json",
        )
        fragment = xdash_chakra_cost_fragment(
            selection,
            owner="battle_logic.runtime_injector",
        )
        self.assertIsNotNone(fragment)
        assert fragment is not None
        self.assertEqual(struct.unpack("<f", fragment.payload), (1.0,))

    def test_false_disables_the_fragment(self) -> None:
        base = json.loads(
            (self.configurations / "base.json").read_text(encoding="utf-8")
        )
        base["features"]["battle_logic"]["xdash_chakra_cost"] = False
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
                owner="battle_logic.runtime_injector",
            )
        )

    def test_catalog_rejects_cost_outside_the_chakra_gauge(self) -> None:
        base = json.loads(
            (self.configurations / "base.json").read_text(encoding="utf-8")
        )
        with tempfile.TemporaryDirectory() as directory:
            configuration_path = Path(directory) / "invalid.json"
            for value in (-0.5, 15.5):
                with self.subTest(value=value):
                    base["features"]["battle_logic"]["xdash_chakra_cost"] = value
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

        assembly = injection["payload"]["xdash_chakra_cost_abi"]
        self.assertEqual(
            assembly["path"],
            "src/battle_logic/xdash_chakra_cost_abi.S",
        )
        compiled = dict(
            catalog._compile_source(
                self.repository,
                "battle_logic.runtime_injector",
                "xdash_chakra_cost_abi",
                assembly,
                "xdash_chakra_cost_abi",
            )
        )
        shim = compiled[114]
        self.assertEqual(
            shim.payload.hex().upper(),
            "F0FFBD270000BFAF0400A4AF0000000C000000000400A48F"
            "A038080C000000000000BF8F1000BD270800E00300000000",
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
