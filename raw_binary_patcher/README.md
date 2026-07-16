# Raw binary patcher

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

## Commands

Run commands from the repository root.

```powershell
python raw_binary_patcher/patch_binary.py validate `
  --package raw_binary_patcher/patch_sets/menu_input_20260716 `
  --root na2=source/NA2 `
  --root un5=source/UN5
```

```powershell
python raw_binary_patcher/patch_binary.py plan `
  --package raw_binary_patcher/patch_sets/menu_input_20260716 `
  --root na2=source/NA2 `
  --root un5=source/UN5 `
  --patch ELF-M008
```

Application requires a new output directory and an approved patch status:

```powershell
python raw_binary_patcher/patch_binary.py apply `
  --package raw_binary_patcher/patch_sets/example `
  --root na2=source/NA2 `
  --root un5=source/UN5 `
  --patch example_patch `
  --output-root work/temp/example_patch_output
```

Default logs are written under `logs/raw_binary_patcher/<run-id>/`.

## Patch status lifecycle

`pending` -> `approved_for_test` -> `runtime_proven` or `runtime_failed`

`deprecated` keeps historical data without permitting application. A patch may be
enabled by default only after it is `runtime_proven`.

## Schema

Schema v1 is described by the column tables under `schemas/v1/`. TSV headers are
strict and must match exactly. Complex relationships use normalized rows instead of
lists or JSON inside cells.
