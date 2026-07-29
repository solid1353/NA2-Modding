from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from na228_builder.image_assembler.assembler import (
    building_image_path,
    staged_output_image,
)


class IsoStagingTests(unittest.TestCase):
    def test_failure_removes_temporary_iso_and_preserves_current(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.iso"
            output = root / "build" / "NA2.28 - Current.iso"
            source.write_bytes(b"new source")
            output.parent.mkdir()
            output.write_bytes(b"known good")

            with self.assertRaisesRegex(RuntimeError, "synthetic failure"):
                with staged_output_image(source, output) as temporary:
                    self.assertEqual(temporary, output.parent / "NA2.28 - Current.iso.building")
                    self.assertEqual(temporary.read_bytes(), b"new source")
                    self.assertEqual(output.read_bytes(), b"known good")
                    raise RuntimeError("synthetic failure")

            self.assertEqual(output.read_bytes(), b"known good")
            self.assertFalse(building_image_path(output).exists())

    def test_success_leaves_verified_candidate_for_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.iso"
            output = root / "build" / "NA2.28 - Current.iso"
            source.write_bytes(b"new source")
            output.parent.mkdir()
            output.write_bytes(b"known good")

            with staged_output_image(source, output) as temporary:
                temporary.write_bytes(b"verified build")
                self.assertEqual(output.read_bytes(), b"known good")

            self.assertEqual(output.read_bytes(), b"known good")
            self.assertEqual(building_image_path(output).read_bytes(), b"verified build")


if __name__ == "__main__":
    unittest.main()
