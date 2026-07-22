from __future__ import annotations

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from na2_patcher import build_profile


class BuildProfileCliTests(unittest.TestCase):
    def test_normal_cli_logs_requested_output_not_staging_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory).resolve()
            source_iso = workspace / "source.iso"
            source_iso.write_bytes(b"source")
            output_iso = workspace / "build" / "NA2.28 - Current.iso"
            profile_directory = workspace / "profiles" / "current"
            profile_log_directory = workspace / "logs" / "profile"
            profile = SimpleNamespace(profile_id="current", features=(), modules=())
            staged_iso = build_profile.building_image_path(output_iso)
            payload_build = build_profile.ResidentPayloadBuild(
                output_path="PRG/228.BIN",
                payload=b"payload",
                load_base=0,
                entrypoint=0,
                memory_end=7,
                symbols={},
                map_rows=(),
                summary={},
            )
            result = build_profile.ProfileBuildResult(
                (),
                {"build": payload_build, "paths": ["PRG/228.BIN"]},
                ({"target": "SYSTEM.CNF"},),
                staged_iso,
            )
            arguments = [
                "build_profile",
                "--source",
                str(source_iso),
                "--output",
                str(output_iso),
                "--profile",
                str(profile_directory),
                "--profile-log-directory",
                "logs/profile",
            ]

            output = io.StringIO()
            with (
                patch.object(sys, "argv", arguments),
                patch.object(
                    build_profile,
                    "PROJECT_PATHS",
                    new=SimpleNamespace(repository=workspace),
                ),
                patch.object(build_profile, "load_profile", return_value=profile),
                patch.object(
                    build_profile.binary_patcher_module,
                    "command_relative_path",
                    return_value=profile_log_directory,
                ),
                patch.object(
                    build_profile,
                    "build_profile_candidate",
                    return_value=result,
                ) as compose,
                redirect_stdout(output),
            ):
                self.assertEqual(build_profile.main(), 0)

            kwargs = compose.call_args.kwargs
            self.assertEqual(kwargs["output_iso"], output_iso)
            self.assertEqual(kwargs["profile_log_directory"], profile_log_directory)
            self.assertIn("payload_builder (0 symbols, 7 bytes)", output.getvalue())
            self.assertIn("identity (1 edits)", output.getvalue())
            self.assertIn(
                "Verified staged ISO: NA2.28 - Current.iso.building",
                output.getvalue(),
            )


if __name__ == "__main__":
    unittest.main()
