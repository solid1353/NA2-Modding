from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.lib.paths import derive_game_paths, load_local_paths, load_paths


class ProjectPathTests(unittest.TestCase):
    def write_manifest(self, root: Path, files: dict[str, str] | None) -> Path:
        manifest = {
            "roots": {"repository": ".", "build": "build"},
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
                    "latest_iso": "@build/NA2.28 - Latest.iso",
                    "previous_iso": "@build/NA2.28 - Previous.iso",
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
                paths.file("latest_iso"),
                root.resolve() / "build" / "NA2.28 - Latest.iso",
            )
            self.assertEqual(
                paths.file("previous_iso"),
                root.resolve() / "build" / "NA2.28 - Previous.iso",
            )

    def test_local_paths_do_not_load_missing_imported_projects(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = {
                "imports": {"workshop": "../missing/paths.json"},
                "roots": {"repository": ".", "build": "build"},
                "files": {"settings": "game.json"},
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
                {"latest_iso": "../outside.iso"},
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
                    "repository": ".",
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
                    "repository": ".",
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
                    "repository": ".",
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
                "roots": {"repository": "."},
                "files": {"latest_iso": "Latest.iso"},
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
                    "repository": ".",
                    "first": "@second/child",
                    "second": "@first/child",
                },
                "files": {"latest_iso": "Latest.iso"},
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
                {"latest_iso": "@build/../outside.iso"},
            )

            with self.assertRaisesRegex(ValueError, "within configured root"):
                load_paths(manifest)

    def test_rejects_unknown_file_root_alias(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.write_manifest(
                root,
                {"latest_iso": "@missing/Latest.iso"},
            )

            with self.assertRaisesRegex(ValueError, "unknown project root"):
                load_paths(manifest)

    def test_requires_canonical_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.write_manifest(root, None)

            with self.assertRaisesRegex(ValueError, "has no files"):
                load_paths(manifest)

    def test_game_catalog_derives_builds_and_sources(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for path in (
                "build",
                "source/NA2.iso.files",
                "source/NUN5.iso.files",
                "pcsx2/game_settings",
                "pcsx2/input_profiles",
                "pcsx2/memory_cards",
                "pcsx2_files/games/NA2",
                "pcsx2_files/games/NA228",
                "pcsx2_files/games/NUN5",
            ):
                (root / path).mkdir(parents=True, exist_ok=True)
            manifest = {
                "roots": {
                    "repository": ".",
                    "build": "build",
                    "source": "source",
                    "pcsx2_files": "pcsx2_files",
                    "pcsx2_game_settings": "pcsx2/game_settings",
                    "pcsx2_input_profiles": "pcsx2/input_profiles",
                    "pcsx2_memory_cards": "pcsx2/memory_cards",
                },
                "files": {
                    "game_catalog": "@repository/games.json",
                    "settings": "@repository/game.json",
                },
            }
            source_catalog = {
                "sources": {
                    "NA2": {
                        "serial": "SLPS-25837",
                        "crc": "C0659AD1",
                    },
                    "NUN5": {
                        "serial": "SLUS-21727",
                        "crc": "EE3737A4",
                    },
                },
            }
            settings = {
                "title": "Narutimate Accel v2.28",
                "serial": "SLOP-NA228",
                "output_boot_path": "SLOP_NA2.28",
                "launch_settings": {
                    "startup_fast_forward_frames": 321,
                    "practice": {"startup_fast_forward_frames": 654},
                },
                "builds": {
                    "latest": {
                        "aliases": ["l"],
                        "configuration": "dev",
                        "rotate_to": "previous",
                    },
                    "previous": {},
                    "e2e_test_shifted": {"configuration": "test"},
                },
            }
            manifest_path = root / "paths.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            (root / "games.json").write_text(
                json.dumps(source_catalog), encoding="utf-8"
            )
            (root / "game.json").write_text(
                json.dumps(settings), encoding="utf-8"
            )
            (root / "pcsx2_files/games/NA228/NA228.ini").write_text(
                "[EmuCore]\nEnableCheats = true\n",
                encoding="utf-8",
            )
            override_directory = (
                root / "pcsx2/input_profiles/sources/overrides/games"
            )
            override_directory.mkdir(parents=True)
            (override_directory / "NA2.ini").write_text(
                "[Pad1]\nCross = SDL-0/FaceNorth\n",
                encoding="utf-8",
            )

            paths = load_paths(manifest_path)

            self.assertEqual(
                paths.file("latest_iso"),
                root.resolve() / "build" / "Narutimate Accel v2.28 - Latest.iso",
            )
            self.assertEqual(
                paths.file("latest_memory_card"),
                root.resolve() / "pcsx2_files/games/NA228/NA228.ps2",
            )
            self.assertEqual(
                paths.file("e2e_test_shifted_iso"),
                root.resolve()
                / "build/Narutimate Accel v2.28 - E2E Test Shifted.iso",
            )
            self.assertEqual(
                paths.file("nun5_iso"),
                root.resolve() / "source/NUN5.iso",
            )
            self.assertEqual(
                paths.path("source_nun5"),
                root.resolve() / "source/NUN5.iso.files",
            )
            self.assertEqual(
                paths.file("input_profile"),
                root.resolve() / "pcsx2/input_profiles/Default_Base.ini",
            )
            catalog = {
                "sources": source_catalog["sources"],
                "title": settings["title"],
                "serial": settings["serial"],
                "builds": settings["builds"],
            }
            na2_paths = derive_game_paths(
                "NA2",
                catalog,
                {
                    "repository": root.resolve(),
                    "build": root.resolve() / "build",
                    "source": root.resolve() / "source",
                    "pcsx2_files": root.resolve() / "pcsx2_files",
                    "pcsx2_game_settings": root.resolve() / "pcsx2/game_settings",
                    "pcsx2_input_profiles": root.resolve() / "pcsx2/input_profiles",
                    "pcsx2_memory_cards": root.resolve() / "pcsx2/memory_cards",
                },
            )
            self.assertEqual(
                na2_paths["input_profile"],
                root.resolve() / "pcsx2/input_profiles/Default_NA2.ini",
            )
            self.assertEqual(
                na2_paths["input_profile_overrides"],
                root.resolve()
                / "pcsx2/input_profiles/sources/overrides/games/NA2.ini",
            )
            self.assertEqual(
                na2_paths["cheats"],
                root.resolve() / "pcsx2_files/games/NA2/NA2.pnach",
            )
            self.assertEqual(
                na2_paths["game_settings"],
                root.resolve() / "pcsx2_files/games/NA2/NA2.ini",
            )
            self.assertEqual(
                na2_paths["memory_card"],
                root.resolve() / "pcsx2_files/games/NA2/NA2.ps2",
            )
            self.assertEqual(
                paths.file("cheat_template"),
                root.resolve() / "pcsx2_files/games/NA228/NA228.pnach",
            )
            self.assertEqual(
                paths.file("gamesettings_template"),
                root.resolve() / "pcsx2_files/games/NA228/NA228.ini",
            )

if __name__ == "__main__":
    unittest.main()
