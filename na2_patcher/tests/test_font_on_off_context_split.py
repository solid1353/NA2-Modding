from __future__ import annotations

import csv
import unittest
from pathlib import Path

from na2_patcher.modules.binary_patcher import engine as binary_engine
from na2_patcher.modules.runtime_injector import engine as runtime_engine
from scripts.research.localization import generate_on_off_context_split


class OnOffContextSplitTests(unittest.TestCase):
    def test_canonical_pointer_patch_matches_the_generator(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        package = binary_engine.load_package(
            repository
            / "na2_patcher"
            / "features"
            / "localization"
            / "binary_patcher"
        )
        patch = package.patches[
            generate_on_off_context_split.PATCH_ID
        ]
        self.assertTrue(patch.enabled)
        self.assertEqual(patch.status, "runtime_proven")
        self.assertEqual(patch.confidence, "verified")
        self.assertEqual(patch.group_id, "auto_fit")

        canonical = [
            edit
            for edit in package.edits
            if edit.patch_id == generate_on_off_context_split.PATCH_ID
        ]
        generated = generate_on_off_context_split.generated_edits()
        self.assertEqual(len(canonical), len(generated))
        for edit, expected in zip(canonical, generated, strict=True):
            self.assertEqual(edit.edit_id, expected["edit_id"])
            self.assertEqual(edit.order, expected["order"])
            self.assertEqual(
                edit.destination_target_id,
                expected["destination_target_id"],
            )
            self.assertEqual(
                edit.destination_offset,
                expected["destination_offset"],
            )
            self.assertEqual(edit.operation, expected["operation"])
            self.assertEqual(edit.length, expected["length"])
            self.assertEqual(edit.expected_hex, expected["expected_hex"])
            self.assertEqual(
                edit.replacement_hex,
                expected["replacement_hex"],
            )

    def test_clean_elf_guards_are_exact(self) -> None:
        btl, elf = generate_on_off_context_split.verify_source()
        self.assertTrue(btl.is_file())
        self.assertTrue(elf.is_file())

    def test_special_controls_uses_dedicated_ascii_mappings_without_hook(
        self,
    ) -> None:
        repository = Path(__file__).resolve().parents[2]
        mappings_path = (
            repository
            / "na2_patcher"
            / "features"
            / "localization"
            / "translation_importer"
            / "mappings.tsv"
        )
        with mappings_path.open(
            "r", encoding="utf-8-sig", newline=""
        ) as handle:
            mappings = {
                row["id"]: row
                for row in csv.DictReader(handle, delimiter="\t")
                if row["id"] in {"T2203", "T2204"}
            }
        self.assertEqual(set(mappings), {"T2203", "T2204"})
        self.assertEqual(
            (
                mappings["T2203"]["source"],
                mappings["T2203"]["donor"],
                mappings["T2203"]["source_ref"],
            ),
            ("Ｏ　Ｎ", "ON", "NA2_SLPS@0x505AF0"),
        )
        self.assertEqual(
            (
                mappings["T2204"]["source"],
                mappings["T2204"]["donor"],
                mappings["T2204"]["source_ref"],
            ),
            ("ＯＦＦ", "OFF", "NA2_SLPS@0x505AF8"),
        )

        package = runtime_engine.load_package(
            repository
            / "na2_patcher"
            / "features"
            / "localization"
            / "runtime_injector",
            owner="localization.runtime_injector",
        )
        controls = package.patches["font_v2_controls"]
        self.assertTrue(controls.enabled)
        self.assertEqual(controls.status, "runtime_proven")
        selector_edits = [
            edit
            for edit in package.edits
            if edit.symbolic_patch.offset == 0x2888D4
        ]
        self.assertEqual(selector_edits, [])

    def test_practice_rows_share_the_existing_titlecase_table(self) -> None:
        edits = [
            edit
            for edit in generate_on_off_context_split.generated_edits()
            if edit["destination_target_id"] == "na2_btl"
        ]
        self.assertEqual(len(edits), 3)
        for edit in edits:
            self.assertEqual(
                edit["replacement_hex"],
                generate_on_off_context_split.TITLECASE_TABLE_POINTER_HEX,
            )


if __name__ == "__main__":
    unittest.main()
