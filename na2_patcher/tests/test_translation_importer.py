from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from na2_patcher.modules import translation_importer
from na2_patcher.modules.translation_importer import engine


class TranslationImporterTests(unittest.TestCase):
    def write_rebuild_rows(
        self,
        path: Path,
        rows: list[dict[str, str]],
    ) -> None:
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=engine.REBUILD_FIELDS,
                delimiter="\t",
                lineterminator="\n",
            )
            writer.writeheader()
            writer.writerows(rows)

    def rebuild_row(self, mapping_id: str, source_ref: str) -> dict[str, str]:
        return {
            "id": mapping_id,
            "display_context": "Unconfirmed > Test",
            "source": "日本語",
            "donor": "",
            "prefix": "",
            "replacement": "",
            "display_basis": "",
            "source_ref": source_ref,
            "donor_ref": "",
            "mode": "slot",
            "capacity": "16",
            "transform": "",
            "arguments": "",
            "reference_refs": "",
            "parent_mapping_id": "",
            "legacy_ids": "M0001",
        }

    def test_package_exports_mapping_id_import_builder(self) -> None:
        self.assertIs(
            translation_importer.build_mapping_id_import_plan,
            engine.build_mapping_id_import_plan,
        )
        self.assertIs(
            translation_importer.build_replacement_import_plan,
            engine.build_replacement_import_plan,
        )

    def test_encountered_replacement_uses_mapping_schema_and_rebuild_guards(
        self,
    ) -> None:
        repository = Path(__file__).resolve().parents[2]
        data_root = (
            repository
            / "na2_patcher/features/localization/translation_importer"
        )
        replacement_raw = engine.read_rows(data_root / "replacement.tsv")
        replacement = engine.parse_mappings(
            replacement_raw,
            table_name="replacement.tsv",
        )
        rebuild = {
            row["id"]: row
            for row in engine.read_rebuild_rows(data_root / "rebuild.tsv")
        }
        accepted = {
            row["source_ref"]: row
            for row in engine.read_rows(data_root / "mappings.tsv")
        }
        verified_corrections = {
            "T1956": ("Off", "NUN5_SLES@0x513EF8"),
            "T1957": ("On", "NUN5_SLES@0x513EFC"),
            "T2158": ("Warning", "NUN5_SLES@0x513F38"),
        }
        semantic_donor_corrections = {
            "T27": ("Simple", "NUN5_SLES@0x514218", ""),
            "T1983": ("Easy", "NUN5_SLES@0x514220", ""),
            "T28": ("Normal", "NUN5_SLES@0x514228", ""),
            "T1984": ("Hard", "NUN5_SLES@0x514230", ""),
            "T29": ("Insane", "NUN5_SLES@0x514238", ""),
            "T50": (
                "Difficulty",
                "NUN5_TEXTENG@0xF880",
                "NA2_BTL@0x20A264",
            ),
        }
        donorless_replacements = {
            "T24": (
                "T24 You can set the opponent's state. During Double Jump, "
                "the opponent performs the action selected below while double-jumping."
            ),
            "T30": "T30 Ult",
            "T744": "T744 Faint Relief",
            "T767": "T767 An Older Sister's Joy",
        }
        donorless_ids = set(donorless_replacements)
        donor_backed_overrides = {
            "T2027": "Press <iconCROSS> to choose item.",
            "T2033": "Select an item and press <iconCROSS> to buy.",
        }
        structural_rows = {
            "T2011": (
                "Save or Load menu > saving-progress message",
                "seen:replacement-validation-save-progress-corruption",
            ),
            "T2041": (
                "Save or Load menu > saving-progress message",
                "inferred:complete-save-progress-message-family-from-paired-screen",
            ),
            "T2042": (
                "Save or Load menu > saving-progress message",
                "inferred:complete-save-progress-message-family-from-paired-screen",
            ),
            "T2014": (
                "Save or Load menu > overwrite confirmation",
                "seen:tid-pass-2026-07-26 paired screenshot",
            ),
            "T2015": (
                "Save or Load menu > overwrite confirmation",
                "inferred:complete-overwrite-message-family",
            ),
        }

        self.assertEqual(len(replacement_raw), 2053)
        self.assertEqual(len(replacement["text"]), 2053)
        self.assertEqual(replacement["inactive"], [])
        self.assertEqual(
            len({row["id"] for row in replacement_raw}),
            len(replacement_raw),
        )
        self.assertEqual(
            replacement_raw,
            sorted(
                replacement_raw,
                key=lambda row: (
                    row["display_context"].casefold(),
                    int(row["id"][1:]),
                ),
            ),
        )
        for row in replacement_raw:
            self.assertIn(row["id"], rebuild)
            candidate = rebuild[row["id"]]
            self.assertEqual(row["enabled"], "1")
            self.assertTrue(row["display_context"])
            self.assertTrue(
                row["display_basis"].startswith(engine.DISPLAY_BASIS_PREFIXES)
            )
            self.assertEqual(row["source"], candidate["source"])
            self.assertEqual(row["source_ref"], candidate["source_ref"])
            self.assertEqual(row["mode"], candidate["mode"])
            self.assertEqual(row["capacity"], candidate["capacity"])
            if row["id"] in verified_corrections:
                donor, donor_ref = verified_corrections[row["id"]]
                self.assertEqual(row["donor"], donor)
                self.assertEqual(row["donor_ref"], donor_ref)
                continue
            if row["id"] in semantic_donor_corrections:
                donor, donor_ref, reference_refs = semantic_donor_corrections[
                    row["id"]
                ]
                self.assertEqual(row["donor"], donor)
                self.assertEqual(row["donor_ref"], donor_ref)
                self.assertEqual(row["reference_refs"], reference_refs)
                self.assertEqual(row["replacement"], "")
                continue
            if row["id"] in donorless_ids:
                self.assertEqual(row["donor"], "")
                self.assertEqual(row["donor_ref"], "")
                self.assertEqual(
                    row["replacement"],
                    donorless_replacements[row["id"]],
                )
                self.assertEqual(row["reference_refs"], "")
                continue
            self.assertIn(row["source_ref"], accepted)
            reference = accepted[row["source_ref"]]
            for field in (
                "donor",
                "prefix",
                "replacement",
                "donor_ref",
                "transform",
                "arguments",
                "reference_refs",
                "parent_mapping_id",
            ):
                if (
                    row["id"] in {"T2042", "T2045", "T2050"}
                    and field == "parent_mapping_id"
                ):
                    continue
                if (
                    row["id"] in donor_backed_overrides
                    and field == "replacement"
                ):
                    self.assertEqual(
                        row["replacement"],
                        donor_backed_overrides[row["id"]],
                    )
                    continue
                self.assertEqual(row[field], reference[field])

        self.assertEqual(
            sum(
                row["id"]
                not in (
                    set(verified_corrections)
                    | set(semantic_donor_corrections)
                    | donorless_ids
                )
                for row in replacement_raw
            ),
            2040,
        )
        self.assertEqual(
            {
                row["id"]
                for row in replacement_raw
                if not row["donor"] and not row["donor_ref"]
            },
            donorless_ids,
        )
        self.assertEqual(
            {
                row["id"]: row["replacement"]
                for row in replacement_raw
                if row["replacement"] and row["id"] not in donorless_ids
            },
            donor_backed_overrides,
        )
        by_id = {row["id"]: row for row in replacement_raw}
        for mapping_id, (display_context, display_basis) in structural_rows.items():
            self.assertEqual(by_id[mapping_id]["display_context"], display_context)
            self.assertEqual(by_id[mapping_id]["display_basis"], display_basis)
        self.assertEqual(by_id["T2042"]["parent_mapping_id"], "T2011")
        self.assertEqual(by_id["T2045"]["parent_mapping_id"], "T2043")
        self.assertEqual(by_id["T2050"]["parent_mapping_id"], "T2048")

        engine.validate_structured_message_families(
            replacement["text"],
            table_name="replacement.tsv",
        )
        for missing_id in ("T2041", "T2042", "T2015"):
            with self.subTest(missing_id=missing_id):
                with self.assertRaisesRegex(
                    ValueError,
                    "incomplete structured message family.*missing parts",
                ):
                    engine.validate_structured_message_families(
                        [
                            row
                            for row in replacement["text"]
                            if row["id"] != missing_id
                        ],
                        table_name="replacement.tsv",
                    )

    def test_iso_source_delegates_to_the_shared_iso_reader(self) -> None:
        exact = SimpleNamespace(path="PRG/BTL.BIN", is_dir=False)
        basename = SimpleNamespace(path="OTHER/ETC.BIN", is_dir=False)
        image = SimpleNamespace(
            by_path={"PRG/BTL.BIN": exact, "OTHER/ETC.BIN": basename},
            read_file=mock.Mock(side_effect=lambda record: record.path.encode("ascii")),
        )
        with mock.patch.object(engine, "Iso9660", return_value=image) as iso_type:
            source = engine.IsoSource(Path("source.iso"))
        iso_type.assert_called_once()
        self.assertEqual(
            source.read(("PRG/BTL.BIN",), "BTL"), b"PRG/BTL.BIN"
        )
        self.assertEqual(source.read(("ETC.BIN",), "ETC"), b"OTHER/ETC.BIN")

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

    def test_rebuild_ids_follow_physical_row_order_and_sources_are_unique(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "rebuild.tsv"
            rows = [
                self.rebuild_row("T1", "NA2_SLPS@0x10"),
                self.rebuild_row("T3", "NA2_SLPS@0x20"),
            ]
            self.write_rebuild_rows(path, rows)
            with self.assertRaisesRegex(ValueError, "physical row order"):
                engine.read_rebuild_rows(path)

            rows[1]["id"] = "T2"
            rows[1]["source_ref"] = rows[0]["source_ref"]
            self.write_rebuild_rows(path, rows)
            with self.assertRaisesRegex(ValueError, "duplicate source_ref"):
                engine.read_rebuild_rows(path)

            rows = [
                self.rebuild_row("T2", "NA2_SLPS@0x10"),
                self.rebuild_row("T1", "NA2_SLPS@0x20"),
            ]
            self.write_rebuild_rows(path, rows)
            with self.assertRaisesRegex(ValueError, "physical row order"):
                engine.read_rebuild_rows(path)

    def test_rebuild_rows_do_not_require_or_resolve_donor_text(self) -> None:
        row = self.rebuild_row("T1", "NA2_SLPS@0x10")
        row["legacy_ids"] = ""
        parsed = engine.parse_rebuild_mappings([row])
        self.assertEqual(parsed[0]["id"], "T1")
        self.assertEqual(parsed[0]["donor"], "")
        self.assertEqual(parsed[0]["donor_ref"], "")
        self.assertEqual(parsed[0]["legacy_ids"], ())

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
            engine.validate_semantic_replacement("unknown", "pjrvspl0", "M1336")

    def test_allows_placeholder_word_for_visible_target(self) -> None:
        engine.validate_semantic_replacement("Unknown", "<r不明|ふめい>", "visible")

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

    def test_empty_transform_materializes_an_intentionally_empty_string(self) -> None:
        row = {
            "donor": "Unused official fragment",
            "prefix": "",
            "replacement": "",
            "transform": "empty",
            "arguments": {},
        }
        self.assertEqual(engine.resolve_replacement_text(row, "M0822"), "")

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

    def test_literal_format_argument_can_materialize_dialog_prefix(self) -> None:
        row = {
            "donor": "Quit %1 and return to %2?",
            "prefix": "",
            "replacement": "",
            "transform": "format_literal_prefix_arg2",
            "arguments": {"arg1": "Free Battle"},
        }
        self.assertEqual(
            engine.resolve_replacement_text(row, "formatted-prefix"),
            "Quit Free Battle and return to ",
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

    def test_fullwidth_ascii_is_normalized_in_donor_reference_arguments(self) -> None:
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

    def test_importer_preserves_canonical_game_title_donor(self) -> None:
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

    def test_empty_import_log_requires_explicit_replacement_mode_opt_in(self) -> None:
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
