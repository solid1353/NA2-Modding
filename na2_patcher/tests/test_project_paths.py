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
                    "na2_iso": "@build/NA2.iso",
                    "nun5_iso": "@build/NUN5.iso",
                    "current_iso": "@build/NA2.28 - Current.iso",
                    "previous_iso": "@build/NA2.28 - Previous.iso",
                },
            )

            paths = load_project_paths(manifest)

            self.assertEqual(
                paths.file("na2_iso"),
                root.resolve() / "build" / "NA2.iso",
            )
            self.assertEqual(
                paths.file("nun5_iso"),
                root.resolve() / "build" / "NUN5.iso",
            )
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

    def test_loads_file_below_external_configured_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            root = workspace / "repository"
            source = workspace / "source"
            root.mkdir()
            source.mkdir()
            manifest = {
                "schema_version": 1,
                "roots": {
                    "repository": ".",
                    "source": "../source",
                },
                "files": {"nun5_iso": "@source/NUN5.iso"},
            }
            manifest_path = root / "project-paths.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            paths = load_project_paths(manifest_path)

            self.assertEqual(paths.file("nun5_iso"), source.resolve() / "NUN5.iso")

    def test_loads_root_below_another_configured_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            root = workspace / "repository"
            source = workspace / "source"
            extracted = source / "NA2.iso.files"
            root.mkdir()
            extracted.mkdir(parents=True)
            manifest = {
                "schema_version": 1,
                "roots": {
                    "repository": ".",
                    "source_na2": "@source/NA2.iso.files",
                    "source": "../source",
                },
                "files": {"na2_iso": "@source/NA2.iso"},
            }
            manifest_path = root / "project-paths.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            paths = load_project_paths(manifest_path)

            self.assertEqual(paths.path("source_na2"), extracted.resolve())

    def test_defers_existence_checks_for_protected_root_and_children(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = {
                "schema_version": 1,
                "existence_deferred_roots": ["pcsx2_user"],
                "roots": {
                    "repository": ".",
                    "pcsx2_user": "missing-user-pcsx2",
                    "pcsx2_user_memcards": "@pcsx2_user/memcards",
                },
                "files": {
                    "pcsx2_user_exe": "@pcsx2_user/pcsx2-qt.exe",
                },
            }
            manifest_path = root / "project-paths.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            paths = load_project_paths(manifest_path)

            self.assertEqual(
                paths.path("pcsx2_user_memcards"),
                root.resolve() / "missing-user-pcsx2" / "memcards",
            )

    def test_rejects_unknown_existence_deferred_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = {
                "schema_version": 1,
                "existence_deferred_roots": ["missing"],
                "roots": {"repository": "."},
                "files": {"current_iso": "Current.iso"},
            }
            manifest_path = root / "project-paths.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            with self.assertRaisesRegex(
                ValueError, "Invalid existence-deferred project root"
            ):
                load_project_paths(manifest_path)

    def test_rejects_root_alias_cycle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = {
                "schema_version": 1,
                "roots": {
                    "repository": ".",
                    "first": "@second/child",
                    "second": "@first/child",
                },
                "files": {"current_iso": "Current.iso"},
            }
            manifest_path = root / "project-paths.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "dependency cycle"):
                load_project_paths(manifest_path, allow_missing=True)

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
