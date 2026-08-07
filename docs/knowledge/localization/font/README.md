# Font renderer and asset findings

This directory preserves the confirmed visual, structural, runtime, and
byte-level evidence for the native NUN5-derived Font stack. Raw schema-v1
replicas of retired m01/v22/v23 packages and the rejected palette experiment
remain recoverable from Git commit `55d1163`; they are not implementation
parents or active patch inputs.

## Documents

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
- [Experiments and negative results](experiments.md): superseded baselines and
  rejected renderer/asset approaches.
- [Open hypotheses](hypotheses.md): unresolved Font-specific hypotheses only.
- [2026-07-24 matched savestate analysis](savestate_analysis_2026-07-24.md):
  focused paired-screen evidence used by the later work.
