"""Print captured PNG names whose decoded pixels match the existing image."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


def images_match(existing_path: Path, captured_path: Path) -> bool:
    with Image.open(existing_path) as existing_source:
        with Image.open(captured_path) as captured_source:
            if existing_source.size != captured_source.size:
                return False
            existing = existing_source.convert("RGBA")
            captured = captured_source.convert("RGBA")
            return existing.tobytes() == captured.tobytes()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--existing", type=Path, required=True)
    parser.add_argument("--captured", type=Path, required=True)
    args = parser.parse_args()

    for captured_path in sorted(args.captured.glob("*.png")):
        existing_path = args.existing / captured_path.name
        if existing_path.is_file() and images_match(existing_path, captured_path):
            print(captured_path.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
