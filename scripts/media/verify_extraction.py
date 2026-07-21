from __future__ import annotations

import argparse
import os
import stat
import struct
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[2]
if str(REPOSITORY) not in sys.path:
    sys.path.insert(0, str(REPOSITORY))

from na2_patcher.image_assembler.iso9660 import Iso9660, IsoRecord
from na2_patcher.project_paths import load_project_paths


PROJECT_PATHS = load_project_paths(REPOSITORY)


@dataclass
class Totals:
    iso_archives: int = 0
    afs_archives: int = 0
    cvm_archives: int = 0
    files: int = 0
    bytes: int = 0


def configured_path(path: Path) -> Path:
    resolved = path.resolve()
    roots = [
        value.resolve()
        for name, value in PROJECT_PATHS.roots.items()
        if name != "repository"
    ] + [PROJECT_PATHS.repository.resolve()]
    if not any(resolved == root or root in resolved.parents for root in roots):
        raise ValueError(f"Path is outside configured project roots: {path}")
    return resolved


def compare_extent(archive: Path, offset: int, size: int, extracted: Path) -> None:
    if extracted.stat().st_size != size:
        raise RuntimeError(
            f"Size mismatch for {extracted}: expected {size}, found {extracted.stat().st_size}"
        )
    with archive.open("rb") as source, extracted.open("rb") as target:
        source.seek(offset)
        remaining = size
        while remaining:
            amount = min(4 * 1024 * 1024, remaining)
            left = source.read(amount)
            right = target.read(amount)
            if left != right:
                raise RuntimeError(f"Content mismatch: {extracted}")
            remaining -= amount


def base_tree(root: Path) -> tuple[dict[str, Path], dict[str, Path]]:
    files: dict[str, Path] = {}
    directories: dict[str, Path] = {"": root}
    for current, names, filenames in os.walk(root):
        current_path = Path(current)
        names[:] = [
            name
            for name in names
            if not (
                name.lower().endswith(".files")
                and (current_path / name[:-6]).is_file()
                and (current_path / name[:-6]).suffix.lower() in {".iso", ".cvm", ".afs"}
            )
        ]
        for name in names:
            path = current_path / name
            key = path.relative_to(root).as_posix().upper()
            directories[key] = path
        for name in filenames:
            path = current_path / name
            key = path.relative_to(root).as_posix().upper()
            if key in files:
                raise RuntimeError(f"Case-colliding extraction path: {path}")
            files[key] = path
    return files, directories


def record_timestamp(record: IsoRecord, archive: Path) -> float:
    return (
        record.recorded_at.timestamp()
        if record.recorded_at is not None
        else archive.stat().st_mtime
    )


def verify_iso(
    archive: Path,
    output: Path,
    normalize_timestamps: bool,
    totals: Totals,
) -> None:
    image = Iso9660(archive)
    actual_files, actual_directories = base_tree(output)
    expected_files = {
        record.path.upper(): record
        for record in image.records
        if record.path and not record.is_dir
    }
    expected_directories = {
        record.path.upper(): record
        for record in image.records
        if record.is_dir
    }
    if set(actual_files) != set(expected_files):
        missing = sorted(set(expected_files) - set(actual_files))
        extra = sorted(set(actual_files) - set(expected_files))
        raise RuntimeError(f"ISO file-set mismatch for {archive}: missing={missing}, extra={extra}")
    if set(actual_directories) != set(expected_directories):
        missing = sorted(set(expected_directories) - set(actual_directories))
        extra = sorted(set(actual_directories) - set(expected_directories))
        raise RuntimeError(
            f"ISO directory-set mismatch for {archive}: missing={missing}, extra={extra}"
        )

    for key, record in expected_files.items():
        target = actual_files[key]
        compare_extent(archive, record.byte_offset, record.size, target)
        if normalize_timestamps:
            timestamp = record_timestamp(record, archive)
            os.utime(target, (timestamp, timestamp))
        totals.files += 1
        totals.bytes += record.size

    if normalize_timestamps:
        for key in sorted(expected_directories, key=lambda value: value.count("/"), reverse=True):
            timestamp = record_timestamp(expected_directories[key], archive)
            os.utime(actual_directories[key], (timestamp, timestamp))
    totals.iso_archives += 1


def guessed_extension(sample: bytes) -> str:
    if sample.startswith(b"AFS\0"):
        return ".afs"
    if sample.startswith(b"RIFF"):
        return ".wav"
    if sample.startswith(b"TIM2"):
        return ".tm2"
    if sample.startswith(b"\0\0\x01\xba"):
        return ".pss"
    if sample.startswith(b"AHX"):
        return ".ahx"
    if sample.startswith(b"\x80\0") or b"CRI" in sample:
        return ".adx"
    return ".bin"


def afs_metadata(handle, count: int, archive_size: int) -> list[datetime | None]:
    pointer = handle.read(8)
    if len(pointer) != 8:
        return []
    offset, size = struct.unpack("<II", pointer)
    required = count * 48
    if offset <= 0 or size < required or offset + required > archive_size:
        return []
    handle.seek(offset)
    result: list[datetime | None] = []
    for _ in range(count):
        row = handle.read(48)
        if len(row) != 48:
            raise RuntimeError("Unexpected EOF in AFS metadata")
        year, month, day, hour, minute, second = struct.unpack_from("<6H", row, 32)
        try:
            result.append(datetime(year, month, day, hour, minute, second))
        except ValueError:
            result.append(None)
    return result


def verify_afs(
    archive: Path,
    output: Path,
    normalize_timestamps: bool,
    totals: Totals,
) -> None:
    with archive.open("rb") as handle:
        if handle.read(4) != b"AFS\0":
            raise RuntimeError(f"Invalid AFS magic: {archive}")
        count = struct.unpack("<I", handle.read(4))[0]
        entries = [struct.unpack("<II", handle.read(8)) for _ in range(count)]
        metadata = afs_metadata(handle, count, archive.stat().st_size)

        width = max(3, len(str(max(0, count - 1))))
        expected_names: set[str] = set()
        for index, (offset, size) in enumerate(entries):
            if offset + size > archive.stat().st_size:
                raise RuntimeError(f"AFS entry points outside archive: {archive} #{index}")
            handle.seek(offset)
            sample = handle.read(min(size, 512))
            name = f"{index:0{width}d}{guessed_extension(sample)}"
            expected_names.add(name.lower())
            target = output / name
            if not target.is_file():
                raise RuntimeError(f"Missing AFS member: {target}")
            compare_extent(archive, offset, size, target)
            if normalize_timestamps:
                timestamp = (
                    metadata[index].timestamp()
                    if len(metadata) == count and metadata[index] is not None
                    else archive.stat().st_mtime
                )
                os.utime(target, (timestamp, timestamp))
            totals.files += 1
            totals.bytes += size

    actual_names = {path.name.lower() for path in output.iterdir() if path.is_file()}
    if actual_names != expected_names:
        raise RuntimeError(
            f"AFS file-set mismatch for {archive}: "
            f"missing={sorted(expected_names - actual_names)}, "
            f"extra={sorted(actual_names - expected_names)}"
        )
    if normalize_timestamps:
        timestamp = archive.stat().st_mtime
        os.utime(output, (timestamp, timestamp))
    totals.afs_archives += 1


def verify_read_only(paths: list[Path]) -> None:
    readonly_flag = getattr(stat, "FILE_ATTRIBUTE_READONLY", 1)
    missing: list[Path] = []
    for root in paths:
        for path in [root, *root.rglob("*")]:
            attributes = getattr(path.stat(), "st_file_attributes", 0)
            if not attributes & readonly_flag:
                missing.append(path)
                if len(missing) >= 20:
                    break
        if missing:
            break
    if missing:
        raise RuntimeError("Items are not read-only: " + ", ".join(str(path) for path in missing))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iso", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--normalize-timestamps", action="store_true")
    parser.add_argument("--require-read-only", action="store_true")
    args = parser.parse_args()

    outer_iso = configured_path(args.iso)
    outer_output = configured_path(args.out_dir)
    if not outer_iso.is_file() or not outer_output.is_dir():
        raise FileNotFoundError(outer_iso if not outer_iso.is_file() else outer_output)

    iso_jobs: list[tuple[Path, Path]] = [(outer_iso, outer_output)]
    afs_jobs: list[tuple[Path, Path]] = []
    cvm_files: list[Path] = []
    for path in outer_output.rglob("*"):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        extracted = Path(str(path) + ".files")
        if suffix == ".iso":
            iso_jobs.append((path, extracted))
        elif suffix == ".afs":
            afs_jobs.append((path, extracted))
        elif suffix == ".cvm":
            cvm_files.append(path)

    totals = Totals(cvm_archives=len(cvm_files))
    for cvm in cvm_files:
        extracted = Path(str(cvm) + ".files")
        inner_iso = extracted / f"{cvm.name}.iso"
        header = extracted / f"{cvm.name}.hdr"
        if not inner_iso.is_file() or not header.is_file() or not Path(str(inner_iso) + ".files").is_dir():
            raise RuntimeError(f"Incomplete CVM extraction: {cvm}")

    for archive, output in iso_jobs:
        if not output.is_dir():
            raise RuntimeError(f"Missing ISO extraction: {output}")
        verify_iso(archive, output, args.normalize_timestamps, totals)
    for archive, output in afs_jobs:
        if not output.is_dir():
            raise RuntimeError(f"Missing AFS extraction: {output}")
        verify_afs(archive, output, args.normalize_timestamps, totals)

    if args.normalize_timestamps:
        for archive, output in sorted(
            [*iso_jobs, *afs_jobs, *((cvm, Path(str(cvm) + ".files")) for cvm in cvm_files)],
            key=lambda item: len(item[1].parts),
            reverse=True,
        ):
            timestamp = archive.stat().st_mtime
            os.utime(output, (timestamp, timestamp))

    if args.require_read_only:
        verify_read_only([outer_iso, outer_output])

    print(
        f"Verified {outer_iso.name}: "
        f"{totals.iso_archives} ISO, {totals.cvm_archives} CVM, "
        f"{totals.afs_archives} AFS, {totals.files} members, {totals.bytes} bytes"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
