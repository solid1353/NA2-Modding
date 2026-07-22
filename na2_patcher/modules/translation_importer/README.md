# Translation importer engine

This reusable engine reads a feature-owned `mappings.tsv`, validates canonical
NA2 and NUN5 sources, and produces deterministic in-memory string imports. It
does not write game payloads. The active mapping package and its review history
live under `na2_patcher/features/localization/translation_importer/`.

## Invokes

- `string_patcher` as a derived consumer of the validated translation artifact.
  No feature-owned string-patcher directory is required when there are no local
  string declarations.
