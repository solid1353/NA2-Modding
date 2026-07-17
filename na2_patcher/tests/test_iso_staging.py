from __future__ import annotations

import sys
import tempfile
import unittest
from types import SimpleNamespace
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[2]
SCRIPTS = REPOSITORY / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from build_na2_profile import building_iso_path, payload_size_changes, staged_output_iso


class IsoStagingTests(unittest.TestCase):
    def test_failure_removes_temporary_iso_and_preserves_current(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.iso"
            output = root / "build" / "Current.iso"
            source.write_bytes(b"new source")
            output.parent.mkdir()
            output.write_bytes(b"known good")

            with self.assertRaisesRegex(RuntimeError, "synthetic failure"):
                with staged_output_iso(source, output) as temporary:
                    self.assertEqual(temporary, output.parent / "Current.iso.building")
                    self.assertEqual(temporary.read_bytes(), b"new source")
                    self.assertEqual(output.read_bytes(), b"known good")
                    raise RuntimeError("synthetic failure")

            self.assertEqual(output.read_bytes(), b"known good")
            self.assertFalse(building_iso_path(output).exists())

    def test_success_leaves_verified_candidate_for_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.iso"
            output = root / "build" / "Current.iso"
            source.write_bytes(b"new source")
            output.parent.mkdir()
            output.write_bytes(b"known good")

            with staged_output_iso(source, output) as temporary:
                temporary.write_bytes(b"verified build")
                self.assertEqual(output.read_bytes(), b"known good")

            self.assertEqual(output.read_bytes(), b"known good")
            self.assertEqual(building_iso_path(output).read_bytes(), b"verified build")

    def test_payload_size_changes_reports_only_changed_files(self) -> None:
        source = SimpleNamespace(
            by_path={
                "SAME.BIN": SimpleNamespace(size=4),
                "GROWN.BIN": SimpleNamespace(size=4),
            }
        )
        changes = payload_size_changes(
            source,
            {
                "SAME.BIN": bytearray(b"same"),
                "GROWN.BIN": bytearray(b"larger"),
            },
        )
        self.assertEqual(changes, [("GROWN.BIN", 4, 6)])


if __name__ == "__main__":
    unittest.main()
