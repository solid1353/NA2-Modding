from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.lib.paths import load_local_paths, load_paths


class ProjectPathTests(unittest.TestCase):
    def write_manifest(self, root: Path, files: dict[str, str] | None) -> Path:
        manifest = {
            "roots": {"build": "build"},
        }
        if files is not None:
            manifest["files"] = files
        path = root / "paths.json"
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
                    "first_output": "@build/first.iso",
                    "second_output": "@build/second.iso",
                },
            )

            paths = load_paths(manifest)

            self.assertEqual(
                paths.file("na2_iso"),
                root.resolve() / "build" / "NA2.iso",
            )
            self.assertEqual(
                paths.file("nun5_iso"),
                root.resolve() / "build" / "NUN5.iso",
            )
            self.assertEqual(
                paths.file("first_output"),
                root.resolve() / "build" / "first.iso",
            )
            self.assertEqual(
                paths.file("second_output"),
                root.resolve() / "build" / "second.iso",
            )

    def test_local_paths_do_not_load_missing_imported_projects(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = {
                "imports": {"workshop": "../missing/paths.json"},
                "roots": {"build": "build"},
                "files": {"project_settings": "game.json"},
            }
            (root / "paths.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )
            (root / "build").mkdir()

            paths = load_local_paths(root)

            self.assertEqual(paths.repository, root.resolve())
            self.assertEqual(paths.path("build"), root.resolve() / "build")
            self.assertNotIn("workshop", paths.roots)

    def test_rejects_file_outside_repository(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.write_manifest(
                root,
                {"output_iso": "../outside.iso"},
            )

            with self.assertRaisesRegex(ValueError, "remain within the repository"):
                load_paths(manifest)

    def test_loads_file_below_external_configured_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            root = workspace / "repository"
            source = workspace / "source"
            root.mkdir()
            source.mkdir()
            manifest = {
                "roots": {
                    "source": "../source",
                },
                "files": {"nun5_iso": "@source/NUN5.iso"},
            }
            manifest_path = root / "paths.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            paths = load_paths(manifest_path)

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
                "roots": {
                    "source_na2": "@source/NA2.iso.files",
                    "source": "../source",
                },
                "files": {"na2_iso": "@source/NA2.iso"},
            }
            manifest_path = root / "paths.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            paths = load_paths(manifest_path)

            self.assertEqual(paths.path("source_na2"), extracted.resolve())

    def test_defers_existence_checks_for_protected_root_and_children(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = {
                "existence_deferred_roots": ["optional_runtime"],
                "roots": {
                    "optional_runtime": "missing-user-runtime",
                    "optional_runtime_data": "@optional_runtime/data",
                },
                "files": {
                    "optional_runtime_exe": "@optional_runtime/runtime.exe",
                },
            }
            manifest_path = root / "paths.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            paths = load_paths(manifest_path)

            self.assertEqual(
                paths.path("optional_runtime_data"),
                root.resolve() / "missing-user-runtime" / "data",
            )

    def test_rejects_unknown_existence_deferred_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = {
                "existence_deferred_roots": ["missing"],
                "roots": {"build": "build"},
                "files": {"output_iso": "output.iso"},
            }
            manifest_path = root / "paths.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            with self.assertRaisesRegex(
                ValueError, "Invalid existence-deferred project root"
            ):
                load_paths(manifest_path)

    def test_rejects_root_alias_cycle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = {
                "roots": {
                    "first": "@second/child",
                    "second": "@first/child",
                },
                "files": {"output_iso": "output.iso"},
            }
            manifest_path = root / "paths.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "dependency cycle"):
                load_paths(manifest_path, allow_missing=True)

    def test_rejects_file_alias_escape(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.write_manifest(
                root,
                {"output_iso": "@build/../outside.iso"},
            )

            with self.assertRaisesRegex(ValueError, "within configured root"):
                load_paths(manifest)

    def test_rejects_unknown_file_root_alias(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.write_manifest(
                root,
                {"output_iso": "@missing/output.iso"},
            )

            with self.assertRaisesRegex(ValueError, "unknown project root"):
                load_paths(manifest)

    def test_requires_canonical_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.write_manifest(root, None)

            with self.assertRaisesRegex(ValueError, "has no files"):
                load_paths(manifest)

    def write_workshop_project(
        self, workspace: Path, launch_settings: dict[str, object]
    ) -> Path:
        """Create a project importing a Workshop with the real catalog code."""
        real_repository = Path(__file__).resolve().parents[2]
        real_import = json.loads(
            (real_repository / "paths.json").read_text(encoding="utf-8")
        )["imports"]["workshop"]
        real_workshop_lib = (real_repository / real_import).parent / "scripts" / "lib"
        workshop = workspace / "workshop"
        repository = workspace / "repository"
        for path in (
            workshop / "scripts/lib",
            workshop / "source/NA2.iso.files",
            workshop / "source/NUN3.iso.files",
            workshop / "source/NUN5.iso.files",
            workshop / "pcsx2_files/games/NUN3",
            workshop / "pcsx2_files/input_profiles/sources/overrides/games",
            repository / "build",
            repository / "pcsx2_files/games/NA2",
            repository / "pcsx2_files/games/NUN5",
        ):
            path.mkdir(parents=True)
        for name in ("paths.py", "game_catalog.py"):
            shutil.copyfile(real_workshop_lib / name, workshop / "scripts/lib" / name)
        (workshop / "paths.json").write_text(
            json.dumps(
                {
                    "roots": {
                        "source": "source",
                        "pcsx2_files": "pcsx2_files",
                        "pcsx2_input_profiles": "@pcsx2_files/input_profiles",
                    },
                    "files": {"source_catalog": "games.json"},
                }
            ),
            encoding="utf-8",
        )
        (workshop / "games.json").write_text(
            json.dumps(
                {
                    "sources": {
                        "NA2": {"serial": "SLPS-25837", "crc": "C0659AD1"},
                        "NUN3": {"serial": "SLUS-21727", "crc": "EE3737A4"},
                        "NUN5": {"serial": "SLES-55605", "crc": "C071D4C1"},
                    }
                }
            ),
            encoding="utf-8",
        )
        (
            workshop
            / "pcsx2_files/input_profiles/sources/overrides/games/NA2.ini"
        ).write_text("[Pad1]\nCross = SDL-0/FaceNorth\n", encoding="utf-8")
        (repository / "paths.json").write_text(
            json.dumps(
                {
                    "imports": {"workshop": "../workshop/paths.json"},
                    "roots": {"build": "build", "pcsx2_files": "pcsx2_files"},
                    "files": {"project_settings": "project.json"},
                }
            ),
            encoding="utf-8",
        )
        (repository / "project.json").write_text(
            json.dumps({"launch_settings": launch_settings}), encoding="utf-8"
        )
        return repository / "paths.json"

    def test_game_catalog_derives_sources_from_their_bundle_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory).resolve()
            manifest_path = self.write_workshop_project(
                workspace,
                {
                    "default": {
                        "startup_fast_forward_frames": 321,
                        "speed_after_startup": "turbo",
                    },
                    "practice": {"speed_after_startup": "normal"},
                },
            )
            workshop = workspace / "workshop"
            bundles = workspace / "repository/pcsx2_files/games"

            paths = load_paths(manifest_path)

            self.assertEqual(paths.file("nun5_iso"), workshop / "source/NUN5.iso")
            self.assertEqual(
                paths.path("source_nun5"), workshop / "source/NUN5.iso.files"
            )
            self.assertEqual(
                paths.file("input_profile"),
                workshop / "pcsx2_files/input_profiles/Default_NA2.ini",
            )
            na2 = paths.games["NA2"]["config"]
            self.assertEqual(
                na2["input_profile_overrides"],
                workshop
                / "pcsx2_files/input_profiles/sources/overrides/games/NA2.ini",
            )
            self.assertEqual(na2["cheats"], bundles / "NA2/NA2.pnach")
            self.assertEqual(na2["game_settings"], bundles / "NA2/NA2.ini")
            self.assertEqual(na2["memory_card"], bundles / "NA2/NA2.ps2")
            self.assertEqual(
                paths.file("nun3_memory_card"),
                workshop / "pcsx2_files/games/NUN3/NUN3.ps2",
            )
            self.assertEqual(
                paths.settings["launch_settings"]["practice"],
                {"speed_after_startup": "normal"},
            )

    def test_rejects_invalid_launch_settings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest_path = self.write_workshop_project(
                Path(directory).resolve(),
                {
                    "default": {
                        "startup_fast_forward_frames": 321,
                        "speed_after_startup": "fast",
                    }
                },
            )

            with self.assertRaisesRegex(ValueError, "must be normal or turbo"):
                load_paths(manifest_path)

if __name__ == "__main__":
    unittest.main()
