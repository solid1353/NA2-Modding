from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from na228_builder.scripts.composer import (
    MODULE_ARTIFACT_CONTRACTS,
    compose_assembly_plan,
    resolve_module_order,
    resolve_source_ref,
)
from na228_builder.image_assembler.operations import IsoFileRef, IsoRangeRef
from na228_builder.scripts.configuration import ModuleInvocation, ProductIdentity


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

    def test_allows_importer_with_derived_string_consumer(self) -> None:
        importer = module("localization.translation_importer", 1, "translation_importer")
        self.assertEqual(resolve_module_order((importer,)), (importer,))
        self.assertEqual(
            MODULE_ARTIFACT_CONTRACTS["translation_importer"].derived_consumers,
            ("string_patcher",),
        )

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

    def test_product_identity_becomes_guarded_edits_and_rename(self) -> None:
        system = b"BOOT2 = cdrom0:\\SLPS_258.37;1\r\n"
        source_directory = b"BISLPS-25837NARUTO5"
        output_directory = b"BASLOP-NA228NARUTO6"
        source_title = b"Original" + bytes(8)
        title_offset = len(source_directory) + 1
        boot = source_directory + b":" + source_title + b":" + source_directory
        records = {
            "SYSTEM.CNF": SimpleNamespace(
                path="SYSTEM.CNF", is_dir=False, size=len(system)
            ),
            "SLPS_258.37": SimpleNamespace(
                path="SLPS_258.37", is_dir=False, size=len(boot)
            ),
        }
        payloads = {"SYSTEM.CNF": system, "SLPS_258.37": boot}
        source = SimpleNamespace(
            by_path=records,
            read_file=lambda supplied: payloads[supplied.path],
        )
        identity = ProductIdentity(
            source_boot_path="SLPS_258.37",
            output_boot_path="SLOP_NA2.28",
            system_cnf_path="SYSTEM.CNF",
            source_memory_card_directory=source_directory.decode("ascii"),
            output_memory_card_directory=output_directory.decode("ascii"),
            memory_card_directory_occurrence_count=2,
            memory_card_title_offset=title_offset,
            memory_card_title_capacity=16,
            memory_card_title_encoding="ascii",
            source_memory_card_title="Original",
            output_memory_card_title="NA 2.28",
            imported_game_title="Imported Game",
            output_game_title="Output Game",
            game_title_mapping_count=1,
            game_title_occurrence_count=1,
        )
        result = compose_assembly_plan(
            source=source,
            identity=identity,
            payloads={},
            owners={},
            insertions={},
            insertion_owners={},
        )
        self.assertEqual(len(result.plan.replacements), 2)
        replacements = {item.path: item for item in result.plan.replacements}
        self.assertEqual(replacements["SYSTEM.CNF"].expected, system)
        self.assertIn(b"SLOP_NA2.28", replacements["SYSTEM.CNF"].replacement)
        self.assertEqual(
            replacements["SLPS_258.37"].replacement[
                title_offset:title_offset + 16
            ],
            b"NA 2.28" + bytes(9),
        )
        self.assertEqual(
            replacements["SLPS_258.37"].replacement.count(output_directory),
            2,
        )
        self.assertNotIn(
            source_directory,
            replacements["SLPS_258.37"].replacement,
        )
        self.assertEqual(result.plan.renames[0].source_path, "SLPS_258.37")
        self.assertEqual(result.plan.renames[0].replacement_path, "SLOP_NA2.28")
        self.assertEqual(
            [row["target"] for row in result.identity_edits],
            ["SYSTEM.CNF", "SLPS_258.37", "SLPS_258.37", "SLPS_258.37"],
        )
        self.assertEqual(
            [row["offset"] for row in result.identity_edits[1:3]],
            ["0x0", f"0x{title_offset + 17:X}"],
        )

    def test_product_identity_rejects_title_guard_mismatch(self) -> None:
        system = b"BOOT2 = cdrom0:\\SLPS_258.37;1\r\n"
        source_directory = b"BISLPS-25837NARUTO5"
        output_directory = b"BASLOP-NA228NARUTO6"
        title_offset = len(source_directory) + 1
        boot = (
            source_directory
            + b":"
            + b"Unexpected"
            + bytes(6)
            + b":"
            + source_directory
        )
        records = {
            "SYSTEM.CNF": SimpleNamespace(
                path="SYSTEM.CNF", is_dir=False, size=len(system)
            ),
            "SLPS_258.37": SimpleNamespace(
                path="SLPS_258.37", is_dir=False, size=len(boot)
            ),
        }
        payloads = {"SYSTEM.CNF": system, "SLPS_258.37": boot}
        source = SimpleNamespace(
            by_path=records,
            read_file=lambda supplied: payloads[supplied.path],
        )
        identity = ProductIdentity(
            source_boot_path="SLPS_258.37",
            output_boot_path="SLOP_NA2.28",
            system_cnf_path="SYSTEM.CNF",
            source_memory_card_directory=source_directory.decode("ascii"),
            output_memory_card_directory=output_directory.decode("ascii"),
            memory_card_directory_occurrence_count=2,
            memory_card_title_offset=title_offset,
            memory_card_title_capacity=16,
            memory_card_title_encoding="ascii",
            source_memory_card_title="Original",
            output_memory_card_title="NA 2.28",
            imported_game_title="Imported Game",
            output_game_title="Output Game",
            game_title_mapping_count=1,
            game_title_occurrence_count=1,
        )
        with self.assertRaisesRegex(RuntimeError, "title guard failed"):
            compose_assembly_plan(
                source=source,
                identity=identity,
                payloads={},
                owners={},
                insertions={},
                insertion_owners={},
            )

    def test_product_identity_rejects_memory_card_directory_count_mismatch(self) -> None:
        system = b"BOOT2 = cdrom0:\\SLPS_258.37;1\r\n"
        source_directory = b"BISLPS-25837NARUTO5"
        source_title = b"Original" + bytes(8)
        boot = source_directory + b":" + source_title
        records = {
            "SYSTEM.CNF": SimpleNamespace(
                path="SYSTEM.CNF", is_dir=False, size=len(system)
            ),
            "SLPS_258.37": SimpleNamespace(
                path="SLPS_258.37", is_dir=False, size=len(boot)
            ),
        }
        payloads = {"SYSTEM.CNF": system, "SLPS_258.37": boot}
        source = SimpleNamespace(
            by_path=records,
            read_file=lambda supplied: payloads[supplied.path],
        )
        identity = ProductIdentity(
            source_boot_path="SLPS_258.37",
            output_boot_path="SLOP_NA2.28",
            system_cnf_path="SYSTEM.CNF",
            source_memory_card_directory=source_directory.decode("ascii"),
            output_memory_card_directory="BASLOP-NA228NARUTO6",
            memory_card_directory_occurrence_count=2,
            memory_card_title_offset=len(source_directory) + 1,
            memory_card_title_capacity=16,
            memory_card_title_encoding="ascii",
            source_memory_card_title="Original",
            output_memory_card_title="NA 2.28",
            imported_game_title="Imported Game",
            output_game_title="Output Game",
            game_title_mapping_count=1,
            game_title_occurrence_count=1,
        )
        with self.assertRaisesRegex(RuntimeError, "exactly 2 times; found 1"):
            compose_assembly_plan(
                source=source,
                identity=identity,
                payloads={},
                owners={},
                insertions={},
                insertion_owners={},
            )


if __name__ == "__main__":
    unittest.main()
