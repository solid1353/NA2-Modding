#!/usr/bin/env python3
"""Compose one NUN5-left / Current-NA2-right Font comparison artifact."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont


REPOSITORY_BOOTSTRAP = Path(__file__).resolve().parents[3]
if str(REPOSITORY_BOOTSTRAP) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_BOOTSTRAP))

from na2_patcher.project_paths import load_project_paths


PROJECT_PATHS = load_project_paths(Path(__file__).resolve(), allow_missing=True)
REPOSITORY = PROJECT_PATHS.repository
BACKGROUND = (20, 22, 27)
PRIMARY = (236, 239, 245)
SECONDARY = (177, 185, 198)
ACCENT = (255, 202, 64)
PADDING = 16
GAP = 12
HEADER_HEIGHT = 92


def repository_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        raise argparse.ArgumentTypeError("paths must be repository-relative")
    resolved = (REPOSITORY / path).resolve()
    if REPOSITORY not in resolved.parents and resolved != REPOSITORY:
        raise argparse.ArgumentTypeError("path escapes the repository")
    return resolved


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", required=True, type=repository_path)
    parser.add_argument("--current", required=True, type=repository_path)
    parser.add_argument("--output", required=True, type=repository_path)
    parser.add_argument("--section", required=True)
    parser.add_argument("--case", required=True)
    parser.add_argument("--status", required=True)
    parser.add_argument("--finding", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    reference = Image.open(args.reference).convert("RGB")
    current = Image.open(args.current).convert("RGB")
    if reference.size != current.size:
        raise ValueError(
            f"source dimensions differ: {reference.size} versus {current.size}"
        )

    font = ImageFont.load_default()
    width, height = reference.size
    canvas = Image.new(
        "RGB",
        (
            PADDING * 2 + width * 2 + GAP,
            PADDING * 2 + HEADER_HEIGHT + height,
        ),
        BACKGROUND,
    )
    draw = ImageDraw.Draw(canvas)
    draw.text((PADDING, 10), args.section, fill=PRIMARY, font=font)
    draw.text(
        (PADDING, 30),
        f"{args.case}  |  {args.status}",
        fill=ACCENT,
        font=font,
    )
    draw.text((PADDING, 50), args.finding, fill=SECONDARY, font=font)
    draw.text(
        (PADDING + width // 2, 72),
        "NUN5 reference",
        anchor="mm",
        fill=PRIMARY,
        font=font,
    )
    draw.text(
        (PADDING + width + GAP + width // 2, 72),
        "Current NA2.28",
        anchor="mm",
        fill=PRIMARY,
        font=font,
    )

    y = PADDING + HEADER_HEIGHT
    canvas.paste(reference, (PADDING, y))
    canvas.paste(current, (PADDING + width + GAP, y))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(args.output, optimize=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
