# Project path configuration

`project-paths.json` is the single source of truth for project directory roots
and canonical project files. Every persisted value in it must be relative to
the repository directory or another named root; the PowerShell and Python
loaders reject absolute paths. A repository migration or a move of shared
media/tools should require changing this file only.

`existence_deferred_roots` lists protected roots whose paths and aliases are
validated without probing the filesystem during ordinary manifest loading.
Their authorized user or provisioning consumer performs the necessary
existence/content validation at the point of use. Descendant root aliases
inherit the same deferred behavior.

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
- `build`, `logs`, `patcher`, `scripts`, and `work`:
  their corresponding project areas.
- `workstream_logs`: shared generated evidence grouped below
  `@logs/workstreams/<exact task title>/`; see `docs/LOGGING.md`.
- `features`: the canonical feature-package root beneath `@patcher/`; profile
  module discovery resolves this root instead of hardcoding its repository path.
- `pcsx2_files`: project-owned PCSX2-related files: the canonical PNACH,
  screenshots, and input recordings.
- `pcsx2_user`: the user's protected portable PCSX2 installation. User launch,
  build-promotion, and actualization commands address it; agents do not.
- `pcsx2_clean`: the protected immutable worker template under
  `@utils/pcsx2_clean/`. The maintained provisioner may only validate and copy
  its complete tree into `work/<task title>/pcsx2/`; it is never launched or
  modified directly.
- `pcsx2_user_gamesettings` and `pcsx2_user_memcards`: user-state children of
  `@pcsx2_user/` used only by user-owned actualization.

Documentation uses `@root/child` notation, such as `@source_na2/PRG/BTL.BIN`.
This is a logical reference, not a literal filesystem path. Profile `roots.tsv`
files accept the same syntax. Enabled feature folders are resolved through
`@features/` and pinned by aggregate canonical-input hash.

## Named files

The manifest also defines canonical file paths which may not exist yet before
their producing workflow runs. File entries should reference a named root with
`@root/child` syntax so the root path is not duplicated:

- `pcsx2_user_exe`: `@pcsx2_user/pcsx2-qt.exe`.
- `pcsx2_user_ini`: `@pcsx2_user/inis/PCSX2.ini`.
- `canonical_cheats`: `@pcsx2_files/cheats.pnach`.
- `canonical_gamesettings`: `@pcsx2_files/gamesettings.ini`.
- `current_gamesettings`, `previous_gamesettings`, and
  `candidate_gamesettings`: generated role settings under
  `@pcsx2_user_gamesettings/.na2/`.
- `na228_base_memcard`: the copy-only
  `@pcsx2_user_memcards/Mcd001_NA228.ps2` base.
- `na228_current_memcard`, `na228_previous_memcard`, and
  `na228_candidate_memcard`: persistent role-specific working cards.
- `comparison_input_profile`:
  `@pcsx2_files/input_profiles/Comparison.ini`.
- `comparison_na2_input_profile`:
  `@pcsx2_files/input_profiles/Comparison_NA2.ini`.
- `notification_state`: the shared mute state for the dedicated Notifications
  task at `@repository/.agents/notifications.json`.
- `na2_command`: `@repository/_na2.ps1`.
- `na2_iso`: `@source/NA2.iso`.
- `nun3_iso`: `@source/NUN3.iso`.
- `nun5_iso`: `@source/NUN5.iso`.
- `nun6_iso`: `@source/NUN6 A35.iso`.
- `current_iso`: `@build/NA2.28 - Current.iso`.
- `previous_iso`: `@build/NA2.28 - Previous.iso`.
- `candidate_iso`: `@build/NA2.28 - Candidate.iso`.

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

The ignored repository-root `source`, `pcsx2`, and `utils` symlinks are human
convenience links to the corresponding parent-level directories and are the
local bindings for `@source`, `@pcsx2_user`, and `@utils`. A fresh checkout must
recreate them before loading the manifest. The `pcsx2` link still points to a
protected user installation and grants agents no access.
