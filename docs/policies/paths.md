# Path configuration

## Ownership

- Workshop `paths.json` owns shared source, tooling, PCSX2, work, log, and
  savestate paths.
- NA2 `paths.json` imports Workshop and defines only NA2-owned roots and files.
- Workshop `games.json` owns source-game names, aliases, serials, and CRCs.
- NA2 `game.json` owns the project identity, build targets, launch settings,
  and launch-profile overrides.

Workshop must not depend on NA2. NA2 may override imported entries only by
defining the same name in its own manifest.

## Manifest contract

- Roots and files use repository-relative paths or `@root/child` references.
- Each manifest is resolved relative to its own directory, never the caller's
  working directory.
- Loaders inject `repository`; manifests do not define it.
- Parent roots precede entries derived from them. Group related roots and files
  together; do not alphabetize aliases away from their parent.
- `existence_deferred_roots` contains only generated roots that may be absent
  while loading the manifest.
- Consumers use manifest names through a maintained loader. Do not repeat a
  backing path in code, tests, commands, or documentation.

Workshop owns shared names such as `source_catalog`, `game_resolver`,
`pcsx2_dev`, and `pcsx2_*_command`. NA2 owns `project_settings`,
`publish_release_command`, and its local build, work, log, and PCSX2 content
roots. The manifests are the complete inventory; this policy does not duplicate
their entries.

## Registered game content

Alias-owned PCSX2 content is stored as one bundle:

```text
pcsx2_files/games/<alias>/
  <alias>.ini
  <alias>.pnach
  <alias>.ps2
```

Each registered bundle must exist in exactly one configured `pcsx2_files` root.
Workshop owns NUN3; NA2 owns NA2, NA228, NUN5, and NUN6. All NA2.28 build
selectors use the NA228 bundle. Shared default and test cards remain in
Workshop `pcsx2_files/memory_cards`; input recordings remain under each owning
repository's `pcsx2_files/input_recordings`.

`resolve_game.py <selector> [--project-root <path>]` resolves selectors
case-insensitively and returns absolute ISO, extracted-source, bundle-file, and
input-profile paths, plus the build postfix. Project resolution searches
Workshop and the invoking repository and rejects missing or duplicate
registered bundles.

## Loader APIs

- PowerShell: `Get-Na2Paths` or `Get-UnWorkshopPaths`.
- Python: `load_paths()`, `load_workshop_paths()`, or `resolve_game.py`.
- Runtime-derived entries include `source_<source>`, `<source>_iso`,
  `<build>_iso`, `<build>_memory_card`, `input_profile`, `cheat_template`, and
  `gamesettings_template`.

## Changes and validation

Move the canonical content first, then update its manifest name and every
consumer in the same change. Delete retired names and logic; do not add
compatibility handling.

For NA2 path changes, run:

```powershell
& { . .\scripts\lib\paths.ps1; Get-Na2Paths | Out-Null }
& .\scripts\lib\run_python.ps1 `
  -PackageSet builder `
  -Module unittest `
  -NoBytecode `
  -ArgumentList @('discover', '-s', 'tests/na228_builder', '-p', 'test_paths.py')
```

For Workshop path changes, run its affected tests or the full
`tests/run.ps1` suite.
