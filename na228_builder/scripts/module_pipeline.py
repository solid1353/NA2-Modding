from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from . import catalog as catalog_module
from .composer import (
    MODULE_ARTIFACT_CONTRACTS,
    resolve_module_order,
    resolve_symbolic_patches,
)
from ..modules import translation_importer as translation_importer_module
from ..modules import runtime_injector as runtime_injector_module
from ..modules.binary_patcher import engine as binary_patcher_module
from ..modules.string_patcher import engine as string_patcher_module
from ..payload_builder import builder as payload_builder_module
from ..payload_builder.operations import (
    PayloadFragment,
    ResidentPayloadBuild,
    ResolvedPatch,
)
from .configuration import BuildConfiguration, ModuleInvocation
from .character_overrides import character_override_fragment
from .practice_bootstrap import practice_bootstrap_fragment
from .xdash_chakra_cost import xdash_chakra_cost_fragment


@dataclass(frozen=True)
class PreparedModulePipeline:
    ordered_modules: tuple[ModuleInvocation, ...]
    import_plans: dict[
        str, translation_importer_module.TranslationImportPlan
    ]
    string_plans: dict[str, string_patcher_module.StringPatchPlan]
    derived_string_plans: dict[str, string_patcher_module.StringPatchPlan]
    runtime_injection_declarations: dict[
        str, runtime_injector_module.RuntimeInjectionPackage
    ]
    runtime_injection_packages: dict[str, binary_patcher_module.Package]
    payload_build: ResidentPayloadBuild | None


@dataclass(frozen=True)
class _StringPreparation:
    provider: ModuleInvocation
    consumer: ModuleInvocation | None
    owner: str
    draft: string_patcher_module.StringPatchDraft


def _translation_source_arguments(root: Path, prefix: str) -> dict[str, Path]:
    if root.is_dir():
        return {f"{prefix}_folder": root}
    if root.is_file():
        return {f"{prefix}_iso": root}
    raise FileNotFoundError(root)


def _bind_string_consumer(
    provider: ModuleInvocation,
    ordered_modules: tuple[ModuleInvocation, ...],
) -> ModuleInvocation | None:
    consumers = [
        module
        for module in ordered_modules
        if module.feature_id == provider.feature_id
        and module.module == "string_patcher"
    ]
    if len(consumers) > 1:
        raise ValueError(
            f"{provider.module_id} has multiple same-feature string_patcher consumers"
        )
    if consumers:
        return consumers[0]
    if (
        "string_patcher"
        not in MODULE_ARTIFACT_CONTRACTS[provider.module].derived_consumers
    ):
        raise ValueError(f"{provider.module_id} has no declared string consumer")
    return None


def _selected_game_title_policy(
    configuration: BuildConfiguration,
) -> string_patcher_module.GameTitlePolicy | None:
    selected = catalog_module.selected_string_patches(
        configuration.selection,
        "replace_imported_game_title",
    )
    if len(selected) > 1:
        raise ValueError(
            "Configuration selects multiple imported game-title replacements"
        )
    if not selected:
        return None
    _node, _patch_id, definition = selected[0]
    return string_patcher_module.GameTitlePolicy(
        imported_title=str(definition["expected_value"]),
        output_title=configuration.product_title,
        expected_mapping_count=int(definition["expected_mapping_count"]),
        expected_occurrence_count=int(definition["expected_occurrence_count"]),
    )


def prepare_module_pipeline(
    configuration: BuildConfiguration,
    *,
    payload_shift: int = 0,
) -> PreparedModulePipeline:
    """Prepare artifacts and link all shared payload contributions once."""
    if payload_shift < 0 or payload_shift > 0x10000 or payload_shift & 0xF:
        raise ValueError(
            "Payload shift must be a 16-byte multiple from 0 through 65536"
        )
    ordered_modules = resolve_module_order(configuration.modules)
    if any(module.module == "translation_importer" for module in ordered_modules):
        if "na2" not in configuration.roots:
            raise ValueError("Translation importer requires the na2 configuration root")

    import_plans: dict[
        str, translation_importer_module.TranslationImportPlan
    ] = {}
    preparations: list[_StringPreparation] = []
    owners: set[str] = set()
    runtime_injection_declarations: dict[
        str, runtime_injector_module.RuntimeInjectionPackage
    ] = {}
    title_policy = _selected_game_title_policy(configuration)
    for module in ordered_modules:
        if module.module != "runtime_injector":
            continue
        if configuration.selection is not None:
            declaration = catalog_module.load_runtime_package(
                configuration.selection,
                module.feature_id,
                configuration.targets_path,
                configuration.selection.catalog_path.parent.parent,
                module.module_id,
            )
            if (
                module.feature_id == "battle_logic"
                and configuration.character_overrides is not None
            ):
                declaration = replace(
                    declaration,
                    fragments=(
                        character_override_fragment(
                            configuration.character_overrides,
                            owner=module.module_id,
                        ),
                        *declaration.fragments,
                    ),
                )
            if module.feature_id == "battle_logic":
                xdash_cost_fragment = xdash_chakra_cost_fragment(
                    configuration.selection,
                    owner=module.module_id,
                )
                if xdash_cost_fragment is not None:
                    declaration = replace(
                        declaration,
                        fragments=(
                            xdash_cost_fragment,
                            *declaration.fragments,
                        ),
                    )
            if module.feature_id == "qol":
                bootstrap_fragment = practice_bootstrap_fragment(
                    configuration.selection,
                    owner=module.module_id,
                    awakening_ids_by_character=(
                        configuration.character_overrides.awakening_ids_by_character()
                        if configuration.character_overrides is not None
                        else {}
                    ),
                )
                if bootstrap_fragment is not None:
                    declaration = replace(
                        declaration,
                        fragments=(
                            bootstrap_fragment,
                            *declaration.fragments,
                        ),
                    )
        else:
            declaration = runtime_injector_module.load_package(
                module.input_path,
                owner=module.module_id,
                targets_path=configuration.targets_path,
            )
        if module.module_id in owners:
            raise ValueError(
                f"Duplicate resident-payload owner: {module.module_id}"
            )
        owners.add(module.module_id)
        runtime_injection_declarations[module.module_id] = declaration

    for provider in ordered_modules:
        if provider.module != "translation_importer":
            continue
        source_arguments = _translation_source_arguments(
            configuration.roots["na2"], "na2"
        )
        import_plan = translation_importer_module.build_translation_import_plan(
            **source_arguments,
            data_root=provider.input_path,
            apply="BTL,ETC,SLPS",
        )
        consumer = _bind_string_consumer(provider, ordered_modules)
        owner = (
            consumer.module_id
            if consumer is not None
            else f"{provider.feature_id}.string_patcher"
        )
        if owner in owners:
            raise ValueError(f"Duplicate prepared string-patcher owner: {owner}")
        owners.add(owner)
        draft = string_patcher_module.build_translation_draft(
            translation_plan=import_plan,
            owner=owner,
            title_policy=title_policy,
        )
        import_plans[provider.module_id] = draft.translation_plan
        preparations.append(
            _StringPreparation(
                provider=provider,
                consumer=consumer,
                owner=owner,
                draft=draft,
            )
        )

    fragments = tuple(
        fragment
        for preparation in preparations
        for fragment in preparation.draft.external_draft.fragments
    ) + tuple(
        fragment
        for declaration in runtime_injection_declarations.values()
        for fragment in declaration.payload_fragments
    )
    symbolic_patches = tuple(
        patch
        for preparation in preparations
        for patch in preparation.draft.external_draft.symbolic_patches
    ) + tuple(
        patch
        for declaration in runtime_injection_declarations.values()
        for patch in declaration.symbolic_patches
    )
    payload_build = (
        payload_builder_module.build_resident_payload(
            fragments,
            layout_shift=payload_shift,
        )
        if fragments
        else None
    )
    resolved_by_owner: dict[str, tuple[ResolvedPatch, ...]] = {}
    if payload_build is not None:
        resolved = resolve_symbolic_patches(payload_build, symbolic_patches)
        for owner in owners:
            resolved_by_owner[owner] = tuple(
                patch for patch in resolved if patch.owner == owner
            )
    elif symbolic_patches:
        raise ValueError("Symbolic payload patches exist without payload fragments")

    string_plans: dict[str, string_patcher_module.StringPatchPlan] = {}
    derived_string_plans: dict[str, string_patcher_module.StringPatchPlan] = {}
    for preparation in preparations:
        plan = string_patcher_module.finalize_translation_plan(
            (
                preparation.consumer.input_path
                if preparation.consumer is not None
                else None
            ),
            draft=preparation.draft,
            build=payload_build,
            resolved_patches=resolved_by_owner.get(preparation.owner, ()),
        )
        if preparation.consumer is not None:
            string_plans[preparation.consumer.module_id] = plan
        else:
            derived_string_plans[preparation.provider.module_id] = plan

    runtime_injection_packages = {
        module_id: runtime_injector_module.build_binary_package(
            declaration, resolved_by_owner.get(module_id, ())
        )
        for module_id, declaration in runtime_injection_declarations.items()
    }
    return PreparedModulePipeline(
        ordered_modules=ordered_modules,
        import_plans=import_plans,
        string_plans=string_plans,
        derived_string_plans=derived_string_plans,
        runtime_injection_declarations=runtime_injection_declarations,
        runtime_injection_packages=runtime_injection_packages,
        payload_build=payload_build,
    )
