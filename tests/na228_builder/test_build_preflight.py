from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from na228_builder.scripts import build_preflight
from na228_builder.scripts.build_preflight import (
    builder_tree_entry,
    collect_build_state,
    lookup_registry,
    record_registry,
    resolve_registry,
    state_fingerprint,
)
from na228_builder.modules.binary_patcher import engine as binary_patcher
from scripts.lib.paths import load_local_paths


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
        workspace.mkdir()
        (workspace / "paths.json").write_text(
            json.dumps(
                {
                    "existence_deferred_roots": ["cache"],
                    "roots": {
                        "builder": "na228_builder",
                        "source": "source_roots",
                        "build": "build",
                        "cache": "@build/cache",
                        "logs": "logs",
                        "pcsx2_files": "shared",
                        "pcsx2_input_profiles": "@pcsx2_files/input_profiles",
                        "pcsx2_memory_cards": "@pcsx2_files/memory_cards",
                    },
                    "files": {
                        "project_settings": "game.json",
                        "source_catalog": "games.json",
                    },
                }
            ),
            encoding="utf-8",
        )
        project_paths = load_local_paths(workspace, allow_missing=True)
        project_paths.path("logs").mkdir()
        builder = project_paths.path("builder")
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
        source_roots = project_paths.path("source")
        source_roots.mkdir(parents=True)
        (source_roots / "NA2.iso.files").mkdir()
        (source_roots / "NUN5.iso.files").mkdir()
        shared = project_paths.path("pcsx2_files")
        for name in (
            "cheats",
            "game_settings",
            "input_profiles",
            "memory_cards",
        ):
            (shared / name).mkdir(parents=True)
        project_paths.path("build").mkdir()
        (workspace / "games.json").write_text(
            json.dumps(
                {
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
                    "title": "Test Product",
                    "serial": "TEST-00000",
                    "output_boot_path": "SLOP_NA2.28",
                    "launch_settings": {
                        "startup_fast_forward_frames": 321,
                        "practice": {"startup_fast_forward_frames": 654},
                    },
                    "configurations": {"release": "r"},
                }
            ),
            encoding="utf-8",
        )
        na2_iso = root / "source" / "NA2.iso"
        nun5_iso = root / "source" / "NUN5.iso"
        na2_iso.parent.mkdir()
        na2_iso.write_bytes(b"clean na2")
        nun5_iso.write_bytes(b"clean nun5")
        sample_iso = project_paths.path("build", "sample.iso")
        sample_iso.parent.mkdir(exist_ok=True)
        sample_iso.write_bytes(b"verified sample")
        return {
            "workspace": workspace,
            "builder": builder,
            "configuration": configuration,
            "na2_iso": na2_iso,
            "nun5_iso": nun5_iso,
            "sample_iso": sample_iso,
            "registry": project_paths.path(
                "logs", "na228", "preflight", "registry.json"
            ),
            "cache": project_paths.path("build"),
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
        incoming.write_bytes(paths["sample_iso"].read_bytes())
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

    def test_assembly_resource_selects_ee_toolchain_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = self.create_workspace(Path(directory))
            workspace = paths["workspace"]
            assembly = workspace / "src" / "runtime.S"
            assembly.parent.mkdir()
            assembly.write_text("nop\n", encoding="ascii")
            injections_path = paths["builder"] / "catalog" / "injections.json"
            injections = json.loads(injections_path.read_text(encoding="utf-8"))
            injections["i__localization__enabled"]["payload"] = {
                "runtime_asm": {
                    "kind": "asm",
                    "path": "src/runtime.S",
                    "namespace": "runtime.asm",
                    "imports": {},
                    "fragments": {
                        "runtime_code": {
                            "object": "runtime.asm.text",
                        }
                    },
                }
            }
            injections_path.write_text(
                json.dumps(injections, indent=2) + "\n", encoding="utf-8"
            )
            toolchain = {"label": "ee_toolchain", "sha256": "A" * 64}
            with mock.patch.object(
                build_preflight, "ee_toolchain_entry", return_value=toolchain
            ) as fingerprint_toolchain:
                state = self.state(paths)
            self.assertTrue(state["configuration_resources"]["uses_ee_compiler"])
            self.assertEqual(toolchain, state["ee_toolchain"])
            self.assertEqual(
                workspace.resolve(), fingerprint_toolchain.call_args.args[0].resolve()
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

    def test_registry_paths_are_portable_and_provenance_is_retained(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = self.create_workspace(Path(directory))
            fingerprint = state_fingerprint(self.state(paths))
            result = self.record(paths, fingerprint)

            text = paths["registry"].read_text(encoding="utf-8")
            self.assertNotIn(str(paths["workspace"]), text)
            self.assertIn('"configuration": "release"', text)
            self.assertIn('"path": "build/NA v2.28 - ', text)
            self.assertTrue(Path(str(result["provenance"])).is_dir())

    def test_identical_outputs_share_one_named_iso(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = self.create_workspace(Path(directory))
            first_state = self.state(paths)
            first_fingerprint = state_fingerprint(first_state)
            first = self.record(paths, first_fingerprint)

            second_state = self.state(
                paths,
                dependencies=dict(DEPENDENCIES, python_version="other-inputs"),
            )
            second_fingerprint = state_fingerprint(second_state)
            second_image = paths["cache"] / ".incoming" / "same-output.iso"
            second_image.parent.mkdir(parents=True, exist_ok=True)
            second_image.write_bytes(paths["sample_iso"].read_bytes())
            second = record_registry(
                workspace=paths["workspace"],
                registry_path=paths["registry"],
                cache_root=paths["cache"],
                state=second_state,
                expected_fingerprint=second_fingerprint,
                image=second_image,
                provenance=None,
            )

            self.assertEqual(second["image"], first["image"])
            self.assertFalse(second_image.exists())
            self.assertEqual(
                len(list(paths["cache"].glob("NA v2.28 - *.iso"))),
                1,
            )
            registry = json.loads(paths["registry"].read_text(encoding="utf-8"))
            self.assertEqual(len(registry["entries"]), 2)
            self.assertEqual(len(registry["images"]), 1)

    def test_resolve_returns_the_newest_configuration_build(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = self.create_workspace(Path(directory))
            first_state = self.state(paths)
            first = self.record(paths, state_fingerprint(first_state))
            second_state = dict(first_state, variant="newer")
            second_image = paths["cache"] / ".incoming" / "newer.iso"
            second_image.parent.mkdir(parents=True, exist_ok=True)
            second_image.write_bytes(b"newer output")
            second = record_registry(
                workspace=paths["workspace"],
                registry_path=paths["registry"],
                cache_root=paths["cache"],
                state=second_state,
                expected_fingerprint=state_fingerprint(second_state),
                image=second_image,
                provenance=None,
            )

            resolved = resolve_registry(
                workspace=paths["workspace"],
                registry_path=paths["registry"],
                cache_root=paths["cache"],
                configuration_id="release",
            )
            self.assertEqual(resolved["status"], "resolved")
            self.assertEqual(resolved["image"], second["image"])
            self.assertNotEqual(resolved["image"], first["image"])

    def test_registry_retains_at_most_ten_unique_images(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = self.create_workspace(Path(directory))
            first_image: Path | None = None
            for index in range(build_preflight.MAX_IMAGES + 1):
                state = dict(self.state(paths), variant=index)
                incoming = paths["cache"] / ".incoming" / f"image-{index}.iso"
                incoming.parent.mkdir(parents=True, exist_ok=True)
                incoming.write_bytes(f"image-{index}".encode("ascii"))
                result = record_registry(
                    workspace=paths["workspace"],
                    registry_path=paths["registry"],
                    cache_root=paths["cache"],
                    state=state,
                    expected_fingerprint=state_fingerprint(state),
                    image=incoming,
                    provenance=None,
                )
                if index == 0:
                    first_image = Path(str(result["image"]))

            registry = json.loads(paths["registry"].read_text(encoding="utf-8"))
            self.assertEqual(len(registry["entries"]), build_preflight.MAX_IMAGES)
            self.assertEqual(len(registry["images"]), build_preflight.MAX_IMAGES)
            self.assertEqual(
                len(list(paths["cache"].glob("NA v2.28 - *.iso"))),
                build_preflight.MAX_IMAGES,
            )
            self.assertIsNotNone(first_image)
            self.assertFalse(first_image.exists())

if __name__ == "__main__":
    unittest.main()
