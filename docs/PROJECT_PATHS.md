# Project path configuration

`project-paths.json` is the single source of truth for project directory roots.
Every persisted value in it must be relative to the repository directory; the
PowerShell and Python loaders reject absolute paths. A repository migration or a
move of shared media/tools should require changing this file only.

## Named roots

The manifest currently defines these stable logical names:

- `repository`: the repository itself; this must remain `.`.
- `source`: read-only original media, extracted views, and preserved disassemblies.
- `utils`: shared utilities, including Ghidra and the untrusted historical dump.
- `build`, `logs`, `patcher`, `releases`, `scripts`, `trash`, and `work`:
  their corresponding project areas.
- `pcsx2_files`: project-owned PCSX2-related files: the canonical PNACH,
  screenshots, and input recordings.
- `pcsx2`: the portable, self-contained PCSX2 installation. Its support folders
  remain under `@pcsx2/`; only its CRC-named PNACH symlinks target the canonical
  project PNACH under `@pcsx2_files/`.

Documentation uses `@root/child` notation, such as `@source/NA2.iso`. This is a
logical reference, not a literal filesystem path. Profile `roots.tsv` files accept
the same syntax. Other profile inputs remain repository-relative and hash-pinned.

## PowerShell

Every PowerShell entry point dot-sources `scripts/project_paths.ps1` and loads the
manifest before doing work:

```powershell
. (Join-Path $PSScriptRoot 'project_paths.ps1')
$projectPaths = Get-Na2ProjectPaths
$iso = Join-Path $projectPaths.source 'NA2.iso'
```

The root `_na2.ps1` entry point uses `scripts/project_paths.ps1` as its bootstrap.
The manifest and both path loaders are stable bootstrap files and should not be
moved during an ordinary directory migration.

## Python

Repository Python code imports the shared loader from `na2_patcher.project_paths`.
Standalone tools in `scripts/` use the small `scripts/project_paths.py` bootstrap:

```python
from project_paths import PROJECT_PATHS

iso = PROJECT_PATHS.path("source", "NA2.iso")
```

## Migration procedure

1. Move the directory without changing its contents.
2. Edit only that root's repository-relative value in `project-paths.json`.
3. Run the path-loader checks and automated tests.
4. Search documentation for literal legacy paths and express them as `@root/...`.

Do not copy resolved absolute paths into scripts, logs, profiles, or documentation.
