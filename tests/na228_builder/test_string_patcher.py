from __future__ import annotations

import unittest

from na228_builder.modules.binary_patcher import engine as binary_patcher
from na228_builder.modules.string_patcher import engine as string_patcher


class StringPatcherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.package = string_patcher.build_binary_package()

    def test_allows_import_only_derived_consumer(self) -> None:
        self.assertIsInstance(self.package, binary_patcher.Package)
        self.assertEqual(self.package.package_id, "derived.string_patcher")
        self.assertEqual(list(self.package.targets), [])
        self.assertEqual(list(self.package.groups), [])
        self.assertEqual(list(self.package.patches), [])
        self.assertEqual(self.package.edits, [])

    def test_compiles_imported_strings_as_default_binary_patches(self) -> None:
        package = string_patcher.build_binary_package(
            imported_rows=(
                {
                    "import_id": "BTL-I0001",
                    "group_id": "BTL",
                    "path": "PRG/BTL.BIN",
                    "offset": "0x2",
                    "expected_hex": "4A50",
                    "replacement_hex": "454E",
                    "source_mapping_id": "BTL-M001",
                    "reason": "Import official battle text.",
                },
            ),
            imported_targets={
                "PRG/BTL.BIN": {
                    "root_id": "na2",
                    "expected_size": 8,
                    "expected_sha256": "0" * 64,
                }
            },
        )

        self.assertIn("BTL", package.groups)
        self.assertEqual(package.patches["BTL-I0001"].evidence_id, "BTL-M001")
        self.assertTrue(package.patches["BTL-I0001"].enabled)
        selected = ["BTL-I0001"]
        edits = binary_patcher.validate_selection(
            package, selected, for_apply=True
        )
        imported_edit = edits[0]
        target_id = imported_edit.destination_target_id
        baseline = b"\0\0JP\0\0\0\0"
        buffers, rows, _ = binary_patcher.compose_edits(
            package,
            {target_id: baseline},
            edits,
        )
        self.assertEqual(bytes(buffers[target_id]), b"\0\0EN\0\0\0\0")
        self.assertEqual(rows[0]["evidence_id"], "BTL-M001")


if __name__ == "__main__":
    unittest.main()
