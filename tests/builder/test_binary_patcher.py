from __future__ import annotations

import csv
from contextlib import redirect_stderr
import hashlib
import io
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from na228_builder.modules.binary_patcher import engine as patcher


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def write_tsv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


class BinaryPatcherTests(unittest.TestCase):
    def make_fixture(self, root: Path) -> tuple[patcher.Package, dict[str, Path], dict[str, bytes]]:
        na2 = root / "na2"
        nun5 = root / "nun5"
        package_dir = root / "package"
        na2.mkdir()
        nun5.mkdir()
        clean = bytes(range(16))
        source = bytes.fromhex("AABBCCDD") + bytes(range(4, 16))
        (na2 / "target.bin").write_bytes(clean)
        (nun5 / "source.bin").write_bytes(source)

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
                    "root_id": "nun5",
                    "role": "source",
                    "path": "source.bin",
                    "expected_size": len(source),
                    "expected_sha256": sha256(source),
                },
            ],
        )
        write_tsv(
            package_dir / "groups.tsv",
            patcher.GROUP_FIELDS,
            [{
                "group_id": "fixture_group",
                "enabled": 1,
                "name": "Fixture group",
                "description": "Fixture patches.",
                "review_notes": "",
            }],
        )
        write_tsv(
            package_dir / "patches.tsv",
            patcher.PATCH_FIELDS,
            [{
                "patch_id": "test_patch",
                "group_id": "fixture_group",
                "enabled": 0,
                "status": "approved_for_test",
                "confidence": "verified",
                "name": "test patch",
                "description": "replace and copy",
                "evidence_id": "",
                "review_notes": "",
            }],
        )
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
        roots = {"na2": na2, "nun5": nun5}
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
                "logs/na228/binary_patcher/test",
                selection_mode="explicit",
            )
            result = (output / "target.bin").read_bytes()
            self.assertEqual(len(result), 16)
            self.assertEqual(result[4:8], bytes.fromhex("10203040"))
            self.assertEqual(result[12:16], bytes.fromhex("AABBCCDD"))
            self.assertTrue((logs / "patch_log.tsv").is_file())
            with (logs / "patch_selection.tsv").open(
                encoding="utf-8", newline=""
            ) as handle:
                row = next(csv.DictReader(handle, delimiter="\t"))
            self.assertEqual(row["group_id"], "fixture_group")
            self.assertEqual(row["group_name"], "Fixture group")
            self.assertEqual(row["group_enabled"], "1")
            self.assertEqual(row["patch_enabled"], "0")
            self.assertEqual(row["effective_selected"], "1")
            self.assertEqual(row["selection_mode"], "explicit")
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

    def test_obsolete_manifest_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            package, _, _ = self.make_fixture(root)
            (package.directory / "manifest.tsv").write_text(
                "schema_version\tpackage_id\n2\tfixture\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(patcher.PatchError, "obsolete"):
                patcher.load_package(package.directory)

    def test_patch_must_reference_declared_group(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            package, _, _ = self.make_fixture(root)
            patches = package.directory / "patches.tsv"
            patches.write_text(
                patches.read_text(encoding="utf-8").replace(
                    "test_patch\tfixture_group\t",
                    "test_patch\tmissing_group\t",
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(patcher.PatchError, "unknown group_id"):
                patcher.load_package(package.directory)

    def test_group_without_patches_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            package, _, _ = self.make_fixture(root)
            groups = package.directory / "groups.tsv"
            with groups.open("a", encoding="utf-8", newline="") as handle:
                handle.write("unused\t1\tUnused\tNo patches.\t\n")
            with self.assertRaisesRegex(patcher.PatchError, "group unused has no patches"):
                patcher.load_package(package.directory)

    def test_hierarchical_enabled_selection_and_explicit_override(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package, _, target_data = self.make_fixture(Path(temporary))
            package.patches["test_patch"] = replace(
                package.patches["test_patch"], enabled=True
            )
            selected = patcher.selected_patch_ids(package, [], enabled=True)
            self.assertEqual(selected, ["test_patch"])

            package.groups["fixture_group"] = replace(
                package.groups["fixture_group"], enabled=False
            )
            self.assertEqual(
                patcher.selected_patch_ids(package, [], enabled=True),
                [],
            )
            self.assertEqual(
                patcher.selected_patch_ids(
                    package, ["test_patch"], enabled=False
                ),
                ["test_patch"],
            )

            package.groups["fixture_group"] = replace(
                package.groups["fixture_group"], enabled=True
            )
            self.assertEqual(
                patcher.selected_patch_ids(package, [], enabled=True),
                ["test_patch"],
            )
            edits = patcher.validate_selection(package, selected, for_apply=True)
            buffers, rows, _ = patcher.compose_edits(package, target_data, edits)
            self.assertEqual(len(edits), 2)
            self.assertEqual([row["outcome"] for row in rows], ["applied", "applied"])
            self.assertEqual(buffers["destination"][4:8], bytes.fromhex("10203040"))

    def test_enabled_non_applicable_patch_is_rejected_under_disabled_group(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            package, _, _ = self.make_fixture(root)
            groups = package.directory / "groups.tsv"
            groups.write_text(
                groups.read_text(encoding="utf-8").replace(
                    "fixture_group\t1\t",
                    "fixture_group\t0\t",
                ),
                encoding="utf-8",
            )
            patches = package.directory / "patches.tsv"
            patches.write_text(
                patches.read_text(encoding="utf-8")
                .replace("test_patch\tfixture_group\t0\t", "test_patch\tfixture_group\t1\t")
                .replace("approved_for_test", "pending"),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                patcher.PatchError, "enabled patches must be applicable"
            ):
                patcher.load_package(package.directory)

    def test_cli_exposes_enabled_selection_without_defaults_alias(self) -> None:
        parser = patcher.build_parser()
        enabled_args = parser.parse_args(
            ["plan", "--package", "fixture", "--enabled"]
        )
        self.assertTrue(enabled_args.enabled)
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            parser.parse_args(["plan", "--package", "fixture", "--defaults"])

    def test_empty_v3_package_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "empty"
            write_tsv(directory / "targets.tsv", patcher.TARGET_FIELDS, [])
            write_tsv(directory / "groups.tsv", patcher.GROUP_FIELDS, [])
            write_tsv(directory / "patches.tsv", patcher.PATCH_FIELDS, [])
            write_tsv(directory / "edits.tsv", patcher.EDIT_FIELDS, [])
            package = patcher.load_package(directory)
            self.assertEqual(package.groups, {})
            self.assertEqual(package.patches, {})
            self.assertEqual(patcher.verify_package_data(package, {}), {})

    def test_incompatible_overlapping_patches_fail_during_composition(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package, _, target_data = self.make_fixture(Path(temporary))
            second_group = patcher.Group("second_group", True, "Second", "", "")
            second_patch = replace(
                package.patches["test_patch"],
                patch_id="second_patch",
                group_id="second_group",
            )
            package.groups["second_group"] = second_group
            package.patches["second_patch"] = second_patch
            package.edits.append(
                replace(
                    package.edits[0],
                    edit_id="conflicting_edit",
                    patch_id="second_patch",
                    replacement_hex="FFFFFFFF",
                )
            )
            edits = patcher.validate_selection(
                package, ["test_patch", "second_patch"], for_apply=True
            )
            with self.assertRaisesRegex(patcher.PatchError, "Conflicting edit"):
                patcher.compose_edits(package, target_data, edits, feature_id="feature")

    def test_intentional_overlapping_patch_chain_is_applied_in_order(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package, _, target_data = self.make_fixture(Path(temporary))
            package.groups["second_group"] = patcher.Group(
                "second_group", True, "Second", "", ""
            )
            package.patches["second_patch"] = replace(
                package.patches["test_patch"],
                patch_id="second_patch",
                group_id="second_group",
            )
            package.edits.append(
                replace(
                    package.edits[0],
                    edit_id="chained_edit",
                    patch_id="second_patch",
                    expected_hex="10203040",
                    replacement_hex="55667788",
                )
            )
            edits = patcher.validate_selection(
                package, ["test_patch", "second_patch"], for_apply=True
            )
            buffers, rows, _ = patcher.compose_edits(package, target_data, edits)
            self.assertEqual(buffers["destination"][4:8], bytes.fromhex("55667788"))
            self.assertEqual(rows[0]["outcome"], "applied")
            self.assertEqual(rows[1]["outcome"], "applied")
if __name__ == "__main__":
    unittest.main()
