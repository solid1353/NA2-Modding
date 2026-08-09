# Localization feature documentation

The selectable hierarchy lives in `na228_builder/catalog/localization.modcat`;
its guarded edits and runtime units live in
`na228_builder/catalog/implementation/edits.json` and
`na228_builder/catalog/implementation/injections.json`. Non-inline assets and
the remaining translation/texture TSV inputs live under
`na228_builder/localization/`.

Localization composes the accepted English translation, source-derived UI
textures, guarded UI layout edits, the native NUN5-derived Font stack, compact
external strings, and regional menu input behavior. Enabling the feature
is selected by a structurally matching configuration. The build-resource
fingerprint covers its canonical executable inputs.

## Canonical builder inputs

`na228_builder/catalog/localization.modcat` owns localization's nested selection
and leaf references. `na228_builder/catalog/implementation/edits.json` owns
guarded binary edits;
`na228_builder/catalog/implementation/injections.json` owns runtime hooks,
resident sources and fragments, relocations, and ABI metadata. Files retained under
`na228_builder/localization/` are only non-inline inputs:

- `assets/`: edit-referenced native Font assets;
- `translation_importer/`: canonical text mappings and donor provenance;
- `texture_patcher/`: source-derived English UI containers.

There are no separate binary-patcher or runtime-injector data directories.
Those engines consume the selected definitions, and the translation importer invokes the
shared string-patcher engine as a derived stage.

## Documents

- [Translation importer](translation_importer.md): current mapping schema,
  source/donor contract, output, safety, and integration behavior.
- [UI textures](ui_textures.md): source-derived fixed-size CCS replacements.
- [UI layout patches](ui_layout.md): guarded executable layout edits paired
  with the localized UI containers.
- [Compact external strings](external_strings.md): linked resident string
  placement and loader integration.
- [Native NUN5-derived Font](font.md): feature-owned Font assets, hooks, and
  runtime contributions.

## Intentional exclusion

Shop is intentionally omitted from Mode Select and is not a maintained
localization target. Shop-owned translations, texture imports, layout patches,
tests, and detailed maintenance documentation remain excluded. The QoL
`Remove Shop` patch remains the shipped default, while the disabled
`Restore Shop` cheat remains available for deliberate inspection. Strings
owned by Game Mode Select or Collection remain maintained even when their text
mentions Shop.

## String placement boundary

The generic module owns string placement policy. Localization has no
`string_patcher/` data directory because it owns no local string declarations;
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

The Localization catalog subtree owns guarded edits for accepted menu, overlay,
setup, stage, pause, result-tally, and audio input behavior. Enablement lives in
configuration JSON; evidence and runtime conclusions live in documentation.
