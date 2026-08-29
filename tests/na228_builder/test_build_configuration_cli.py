from __future__ import annotations

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from na228_builder.scripts import build_configuration


class BuildConfigurationCliTests(unittest.TestCase):
    def test_texture_summary_reports_cache_reuse(self) -> None:
        plan = build_configuration.texture_patcher_module.TexturePatchPlan(
            package=SimpleNamespace(),
            containers=(
                SimpleNamespace(mapping_ids=("a",), cache_reused=True),
                SimpleNamespace(mapping_ids=("b", "c"), cache_reused=False),
            ),
            target_header=b"",
        )
        module = build_configuration.ModuleInvocation(
            module_id="localization.texture_patcher",
            order=5,
            module="texture_patcher",
            input_path=Path("texture_patcher"),
            input_sha256="A" * 64,
            feature_id="localization",
        )
        output = io.StringIO()
        with redirect_stdout(output):
            build_configuration.print_configuration_summary(
                SimpleNamespace(configuration_id="test"),
                [{"module": module, "texture_patch_plan": plan, "paths": []}],
                None,
            )
        self.assertIn(
            "texture cache 1 reused/1 derived",
            output.getvalue(),
        )

    def test_compose_only_skips_output_staging_and_configuration_logs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory).resolve()
            source_iso = workspace / "source.iso"
            source_iso.write_bytes(b"source")
            configuration_path = workspace / "configurations" / "default.json"
            configuration = SimpleNamespace(
                configuration_id="default", features=(), modules=()
            )
            plan = SimpleNamespace(
                replacements=(object(), object()),
                insertions=(object(),),
                renames=(object(),),
            )
            composed = build_configuration.ConfigurationCompositionResult(
                results=(),
                payload_result=None,
                composition=SimpleNamespace(
                    plan=plan,
                    identity_edits=({"target": "SYSTEM.CNF"},),
                ),
                insertion_owners={},
            )
            arguments = [
                "build_configuration",
                "--source",
                str(source_iso),
                "--configuration",
                str(configuration_path),
                "--compose-only",
            ]

            output = io.StringIO()
            with (
                patch.object(sys, "argv", arguments),
                patch.object(
                    build_configuration,
                    "PATHS",
                    new=SimpleNamespace(
                        repository=workspace,
                        path=lambda root, *children: workspace.joinpath(
                            root, *children
                        ),
                    ),
                ),
                patch.object(
                    build_configuration,
                    "load_configuration",
                    return_value=configuration,
                ),
                patch.object(
                    build_configuration,
                    "compose_configuration_candidate",
                    return_value=composed,
                ) as compose,
                patch.object(
                    build_configuration, "build_configuration_candidate"
                ) as build,
                redirect_stdout(output),
            ):
                self.assertEqual(build_configuration.main(), 0)

            compose.assert_called_once_with(
                source_iso=source_iso,
                configuration=configuration,
            )
            build.assert_not_called()
            self.assertIn("identity (1 edits)", output.getvalue())
            self.assertIn(
                "Validated composition: 2 replacements, 1 insertions, "
                "1 renames; no ISO staged.",
                output.getvalue(),
            )

    def test_normal_cli_logs_requested_output_not_staging_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory).resolve()
            source_iso = workspace / "source.iso"
            source_iso.write_bytes(b"source")
            output_iso = workspace / "build" / "NA2.28 - Latest.iso"
            configuration_path = workspace / "configurations" / "default.json"
            configuration_log_directory = workspace / "logs" / "configuration"
            configuration = SimpleNamespace(
                configuration_id="default", features=(), modules=()
            )
            payload_build = build_configuration.ResidentPayloadBuild(
                output_path="PRG/228.BIN",
                payload=b"payload",
                load_base=0,
                entrypoint=0,
                memory_end=7,
                used_end=7,
                symbols={},
                map_rows=(),
                summary={},
            )
            result = build_configuration.ConfigurationBuildResult(
                (),
                {"build": payload_build, "paths": ["PRG/228.BIN"]},
                ({"target": "SYSTEM.CNF"},),
                output_iso,
            )
            arguments = [
                "build_configuration",
                "--source",
                str(source_iso),
                "--output",
                str(output_iso),
                "--configuration",
                str(configuration_path),
                "--configuration-log-directory",
                "logs/configuration",
            ]

            output = io.StringIO()
            with (
                patch.object(sys, "argv", arguments),
                patch.object(
                    build_configuration,
                    "PATHS",
                    new=SimpleNamespace(
                        repository=workspace,
                        path=lambda root, *children: workspace.joinpath(
                            root, *children
                        ),
                    ),
                ),
                patch.object(
                    build_configuration,
                    "load_configuration",
                    return_value=configuration,
                ),
                patch.object(
                    build_configuration.binary_patcher_module,
                    "command_relative_path",
                    return_value=configuration_log_directory,
                ),
                patch.object(
                    build_configuration,
                    "build_configuration_candidate",
                    return_value=result,
                ) as compose,
                redirect_stdout(output),
            ):
                self.assertEqual(build_configuration.main(), 0)

            kwargs = compose.call_args.kwargs
            self.assertEqual(kwargs["output_iso"], output_iso)
            self.assertEqual(
                kwargs["configuration_log_directory"],
                configuration_log_directory,
            )
            self.assertFalse(kwargs["best_effort_metadata"])
            self.assertIn("payload_builder (0 symbols, 7 bytes)", output.getvalue())
            self.assertIn("identity (1 edits)", output.getvalue())
            self.assertIn(
                "Verified ISO candidate: NA2.28 - Latest.iso",
                output.getvalue(),
            )

    def test_best_effort_metadata_keeps_verified_candidate_on_log_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory).resolve()
            source_iso = workspace / "source.iso"
            source_iso.write_bytes(b"source")
            output_iso = workspace / "build" / "Latest.iso"
            log_directory = workspace / "logs" / "configuration"
            configuration = SimpleNamespace(identity=SimpleNamespace())
            composed = build_configuration.ConfigurationCompositionResult(
                results=(),
                payload_result=None,
                composition=SimpleNamespace(plan=object(), identity_edits=()),
                insertion_owners={},
            )

            def assemble(*_args: object) -> SimpleNamespace:
                output_iso.parent.mkdir(parents=True, exist_ok=True)
                output_iso.write_bytes(b"verified")
                return SimpleNamespace(
                    insertions=(), iso9660_renames=(), udf_renames=()
                )

            errors = io.StringIO()
            with (
                patch.object(
                    build_configuration,
                    "compose_configuration_candidate",
                    return_value=composed,
                ),
                patch.object(
                    build_configuration, "assemble_image", side_effect=assemble
                ),
                patch.object(
                    build_configuration,
                    "write_configuration_log",
                    side_effect=OSError("metadata unavailable"),
                ),
                redirect_stderr(errors),
            ):
                result = build_configuration.build_configuration_candidate(
                    source_iso=source_iso,
                    output_iso=output_iso,
                    configuration=configuration,
                    workspace=workspace,
                    configuration_log_directory=log_directory,
                    best_effort_metadata=True,
                    texture_cache_root=workspace / "texture-cache",
                )

            self.assertEqual(result.output_iso, output_iso)
            self.assertEqual(output_iso.read_bytes(), b"verified")
            self.assertIn(
                "WARNING: Configuration build record was not written: metadata unavailable",
                errors.getvalue(),
            )

    def test_default_metadata_failure_discards_staging(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory).resolve()
            source_iso = workspace / "source.iso"
            source_iso.write_bytes(b"source")
            output_iso = workspace / "build" / "Latest.iso"
            configuration = SimpleNamespace(identity=SimpleNamespace())
            composed = build_configuration.ConfigurationCompositionResult(
                results=(),
                payload_result=None,
                composition=SimpleNamespace(plan=object(), identity_edits=()),
                insertion_owners={},
            )

            def assemble(*_args: object) -> SimpleNamespace:
                output_iso.parent.mkdir(parents=True, exist_ok=True)
                output_iso.write_bytes(b"verified")
                return SimpleNamespace(
                    insertions=(), iso9660_renames=(), udf_renames=()
                )

            with (
                patch.object(
                    build_configuration,
                    "compose_configuration_candidate",
                    return_value=composed,
                ),
                patch.object(
                    build_configuration, "assemble_image", side_effect=assemble
                ),
                patch.object(
                    build_configuration,
                    "write_configuration_log",
                    side_effect=OSError("metadata unavailable"),
                ),
                self.assertRaisesRegex(OSError, "metadata unavailable"),
            ):
                build_configuration.build_configuration_candidate(
                    source_iso=source_iso,
                    output_iso=output_iso,
                    configuration=configuration,
                    workspace=workspace,
                    configuration_log_directory=workspace / "logs" / "configuration",
                    texture_cache_root=workspace / "texture-cache",
                )

            self.assertFalse(output_iso.exists())


if __name__ == "__main__":
    unittest.main()
