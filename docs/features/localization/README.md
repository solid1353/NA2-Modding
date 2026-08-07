# Localization feature documentation

The canonical executable inputs live under
`na228_builder/features/localization/`. This directory owns the substantial
feature documentation while the code-local README remains a concise contract
and index.

Localization composes the accepted English translation, source-derived UI
textures, guarded UI layout edits, the native NUN5-derived Font stack, compact
external strings, and regional menu input behavior. Enabling the feature
enables all of its owned module directories; one aggregate profile pin covers
their canonical inputs.

## Documents

- [Translation importer](translation_importer.md): current mapping schema,
  source/donor contract, output, safety, and integration behavior.
- [Translation history](translation_history.md): mapping-version history,
  runtime issue log, and historical validation checklist.
- [UI textures](ui_textures.md): source-derived fixed-size CCS replacements.
- [UI layout patches](ui_layout.md): guarded executable layout edits paired
  with the localized UI containers.
- [Compact external strings](external_strings.md): linked resident string
  placement and loader integration.
- [Native NUN5-derived Font](font.md): feature-owned Font assets, hooks, and
  runtime contributions.

## String placement boundary

The generic module owns string placement policy. Localization has no
`string_patcher/` feature directory because it owns no local string declarations;
the importer artifact invokes the engine as a derived consumer. It accepts
validated in-memory rows, resolved source text, and references, compiles inline
imports, contributes external strings as named read-only-data fragments, and
declares symbolic pointer writes. The shared `payload_builder` chooses offsets
and constructs `PRG/228.BIN`; the composer resolves symbols; `binary_patcher`
owns byte guards, conflict handling, replacement, and logging. If Localization
later owns local declarations, it can add `string_patcher/strings.tsv` then.

The memory-card title is output identity and is therefore declared by root
`product.json`; its evidence is documented in
`docs/knowledge/game/disc_identity.md`.

## Regional menu input

The Localization feature owns these declarative `binary_patcher` patches for
the accepted menu, overlay, setup, stage, pause, result-tally, and audio input behavior.
`binary_patcher/` contains the guarded targets, enabled patches, edits,
evidence, and runtime classifications.
