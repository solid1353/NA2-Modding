#!/usr/bin/env python3
"""Build every individual and paged reference/current comparison view."""

from __future__ import annotations

import argparse
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageChops, ImageEnhance, ImageOps


SLOT_SUFFIX = re.compile(r"(\d+)$")
SCREENSHOT_NAME = re.compile(r"^(\d+)_(a_reference|b_current)\.png$")
PAIRED_GRID_NAMES = (
    re.compile(r"^(?P<case>.+)-(?P<tier>a-reference|b-current)\.png$"),
    re.compile(r"^(?P<case>page_\d+)_(?P<tier>a_reference|b_current)\.png$"),
)
GRID_COLUMNS = 3
GRID_ROWS = 2
GRID_ITEMS_PER_PAGE = GRID_COLUMNS * GRID_ROWS
GRID_BACKGROUND = (0, 0, 0)
PAIR_GRID_COLUMNS = 2
PAIR_GRID_ITEMS_PER_PAGE = 4
PAIR_GRID_BACKGROUND = (8, 8, 8)


@dataclass(frozen=True)
class CaptureRow:
    slot: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--current", type=Path)
    parser.add_argument("--screenshots", type=Path)
    parser.add_argument("--paired-grids", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--slots")
    parser.add_argument(
        "--kind",
        choices=("all", "pair", "blend", "diff"),
        default="all",
        help="generate all comparison variants or one independent variant",
    )
    args = parser.parse_args()
    grid_input_count = sum(
        value is not None for value in (args.screenshots, args.paired_grids)
    )
    if grid_input_count > 1:
        parser.error("--screenshots and --paired-grids cannot be combined")
    if grid_input_count == 1:
        if args.reference is not None or args.current is not None:
            parser.error(
                "grid inputs cannot be combined with --reference or --current"
            )
        if args.slots is not None:
            parser.error("--slots is not supported with grid inputs")
    elif args.reference is None or args.current is None:
        parser.error("--reference and --current are required for comparisons")
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


def make_pair(
    reference: Image.Image,
    current: Image.Image,
) -> Image.Image:
    pair = Image.new(
        "RGB",
        (reference.width + current.width, reference.height),
        (0, 0, 0),
    )
    pair.paste(reference, (0, 0))
    pair.paste(current, (reference.width, 0))
    return pair


def make_blend(
    reference: Image.Image,
    current: Image.Image,
) -> Image.Image:
    return Image.blend(reference, current, 0.5)


def make_diff(
    reference: Image.Image,
    current: Image.Image,
    raw: Image.Image | None = None,
) -> Image.Image | None:
    raw = raw if raw is not None else ImageChops.difference(reference, current)
    if raw.getbbox() is None:
        return None
    return ImageEnhance.Contrast(ImageOps.autocontrast(raw)).enhance(2.0)


def write_fixed_grid_pages(
    items: list[tuple[CaptureRow, Image.Image]],
    output: Path,
    filename_suffix: str | None = None,
) -> None:
    if not items:
        return
    ordered = sorted(items, key=lambda item: item[0].slot)
    slots = [row.slot for row, _ in ordered]
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
        for row, image in ordered:
            item_page = ((row.slot - 1) // GRID_ITEMS_PER_PAGE) + 1
            if item_page != page_index:
                continue
            cell = (row.slot - 1) % GRID_ITEMS_PER_PAGE
            x = (cell % GRID_COLUMNS) * cell_width
            y = (cell // GRID_COLUMNS) * cell_height
            grid.paste(image, (x, y))
        suffix = f"_{filename_suffix}" if filename_suffix else ""
        grid.save(output / f"page_{page_index:02d}{suffix}.png")


def write_pair_grid_pages(
    items: list[tuple[CaptureRow, Image.Image]],
    output: Path,
) -> None:
    output.mkdir(parents=True, exist_ok=True)
    for page_index, start in enumerate(
        range(0, len(items), PAIR_GRID_ITEMS_PER_PAGE), start=1
    ):
        page_items = items[start : start + PAIR_GRID_ITEMS_PER_PAGE]
        cell_width = max(image.width for _, image in page_items)
        cell_height = max(image.height for _, image in page_items)
        used_columns = min(PAIR_GRID_COLUMNS, len(page_items))
        rows = (len(page_items) + PAIR_GRID_COLUMNS - 1) // PAIR_GRID_COLUMNS
        grid = Image.new(
            "RGB",
            (cell_width * used_columns, cell_height * rows),
            PAIR_GRID_BACKGROUND,
        )
        for item_index, (_, image) in enumerate(page_items):
            x = (item_index % PAIR_GRID_COLUMNS) * cell_width
            y = (item_index // PAIR_GRID_COLUMNS) * cell_height
            grid.paste(image, (x, y))
        grid.save(output / f"page_{page_index:02d}.png")


def clear_generated_grid_pages(output: Path) -> None:
    if not output.is_dir():
        return
    for path in output.glob("page_*.png"):
        path.unlink()


def write_screenshot_grid_pages(
    screenshots: Path,
    output: Path,
) -> None:
    paths = sorted(screenshots.glob("*.png"))
    if not paths:
        raise ValueError(f"No PNG screenshots found in {screenshots}")
    groups: dict[str, list[tuple[CaptureRow, Image.Image]]] = {
        "a_reference": [],
        "b_current": [],
    }
    for path in paths:
        match = SCREENSHOT_NAME.fullmatch(path.name)
        if match is None:
            raise ValueError(f"Invalid canonical screenshot name: {path}")
        groups[match.group(2)].append(
            (CaptureRow(int(match.group(1))), open_rgb(path))
        )
    clear_generated_grid_pages(output)
    for suffix, items in groups.items():
        if items:
            write_fixed_grid_pages(
                items,
                output,
                filename_suffix=suffix,
            )


def parse_paired_grid_name(path: Path) -> tuple[str, str]:
    for pattern in PAIRED_GRID_NAMES:
        match = pattern.fullmatch(path.name)
        if match is not None:
            tier = match.group("tier").replace("_", "-")
            return match.group("case"), tier
    raise ValueError(f"Invalid paired grid name: {path}")


def write_paired_grid_comparisons(
    grids: Path,
    output: Path,
    kind: str,
) -> None:
    if not grids.is_dir():
        raise FileNotFoundError(f"Paired grid directory does not exist: {grids}")

    cases: dict[str, dict[str, Path]] = {}
    for path in sorted(grids.glob("*.png")):
        case, tier = parse_paired_grid_name(path)
        tiers = cases.setdefault(case, {})
        if tier in tiers:
            raise ValueError(f"Duplicate paired {tier} grid: {path}")
        tiers[tier] = path

    output_directories = {
        "pair": output / "pairs",
        "blend": output / "blends",
        "diff": output / "diffs",
    }
    kinds = ("pair", "blend", "diff") if kind == "all" else (kind,)
    for name, directory in output_directories.items():
        if name not in kinds:
            continue
        if directory.exists():
            shutil.rmtree(directory)
        directory.mkdir(parents=True, exist_ok=True)

    compared = 0
    changed = 0
    for case, tiers in sorted(cases.items()):
        reference_path = tiers.get("a-reference")
        current_path = tiers.get("b-current")
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

        images: dict[str, Image.Image | None] = {}
        if "pair" in kinds:
            images["pair"] = make_pair(reference, current)
        if "blend" in kinds:
            images["blend"] = make_blend(reference, current)
        if "diff" in kinds:
            images["diff"] = make_diff(
                reference,
                current,
                raw_difference,
            )
        for kind, image in images.items():
            if image is None:
                raise RuntimeError(f"Changed generated grid {case} produced no {kind}")
            directory = output_directories[kind]
            directory.mkdir(parents=True, exist_ok=True)
            image.save(directory / f"{case}.png")

    print(
        f"Compared {compared} paired grids; "
        f"wrote {changed} changed comparison sets to {output}"
    )


def main() -> int:
    args = parse_args()
    if args.screenshots is not None:
        write_screenshot_grid_pages(
            args.screenshots,
            args.output,
        )
        print(f"Screenshot grids written to {args.output}")
        return 0
    if args.paired_grids is not None:
        write_paired_grid_comparisons(
            args.paired_grids,
            args.output,
            args.kind,
        )
        return 0

    reference_paths = index_pngs(args.reference)
    current_paths = index_pngs(args.current)
    captures = pair_capture_slots(set(reference_paths), set(current_paths))
    slots = parse_slot_selection(args.slots, [row.slot for row in captures])
    captures = [row for row in captures if row.slot in set(slots)]
    args.output.mkdir(parents=True, exist_ok=True)
    pair_grid_root = args.output / "pairs"
    blend_grid_root = args.output / "blends"
    diff_grid_root = args.output / "diffs"

    kinds = ("pair", "blend", "diff") if args.kind == "all" else (args.kind,)
    grid_directories = {
        "pair": pair_grid_root,
        "blend": blend_grid_root,
        "diff": diff_grid_root,
    }
    grid_items: dict[str, list[tuple[CaptureRow, Image.Image]]] = {
        kind: [] for kind in kinds
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

        raw_difference = ImageChops.difference(reference, current)
        if raw_difference.getbbox() is None:
            continue

        images: dict[str, Image.Image] = {}
        if "pair" in kinds:
            images["pair"] = make_pair(reference, current)
        if "blend" in kinds:
            images["blend"] = make_blend(reference, current)
        if "diff" in kinds:
            diff = make_diff(
                reference,
                current,
                raw_difference,
            )
            if diff is None:
                raise RuntimeError(f"Changed slot {row.slot:04d} produced no diff")
            images["diff"] = diff
        for kind, image in images.items():
            grid_items[kind].append((row, image))

    for kind in kinds:
        output = grid_directories[kind]
        clear_generated_grid_pages(output)
        output.mkdir(parents=True, exist_ok=True)
        if grid_items[kind]:
            if kind == "pair":
                write_pair_grid_pages(grid_items[kind], output)
            else:
                write_fixed_grid_pages(grid_items[kind], output)
    print(
        f"Compared {len(captures)} exact-scale pairs; evidence written to {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
