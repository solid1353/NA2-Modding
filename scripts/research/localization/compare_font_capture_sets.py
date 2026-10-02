#!/usr/bin/env python3
"""Build paged screenshot grids and paired-grid reference/current comparisons."""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

from PIL import Image, ImageChops, ImageEnhance, ImageOps


SCREENSHOT_NAME = re.compile(r"^(\d+)_(a_reference|b_current)\.png$")
PAIRED_GRID_NAME = re.compile(
    r"^(?P<case>.+)_(?P<tier>a_reference|b_current)\.png$"
)
GRID_COLUMNS = 3
GRID_ROWS = 2
GRID_ITEMS_PER_PAGE = GRID_COLUMNS * GRID_ROWS
GRID_BACKGROUND = (0, 0, 0)
COMPARISON_DIRECTORIES = {"pair": "pairs", "blend": "blends", "diff": "diffs"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--screenshots", type=Path)
    inputs.add_argument("--paired-grids", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def open_rgb(path: Path) -> Image.Image:
    with Image.open(path) as image:
        return image.convert("RGB")


def make_pair(reference: Image.Image, current: Image.Image) -> Image.Image:
    pair = Image.new(
        "RGB",
        (reference.width + current.width, reference.height),
        (0, 0, 0),
    )
    pair.paste(reference, (0, 0))
    pair.paste(current, (reference.width, 0))
    return pair


def make_diff(raw_difference: Image.Image) -> Image.Image:
    return ImageEnhance.Contrast(ImageOps.autocontrast(raw_difference)).enhance(2.0)


def write_fixed_grid_pages(
    items: list[tuple[int, Image.Image]],
    output: Path,
    filename_suffix: str,
) -> None:
    ordered = sorted(items, key=lambda item: item[0])
    slots = [slot for slot, _ in ordered]
    if slots[0] < 1:
        raise ValueError(f"Grid slots must be positive: {slots[0]}")
    if len(slots) != len(set(slots)):
        raise ValueError(f"Grid slots must be unique: {slots}")

    output.mkdir(parents=True, exist_ok=True)
    cell_width = max(image.width for _, image in ordered)
    cell_height = max(image.height for _, image in ordered)
    last_page = ((slots[-1] - 1) // GRID_ITEMS_PER_PAGE) + 1
    for page_index in range(1, last_page + 1):
        grid = Image.new(
            "RGB",
            (cell_width * GRID_COLUMNS, cell_height * GRID_ROWS),
            GRID_BACKGROUND,
        )
        for slot, image in ordered:
            if ((slot - 1) // GRID_ITEMS_PER_PAGE) + 1 != page_index:
                continue
            cell = (slot - 1) % GRID_ITEMS_PER_PAGE
            x = (cell % GRID_COLUMNS) * cell_width
            y = (cell // GRID_COLUMNS) * cell_height
            grid.paste(image, (x, y))
        grid.save(output / f"page_{page_index:02d}_{filename_suffix}.png")


def write_screenshot_grid_pages(screenshots: Path, output: Path) -> None:
    paths = sorted(screenshots.glob("*.png"))
    if not paths:
        raise ValueError(f"No PNG screenshots found in {screenshots}")
    groups: dict[str, list[tuple[int, Image.Image]]] = {
        "a_reference": [],
        "b_current": [],
    }
    for path in paths:
        match = SCREENSHOT_NAME.fullmatch(path.name)
        if match is None:
            raise ValueError(f"Invalid canonical screenshot name: {path}")
        groups[match.group(2)].append((int(match.group(1)), open_rgb(path)))
    if output.is_dir():
        for path in output.glob("page_*.png"):
            path.unlink()
    for suffix, items in groups.items():
        if items:
            write_fixed_grid_pages(items, output, suffix)


def write_paired_grid_comparisons(grids: Path, output: Path) -> None:
    if not grids.is_dir():
        raise FileNotFoundError(f"Paired grid directory does not exist: {grids}")

    cases: dict[str, dict[str, Path]] = {}
    for path in sorted(grids.glob("*.png")):
        match = PAIRED_GRID_NAME.fullmatch(path.name)
        if match is None:
            raise ValueError(f"Invalid paired grid name: {path}")
        tiers = cases.setdefault(match.group("case"), {})
        tier = match.group("tier")
        if tier in tiers:
            raise ValueError(f"Duplicate paired {tier} grid: {path}")
        tiers[tier] = path

    for directory_name in COMPARISON_DIRECTORIES.values():
        directory = output / directory_name
        if directory.exists():
            shutil.rmtree(directory)
        directory.mkdir(parents=True)

    compared = 0
    changed = 0
    for case, tiers in sorted(cases.items()):
        reference_path = tiers.get("a_reference")
        current_path = tiers.get("b_current")
        if reference_path is None or current_path is None:
            continue

        reference = open_rgb(reference_path)
        current = open_rgb(current_path)
        if reference.size != current.size:
            raise ValueError(
                f"Paired grid size mismatch for {case}: "
                f"{reference.size} vs {current.size}"
            )
        compared += 1
        raw_difference = ImageChops.difference(reference, current)
        if raw_difference.getbbox() is None:
            continue
        changed += 1

        for name in COMPARISON_DIRECTORIES:
            if name == "pair":
                image = make_pair(reference, current)
            elif name == "blend":
                image = Image.blend(reference, current, 0.5)
            else:
                image = make_diff(raw_difference)
            image.save(output / COMPARISON_DIRECTORIES[name] / f"{case}.png")

    print(
        f"Compared {compared} paired grids; "
        f"wrote {changed} changed comparison sets to {output}"
    )


def main() -> int:
    args = parse_args()
    if args.screenshots is not None:
        write_screenshot_grid_pages(args.screenshots, args.output)
        print(f"Screenshot grids written to {args.output}")
    else:
        write_paired_grid_comparisons(args.paired_grids, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
