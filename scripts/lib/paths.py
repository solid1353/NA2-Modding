from __future__ import annotations

import json
import importlib.util
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

MANIFEST_NAME = "paths.json"


@lru_cache(maxsize=1)
def _load_workshop_game_catalog():
    repository = Path(__file__).resolve().parents[2]
    manifest = json.loads(
        (repository / MANIFEST_NAME).read_text(encoding="utf-8")
    )
    raw_manifest = manifest.get("imports", {}).get("workshop")
    if not isinstance(raw_manifest, str) or not raw_manifest:
        raise ValueError("Project paths must import the Workshop manifest")
    import_manifest = Path(raw_manifest)
    if import_manifest.is_absolute():
        raise ValueError("Workshop manifest import must be repository-relative")
    workshop_root = Path(os.path.abspath(repository / import_manifest)).parent
    module_path = workshop_root / "scripts" / "lib" / "game_catalog.py"
    spec = importlib.util.spec_from_file_location(
        "un_workshop_game_catalog", module_path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load Workshop game catalog: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def derive_game_paths(
    game_name: str,
    catalog: dict[str, object],
    roots: Mapping[str, Path],
) -> dict[str, Path]:
    """Load Workshop game-path derivation only for callers that need it."""
    return _load_workshop_game_catalog().derive_game_paths(game_name, catalog, roots)


@dataclass(frozen=True)
class Paths:
    manifest: Path
    roots: Mapping[str, Path]
    files: Mapping[str, Path]

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


def _find_manifest(start: Path) -> Path:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for candidate_root in (current, *current.parents):
        candidate = candidate_root / MANIFEST_NAME
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"Could not find {MANIFEST_NAME} above {start}")


def _load_paths(
    start: Path | None = None,
    *,
    allow_missing: bool = False,
    include_catalog: bool = True,
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
    local_root_names = set(configured)
    local_files = data.get("files")
    if not isinstance(local_files, dict) or not local_files:
        raise ValueError("Project path manifest has no files")
    local_file_names = set(local_files)

    imports = data.get("imports", {})
    if not isinstance(imports, dict):
        raise ValueError("Project path manifest imports must be an object")
    selected_imports = imports.items() if include_imports else ()
    for import_name, raw_manifest in selected_imports:
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
        loader_path = imported_manifest.parent / "scripts" / "lib" / "paths.py"
        spec = importlib.util.spec_from_file_location(
            f"paths_import_{import_name}", loader_path
        )
        if spec is None or spec.loader is None:
            raise ImportError(
                f"Could not load path import {import_name!r}: {loader_path}"
            )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        imported = module.load_workshop_paths(imported_manifest.parent)
        imported_repository = imported.roots["repository"]
        if import_name in roots:
            raise ValueError(f"Duplicate imported root: {import_name!r}")
        roots[import_name] = imported_repository
        for name, value in imported.roots.items():
            if name == "repository" or name in local_root_names:
                continue
            if name in roots:
                raise ValueError(f"Duplicate imported root: {name!r}")
            roots[name] = value
        for name, value in imported.files.items():
            if name in local_file_names:
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
        try:
            raw_value = configured[name]
        except KeyError as exc:
            raise ValueError(f"Unknown project root: {name!r}") from exc
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
                or parent_name not in configured
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
            if (
                configured_path != base_path
                and base_path not in configured_path.parents
            ):
                raise ValueError(
                    f"Project root {name!r} must remain within {parent_name!r}"
                )
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

    if roots.get("repository") != repository:
        raise ValueError(
            "The 'repository' root must resolve to the directory containing "
            f"{MANIFEST_NAME}"
        )
    configured_files = local_files
    for name, raw_value in configured_files.items():
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
        if raw_value.startswith("@") and base_path not in configured_path.parents:
            raise ValueError(
                f"Project file {name!r} must remain within its configured root"
            )
        if not raw_value.startswith("@") and repository not in configured_path.parents:
            raise ValueError(
                f"Project file {name!r} must remain within the repository"
            )
        files[name] = configured_path

    settings_path = files.get("project_settings") if include_catalog else None
    if settings_path is not None:
        if not settings_path.is_file():
            raise FileNotFoundError(f"Project settings not found: {settings_path}")
        project_settings = json.loads(settings_path.read_text(encoding="utf-8"))
        source_catalog_path = files.get("source_catalog")
        if source_catalog_path is not None:
            if not source_catalog_path.is_file():
                raise FileNotFoundError(
                    f"Source game catalog not found: {source_catalog_path}"
                )
            source_catalog = json.loads(
                source_catalog_path.read_text(encoding="utf-8")
            )
            catalog = {
                "sources": source_catalog.get("sources"),
                "title": project_settings.get("title"),
                "serial": project_settings.get("serial"),
            }
        else:
            catalog = project_settings

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
            result = Path(os.path.abspath(base_path / child_path))
            if base_path not in result.parents:
                raise ValueError(f"{label} must remain within {root_name!r}")
            return result

        selectors: set[str] = set()
        for category in ("sources",):
            section = catalog.get(category)
            if not isinstance(section, dict) or not section:
                raise ValueError(
                    f"Game catalog has no non-empty {category!r} section"
                )
            resolved_category_config: dict[str, object] = {}
            definitions = section

            for game_name, definition in definitions.items():
                if (
                    not isinstance(game_name, str)
                    or not game_name
                    or not game_name[0].isalnum()
                    or not game_name.replace("_", "").isalnum()
                ):
                    raise ValueError(
                        f"Invalid canonical game selector: {game_name!r}"
                    )
                if game_name.casefold() in selectors:
                    raise ValueError(
                        f"Duplicate game selector or alias: {game_name!r}"
                    )
                selectors.add(game_name.casefold())
                if not isinstance(definition, dict):
                    raise ValueError(
                        f"Game {game_name!r} definition must be an object"
                    )

                aliases = definition.get("aliases")
                if aliases is None:
                    aliases = []
                elif not isinstance(aliases, list):
                    raise ValueError(
                        f"Game {game_name!r} aliases must be a list"
                    )
                for alias in aliases:
                    if (
                        not isinstance(alias, str)
                        or not alias
                        or not alias[0].isalnum()
                        or not alias.replace("_", "").isalnum()
                    ):
                        raise ValueError(
                            f"Invalid alias for game {game_name!r}: {alias!r}"
                        )
                    if alias.casefold() in selectors:
                        raise ValueError(
                            f"Duplicate game selector or alias: {alias!r}"
                        )
                    selectors.add(alias.casefold())

                memory_card_path: Path | None = None
                structural_fields = {"aliases", "postfix"}
                resolved_game_config = dict(resolved_category_config)
                for config_name, raw_value in definition.items():
                    if config_name in structural_fields:
                        continue
                    if (
                        not isinstance(config_name, str)
                        or not config_name
                        or not config_name[0].islower()
                        or not config_name.replace("_", "").isalnum()
                    ):
                        raise ValueError(
                            f"Invalid game {game_name!r} configuration name: "
                            f"{config_name!r}"
                        )
                    resolved_game_config[config_name] = resolve_catalog_value(
                        f"Game {game_name!r} configuration {config_name!r}",
                        raw_value,
                    )

                derived = derive_game_paths(game_name, catalog, roots)
                iso_path = derived["iso"]
                memory_card_path = derived["memory_card"]
                extracted_path = derived.get("extracted")
                files.setdefault("input_profile", derived["input_profile"])
                assert extracted_path is not None
                if not allow_missing and not extracted_path.exists():
                    raise FileNotFoundError(
                        f"Configured source extraction for {game_name!r}: "
                        f"{extracted_path}"
                    )
                root_name = f"source_{game_name.casefold()}"
                if root_name in roots:
                    raise ValueError(
                        f"Project root {root_name!r} duplicates game catalogs"
                    )
                roots[root_name] = extracted_path

                file_name = f"{game_name.casefold()}_iso"
                if file_name in files:
                    raise ValueError(
                        f"Project file {file_name!r} duplicates game catalogs"
                    )
                files[file_name] = iso_path
                if memory_card_path is not None:
                    memory_card_file = f"{game_name.casefold()}_memory_card"
                    if memory_card_file in files:
                        raise ValueError(
                            f"Project file {memory_card_file!r} duplicates "
                            "games.json"
                        )
                    files[memory_card_file] = memory_card_path

                for alias in aliases:
                    alias_name = alias.casefold()
                    roots.setdefault(f"source_{alias_name}", extracted_path)
                    files.setdefault(f"{alias_name}_iso", iso_path)

    return Paths(
        manifest_path,
        MappingProxyType(roots),
        MappingProxyType(files),
    )


def load_local_paths(
    start: Path | None = None, *, allow_missing: bool = False
) -> Paths:
    """Load only paths owned by this repository, without imported projects."""
    return _load_paths(
        start,
        allow_missing=allow_missing,
        include_catalog=False,
        include_imports=False,
    )


def load_paths(
    start: Path | None = None, *, allow_missing: bool = False
) -> Paths:
    return _load_paths(
        start, allow_missing=allow_missing, include_catalog=True
    )


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
