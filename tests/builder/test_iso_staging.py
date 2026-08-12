from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from na228_builder.image_assembler.assembler import output_image_candidate


class IsoCandidateTests(unittest.TestCase):
    def test_failure_removes_unique_output_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.iso"
            output = root / "cache" / ".incoming" / "build-id.iso"
            source.write_bytes(b"new source")

            with self.assertRaisesRegex(RuntimeError, "synthetic failure"):
                with output_image_candidate(source, output) as candidate:
                    self.assertEqual(candidate, output)
                    self.assertEqual(candidate.read_bytes(), b"new source")
                    raise RuntimeError("synthetic failure")

            self.assertFalse(output.exists())

    def test_success_leaves_exact_candidate_for_registration(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.iso"
            output = root / "cache" / ".incoming" / "build-id.iso"
            source.write_bytes(b"new source")

            with output_image_candidate(source, output) as candidate:
                candidate.write_bytes(b"verified build")

            self.assertEqual(output.read_bytes(), b"verified build")

    def test_existing_candidate_is_never_replaced(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.iso"
            output = root / "candidate.iso"
            source.write_bytes(b"source")
            output.write_bytes(b"preserve")

            with self.assertRaises(FileExistsError):
                with output_image_candidate(source, output):
                    pass
            self.assertEqual(output.read_bytes(), b"preserve")


if __name__ == "__main__":
    unittest.main()
