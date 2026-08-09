# Font renderer and asset findings

This directory preserves the confirmed visual, structural, runtime, and
byte-level evidence for the native NUN5-derived Font stack. Raw schema-v1
replicas of retired m01/v22/v23 packages and the rejected palette experiment
remain recoverable from Git commit `55d1163`; they are not implementation
parents or active patch inputs.

## Documents

- [Font assets](assets.md): glyph cells, descriptors, palettes, rejected donor
  combinations, and unresolved asset refinements.
- [Integration baseline](integration_baseline.md): accepted native 14x20
  integration, staged autofit reset, and contextual selector behavior.
- [Numeric rendering](numeric_rendering.md): Save/Load, Battle Settings, Ninja
  Song, and related numeric formatting.
- [Renderer metrics](renderer_metrics.md): geometry, tracking, spacing,
  bearings, and the retired v1 metric port.
- [Screen layouts](screen_layouts.md): caller-specific menu, modal, list, and
  selected-state layout findings.
- [Runtime migration](runtime_migration.md): resident relocation, C migration,
  payload composition, and deterministic runtime boundaries.
