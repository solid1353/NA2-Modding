from __future__ import annotations

import csv
import hashlib
import tempfile
import unittest
from pathlib import Path

from na2_patcher.profile import (
    MODULE_FIELDS,
    content_sha256,
    load_profile,
    module_content_sha256,
)


def write_tsv(path: Path, fields: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(fields)
        writer.writerows(rows)


class ProfileTests(unittest.TestCase):
    def create_profile(
        self,
        workspace: Path,
        expected_hash: str,
        *,
        enabled: str = "1",
    ) -> Path:
        source = workspace / "source" / "input.bin"
        source.parent.mkdir(parents=True)
        source.write_bytes(b"profile input")
        profile = workspace / "profiles" / "test"
        write_tsv(
            profile / "manifest.tsv",
            ["key", "value"],
            [["schema_version", "1"], ["profile_id", "test"]],
        )
        write_tsv(
            profile / "roots.tsv",
            ["root_id", "path"],
            [["na2", "source"]],
        )
        write_tsv(
            profile / "modules.tsv",
            MODULE_FIELDS,
            [
                [
                    "one",
                    "10",
                    enabled,
                    "translation",
                    "source/input.bin",
                    expected_hash,
                    "",
                    "test",
                ]
            ],
        )
        return profile

    def test_loads_hash_pinned_relative_profile(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            expected = hashlib.sha256(b"profile input").hexdigest().upper()
            profile = load_profile(self.create_profile(workspace, expected), workspace)
            self.assertEqual(profile.manifest["profile_id"], "test")
            self.assertEqual(profile.modules[0].module_id, "one")

    def test_rejects_enabled_input_hash_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            profile_path = self.create_profile(workspace, "0" * 64)
            with self.assertRaisesRegex(ValueError, "does not match"):
                load_profile(profile_path, workspace)

    def test_disabled_input_hash_mismatch_does_not_block_active_profile(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            disabled = self.create_profile(workspace, "0" * 64, enabled="0")
            modules = disabled / "modules.tsv"
            with modules.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle, delimiter="\t"))
            rows.append(
                {
                    "module_id": "enabled",
                    "order": "20",
                    "enabled": "1",
                    "module": "translation",
                    "input": "source/input.bin",
                    "expected_sha256": hashlib.sha256(b"profile input")
                    .hexdigest()
                    .upper(),
                    "selection": "",
                    "reason": "active",
                }
            )
            with modules.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle, fieldnames=MODULE_FIELDS, delimiter="\t", lineterminator="\n"
                )
                writer.writeheader()
                writer.writerows(rows)
            profile = load_profile(disabled, workspace)
            self.assertFalse(profile.modules[0].enabled)
            self.assertTrue(profile.modules[1].enabled)

    def test_rejects_retired_zip_overlay_module(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            expected = hashlib.sha256(b"profile input").hexdigest().upper()
            profile_path = self.create_profile(workspace, expected)
            modules = profile_path / "modules.tsv"
            text = modules.read_text(encoding="utf-8")
            modules.write_text(
                text.replace("\ttranslation\t", "\tzip_overlay\t"),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "unsupported module 'zip_overlay'"):
                load_profile(profile_path, workspace)

    def test_directory_hash_is_path_and_content_sensitive(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "a").mkdir()
            (root / "a" / "one.txt").write_text("one", encoding="utf-8")
            first = content_sha256(root / "a")
            (root / "a" / "one.txt").write_text("two", encoding="utf-8")
            second = content_sha256(root / "a")
            self.assertNotEqual(first, second)

    def test_raw_binary_hash_excludes_documentation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / "package"
            package.mkdir()
            for name in ("manifest.tsv", "targets.tsv", "patches.tsv", "relations.tsv"):
                (package / name).write_text(f"{name}\n", encoding="utf-8")
            (package / "edits.tsv").write_text("blob_path\n", encoding="utf-8")
            (package / "README.md").write_text("first\n", encoding="utf-8")

            first = module_content_sha256(package, "raw_binary")
            (package / "README.md").write_text("second\n", encoding="utf-8")
            second = module_content_sha256(package, "raw_binary")
            self.assertEqual(first, second)

            (package / "patches.tsv").write_text("changed\n", encoding="utf-8")
            third = module_content_sha256(package, "raw_binary")
            self.assertNotEqual(second, third)

    def test_raw_binary_hash_includes_referenced_blobs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / "package"
            package.mkdir()
            for name in ("manifest.tsv", "targets.tsv", "patches.tsv", "relations.tsv"):
                (package / name).write_text(f"{name}\n", encoding="utf-8")
            (package / "payload.bin").write_bytes(b"one")
            (package / "edits.tsv").write_text(
                "blob_path\npayload.bin\n", encoding="utf-8"
            )

            first = module_content_sha256(package, "raw_binary")
            (package / "payload.bin").write_bytes(b"two")
            second = module_content_sha256(package, "raw_binary")
            self.assertNotEqual(first, second)

    def test_current_enabled_module_hashes_match(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        modules_path = (
            repository / "na2_patcher" / "profiles" / "current" / "modules.tsv"
        )
        with modules_path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle, delimiter="\t"))
        for row in rows:
            if row["enabled"] != "1":
                continue
            input_path = repository / row["input"]
            self.assertEqual(
                module_content_sha256(input_path, row["module"]),
                row["expected_sha256"],
                row["module_id"],
            )


if __name__ == "__main__":
    unittest.main()
