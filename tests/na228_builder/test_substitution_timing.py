from __future__ import annotations

import json
import struct
import tempfile
import unittest
from pathlib import Path

from na228_builder.modules.binary_patcher import adapters
from na228_builder.scripts import catalog
from na228_builder.scripts.substitution_timing import (
    substitution_frames_after_fragment,
)
from scripts.lib.paths import load_local_paths


class SubstitutionTimingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.paths = load_local_paths(Path(__file__).resolve(), allow_missing=True)
        cls.repository = cls.paths.repository
        cls.builder = cls.paths.path("builder")
        cls.catalog_path = cls.builder / "catalog"
        cls.configurations = cls.builder / "configurations"
        cls.operations = cls.builder / "modules" / "binary_patcher" / "operations"

    def _selection_with(self, name: str, value: object) -> catalog.CatalogSelection:
        base = json.loads(
            (self.configurations / "base.json").read_text(encoding="utf-8")
        )
        base["features"]["battle"]["substitution"][name] = value
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "configuration.json"
        path.write_text(json.dumps(base, indent=2) + "\n", encoding="utf-8")
        return catalog.load_selection(self.catalog_path, path)

    def _before_replacement(
        self, selection: catalog.CatalogSelection
    ) -> str | None:
        package = catalog.load_binary_package(
            selection,
            "battle",
            self.catalog_path / "targets.tsv",
            self.repository,
            self.operations,
        )
        matches = [
            edit
            for edit in package.edits
            if "e__battle_logic__substitution__frames_before" in edit.edit_id
        ]
        if not matches:
            return None
        self.assertEqual(len(matches), 1)
        return matches[0].replacement_hex

    def test_base_encodes_literal_four_frame_windows(self) -> None:
        selection = catalog.load_selection(
            self.catalog_path,
            self.configurations / "base.json",
        )
        self.assertEqual(
            self._before_replacement(selection),
            "1500001004001024",
        )
        fragment = substitution_frames_after_fragment(
            selection,
            owner="battle.runtime_injector",
        )
        self.assertIsNotNone(fragment)
        assert fragment is not None
        self.assertEqual(struct.unpack("<I", fragment.payload), (4,))

    def test_before_adapter_encodes_literal_prior_frame_count(self) -> None:
        expected = "1100010600000000"
        replacements = {
            frames: adapters.apply_adapter(
                "mips_substitution_frames_before", expected, frames
            )
            for frames in (0, 4, 8, 16)
        }
        self.assertEqual(replacements[0], "1500001000001024")
        self.assertEqual(replacements[4], "1500001004001024")
        self.assertEqual(replacements[8], "1500001008001024")
        self.assertEqual(replacements[16], "1500001010001024")

    def test_each_window_is_independently_selectable(self) -> None:
        before_disabled = self._selection_with("frames_before", False)
        self.assertIsNone(self._before_replacement(before_disabled))
        after_disabled = self._selection_with("frames_after", False)
        self.assertIsNone(
            substitution_frames_after_fragment(
                after_disabled,
                owner="battle.runtime_injector",
            )
        )

    def test_catalog_rejects_values_outside_zero_through_sixteen(self) -> None:
        for name in ("frames_before", "frames_after"):
            for value in (-1, 17, 1.5, True):
                with self.subTest(name=name, value=value):
                    with self.assertRaises(catalog.ConfigurationError):
                        self._selection_with(name, value)

    def test_after_hook_wraps_only_the_ordinary_response_driver(self) -> None:
        selection = catalog.load_selection(
            self.catalog_path,
            self.configurations / "base.json",
        )
        injection = selection.injections[
            "i__battle_logic__substitution__frames_after"
        ]
        self.assertEqual(
            set(injection["hooks"]),
            {"retry_substitution_during_initial_hit_response"},
        )
        hook = injection["hooks"][
            "retry_substitution_during_initial_hit_response"
        ]
        self.assertEqual(hook["target_id"], "na2_elf")
        self.assertEqual(hook["offset"], "0x149DF0")
        self.assertEqual(hook["expected_hex"], "68D3080C00000000")
        self.assertEqual(
            hook["symbol"],
            "battle_logic_substitution_update_ordinary_response",
        )
        source = injection["payload"]["substitution_timing_abi"]
        self.assertEqual(
            source["path"],
            "src/battle_logic/substitution_timing_abi.S",
        )
        self.assertEqual(
            source["imports"]["battle_logic_substitution_frames_after"],
            "battle_logic_substitution_frames_after",
        )

    def test_before_adapter_rejects_wrong_guard(self) -> None:
        with self.assertRaisesRegex(ValueError, "native"):
            adapters.apply_adapter(
                "mips_substitution_frames_before",
                "1500001003001024",
                8,
            )


if __name__ == "__main__":
    unittest.main()
