from __future__ import annotations

import argparse
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
from typing import Callable, Iterable, Sequence

from . import jsonc
from .configuration import validate_product_title


RELEASE_MANIFEST_NAME = "release_manifest.json"
HASH_CHUNK_SIZE = 8 * 1024 * 1024
ERROR_LOG_NAME = "builder-error.log"

Emit = Callable[[str], None]
ReleaseBuilder = Callable[[Path, Path, Path, Emit], None]
ReleaseConfigurationValidator = Callable[[Path], None]


class ReleaseError(RuntimeError):
    """A release failure that can be shown directly to an end user."""


@dataclass(frozen=True)
class SupportedImage:
    label: str
    size: int
    sha256: str


@dataclass(frozen=True)
class ReleaseManifest:
    product_name: str
    product_version: str
    output_name: str
    configuration: str
    configuration_name: str
    image: SupportedImage


def application_directory() -> Path:
    """Return the directory users perceive as containing the application.

    PyInstaller sets ``sys.frozen`` and points ``sys.executable`` at the
    packaged EXE. During source execution, use the repository root so
    ``python -m na228_builder.infrastructure.orchestration.app`` remains predictable.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def _required_text(data: dict[str, object], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ReleaseError(f"Release manifest field {key!r} must be non-empty text")
    return value.strip()


def _validate_file_name(value: str, field: str, suffix: str) -> str:
    path = Path(value)
    if (
        path.is_absolute()
        or path.name != value
        or "/" in value
        or "\\" in value
        or path.suffix.casefold() != suffix
    ):
        raise ReleaseError(f"Release {field} must be one {suffix} filename")
    return value


def _validate_configuration(value: str) -> str:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ReleaseError("Release configuration must be relative to the builder root")
    return value.replace("\\", "/")


def parse_release_manifest(text: str) -> ReleaseManifest:
    try:
        data = json.loads(text)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ReleaseError("Release manifest is not valid JSON") from exc
    if not isinstance(data, dict):
        raise ReleaseError("Release manifest root must be an object")
    raw_images = data.get("images")
    if (
        not isinstance(raw_images, list)
        or len(raw_images) != 1
        or not isinstance(raw_images[0], dict)
        or _required_text(raw_images[0], "id").casefold() != "na2"
    ):
        raise ReleaseError("Release manifest images must define exactly NA2")
    raw_image = raw_images[0]
    label = _required_text(raw_image, "label")
    size = raw_image.get("size")
    if isinstance(size, bool) or not isinstance(size, int) or size <= 0:
        raise ReleaseError("Release image size must be a positive integer")
    digest = raw_image.get("sha256")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9A-Fa-f]{64}", digest):
        raise ReleaseError("Release image sha256 must be 64 hexadecimal digits")

    try:
        product_name = validate_product_title(data.get("title"))
    except ValueError as exc:
        raise ReleaseError(str(exc)) from exc
    product_version = _required_text(data, "product_version")

    return ReleaseManifest(
        product_name=product_name,
        product_version=product_version,
        output_name=_validate_file_name(
            f"{product_name}_{product_version}.iso", "output_name", ".iso"
        ),
        configuration=_validate_configuration(
            _required_text(data, "configuration")
        ),
        configuration_name=_validate_file_name(
            _required_text(data, "configuration_name"), "configuration_name", ".jsonc"
        ),
        image=SupportedImage(label, size, digest.upper()),
    )


def load_release_manifest() -> ReleaseManifest:
    try:
        resource = resources.files("na228_builder").joinpath(
            "release", RELEASE_MANIFEST_NAME
        )
        text = resource.read_text(encoding="utf-8")
    except (FileNotFoundError, ModuleNotFoundError, OSError) as exc:
        raise ReleaseError(
            f"Packaged release data is missing: {RELEASE_MANIFEST_NAME}"
        ) from exc
    return parse_release_manifest(text)


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


def identify_supported_image(
    directory: Path,
    image: SupportedImage,
    *,
    ignored_names: Iterable[str] = (),
    allow_missing: bool = False,
    emit: Emit = print,
) -> Path | None:
    candidates = iso_candidates(directory, ignored_names=ignored_names)
    emit(
        f"Found {len(candidates)} ISO file"
        f"{'s' if len(candidates) != 1 else ''} beside this program."
    )
    matches: list[Path] = []
    for path in candidates:
        try:
            size = path.stat().st_size
        except OSError as exc:
            raise ReleaseError(f"Could not inspect {path.name}: {exc}") from exc
        if size != image.size:
            continue
        emit(f"Checking {path.name}...")
        if file_sha256(path, expected_size=size, emit=emit) == image.sha256:
            matches.append(path)
            emit(f"[OK] {image.label}: {path.name}")
        else:
            emit(f"Ignored {path.name}: hash is not supported.")

    if len(matches) > 1:
        names = ", ".join(path.name for path in matches)
        problem = f"Found multiple copies of the supported {image.label}: {names}."
    elif matches or allow_missing:
        return matches[0] if matches else None
    else:
        problem = f"Could not find the supported {image.label}."
    raise ReleaseError(
        f"{problem} Place exactly one supported {image.label} beside this program."
    )


def identify_input_iso(path: Path, image: SupportedImage, *, emit: Emit) -> Path:
    path = path.expanduser().resolve()
    if not path.is_file():
        raise ReleaseError(f"Source ISO does not exist: {path}")
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise ReleaseError(f"Could not inspect source ISO: {exc}") from exc
    if size != image.size:
        raise ReleaseError(f"{path.name} is not the supported {image.label} (wrong size)")
    emit(f"Checking {path.name}...")
    if file_sha256(path, expected_size=size, emit=emit) != image.sha256:
        raise ReleaseError(f"{path.name} is not the supported {image.label} (wrong hash)")
    emit(f"[OK] {image.label}: {path}")
    return path


def _prompt_source_iso(read: Callable[[str], str]) -> Path:
    supplied = read("Path to the clean NA2 ISO: ").strip()
    if len(supplied) >= 2 and supplied[0] == supplied[-1] == '"':
        supplied = supplied[1:-1]
    if not supplied:
        raise ReleaseError("No source ISO was provided")
    return Path(supplied)


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


def verify_locked_image(path: Path, image: SupportedImage, *, emit: Emit) -> None:
    """Recheck the identity after the application has acquired the input lock."""
    emit("Locking and rechecking the selected source ISOs...")
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise ReleaseError(f"Could not recheck {path.name}: {exc}") from exc
    if (
        size != image.size
        or file_sha256(path, expected_size=size, emit=emit) != image.sha256
    ):
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
    configuration_path: Path,
    building_iso: Path,
    emit: Emit,
) -> None:
    from .release_runtime import build_release_iso

    build_release_iso(na2_iso, configuration_path, building_iso, emit)


def _runtime_configuration_validator(configuration_path: Path) -> None:
    from .release_runtime import validate_release_configuration

    try:
        validate_release_configuration(configuration_path)
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
    input_iso: Path | None = None,
    output_directory: Path | None = None,
    emit: Emit = print,
    read: Callable[[str], str] = input,
) -> Path:
    directory = directory.resolve()
    if not directory.is_dir():
        raise ReleaseError("The application directory is unavailable")

    destination = (output_directory or directory).expanduser().resolve()
    if destination.exists() and not destination.is_dir():
        raise ReleaseError(f"Output folder is not a directory: {destination}")
    output_iso = destination / manifest.output_name
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
    if configuration_validator is not None:
        configuration_validator(configuration_path)
    image = manifest.image
    source: Path | None = None
    if input_iso is None:
        emit("Scanning for supported ISO files...")
        source = identify_supported_image(
            directory,
            image,
            ignored_names=(manifest.output_name, building_iso.name),
            allow_missing=True,
            emit=emit,
        )
        if source is None:
            emit("No supported NA2 ISO was found beside this program.")
            input_iso = _prompt_source_iso(read)
    if input_iso is not None:
        source = identify_input_iso(input_iso, image, emit=emit)
    if source == output_iso.resolve():
        raise ReleaseError("The source and output ISO paths must differ")
    try:
        with locked_input_files((source,)):
            verify_locked_image(source, image, emit=emit)
            destination.mkdir(parents=True, exist_ok=True)
            emit(f"Building {manifest.output_name}...")
            builder(source, configuration_path, building_iso, emit)
        if building_iso.is_symlink() or not building_iso.is_file():
            raise ReleaseError("The build engine did not produce a verified ISO")
        actual_size = building_iso.stat().st_size
        if actual_size != image.size:
            raise ReleaseError(
                "The built ISO has the wrong size "
                f"({actual_size} bytes; expected {image.size})"
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
    argv: Sequence[str] = (),
    directory: Path | None = None,
    manifest: ReleaseManifest | None = None,
    builder: ReleaseBuilder | None = None,
    configuration_validator: ReleaseConfigurationValidator | None = None,
    emit: Emit = print,
    read: Callable[[str], str] = input,
) -> int:
    parser = argparse.ArgumentParser(
        description="Build a patched ISO from a supported clean NA2 ISO."
    )
    parser.add_argument(
        "--input", type=Path, metavar="ISO", help="path to the clean NA2 ISO"
    )
    parser.add_argument(
        "--output",
        type=Path,
        metavar="FOLDER",
        help="folder for the patched ISO (default: folder containing the EXE)",
    )
    arguments = parser.parse_args(argv)
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
            input_iso=arguments.input,
            output_directory=arguments.output,
            emit=report,
            read=read,
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
        if not argv:
            _pause(read)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main(argv=sys.argv[1:]))
