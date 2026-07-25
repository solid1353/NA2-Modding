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
