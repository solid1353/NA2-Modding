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


class SubstitutionActiveFramesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.paths = load_local_paths(Path(__file__).resolve(), allow_missing=True)
        cls.repository = cls.paths.repository
        cls.builder = cls.paths.path("builder")
        cls.catalog_path = cls.builder / "catalog.modcat"
        cls.configurations = cls.builder / "configurations"

    def _selection_with(self, value: object) -> catalog.CatalogSelection:
        base = jsonc.loads(
            (self.configurations / "base.jsonc").read_text(encoding="utf-8")
        )
        base["features"]["settings"]["ingame"]["battle_mechanics"][
            "sub_active_frames"
        ] = value
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "configuration.jsonc"
        path.write_text(json.dumps(base, indent=2) + "\n", encoding="utf-8")
        return catalog.load_selection(self.catalog_path, path)

    def test_base_runtime_config_uses_five_active_frames(self) -> None:
        selection = catalog.load_selection(
            self.catalog_path,
            self.configurations / "base.jsonc",
        )
        fragments = battle_settings_runtime_fragments(
            selection,
            owner="settings.runtime_injector",
        )
        fragment = next(
            item
            for item in fragments
            if item.symbol == "battle_settings_sub_active_frames_default"
        )
        self.assertEqual(struct.unpack("<I", fragment.payload)[0], 5)

    def test_catalog_accepts_the_active_frame_boundaries(self) -> None:
        for value in ("default", 1, 15):
            with self.subTest(value=value):
                fragments = battle_settings_runtime_fragments(
                    self._selection_with(value),
                    owner="settings.runtime_injector",
                )
                fragment = next(
                    item
                    for item in fragments
                    if item.symbol == "battle_settings_sub_active_frames_default"
                )
                expected = 0 if value == "default" else value
                self.assertEqual(struct.unpack("<I", fragment.payload)[0], expected)

    def test_catalog_rejects_values_outside_the_active_frame_range(self) -> None:
        for value in (0, 16):
            with self.subTest(value=value):
                with self.assertRaises(catalog.ConfigurationError):
                    self._selection_with(value)

    def test_hook_loads_the_runtime_window_at_the_pre_impact_branch(self) -> None:
        selection = catalog.load_selection(
            self.catalog_path,
            self.configurations / "base.jsonc",
        )
        injection = selection.injections[
            "settings.battle_mechanics.sub_active_frames"
        ]
        self.assertEqual(
            injection["hooks"]["select_substitution_active_history"],
            {
                "description": (
                    "Resume native random and clamped timing for Default, or "
                    "convert the selected total window to prior-history frames "
                    "and rejoin the guard-age and history checks."
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
