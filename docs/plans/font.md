# Font Workstream

## Objective

Bring NA2's English font rendering to visual and behavioral parity with the
UN5/NUN5 reference without another blind resource swap or a full renderer
transplant. The work is separated into glyph appearance, alignment and
metrics, and finally boxed auto-adjust behavior because each stage depends on
the preceding renderer state.

Confirmed findings and negative results remain canonical in
`docs/knowledge/font/README.md`. This document defines the active work and its
execution order.

## Required execution order

1. Make the font visually identical to UN5.
2. Fix horizontal and vertical alignment issues and establish metric parity.
3. Research and implement NUN5 auto-adjust behavior using the corrected
   measurement and renderer paths.

Auto-adjust is downstream of horizontal metrics. A scaling test is not valid
until logical width, visible glyph bounds, advances, and centering agree with
NUN5 for the same strings.

## Active tasks

### Make font identical to UN5

Focus this task on glyph appearance rather than placement:

- Match glyph shape, apparent size, weight, raster coverage, and consistency
  against matched NUN5 captures.
- Retain complete English glyph coverage without the patchy rendering caused
  by direct whole-file GF4 swaps.
- Determine which accepted `font_m01` GF4 changes are correct and which
  remaining differences belong to GF4/GF4C data or renderer interpretation.
- Compare exact source structures and renderer consumers before proposing any
  new binary edit.
- Preserve file sizes and express every accepted binary change through a
  script-generated raw-binary patch.

Acceptance requires matched NA2/NUN5 captures at the same presentation scale,
with representative short and long strings and no new missing, touching, or
overlapping glyphs.

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

### Research and implement NUN5 auto-adjust behavior

Resume this task only after the first two stages establish stable font metrics.
The implementation must reproduce NUN5's fit decision as well as its scaling:

- Compare NUN5's boxed path
  `FUN_00399df0 -> FUN_00389df0 -> FUN_0018b1b0 -> FUN_0018ca40` with the
  corresponding NA2 call sites and renderer state.
- Reconcile NUN5 measurement through `FUN_0018b7f0` with NA2's legacy
  `FUN_003798e0 -> FUN_001859a0 -> FUN_00184e60` path.
- Preserve NUN5's per-call behavior: the first eight Control Settings labels
  use the 128-pixel box, while the final `OFF` row uses the ordinary renderer.
- Verify both the threshold decision and final visual bounds; do not accept a
  result merely because clipping disappears.

## Preserved baseline and evidence

- `na2_patcher/modules/raw_binary/patch_sets/font_m01/` is the accepted active
  clean-coverage baseline. Its canonical package hash is
  `7F08FC58F1EBEF47B586CFB05BCCFC09F599D453390DC25331F7018ADF1F17AF`.
- The accepted `font_m01` output hashes are documented beside that patch set.
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
- Do not assume GF4C replacement is independently useful. Its functional
  significance remains unproven.
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
