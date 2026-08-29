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


class SubstitutionActiveFramesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.paths = load_local_paths(Path(__file__).resolve(), allow_missing=True)
        cls.repository = cls.paths.repository
        cls.builder = cls.paths.path("builder")
        cls.catalog_path = cls.builder / "catalog"
        cls.configurations = cls.builder / "configurations"

    def _selection_with(self, value: object) -> catalog.CatalogSelection:
        base = json.loads(
            (self.configurations / "base.json").read_text(encoding="utf-8")
        )
        base["features"]["settings"]["shared"]["sub_active_frames"] = value
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "configuration.json"
        path.write_text(json.dumps(base, indent=2) + "\n", encoding="utf-8")
        return catalog.load_selection(self.catalog_path, path)

    def test_base_runtime_config_uses_four_active_frames(self) -> None:
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
        self.assertEqual(struct.unpack("<6I", fragment.payload)[3], 4)

    def test_catalog_accepts_the_active_frame_boundaries(self) -> None:
        for value in (0, 16):
            with self.subTest(value=value):
                fragment = battle_settings_runtime_fragment(
                    self._selection_with(value),
                    owner="settings.runtime_injector",
                )
                self.assertIsNotNone(fragment)
                assert fragment is not None
                self.assertEqual(struct.unpack("<6I", fragment.payload)[3], value)

    def test_catalog_rejects_values_outside_the_active_frame_range(self) -> None:
        for value in (-1, 17):
            with self.subTest(value=value):
                with self.assertRaises(catalog.ConfigurationError):
                    self._selection_with(value)

    def test_hook_loads_the_runtime_window_at_the_pre_impact_branch(self) -> None:
        selection = catalog.load_selection(
            self.catalog_path,
            self.configurations / "base.json",
        )
        injection = selection.injections[
            "i__battle_logic__sub_active_frames"
        ]
        self.assertEqual(
            injection["hooks"]["select_substitution_active_history"],
            {
                "description": (
                    "Replace the native attack-authored random and clamped "
                    "timing branch with a wrapper that loads the selected "
                    "number of prior input-history frames and rejoins the "
                    "unchanged guard-age and history checks."
                ),
                "target_id": "na2_elf",
                "offset": "0x1296C8",
                "expected_hex": "1100010600000000",
                "symbol": "battle_logic_substitution_select_active_history",
                "encoding": "j26",
                "replacement_hex": "0000000800000000",
            },
        )
        source = injection["payload"]["substitution_active_frames_abi"]
        self.assertEqual(
            source["imports"],
            {"sub_active_frames_get": "sub_active_frames_get"},
        )
        compiled = {
            fragment.symbol: fragment
            for fragment in catalog._compile_source(
                self.repository,
                "settings.runtime_injector",
                "substitution_active_frames_abi",
                source,
                "substitution_active_frames_abi",
            )
        }
        wrapper = compiled["battle_logic_substitution_select_active_history"]
        self.assertEqual(
            [(item.kind, item.symbol) for item in wrapper.relocations],
            [("jal26", "sub_active_frames_get")],
        )


if __name__ == "__main__":
    unittest.main()
