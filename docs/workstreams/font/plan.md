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

The replacement v2 shared core and Controls family are now runtime-proven and
enabled. The user accepted the exact matched Controls result on
2026-07-26, and supplied slot 1 proves the same worker ISO completes a real
title-to-Load transition without freezing.

The isolated Command Chart and Practice title layer remains runtime-proven and
enabled. The user explicitly accepted the Command Chart result on
2026-07-27; the Practice title result remains agent-validated and awaiting
acceptance. The next Practice explanation family is also agent-validated
across supplied slots 2-7: wrapping, line spacing, placement, and native inline
icons match NUN5. Its composed comparison grids await user acceptance before
the next caller family begins.

The reset baseline is documented in the existing
[Font knowledge record](../../knowledge/localization/font/README.md). User
slot 9 records the currently broken Save/Load lower modal: its panel is
vertically compressed, the instruction starts 20 pixels farther right and 14
pixels lower than the retained NUN5 reference, and the action row is about 13
pixels higher. Its comparison grid remains a task-owned artifact under
`work/Font/artifacts/`. A fresh post-reset capture is required before assigning
causation or reintroducing any old wrapper.

The ss3 Pause Controls list layer is implemented and statically validated
through a dedicated v2 BTL hook. It applies the retained 216-unit shrink-only
box and four-unit Y correction without enabling the retained shared wrapper or
any ss4 caller. Runtime comparison against the supplied ss3 pair remains
pending.

## Active ss1–ss6 epic priorities

The user directed Font to work only on the
[ss1–ss6 layout-parity epic](epics/ss2-6-layout/README.md) for now. Its
efficiency-prioritized sequential order supersedes the generic remaining-family
order below while the epic is active:

1. **ss3 — Pause Controls list.** Rebuild the retained 216-unit shrink-only
   list behavior and Y correction through a dedicated v2 entrypoint. This
   establishes the shared UI plumbing needed by ss4 without enabling ss4 yet.
2. **ss4 — Quit confirmation.** Reuse the ss3 shared UI plumbing, then add only
   the guarded confirmation-body and Yes/No positioning behavior. Commit and
   review it independently.
3. **ss1 — Special Controls final selector.** Reuse the accepted Controls core
   through a dedicated final-selector adapter that matches NUN5 glyph scale
   and advance together; preserve the already-correct ASCII `Off`/`On` source
   and the accepted first-eight Controls result.
4. **ss2 — Command Chart body.** Adapt the accepted v2 multiline primitives to
   the separate command-description caller; do not reopen the accepted title.
5. **ss5 — Character model move list.** Add bounded wrapping and positioning
   for the right-side move-name column.
6. **ss6 — Movie list.** Implement the variable-height wrapped-row behavior
   last because it has the largest caller-specific layout and row-advance
   burden.

Complete, commit, push, report, and obtain explicit acceptance for each item
before beginning the next. Shared primitives are implemented once, but each
slot keeps its own guarded caller and acceptance boundary.

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
remaining disabled. The shared v2 core and its adapter/session ABI are now
separate completed foundations; no caller-family behavior is enabled by either
boundary.

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

1. `font_v2_layout_core` was introduced as a default-disabled resident patch with a separate
   generated v2 asset. It exports the accepted 95-entry width table, guarded
   printable-ASCII and explicit-line measurement, shrink-only preparation,
   horizontal and vertical box positioning, one zero-initialized active-session
   pointer, and five null-session renderer hooks. It does not target any
   retained v1 symbol or redirect a screen.
2. The adapter/session ABI is a separate resident fragment that prepares one
   caller-owned stack record, publishes it only around one native callback,
   and restores the previous session, renderer tracking, horizontal scale and
   callback result through one cleanup path. Its record carries four native
   callback arguments and keeps nested calls safe by restoring the prior active
   session. It likewise has no caller-family hook by itself.

Only after both foundations are committed does Controls receive the first
family-specific wrapper and runtime comparison.

### First caller family: Controls

The first caller-specific implementation and commit adds the Controls adapter
on top of the completed foundations:

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

The first fully normalized capture restored all eight row advances and matched
their vertical bounds, but its empirical box-left `59` placed every NA2 text
bound one output pixel left of NUN5. A pushed box-left `58` candidate moved the
bounds another one to two pixels left and is rejected. The preserved callers
prove the replacement formula directly: NUN5 uses box-left `60`/`324`, while
NA2 supplies native centers `124`/`388`, so the exact family rule is
`box_left = caller_center - 64`. No shared metric, scale, row, or `OFF`
behavior changes.

The final matched 640x480 comparison reproduces all eight NUN5 label bounds
and centers, keeps `Linked Attack` full width, and leaves `OFF` on the ordinary
renderer. The user explicitly accepted that result on 2026-07-26. Supplied
`ss1`, copied with provenance under
`work/Font/inputs/sstates/autofit_v2/controls/load-transition/`, has boot CRC
`A8A3C694` and shows the same exact worker ISO fully rendering the Load screen
after a real title transition. The accepted core and Controls rows are
therefore runtime-proven and enabled.

The final Special Controls selector is a deferred Controls/autofit case rather
than a text-conversion case. The supplied remade `ss1` proves that its live
table already contains ASCII `Off`/`On` through T1956/T1957. Redirecting that
table to the separate ASCII `OFF`/`ON` literals changed zero pixels across the
entire modal, so no literal or table redirect is retained. Its remaining NUN5
parity defect is the physically larger, wider-spaced presentation: NUN5 routes
the title-case strings through `FUN_00385df0` with a 128-unit width, while NA2
uses native `FUN_00379240`. Revisit that caller only with the broader
autofit/positioning work, preserve the accepted first-eight Controls result,
and validate glyph scale and advance together instead of patching either
literal family.

### Second caller family: Command Chart and Practice titles

The title family reuses the accepted v2 core through one configurable
adapter, with two thin explicit BTL entrypoints:

- Command Chart replaces only the title call at BTL file `0x1C6A28` and uses
  the 288-by-20 box at X `27.2` with caller Y minus `3.8`;
- Practice replaces only the title call at BTL file `0x1C4B98` and uses the
  352-by-20 box at X `31.2` with caller Y minus `6.8`;
- both modes are left-aligned, single-line, shrink-only, and call NA2's native
  `0x00382310` draw entry after v2 preparation;
- the title layer does not select the Practice explanation loop or the two
  Command Chart auxiliary-string calls; each remains a separate caller family.

Both hook guards are the original `jal 0x00382310` plus its NOP delay slot.
The shared adapter preserves the original render object, string and style,
selects geometry through the explicit entrypoint mode, and delegates all
measurement, scale publication and restoration to the already accepted v2
session core.

Hidden worker captures on the final isolated ISO cover Command Chart slot 3,
Practice command slots 2-7, and the accepted Controls regression. They prove
the 288-unit long-title shrink, the 352-unit Practice title origins, unchanged
short-title scale, and unchanged later Practice explanation rows. The supplied
states also correct the live BTL mapping to `0x006B3F00 + file offset`; using
the `0x006B3EC0` Ghidra mapping as a live base writes `0x40` bytes too early.
The user explicitly accepted the Command Chart result on 2026-07-27. Practice
title acceptance remains pending.

### Third caller family: Practice explanations

The Practice explanation family replaces only the per-token draw loop reached
from BTL file `0x1C4BA0` / runtime `0x00878AA0`. Its adapter builds one bounded
512-byte mixed text/tag buffer, installs call-local native metric and draw
callbacks, and routes the result through the shared v2 measurement and
positioning primitives:

- the box is 364 by 48 at X `39.2`, with caller Y plus `21.2`;
- glyph height is 28 and line advance is 14;
- wrapping is shrink-free and word-based, with no artificial two-line cap;
- the exact 13-record token map preserves D-pad, face, plus, and shoulder
  glyphs through NA2's native icon table and renderer;
- callback pointers, renderer state, tracking, scale, and both icon objects are
  restored after every call.

The unlimited line count is required by the supplied `ss3` Flee explanation,
which uses three lines in NUN5. Supplied slots 2-7 also cover one- and two-line
rows and every supported icon class. Their matched 640x480 captures reproduce
NUN5 wrapping, line spacing, X/Y placement, and inline-icon alignment. The
`ss5` title remains `Charge` in Current versus `Charge Chakra` in NUN5; that is
a separate text mapping difference and not a Font layout defect.

The isolated worker ISO has SHA-256
`D624C39F0132FF5ED3BA4D60E99B78113AF85805D3870B072643B9400CC2B10B`
and boot CRC `A85C52F7`. Its 7,536-byte resident payload has SHA-256
`47EF54100642B25366FADF4A0D5C12B7255D3CF89456BD3F3DB5ACB056ED1101`;
the 4,084-byte generated v2 asset has SHA-256
`382AD202C1225326B59832BECE7A8AE61A2A69870B18B17D1F606B6C5152BE90`.
The Controls and Command Chart regression captures remain intact. The family
is runtime-proven and enabled, with user acceptance of the composed
Practice grids still pending.

### ss3 epic caller family: Pause Controls list

The Pause Controls list layer redirects only the list-row call at BTL file
`0x1C97D8` / runtime `0x0087D6D8`. The clean guard is
`jal 0x00382470` plus its NOP delay slot. Its dedicated v2 adapter:

- preserves the native object, text, style, and X origin;
- applies the retained NUN5 four-unit upward Y correction;
- uses one single-line, left-aligned, 216-unit shrink-only box;
- calls the original NA2 list helper at `0x00382470`;
- delegates measurement, scaling, session publication, and restoration to the
  accepted v2 core.

The retained `font_layout_wrappers` patch remains disabled, and no ss4
confirmation-body or Yes/No call is selected. Generation, relocation, hook,
ABI, and package tests pass. Runtime comparison against the supplied ss3 pair
is still required before changing the patch from `approved_for_test`.

### Static and automated validation

Before each caller-family commit:

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

1. Implemented and runtime-proven: Command Chart and Practice titles through
   one configurable title adapter, retaining their distinct 288- and 352-unit
   containers. Command Chart is user-accepted; Practice title acceptance
   remains pending.
2. Shared confirmation choices and confirmation bodies.
3. Agent-validated, awaiting user acceptance: Practice explanations through a
   364-by-48 wrapping container, with markup and controller icons preserved as
   atomic native tokens.
4. Save/Load instruction and action-row layout, with panel geometry handled
   separately from text placement.
5. Remaining proven caller families identified through matched evidence.

Any later change to the shared core must rerun all previously accepted families.
Do not begin the next family until the current result is committed, pushed and
visually accepted.

### User input and effort

Needed from the user:

- after each family: accept the comparison or identify the remaining defect;
- later only when requested: provide a matched NUN5/NA2 savestate pair for a
  caller not covered by existing evidence.

The agent owns analysis, generation, worker builds, task PCSX2 operation,
validation, commits and pushes. Existing states were sufficient to implement
and review the Practice explanation family.

Recommended effort: **max**, due to cross-function MIPS ABI preservation,
renderer-state restoration, symbolic resident linking and multi-screen runtime
regression risk.

**Plan approved; foundations complete; Controls and Command Chart accepted;
Practice title and Practice explanations agent-validated and awaiting user
acceptance**

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
  `na2_patcher/features/localization/runtime_injector/` retains the linked
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
