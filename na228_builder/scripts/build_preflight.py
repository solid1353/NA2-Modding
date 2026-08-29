from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import time
import zlib
from datetime import datetime, timezone
from pathlib import Path

from .configuration import configuration_resource_files, load_configuration
from scripts.lib.paths import load_paths


REGISTRY_SCHEMA_VERSION = 2
FINGERPRINT_SCHEMA_VERSION = 11
SHA256_HEX_LENGTH = 64
MAX_ENTRIES = 15
MAX_LOCATIONS_PER_IMAGE = 20
ROLE_FILE_NAMES = ("latest_iso", "previous_iso", "manual_iso")
GENERATED_SUFFIXES = {".pyc", ".pyo"}
NON_COMPOSING_BUILDER_FILES = {
    "scripts/app.py",
    "scripts/build_preflight.py",
    "release_manifest.json",
    "scripts/release_runtime.py",
}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def bytes_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def state_fingerprint(state: dict[str, object]) -> str:
    return bytes_sha256(canonical_json(state))


def _valid_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == SHA256_HEX_LENGTH
        and all(character in "0123456789ABCDEF" for character in value)
    )


def _file_entry(label: str, path: Path) -> dict[str, object]:
    if not path.is_file():
        raise FileNotFoundError(path)
    return {
        "label": label,
        "size": path.stat().st_size,
        "sha256": file_sha256(path),
    }


def _builder_files(builder: Path) -> list[Path]:
    if not builder.is_dir():
        raise FileNotFoundError(builder)
    return sorted(
        (
            path
            for path in builder.rglob("*")
            if path.is_file()
            and "__pycache__" not in path.relative_to(builder).parts
            and path.suffix.casefold() not in GENERATED_SUFFIXES
            and path.suffix.casefold() == ".py"
            and path.relative_to(builder).as_posix()
            not in NON_COMPOSING_BUILDER_FILES
        ),
        key=lambda path: path.relative_to(builder).as_posix(),
    )


def builder_tree_entry(builder: Path) -> dict[str, object]:
    digest = hashlib.sha256()
    files = _builder_files(builder)
    if not files:
        raise ValueError("na228_builder contains no fingerprintable files")
    total_size = 0
    for path in files:
        relative = path.relative_to(builder).as_posix()
        size = path.stat().st_size
        total_size += size
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(size).encode("ascii"))
        digest.update(b"\0")
        digest.update(file_sha256(path).encode("ascii"))
        digest.update(b"\n")
    return {
        "label": "na228_builder",
        "file_count": len(files),
        "size": total_size,
        "sha256": digest.hexdigest().upper(),
    }


def configuration_resources_entry(
    workspace: Path,
    configuration_path: Path,
) -> dict[str, object]:
    paths = load_paths(workspace)
    configuration = load_configuration(
        configuration_path,
        workspace,
        paths.path("builder"),
        project_paths=paths,
    )
    files = sorted(
        set(configuration_resource_files(configuration)) | {paths.manifest},
        key=lambda path: path.as_posix(),
    )
    digest = hashlib.sha256()
    total_size = 0
    for path in files:
        if not path.is_file():
            raise FileNotFoundError(path)
        try:
            relative = path.resolve().relative_to(workspace).as_posix()
        except ValueError as error:
            raise ValueError(
                f"Configuration resource is outside the repository: {path}"
            ) from error
        if path.suffix.casefold() == ".md":
            size = 0
            content_hash = "STRUCTURAL-PRESENCE-ONLY"
        else:
            size = path.stat().st_size
            content_hash = file_sha256(path)
            total_size += size
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(size).encode("ascii"))
        digest.update(b"\0")
        digest.update(content_hash.encode("ascii"))
        digest.update(b"\n")
    return {
        "label": "configuration_resources",
        "file_count": len(files),
        "size": total_size,
        "sha256": digest.hexdigest().upper(),
        "uses_ee_compiler": any(path.suffix in {".c", ".S"} for path in files),
    }


def ee_toolchain_entry(workspace: Path) -> dict[str, object]:
    paths = load_paths(workspace)
    ee_root = paths.path("ps2_msys", "1.0", "local", "ps2dev", "ee")
    discovered = {
        "bin/ee-gcc.exe": ee_root / "bin" / "ee-gcc.exe",
        "bin/ee-as.exe": ee_root / "bin" / "ee-as.exe",
    }
    for name in ("cc1.exe", "specs"):
        matches = sorted((ee_root / "lib" / "gcc-lib" / "ee").glob(f"*/{name}"))
        if len(matches) != 1:
            raise ValueError(
                f"Expected exactly one EE compiler {name}, found {len(matches)}"
            )
        discovered[matches[0].relative_to(ee_root).as_posix()] = matches[0]
    digest = hashlib.sha256()
    total_size = 0
    for relative, path in sorted(discovered.items()):
        if not path.is_file():
            raise FileNotFoundError(path)
        size = path.stat().st_size
        total_size += size
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(size).encode("ascii"))
        digest.update(b"\0")
        digest.update(file_sha256(path).encode("ascii"))
        digest.update(b"\n")
    return {
        "label": "ee_toolchain",
        "file_count": len(discovered),
        "size": total_size,
        "sha256": digest.hexdigest().upper(),
    }


def dependency_versions() -> dict[str, str]:
    try:
        zopfli_version = importlib.metadata.version("zopfli")
    except importlib.metadata.PackageNotFoundError:
        zopfli_version = "missing"
    return {
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "zlib_compile_version": zlib.ZLIB_VERSION,
        "zlib_runtime_version": zlib.ZLIB_RUNTIME_VERSION,
        "zopfli_version": zopfli_version,
    }


def collect_build_state(
    *,
    workspace: Path,
    na2_iso: Path,
    nun5_iso: Path,
    configuration_path: Path,
    dependencies: dict[str, str] | None = None,
) -> dict[str, object]:
    workspace = workspace.resolve()
    na2_iso = na2_iso.resolve()
    nun5_iso = nun5_iso.resolve()
    configuration_path = configuration_path.resolve()
    builder = load_paths(workspace).path("builder").resolve()
    try:
        configuration_name = configuration_path.relative_to(builder).as_posix()
    except ValueError as error:
        raise ValueError("Configuration must be inside na228_builder") from error
    if not configuration_path.is_file():
        raise FileNotFoundError(configuration_path)
    resources = configuration_resources_entry(workspace, configuration_path)
    state = {
        "fingerprint_schema_version": FINGERPRINT_SCHEMA_VERSION,
        "source_isos": [
            _file_entry(f"source/{na2_iso.name}", na2_iso),
            _file_entry(f"source/{nun5_iso.name}", nun5_iso),
        ],
        "builder_tree": builder_tree_entry(builder),
        "configuration_resources": resources,
        "configuration": configuration_name,
        "dependencies": dependencies if dependencies is not None else dependency_versions(),
    }
    if resources["uses_ee_compiler"]:
        state["ee_toolchain"] = ee_toolchain_entry(workspace)
    return state


def _empty_registry() -> dict[str, object]:
    return {
        "schema_version": REGISTRY_SCHEMA_VERSION,
        "entries": {},
        "images": {},
    }


def _read_registry(path: Path) -> dict[str, object]:
    if not path.is_file():
        return _empty_registry()
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("verification registry has an invalid structure")
    if (
        value.get("schema_version") != REGISTRY_SCHEMA_VERSION
        or not isinstance(value.get("entries"), dict)
        or not isinstance(value.get("images"), dict)
    ):
        raise ValueError("verification registry has an invalid structure")
    return {
        "schema_version": REGISTRY_SCHEMA_VERSION,
        "entries": value["entries"],
        "images": value["images"],
    }


def _write_registry(path: Path, registry: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(registry, handle, indent=2, ensure_ascii=True, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


@contextlib.contextmanager
def _registry_lock(registry_path: Path):
    lock_path = registry_path.with_suffix(registry_path.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as handle:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"\0")
            handle.flush()
        deadline = time.monotonic() + 120
        while True:
            try:
                if os.name == "nt":
                    import msvcrt

                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"Timed out waiting for registry lock: {lock_path}")
                time.sleep(0.1)
        try:
            yield
        finally:
            if os.name == "nt":
                import msvcrt

                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _relative_workspace_path(path: Path, workspace: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(workspace.resolve()).as_posix()
    except ValueError as error:
        raise ValueError(f"Registry path is outside the repository: {path}") from error


def _valid_image(path: Path, size: int, sha256: str) -> bool:
    try:
        return (
            path.is_file()
            and path.stat().st_size == size
            and file_sha256(path) == sha256
        )
    except OSError:
        return False


def _entry_image(
    entry: dict[str, object],
    images: dict[str, object],
    workspace: Path,
    cache_root: Path,
) -> Path | None:
    sha256 = entry.get("sha256")
    if not _valid_sha256(sha256):
        return None
    image = images.get(sha256)
    if not isinstance(image, dict):
        return None
    size = image.get("size")
    if not isinstance(size, int) or size < 0:
        return None
    cache_image = cache_root / f"{sha256}.iso"
    if _valid_image(cache_image, size, sha256):
        return cache_image.resolve()
    locations = image.get("locations", [])
    if not isinstance(locations, list):
        return None
    for raw_location in locations:
        if not isinstance(raw_location, str):
            continue
        location = (workspace / raw_location).resolve()
        if workspace.resolve() not in location.parents:
            continue
        if _valid_image(location, size, sha256):
            return location
    return None


def lookup_registry(
    *,
    workspace: Path,
    registry_path: Path,
    cache_root: Path,
    state: dict[str, object],
) -> dict[str, object]:
    fingerprint = state_fingerprint(state)
    try:
        registry = _read_registry(registry_path)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return {
            "status": "miss",
            "reason": "registry-invalid",
            "detail": str(error),
            "fingerprint": fingerprint,
        }
    entry = registry["entries"].get(fingerprint)
    if not isinstance(entry, dict) or entry.get("state") != state:
        return {
            "status": "miss",
            "reason": "fingerprint-missing",
            "fingerprint": fingerprint,
        }
    sha256 = entry.get("sha256")
    images = registry["images"]
    image_record = images.get(sha256) if isinstance(images, dict) else None
    size = image_record.get("size") if isinstance(image_record, dict) else None
    if not isinstance(size, int) or size < 0 or not _valid_sha256(sha256):
        return {
            "status": "miss",
            "reason": "entry-invalid",
            "fingerprint": fingerprint,
        }
    image = _entry_image(entry, images, workspace, cache_root)
    if image is None:
        return {
            "status": "miss",
            "reason": "physical-image-missing",
            "fingerprint": fingerprint,
            "output_size_bytes": size,
            "output_sha256": sha256,
        }
    provenance = registry_path.parent / "records" / fingerprint
    result: dict[str, object] = {
        "status": "hit",
        "reason": "verified-build-match",
        "fingerprint": fingerprint,
        "output_size_bytes": size,
        "output_sha256": sha256,
    }
    if image is not None:
        result["image"] = str(image)
    if provenance.is_dir():
        result["provenance"] = str(provenance.resolve())
    return result


def _copy_provenance(source: Path, destination: Path) -> None:
    if not source.is_dir():
        raise FileNotFoundError(source)
    temporary = destination.with_name(f".{destination.name}.{os.getpid()}.tmp")
    if temporary.exists():
        shutil.rmtree(temporary)
    shutil.copytree(source, temporary)
    if destination.exists():
        shutil.rmtree(destination)
    os.replace(temporary, destination)


def _replace_with_hardlink(source: Path, destination: Path) -> None:
    source = source.resolve()
    destination = destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.{os.getpid()}.tmp")
    try:
        if temporary.exists():
            temporary.unlink()
        os.link(source, temporary)
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()


def _configured_role_paths(workspace: Path) -> dict[str, Path]:
    try:
        paths = load_paths(workspace, allow_missing=True)
    except (OSError, ValueError, KeyError):
        return {}
    result: dict[str, Path] = {}
    for name in ROLE_FILE_NAMES:
        try:
            role_path = paths.file(name).resolve()
            relative = _relative_workspace_path(role_path, workspace)
        except (KeyError, ValueError):
            continue
        result[relative] = role_path
    return result


def _ensure_role_cache_hardlinks(
    registry: dict[str, object], workspace: Path, cache_root: Path
) -> set[str]:
    images = registry["images"]
    assert isinstance(images, dict)
    role_paths = _configured_role_paths(workspace)
    protected: set[str] = set()
    for sha256, image in images.items():
        if not _valid_sha256(sha256) or not isinstance(image, dict):
            continue
        size = image.get("size")
        locations = image.get("locations")
        if not isinstance(size, int) or size < 0 or not isinstance(locations, list):
            continue
        for relative, role_path in role_paths.items():
            if relative not in locations or not role_path.is_file():
                continue
            cache_image = cache_root / f"{sha256}.iso"
            try:
                if cache_image.is_file() and os.path.samefile(role_path, cache_image):
                    protected.add(sha256)
                    break
            except OSError:
                pass
            if not _valid_image(role_path, size, sha256):
                continue
            if cache_image.is_file():
                if not _valid_image(cache_image, size, sha256):
                    _replace_with_hardlink(role_path, cache_image)
                _replace_with_hardlink(cache_image, role_path)
            else:
                _replace_with_hardlink(role_path, cache_image)
            if not os.path.samefile(role_path, cache_image):
                raise RuntimeError(
                    f"Role ISO is not linked to its canonical cache image: {role_path}"
                )
            protected.add(sha256)
            break
    return protected


def _prune_registry(
    registry: dict[str, object], workspace: Path, cache_root: Path
) -> list[tuple[str, dict[str, object]]]:
    entries = registry["entries"]
    assert isinstance(entries, dict)
    protected_hashes = _ensure_role_cache_hardlinks(
        registry, workspace, cache_root
    )
    candidates = sorted(
        (
            (fingerprint, entry)
            for fingerprint, entry in entries.items()
            if isinstance(entry, dict)
        ),
        key=lambda item: str(item[1].get("verified_utc", "")),
    )
    removed: list[tuple[str, dict[str, object]]] = []
    while len(entries) > MAX_ENTRIES and candidates:
        fingerprint, entry = candidates.pop(0)
        if fingerprint not in entries:
            continue
        del entries[fingerprint]
        removed.append((fingerprint, entry))

    def retained_hashes() -> set[str]:
        return {
            sha256
            for entry in entries.values()
            if isinstance(entry, dict)
            and _valid_sha256(sha256 := entry.get("sha256"))
        }

    required_hashes = retained_hashes() | protected_hashes
    while len(required_hashes) > MAX_ENTRIES:
        candidate = next(
            (
                (fingerprint, entry)
                for fingerprint, entry in candidates
                if fingerprint in entries
                and entry.get("sha256") not in protected_hashes
            ),
            None,
        )
        if candidate is None:
            break
        fingerprint, entry = candidate
        del entries[fingerprint]
        removed.append((fingerprint, entry))
        required_hashes = retained_hashes() | protected_hashes

    registry["images"] = {
        sha256: image
        for sha256, image in registry["images"].items()
        if sha256 in required_hashes
    }
    return removed


def _cleanup_registry_artifacts(
    registry: dict[str, object], registry_path: Path, cache_root: Path
) -> None:
    entries = registry["entries"]
    assert isinstance(entries, dict)
    retained_fingerprints = set(entries)
    retained_hashes = set(registry["images"])
    records_root = registry_path.parent / "records"
    if records_root.is_dir():
        for record in records_root.iterdir():
            if record.is_dir() and record.name not in retained_fingerprints:
                try:
                    shutil.rmtree(record)
                except OSError:
                    pass
    if cache_root.is_dir():
        for image in cache_root.glob("*.iso"):
            if image.stem not in retained_hashes:
                try:
                    image.unlink()
                except OSError:
                    pass


def _cleanup_cache_temporaries(cache_root: Path) -> None:
    if not cache_root.is_dir():
        return
    for temporary in cache_root.glob(".*.tmp"):
        if temporary.is_file():
            try:
                temporary.unlink()
            except OSError:
                pass


def record_registry(
    *,
    workspace: Path,
    registry_path: Path,
    cache_root: Path,
    state: dict[str, object],
    expected_fingerprint: str,
    image: Path,
    provenance: Path | None,
) -> dict[str, object]:
    fingerprint = state_fingerprint(state)
    if fingerprint != expected_fingerprint:
        return {
            "status": "skipped",
            "reason": "inputs-changed-during-build",
            "fingerprint": fingerprint,
        }
    image = image.resolve()
    if not image.is_file():
        return {"status": "skipped", "reason": "output-iso-missing"}
    size = image.stat().st_size
    sha256 = file_sha256(image)
    cache_image: Path | None = None
    cache_image_preexisting = False

    with _registry_lock(registry_path):
        try:
            _cleanup_cache_temporaries(cache_root)
            registry = _read_registry(registry_path)
            record_directory = registry_path.parent / "records" / fingerprint
            if provenance is not None:
                record_directory.parent.mkdir(parents=True, exist_ok=True)
                _copy_provenance(provenance.resolve(), record_directory)
            cache_root.mkdir(parents=True, exist_ok=True)
            cache_image = cache_root / f"{sha256}.iso"
            if cache_image.exists():
                cache_image_preexisting = True
                if not _valid_image(cache_image, size, sha256):
                    raise RuntimeError(f"Cached ISO identity mismatch: {cache_image}")
                image.unlink()
            else:
                os.replace(image, cache_image)
            existing = registry["entries"].get(fingerprint)
            images = registry["images"]
            assert isinstance(images, dict)
            existing_image = images.get(sha256)
            if isinstance(existing_image, dict):
                if existing_image.get("size") != size:
                    raise RuntimeError(
                        f"Registry image identity has inconsistent sizes: {sha256}"
                    )
            else:
                images[sha256] = {"size": size, "locations": []}
            registry["entries"][fingerprint] = {
                "state": state,
                "sha256": sha256,
                "verified_utc": datetime.now(timezone.utc).isoformat(),
            }
            _prune_registry(registry, workspace, cache_root)
            _write_registry(registry_path, registry)
            _cleanup_registry_artifacts(registry, registry_path, cache_root)
        except BaseException:
            if (
                not image.exists()
                and cache_image is not None
                and cache_image.is_file()
            ):
                image.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(cache_image, image)
                if not cache_image_preexisting:
                    try:
                        cache_image.unlink()
                    except OSError:
                        pass
            raise
    result: dict[str, object] = {
        "status": "recorded",
        "reason": "verified-build-recorded",
        "fingerprint": fingerprint,
        "output_size_bytes": size,
        "output_sha256": sha256,
    }
    if cache_image is not None:
        result["image"] = str(cache_image.resolve())
    if (registry_path.parent / "records" / fingerprint).is_dir():
        result["provenance"] = str(
            (registry_path.parent / "records" / fingerprint).resolve()
        )
    return result


def record_locations(
    *,
    workspace: Path,
    registry_path: Path,
    cache_root: Path,
    fingerprint: str,
    locations: list[Path],
) -> dict[str, object]:
    with _registry_lock(registry_path):
        _cleanup_cache_temporaries(cache_root)
        registry = _read_registry(registry_path)
        entry = registry["entries"].get(fingerprint)
        if not isinstance(entry, dict):
            raise ValueError(f"Unknown verification fingerprint: {fingerprint}")
        images = registry["images"]
        assert isinstance(images, dict)
        if not locations:
            raise ValueError("At least one completed location is required")
        target_sha256 = entry.get("sha256")
        target_image = images.get(target_sha256)
        if not _valid_sha256(target_sha256) or not isinstance(target_image, dict):
            raise ValueError(f"Unknown registry image identity: {target_sha256}")
        observed: list[tuple[str, int, str]] = []
        for index, location in enumerate(locations):
            relative = _relative_workspace_path(location, workspace)
            if not location.is_file():
                raise RuntimeError(f"Promoted ISO does not exist: {location}")
            size = location.stat().st_size
            sha256 = file_sha256(location)
            if index == 0 and (
                sha256 != target_sha256 or size != target_image.get("size")
            ):
                raise RuntimeError(f"Promoted ISO identity mismatch: {location}")
            observed.append((relative, size, sha256))

        for image in images.values():
            if not isinstance(image, dict):
                continue
            image_locations = image.get("locations")
            if not isinstance(image_locations, list):
                continue
            image_locations[:] = [
                raw_location
                for raw_location in image_locations
                if isinstance(raw_location, str)
                and (workspace / raw_location).is_file()
                and all(raw_location != relative for relative, _, _ in observed)
            ]

        for relative, size, sha256 in observed:
            image = images.get(sha256)
            if not isinstance(image, dict):
                continue
            if image.get("size") != size:
                raise RuntimeError(
                    f"Registry image identity has inconsistent sizes: {sha256}"
                )
            image_locations = image.setdefault("locations", [])
            if not isinstance(image_locations, list):
                raise ValueError(f"Registry image locations are invalid: {sha256}")
            if relative not in image_locations:
                image_locations.append(relative)
            if len(image_locations) > MAX_LOCATIONS_PER_IMAGE:
                del image_locations[:-MAX_LOCATIONS_PER_IMAGE]
        _write_registry(registry_path, registry)
    return {
        "status": "completed",
        "fingerprint": fingerprint,
    }


def _configuration_path(value: Path, workspace: Path) -> Path:
    return value if value.is_absolute() else workspace / value


def _emit(value: dict[str, object]) -> None:
    print(json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Query and update the shared NA2 verified-build registry."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("lookup", "record"):
        command = subparsers.add_parser(name)
        command.add_argument("--na2-iso", required=True, type=Path)
        command.add_argument("--nun5-iso", required=True, type=Path)
        command.add_argument("--configuration", required=True, type=Path)
        command.add_argument("--registry", required=True, type=Path)
        command.add_argument("--cache-root", required=True, type=Path)
        if name == "record":
            command.add_argument("--expected-fingerprint", required=True)
            command.add_argument("--image", required=True, type=Path)
            command.add_argument("--provenance", type=Path)
    command = subparsers.add_parser("complete")
    command.add_argument("--registry", required=True, type=Path)
    command.add_argument("--cache-root", required=True, type=Path)
    command.add_argument("--fingerprint", required=True)
    command.add_argument("--location", required=True, action="append", type=Path)

    args = parser.parse_args()
    paths = load_paths(Path(__file__).resolve(), allow_missing=True)
    workspace = paths.repository
    if args.command in {"lookup", "record"}:
        state = collect_build_state(
            workspace=workspace,
            na2_iso=args.na2_iso,
            nun5_iso=args.nun5_iso,
            configuration_path=_configuration_path(args.configuration, workspace),
        )
        if args.command == "lookup":
            result = lookup_registry(
                workspace=workspace,
                registry_path=args.registry,
                cache_root=args.cache_root,
                state=state,
            )
        else:
            result = record_registry(
                workspace=workspace,
                registry_path=args.registry,
                cache_root=args.cache_root,
                state=state,
                expected_fingerprint=args.expected_fingerprint.upper(),
                image=args.image,
                provenance=args.provenance,
            )
    else:
        result = record_locations(
            workspace=workspace,
            registry_path=args.registry,
            cache_root=args.cache_root,
            fingerprint=args.fingerprint.upper(),
            locations=args.location,
        )
    _emit(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
