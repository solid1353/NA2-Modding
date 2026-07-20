#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from .iso9660 import (
    Iso9660,
    IsoInsertion,
    compose_filesystems,
    normalize_iso_path,
)
from .modules import translation as translation_module
from .modules.disc_identity import engine as disc_identity_module
from .modules.raw_binary import engine as patch_binary
from .modules.ui_textures import engine as ui_texture_module
from .profile import FeatureSelection, Profile, ProfileModule, load_profile
from .project_paths import load_project_paths


PROJECT_PATHS = load_project_paths(Path(__file__).resolve())
EXTERNAL_TRANSLATION_INSERTION_PATHS = (
    "PRG/MOD.BIN",
    "PRG/TEXTENG.BIN",
)


def normalize(path: str) -> str:
    return normalize_iso_path(path)


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
    feature_selections: tuple[FeatureSelection, ...],
    source: Iso9660,
    payloads: dict[str, bytearray],
    owners: dict[str, str],
) -> dict[str, object]:
    package = patch_binary.load_package(package_directory)
    target_data = patch_binary.verify_package_data(package, roots)
    selected = patch_binary.resolve_patch_selections(
        package,
        [
            (item.feature_id, item.selection_kind, item.selection_id)
            for item in feature_selections
        ],
    )
    edits = patch_binary.validate_patch_selections(
        package,
        selected,
        for_apply=True,
    )

    initial_buffers: dict[str, bytes | bytearray] = {}
    target_paths: dict[str, str] = {}
    for target_id in {item.edit.destination_target_id for item in edits}:
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


def apply_ui_texture_package(
    package_directory: Path,
    *,
    module_id: str,
    roots: dict[str, Path],
    selection: tuple[str, ...],
    source: Iso9660,
    payloads: dict[str, bytearray],
    owners: dict[str, str],
) -> tuple[ui_texture_module.UiTexturePlan, str]:
    if "na2" not in roots or "nun5" not in roots:
        raise ValueError("UI texture module requires na2 and nun5 profile roots")
    if not roots["na2"].is_dir() or not roots["nun5"].is_dir():
        raise ValueError(
            "UI texture module requires extracted na2 and nun5 profile roots"
        )
    if not package_directory.is_dir():
        raise ValueError(f"UI texture module input must be a directory: {package_directory}")

    plan = ui_texture_module.build_ui_texture_plan(
        na2_root=roots["na2"],
        nun5_root=roots["nun5"],
        data_root=package_directory,
        selection=selection,
    )
    path = "DATA/DATA.CVM"
    record = source.by_path.get(path)
    if record is None or record.is_dir:
        raise RuntimeError("UI texture module requires DATA/DATA.CVM in the source ISO")
    data = payloads.get(path)
    if data is None:
        data = bytearray(source.read_file(record))
    plan.apply_to_cvm(data)
    payloads[path] = data
    owners[path] = module_id
    return plan, path


def apply_external_translation_package(
    package_directory: Path,
    *,
    module_id: str,
    roots: dict[str, Path],
    selection: tuple[str, ...],
    source: Iso9660,
    payloads: dict[str, bytearray],
    owners: dict[str, str],
    insertions: dict[str, bytes],
    insertion_owners: dict[str, str],
) -> tuple[object, object, int, list[str]]:
    if selection:
        raise ValueError("external_translation modules do not accept selections")
    if not package_directory.is_dir():
        raise ValueError(
            f"External-translation module input must be a directory: {package_directory}"
        )

    # Kept lazy so profiles without this module do not require its package.
    from .modules import external_translation as external_translation_module

    plan = external_translation_module.build_external_translation_plan(
        package_directory=package_directory,
        roots=roots,
    )
    edits = tuple(plan.edits)
    if not edits:
        raise RuntimeError(f"External-translation module contains no edits: {module_id}")

    patched_paths: list[str] = []
    patched_set: set[str] = set()
    for edit_number, edit in enumerate(edits, 1):
        path = normalize(edit.path)
        if path != edit.path:
            raise ValueError(
                f"External-translation edit {edit_number} path is not normalized: "
                f"{edit.path!r}"
            )
        record = source.by_path.get(path)
        if record is None or record.is_dir:
            raise RuntimeError(
                f"External-translation edit {edit_number} path is not in the clean "
                f"source ISO: {path}"
            )
        expected = bytes(edit.expected)
        replacement = bytes(edit.replacement)
        if not expected:
            raise ValueError(
                f"External-translation edit {edit_number} has an empty guarded range"
            )
        if len(expected) != len(replacement):
            raise ValueError(
                f"External-translation edit {edit_number} must preserve length "
                f"({len(expected)} != {len(replacement)})"
            )
        offset = edit.offset
        if not isinstance(offset, int):
            raise TypeError(
                f"External-translation edit {edit_number} offset must be an integer"
            )
        data = payloads.get(path)
        if data is None:
            data = bytearray(source.read_file(record))
            payloads[path] = data
        end = offset + len(expected)
        if offset < 0 or end > len(data):
            raise ValueError(
                f"External-translation edit {edit_number} range "
                f"0x{offset:X}-0x{end:X} is outside {path} ({len(data)} bytes)"
            )
        actual = bytes(data[offset:end])
        if actual != expected:
            raise RuntimeError(
                f"External-translation conflict in {module_id}, edit {edit_number}, "
                f"{path} at 0x{offset:X}: expected {expected.hex().upper()}, "
                f"found {actual.hex().upper()}"
            )
        data[offset:end] = replacement
        owners[path] = module_id
        if path not in patched_set:
            patched_set.add(path)
            patched_paths.append(path)

    planned_insertions: dict[str, bytes] = {}
    for supplied_path, supplied_data in plan.insertions.items():
        path = normalize(supplied_path)
        if path != supplied_path:
            raise ValueError(
                f"External-translation insertion path is not normalized: {supplied_path!r}"
            )
        if path in planned_insertions:
            raise ValueError(f"Duplicate external-translation insertion path: {path}")
        if not isinstance(supplied_data, (bytes, bytearray, memoryview)):
            raise TypeError(
                f"External-translation insertion payload must be bytes: {path}"
            )
        planned_insertions[path] = bytes(supplied_data)
    if tuple(sorted(planned_insertions)) != EXTERNAL_TRANSLATION_INSERTION_PATHS:
        raise RuntimeError(
            "External-translation module must insert exactly "
            + ", ".join(EXTERNAL_TRANSLATION_INSERTION_PATHS)
        )
    for path in EXTERNAL_TRANSLATION_INSERTION_PATHS:
        if path in insertions:
            raise RuntimeError(f"Multiple modules declare ISO insertion path: {path}")
        if not planned_insertions[path]:
            raise ValueError(f"External-translation insertion payload is empty: {path}")
        insertions[path] = planned_insertions[path]
        insertion_owners[path] = module_id

    return (
        external_translation_module,
        plan,
        len(edits),
        patched_paths + list(EXTERNAL_TRANSLATION_INSERTION_PATHS),
    )


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
            "package_id", "feature_id", "selection_kind", "selection_id",
            "group_id", "group_name", "patch_id", "edit_id", "target_id", "path",
            "offset", "length", "original_hex", "new_hex", "operation", "outcome", "reason",
        ],
        result["patch_rows"],
    )
    patch_binary.write_tsv(
        log_directory / "selected_patches.tsv",
        [
            "feature_id", "selection_kind", "selection_id", "group_id",
            "group_name", "patch_id", "status", "confidence", "name",
        ],
        [
            {
                "feature_id": selection.feature_id,
                "selection_kind": selection.selection_kind,
                "selection_id": selection.selection_id,
                "group_id": package.patches[selection.patch_id].group_id,
                "group_name": package.groups[
                    package.patches[selection.patch_id].group_id
                ].name,
                "patch_id": selection.patch_id,
                "status": package.patches[selection.patch_id].status,
                "confidence": package.patches[selection.patch_id].confidence,
                "name": package.patches[selection.patch_id].name,
            }
            for selection in selected
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
            "output_iso", "log_directory", "group_count", "patch_count",
            "unique_patch_count", "edit_count",
        ],
        [{
            "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "schema_version": package.manifest["schema_version"],
            "package_id": package.manifest["package_id"],
            "package_version": package.manifest["package_version"],
            "output_iso": output_iso_text.replace("\\", "/"),
            "log_directory": log_directory_text.replace("\\", "/"),
            "group_count": len(
                {
                    package.patches[selection.patch_id].group_id
                    for selection in selected
                }
            ),
            "patch_count": len(selected),
            "unique_patch_count": len(
                {selection.patch_id for selection in selected}
            ),
            "edit_count": len(edits),
        }],
    )


def write_ui_texture_log(
    plan: ui_texture_module.UiTexturePlan,
    log_directory: Path,
) -> None:
    log_directory.mkdir(parents=True, exist_ok=True)
    patch_binary.write_tsv(
        log_directory / "patch_log.tsv",
        [
            "file",
            "member",
            "offset",
            "length",
            "original_sha256",
            "derivation",
            "new_sha256",
            "mapping_ids",
            "reason",
        ],
        [
            {
                "file": "DATA/DATA.CVM",
                "member": result.spec.path,
                "offset": f"0x{result.outer_cvm_offset:X}",
                "length": len(result.replacement),
                "original_sha256": ui_texture_module.sha256(result.original),
                "derivation": f"canonical_nun5_{result.strategy.strategy}",
                "new_sha256": ui_texture_module.sha256(result.replacement),
                "mapping_ids": ",".join(result.mapping_ids),
                "reason": result.strategy.reason,
            }
            for result in plan.containers
        ],
    )
    patch_binary.write_tsv(
        log_directory / "container_summary.tsv",
        [
            "container_id",
            "strategy",
            "fixed_size",
            "compressed_stream_size",
            "zero_padding",
            "target_sha256",
            "donor_sha256",
            "replacement_sha256",
            "payload_sha256",
        ],
        [
            {
                key: row[key]
                for key in (
                    "container_id",
                    "strategy",
                    "fixed_size",
                    "compressed_stream_size",
                    "zero_padding",
                    "target_sha256",
                    "donor_sha256",
                    "replacement_sha256",
                    "payload_sha256",
                )
            }
            for row in ui_texture_module.result_rows(plan)
        ],
    )
    patch_binary.write_tsv(
        log_directory / "run_summary.tsv",
        ["container_count", "mapping_count", "fixed_bytes"],
        [
            {
                "container_count": len(plan.containers),
                "mapping_count": plan.mapping_count,
                "fixed_bytes": sum(
                    len(result.replacement) for result in plan.containers
                ),
            }
        ],
    )


def write_external_translation_log(
    external_translation_module: object,
    plan: object,
    insertion_results: tuple[IsoInsertion, ...],
    log_directory: Path,
) -> None:
    log_directory.mkdir(parents=True, exist_ok=True)
    patch_binary.write_tsv(
        log_directory / "patch_log.tsv",
        [
            "target",
            "offset",
            "length",
            "original_hex",
            "new_hex",
            "mapping_id",
            "kind",
            "reason",
        ],
        external_translation_module.patch_log_rows(plan),
    )
    patch_binary.write_tsv(
        log_directory / "insertions.tsv",
        [
            "path",
            "extent",
            "byte_offset",
            "size",
            "sha256",
            "directory_record_offset",
            "udf_file_entry_offset",
            "udf_directory_record_offset",
        ],
        [
            {
                "path": result.path,
                "extent": result.extent,
                "byte_offset": f"0x{result.byte_offset:X}",
                "size": result.size,
                "sha256": result.sha256,
                "directory_record_offset": f"0x{result.directory_record_offset:X}",
                "udf_file_entry_offset": (
                    f"0x{result.udf_file_entry_offset:X}"
                    if result.udf_file_entry_offset is not None
                    else ""
                ),
                "udf_directory_record_offset": (
                    f"0x{result.udf_directory_record_offset:X}"
                    if result.udf_directory_record_offset is not None
                    else ""
                ),
            }
            for result in insertion_results
        ],
    )
    translation_module.write_json(
        log_directory / "external_translation_summary.json",
        plan.summary,
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
    insertions: dict[str, bytes],
    insertion_owners: dict[str, str],
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
                feature_selections=module.selections,
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
        if module.module == "ui_textures":
            plan, path = apply_ui_texture_package(
                module.input_path,
                module_id=module.module_id,
                roots=profile.roots,
                selection=module.selection,
                source=source,
                payloads=payloads,
                owners=owners,
            )
            results.append(
                {
                    "module": module,
                    "ui_texture_plan": plan,
                    "paths": [path],
                }
            )
            continue
        if module.module == "external_translation":
            if any("external_translation_plan" in item for item in results):
                raise ValueError(
                    "Profile may enable only one external_translation module"
                )
            (
                external_translation_module,
                plan,
                edit_count,
                paths,
            ) = apply_external_translation_package(
                module.input_path,
                module_id=module.module_id,
                roots=profile.roots,
                selection=module.selection,
                source=source,
                payloads=payloads,
                owners=owners,
                insertions=insertions,
                insertion_owners=insertion_owners,
            )
            results.append(
                {
                    "module": module,
                    "external_translation_module": external_translation_module,
                    "external_translation_plan": plan,
                    "external_translation_edits": edit_count,
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
                "feature_ids": ",".join(
                    selection.feature_id for selection in module.selections
                ),
                "selection_count": len(module.selections),
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
        if "ui_texture_plan" in item:
            plan = item["ui_texture_plan"]
            assert isinstance(plan, ui_texture_module.UiTexturePlan)
            write_ui_texture_log(plan, module_log)
        if "external_translation_plan" in item:
            insertion_results = item.get("insertion_results")
            if not isinstance(insertion_results, tuple) or not all(
                isinstance(result, IsoInsertion) for result in insertion_results
            ):
                raise RuntimeError(
                    f"Missing verified insertion results for {module.module_id}"
                )
            write_external_translation_log(
                item["external_translation_module"],
                item["external_translation_plan"],
                insertion_results,
                module_log,
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
        log_directory / "features.tsv",
        ["feature_id", "enabled", "name", "description", "reason"],
        [
            {
                "feature_id": feature.feature_id,
                "enabled": int(feature.enabled),
                "name": feature.name,
                "description": feature.description,
                "reason": feature.reason,
            }
            for feature in profile.features
        ],
    )
    enabled_features = {
        feature.feature_id for feature in profile.features if feature.enabled
    }
    patch_binary.write_tsv(
        log_directory / "feature_selections.tsv",
        [
            "feature_id", "active", "module_id", "selection_kind",
            "selection_id", "reason",
        ],
        [
            {
                "feature_id": selection.feature_id,
                "active": int(selection.feature_id in enabled_features),
                "module_id": selection.module_id,
                "selection_kind": selection.selection_kind,
                "selection_id": selection.selection_id,
                "reason": selection.reason,
            }
            for selection in profile.selections
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
            "feature_ids",
            "selection_count",
            "patched_paths",
        ],
        module_rows,
    )
    patch_binary.write_tsv(
        log_directory / "run_summary.tsv",
        [
            "timestamp_utc", "profile_id", "output_iso", "feature_count",
            "enabled_feature_count", "module_count",
        ],
        [
            {
                "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "profile_id": profile.manifest["profile_id"],
                "output_iso": output_iso_text.replace("\\", "/"),
                "feature_count": len(profile.features),
                "enabled_feature_count": len(enabled_features),
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
    insertions: dict[str, bytes] = {}
    insertion_owners: dict[str, str] = {}
    profile_results = apply_profile_modules(
        profile,
        source=source,
        payloads=payloads,
        owners=owners,
        insertions=insertions,
        insertion_owners=insertion_owners,
    )

    if not payloads and not insertions:
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

        udf_renames = {}
        if identity_items:
            identity = identity_items[0]["disc_identity"]
            assert isinstance(identity, disc_identity_module.DiscIdentity)
            udf_renames[identity.source_boot_path] = identity.replacement_boot_path
        composition = compose_filesystems(
            working_iso,
            insertions,
            udf_renames=udf_renames,
        )
        insertion_results = composition.insertions
        if identity_items:
            for rename in composition.udf_renames:
                identity_items[0]["identity_edits"].append(
                    {
                        "target": "<UDF root directory>",
                        "offset": f"0x{rename.identifier_offset:X}",
                        "length": len(rename.original_identifier),
                        "original_hex": rename.original_identifier.hex().upper(),
                        "new_hex": rename.replacement_identifier.hex().upper(),
                        "reason": "Mirror boot executable identifier in UDF tree",
                    }
                )
        if working_iso.stat().st_size != source.file_size:
            raise RuntimeError("Profile composition changed the ISO image size")
        results_by_owner: dict[str, list[IsoInsertion]] = {}
        for insertion in insertion_results:
            owner = insertion_owners[insertion.path]
            results_by_owner.setdefault(owner, []).append(insertion)
        for item in profile_results:
            module = item["module"]
            assert isinstance(module, ProfileModule)
            owned = results_by_owner.get(module.module_id)
            if owned:
                item["insertion_results"] = tuple(owned)

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
        source_tree.update((path, False) for path in insertions)
        result_tree = {(record.path, record.is_dir) for record in result.records}
        if result_tree != source_tree:
            raise RuntimeError(
                "Final ISO file tree differs from the source tree plus its declared "
                "identity rename and insertions"
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

        insertion_by_path = {item.path: item for item in insertion_results}
        if set(insertion_by_path) != set(insertions):
            raise RuntimeError("Final ISO insertion result set is incomplete")
        for path, payload in insertions.items():
            result_record = result.by_path.get(path)
            insertion = insertion_by_path[path]
            if (
                result_record is None
                or result_record.is_dir
                or result_record.extent != insertion.extent
                or result_record.size != len(payload)
                or result.read_file(result_record) != payload
            ):
                raise RuntimeError(f"Final ISO insertion verification failed: {path}")

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
        elif "ui_texture_plan" in item:
            plan = item["ui_texture_plan"]
            assert isinstance(plan, ui_texture_module.UiTexturePlan)
            detail = f", {len(plan.containers)} containers, {plan.mapping_count} mappings"
        elif "external_translation_plan" in item:
            detail = (
                f", {item['external_translation_edits']} edits, "
                f"{len(item.get('insertion_results', ()))} insertions"
            )
        elif "disc_identity" in item:
            detail = f", {len(item['identity_edits'])} edits"
        print(f"  {module.order:03d} {module.module_id} ({module.module}{detail})")
        for path in sorted(str(value) for value in item.get("paths", [])):
            print(f"    {green}{path}{reset}")
    print(f"Verified staged ISO: {building_iso_path(output_iso).name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
