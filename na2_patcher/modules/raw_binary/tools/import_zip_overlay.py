#!/usr/bin/env python3
"""Convert a same-size ZIP overlay into one declarative raw-binary patch set."""
from __future__ import annotations

import argparse
import csv
import hashlib
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from na2_patcher.modules.raw_binary import engine


def repository_path(value: str, label: str, *, must_exist: bool = True) -> Path:
    workspace = Path.cwd().resolve()
    raw = Path(value)
    if raw.is_absolute() or ".." in raw.parts:
        raise ValueError(f"{label} must be repository-relative: {value}")
    resolved = (workspace / raw).resolve()
    try:
        resolved.relative_to(workspace)
    except ValueError as exc:
        raise ValueError(f"{label} escapes the repository: {value}") from exc
    if must_exist and not resolved.exists():
        raise FileNotFoundError(resolved)
    return resolved


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def write_tsv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def normalized_entry(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if (
        not value
        or "\\" in value
        or path.is_absolute()
        or any(part in {"", ".", ".."} for part in path.parts)
        or path.as_posix() != value
    ):
        raise ValueError(f"Unsafe or non-normalized ZIP entry: {value!r}")
    return path


def target_id(path: PurePosixPath) -> str:
    value = re.sub(r"[^a-z0-9]+", "_", path.as_posix().lower()).strip("_")
    if not value:
        raise ValueError(f"Could not derive target ID from {path}")
    return value


def changed_ranges(clean: bytes, replacement: bytes, maximum_gap: int) -> list[tuple[int, int]]:
    changed = [index for index, pair in enumerate(zip(clean, replacement)) if pair[0] != pair[1]]
    if not changed:
        return []
    ranges: list[tuple[int, int]] = []
    start = previous = changed[0]
    for index in changed[1:]:
        if index - previous - 1 > maximum_gap:
            ranges.append((start, previous + 1))
            start = index
        previous = index
    ranges.append((start, previous + 1))
    return ranges


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True)
    parser.add_argument("--archive-sha256", required=True)
    parser.add_argument("--root", required=True)
    parser.add_argument("--root-id", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--package-id", required=True)
    parser.add_argument("--patch-id", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--description", required=True)
    parser.add_argument("--evidence-path", default="")
    parser.add_argument("--maximum-gap", type=int, default=64)
    parser.add_argument("--default-enabled", action="store_true")
    args = parser.parse_args()

    if args.maximum_gap < 0:
        raise ValueError("--maximum-gap must be nonnegative")
    archive = repository_path(args.archive, "--archive")
    root = repository_path(args.root, "--root")
    output = repository_path(args.output, "--output", must_exist=False)
    if output.exists():
        raise FileExistsError(f"Output already exists: {args.output}")
    if not root.is_dir():
        raise NotADirectoryError(root)

    archive_data = archive.read_bytes()
    actual_archive_hash = sha256(archive_data)
    expected_archive_hash = args.archive_sha256.strip().upper()
    if actual_archive_hash != expected_archive_hash:
        raise ValueError(
            f"Archive SHA-256 mismatch: expected {expected_archive_hash}, found {actual_archive_hash}"
        )

    targets: list[dict[str, object]] = []
    edits: list[dict[str, object]] = []
    seen_targets: set[str] = set()
    order = 0
    with zipfile.ZipFile(archive) as package:
        infos = sorted((info for info in package.infolist() if not info.is_dir()), key=lambda item: item.filename)
        if not infos:
            raise ValueError("Archive contains no files")
        seen_entries: set[PurePosixPath] = set()
        for info in infos:
            entry = normalized_entry(info.filename)
            if entry in seen_entries:
                raise ValueError(f"Duplicate ZIP entry: {entry}")
            seen_entries.add(entry)
            identifier = target_id(entry)
            if identifier in seen_targets:
                raise ValueError(f"Target ID collision for {entry}: {identifier}")
            seen_targets.add(identifier)

            source_path = root.joinpath(*entry.parts)
            if not source_path.is_file():
                raise FileNotFoundError(f"Clean target is missing: {args.root}/{entry.as_posix()}")
            clean = source_path.read_bytes()
            replacement = package.read(info)
            if len(clean) != len(replacement):
                raise ValueError(
                    f"Size-changing overlay is unsupported for {entry}: {len(clean)} -> {len(replacement)}"
                )
            ranges = changed_ranges(clean, replacement, args.maximum_gap)
            if not ranges:
                raise ValueError(f"Overlay entry is unchanged: {entry}")

            targets.append(
                {
                    "target_id": identifier,
                    "root_id": args.root_id,
                    "role": "destination",
                    "path": entry.as_posix(),
                    "expected_size": len(clean),
                    "expected_sha256": sha256(clean),
                }
            )
            for range_number, (start, end) in enumerate(ranges, 1):
                order += 10
                blank = {
                    "expected_sha256": "",
                    "source_target_id": "",
                    "source_offset": "",
                    "source_expected_hex": "",
                    "source_expected_sha256": "",
                    "blob_path": "",
                    "blob_offset": "",
                    "blob_sha256": "",
                    "fill_hex": "",
                }
                edits.append(
                    {
                        **blank,
                        "edit_id": f"{args.patch_id}_{identifier}_{range_number:02d}",
                        "patch_id": args.patch_id,
                        "order": order,
                        "destination_target_id": identifier,
                        "destination_offset": f"0x{start:X}",
                        "operation": "replace",
                        "length": end - start,
                        "expected_hex": clean[start:end].hex().upper(),
                        "replacement_hex": replacement[start:end].hex().upper(),
                        "reason": f"Exact normalized {entry.as_posix()} range from the accepted overlay.",
                    }
                )
            print(
                f"{entry.as_posix()}: {len(ranges)} ranges, "
                f"{sum(end - start for start, end in ranges)} covered bytes, "
                f"output SHA-256 {sha256(replacement)}"
            )

    output.mkdir(parents=True)
    write_tsv(
        output / "manifest.tsv",
        engine.MANIFEST_FIELDS,
        [
            {
                "schema_version": 1,
                "package_id": args.package_id,
                "package_version": 1,
                "game": "NA2",
                "description": args.description,
                "evidence_path": args.evidence_path,
            }
        ],
    )
    write_tsv(output / "targets.tsv", engine.TARGET_FIELDS, targets)
    write_tsv(
        output / "patches.tsv",
        engine.PATCH_FIELDS,
        [
            {
                "patch_id": args.patch_id,
                "default_enabled": 1 if args.default_enabled else 0,
                "status": "runtime_proven",
                "confidence": "verified",
                "name": args.name,
                "description": args.description,
                "source_mapping_id": "normalized_zip_overlay",
                "runtime_classification": "Accepted runtime milestone.",
                "review_notes": f"Source archive SHA-256 {actual_archive_hash}; retained in Git history.",
            }
        ],
    )
    write_tsv(output / "relations.tsv", engine.RELATION_FIELDS, [])
    write_tsv(output / "edits.tsv", engine.EDIT_FIELDS, edits)
    print(f"Wrote {args.output}: {len(targets)} targets, {len(edits)} edits")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
