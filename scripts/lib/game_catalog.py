from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from types import ModuleType


REPOSITORY = Path(__file__).resolve().parents[2]


def _workshop_root() -> Path:
    manifest = json.loads(
        (REPOSITORY / "paths.json").read_text(encoding="utf-8")
    )
    raw = manifest["imports"]["workshop"]
    path = Path(raw)
    if path.is_absolute() or raw.startswith("@"):
        raise ValueError("Workshop bootstrap path must be repository-relative")
    return Path(os.path.abspath(REPOSITORY / path)).parent


def _shared_module() -> ModuleType:
    path = _workshop_root() / "scripts" / "lib" / "game_catalog.py"
    spec = importlib.util.spec_from_file_location("un_workshop_game_catalog", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load Workshop game catalog module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_SHARED = _shared_module()
derive_game_paths = _SHARED.derive_game_paths
find_definition = _SHARED.find_definition


def load_game_catalog() -> dict[str, object]:
    return _SHARED.load_catalog(_workshop_root(), REPOSITORY)


def resolve_game(selector: str) -> dict[str, str]:
    from .project_paths import load_base_project_paths

    paths = load_base_project_paths(REPOSITORY, allow_missing=True)
    return {
        name: os.path.abspath(path)
        for name, path in derive_game_paths(
            selector,
            load_game_catalog(),
            paths.roots,
        ).items()
    }
