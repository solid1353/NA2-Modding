#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


GAMETITLE = "gametitle=Naruto Shippuuden: Narutimate Accel 2 (SLPS-25837)"


def render_sections(directory: Path) -> str:
    sections = []
    for path in sorted(directory.glob("*.pnach"), key=lambda item: item.name.lower()):
        text = path.read_text(encoding="utf-8-sig").strip()
        if text:
            sections.append(text)
    return GAMETITLE + "\n\n" + "\n\n".join(sections) + "\n"


def repository_path(workspace: Path, value: str, label: str) -> Path:
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"{label} must be repository-relative: {value}")
    result = (workspace / candidate).resolve()
    result.relative_to(workspace)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Render patcher-owned PNACH sections.")
    parser.add_argument("--workspace", type=Path, default=Path("."))
    parser.add_argument(
        "--sections", default="na2_patcher/modules/pnach/sections"
    )
    parser.add_argument(
        "--output", default="cheats/SLPS-25837_C0659AD1.pnach"
    )
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    sections = repository_path(workspace, args.sections, "sections")
    output = repository_path(workspace, args.output, "output")
    if not sections.is_dir():
        raise FileNotFoundError(sections)
    output.parent.mkdir(parents=True, exist_ok=True)
    rendered = render_sections(sections)
    if not output.is_file() or output.read_text(encoding="utf-8-sig") != rendered:
        output.write_text(rendered, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
