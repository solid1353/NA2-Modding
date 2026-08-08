from __future__ import annotations

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from na228_builder.scripts import build_configuration


class BuildConfigurationCliTests(unittest.TestCase):
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
                    new=SimpleNamespace(repository=workspace),
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
                payload_shift=0,
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
            staged_iso = build_configuration.building_image_path(output_iso)
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
                staged_iso,
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
                    new=SimpleNamespace(repository=workspace),
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
            self.assertIn("payload_builder (0 symbols, 7 bytes)", output.getvalue())
            self.assertIn("identity (1 edits)", output.getvalue())
            self.assertIn(
                "Verified staged ISO: NA2.28 - Latest.iso.building",
                output.getvalue(),
            )


if __name__ == "__main__":
    unittest.main()
