# NA2 modular patcher

Profiles replace implicit newest-package selection with explicit, reproducible module inputs.

Each profile directory contains:

- `manifest.tsv`: schema version, profile ID, and description.
- `roots.tsv`: repository-relative bindings or `@root/...` aliases resolved from
  `project-paths.json`.
- `modules.tsv`: ordered module instances with exact input hashes and selections.

Schema v1 supports declarative, size-preserving `raw_binary` and `translation`
modules. Package and ZIP-overlay workflows are retired; profiles consume only
repository-owned declarative inputs.

Profiles never select the newest file implicitly. Enabled module inputs are content-hashed before composition. Disabled modules remain visible in the profile as WIP or review candidates but do not block the active build when their contents change.

For raw-binary modules, the profile hash covers only executable package inputs:

- `manifest.tsv`
- `targets.tsv`
- `patches.tsv`
- `relations.tsv`
- `edits.tsv`
- every blob referenced by `blob_path`

Adjacent documentation and authoring tools do not affect the profile pin.
Translation inputs are hashed as exact files.

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

Build the configured current profile with:

```powershell
& scripts/na2/build.ps1
```

`na2_patcher/build_profile.py` writes the candidate ISO as `build/Current.iso.building`, verifies it completely, fsyncs it, and writes the profile log before returning. `scripts/na2/build.ps1` compares the candidate with `Current.iso`; an identical candidate is discarded without touching `Current.iso` or `Previous.iso`, while a changed candidate atomically replaces `Previous.iso` with the outgoing `Current.iso` and becomes the new `Current.iso`. A failed promotion restores the outgoing ISO when safe, and any caught failure removes `.building`.

File-size changes are always rejected. Structural expansion requires a separately designed and approved implementation rather than a build flag.

The ordinary `na2` command dispatches the profile build, then delegates mandatory PNACH actualization and PCSX2 launch to `scripts/na2/launch.ps1`. `na2 -c` launches `Current.iso` without rebuilding, and `na2 -p` launches `Previous.iso` without rebuilding. Translation is invoked only as a pinned profile module and records its review plan inside the profile log.

The profile references `na2_patcher/modules/translation/mappings.tsv` directly and pins its exact hash. Updating that table therefore requires an explicit profile-pin update.
