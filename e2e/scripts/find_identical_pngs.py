"""Print captured PNG names whose decoded pixels match the existing image."""

from __future__ import annotations

import argparse
import io
from pathlib import Path
import subprocess

from PIL import Image


def read_head_file(repository: Path, relative_path: str) -> bytes | None:
    result = subprocess.run(
        ["git", "-C", str(repository), "show", f"HEAD:{relative_path}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.stdout if result.returncode == 0 else None


def images_match(existing_data: bytes, captured_path: Path) -> bool:
    with Image.open(io.BytesIO(existing_data)) as existing_source:
        with Image.open(captured_path) as captured_source:
            if existing_source.size != captured_source.size:
                return False
            existing = existing_source.convert("RGBA")
            captured = captured_source.convert("RGBA")
            return existing.tobytes() == captured.tobytes()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--existing-prefix", required=True)
    parser.add_argument("--existing-order", required=True)
    parser.add_argument("--existing-label", required=True)
    parser.add_argument("--captured", type=Path, required=True)
    parser.add_argument("--state-prefix", required=True)
    parser.add_argument("--state-output", type=Path, required=True)
    args = parser.parse_args()

    args.state_output.mkdir(parents=True, exist_ok=True)
    for captured_path in sorted(args.captured.glob("*.png")):
        if not captured_path.stem.isdecimal():
            raise ValueError(f"Captured PNG name is not numeric: {captured_path.name}")
        slot = int(captured_path.stem)
        existing_name = (
            f"{slot:03d}_{args.existing_order}_{args.existing_label}.png"
        )
        existing_path = f"{args.existing_prefix.rstrip('/')}/{existing_name}"
        existing_data = read_head_file(args.repository, existing_path)
        if existing_data is None or not images_match(existing_data, captured_path):
            continue
        print(captured_path.name)
        state_name = captured_path.with_suffix(".p2s").name
        state_path = f"{args.state_prefix.rstrip('/')}/{state_name}"
        state_data = read_head_file(args.repository, state_path)
        if state_data is not None:
            (args.state_output / state_name).write_bytes(state_data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
