#!/usr/bin/env python3
"""Build exact-scale paired, blended, difference, and paged grid evidence."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFont, ImageOps


SLOT_SUFFIX = re.compile(r"(\d+)$")
HEADER_HEIGHT = 32
LABEL_MARGIN = 8


@dataclass(frozen=True)
class CaptureRow:
    slot: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", required=True, type=Path)
    parser.add_argument("--current", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--reference-label", default="Reference")
    parser.add_argument("--current-label", default="Current")
    parser.add_argument("--slots")
    parser.add_argument("--grid-columns", type=int, default=2)
    parser.add_argument("--grid-items-per-page", type=int, default=4)
    args = parser.parse_args()
    if args.grid_columns < 1:
        parser.error("--grid-columns must be positive")
    if args.grid_items_per_page < 1:
        parser.error("--grid-items-per-page must be positive")
    return args


def numeric_slot(path: Path) -> int:
    match = SLOT_SUFFIX.search(path.stem)
    if match is None:
        raise ValueError(f"PNG name has no numeric suffix: {path.name}")
    return int(match.group(1))


def index_pngs(directory: Path) -> dict[int, Path]:
    if not directory.is_dir():
        raise FileNotFoundError(f"Screenshot directory does not exist: {directory}")
    result: dict[int, Path] = {}
    for path in sorted(directory.glob("*.png")):
        slot = numeric_slot(path)
        if slot in result:
            raise ValueError(
                f"Duplicate numeric slot {slot}: {result[slot].name}, {path.name}"
            )
        result[slot] = path
    if not result:
        raise ValueError(f"No PNG screenshots found in {directory}")
    return result


def pair_capture_slots(
    reference_slots: set[int],
    current_slots: set[int],
) -> list[CaptureRow]:
    if reference_slots != current_slots:
        missing = sorted(reference_slots - current_slots)
        extra = sorted(current_slots - reference_slots)
        raise ValueError(
            f"Capture slot mismatch; missing current={missing}, extra current={extra}"
        )
    return [CaptureRow(slot) for slot in sorted(reference_slots)]


def parse_slot_selection(specification: str | None, available: list[int]) -> list[int]:
    if specification is None:
        return available
    selected: set[int] = set()
    for token in specification.split(","):
        token = token.strip()
        if not token:
            continue
        if "-" in token:
            start_text, end_text = token.split("-", 1)
            start = int(start_text)
            end = int(end_text)
            if end < start:
                raise ValueError(f"Descending slot range is invalid: {token}")
            selected.update(range(start, end + 1))
        else:
            selected.add(int(token))
    missing = sorted(selected - set(available))
    if missing:
        raise ValueError(f"Selected slots are absent from capture sets: {missing}")
    if not selected:
        raise ValueError("Slot selection is empty")
    return sorted(selected)


def open_rgb(path: Path) -> Image.Image:
    with Image.open(path) as image:
        return image.convert("RGB")


def draw_header(image: Image.Image, left: str, right: str | None = None) -> None:
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    draw.rectangle((0, 0, image.width, HEADER_HEIGHT - 1), fill=(20, 20, 20))
    draw.text((LABEL_MARGIN, 10), left, font=font, fill=(255, 255, 255))
    if right is not None:
        midpoint = image.width // 2
        draw.line((midpoint, 0, midpoint, image.height), fill=(255, 255, 255), width=1)
        draw.text((midpoint + LABEL_MARGIN, 10), right, font=font, fill=(255, 255, 255))


def make_pair(
    reference: Image.Image,
    current: Image.Image,
    row: CaptureRow,
    reference_label: str,
    current_label: str,
) -> Image.Image:
    pair = Image.new(
        "RGB",
        (reference.width + current.width, HEADER_HEIGHT + reference.height),
        (0, 0, 0),
    )
    pair.paste(reference, (0, HEADER_HEIGHT))
    pair.paste(current, (reference.width, HEADER_HEIGHT))
    draw_header(
        pair,
        f"{reference_label} {row.slot:04d}",
        f"{current_label} {row.slot:04d}",
    )
    return pair


def make_blend(
    reference: Image.Image,
    current: Image.Image,
    row: CaptureRow,
    reference_label: str,
    current_label: str,
) -> Image.Image:
    blended = Image.blend(reference, current, 0.5)
    result = Image.new("RGB", (blended.width, HEADER_HEIGHT + blended.height), (0, 0, 0))
    result.paste(blended, (0, HEADER_HEIGHT))
    draw_header(
        result,
        (
            f"50% blend {reference_label} {row.slot:04d}/"
            f"{current_label} {row.slot:04d}"
        ),
    )
    return result


def make_diff(
    reference: Image.Image,
    current: Image.Image,
    row: CaptureRow,
    reference_label: str,
    current_label: str,
) -> Image.Image | None:
    raw = ImageChops.difference(reference, current)
    if raw.getbbox() is None:
        return None
    visible = ImageEnhance.Contrast(ImageOps.autocontrast(raw)).enhance(2.0)
    result = Image.new("RGB", (visible.width, HEADER_HEIGHT + visible.height), (0, 0, 0))
    result.paste(visible, (0, HEADER_HEIGHT))
    draw_header(
        result,
        (
            f"Amplified diff {reference_label} {row.slot:04d}/"
            f"{current_label} {row.slot:04d}"
        ),
    )
    return result


def write_grid_pages(
    items: list[tuple[CaptureRow, Image.Image]],
    output: Path,
    columns: int,
    items_per_page: int,
    suffix: str,
) -> None:
    output.mkdir(parents=True, exist_ok=True)
    for page_index, start in enumerate(
        range(0, len(items), items_per_page), start=1
    ):
        page_items = items[start : start + items_per_page]
        cell_width = max(image.width for _, image in page_items)
        cell_height = max(image.height for _, image in page_items)
        used_columns = min(columns, len(page_items))
        rows = (len(page_items) + columns - 1) // columns
        grid = Image.new(
            "RGB", (cell_width * used_columns, cell_height * rows), (8, 8, 8)
        )
        for item_index, (_, image) in enumerate(page_items):
            x = (item_index % columns) * cell_width
            y = (item_index // columns) * cell_height
            grid.paste(image, (x, y))
        grid.save(output / f"page_{page_index:02d}_{suffix}.png")


def clear_generated_grid_pages(output: Path) -> None:
    if not output.is_dir():
        return
    for path in output.glob("page_*.png"):
        path.unlink()


def main() -> int:
    args = parse_args()
    reference_paths = index_pngs(args.reference)
    current_paths = index_pngs(args.current)
    captures = pair_capture_slots(set(reference_paths), set(current_paths))
    slots = parse_slot_selection(args.slots, [row.slot for row in captures])
    captures = [row for row in captures if row.slot in set(slots)]
    args.output.mkdir(parents=True, exist_ok=True)
    pair_dir = args.output / "pairs"
    blend_dir = args.output / "blends"
    diff_dir = args.output / "diffs"

    grid_items: dict[str, list[tuple[CaptureRow, Image.Image]]] = {
        "c_pair": [],
        "d_blend": [],
        "e_diff": [],
    }
    expected_size: tuple[int, int] | None = None
    for row in captures:
        reference = open_rgb(reference_paths[row.slot])
        current = open_rgb(current_paths[row.slot])
        if reference.size != current.size:
            raise ValueError(
                f"Slot {row.slot:04d} size mismatch: {reference.size} vs {current.size}"
            )
        if expected_size is None:
            expected_size = reference.size
        elif reference.size != expected_size:
            raise ValueError(
                f"Slot {row.slot:04d} differs from suite size {expected_size}: {reference.size}"
            )

        diff = make_diff(
            reference,
            current,
            row,
            args.reference_label,
            args.current_label,
        )
        if diff is None:
            continue

        pair = make_pair(
            reference,
            current,
            row,
            args.reference_label,
            args.current_label,
        )
        blend = make_blend(
            reference,
            current,
            row,
            args.reference_label,
            args.current_label,
        )
        for directory in (pair_dir, blend_dir, diff_dir):
            directory.mkdir(parents=True, exist_ok=True)
        pair.save(pair_dir / f"{row.slot:04d}.png")
        blend.save(blend_dir / f"{row.slot:04d}.png")
        diff.save(diff_dir / f"{row.slot:04d}.png")
        grid_items["c_pair"].append((row, pair))
        grid_items["d_blend"].append((row, blend))
        grid_items["e_diff"].append((row, diff))

    if grid_items["c_pair"]:
        grid_root = args.output / "grids"
        clear_generated_grid_pages(grid_root)
        for suffix, items in grid_items.items():
            write_grid_pages(
                items,
                grid_root,
                args.grid_columns,
                args.grid_items_per_page,
                suffix,
            )
    print(
        f"Compared {len(captures)} exact-scale pairs; evidence written to {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
