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
- `source`: read-only original media and extracted views under the sibling
  `UN Workshop/source/` tree.
- `source_na2`: the extracted read-only NA2 source tree.
- `source_nun3`: the extracted read-only NUN3 source tree.
- `source_nun5`: the extracted read-only NUN5 source tree.
- `source_nun6`: the extracted read-only NUN6 A35 source tree.
- `analysis`: shared reverse-engineering projects and disassembly exports under
  `UN Workshop/analysis/`.
- `utils`: shared utilities under `UN Workshop/tools/`, including Ghidra and
  the untrusted historical dump.
- `build`, `logs`, `patcher`, `scripts`, and `work`:
  their corresponding project areas.
- `pcsx2_scripts`: maintained PCSX2 launch, process, configuration, and CRC
  helpers under `@scripts/pcsx2/`.
- `workstream_logs`: shared generated evidence grouped below
  `@logs/workstreams/<exact task title>/`; see `docs/LOGGING.md`.
- `features`: the canonical feature-package root beneath `@patcher/`; profile
  module discovery resolves this root instead of hardcoding its repository path.
- `pcsx2_files`: shared PCSX2-related files under
  `UN Workshop/pcsx2/files/`.
- `pcsx2_game_settings`, `pcsx2_input_profiles`, and
  `pcsx2_input_recordings`: the three project trees maintained by
  `act links`.
- `pcsx2_user`: the user's protected portable stable PCSX2 installation under
  `UN Workshop/pcsx2/stable/`. User launch, build-promotion, and actualization
  commands address it; agents do not.
- `pcsx2_dev`: the locally built, reload-enabled PCSX2 development runtime
  copied from the separate PCSX2 source checkout into
  `UN Workshop/pcsx2/dev/`. It is existence-deferred because a fresh checkout
  does not contain the local emulator build.
- `pcsx2_clean`: the protected immutable stable worker template under
  `UN Workshop/pcsx2/clean/stable/`. Agents copy its complete tree into
  `work/<task title>/pcsx2/` before use; it is never launched or modified
  directly.
- `ps2_msys`: the local shared MSYS/PS2SDK toolchain under
  `UN Workshop/injection_lab/msys/`. Injection Lab resolves it through the
  manifest rather than storing the toolchain inside the repository.
- `pcsx2_user_gamesettings`, `pcsx2_user_inputprofiles`,
  `pcsx2_user_inputrecordings`, and `pcsx2_user_memcards`: the corresponding
  user-state children used only by user-owned actualization. The PCSX2 INI is
  not a separate manifest entry.

Documentation uses `@root/child` notation, such as `@source_na2/PRG/BTL.BIN`.
This is a logical reference, not a literal filesystem path. Profile `roots.tsv`
files accept the same syntax. Enabled feature folders are resolved through
`@features/` and pinned by aggregate canonical-input hash.

## Named files

The manifest also defines canonical file paths which may not exist yet before
their producing workflow runs. File entries should reference a named root with
`@root/child` syntax so the root path is not duplicated:

- `pcsx2_user_exe`: `@pcsx2_user/pcsx2-qt.exe`, used by user-owned launch and
  standard-build process control.
- `pcsx2_dev_exe`: `@pcsx2_dev/pcsx2-qtx64-avx2-dev.exe`, used for explicit
  Injection Lab development runs.
- `canonical_cheats`: `@pcsx2_files/cheats.pnach`.
- `canonical_gamesettings`: `@pcsx2_files/gamesettings.ini`.
- `comparison_input_profile`:
  `@pcsx2_files/input_profiles/Comparison.ini`.
- `comparison_na2_input_profile`:
  `@pcsx2_files/input_profiles/Comparison_NA2.ini`.
- `notification_state`: the shared mute state for the dedicated Notifications
  task at `@repository/.agents/notifications.json`.
- `na2_command`: `@repository/_na2.ps1`.
- `pcsx2_launch_command`: `@pcsx2_scripts/launch.ps1`.
- `pcsx2_savestate_move_command`:
  `@pcsx2_scripts/move_na2_savestates.ps1`.
- `pcsx2_game_commands`: `@pcsx2_scripts/game_commands.ps1`.
- `pcsx2_pair_launch_command`: `@pcsx2_scripts/launch_pair.ps1`.
- `actualize_command`: `@scripts/actualization/act.ps1`.
- `actualize_na2_command`, `actualize_input_command`, and
  `actualize_links_command`: the three standalone actualization modes.
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

Shared media, analysis, tools, and PCSX2 roots resolve directly into the
sibling `UN Workshop/` tree. No repository-root convenience symlinks are
required. The stable PCSX2 binding remains protected and grants agents no
additional access.
