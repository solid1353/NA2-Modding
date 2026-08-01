from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.lib.game_catalog import derive_game_paths
from scripts.lib.project_paths import load_project_paths


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
                    "latest_iso": "@build/NA2.28 - Latest.iso",
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
                paths.file("latest_iso"),
                root.resolve() / "build" / "NA2.28 - Latest.iso",
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
                {"latest_iso": "../outside.iso"},
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
                "existence_deferred_roots": ["pcsx2_stable"],
                "roots": {
                    "repository": ".",
                    "pcsx2_stable": "missing-user-pcsx2",
                    "pcsx2_stable_memcards": "@pcsx2_stable/memcards",
                },
                "files": {
                    "pcsx2_stable_exe": "@pcsx2_stable/pcsx2-qt.exe",
                },
            }
            manifest_path = root / "project-paths.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            paths = load_project_paths(manifest_path)

            self.assertEqual(
                paths.path("pcsx2_stable_memcards"),
                root.resolve() / "missing-user-pcsx2" / "memcards",
            )

    def test_rejects_unknown_existence_deferred_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = {
                "schema_version": 1,
                "existence_deferred_roots": ["missing"],
                "roots": {"repository": "."},
                "files": {"latest_iso": "Latest.iso"},
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
                "files": {"latest_iso": "Latest.iso"},
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
                {"latest_iso": "@build/../outside.iso"},
            )

            with self.assertRaisesRegex(ValueError, "within configured root"):
                load_project_paths(manifest)

    def test_rejects_unknown_file_root_alias(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.write_manifest(
                root,
                {"latest_iso": "@missing/Latest.iso"},
            )

            with self.assertRaisesRegex(ValueError, "unknown project root"):
                load_project_paths(manifest)

    def test_requires_canonical_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.write_manifest(root, None)

            with self.assertRaisesRegex(ValueError, "has no files"):
                load_project_paths(manifest)

    def test_game_catalog_derives_builds_sources_and_shared_config(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for path in (
                "build",
                "source/NA2.iso.files",
                "source/NUN5.iso.files",
                "pcsx2/cheats",
                "pcsx2/game_settings",
                "pcsx2/input_profiles",
                "pcsx2/memory_cards",
            ):
                (root / path).mkdir(parents=True, exist_ok=True)
            manifest = {
                "schema_version": 1,
                "roots": {
                    "repository": ".",
                    "build": "build",
                    "source": "source",
                    "pcsx2_cheats": "pcsx2/cheats",
                    "pcsx2_game_settings": "pcsx2/game_settings",
                    "pcsx2_input_profiles": "pcsx2/input_profiles",
                    "pcsx2_memory_cards": "pcsx2/memory_cards",
                },
                "files": {"game_catalog": "@repository/settings/games.json"},
            }
            catalog = {
                "schema_version": 1,
                "config": {
                    "input_profile": "Default"
                },
                "builds": {
                    "title": "NA v2.28",
                    "serial": "SLOP-NA228",
                    "entries": {
                        "latest": {
                            "aliases": ["l"],
                            "postfix": "Latest",
                        },
                        "previous": {
                            "aliases": ["p"],
                            "postfix": "Previous",
                        },
                    },
                },
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
            manifest_path = root / "project-paths.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            (root / "settings").mkdir()
            (root / "settings/games.json").write_text(
                json.dumps(catalog),
                encoding="utf-8",
            )
            override_directory = root / "pcsx2/input_profiles/sources/games"
            override_directory.mkdir(parents=True)
            (override_directory / "NA2.ini").write_text(
                "[Pad1]\nCross = SDL-0/FaceNorth\n",
                encoding="utf-8",
            )

            paths = load_project_paths(manifest_path)

            self.assertEqual(
                paths.file("latest_iso"),
                root.resolve() / "build" / "NA v2.28 - Latest.iso",
            )
            self.assertEqual(
                paths.file("latest_memory_card"),
                root.resolve() / "pcsx2/memory_cards/NA v2.28 - Latest.ps2",
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
                root.resolve() / "pcsx2/input_profiles/Default.ini",
            )
            na2_paths = derive_game_paths(
                "NA2",
                catalog,
                {
                    "build": root.resolve() / "build",
                    "source": root.resolve() / "source",
                    "pcsx2_cheats": root.resolve() / "pcsx2/cheats",
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
                root.resolve() / "pcsx2/input_profiles/sources/games/NA2.ini",
            )
            self.assertEqual(
                paths.file("cheat_template"),
                root.resolve() / "pcsx2/cheats/sources/SLOP-NA228.pnach",
            )
            self.assertEqual(
                paths.file("gamesettings_template"),
                root.resolve()
                / "pcsx2/game_settings/sources/SLOP-NA228.ini",
            )

    def test_rejects_catalog_file_duplicated_by_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "build").mkdir()
            (root / "pcsx2/cheats").mkdir(parents=True)
            (root / "pcsx2/game_settings").mkdir(parents=True)
            (root / "pcsx2/input_profiles").mkdir(parents=True)
            (root / "pcsx2/memory_cards").mkdir(parents=True)
            manifest = {
                "schema_version": 1,
                "roots": {
                    "repository": ".",
                    "build": "build",
                    "pcsx2_cheats": "pcsx2/cheats",
                    "pcsx2_game_settings": "pcsx2/game_settings",
                    "pcsx2_input_profiles": "pcsx2/input_profiles",
                    "pcsx2_memory_cards": "pcsx2/memory_cards",
                },
                "files": {
                    "game_catalog": "@repository/settings/games.json",
                    "latest_iso": "@build/Latest.iso",
                },
            }
            catalog = {
                "schema_version": 1,
                "config": {"input_profile": "Default"},
                "builds": {
                    "title": "NA v2.28",
                    "serial": "SLOP-NA228",
                    "entries": {
                        "latest": {
                            "postfix": "Latest",
                        }
                    }
                },
                "sources": {
                    "NA2": {
                        "serial": "SLPS-25837",
                        "crc": "C0659AD1",
                    }
                },
            }
            manifest_path = root / "project-paths.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            (root / "settings").mkdir()
            (root / "settings/games.json").write_text(
                json.dumps(catalog),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "duplicates games.json"):
                load_project_paths(manifest_path)


if __name__ == "__main__":
    unittest.main()
