from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from na2_patcher.project_paths import load_project_paths


class ProjectPathTests(unittest.TestCase):
    def write_manifest(self, root: Path, files: dict[str, str] | None) -> Path:
        manifest = {
            "schema_version": 1,
            "roots": {"repository": ".", "build": "build"},
        }
        if files is not None:
            manifest["files"] = files
        path = root / "project-paths.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        (root / "build").mkdir()
        return path

    def test_loads_canonical_files_without_requiring_outputs_to_exist(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.write_manifest(
                root,
                {
                    "current_iso": "@build/NA2.28 - Current.iso",
                    "previous_iso": "@build/NA2.28 - Previous.iso",
                },
            )

            paths = load_project_paths(manifest)

            self.assertEqual(
                paths.file("current_iso"),
                root.resolve() / "build" / "NA2.28 - Current.iso",
            )
            self.assertEqual(
                paths.file("previous_iso"),
                root.resolve() / "build" / "NA2.28 - Previous.iso",
            )

    def test_rejects_file_outside_repository(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.write_manifest(
                root,
                {"current_iso": "../outside.iso"},
            )

            with self.assertRaisesRegex(ValueError, "remain within the repository"):
                load_project_paths(manifest)

    def test_rejects_file_alias_escape(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.write_manifest(
                root,
                {"current_iso": "@build/../outside.iso"},
            )

            with self.assertRaisesRegex(ValueError, "within configured root"):
                load_project_paths(manifest)

    def test_rejects_unknown_file_root_alias(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.write_manifest(
                root,
                {"current_iso": "@missing/Current.iso"},
            )

            with self.assertRaisesRegex(ValueError, "unknown project root"):
                load_project_paths(manifest)

    def test_requires_canonical_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.write_manifest(root, None)

            with self.assertRaisesRegex(ValueError, "has no files"):
                load_project_paths(manifest)


if __name__ == "__main__":
    unittest.main()
