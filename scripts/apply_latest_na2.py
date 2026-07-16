#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import fnmatch
import os
import re
import shutil
import sys
import zipfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from iso9660_tools import Iso9660, SECTOR

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from na2_patcher.modules.raw_binary import engine as patch_binary
from na2_patcher.profile import Profile, ProfileModule, load_profile
from na2_patcher.modules import translation as translation_module


def normalize(path: str) -> str:
    return path.replace("\\", "/").strip("/").upper()


def normalize_category(value: str) -> str:
    category = "".join(char if char.isalnum() else "_" for char in value.strip().upper())
    category = "_".join(part for part in category.split("_") if part)
    if not category:
        raise ValueError("Empty package category")
    return category


def filename_release_key(path: Path) -> tuple[int, str, int, str]:
    name = path.name.upper()
    timestamp_match = re.search(r"(?<!\d)(20\d{6})[_-](\d{6})(?!\d)", name)
    version_match = re.search(r"(?:^|[_-])V(\d+)(?:[_-]|\.|$)", name)
    timestamp = "" if timestamp_match is None else "".join(timestamp_match.groups())
    version = -1 if version_match is None else int(version_match.group(1))
    return (int(bool(timestamp)), timestamp, version, name)


def latest_file(directory: Path, pattern: str) -> Path:
    pattern_upper = pattern.upper()
    matches = [
        path
        for path in directory.iterdir()
        if path.is_file() and fnmatch.fnmatch(path.name.upper(), pattern_upper)
    ]
    if not matches:
        raise FileNotFoundError(f"No file matches {directory / pattern}")
    return max(matches, key=filename_release_key)


def building_iso_path(output_iso: Path) -> Path:
    return output_iso.with_name(output_iso.name + ".building")


@contextmanager
def staged_output_iso(source_iso: Path, output_iso: Path, *, promote: bool = True):
    """Build beside the final ISO and optionally promote it after full success.

    ``promote=False`` is used by the PowerShell orchestration wrapper.  It
    leaves the fully verified ``.building`` candidate in place so the wrapper
    can close PCSX2, rotate Current to Previous, and promote the candidate.
    """
    output_iso.parent.mkdir(parents=True, exist_ok=True)
    building_iso = building_iso_path(output_iso)
    if source_iso == building_iso:
        raise ValueError("Source ISO cannot use the reserved .building output path")
    if building_iso.exists() or building_iso.is_symlink():
        if not building_iso.is_file() and not building_iso.is_symlink():
            raise RuntimeError(f"Temporary build path is not a file: {building_iso}")
        building_iso.unlink()

    print(f"Initializing temporary output: {building_iso.name}")
    try:
        shutil.copyfile(source_iso, building_iso)
        yield building_iso
        if promote:
            os.replace(building_iso, output_iso)
    except BaseException:
        if building_iso.exists() or building_iso.is_symlink():
            building_iso.unlink()
        raise


def payload_size_changes(
    source: Iso9660, payloads: dict[str, bytearray]
) -> list[tuple[str, int, int]]:
    return [
        (path, source.by_path[path].size, len(data))
        for path, data in payloads.items()
        if len(data) != source.by_path[path].size
    ]


def directory_record_offset(iso: Iso9660, path: str) -> int:
    parent_path, _, leaf = path.rpartition("/")
    parent = iso.by_path.get(parent_path)
    if parent is None or not parent.is_dir:
        raise RuntimeError(f"Parent directory not found for {path}")
    data = iso.read_file(parent)
    offset = 0
    while offset < len(data):
        length = data[offset]
        if length == 0:
            offset = ((offset // SECTOR) + 1) * SECTOR
            continue
        raw = data[offset : offset + length]
        name_length = raw[32]
        name_bytes = raw[33 : 33 + name_length]
        if name_bytes not in (b"\x00", b"\x01"):
            name = name_bytes.decode("ascii").split(";", 1)[0].upper()
            if name == leaf:
                return parent.byte_offset + offset
        offset += length
    raise RuntimeError(f"Directory record not found for {path}")


def write_both_endian_32(output, offset: int, value: int) -> None:
    output.seek(offset)
    output.write(value.to_bytes(4, "little"))
    output.write(value.to_bytes(4, "big"))


def update_volume_space_size(output, sectors: int) -> None:
    for sector in range(16, 128):
        offset = sector * SECTOR
        output.seek(offset)
        descriptor = output.read(SECTOR)
        if len(descriptor) != SECTOR or descriptor[1:6] != b"CD001":
            continue
        if descriptor[0] == 1:
            write_both_endian_32(output, offset + 80, sectors)
        if descriptor[0] == 255:
            break


def load_zip_payloads(
    package: Path,
    *,
    source: Iso9660,
    payloads: dict[str, bytearray],
    owners: dict[str, str],
) -> list[str]:
    applied: list[str] = []
    seen: set[str] = set()
    with zipfile.ZipFile(package) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            path = normalize(info.filename)
            if path in seen:
                raise RuntimeError(f"Duplicate ZIP path in {package.name}: {path}")
            seen.add(path)
            if path in owners:
                raise RuntimeError(
                    f"Selected ZIP packages replace the same ISO path: {path} "
                    f"({owners[path]} and {package.name})"
                )
            record = source.by_path.get(path)
            if record is None or record.is_dir:
                raise RuntimeError(f"ZIP path is not in the clean source ISO: {path}")
            payloads[path] = bytearray(archive.read(info))
            owners[path] = package.name
            applied.append(path)
    if not applied:
        raise RuntimeError(f"Package contains no files: {package}")
    return applied


def parse_offset(value: str, *, row_number: int) -> int:
    text = value.strip()
    if not text:
        raise ValueError(f"Translation TSV row {row_number}: empty offset")
    try:
        return int(text, 0)
    except ValueError as exc:
        raise ValueError(
            f"Translation TSV row {row_number}: invalid offset {value!r}"
        ) from exc


def parse_hex(value: str, *, field: str, row_number: int) -> bytes:
    compact = "".join(value.split())
    if not compact:
        raise ValueError(f"Translation TSV row {row_number}: empty {field}")
    if len(compact) % 2:
        raise ValueError(f"Translation TSV row {row_number}: odd-length {field}")
    try:
        return bytes.fromhex(compact)
    except ValueError as exc:
        raise ValueError(
            f"Translation TSV row {row_number}: invalid {field}"
        ) from exc


def apply_translation_rows(
    rows: list[dict[str, str]],
    *,
    owner_name: str,
    source: Iso9660,
    payloads: dict[str, bytearray],
    owners: dict[str, str],
) -> tuple[int, list[str]]:
    patched_paths: list[str] = []
    patched_set: set[str] = set()
    row_count = 0

    for row_number, row in enumerate(rows, 2):
        if not any((value or "").strip() for value in row.values()):
            continue
        path = normalize(row["path"])
        record = source.by_path.get(path)
        if record is None or record.is_dir:
            raise RuntimeError(
                f"Translation row {row_number}: path is not in the clean source ISO: {path}"
            )
        if path not in payloads:
            payloads[path] = bytearray(source.read_file(record))
            owners[path] = owner_name

        offset = parse_offset(row["offset"], row_number=row_number)
        expected = parse_hex(
            row["expected_hex"], field="expected_hex", row_number=row_number
        )
        replacement = parse_hex(
            row["replacement_hex"], field="replacement_hex", row_number=row_number
        )
        if len(expected) != len(replacement):
            raise ValueError(
                f"Translation row {row_number}: expected/replacement lengths differ "
                f"({len(expected)} != {len(replacement)})"
            )

        data = payloads[path]
        end = offset + len(expected)
        if offset < 0 or end > len(data):
            raise ValueError(
                f"Translation row {row_number}: range 0x{offset:X}-0x{end:X} "
                f"is outside {path} ({len(data)} bytes)"
            )
        actual = bytes(data[offset:end])
        if actual != expected:
            raise RuntimeError(
                f"Translation conflict in {owner_name}, row {row_number}, {path} "
                f"at 0x{offset:X}: expected {expected.hex().upper()}, "
                f"found {actual.hex().upper()}"
            )
        data[offset:end] = replacement
        owners[path] = owner_name
        row_count += 1
        if path not in patched_set:
            patched_set.add(path)
            patched_paths.append(path)

    if row_count == 0:
        raise RuntimeError(f"Translation module contains no patch rows: {owner_name}")
    return row_count, patched_paths


def apply_translation_tsv(
    table: Path,
    *,
    source: Iso9660,
    payloads: dict[str, bytearray],
    owners: dict[str, str],
) -> tuple[int, list[str]]:
    patch_fields = ["path", "offset", "expected_hex", "replacement_hex"]
    descriptive_fields = patch_fields + ["source_text", "replacement_text"]
    with table.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fields = reader.fieldnames or []
        if fields not in (patch_fields, descriptive_fields):
            raise ValueError(
                "Translation TSV columns must be either: "
                + "\t".join(patch_fields)
                + " or "
                + "\t".join(descriptive_fields)
            )
        rows = [dict(row) for row in reader]
    return apply_translation_rows(
        rows,
        owner_name=table.name,
        source=source,
        payloads=payloads,
        owners=owners,
    )


def apply_raw_patch_set(
    package_directory: Path,
    *,
    roots: dict[str, Path],
    requested_patches: list[str],
    defaults: bool,
    source: Iso9660,
    payloads: dict[str, bytearray],
    owners: dict[str, str],
) -> dict[str, object]:
    package = patch_binary.load_package(package_directory)
    target_data = patch_binary.verify_package_data(package, roots)
    selected = patch_binary.selected_patch_ids(
        package,
        requested_patches,
        defaults,
    )
    edits = patch_binary.validate_selection(package, selected, for_apply=True)

    initial_buffers: dict[str, bytes | bytearray] = {}
    target_paths: dict[str, str] = {}
    for target_id in {edit.destination_target_id for edit in edits}:
        target = package.targets[target_id]
        path = normalize(target.path.as_posix())
        record = source.by_path.get(path)
        if record is None or record.is_dir:
            raise RuntimeError(
                f"Raw patch destination is not in the clean source ISO: {path}"
            )
        initial_buffers[target_id] = (
            payloads[path] if path in payloads else source.read_file(record)
        )
        target_paths[target_id] = path

    buffers, patch_rows, before_hashes = patch_binary.compose_edits(
        package,
        target_data,
        edits,
        initial_buffers,
    )
    after_hashes: dict[str, str] = {}
    patched_paths: list[str] = []
    for target_id, data in buffers.items():
        path = target_paths[target_id]
        payloads[path] = data
        owners[path] = package.manifest["package_id"]
        after_hashes[target_id] = patch_binary.data_sha256(data)
        patched_paths.append(path)

    return {
        "package": package,
        "selected": selected,
        "edits": edits,
        "patch_rows": patch_rows,
        "before_hashes": before_hashes,
        "after_hashes": after_hashes,
        "patched_paths": patched_paths,
    }


def write_raw_composition_log(
    result: dict[str, object],
    log_directory: Path,
    *,
    output_iso_text: str,
    log_directory_text: str,
) -> None:
    package = result["package"]
    selected = result["selected"]
    edits = result["edits"]
    before_hashes = result["before_hashes"]
    after_hashes = result["after_hashes"]
    assert isinstance(package, patch_binary.Package)
    assert isinstance(selected, list)
    assert isinstance(edits, list)
    assert isinstance(before_hashes, dict)
    assert isinstance(after_hashes, dict)

    patch_binary.write_tsv(
        log_directory / "patch_log.tsv",
        [
            "package_id", "patch_id", "edit_id", "target_id", "path",
            "offset", "length", "original_hex", "new_hex", "operation", "reason",
        ],
        result["patch_rows"],
    )
    patch_binary.write_tsv(
        log_directory / "selected_patches.tsv",
        ["patch_id", "status", "confidence", "name"],
        [
            {
                "patch_id": patch_id,
                "status": package.patches[patch_id].status,
                "confidence": package.patches[patch_id].confidence,
                "name": package.patches[patch_id].name,
            }
            for patch_id in selected
        ],
    )
    patch_binary.write_tsv(
        log_directory / "staged_file_hashes.tsv",
        ["target_id", "path", "size", "before_sha256", "after_sha256"],
        [
            {
                "target_id": target_id,
                "path": package.targets[target_id].path.as_posix(),
                "size": package.targets[target_id].expected_size,
                "before_sha256": before_hashes[target_id],
                "after_sha256": after_hashes[target_id],
            }
            for target_id in sorted(after_hashes)
        ],
    )
    patch_binary.write_tsv(
        log_directory / "run_summary.tsv",
        [
            "timestamp_utc", "schema_version", "package_id", "package_version",
            "output_iso", "log_directory", "patch_count", "edit_count",
        ],
        [{
            "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "schema_version": package.manifest["schema_version"],
            "package_id": package.manifest["package_id"],
            "package_version": package.manifest["package_version"],
            "output_iso": output_iso_text.replace("\\", "/"),
            "log_directory": log_directory_text.replace("\\", "/"),
            "patch_count": len(selected),
            "edit_count": len(edits),
        }],
    )


def _translation_source_arguments(root: Path, prefix: str) -> dict[str, Path]:
    if root.is_dir():
        return {f"{prefix}_folder": root}
    if root.is_file():
        return {f"{prefix}_iso": root}
    raise FileNotFoundError(root)


def apply_profile_modules(
    profile: Profile,
    *,
    source: Iso9660,
    payloads: dict[str, bytearray],
    owners: dict[str, str],
) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for module in profile.modules:
        if not module.enabled:
            continue
        if module.module == "zip_overlay":
            paths = load_zip_payloads(
                module.input_path,
                source=source,
                payloads=payloads,
                owners=owners,
            )
            results.append({"module": module, "paths": paths})
            continue
        if module.module == "raw_binary":
            result = apply_raw_patch_set(
                module.input_path,
                roots=profile.roots,
                requested_patches=list(module.selection),
                defaults=not module.selection,
                source=source,
                payloads=payloads,
                owners=owners,
            )
            results.append({"module": module, "raw_result": result, "paths": result["patched_paths"]})
            continue
        if module.module == "translation":
            if module.input_path.name.lower() != "mappings.tsv":
                raise ValueError(
                    f"Translation module {module.module_id} input must be mappings.tsv"
                )
            if "na2" not in profile.roots or "un5" not in profile.roots:
                raise ValueError("Translation module requires na2 and un5 profile roots")
            plan = translation_module.build_translation_plan(
                **_translation_source_arguments(profile.roots["na2"], "na2"),
                **_translation_source_arguments(profile.roots["un5"], "un5"),
                data_root=module.input_path.parent,
                apply=",".join(module.selection) if module.selection else "BTL,ETC,SLPS",
                strict_hash=True,
                persist_state=False,
            )
            rows, paths = apply_translation_rows(
                plan.patch_rows,
                owner_name=module.module_id,
                source=source,
                payloads=payloads,
                owners=owners,
            )
            results.append(
                {
                    "module": module,
                    "translation_plan": plan,
                    "translation_rows": rows,
                    "paths": paths,
                }
            )
            continue
        raise AssertionError(module.module)
    return results


def write_profile_log(
    profile: Profile,
    results: list[dict[str, object]],
    log_directory: Path,
    *,
    workspace: Path,
    output_iso_text: str,
) -> None:
    log_directory.mkdir(parents=True, exist_ok=False)
    module_rows: list[dict[str, object]] = []
    for item in results:
        module = item["module"]
        assert isinstance(module, ProfileModule)
        paths = item.get("paths", [])
        assert isinstance(paths, list)
        module_rows.append(
            {
                "module_id": module.module_id,
                "order": module.order,
                "module": module.module,
                "input": module.input_path.relative_to(workspace).as_posix(),
                "input_sha256": module.expected_sha256,
                "selection": ",".join(module.selection),
                "patched_paths": ",".join(sorted(str(path) for path in paths)),
            }
        )
        module_log = log_directory / module.module_id
        if "raw_result" in item:
            write_raw_composition_log(
                item["raw_result"],
                module_log,
                output_iso_text=output_iso_text,
                log_directory_text=module_log.relative_to(workspace).as_posix(),
            )
        if "translation_plan" in item:
            plan = item["translation_plan"]
            assert isinstance(plan, translation_module.TranslationPlan)
            module_log.mkdir(parents=True, exist_ok=True)
            translation_module.write_translation_tsv(
                module_log / "translation_plan.tsv", plan.patch_rows
            )
            translation_module.write_json(
                module_log / "translation_summary.json", plan.summary
            )
    patch_binary.write_tsv(
        log_directory / "modules.tsv",
        [
            "module_id",
            "order",
            "module",
            "input",
            "input_sha256",
            "selection",
            "patched_paths",
        ],
        module_rows,
    )
    patch_binary.write_tsv(
        log_directory / "run_summary.tsv",
        ["timestamp_utc", "profile_id", "output_iso", "module_count"],
        [
            {
                "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "profile_id": profile.manifest["profile_id"],
                "output_iso": output_iso_text.replace("\\", "/"),
                "module_count": len(results),
            }
        ],
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Recreate the output ISO, compose the newest selected NA2 ZIP packages, "
            "then apply the newest translation TSV last."
        )
    )
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--package-directory", type=Path)
    parser.add_argument("--profile", type=Path)
    parser.add_argument("--profile-log-directory", type=Path)
    parser.add_argument("--translation-tsv", type=Path)
    parser.add_argument("--package", action="append", default=[])
    parser.add_argument("--raw-patch-package", type=Path)
    parser.add_argument("--raw-root", action="append", default=[], metavar="ID=PATH")
    parser.add_argument("--raw-patch", action="append", default=[])
    parser.add_argument("--raw-defaults", action="store_true")
    parser.add_argument("--raw-log-directory", type=Path)
    parser.add_argument(
        "--stage-only",
        action="store_true",
        help="leave the verified .building ISO for the orchestration wrapper to promote",
    )
    parser.add_argument(
        "--allow-size-changes",
        action="store_true",
        help="Allow legacy payloads to relocate ISO files whose sizes change.",
    )
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    source_iso = args.source.resolve()
    output_iso = args.output.resolve()
    package_directory = args.package_directory.resolve() if args.package_directory else None
    explicit_translation = (
        args.translation_tsv.resolve() if args.translation_tsv else None
    )
    if not source_iso.is_file():
        raise FileNotFoundError(source_iso)
    if explicit_translation is not None and not explicit_translation.is_file():
        raise FileNotFoundError(explicit_translation)
    if source_iso == output_iso:
        raise ValueError("Source and output ISO paths must differ")

    profile = None
    profile_log_directory = None
    if args.profile is not None:
        legacy_options = bool(
            args.package_directory
            or args.translation_tsv
            or args.package
            or args.raw_patch_package
            or args.raw_root
            or args.raw_patch
            or args.raw_defaults
            or args.raw_log_directory
        )
        if legacy_options:
            raise ValueError("--profile cannot be combined with legacy package/raw/translation options")
        if args.profile_log_directory is None:
            raise ValueError("--profile-log-directory is required with --profile")
        profile_directory = (
            args.profile if args.profile.is_absolute() else workspace / args.profile
        )
        profile = load_profile(profile_directory, workspace)
        profile_log_directory = patch_binary.command_relative_path(
            str(args.profile_log_directory), "--profile-log-directory", workspace
        )
        if profile_log_directory.exists():
            raise FileExistsError(profile_log_directory)
    else:
        if args.profile_log_directory is not None:
            raise ValueError("--profile-log-directory requires --profile")
        if package_directory is None or not package_directory.is_dir():
            raise FileNotFoundError(package_directory or "--package-directory")

    raw_requested = args.raw_patch_package is not None
    raw_options_present = bool(
        args.raw_root or args.raw_patch or args.raw_defaults or args.raw_log_directory
    )
    if not raw_requested and raw_options_present:
        raise ValueError("Raw patch options require --raw-patch-package")
    raw_package_directory = None
    raw_roots: dict[str, Path] = {}
    raw_log_directory = None
    raw_log_text = ""
    if raw_requested:
        raw_package_directory = patch_binary.command_relative_path(
            str(args.raw_patch_package), "--raw-patch-package", workspace
        )
        if not raw_package_directory.is_dir():
            raise FileNotFoundError(raw_package_directory)
        raw_roots = patch_binary.parse_roots(args.raw_root, workspace)
        if args.raw_log_directory is None:
            raise ValueError("--raw-log-directory is required with raw patches")
        raw_log_text = str(args.raw_log_directory)
        raw_log_directory = patch_binary.command_relative_path(
            raw_log_text, "--raw-log-directory", workspace
        )
        if raw_log_directory.exists():
            raise FileExistsError(raw_log_directory)

    packages: list[tuple[str, Path]] = []
    translation_table = None
    if profile is None:
        assert package_directory is not None
        requested = args.package or ["Font", "Translation"]
        categories: list[str] = []
        for value in requested:
            category = normalize_category(value)
            if category not in categories:
                categories.append(category)

        zip_categories = [category for category in categories if category != "TRANSLATION"]
        translation_selected = "TRANSLATION" in categories
        for category in zip_categories:
            package = latest_file(package_directory, f"NA2_APPLY__{category}__*.zip")
            packages.append((category, package))

        if translation_selected:
            translation_table = explicit_translation or latest_file(
                package_directory, "NA2_APPLY__TRANSLATION__*.tsv"
            )
        elif explicit_translation is not None:
            raise ValueError("--translation-tsv requires the Translation package")

    source = Iso9660(source_iso)
    payloads: dict[str, bytearray] = {}
    owners: dict[str, str] = {}
    package_paths: dict[str, list[str]] = {}
    raw_result = None
    translated_rows = 0
    translated_paths: list[str] = []
    profile_results: list[dict[str, object]] = []
    if profile is not None:
        profile_results = apply_profile_modules(
            profile,
            source=source,
            payloads=payloads,
            owners=owners,
        )
    else:
        for category, package in packages:
            package_paths[category] = load_zip_payloads(
                package,
                source=source,
                payloads=payloads,
                owners=owners,
            )

        if raw_package_directory is not None:
            raw_result = apply_raw_patch_set(
                raw_package_directory,
                roots=raw_roots,
                requested_patches=args.raw_patch,
                defaults=args.raw_defaults,
                source=source,
                payloads=payloads,
                owners=owners,
            )

        if translation_table is not None:
            translated_rows, translated_paths = apply_translation_tsv(
                translation_table,
                source=source,
                payloads=payloads,
                owners=owners,
            )

    if not payloads:
        raise RuntimeError("No package files or translation patches were selected")

    size_changes = payload_size_changes(source, payloads)
    if size_changes and not args.allow_size_changes:
        details = ", ".join(
            f"{path} ({old_size} -> {new_size})"
            for path, old_size, new_size in size_changes
        )
        raise RuntimeError(
            "Selected payloads change ISO file sizes; pass --allow-size-changes "
            f"only for an explicitly approved relocation build: {details}"
        )

    with staged_output_iso(source_iso, output_iso, promote=not args.stage_only) as working_iso:
        current = Iso9660(working_iso)
        with working_iso.open("r+b") as output:
            for path, data in payloads.items():
                record = current.by_path[path]
                payload = bytes(data)
                if len(payload) == record.size:
                    output.seek(record.byte_offset)
                    output.write(payload)
                    continue

                output.seek(0, os.SEEK_END)
                extent = (output.tell() + SECTOR - 1) // SECTOR
                output.seek(extent * SECTOR)
                output.write(payload)
                padding = (-len(payload)) % SECTOR
                if padding:
                    output.write(b"\x00" * padding)

                record_offset = directory_record_offset(current, path)
                write_both_endian_32(output, record_offset + 2, extent)
                write_both_endian_32(output, record_offset + 10, len(payload))

            output.seek(0, os.SEEK_END)
            sectors = (output.tell() + SECTOR - 1) // SECTOR
            output.truncate(sectors * SECTOR)
            update_volume_space_size(output, sectors)
            output.flush()
            os.fsync(output.fileno())

        result = Iso9660(working_iso)
        source_tree = {(record.path, record.is_dir) for record in source.records}
        result_tree = {(record.path, record.is_dir) for record in result.records}
        if result_tree != source_tree:
            raise RuntimeError("Final ISO file tree differs from the source tree")

        for source_record in source.records:
            if source_record.is_dir:
                continue
            result_record = result.by_path.get(source_record.path)
            if result_record is None or result_record.is_dir:
                raise RuntimeError(f"Final ISO is missing source file: {source_record.path}")
            expected = (
                bytes(payloads[source_record.path])
                if source_record.path in payloads
                else source.read_file(source_record)
            )
            if result.read_file(result_record) != expected:
                raise RuntimeError(
                    f"Final ISO file verification failed: {source_record.path}"
                )

        if profile is not None:
            assert profile_log_directory is not None
            write_profile_log(
                profile,
                profile_results,
                profile_log_directory,
                workspace=workspace,
                output_iso_text=output_iso.relative_to(workspace).as_posix(),
            )
        elif raw_result is not None:
            assert raw_log_directory is not None
            write_raw_composition_log(
                raw_result,
                raw_log_directory,
                output_iso_text=str(args.output),
                log_directory_text=raw_log_text,
            )

    green = "\033[32m"
    reset = "\033[0m"
    if profile is not None:
        print(f"Applied profile: {profile.manifest['profile_id']}")
        for item in profile_results:
            module = item["module"]
            assert isinstance(module, ProfileModule)
            detail = ""
            if "raw_result" in item:
                detail = f", {len(item['raw_result']['edits'])} edits"
            elif "translation_rows" in item:
                detail = f", {item['translation_rows']} rows"
            print(f"  {module.order:03d} {module.module_id} ({module.module}{detail})")
            for path in sorted(str(value) for value in item.get("paths", [])):
                print(f"    {green}{path}{reset}")
    else:
        for category, package in packages:
            print(f"Applied {category} package: {package.name}")
            for path in sorted(package_paths[category]):
                print(f"  {green}{path}{reset}")
        if raw_result is not None:
            raw_package = raw_result["package"]
            assert isinstance(raw_package, patch_binary.Package)
            print(f"Applied raw patch set: {raw_package.manifest['package_id']}")
            print(f"  patches: {len(raw_result['selected'])}")
            print(f"  edits: {len(raw_result['edits'])}")
            for path in sorted(raw_result["patched_paths"]):
                print(f"  {green}{path}{reset}")
        if translation_table is not None:
            print(f"Applied translation table: {translation_table.name}")
            print(f"  rows: {translated_rows}")
            for path in sorted(translated_paths):
                print(f"  {green}{path}{reset}")
    try:
        display_iso = output_iso.relative_to(workspace).as_posix()
    except ValueError:
        display_iso = output_iso.name
    if args.stage_only:
        print(f"Verified staged ISO: {building_iso_path(output_iso).name}")
    else:
        print(f"ISO: {display_iso}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
