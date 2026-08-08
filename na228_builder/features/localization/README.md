# Localization feature

The `localization` subtree in [`../../catalog.json`](../../catalog.json) owns its nested selection, guarded binary edits, runtime hooks, resident sources/fragments, relocations, and ABI metadata.
Its `translated_text` and `translated_textures` leaves select the retained TSV-backed importer inputs without exposing those internal engines to configurations.

Files retained here are only non-inline owned inputs:

- `assets/`: catalog-referenced native font assets;
- `translation_importer/`: canonical text mappings and donor provenance;
- `texture_patcher/`: source-derived English UI containers.

There are no binary-patcher or runtime-injector data directories. Those engines are internal consumers of catalog data. The translation importer still invokes the shared string-patcher engine as a derived stage.

Substantial documentation is under [`docs/features/localization/`](../../../docs/features/localization/README.md), including translation, UI texture/layout, compact external strings, font integration, and regional input behavior.
