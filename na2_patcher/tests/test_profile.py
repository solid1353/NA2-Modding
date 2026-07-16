from __future__ import annotations

import csv
import hashlib
import tempfile
import unittest
from pathlib import Path

from na2_patcher.profile import content_sha256, load_profile


def write_tsv(path: Path, fields: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(fields)
        writer.writerows(rows)


class ProfileTests(unittest.TestCase):
    def create_profile(self, workspace: Path, expected_hash: str) -> Path:
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
            [
                "module_id",
                "order",
                "enabled",
                "module",
                "input",
                "expected_sha256",
                "selection",
                "reason",
            ],
            [["one", "10", "1", "zip_overlay", "source/input.bin", expected_hash, "", "test"]],
        )
        return profile

    def test_loads_hash_pinned_relative_profile(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            expected = hashlib.sha256(b"profile input").hexdigest().upper()
            profile = load_profile(self.create_profile(workspace, expected), workspace)
            self.assertEqual(profile.manifest["profile_id"], "test")
            self.assertEqual(profile.modules[0].module_id, "one")

    def test_rejects_input_hash_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            profile_path = self.create_profile(workspace, "0" * 64)
            with self.assertRaisesRegex(ValueError, "does not match"):
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


if __name__ == "__main__":
    unittest.main()
