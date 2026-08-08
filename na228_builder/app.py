from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Callable, Iterable


RELEASE_MANIFEST_NAME = "release_manifest.json"
REQUIRED_IMAGE_IDS = ("na2", "nun5")
HASH_CHUNK_SIZE = 8 * 1024 * 1024

Emit = Callable[[str], None]
ReleaseBuilder = Callable[[Path, Path, Path, Emit], None]


class ReleaseError(RuntimeError):
    """A release failure that can be shown directly to an end user."""


@dataclass(frozen=True)
class SupportedImage:
    image_id: str
    label: str
    size: int
    sha256: str


@dataclass(frozen=True)
class ReleaseManifest:
    schema_version: int
    product_name: str
    product_version: str
    executable_name: str
    output_name: str
    configuration: str
    images: tuple[SupportedImage, ...]


def application_directory(
    *, executable: str | os.PathLike[str] | None = None
) -> Path:
    """Return the directory users perceive as containing the application.

    PyInstaller sets ``sys.frozen`` and points ``sys.executable`` at the
    packaged EXE. During source execution, use the repository root so
    ``python -m na228_builder.app`` remains predictable.
    """
    if executable is not None:
        return Path(executable).resolve().parent
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def _required_text(data: dict[str, object], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ReleaseError(f"Release manifest field {key!r} must be non-empty text")
    return value.strip()


def _validate_output_name(value: str) -> str:
    path = Path(value)
    if (
        path.is_absolute()
        or path.name != value
        or "/" in value
        or "\\" in value
        or value in {".", ".."}
    ):
        raise ReleaseError("Release output_name must be one filename")
    if path.suffix.casefold() != ".iso":
        raise ReleaseError("Release output_name must end in .iso")
    return value


def _validate_executable_name(value: str) -> str:
    path = Path(value)
    if (
        path.is_absolute()
        or path.name != value
        or "/" in value
        or "\\" in value
        or path.suffix.casefold() != ".exe"
    ):
        raise ReleaseError("Release executable_name must be one .exe filename")
    return value


def _validate_configuration(value: str) -> str:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ReleaseError("Release configuration must be a repository-relative path")
    return value.replace("\\", "/")


def parse_release_manifest(text: str) -> ReleaseManifest:
    try:
        data = json.loads(text)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ReleaseError("Release manifest is not valid JSON") from exc
    if not isinstance(data, dict):
        raise ReleaseError("Release manifest root must be an object")
    if data.get("schema_version") != 1:
        raise ReleaseError(
            f"Unsupported release manifest schema: {data.get('schema_version')!r}"
        )

    raw_images = data.get("images")
    if not isinstance(raw_images, list):
        raise ReleaseError("Release manifest images must be a list")

    images: list[SupportedImage] = []
    image_ids: set[str] = set()
    identities: set[tuple[int, str]] = set()
    for index, raw_image in enumerate(raw_images, 1):
        if not isinstance(raw_image, dict):
            raise ReleaseError(f"Release image {index} must be an object")
        image_id = _required_text(raw_image, "id").casefold()
        if not re.fullmatch(r"[a-z0-9_]+", image_id):
            raise ReleaseError(f"Release image {index} has an invalid id")
        if image_id in image_ids:
            raise ReleaseError(f"Duplicate release image id: {image_id}")

        label = _required_text(raw_image, "label")
        size = raw_image.get("size")
        if isinstance(size, bool) or not isinstance(size, int) or size <= 0:
            raise ReleaseError(
                f"Release image {image_id!r} size must be a positive integer"
            )
        digest = raw_image.get("sha256")
        if not isinstance(digest, str) or not re.fullmatch(
            r"[0-9A-Fa-f]{64}", digest
        ):
            raise ReleaseError(
                f"Release image {image_id!r} sha256 must be 64 hexadecimal digits"
            )
        digest = digest.upper()
        identity = (size, digest)
        if identity in identities:
            raise ReleaseError(
                "Release manifest assigns one ISO identity to multiple image ids"
            )

        image_ids.add(image_id)
        identities.add(identity)
        images.append(SupportedImage(image_id, label, size, digest))

    expected_ids = set(REQUIRED_IMAGE_IDS)
    if image_ids != expected_ids:
        missing = sorted(expected_ids - image_ids)
        extra = sorted(image_ids - expected_ids)
        details: list[str] = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if extra:
            details.append("unexpected " + ", ".join(extra))
        raise ReleaseError(
            "Release manifest must define exactly NA2 and NUN5 ("
            + "; ".join(details)
            + ")"
        )

    return ReleaseManifest(
        schema_version=1,
        product_name=_required_text(data, "product_name"),
        product_version=_required_text(data, "product_version"),
        executable_name=_validate_executable_name(
            _required_text(data, "executable_name")
        ),
        output_name=_validate_output_name(_required_text(data, "output_name")),
        configuration=_validate_configuration(
            _required_text(data, "configuration")
        ),
        images=tuple(images),
    )


def load_release_manifest() -> ReleaseManifest:
    try:
        resource = resources.files("na228_builder").joinpath(RELEASE_MANIFEST_NAME)
        text = resource.read_text(encoding="utf-8")
    except (FileNotFoundError, ModuleNotFoundError, OSError) as exc:
        raise ReleaseError(
            f"Packaged release data is missing: {RELEASE_MANIFEST_NAME}"
        ) from exc
    return parse_release_manifest(text)


def iso_candidates(directory: Path) -> list[Path]:
    try:
        entries = list(directory.iterdir())
    except OSError as exc:
        raise ReleaseError(f"Could not scan the application directory: {exc}") from exc
    candidates: list[Path] = []
    for path in entries:
        if path.suffix.casefold() != ".iso":
            continue
        try:
            is_file = path.is_file()
        except OSError as exc:
            raise ReleaseError(f"Could not inspect {path.name}: {exc}") from exc
        if is_file:
            candidates.append(path)
    return sorted(candidates, key=lambda path: (path.name.casefold(), path.name))


def file_sha256(
    path: Path,
    *,
    expected_size: int,
    emit: Emit,
    chunk_size: int = HASH_CHUNK_SIZE,
) -> str:
    digest = hashlib.sha256()
    processed = 0
    next_percentage = 10
    try:
        with path.open("rb") as source:
            while True:
                chunk = source.read(chunk_size)
                if not chunk:
                    break
                digest.update(chunk)
                processed += len(chunk)
                percentage = min(100, processed * 100 // expected_size)
                if percentage >= next_percentage:
                    emit(f"  {path.name}: {percentage}%")
                    next_percentage = (percentage // 10 + 1) * 10
    except OSError as exc:
        raise ReleaseError(f"Could not read {path.name}: {exc}") from exc
    if processed != expected_size:
        raise ReleaseError(
            f"{path.name} changed size while it was being checked; try again"
        )
    return digest.hexdigest().upper()


def identify_supported_images(
    directory: Path,
    images: Iterable[SupportedImage],
    *,
    emit: Emit = print,
) -> dict[str, Path]:
    specs = tuple(images)
    by_size: dict[int, list[SupportedImage]] = {}
    for image in specs:
        by_size.setdefault(image.size, []).append(image)

    candidates = iso_candidates(directory)
    emit(
        f"Found {len(candidates)} ISO file"
        f"{'s' if len(candidates) != 1 else ''} beside this program."
    )
    matches: dict[str, list[Path]] = {image.image_id: [] for image in specs}
    for path in candidates:
        try:
            size = path.stat().st_size
        except OSError as exc:
            raise ReleaseError(f"Could not inspect {path.name}: {exc}") from exc
        possible = by_size.get(size)
        if not possible:
            continue
        emit(f"Checking {path.name}...")
        digest = file_sha256(path, expected_size=size, emit=emit)
        matched = False
        for image in possible:
            if digest == image.sha256:
                matches[image.image_id].append(path)
                emit(f"[OK] {image.label}: {path.name}")
                matched = True
        if not matched:
            emit(f"Ignored {path.name}: hash is not supported.")

    selected: dict[str, Path] = {}
    problems: list[str] = []
    for image in specs:
        paths = matches[image.image_id]
        if not paths:
            problems.append(f"Could not find the supported {image.label}.")
        elif len(paths) > 1:
            names = ", ".join(path.name for path in paths)
            problems.append(
                f"Found multiple copies of the supported {image.label}: {names}."
            )
        else:
            selected[image.image_id] = paths[0]
    if problems:
        raise ReleaseError(
            " ".join(problems)
            + " Place exactly one supported NA2 ISO and one supported NUN5 ISO "
            "beside this program."
        )
    return selected


@contextmanager
def locked_input_files(paths: Iterable[Path]):
    """Prevent supported Windows inputs from being written or replaced."""
    ordered = tuple(dict.fromkeys(path.resolve() for path in paths))
    if os.name != "nt":
        handles = []
        try:
            handles = [path.open("rb") for path in ordered]
            yield
        except OSError as exc:
            raise ReleaseError(f"Could not hold the input ISOs open: {exc}") from exc
        finally:
            for handle in reversed(handles):
                handle.close()
        return

    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    )
    create_file.restype = wintypes.HANDLE
    close_handle = kernel32.CloseHandle
    close_handle.argtypes = (wintypes.HANDLE,)
    close_handle.restype = wintypes.BOOL

    generic_read = 0x80000000
    share_read = 0x00000001
    open_existing = 3
    sequential_scan = 0x08000000
    invalid_handle = wintypes.HANDLE(-1).value
    handles: list[int] = []
    try:
        for path in ordered:
            handle = create_file(
                str(path),
                generic_read,
                share_read,
                None,
                open_existing,
                sequential_scan,
                None,
            )
            if handle == invalid_handle:
                error = ctypes.WinError(ctypes.get_last_error())
                raise ReleaseError(
                    f"Could not lock {path.name} against changes: {error}"
                )
            handles.append(handle)
        yield
    finally:
        for handle in reversed(handles):
            close_handle(handle)


def verify_locked_images(
    selected: dict[str, Path],
    images: Iterable[SupportedImage],
    *,
    emit: Emit,
) -> None:
    """Recheck identities after the application has acquired input locks."""
    emit("Locking and rechecking the selected source ISOs...")
    for image in images:
        path = selected[image.image_id]
        try:
            size = path.stat().st_size
        except OSError as exc:
            raise ReleaseError(f"Could not recheck {path.name}: {exc}") from exc
        if size != image.size:
            raise ReleaseError(f"{path.name} changed after identification; try again")
        digest = file_sha256(path, expected_size=size, emit=emit)
        if digest != image.sha256:
            raise ReleaseError(f"{path.name} changed after identification; try again")


def _occupied(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def _remove_staging(path: Path) -> OSError | None:
    if not _occupied(path):
        return None
    try:
        path.unlink()
    except OSError as exc:
        return exc
    return None


def _runtime_builder(
    na2_iso: Path,
    nun5_iso: Path,
    building_iso: Path,
    emit: Emit,
) -> None:
    from .release_runtime import build_release_iso

    build_release_iso(na2_iso, nun5_iso, building_iso, emit)


def run_release(
    directory: Path,
    manifest: ReleaseManifest,
    builder: ReleaseBuilder,
    *,
    emit: Emit = print,
) -> Path:
    directory = directory.resolve()
    if not directory.is_dir():
        raise ReleaseError("The application directory is unavailable")

    output_iso = directory / manifest.output_name
    building_iso = output_iso.with_name(output_iso.name + ".building")
    if _occupied(output_iso):
        raise ReleaseError(
            f"Output already exists: {output_iso.name}. Move or rename it and try again."
        )
    if _occupied(building_iso):
        raise ReleaseError(
            f"Reserved temporary output already exists: {building_iso.name}. "
            "Remove it after confirming it is not needed, then try again."
        )

    emit(f"{manifest.product_name} {manifest.product_version}")
    emit("Scanning for supported ISO files...")
    selected = identify_supported_images(directory, manifest.images, emit=emit)
    try:
        with locked_input_files(selected.values()):
            verify_locked_images(selected, manifest.images, emit=emit)
            emit("Building NA2.28.iso...")
            builder(
                selected["na2"],
                selected["nun5"],
                building_iso,
                emit,
            )
        if building_iso.is_symlink() or not building_iso.is_file():
            raise ReleaseError("The build engine did not produce a verified ISO")
        na2_size = next(
            image.size for image in manifest.images if image.image_id == "na2"
        )
        actual_size = building_iso.stat().st_size
        if actual_size != na2_size:
            raise ReleaseError(
                "The built ISO has the wrong size "
                f"({actual_size} bytes; expected {na2_size})"
            )
        if _occupied(output_iso):
            raise ReleaseError(
                f"Output appeared during the build: {output_iso.name}; refusing to overwrite it"
            )
        os.rename(building_iso, output_iso)
    except BaseException as exc:
        cleanup_error = _remove_staging(building_iso)
        if cleanup_error is not None:
            raise ReleaseError(
                f"{exc} Temporary output cleanup also failed: {cleanup_error}"
            ) from exc
        raise

    emit("")
    emit(f"Build completed successfully: {output_iso.name}")
    return output_iso


def _pause(read: Callable[[str], str]) -> None:
    try:
        read("Press Enter to close.")
    except (EOFError, KeyboardInterrupt):
        pass


def main(
    *,
    directory: Path | None = None,
    manifest: ReleaseManifest | None = None,
    builder: ReleaseBuilder | None = None,
    emit: Emit = print,
    read: Callable[[str], str] = input,
) -> int:
    exit_code = 0
    try:
        release_manifest = manifest or load_release_manifest()
        run_release(
            directory or application_directory(),
            release_manifest,
            builder or _runtime_builder,
            emit=emit,
        )
    except KeyboardInterrupt:
        emit("")
        emit("Build cancelled.")
        exit_code = 1
    except Exception as exc:
        emit("")
        emit(f"Build failed: {exc}")
        exit_code = 1
    finally:
        emit("")
        _pause(read)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
