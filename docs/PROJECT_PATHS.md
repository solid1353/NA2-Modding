# Project path configuration

`project-paths.json` is the source of truth for stable project infrastructure
roots and named files. `games.json` is the source of truth for registered
source games, NA2.28 build roles, selector aliases, and their game-specific
configuration. The shared PowerShell and Python loaders merge both files.
Every persisted path must be relative to the repository directory or another
named root; both loaders reject absolute paths.

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
- `source_na2`, `source_nun3`, `source_nun5`, and `source_nun6`: derived by
  the loaders from each source game's `extracted` path in `games.json`.
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
  create task-owned runtimes with `scripts/pcsx2/copy_worker.ps1`, which copies
  the template and shared BIOS together. They may then copy any other assets
  for which they have a concrete task- or test-related reason from
  `@pcsx2_files`. The source template is never populated, launched, or modified
  directly.
- `ps2_msys`: the local shared MSYS/PS2SDK toolchain under
  `@workshop/tools/msys/`. The runtime-injection compiler resolves it through
  the manifest rather than storing the toolchain inside the repository.

Documentation uses `@root/child` notation, such as `@source_na2/PRG/BTL.BIN`.
This is a logical reference, not a literal filesystem path. Profile `roots.tsv`
files accept the same syntax. Enabled feature folders are resolved through
`@features/` and pinned by aggregate canonical-input hash.

## Named files

The manifest defines infrastructure entry points which may not exist yet before
their producing workflow runs. File entries reference a named root with
`@root/child` syntax so the root path is not duplicated:

- `pcsx2_stable_exe`: `@pcsx2_stable/pcsx2-qt.exe`, used for explicit stable
  compatibility and release checks.
- `pcsx2_dev_exe`: `@pcsx2_dev/pcsx2-qtx64-avx2-dev.exe`, used by default
  configured launches and user runtime-injection development.
- `game_catalog`: `@repository/games.json`.
- `watch_catalog`: `@repository/watchers.json`, containing named user-facing
  live-injection targets.
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

The loaders additionally expose catalog-derived compatibility files:

- `<source>_iso` from each direct `sources.<source>.iso` entry.
- `<build>_iso` as `@build/<builds.title> - <postfix>.iso`.
- `<build>_memory_card` as
  the configured `builds.memory_card` stem plus ` - <postfix>`.
- `input_profile` from the root catalog configuration.
- `cheat_template` and `gamesettings_template` from build-wide configuration.

PowerShell accesses these as `$projectPaths.files.na2_iso` and
`$projectPaths.files.latest_iso`. Python accesses them through calls such as
`PROJECT_PATHS.file("nun5_iso")` and `PROJECT_PATHS.file("previous_iso")`.

## Game catalog

`games.json` keeps `sources` as a direct game map. `builds` contains shared
build configuration plus an `entries` map because those keys occupy the same
section. Empty optional values are omitted.

Configuration inherits from root `config`, then category-wide build
configuration, then a game's own non-structural fields. The current root
default is the base `input_profile`; NA2 overrides it with the generated
`Base_NA2` mapping. Source entries also register their `cheats`,
`game_settings`, and `memory_card` files. Build entries derive their ISO and
memory-card names
from one `postfix`, while their CRC-named cheats and GameSettings continue to
be produced from the build templates.

Keep per-game configuration fields in this order when present: `cheats`,
`game_settings`, `memory_card`, `input_profile`. Build-wide equivalents use
`title`, `cheat_template`, `gamesettings_template`, `memory_card`.

The PowerShell loader exposes canonical selectors and aliases through
`$projectPaths.games`. The build aliases `l`, `p`, and `t` resolve to `latest`,
`previous`, and `test`.

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
2. Edit its repository-relative value in `project-paths.json` for shared
   infrastructure or `games.json` for a game/build entry.
3. Run the path-loader checks and automated tests.
4. Search documentation for literal legacy paths and express them as `@root/...`.

Do not copy resolved absolute paths into scripts, logs, profiles, or documentation.

Shared media, analysis, tools, and PCSX2 roots resolve through `@workshop`.
No repository-root convenience symlinks are
required. Stable and development PCSX2 resolve shared asset folders directly
through their native `[Folders]` configuration. The stable PCSX2 binding
remains protected and grants agents no additional access.
