from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from na2_patcher.modules.translation_importer import engine


class TranslationImporterTests(unittest.TestCase):
    def test_iso_source_delegates_to_the_shared_iso_reader(self) -> None:
        exact = SimpleNamespace(path="PRG/BTL.BIN", is_dir=False)
        basename = SimpleNamespace(path="OTHER/ETC.BIN", is_dir=False)
        image = SimpleNamespace(
            by_path={"PRG/BTL.BIN": exact, "OTHER/ETC.BIN": basename},
            read_file=mock.Mock(
                side_effect=lambda record: record.path.encode("ascii")
            ),
        )
        with mock.patch.object(engine, "Iso9660", return_value=image) as iso_type:
            source = engine.IsoSource(Path("source.iso"))
        iso_type.assert_called_once()
        self.assertEqual(
            source.read(("PRG/BTL.BIN",), "BTL"),
            b"PRG/BTL.BIN",
        )
        self.assertEqual(
            source.read(("ETC.BIN",), "ETC"),
            b"OTHER/ETC.BIN",
        )

    def test_rejects_unresolved_mode(self) -> None:
        row = {
            "id": "MTEST",
            "enabled": "1",
            "display_context": "Test screen > value",
            "display_basis": "seen:test-fixture",
            "mode": "unresolved",
            "source_ref": "NA2_SLPS@0",
            "donor_ref": "NUN5_SLES@0",
            "capacity": "8",
            "source": "",
            "donor": "",
            "prefix": "",
            "replacement": "",
            "transform": "",
            "arguments": "",
            "reference_refs": "",
            "parent_mapping_id": "",
        }
        with self.assertRaisesRegex(ValueError, "unsupported mode"):
            engine.parse_mappings([row])

    def test_rejects_missing_display_metadata(self) -> None:
        row = {
            "id": "MTEST",
            "enabled": "1",
            "display_context": "",
            "display_basis": "",
            "mode": "slot",
            "source_ref": "NA2_SLPS@0",
            "donor_ref": "NUN5_SLES@0",
            "capacity": "8",
            "source": "source",
            "donor": "donor",
            "prefix": "",
            "replacement": "",
            "transform": "",
            "arguments": "",
            "reference_refs": "",
            "parent_mapping_id": "",
        }
        with self.assertRaisesRegex(ValueError, "display_context is required"):
            engine.parse_mappings([row])
        row["display_context"] = "Test screen > value"
        with self.assertRaisesRegex(ValueError, "display_basis must begin"):
            engine.parse_mappings([row])

    def test_rejects_placeholder_donor_for_identifier_target(self) -> None:
        with self.assertRaisesRegex(ValueError, "placeholder donor text"):
            engine.validate_semantic_replacement(
                "unknown",
                "pjrvspl0",
                "M1336",
            )

    def test_allows_placeholder_word_for_visible_target(self) -> None:
        self.assertIsNone(
            engine.validate_semantic_replacement(
                "Unknown",
                "<r不明|ふめい>",
                "visible",
            )
        )

    def test_empty_replacement_uses_the_imported_donor(self) -> None:
        row = {
            "donor": "Official translation",
            "prefix": "",
            "replacement": "",
            "transform": "",
            "arguments": {},
        }
        self.assertEqual(
            engine.resolve_replacement_text(row, "MTEST"),
            "Official translation",
        )

    def test_empty_transform_materializes_an_intentionally_empty_string(
        self,
    ) -> None:
        row = {
            "donor": "Unused official fragment",
            "prefix": "",
            "replacement": "",
            "transform": "empty",
            "arguments": {},
        }
        self.assertEqual(
            engine.resolve_replacement_text(row, "M0822"),
            "",
        )

    def test_user_prefix_is_prepended_to_the_selected_translation(self) -> None:
        imported = {
            "donor": "Official translation",
            "prefix": "[P] ",
            "replacement": "",
            "transform": "",
            "arguments": {},
        }
        overridden = {
            **imported,
            "replacement": "User override",
        }
        self.assertEqual(
            engine.resolve_replacement_text(imported, "imported"),
            "[P] Official translation",
        )
        self.assertEqual(
            engine.resolve_replacement_text(overridden, "overridden"),
            "[P] User override",
        )

    def test_user_prefix_is_applied_after_the_transform(self) -> None:
        row = {
            "donor": "First line<br>Second line",
            "prefix": "[P] ",
            "replacement": "",
            "transform": "split_br",
            "arguments": {"part": "1"},
        }
        self.assertEqual(
            engine.resolve_replacement_text(row, "transformed"),
            "[P] Second line",
        )

    def test_literal_format_argument_keeps_replacement_field_empty(self) -> None:
        row = {
            "donor": "Quit %1?",
            "prefix": "",
            "replacement": "",
            "transform": "format_literal_arg1",
            "arguments": {"arg1": "Collection"},
        }
        self.assertEqual(
            engine.resolve_replacement_text(row, "formatted"),
            "Quit Collection?",
        )

    def test_literal_format_argument_can_materialize_through_arg1(self) -> None:
        row = {
            "donor": "Quit %1 and return to %2?",
            "prefix": "",
            "replacement": "",
            "transform": "format_literal_through_arg1",
            "arguments": {"arg1": "Battle"},
        }
        self.assertEqual(
            engine.resolve_replacement_text(row, "formatted-through-arg1"),
            "Quit Battle",
        )

    def test_fullwidth_ascii_is_normalized_only_in_resolved_output(self) -> None:
        row = {
            "donor": "ＭＡＸ　Ｄａｍａｇｅ！",
            "prefix": "［P］ ",
            "replacement": "",
            "transform": "",
            "arguments": {},
        }
        self.assertEqual(
            engine.resolve_replacement_text(row, "normalized"),
            "[P] MAX Damage!",
        )

    def test_fullwidth_ascii_is_normalized_in_donor_reference_arguments(
        self,
    ) -> None:
        row = {
            "donor": "Quit %1?",
            "prefix": "",
            "replacement": "",
            "transform": "format_arg1",
            "arguments": {"arg1": "NUN5_TEXTENG@0x10"},
        }
        self.assertEqual(
            engine.resolve_replacement_text(
                row,
                "normalized-reference",
                {"NUN5_TEXTENG@0x10": "Ｃｏｌｌｅｃｔｉｏｎ"},
            ),
            "Quit Collection?",
        )

    def test_declared_source_must_match_clean_target_text(self) -> None:
        engine.validate_declared_source("最大", "最大", "M2247")
        with self.assertRaisesRegex(ValueError, "does not match clean target"):
            engine.validate_declared_source("最大", "最小", "M2247")

    def test_combined_source_and_pointer_references_are_parsed(self) -> None:
        self.assertEqual(
            engine.parse_source_ref("NA2_BTL@0x1234", "source"),
            ("BTL", 0x1234),
        )
        self.assertEqual(
            engine.parse_reference_refs(
                "NA2_BTL@0x10,NA2_SLPS@0x20",
                "pointers",
            ),
            (("BTL", 0x10), ("SLPS", 0x20)),
        )

    def test_materialization_preserves_the_imported_donor(self) -> None:
        mappings = [
            {
                "id": "MTEST",
                "target": "SLPS",
                "mode": "slot",
                "donor_ref": "NUN5_TEXTENG@0x10",
                "source": "clean Japanese title",
                "donor": "Create Naruto Shippuden: Ultimate Ninja 5 data?",
                "prefix": "",
                "replacement": "",
                "transform": "",
                "arguments": {},
            }
        ]
        resolved, sequences, sources, donors, materialized = (
            engine.resolve_text_materializations(
                mappings,
                {"SLPS"},
            )
        )
        self.assertEqual(sequences, {})
        self.assertEqual(sources["MTEST"], "clean Japanese title")
        self.assertEqual(
            donors["MTEST"],
            "Create Naruto Shippuden: Ultimate Ninja 5 data?",
        )
        self.assertEqual(resolved["MTEST"], donors["MTEST"])
        self.assertEqual(materialized["MTEST"], resolved["MTEST"])

    def test_split_br_is_a_view_of_the_complete_replacement(self) -> None:
        row = {
            "donor": "First line<br>Second line",
            "prefix": "",
            "replacement": "",
            "transform": "split_br",
            "arguments": {"part": "0"},
        }
        self.assertEqual(
            engine.resolve_replacement_text(row, "parent"),
            "First line",
        )

    def test_split_br_rejects_out_of_range_part(self) -> None:
        row = {
            "donor": "First line<br>Second line",
            "prefix": "",
            "replacement": "",
            "transform": "split_br",
            "arguments": {"part": "2"},
        }
        with self.assertRaisesRegex(ValueError, "outside 2 parts"):
            engine.resolve_replacement_text(row, "parent")

    def test_empty_import_log_requires_explicit_replacement_mode_opt_in(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "translation_imports.tsv"
            with self.assertRaisesRegex(
                ValueError,
                "No translation imports were generated",
            ):
                engine.write_import_tsv(path, [])
            engine.write_import_tsv(path, [], allow_empty=True)
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                self.assertEqual(
                    next(csv.reader(handle, delimiter="\t")),
                    [
                        "import_id",
                        "group_id",
                        "path",
                        "offset",
                        "expected_hex",
                        "replacement_hex",
                        "source_text",
                        "replacement_text",
                        "source_mapping_id",
                        "reason",
                    ],
                )


if __name__ == "__main__":
    unittest.main()
