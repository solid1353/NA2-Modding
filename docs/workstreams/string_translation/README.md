# String translation

Canonical documentation landing page for the `String translation` workstream.

## Workstream policy

- Translate only strings confirmed to be displayed through savestate-driven
  inspection. Existing translations and mappings are reference material rather
  than presumed required coverage.
- The rebuilt executable table admits a row only when it has a concrete
  `display_context` and a `display_basis`: directly seen in an ID screenshot,
  inferred from a proven selector/help-text family, or covered by the explicit
  character-family exception. Rows without a display location remain untouched
  Japanese data.
- Character-specific strings may be translated systematically without
  individual runtime encounters because their structure is predictable and
  exhaustive testing is disproportionately time-consuming.
- Hidden selector values and running help text are reconstructed from verified
  NUN5/NA2 table structure and the pre-rebuild v40 table retained in Git
  history. The user is not required to capture every value separately.
- Keep complete official donor text and complete user-authored overrides in
  canonical mappings. A blank `replacement` uses `donor`; `prefix` is
  prepended to the selected text. Inline versus external placement is derived
  at build time from the final encoded length, guarded slot capacity, and
  available pointer references; do not retain shortened fallbacks or placement
  markers.
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

Global source, binary-safety, profile, testing, and cleanup rules remain in
`AGENTS.md` and are not duplicated here.

## Documents

- [From-scratch translation rebuild and validation plan](rebuild.md)
- [Localization feature and mapping history](../../../na2_patcher/features/localization/README.md)
- [External string-payload architecture](../../knowledge/localization/external_string_payload.md)
