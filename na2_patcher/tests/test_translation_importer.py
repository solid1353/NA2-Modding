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
            "source_ref": "",
            "transform": "",
            "arguments": "",
            "value": "",
            "reason": "research does not belong in executable mappings",
        }
        with self.assertRaisesRegex(ValueError, "unsupported mode"):
            engine.parse_mappings([row])

    def test_rejects_placeholder_donor_for_identifier_target(self) -> None:
        with self.assertRaisesRegex(ValueError, "placeholder donor text"):
            engine.validate_semantic_replacement("unknown", "pjrvspl0", "M1336")

    def test_allows_placeholder_word_for_visible_target(self) -> None:
        engine.validate_semantic_replacement("Unknown", "<r不明|ふめい>", "visible")

    def test_empty_transform_is_explicit(self) -> None:
        row = {
            "source": "NUN5_TEXTENG",
            "source_offset": 0,
            "transform": "empty",
            "arguments": {},
        }
        self.assertEqual(
            engine.resolve_source_text(row, {"NUN5_TEXTENG": b"Finished\x00"}, "M0822"),
            "",
        )

    def test_uppercase_transform_preserves_official_source_authority(self) -> None:
        row = {
            "source": "NUN5_SLES",
            "source_offset": 0,
            "transform": "uppercase",
            "arguments": {},
        }
        self.assertEqual(
            engine.resolve_source_text(row, {"NUN5_SLES": b"Yes\x00"}, "M0799"),
            "YES",
        )

    def test_game_title_policy_preserves_raw_template_and_changes_materialization(self) -> None:
        mappings = [
            {
                "id": "MTEST",
                "target": "SLPS",
                "mode": "slot",
                "source": "NUN5_TEXTENG",
                "source_offset": 0,
                "transform": "",
                "arguments": {},
            }
        ]
        policy = engine.GameTitlePolicy(
            donor_title="Naruto Shippuden: Ultimate Ninja 5",
            output_title="Narutimate Accel v2.28",
            target="SLPS",
            expected_mapping_count=1,
            expected_occurrence_count=1,
        )
        resolved, sequences, templates, materialized = (
            engine.resolve_text_materializations(
                mappings,
                {"SLPS"},
                {
                    "NUN5_TEXTENG": (
                        b"Create Naruto Shippuden: Ultimate Ninja 5 data?\x00"
                    )
                },
                policy,
            )
        )
        self.assertEqual(sequences, {})
        self.assertEqual(
            templates["MTEST"],
            "Create Naruto Shippuden: Ultimate Ninja 5 data?",
        )
        self.assertEqual(
            resolved["MTEST"], "Create Narutimate Accel v2.28 data?"
        )
        self.assertEqual(materialized["MTEST"], resolved["MTEST"])

    def test_game_title_policy_fails_closed_when_expected_target_loses_token(self) -> None:
        mappings = [
            {
                "id": "MTEST",
                "target": "SLPS",
                "mode": "slot",
                "source": "NUN5_TEXTENG",
                "source_offset": 0,
                "transform": "",
                "arguments": {},
            }
        ]
        policy = engine.GameTitlePolicy(
            donor_title="Naruto Shippuden: Ultimate Ninja 5",
            output_title="Narutimate Accel v2.28",
            target="SLPS",
            expected_mapping_count=1,
            expected_occurrence_count=1,
        )
        with self.assertRaisesRegex(ValueError, "policy coverage differs"):
            engine.resolve_text_materializations(
                mappings,
                {"SLPS"},
                {"NUN5_TEXTENG": b"Create data?\x00"},
                policy,
            )

    def test_insert_br_after_words_preserves_official_text(self) -> None:
        source = b"Sealing Jutsu: Nine Phantom Dragons\x00"
        row = {
            "source": "NUN5_TEXTENG",
            "source_offset": 0,
            "transform": "insert_br_after_words",
            "arguments": {"words": "3"},
        }

        self.assertEqual(
            engine.resolve_source_text(row, {"NUN5_TEXTENG": source}, "movie"),
            "Sealing Jutsu: Nine<br>Phantom Dragons",
        )

    def test_insert_br_after_words_rejects_non_boundary_counts(self) -> None:
        source = b"Fourth Awakened Mode\x00"
        for count in ("0", "3"):
            with self.subTest(count=count):
                row = {
                    "source": "NUN5_TEXTENG",
                    "source_offset": 0,
                    "transform": "insert_br_after_words",
                    "arguments": {"words": count},
                }
                with self.assertRaisesRegex(ValueError, "word break"):
                    engine.resolve_source_text(
                        row, {"NUN5_TEXTENG": source}, "movie"
                    )


if __name__ == "__main__":
    unittest.main()
