from __future__ import annotations

from pathlib import Path
from typing import Callable

from . import catalog as catalog_module
from .app import application_directory, load_release_manifest
from .build_profile import build_profile_candidate
from .profile import Profile, load_configuration
from scripts.lib.paths import load_local_paths


Emit = Callable[[str], None]


def packaged_workspace() -> Path:
    """Return the checkout or PyInstaller extraction root containing release data."""
    return Path(__file__).resolve().parents[1]


def load_release_configuration(
    configuration_path: Path,
    na2_iso: Path,
    nun5_iso: Path,
) -> tuple[Path, Profile]:
    workspace = packaged_workspace()
    manifest = load_release_manifest()
    configuration_path = configuration_path.resolve()
    builder_root = (workspace / "na228_builder").resolve()
    try:
        builder_root.relative_to(workspace)
    except ValueError as exc:
        raise RuntimeError("Packaged builder root escapes release data") from exc
    if not configuration_path.is_file():
        raise FileNotFoundError(
            f"Release configuration is missing: {configuration_path.name}"
        )

    profile = load_configuration(
        configuration_path,
        workspace,
        builder_root,
        project_paths=load_local_paths(workspace, allow_missing=True),
        root_overrides={"na2": na2_iso, "nun5": nun5_iso},
    )
    if profile.identity.output_game_title != manifest.product_name:
        raise RuntimeError(
            "Packaged product name does not match the product identity"
        )
    return workspace, profile


def validate_release_configuration(configuration_path: Path) -> int:
    """Validate one external configuration without requiring copyrighted ISOs."""
    workspace = packaged_workspace()
    marker = workspace / "na228_builder" / "release_manifest.json"
    _, profile = load_release_configuration(configuration_path, marker, marker)
    if not profile.modules:
        raise RuntimeError("Release configuration has no module invocations")
    return len(profile.modules)


def validate_packaged_release() -> int:
    """Verify the external configuration and packaged data without source ISOs."""
    manifest = load_release_manifest()
    configuration_path = application_directory() / manifest.configuration_name
    marker = packaged_workspace() / "na228_builder" / "release_manifest.json"
    workspace, profile = load_release_configuration(
        configuration_path,
        marker,
        marker,
    )
    if profile.selection is None:
        raise RuntimeError("Release configuration has no catalog selection")
    for feature_id in profile.selection.feature_ids:
        for source in catalog_module.referenced_files(
            profile.selection,
            workspace,
            feature_id,
        ):
            if source.suffix.lower() == ".c":
                packaged_object = source.with_name(source.name + ".o")
                if not packaged_object.is_file():
                    raise FileNotFoundError(
                        f"Packaged runtime object is missing: {packaged_object}"
                    )
    if not profile.modules:
        raise RuntimeError("Release configuration has no module invocations")
    return len(profile.modules)


def build_release_iso(
    na2_iso: Path,
    nun5_iso: Path,
    configuration_path: Path,
    building_iso: Path,
    emit: Emit,
) -> None:
    """Apply the packaged release configuration without writing runtime logs."""
    if not building_iso.name.endswith(".building"):
        raise ValueError("Release staging path must end in .building")
    output_iso = building_iso.with_name(
        building_iso.name[: -len(".building")]
    )
    emit("Loading and verifying the selected configuration...")
    workspace, profile = load_release_configuration(
        configuration_path,
        na2_iso,
        nun5_iso,
    )
    emit("Applying modules and assembling the output image...")
    build = build_profile_candidate(
        source_iso=na2_iso,
        output_iso=output_iso,
        profile=profile,
        workspace=workspace,
        profile_log_directory=None,
    )
    if build.staged_iso != building_iso.resolve():
        raise RuntimeError("Build engine produced an unexpected staging path")
    emit(
        f"Verified {len(build.results)} module invocations in {building_iso.name}."
    )
