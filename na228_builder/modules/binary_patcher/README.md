# Binary patcher module

This internal engine applies selected guarded edits to verified clean binaries.
`na228_builder/catalog/implementation/edits.json` owns production edit
definitions; feature files under `na228_builder/catalog/` assign their IDs to
selectable leaves. The TSV
files in `operations/` define each operation's allowed fields and basic types.

## Invokes

None. `binary_patcher` is the terminal module-level executor for concrete
guarded file edits.

## Safety model

- All persisted paths are relative.
- Every input target is checked by size and SHA-256.
- Every destination range is checked by exact bytes or a range SHA-256.
- Copy sources are covered by the complete source target's size and SHA-256.
- Configuration selection determines which catalog nodes apply; the engine's
  synthetic groups and patches are internal execution objects only.
- Patch ranges may overlap; ordered composition accepts compatible chains and rejects guard conflicts.
- Concrete edits are simulated in deterministic order before output creation. Already-satisfied
  writes and guarded chains are allowed; incompatible staged bytes are rejected as conflicts.
- Migrated nodes marked `proven: false` remain executable while they await
  individual proof; the marker is catalog metadata, not an engine status.
- Outputs must be new, stay outside input roots, and preserve target sizes.
- Every applied edit and before/after file hash is logged.
- Do not use fixed-address PNACH writes against on-demand overlays such as
  `BTL.BIN` or `ETC.BIN`; test those edits by patching the file and rebuilding.

## Production use

The catalog loader validates an edit against its operation manifest, resolves
the shared target registry, and constructs the engine's in-memory package.
Normal builds do not load separate binary-patcher TSV data packages. Build logs
retain the selected edit inventory and before/after hashes beneath the
configuration build record.
