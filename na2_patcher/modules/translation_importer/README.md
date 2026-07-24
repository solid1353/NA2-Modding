# Translation importer engine

This reusable engine reads one feature-owned `mappings.tsv`, validates the clean
NA2 targets and the table's folded pointer inventory, and produces a canonical
in-memory translation artifact. `source`, `donor_ref`, and `donor` are
informational provenance; `replacement` is the executable text. The importer
does not choose inline versus external placement and does not write game
payloads. The active mapping package and its review history live under
`na2_patcher/features/localization/translation_importer/`.

## Invokes

- `string_patcher` as a derived consumer of the validated translation artifact.
  No feature-owned string-patcher directory is required when there are no local
  string declarations.
