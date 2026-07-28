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
The generic runtime injector remains. The obsolete July v1 renderer, its five
disabled logical selections, and its unreachable code/data declarations were
retired on 2026-07-28. The independently reviewed Character Select modal
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

The Pause Controls list layer now covers its two distinct native draw paths.
The normal ss2 state remains user-accepted. The remade ss3 state proves that
the selected red path bypassed that fit, overflowed, and shifted relative to
the same unselected row. A second guarded BTL hook now applies the same
216-unit shrink-only box and four-unit Y correction while preserving the red
style and applying the proven two-unit selected-helper X compensation. The
user verified the rebuilt selected state on 2026-07-27, so the whole Pause
Controls caller family is accepted.

The ss4 Battle quit-confirmation implementation is now statically complete and
awaiting the user's fresh-build runtime review. It leaves T63–T67 unchanged,
wraps only a bounded stack copy at the exact body draw call, and scopes the
shared selected/unselected coordinate adapters only around the exact ss4
Yes/No list call. No stale savestate can validate this overlay/resident change.

## Deferred font-appearance refinement — outside the layout epic

A small residual font-appearance mismatch against NUN5 remains after the
accepted Pause Controls layout correction. Its exact refinement is not yet
scoped. It is recorded here as separate Font work and does not reopen the
accepted fitting, positioning, or clipping behavior in the ss1–ss6 layout
epic.

## Active ss1–ss6 epic priorities

The user directed Font to work only on the
[ss1–ss6 layout-parity epic](epics/ss2-6-layout/README.md) for now. Its
efficiency-prioritized sequential order supersedes the generic remaining-family
order below while the epic is active:

1. **ss4 — Quit confirmation.** Reuse the accepted Pause Controls plumbing, then add only
   the guarded confirmation-body and Yes/No positioning behavior. Commit and
   review it independently.
2. **ss1 — Special Controls final selector.** Convert the two proven
   modal-specific fullwidth Shift-JIS slots to official NUN5 ASCII `ON`/`OFF`
   through canonical mappings, then measure the fresh mapped result and add a
   bounded positioning correction only if it remains necessary. Preserve the
   accepted first-eight Control Settings result.
3. **ss5 — Character model move list.** Add bounded wrapping and positioning
   for the right-side move-name column.
4. **ss6 — Movie list.** Implement the variable-height wrapped-row behavior
   last because it has the largest caller-specific layout and row-advance
   burden.

Complete, commit, push, report, and obtain explicit acceptance for each item
before beginning the next. Shared primitives are implemented once, but each
slot keeps its own guarded caller and acceptance boundary.

## Required execution order

1. Completed and retained: establish and accept the native NUN5-derived font.
2. Completed: retire the rejected July 24-25 v1 executable stack after the v2
   implementation made every one of its fragments unreachable; retain its
   reusable evidence in canonical knowledge and Git history.
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

Status: approved and active. Keep the accepted font unchanged. The retired July
v1 implementation is historical evidence only. The shared v2 core and its
adapter/session ABI are the current behavioral baseline.

### Architecture

Use the independent `localization.font.v2.*` implementation linked into
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
6. Avoid the retired monolithic return-address multiplexer. Prefer one explicit
   entrypoint per family; if callers genuinely converge, pass an explicit mode
   from the outer caller rather than inferring behavior from nested returns.

### Resident implementation

`scripts/localization/generate_font_renderer.py` generates the live v2
resident asset and unique `localization.font.v2.*` symbols:

- the accepted 95-entry proportional-width table;
- exact printable-ASCII measurement;
- shrink-only fit calculation;
- horizontal and vertical box positioning;
- wrapping and line measurement when a caller requires them;
- guarded space, bearing, glyph-advance and newline helpers;
- call-local layout-session entry and cleanup;
- one adapter per implemented caller family.

No retired v1 fragment or hook remains in canonical executable inputs.

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

The retired v1 autofit/layout rows must not return. Live resident structure is:

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

1. `font_v2_layout_core` exports the accepted 95-entry width table, guarded
   printable-ASCII and explicit-line measurement, shrink-only preparation,
   horizontal and vertical box positioning, one zero-initialized active-session
   pointer, and five null-session renderer hooks. It does not target any
   retired v1 symbol or redirect a screen.
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

The remade Special Controls `ss1` and exact-guarded telemetry prove that the
modal does not use the Control Settings T1956/T1957 table. It draws clean-SLPS
fullwidth slots `Ｏ　Ｎ` and `ＯＦＦ` from files `0x505AF0` and `0x505AF8`,
seen at runtime `0x006059F0` and `0x006059F8`. Canonical mappings
T2203/T2204 replace only those slots with the official NUN5 SLES `ON`/`OFF`
donors. The previously added ELF `0x2888D4` hook targets the unrelated Control
Settings vibration row and is removed. After the mapping boundary is committed,
apply its exact bytes to the task-owned ss1 state and measure remaining
positioning before authoring any renderer change.

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

### ss2/ss3 epic caller family: Pause Controls list

The remade ss2 and ss3 pair are two selection states of the same Pause Controls
modal. The normal layer redirects BTL file `0x1C97D8` / runtime `0x0087D6D8`,
guarded by `jal 0x00382470` plus NOP. Its accepted adapter remains unchanged.
The selected layer redirects BTL file `0x1C9794` / runtime `0x0087D694`,
guarded by `jal 0x003827A0` plus NOP. Together they:

- use one single-line, left-aligned, 216-unit shrink-only box;
- apply the retained NUN5 four-unit upward Y correction;
- preserve the normal float ABI and selected integer/text/color ABI
  independently;
- preserve the native red selected style;
- compensate the selected shadow helper by two local X units so the row does
  not move when selected;
- delegate measurement, scaling, session publication, and restoration to the
  accepted v2 core, then call the original native helper for each path.

The retired v1 `font_layout_wrappers` patch is not present, and no ss4
confirmation-body or Yes/No call is selected. Generation, relocation, hook,
ABI, and package tests pass. The normal ss2 state and corrected selected ss3
state are both user-verified; the Pause Controls caller family is accepted.

### ss4 epic caller family: Battle quit confirmation

The ss4 implementation adds one explicit caller-local layer rather than
restoring the retired v1 global layout multiplexer:

- BTL file `0x1C4048` scopes the native `0x00383600` Yes/No list call;
- BTL file `0x1C407C` routes the native `0x003825B0` body call through a
  bounded draw-time wrapper;
- ELF files `0x283914` and `0x283A60` replace only the selected and unselected
  calls inside `0x00383600`.

The body wrapper copies at most 255 bytes, greedily wraps the copy inside a
420-unit two-line box, and draws at the retained NUN5-local X/Y origin. It
never mutates T63–T67, the source buffer, or any translation mapping. The list
wrapper publishes one nested-safe transient word only while the exact ss4 list
is drawing; outside that interval both shared call-site adapters tail-call
native behavior unchanged. Yes and No retain their independently measured
NUN5 coordinates in either selection state.

Deterministic generation and focused package tests verify all four clean
guards, relocation targets, transient-data initialization, native fallback
tails, two-line geometry, bounded copy, and mapping neutrality. Runtime status
remains `approved_for_test` until the user builds a fresh ISO and reviews ss4;
the supplied pre-build state restores changed BTL/ELF/resident bytes and
cannot validate this patch.

### Static and automated validation

Before each caller-family commit:

1. Verify deterministic regeneration of the live C/assembly resident assets
   and tables.
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
6. Stop and give the user the exact regression checklist; do not perform the
   runtime regression pass for them.
7. After the user supplies the resulting captures, present one composed grid
   with NUN5 on the left and Current NA2 on the right.
8. Wait for user acceptance before beginning the next family.

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

Recommended effort: **high**, due to cross-function MIPS ABI preservation,
renderer-state restoration, symbolic resident linking and multi-screen runtime
regression risk.

**Plan approved; foundations complete; Controls and Command Chart accepted;
Practice title and Practice explanations agent-validated and awaiting user
acceptance**

## Approved C migration

The live v2 behavioral renderer migrates from hand-encoded MIPS to ordinary C
compiled for PS2 EE and contributed through the existing runtime-injector and
payload-builder architecture. The Injection Lab is a development compiler and
hot-reload aid only; canonical builds consume deterministic generated
fragments and never depend on a PNACH or a fixed development-bank address.

Migration proceeds in independently committed stages:

1. Completed on 2026-07-28: add deterministic EE C compilation and
   object-section extraction for Font, with no game hook or behavior change.
2. Replace shared v2 measurement, spacing, fitting, positioning, and the
   session dispatcher with C while retaining only the minimal assembly ABI and
   displaced-instruction shims.
3. Replace caller-family behavioral adapters one family at a time.
4. Evaluate the independent numeric formatter separately and migrate it only
   when doing so reduces maintained assembly without broadening behavior.
5. Remove each superseded assembly implementation only in the same commit that
   proves static parity for its C replacement.

Native glyph assets, donor bytes, constants, coordinates, guarded call-site
edits, and unavoidable register/return trampolines remain declarative binary
or assembly inputs. C code must not own final `228.BIN` placement: generated
sections and relocations are exported as runtime-injector fragments, and the
shared payload builder assigns their final addresses.

### Stage 1 C compiler/extraction boundary

`na2_patcher/payload_builder/ee_c_fragments.py` reuses Injection Lab's
bundled `ee-gcc` and proven EE compilation contract. It does not duplicate the
compiler or use the lab's fixed development-bank linker. Instead, it converts
the compiler's ELF32 little-endian MIPS relocatable object into canonical
payload-builder inputs:

- allocated code, read-only data, initialized data, and zero-initialized BSS
  become address-independent runtime-injector fragments;
- exported C symbols retain their section-relative offsets;
- `R_MIPS_32`, `R_MIPS_26`, `R_MIPS_HI16`, and `R_MIPS_LO16` become the
  payload builder's existing `abs32`, `j26`/`jal26`, `hi16`, and `lo16`
  relocations;
- external C symbols require an explicit payload-symbol mapping and fail
  closed when missing;
- deterministic fingerprints cover extracted bytes, relocations, and exported
  symbol references.

This boundary adds no canonical fragment row, resident asset, hook, profile-pin
change, or runtime behavior. The next stage may feed extracted C fragments into
the existing Font generator while retaining the assembly implementation until
static and user-run regression parity are established.

### Stage 2 shared-core C replacement — accepted

The accepted replacement changes only the canonical v2 measurement and
preparation fragments to compiled C:

- `font_v2_measure` preserves printable-ASCII measurement, `<br>` handling,
  explicit newline handling, maximum-line width, and line count;
- `font_v2_prepare` preserves premeasured input, line-limit validation,
  shrink-only horizontal scale, separate glyph-height/line-advance handling,
  rendered bounds, and start/center/end positioning;
- the C struct contains compile-time assertions for every shared session offset
  consumed by the existing assembly adapters;
- the generated C has no runtime-library helper, heap use, absolute game
  address, or unsupported relocation;
- the existing adapter and every caller-family hook remain unchanged and still
  call the canonical `localization.font.v2.prepare` symbol;
- the user confirmed no visible change across the shared-core regression pass,
  after which the superseded measure/prepare assembly builders were removed.

The C core adds one private `<br>` helper and increases the v2 renderer blob
from 5,652 to 5,832 bytes. Its call-site patches, caller adapters, and
caller-specific constants remain unchanged.

### Stage 3 shared-session C replacement — accepted

The shared `localization.font.v2.adapter_call` dispatcher is now generated from
`font_v2_adapter_call` in the same C source as the accepted measurement and
preparation core. The candidate preserves the existing session ABI and caller
adapters:

- validate and prepare the caller-owned session before changing renderer state;
- save the prior active session, renderer tracking, and horizontal scale;
- clear tracking, apply the prepared horizontal scale, and publish the session;
- invoke the original native callback indirectly with its four stored
  arguments;
- restore scale, tracking, and the prior session before returning the callback
  result.

The compiled dispatcher is 216 bytes, uses only the supported symbolic
relocations to `prepare` and the active-session pointer, and emits no runtime
library helper. Replacing the 244-byte assembly dispatcher reduces the v2
renderer blob from 5,832 to 5,804 bytes. The user confirmed no visible change
across the shared-session regression pass, after which the superseded assembly
builder was removed. Caller-family adapters and every game hook remain
unchanged.

### Stage 4 Controls C replacement — accepted

The accepted first-eight-label Controls behavior now constructs its stack-local
session in compiled C. The C entry receives the existing hook's text/style
arguments and native `$f12`/`$f13` center coordinates directly, subtracts the
proven 64-unit half-width, and supplies the unchanged 128-by-20 centered,
single-line, shrink-only request to the shared dispatcher.

The 136-byte C adapter replaces the 144-byte assembly adapter and reduces the
v2 renderer blob from 5,804 to 5,796 bytes. The hook, Controls constants,
shared dispatcher, and native drawing behavior are unchanged. The existing
108-byte assembly callback remains the minimal native-renderer ABI shim: it
must call the original absolute measurement and centered-draw entrypoints with
their exact mixed integer/float register convention. The user confirmed no
visible change across the Controls regression pass, after which the old
assembly session builder was removed.

### Stage 5 Command Chart / Practice title C replacement — accepted

The accepted shared title family now uses compiled C for its common session
construction and both direct hook entries. EE GCC consumes the existing three
integer arguments plus native `$f12`/`$f13` coordinates directly, so no new
register shim is needed. The two C entries preserve their separate accepted
geometry and call one shared C helper:

- Command Chart: X `27.2`, native Y plus `-3.8`, width `288`;
- Practice title: X `31.2`, native Y plus `-6.8`, width `352`;
- both: height and line height `20`, start alignment, one line, shrink-only.

The 120-byte common C adapter and two 56-byte C entries replace the 220-byte
assembly adapter plus two 12-byte assembly entries, reducing the v2 renderer
blob from 5,796 to 5,784 bytes. Both guarded hooks and the 16-byte native boxed
draw callback remain unchanged. That callback is the minimal ABI shim which
loads prepared `$f12`/`$f13` coordinates and tail-calls the absolute original
renderer entrypoint. The user confirmed no visible change across the
title-family regression pass, after which the old assembly title adapter and
entries were removed.

### Approved collapsed remainder

On 2026-07-28, the user approved collapsing the remaining C migration into
exactly three independently committed steps:

1. Port all remaining behavioral layout code together: Pause Controls,
   shared native measurement/wrapping, Quit confirmation, Special Controls
   explanatory body, and Practice explanations/icon flow. Preserve only
   unavoidable native-entry and displaced-instruction ABI shims. Stop after
   the pushed candidate for one regression pass covering every affected screen.
2. Evaluate and, when it reduces maintained assembly without changing scope,
   port the independent numeric formatter to C.
3. Move canonical C/compiler/generator inputs out of `scripts/research/`,
   remove every superseded assembly builder, and document the minimal retained
   ABI shims. This final structural step must not change generated payload
   bytes.

For the collapsed migration, deterministic regeneration, object/symbol/
relocation inspection, package loading, and exact Localization-pin validation
precede delivery of each candidate. Per the user's 2026-07-28 instruction,
runtime regression is manual first: Font stops with a concrete verification
checklist, the user performs the pass, and only an accepted candidate is added
to or updates permanent automated coverage. Unaccepted implementation choices
remain outside the permanent suite.

### Collapsed step 1 — accepted

The first collapsed candidate ports the remaining behavioral layout code to
the existing compiled-C pipeline:

- Pause Controls normal and selected session construction;
- nested Quit-confirmation scope and selected/unselected coordinate mapping;
- native measurement with ordinary-space correction and greedy draw-time
  wrapping;
- shared Quit/Special Controls explanatory-body construction;
- Practice mixed text/icon assembly, icon metrics/drawing, and wrapped layout.

The compiler exports 25 C fragments. Together with retained data and ABI
bridges, the v2 package contains 49 fragments in a 5,924-byte resident blob,
SHA-256
`7F021178787EA9A845EED8AE348B731345C3459BF1AF29D48CA02B26E84D5F28`.
The independent 188-byte numeric blob remains byte-identical at SHA-256
`A110555F91F4A21E32546F49B9C0FF7D7EDD1C72EB2EA9796D3AB00C3A9D0604`.

Assembly remains only where the native game ABI or displaced instructions
require it: absolute renderer tail calls, live-register capture at selected
Pause and Practice entries, the scoped native Quit-list call, and the five
session-guarded renderer hooks. Manual object disassembly caught and corrected
one EE EABI issue before canonical generation: integer arguments five and six
are passed in `t0`/`t1`, not caller-stack slots. The runtime-injector package
loads with 2 targets, 3 groups, 8 patches, 50 total fragments including the
numeric formatter, and 21 guarded edits. The combined Localization pin is
`430D8B6EC42EC0EC2322DD53657C21655EBA797E24CA0A7B097B8C4A2D10D266`,
with the user-owned bypass value preserved at `1`.

The normal `na2` workflow built and promoted Current CRC `12369AA2`, build
record `@logs/na2/builds/20260728_203916_483_pid40912`. The user manually
regressed Pause Controls, Quit confirmations, Special Controls, Practice
explanations, Controls, and both title callers and reported `no diff`.

After that explicit acceptance, permanent coverage was updated to protect the
relocatable C contract, documented EE `t0`/`t1` entry ABI, canonical hooks,
native callbacks, and required fragment dependency chains without freezing
compiler hashes or obsolete instruction layouts. Focused Font C/injector tests
pass 11/11 and the full patcher suite passes 201/201.

### Collapsed step 2 — accepted

The independent Ninja Song ASCII-number helper is now compiled from
`font_numeric.c`. It retains the accepted public symbol and all five guarded
BTL call-site hooks. The C entry consumes the original EE EABI arguments
unchanged: value in `a1`, width in `a2`, destination in `a3`, and the fifth
integer padding-mode argument in `t0`. Its accepted modes remain
space-padded, unpadded, and zero-padded.

Only the game-native variadic call remains an assembly ABI bridge. The
20-byte `localization.font.c.numeric_format_decimal` fragment converts the C
two-argument callback into
`sprintf(destination, 0x006042D3 /* "%d" */, value)` and tail-calls native
`0x0017BCA0`. The compiled C fragment is 184 bytes; together they form a
204-byte numeric blob with SHA-256
`8043B1393F6D901FC91DF6BB4BFC8AB4D2800F7FD9E17CA4EEE2C4C34992A9F6`.
The combined Localization pin is
`F0E4F4A1E0E05504EE3C74E9AECB9C5673D2E683130534F2132B24D33810FD6D`,
with the user-owned bypass value preserved at `1`.

Manual object disassembly confirms the fifth argument is captured from `t0`,
the destination and width survive the native callback, the bounded 16-byte
temporary cannot overlap the compiler's saved-register area, the return value
remains the native decimal length, and the only C relocation targets the
explicit ABI bridge. The normal build promoted Current CRC `12369A62`; the user
manually regressed the supplied Ninja Song ss2–ss5 cases and reported that the
result is good. Permanent coverage added after that acceptance protects the
public symbol, deterministic relocatable C output, fifth-argument `t0`
contract, native formatting bridge, five guarded callers, and accepted padding
modes without freezing the complete compiler output.

The remainder of the approved migration is consolidated into one boundary.
Save/Load and Battle Settings now join Ninja Song in `font_numeric.c`.
Save/Load's six native blocks retain only argument setup, symbolic calls, and
the required `v0`-to-`s6` year lifetime; Battle Settings retains only its
ordinary-value argument setup and symbolic call. C owns EU date order,
two-digit fields, the signed 99-hour cap, and ordinary Battle Settings decimal
formatting. The adjacent Battle Settings value-100 infinity branch remains
untouched.

Production inputs no longer live under `scripts/research/`: C sources reside
under `na2_patcher/features/localization/runtime_injector/sources/`, the
generic EE object extractor resides in `na2_patcher/payload_builder/`, and the
deterministic generator resides in `scripts/localization/`. The superseded
Save/Load and Battle Settings in-place assembly generators were removed.
Retained assembly is limited to native renderer/displaced-instruction ABI
shims, the two typed-to-variadic `sprintf` bridges, and minimal register setup
at guarded hooks.

The consolidated numeric object exports Ninja Song, Save/Load day/two-digit/
year/hour, and Battle Settings entries. Together with the two native bridges,
it produces a 456-byte numeric blob, SHA-256
`C82F4BD35793FC8866D961912F35B50F39D11124745ECA13F6C98AA6441A4341`.
Manual EE disassembly confirms the first Save/Load entry returns the loaded
year after the `%02d` call, the hour entry implements signed
`value < 100 ? value : 99`, and every typed wrapper relocates only to its
declared native-format bridge. The runtime package contains 4 groups,
10 patches, 57 fragments, and 28 guarded edits. Its combined Localization pin
is `05C66C7858830DE7356F3C69B22E76786C841FD226A06E0C1BEB81D7EA867A44`,
with the user-owned bypass value preserved at `1`. Runtime regression remains
the user's next boundary. Deterministic regeneration passes and the full
patcher suite passes 201/201.

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

### Historical v1 NUN5 auto-adjust experiment - retired

The July 24-25 implementation reproduced NUN5's fit decision as well as its
scaling, without redirecting NA2 to a layout-incompatible NUN5 function.
The implementation is retired and recoverable from Git history. Its reusable
findings remain canonical inputs to the live v2 per-caller renderer:

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
  native secondary font, guarded hook-site edits, and independent Character
  Select modal alignment.
  `na2_patcher/features/localization/runtime_injector/` contains the live v2
  metric, fit, scale, layout, and numeric fragments. All remain covered by the
  current Localization aggregate feature pin.
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
