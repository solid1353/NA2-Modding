# Project path configuration

`project-paths.json` is the single source of truth for project directory roots
and canonical project files. Every persisted value in it must be relative to
the repository directory or another named root; the PowerShell and Python
loaders reject absolute paths. A repository migration or a move of shared
media/tools should require changing this file only.

The loader supports an optional `existence_deferred_roots` list for portable
manifests whose external resources are provisioned only at use time. The
current project does not defer any roots: every configured local root must
exist during ordinary manifest loading.

Stable paths and named files used by maintained workflows belong in this
manifest instead of being repeated as literals. Prefer the root and file
abstractions wherever they make the workflow easier to relocate or understand,
but do not add entries solely for transient, generated, caller-supplied, or
genuinely local one-off paths.

## Named roots

The manifest currently defines these stable logical names:

- `repository`: the repository itself; this must remain `.`.
- `workshop`: the sibling `UN Workshop/` environment containing shared media,
  analysis, tools, and configured emulator installations.
- `source`: read-only original media and extracted views under
  `@workshop/source/`.
- `source_na2`: the extracted read-only NA2 source tree.
- `source_nun3`: the extracted read-only NUN3 source tree.
- `source_nun5`: the extracted read-only NUN5 source tree.
- `source_nun6`: the extracted read-only NUN6 A35 source tree.
- `analysis`: shared reverse-engineering projects and disassembly exports under
  `@workshop/analysis/`.
- `utils`: shared utilities under `@workshop/tools/`, including Ghidra and
  the untrusted historical dump.
- `build`, `logs`, `builder`, `scripts`, and `work`:
  their corresponding project areas.
- `pcsx2_scripts`: maintained PCSX2 launch, process, configuration, and CRC
  helpers under `@scripts/pcsx2/`.
- `workstream_logs`: shared generated evidence grouped below
  `@logs/workstreams/<exact task title>/`; see `docs/LOGGING.md`.
- `features`: the canonical feature-package root beneath `@builder/`; profile
  module discovery resolves this root instead of hardcoding its repository path.
- `pcsx2_files`: shared PCSX2-related files under
  `@workshop/pcsx2/__shared/`.
- `pcsx2_bios`, `pcsx2_cheats`, `pcsx2_game_settings`,
  `pcsx2_input_profiles`, `pcsx2_input_recordings`, and
  `pcsx2_memory_cards`: the canonical shared asset categories used by both
  configured PCSX2 installations. Input recordings are opened explicitly
  because PCSX2 does not expose a configurable folder for them.
- `pcsx2_stable`: the user's protected portable stable PCSX2 installation under
  `@workshop/pcsx2/stable/`, retained for explicit compatibility and release
  checks.
- `pcsx2_dev`: the locally built, reload-enabled PCSX2 development runtime
  copied from the separate PCSX2 source checkout into `@workshop/pcsx2/dev/`.
  It is the default for configured user-facing launch and savestate commands.
- `pcsx2_clean`: the protected immutable worker template at the external
  PCSX2 checkout's clean compiled `bin/` output (`../../PCSX2/bin`). Agents
  copy it into `work/<task title>/pcsx2/` and may copy any assets for which
  they have a concrete task- or test-related reason from `@pcsx2_files` into
  the task-owned runtime. The source template is never populated, launched,
  or modified directly.
- `ps2_msys`: the local shared MSYS/PS2SDK toolchain under
  `@workshop/tools/msys/`. The runtime-injection compiler resolves it through
  the manifest rather than storing the toolchain inside the repository.

Documentation uses `@root/child` notation, such as `@source_na2/PRG/BTL.BIN`.
This is a logical reference, not a literal filesystem path. Profile `roots.tsv`
files accept the same syntax. Enabled feature folders are resolved through
`@features/` and pinned by aggregate canonical-input hash.

## Named files

The manifest also defines canonical file paths which may not exist yet before
their producing workflow runs. File entries should reference a named root with
`@root/child` syntax so the root path is not duplicated:

- `pcsx2_stable_exe`: `@pcsx2_stable/pcsx2-qt.exe`, used for explicit stable
  compatibility and release checks.
- `pcsx2_dev_exe`: `@pcsx2_dev/pcsx2-qtx64-avx2-dev.exe`, used by default
  configured launches and user runtime-injection development.
- `cheat_template`: `@pcsx2_cheats/SLOP-NA228.pnach`.
- `gamesettings_template`: `@pcsx2_game_settings/SLOP-NA228.ini`.
- `current_memory_card`: `@pcsx2_memory_cards/NA228 - Current.ps2`.
- `previous_memory_card`: `@pcsx2_memory_cards/NA228 - Previous.ps2`.
- `candidate_memory_card`: `@pcsx2_memory_cards/NA228 - Candidate.ps2`.
- `comparison_input_profile`:
  `@pcsx2_files/input_profiles/Comparison.ini`.
- `comparison_na2_input_profile`:
  `@pcsx2_files/input_profiles/Comparison_NA2.ini`.
- `notification_state`: the shared mute state for the dedicated Notifications
  task at `@repository/.agents/notifications.json`.
- `na228_command`: `@repository/_na228.ps1`.
- `pcsx2_launch_command`: `@pcsx2_scripts/launch.ps1`.
- `pcsx2_savestate_move_command`:
  `@pcsx2_scripts/move_na228_savestates.ps1`.
- `na228_game_launch_command`: `@scripts/na228/launch_games.ps1`.
- `actualize_command`: `@pcsx2_scripts/actualization/act.ps1`.
- `actualize_na228_command` and `actualize_input_command`: the two standalone
  actualization modes under `@pcsx2_scripts/actualization/`.
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

The root `_na228.ps1` entry point uses `scripts/lib/project_paths.ps1` as its
bootstrap. The manifest and shared path loaders are stable bootstrap files and
should not be moved during an ordinary directory migration.

## Python

Repository Python code imports the shared loader from
`na228_builder.project_paths`. Preserved menu-input research tools use their small
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

Shared media, analysis, tools, and PCSX2 roots resolve through `@workshop`.
No repository-root convenience symlinks are
required. Stable and development PCSX2 resolve shared asset folders directly
through their native `[Folders]` configuration. The stable PCSX2 binding
remains protected and grants agents no additional access.
