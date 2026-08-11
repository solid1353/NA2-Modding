from __future__ import annotations

import hashlib
import io
import os
import shutil
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

from .iso9660 import Iso9660, compose_filesystems, normalize_iso_path
from .operations import (
    AssemblyDigestResult,
    AssemblyPlan,
    AssemblyResult,
    FileRename,
)


class _VirtualImage:
    """Seekable source image plus sparse in-memory writes."""

    def __init__(self, source: Path) -> None:
        self.source = source.resolve()
        self.file_size = self.source.stat().st_size
        self.writes: list[tuple[int, bytes]] = []

    def resolve(self) -> _VirtualImage:
        return self

    def stat(self) -> SimpleNamespace:
        return SimpleNamespace(st_size=self.file_size)

    def open(self, mode: str = "rb") -> _VirtualImageHandle:
        if mode not in {"rb", "r+b", "rb+"}:
            raise ValueError(f"Unsupported virtual-image mode: {mode}")
        return _VirtualImageHandle(self, writable="+" in mode)

    def write(self, offset: int, data: bytes) -> None:
        if offset < 0 or offset + len(data) > self.file_size:
            raise ValueError("Virtual-image write is outside the source image")
        if data:
            self.writes.append((offset, bytes(data)))

    def __str__(self) -> str:
        return f"<virtual ISO over {self.source}>"


class _VirtualImageHandle:
    def __init__(self, image: _VirtualImage, *, writable: bool) -> None:
        self.image = image
        self.writable = writable
        self.position = 0
        self.base = image.source.open("rb")

    def __enter__(self) -> _VirtualImageHandle:
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def close(self) -> None:
        self.base.close()

    def flush(self) -> None:
        return None

    def fileno(self) -> int:
        raise io.UnsupportedOperation("virtual image has no file descriptor")

    def tell(self) -> int:
        return self.position

    def seek(self, offset: int, whence: int = os.SEEK_SET) -> int:
        if whence == os.SEEK_SET:
            position = offset
        elif whence == os.SEEK_CUR:
            position = self.position + offset
        elif whence == os.SEEK_END:
            position = self.image.file_size + offset
        else:
            raise ValueError(f"Unsupported seek origin: {whence}")
        if position < 0:
            raise ValueError("Negative virtual-image seek position")
        self.position = position
        return position

    def read(self, size: int = -1) -> bytes:
        if size < 0:
            size = max(0, self.image.file_size - self.position)
        else:
            size = min(size, max(0, self.image.file_size - self.position))
        start = self.position
        end = start + size
        self.base.seek(start)
        data = bytearray(self.base.read(size))
        actual_end = start + len(data)
        for write_offset, replacement in self.image.writes:
            write_end = write_offset + len(replacement)
            overlap_start = max(start, write_offset)
            overlap_end = min(actual_end, write_end)
            if overlap_start >= overlap_end:
                continue
            data[overlap_start - start:overlap_end - start] = replacement[
                overlap_start - write_offset:overlap_end - write_offset
            ]
        self.position = actual_end
        return bytes(data)

    def write(self, data: bytes | bytearray | memoryview) -> int:
        if not self.writable:
            raise io.UnsupportedOperation("virtual image is read-only")
        payload = bytes(data)
        self.image.write(self.position, payload)
        self.position += len(payload)
        return len(payload)


def _flush_image(handle: object) -> None:
    handle.flush()
    try:
        descriptor = handle.fileno()
    except (AttributeError, OSError, io.UnsupportedOperation):
        return
    os.fsync(descriptor)


def building_image_path(output_image: Path) -> Path:
    return output_image.with_name(output_image.name + ".building")


@contextmanager
def staged_output_image(source_image: Path, output_image: Path):
    """Copy a source image beside its destination and clean failed candidates."""
    output_image.parent.mkdir(parents=True, exist_ok=True)
    building_image = building_image_path(output_image)
    if source_image == building_image:
        raise ValueError("Source image cannot use the reserved .building output path")
    if building_image.exists() or building_image.is_symlink():
        if not building_image.is_file() and not building_image.is_symlink():
            raise RuntimeError(f"Temporary build path is not a file: {building_image}")
        building_image.unlink()

    print(f"Initializing temporary output: {building_image.name}")
    try:
        shutil.copyfile(source_image, building_image)
        yield building_image
    except BaseException:
        if building_image.exists() or building_image.is_symlink():
            building_image.unlink()
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

    with staged_output_image(source_image, output_image) as working_image:
        return _apply_and_verify_assembly(
            working_image,
            source,
            replacements,
            insertions,
            renames,
        )


def assemble_image_digest(
    source_image: Path,
    plan: AssemblyPlan,
) -> AssemblyDigestResult:
    """Verify an assembly in a sparse virtual image and stream its digest."""
    source_image = source_image.resolve()
    source, replacements, insertions, renames = _prepare_assembly(source_image, plan)
    working_image = _VirtualImage(source_image)
    assembly = _apply_and_verify_assembly(
        working_image,
        source,
        replacements,
        insertions,
        renames,
    )
    digest = hashlib.sha256()
    with working_image.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return AssemblyDigestResult(
        assembly=assembly,
        size_bytes=working_image.file_size,
        sha256=digest.hexdigest().upper(),
    )
