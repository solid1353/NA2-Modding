from __future__ import annotations

import csv
import hashlib
import re
from collections.abc import Collection, Sequence
from pathlib import Path


SYMBOL_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*\Z")


def sha256_hex(data: bytes | bytearray) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def parse_int(value: str, label: str) -> int:
    """Parse a nonnegative decimal or 0x-prefixed integer."""
    text = value.strip()
    try:
        result = int(text, 0)
    except ValueError as exc:
        raise ValueError(f"{label}: invalid integer {text!r}") from exc
    if result < 0:
        raise ValueError(f"{label}: negative integer")
    return result


def read_tsv(
    path: Path,
    fields: Sequence[str],
    *,
    verbatim: Collection[str] = (),
) -> list[dict[str, str]]:
    """Read a TSV with exactly `fields` as its header.

    Blank rows are skipped and missing trailing cells read as empty. Values are
    stripped except in the `verbatim` columns.
    """
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != list(fields):
            raise ValueError(f"{path.name}: expected columns " + "\t".join(fields))
        rows = []
        for line, row in enumerate(reader, 2):
            if None in row:
                raise ValueError(f"{path.name} line {line} has extra columns")
            values = {key: value or "" for key, value in row.items()}
            if any(value.strip() for value in values.values()):
                rows.append({
                    key: value if key in verbatim else value.strip()
                    for key, value in values.items()
                })
    return rows


UINT64_MAX = (1 << 64) - 1


def key_problems(
    actual: Collection[str],
    required: Collection[str],
    allowed: Collection[str] | None = None,
    *,
    noun: str = "keys",
) -> str:
    """Describe missing and unknown keys, or return "" when there are none."""
    missing = sorted(set(required) - set(actual))
    extra = sorted(set(actual) - set(required if allowed is None else allowed))
    problems = []
    if missing:
        problems.append(f"missing {noun}: " + ", ".join(missing))
    if extra:
        problems.append(f"unknown {noun}: " + ", ".join(extra))
    return "; ".join(problems)


def indexed_png_pixels(path: Path, size: tuple[int, int], *, flip: bool = False) -> bytes:
    """Palette indices of an indexed PNG, top row first unless flipped."""
    from PIL import Image

    with Image.open(path) as image:
        if image.size != size or image.mode != "P":
            raise ValueError(f"{path.name} must be a {size[0]}x{size[1]} indexed PNG")
        if flip:
            image = image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        return image.tobytes()
