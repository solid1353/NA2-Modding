# Project path configuration

`project-paths.json` is the root bootstrap and source of truth for stable
project infrastructure roots and named files. `settings/games.json` is the
source of truth for registered source games, NA2.28 build roles, selector
aliases, and their game-specific configuration. The shared PowerShell and
Python loaders merge both files. Every persisted path must be relative to the
repository directory or another named root; both loaders reject absolute
paths.

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
  the game resolver from each canonical source identifier. `NUN6` aliases the
  canonical `NUN6_A35` source while retaining the established root name.
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
- `game_catalog`: `@repository/settings/games.json`.
- `notification_state`: the shared mute state for the dedicated Notifications
  task at `@repository/settings/notifications.json`.
- `na228_command`: `@repository/na228.ps1`.
- `pcsx2_launch_command`: `@pcsx2_scripts/launch.ps1`.
- `pcsx2_savestates_command`: `@pcsx2_scripts/savestates.ps1`.
- `na228_game_launch_command`: `@scripts/na228/launch_games.ps1`.
- `actualize_command`: `@pcsx2_scripts/actualization/act.ps1`.
- `actualize_na228_command` and `actualize_input_command`: the two standalone
  actualization modes under `@pcsx2_scripts/actualization/`.

The loaders additionally expose catalog-derived compatibility files:

- `<source>_iso` from the canonical source identifier.
- `<build>_iso` as `@build/<builds.title> - <postfix>.iso`.
- `<build>_memory_card` as
  `@pcsx2_memory_cards/<builds.title> - <postfix>.ps2`.
- `input_profile` from the root catalog configuration.
- `cheat_template` and `gamesettings_template` from the configured
  `builds.template_stem`, with only their respective extensions added.

PowerShell accesses these as `$projectPaths.files.na2_iso` and
`$projectPaths.files.latest_iso`. Python accesses them through calls such as
`PROJECT_PATHS.file("nun5_iso")` and `PROJECT_PATHS.file("previous_iso")`.

## Game catalog

`settings/games.json` keeps `sources` as a direct game map. A source's
canonical key is also its ISO, extraction-directory, and memory-card filename
stem. Each source stores only `serial`, `crc`, aliases, and genuine overrides.
`builds` contains the shared build `title`, `serial`, and explicit
`template_stem` plus an `entries` map. Empty optional values are omitted.

Configuration inherits from root `config`, then category-wide build
configuration, then a game's own non-structural fields. The current root
default is the generated `input_profile`. When
`input_profiles/sources/games/<GAME>.ini` exists for a canonical game selector,
the resolver derives the generated complete `<profile>_<GAME>.ini` profile.

`scripts/lib/resolve_game.py <selector>` is the sole derivation entry point for
PowerShell. It resolves one selector case-insensitively and prints one JSON
object containing absolute `iso`, `extracted` when applicable, `cheats`,
`game_settings`, `memory_card`, and resolved `input_profile` paths. Games with
an override also include the absolute `input_profile_overrides` path. The
catalog stores only the default profile name; the resolver derives canonical
game inputs and generated filenames under `@pcsx2_input_profiles`. Python callers import
`resolve_game()` from `scripts.lib.game_catalog`; they do not start another
Python process.

Source ISO, extraction, and memory-card paths derive from the canonical key;
cheats and GameSettings derive from `serial` plus `crc`. Build ISO and
memory-card paths derive from `title` plus the entry `postfix`; build template
paths use the explicit `template_stem` because that name is a project
convention rather than a PCSX2 identity rule.

The PowerShell loader exposes canonical selectors and aliases through
`$projectPaths.games`. Matching is case-insensitive. The build aliases `l`,
`p`, and `t` resolve to `latest`, `previous`, and `test`; `NUN6` resolves to
the canonical `NUN6_A35` source.

## PowerShell

Every PowerShell entry point dot-sources `scripts/lib/project_paths.ps1` and
loads the manifest before doing work. For example, a script one directory below
`scripts/` uses:

```powershell
. (Join-Path $PSScriptRoot '..\lib\project_paths.ps1')
$projectPaths = Get-Na2ProjectPaths
$iso = $projectPaths.files.na2_iso
```

The root `na228.ps1` entry point uses `scripts/lib/project_paths.ps1` as its
bootstrap. The manifest and shared path loaders are stable bootstrap files and
should not be moved during an ordinary directory migration.

## Python

Repository Python code imports the shared loader from
`scripts.lib.project_paths`. Preserved menu-input research tools use their small
local `scripts/research/menu_input/project_paths.py` bootstrap:

```python
from project_paths import PROJECT_PATHS

iso = PROJECT_PATHS.file("na2_iso")
```

## Migration procedure

1. Move the directory or canonical file without changing its contents.
2. Edit its repository-relative value in `project-paths.json` for shared
   infrastructure or `settings/games.json` for a game/build entry.
3. Run the path-loader checks and automated tests.
4. Search documentation for literal legacy paths and express them as `@root/...`.

Do not copy resolved absolute paths into scripts, logs, profiles, or documentation.

Shared media, analysis, tools, and PCSX2 roots resolve through `@workshop`.
No repository-root convenience symlinks are
required. Stable and development PCSX2 resolve shared asset folders directly
through their native `[Folders]` configuration. The stable PCSX2 binding
remains protected and grants agents no additional access.
