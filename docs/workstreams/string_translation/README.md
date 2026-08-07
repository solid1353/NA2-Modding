# String translation

Durable context for the `String translation` workstream.

## Durable working rules

- `mappings.tsv` is the single canonical translation table and the only
  translation source consumed by normal builds. Existing legacy mappings and
  donor links are reference material rather than presumed correct coverage.
- Translate only strings confirmed to be displayed through the `T#`
  screenshot pass. The rebuilt executable table admits a row only when it has
  a concrete `display_context` and a `display_basis`: directly seen in an ID
  screenshot, inferred from a proven selector/help-text family, or covered by
  the explicit character-family exception. Rows without a display location
  remain untouched Japanese data after final cutover.
- Character-specific strings may be translated systematically without
  individual runtime encounters because their structure is predictable and
  exhaustive testing is disproportionately time-consuming.
- Hidden selector values and running help text are reconstructed from verified
  NUN5/NA2 table structure and legacy tables used strictly as reference. The
  user is not required to capture every value separately.
- Keep complete official donor text and complete user-authored overrides in
  canonical mappings. A blank `replacement` uses `donor`; `prefix` is
  prepended to the selected text. Inline versus external placement is derived
  at build time from the final encoded length, guarded slot capacity, and
  available pointer references; do not retain shortened fallbacks or placement
  markers unless the user explicitly orders a specific inline fit exception.
- Do not replace identifiers, placeholders, or other data of uncertain display
  purpose with arbitrary text.
- Match the case used by the displayed official NUN5 text. Normalize fullwidth
  Latin letters, digits, punctuation, and spaces to ASCII in resolved English
  output while retaining exact CP932 source text and bytes as guards.
- Treat PCSX2 operator overlays and the underlying game screen as separate
  evidence. Validate NA2 and NUN5 memory-card formatting/data-creation flows by
  meaning rather than assuming their screen sequences correspond one-to-one.
- This workstream owns game text and its mapping/reference data. Font fitting
  belongs to `Font`; graphical UI assets and their placement belong to
  `UI Translation`.

## Documents

- [Localization feature and mapping history](../../features/localization/README.md)
- [External string-payload architecture](../../knowledge/localization/external_string_payload.md)
