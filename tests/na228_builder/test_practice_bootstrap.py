from __future__ import annotations

import json
import struct
import tempfile
import unittest
from pathlib import Path

from na228_builder.scripts import catalog
from na228_builder.scripts.practice_bootstrap import (
    PRACTICE_BOOTSTRAP_NO_AWAKENING,
    practice_bootstrap_fragment,
)


class PracticeBootstrapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repository = Path(__file__).resolve().parents[2]
        cls.builder = cls.repository / "na228_builder"
        cls.catalog_path = cls.builder / "catalog"
        cls.configurations = cls.builder / "configurations"

    def test_only_test_configuration_enables_baseline_bootstrap(self) -> None:
        selections = {
            name: catalog.load_selection(
                self.catalog_path,
                self.configurations / f"{name}.json",
            )
            for name in ("dev", "test", "release")
        }

        for name in ("dev", "release"):
            with self.subTest(configuration=name):
                self.assertIsNone(
                    practice_bootstrap_fragment(
                        selections[name], owner="qol.runtime_injector"
                    )
                )

        fragment = practice_bootstrap_fragment(
            selections["test"], owner="qol.runtime_injector"
        )
        self.assertIsNotNone(fragment)
        assert fragment is not None
        self.assertEqual(fragment.symbol, "practice_bootstrap_configuration")
        self.assertEqual(fragment.kind, "rodata")
        self.assertEqual(
            struct.unpack("<4I", fragment.payload),
            (1, 84, 26, 0xFFFFFFFF),
        )

    def test_none_and_character_specific_awakening_ids_encode_directly(self) -> None:
        base = json.loads(
            (self.configurations / "base.json").read_text(encoding="utf-8")
        )
        with tempfile.TemporaryDirectory() as directory:
            configuration_path = Path(directory) / "bootstrap.json"
            for awakening, effect_id in (
                ("none", PRACTICE_BOOTSTRAP_NO_AWAKENING),
                (0x57, 0x57),
                (0x22, 0x22),
                (0x89, 0x89),
            ):
                with self.subTest(awakening=awakening):
                    base["features"]["qol"]["practice"]["bootstrap"] = {
                        "p1": 83,
                        "support": 31,
                        "awakening": awakening,
                    }
                    configuration_path.write_text(
                        json.dumps(base, indent=2) + "\n",
                        encoding="utf-8",
                    )
                    selection = catalog.load_selection(
                        self.catalog_path, configuration_path
                    )
                    fragment = practice_bootstrap_fragment(
                        selection, owner="qol.runtime_injector"
                    )
                    self.assertIsNotNone(fragment)
                    assert fragment is not None
                    self.assertEqual(
                        struct.unpack("<4I", fragment.payload),
                        (1, 83, 31, effect_id),
                    )

    def test_repository_route_and_runtime_hooks_keep_exact_clean_guards(self) -> None:
        selection = catalog.load_selection(
            self.catalog_path,
            self.configurations / "test.json",
        )
        package = catalog.load_binary_package(
            selection,
            "qol",
            self.catalog_path / "implementation" / "targets.tsv",
            self.repository,
            self.builder / "modules" / "binary_patcher" / "operations",
        )
        route = [
            edit
            for edit in package.edits
            if "e__qol__practice__bootstrap__enter_practice_after_continue"
            in edit.edit_id
        ]
        self.assertEqual(len(route), 1)
        self.assertEqual(route[0].destination_offset, 0xE9BF8)
        self.assertEqual(
            route[0].expected_hex,
            "04000224080002AE0C0004AE2900001000000000",
        )
        self.assertEqual(
            route[0].replacement_hex,
            "04000224080002AE03000224290000100C0002AE",
        )

        injection = selection.injections[
            "i__qol__practice__bootstrap__configured_battle"
        ]
        hooks = injection["hooks"]
        self.assertEqual(
            (hooks["replace_character_select_with_configured_practice_match"]["offset"],
             hooks["replace_character_select_with_configured_practice_match"]["expected_hex"]),
            ("0xECB2C", "14B5070C"),
        )
        self.assertEqual(
            (hooks["apply_configured_awakening_after_battle_start"]["offset"],
             hooks["apply_configured_awakening_after_battle_start"]["expected_hex"]),
            ("0xECBCC", "DCB6070C"),
        )


if __name__ == "__main__":
    unittest.main()
