from __future__ import annotations

from pathlib import Path
from typing import Callable

from .app import load_release_manifest
from .build_profile import build_profile_candidate
from .profile import Profile, load_profile


Emit = Callable[[str], None]


def packaged_workspace() -> Path:
    """Return the checkout or PyInstaller extraction root containing release data."""
    return Path(__file__).resolve().parents[1]


def load_release_configuration(na2_iso: Path, nun5_iso: Path) -> tuple[Path, Profile]:
    workspace = packaged_workspace()
    manifest = load_release_manifest()
    configuration_path = (workspace / manifest.configuration).resolve()
    try:
        configuration_path.relative_to(workspace)
    except ValueError as exc:
        raise RuntimeError("Packaged configuration path escapes release data") from exc
    if not configuration_path.is_file():
        raise FileNotFoundError("Packaged release configuration is missing")

    profile = load_profile(
        configuration_path,
        workspace,
        root_overrides={"na2": na2_iso, "nun5": nun5_iso},
    )
    if profile.identity.output_game_title != manifest.product_name:
        raise RuntimeError(
            "Packaged product name does not match the product identity"
        )
    return workspace, profile


def validate_packaged_release() -> int:
    """Verify embedded configuration data without requiring copyrighted source ISOs."""
    workspace = packaged_workspace()
    manifest = load_release_manifest()
    marker = workspace / "na228_builder" / "release_manifest.json"
    _, profile = load_release_configuration(marker, marker)
    if not profile.modules:
        raise RuntimeError("Packaged release configuration has no module invocations")
    return len(profile.modules)


def build_release_iso(
    na2_iso: Path,
    nun5_iso: Path,
    building_iso: Path,
    emit: Emit,
) -> None:
    """Apply the packaged release configuration without writing runtime logs."""
    if not building_iso.name.endswith(".building"):
        raise ValueError("Release staging path must end in .building")
    output_iso = building_iso.with_name(
        building_iso.name[: -len(".building")]
    )
    emit("Loading and verifying the packaged configuration...")
    workspace, profile = load_release_configuration(na2_iso, nun5_iso)
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
