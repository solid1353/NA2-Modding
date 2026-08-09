# Path configuration

The maintained modding project may span NA2, Workshop, maintained
subrepositories such as the PCSX2 fork, and future repositories added to the
project. The path system has four layers with separate technical owners:

1. Workshop root `paths.json` owns every shared root and named file.
2. NA2 root `paths.json` imports Workshop and adds only NA2-local paths.
3. Workshop root `games.json` owns shared source-game selectors, aliases,
   serials, and CRCs.
4. NA2 root `product.json` owns NA2.28 source inputs, output identity, and build
   variants.

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
  tooling under `@workshop/scripts/`;
- source-game configuration under `@workshop/games.json`;
- source-game savestate filing under ignored `@workshop/work/sstates/`;
  project build savestates stay under the invoking project's ignored
  `work/sstates/`.

The public repository ignores original media, extracted data, private analysis
databases, toolchains, emulator binaries, BIOS files, memory cards, savestates,
logs, and task artifacts.

## Source games

The configured original project files are `na2_iso`, `nun3_iso`, `nun5_iso`,
and `nun6_iso`. NUN6 A35 is a Brazilian NUN5 mod retained as a possible
feature donor, not an official successor or English authority.

## Important NA2 roots

- `repository`: this repository; always `.`.
- `workshop`, `source`, `analysis`, and `tools`: imported Workshop roots.
- `build`, `logs`, `task_logs`, `builder`, `features`, `scripts`, `work`: NA2
  roots. `task_logs` resolves to deferred generated records under
  `@logs/tasks/`.
- `pcsx2_scripts`: `@workshop/scripts/pcsx2`.
- `pcsx2_stable`, `pcsx2_dev`, `pcsx2_clean`: protected configured runtimes
  and the external clean worker template.
- `pcsx2_files` and its BIOS, cheats, GameSettings, input-profile,
  input-recording, and memory-card children: shared PCSX2 assets.
- `source_<game>`: derived extraction roots from the Workshop source catalog.

## Important NA2 files

- `game_catalog`: Workshop root `games.json`.
- `product_config`: root `product.json`.
- `game_resolver`: Workshop `scripts/lib/resolve_game.py`.
- `notification_state` and `git_authors`: shared Workshop settings.
- `workshop_command`: Workshop `workshop.ps1`.
- `pcsx2_launch_command`, `pcsx2_game_launch_command`, `pcsx2_copy_worker_command`,
  `pcsx2_pine_command`, and `pcsx2_iso_identity`: Workshop utilities.
- `ghidra_runtime`: Workshop headless-Ghidra runtime setup.
- `na228_command` and `release_publish_command`: NA2-specific entrypoints.

Catalog-derived compatibility files remain available to callers:

- `<source>_iso` and `source_<source>`;
- `<build>_iso` and `<build>_memory_card`;
- `input_profile`, `cheat_template`, and `gamesettings_template`.

## Catalog schemas

Workshop source games use a direct map:

```json
{
  "schema_version": 1,
  "sources": {
    "NUN5": { "serial": "SLES-55605", "crc": "C071D4C1" }
  }
}
```

The NA2 product configuration is deliberately flat apart from its explicit
inputs, identity, and builds sections:

```json
{
  "schema_version": 1,
  "title": "Narutimate Accel v2.28",
  "serial": "SLOP-NA228",
  "inputs": { "na2": "@source_na2", "nun5": "@source_nun5" },
  "identity": { "image": {}, "memory_card": {}, "game_title": {} },
  "builds": {
    "latest": { "aliases": ["l"], "postfix": "Latest" }
  }
}
```

Workshop `resolve_game.py <selector> [--project-root <path>]` resolves one
selector case-insensitively and emits one JSON object containing fully resolved
absolute paths. Source paths derive from the canonical key plus serial/CRC.
Build ISO paths derive from title and postfix; PCSX2 files derive from serial,
and build memory-card paths retain the GameSettings card base plus the build
postfix. The command is independent of the caller's current working directory.

PowerShell callers use `Get-Na2Paths`; Python callers use
`load_paths()` or Workshop's `resolve_game.py`. They do not
duplicate derivation logic. NA2 overlays its local roots/files on the imported
Workshop map; Workshop never imports NA2.

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
  -ArgumentList @('discover', '-s', 'tests/builder', '-p', 'test_paths.py')
```

Never persist resolved machine-specific paths in project files.
