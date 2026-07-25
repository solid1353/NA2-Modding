# Font Workstream Plan

## Objective

Make NA2 English text fit and align as cleanly as the UN5/NUN5 reference. The
accepted integration baseline combines call-local renderer fixes with a native
14x20 NUN5-derived secondary font generated from clean NA2 and official NUN5
sources. Renderer geometry, measurement, positioning, and boxed auto-fit
remain separate from raster-weight refinement so an appearance change cannot
silently invalidate the accepted layout.

Confirmed findings and negative results remain canonical in
`docs/knowledge/localization/font/README.md`. This document defines the active work and its
execution order.

## Current result for review

The implementation preserves clean NA2 GF4C and file sizes while installing a
guarded native 14x20 secondary atlas in GF4. Matched captures show a good
accepted result for Controls, Practice, Save/Load, and the character modal.
The final secondary-only height helper restores the intended 24x28 quad while
leaving width, spacing, fit, and row positions unchanged. `Ultimate Jutsu
Prep` fits, `Linked Attack` stays full width, and the matched Controls sample
has median height and center-Y deltas of zero against NUN5. The user accepted
the font itself as almost pixel-for-pixel. Fullwidth Shift-JIS Save/Load digits
are not a halfwidth-Latin parity target. The rejected shared 28x28 experiment
remains disabled as negative evidence. Executable Font helpers now live in the
shared resident `PRG/228.BIN`; a fresh worker build survives the Load transition
that erased the former boot-ELF padding helpers.

## Required execution order

1. Completed: establish the clean NA2 GF4/GF4C baseline and isolate vertical
   geometry.
2. Completed for the reviewed screens: fix horizontal and vertical alignment
   with call-local edits.
3. Completed for the reviewed Controls call sites: reproduce NUN5's
   shrink-only fit decision and restore renderer state after every draw.
4. Completed: promote the proven secondary-only descriptor-height path into
   the canonical glyph component and obtain final matched visual acceptance.
5. In progress: the shared NUN5 renderer metric, Controls denominator,
   Practice pause-list box, confirmation-choice positions, confirmation-body
   placement, and character-return box are implemented. Continue through the
   remaining caller families identified by the ten-pair savestate analysis.

Auto-adjust is downstream of horizontal metrics. A scaling test is not valid
until logical width, visible glyph bounds, advances, and centering are measured
for the same strings. The historical m01 and semantic-palette experiments are
negative evidence, not implementation parents.

## Accepted font implementation

### Make font identical to UN5 — accepted

The accepted integration baseline uses a new donor generated independently of
the rejected historical candidates:

- Import native 14x20 NUN5 geometry and metric rows only for same-semantic
  English cells.
- Reconstruct unsupported punctuation from clean NA2 and retain complete
  95/95 printable-ASCII coverage.
- Preserve clean NA2 GF4C palette semantics and both target file sizes.
- Bound the shortened 123-cell secondary atlas locally and keep the primary
  font parser unchanged.
- Use descriptor height only for the secondary glyph quad while preserving the
  primary/fullwidth 24-pixel path and all accepted horizontal behavior.
- Treat `font_m01`, `font_nun5_appearance`, the 10x22 resample, and the global
  parser experiment as negative or comparison evidence, not implementation
  parents.

The final guarded capture uses matched native-scale NA2/NUN5 Controls screens
with representative short and long strings. It preserves complete printable
ASCII coverage, contains no missing, touching, overlapping, or palette-damaged
glyphs, and reproduces the accepted width, spacing, bearing, fit, and vertical
presentation together. The user accepted the font itself as almost
pixel-for-pixel.

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
long fifth row fits within the modal. Independently, the glyph-owned helper at
ELF file offset `0x2F8840`, reached from the guarded hook at `0x88078`, uses
descriptor height only when the existing secondary-font mode bit is set. This
restores the intended 24x28 secondary quad without changing X geometry or the
primary/fullwidth path.

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

The shared renderer helper measures through the accepted native
secondary-font metrics and corrects ordinary ASCII spaces once for every boxed
caller. The Controls wrapper keeps non-overflowing text at scale `1.0` and
applies its 128-unit box ratio only to overflow. `Linked Attack` remains full
width, while the official 19-byte `Ultimate Jutsu Prep` probe matches NUN5's
157-pixel visible width and X center. Scale returns to `1.0` before the next
call. `OFF` remains on the ordinary renderer.

## Preserved baseline and evidence

- `na2_patcher/features/localization/binary_patcher/` contains the active
  runtime-proven native secondary font plus static alignment and renderer
  state. `na2_patcher/features/localization/resident_patcher/` contains the
  linked executable metric, fit, scale, and layout helpers. Together they
  target clean `SLPS_258.37` and `DATA/GF4.BIN`, preserve clean GF4C, and are
  covered by the current Localization aggregate feature pin
  `F68B5DB40A78F46CFCEB429F09E434CA4A106BD731420E76A7324415CD817BD8`.
- `docs/knowledge/localization/font/README.md` consolidates the v23, semantic-palette, and
  2026-07-19 auto-fit negative results. The retired raw declarative records
  are recoverable from Git commit `69da715` and are not retained in the
  working tree.
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
- Do not transplant the complete NUN5 renderer blindly. Prefer broad,
  evidence-backed renderer-logic ports when the homologous behavior is proven;
  retain caller wrappers only for genuinely container-specific bounds and
  alignment.

## Validation requirements

- Use clean, hash-verified NA2 and official NUN5 inputs.
- Keep `@source/` untouched and reuse preserved disassembly rather than
  disassembling the same binaries again.
- Log file, offset, original bytes, replacement bytes, and reason for every
  binary edit.
- Test glyph appearance and alignment before auto-adjust, then test all three
  together for regressions.
- Compare matched screenshots and record useful negative results under
  `docs/knowledge/localization/font/`.
- Keep experimental patches separately selectable until runtime-proven.
