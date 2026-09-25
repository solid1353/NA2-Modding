#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from . import catalog as catalog_module
from .composer import CompositionResult, compose_assembly_plan
from ..modules.image_assembler.assembler import assemble_image
from ..modules.image_assembler.iso9660 import Iso9660, IsoInsertion, normalize_iso_path
from .module_pipeline import prepare_module_pipeline
from ..modules import translation_importer as translation_importer_module
from ..modules.binary_patcher import engine as binary_patcher_module
from ..modules.string_patcher import engine as string_patcher_module
from ..modules.texture_patcher import engine as texture_patcher_module
from ..modules.payload_builder import builder as payload_builder_module
from ..modules.payload_builder import integration as payload_integration_module
from ..modules.payload_builder.operations import ResidentPayloadBuild
from .configuration import (
    BuildConfiguration,
    ModuleInvocation,
    SOURCE_BOOT_PATH,
    SYSTEM_CNF_PATH,
    load_configuration,
)
from scripts.lib.paths import load_paths


PATHS = None


@dataclass(frozen=True)
class ConfigurationBuildResult:
    results: tuple[dict[str, object], ...]
    payload_result: dict[str, object] | None
    identity_edits: tuple[dict[str, object], ...]
    output_iso: Path


@dataclass(frozen=True)
class ConfigurationCompositionResult:
    results: tuple[dict[str, object], ...]
    payload_result: dict[str, object] | None
    composition: CompositionResult
    insertion_owners: dict[str, str]


def normalize(path: str) -> str:
    return normalize_iso_path(path)


def apply_binary_patch_set(
    *,
    package: binary_patcher_module.Package,
    roots: dict[str, Path],
    feature_id: str,
    source: Iso9660,
    payloads: dict[str, bytearray],
    owners: dict[str, str],
    allow_empty: bool = False,
) -> dict[str, object]:
    target_data = binary_patcher_module.verify_package_data(package, roots)
    if not package.patches and allow_empty:
        return {
            "package": package,
            "edits": [],
            "patch_rows": [],
            "before_hashes": {},
            "after_hashes": {},
            "patched_paths": [],
        }
    edits = binary_patcher_module.ordered_edits(package)

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
    insertions: dict[str, bytes],
    insertion_owners: dict[str, str],
) -> tuple[texture_patcher_module.ExternalTexturePackPlan, str]:
    if not package_directory.is_dir():
        raise ValueError(f"Texture-patcher module input must be a directory: {package_directory}")

    plan = texture_patcher_module.build_external_texture_pack(package_directory)
    path = texture_patcher_module.EXTERNAL_PACK_PATH
    if path in insertions:
        raise RuntimeError(f"Duplicate image insertion: {path}")
    insertions[path] = plan.payload
    insertion_owners[path] = module_id
    return plan, path


def write_binary_patch_log(
    result: dict[str, object],
    log_directory: Path,
    *,
    output_iso_text: str,
    log_directory_text: str,
) -> None:
    package = result["package"]
    edits = result["edits"]
    before_hashes = result["before_hashes"]
    after_hashes = result["after_hashes"]
    assert isinstance(package, binary_patcher_module.Package)
    assert isinstance(edits, list)
    assert isinstance(before_hashes, dict)
    assert isinstance(after_hashes, dict)

    binary_patcher_module.write_tsv(
        log_directory / "patch_log.tsv",
        [
            "package_id", "feature_id", "group_id", "patch_id", "evidence_id",
            "edit_id", "target_id", "path",
            "offset", "length", "original_hex", "new_hex", "operation", "outcome", "reason",
        ],
        result["patch_rows"],
    )
    binary_patcher_module.write_tsv(
        log_directory / "patch_inventory.tsv",
        ["group_id", "patch_id", "evidence_id"],
        binary_patcher_module.patch_inventory_rows(package),
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
            "timestamp_utc", "package_id",
            "output_iso", "log_directory", "group_count", "patch_count",
            "edit_count",
        ],
        [{
            "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "package_id": package.package_id,
            "output_iso": output_iso_text.replace("\\", "/"),
            "log_directory": log_directory_text.replace("\\", "/"),
            "group_count": len(
                {
                    patch.group_id
                    for patch in package.patches.values()
                }
            ),
            "patch_count": len(package.patches),
            "edit_count": len(edits),
        }],
    )


def write_texture_patch_log(
    plan: texture_patcher_module.ExternalTexturePackPlan,
    log_directory: Path,
    insertion: IsoInsertion,
) -> None:
    log_directory.mkdir(parents=True, exist_ok=True)
    binary_patcher_module.write_tsv(
        log_directory / "patch_log.tsv",
        [
            "pack",
            "member",
            "sector",
            "length",
            "asset_sha256",
        ],
        [
            {
                "pack": texture_patcher_module.EXTERNAL_PACK_PATH,
                "member": result.spec.path,
                "sector": result.pack_sector,
                "length": len(result.replacement),
                "asset_sha256": texture_patcher_module.sha256(result.replacement),
            }
            for result in plan.containers
        ],
    )
    binary_patcher_module.write_tsv(
        log_directory / "container_summary.tsv",
        [
            "container_id",
            "fixed_size",
            "compressed_stream_size",
            "zero_padding",
            "asset_sha256",
            "payload_sha256",
            "pack_sector",
            "pack_sectors",
        ],
        [
            {
                key: row[key]
                for key in (
                    "container_id",
                    "fixed_size",
                    "compressed_stream_size",
                    "zero_padding",
                    "asset_sha256",
                    "payload_sha256",
                    "pack_sector",
                    "pack_sectors",
                )
            }
            for row in texture_patcher_module.result_rows(plan)
        ],
    )
    binary_patcher_module.write_tsv(
        log_directory / "run_summary.tsv",
        [
            "container_count",
            "fixed_bytes",
            "pack_bytes",
            "pack_sha256",
            "pack_extent",
        ],
        [
            {
                "container_count": len(plan.containers),
                "fixed_bytes": sum(
                    len(result.replacement) for result in plan.containers
                ),
                "pack_bytes": len(plan.payload),
                "pack_sha256": insertion.sha256,
                "pack_extent": insertion.extent,
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


def apply_configuration_modules(
    configuration: BuildConfiguration,
    *,
    source: Iso9660,
    payloads: dict[str, bytearray],
    owners: dict[str, str],
    insertions: dict[str, bytes],
    insertion_owners: dict[str, str],
) -> tuple[list[dict[str, object]], dict[str, object] | None]:
    pipeline = prepare_module_pipeline(configuration)
    ordered_modules = pipeline.ordered_modules
    import_plans = pipeline.import_plans
    derived_string_plans = pipeline.derived_string_plans
    runtime_injection_declarations = pipeline.runtime_injection_declarations
    runtime_injection_packages = pipeline.runtime_injection_packages
    payload_build = pipeline.payload_build

    results: list[dict[str, object]] = []
    for module in ordered_modules:
        if module.module == "binary_patcher":
            package = catalog_module.load_binary_package(
                configuration.selection,
                module.feature_id,
                configuration.targets_path,
                configuration.selection.catalog_path.parent.parent,
                configuration.selection.catalog_path.parent
                / "infrastructure"
                / "modules"
                / "binary_patcher"
                / "operations",
            )
            result = apply_binary_patch_set(
                package=package,
                roots=configuration.roots,
                feature_id=module.feature_id,
                source=source,
                payloads=payloads,
                owners=owners,
                allow_empty=True,
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
                package=runtime_injection_packages[module.module_id],
                roots=configuration.roots,
                feature_id=module.feature_id,
                source=source,
                payloads=payloads,
                owners=owners,
                allow_empty=True,
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
                    package=derived.package,
                    roots=configuration.roots,
                    feature_id=module.feature_id,
                    source=source,
                    payloads=payloads,
                    owners=owners,
                    allow_empty=False,
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
                insertions=insertions,
                insertion_owners=insertion_owners,
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
        boot_path = SOURCE_BOOT_PATH
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
            package=integration_package,
            roots=configuration.roots,
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


def write_configuration_log(
    configuration: BuildConfiguration,
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
        assert isinstance(module, ModuleInvocation)
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
            assert isinstance(
                plan, texture_patcher_module.ExternalTexturePackPlan
            )
            insertion_results = item.get("insertion_results")
            if not isinstance(insertion_results, tuple) or len(insertion_results) != 1:
                raise RuntimeError(
                    "Texture pack is missing its verified image insertion"
                )
            insertion = insertion_results[0]
            if not isinstance(insertion, IsoInsertion):
                raise RuntimeError("Texture pack insertion result has an invalid type")
            write_texture_patch_log(plan, module_log, insertion)
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
            "input_sha256",
        ],
        [
            {
                "feature_id": feature.feature_id,
                "input_sha256": feature.input_sha256,
            }
            for feature in configuration.features
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
            "edit_count",
        ],
        [
            {
                "source_boot_path": SOURCE_BOOT_PATH,
                "output_boot_path": configuration.output_boot_path,
                "system_cnf_path": SYSTEM_CNF_PATH,
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
    summary = log_directory / "run_summary.tsv"
    pending_summary = log_directory / "run_summary.pending.tsv"
    try:
        binary_patcher_module.write_tsv(
            pending_summary,
            [
                "timestamp_utc", "configuration_id", "output_iso", "feature_count",
                "module_count",
            ],
            [
                {
                    "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "configuration_id": configuration.configuration_id,
                    "output_iso": output_iso_text.replace("\\", "/"),
                    "feature_count": len(configuration.features),
                    "module_count": len(results),
                }
            ],
        )
        pending_summary.replace(summary)
    finally:
        try:
            pending_summary.unlink(missing_ok=True)
        except OSError as error:
            print(
                f"WARNING: Pending configuration summary could not be removed: {error}",
                file=sys.stderr,
            )


def compose_configuration_candidate(
    *,
    source_iso: Path,
    configuration: BuildConfiguration,
) -> ConfigurationCompositionResult:
    """Compose and conflict-check one configuration without staging an image."""
    source_iso = source_iso.resolve()
    if not source_iso.is_file():
        raise FileNotFoundError(source_iso)
    source = Iso9660(source_iso)
    payloads: dict[str, bytearray] = {}
    owners: dict[str, str] = {}
    insertions: dict[str, bytes] = {}
    insertion_owners: dict[str, str] = {}
    for _node, patch_id, image_file in catalog_module.selected_image_files(
        configuration.selection
    ):
        path = normalize_iso_path(image_file["path"])
        asset = (
            configuration.selection.catalog_path.parent.parent / image_file["asset"]
        ).resolve()
        payload = asset.read_bytes()
        digest = hashlib.sha256(payload).hexdigest().upper()
        if digest != image_file["sha256"]:
            raise ValueError(
                f"{patch_id}: image file {asset} SHA-256 {digest} "
                f"does not match {image_file['sha256']}"
            )
        if path in insertions:
            raise ValueError(f"Duplicate image insertion: {path}")
        insertions[path] = payload
        insertion_owners[path] = patch_id
    configuration_results, payload_result = apply_configuration_modules(
        configuration,
        source=source,
        payloads=payloads,
        owners=owners,
        insertions=insertions,
        insertion_owners=insertion_owners,
    )
    composition = compose_assembly_plan(
        source=source,
        output_boot_path=configuration.output_boot_path,
        identity_owner=configuration.identity_patch_id or "image_assembler",
        payloads=payloads,
        owners=owners,
        insertions=insertions,
        insertion_owners=insertion_owners,
    )
    return ConfigurationCompositionResult(
        results=tuple(configuration_results),
        payload_result=payload_result,
        composition=composition,
        insertion_owners=insertion_owners,
    )


def build_configuration_candidate(
    *,
    source_iso: Path,
    output_iso: Path,
    configuration: BuildConfiguration,
    workspace: Path,
    configuration_log_directory: Path | None,
) -> ConfigurationBuildResult:
    """Compose and verify one physical configuration image."""
    source_iso = source_iso.resolve()
    output_iso = output_iso.resolve()
    workspace = workspace.resolve()
    if not source_iso.is_file():
        raise FileNotFoundError(source_iso)
    if source_iso == output_iso:
        raise ValueError("Source and output ISO paths must differ")
    if configuration_log_directory is not None and configuration_log_directory.exists():
        raise FileExistsError(configuration_log_directory)

    composed = compose_configuration_candidate(
        source_iso=source_iso,
        configuration=configuration,
    )
    configuration_results = list(composed.results)
    payload_result = composed.payload_result
    composition = composed.composition
    assembly = assemble_image(source_iso, output_iso, composition.plan)
    results_by_owner: dict[str, list[IsoInsertion]] = {}
    for insertion in assembly.insertions:
        owner = composed.insertion_owners[insertion.path]
        results_by_owner.setdefault(owner, []).append(insertion)
    for item in configuration_results:
        module = item["module"]
        assert isinstance(module, ModuleInvocation)
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
            "reason": "Mirror the selected disc identity in the UDF tree",
            "owner": configuration.identity_patch_id,
        }
        for rename in assembly.udf_renames
    )
    if configuration_log_directory is not None:
        try:
            output_iso_text = output_iso.relative_to(workspace).as_posix()
        except ValueError:
            output_iso_text = output_iso.name
        try:
            write_configuration_log(
                configuration,
                configuration_results,
                payload_result,
                configuration_log_directory,
                workspace=workspace,
                output_iso_text=output_iso_text,
                identity_edits=tuple(identity_edits),
            )
        except OSError as error:
            print(
                f"WARNING: Configuration log could not be written: {error}",
                file=sys.stderr,
            )

    return ConfigurationBuildResult(
        results=tuple(configuration_results),
        payload_result=payload_result,
        identity_edits=tuple(identity_edits),
        output_iso=output_iso,
    )


def print_configuration_summary(
    configuration: BuildConfiguration,
    configuration_results: tuple[dict[str, object], ...] | list[dict[str, object]],
    payload_result: dict[str, object] | None,
) -> None:
    green = "\033[32m"
    reset = "\033[0m"
    print(f"Applied configuration: {configuration.configuration_id}")
    for item in configuration_results:
        module = item["module"]
        assert isinstance(module, ModuleInvocation)
        detail = ""
        if "binary_patch_result" in item:
            detail = f", {len(item['binary_patch_result']['edits'])} edits"
        elif "translation_import_rows" in item:
            detail = f", {item['translation_import_rows']} imports"
        elif "texture_patch_plan" in item:
            plan = item["texture_patch_plan"]
            assert isinstance(
                plan, texture_patcher_module.ExternalTexturePackPlan
            )
            detail = (
                f", {len(plan.containers)} containers, "
                f"{len(plan.payload)} external bytes"
            )
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
        description="Build a verified staged NA2 ISO from one configuration."
    )
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--configuration", required=True, type=Path)
    parser.add_argument("--configuration-log-directory", type=Path)
    parser.add_argument(
        "--compose-only",
        action="store_true",
        help="Compose and conflict-check the configuration without staging an ISO.",
    )
    args = parser.parse_args()
    paths = PATHS or load_paths(Path(__file__).resolve(), allow_missing=True)
    workspace = paths.repository
    source_iso = args.source.resolve()
    if not source_iso.is_file():
        raise FileNotFoundError(source_iso)

    configuration_path = (
        args.configuration
        if args.configuration.is_absolute()
        else workspace / args.configuration
    )
    configuration = load_configuration(
        configuration_path,
        workspace,
        paths.path("builder"),
    )
    if args.compose_only:
        composed = compose_configuration_candidate(
            source_iso=source_iso,
            configuration=configuration,
        )
        print_configuration_summary(
            configuration, composed.results, composed.payload_result
        )
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
    if args.configuration_log_directory is None:
        parser.error(
            "--configuration-log-directory is required unless --compose-only is used"
        )
    output_iso = args.output.resolve()
    if source_iso == output_iso:
        raise ValueError("Source and output ISO paths must differ")
    configuration_log_directory = binary_patcher_module.command_relative_path(
        str(args.configuration_log_directory),
        "--configuration-log-directory",
        workspace,
    )

    build = build_configuration_candidate(
        source_iso=source_iso,
        output_iso=output_iso,
        configuration=configuration,
        workspace=workspace,
        configuration_log_directory=configuration_log_directory,
    )
    configuration_results = build.results
    payload_result = build.payload_result

    print_configuration_summary(configuration, configuration_results, payload_result)
    print(f"  identity ({len(build.identity_edits)} edits)")
    print(f"Verified ISO candidate: {build.output_iso.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
