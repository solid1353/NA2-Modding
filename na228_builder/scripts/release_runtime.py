from __future__ import annotations

from pathlib import Path
from typing import Callable

from . import catalog as catalog_module
from .app import application_directory, load_release_manifest
from .build_configuration import build_configuration_candidate
from .configuration import BuildConfiguration, load_configuration
from scripts.lib.paths import load_local_paths


Emit = Callable[[str], None]


def packaged_workspace() -> Path:
    """Return the checkout or PyInstaller extraction root containing release data."""
    return Path(__file__).resolve().parents[2]


def application_cache_root() -> Path:
    """Map the configured cache root onto the release application directory."""
    paths = load_local_paths(packaged_workspace(), allow_missing=True)
    relative_cache = paths.path("cache").relative_to(paths.repository)
    return application_directory() / relative_cache


def load_release_configuration(
    configuration_path: Path,
    na2_iso: Path,
    nun5_iso: Path | None,
) -> tuple[Path, BuildConfiguration]:
    workspace = packaged_workspace()
    paths = load_local_paths(workspace, allow_missing=True)
    manifest = load_release_manifest()
    configuration_path = configuration_path.resolve()
    builder_root = paths.path("builder").resolve()
    try:
        builder_root.relative_to(workspace)
    except ValueError as exc:
        raise RuntimeError("Packaged builder root escapes release data") from exc
    if not configuration_path.is_file():
        raise FileNotFoundError(
            f"Release configuration is missing: {configuration_path.name}"
        )

    root_overrides = {"na2": na2_iso}
    if nun5_iso is not None:
        root_overrides["nun5"] = nun5_iso
    configuration = load_configuration(
        configuration_path,
        workspace,
        builder_root,
        project_paths=paths,
        root_overrides=root_overrides,
    )
    if configuration.product_title != manifest.product_name:
        raise RuntimeError(
            "Packaged product name does not match the product title"
        )
    return workspace, configuration


def required_release_image_ids(
    configuration: BuildConfiguration,
) -> tuple[str, ...]:
    image_ids = ["na2"]
    if any(module.module == "texture_patcher" for module in configuration.modules):
        image_ids.append("nun5")
    return tuple(image_ids)


def validate_release_configuration(configuration_path: Path) -> tuple[str, ...]:
    """Validate one external configuration without requiring copyrighted ISOs."""
    workspace = packaged_workspace()
    marker = load_local_paths(workspace, allow_missing=True).path(
        "builder", "release_manifest.json"
    )
    _, configuration = load_release_configuration(configuration_path, marker, marker)
    if not configuration.modules:
        raise RuntimeError("Release configuration has no module invocations")
    return required_release_image_ids(configuration)


def validate_packaged_release() -> int:
    """Verify the external configuration and packaged data without source ISOs."""
    manifest = load_release_manifest()
    configuration_path = application_directory() / manifest.configuration_name
    workspace = packaged_workspace()
    marker = load_local_paths(workspace, allow_missing=True).path(
        "builder", "release_manifest.json"
    )
    workspace, configuration = load_release_configuration(
        configuration_path,
        marker,
        marker,
    )
    if configuration.selection is None:
        raise RuntimeError("Release configuration has no catalog selection")
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
    if not configuration.modules:
        raise RuntimeError("Release configuration has no module invocations")
    return len(configuration.modules)


def build_release_iso(
    na2_iso: Path,
    nun5_iso: Path | None,
    configuration_path: Path,
    building_iso: Path,
    emit: Emit,
) -> None:
    """Apply the packaged release configuration without writing runtime logs."""
    if not building_iso.name.endswith(".building"):
        raise ValueError("Release staging path must end in .building")
    emit("Loading and verifying the selected configuration...")
    workspace, configuration = load_release_configuration(
        configuration_path,
        na2_iso,
        nun5_iso,
    )
    emit("Applying modules and assembling the output image...")
    build = build_configuration_candidate(
        source_iso=na2_iso,
        output_iso=building_iso,
        configuration=configuration,
        workspace=workspace,
        configuration_log_directory=None,
        texture_cache_root=application_cache_root() / "texture_patcher",
    )
    if build.output_iso != building_iso.resolve():
        raise RuntimeError("Build engine produced an unexpected staging path")
    emit(
        f"Verified {len(build.results)} module invocations in {building_iso.name}."
    )
