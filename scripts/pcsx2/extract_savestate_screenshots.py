from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


SCREENSHOT_MEMBER = "Screenshot.png"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def extract_screenshot(state: Path) -> bytes:
    try:
        with zipfile.ZipFile(state) as archive:
            if SCREENSHOT_MEMBER not in archive.namelist():
                raise RuntimeError(
                    f"{state.name} has no embedded {SCREENSHOT_MEMBER}"
                )
            try:
                data = archive.read(SCREENSHOT_MEMBER)
            except (NotImplementedError, RuntimeError):
                data = b""
    except zipfile.BadZipFile as exc:
        raise RuntimeError(f"{state.name} is not a valid savestate ZIP") from exc

    if not data:
        tar = shutil.which("tar")
        if tar is None:
            raise RuntimeError(
                f"{state.name} uses unsupported ZIP compression and tar is unavailable"
            )
        result = subprocess.run(
            [tar, "-xOf", str(state), SCREENSHOT_MEMBER],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        data = result.stdout
        if result.returncode != 0 and not data.startswith(PNG_SIGNATURE):
            detail = result.stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(f"Could not extract {state.name}: {detail}")

    if not data.startswith(PNG_SIGNATURE):
        raise RuntimeError(f"Embedded screenshot in {state.name} is not a PNG")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract embedded screenshots from every savestate in a folder."
    )
    parser.add_argument("folder", type=Path)
    args = parser.parse_args()

    folder = args.folder.resolve()
    if not folder.is_dir():
        parser.error(f"folder does not exist: {folder}")

    states = sorted(
        (
            path
            for path in folder.iterdir()
            if path.is_file() and path.suffix.casefold() == ".p2s"
        ),
        key=lambda path: path.name.casefold(),
    )
    if not states:
        print(f"No .p2s savestates found in {folder}")
        return 0

    for state in states:
        output = state.with_suffix(".png")
        output.write_bytes(extract_screenshot(state))
        print(f"{state.name} -> {output.name}")

    print(f"Extracted {len(states)} screenshot(s) into {folder}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
