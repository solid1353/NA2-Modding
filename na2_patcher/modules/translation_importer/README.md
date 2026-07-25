# Translation importer engine

This reusable engine reads the feature-owned `mappings.tsv`, validates the
clean NA2 targets and the table's folded pointer inventory, and produces a
canonical in-memory translation artifact. `source_ref` and `donor_ref`
identify the paired NA2 and NUN5 locations; `source` and `donor` retain their
decoded text together. Every executable row also declares a concrete
`display_context` and a `display_basis` beginning with `seen:`, `inferred:`,
or `character:`. The engine rejects rows without that evidence metadata and
rejects a declared `source` that differs from the clean target bytes.

The same module input also owns adjacent `rebuild.tsv`. It is a separate,
translation-free candidate inventory for worker-only mapping-ID builds:
permanent `T1`, `T2`, ... identifiers, exact clean source text and location,
capacity/mode, provisional screen context, and optional legacy `M` IDs for
lookup.
Normal importer paths do not import or execute its rows; profile integrity
checking still hash-covers the file. Diagnostic builds import every rebuild row
and validate the exact clean source bytes, but ignore all donor/translation
fields. This keeps the accepted `mappings.tsv` behavior unchanged while the
replacement table is reconstructed from screenshots.

The official `donor` is the default executable translation. User-authored
`prefix` is prepended to the resolved text, while a nonempty user-authored
`replacement` overrides the donor before transforms are applied. The importer
normalizes fullwidth ASCII-compatible characters in resolved output while
preserving exact CP932 source guards.

It does not choose inline versus external placement and does not write game
payloads. Canonical rows store pointer sites as combined `reference_refs` and
generate patch-log reasons from their mapping IDs instead of carrying historical
version labels. The active mapping package and its review history live under
`na2_patcher/features/localization/translation_importer/`.

## Invokes

- `string_patcher` as a derived consumer of the validated translation artifact.
  No feature-owned string-patcher directory is required when there are no local
  string declarations.
