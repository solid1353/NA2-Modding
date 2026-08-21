from __future__ import annotations

import binascii
import shutil
import struct
import subprocess
import tempfile
import unittest
import zlib
from pathlib import Path

from PIL import Image
from scripts.lib.paths import load_paths

REPOSITORY = Path(__file__).resolve().parents[3]
COMPARATOR = load_paths(REPOSITORY).path(
    "scripts", "research", "localization", "compare_font_capture_sets.ps1"
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


def read_png_pixel(path: Path, x: int, y: int) -> tuple[int, int, int]:
    with Image.open(path) as image:
        return image.convert("RGB").getpixel((x, y))


class ComparisonGridTests(unittest.TestCase):
    def test_emits_flat_generated_grid_comparison_families(self) -> None:
        powershell = shutil.which("pwsh")
        self.assertIsNotNone(powershell)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            grids = root / "screenshots"
            output = root / "output"
            grids.mkdir()
            write_rgb_png(
                grids / "002_naruto_base_a_reference.png",
                (1, 0, 0),
            )
            write_rgb_png(
                grids / "002_naruto_base_b_current.png",
                (1, 1, 0),
            )
            write_rgb_png(
                grids / "003_sakura_base_a_reference.png",
                (2, 0, 0),
            )
            write_rgb_png(
                grids / "003_sakura_base_b_current.png",
                (2, 0, 0),
            )
            write_rgb_png(
                grids / "004_kakashi_base_b_current.png",
                (3, 0, 0),
            )
            for directory in ("pairs", "blends", "diffs"):
                stale = output / directory / "stale.png"
                stale.parent.mkdir(parents=True, exist_ok=True)
                stale.write_bytes(b"stale")

            subprocess.run(
                [
                    powershell,
                    "-NoProfile",
                    "-File",
                    str(COMPARATOR),
                    "-PairedGridDirectory",
                    str(grids),
                    "-OutputDirectory",
                    str(output),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            for directory in ("pairs", "blends", "diffs"):
                self.assertEqual(
                    sorted(path.name for path in (output / directory).glob("*.png")),
                    ["002_naruto_base.png"],
                )
            self.assertEqual(
                read_png_size(output / "pairs" / "002_naruto_base.png"),
                (2, 1),
            )
            self.assertEqual(
                read_png_size(output / "blends" / "002_naruto_base.png"),
                (1, 1),
            )
            self.assertEqual(
                read_png_size(output / "diffs" / "002_naruto_base.png"),
                (1, 1),
            )

    def test_can_generate_one_independent_comparison_branch(self) -> None:
        powershell = shutil.which("pwsh")
        self.assertIsNotNone(powershell)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            reference = root / "reference"
            current = root / "current"
            output = root / "output"
            reference.mkdir()
            current.mkdir()
            write_rgb_png(reference / "001.png", (1, 0, 0))
            write_rgb_png(current / "001.png", (1, 1, 0))

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
                    "-Kind",
                    "Blend",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertTrue((output / "blends" / "page_01.png").is_file())
            self.assertEqual(
                read_png_size(output / "blends" / "page_01.png"),
                (3, 2),
            )
            self.assertFalse((output / "pairs").exists())
            self.assertFalse((output / "diffs").exists())

    def test_emits_fixed_grids_without_compacting_missing_slots(self) -> None:
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
            stale_screenshot_grid = output / "screenshots" / "page_99.png"
            stale_pair_grid = output / "pairs" / "page_99.png"
            stale_blend_grid = output / "blends" / "page_99.png"
            stale_diff_grid = output / "diffs" / "page_99.png"
            for stale in (
                stale_screenshot_grid,
                stale_pair_grid,
                stale_blend_grid,
                stale_diff_grid,
            ):
                stale.parent.mkdir(parents=True)
                stale.write_bytes(b"stale")

            for slot in (1, 3, 5):
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
                    str(output / "screenshots"),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertEqual(
                sorted(
                    path.name for path in (output / "screenshots").glob("*.png")
                ),
                [
                    "page_01_a_reference.png",
                    "page_01_b_current.png",
                ],
            )
            self.assertEqual(
                sorted(
                    path.name for path in (output / "pairs").glob("*.png")
                ),
                ["page_01.png"],
            )
            self.assertEqual(
                sorted(path.name for path in (output / "blends").glob("*.png")),
                ["page_01.png"],
            )
            self.assertEqual(
                sorted(path.name for path in (output / "diffs").glob("*.png")),
                ["page_01.png"],
            )
            self.assertEqual(
                read_png_size(output / "screenshots" / "page_01_a_reference.png"),
                (3, 2),
            )
            self.assertEqual(
                read_png_size(output / "pairs" / "page_01.png"),
                (4, 2),
            )
            self.assertEqual(
                read_png_size(output / "blends" / "page_01.png"),
                (3, 2),
            )
            self.assertEqual(
                read_png_size(output / "diffs" / "page_01.png"),
                (3, 2),
            )
            screenshot_grid = output / "screenshots" / "page_01_a_reference.png"
            self.assertEqual(read_png_pixel(screenshot_grid, 0, 0), (1, 0, 0))
            self.assertEqual(read_png_pixel(screenshot_grid, 1, 0), (0, 0, 0))
            self.assertEqual(read_png_pixel(screenshot_grid, 2, 0), (3, 0, 0))
            self.assertEqual(read_png_pixel(screenshot_grid, 0, 1), (0, 0, 0))
            self.assertEqual(read_png_pixel(screenshot_grid, 1, 1), (5, 0, 0))
            self.assertEqual(read_png_pixel(screenshot_grid, 2, 1), (0, 0, 0))
            pair_grid = output / "pairs" / "page_01.png"
            self.assertEqual(read_png_pixel(pair_grid, 0, 0), (1, 0, 0))
            self.assertEqual(read_png_pixel(pair_grid, 1, 0), (1, 1, 0))
            self.assertEqual(read_png_pixel(pair_grid, 2, 0), (3, 0, 0))
            self.assertEqual(read_png_pixel(pair_grid, 3, 0), (3, 1, 0))
            self.assertEqual(read_png_pixel(pair_grid, 0, 1), (5, 0, 0))
            self.assertEqual(read_png_pixel(pair_grid, 1, 1), (5, 1, 0))
            self.assertEqual(read_png_pixel(pair_grid, 2, 1), (8, 8, 8))


if __name__ == "__main__":
    unittest.main()
