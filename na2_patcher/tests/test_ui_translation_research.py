from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.research.ui_translation.match_assembly_function import parse_functions


class AssemblyMatcherTests(unittest.TestCase):
    def test_parser_accepts_elf_and_overlay_ghidra_address_formats(self) -> None:
        listing = """
                            ;undefined FUN_00382470()
SECTION4:0038...27bdffd0        addiu       sp,sp,-0x30
SECTION4:0038...03e00008        jr          ra
                            ;undefined FUN_006bcfd0()
text:006bcfd0   b0ffbd27        addiu       sp,sp,-0x50
text:006bcfd4   0800e003        jr          ra
"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "listing.txt"
            path.write_text(listing, encoding="utf-8")
            functions = parse_functions(path)

        self.assertEqual(set(functions), {"FUN_00382470", "FUN_006bcfd0"})
        self.assertEqual(functions["FUN_00382470"].address, 0x00382470)
        self.assertEqual(functions["FUN_006bcfd0"].address, 0x006BCFD0)
        self.assertEqual(len(functions["FUN_00382470"].signatures), 2)
        self.assertEqual(len(functions["FUN_006bcfd0"].signatures), 2)


if __name__ == "__main__":
    unittest.main()
