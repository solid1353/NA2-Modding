from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from . import catalog as catalog_module
from .composer import resolve_symbolic_patches
from ..modules import translation_importer as translation_importer_module
from ..modules import runtime_injector as runtime_injector_module
from ..modules.binary_patcher import engine as binary_patcher_module
from ..modules.string_patcher import engine as string_patcher_module
from ..payload_builder import builder as payload_builder_module
from ..payload_builder.operations import (
    ResidentPayloadBuild,
    ResolvedPatch,
)
from .configuration import BuildConfiguration, ModuleInvocation
from .character_overrides import (
    character_override_fragment,
    character_override_fragment_feature,
    character_overrides_enabled_fragment,
)
from .battle_settings import battle_settings_fragment
from .substitution_gauge import substitution_gauge_fragment
from .practice_settings import practice_settings_fragment
from .battle_settings_runtime import battle_settings_runtime_fragment


@dataclass(frozen=True)
class PreparedModulePipeline:
    ordered_modules: tuple[ModuleInvocation, ...]
    import_plans: dict[
        str, translation_importer_module.TranslationImportPlan
    ]
    derived_string_plans: dict[str, string_patcher_module.StringPatchPlan]
    runtime_injection_declarations: dict[
        str, runtime_injector_module.RuntimeInjectionPackage
    ]
    runtime_injection_packages: dict[str, binary_patcher_module.Package]
    payload_build: ResidentPayloadBuild | None


@dataclass(frozen=True)
class _StringPreparation:
    provider: ModuleInvocation
    owner: str
    draft: string_patcher_module.StringPatchDraft


def _translation_source_arguments(root: Path, prefix: str) -> dict[str, Path]:
    if root.is_dir():
        return {f"{prefix}_folder": root}
    if root.is_file():
        return {f"{prefix}_iso": root}
    raise FileNotFoundError(root)


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
) -> PreparedModulePipeline:
    """Prepare artifacts and link all shared payload contributions once."""
    ordered_modules = configuration.modules
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
    character_overrides_enabled = configuration.selection.node_enabled(
        "features", "general", "character_overrides"
    )
    character_select_overlay_enabled = configuration.selection.node_enabled(
        "features", "character_select", "balance_overlay"
    )
    character_override_feature = character_override_fragment_feature(
        configuration.selection
    )
    for module in ordered_modules:
        if module.module != "runtime_injector":
            continue
        declaration = catalog_module.load_runtime_package(
            configuration.selection,
            module.feature_id,
            configuration.targets_path,
            configuration.selection.catalog_path.parent.parent,
            module.module_id,
        )
        if (
            module.feature_id == character_override_feature
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
        if (
            module.feature_id == "character_select"
            and character_select_overlay_enabled
        ):
            declaration = replace(
                declaration,
                fragments=(
                    character_overrides_enabled_fragment(
                        character_overrides_enabled,
                        owner=module.module_id,
                    ),
                    *declaration.fragments,
                ),
            )
        if module.feature_id == "settings":
            battle_schema_fragment = battle_settings_fragment(
                configuration.selection,
                owner=module.module_id,
            )
            if battle_schema_fragment is not None:
                declaration = replace(
                    declaration,
                    fragments=(
                        battle_schema_fragment,
                        *declaration.fragments,
                    ),
                )
            practice_schema_fragment = practice_settings_fragment(
                configuration.selection,
                owner=module.module_id,
            )
            if practice_schema_fragment is not None:
                declaration = replace(
                    declaration,
                    fragments=(
                        practice_schema_fragment,
                        *declaration.fragments,
                    ),
                )
            runtime_config_fragment = battle_settings_runtime_fragment(
                configuration.selection,
                owner=module.module_id,
            )
            if runtime_config_fragment is not None:
                declaration = replace(
                    declaration,
                    fragments=(
                        runtime_config_fragment,
                        *declaration.fragments,
                    ),
                )
            gauge_config_fragment = substitution_gauge_fragment(
                configuration.selection,
                owner=module.module_id,
            )
            if gauge_config_fragment is not None:
                declaration = replace(
                    declaration,
                    fragments=(
                        gauge_config_fragment,
                        *declaration.fragments,
                    ),
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
        owner = f"{provider.feature_id}.string_patcher"
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

    derived_string_plans: dict[str, string_patcher_module.StringPatchPlan] = {}
    for preparation in preparations:
        plan = string_patcher_module.finalize_translation_plan(
            draft=preparation.draft,
            build=payload_build,
            resolved_patches=resolved_by_owner.get(preparation.owner, ()),
        )
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
        derived_string_plans=derived_string_plans,
        runtime_injection_declarations=runtime_injection_declarations,
        runtime_injection_packages=runtime_injection_packages,
        payload_build=payload_build,
    )
