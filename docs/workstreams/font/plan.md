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

The accepted native 14x20 NUN5-derived font remains enabled and unchanged.
The generic resident patcher and all Font code/data declarations also remain.
The user rejected the combined July 24-25 autofit/layout result as unstable,
so its five logical selections are retained but default-disabled before the
stage-by-stage rebuild. The independently reviewed Character Select modal
alignment remains enabled.

The reset baseline is documented in the existing
[Font knowledge record](../../knowledge/localization/font/README.md). User
slot 9 records the currently broken Save/Load lower modal: its panel is
vertically compressed, the instruction starts 20 pixels farther right and 14
pixels lower than the retained NUN5 reference, and the action row is about 13
pixels higher. Its comparison grid remains a task-owned artifact under
`work/Font/artifacts/`. A fresh post-reset capture is required before assigning
causation or reintroducing any old wrapper.

## Required execution order

1. Completed and retained: establish and accept the native NUN5-derived font.
2. Current stage: default-disable the rejected July 24-25 autofit/layout stack
   without deleting its code, assets, declarations, or evidence.
3. Capture and accept the post-reset baseline, including the Save/Load lower
   modal from slot 9.
4. Reimplement one proven caller family at a time. Commit, push, and obtain
   visual acceptance before beginning the next family.
5. Prefer one shared denominator or wrapper when cross-screen evidence proves
   it; never duplicate shared behavior merely because it appears in several
   screens.

Auto-adjust is downstream of horizontal metrics. A scaling test is not valid
until logical width, visible glyph bounds, advances, and centering are measured
for the same strings. The historical m01 and semantic-palette experiments are
negative evidence, not implementation parents.

## Approved replacement architecture — implementation active

Status: approved for implementation. Keep the accepted font and the retained
July autofit/layout implementation unchanged, with the old implementation
remaining disabled. The shared v2 core and its adapter/session ABI are separate
foundational commit boundaries before any caller-family behavior is enabled.

### Architecture

Add an independent `localization.font.v2.*` implementation linked into
`PRG/228.BIN`. It is a shared NUN5-compatible layout core plus thin
caller-family adapters, not a transplanted NUN5 renderer:

1. The shared core owns logical measurement, ordinary spacing, shrink-only
   fitting, wrapping, alignment, and renderer-state restoration.
2. Each caller-family adapter supplies its native arguments, text box, alignment
   and exceptional behavior.
3. NA2 continues drawing glyphs, colours, shadows, markup and controller icons
   through its original renderer and callbacks.
4. Original `SLPS`, `BTL`, and `ETC` files receive only guarded call-site hooks,
   displaced-instruction handling and genuinely local static coordinates.
5. No adapter duplicates measurement, spacing, fitting or wrapping formulas.
   Several windows may share an adapter only when their call contract and layout
   semantics are genuinely the same.
6. Avoid the retained monolithic return-address multiplexer. Prefer one explicit
   entrypoint per family; if callers genuinely converge, pass an explicit mode
   from the outer caller rather than inferring behavior from nested returns.

### Resident implementation

Extend `scripts/research/localization/generate_font_renderer.py` to generate a
separate v2 resident asset while preserving the retained old blob and symbols.
New fragments use unique `localization.font.v2.*` names and provide:

- the accepted 95-entry proportional-width table;
- exact printable-ASCII measurement;
- shrink-only fit calculation;
- horizontal and vertical box positioning;
- wrapping and line measurement when a caller requires them;
- guarded space, bearing, glyph-advance and newline helpers;
- call-local layout-session entry and cleanup;
- one adapter per implemented caller family.

The resident patcher may still link retained old fragments when any Font
resident patch is active, but no new hook may target them. Their presence is
inert retained evidence, not executable behavior.

### Call-local layout session

Each adapter builds its request and saved state on its own stack frame. The
record contains the text, box origin and dimensions, alignment, wrapping mode,
line limit, scale, spacing mode and native draw callback. One resident writable
word points to the active stack record:

1. Save the previous session pointer, renderer fields, tracking, scale,
   coordinates, arguments and displaced state.
2. Set the accepted secondary-font mode, tracking and initial scale for this
   call.
3. Measure, fit, wrap and calculate the final origin.
4. Publish the call-local session pointer and invoke the original NA2 draw path.
5. Restore every saved value through one cleanup path, including on unscaled
   and exceptional branches.

A null session pointer makes every shared hook reproduce original NA2 behavior.
Saving and restoring the previous pointer permits nested renderer callbacks
without leaving stale state.

### Measurement, spacing and fit

Measurement and drawing must consume the same table and formulas:

- secondary tracking is `0` during a v2 layout session;
- an ordinary ASCII space advances eight logical units;
- glyph advances use the accepted proportional metrics;
- horizontal leading bearings, glyph geometry and advances use the same local
  horizontal scale;
- fitting uses `min(1, box_width / measured_width)` and never enlarges text;
- the accepted font's existing scale integration is saved, used and restored;
- outside a v2 session, tracking, spacing and scale retain original NA2
  behavior.

This prevents a denominator-only port in which the fit decision and the actual
drawn spacing disagree.

### Positioning

The core positions text inside a supplied container:

```text
left   = box.x
center = box.x + (box.width - rendered_width) / 2
right  = box.x + box.width - rendered_width
```

Vertical placement uses the corresponding box height, line count, line height
and requested alignment. A caller adapter may supply a proven NUN5 bias or
fixed anchor, but must not contain per-string or per-row pixel tuning unless
the NUN5 caller itself proves that exception. Moving panel artwork or the
window itself remains a local screen/table change outside the layout core.

### Canonical patch structure

Retain every old autofit/layout row as default-disabled. Add new resident
patches rather than altering those rows:

- one v2 shared-core patch for guarded renderer primitives;
- one independently selectable patch for each caller family;
- matching binary-patcher rows only for local constants or coordinates that
  cannot be expressed by the resident adapter.

The generator produces the v2 blob plus deterministic fragment and relocation
rows. Resident `groups.tsv`, `patches.tsv`, `fragments.tsv`,
`relocations.tsv`, and `edits.tsv` declare the generated code and symbolic
hooks. Binary `patches.tsv` and `edits.tsv` declare only guarded static changes.
Tests cover generation, package selection and linked targets.

At each coherent boundary, recompute the exact combined Localization feature
pin while preserving the existing `bypass_check` value exactly. Only the user
may change that value.

### Foundational implementation boundaries

The user directed the shared core and adapter/session layer to be completed
before caller-family behavior:

1. `font_v2_layout_core` is a default-disabled resident patch with a separate
   generated v2 asset. It exports the accepted 95-entry width table, guarded
   printable-ASCII and explicit-line measurement, shrink-only preparation,
   horizontal and vertical box positioning, one zero-initialized active-session
   pointer, and five null-session renderer hooks. It does not target any
   retained v1 symbol or redirect a screen.
2. The adapter/session ABI is a separate resident fragment that prepares one
   caller-owned stack record, publishes it only around one native callback,
   and restores the previous session, renderer tracking, horizontal scale and
   callback result through one cleanup path. It likewise has no caller-family
   hook by itself.

Only after both foundations are committed does Controls receive the first
family-specific wrapper and runtime comparison.

### First caller family: Controls

The first implementation and commit contains the v2 core plus the Controls
adapter:

- use the proven 128-unit container for the first eight action labels;
- keep non-overflowing labels at scale `1`;
- keep `Linked Attack` full width;
- measure `Ultimate Jutsu Prep` as 178 logical units and apply `128 / 178`;
- leave `OFF` on the ordinary renderer;
- apply only the proven labels-only Controls position correction;
- restore scale, tracking, coordinates, renderer fields and the session pointer
  before the next draw.

Acceptance requires matched NUN5/Current bounds and centers, correct short-label
spacing, the complete long label, an unchanged `OFF` path and a successful real
title-to-Load transition.

### Static and automated validation

Before the Controls commit:

1. Verify deterministic regeneration of the old and v2 resident assets and
   tables.
2. Verify unique symbols, exact relocation targets and preserved jump delay
   slots.
3. Verify inactive hooks reproduce the original NA2 instructions and formulas.
4. Unit-test known NUN5 denominators, overflow decisions and restoration paths.
5. Validate resident and binary packages, linked payload bounds and the exact
   combined Localization feature pin.
6. Run the focused Font tests and the complete repository suite.
7. Confirm no GF4/GF4C change beyond the already accepted font baseline.

### Runtime validation and reporting

Build only a worker ISO at `work/Font/build/` and operate only the Font-owned
PCSX2 copy created from `@pcsx2_clean`. Never launch or control the protected
user installation. Copy any selected user savestate read-only into
`work/Font/inputs/sstates/` with provenance before use.

For each family:

1. Capture the clean current baseline.
2. Capture the v2 result under matching game and emulator conditions.
3. Verify representative short, fitting and overflowing strings.
4. Rerun every previously accepted caller family for regressions.
5. Commit and push the completed family.
6. Present one composed grid with NUN5 on the left and Current NA2 on the right.
7. Wait for user acceptance before beginning the next family.

### Remaining caller-family order

After accepted Controls:

1. Command Chart and Practice titles through one configurable title adapter,
   retaining their distinct 288- and 352-unit containers.
2. Shared confirmation choices and confirmation bodies.
3. Practice explanations through a 364-by-48 wrapping container. Treat markup
   and controller icons as atomic tokens and preserve NA2's native icon
   callback; do not promote this family until that callback is proven.
4. Save/Load instruction and action-row layout, with panel geometry handled
   separately from text placement.
5. Remaining proven caller families identified through matched evidence.

Any later change to the shared core must rerun all previously accepted families.
Do not begin the next family until the current result is committed, pushed and
visually accepted.

### User input and effort

Needed from the user:

- now: approve this replacement plan with `qwe`;
- after reset: accept the clean post-reset baseline;
- after each family: accept the comparison or identify the remaining defect;
- later only when requested: provide a matched NUN5/NA2 savestate pair for a
  caller not covered by existing evidence.

The agent owns analysis, generation, worker builds, task PCSX2 operation,
validation, commits and pushes. Existing states are sufficient to begin
Controls.

Recommended effort: **max**, due to cross-function MIPS ABI preservation,
renderer-state restoration, symbolic resident linking and multi-screen runtime
regression risk.

**Plan approved; foundational stages 1-2 in progress**

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

### Research and implement NUN5 auto-adjust behavior - preserved, disabled

The July 24-25 implementation reproduced NUN5's fit decision as well as its
scaling, without redirecting NA2 to a layout-incompatible NUN5 function.
Its findings remain useful, but its combined executable selection is now
default-disabled pending the stage-by-stage rebuild:

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

- `na2_patcher/features/localization/binary_patcher/` contains the enabled
  native secondary font and independent Character Select modal alignment plus
  the retained, disabled static autofit state.
  `na2_patcher/features/localization/resident_patcher/` retains the linked
  metric, fit, scale, and layout helpers with their default selections
  disabled. All remain covered by the current Localization aggregate feature
  pin.
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
