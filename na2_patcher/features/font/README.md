# Native NUN5-derived Font patch set

This package starts from hash-verified clean NA2 and official NUN5 inputs. It
does not use `font_m01`, v22/v23, the rejected GF4C palette swap, or a whole
GF4 replacement as an implementation parent. The accepted build changes
`DATA/GF4.BIN` and `SLPS_258.37` without changing either file's size;
`DATA/GF4C.BIN` remains byte-identical to clean NA2.

Three components are enabled by default and applied together when the Font
feature is enabled:

- `font_nun5_glyphs` installs native 14x20 NUN5 raster geometry and metrics
  for same-semantic English cells. Unsupported printable punctuation is
  reconstructed from clean NA2, preserving 95/95 printable-ASCII coverage.
  The shortened 123-cell secondary atlas is locally guarded. Its metric rows
  are packed into the value words of empty primary-map slots and decoded only
  by the secondary draw and measurement hooks.
- `font_controls_auto_fit` reproduces NUN5's shrink-only Controls behavior.
  It keeps `Linked Attack` full width, fits the official
  `Ultimate Jutsu Prep` label, leaves `OFF` on the ordinary renderer, and
  shifts only the left and right labels for visible-ink centering. Its local
  scale is restored immediately after every fitted call.
- `font_modal_alignment` loads independently measured X positions for the
  five character-select `Back to Game Mode Screen` rows while retaining the
  accepted local Y behavior. Its selected-path compensation prevents the
  shadow draw from shifting visible ink.

Both layout components require `font_nun5_glyphs` because their positions and
fit decisions are tuned to its metrics. They otherwise remain independent.
The disabled `font_vertical_quad_height` component remains exact negative
evidence and conflicts with the native glyph component.

Matched Controls, Practice, Save/Load, and character-modal captures were
runtime-reviewed. The user accepted this iteration's alignment and overflow
result. The remaining known defect is that halfwidth Latin glyphs are visibly
bolder than NUN5; weight refinement is deliberately deferred to the next
iteration. Fullwidth Shift-JIS Save/Load digits use a different glyph path and
are not a Latin-weight parity target.

`generate_nun5_donor.py` deterministically regenerates and verifies the four
referenced blobs from configured `@source_na2/` and `@source_nun5/` inputs.
Exact offsets, guards, replacement bytes, and reasons are recorded in
`edits.tsv`; confirmed evidence and negative results are recorded in
`docs/knowledge/font/README.md`.
