from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.lib.paths import derive_game_paths, load_local_paths, load_paths


class ProjectPathTests(unittest.TestCase):
    def write_manifest(self, root: Path, files: dict[str, str] | None) -> Path:
        manifest = {
            "schema_version": 1,
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
                "schema_version": 1,
                "imports": {"workshop": "../missing/paths.json"},
                "roots": {"repository": ".", "build": "build"},
                "files": {"product_config": "product.json"},
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
                "schema_version": 1,
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
                "schema_version": 1,
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
            manifest_path = root / "paths.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            paths = load_paths(manifest_path)

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
                "schema_version": 1,
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
                "files": {
                    "game_catalog": "@repository/games.json",
                    "product_config": "@repository/product.json",
                },
            }
            source_catalog = {
                "schema_version": 1,
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
            product_config = {
                "schema_version": 1,
                "title": "Narutimate Accel v2.28",
                "serial": "SLOP-NA228",
                "builds": {
                    "latest": {
                        "aliases": ["l"],
                    },
                    "e2e_test_shifted": {},
                },
            }
            manifest_path = root / "paths.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            (root / "games.json").write_text(
                json.dumps(source_catalog), encoding="utf-8"
            )
            (root / "product.json").write_text(
                json.dumps(product_config), encoding="utf-8"
            )
            (root / "pcsx2/game_settings/SLOP-NA228.ini").write_text(
                "[MemoryCards]\nSlot1_Filename = NA v2.28.ps2\n",
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
                root.resolve() / "pcsx2/memory_cards/NA v2.28 - Latest.ps2",
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
                "schema_version": 1,
                "sources": source_catalog["sources"],
                "title": product_config["title"],
                "serial": product_config["serial"],
                "builds": product_config["builds"],
            }
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
                root.resolve()
                / "pcsx2/input_profiles/sources/overrides/games/NA2.ini",
            )
            self.assertEqual(
                paths.file("cheat_template"),
                root.resolve() / "pcsx2/cheats/SLOP-NA228.pnach",
            )
            self.assertEqual(
                paths.file("gamesettings_template"),
                root.resolve() / "pcsx2/game_settings/SLOP-NA228.ini",
            )

if __name__ == "__main__":
    unittest.main()
