# Localization feature documentation

The selectable hierarchy lives under `features.localization` in
`@builder/catalog.modcat`; its unified definitions live in
`@builder/patches/*.json`. Patch-owned assets and module inputs live under
the matching path in `@builder/patches/localization/`.

Localization composes the accepted English translation, source-derived UI
textures, guarded UI layout edits, the native NUN5-derived Font stack, compact
external strings, and regional menu input behavior. Enabling the feature
is selected by a structurally matching configuration. The build-resource
fingerprint covers its canonical executable inputs.

`localization.ui` atomically selects the source-derived English UI textures and
their matching guarded layout/runtime patches. Neither implementation side is
independently selectable.

## Canonical builder inputs

`features.localization` in `@builder/catalog.modcat` owns
localization's nested selection and leaf references.
`@builder/patches/localization.json` owns guarded binary edits, runtime hooks,
resident sources and fragments, relocations, ABI metadata, string
transformations, and required module declarations. Non-inline inputs follow
their owning patch IDs:

- `patches/localization/font/glyphs/`: edit-referenced native Font assets;
- `patches/localization/strings/`: canonical text mappings and donor provenance;
- `patches/localization/ui/`: source-derived English UI containers.

There are no separate binary-patcher or runtime-injector data directories.
Those engines consume the selected definitions, and the translation importer invokes the
shared string-patcher engine as a derived stage.

## Documents

- [Translation importer](translation_importer.md): current mapping schema,
  source/donor contract, output, safety, and integration behavior.
- [English UI integration](ui_layout.md): the combined `localization.ui`
  selection and its guarded layout/runtime behavior; [texture derivation](ui_textures.md)
  documents its source-derived fixed-size CCS replacements.
- [Compact external strings](external_strings.md): linked resident string
  placement and loader integration.
- [Native NUN5-derived Font](font.md): feature-owned Font assets, hooks, and
  runtime contributions.

## String placement boundary

The derived string-patcher stage owns string placement policy. The importer
invokes it directly with validated in-memory rows, resolved source text, and
references, compiles inline
imports, contributes external strings as named read-only-data fragments, and
declares symbolic pointer writes. The shared `payload_builder` chooses offsets
and constructs `PRG/228.BIN`; the composer resolves symbols; `binary_patcher`
owns byte guards, conflict handling, replacement, and logging. There is no
physical `string_patcher/` module or `strings.tsv` interface.

The selectable memory-card title is owned by
`memory_card.replace_memory_card_title`; its evidence is documented in
`docs/knowledge/game/disc_identity.md`.

## Regional menu input

The Localization catalog subtree owns guarded edits for accepted menu, overlay,
setup, stage, pause, result-tally, and audio input behavior. Enablement lives in
configuration JSON; evidence and runtime conclusions live in documentation.
