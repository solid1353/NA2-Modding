from __future__ import annotations

import binascii
import shutil
import struct
import subprocess
import tempfile
import unittest
import zlib
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[2]
COMPARATOR = (
    REPOSITORY
    / "scripts"
    / "research"
    / "localization"
    / "compare_font_capture_sets.ps1"
)


def write_rgb_png(path: Path, color: tuple[int, int, int]) -> None:
    def chunk(kind: bytes, data: bytes) -> bytes:
        checksum = binascii.crc32(kind + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", checksum)

    header = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    pixels = zlib.compress(b"\x00" + bytes(color))
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", pixels)
        + chunk(b"IEND", b"")
    )


def read_png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    return struct.unpack(">II", data[16:24])


class ComparisonGridTests(unittest.TestCase):
    def test_writes_matching_pair_blend_and_diff_grid_pages(self) -> None:
        powershell = shutil.which("pwsh")
        self.assertIsNotNone(powershell)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            reference = root / "reference"
            current = root / "current"
            output = root / "output"
            reference.mkdir()
            current.mkdir()
            stale_grid = output / "grids" / "page_01.png"
            stale_grid.parent.mkdir(parents=True)
            stale_grid.write_bytes(b"stale")

            for slot in range(1, 6):
                write_rgb_png(reference / f"{slot:03d}.png", (slot, 0, 0))
                write_rgb_png(current / f"{slot:03d}.png", (slot, 1, 0))

            subprocess.run(
                [
                    powershell,
                    "-NoProfile",
                    "-File",
                    str(COMPARATOR),
                    "-ReferenceDirectory",
                    str(reference),
                    "-CurrentDirectory",
                    str(current),
                    "-OutputDirectory",
                    str(output),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertEqual(
                sorted(path.name for path in (output / "grids").glob("*.png")),
                [
                    "page_01_c_pair.png",
                    "page_01_d_blend.png",
                    "page_01_e_diff.png",
                    "page_02_c_pair.png",
                    "page_02_d_blend.png",
                    "page_02_e_diff.png",
                ],
            )
            self.assertEqual(
                read_png_size(output / "grids" / "page_02_c_pair.png")[0],
                2,
            )
            self.assertEqual(
                read_png_size(output / "grids" / "page_02_d_blend.png")[0],
                1,
            )
            self.assertEqual(
                read_png_size(output / "grids" / "page_02_e_diff.png")[0],
                1,
            )


if __name__ == "__main__":
    unittest.main()
