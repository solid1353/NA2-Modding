from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from na228_builder.image_assembler.assembler import _write_exact, output_image_candidate


class PartialWriter:
    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.data = bytearray()

    def write(self, data: memoryview) -> int:
        count = min(self.limit, len(data))
        self.data.extend(data[:count])
        return count


class IsoCandidateTests(unittest.TestCase):
    def test_exact_write_completes_partial_writes(self) -> None:
        writer = PartialWriter(3)

        _write_exact(writer, b"complete replacement")

        self.assertEqual(bytes(writer.data), b"complete replacement")

    def test_exact_write_rejects_stalled_writes(self) -> None:
        with self.assertRaisesRegex(OSError, "stopped after 0 of 11 bytes"):
            _write_exact(PartialWriter(0), b"replacement")

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
