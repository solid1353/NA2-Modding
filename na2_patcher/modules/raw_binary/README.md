# Raw binary module

This component applies repository-owned declarative TSV patch sets to verified clean
binaries. GPT-generated mapping archives are evidence inputs, not executable patch
sets.

## Safety model

- All persisted paths are relative.
- Every input target is checked by size and SHA-256.
- Every destination range is checked by exact bytes or a range SHA-256.
- Copy operations also verify the exact source range.
- Patch sets contain organizational groups and independently applicable atomic patches.
- Group and patch selections may overlap and every selection occurrence retains provenance.
- Concrete edits are simulated in deterministic order before output creation. Already-satisfied
  writes and guarded chains are allowed; incompatible staged bytes are rejected as conflicts.
- Raw-binary v2 has no patch dependency or declarative relation mechanism.
- Only `approved_for_test` and `runtime_proven` patches can be applied.
- Pending candidates can be inspected with `plan` but cannot be applied.
- Outputs must be new, stay outside input roots, and preserve target sizes.
- Every applied edit and before/after file hash is logged.
- Do not use fixed-address PNACH writes against on-demand overlays such as
  `BTL.BIN` or `ETC.BIN`; test those edits by patching the file and rebuilding.

## Commands

Run commands from the repository root.

```powershell
python -m na2_patcher.modules.raw_binary.engine validate `
  --package na2_patcher/modules/raw_binary/patch_sets/menu_input `
  --root na2=@source_na2 `
  --root nun5=@source_nun5
```

```powershell
python -m na2_patcher.modules.raw_binary.engine plan `
  --package na2_patcher/modules/raw_binary/patch_sets/menu_input `
  --root na2=@source_na2 `
  --root nun5=@source_nun5 `
  --patch ELF-M008
```

Application requires a new output directory and an approved patch status:

```powershell
python -m na2_patcher.modules.raw_binary.engine apply `
  --package na2_patcher/modules/raw_binary/patch_sets/example `
  --root na2=@source_na2 `
  --root nun5=@source_nun5 `
  --patch example_patch `
  --output-root work/temp/example_patch_output
```

Default standalone logs are written under `logs/na2_patcher/raw_binary/<run-id>/`.
Profile builds store the same patch and hash tables beneath that profile run's
module directory.

## Patch status lifecycle

`pending` -> `approved_for_test` -> `runtime_proven` or `runtime_failed`

`deprecated` keeps historical data without permitting application. A patch may be
enabled by default only after it is `runtime_proven`.

## Schema

Schema v2 is described by the column tables under `schemas/v2/`. Every package has
`manifest.tsv`, `targets.tsv`, `groups.tsv`, `patches.tsv`, and `edits.tsv`.
Headers are strict and must match exactly. Groups organize patches; patches own one
or more exact edits. A completely empty reserved package is valid, but declared
groups without patches and patches without edits are rejected. Schema v1 is not
accepted by the live engine and remains available only through Git history.
