from __future__ import annotations

import json
import struct
import tempfile
import unittest
from pathlib import Path

from na228_builder.scripts import catalog
from na228_builder.scripts.character_overrides import load_character_overrides
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
        cls.awakening_ids = load_character_overrides(
            cls.configurations / "dev.json",
            cls.builder,
        ).awakening_ids_by_character()

    def test_disabled_bootstrap_emits_no_fragment(self) -> None:
        selection = catalog.load_selection(
            self.catalog_path,
            self.configurations / "dev.json",
        )
        self.assertIsNone(
            practice_bootstrap_fragment(
                selection,
                owner="qol.runtime_injector",
                awakening_ids_by_character=self.awakening_ids,
            )
        )

    def test_none_and_character_specific_awakening_ids_encode_directly(self) -> None:
        base = json.loads(
            (self.configurations / "base.json").read_text(encoding="utf-8")
        )
        with tempfile.TemporaryDirectory() as directory:
            configuration_path = Path(directory) / "bootstrap.json"
            for p1, awakening, effect_id in (
                (84, "none", PRACTICE_BOOTSTRAP_NO_AWAKENING),
                (84, "0x57", 0x57),
                (92, "0x61", 0x61),
                (92, "0X62", 0x62),
            ):
                with self.subTest(p1=p1, awakening=awakening):
                    base["features"]["qol"]["practice"]["bootstrap"] = {
                        "p1": p1,
                        "support": "0x1F",
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
                        selection,
                        owner="qol.runtime_injector",
                        awakening_ids_by_character=self.awakening_ids,
                    )
                    self.assertIsNotNone(fragment)
                    assert fragment is not None
                    self.assertEqual(
                        struct.unpack("<4I", fragment.payload),
                        (1, p1, 0x1F, effect_id),
                    )

    def test_rejects_unknown_characters_and_mismatched_awakening_ids(self) -> None:
        base = json.loads(
            (self.configurations / "base.json").read_text(encoding="utf-8")
        )
        cases = (
            (84, "0x24", "is not valid for p1 character ID 84"),
            (84, "0x89", "is not valid for p1 character ID 84"),
            (8, "none", "p1 character ID 8 is unknown"),
        )
        with tempfile.TemporaryDirectory() as directory:
            configuration_path = Path(directory) / "bootstrap.json"
            for p1, awakening, expected in cases:
                with self.subTest(p1=p1, awakening=awakening):
                    base["features"]["qol"]["practice"]["bootstrap"] = {
                        "p1": p1,
                        "support": "0x1F",
                        "awakening": awakening,
                    }
                    configuration_path.write_text(
                        json.dumps(base, indent=2) + "\n",
                        encoding="utf-8",
                    )
                    selection = catalog.load_selection(
                        self.catalog_path,
                        configuration_path,
                    )
                    with self.assertRaisesRegex(ValueError, expected):
                        practice_bootstrap_fragment(
                            selection,
                            owner="qol.runtime_injector",
                            awakening_ids_by_character=self.awakening_ids,
                        )

    def test_requires_hexadecimal_support_and_awakening_strings(self) -> None:
        base = json.loads(
            (self.configurations / "base.json").read_text(encoding="utf-8")
        )
        cases = (
            ("31", "none", "support must be a hexadecimal support ID"),
            ("0x26", "none", "support must be a hexadecimal support ID"),
            ("0x18", "87", "awakening must be a hexadecimal awakening ID"),
            ("0x18", "0x8A", "awakening must be a hexadecimal awakening ID"),
        )
        with tempfile.TemporaryDirectory() as directory:
            configuration_path = Path(directory) / "bootstrap.json"
            for support, awakening, expected in cases:
                with self.subTest(support=support, awakening=awakening):
                    base["features"]["qol"]["practice"]["bootstrap"] = {
                        "p1": 84,
                        "support": support,
                        "awakening": awakening,
                    }
                    configuration_path.write_text(
                        json.dumps(base, indent=2) + "\n",
                        encoding="utf-8",
                    )
                    selection = catalog.load_selection(
                        self.catalog_path,
                        configuration_path,
                    )
                    with self.assertRaisesRegex(ValueError, expected):
                        practice_bootstrap_fragment(
                            selection,
                            owner="qol.runtime_injector",
                            awakening_ids_by_character=self.awakening_ids,
                        )

    def test_catalog_rejects_numeric_support_and_awakening_ids(self) -> None:
        base = json.loads(
            (self.configurations / "base.json").read_text(encoding="utf-8")
        )
        cases = (
            (31, "none"),
            ("0x18", 87),
        )
        with tempfile.TemporaryDirectory() as directory:
            configuration_path = Path(directory) / "bootstrap.json"
            for support, awakening in cases:
                with self.subTest(support=support, awakening=awakening):
                    base["features"]["qol"]["practice"]["bootstrap"] = {
                        "p1": 84,
                        "support": support,
                        "awakening": awakening,
                    }
                    configuration_path.write_text(
                        json.dumps(base, indent=2) + "\n",
                        encoding="utf-8",
                    )
                    with self.assertRaises(catalog.ConfigurationError):
                        catalog.load_selection(
                            self.catalog_path,
                            configuration_path,
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
