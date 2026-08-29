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


REGISTRY_SCHEMA_VERSION = 3
FINGERPRINT_SCHEMA_VERSION = 11
SHA256_HEX_LENGTH = 64
MAX_IMAGES = 10
ISO_NAME_PREFIX = "NA v2.28"
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
    relative = image.get("path")
    if not isinstance(relative, str):
        return None
    location = (workspace / relative).resolve()
    resolved_root = cache_root.resolve()
    if location.parent != resolved_root:
        return None
    return location if _valid_image(location, size, sha256) else None


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


def resolve_registry(
    *,
    workspace: Path,
    registry_path: Path,
    cache_root: Path,
    configuration_id: str,
) -> dict[str, object]:
    try:
        registry = _read_registry(registry_path)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return {
            "status": "missing",
            "reason": "registry-invalid",
            "detail": str(error),
            "configuration": configuration_id,
        }
    candidates = sorted(
        (
            (fingerprint, entry)
            for fingerprint, entry in registry["entries"].items()
            if isinstance(entry, dict)
            and entry.get("configuration") == configuration_id
        ),
        key=lambda item: str(item[1].get("verified_utc", "")),
        reverse=True,
    )
    for fingerprint, entry in candidates:
        image = _entry_image(
            entry,
            registry["images"],
            workspace,
            cache_root,
        )
        if image is None:
            continue
        sha256 = entry["sha256"]
        image_record = registry["images"][sha256]
        result: dict[str, object] = {
            "status": "resolved",
            "configuration": configuration_id,
            "fingerprint": fingerprint,
            "output_size_bytes": image_record["size"],
            "output_sha256": sha256,
            "image": str(image),
            "verified_utc": entry["verified_utc"],
        }
        provenance = registry_path.parent / "records" / fingerprint
        if provenance.is_dir():
            result["provenance"] = str(provenance.resolve())
        return result
    return {
        "status": "missing",
        "reason": "configuration-build-missing",
        "configuration": configuration_id,
    }


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


def _prune_registry(registry: dict[str, object]) -> None:
    entries = registry["entries"]
    assert isinstance(entries, dict)
    images = registry["images"]
    assert isinstance(images, dict)
    newest_by_hash: dict[str, str] = {}
    for entry in entries.values():
        if not isinstance(entry, dict):
            continue
        sha256 = entry.get("sha256")
        if not _valid_sha256(sha256):
            continue
        verified = str(entry.get("verified_utc", ""))
        newest_by_hash[sha256] = max(newest_by_hash.get(sha256, ""), verified)
    retained_hashes = {
        sha256
        for sha256, _ in sorted(
            newest_by_hash.items(), key=lambda item: item[1], reverse=True
        )[:MAX_IMAGES]
    }
    for sha256 in list(images):
        if sha256 not in retained_hashes:
            del images[sha256]
    for fingerprint in list(entries):
        entry = entries[fingerprint]
        if not isinstance(entry, dict) or entry.get("sha256") not in retained_hashes:
            del entries[fingerprint]


def _cleanup_registry_artifacts(
    registry: dict[str, object],
    registry_path: Path,
    workspace: Path,
    cache_root: Path,
) -> None:
    entries = registry["entries"]
    assert isinstance(entries, dict)
    retained_fingerprints = set(entries)
    records_root = registry_path.parent / "records"
    if records_root.is_dir():
        for record in records_root.iterdir():
            if record.is_dir() and record.name not in retained_fingerprints:
                try:
                    shutil.rmtree(record)
                except OSError:
                    pass
    retained_images = {
        (workspace / image["path"]).resolve()
        for image in registry["images"].values()
        if isinstance(image, dict) and isinstance(image.get("path"), str)
    }
    for image in cache_root.glob(f"{ISO_NAME_PREFIX} - *.iso"):
        if image.resolve() in retained_images:
            continue
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
            try:
                registry = _read_registry(registry_path)
            except (OSError, ValueError, json.JSONDecodeError):
                registry = _empty_registry()
            record_directory = registry_path.parent / "records" / fingerprint
            if provenance is not None:
                record_directory.parent.mkdir(parents=True, exist_ok=True)
                _copy_provenance(provenance.resolve(), record_directory)
            cache_root.mkdir(parents=True, exist_ok=True)
            images = registry["images"]
            assert isinstance(images, dict)
            existing_image = images.get(sha256)
            if isinstance(existing_image, dict):
                if existing_image.get("size") != size:
                    raise RuntimeError(
                        f"Registry image identity has inconsistent sizes: {sha256}"
                    )
                existing_path = existing_image.get("path")
                if not isinstance(existing_path, str):
                    raise RuntimeError(f"Registry image path is invalid: {sha256}")
                cache_image = (workspace / existing_path).resolve()
                if cache_image.parent != cache_root.resolve():
                    raise RuntimeError(
                        "Registry image path is outside the build directory: "
                        f"{sha256}"
                    )
                if not _valid_image(cache_image, size, sha256):
                    raise RuntimeError(f"Cached ISO identity mismatch: {cache_image}")
                cache_image_preexisting = True
                image.unlink()
            else:
                local_timestamp = datetime.now().astimezone().strftime(
                    "%Y-%m-%d %H.%M.%S"
                )
                cache_image = cache_root / (
                    f"{ISO_NAME_PREFIX} - {local_timestamp} - {sha256[:12]}.iso"
                )
                if cache_image.exists():
                    if not _valid_image(cache_image, size, sha256):
                        raise RuntimeError(f"Cached ISO name collision: {cache_image}")
                    cache_image_preexisting = True
                    image.unlink()
                else:
                    os.replace(image, cache_image)
                images[sha256] = {
                    "size": size,
                    "path": _relative_workspace_path(cache_image, workspace),
                    "created_utc": datetime.now(timezone.utc).isoformat(),
                }
            configuration_value = state.get("configuration")
            if not isinstance(configuration_value, str):
                raise ValueError("Build state has no configuration path")
            configuration_id = Path(configuration_value).stem
            registry["entries"][fingerprint] = {
                "state": state,
                "configuration": configuration_id,
                "sha256": sha256,
                "verified_utc": datetime.now(timezone.utc).isoformat(),
            }
            _prune_registry(registry)
            _write_registry(registry_path, registry)
            _cleanup_registry_artifacts(
                registry, registry_path, workspace, cache_root
            )
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
    command = subparsers.add_parser("resolve")
    command.add_argument("--registry", required=True, type=Path)
    command.add_argument("--cache-root", required=True, type=Path)
    command.add_argument("--configuration-id", required=True)

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
        result = resolve_registry(
            workspace=workspace,
            registry_path=args.registry,
            cache_root=args.cache_root,
            configuration_id=args.configuration_id,
        )
    _emit(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
