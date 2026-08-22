from __future__ import annotations

import unittest
from types import SimpleNamespace

from na228_builder.scripts.composer import compose_assembly_plan


class ComposerTests(unittest.TestCase):
    def test_product_boot_path_becomes_guarded_edit_and_rename(self) -> None:
        system = b"BOOT2 = cdrom0:\\SLPS_258.37;1\r\n"
        records = {
            "SYSTEM.CNF": SimpleNamespace(
                path="SYSTEM.CNF", is_dir=False, size=len(system)
            ),
            "SLPS_258.37": SimpleNamespace(
                path="SLPS_258.37", is_dir=False, size=4
            ),
        }
        payloads = {"SYSTEM.CNF": system, "SLPS_258.37": b"BOOT"}
        source = SimpleNamespace(
            by_path=records,
            read_file=lambda supplied: payloads[supplied.path],
        )
        result = compose_assembly_plan(
            source=source,
            output_boot_path="SLOP_NA2.28",
            payloads={},
            owners={},
            insertions={},
            insertion_owners={},
        )
        self.assertEqual(len(result.plan.replacements), 1)
        replacements = {item.path: item for item in result.plan.replacements}
        self.assertEqual(replacements["SYSTEM.CNF"].expected, system)
        self.assertIn(b"SLOP_NA2.28", replacements["SYSTEM.CNF"].replacement)
        self.assertEqual(result.plan.renames[0].source_path, "SLPS_258.37")
        self.assertEqual(result.plan.renames[0].replacement_path, "SLOP_NA2.28")
        self.assertEqual(
            [row["target"] for row in result.identity_edits], ["SYSTEM.CNF"]
        )

if __name__ == "__main__":
    unittest.main()
