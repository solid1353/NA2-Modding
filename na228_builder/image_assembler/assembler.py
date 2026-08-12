from __future__ import annotations

import os
import shutil
from contextlib import contextmanager
from pathlib import Path

from .iso9660 import Iso9660, compose_filesystems, normalize_iso_path
from .operations import (
    AssemblyPlan,
    AssemblyResult,
    FileRename,
)

def _flush_image(handle: object) -> None:
    handle.flush()
    try:
        descriptor = handle.fileno()
    except (AttributeError, OSError):
        return
    os.fsync(descriptor)


@contextmanager
def output_image_candidate(source_image: Path, output_image: Path):
    """Initialize a unique output candidate and remove it if assembly fails."""
    output_image.parent.mkdir(parents=True, exist_ok=True)
    if source_image == output_image:
        raise ValueError("Source and output image paths must differ")
    if output_image.exists() or output_image.is_symlink():
        raise FileExistsError(output_image)

    print(f"Initializing output candidate: {output_image.name}")
    try:
        shutil.copyfile(source_image, output_image)
        yield output_image
    except BaseException:
        if output_image.exists() or output_image.is_symlink():
            output_image.unlink()
        raise


def _normalize_renames(renames: tuple[FileRename, ...]) -> dict[str, FileRename]:
    normalized: dict[str, FileRename] = {}
    targets: set[str] = set()
    for operation in renames:
        source = normalize_iso_path(operation.source_path)
        replacement = normalize_iso_path(operation.replacement_path)
        if source in normalized:
            raise ValueError(f"Duplicate image rename source: {source}")
        if replacement in targets:
            raise ValueError(f"Duplicate image rename target: {replacement}")
        if source == replacement:
            raise ValueError(f"Image rename source and target are identical: {source}")
        if source.rpartition("/")[0] != replacement.rpartition("/")[0]:
            raise ValueError("Image renames cannot move files between directories")
        if len(f"{source};1".encode("ascii")) != len(
            f"{replacement};1".encode("ascii")
        ):
            raise ValueError("Image rename identifiers must have equal byte lengths")
        normalized[source] = FileRename(
            source,
            replacement,
            operation.owner,
            operation.reason,
        )
        targets.add(replacement)
    if set(normalized) & targets:
        raise ValueError("Chained image renames are not supported")
    return normalized


def _apply_iso9660_rename(image: Path, operation: FileRename) -> dict[str, object]:
    iso = Iso9660(image)
    source_record = iso.by_path.get(operation.source_path)
    if source_record is None or source_record.is_dir:
        raise RuntimeError(
            f"Image rename source is not an ISO file: {operation.source_path}"
        )
    if operation.replacement_path in iso.by_path:
        raise RuntimeError(
            f"Image rename target already exists: {operation.replacement_path}"
        )
    if source_record.directory_record_offset is None:
        raise RuntimeError(
            f"Image rename source lacks a directory record: {operation.source_path}"
        )

    source = f"{operation.source_path};1".encode("ascii")
    replacement = f"{operation.replacement_path};1".encode("ascii")
    record_offset = source_record.directory_record_offset
    with image.open("r+b") as handle:
        handle.seek(record_offset)
        header = handle.read(33)
        if len(header) != 33 or header[0] < 34:
            raise RuntimeError("Invalid ISO9660 file directory record")
        name_length = header[32]
        actual = handle.read(name_length)
        if name_length != len(source) or actual != source:
            raise RuntimeError(
                f"ISO9660 rename guard mismatch for {operation.source_path}"
            )
        identifier_offset = record_offset + 33
        handle.seek(identifier_offset)
        handle.write(replacement)
        _flush_image(handle)

    return {
        "target": "<ISO9660 directory>",
        "offset": f"0x{identifier_offset:X}",
        "length": len(source),
        "original_hex": source.hex().upper(),
        "new_hex": replacement.hex().upper(),
        "reason": operation.reason,
        "owner": operation.owner,
    }


def _prepare_assembly(
    source_image: Path,
    plan: AssemblyPlan,
) -> tuple[Iso9660, dict[str, bytes], dict[str, bytes], dict[str, FileRename]]:
    source_image = source_image.resolve()
    if not source_image.is_file():
        raise FileNotFoundError(source_image)
    if not plan.replacements and not plan.insertions and not plan.renames:
        raise RuntimeError("The assembly plan contains no image changes")

    source = Iso9660(source_image)
    replacements = {}
    for operation in plan.replacements:
        path = normalize_iso_path(operation.path)
        if path in replacements:
            raise ValueError(f"Duplicate file replacement: {path}")
        record = source.by_path.get(path)
        if record is None or record.is_dir:
            raise RuntimeError(f"Replacement target is not a source file: {path}")
        expected = bytes(operation.expected)
        replacement = bytes(operation.replacement)
        if len(expected) != len(replacement) or len(expected) != record.size:
            raise RuntimeError(f"File replacement must preserve size: {path}")
        actual = source.read_file(record)
        if actual != expected:
            raise RuntimeError(f"File replacement source guard mismatch: {path}")
        replacements[path] = replacement

    insertions = {}
    for operation in plan.insertions:
        path = normalize_iso_path(operation.path)
        if path in insertions:
            raise ValueError(f"Duplicate file insertion: {path}")
        if path in source.by_path:
            raise RuntimeError(f"File insertion path already exists: {path}")
        payload = bytes(operation.payload)
        if not payload:
            raise ValueError(f"File insertion payload is empty: {path}")
        insertions[path] = payload

    renames = _normalize_renames(plan.renames)
    for source_path, operation in renames.items():
        record = source.by_path.get(source_path)
        if record is None or record.is_dir:
            raise RuntimeError(f"Image rename source is not a source file: {source_path}")
        if operation.replacement_path in source.by_path:
            raise RuntimeError(
                f"Image rename target already exists: {operation.replacement_path}"
            )
        if source_path in replacements:
            # Replacing a file and renaming its directory entry is valid.
            continue
    if set(insertions) & {item.replacement_path for item in renames.values()}:
        raise RuntimeError("An insertion cannot also be an image rename target")

    return source, replacements, insertions, renames


def _apply_and_verify_assembly(
    working_image: object,
    source: Iso9660,
    replacements: dict[str, bytes],
    insertions: dict[str, bytes],
    renames: dict[str, FileRename],
) -> AssemblyResult:
    current = Iso9660(working_image)
    with working_image.open("r+b") as output:
        for path in sorted(replacements):
            record = current.by_path[path]
            output.seek(record.byte_offset)
            output.write(replacements[path])
        _flush_image(output)

    iso9660_rename_results = tuple(
        _apply_iso9660_rename(working_image, renames[path])
        for path in sorted(renames)
    )
    composition = compose_filesystems(
        working_image,
        insertions,
        udf_renames={
            source_path: operation.replacement_path
            for source_path, operation in renames.items()
        },
    )
    if working_image.stat().st_size != source.file_size:
        raise RuntimeError("Image assembly changed the image size")

    result = Iso9660(working_image)
    expected_tree = {
        (
            renames[record.path].replacement_path
            if record.path in renames
            else record.path,
            record.is_dir,
        )
        for record in source.records
    }
    expected_tree.update((path, False) for path in insertions)
    result_tree = {(record.path, record.is_dir) for record in result.records}
    if result_tree != expected_tree:
        raise RuntimeError("Final image file tree differs from the assembly plan")

    for source_record in source.records:
        if source_record.is_dir:
            continue
        result_path = (
            renames[source_record.path].replacement_path
            if source_record.path in renames
            else source_record.path
        )
        result_record = result.by_path.get(result_path)
        if result_record is None or result_record.is_dir:
            raise RuntimeError(f"Final image is missing source file: {source_record.path}")
        expected = replacements.get(
            source_record.path,
            source.read_file(source_record),
        )
        if result.read_file(result_record) != expected:
            raise RuntimeError(
                f"Final image file verification failed: {source_record.path}"
            )

    insertion_by_path = {item.path: item for item in composition.insertions}
    if set(insertion_by_path) != set(insertions):
        raise RuntimeError("Final image insertion result set is incomplete")
    for path, payload in insertions.items():
        record = result.by_path.get(path)
        insertion = insertion_by_path[path]
        if (
            record is None
            or record.is_dir
            or record.extent != insertion.extent
            or record.size != len(payload)
            or result.read_file(record) != payload
        ):
            raise RuntimeError(f"Final image insertion verification failed: {path}")

    return AssemblyResult(
        insertions=composition.insertions,
        iso9660_renames=iso9660_rename_results,
        udf_renames=composition.udf_renames,
    )


def assemble_image(
    source_image: Path,
    output_image: Path,
    plan: AssemblyPlan,
) -> AssemblyResult:
    """Apply a closed operation plan to a staged image and verify the result."""
    source_image = source_image.resolve()
    output_image = output_image.resolve()
    if source_image == output_image:
        raise ValueError("Source and output image paths must differ")
    source, replacements, insertions, renames = _prepare_assembly(source_image, plan)

    with output_image_candidate(source_image, output_image) as working_image:
        return _apply_and_verify_assembly(
            working_image,
            source,
            replacements,
            insertions,
            renames,
        )
