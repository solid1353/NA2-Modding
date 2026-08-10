from __future__ import annotations

import unittest
from types import SimpleNamespace

from na228_builder.modules.string_patcher import engine as string_patcher
from na228_builder.modules.translation_importer import engine as translation_importer
from na228_builder.scripts import catalog, module_pipeline


def synthetic_plan() -> translation_importer.TranslationImportPlan:
    return translation_importer.TranslationImportPlan(
        import_rows=[],
        targets={},
        text_mappings=(),
        references=(),
        resolved_texts={"first": "Imported Game", "other": "Unchanged"},
        resolved_sequences={"second": ("Imported Game", "Again: Imported Game")},
        source_texts={},
        donor_texts={},
        materialized_templates={"template": "Title: Imported Game"},
        clean_targets={},
        summary={"active_mapping_coverage": {}},
    )


class StringPatcherPolicyTests(unittest.TestCase):
    def test_catalog_policy_uses_root_product_title(self) -> None:
        patch_id = "s__general__replace_imported_game_title"
        selection = SimpleNamespace(
            nodes=(
                catalog.CatalogNode(
                    path=("features", "general", "replace_imported_game_title"),
                    enabled=True,
                    patches=(patch_id,),
                ),
            ),
            string_patches={
                patch_id: {
                    "operation": "replace_imported_game_title",
                    "expected_value": "Imported Game",
                    "expected_mapping_count": 2,
                    "expected_occurrence_count": 3,
                }
            },
        )
        policy = module_pipeline._selected_game_title_policy(
            SimpleNamespace(selection=selection, product_title="Output Game")
        )
        self.assertEqual(
            policy,
            string_patcher.GameTitlePolicy(
                imported_title="Imported Game",
                output_title="Output Game",
                expected_mapping_count=2,
                expected_occurrence_count=3,
            ),
        )

    def test_selected_game_title_policy_replaces_guarded_coverage(self) -> None:
        transformed = string_patcher._apply_game_title_policy(
            synthetic_plan(),
            string_patcher.GameTitlePolicy(
                imported_title="Imported Game",
                output_title="Output Game",
                expected_mapping_count=2,
                expected_occurrence_count=3,
            ),
        )
        self.assertEqual(transformed.resolved_texts["first"], "Output Game")
        self.assertEqual(
            transformed.resolved_sequences["second"],
            ("Output Game", "Again: Output Game"),
        )
        self.assertEqual(
            transformed.materialized_templates["template"], "Title: Output Game"
        )
        self.assertEqual(transformed.resolved_texts["other"], "Unchanged")

    def test_disabled_game_title_policy_leaves_imported_text_unchanged(self) -> None:
        draft = string_patcher.build_translation_draft(
            translation_plan=synthetic_plan(),
            owner="synthetic.string_patcher",
            title_policy=None,
        )
        self.assertEqual(draft.translation_plan.resolved_texts["first"], "Imported Game")
        self.assertEqual(draft.game_title_policy, {"applied": False})

    def test_selected_game_title_policy_rejects_changed_coverage(self) -> None:
        with self.assertRaisesRegex(ValueError, "catalog guard"):
            string_patcher._apply_game_title_policy(
                synthetic_plan(),
                string_patcher.GameTitlePolicy(
                    imported_title="Imported Game",
                    output_title="Output Game",
                    expected_mapping_count=2,
                    expected_occurrence_count=4,
                ),
            )


if __name__ == "__main__":
    unittest.main()
