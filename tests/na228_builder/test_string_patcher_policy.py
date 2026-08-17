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


def linked_plan(
    *,
    mappings: tuple[dict[str, object], ...],
    resolved_texts: dict[str, str],
    references: tuple[translation_importer.Reference, ...] = (),
    clean: bytes,
) -> translation_importer.TranslationImportPlan:
    return translation_importer.TranslationImportPlan(
        import_rows=[],
        targets={},
        text_mappings=mappings,
        references=references,
        resolved_texts=resolved_texts,
        resolved_sequences={},
        source_texts={},
        donor_texts={},
        materialized_templates={},
        clean_targets={"BTL": clean},
        summary={"active_mapping_coverage": {}},
    )


def text_mapping(
    mapping_id: str,
    *,
    offset: int,
    capacity: int,
    source: str,
    donor_ref: str = "donor",
    transform: str = "",
) -> dict[str, object]:
    return {
        "id": mapping_id,
        "target": "BTL",
        "target_offset": offset,
        "capacity": capacity,
        "mode": "slot",
        "source": source,
        "donor_ref": donor_ref,
        "transform": transform,
        "replacement": "",
        "prefix": "",
        "display_context": "test",
    }


class StringPatcherPolicyTests(unittest.TestCase):
    def test_catalog_policy_uses_settings_product_title(self) -> None:
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


class LinkedStringTests(unittest.TestCase):
    def test_declared_reference_does_not_externalize_text_that_fits_inline(self) -> None:
        clean = bytearray(32)
        clean[:4] = b"A\0\0\0"
        clean[16:20] = (0x1000).to_bytes(4, "little")
        reference = translation_importer.Reference(
            mapping_id="M1",
            target="BTL",
            target_file_offset=0,
            target_runtime_address=0x1000,
            resolution="direct",
            reference_binary="BTL",
            reference_file_offsets=(16,),
            parent_mapping_id=None,
            parent_file_offset=None,
            parent_runtime_address=None,
        )
        draft = string_patcher.build_translation_draft(
            translation_plan=linked_plan(
                mappings=(
                    text_mapping("M1", offset=0, capacity=4, source="A"),
                ),
                resolved_texts={"M1": "OK"},
                references=(reference,),
                clean=bytes(clean),
            ),
            owner="test.string_patcher",
            title_policy=None,
        )
        self.assertEqual(draft.external_draft.fragments, ())
        self.assertEqual(draft.external_draft.symbolic_patches, ())
        self.assertEqual(draft.external_draft.excluded_mapping_ids, frozenset())

    def test_pointer_specific_alias_externalizes_even_when_text_fits(self) -> None:
        clean = bytearray(32)
        clean[:4] = b"A\0\0\0"
        clean[16:20] = (0x1000).to_bytes(4, "little")
        reference = translation_importer.Reference(
            mapping_id="ALIAS",
            target="BTL",
            target_file_offset=0,
            target_runtime_address=0x1000,
            resolution="direct",
            reference_binary="BTL",
            reference_file_offsets=(16,),
            parent_mapping_id=None,
            parent_file_offset=None,
            parent_runtime_address=None,
        )
        draft = string_patcher.build_translation_draft(
            translation_plan=linked_plan(
                mappings=(
                    text_mapping(
                        "DEFAULT",
                        offset=0,
                        capacity=4,
                        source="A",
                        donor_ref="default",
                    ),
                    text_mapping(
                        "ALIAS",
                        offset=0,
                        capacity=4,
                        source="A",
                        donor_ref="alias",
                    ),
                ),
                resolved_texts={"DEFAULT": "OK", "ALIAS": "NO"},
                references=(reference,),
                clean=bytes(clean),
            ),
            owner="test.string_patcher",
            title_policy=None,
        )
        self.assertEqual(
            draft.external_draft.excluded_mapping_ids,
            frozenset({"ALIAS"}),
        )
        self.assertEqual(
            draft.external_draft.fragments[0].payload,
            b"NO\0",
        )
        self.assertEqual(
            draft.external_draft.symbolic_patches[0].mapping_id,
            "ALIAS",
        )

    def test_empty_shared_slot_supports_only_pointer_specific_aliases(self) -> None:
        clean = bytearray(32)
        clean[16:20] = (0x1000).to_bytes(4, "little")
        clean[20:24] = (0x1000).to_bytes(4, "little")
        references = tuple(
            translation_importer.Reference(
                mapping_id=mapping_id,
                target="BTL",
                target_file_offset=0,
                target_runtime_address=0x1000,
                resolution="direct",
                reference_binary="BTL",
                reference_file_offsets=(reference_offset,),
                parent_mapping_id=None,
                parent_file_offset=None,
                parent_runtime_address=None,
            )
            for mapping_id, reference_offset in (
                ("FIRST", 16),
                ("SECOND", 20),
            )
        )
        draft = string_patcher.build_translation_draft(
            translation_plan=linked_plan(
                mappings=(
                    text_mapping(
                        "FIRST",
                        offset=0,
                        capacity=4,
                        source="",
                        donor_ref="first",
                    ),
                    text_mapping(
                        "SECOND",
                        offset=0,
                        capacity=4,
                        source="",
                        donor_ref="second",
                    ),
                ),
                resolved_texts={"FIRST": "ONE", "SECOND": "TWO"},
                references=references,
                clean=bytes(clean),
            ),
            owner="test.string_patcher",
            title_policy=None,
        )
        self.assertEqual(
            draft.external_draft.excluded_mapping_ids,
            frozenset({"FIRST", "SECOND"}),
        )
        self.assertEqual(
            {fragment.payload for fragment in draft.external_draft.fragments},
            {b"ONE\0", b"TWO\0"},
        )
        self.assertEqual(
            {
                patch.mapping_id
                for patch in draft.external_draft.symbolic_patches
            },
            {"FIRST", "SECOND"},
        )

    def test_shared_slot_without_one_pointer_specific_alias_fails(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "requires one unreferenced inline mapping",
        ):
            string_patcher.build_translation_draft(
                translation_plan=linked_plan(
                    mappings=(
                        text_mapping("FIRST", offset=0, capacity=4, source="A"),
                        text_mapping("SECOND", offset=0, capacity=4, source="A"),
                    ),
                    resolved_texts={"FIRST": "OK", "SECOND": "NO"},
                    clean=b"A\0\0\0",
                ),
                owner="test.string_patcher",
                title_policy=None,
            )

    def test_pointer_specific_alias_cannot_redirect_shared_slot(self) -> None:
        reference = translation_importer.Reference(
            mapping_id="ALIAS",
            target="BTL",
            target_file_offset=0,
            target_runtime_address=0x1000,
            resolution="direct",
            reference_binary="BTL",
            reference_file_offsets=(0,),
            parent_mapping_id=None,
            parent_file_offset=None,
            parent_runtime_address=None,
        )
        with self.assertRaisesRegex(
            ValueError,
            "cannot redirect the shared source slot itself",
        ):
            string_patcher.build_translation_draft(
                translation_plan=linked_plan(
                    mappings=(
                        text_mapping("DEFAULT", offset=0, capacity=4, source="A"),
                        text_mapping("ALIAS", offset=0, capacity=4, source="A"),
                    ),
                    resolved_texts={"DEFAULT": "OK", "ALIAS": "NO"},
                    references=(reference,),
                    clean=(0x1000).to_bytes(4, "little"),
                ),
                owner="test.string_patcher",
                title_policy=None,
            )

    def test_overflow_without_pointer_reference_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "no pointer reference"):
            string_patcher.build_translation_draft(
                translation_plan=linked_plan(
                    mappings=(
                        text_mapping("M1", offset=0, capacity=4, source="A"),
                    ),
                    resolved_texts={"M1": "TOO LONG"},
                    clean=b"A\0\0\0",
                ),
                owner="test.string_patcher",
                title_policy=None,
            )

    def test_structured_family_preserves_nul_fragment_layout(self) -> None:
        clean = bytearray(32)
        clean[:4] = b"A\0\0\0"
        clean[4:8] = b"B\0\0\0"
        clean[16:20] = (0x2000).to_bytes(4, "little")
        reference = translation_importer.Reference(
            mapping_id="CHILD",
            target="BTL",
            target_file_offset=4,
            target_runtime_address=0x2004,
            resolution="structured",
            reference_binary="BTL",
            reference_file_offsets=(16,),
            parent_mapping_id="PARENT",
            parent_file_offset=0,
            parent_runtime_address=0x2000,
        )
        draft = string_patcher.build_translation_draft(
            translation_plan=linked_plan(
                mappings=(
                    text_mapping(
                        "PARENT",
                        offset=0,
                        capacity=4,
                        source="A",
                        transform="split_br",
                    ),
                    text_mapping(
                        "CHILD",
                        offset=4,
                        capacity=4,
                        source="B",
                        transform="split_br",
                    ),
                ),
                resolved_texts={"PARENT": "One", "CHILD": "Second"},
                references=(reference,),
                clean=bytes(clean),
            ),
            owner="test.string_patcher",
            title_policy=None,
        )
        self.assertEqual(len(draft.external_draft.fragments), 1)
        self.assertEqual(
            draft.external_draft.fragments[0].payload,
            b"One\0Second\0\0",
        )
        self.assertEqual(
            draft.external_draft.rows[0]["materialization"],
            "packed_structured_family",
        )


if __name__ == "__main__":
    unittest.main()
