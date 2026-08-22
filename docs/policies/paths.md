# Path configuration

The path system has four layers with separate technical owners:

1. Workshop root `paths.json` owns every shared root and named file.
2. NA2 root `paths.json` imports Workshop and adds only NA2-local paths.
3. Workshop root `games.json` owns shared source-game selectors, aliases,
   serials, and CRCs.
4. NA2 root `game.json` owns NA2.28 output identity, build targets, each
   buildable target's configuration, rotation relationships, base launch
   settings, and direct named launch-profile overrides.

The PowerShell and Python loaders merge both catalogs. Canonical files store
only repository-relative paths or `@root/child` references. Resolved absolute
paths exist only at runtime.

## Workshop boundary

`@workshop` is imported from the sibling `UN Workshop/paths.json`. Workshop
is shared across consuming modding projects and does not depend on NA2. Its
root manifest owns reusable public infrastructure:

- source media, analysis, tools, and configured emulator roots;
- shared PCSX2 assets;
- reusable PCSX2, savestate, PINE, input-profile, ISO-identity, and Ghidra
  tooling under `@scripts/`;
- source-game configuration in the configured `game_catalog` file;
- source-game savestate filing under ignored `@savestates/`;
  project build savestates stay under the invoking project's ignored
  `@work/sstates/`.

The public repository ignores original media, extracted data, private analysis
databases, toolchains, emulator binaries, BIOS files, memory cards, savestates,
logs, and task artifacts.

## Source games

The configured original project files are `na2_iso`, `nun3_iso`, `nun5_iso`,
and `nun6_iso`. NUN6 is a Brazilian NUN5 mod retained as a possible
feature donor, not an official successor or English authority.

## Important NA2 roots

- `repository`: this repository; always `.`.
- `workshop`, `source`, `disassembly`, and `tools`: imported Workshop roots.
- `build`, `logs`, `task_logs`, `builder`, `resources`, `scripts`, `work`, and
  `release`: NA2 roots. `task_logs` owns deferred generated records. `work`
  contains only chat-owned workspaces; `release` owns the ignored publication
  directory.
  `resources` owns repository-wide metadata shared by the builder and launcher.
- `pcsx2_scripts`: imported shared PCSX2 scripts.
- `pcsx2_dev` and `pcsx2_fork`: the protected configured development runtime
  and the external clean worker template.
- `pcsx2_files` and `pcsx2_input_recordings`: NA2-owned game bundles under
  `@pcsx2_files/games/` and recordings. Root `launch_profiles/` owns
  launch-profile behavior and assets. Workshop retains shared BIOS and input
  profiles, NUN3's flat PNACH, GameSettings, and memory card, and default and
  test cards.
- `source_<game>`: derived extraction roots from the Workshop source catalog.

## Important NA2 files

- `game_catalog`: Workshop root `games.json`.
- `settings`: root `game.json`.
- `game_resolver`: configured Workshop game resolver.
- `workshop_command`: Workshop `workshop.ps1`.
- `pcsx2_launch_command`, `pcsx2_game_launch_command`, `pcsx2_copy_worker_command`,
  `pcsx2_pine_command`, and `pcsx2_iso_identity`: Workshop utilities.
- `ghidra_runtime`: Workshop headless-Ghidra runtime setup.
- `na228_command` and `release_publish_command`: NA2-specific entrypoints.

Catalog-derived compatibility files remain available to callers:

- `<source>_iso` and `source_<source>`;
- `<build>_iso` and `<build>_memory_card`;
- `input_profile`, `cheat_template`, and `gamesettings_template`.

## Resolution

Workshop `resolve_game.py <selector> [--project-root <path>]` resolves one
selector case-insensitively and emits one JSON object containing fully resolved
absolute paths, plus the derived postfix for project builds. Source paths derive
from the canonical key plus serial/CRC.
Build postfixes derive from canonical keys by replacing underscores with spaces
and title-casing the result (`e2e_test` becomes `E2E Test`). Build ISO paths
derive from title and that postfix. NA2-family PCSX2 files resolve from their
canonical bundle under `@pcsx2_files/games/`, and all NA2.28 builds use the
`NA228` bundle.
The command is independent of the caller's current working directory.

PowerShell callers use `Get-Na2Paths`; Python callers use
`load_paths()` or Workshop's `resolve_game.py`.
Once `paths.json` names a root, code, tests, logs, and documentation use it
through `@root/...` or the loader API; only manifest definitions and the minimal
loader bootstrap may spell backing paths. NA2 overlays its local roots/files on
the imported Workshop map; Workshop never imports NA2.

## Migration rule

Move the canonical owner first and update `paths.json` or the owning builder
definition file.
For an NA2 path/catalog change, validate the PowerShell loader and its existing
Python unit tests with:

```powershell
& { . .\scripts\lib\paths.ps1; Get-Na2Paths | Out-Null }
& .\scripts\lib\run_python.ps1 `
  -PackageSet builder `
  -Module unittest `
  -NoBytecode `
  -ArgumentList @('discover', '-s', 'tests/na228_builder', '-p', 'test_paths.py')
```
