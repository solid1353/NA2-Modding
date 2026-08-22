# Font renderer and asset findings

This directory preserves the confirmed visual, structural, runtime, and
byte-level evidence for the native NUN5-derived Font stack. Removed Font
architectures are summarized in the repository-wide
[`retired approaches`](../../retired_approaches.md) record.

## Documents

- [Font assets](assets.md): glyph cells, descriptors, palettes, rejected donor
  combinations, and unresolved asset refinements.
- [Integration baseline](integration_baseline.md): accepted native 14x20
  integration, staged autofit reset, and contextual selector behavior.
- [Numeric rendering](numeric_rendering.md): Save/Load, Battle Settings, Ninja
  Song, and related numeric formatting.
- [Renderer metrics](renderer_metrics.md): geometry, tracking, spacing, and
  bearings.
- [Screen layouts](screen_layouts/README.md): caller-specific menu, modal,
  list, and selected-state layout findings split by screen family.
- [Runtime migration](runtime_migration.md): resident relocation, C migration,
  payload composition, and deterministic runtime boundaries.
