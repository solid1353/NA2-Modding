# Texture patcher engine

This engine verifies the checked-in localized CCS assets owned by
`@builder/patches/localization/ui/` and composes the deterministic external
`PRG/228_UI.BIN` texture pack. The pack index and every member are sector-aligned
for the resident CCS-loader redirect. An ordinary build reads no donor image,
does not rewrite `DATA/DATA.CVM`, and uses no texture cache.

The feature-owned `assets.tsv` records each logical path and accepted compressed
and decompressed hashes. The engine verifies every checked-in asset against
those hashes before packing it.

Source-game derivation and preview tooling lives under
`@scripts/research/ui_translation/`; it is not imported by this engine or
packaged release builds.

## Invokes

None. The configuration orchestrator inserts the completed pack into the ISO.
