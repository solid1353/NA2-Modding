from __future__ import annotations

from dataclasses import dataclass, replace

from . import catalog as catalog_module
from .composer import resolve_symbolic_patches
from ..modules.translation_importer import engine as translation_importer_module
from ..modules.runtime_injector import engine as runtime_injector_module
from ..modules.binary_patcher import engine as binary_patcher_module
from ..modules.string_patcher import engine as string_patcher_module
from ..modules.payload_builder import builder as payload_builder_module
from ..modules.payload_builder.operations import (
    PayloadFragment,
    ResidentPayloadBuild,
    ResolvedPatch,
)
from .configuration import BuildConfiguration, ModuleInvocation
from ...patches.localization.mod_strings import ModStrings
from ...patches.localization.retail_strings import owned_retail_strings, retail_string_package
from ...patches.settings.character_overrides.character_overrides import (
    character_override_fragment,
)
from ...patches.settings.ingame.battle_mode.battle_settings import battle_settings_fragments
from ...patches.settings.ingame.battle_mechanics.substitution_resource.substitution_gauge import substitution_gauge_fragment
from ...patches.settings.ingame.battle_mechanics.items.items_settings import items_settings_fragment
from ...patches.settings.ingame.practice_mode.practice_settings import practice_settings_fragments
from ...patches.settings.ingame.battle_mechanics.battle_settings_runtime import battle_settings_runtime_fragments
from ...patches.settings.ingame.shared.native_settings_defaults import native_settings_defaults_fragment
from ...patches.settings.mod_settings.mod_settings import (
    mod_settings_graphics_fragments,
    mod_settings_menu_fragments,
    mod_settings_state_fragment,
)
from ...patches.general.unlock_all.unlock_all import unlock_all_configuration_fragment
from ...patches.general.battle_results_rematch import rematch_label_fragment
from ...patches.general.controls.control_defaults import control_default_fragments
from ...patches.memory_card.save_load import save_load_continuation_fragments
from ...patches.memory_card.save_appendix import (
    save_appendix_load_status_fragment,
    save_appendix_schema_fragment,
)


@dataclass(frozen=True)
class PreparedModulePipeline:
    ordered_modules: tuple[ModuleInvocation, ...]
    import_plans: dict[
        str, translation_importer_module.TranslationImportPlan
    ]
    derived_string_plans: dict[str, string_patcher_module.StringPatchPlan]
    runtime_injection_packages: dict[str, binary_patcher_module.Package]
    payload_build: ResidentPayloadBuild | None


@dataclass(frozen=True)
class _StringPreparation:
    provider: ModuleInvocation
    owner: str
    draft: string_patcher_module.StringPatchDraft


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


def _runtime_injection_declaration(
    configuration: BuildConfiguration,
    module: ModuleInvocation,
) -> runtime_injector_module.RuntimeInjectionPackage:
    """Load one feature's catalog injections plus its generated fragments."""
    selection = configuration.selection
    owner = module.module_id
    declaration = catalog_module.load_runtime_package(
        selection,
        module.feature_id,
        configuration.targets_path,
        selection.catalog_path.parent.parent,
        owner,
    )
    # Each group goes in front of the fragments generated before it.
    generated: list[PayloadFragment] = []

    def prepend(*fragments: PayloadFragment) -> None:
        generated[:0] = fragments

    if module.feature_id == "defaults":
        if configuration.character_overrides is not None:
            prepend(
                character_override_fragment(
                    configuration.character_overrides,
                    owner=owner,
                )
            )
        prepend(
            mod_settings_state_fragment(selection, owner=owner),
            *mod_settings_graphics_fragments(owner=owner),
            *mod_settings_menu_fragments(selection, owner=owner),
        )
        prepend(native_settings_defaults_fragment(selection, owner=owner))
        prepend(
            *battle_settings_fragments(selection, owner=owner),
            *practice_settings_fragments(selection, owner=owner),
            *battle_settings_runtime_fragments(selection, owner=owner),
            items_settings_fragment(selection, owner=owner),
            substitution_gauge_fragment(selection, owner=owner),
        )
        prepend(*control_default_fragments(selection, owner=owner))
    if module.feature_id == "general":
        if any(
            node.path == ("features", "general", "battle_results_rematch")
            and node.enabled
            for node in selection.nodes
        ):
            prepend(rematch_label_fragment(owner=owner))
        unlock_all_fragment = unlock_all_configuration_fragment(
            selection,
            owner=owner,
        )
        if unlock_all_fragment is not None:
            prepend(unlock_all_fragment)
    if module.feature_id == "memory_card":
        visible_updates = (
            "save_appendix_update",
            "dialogs_rework_update",
            "display_only_first_save_update",
        )
        selected_update = next((
            symbol for symbol in visible_updates
            if any(edit.symbolic_patch.symbol == symbol for edit in declaration.edits)
        ), None)
        declaration = replace(
            declaration,
            edits=tuple(
                edit for edit in declaration.edits
                if edit.symbolic_patch.symbol not in visible_updates
                or edit.symbolic_patch.symbol == selected_update
            ),
        )
        prepend(*save_load_continuation_fragments(selection, owner=owner))
        if selection.node_enabled("features", "memory_card", "extended_save_data"):
            prepend(
                save_appendix_load_status_fragment(owner=owner),
                save_appendix_schema_fragment(selection, owner=owner),
            )
        elif any(
            node.path == ("features", "memory_card", "auto_loading")
            and node.enabled
            for node in selection.nodes
        ):
            prepend(save_appendix_load_status_fragment(owner=owner))
    declaration = replace(
        declaration,
        fragments=(*generated, *declaration.fragments),
    )
    if module.feature_id == "defaults":
        declaration = retail_string_package(
            declaration, configuration.roots["na2"], configuration.targets_path
        )
    return declaration


def prepare_module_pipeline(
    configuration: BuildConfiguration,
) -> PreparedModulePipeline:
    """Prepare artifacts and link all shared payload contributions once."""
    ordered_modules = configuration.modules
    import_plans: dict[
        str, translation_importer_module.TranslationImportPlan
    ] = {}
    preparations: list[_StringPreparation] = []
    runtime_injection_declarations = {
        module.module_id: _runtime_injection_declaration(configuration, module)
        for module in ordered_modules
        if module.module == "runtime_injector"
    }
    owners = set(runtime_injection_declarations)
    title_policy = _selected_game_title_policy(configuration)
    for provider in ordered_modules:
        if provider.module != "translation_importer":
            continue
        import_plan = translation_importer_module.build_translation_import_plan(
            source_root=configuration.roots["na2"],
            data_root=provider.input_path,
        )
        owner = f"{provider.feature_id}.string_patcher"
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
    fragments += ModStrings(
        configuration.selection,
        retail_ids={entry.string_id for entry in owned_retail_strings()},
        retail_arguments={"title": configuration.product_title},
    ).fragments(fragments, symbolic_patches)
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
        runtime_injection_packages=runtime_injection_packages,
        payload_build=payload_build,
    )
