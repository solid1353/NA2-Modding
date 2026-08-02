#!/usr/bin/env python3
"""Create exact-scale Reference | Approved | Pending review grids."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


HEADER = 32


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", required=True, type=Path)
    parser.add_argument("--approved", required=True, type=Path)
    parser.add_argument("--pending", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def index_pngs(directory: Path) -> dict[int, Path]:
    result: dict[int, Path] = {}
    for path in directory.glob("*.png"):
        digits = "".join(reversed(list(_take_digits(reversed(path.stem)))))
        if not digits:
            raise ValueError(f"PNG name has no numeric suffix: {path.name}")
        result[int(digits)] = path
    return result


def _take_digits(characters):
    for character in characters:
        if not character.isdigit():
            break
        yield character


def open_rgb(path: Path) -> Image.Image:
    with Image.open(path) as image:
        return image.convert("RGB")


def main() -> int:
    args = parse_args()
    sets = {
        "Reference": index_pngs(args.reference),
        "Approved": index_pngs(args.approved),
        "Pending": index_pngs(args.pending),
    }
    with args.manifest.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    args.output.mkdir(parents=True, exist_ok=True)
    cells: list[Image.Image] = []
    for row in rows:
        slot = int(row["slot"])
        images = [open_rgb(sets[label][slot]) for label in sets]
        if len({image.size for image in images}) != 1:
            raise ValueError(f"Slot {slot:04d} has mismatched image sizes")
        if images[0].tobytes() == images[1].tobytes() == images[2].tobytes():
            continue
        width, height = images[0].size
        review = Image.new("RGB", (width * 3, height + HEADER), (12, 12, 12))
        draw = ImageDraw.Draw(review)
        font = ImageFont.load_default()
        for index, (label, image) in enumerate(zip(sets, images)):
            x = index * width
            review.paste(image, (x, HEADER))
            draw.text((x + 8, 10), f"{label} {slot:04d}", font=font, fill="white")
            if index:
                draw.line((x, 0, x, review.height), fill="white")
        review.save(args.output / f"{slot:04d}.png")
        cells.append(review)

    per_page = 4
    columns = 2
    for page, start in enumerate(range(0, len(cells), per_page), 1):
        page_cells = cells[start : start + per_page]
        width = max(cell.width for cell in page_cells)
        height = max(cell.height for cell in page_cells)
        rows_count = (len(page_cells) + columns - 1) // columns
        grid = Image.new("RGB", (width * columns, height * rows_count), (8, 8, 8))
        for index, cell in enumerate(page_cells):
            grid.paste(cell, ((index % columns) * width, (index // columns) * height))
        grid.save(args.output / f"page_{page:02d}.png")
    print(f"Created {len(cells)} three-way review images in {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
