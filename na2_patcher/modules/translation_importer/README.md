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

Adjacent `replacement.tsv` uses the exact accepted `mappings.tsv` schema. It
contains screenshot-confirmed rows plus the explicit character-family
exception. Its cumulative first two passes contribute 752 rows, and the
verified 74-table Command Chart family contributes another 1,041. A subsequent
missing-row audit adds 260 policy-supported rows—53 directly seen, 10
structurally inferred, and 197 character-family rows—for 2,053 enabled rows. Of
those, 2,040 retain the unique accepted row at the same exact `source_ref` as
their donor/transform starting point, with T2042, T2045, and T2050 parents
rewritten into the replacement `T#` namespace. Paired screenshots
independently correct T1956 to `Off`, T1957 to `On`, and T2158 to `Warning`.
Six Difficulty-family rows are matched by meaning against the exact NUN5
strings rather than by table position. Exactly four rows—T24, T30, T744, and
T767—have no trustworthy NUN5 donor and therefore store an ID-prefixed literal
translation in `replacement`; T30 uses the explicit `T30 Ult` inline-fit
exception. Donor-backed rows otherwise leave `replacement` blank and execute
the official donor text; T2027 and T2033 are the only donor-backed exceptions
and retain the established Cross-confirm Shop overrides. Only explicit
replacement worker builds import these rows; normal and diagnostic builds do
not. Profile integrity checking hash-covers the table so the in-progress
replacement cannot drift outside the reproducible project state.

Replacement imports also validate complete structured message families.
Active `split_br` and `join_br_parts` rows sharing a donor reference must use
one consistent full template and cover every `<br>` part exactly once. Missing,
duplicate, or out-of-range parts fail before materialization; accepted normal
imports are unaffected.

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
