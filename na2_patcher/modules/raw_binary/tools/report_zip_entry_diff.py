#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import zipfile
from pathlib import Path


def relative_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("Paths must be repository-relative")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Report aligned differences for one ZIP entry.")
    parser.add_argument("--clean", required=True)
    parser.add_argument("--archive", required=True)
    parser.add_argument("--entry", required=True)
    parser.add_argument("--alignment", type=int, default=1)
    args = parser.parse_args()

    clean_path = relative_path(args.clean)
    archive_path = relative_path(args.archive)
    if args.alignment <= 0:
        raise ValueError("--alignment must be positive")
    clean = clean_path.read_bytes()
    with zipfile.ZipFile(archive_path) as archive:
        modified = archive.read(args.entry)
    if len(clean) != len(modified):
        raise ValueError(f"Sizes differ: {len(clean)} != {len(modified)}")

    changed_units = sorted(
        {index // args.alignment for index, (old, new) in enumerate(zip(clean, modified)) if old != new}
    )
    print("offset\tlength\texpected_hex\treplacement_hex")
    if not changed_units:
        return 0
    start = previous = changed_units[0]
    ranges: list[tuple[int, int]] = []
    for unit in changed_units[1:]:
        if unit != previous + 1:
            ranges.append((start * args.alignment, (previous + 1) * args.alignment))
            start = unit
        previous = unit
    ranges.append((start * args.alignment, min((previous + 1) * args.alignment, len(clean))))
    for start, end in ranges:
        print(
            f"0x{start:X}\t{end - start}\t"
            f"{clean[start:end].hex().upper()}\t{modified[start:end].hex().upper()}"
        )
    print(f"# clean_sha256={hashlib.sha256(clean).hexdigest().upper()}")
    print(f"# modified_sha256={hashlib.sha256(modified).hexdigest().upper()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
