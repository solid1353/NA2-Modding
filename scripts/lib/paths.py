from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType, ModuleType
from typing import Mapping

MANIFEST_NAME = "paths.json"
LAUNCH_SETTING_NAMES = ("startup_fast_forward_frames", "speed_after_startup")


def _load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load {name}: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=None)
def _workshop_module(workshop_root: Path, name: str) -> ModuleType:
    return _load_module(
        f"un_workshop_{name}", workshop_root / "scripts" / "lib" / f"{name}.py"
    )


@dataclass(frozen=True)
class Paths:
    manifest: Path
    roots: Mapping[str, Path]
    files: Mapping[str, Path]
    settings: Mapping[str, object] | None = None
    games: Mapping[str, Mapping[str, object]] = field(
        default_factory=lambda: MappingProxyType({})
    )

    @property
    def repository(self) -> Path:
        return self.roots["repository"]

    def path(self, root: str, *children: str | Path) -> Path:
        try:
            result = self.roots[root]
        except KeyError as exc:
            raise KeyError(f"Unknown project root: {root}") from exc
        for child in children:
            result /= child
        return result

    def file(self, name: str) -> Path:
        try:
            return self.files[name]
        except KeyError as exc:
            raise KeyError(f"Unknown project file: {name}") from exc


def task_work_root(paths: Paths) -> Path:
    configured = os.environ.get("NA228_TASK_WORK_ROOT")
    if not configured:
        raise ValueError("NA228_TASK_WORK_ROOT must name the current chat work directory")
    root = Path(configured)
    if not root.is_absolute():
        root = paths.repository / root
    root = root.resolve()
    if root.parent != paths.path("work").resolve():
        raise ValueError("NA228_TASK_WORK_ROOT must name an immediate child of work/")
    return root


def _find_manifest(start: Path) -> Path:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for candidate_root in (current, *current.parents):
        candidate = candidate_root / MANIFEST_NAME
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"Could not find {MANIFEST_NAME} above {start}")


def _is_selector(value: object) -> bool:
    return (
        isinstance(value, str)
        and bool(value)
        and value[0].isalnum()
        and value.replace("_", "").isalnum()
    )


def _validate_launch_settings(settings: Mapping[str, object]) -> None:
    launch_settings = settings.get("launch_settings")
    if not isinstance(launch_settings, dict):
        raise ValueError("Project launch_settings must be an object")
    default = launch_settings.get("default")
    if not isinstance(default, dict):
        raise ValueError("Project launch_settings.default must be an object")
    for name, definition in launch_settings.items():
        label = f"Project launch_settings.{name}"
        if not isinstance(definition, dict):
            raise ValueError(f"{label} must be an object")
        if set(definition) - set(LAUNCH_SETTING_NAMES):
            raise ValueError(
                f"{label} may define only startup_fast_forward_frames and "
                "speed_after_startup"
            )
        frames = definition.get("startup_fast_forward_frames", 0)
        if isinstance(frames, bool) or not isinstance(frames, int) or frames < 0:
            raise ValueError(
                f"{label}.startup_fast_forward_frames must be a non-negative integer"
            )
        if definition.get("speed_after_startup", "normal") not in {"normal", "turbo"}:
            raise ValueError(f"{label}.speed_after_startup must be normal or turbo")
    for name in LAUNCH_SETTING_NAMES:
        if name not in default:
            raise ValueError(f"Project launch_settings.default must define {name}")


def _load_paths(
    start: Path | None = None,
    *,
    allow_missing: bool = False,
    include_imports: bool = True,
) -> Paths:
    manifest_path = _find_manifest(start or Path.cwd())
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    configured = data.get("roots")
    if not isinstance(configured, dict) or not configured:
        raise ValueError("Project path manifest has no roots")
    configured_deferred = data.get("existence_deferred_roots", [])
    if (
        not isinstance(configured_deferred, list)
        or any(
            not isinstance(name, str)
            or not name
            or name not in configured
            for name in configured_deferred
        )
    ):
        raise ValueError("Invalid existence-deferred project root")

    repository = manifest_path.parent.resolve()
    roots: dict[str, Path] = {"repository": repository}
    files: dict[str, Path] = {}
    local_files = data.get("files")
    if not isinstance(local_files, dict) or not local_files:
        raise ValueError("Project path manifest has no files")

    imports = data.get("imports", {})
    if not isinstance(imports, dict):
        raise ValueError("Project path manifest imports must be an object")
    imported_roots: dict[str, Mapping[str, Path]] = {}
    for import_name, raw_manifest in imports.items() if include_imports else ():
        if (
            not isinstance(import_name, str)
            or not import_name
            or not isinstance(raw_manifest, str)
            or not raw_manifest
        ):
            raise ValueError("Invalid project path import")
        import_path = Path(raw_manifest)
        if import_path.is_absolute():
            raise ValueError(
                f"Project path import {import_name!r} must be relative"
            )
        imported_manifest = Path(os.path.abspath(repository / import_path))
        if not imported_manifest.is_file():
            raise FileNotFoundError(
                f"Project path import {import_name!r}: {imported_manifest}"
            )
        imported = _load_module(
            f"paths_import_{import_name}",
            imported_manifest.parent / "scripts" / "lib" / "paths.py",
        ).load_workshop_paths(imported_manifest.parent)
        imported_roots[import_name] = imported.roots
        if import_name in roots:
            raise ValueError(f"Duplicate imported root: {import_name!r}")
        roots[import_name] = imported.roots["repository"]
        for name, value in imported.roots.items():
            if name == "repository" or name in configured:
                continue
            if name in roots:
                raise ValueError(f"Duplicate imported root: {name!r}")
            roots[name] = value
        for name, value in imported.files.items():
            if name in local_files:
                continue
            if name in files:
                raise ValueError(f"Duplicate imported file: {name!r}")
            files[name] = value

    resolving: set[str] = set()
    deferred_roots = set(configured_deferred)

    def resolve_root(name: str) -> Path:
        if name in roots:
            return roots[name]
        if name in resolving:
            raise ValueError(
                f"Project root aliases contain a dependency cycle at {name!r}"
            )
        raw_value = configured[name]
        if not isinstance(raw_value, str) or not raw_value:
            raise ValueError(
                f"Project root {name!r} must be a non-empty repository-relative "
                "path or @root path"
            )

        resolving.add(name)
        if raw_value.startswith("@"):
            root_and_child = raw_value[1:].replace("\\", "/").split("/", 1)
            parent_name = root_and_child[0]
            child = root_and_child[1] if len(root_and_child) == 2 else ""
            child_path = Path(child)
            if (
                not parent_name
                or (parent_name not in configured and parent_name not in roots)
                or child_path.is_absolute()
                or ".." in child_path.parts
            ):
                raise ValueError(
                    f"Project root {name!r} has an invalid root alias: {raw_value!r}"
                )
            base_path = resolve_root(parent_name)
            if parent_name in deferred_roots:
                deferred_roots.add(name)
            configured_path = Path(os.path.abspath(base_path / child_path))
        else:
            value = Path(raw_value)
            if value.is_absolute():
                raise ValueError(
                    f"Project root {name!r} must be a non-empty repository-relative "
                    "path or @root path"
                )
            configured_path = Path(os.path.abspath(repository / value))
        if (
            not allow_missing
            and name not in deferred_roots
            and not configured_path.exists()
            and not configured_path.is_symlink()
        ):
            raise FileNotFoundError(
                f"Configured project root {name!r}: {configured_path}"
            )
        roots[name] = configured_path
        resolving.remove(name)
        return configured_path

    for name in configured:
        resolve_root(name)

    for name, raw_value in local_files.items():
        if not isinstance(raw_value, str) or not raw_value:
            raise ValueError(
                f"Project file {name!r} must be a non-empty "
                "repository-relative path or @root path"
            )

        if raw_value.startswith("@"):
            root_and_child = raw_value[1:].replace("\\", "/").split("/", 1)
            if len(root_and_child) != 2 or not all(root_and_child):
                raise ValueError(
                    f"Project file {name!r} has an invalid root alias: {raw_value!r}"
                )
            root, child = root_and_child
            try:
                base_path = roots[root]
            except KeyError as exc:
                raise ValueError(
                    f"Project file {name!r} references unknown project root "
                    f"{root!r}"
                ) from exc
            value = Path(child)
            if value.is_absolute() or ".." in value.parts:
                raise ValueError(
                    f"Project file {name!r} must remain within configured root "
                    f"{root!r}"
                )
        else:
            base_path = repository
            value = Path(raw_value)
            if value.is_absolute():
                raise ValueError(
                    f"Project file {name!r} must be a non-empty "
                    "repository-relative path or @root path"
                )

        configured_path = Path(os.path.abspath(base_path / value))
        if base_path not in configured_path.parents:
            scope = (
                "its configured root" if raw_value.startswith("@") else "the repository"
            )
            raise ValueError(f"Project file {name!r} must remain within {scope}")
        files[name] = configured_path

    settings: dict[str, object] | None = None
    games: dict[str, Mapping[str, object]] = {}
    settings_path = files.get("project_settings") if include_imports else None
    if settings_path is not None:
        if not settings_path.is_file():
            raise FileNotFoundError(f"Project settings not found: {settings_path}")
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        if not isinstance(settings, dict):
            raise ValueError("Project settings must be an object")
        _validate_launch_settings(settings)
        source_catalog_path = files.get("source_catalog")
        workshop_roots = imported_roots.get("workshop")
        if source_catalog_path is None or workshop_roots is None:
            raise ValueError("Project game catalogs require the Workshop import")
        if not source_catalog_path.is_file():
            raise FileNotFoundError(
                f"Source game catalog not found: {source_catalog_path}"
            )
        catalog = {
            "sources": json.loads(
                source_catalog_path.read_text(encoding="utf-8")
            ).get("sources"),
        }
        game_catalog = _workshop_module(roots["workshop"], "game_catalog")
        content_roots = list(
            dict.fromkeys((roots["pcsx2_files"], workshop_roots["pcsx2_files"]))
        )

        def resolve_catalog_value(label: str, raw_value: object) -> object:
            if not isinstance(raw_value, str) or not raw_value:
                raise ValueError(f"{label} has an invalid value: {raw_value!r}")
            if not raw_value.startswith("@"):
                return raw_value
            root_and_child = raw_value[1:].replace("\\", "/").split("/", 1)
            if len(root_and_child) != 2 or not all(root_and_child):
                raise ValueError(f"{label} has an invalid path: {raw_value!r}")
            root_name, child = root_and_child
            try:
                base_path = roots[root_name]
            except KeyError as exc:
                raise ValueError(
                    f"{label} references unknown project root {root_name!r}"
                ) from exc
            child_path = Path(child)
            if child_path.is_absolute() or ".." in child_path.parts:
                raise ValueError(f"{label} must remain within {root_name!r}")
            return Path(os.path.abspath(base_path / child_path))

        definitions = catalog["sources"]
        if not isinstance(definitions, dict) or not definitions:
            raise ValueError("Game catalog has no non-empty 'sources' section")
        selectors: set[str] = set()
        for game_name, definition in definitions.items():
            if not _is_selector(game_name):
                raise ValueError(f"Invalid canonical game selector: {game_name!r}")
            if game_name.casefold() in selectors:
                raise ValueError(f"Duplicate game selector or alias: {game_name!r}")
            selectors.add(game_name.casefold())
            if not isinstance(definition, dict):
                raise ValueError(f"Game {game_name!r} definition must be an object")

            aliases = definition.get("aliases", [])
            if not isinstance(aliases, list):
                raise ValueError(f"Game {game_name!r} aliases must be a list")
            for alias in aliases:
                if not _is_selector(alias):
                    raise ValueError(
                        f"Invalid alias for game {game_name!r}: {alias!r}"
                    )
                if alias.casefold() in selectors:
                    raise ValueError(f"Duplicate game selector or alias: {alias!r}")
                selectors.add(alias.casefold())

            config: dict[str, object] = {}
            for config_name, raw_value in definition.items():
                if config_name == "aliases":
                    continue
                if not (
                    isinstance(config_name, str)
                    and config_name[:1].islower()
                    and config_name.replace("_", "").isalnum()
                ):
                    raise ValueError(
                        f"Invalid game {game_name!r} configuration name: "
                        f"{config_name!r}"
                    )
                config[config_name] = resolve_catalog_value(
                    f"Game {game_name!r} configuration {config_name!r}",
                    raw_value,
                )

            content = [
                root for root in content_roots if (root / "games" / game_name).is_dir()
            ]
            if len(content) != 1:
                raise ValueError(
                    f"Registered game {game_name!r} must exist in exactly one "
                    f"configured pcsx2_files root; found {len(content)}"
                )
            derived = game_catalog.derive_game_paths(
                game_name, catalog, {**roots, "pcsx2_files": content[0]}
            )
            for name in (
                "input_profile",
                "input_profile_overrides",
                "cheats",
                "game_settings",
                "memory_card",
            ):
                if name in derived:
                    config[name] = derived[name]
            files.setdefault("input_profile", derived["input_profile"])

            extracted_path = derived["extracted"]
            if not allow_missing and not extracted_path.exists():
                raise FileNotFoundError(
                    f"Configured source extraction for {game_name!r}: "
                    f"{extracted_path}"
                )
            game_key = game_name.casefold()
            for kind, mapping, name, value in (
                ("root", roots, f"source_{game_key}", extracted_path),
                ("file", files, f"{game_key}_iso", derived["iso"]),
                ("file", files, f"{game_key}_memory_card", derived["memory_card"]),
            ):
                if name in mapping:
                    raise ValueError(
                        f"Project {kind} {name!r} duplicates game catalogs"
                    )
                mapping[name] = value
            for alias in aliases:
                roots.setdefault(f"source_{alias.casefold()}", extracted_path)
                files.setdefault(f"{alias.casefold()}_iso", derived["iso"])
            games[game_name] = MappingProxyType(
                {"aliases": tuple(aliases), "config": MappingProxyType(config)}
            )

    return Paths(
        manifest_path,
        MappingProxyType(roots),
        MappingProxyType(files),
        settings,
        MappingProxyType(games),
    )


def load_local_paths(
    start: Path | None = None, *, allow_missing: bool = False
) -> Paths:
    """Load only paths owned by this repository, without imported projects."""
    return _load_paths(start, allow_missing=allow_missing, include_imports=False)


def load_paths(
    start: Path | None = None, *, allow_missing: bool = False
) -> Paths:
    return _load_paths(start, allow_missing=allow_missing)


def resolve_alias(value: str, paths: Paths) -> Path:
    """Resolve @root/child syntax used by declarative profile root tables."""
    if not value.startswith("@"):
        raise ValueError(f"Project path alias must start with '@': {value!r}")
    root_and_child = value[1:].replace("\\", "/").split("/", 1)
    root = root_and_child[0]
    child = root_and_child[1] if len(root_and_child) == 2 else ""
    child_path = Path(child)
    if not root or child_path.is_absolute() or ".." in child_path.parts:
        raise ValueError(f"Invalid project path alias: {value!r}")
    return paths.path(root, child)


def _json_value(value: object) -> object:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return dict(value)
    raise TypeError(f"Cannot serialize {type(value).__name__}")


def main() -> int:
    """Print resolved paths as JSON for the PowerShell loader."""
    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--allow-missing", action="store_true")
    parser.add_argument("--local", action="store_true")
    args = parser.parse_args()
    loader = load_local_paths if args.local else load_paths
    try:
        paths = loader(args.manifest, allow_missing=args.allow_missing)
    except (ImportError, KeyError, OSError, ValueError) as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "manifest": paths.manifest,
                "roots": paths.roots,
                "files": paths.files,
                "settings": paths.settings,
                "games": paths.games,
            },
            default=_json_value,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
