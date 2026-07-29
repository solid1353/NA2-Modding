# Binary patcher module

This component applies repository-owned declarative TSV patch sets to verified clean
binaries. GPT-generated mapping archives are evidence inputs, not executable patch
sets.

## Invokes

None. `binary_patcher` is the terminal module-level executor for concrete
guarded file edits.

## Safety model

- All persisted paths are relative.
- Every input target is checked by size and SHA-256.
- Every destination range is checked by exact bytes or a range SHA-256.
- Copy operations also verify the exact source range.
- Patch sets contain organizational groups and independently applicable atomic patches.
- Normal profile composition applies a patch when both its group and patch
  `enabled` switches are `1`.
- Focused CLI commands may request explicit patch IDs without changing feature composition.
- Patch ranges may overlap; ordered composition accepts compatible chains and rejects guard conflicts.
- Concrete edits are simulated in deterministic order before output creation. Already-satisfied
  writes and guarded chains are allowed; incompatible staged bytes are rejected as conflicts.
- Binary-patcher v4 has no patch dependency or declarative relation mechanism.
- Only `approved_for_test` and `runtime_proven` patches can be applied.
- Pending candidates can be inspected with `plan` but cannot be applied.
- Outputs must be new, stay outside input roots, and preserve target sizes.
- Every applied edit and before/after file hash is logged.
- Do not use fixed-address PNACH writes against on-demand overlays such as
  `BTL.BIN` or `ETC.BIN`; test those edits by patching the file and rebuilding.

## Commands

Run commands from the repository root.

```powershell
python -m na228_builder.modules.binary_patcher.engine validate `
  --package na228_builder/features/localization/binary_patcher `
  --root na2=@source_na2 `
  --root nun5=@source_nun5
```

```powershell
python -m na228_builder.modules.binary_patcher.engine plan `
  --package na228_builder/features/localization/binary_patcher `
  --root na2=@source_na2 `
  --root nun5=@source_nun5 `
  --patch regional_input_selectable_modal
```

Application requires a new output directory and an approved patch status:

```powershell
python -m na228_builder.modules.binary_patcher.engine apply `
  --package na228_builder/features/localization/binary_patcher `
  --root na2=@source_na2 `
  --root nun5=@source_nun5 `
  --patch regional_input_selectable_modal `
  --output-root work/temp/example_patch_output
```

Default standalone logs are written under `logs/na228_builder/binary_patcher/<run-id>/`.
Profile builds store the same patch and hash tables beneath that profile run's
module directory.

## Patch status lifecycle

`pending` -> `approved_for_test` -> `runtime_proven` or `runtime_failed`

`deprecated` keeps historical data without permitting application. A patch may
have `enabled=1` only while it is `approved_for_test` or `runtime_proven`;
normal profile composition is itself a verified test path for accepted
integrated work. A disabled group masks its members without changing their
individual switches. Explicit `--patch` selection overrides both switches but
does not bypass status, guard, overlap, or conflict validation.

## Schema

Schema v4 is described by the column tables under `schemas/v4/`. Every package has
exactly four canonical control tables: `targets.tsv`, `groups.tsv`, `patches.tsv`,
and `edits.tsv`, plus any blobs referenced by edit rows. Package identity is
derived from its feature/module path; identity manifests and package-version
metadata are not accepted. Headers are strict and must match exactly. Groups
organize patches; patches own one or more exact edits. Patch rows use one
`evidence_id` for analytical or provenance identity; runtime observations belong
in `review_notes` rather than a parallel classification column. A completely empty reserved
package is valid, but declared groups without patches and patches without edits are
rejected. Earlier schemas are available only through Git history.
