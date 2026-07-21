from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from na2_patcher.composer import (
    compose_assembly_plan,
    resolve_module_order,
    resolve_source_ref,
)
from na2_patcher.image_assembler.operations import IsoFileRef, IsoRangeRef
from na2_patcher.profile import ProfileImage, ProfileModule


def module(module_id: str, order: int, module_type: str) -> ProfileModule:
    return ProfileModule(
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

    def test_rejects_unconsumed_translation_imports(self) -> None:
        importer = module("localization.translation_importer", 1, "translation_importer")
        with self.assertRaisesRegex(ValueError, "no string_patcher consumes"):
            resolve_module_order((importer,))

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

    def test_profile_image_becomes_guarded_system_edit_and_rename(self) -> None:
        system = b"BOOT2 = cdrom0:\\SLPS_258.37;1\r\n"
        record = SimpleNamespace(path="SYSTEM.CNF", is_dir=False, size=len(system))
        source = SimpleNamespace(
            by_path={"SYSTEM.CNF": record},
            read_file=lambda supplied: system,
        )
        result = compose_assembly_plan(
            source=source,
            image=ProfileImage("SLPS_258.37", "SLPS_222.28", "SYSTEM.CNF"),
            payloads={},
            owners={},
            insertions={},
            insertion_owners={},
        )
        self.assertEqual(len(result.plan.replacements), 1)
        self.assertEqual(result.plan.replacements[0].expected, system)
        self.assertIn(b"SLPS_222.28", result.plan.replacements[0].replacement)
        self.assertEqual(result.plan.renames[0].source_path, "SLPS_258.37")
        self.assertEqual(result.plan.renames[0].replacement_path, "SLPS_222.28")
        self.assertEqual(result.image_edits[0]["target"], "SYSTEM.CNF")


if __name__ == "__main__":
    unittest.main()
