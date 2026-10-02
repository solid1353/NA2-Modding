from __future__ import annotations

from pathlib import Path

from . import catalog as catalog_module
from .app import Emit, application_directory, load_release_manifest
from .build_configuration import build_configuration_candidate
from .configuration import BuildConfiguration, load_configuration
from scripts.lib.paths import load_local_paths


def packaged_workspace() -> Path:
    """Return the checkout or PyInstaller extraction root containing release data."""
    return Path(__file__).resolve().parents[3]


def load_release_configuration(
    configuration_path: Path,
    na2_iso: Path,
) -> tuple[Path, BuildConfiguration]:
    workspace = packaged_workspace()
    paths = load_local_paths(workspace, allow_missing=True)
    manifest = load_release_manifest()
    builder_root = paths.path("builder").resolve()
    configuration = load_configuration(
        configuration_path,
        workspace,
        builder_root,
        project_paths=paths,
        root_overrides={"na2": na2_iso},
        release_defaults_path=builder_root / "configurations" / "base.jsonc",
        release_definition_path=builder_root / manifest.configuration,
    )
    return workspace, configuration


def _load_without_source(configuration_path: Path) -> tuple[Path, BuildConfiguration]:
    """Load a release configuration with the packaged manifest standing in for the ISO."""
    marker = load_local_paths(packaged_workspace(), allow_missing=True).path(
        "builder", "release", "release_manifest.json"
    )
    workspace, configuration = load_release_configuration(configuration_path, marker)
    if not configuration.modules:
        raise RuntimeError("Release configuration has no module invocations")
    return workspace, configuration


def validate_release_configuration(configuration_path: Path) -> None:
    """Validate one external configuration without requiring copyrighted ISOs."""
    _load_without_source(configuration_path)


def validate_packaged_release() -> int:
    """Verify the external configuration and packaged data without source ISOs."""
    manifest = load_release_manifest()
    workspace, configuration = _load_without_source(
        application_directory() / manifest.configuration_name
    )
    for feature_id in configuration.selection.feature_ids:
        for source in catalog_module.referenced_files(
            configuration.selection,
            workspace,
            feature_id,
        ):
            if source.suffix in {".c", ".S"}:
                packaged_object = source.with_name(source.name + ".o")
                if not packaged_object.is_file():
                    raise FileNotFoundError(
                        f"Packaged runtime object is missing: {packaged_object}"
                    )
    return len(configuration.modules)


def build_release_iso(
    na2_iso: Path,
    configuration_path: Path,
    building_iso: Path,
    emit: Emit,
) -> None:
    """Apply the packaged release configuration without writing runtime logs."""
    emit("Loading and verifying the selected configuration...")
    workspace, configuration = load_release_configuration(
        configuration_path,
        na2_iso,
    )
    emit("Applying modules and assembling the output image...")
    build = build_configuration_candidate(
        source_iso=na2_iso,
        output_iso=building_iso,
        configuration=configuration,
        workspace=workspace,
        configuration_log_directory=None,
    )
    emit(
        f"Verified {len(build.results)} module invocations in {building_iso.name}."
    )
