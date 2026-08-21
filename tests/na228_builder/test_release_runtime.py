from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from na228_builder.scripts import release_runtime
from scripts.lib.paths import load_local_paths


class ReleaseRuntimeTests(unittest.TestCase):
    def test_application_cache_root_uses_configured_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / "workspace"
            application = root / "application"
            workspace.mkdir()
            application.mkdir()
            (workspace / "paths.json").write_text(
                '{"schema_version":1,"roots":{"repository":".",'
                '"build":"build","cache":"@build/cache"},'
                '"files":{"settings":"game.json"}}',
                encoding="utf-8",
            )
            configured = load_local_paths(workspace, allow_missing=True)
            expected = application / configured.path("cache").relative_to(
                configured.repository
            )

            with (
                mock.patch.object(
                    release_runtime, "packaged_workspace", return_value=workspace
                ),
                mock.patch.object(
                    release_runtime,
                    "application_directory",
                    return_value=application,
                ),
            ):
                self.assertEqual(expected, release_runtime.application_cache_root())

    def test_packaged_release_requires_precompiled_assembly_object(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            (workspace / "paths.json").write_text(
                '{"schema_version":1,"roots":{"repository":".",'
                '"builder":"na228_builder"},'
                '"files":{"settings":"game.json"}}',
                encoding="utf-8",
            )
            assembly = workspace / "src" / "runtime.S"
            assembly.parent.mkdir()
            assembly.write_text("nop\n", encoding="ascii")
            manifest = SimpleNamespace(configuration_name="release.json")
            configuration = SimpleNamespace(
                selection=SimpleNamespace(feature_ids=("feature",)),
                modules=(object(),),
            )
            patches = (
                mock.patch.object(
                    release_runtime, "load_release_manifest", return_value=manifest
                ),
                mock.patch.object(
                    release_runtime, "application_directory", return_value=workspace
                ),
                mock.patch.object(
                    release_runtime, "packaged_workspace", return_value=workspace
                ),
                mock.patch.object(
                    release_runtime,
                    "load_release_configuration",
                    return_value=(workspace, configuration),
                ),
                mock.patch.object(
                    release_runtime.catalog_module,
                    "referenced_files",
                    return_value=(assembly,),
                ),
            )
            with patches[0], patches[1], patches[2], patches[3], patches[4]:
                with self.assertRaisesRegex(
                    FileNotFoundError, "Packaged runtime object is missing"
                ):
                    release_runtime.validate_packaged_release()
                assembly.with_name("runtime.S.o").write_bytes(b"object")
                self.assertEqual(1, release_runtime.validate_packaged_release())


if __name__ == "__main__":
    unittest.main()
