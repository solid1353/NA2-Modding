from __future__ import annotations

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from na228_builder.infrastructure.orchestration import build_configuration


class BuildConfigurationCliTests(unittest.TestCase):
    def test_texture_summary_reports_external_pack_size(self) -> None:
        plan = build_configuration.texture_patcher_module.ExternalTexturePackPlan(
            containers=(SimpleNamespace(), SimpleNamespace()),
            payload=b"pack",
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
            "2 containers, 4 external bytes",
            output.getvalue(),
        )

    def test_normal_cli_builds_into_incoming_and_logs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory).resolve()
            source_iso = workspace / "source.iso"
            source_iso.write_bytes(b"source")
            output_iso = workspace / "build" / ".incoming" / "candidate.iso"
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
                "--build-id",
                "candidate",
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
            self.assertIn("payload_builder (0 symbols, 7 bytes)", output.getvalue())
            self.assertIn("identity (1 edits)", output.getvalue())
            self.assertIn(
                "Verified ISO candidate: candidate.iso",
                output.getvalue(),
            )


if __name__ == "__main__":
    unittest.main()
