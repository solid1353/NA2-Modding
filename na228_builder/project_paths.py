from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping


MANIFEST_NAME = "project-paths.json"


@dataclass(frozen=True)
class ProjectPaths:
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


def load_project_paths(
    start: Path | None = None, *, allow_missing: bool = False
) -> ProjectPaths:
    manifest_path = _find_manifest(start or Path.cwd())
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError(
            f"Unsupported project path manifest schema: {data.get('schema_version')!r}"
        )
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
    roots: dict[str, Path] = {}
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
    configured_files = data.get("files")
    if not isinstance(configured_files, dict) or not configured_files:
        raise ValueError("Project path manifest has no files")
    files: dict[str, Path] = {}
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

    catalog_path = files.get("game_catalog")
    if catalog_path is not None:
        if not catalog_path.is_file():
            raise FileNotFoundError(f"Game catalog not found: {catalog_path}")
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        if catalog.get("schema_version") != 1:
            raise ValueError(
                "Unsupported game catalog schema: "
                f"{catalog.get('schema_version')!r}"
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
            result = Path(os.path.abspath(base_path / child_path))
            if base_path not in result.parents:
                raise ValueError(f"{label} must remain within {root_name!r}")
            return result

        global_config = catalog.get("config", {})
        if not isinstance(global_config, dict):
            raise ValueError("Game catalog 'config' must be an object")
        resolved_global_config: dict[str, object] = {}
        for config_name, raw_value in global_config.items():
            if (
                not isinstance(config_name, str)
                or not config_name
                or not config_name[0].islower()
                or not config_name.replace("_", "").isalnum()
            ):
                raise ValueError(
                    f"Invalid global game configuration name: {config_name!r}"
                )
            if config_name in files:
                raise ValueError(
                    f"Project file {config_name!r} duplicates games.json"
                )
            resolved = resolve_catalog_value(
                f"Global game configuration {config_name!r}",
                raw_value,
            )
            resolved_global_config[config_name] = resolved
            if isinstance(resolved, Path):
                files[config_name] = resolved

        selectors: set[str] = set()
        for category in ("builds", "sources"):
            section = catalog.get(category)
            if not isinstance(section, dict) or not section:
                raise ValueError(
                    f"Game catalog has no non-empty {category!r} section"
                )
            resolved_category_config = dict(resolved_global_config)
            if category == "builds":
                definitions = section.get("entries")
                if not isinstance(definitions, dict) or not definitions:
                    raise ValueError(
                        "Game catalog 'builds' section has no non-empty "
                        "'entries' object"
                    )
                category_config = {
                    name: value
                    for name, value in section.items()
                    if name != "entries"
                }
                for config_name, raw_value in category_config.items():
                    if (
                        not isinstance(config_name, str)
                        or not config_name
                        or not config_name[0].islower()
                        or not config_name.replace("_", "").isalnum()
                    ):
                        raise ValueError(
                            f"Invalid {category!r} configuration name: "
                            f"{config_name!r}"
                        )
                    resolved = resolve_catalog_value(
                        f"Game category {category!r} configuration "
                        f"{config_name!r}",
                        raw_value,
                    )
                    resolved_category_config[config_name] = resolved
                    if isinstance(resolved, Path):
                        files.setdefault(config_name, resolved)
            else:
                definitions = section

            for game_name, definition in definitions.items():
                if (
                    not isinstance(game_name, str)
                    or not game_name
                    or not game_name[0].islower()
                    or not game_name.isalnum()
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
                        or not alias[0].islower()
                        or not alias.isalnum()
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
                structural_fields = {"aliases", "postfix", "iso", "extracted"}
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

                if category == "builds":
                    title = resolved_category_config.get("title")
                    if (
                        not isinstance(title, str)
                        or not title.strip()
                        or Path(title).name != title
                    ):
                        raise ValueError(
                            f"Game catalog has an invalid build title: {title!r}"
                        )
                    memory_card_template = resolved_category_config.get(
                        "memory_card"
                    )
                    if not isinstance(memory_card_template, Path):
                        raise ValueError(
                            "Game catalog has no valid build memory_card"
                        )
                    postfix = definition.get("postfix")
                    if (
                        not isinstance(postfix, str)
                        or not postfix.strip()
                        or Path(postfix).name != postfix
                    ):
                        raise ValueError(
                            f"Game {game_name!r} has an invalid build postfix: "
                            f"{postfix!r}"
                        )
                    try:
                        build_root = roots["build"]
                    except KeyError as exc:
                        raise ValueError(
                            f"Build game {game_name!r} requires project root "
                            f"{exc.args[0]!r}"
                        ) from exc
                    iso_path = build_root / f"{title} - {postfix}.iso"
                    memory_card_path = memory_card_template.with_name(
                        f"{memory_card_template.stem} - {postfix}"
                        f"{memory_card_template.suffix}"
                    )
                else:
                    iso_path = resolve_catalog_value(
                        f"Game {game_name!r} ISO path",
                        definition.get("iso"),
                    )
                    extracted_path = resolve_catalog_value(
                        f"Game {game_name!r} extracted path",
                        definition.get("extracted"),
                    )
                    if not isinstance(iso_path, Path):
                        raise ValueError(
                            f"Game {game_name!r} ISO path is not a path"
                        )
                    if not isinstance(extracted_path, Path):
                        raise ValueError(
                            f"Game {game_name!r} extracted path is not a path"
                        )
                    if not allow_missing and not extracted_path.exists():
                        raise FileNotFoundError(
                            f"Configured source extraction for {game_name!r}: "
                            f"{extracted_path}"
                        )
                    root_name = f"source_{game_name}"
                    if root_name in roots:
                        raise ValueError(
                            f"Project root {root_name!r} duplicates games.json"
                        )
                    roots[root_name] = extracted_path

                file_name = f"{game_name}_iso"
                if file_name in files:
                    raise ValueError(
                        f"Project file {file_name!r} duplicates games.json"
                    )
                files[file_name] = iso_path
                if memory_card_path is not None:
                    memory_card_file = f"{game_name}_memory_card"
                    if memory_card_file in files:
                        raise ValueError(
                            f"Project file {memory_card_file!r} duplicates "
                            "games.json"
                        )
                    files[memory_card_file] = memory_card_path

    return ProjectPaths(
        manifest_path,
        MappingProxyType(roots),
        MappingProxyType(files),
    )


def resolve_alias(value: str, paths: ProjectPaths) -> Path:
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
