from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import traceback
from contextlib import contextmanager
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

from . import jsonc
from typing import Callable, Iterable


RELEASE_MANIFEST_NAME = "release_manifest.json"
SETTINGS_NAME = "game.json"
REQUIRED_IMAGE_IDS = ("na2", "nun5")
HASH_CHUNK_SIZE = 8 * 1024 * 1024
ERROR_LOG_NAME = "builder-error.log"

Emit = Callable[[str], None]
ReleaseBuilder = Callable[[Path, Path | None, Path, Path, Emit], None]
ReleaseConfigurationValidator = Callable[[Path], Iterable[str] | None]


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
    product_name: str
    product_version: str
    executable_name: str
    output_name: str
    configuration: str
    configuration_name: str
    images: tuple[SupportedImage, ...]


def application_directory(
    *, executable: str | os.PathLike[str] | None = None
) -> Path:
    """Return the directory users perceive as containing the application.

    PyInstaller sets ``sys.frozen`` and points ``sys.executable`` at the
    packaged EXE. During source execution, use the repository root so
    ``python -m na228_builder.scripts.app`` remains predictable.
    """
    if executable is not None:
        return Path(executable).resolve().parent
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


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


def _validate_configuration_name(value: str) -> str:
    path = Path(value)
    if (
        path.is_absolute()
        or path.name != value
        or "/" in value
        or "\\" in value
        or path.suffix.casefold() != ".jsonc"
    ):
        raise ReleaseError("Release configuration_name must be one .jsonc filename")
    return value


def parse_release_manifest(text: str, *, product_name: str) -> ReleaseManifest:
    try:
        data = json.loads(text)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ReleaseError("Release manifest is not valid JSON") from exc
    if not isinstance(data, dict):
        raise ReleaseError("Release manifest root must be an object")
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

    if not isinstance(product_name, str) or not product_name.strip():
        raise ReleaseError("Product title must be non-empty text")
    product_name = product_name.strip()
    product_version = _required_text(data, "product_version")

    return ReleaseManifest(
        product_name=product_name,
        product_version=product_version,
        executable_name=_validate_executable_name(
            f"{product_name}_{product_version}.exe"
        ),
        output_name=_validate_output_name(f"{product_name}.iso"),
        configuration=_validate_configuration(
            _required_text(data, "configuration")
        ),
        configuration_name=_validate_configuration_name(
            _required_text(data, "configuration_name")
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
    settings_path = Path(__file__).resolve().parents[2] / SETTINGS_NAME
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError) as exc:
        raise ReleaseError(
            f"Packaged release data is missing or invalid: {SETTINGS_NAME}"
        ) from exc
    if not isinstance(settings, dict):
        raise ReleaseError("Settings root must be an object")
    return parse_release_manifest(text, product_name=settings.get("title"))


def iso_candidates(
    directory: Path,
    *,
    ignored_names: Iterable[str] = (),
) -> list[Path]:
    try:
        entries = list(directory.iterdir())
    except OSError as exc:
        raise ReleaseError(f"Could not scan the application directory: {exc}") from exc
    ignored = {name.casefold() for name in ignored_names}
    candidates: list[Path] = []
    for path in entries:
        if path.suffix.casefold() != ".iso" or path.name.casefold() in ignored:
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
    ignored_names: Iterable[str] = (),
    emit: Emit = print,
) -> dict[str, Path]:
    specs = tuple(images)
    by_size: dict[int, list[SupportedImage]] = {}
    for image in specs:
        by_size.setdefault(image.size, []).append(image)

    candidates = iso_candidates(directory, ignored_names=ignored_names)
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
        labels = [image.label for image in specs]
        required = (
            labels[0]
            if len(labels) == 1
            else ", ".join(labels[:-1]) + f" and {labels[-1]}"
        )
        raise ReleaseError(
            " ".join(problems)
            + f" Place exactly one supported {required} beside this program."
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
    nun5_iso: Path | None,
    configuration_path: Path,
    building_iso: Path,
    emit: Emit,
) -> None:
    from .release_runtime import build_release_iso

    build_release_iso(na2_iso, nun5_iso, configuration_path, building_iso, emit)


def _runtime_configuration_validator(configuration_path: Path) -> tuple[str, ...]:
    from .release_runtime import validate_release_configuration

    try:
        return validate_release_configuration(configuration_path)
    except ReleaseError:
        raise
    except Exception as exc:
        raise ReleaseError(f"Invalid build configuration: {exc}") from exc


def _validate_user_configuration(configuration_path: Path) -> None:
    if not configuration_path.is_file():
        raise ReleaseError(
            f"Configuration is missing: {configuration_path.name}. "
            "Keep the JSONC file supplied with this program beside the EXE."
        )
    try:
        value = jsonc.loads(configuration_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ReleaseError(
            f"{configuration_path.name} is not valid JSONC at line {exc.lineno}, "
            f"column {exc.colno}: {exc.msg}"
        ) from exc
    except (OSError, UnicodeError) as exc:
        raise ReleaseError(
            f"Could not read {configuration_path.name}: {exc}"
        ) from exc
    if not isinstance(value, dict):
        raise ReleaseError(
            f"Invalid config value at the root: got {type(value).__name__}; "
            "expected an object"
        )


def run_release(
    directory: Path,
    manifest: ReleaseManifest,
    builder: ReleaseBuilder,
    *,
    configuration_validator: ReleaseConfigurationValidator | None = None,
    emit: Emit = print,
) -> Path:
    directory = directory.resolve()
    if not directory.is_dir():
        raise ReleaseError("The application directory is unavailable")

    output_iso = directory / manifest.output_name
    building_iso = output_iso.with_name(output_iso.name + ".building")
    configuration_path = directory / manifest.configuration_name
    if _occupied(building_iso):
        raise ReleaseError(
            f"Reserved temporary output already exists: {building_iso.name}. "
            "Remove it after confirming it is not needed, then try again."
        )

    emit(f"{manifest.product_name} {manifest.product_version}")
    emit(f"Loading {configuration_path.name}...")
    _validate_user_configuration(configuration_path)
    required_image_ids: tuple[str, ...] | None = None
    if configuration_validator is not None:
        validated_ids = configuration_validator(configuration_path)
        if validated_ids is not None:
            required_image_ids = tuple(validated_ids)
    if required_image_ids is None:
        required_image_ids = tuple(image.image_id for image in manifest.images)
    if "na2" not in required_image_ids:
        raise ReleaseError("Release configuration must require the NA2 source ISO")
    if len(required_image_ids) != len(set(required_image_ids)):
        raise ReleaseError("Release configuration returned duplicate source image ids")
    images_by_id = {image.image_id: image for image in manifest.images}
    unknown_ids = sorted(set(required_image_ids) - set(images_by_id))
    if unknown_ids:
        raise ReleaseError(
            "Release configuration requires unknown source image ids: "
            + ", ".join(unknown_ids)
        )
    required_images = tuple(images_by_id[image_id] for image_id in required_image_ids)
    emit("Scanning for supported ISO files...")
    selected = identify_supported_images(
        directory,
        required_images,
        ignored_names=(manifest.output_name, building_iso.name),
        emit=emit,
    )
    try:
        with locked_input_files(selected.values()):
            verify_locked_images(selected, required_images, emit=emit)
            emit(f"Building {manifest.output_name}...")
            builder(
                selected["na2"],
                selected.get("nun5"),
                configuration_path,
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
        os.replace(building_iso, output_iso)
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


def _write_error_log(
    path: Path,
    messages: Iterable[str],
    *,
    failure: BaseException,
) -> None:
    lines = [
        "Outcome: failed",
        "",
        *messages,
        "",
        "Technical details:",
        "".join(
            traceback.format_exception(
                type(failure), failure, failure.__traceback__
            )
        ).rstrip(),
    ]
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main(
    *,
    directory: Path | None = None,
    manifest: ReleaseManifest | None = None,
    builder: ReleaseBuilder | None = None,
    configuration_validator: ReleaseConfigurationValidator | None = None,
    emit: Emit = print,
    read: Callable[[str], str] = input,
) -> int:
    exit_code = 0
    failure: BaseException | None = None
    outcome = "success"
    messages: list[str] = []

    def report(message: str) -> None:
        messages.append(message)
        emit(message)

    release_directory = (directory or application_directory()).resolve()
    try:
        release_manifest = manifest or load_release_manifest()
        selected_builder = builder or _runtime_builder
        selected_validator = configuration_validator
        if builder is None and selected_validator is None:
            selected_validator = _runtime_configuration_validator
        run_release(
            release_directory,
            release_manifest,
            selected_builder,
            configuration_validator=selected_validator,
            emit=report,
        )
    except KeyboardInterrupt as exc:
        failure = exc
        outcome = "cancelled"
        report("")
        report("Build cancelled.")
        exit_code = 1
    except Exception as exc:
        failure = exc
        outcome = "failed"
        report("")
        report(f"Build failed: {exc}")
        exit_code = 1
    finally:
        if failure is not None and outcome == "failed":
            log_path = release_directory / ERROR_LOG_NAME
            try:
                _write_error_log(log_path, messages, failure=failure)
            except (OSError, UnicodeError) as log_error:
                report(f"Could not write {ERROR_LOG_NAME}: {log_error}")
            else:
                report(f"Technical details: {ERROR_LOG_NAME}")
        report("")
        _pause(read)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
