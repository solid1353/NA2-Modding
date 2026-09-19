from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from na228_builder.infrastructure.orchestration import release_runtime


class ReleaseRuntimeTests(unittest.TestCase):
    def test_packaged_workspace_contains_release_inputs(self) -> None:
        workspace = release_runtime.packaged_workspace()

        self.assertTrue((workspace / "game.json").is_file())
        self.assertTrue(
            (workspace / "na228_builder" / "release_manifest.json").is_file()
        )

    def test_required_images_are_na2_only(self) -> None:
        configuration = SimpleNamespace(modules=(SimpleNamespace(),))
        self.assertEqual(
            ("na2",),
            release_runtime.required_release_image_ids(configuration),
        )

    def test_packaged_release_requires_precompiled_assembly_object(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            (workspace / "paths.json").write_text(
                '{"roots":{"builder":"na228_builder"},'
                '"files":{"project_settings":"game.json"}}',
                encoding="utf-8",
            )
            assembly = workspace / "na228_builder" / "patches" / "feature" / "runtime.S"
            assembly.parent.mkdir(parents=True)
            assembly.write_text("nop\n", encoding="ascii")
            manifest = SimpleNamespace(configuration_name="release.jsonc")
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
