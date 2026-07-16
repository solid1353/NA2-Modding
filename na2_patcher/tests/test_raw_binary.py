from __future__ import annotations

import csv
import hashlib
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from na2_patcher.modules.raw_binary import engine as patcher
from na2_patcher.modules.raw_binary.tools import import_zip_overlay


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def write_tsv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


class RawBinaryPatcherTests(unittest.TestCase):
    def make_fixture(self, root: Path) -> tuple[patcher.Package, dict[str, Path], dict[str, bytes]]:
        na2 = root / "na2"
        un5 = root / "un5"
        package_dir = root / "package"
        na2.mkdir()
        un5.mkdir()
        clean = bytes(range(16))
        source = bytes.fromhex("AABBCCDD") + bytes(range(4, 16))
        (na2 / "target.bin").write_bytes(clean)
        (un5 / "source.bin").write_bytes(source)

        write_tsv(
            package_dir / "manifest.tsv",
            patcher.MANIFEST_FIELDS,
            [{
                "schema_version": 1,
                "package_id": "fixture",
                "package_version": 1,
                "game": "NA2",
                "description": "test fixture",
                "evidence_path": "evidence/source.zip",
            }],
        )
        write_tsv(
            package_dir / "targets.tsv",
            patcher.TARGET_FIELDS,
            [
                {
                    "target_id": "destination",
                    "root_id": "na2",
                    "role": "destination",
                    "path": "target.bin",
                    "expected_size": len(clean),
                    "expected_sha256": sha256(clean),
                },
                {
                    "target_id": "source",
                    "root_id": "un5",
                    "role": "source",
                    "path": "source.bin",
                    "expected_size": len(source),
                    "expected_sha256": sha256(source),
                },
            ],
        )
        write_tsv(
            package_dir / "patches.tsv",
            patcher.PATCH_FIELDS,
            [{
                "patch_id": "test_patch",
                "default_enabled": 0,
                "status": "approved_for_test",
                "confidence": "verified",
                "name": "test patch",
                "description": "replace and copy",
                "source_mapping_id": "",
                "runtime_classification": "",
                "review_notes": "",
            }],
        )
        write_tsv(package_dir / "relations.tsv", patcher.RELATION_FIELDS, [])
        blank = {
            "expected_sha256": "",
            "replacement_hex": "",
            "source_target_id": "",
            "source_offset": "",
            "source_expected_hex": "",
            "source_expected_sha256": "",
            "blob_path": "",
            "blob_offset": "",
            "blob_sha256": "",
            "fill_hex": "",
        }
        write_tsv(
            package_dir / "edits.tsv",
            patcher.EDIT_FIELDS,
            [
                {
                    **blank,
                    "edit_id": "replace_word",
                    "patch_id": "test_patch",
                    "order": 10,
                    "destination_target_id": "destination",
                    "destination_offset": "0x4",
                    "operation": "replace",
                    "length": 4,
                    "expected_hex": clean[4:8].hex().upper(),
                    "replacement_hex": "10203040",
                    "reason": "literal replacement",
                },
                {
                    **blank,
                    "edit_id": "copy_word",
                    "patch_id": "test_patch",
                    "order": 20,
                    "destination_target_id": "destination",
                    "destination_offset": "0xC",
                    "operation": "copy",
                    "length": 4,
                    "expected_hex": clean[12:16].hex().upper(),
                    "source_target_id": "source",
                    "source_offset": "0x0",
                    "source_expected_hex": "AABBCCDD",
                    "reason": "verified source copy",
                },
            ],
        )
        package = patcher.load_package(package_dir)
        roots = {"na2": na2, "un5": un5}
        target_data = patcher.verify_package_data(package, roots)
        return package, roots, target_data

    def test_apply_is_size_preserving_and_logged(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            package, roots, target_data = self.make_fixture(root)
            selected = ["test_patch"]
            edits = patcher.validate_selection(package, selected, for_apply=True)
            output = root / "output"
            logs = root / "logs"
            patcher.apply_package(
                package,
                roots,
                target_data,
                selected,
                edits,
                output,
                "work/temp/output",
                logs,
                "logs/na2_patcher/raw_binary/test",
            )
            result = (output / "target.bin").read_bytes()
            self.assertEqual(len(result), 16)
            self.assertEqual(result[4:8], bytes.fromhex("10203040"))
            self.assertEqual(result[12:16], bytes.fromhex("AABBCCDD"))
            self.assertTrue((logs / "patch_log.tsv").is_file())
            self.assertEqual((roots["na2"] / "target.bin").read_bytes(), bytes(range(16)))

    def test_pending_patch_cannot_apply(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package, _, _ = self.make_fixture(Path(temporary))
            package.patches["test_patch"] = replace(
                package.patches["test_patch"], status="pending"
            )
            with self.assertRaisesRegex(patcher.PatchError, "not approved"):
                patcher.validate_selection(package, ["test_patch"], for_apply=True)

    def test_expected_byte_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            package, roots, _ = self.make_fixture(root)
            (roots["na2"] / "target.bin").write_bytes(b"X" + bytes(range(1, 16)))
            with self.assertRaisesRegex(patcher.PatchError, "SHA-256 mismatch"):
                patcher.verify_package_data(package, roots)

    def test_composition_accepts_unrelated_prior_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package, _, target_data = self.make_fixture(Path(temporary))
            edits = patcher.validate_selection(
                package, ["test_patch"], for_apply=True
            )
            staged = bytearray(target_data["destination"])
            staged[0] = 0xFE
            buffers, _, before_hashes = patcher.compose_edits(
                package,
                target_data,
                edits,
                {"destination": staged},
            )
            self.assertEqual(buffers["destination"][0], 0xFE)
            self.assertEqual(
                buffers["destination"][4:8], bytes.fromhex("10203040")
            )
            self.assertEqual(before_hashes["destination"], sha256(staged))

    def test_composition_rejects_prior_change_in_patch_range(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package, _, target_data = self.make_fixture(Path(temporary))
            edits = patcher.validate_selection(
                package, ["test_patch"], for_apply=True
            )
            staged = bytearray(target_data["destination"])
            staged[4] ^= 0xFF
            with self.assertRaisesRegex(patcher.PatchError, "staged destination"):
                patcher.compose_edits(
                    package,
                    target_data,
                    edits,
                    {"destination": staged},
                )


class ZipOverlayImporterTests(unittest.TestCase):
    def test_changed_ranges_merge_only_small_unchanged_gaps(self) -> None:
        self.assertEqual(
            import_zip_overlay.changed_ranges(
                b"abcdefghij", b"aXcdYfghiZ", maximum_gap=2
            ),
            [(1, 5), (9, 10)],
        )

    def test_rejects_unsafe_zip_entry(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            import_zip_overlay.normalized_entry("../escape.bin")


if __name__ == "__main__":
    unittest.main()
