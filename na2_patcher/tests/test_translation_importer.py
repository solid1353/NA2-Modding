from __future__ import annotations

import unittest

from na2_patcher.modules.translation_importer import engine


class TranslationImporterTests(unittest.TestCase):
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
