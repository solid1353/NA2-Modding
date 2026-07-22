from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .composer import (
    MODULE_ARTIFACT_CONTRACTS,
    resolve_module_order,
    resolve_symbolic_patches,
)
from .modules import translation_importer as translation_importer_module
from .modules.string_patcher import engine as string_patcher_module
from .payload_builder import builder as payload_builder_module
from .payload_builder.operations import ResidentPayloadBuild, ResolvedPatch
from .profile import Profile, ProfileModule


@dataclass(frozen=True)
class PreparedModulePipeline:
    ordered_modules: tuple[ProfileModule, ...]
    import_plans: dict[
        str, translation_importer_module.TranslationImportPlan
    ]
    string_plans: dict[str, string_patcher_module.StringPatchPlan]
    derived_string_plans: dict[str, string_patcher_module.StringPatchPlan]
    payload_build: ResidentPayloadBuild | None


@dataclass(frozen=True)
class _StringPreparation:
    provider: ProfileModule
    consumer: ProfileModule | None
    owner: str
    import_plan: translation_importer_module.TranslationImportPlan
    draft: string_patcher_module.StringPatchDraft


def _translation_source_arguments(root: Path, prefix: str) -> dict[str, Path]:
    if root.is_dir():
        return {f"{prefix}_folder": root}
    if root.is_file():
        return {f"{prefix}_iso": root}
    raise FileNotFoundError(root)


def _bind_string_consumer(
    provider: ProfileModule,
    ordered_modules: tuple[ProfileModule, ...],
) -> ProfileModule | None:
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


def prepare_module_pipeline(profile: Profile) -> PreparedModulePipeline:
    """Prepare artifacts and link all shared payload contributions once."""
    ordered_modules = resolve_module_order(profile.modules)
    if any(module.module == "translation_importer" for module in ordered_modules):
        if "na2" not in profile.roots or "nun5" not in profile.roots:
            raise ValueError("Translation importer requires na2 and nun5 profile roots")

    import_plans: dict[
        str, translation_importer_module.TranslationImportPlan
    ] = {}
    preparations: list[_StringPreparation] = []
    owners: set[str] = set()
    for provider in ordered_modules:
        if provider.module != "translation_importer":
            continue
        import_plan = translation_importer_module.build_translation_import_plan(
            **_translation_source_arguments(profile.roots["na2"], "na2"),
            **_translation_source_arguments(profile.roots["nun5"], "nun5"),
            data_root=provider.input_path,
            apply="BTL,ETC,SLPS",
        )
        import_plans[provider.module_id] = import_plan
        consumer = _bind_string_consumer(provider, ordered_modules)
        owner = (
            consumer.module_id
            if consumer is not None
            else f"{provider.feature_id}.string_patcher"
        )
        if owner in owners:
            raise ValueError(f"Duplicate prepared string-patcher owner: {owner}")
        owners.add(owner)
        preparations.append(
            _StringPreparation(
                provider=provider,
                consumer=consumer,
                owner=owner,
                import_plan=import_plan,
                draft=string_patcher_module.build_translation_draft(
                    translation_plan=import_plan,
                    owner=owner,
                ),
            )
        )

    fragments = tuple(
        fragment
        for preparation in preparations
        for fragment in preparation.draft.external_draft.fragments
    )
    symbolic_patches = tuple(
        patch
        for preparation in preparations
        for patch in preparation.draft.external_draft.symbolic_patches
    )
    payload_build = (
        payload_builder_module.build_resident_payload(fragments)
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
            translation_plan=preparation.import_plan,
            draft=preparation.draft,
            build=payload_build,
            resolved_patches=resolved_by_owner.get(preparation.owner, ()),
        )
        if preparation.consumer is not None:
            string_plans[preparation.consumer.module_id] = plan
        else:
            derived_string_plans[preparation.provider.module_id] = plan

    return PreparedModulePipeline(
        ordered_modules=ordered_modules,
        import_plans=import_plans,
        string_plans=string_plans,
        derived_string_plans=derived_string_plans,
        payload_build=payload_build,
    )
