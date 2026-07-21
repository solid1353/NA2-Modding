# Font Workstream

## Objective

Make NA2 English text fit and align as cleanly as the UN5/NUN5 reference. The
accepted integration baseline combines call-local renderer fixes with a native
14x20 NUN5-derived secondary font generated from clean NA2 and official NUN5
sources. Renderer geometry, measurement, positioning, and boxed auto-fit
remain separate from raster-weight refinement so an appearance change cannot
silently invalidate the accepted layout.

Confirmed findings and negative results remain canonical in
`docs/knowledge/font/README.md`. This document defines the active work and its
execution order.

## Current result for review

The implementation preserves clean NA2 GF4C and file sizes while installing a
guarded native 14x20 secondary atlas in GF4. Matched captures show a good
accepted result for Controls, Practice, Save/Load, and the character modal:
overflowing Controls text fits, `Linked Attack` stays full width, and reviewed
rows align closely with NUN5. The remaining visible defect is that halfwidth
Latin glyphs are noticeably bolder than NUN5. The user accepted this iteration
and deferred weight refinement to the next one. Fullwidth Shift-JIS Save/Load
digits are not a Latin-weight parity target. The rejected 28x28 quad experiment
remains disabled as negative evidence.

## Required execution order

1. Completed: establish the clean NA2 GF4/GF4C baseline and isolate vertical
   geometry.
2. Completed for the reviewed screens: fix horizontal and vertical alignment
   with call-local edits.
3. Completed for the reviewed Controls call sites: reproduce NUN5's
   shrink-only fit decision and restore renderer state after every draw.
4. Next iteration: refine the accepted native donor's halfwidth Latin weight
   against matched NUN5 captures without moving rows pixel-by-pixel unless the
   refined metrics genuinely change their measured centers.

Auto-adjust is downstream of horizontal metrics. A scaling test is not valid
until logical width, visible glyph bounds, advances, and centering are measured
for the same strings. The historical m01 and semantic-palette experiments are
negative evidence, not implementation parents.

## Active task

### Make font identical to UN5

The accepted integration baseline uses a new donor generated independently of
the rejected historical candidates:

- Import native 14x20 NUN5 geometry and metric rows only for same-semantic
  English cells.
- Reconstruct unsupported punctuation from clean NA2 and retain complete
  95/95 printable-ASCII coverage.
- Preserve clean NA2 GF4C palette semantics and both target file sizes.
- Bound the shortened 123-cell secondary atlas locally and keep the primary
  font parser unchanged.
- Treat `font_m01`, `font_nun5_appearance`, the 10x22 resample, and the global
  parser experiment as negative or comparison evidence, not implementation
  parents.
- Refine the remaining heavier Latin weight in the next iteration using
  matched captures; do not use fullwidth Shift-JIS digits as a weight target.

Final parity still requires matched NA2/NUN5 captures at the same presentation
scale, with representative short and long strings and no missing, touching,
overlapping, or palette-damaged glyphs. The current result is the accepted
integration baseline, not the final weight match.

## Completed implementation baseline

### Fix alignment issues

Treat alignment as two related but separately measurable problems:

- Horizontal: left bearings, glyph advances, tracking, spaces, logical string
  width, visible ink bounds, box origin, final anchor, and centering.
- Vertical: baseline, top/bottom bearing, line height, and consistent placement
  between glyphs and rows.

For each representative string, record the NUN5 and NA2 logical width,
rendered bounds, anchor, and final position. The Control Settings strings are
especially useful because `Linked Attack`, `Item Select`, `Item Use`, and the
short labels exercise different widths inside the same layout.

Horizontal parity is a prerequisite for auto-adjust. Vertical corrections may
be implemented independently only when evidence shows they do not share the
same metric initialization or renderer state.

The first clean-source test at ELF file offset `0x88064` was runtime-rejected:
it made the untouched 24x24 quad 28x28, stretching both axes without changing
logical measurement. The accepted alignment changes are call-local instead.
Controls preloads the clean 48-unit row origin, then shifts only its left and
right text labels one local X unit for native visible-ink centering without
moving selection markers. The character modal uses independently measured X
values `81.75, 73.375, 72.375, 63.5, 3.5` and retains its accepted local Y
behavior. Reviewed ordinary-row centers are within one pixel of NUN5, and the
long fifth row fits within the modal.

### Research and implement NUN5 auto-adjust behavior

The accepted implementation reproduces NUN5's fit decision as well as its
scaling, without redirecting NA2 to a layout-incompatible NUN5 function:

- Compare NUN5's boxed path
  `FUN_00399df0 -> FUN_00389df0 -> FUN_0018b1b0 -> FUN_0018ca40` with the
  corresponding NA2 call sites and renderer state.
- Reconcile NUN5 measurement through `FUN_0018b7f0` with NA2's legacy
  `FUN_003798e0 -> FUN_001859a0 -> FUN_00184e60` path.
- Preserve NUN5's per-call behavior: the first eight Control Settings labels
  use the 128-pixel box, while the final `OFF` row uses the ordinary renderer.
- Verify both the threshold decision and final visual bounds; do not accept a
  result merely because clipping disappears.

The local helper measures through the accepted native secondary-font metrics,
keeps non-overflowing text at scale `1.0`, and applies the box ratio only to
overflow. `Linked Attack` remains full width, while the official 19-byte
`Ultimate Jutsu Prep` probe fits and centers closely to NUN5. Scale returns to
`1.0` before the next call. `OFF` remains on the ordinary renderer, and
Save/Load and Practice remain outside the Controls fit decision.

## Preserved baseline and evidence

- `na2_patcher/features/localization/binary_patcher/` contains the active
  runtime-proven native secondary font, alignment, and fit components. It
  targets clean `SLPS_258.37` and `DATA/GF4.BIN`, preserves clean GF4C, and
  is covered by the current Localization aggregate feature pin
  `2DDBDFF59F6C1984064138A261612D49EEF0E301E7C05AA3CFC0F29716B15FAD`.
- `docs/knowledge/font/history/font_m01/` is historical evidence, deliberately
  kept outside active patch-set discovery.
  Its semantic NUN5 appearance patch is disabled and `runtime_failed`.
- `docs/knowledge/font/history/font_elf_history/` preserves historical ELF
  experiments outside active patch-set discovery.
- `docs/knowledge/font/README.md` records the v23 and 2026-07-19 auto-fit
  negative results.
- Reuse the preserved NA2 and NUN5 analysis under
  `@analysis/disassembly/NA2/` and `@analysis/disassembly/NUN5/`.

## Negative results that must not be repeated

- Do not directly replace NA2 GF4 with padded or unpadded NUN5 GF4. Previous
  swaps produced broad spacing, patchy glyph rendering, and unstable behavior.
- Do not repeat the v23 single-field tracking change at ELF file offset
  `0x866E0`; it produced no meaningful visual improvement.
- Do not replace GF4C. The rejected NUN5-palette experiment deterministically
  changed untouched NA2 raster colors and damaged outlines, especially digits.
- Do not re-enable the descriptor-height edit at ELF file offset `0x88064`;
  its clean 28x28 result stretched both axes and damaged outlines.
- Do not repeat the threshold-only Controls wrapper. It incorrectly narrowed
  `Linked Attack` because NA2 and NUN5 made different width decisions.
- Do not transplant the complete NUN5 renderer. Continue with small,
  evidence-backed, size-preserving comparisons.

## Validation requirements

- Use clean, hash-verified NA2 and official NUN5 inputs.
- Keep `@source/` untouched and reuse preserved disassembly rather than
  disassembling the same binaries again.
- Log file, offset, original bytes, replacement bytes, and reason for every
  binary edit.
- Test glyph appearance and alignment before auto-adjust, then test all three
  together for regressions.
- Compare matched screenshots and record useful negative results under
  `docs/knowledge/font/`.
- Keep experimental patches separately selectable until runtime-proven.
