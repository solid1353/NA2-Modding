# Project path configuration

`project-paths.json` is the single source of truth for project directory roots
and canonical project files. Every persisted value in it must be relative to
the repository directory or another named root; the PowerShell and Python
loaders reject absolute paths. A repository migration or a move of shared
media/tools should require changing this file only.

Stable paths and named files used by maintained workflows belong in this
manifest instead of being repeated as literals. Prefer the root and file
abstractions wherever they make the workflow easier to relocate or understand,
but do not add entries solely for transient, generated, caller-supplied, or
genuinely local one-off paths.

## Named roots

The manifest currently defines these stable logical names:

- `repository`: the repository itself; this must remain `.`.
- `source`: read-only original media and extracted views.
- `source_na2`: the extracted read-only NA2 source tree.
- `source_nun3`: the extracted read-only NUN3 source tree.
- `source_nun5`: the extracted read-only NUN5 source tree.
- `source_nun6`: the extracted read-only NUN6 A35 source tree.
- `analysis`: shared reverse-engineering projects and disassembly exports for
  related game projects.
- `utils`: shared utilities, including Ghidra and the untrusted historical dump.
- `build`, `logs`, `patcher`, `releases`, `scripts`, and `work`:
  their corresponding project areas.
- `features`: the canonical feature-package root beneath `@patcher/`; profile
  module discovery resolves this root instead of hardcoding its repository path.
- `pcsx2_files`: project-owned PCSX2-related files: the canonical PNACH,
  screenshots, and input recordings.
- `pcsx2`: the portable, self-contained PCSX2 installation. Its support folders
  remain under `@pcsx2/`; only its CRC-named PNACH symlinks target the canonical
  project PNACH under `@pcsx2_files/`.

Documentation uses `@root/child` notation, such as `@source_na2/PRG/BTL.BIN`.
This is a logical reference, not a literal filesystem path. Profile `roots.tsv`
files accept the same syntax. Enabled feature folders are resolved through
`@features/` and pinned by aggregate canonical-input hash.

## Named files

The manifest also defines canonical file paths which may not exist yet before
their producing workflow runs. File entries should reference a named root with
`@root/child` syntax so the root path is not duplicated:

- `na2_iso`: `@source/NA2.iso`.
- `nun3_iso`: `@source/NUN3.iso`.
- `nun5_iso`: `@source/NUN5.iso`.
- `nun6_iso`: `@source/NUN6 A35.iso`.
- `current_iso`: `@build/NA2.28 - Current.iso`.
- `previous_iso`: `@build/NA2.28 - Previous.iso`.

PowerShell accesses these as `$projectPaths.files.na2_iso` and
`$projectPaths.files.current_iso`. Python accesses them through calls such as
`PROJECT_PATHS.file("nun5_iso")` and `PROJECT_PATHS.file("previous_iso")`.

## PowerShell

Every PowerShell entry point dot-sources `scripts/lib/project_paths.ps1` and
loads the manifest before doing work. For example, a script one directory below
`scripts/` uses:

```powershell
. (Join-Path $PSScriptRoot '..\lib\project_paths.ps1')
$projectPaths = Get-Na2ProjectPaths
$iso = $projectPaths.files.na2_iso
```

The root `_na2.ps1` entry point uses `scripts/lib/project_paths.ps1` as its
bootstrap. The manifest and shared path loaders are stable bootstrap files and
should not be moved during an ordinary directory migration.

## Python

Repository Python code imports the shared loader from
`na2_patcher.project_paths`. Preserved menu-input research tools use their small
local `scripts/research/menu_input/project_paths.py` bootstrap:

```python
from project_paths import PROJECT_PATHS

iso = PROJECT_PATHS.file("na2_iso")
```

## Migration procedure

1. Move the directory or canonical file without changing its contents.
2. Edit only that root or file's repository-relative value in
   `project-paths.json`.
3. Run the path-loader checks and automated tests.
4. Search documentation for literal legacy paths and express them as `@root/...`.

Do not copy resolved absolute paths into scripts, logs, profiles, or documentation.
