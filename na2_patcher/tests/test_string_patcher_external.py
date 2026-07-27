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
        self.assertEqual(len(mod), 0x6E0)
        self.assertEqual(
            binary_patcher.data_sha256(mod),
            "A6E4015FE78252234E0A7E121309D642B13EFE5AC167B5B7044B59CA30F03735",
        )
        self.assertEqual(
            struct.unpack_from("<4s7I", mod, 0),
            (b"MWo3", 8, 0x008F3D00, 0x40, 0x690, 0, 0x008F43E0, 0x008F43E0),
        )
        self.assertEqual(mod[0x20:0x28], b"228.bin\0")
        self.assertEqual(struct.unpack_from("<II", mod, 0x40), (0x03E00008, 0))

    def test_string_patcher_declares_fragments_and_symbolic_pointers_only(self) -> None:
        self.assertEqual(len(self.draft.external_draft.fragments), 30)
        self.assertEqual(len(self.draft.external_draft.symbolic_patches), 35)
        self.assertEqual(len(self.plan.external_plan.resolved_patches), 35)
        self.assertTrue(all(patch.kind == "redirect_pointer" for patch in self.resolved))
        self.assertEqual(self.plan.summary["external_mappings"], 33)
        self.assertEqual(self.plan.summary["external_binary_edits"], 35)
        self.assertEqual(self.plan.summary["compiled_binary_edits"], 2309)

    def test_pool_contains_only_referenced_strings_and_deduplicates_one_pair(self) -> None:
        summary = self.plan.summary["external_strings"]
        self.assertEqual(summary["count"], 31)
        self.assertEqual(summary["distinct"], 30)
        self.assertEqual(summary["encoded_bytes"], 1440)
        self.assertEqual(summary["derived"], 3)
        rows = {row["mapping_id"]: row for row in summary["rows"]}
        self.assertEqual(rows["T364"]["runtime_address"], rows["T117"]["runtime_address"])
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
            self.import_plan.materialized_templates["T2048"],
        )
        self.assertEqual(
            self.import_plan.resolved_texts["T2048"],
            "Creating Naruto Shippuden: Ultimate Ninja 5 data",
        )
        self.assertIn(
            "Naruto Shippuden: Ultimate Ninja 5",
            self.import_plan.resolved_sequences["T2055"][2],
        )
        transformed = self.draft.translation_plan
        self.assertIn("Narutimate Accel v2.28", transformed.resolved_texts["T2048"])
        self.assertNotIn(
            "Naruto Shippuden: Ultimate Ninja 5",
            transformed.materialized_templates["T2048"],
        )
        payload_text = self.build.payload.decode("cp1252", "ignore")
        self.assertIn("Narutimate Accel v2.28", payload_text)
        self.assertNotIn("Naruto Shippuden: Ultimate Ninja 5", payload_text)

    def test_parent_messages_preserve_the_original_nul_fragment_layout(self) -> None:
        payload_by_symbol = {
            fragment.symbol: fragment.payload
            for fragment in self.draft.external_draft.fragments
        }
        rows = {
            str(row["mapping_id"]): row
            for row in self.draft.external_draft.rows
        }
        families = {
            "T2011": ("T2011", "T2041", "T2042"),
            "T2043": ("T2043", "T2044", "T2045"),
            "T2048": ("T2048", "T2049", "T2050"),
        }
        for parent_id, member_ids in families.items():
            expected = (
                b"".join(
                    self.draft.translation_plan.resolved_texts[mapping_id].encode(
                        "cp1252"
                    )
                    + b"\0"
                    for mapping_id in member_ids
                )
                + b"\0"
            )
            symbol = f"localization.string_patcher.string.{parent_id}"
            self.assertEqual(payload_by_symbol[symbol], expected)
            self.assertEqual(expected.count(b"\0"), 4)
            self.assertEqual(
                rows[parent_id]["materialization"],
                "packed_structured_family",
            )

    def test_ninja_song_positional_donors_preserve_printf_slots(self) -> None:
        mappings = {
            str(row["id"]): row for row in self.draft.translation_plan.text_mappings
        }
        for mapping_id in ("T87", "T88", "T92", "T94", "T95", "T96"):
            row = mappings[mapping_id]
            adapted = translation_importer.adapt_source_markup(
                self.draft.translation_plan.resolved_texts[mapping_id],
                str(row["source"]),
                mapping_id,
            )
            self.assertNotIn("%1", adapted)
            self.assertEqual(adapted.count("%s"), 1)

    def test_full_replacement_is_inline_when_it_fits_despite_reference_inventory(self) -> None:
        self.assertNotIn("T65", self.draft.external_draft.excluded_mapping_ids)
        mapping = next(
            row
            for row in self.draft.translation_plan.text_mappings
            if row["id"] == "T65"
        )
        self.assertLess(
            len(self.draft.translation_plan.resolved_texts["T65"].encode("cp1252")),
            int(mapping["capacity"]),
        )
        self.assertTrue(
            any(
                row["source_mapping_id"] == "T65"
                for row in self.draft.translation_plan.import_rows
            )
        )

    def test_overflow_without_reference_fails_closed(self) -> None:
        resolved = dict(self.draft.translation_plan.resolved_texts)
        resolved["T65"] = "X" * 200
        plan = replace(
            self.draft.translation_plan,
            resolved_texts=resolved,
            references=tuple(
                row
                for row in self.draft.translation_plan.references
                if row.mapping_id != "T65"
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
        self.assertEqual(len(self.import_plan.text_mappings), 2075)
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
            {str(row["id"]) for row in override_rows},
            {"T30", "T1920", "T1958", "T2194", "T2197"},
        )
        self.assertEqual(self.import_plan.resolved_texts["T1920"], "Charge Chakra")
        self.assertEqual(
            {
                mapping_id: self.import_plan.resolved_texts[mapping_id]
                for mapping_id in (
                    "T63",
                    "T64",
                    "T66",
                    "T67",
                    "T2201",
                    "T2202",
                    "T2203",
                    "T2204",
                )
            },
            {
                "T63": "Are you sure you want to quit Battle",
                "T64": "Are you sure you want to quit Practice",
                "T66": " and return to ",
                "T67": "?",
                "T2201": "Character Select",
                "T2202": "Game Mode Select",
                "T2203": "ON",
                "T2204": "OFF",
            },
        )
        inline_mapping_ids = {
            str(row["source_mapping_id"])
            for row in self.draft.translation_plan.import_rows
        }
        self.assertTrue(
            {"T2201", "T2202", "T2203", "T2204"} <= inline_mapping_ids
        )
        self.assertTrue(
            {"T63", "T64"}
            <= {
                str(row["mapping_id"])
                for row in self.draft.external_draft.rows
            }
        )
        self.assertEqual(len(self.import_plan.references), 34)
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

    def test_canonical_mappings_preserve_confirmed_fixes(self) -> None:
        self.assertEqual(self.import_plan.resolved_texts["T443"], "Kankuro")
        self.assertEqual(self.import_plan.resolved_texts["T812"], "Provocation")
        self.assertEqual(
            self.import_plan.resolved_texts["T813"],
            "Contrasting Pair",
        )
        self.assertEqual(self.import_plan.resolved_texts["T2158"], "Warning")
        self.assertEqual(self.import_plan.resolved_texts["T5"], "MAX")
        self.assertEqual(self.import_plan.resolved_texts["T528"], "Opponent")

    def test_generic_choice_labels_preserve_official_case(self) -> None:
        self.assertEqual(self.import_plan.resolved_texts["T2025"], "No")
        self.assertEqual(self.import_plan.resolved_texts["T2026"], "Yes")

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
