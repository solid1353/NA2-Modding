# Font Workstream

## Objective

Make NA2 English text fit and align as cleanly as the UN5/NUN5 reference while
starting from clean NA2 assets. The clean font is serviceable and complete;
asset replacement is no longer assumed to be necessary. Renderer geometry,
measurement, positioning, and boxed auto-fit take priority, and glyph data is
changed only if matched captures still prove an appearance defect afterward.

Confirmed findings and negative results remain canonical in
`docs/knowledge/font/README.md`. This document defines the active work and its
execution order.

## Current result for review

The implementation keeps clean NA2 GF4/GF4C unchanged. Matched captures show
that the remaining material defects were call-local placement and overflow,
not an asset failure. The active `font` package now supplies separately
selectable, runtime-proven Controls auto-fit and character-modal alignment.
The rejected 28x28 quad experiment remains disabled as negative evidence.

## Required execution order

1. Establish the clean NA2 GF4/GF4C baseline and isolate vertical geometry.
2. Fix horizontal and vertical alignment while keeping clean glyph assets.
3. Reproduce NUN5's boxed measurement and shrink-only auto-fit decision.
4. Revisit glyph appearance only if matched captures still show a material
   asset defect after layout is correct.

Auto-adjust is downstream of horizontal metrics. A scaling test is not valid
until logical width, visible glyph bounds, advances, and centering are measured
for the same strings. The historical m01 and semantic-palette experiments are
negative evidence, not implementation parents.

## Active tasks

### Make font identical to UN5

Runtime review determined that no asset change is needed for this result:

- Use clean NA2 GF4 and GF4C while renderer alignment and fit are corrected.
- Compare glyph shape, apparent size, weight, raster coverage, and consistency
  against matched NUN5 captures only after placement is stable.
- Retain clean NA2's complete 95/95 printable-ASCII coverage.
- Treat `font_m01` and `font_nun5_appearance` as historical comparison data;
  do not copy their descriptor, placement, palette, or 123-cell construction.
- If a later screen proves an independent glyph defect, derive any donor from
  clean NA2 and official NUN5 structures and preserve NA2 palette semantics.
- Preserve file sizes and express every accepted binary change through a
  script-generated raw-binary patch.

Acceptance requires matched NA2/NUN5 captures at the same presentation scale,
with representative short and long strings and no missing, touching,
overlapping, or palette-damaged glyphs. No font-asset patch is an acceptable
outcome if clean assets already satisfy this requirement.

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
logical measurement. The accepted alignment changes are call-local instead:
the Controls row origin moves from 48 to 50, and the character modal uses five
measured X positions plus corrected row Y values. The modal centers are within
one pixel of NUN5; its selected red row matches exactly.

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

Clean NA2's applicable ASCII width is `9.5 * byte_count + 1`. The local helper
keeps every string below 14 bytes at scale `1.0`, so `Linked Attack` remains
full width, and applies `128 / measured_width` only to overflow. The official
19-byte `Ultimate Jutsu Prep` probe fits with scale `256 / 363` and centers
within half a pixel of NUN5. Scale returns to `1.0` before the next call, and
`OFF`, Save/Load, Practice, GF4, and GF4C remain outside the fit decision.

## Preserved baseline and evidence

- `na2_patcher/modules/raw_binary/patch_sets/font/` contains the active
  clean-source, runtime-proven alignment and fit components. It targets only
  clean `SLPS_258.37` and contains no GF4 or GF4C edit. Its current module hash
  is `86C229F4132A1388CEDFAD9EAF7735856911EF6B6D2E197DCEDC0C0762133AF4`.
- `na2_patcher/modules/raw_binary/patch_sets/font_m01/` is historical evidence.
  Its semantic NUN5 appearance patch is disabled and `runtime_failed`.
- `na2_patcher/modules/raw_binary/patch_sets/font_elf_history/` preserves
  historical ELF experiments.
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
