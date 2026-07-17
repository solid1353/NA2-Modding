# NA2 modular patcher

Profiles replace implicit newest-package selection with explicit, reproducible module inputs.

Each profile directory contains:

- `manifest.tsv`: schema version, profile ID, and description.
- `roots.tsv`: repository-relative bindings or `@root/...` aliases resolved from
  `project-paths.json`.
- `modules.tsv`: ordered module instances with exact input hashes and selections.

Schema v1 supports `zip_overlay`, `raw_binary`, and `translation`. `zip_overlay` remains a legacy compatibility type, but the current profile uses only declarative, size-preserving raw-binary and translation modules.

Profiles never select the newest file implicitly. Enabled module inputs are content-hashed before composition. Disabled modules remain visible in the profile as WIP or review candidates but do not block the active build when their contents change.

For raw-binary modules, the profile hash covers only executable package inputs:

- `manifest.tsv`
- `targets.tsv`
- `patches.tsv`
- `relations.tsv`
- `edits.tsv`
- every blob referenced by `blob_path`

Adjacent documentation and authoring tools do not affect the profile pin. Translation and ZIP inputs are hashed as exact files.

The current profile composes:

1. exact font m01 `GF4.BIN` and ELF reconstruction through `raw_binary`;
2. the runtime-proven menu-input handler set through `raw_binary`;
3. separate `QoL` and `Battle logic` raw-binary sections using their preserved default states;
4. hash-pinned v33 mappings from the integrated `translation` module.

The disabled `Testing` section remains a separate raw package. The empty
`Rendering` patch set remains listed as a disabled module until populated.

Migrated PNACH structure uses the existing format directly: one patch set per
section, one patch row per cheat, and one or more edit rows per subcheat. The
patch's `default_enabled` value preserves whether that cheat was enabled.

Build it with:

```powershell
. scripts/project_paths.ps1
$paths = Get-Na2ProjectPaths
$profile = [IO.Path]::GetRelativePath($paths.repository, (Join-Path $paths.patcher 'profiles\current'))
$profileLog = [IO.Path]::GetRelativePath($paths.repository, (Join-Path $paths.logs 'na2_patcher\current_<unique_run_id>'))
& scripts/apply_latest_na2.ps1 -BuildOnly `
  -InputIso (Join-Path $paths.source 'NA2.iso') `
  -OutputIso (Join-Path $paths.build 'Current.iso') `
  -Profile $profile `
  -ProfileLogDirectory $profileLog
```

The compositor writes the candidate ISO as `build/Current.iso.building`, verifies it completely, fsyncs it, and writes the build logs before promotion. The PowerShell orchestration wrapper then closes portable PCSX2, atomically replaces `build/Previous.iso` with the outgoing `build/Current.iso`, and atomically promotes the verified candidate to `build/Current.iso`. A failed promotion restores the outgoing ISO to `Current.iso` when safe, and any caught failure removes `.building`.

File-size changes are rejected by default. Legacy relocation behavior is available only through the explicit `-AllowSizeChanges` / `--allow-size-changes` option.

The ordinary `na2` shortcut supplies the profile values automatically. Its first stage builds without PNACH actualization; its second stage actualizes once for the completed ISO and launches PCSX2. Standalone translation TSV export remains available through `na2 tr` for review and external compatibility; it is not an intermediate of profile builds.

The profile references `na2_patcher/modules/translation/mappings.tsv` directly and pins its exact hash. Updating that table therefore requires an explicit profile-pin update.
