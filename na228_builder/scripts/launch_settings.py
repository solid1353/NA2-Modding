from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .catalog import load_startup_fast_forward_frames


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Resolve configuration-dependent NA2 launch settings."
    )
    parser.add_argument("--catalog", required=True, type=Path)
    parser.add_argument("--configuration", required=True, type=Path)
    parser.add_argument("--baseline-frames", required=True, type=int)
    args = parser.parse_args()
    try:
        frames = load_startup_fast_forward_frames(
            args.catalog,
            args.configuration,
            args.baseline_frames,
        )
    except (OSError, ValueError) as exc:
        print(f"ConfigurationError: {exc}", file=sys.stderr)
        return 2
    print(frames)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
