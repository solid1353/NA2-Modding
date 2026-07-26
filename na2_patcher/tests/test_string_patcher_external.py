from __future__ import annotations

import struct
import unittest
from dataclasses import replace
from pathlib import Path

from na2_patcher.composer import resolve_symbolic_patches
from na2_patcher.modules.binary_patcher import engine as binary_patcher
from na2_patcher.modules.string_patcher import engine as string_patcher
from na2_patcher.modules.translation_importer import engine as translation_importer
from na2_patcher.payload_builder import builder as payload_builder
from na2_patcher.payload_builder import integration as payload_integration
from na2_patcher.project_paths import load_project_paths


class IntegratedExternalStringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repository = Path(__file__).resolve().parents[2]
        paths = load_project_paths(cls.repository, allow_missing=True)
        cls.roots = {"na2": paths.path("source_na2")}
        if not all(root.is_dir() for root in cls.roots.values()):
            raise unittest.SkipTest(
                "External string verification requires the extracted NA2 source"
            )
        cls.localization = cls.repository / "na2_patcher/features/localization"
        cls.import_plan = translation_importer.build_translation_import_plan(
            na2_folder=cls.roots["na2"],
            data_root=cls.localization / "translation_importer",
            apply="BTL,ETC,SLPS",
        )
        cls.diagnostic_import_plan = (
            translation_importer.build_mapping_id_import_plan(
                na2_folder=cls.roots["na2"],
                data_root=cls.localization / "translation_importer",
                apply="BTL,ETC,SLPS",
            )
        )
        cls.replacement_import_plan = (
            translation_importer.build_replacement_import_plan(
                na2_folder=cls.roots["na2"],
                data_root=cls.localization / "translation_importer",
                apply="BTL,ETC,SLPS",
            )
        )
        cls.draft = string_patcher.build_translation_draft(
            translation_plan=cls.import_plan,
            owner="localization.string_patcher",
            title_policy=string_patcher.GameTitlePolicy(
                imported_title="Naruto Shippuden: Ultimate Ninja 5",
                output_title="Narutimate Accel v2.28",
                expected_mapping_count=6,
                expected_occurrence_count=7,
            ),
        )
        cls.build = payload_builder.build_resident_payload(
            cls.draft.external_draft.fragments
        )
        cls.resolved = resolve_symbolic_patches(
            cls.build, cls.draft.external_draft.symbolic_patches
        )
        cls.plan = string_patcher.finalize_translation_plan(
            None,
            draft=cls.draft,
            build=cls.build,
            resolved_patches=cls.resolved,
        )
        cls.integration_patches = payload_integration.build_integration_patches(
            cls.build,
            config=payload_builder.load_config(),
            boot_path="SLPS_258.37",
            clean_boot=cls.import_plan.clean_targets["SLPS"],
        )

    def test_shared_builder_produces_the_exact_fit_derived_228_binary(self) -> None:
        mod = self.build.payload
        self.assertEqual(self.build.output_path, "PRG/228.BIN")
        self.assertEqual(len(mod), 0x6F0)
        self.assertEqual(
            binary_patcher.data_sha256(mod),
            "84DD5C72F4B7D7A472EE2E3C69FBB92621A806E04116D281ED734AE61F5D02EF",
        )
        self.assertEqual(
            struct.unpack_from("<4s7I", mod, 0),
            (b"MWo3", 8, 0x008F3D00, 0x40, 0x6A0, 0, 0x008F43F0, 0x008F43F0),
        )
        self.assertEqual(mod[0x20:0x28], b"228.bin\0")
        self.assertEqual(struct.unpack_from("<II", mod, 0x40), (0x03E00008, 0))

    def test_string_patcher_declares_fragments_and_symbolic_pointers_only(self) -> None:
        self.assertEqual(len(self.draft.external_draft.fragments), 28)
        self.assertEqual(len(self.draft.external_draft.symbolic_patches), 33)
        self.assertEqual(len(self.plan.external_plan.resolved_patches), 33)
        self.assertTrue(all(patch.kind == "redirect_pointer" for patch in self.resolved))
        self.assertEqual(self.plan.summary["external_mappings"], 31)
        self.assertEqual(self.plan.summary["external_binary_edits"], 33)
        self.assertEqual(self.plan.summary["compiled_binary_edits"], 2290)

    def test_pool_contains_only_referenced_strings_and_deduplicates_one_pair(self) -> None:
        summary = self.plan.summary["external_strings"]
        self.assertEqual(summary["count"], 29)
        self.assertEqual(summary["distinct"], 28)
        self.assertEqual(summary["encoded_bytes"], 1470)
        self.assertEqual(summary["derived"], 3)
        rows = {row["mapping_id"]: row for row in summary["rows"]}
        self.assertEqual(rows["M2003"]["runtime_address"], rows["M2065"]["runtime_address"])
        self.assertGreaterEqual(min(int(row["file_offset"], 0) for row in rows.values()), 0x100)

    def test_structural_loader_edits_are_owned_by_payload_builder(self) -> None:
        counts: dict[str, int] = {}
        for patch in self.integration_patches:
            counts[patch.kind] = counts.get(patch.kind, 0) + 1
            self.assertEqual(patch.owner, "payload_builder")
        self.assertEqual(counts, {"memory_layout": 12, "loader": 3})
        by_id = {patch.mapping_id: patch for patch in self.integration_patches}
        hook = by_id["ELF-RP-HOOK"]
        self.assertEqual(struct.unpack("<I", hook.expected)[0], 0x0C06F694)
        self.assertEqual(struct.unpack("<I", hook.replacement)[0], 0x0C181CC5)
        self.assertEqual(by_id["ELF-RP-BOOTSTRAP"].replacement[-8:], b"228.BIN\0")
        self.assertEqual(by_id["ELF-RP-LOAD-SLOT"].replacement, struct.pack("<I", 0x008F3D00))

    def test_project_title_policy_reaches_inline_sequence_and_parent_materializations(self) -> None:
        self.assertIn(
            "Naruto Shippuden: Ultimate Ninja 5",
            self.import_plan.materialized_templates["M0823"],
        )
        self.assertEqual(
            self.import_plan.resolved_texts["M0823"],
            "Creating Naruto Shippuden: Ultimate Ninja 5 data",
        )
        self.assertIn(
            "Naruto Shippuden: Ultimate Ninja 5",
            self.import_plan.resolved_sequences["M0829"][2],
        )
        transformed = self.draft.translation_plan
        self.assertIn("Narutimate Accel v2.28", transformed.resolved_texts["M0823"])
        self.assertNotIn(
            "Naruto Shippuden: Ultimate Ninja 5",
            transformed.materialized_templates["M0823"],
        )
        payload_text = self.build.payload.decode("cp1252", "ignore")
        self.assertIn("Narutimate Accel v2.28", payload_text)
        self.assertNotIn("Naruto Shippuden: Ultimate Ninja 5", payload_text)

    def test_full_replacement_is_inline_when_it_fits_despite_reference_inventory(self) -> None:
        self.assertNotIn("M0743", self.draft.external_draft.excluded_mapping_ids)
        mapping = next(
            row
            for row in self.draft.translation_plan.text_mappings
            if row["id"] == "M0743"
        )
        self.assertLess(
            len(self.draft.translation_plan.resolved_texts["M0743"].encode("cp1252")),
            int(mapping["capacity"]),
        )
        self.assertTrue(
            any(
                row["source_mapping_id"] == "M0743"
                for row in self.draft.translation_plan.import_rows
            )
        )

    def test_overflow_without_reference_fails_closed(self) -> None:
        resolved = dict(self.draft.translation_plan.resolved_texts)
        resolved["M0743"] = "X" * 200
        plan = replace(
            self.draft.translation_plan,
            resolved_texts=resolved,
            references=tuple(
                row
                for row in self.draft.translation_plan.references
                if row.mapping_id != "M0743"
            ),
        )
        with self.assertRaisesRegex(ValueError, "no pointer reference"):
            string_patcher.build_translation_draft(
                translation_plan=plan,
                owner="localization.string_patcher",
                title_policy=string_patcher.GameTitlePolicy(
                    imported_title="missing title",
                    output_title="different title",
                    expected_mapping_count=0,
                    expected_occurrence_count=0,
                ),
            )

    def test_canonical_rows_derive_translation_and_placement_state(self) -> None:
        self.assertEqual(len(self.import_plan.text_mappings), 2052)
        self.assertTrue(
            all(row["mode"] in {"slot", "sequence"} for row in self.import_plan.text_mappings)
        )
        self.assertTrue(
            all(not str(row["replacement"]).startswith("[S]") for row in self.import_plan.text_mappings)
        )
        override_rows = [
            row for row in self.import_plan.text_mappings if str(row["replacement"])
        ]
        self.assertEqual(
            [str(row["id"]) for row in override_rows],
            ["M0530", "M0537"],
        )
        self.assertEqual(
            self.import_plan.resolved_texts["M0530"],
            "Press <iconCROSS> to choose item.",
        )
        self.assertEqual(
            self.import_plan.resolved_texts["M0537"],
            "Select an item and press <iconCROSS> to buy.",
        )
        self.assertEqual(len(self.import_plan.references), 32)
        self.assertTrue(
            all(str(row["display_context"]) for row in self.import_plan.text_mappings)
        )
        self.assertTrue(
            all(
                str(row["display_basis"]).startswith(
                    ("seen:", "inferred:", "character:")
                )
                for row in self.import_plan.text_mappings
            )
        )

    def test_rebuild_fixes_confirmed_mapping_defects(self) -> None:
        self.assertEqual(self.import_plan.resolved_texts["M0246"], "Kankuro")
        self.assertEqual(self.import_plan.resolved_texts["M0521"], "Provocation")
        self.assertEqual(
            self.import_plan.resolved_texts["M0522"],
            "Contrasting Pair",
        )
        self.assertNotIn(
            "M0523",
            {str(row["id"]) for row in self.import_plan.text_mappings},
        )
        self.assertEqual(self.import_plan.resolved_texts["M2247"], "MAX")
        self.assertEqual(self.import_plan.resolved_texts["M0550"], "Opponent")

    def test_generic_choice_labels_preserve_official_case(self) -> None:
        self.assertEqual(self.import_plan.resolved_texts["M0566"], "No")
        self.assertEqual(self.import_plan.resolved_texts["M0799"], "Yes")

    def test_rebuild_inventory_is_adjacent_and_translation_free(self) -> None:
        self.assertEqual(len(self.diagnostic_import_plan.text_mappings), 2173)
        self.assertEqual(
            self.import_plan.summary["mappings_sha256"],
            "7601F834646C374F3E89087724726AAE78E9A87A46A5F936CC5C776C4E60C0B6",
        )
        self.assertEqual(
            self.diagnostic_import_plan.summary["rebuild_sha256"],
            "EA6D79AF9A955180498E93783E0F70AB9439E34B195806991D400686D79BD71C",
        )
        self.assertEqual(self.diagnostic_import_plan.donor_texts, {})
        self.assertTrue(
            all(
                not str(row["donor"])
                and not str(row["donor_ref"])
                and tuple(row["legacy_ids"])
                for row in self.diagnostic_import_plan.text_mappings
            )
        )

    def test_mapping_id_display_uses_readable_ids_and_fits_small_slots(self) -> None:
        draft = string_patcher.build_translation_draft(
            translation_plan=self.diagnostic_import_plan,
            owner="localization.string_patcher",
            title_policy=string_patcher.GameTitlePolicy(
                imported_title="unused in diagnostic mode",
                output_title="also unused in diagnostic mode",
                expected_mapping_count=0,
                expected_occurrence_count=0,
            ),
            translation_display="mapping_ids",
        )
        plan = draft.translation_plan
        self.assertEqual(plan.display_mode, "mapping_ids")
        self.assertEqual(plan.resolved_texts["T1"], "T1")
        self.assertEqual(plan.resolved_texts["T5"], "T5")
        self.assertEqual(
            plan.resolved_sequences["T2036"],
            ("T2036.1", "T2036.2", "T2036.3"),
        )
        self.assertEqual(draft.external_draft.fragments, ())
        self.assertEqual(draft.external_draft.symbolic_patches, ())
        diagnostic = plan.summary["diagnostic_display"]
        self.assertEqual(diagnostic["mode"], "mapping_ids")
        self.assertEqual(diagnostic["mapping_count"], 2173)
        self.assertEqual(
            diagnostic["mapping_count"],
            len(plan.resolved_texts) + len(plan.resolved_sequences),
        )

    def test_mapping_id_display_rejects_unknown_mode(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported translation display"):
            string_patcher.build_translation_draft(
                translation_plan=self.import_plan,
                owner="localization.string_patcher",
                title_policy=string_patcher.GameTitlePolicy(
                    imported_title="Naruto Shippuden: Ultimate Ninja 5",
                    output_title="Narutimate Accel v2.28",
                    expected_mapping_count=6,
                    expected_occurrence_count=7,
                ),
                translation_display="guess",
            )

    def test_replacement_display_uses_only_enabled_replacement_rows(self) -> None:
        draft = string_patcher.build_translation_draft(
            translation_plan=self.replacement_import_plan,
            owner="localization.string_patcher",
            title_policy=string_patcher.GameTitlePolicy(
                imported_title="not applied to a partial replacement",
                output_title="also not applied",
                expected_mapping_count=99,
                expected_occurrence_count=99,
            ),
            translation_display="replacement",
        )
        self.assertEqual(draft.translation_plan.display_mode, "replacement")
        self.assertEqual(len(draft.translation_plan.text_mappings), 752)
        self.assertEqual(len(draft.translation_plan.import_rows), 839)
        self.assertEqual(len(draft.external_draft.fragments), 18)
        self.assertEqual(len(draft.external_draft.symbolic_patches), 22)
        self.assertEqual(
            self.replacement_import_plan.summary["table_rows"],
            752,
        )
        self.assertEqual(
            self.replacement_import_plan.summary["inactive_rows"],
            0,
        )
        self.assertEqual(
            self.replacement_import_plan.summary["reference_inventory"][
                "parent_message"
            ],
            1,
        )
        self.assertTrue(
            {"T50", "T2011", "T2042"}.issubset(
                draft.external_draft.excluded_mapping_ids
            )
        )
        self.assertEqual(
            self.replacement_import_plan.resolved_texts["T50"],
            "Difficulty",
        )
        for donorless_id in ("T24", "T30", "T744", "T767"):
            self.assertEqual(
                self.replacement_import_plan.resolved_texts[donorless_id],
                donorless_id,
            )
        save_progress = (
            "Saving to memory card (PS2) in <br>MEMORY CARD slot 1."
            "<br>Please do not remove memory card (PS2), "
            "<br>controller, or reset/switch off the console."
        )
        self.assertEqual(
            self.replacement_import_plan.materialized_templates["T2011"],
            save_progress,
        )
        self.assertEqual(
            self.replacement_import_plan.materialized_templates["T2042"],
            save_progress,
        )
        self.assertEqual(
            self.replacement_import_plan.resolved_texts["T2041"],
            "MEMORY CARD slot 1.",
        )
        self.assertEqual(
            self.replacement_import_plan.resolved_texts["T2015"],
            "Overwrite?",
        )
        self.assertFalse(draft.game_title_policy["applied"])

    def test_title_policy_fails_closed_in_string_patcher(self) -> None:
        with self.assertRaisesRegex(ValueError, "policy coverage differs"):
            string_patcher.build_translation_draft(
                translation_plan=self.import_plan,
                owner="localization.string_patcher",
                title_policy=string_patcher.GameTitlePolicy(
                    imported_title="missing title",
                    output_title="Narutimate Accel v2.28",
                    expected_mapping_count=6,
                    expected_occurrence_count=7,
                ),
            )


if __name__ == "__main__":
    unittest.main()
