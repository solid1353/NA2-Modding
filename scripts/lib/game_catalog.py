from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Mapping


def _required_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _root(roots: Mapping[str, Path], name: str) -> Path:
    try:
        return roots[name]
    except KeyError as exc:
        raise ValueError(f"Game path derivation requires project root {name!r}") from exc


def _find_definition(
    selector: str, catalog: Mapping[str, object]
) -> tuple[str, str, Mapping[str, object], Mapping[str, object]]:
    requested = selector.casefold()
    match: tuple[str, str, Mapping[str, object], Mapping[str, object]] | None = None

    for category in ("builds", "sources"):
        section = catalog.get(category)
        if not isinstance(section, dict) or not section:
            raise ValueError(f"Game catalog has no non-empty {category!r} section")
        definitions = section.get("entries") if category == "builds" else section
        if not isinstance(definitions, dict) or not definitions:
            raise ValueError(f"Game catalog has no non-empty {category!r} entries")

        for canonical_name, raw_definition in definitions.items():
            if not isinstance(canonical_name, str) or not canonical_name:
                raise ValueError(f"Invalid canonical game selector: {canonical_name!r}")
            if not isinstance(raw_definition, dict):
                raise ValueError(
                    f"Game {canonical_name!r} definition must be an object"
                )
            aliases = raw_definition.get("aliases", [])
            if not isinstance(aliases, list) or any(
                not isinstance(alias, str) or not alias for alias in aliases
            ):
                raise ValueError(f"Game {canonical_name!r} aliases must be strings")
            names = (canonical_name, *aliases)
            if any(name.casefold() == requested for name in names):
                if match is not None:
                    raise ValueError(f"Duplicate game selector or alias: {selector!r}")
                match = (category, canonical_name, raw_definition, section)

    if match is None:
        raise KeyError(f"Unknown game selector: {selector}")
    return match


def derive_game_paths(
    selector: str,
    catalog: Mapping[str, object],
    roots: Mapping[str, Path],
) -> dict[str, Path]:
    category, canonical_name, definition, section = _find_definition(
        selector, catalog
    )
    global_config = catalog.get("config", {})
    if not isinstance(global_config, dict):
        raise ValueError("Game catalog 'config' must be an object")
    input_profile = _required_text(
        definition.get("input_profile", global_config.get("input_profile")),
        f"Game {canonical_name!r} input_profile",
    )
    if Path(input_profile).name != input_profile or Path(input_profile).suffix:
        raise ValueError(
            f"Game {canonical_name!r} input_profile must be a profile name"
        )
    input_profile_path = (
        _root(roots, "pcsx2_input_profiles") / f"{input_profile}.ini"
    )

    if category == "sources":
        serial = _required_text(
            definition.get("serial"), f"Game {canonical_name!r} serial"
        )
        crc = _required_text(
            definition.get("crc"), f"Game {canonical_name!r} crc"
        ).upper()
        source = _root(roots, "source")
        extracted = source / f"{canonical_name}.iso.files"
        result = {
            "iso": source / f"{canonical_name}.iso",
            "extracted": extracted,
            "cheats": _root(roots, "pcsx2_cheats") / f"{serial}_{crc}.pnach",
            "game_settings": (
                _root(roots, "pcsx2_game_settings") / f"{serial}_{crc}.ini"
            ),
            "memory_card": (
                _root(roots, "pcsx2_memory_cards") / f"{canonical_name}.ps2"
            ),
            "input_profile": input_profile_path,
        }
        return result

    title = _required_text(section.get("title"), "Build title")
    serial = _required_text(section.get("serial"), "Build serial")
    postfix = _required_text(
        definition.get("postfix"), f"Game {canonical_name!r} postfix"
    )
    return {
        "iso": _root(roots, "build") / f"{title} - {postfix}.iso",
        "cheats": _root(roots, "pcsx2_cheats") / f"_{serial}.pnach",
        "game_settings": (
            _root(roots, "pcsx2_game_settings") / f"_{serial}.ini"
        ),
        "memory_card": (
            _root(roots, "pcsx2_memory_cards") / f"{title} - {postfix}.ps2"
        ),
        "input_profile": input_profile_path,
    }


def resolve_game(selector: str) -> dict[str, str]:
    from .project_paths import load_base_project_paths

    root = Path(__file__).resolve().parents[2]
    paths = load_base_project_paths(root, allow_missing=True)
    catalog_path = paths.file("game_catalog")
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    if catalog.get("schema_version") != 1:
        raise ValueError(
            f"Unsupported game catalog schema: {catalog.get('schema_version')!r}"
        )
    return {
        name: os.path.abspath(path)
        for name, path in derive_game_paths(
            selector, catalog, paths.roots
        ).items()
    }
