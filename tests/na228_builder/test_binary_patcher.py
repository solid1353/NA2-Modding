from __future__ import annotations

import csv
import hashlib
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path, PurePosixPath

from na228_builder.modules.binary_patcher import engine as patcher
from na228_builder.scripts.build_configuration import write_binary_patch_log


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


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
        package = patcher.Package(
            directory=package_dir,
            package_id="fixture.binary_patcher",
            targets={
                "destination": patcher.Target(
                    target_id="destination",
                    root_id="na2",
                    role="destination",
                    path=PurePosixPath("target.bin"),
                    expected_size=len(clean),
                    expected_sha256=sha256(clean),
                ),
                "source": patcher.Target(
                    target_id="source",
                    root_id="nun5",
                    role="source",
                    path=PurePosixPath("source.bin"),
                    expected_size=len(source),
                    expected_sha256=sha256(source),
                ),
            },
            patches={
                "test_patch": patcher.Patch(
                    patch_id="test_patch",
                    group_id="fixture_group",
                    evidence_id="",
                )
            },
            edits=[
                patcher.Edit(
                    edit_id="replace_word",
                    patch_id="test_patch",
                    order=10,
                    destination_target_id="destination",
                    destination_offset=4,
                    operation="replace",
                    length=4,
                    expected_hex=clean[4:8].hex().upper(),
                    expected_sha256="",
                    replacement_hex="10203040",
                    source_target_id="",
                    source_offset=None,
                    source_expected_hex="",
                    source_expected_sha256="",
                    blob_path=None,
                    blob_offset=None,
                    blob_sha256="",
                    fill_hex="",
                    reason="literal replacement",
                ),
                patcher.Edit(
                    edit_id="copy_word",
                    patch_id="test_patch",
                    order=20,
                    destination_target_id="destination",
                    destination_offset=12,
                    operation="copy",
                    length=4,
                    expected_hex=clean[12:16].hex().upper(),
                    expected_sha256="",
                    replacement_hex="",
                    source_target_id="source",
                    source_offset=0,
                    source_expected_hex="AABBCCDD",
                    source_expected_sha256="",
                    blob_path=None,
                    blob_offset=None,
                    blob_sha256="",
                    fill_hex="",
                    reason="verified source copy",
                ),
            ],
        )
        roots = {"na2": na2, "nun5": nun5}
        target_data = patcher.verify_package_data(package, roots)
        return package, roots, target_data

    def test_configuration_log_writes_binary_patch_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            package, _, target_data = self.make_fixture(root)
            edits = patcher.ordered_edits(package)
            buffers, patch_rows, before_hashes = patcher.compose_edits(
                package,
                target_data,
                edits,
            )
            after_hashes = {
                target_id: sha256(bytes(data))
                for target_id, data in buffers.items()
            }
            logs = root / "logs"

            write_binary_patch_log(
                {
                    "package": package,
                    "edits": edits,
                    "patch_rows": patch_rows,
                    "before_hashes": before_hashes,
                    "after_hashes": after_hashes,
                },
                logs,
                output_iso_text="build/NA2.28.iso",
                log_directory_text="logs/binary_patcher",
            )

            with (logs / "run_summary.tsv").open(
                encoding="utf-8", newline=""
            ) as handle:
                reader = csv.DictReader(handle, delimiter="\t")
                summary = next(reader)

            self.assertEqual(summary["package_id"], package.package_id)
            with (logs / "patch_inventory.tsv").open(
                encoding="utf-8", newline=""
            ) as handle:
                inventory = list(csv.DictReader(handle, delimiter="\t"))
            self.assertEqual(
                inventory,
                [{
                    "group_id": "fixture_group",
                    "patch_id": "test_patch",
                    "evidence_id": "",
                }],
            )

    def test_edits_cannot_reference_a_patch_outside_the_package(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package, _, _ = self.make_fixture(Path(temporary))
            package.edits[0] = replace(
                package.edits[0], patch_id="missing_patch"
            )
            with self.assertRaisesRegex(patcher.PatchError, "unknown patches"):
                patcher.ordered_edits(package)

    def test_expected_byte_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            package, roots, _ = self.make_fixture(root)
            (roots["na2"] / "target.bin").write_bytes(b"X" + bytes(range(1, 16)))
            with self.assertRaisesRegex(patcher.PatchError, "SHA-256 mismatch"):
                patcher.verify_package_data(package, roots)

    def test_blob_replacement_verifies_file_and_composes_selected_range(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            package, roots, _ = self.make_fixture(root)
            blob = bytes.fromhex("00AABBCCDDFF")
            blob_path = package.directory / "assets" / "replacement.bin"
            blob_path.parent.mkdir(parents=True)
            blob_path.write_bytes(blob)
            package.edits = [
                replace(
                    package.edits[0],
                    operation="blob",
                    replacement_hex="",
                    blob_path=PurePosixPath("assets/replacement.bin"),
                    blob_offset=1,
                    blob_sha256=sha256(blob),
                )
            ]

            target_data = patcher.verify_package_data(package, roots)
            edits = patcher.ordered_edits(package)
            buffers, _, _ = patcher.compose_edits(
                package,
                target_data,
                edits,
            )
            self.assertEqual(
                buffers["destination"][4:8], bytes.fromhex("AABBCCDD")
            )

            blob_path.write_bytes(blob + b"X")
            with self.assertRaisesRegex(patcher.PatchError, "blob SHA-256 mismatch"):
                patcher.verify_package_data(package, roots)

    def test_composition_accepts_unrelated_prior_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package, _, target_data = self.make_fixture(Path(temporary))
            edits = patcher.ordered_edits(package)
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
            edits = patcher.ordered_edits(package)
            staged = bytearray(target_data["destination"])
            staged[4] ^= 0xFF
            with self.assertRaisesRegex(patcher.PatchError, "staged destination"):
                patcher.compose_edits(
                    package,
                    target_data,
                    edits,
                    {"destination": staged},
                )

    def test_package_applies_every_patch_in_declared_order(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package, _, target_data = self.make_fixture(Path(temporary))
            package.patches["second_patch"] = patcher.Patch(
                patch_id="second_patch",
                group_id="second_group",
                evidence_id="SECOND",
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
            edits = patcher.ordered_edits(package)
            buffers, rows, _ = patcher.compose_edits(package, target_data, edits)
            self.assertEqual(len(edits), 3)
            self.assertEqual(
                [row["patch_id"] for row in rows[:2]],
                ["test_patch", "second_patch"],
            )
            self.assertEqual(buffers["destination"][4:8], bytes.fromhex("55667788"))

    def test_incompatible_overlapping_patches_fail_during_composition(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package, _, target_data = self.make_fixture(Path(temporary))
            second_patch = patcher.Patch(
                patch_id="second_patch",
                group_id="second_group",
                evidence_id="",
            )
            package.patches["second_patch"] = second_patch
            package.edits.append(
                replace(
                    package.edits[0],
                    edit_id="conflicting_edit",
                    patch_id="second_patch",
                    replacement_hex="FFFFFFFF",
                )
            )
            edits = patcher.ordered_edits(package)
            with self.assertRaisesRegex(patcher.PatchError, "Conflicting edit"):
                patcher.compose_edits(package, target_data, edits, feature_id="feature")

    def test_intentional_overlapping_patch_chain_is_applied_in_order(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package, _, target_data = self.make_fixture(Path(temporary))
            package.patches["second_patch"] = patcher.Patch(
                patch_id="second_patch",
                group_id="second_group",
                evidence_id="",
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
            edits = patcher.ordered_edits(package)
            buffers, rows, _ = patcher.compose_edits(package, target_data, edits)
            self.assertEqual(buffers["destination"][4:8], bytes.fromhex("55667788"))
            self.assertEqual(rows[0]["outcome"], "applied")
            self.assertEqual(rows[1]["outcome"], "applied")
if __name__ == "__main__":
    unittest.main()
