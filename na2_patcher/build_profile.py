#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from .iso9660 import Iso9660
from .modules import translation as translation_module
from .modules.disc_identity import engine as disc_identity_module
from .modules.raw_binary import engine as patch_binary
from .profile import Profile, ProfileModule, load_profile
from .project_paths import load_project_paths


PROJECT_PATHS = load_project_paths(Path(__file__).resolve())


def normalize(path: str) -> str:
    return path.replace("\\", "/").strip("/").upper()


def building_iso_path(output_iso: Path) -> Path:
    return output_iso.with_name(output_iso.name + ".building")


@contextmanager
def staged_output_iso(source_iso: Path, output_iso: Path):
    """Build beside the final ISO and leave the verified candidate for promotion."""
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
        if module.module == "disc_identity":
            if any("disc_identity" in item for item in results):
                raise ValueError("Profile may enable only one disc_identity module")
            if module.selection:
                raise ValueError("disc_identity modules do not accept selections")
            identity = disc_identity_module.load_identity(module.input_path)
            system_path = "SYSTEM.CNF"
            record = source.by_path.get(system_path)
            if record is None or record.is_dir:
                raise RuntimeError("Disc identity requires SYSTEM.CNF in the source ISO")
            initial = payloads.get(system_path, bytearray(source.read_file(record)))
            updated, system_edit = disc_identity_module.apply_system_cnf(
                identity,
                initial,
            )
            payloads[system_path] = updated
            owners[system_path] = module.module_id
            results.append(
                {
                    "module": module,
                    "disc_identity": identity,
                    "identity_edits": [system_edit],
                    "paths": [
                        system_path,
                        f"{identity.source_boot_path} -> {identity.replacement_boot_path}",
                    ],
                }
            )
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
            if "na2" not in profile.roots or "nun5" not in profile.roots:
                raise ValueError("Translation module requires na2 and nun5 profile roots")
            plan = translation_module.build_translation_plan(
                **_translation_source_arguments(profile.roots["na2"], "na2"),
                **_translation_source_arguments(profile.roots["nun5"], "nun5"),
                data_root=module.input_path.parent,
                apply=",".join(module.selection) if module.selection else "BTL,ETC,SLPS",
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
        if "disc_identity" in item:
            identity = item["disc_identity"]
            assert isinstance(identity, disc_identity_module.DiscIdentity)
            edits = item["identity_edits"]
            assert isinstance(edits, list)
            patch_binary.write_tsv(
                module_log / "patch_log.tsv",
                [
                    "target",
                    "offset",
                    "length",
                    "original_hex",
                    "new_hex",
                    "reason",
                ],
                edits,
            )
            patch_binary.write_tsv(
                module_log / "run_summary.tsv",
                ["source_serial", "replacement_serial", "edit_count"],
                [
                    {
                        "source_serial": identity.source_serial,
                        "replacement_serial": identity.replacement_serial,
                        "edit_count": len(edits),
                    }
                ],
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
        description="Build a verified staged NA2 ISO from one hash-pinned profile."
    )
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--profile-log-directory", required=True, type=Path)
    args = parser.parse_args()

    workspace = PROJECT_PATHS.repository
    source_iso = args.source.resolve()
    output_iso = args.output.resolve()
    if not source_iso.is_file():
        raise FileNotFoundError(source_iso)
    if source_iso == output_iso:
        raise ValueError("Source and output ISO paths must differ")

    profile_directory = args.profile if args.profile.is_absolute() else workspace / args.profile
    profile = load_profile(profile_directory, workspace)
    profile_log_directory = patch_binary.command_relative_path(
        str(args.profile_log_directory), "--profile-log-directory", workspace
    )
    if profile_log_directory.exists():
        raise FileExistsError(profile_log_directory)

    source = Iso9660(source_iso)
    payloads: dict[str, bytearray] = {}
    owners: dict[str, str] = {}
    profile_results = apply_profile_modules(
        profile,
        source=source,
        payloads=payloads,
        owners=owners,
    )

    if not payloads:
        raise RuntimeError("The profile selected no file changes")

    size_changes = payload_size_changes(source, payloads)
    if size_changes:
        details = ", ".join(
            f"{path} ({old_size} -> {new_size})"
            for path, old_size, new_size in size_changes
        )
        raise RuntimeError(
            f"Profile payloads must preserve ISO file sizes: {details}"
        )

    with staged_output_iso(source_iso, output_iso) as working_iso:
        current = Iso9660(working_iso)
        with working_iso.open("r+b") as output:
            for path, data in payloads.items():
                record = current.by_path[path]
                payload = bytes(data)
                output.seek(record.byte_offset)
                output.write(payload)
            output.flush()
            os.fsync(output.fileno())

        identity_items = [
            item for item in profile_results if "disc_identity" in item
        ]
        if identity_items:
            identity_item = identity_items[0]
            identity = identity_item["disc_identity"]
            assert isinstance(identity, disc_identity_module.DiscIdentity)
            iso_edit = disc_identity_module.apply_iso_directory_identifier(
                identity,
                Iso9660(working_iso),
            )
            identity_item["identity_edits"].append(iso_edit)

        result = Iso9660(working_iso)
        identity = (
            identity_items[0]["disc_identity"] if identity_items else None
        )
        source_tree = set()
        for record in source.records:
            path = record.path
            if (
                isinstance(identity, disc_identity_module.DiscIdentity)
                and path == identity.source_boot_path
            ):
                path = identity.replacement_boot_path
            source_tree.add((path, record.is_dir))
        result_tree = {(record.path, record.is_dir) for record in result.records}
        if result_tree != source_tree:
            raise RuntimeError(
                "Final ISO file tree differs from the source tree plus its declared identity rename"
            )

        for source_record in source.records:
            if source_record.is_dir:
                continue
            result_path = source_record.path
            if (
                isinstance(identity, disc_identity_module.DiscIdentity)
                and result_path == identity.source_boot_path
            ):
                result_path = identity.replacement_boot_path
            result_record = result.by_path.get(result_path)
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

        try:
            output_iso_text = output_iso.relative_to(workspace).as_posix()
        except ValueError:
            output_iso_text = output_iso.name
        write_profile_log(
            profile,
            profile_results,
            profile_log_directory,
            workspace=workspace,
            output_iso_text=output_iso_text,
        )

    green = "\033[32m"
    reset = "\033[0m"
    print(f"Applied profile: {profile.manifest['profile_id']}")
    for item in profile_results:
        module = item["module"]
        assert isinstance(module, ProfileModule)
        detail = ""
        if "raw_result" in item:
            detail = f", {len(item['raw_result']['edits'])} edits"
        elif "translation_rows" in item:
            detail = f", {item['translation_rows']} rows"
        elif "disc_identity" in item:
            detail = f", {len(item['identity_edits'])} edits"
        print(f"  {module.order:03d} {module.module_id} ({module.module}{detail})")
        for path in sorted(str(value) for value in item.get("paths", [])):
            print(f"    {green}{path}{reset}")
    print(f"Verified staged ISO: {building_iso_path(output_iso).name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
