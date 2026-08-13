from __future__ import annotations

import binascii
import shutil
import struct
import subprocess
import tempfile
import unittest
import zlib
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[3]
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
    def test_emits_every_individual_and_grid_comparison_type(self) -> None:
        powershell = shutil.which("pwsh")
        self.assertIsNotNone(powershell)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            reference = root / "reference"
            current = root / "current"
            screenshots = root / "screenshots"
            output = root / "output"
            reference.mkdir()
            current.mkdir()
            screenshots.mkdir()
            stale_screenshot_grid = output / "grid-screenshots" / "page_99.png"
            stale_pair_grid = output / "grid-pairs" / "page_99.png"
            stale_blend_grid = output / "grid-blends" / "page_99.png"
            stale_diff_grid = output / "grid-diffs" / "page_99.png"
            for stale in (
                stale_screenshot_grid,
                stale_pair_grid,
                stale_blend_grid,
                stale_diff_grid,
            ):
                stale.parent.mkdir(parents=True)
                stale.write_bytes(b"stale")

            for slot in range(1, 6):
                write_rgb_png(reference / f"{slot:03d}.png", (slot, 0, 0))
                write_rgb_png(current / f"{slot:03d}.png", (slot, 1, 0))
                write_rgb_png(
                    screenshots / f"{slot:03d}_a_reference.png",
                    (slot, 0, 0),
                )
                write_rgb_png(
                    screenshots / f"{slot:03d}_b_current.png",
                    (slot, 1, 0),
                )

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
            subprocess.run(
                [
                    powershell,
                    "-NoProfile",
                    "-File",
                    str(COMPARATOR),
                    "-ScreenshotDirectory",
                    str(screenshots),
                    "-OutputDirectory",
                    str(output / "grid-screenshots"),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertEqual(
                sorted(
                    path.name
                    for path in (output / "base-pairs").glob("*.png")
                ),
                [
                    "0001.png",
                    "0002.png",
                    "0003.png",
                    "0004.png",
                    "0005.png",
                ],
            )
            self.assertEqual(
                sorted(
                    path.name
                    for path in (output / "base-blends").glob("*.png")
                ),
                [
                    "0001.png",
                    "0002.png",
                    "0003.png",
                    "0004.png",
                    "0005.png",
                ],
            )
            self.assertEqual(
                sorted(
                    path.name
                    for path in (output / "base-diffs").glob("*.png")
                ),
                [
                    "0001.png",
                    "0002.png",
                    "0003.png",
                    "0004.png",
                    "0005.png",
                ],
            )
            self.assertEqual(
                sorted(
                    path.name
                    for path in (output / "grid-screenshots").glob("*.png")
                ),
                [
                    "page_01_a_reference.png",
                    "page_01_b_current.png",
                    "page_02_a_reference.png",
                    "page_02_b_current.png",
                ],
            )
            self.assertEqual(
                sorted(
                    path.name for path in (output / "grid-pairs").glob("*.png")
                ),
                ["page_01.png", "page_02.png"],
            )
            self.assertEqual(
                sorted(path.name for path in (output / "grid-blends").glob("*.png")),
                ["page_01.png", "page_02.png"],
            )
            self.assertEqual(
                sorted(path.name for path in (output / "grid-diffs").glob("*.png")),
                ["page_01.png", "page_02.png"],
            )
            self.assertEqual(
                read_png_size(
                    output / "grid-screenshots" / "page_02_a_reference.png"
                )[0],
                1,
            )
            self.assertEqual(
                read_png_size(output / "grid-pairs" / "page_02.png")[0],
                2,
            )
            self.assertEqual(
                read_png_size(output / "grid-blends" / "page_02.png")[0],
                1,
            )
            self.assertEqual(
                read_png_size(output / "grid-diffs" / "page_02.png")[0],
                1,
            )


if __name__ == "__main__":
    unittest.main()
