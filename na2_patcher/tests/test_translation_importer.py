from __future__ import annotations

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
            "section": "test",
            "mode": "unresolved",
            "target": "SLPS",
            "target_offset": "0",
            "capacity": "8",
            "source": "",
            "donor_ref": "",
            "donor": "",
            "replacement": "",
            "transform": "",
            "arguments": "",
            "reference_binary": "",
            "reference_file_offsets": "",
            "parent_mapping_id": "",
            "reason": "research does not belong in executable mappings",
        }
        with self.assertRaisesRegex(ValueError, "unsupported mode"):
            engine.parse_mappings([row])

    def test_rejects_placeholder_donor_for_identifier_target(self) -> None:
        with self.assertRaisesRegex(ValueError, "placeholder donor text"):
            engine.validate_semantic_replacement("unknown", "pjrvspl0", "M1336")

    def test_allows_placeholder_word_for_visible_target(self) -> None:
        engine.validate_semantic_replacement("Unknown", "<r不明|ふめい>", "visible")

    def test_empty_replacement_is_explicit(self) -> None:
        row = {
            "replacement": "",
            "transform": "",
            "arguments": {},
        }
        self.assertEqual(engine.resolve_replacement_text(row, "M0822"), "")

    def test_importer_preserves_canonical_game_title_replacement(self) -> None:
        mappings = [
            {
                "id": "MTEST",
                "target": "SLPS",
                "mode": "slot",
                "source": "clean Japanese title",
                "donor": "Create Naruto Shippuden: Ultimate Ninja 5 data?",
                "replacement": "Create Naruto Shippuden: Ultimate Ninja 5 data?",
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
            "replacement": "First line<br>Second line",
            "transform": "split_br",
            "arguments": {"part": "0"},
        }
        self.assertEqual(
            engine.resolve_replacement_text(row, "parent"),
            "First line",
        )

    def test_split_br_rejects_out_of_range_part(self) -> None:
        row = {
            "replacement": "First line<br>Second line",
            "transform": "split_br",
            "arguments": {"part": "2"},
        }
        with self.assertRaisesRegex(ValueError, "outside 2 parts"):
            engine.resolve_replacement_text(row, "parent")


if __name__ == "__main__":
    unittest.main()
