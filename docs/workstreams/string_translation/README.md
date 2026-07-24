# String translation

Canonical documentation landing page for the `String translation` workstream.

## Workstream policy

- Translate only strings confirmed to be displayed through savestate-driven
  inspection. Existing translations and mappings are reference material rather
  than presumed required coverage.
- Character-specific strings may be translated systematically without
  individual runtime encounters because their structure is predictable and
  exhaustive testing is disproportionately time-consuming.
- Keep `[S]` on authorized shortened mappings that do not fit their original
  slots. The marker is intentional visible debt so fit exceptions can be
  reviewed collectively later.
- Do not replace identifiers, placeholders, or other data of uncertain display
  purpose with arbitrary text.
- This workstream owns game text and its mapping/reference data. Font fitting
  belongs to `Font`; graphical UI assets and their placement belong to
  `UI Translation`.

Global source, binary-safety, profile, testing, and cleanup rules remain in
`AGENTS.md` and are not duplicated here.

## Documents

- [Localization feature and mapping history](../../../na2_patcher/features/localization/README.md)
- [External string-payload architecture](../../knowledge/external_string_payload.md)
