#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[4]
if str(REPOSITORY) not in sys.path:
    sys.path.insert(0, str(REPOSITORY))

from na2_patcher.modules.raw_binary.engine import load_package


GAMETITLE = "gametitle=Naruto Shippuuden: Narutimate Accel 2 (SLPS-25837)"


def render_package(package_directory: Path) -> str:
    package = load_package(package_directory)
    lines = [GAMETITLE, "", "// # Rendering", ""]
    for patch in package.patches.values():
        lines.append(f"// [{patch.name}]")
        prefix = "" if patch.default_enabled else "// "
        edits = sorted(
            (edit for edit in package.edits if edit.patch_id == patch.patch_id),
            key=lambda edit: (edit.order, edit.edit_id),
        )
        for edit in edits:
            if edit.operation != "ee_write":
                raise ValueError(f"Rendering package contains non-EE edit: {edit.edit_id}")
            address = 0x20000000 | edit.destination_offset
            word = int.from_bytes(bytes.fromhex(edit.replacement_hex), "little")
            lines.append(f"{prefix}patch=1,EE,{address:08X},extended,{word:08X}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def repository_path(workspace: Path, value: str, label: str) -> Path:
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"{label} must be repository-relative: {value}")
    result = (workspace / candidate).resolve()
    result.relative_to(workspace)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Render raw EE writes to PNACH.")
    parser.add_argument("--workspace", type=Path, default=Path("."))
    parser.add_argument(
        "--package",
        default="na2_patcher/modules/raw_binary/patch_sets/rendering",
    )
    parser.add_argument("--output", default="cheats/SLPS-25837_C0659AD1.pnach")
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    package = repository_path(workspace, args.package, "package")
    output = repository_path(workspace, args.output, "output")
    rendered = render_package(package)
    if not output.is_file() or output.read_text(encoding="utf-8-sig") != rendered:
        output.write_text(rendered, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
