#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .composer import CompositionResult, compose_assembly_plan
from .elf_identity import apply_elf_crc_discriminator
from .image_assembler.assembler import (
    assemble_image,
    building_image_path,
)
from .image_assembler.iso9660 import Iso9660, IsoInsertion, normalize_iso_path
from .module_pipeline import prepare_module_pipeline
from .modules import translation_importer as translation_importer_module
from .modules.binary_patcher import engine as binary_patcher_module
from .modules.string_patcher import engine as string_patcher_module
from .modules.texture_patcher import engine as texture_patcher_module
from .payload_builder import builder as payload_builder_module
from .payload_builder import integration as payload_integration_module
from .payload_builder.operations import ResidentPayloadBuild
from .profile import Profile, ProfileModule, load_profile
from scripts.lib.paths import load_paths


PATHS = load_paths(Path(__file__).resolve(), allow_missing=True)


@dataclass(frozen=True)
class ProfileBuildResult:
    results: tuple[dict[str, object], ...]
    payload_result: dict[str, object] | None
    identity_edits: tuple[dict[str, object], ...]
    staged_iso: Path


@dataclass(frozen=True)
class ProfileCompositionResult:
    results: tuple[dict[str, object], ...]
    payload_result: dict[str, object] | None
    composition: CompositionResult
    insertion_owners: dict[str, str]


def normalize(path: str) -> str:
    return normalize_iso_path(path)


def apply_binary_patch_set(
    package_directory: Path,
    *,
    package: binary_patcher_module.Package | None = None,
    roots: dict[str, Path],
    feature_id: str,
    source: Iso9660,
    payloads: dict[str, bytearray],
    owners: dict[str, str],
    allow_empty_enabled: bool = False,
) -> dict[str, object]:
    if package is None:
        package = binary_patcher_module.load_package(package_directory)
    target_data = binary_patcher_module.verify_package_data(package, roots)
    enabled_patch_ids = [
        patch.patch_id
        for patch in package.patches.values()
        if binary_patcher_module.patch_is_enabled(package, patch)
    ]
    if not enabled_patch_ids and allow_empty_enabled:
        return {
            "package": package,
            "selected": [],
            "selection_mode": "enabled",
            "edits": [],
            "patch_rows": [],
            "before_hashes": {},
            "after_hashes": {},
            "patched_paths": [],
        }
    selected = binary_patcher_module.selected_patch_ids(
        package, [], enabled=True
    )
    edits = binary_patcher_module.validate_selection(
        package, selected, for_apply=True
    )

    initial_buffers: dict[str, bytes | bytearray] = {}
    target_paths: dict[str, str] = {}
    for target_id in {item.destination_target_id for item in edits}:
        target = package.targets[target_id]
        path = normalize(target.path.as_posix())
        record = source.by_path.get(path)
        if record is None or record.is_dir:
            raise RuntimeError(
                f"Binary patch destination is not in the clean source ISO: {path}"
            )
        initial_buffers[target_id] = (
            payloads[path] if path in payloads else source.read_file(record)
        )
        target_paths[target_id] = path

    buffers, patch_rows, before_hashes = binary_patcher_module.compose_edits(
        package,
        target_data,
        edits,
        initial_buffers,
        feature_id=feature_id,
    )
    after_hashes: dict[str, str] = {}
    patched_paths: list[str] = []
    for target_id, data in buffers.items():
        path = target_paths[target_id]
        payloads[path] = data
        owners[path] = package.package_id
        after_hashes[target_id] = binary_patcher_module.data_sha256(data)
        patched_paths.append(path)

    return {
        "package": package,
        "selected": selected,
        "selection_mode": "enabled",
        "edits": edits,
        "patch_rows": patch_rows,
        "before_hashes": before_hashes,
        "after_hashes": after_hashes,
        "patched_paths": patched_paths,
    }


def apply_texture_patch_package(
    package_directory: Path,
    *,
    module_id: str,
    roots: dict[str, Path],
    source: Iso9660,
    payloads: dict[str, bytearray],
    owners: dict[str, str],
) -> tuple[texture_patcher_module.TexturePatchPlan, str]:
    if "na2" not in roots or "nun5" not in roots:
        raise ValueError("Texture-patcher module requires na2 and nun5 profile roots")
    if not all(
        root.is_dir() or root.is_file()
        for root in (roots["na2"], roots["nun5"])
    ):
        raise ValueError("Texture-patcher module roots must be extractions or ISOs")
    if not package_directory.is_dir():
        raise ValueError(f"Texture-patcher module input must be a directory: {package_directory}")

    plan = texture_patcher_module.build_texture_patch_plan(
        na2_root=roots["na2"],
        nun5_root=roots["nun5"],
        data_root=package_directory,
        selection=(),
    )
    path = "DATA/DATA.CVM"
    record = source.by_path.get(path)
    if record is None or record.is_dir:
        raise RuntimeError("Texture-patcher module requires DATA/DATA.CVM in the source ISO")
    data = payloads.get(path)
    if data is None:
        data = bytearray(source.read_file(record))
    plan.apply_to_cvm(data)
    payloads[path] = data
    owners[path] = module_id
    return plan, path


def write_binary_patch_log(
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
    assert isinstance(package, binary_patcher_module.Package)
    assert isinstance(selected, list)
    assert isinstance(edits, list)
    assert isinstance(before_hashes, dict)
    assert isinstance(after_hashes, dict)

    binary_patcher_module.write_tsv(
        log_directory / "patch_log.tsv",
        [
            "package_id", "feature_id", "group_id", "group_name",
            "patch_id", "evidence_id",
            "edit_id", "target_id", "path",
            "offset", "length", "original_hex", "new_hex", "operation", "outcome", "reason",
        ],
        result["patch_rows"],
    )
    binary_patcher_module.write_tsv(
        log_directory / "patch_selection.tsv",
        [
            "group_id", "group_name", "group_enabled", "patch_id",
            "patch_enabled", "effective_selected", "selection_mode",
            "evidence_id", "status", "confidence", "name",
        ],
        binary_patcher_module.patch_selection_rows(
            package,
            selected,
            selection_mode=str(result["selection_mode"]),
        ),
    )
    binary_patcher_module.write_tsv(
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
    binary_patcher_module.write_tsv(
        log_directory / "run_summary.tsv",
        [
            "timestamp_utc", "schema_version", "package_id",
            "output_iso", "log_directory", "group_count", "patch_count",
            "unique_patch_count", "edit_count",
        ],
        [{
            "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "schema_version": binary_patcher_module.BINARY_PATCHER_SCHEMA_VERSION,
            "package_id": package.package_id,
            "output_iso": output_iso_text.replace("\\", "/"),
            "log_directory": log_directory_text.replace("\\", "/"),
            "group_count": len(
                {
                    package.patches[patch_id].group_id
                    for patch_id in selected
                }
            ),
            "patch_count": len(selected),
            "unique_patch_count": len(set(selected)),
            "edit_count": len(edits),
        }],
    )


def write_texture_patch_log(
    plan: texture_patcher_module.TexturePatchPlan,
    log_directory: Path,
) -> None:
    log_directory.mkdir(parents=True, exist_ok=True)
    binary_patcher_module.write_tsv(
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
                "original_sha256": texture_patcher_module.sha256(result.original),
                "derivation": f"canonical_nun5_{result.strategy.strategy}",
                "new_sha256": texture_patcher_module.sha256(result.replacement),
                "mapping_ids": ",".join(result.mapping_ids),
                "reason": result.strategy.reason,
            }
            for result in plan.containers
        ],
    )
    binary_patcher_module.write_tsv(
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
            for row in texture_patcher_module.result_rows(plan)
        ],
    )
    binary_patcher_module.write_tsv(
        log_directory / "run_summary.tsv",
        ["container_count", "mapping_count", "fixed_bytes", "worker_count"],
        [
            {
                "container_count": len(plan.containers),
                "mapping_count": plan.mapping_count,
                "fixed_bytes": sum(
                    len(result.replacement) for result in plan.containers
                ),
                "worker_count": plan.worker_count,
            }
        ],
    )


def write_string_patch_plan_log(
    plan: string_patcher_module.StringPatchPlan,
    log_directory: Path,
) -> None:
    binary_patcher_module.write_tsv(
        log_directory / "external_strings.tsv",
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
        string_patcher_module.external_patch_log_rows(plan),
    )
    translation_importer_module.write_json(
        log_directory / "string_patch_summary.json",
        plan.summary,
    )


def write_payload_builder_log(
    result: dict[str, object],
    log_directory: Path,
    *,
    output_iso_text: str,
    workspace: Path,
) -> None:
    build = result["build"]
    assert isinstance(build, ResidentPayloadBuild)
    integration = result["binary_patch_result"]
    assert isinstance(integration, dict)
    write_binary_patch_log(
        integration,
        log_directory,
        output_iso_text=output_iso_text,
        log_directory_text=log_directory.relative_to(workspace).as_posix(),
    )
    binary_patcher_module.write_tsv(
        log_directory / "symbol_map.tsv",
        [
            "owner",
            "symbol",
            "kind",
            "file_offset",
            "runtime_address",
            "size",
            "sha256",
            "init",
        ],
        build.map_rows,
    )
    translation_importer_module.write_json(
        log_directory / "payload_summary.json", build.summary
    )
    insertion_results = result.get("insertion_results")
    if not isinstance(insertion_results, tuple) or len(insertion_results) != 1:
        raise RuntimeError("Payload builder is missing its verified image insertion")
    insertion = insertion_results[0]
    if not isinstance(insertion, IsoInsertion):
        raise RuntimeError("Payload builder insertion result has an invalid type")
    binary_patcher_module.write_tsv(
        log_directory / "insertion.tsv",
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
        [{
            "path": insertion.path,
            "extent": insertion.extent,
            "byte_offset": f"0x{insertion.byte_offset:X}",
            "size": insertion.size,
            "sha256": insertion.sha256,
            "directory_record_offset": f"0x{insertion.directory_record_offset:X}",
            "udf_file_entry_offset": (
                f"0x{insertion.udf_file_entry_offset:X}"
                if insertion.udf_file_entry_offset is not None else ""
            ),
            "udf_directory_record_offset": (
                f"0x{insertion.udf_directory_record_offset:X}"
                if insertion.udf_directory_record_offset is not None else ""
            ),
        }],
    )


def apply_profile_modules(
    profile: Profile,
    *,
    source: Iso9660,
    payloads: dict[str, bytearray],
    owners: dict[str, str],
    insertions: dict[str, bytes],
    insertion_owners: dict[str, str],
    payload_padding: int = 0,
) -> tuple[list[dict[str, object]], dict[str, object] | None]:
    pipeline = prepare_module_pipeline(profile, payload_padding=payload_padding)
    ordered_modules = pipeline.ordered_modules
    import_plans = pipeline.import_plans
    string_plans = pipeline.string_plans
    derived_string_plans = pipeline.derived_string_plans
    runtime_injection_declarations = pipeline.runtime_injection_declarations
    runtime_injection_packages = pipeline.runtime_injection_packages
    payload_build = pipeline.payload_build

    results: list[dict[str, object]] = []
    for module in ordered_modules:
        if module.module == "string_patcher":
            string_plan = string_plans.get(module.module_id)
            compiled_package = (
                string_plan.package
                if string_plan is not None
                else string_patcher_module.build_binary_package(module.input_path)
            )
            result = apply_binary_patch_set(
                module.input_path,
                package=compiled_package,
                roots=profile.roots,
                feature_id=module.feature_id,
                source=source,
                payloads=payloads,
                owners=owners,
            )
            paths = list(result["patched_paths"])
            results.append(
                {
                    "module": module,
                    "binary_patch_result": result,
                    "string_patch_plan": string_plan,
                    "paths": paths,
                }
            )
            continue
        if module.module == "binary_patcher":
            result = apply_binary_patch_set(
                module.input_path,
                roots=profile.roots,
                feature_id=module.feature_id,
                source=source,
                payloads=payloads,
                owners=owners,
                allow_empty_enabled=True,
            )
            results.append(
                {
                    "module": module,
                    "binary_patch_result": result,
                    "paths": result["patched_paths"],
                }
            )
            continue
        if module.module == "runtime_injector":
            declaration = runtime_injection_declarations[module.module_id]
            result = apply_binary_patch_set(
                module.input_path,
                package=runtime_injection_packages[module.module_id],
                roots=profile.roots,
                feature_id=module.feature_id,
                source=source,
                payloads=payloads,
                owners=owners,
                allow_empty_enabled=True,
            )
            results.append(
                {
                    "module": module,
                    "runtime_injection_declaration": declaration,
                    "binary_patch_result": result,
                    "paths": result["patched_paths"],
                }
            )
            continue
        if module.module == "translation_importer":
            plan = import_plans[module.module_id]
            item: dict[str, object] = {
                "module": module,
                "translation_import_plan": plan,
                "translation_import_rows": len(plan.import_rows),
                "paths": [],
            }
            derived = derived_string_plans.get(module.module_id)
            if derived is not None:
                derived_result = apply_binary_patch_set(
                    Path(string_patcher_module.__file__).resolve().parent,
                    package=derived.package,
                    roots=profile.roots,
                    feature_id=module.feature_id,
                    source=source,
                    payloads=payloads,
                    owners=owners,
                    allow_empty_enabled=False,
                )
                item["derived_string_patch_result"] = derived_result
                item["string_patch_plan"] = derived
                item["paths"] = list(derived_result["patched_paths"])
            results.append(item)
            continue
        if module.module == "texture_patcher":
            plan, path = apply_texture_patch_package(
                module.input_path,
                module_id=module.module_id,
                roots=profile.roots,
                source=source,
                payloads=payloads,
                owners=owners,
            )
            results.append(
                {
                    "module": module,
                    "texture_patch_plan": plan,
                    "paths": [path],
                }
            )
            continue
        raise AssertionError(module.module)

    payload_result: dict[str, object] | None = None
    if payload_build is not None:
        config = payload_builder_module.load_config()
        boot_path = normalize(profile.identity.source_boot_path)
        boot_record = source.by_path.get(boot_path)
        if boot_record is None or boot_record.is_dir:
            raise RuntimeError(f"Payload integration requires source boot ELF: {boot_path}")
        clean_boot = source.read_file(boot_record)
        integration_patches = payload_integration_module.build_integration_patches(
            payload_build,
            config=config,
            boot_path=boot_path,
            clean_boot=clean_boot,
        )
        integration_package = payload_integration_module.build_integration_package(
            integration_patches,
            boot_path=boot_path,
            clean_boot=clean_boot,
        )
        integration_result = apply_binary_patch_set(
            Path(payload_builder_module.__file__).resolve().parent,
            package=integration_package,
            roots=profile.roots,
            feature_id="payload_builder",
            source=source,
            payloads=payloads,
            owners=owners,
        )
        path = normalize(payload_build.output_path)
        if path in insertions:
            raise RuntimeError(f"Multiple producers declare image insertion path: {path}")
        insertions[path] = payload_build.payload
        insertion_owners[path] = "payload_builder"
        payload_result = {
            "build": payload_build,
            "binary_patch_result": integration_result,
            "paths": list(integration_result["patched_paths"]) + [path],
        }
    return results, payload_result


def write_profile_log(
    profile: Profile,
    results: list[dict[str, object]],
    payload_result: dict[str, object] | None,
    log_directory: Path,
    *,
    workspace: Path,
    output_iso_text: str,
    identity_edits: tuple[dict[str, object], ...],
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
                "input_sha256": module.input_sha256,
                "feature_id": module.feature_id,
                "patched_paths": ",".join(sorted(str(path) for path in paths)),
            }
        )
        module_log = log_directory / module.module_id
        if "binary_patch_result" in item:
            write_binary_patch_log(
                item["binary_patch_result"],
                module_log,
                output_iso_text=output_iso_text,
                log_directory_text=module_log.relative_to(workspace).as_posix(),
            )
        if "derived_string_patch_result" in item:
            derived_log = module_log / "string_patcher"
            write_binary_patch_log(
                item["derived_string_patch_result"],
                derived_log,
                output_iso_text=output_iso_text,
                log_directory_text=derived_log.relative_to(workspace).as_posix(),
            )
        if "translation_import_plan" in item:
            plan = item["translation_import_plan"]
            assert isinstance(
                plan, translation_importer_module.TranslationImportPlan
            )
            module_log.mkdir(parents=True, exist_ok=True)
            translation_importer_module.write_import_tsv(
                module_log / "translation_imports.tsv",
                plan.import_rows,
                allow_empty=False,
            )
            translation_importer_module.write_json(
                module_log / "translation_import_summary.json", plan.summary
            )
        if "texture_patch_plan" in item:
            plan = item["texture_patch_plan"]
            assert isinstance(plan, texture_patcher_module.TexturePatchPlan)
            write_texture_patch_log(plan, module_log)
        if item.get("string_patch_plan") is not None:
            plan = item["string_patch_plan"]
            assert isinstance(plan, string_patcher_module.StringPatchPlan)
            string_log = (
                module_log / "string_patcher"
                if "derived_string_patch_result" in item
                else module_log
            )
            write_string_patch_plan_log(plan, string_log)
    if payload_result is not None:
        write_payload_builder_log(
            payload_result,
            log_directory / "payload_builder",
            output_iso_text=output_iso_text,
            workspace=workspace,
        )
    binary_patcher_module.write_tsv(
        log_directory / "features.tsv",
        [
            "feature_id",
            "input",
            "expected_sha256",
            "actual_sha256",
            "hash_check",
        ],
        [
            {
                "feature_id": feature.feature_id,
                "input": feature.input_path.relative_to(workspace).as_posix(),
                "expected_sha256": feature.expected_sha256,
                "actual_sha256": feature.actual_sha256,
                "hash_check": (
                    "bypassed" if feature.hash_check_bypassed else "verified"
                ),
            }
            for feature in profile.features
        ],
    )
    identity_log = log_directory / "identity"
    binary_patcher_module.write_tsv(
        identity_log / "patch_log.tsv",
        [
            "target",
            "offset",
            "length",
            "original_hex",
            "new_hex",
            "reason",
            "owner",
        ],
        identity_edits,
    )
    binary_patcher_module.write_tsv(
        identity_log / "run_summary.tsv",
        [
            "source_boot_path",
            "output_boot_path",
            "system_cnf_path",
            "memory_card_title_offset",
            "memory_card_title_capacity",
            "memory_card_title_encoding",
            "output_memory_card_title",
            "edit_count",
        ],
        [
            {
                "source_boot_path": profile.identity.source_boot_path,
                "output_boot_path": profile.identity.output_boot_path,
                "system_cnf_path": profile.identity.system_cnf_path,
                "memory_card_title_offset": (
                    f"0x{profile.identity.memory_card_title_offset:X}"
                ),
                "memory_card_title_capacity": (
                    profile.identity.memory_card_title_capacity
                ),
                "memory_card_title_encoding": (
                    profile.identity.memory_card_title_encoding
                ),
                "output_memory_card_title": (
                    profile.identity.output_memory_card_title
                ),
                "edit_count": len(identity_edits),
            }
        ],
    )
    binary_patcher_module.write_tsv(
        log_directory / "module_results.tsv",
        [
            "module_id",
            "order",
            "module",
            "input",
            "input_sha256",
            "feature_id",
            "patched_paths",
        ],
        module_rows,
    )
    binary_patcher_module.write_tsv(
        log_directory / "run_summary.tsv",
        [
            "timestamp_utc", "profile_id", "output_iso", "feature_count",
            "module_count",
        ],
        [
            {
                "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "profile_id": profile.profile_id,
                "output_iso": output_iso_text.replace("\\", "/"),
                "feature_count": len(profile.features),
                "module_count": len(results),
            }
        ],
    )


def compose_profile_candidate(
    *,
    source_iso: Path,
    profile: Profile,
    payload_padding: int = 0,
    boot_elf_crc_discriminator: int = 0,
) -> ProfileCompositionResult:
    """Compose and conflict-check one profile without staging an image."""
    source_iso = source_iso.resolve()
    if not source_iso.is_file():
        raise FileNotFoundError(source_iso)

    source = Iso9660(source_iso)
    payloads: dict[str, bytearray] = {}
    owners: dict[str, str] = {}
    insertions: dict[str, bytes] = {}
    insertion_owners: dict[str, str] = {}
    profile_results, payload_result = apply_profile_modules(
        profile,
        source=source,
        payloads=payloads,
        owners=owners,
        insertions=insertions,
        insertion_owners=insertion_owners,
        payload_padding=payload_padding,
    )
    discriminator_edits: tuple[dict[str, object], ...] = ()
    if boot_elf_crc_discriminator:
        boot_path = normalize(profile.identity.source_boot_path)
        boot_record = source.by_path.get(boot_path)
        if boot_record is None or boot_record.is_dir:
            raise RuntimeError(
                f"Boot ELF CRC discriminator requires source boot ELF: {boot_path}"
            )
        boot_data = payloads.get(boot_path, bytearray(source.read_file(boot_record)))
        marked_boot, edit = apply_elf_crc_discriminator(
            boot_data,
            boot_elf_crc_discriminator,
        )
        assert edit is not None
        payloads[boot_path] = marked_boot
        owners.setdefault(boot_path, "build.variant")
        discriminator_edits = (
            {
                "target": boot_path,
                "offset": f"0x{edit.offset:X}",
                "length": len(edit.replacement),
                "original_hex": edit.original.hex().upper(),
                "new_hex": edit.replacement.hex().upper(),
                "reason": (
                    "Assign this build role a distinct PCSX2 boot-ELF CRC without "
                    "changing runtime-loaded data"
                ),
                "owner": "build.variant",
            },
        )
    composition = compose_assembly_plan(
        source=source,
        identity=profile.identity,
        payloads=payloads,
        owners=owners,
        insertions=insertions,
        insertion_owners=insertion_owners,
    )
    if discriminator_edits:
        composition = CompositionResult(
            plan=composition.plan,
            identity_edits=composition.identity_edits + discriminator_edits,
        )
    return ProfileCompositionResult(
        results=tuple(profile_results),
        payload_result=payload_result,
        composition=composition,
        insertion_owners=insertion_owners,
    )


def build_profile_candidate(
    *,
    source_iso: Path,
    output_iso: Path,
    profile: Profile,
    workspace: Path,
    profile_log_directory: Path | None,
    payload_padding: int = 0,
    boot_elf_crc_discriminator: int = 0,
) -> ProfileBuildResult:
    """Compose and verify one staged profile image without promoting it."""
    source_iso = source_iso.resolve()
    output_iso = output_iso.resolve()
    workspace = workspace.resolve()
    if not source_iso.is_file():
        raise FileNotFoundError(source_iso)
    if source_iso == output_iso:
        raise ValueError("Source and output ISO paths must differ")
    if profile_log_directory is not None and profile_log_directory.exists():
        raise FileExistsError(profile_log_directory)

    composed = compose_profile_candidate(
        source_iso=source_iso,
        profile=profile,
        payload_padding=payload_padding,
        boot_elf_crc_discriminator=boot_elf_crc_discriminator,
    )
    profile_results = list(composed.results)
    payload_result = composed.payload_result
    composition = composed.composition
    assembly = assemble_image(source_iso, output_iso, composition.plan)
    results_by_owner: dict[str, list[IsoInsertion]] = {}
    for insertion in assembly.insertions:
        owner = composed.insertion_owners[insertion.path]
        results_by_owner.setdefault(owner, []).append(insertion)
    for item in profile_results:
        module = item["module"]
        assert isinstance(module, ProfileModule)
        owned = results_by_owner.get(module.module_id)
        if owned:
            item["insertion_results"] = tuple(owned)
    if payload_result is not None:
        payload_result["insertion_results"] = tuple(
            results_by_owner.get("payload_builder", ())
        )

    identity_edits = list(composition.identity_edits)
    identity_edits.extend(assembly.iso9660_renames)
    identity_edits.extend(
        {
            "target": "<UDF directory>",
            "offset": f"0x{rename.identifier_offset:X}",
            "length": len(rename.original_identifier),
            "original_hex": rename.original_identifier.hex().upper(),
            "new_hex": rename.replacement_identifier.hex().upper(),
            "reason": "Mirror the profile identity rename in the UDF tree",
            "owner": "profile.identity",
        }
        for rename in assembly.udf_renames
    )
    try:
        if profile_log_directory is not None:
            try:
                output_iso_text = output_iso.relative_to(workspace).as_posix()
            except ValueError:
                output_iso_text = output_iso.name
            write_profile_log(
                profile,
                profile_results,
                payload_result,
                profile_log_directory,
                workspace=workspace,
                output_iso_text=output_iso_text,
                identity_edits=tuple(identity_edits),
            )
    except BaseException:
        staged = building_image_path(output_iso)
        if staged.exists() or staged.is_symlink():
            staged.unlink()
        raise

    return ProfileBuildResult(
        results=tuple(profile_results),
        payload_result=payload_result,
        identity_edits=tuple(identity_edits),
        staged_iso=building_image_path(output_iso),
    )


def print_profile_summary(
    profile: Profile,
    profile_results: tuple[dict[str, object], ...] | list[dict[str, object]],
    payload_result: dict[str, object] | None,
) -> None:
    green = "\033[32m"
    reset = "\033[0m"
    print(f"Applied profile: {profile.profile_id}")
    bypassed_features = [
        feature for feature in profile.features if feature.hash_check_bypassed
    ]
    for feature in bypassed_features:
        print(
            "Feature hash check bypassed: "
            f"{feature.feature_id} (actual SHA-256 {feature.actual_sha256})"
        )
    for item in profile_results:
        module = item["module"]
        assert isinstance(module, ProfileModule)
        detail = ""
        if "binary_patch_result" in item:
            detail = f", {len(item['binary_patch_result']['edits'])} edits"
        elif "translation_import_rows" in item:
            detail = f", {item['translation_import_rows']} imports"
        elif "texture_patch_plan" in item:
            plan = item["texture_patch_plan"]
            assert isinstance(plan, texture_patcher_module.TexturePatchPlan)
            detail = f", {len(plan.containers)} containers, {plan.mapping_count} mappings"
        if "derived_string_patch_result" in item:
            detail += (
                f", {len(item['derived_string_patch_result']['edits'])} "
                "derived string edits"
            )
        print(f"  {module.order:03d} {module.module_id} ({module.module}{detail})")
        for path in sorted(str(value) for value in item.get("paths", [])):
            print(f"    {green}{path}{reset}")
    if payload_result is not None:
        payload_build = payload_result["build"]
        assert isinstance(payload_build, ResidentPayloadBuild)
        print(
            "  payload_builder "
            f"({len(payload_build.symbols)} symbols, {len(payload_build.payload)} bytes)"
        )
        for path in sorted(str(value) for value in payload_result.get("paths", [])):
            print(f"    {green}{path}{reset}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a verified staged NA2 ISO from one hash-pinned profile."
    )
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--profile-log-directory", type=Path)
    parser.add_argument(
        "--payload-padding",
        type=int,
        default=0,
        help="Test-only aligned resident-payload padding in bytes.",
    )
    parser.add_argument(
        "--boot-elf-crc-discriminator",
        type=lambda value: int(value, 0),
        default=0,
        help=(
            "Test-build-only 32-bit discriminator written to runtime-unloaded "
            "boot-ELF padding."
        ),
    )
    parser.add_argument(
        "--compose-only",
        action="store_true",
        help="Compose and conflict-check the profile without staging an ISO.",
    )
    args = parser.parse_args()

    workspace = PATHS.repository
    source_iso = args.source.resolve()
    if not source_iso.is_file():
        raise FileNotFoundError(source_iso)

    profile_path = args.profile if args.profile.is_absolute() else workspace / args.profile
    profile = load_profile(profile_path, workspace)
    if args.compose_only:
        composed = compose_profile_candidate(
            source_iso=source_iso,
            profile=profile,
            payload_padding=args.payload_padding,
            boot_elf_crc_discriminator=args.boot_elf_crc_discriminator,
        )
        print_profile_summary(profile, composed.results, composed.payload_result)
        plan = composed.composition.plan
        print(f"  identity ({len(composed.composition.identity_edits)} edits)")
        print(
            "Validated composition: "
            f"{len(plan.replacements)} replacements, "
            f"{len(plan.insertions)} insertions, "
            f"{len(plan.renames)} renames; no ISO staged."
        )
        return 0

    if args.output is None:
        parser.error("--output is required unless --compose-only is used")
    if args.profile_log_directory is None:
        parser.error(
            "--profile-log-directory is required unless --compose-only is used"
        )
    output_iso = args.output.resolve()
    if source_iso == output_iso:
        raise ValueError("Source and output ISO paths must differ")
    profile_log_directory = binary_patcher_module.command_relative_path(
        str(args.profile_log_directory), "--profile-log-directory", workspace
    )
    if profile_log_directory.exists():
        raise FileExistsError(profile_log_directory)

    build = build_profile_candidate(
        source_iso=source_iso,
        output_iso=output_iso,
        profile=profile,
        workspace=workspace,
        profile_log_directory=profile_log_directory,
        payload_padding=args.payload_padding,
        boot_elf_crc_discriminator=args.boot_elf_crc_discriminator,
    )
    profile_results = build.results
    payload_result = build.payload_result

    print_profile_summary(profile, profile_results, payload_result)
    print(f"  identity ({len(build.identity_edits)} edits)")
    print(f"Verified staged ISO: {build.staged_iso.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
