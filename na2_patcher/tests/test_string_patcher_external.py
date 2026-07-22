from __future__ import annotations

import struct
import unittest
from pathlib import Path

from na2_patcher.modules.binary_patcher import engine as binary_patcher
from na2_patcher.modules.string_patcher import engine as string_patcher
from na2_patcher.modules.translation_importer import engine as translation_importer
from na2_patcher.project_paths import load_project_paths


class IntegratedExternalStringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repository = Path(__file__).resolve().parents[2]
        paths = load_project_paths(cls.repository)
        cls.roots = {
            "na2": paths.path("source_na2"),
            "nun5": paths.path("source_nun5"),
        }
        cls.package = (
            cls.repository
            / "na2_patcher"
            / "features"
            / "localization"
            / "string_patcher"
        )
        cls.import_plan = translation_importer.build_translation_import_plan(
            na2_folder=cls.roots["na2"],
            nun5_folder=cls.roots["nun5"],
            data_root=cls.package.parent / "translation_importer",
            apply="BTL,ETC,SLPS",
        )
        cls.plan = string_patcher.build_translation_plan(
            cls.package,
            translation_plan=cls.import_plan,
        )

    def test_generates_one_pinned_compact_mod(self) -> None:
        self.assertEqual(list(self.plan.insertions), ["PRG/228.BIN"])
        mod = self.plan.insertions["PRG/228.BIN"]
        self.assertEqual(len(mod), 0x760)
        self.assertEqual(
            binary_patcher.data_sha256(mod),
            "FE1032F45EF3645D3971B9225718470FA6BF2C4303FC7F964CCAD74D51DB90FC",
        )
        self.assertEqual(
            struct.unpack_from("<4s7I", mod, 0),
            (
                b"MWo3",
                8,
                0x008F3D00,
                0x40,
                0x710,
                0,
                0x008F4460,
                0x008F4460,
            ),
        )
        self.assertEqual(mod[0x20:0x28], b"228.bin\0")
        self.assertEqual(struct.unpack_from("<II", mod, 0x40), (0x03E00008, 0))

    def test_pool_contains_only_referenced_strings_and_deduplicates_one_pair(self) -> None:
        summary = self.plan.summary["external_strings"]
        self.assertEqual(summary["count"], 31)
        self.assertEqual(summary["distinct"], 30)
        self.assertEqual(summary["encoded_bytes"], 1572)
        self.assertEqual(summary["derived"], 4)
        rows = {row["mapping_id"]: row for row in summary["rows"]}
        self.assertEqual(rows["M2003"]["runtime_address"], rows["M2065"]["runtime_address"])
        self.assertGreaterEqual(
            min(int(row["file_offset"], 0) for row in rows.values()),
            0x100,
        )

    def test_omits_shortened_inline_writes_and_compiles_external_edits(self) -> None:
        shortening = {
            str(row["id"]): row
            for row in self.import_plan.text_mappings
            if row["mode"] == "shorten"
        }
        self.assertEqual(len(shortening), 33)
        self.assertEqual(self.plan.summary["inline_shortening_imports_omitted"], 33)
        self.assertEqual(
            self.plan.summary["edits_by_kind"],
            {"loader": 3, "memory_layout": 12, "redirect_pointer": 35},
        )
        self.assertEqual(self.plan.summary["external_binary_edits"], 50)
        external_patch_ids = {
            patch.patch_id
            for patch in self.plan.package.patches.values()
            if patch.group_id == "external_strings"
        }
        self.assertEqual(len(external_patch_ids), 50)
        for mapping_id, mapping in shortening.items():
            path = translation_importer.TARGET_SPECS[str(mapping["target"])][0]
            start = int(mapping["target_offset"])
            end = start + int(mapping["capacity"])
            for edit in self.plan.package.edits:
                target = self.plan.package.targets[edit.destination_target_id]
                edit_end = edit.destination_offset + edit.length
                self.assertFalse(
                    target.path.as_posix() == path
                    and edit.destination_offset < end
                    and start < edit_end,
                    mapping_id,
                )

    def test_external_edits_are_guarded_by_clean_targets(self) -> None:
        clean_by_path = {
            translation_importer.TARGET_SPECS[target][0]: payload
            for target, payload in self.import_plan.clean_targets.items()
        }
        for edit in self.plan.external_plan.edits:
            clean = clean_by_path[edit.path]
            self.assertEqual(
                clean[edit.offset : edit.offset + len(edit.expected)],
                edit.expected,
                edit.mapping_id,
            )
            self.assertEqual(len(edit.expected), len(edit.replacement))
        self.assertNotIn(
            "PRG/ADV.BIN", {edit.path for edit in self.plan.external_plan.edits}
        )

    def test_bootstrap_loads_compact_mod_and_preserves_constructor(self) -> None:
        by_id = {edit.mapping_id: edit for edit in self.plan.external_plan.edits}
        hook = by_id["ELF-XT-HOOK"]
        self.assertEqual(struct.unpack("<I", hook.expected)[0], 0x0C06F694)
        self.assertEqual(struct.unpack("<I", hook.replacement)[0], 0x0C181CC5)
        cave = by_id["ELF-XT-BOOTSTRAP"].replacement
        self.assertEqual(cave[-8:], b"228.BIN\0")
        words = struct.unpack_from("<17I", cave, 0)
        self.assertEqual(words[6], 0x0C06F9FC)
        self.assertEqual(words[8], 0x0C23CF50)
        self.assertEqual(words[11], 0x0C06F694)
        self.assertEqual(words[15], 0x03E00008)
        slot = by_id["ELF-XT-LOAD-SLOTS"]
        self.assertEqual(slot.replacement, struct.pack("<I", 0x008F3D00))


if __name__ == "__main__":
    unittest.main()
