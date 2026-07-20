from __future__ import annotations

import unittest

from na2_patcher.modules.translation_importer import engine


class TranslationImporterTests(unittest.TestCase):
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
