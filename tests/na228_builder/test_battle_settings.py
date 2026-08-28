from __future__ import annotations

import json
import struct
import tempfile
import unittest
from pathlib import Path

from na228_builder.scripts import catalog
from na228_builder.scripts.battle_settings import (
    ROW_SIZE,
    SCHEMA_HEADER_SIZE,
    battle_settings_fragment,
)
from scripts.lib.paths import load_local_paths


class BattleSettingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.paths = load_local_paths(Path(__file__).resolve(), allow_missing=True)
        cls.repository = cls.paths.repository
        cls.builder = cls.paths.path("builder")
        cls.catalog_path = cls.builder / "catalog"
        cls.configurations = cls.builder / "configurations"
        cls.selection = catalog.load_selection(
            cls.catalog_path,
            cls.configurations / "base.json",
        )

    def _selection(self, mutate) -> catalog.CatalogSelection:
        base = json.loads(
            (self.configurations / "base.json").read_text(encoding="utf-8")
        )
        mutate(base["features"])
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "configuration.json"
        path.write_text(json.dumps(base), encoding="utf-8")
        return catalog.load_selection(self.catalog_path, path)

    @staticmethod
    def _row_ids(fragment) -> list[int]:
        row_count = struct.unpack_from("<I", fragment.payload)[0]
        return [
            struct.unpack_from(
                "<I",
                fragment.payload,
                SCHEMA_HEADER_SIZE + index * ROW_SIZE,
            )[0]
            for index in range(row_count)
        ]

    def test_base_schema_inserts_substitution_and_omits_ultimate_jutsu(self) -> None:
        fragment = battle_settings_fragment(
            self.selection,
            owner="battle.runtime_injector",
        )
        self.assertIsNotNone(fragment)
        assert fragment is not None
        self.assertEqual(self._row_ids(fragment), [0, 1, 2, 3, 6, 5])
        substitution = struct.unpack_from(
            "<8I",
            fragment.payload,
            SCHEMA_HEADER_SIZE + 4 * ROW_SIZE,
        )
        self.assertEqual(substitution[5:7], (3, 1))
        self.assertEqual(
            [relocation.symbol for relocation in fragment.relocations],
            [
                "substitution_gauge_mode_get",
                "substitution_gauge_mode_set",
                "battle_settings_substitution_label",
                "battle_settings_substitution_help",
                "battle_settings_schema",
                "substitution_gauge_mode_chakra_label",
                "substitution_gauge_mode_gauge_label",
                "substitution_gauge_mode_free_label",
            ],
        )

    def test_enabled_ultimate_jutsu_follows_the_gauge_row(self) -> None:
        selection = self._selection(
            lambda features: features["battle"]["ultimate_jutsu"].__setitem__(
                "contest_disabled", False
            )
        )
        fragment = battle_settings_fragment(
            selection,
            owner="battle.runtime_injector",
        )
        self.assertIsNotNone(fragment)
        assert fragment is not None
        self.assertEqual(self._row_ids(fragment), [0, 1, 2, 3, 6, 4, 5])

    def test_contest_only_schema_omits_gauge_and_ultimate_jutsu(self) -> None:
        selection = self._selection(
            lambda features: features["battle"]["substitution"].__setitem__(
                "gauge", False
            )
        )
        fragment = battle_settings_fragment(
            selection,
            owner="battle.runtime_injector",
        )
        self.assertIsNotNone(fragment)
        assert fragment is not None
        self.assertEqual(self._row_ids(fragment), [0, 1, 2, 3, 5])
        self.assertEqual(fragment.relocations, ())

    def test_sources_compile_with_the_selected_runtime_package(self) -> None:
        injection = self.selection.injections["i__battle__settings_rework"]
        c_fragments = dict(
            catalog._compile_source(
                self.repository,
                "battle.runtime_injector",
                "battle_settings",
                injection["payload"]["battle_settings"],
                "battle_settings",
            )
        )
        asm_fragments = dict(
            catalog._compile_source(
                self.repository,
                "battle.runtime_injector",
                "battle_settings_abi",
                injection["payload"]["battle_settings_abi"],
                "battle_settings_abi",
            )
        )
        self.assertIn(
            "battle_settings_draw_backing",
            {fragment.symbol for fragment in c_fragments.values()},
        )
        self.assertIn(
            "battle_settings_value_loop_bridge",
            {fragment.symbol for fragment in asm_fragments.values()},
        )


if __name__ == "__main__":
    unittest.main()
