from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import zlib
from pathlib import Path
from typing import Iterable

from na228_builder.profile import load_profile, profile_resource_files
from scripts.lib.paths import load_paths


RECEIPT_SCHEMA_VERSION = 1
FINGERPRINT_SCHEMA_VERSION = 5
SHA256_HEX_LENGTH = 64
GENERATED_SUFFIXES = {".pyc", ".pyo"}
NON_COMPOSING_BUILDER_FILES = {
    "app.py",
    "build_preflight.py",
    "release_manifest.json",
    "release_runtime.py",
    "requirements.txt",
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
            and path.suffix.casefold() != ".md"
            and path.relative_to(builder).parts[0] not in {"features", "profiles"}
            and path.relative_to(builder).as_posix() not in NON_COMPOSING_BUILDER_FILES
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


def profile_resources_entry(workspace: Path, profile_path: Path) -> dict[str, object]:
    profile = load_profile(profile_path, workspace)
    paths_file = workspace / "paths.json"
    files = sorted(
        set(profile_resource_files(profile)) | {paths_file},
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
            raise ValueError(f"Profile resource is outside the repository: {path}") from error
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
        "label": "profile_resources",
        "file_count": len(files),
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
    profile_path: Path,
    payload_shift: int = 0,
    boot_elf_crc_discriminator: int = 0,
    dependencies: dict[str, str] | None = None,
) -> dict[str, object]:
    workspace = workspace.resolve()
    na2_iso = na2_iso.resolve()
    nun5_iso = nun5_iso.resolve()
    profile_path = profile_path.resolve()
    if payload_shift < 0 or payload_shift > 0x10000 or payload_shift & 0xF:
        raise ValueError(
            "Payload shift must be a 16-byte multiple from 0 through 65536"
        )
    if boot_elf_crc_discriminator < 0 or boot_elf_crc_discriminator > 0xFFFFFFFF:
        raise ValueError("Boot ELF CRC discriminator must fit in an unsigned 32-bit word")
    builder = (workspace / "na228_builder").resolve()
    try:
        profile = profile_path.relative_to(builder).as_posix()
    except ValueError as error:
        raise ValueError("Profile must be inside na228_builder") from error
    if not profile_path.is_file():
        raise FileNotFoundError(profile_path)
    return {
        "fingerprint_schema_version": FINGERPRINT_SCHEMA_VERSION,
        "source_isos": [
            _file_entry(f"source/{na2_iso.name}", na2_iso),
            _file_entry(f"source/{nun5_iso.name}", nun5_iso),
        ],
        "builder_tree": builder_tree_entry(builder),
        "profile_resources": profile_resources_entry(workspace, profile_path),
        "profile": profile,
        "payload_shift": payload_shift,
        "boot_elf_crc_discriminator": boot_elf_crc_discriminator,
        "dependencies": dependencies if dependencies is not None else dependency_versions(),
    }


def _read_receipt(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or set(value) != {
        "schema_version",
        "fingerprint",
        "output",
        "state",
    }:
        raise ValueError("receipt has unexpected fields")
    if value["schema_version"] != RECEIPT_SCHEMA_VERSION:
        raise ValueError("unsupported receipt schema")
    if not _valid_sha256(value["fingerprint"]):
        raise ValueError("invalid receipt fingerprint")
    output = value["output"]
    if not isinstance(output, dict) or set(output) != {"sha256", "size"}:
        raise ValueError("invalid receipt output")
    if not _valid_sha256(output["sha256"]):
        raise ValueError("invalid receipt output hash")
    if not isinstance(output["size"], int) or output["size"] < 0:
        raise ValueError("invalid receipt output size")
    state = value["state"]
    if not isinstance(state, dict) or state_fingerprint(state) != value["fingerprint"]:
        raise ValueError("receipt state does not match its fingerprint")
    return value


def _miss(reason: str, fingerprint: str | None = None) -> dict[str, object]:
    result: dict[str, object] = {"status": "miss", "reason": reason}
    if fingerprint is not None:
        result["fingerprint"] = fingerprint
    return result


def check_preflight(
    *,
    workspace: Path,
    na2_iso: Path,
    nun5_iso: Path,
    output_iso: Path,
    profile_path: Path,
    receipt_path: Path,
    payload_shift: int = 0,
    boot_elf_crc_discriminator: int = 0,
    dependencies: dict[str, str] | None = None,
) -> dict[str, object]:
    try:
        state = collect_build_state(
            workspace=workspace,
            na2_iso=na2_iso,
            nun5_iso=nun5_iso,
            profile_path=profile_path,
            payload_shift=payload_shift,
            boot_elf_crc_discriminator=boot_elf_crc_discriminator,
            dependencies=dependencies,
        )
        fingerprint = state_fingerprint(state)
    except Exception as error:
        return {"status": "miss", "reason": "preflight-error", "detail": str(error)}

    if not receipt_path.is_file():
        return _miss("receipt-missing", fingerprint)
    try:
        receipt = _read_receipt(receipt_path)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        result = _miss("receipt-invalid", fingerprint)
        result["detail"] = str(error)
        return result
    if receipt["fingerprint"] != fingerprint:
        return _miss("fingerprint-mismatch", fingerprint)
    if not output_iso.is_file():
        return _miss("output-iso-missing", fingerprint)
    output = receipt["output"]
    assert isinstance(output, dict)
    if output_iso.stat().st_size != output["size"]:
        return _miss("output-iso-size-mismatch", fingerprint)
    output_hash = file_sha256(output_iso)
    if output_hash != output["sha256"]:
        return _miss("output-iso-hash-mismatch", fingerprint)
    return {
        "status": "hit",
        "reason": "receipt-and-output-match",
        "fingerprint": fingerprint,
        "output_sha256": output_hash,
    }


def write_receipt(
    *,
    workspace: Path,
    na2_iso: Path,
    nun5_iso: Path,
    output_iso: Path,
    profile_path: Path,
    receipt_path: Path,
    expected_fingerprint: str,
    payload_shift: int = 0,
    boot_elf_crc_discriminator: int = 0,
    dependencies: dict[str, str] | None = None,
) -> dict[str, object]:
    try:
        state = collect_build_state(
            workspace=workspace,
            na2_iso=na2_iso,
            nun5_iso=nun5_iso,
            profile_path=profile_path,
            payload_shift=payload_shift,
            boot_elf_crc_discriminator=boot_elf_crc_discriminator,
            dependencies=dependencies,
        )
        fingerprint = state_fingerprint(state)
        if fingerprint != expected_fingerprint:
            return {
                "status": "skipped",
                "reason": "inputs-changed-during-build",
                "fingerprint": fingerprint,
            }
        if not output_iso.is_file():
            return {"status": "skipped", "reason": "output-iso-missing"}
        receipt = {
            "schema_version": RECEIPT_SCHEMA_VERSION,
            "fingerprint": fingerprint,
            "output": {
                "size": output_iso.stat().st_size,
                "sha256": file_sha256(output_iso),
            },
            "state": state,
        }
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = receipt_path.with_name(f".{receipt_path.name}.{os.getpid()}.tmp")
        try:
            with temporary.open("w", encoding="utf-8", newline="\n") as handle:
                json.dump(receipt, handle, indent=2, ensure_ascii=True, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, receipt_path)
        finally:
            if temporary.exists():
                temporary.unlink()
        return {
            "status": "written",
            "reason": "successful-build",
            "fingerprint": fingerprint,
            "output_sha256": receipt["output"]["sha256"],
        }
    except Exception as error:
        return {"status": "skipped", "reason": "receipt-error", "detail": str(error)}


def _profile_path(value: Path, workspace: Path) -> Path:
    return value if value.is_absolute() else workspace / value


def _emit(value: dict[str, object]) -> None:
    print(json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True))


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check or write the deterministic NA2 build receipt."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("check", "record"):
        command = subparsers.add_parser(name)
        command.add_argument("--na2-iso", required=True, type=Path)
        command.add_argument("--nun5-iso", required=True, type=Path)
        command.add_argument("--output", required=True, type=Path)
        command.add_argument("--profile", required=True, type=Path)
        command.add_argument("--receipt", required=True, type=Path)
        command.add_argument("--payload-shift", type=int, default=0)
        command.add_argument(
            "--boot-elf-crc-discriminator",
            type=lambda value: int(value, 0),
            default=0,
        )
        if name == "record":
            command.add_argument("--expected-fingerprint", required=True)
    args = parser.parse_args(list(argv) if argv is not None else None)

    workspace = load_paths(Path(__file__).resolve()).repository
    common = {
        "workspace": workspace,
        "na2_iso": args.na2_iso,
        "nun5_iso": args.nun5_iso,
        "output_iso": args.output,
        "profile_path": _profile_path(args.profile, workspace),
        "receipt_path": args.receipt,
        "payload_shift": args.payload_shift,
        "boot_elf_crc_discriminator": args.boot_elf_crc_discriminator,
    }
    if args.command == "check":
        _emit(check_preflight(**common))
    else:
        _emit(
            write_receipt(
                **common,
                expected_fingerprint=args.expected_fingerprint.upper(),
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
