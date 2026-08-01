# Path configuration

The path system has four layers with separate owners:

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

`@workshop` is imported from the sibling `UN Workshop/paths.json`. Workshop is
standalone and never references NA2. Its root manifest owns reusable public
infrastructure:

- source media, analysis, tools, and configured emulator roots;
- shared PCSX2 assets;
- reusable PCSX2, savestate, PINE, input-profile, ISO-identity, and Ghidra
  tooling under `@workshop/scripts/`;
- source-game configuration under `@workshop/games.json`;
- source-game savestate filing under ignored `@workshop/work/ss/`; project
  build savestates stay under the invoking project's ignored `work/ss/`.

The public repository ignores original media, extracted data, private analysis
databases, toolchains, emulator binaries, BIOS files, memory cards, savestates,
logs, and task artifacts.

## Important NA2 roots

- `repository`: this repository; always `.`.
- `workshop`, `source`, `analysis`, and `tools`: imported Workshop roots.
- `ss`: NA2-local `@work/ss`; Workshop source savestates use its own
  `@workshop/work/ss` root.
- `build`, `logs`, `builder`, `features`, `scripts`, `work`: NA2 roots.
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
- `pcsx2_launch_command`, `pcsx2_copy_worker_command`,
  `pcsx2_pine_command`, and `pcsx2_iso_identity`: Workshop utilities.
- `ghidra_runtime`: Workshop headless-Ghidra runtime setup.
- `na228_command`, `na228_game_launch_command`, and
  `release_publish_command`: NA2-specific entrypoints.

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
  "title": "NA v2.28",
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
Build paths derive from title, serial, and postfix. The command is independent
of the caller's current working directory.

PowerShell callers use `Get-Na2ProjectPaths`; Python callers use
`load_project_paths()` or `scripts.lib.game_catalog.resolve_game()`. They do not
duplicate derivation logic. NA2 overlays its local roots/files on the imported
Workshop map; Workshop never imports NA2.

## Migration rule

Move the canonical owner first, update `paths.json` or the owning catalog, then
run both path-loader checks and the affected repository tests. Never persist
resolved machine-specific paths in project files.
