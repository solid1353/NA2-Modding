# Translation importer engine

This reusable engine reads one feature-owned `mappings.tsv`, validates the clean
NA2 targets and the table's folded pointer inventory, and produces a canonical
in-memory translation artifact. `source_ref` and `donor_ref` identify the paired
NA2 and NUN5 locations; `source` and `donor` retain their decoded text together.
The official `donor` is the default executable translation. User-authored
`prefix` is prepended to the resolved text, while a nonempty user-authored
`replacement` overrides the donor before transforms are applied. The importer
does not choose inline versus external placement and does not write game
payloads. Canonical rows store pointer sites as combined `reference_refs` and
generate patch-log reasons from their mapping IDs instead of carrying historical
version labels. The active mapping package and its review history live under
`na2_patcher/features/localization/translation_importer/`.

## Invokes

- `string_patcher` as a derived consumer of the validated translation artifact.
  No feature-owned string-patcher directory is required when there are no local
  string declarations.
