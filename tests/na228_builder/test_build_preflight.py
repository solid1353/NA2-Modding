from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from na228_builder.scripts.build_preflight import (
    builder_tree_entry,
    collect_build_state,
    lookup_registry,
    record_locations,
    record_registry,
    state_fingerprint,
)
from na228_builder.modules.binary_patcher import engine as binary_patcher


DEPENDENCIES = {
    "python_implementation": "test-python",
    "python_version": "1.0",
    "zlib_compile_version": "1.0",
    "zlib_runtime_version": "1.0",
    "zopfli_version": "0.4.3",
}


class BuildPreflightTests(unittest.TestCase):
    def create_workspace(self, root: Path) -> dict[str, Path]:
        workspace = root / "repository"
        builder = workspace / "na228_builder"
        configuration = builder / "configurations" / "release.json"
        configuration.parent.mkdir(parents=True)
        scripts = builder / "scripts"
        scripts.mkdir()
        (scripts / "engine.py").write_text("ENGINE = 1\n", encoding="utf-8")
        (builder / "schema.tsv").write_text("schema\t1\n", encoding="utf-8")
        feature = builder / "localization"
        module = feature / "translation_importer"
        module.mkdir(parents=True)
        (module / "mappings.tsv").write_text("id\n", encoding="utf-8")
        texture = feature / "texture_patcher"
        texture.mkdir()
        for name in ("containers.tsv", "mappings.tsv", "strategies.tsv"):
            (texture / name).write_text("id\n", encoding="utf-8")
        catalog_root = builder / "catalog"
        catalog_root.mkdir(parents=True)
        targets = catalog_root / "targets.tsv"
        targets.write_text(
            "\t".join(binary_patcher.TARGET_FIELDS) + "\n",
            encoding="utf-8",
        )
        (catalog_root / "catalog.modcat").write_text(
            '''{
  features: {
    localization: {
      enabled: setting {
        description: "Localization.",
        patches: ["i__localization__enabled"],
      },
    },
  },
}
''',
            encoding="utf-8",
        )
        (catalog_root / "edits.json").write_text("{}\n", encoding="utf-8")
        (catalog_root / "string_patches.json").write_text(
            "{}\n", encoding="utf-8"
        )
        (catalog_root / "injections.json").write_text(
            json.dumps(
                {
                    "i__localization__enabled": {
                        "description": "Synthetic localization selector."
                    }
                }
            )
            + "\n",
            encoding="utf-8",
        )
        (configuration.parent / "base.json").write_text(
            json.dumps({"features": {"localization": {"enabled": True}}}),
            encoding="utf-8",
        )
        configuration.write_text(
            json.dumps({"overrides": {}}),
            encoding="utf-8",
        )
        source_roots = workspace / "source_roots"
        source_roots.mkdir(parents=True)
        (source_roots / "NA2.iso.files").mkdir()
        (source_roots / "NUN5.iso.files").mkdir()
        shared = workspace / "shared"
        for name in (
            "cheats",
            "game_settings",
            "input_profiles",
            "memory_cards",
        ):
            (shared / name).mkdir(parents=True)
        (workspace / "build").mkdir()
        (workspace / "paths.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "roots": {
                        "repository": ".",
                        "builder": "na228_builder",
                        "source": "source_roots",
                        "build": "build",
                        "pcsx2_files": "shared",
                        "pcsx2_cheats": "shared/cheats",
                        "pcsx2_game_settings": "shared/game_settings",
                        "pcsx2_input_profiles": "shared/input_profiles",
                        "pcsx2_memory_cards": "shared/memory_cards",
                    },
                    "files": {
                        "settings": "@repository/game.json",
                        "game_catalog": "@repository/games.json",
                    },
                }
            ),
            encoding="utf-8",
        )
        (workspace / "games.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "sources": {
                        "NA2": {"serial": "SLPS-25837", "crc": "C0659AD1"},
                        "NUN5": {"serial": "SLES-55605", "crc": "C071D4C1"},
                    },
                }
            ),
            encoding="utf-8",
        )
        (workspace / "game.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "title": "Test Product",
                    "serial": "TEST-00000",
                    "output_boot_path": "SLOP_NA2.28",
                    "launch_settings": {
                        "startup_fast_forward_frames": 321,
                        "practice": {"startup_fast_forward_frames": 654},
                    },
                    "builds": {"latest": {}},
                }
            ),
            encoding="utf-8",
        )
        na2_iso = root / "source" / "NA2.iso"
        nun5_iso = root / "source" / "NUN5.iso"
        na2_iso.parent.mkdir()
        na2_iso.write_bytes(b"clean na2")
        nun5_iso.write_bytes(b"clean nun5")
        latest_iso = workspace / "build" / "NA2.28 - Latest.iso"
        latest_iso.parent.mkdir(exist_ok=True)
        latest_iso.write_bytes(b"verified latest")
        return {
            "workspace": workspace,
            "builder": builder,
            "configuration": configuration,
            "na2_iso": na2_iso,
            "nun5_iso": nun5_iso,
            "latest_iso": latest_iso,
            "registry": workspace / "logs" / "na228" / "preflight" / "registry.json",
            "cache": workspace / "work" / "cache" / "isos",
        }

    def state(self, paths: dict[str, Path], **overrides: object) -> dict[str, object]:
        arguments: dict[str, object] = {
            "workspace": paths["workspace"],
            "na2_iso": paths["na2_iso"],
            "nun5_iso": paths["nun5_iso"],
            "configuration_path": paths["configuration"],
            "dependencies": DEPENDENCIES,
        }
        arguments.update(overrides)
        return collect_build_state(**arguments)  # type: ignore[arg-type]

    def check(self, paths: dict[str, Path]) -> dict[str, object]:
        return lookup_registry(
            workspace=paths["workspace"],
            registry_path=paths["registry"],
            cache_root=paths["cache"],
            state=self.state(paths),
        )

    def record(
        self,
        paths: dict[str, Path],
        expected_fingerprint: str,
    ) -> dict[str, object]:
        incoming = paths["cache"] / ".incoming" / "candidate.iso"
        incoming.parent.mkdir(parents=True, exist_ok=True)
        incoming.write_bytes(paths["latest_iso"].read_bytes())
        provenance = paths["workspace"] / "provenance"
        provenance.mkdir(exist_ok=True)
        (provenance / "configuration.tsv").write_text("test\n", encoding="utf-8")
        return record_registry(
            workspace=paths["workspace"],
            registry_path=paths["registry"],
            cache_root=paths["cache"],
            state=self.state(paths),
            expected_fingerprint=expected_fingerprint,
            image=incoming,
            provenance=provenance,
        )

    def test_fingerprint_is_deterministic_and_invalidates_every_declared_input(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = self.create_workspace(Path(directory))
            initial = state_fingerprint(self.state(paths))
            self.assertEqual(initial, state_fingerprint(self.state(paths)))

            self.assertNotEqual(
                initial,
                state_fingerprint(self.state(paths, payload_shift=32)),
            )
            (paths["builder"] / "scripts" / "engine.py").write_text(
                "ENGINE = 2\n", encoding="utf-8"
            )
            self.assertNotEqual(initial, state_fingerprint(self.state(paths)))
            (paths["builder"] / "scripts" / "engine.py").write_text(
                "ENGINE = 1\n", encoding="utf-8"
            )

            paths["na2_iso"].write_bytes(b"changed na2")
            self.assertNotEqual(initial, state_fingerprint(self.state(paths)))
            paths["na2_iso"].write_bytes(b"clean na2")

            paths["nun5_iso"].write_bytes(b"changed nun5")
            self.assertNotEqual(initial, state_fingerprint(self.state(paths)))
            paths["nun5_iso"].write_bytes(b"clean nun5")

            changed_dependencies = dict(DEPENDENCIES, zlib_runtime_version="2.0")
            self.assertNotEqual(
                initial,
                state_fingerprint(
                    self.state(paths, dependencies=changed_dependencies)
                ),
            )

    def test_builder_hash_excludes_non_composing_files_and_python_cache(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = self.create_workspace(Path(directory))
            initial = builder_tree_entry(paths["builder"])
            documentation = paths["builder"] / "README.md"
            documentation.write_text("documentation\n", encoding="utf-8")
            with_documentation = builder_tree_entry(paths["builder"])
            self.assertEqual(initial["sha256"], with_documentation["sha256"])

            (paths["builder"] / "scripts" / "release_runtime.py").write_text(
                "RELEASE_ONLY = True\n", encoding="utf-8"
            )
            self.assertEqual(
                with_documentation["sha256"],
                builder_tree_entry(paths["builder"])["sha256"],
            )

            (paths["builder"] / "configurations" / "unused.json").write_text(
                "{}\n", encoding="utf-8"
            )
            self.assertEqual(
                with_documentation["sha256"],
                builder_tree_entry(paths["builder"])["sha256"],
            )

            cache = paths["builder"] / "__pycache__"
            cache.mkdir()
            (cache / "engine.cpython-999.pyc").write_bytes(b"generated")
            self.assertEqual(
                with_documentation["sha256"],
                builder_tree_entry(paths["builder"])["sha256"],
            )

    def test_configuration_resources_invalidate_but_documentation_content_does_not(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = self.create_workspace(Path(directory))
            initial = state_fingerprint(self.state(paths))
            feature = paths["builder"] / "localization"

            documentation = paths["workspace"] / "docs" / "features" / "localization.md"
            documentation.parent.mkdir(parents=True)
            documentation.write_text(
                "# Updated documentation only\n", encoding="utf-8"
            )
            self.assertEqual(initial, state_fingerprint(self.state(paths)))

            base_configuration = paths["builder"] / "configurations" / "base.json"
            base_configuration.write_text(
                json.dumps(
                    {
                        "features": {"localization": {"enabled": False}},
                    }
                ),
                encoding="utf-8",
            )
            self.assertNotEqual(initial, state_fingerprint(self.state(paths)))
            base_configuration.write_text(
                json.dumps(
                    {
                        "features": {"localization": {"enabled": True}},
                    }
                ),
                encoding="utf-8",
            )

            (feature / "translation_importer" / "mappings.tsv").write_text(
                "id\nchanged\n", encoding="utf-8"
            )
            self.assertNotEqual(initial, state_fingerprint(self.state(paths)))

            (feature / "translation_importer" / "mappings.tsv").write_text(
                "id\n", encoding="utf-8"
            )
            targets = (
                paths["builder"]
                / "catalog"
                / "targets.tsv"
            )
            targets.write_text(
                targets.read_text(encoding="utf-8")
                + "boot\tna2\tdestination\tSLPS_258.37\t16\t"
                + "0" * 64
                + "\n",
                encoding="utf-8",
            )
            self.assertNotEqual(initial, state_fingerprint(self.state(paths)))

    def test_project_settings_invalidate_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = self.create_workspace(Path(directory))
            initial = state_fingerprint(self.state(paths))
            settings = paths["workspace"] / "game.json"
            document = json.loads(settings.read_text(encoding="utf-8"))
            document["title"] = "Changed Product"
            settings.write_text(json.dumps(document), encoding="utf-8")
            self.assertNotEqual(initial, state_fingerprint(self.state(paths)))

    def test_registry_hit_reuses_a_verified_physical_image(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = self.create_workspace(Path(directory))
            fingerprint = state_fingerprint(self.state(paths))
            self.assertEqual(self.check(paths)["reason"], "fingerprint-missing")
            written = self.record(paths, fingerprint)
            self.assertEqual(written["status"], "recorded")
            self.assertEqual(self.check(paths)["status"], "hit")

            cached = Path(str(written["image"]))
            cached.write_bytes(b"X" * cached.stat().st_size)
            self.assertEqual(self.check(paths)["reason"], "physical-image-missing")

            paths["builder"].joinpath("scripts", "engine.py").write_text(
                "ENGINE = 3\n", encoding="utf-8"
            )
            self.assertEqual(self.check(paths)["reason"], "fingerprint-missing")

    def test_missing_corrupt_and_tampered_registry_is_a_safe_miss(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = self.create_workspace(Path(directory))
            fingerprint = state_fingerprint(self.state(paths))
            self.record(paths, fingerprint)

            paths["registry"].write_text("not json\n", encoding="utf-8")
            self.assertEqual(self.check(paths)["reason"], "registry-invalid")

            paths["registry"].unlink()
            self.record(paths, fingerprint)
            registry = json.loads(paths["registry"].read_text(encoding="utf-8"))
            registry["entries"][fingerprint]["state"]["configuration"] = "tampered.json"
            paths["registry"].write_text(json.dumps(registry), encoding="utf-8")
            self.assertEqual(self.check(paths)["reason"], "fingerprint-missing")

            paths["registry"].unlink()
            self.assertEqual(self.check(paths)["reason"], "fingerprint-missing")

    def test_version_one_registry_migrates_without_losing_physical_locations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = self.create_workspace(Path(directory))
            state = self.state(paths)
            fingerprint = state_fingerprint(state)
            recorded = self.record(paths, fingerprint)
            registry = json.loads(paths["registry"].read_text(encoding="utf-8"))
            sha256 = registry["entries"][fingerprint]["sha256"]
            size = registry["images"][sha256]["size"]
            Path(str(recorded["image"])).unlink()
            legacy = {
                "schema_version": 1,
                "entries": {
                    fingerprint: {
                        "state": state,
                        "size": size,
                        "sha256": sha256,
                        "verified_utc": registry["entries"][fingerprint][
                            "verified_utc"
                        ],
                        "locations": ["build/NA2.28 - Latest.iso"],
                    }
                },
                "pending": {},
            }
            paths["registry"].write_text(json.dumps(legacy), encoding="utf-8")

            migrated_hit = self.check(paths)
            self.assertEqual(migrated_hit["status"], "hit")
            self.assertEqual(
                Path(str(migrated_hit["image"])), paths["latest_iso"].resolve()
            )
            record_locations(
                workspace=paths["workspace"],
                registry_path=paths["registry"],
                cache_root=paths["cache"],
                fingerprint=fingerprint,
                locations=[paths["latest_iso"]],
            )
            migrated = json.loads(paths["registry"].read_text(encoding="utf-8"))
            self.assertEqual(migrated["schema_version"], 2)
            self.assertEqual(
                migrated["images"][sha256]["locations"],
                ["build/NA2.28 - Latest.iso"],
            )

    def test_registry_is_not_written_if_inputs_change_during_build(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = self.create_workspace(Path(directory))
            fingerprint = state_fingerprint(self.state(paths))
            paths["builder"].joinpath("scripts", "engine.py").write_text(
                "ENGINE = 4\n", encoding="utf-8"
            )
            result = self.record(paths, fingerprint)
            self.assertEqual(result["reason"], "inputs-changed-during-build")
            self.assertFalse(paths["registry"].exists())

    def test_registry_contains_only_portable_locations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = self.create_workspace(Path(directory))
            fingerprint = state_fingerprint(self.state(paths))
            self.record(paths, fingerprint)
            record_locations(
                workspace=paths["workspace"],
                registry_path=paths["registry"],
                cache_root=paths["cache"],
                fingerprint=fingerprint,
                locations=[paths["latest_iso"]],
            )
            text = paths["registry"].read_text(encoding="utf-8")
            self.assertNotIn(str(paths["workspace"]), text)
            self.assertIn('"configuration": "configurations/release.json"', text)
            self.assertIn('"locations": [', text)

            cached = paths["cache"] / f"{self.check(paths)['output_sha256']}.iso"
            self.assertTrue(cached.exists())
            record_locations(
                workspace=paths["workspace"],
                registry_path=paths["registry"],
                cache_root=paths["cache"],
                fingerprint=fingerprint,
                locations=[paths["latest_iso"]],
            )
            self.assertEqual(cached.read_bytes(), paths["latest_iso"].read_bytes())

    def test_identical_outputs_share_physical_locations_across_fingerprints(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = self.create_workspace(Path(directory))
            first_state = self.state(paths)
            first_fingerprint = state_fingerprint(first_state)
            recorded = self.record(paths, first_fingerprint)
            record_locations(
                workspace=paths["workspace"],
                registry_path=paths["registry"],
                cache_root=paths["cache"],
                fingerprint=first_fingerprint,
                locations=[paths["latest_iso"]],
            )

            second_state = self.state(
                paths,
                dependencies=dict(DEPENDENCIES, python_version="other-inputs"),
            )
            second_fingerprint = state_fingerprint(second_state)
            second_image = paths["cache"] / ".incoming" / "same-output.iso"
            second_image.parent.mkdir(parents=True, exist_ok=True)
            second_image.write_bytes(paths["latest_iso"].read_bytes())
            record_registry(
                workspace=paths["workspace"],
                registry_path=paths["registry"],
                cache_root=paths["cache"],
                state=second_state,
                expected_fingerprint=second_fingerprint,
                image=second_image,
                provenance=None,
            )
            Path(str(recorded["image"])).unlink()

            reused = lookup_registry(
                workspace=paths["workspace"],
                registry_path=paths["registry"],
                cache_root=paths["cache"],
                state=second_state,
            )
            self.assertEqual(reused["status"], "hit")
            self.assertEqual(Path(str(reused["image"])), paths["latest_iso"].resolve())
            registry = json.loads(paths["registry"].read_text(encoding="utf-8"))
            self.assertEqual(len(registry["entries"]), 2)
            self.assertEqual(len(registry["images"]), 1)

    def test_location_completion_tracks_latest_to_previous_rotation_by_image_hash(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = self.create_workspace(Path(directory))
            old_state = self.state(paths)
            old_fingerprint = state_fingerprint(old_state)
            old_record = self.record(paths, old_fingerprint)
            record_locations(
                workspace=paths["workspace"],
                registry_path=paths["registry"],
                cache_root=paths["cache"],
                fingerprint=old_fingerprint,
                locations=[paths["latest_iso"]],
            )
            Path(str(old_record["image"])).unlink()

            new_state = self.state(
                paths,
                dependencies=dict(DEPENDENCIES, python_version="new-inputs"),
            )
            new_fingerprint = state_fingerprint(new_state)
            incoming = paths["cache"] / ".incoming" / "new.iso"
            incoming.parent.mkdir(parents=True, exist_ok=True)
            incoming.write_bytes(b"new verified image")
            new_record = record_registry(
                workspace=paths["workspace"],
                registry_path=paths["registry"],
                cache_root=paths["cache"],
                state=new_state,
                expected_fingerprint=new_fingerprint,
                image=incoming,
                provenance=None,
            )

            previous_iso = paths["latest_iso"].with_name("NA2.28 - Previous.iso")
            paths["latest_iso"].replace(previous_iso)
            paths["latest_iso"].hardlink_to(Path(str(new_record["image"])))
            record_locations(
                workspace=paths["workspace"],
                registry_path=paths["registry"],
                cache_root=paths["cache"],
                fingerprint=new_fingerprint,
                locations=[paths["latest_iso"], previous_iso],
            )

            old_reuse = lookup_registry(
                workspace=paths["workspace"],
                registry_path=paths["registry"],
                cache_root=paths["cache"],
                state=old_state,
            )
            self.assertEqual(Path(str(old_reuse["image"])), previous_iso.resolve())
            registry = json.loads(paths["registry"].read_text(encoding="utf-8"))
            old_sha256 = registry["entries"][old_fingerprint]["sha256"]
            new_sha256 = registry["entries"][new_fingerprint]["sha256"]
            self.assertEqual(
                registry["images"][old_sha256]["locations"],
                ["build/NA2.28 - Previous.iso"],
            )
            self.assertIn(
                "build/NA2.28 - Latest.iso",
                registry["images"][new_sha256]["locations"],
            )

    def test_registry_bounds_entries_and_locations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = self.create_workspace(Path(directory))
            first_state = self.state(paths)
            first_fingerprint = state_fingerprint(first_state)
            self.record(paths, first_fingerprint)
            for index in range(20):
                state = self.state(
                    paths,
                    dependencies=dict(
                        DEPENDENCIES,
                        python_version=f"1.{index + 1}",
                    ),
                )
                fingerprint = state_fingerprint(state)
                image = paths["cache"] / ".incoming" / f"bounded-{index}.iso"
                image.parent.mkdir(parents=True, exist_ok=True)
                if index == 19:
                    image.write_bytes(b"verified latest")
                else:
                    image.write_bytes(f"bounded-{index:02d}".encode("ascii"))
                record_registry(
                    workspace=paths["workspace"],
                    registry_path=paths["registry"],
                    cache_root=paths["cache"],
                    state=state,
                    expected_fingerprint=fingerprint,
                    image=image,
                    provenance=None,
                )

            registry = json.loads(paths["registry"].read_text(encoding="utf-8"))
            self.assertEqual(len(registry["entries"]), 20)
            self.assertNotIn(first_fingerprint, registry["entries"])

            newest_fingerprint = fingerprint
            for index in range(21):
                location = paths["workspace"] / "build" / f"copy-{index}.iso"
                location.write_bytes(b"verified latest")
                record_locations(
                    workspace=paths["workspace"],
                    registry_path=paths["registry"],
                    cache_root=paths["cache"],
                    fingerprint=newest_fingerprint,
                    locations=[location],
                )

            registry = json.loads(paths["registry"].read_text(encoding="utf-8"))
            newest_sha256 = registry["entries"][newest_fingerprint]["sha256"]
            locations = registry["images"][newest_sha256]["locations"]
            self.assertEqual(len(locations), 20)
            self.assertNotIn("build/copy-0.iso", locations)

if __name__ == "__main__":
    unittest.main()
