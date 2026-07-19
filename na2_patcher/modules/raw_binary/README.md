# Raw binary module

This component applies repository-owned declarative TSV patch sets to verified clean
binaries. GPT-generated mapping archives are evidence inputs, not executable patch
sets.

## Safety model

- All persisted paths are relative.
- Every input target is checked by size and SHA-256.
- Every destination range is checked by exact bytes or a range SHA-256.
- Copy operations also verify the exact source range.
- Named patches are atomic; selected ranges may not overlap.
- Dependencies and conflicts are enforced through `relations.tsv`.
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

Schema v1 is described by the column tables under `schemas/v1/`. TSV headers are
strict and must match exactly. Complex relationships use normalized rows instead of
lists or JSON inside cells.
