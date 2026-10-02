#!/usr/bin/env python3
"""Measure color-scoped font ink in paired native-resolution screenshot regions."""

from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


SLOT_SUFFIX = re.compile(r"(\d+)$")
HEADER_HEIGHT = 24
ZOOM = 4
TIERS = ("reference", "current")
BOX_SIDES = ("left", "top", "right", "bottom")


@dataclass(frozen=True)
class Region:
    slot: int
    reference_slot: int
    current_slot: int
    name: str
    reference_box: tuple[int, int, int, int]
    current_box: tuple[int, int, int, int]
    reference_mask: str
    current_mask: str
    notes: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", required=True, type=Path)
    parser.add_argument("--current", required=True, type=Path)
    parser.add_argument("--regions", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--reference-label", default="Reference")
    parser.add_argument("--current-label", default="Current")
    return parser.parse_args()


def numeric_slot(path: Path) -> int:
    match = SLOT_SUFFIX.search(path.stem)
    if match is None:
        raise ValueError(f"PNG name has no numeric suffix: {path.name}")
    return int(match.group(1))


def index_pngs(directory: Path) -> dict[int, Path]:
    result: dict[int, Path] = {}
    for path in sorted(directory.glob("*.png")):
        slot = numeric_slot(path)
        if slot in result:
            raise ValueError(f"Duplicate slot {slot} in {directory}")
        result[slot] = path
    if not result:
        raise ValueError(f"No PNG files in {directory}")
    return result


def load_regions(path: Path) -> list[Region]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        fields = set(reader.fieldnames or ())
        mapped_fields = {
            f"{tier}_{name}" for tier in TIERS for name in ("slot", *BOX_SIDES)
        }
        mapped = mapped_fields <= fields
        per_tier_masks = {f"{tier}_mask" for tier in TIERS} <= fields
        if not (
            {"slot", "region", "notes"} <= fields
            and ("mask" in fields or per_tier_masks)
            and (mapped or set(BOX_SIDES) <= fields)
        ):
            raise ValueError(
                "Region table must contain slot, region, notes, a mask, and either "
                f"{list(BOX_SIDES)} or {sorted(mapped_fields)}"
            )
        rows = list(reader)

    result = []
    for row in rows:
        slots: list[int] = []
        boxes: list[tuple[int, int, int, int]] = []
        masks: list[str] = []
        for tier in TIERS:
            prefix = f"{tier}_" if mapped else ""
            slots.append(int(row[f"{prefix}slot"]))
            box = tuple(int(row[f"{prefix}{side}"]) for side in BOX_SIDES)
            if box[0] >= box[2] or box[1] >= box[3]:
                raise ValueError(f"Invalid box {box} in {path}")
            boxes.append(box)
            mask = row[f"{tier}_mask" if per_tier_masks else "mask"].strip().lower()
            if mask not in {"red", "dark", "light"}:
                raise ValueError(f"Unknown mask {mask!r} in {path}")
            masks.append(mask)
        reference_size, current_size = (
            (box[2] - box[0], box[3] - box[1]) for box in boxes
        )
        if reference_size != current_size:
            raise ValueError(
                f"Mapped region sizes differ {reference_size} vs {current_size} in {path}"
            )
        result.append(
            Region(
                int(row["slot"]),
                *slots,
                row["region"].strip(),
                *boxes,
                *masks,
                row["notes"].strip(),
            )
        )
    if not result:
        raise ValueError(f"No regions in {path}")
    return result


def pixel_matches(pixel: tuple[int, int, int], mask: str) -> bool:
    red, green, blue = pixel
    if mask == "red":
        return red >= 90 and red >= green + 35 and red >= blue + 35
    if mask == "dark":
        return max(red, green, blue) <= 125 and max(red, green, blue) - min(red, green, blue) <= 45
    return min(red, green, blue) >= 175 and max(red, green, blue) - min(red, green, blue) <= 55


def ink_points(image: Image.Image, mask: str) -> list[tuple[int, int]]:
    pixels = image.load()
    candidates = {
        (x, y)
        for y in range(image.height)
        for x in range(image.width)
        if pixel_matches(pixels[x, y], mask)
    }
    retained: list[tuple[int, int]] = []
    while candidates:
        start = candidates.pop()
        component = [start]
        pending = [start]
        while pending:
            x, y = pending.pop()
            for neighbor_y in range(max(0, y - 1), min(image.height, y + 2)):
                for neighbor_x in range(max(0, x - 1), min(image.width, x + 2)):
                    neighbor = (neighbor_x, neighbor_y)
                    if neighbor in candidates:
                        candidates.remove(neighbor)
                        component.append(neighbor)
                        pending.append(neighbor)
        xs = [point[0] for point in component]
        ys = [point[1] for point in component]
        width = max(xs) - min(xs) + 1
        height = max(ys) - min(ys) + 1
        if len(component) >= 2 and width <= 32 and height <= 28:
            retained.extend(component)
    return retained


def ink_bbox(points: list[tuple[int, int]]) -> tuple[int, int, int, int] | None:
    if not points:
        return None
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return min(xs), min(ys), max(xs) + 1, max(ys) + 1


def make_pair(
    reference: Image.Image,
    current: Image.Image,
    title: str,
    reference_label: str,
    current_label: str,
) -> Image.Image:
    width = reference.width + current.width
    result = Image.new("RGB", (width, HEADER_HEIGHT + reference.height), (18, 18, 18))
    result.paste(reference, (0, HEADER_HEIGHT))
    result.paste(current, (reference.width, HEADER_HEIGHT))
    draw = ImageDraw.Draw(result)
    font = ImageFont.load_default()
    draw.text((4, 7), f"{reference_label} | {title}", font=font, fill=(255, 255, 255))
    draw.text(
        (reference.width + 4, 7),
        current_label,
        font=font,
        fill=(255, 255, 255),
    )
    draw.line((reference.width, 0, reference.width, result.height), fill=(255, 255, 255))
    return result


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._") or "region"


def main() -> int:
    args = parse_args()
    reference_paths = index_pngs(args.reference)
    current_paths = index_pngs(args.current)
    regions = load_regions(args.regions)
    args.output.mkdir(parents=True, exist_ok=True)
    one_x = args.output / "1x"
    zoomed = args.output / "4x_nearest"
    one_x.mkdir(exist_ok=True)
    zoomed.mkdir(exist_ok=True)

    rows: list[dict[str, object]] = []
    for region in regions:
        if region.reference_slot not in reference_paths:
            raise ValueError(f"Reference slot {region.reference_slot} is absent")
        if region.current_slot not in current_paths:
            raise ValueError(f"Current slot {region.current_slot} is absent")
        with Image.open(reference_paths[region.reference_slot]) as source:
            reference = source.convert("RGB")
        with Image.open(current_paths[region.current_slot]) as source:
            current = source.convert("RGB")
        if reference.size != current.size:
            raise ValueError(f"Slot {region.slot} image-size mismatch")
        if (
            region.reference_box[2] > reference.width
            or region.reference_box[3] > reference.height
        ):
            raise ValueError(
                f"Region exceeds reference slot {region.reference_slot}: {region.reference_box}"
            )
        if region.current_box[2] > current.width or region.current_box[3] > current.height:
            raise ValueError(
                f"Region exceeds current slot {region.current_slot}: {region.current_box}"
            )

        reference_crop = reference.crop(region.reference_box)
        current_crop = current.crop(region.current_box)
        reference_points = ink_points(reference_crop, region.reference_mask)
        current_points = ink_points(current_crop, region.current_mask)
        reference_bbox = ink_bbox(reference_points)
        current_bbox = ink_bbox(current_points)
        pair = make_pair(
            reference_crop,
            current_crop,
            (
                f"case {region.slot:04d} ref {region.reference_slot:04d} "
                f"cur {region.current_slot:04d} {region.name} "
                f"[{region.reference_mask}/{region.current_mask}]"
            ),
            args.reference_label,
            args.current_label,
        )
        stem = (
            f"{region.slot:04d}_{safe_name(region.name)}_"
            f"{region.reference_mask}-{region.current_mask}"
        )
        pair.save(one_x / f"{stem}.png")
        zoom = pair.resize((pair.width * ZOOM, pair.height * ZOOM), Image.Resampling.NEAREST)
        zoom.save(zoomed / f"{stem}.png")

        deltas = [""] * 4
        if reference_bbox is not None and current_bbox is not None:
            deltas = [current_bbox[index] - reference_bbox[index] for index in range(4)]
        row: dict[str, object] = {
            "slot": region.slot,
            "reference_slot": region.reference_slot,
            "current_slot": region.current_slot,
            "region": region.name,
            "reference_mask": region.reference_mask,
            "current_mask": region.current_mask,
        }
        for tier, bbox in zip(TIERS, (reference_bbox, current_bbox)):
            for index, side in enumerate(BOX_SIDES):
                row[f"{tier}_{side}"] = "" if bbox is None else bbox[index]
        for side, delta in zip(BOX_SIDES, deltas):
            row[f"delta_{side}"] = delta
        row["reference_pixels"] = len(reference_points)
        row["current_pixels"] = len(current_points)
        row["pixel_delta"] = len(current_points) - len(reference_points)
        row["notes"] = region.notes
        rows.append(row)

    with (args.output / "summary.tsv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Measured {len(rows)} font regions; output written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
