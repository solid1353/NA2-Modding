from types import SimpleNamespace
import unittest

from na228_builder.patches.localization.mod_strings import ModStrings


def strings(language: str) -> ModStrings:
    return ModStrings(SimpleNamespace(nodes=(SimpleNamespace(
        path=("features", "localization"), configured_value=language,
    ),)))


class ModStringsTests(unittest.TestCase):
    def test_japanese_numbers_preserve_renderer_commands(self) -> None:
        source = "<iconL1> 5 10% -2.5% 0-10 25/09/2026 999:59:59."
        expected = "<iconL1> ５ １０％ －２．５％ ０－１０ ２５／０９／２０２６ ９９９：５９：５９."
        self.assertEqual(strings("jp").encode(source), expected.encode("cp932"))
        self.assertEqual(strings("en").encode(source), source.encode("ascii"))

    def test_native_numeric_glyphs_match_the_selected_encoding(self) -> None:
        for language, expected in (("en", "5%"), ("jp", "５％")):
            with self.subTest(language=language):
                selected = strings(language)
                table = selected.native_payload("mod_number_glyphs")
                encoded = b""
                for char in "5%":
                    offset = ord(char) * 2
                    glyph = int.from_bytes(table[offset:offset + 2], "little")
                    encoded += glyph.to_bytes(2 if glyph > 255 else 1, "big")
                self.assertEqual(encoded, expected.encode(selected.encoding))

    def test_japanese_handicap_pairs_keep_separate_entries(self) -> None:
        pairs = strings("jp").native_payload("mod_number_handicap").split(b"\0")
        self.assertEqual(len(pairs), 12)
        self.assertEqual(pairs[0], "０－１０".encode("cp932"))
        self.assertEqual(pairs[5], "５－５".encode("cp932"))
        self.assertEqual(pairs[10], "１０－０".encode("cp932"))
        self.assertEqual(pairs[-1], b"")


if __name__ == "__main__":
    unittest.main()
