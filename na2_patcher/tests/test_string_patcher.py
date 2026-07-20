from __future__ import annotations

import unittest
from pathlib import Path

from na2_patcher.modules.binary_patcher import engine as binary_patcher
from na2_patcher.modules.string_patcher import engine as string_patcher


class StringPatcherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.package_directory = (
            Path(__file__).resolve().parents[1] / "modules" / "string_patcher"
        )
        cls.package = string_patcher.build_binary_package(cls.package_directory)

    def test_stores_only_string_declarations(self) -> None:
        self.assertTrue((self.package_directory / "strings.tsv").is_file())
        for name in ("manifest.tsv", "targets.tsv", "groups.tsv", "patches.tsv", "edits.tsv"):
            self.assertFalse((self.package_directory / name).exists(), name)

    def test_compiles_exact_cp932_slot(self) -> None:
        self.assertIsInstance(self.package, binary_patcher.Package)
        self.assertEqual(list(self.package.patches), ["ELF-S001"])
        edit = self.package.edits[0]
        self.assertEqual(edit.destination_offset, 0x2FBAE0)
        self.assertEqual(edit.length, 64)
        self.assertEqual(
            edit.expected_hex,
            "826D8260827182748273826E817C8369838B8367817C81408EBE959793608369"
            "838B836583428381836283678341834E835A838B825100000000000000000000",
        )
        self.assertEqual(
            edit.replacement_hex,
            "826D826081408296825181448251825700000000000000000000000000000000"
            "0000000000000000000000000000000000000000000000000000000000000000",
        )

    def test_shared_binary_patcher_applies_compiled_edit(self) -> None:
        target_id = self.package.edits[0].destination_target_id
        target = self.package.targets[target_id]
        baseline = bytearray(target.expected_size)
        expected = bytes.fromhex(self.package.edits[0].expected_hex)
        start = self.package.edits[0].destination_offset
        baseline[start : start + len(expected)] = expected
        selected = binary_patcher.resolve_patch_selections(
            self.package,
            [("translation", "group", "identity")],
        )
        edits = binary_patcher.validate_patch_selections(
            self.package,
            selected,
            for_apply=True,
        )
        buffers, rows, _ = binary_patcher.compose_edits(
            self.package,
            {target_id: bytes(baseline)},
            edits,
        )
        replacement = bytes.fromhex(self.package.edits[0].replacement_hex)
        self.assertEqual(
            bytes(buffers[target_id][start : start + len(replacement)]),
            replacement,
        )
        self.assertEqual(rows[0]["outcome"], "applied")
        self.assertEqual(rows[0]["package_id"], "string_patcher")


if __name__ == "__main__":
    unittest.main()
