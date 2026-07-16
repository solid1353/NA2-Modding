# NA2 modular patcher

Profiles replace implicit newest-package selection with explicit, reproducible module inputs.

Each profile directory contains:

- `manifest.tsv`: schema version, profile ID, and description.
- `roots.tsv`: repository-relative logical source bindings.
- `modules.tsv`: ordered module instances with exact input hashes and selections.

Schema v1 supports `zip_overlay`, `raw_binary`, and `translation`. `zip_overlay` remains a legacy compatibility type, but the current profile uses only declarative, size-preserving raw-binary and translation modules.

Profiles never select the newest file implicitly. Module inputs are content-hashed, and imported ZIP history is retired after exact profile parity is proven.

The current profile composes:

1. exact font m01 `GF4.BIN` and ELF reconstruction through `raw_binary`;
2. runtime-proven `ELF-M008` through `raw_binary`;
3. immutable translation milestone m03/v33 through the integrated `translation` module.

Build it with:

```powershell
& scripts/apply_latest_na2.ps1 -BuildOnly `
  -InputIso source/NA2.iso `
  -OutputIso build/Current.iso `
  -Profile na2_patcher/profiles/current `
  -ProfileLogDirectory logs/na2_patcher/current_<unique_run_id>
```

The ordinary `na2` shortcut supplies these values automatically, actualizes the PNACH, and launches PCSX2. Standalone translation TSV export remains available through `na2 tr` for review and external compatibility; it is not an intermediate of profile builds.

Translation milestone data is copied into `na2_patcher/milestones/` and hash-pinned by the profile. This allows the live translation workspace to advance without mutating an older reproducible profile.
