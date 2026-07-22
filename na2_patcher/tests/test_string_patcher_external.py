from __future__ import annotations

import struct
import unittest
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
        paths = load_project_paths(cls.repository)
        cls.roots = {"na2": paths.path("source_na2"), "nun5": paths.path("source_nun5")}
        cls.localization = cls.repository / "na2_patcher/features/localization"
        cls.import_plan = translation_importer.build_translation_import_plan(
            na2_folder=cls.roots["na2"],
            nun5_folder=cls.roots["nun5"],
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
            translation_plan=cls.import_plan,
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

    def test_shared_builder_produces_the_exact_v37_228_binary(self) -> None:
        mod = self.build.payload
        self.assertEqual(self.build.output_path, "PRG/228.BIN")
        self.assertEqual(len(mod), 0x720)
        self.assertEqual(
            binary_patcher.data_sha256(mod),
            "AD94B66F2916C0014A87D110F5807DC0F0F5D7E91615AE3F04EC970CFBA00E9F",
        )
        self.assertEqual(
            struct.unpack_from("<4s7I", mod, 0),
            (b"MWo3", 8, 0x008F3D00, 0x40, 0x6D0, 0, 0x008F4420, 0x008F4420),
        )
        self.assertEqual(mod[0x20:0x28], b"228.bin\0")
        self.assertEqual(struct.unpack_from("<II", mod, 0x40), (0x03E00008, 0))

    def test_string_patcher_declares_fragments_and_symbolic_pointers_only(self) -> None:
        self.assertEqual(len(self.draft.external_draft.fragments), 30)
        self.assertEqual(len(self.draft.external_draft.symbolic_patches), 35)
        self.assertEqual(len(self.plan.external_plan.resolved_patches), 35)
        self.assertTrue(all(patch.kind == "redirect_pointer" for patch in self.resolved))
        self.assertEqual(self.plan.summary["inline_shortening_imports_omitted"], 33)
        self.assertEqual(self.plan.summary["external_binary_edits"], 35)
        self.assertEqual(self.plan.summary["compiled_binary_edits"], 2434)

    def test_pool_contains_only_referenced_strings_and_deduplicates_one_pair(self) -> None:
        summary = self.plan.summary["external_strings"]
        self.assertEqual(summary["count"], 31)
        self.assertEqual(summary["distinct"], 30)
        self.assertEqual(summary["encoded_bytes"], 1512)
        self.assertEqual(summary["derived"], 4)
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
            self.import_plan.source_templates["M0823"],
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

    def test_startup_choice_labels_are_uppercase(self) -> None:
        self.assertEqual(self.import_plan.resolved_texts["M0566"], "NO")
        self.assertEqual(self.import_plan.resolved_texts["M0799"], "YES")

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
