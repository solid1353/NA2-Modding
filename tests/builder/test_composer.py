from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from na228_builder.scripts.composer import (
    compose_assembly_plan,
    resolve_module_order,
    resolve_source_ref,
)
from na228_builder.image_assembler.operations import IsoFileRef, IsoRangeRef
from na228_builder.scripts.configuration import ModuleInvocation


def module(module_id: str, order: int, module_type: str) -> ModuleInvocation:
    return ModuleInvocation(
        module_id=module_id,
        order=order,
        module=module_type,
        input_path=Path(module_type),
        input_sha256="0" * 64,
        feature_id="localization",
    )


class ComposerTests(unittest.TestCase):
    def test_resolves_importer_before_string_patcher(self) -> None:
        string_patcher = module("localization.string_patcher", 1, "string_patcher")
        importer = module("localization.translation_importer", 2, "translation_importer")
        binary = module("localization.binary_patcher", 3, "binary_patcher")
        self.assertEqual(
            [item.module_id for item in resolve_module_order((string_patcher, importer, binary))],
            [importer.module_id, string_patcher.module_id, binary.module_id],
        )

    def test_allows_importer_without_a_direct_consumer(self) -> None:
        importer = module("localization.translation_importer", 1, "translation_importer")
        self.assertEqual(resolve_module_order((importer,)), (importer,))

    def test_source_refs_support_whole_files_and_guarded_ranges(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = b"0123456789"
            (root / "PRG").mkdir()
            (root / "PRG" / "DONOR.BIN").write_bytes(payload)
            digest = hashlib.sha256(payload).hexdigest()
            self.assertEqual(
                resolve_source_ref(
                    IsoFileRef("nun5", "PRG/DONOR.BIN", digest),
                    {"nun5": root},
                ),
                payload,
            )
            self.assertEqual(
                resolve_source_ref(
                    IsoRangeRef(
                        "nun5",
                        "PRG/DONOR.BIN",
                        3,
                        4,
                        hashlib.sha256(b"3456").hexdigest(),
                    ),
                    {"nun5": root},
                ),
                b"3456",
            )

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
