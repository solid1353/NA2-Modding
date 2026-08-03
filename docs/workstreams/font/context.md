# Font context

Consolidated on 2026-08-01 from the former Font plan and retired layout-parity
epic. This document contains durable workstream context and concise outcome
summaries. Exact offsets, call paths, geometry, hashes, provenance, negative
trials, and per-screen evidence remain in the linked knowledge documents.

## Objective

Make NA2 English text fit and align as cleanly as the official NUN5 reference
while preserving NA2's native renderer behavior, source-file structure, and
unrelated UI paths.

The accepted baseline combines a native 14x20 NUN5-derived secondary font with
call-local measurement, fitting, wrapping, positioning, and renderer-state
restoration. Raster appearance and layout geometry remain separate so changing
one cannot silently invalidate the other.

## Current state

- The 2026-08-02 Font 3 global layout overhaul is implemented in the shared
  v2 C core and caller-family manifests. The retained global selected-style
  dispatcher is the foundation; structural families provide bounded
  container-specific geometry on top. This replaces individual row tuning and
  does not edit displayed strings.
- The native 14x20 NUN5-derived font is accepted and enabled.
- The shared v2 C renderer/session architecture is the retained behavioral
  baseline; the July v1 renderer is retired.
- The resident payload now uses a fixed `0x00940100` heap reservation boundary.
  Payload-size changes within that envelope no longer relocate the game heap;
  the `font/heap_stability` E2E suite proves normal and `+32`-byte builds produce
  identical non-ignored screenshots.
- Controls, Command Chart, Pause Controls, Character Select option/modal paths,
  Collection exit confirmation, Movie lists, Jutsu selector, Settings page
  templates, Ninja Song numeric output, and Save/Load numeric formatting have
  accepted or runtime-proven boundaries recorded in knowledge.
- The current 49-screen main replay covers confirmation modals, Controls,
  Settings, Practice explanations, Pause, Character Select, and Jutsu.
  Severity-first review found no remaining large Font defect in those cases.
  Its Save confirmation frames represent a retired absolute-position candidate
  and are not evidence for the current native-position behavior.
- The separate final replay proves Sakura and legacy-character Collection
  families across Figure, Ultimate Jutsu, character Music, and Movie. Their
  shared widths, wraps, and header origins have no remaining large Font defect.
- Ninja arithmetic was runtime-proven by the earlier fresh ss3 injection and
  redraws continuously. The final replay desynchronized into Character Select
  before its six objective captures, so only final-build objective runtime
  verification remains unclaimed.
- The secondary metric decoder C cutover retained an `approved_for_test`
  boundary in the old record; verify current live status before selecting new
  work from it.
- The current `TASKS.md` Bugs list has no Font-labelled entry. This is context,
  not task selection or authorization.

## Architecture

- Canonical Font C sources live under `src/localization/font/`.
- The shared core owns proportional measurement, ordinary spacing,
  shrink-only fitting, wrapping, alignment, and renderer-state restoration.
- Thin caller-family adapters supply each native ABI, box geometry, alignment,
  callback, and proven local exception. They do not duplicate core formulas.
- NA2 continues drawing glyphs, colors, shadows, markup, and controller icons
  through its native renderer and callbacks.
- Boot ELF and overlay files receive only guarded call-site hooks,
  displaced-instruction handling, and genuinely local static coordinates.
- The runtime-injector declares compiled C fragments and retained ABI/data
  shims. The payload builder assigns final addresses in expandable
  `PRG/228.BIN`.
- Checked-in aggregate Font MIPS payload blobs are retired. The deterministic
  generator remains an independent reconstruction/verifier rather than a
  production blob writer.

Measurement and drawing use the same proportional metrics and formulas.
Fitting is shrink-only: `min(1, box_width / measured_width)`. One-line rows
retain native glyph geometry. Multiline overrides apply only after a real wrap,
and wrapping alone does not justify vertical squeezing.

## Accepted font and renderer baseline

### Font assets

The accepted donor imports NUN5 14x20 geometry and metrics only for
same-semantic English cells, reconstructs unsupported punctuation from clean
NA2, preserves complete printable-ASCII coverage and NA2 GF4C palette
semantics, and confines the shortened secondary atlas to its own parser path.
The user accepted the font itself as almost pixel-for-pixel.

### Shared renderer

The retained v2 implementation replaced the behavioral hand-written MIPS in
stages with ordinary EE C while preserving exported symbols, native ABI shims,
session layout, caller hooks, and runtime behavior. Retained assembly is limited
to unavoidable native-renderer, displaced-instruction, register-capture, and
typed-to-variadic formatting bridges.

The call-local session saves the previous renderer/session state, measures and
fits the requested text, publishes its state only around the native callback,
then restores everything through one cleanup path. A null session reproduces
native NA2 behavior, and nested callbacks restore the prior session.

### Numeric rendering

Ninja Song, Save/Load, and ordinary Battle Settings numeric behavior are
compiled from canonical C. The accepted implementation preserves native
padding modes, EU date order, two-digit fields, the signed 99-hour cap, and the
separate Battle Settings infinity branch. A rejected non-linking hook variant
caused the Load-screen failure; the corrected linking calls were user-verified.

## Retired layout-parity epic outcomes

The 2026-07-27 through 2026-07-31 epic is retired and retains no report grids.
Its accepted or useful outcomes are:

- **Character Select return confirmation:** the lower body and top selector
  were isolated and user-verified with matched NUN5 geometry.
- **Character Select option lists:** ordinary player-mode rows use the same
  bounded metric session as the selected row; Linked Mode uses one shared row
  formula. The user accepted both.
- **Battle Settings Jutsu selector:** fitting one-line and wrapped two-line rows
  share the width correction but retain separate vertical behavior. The user
  verified the whole-Font hot-reload result; no separate integrated-ISO claim
  was made.
- **Collection exit confirmation:** both live body consumers and the bounded
  Yes/No scope were corrected and user-verified.
- **Collection Movie list:** one-line rows remain native; only measured
  overflow wraps. The exact integrated result was user-verified.
- **Collection character move lists:** the corrected candidate removed an
  unintended glyph-height path and preserved accepted wrapping geometry. The
  target appearance was accepted, while exact integrated ss9/ss10 confirmation
  remained outstanding.

The main retained input batch is under
`work/Font/inputs/sstates/batches/2026-07-30-ss1-10/`. Replacement Jutsu and
supplemental regression batches remain under the adjacent dated input trees
with their provenance records.

## Deferred work

- A small residual raster-appearance mismatch against NUN5 remains separately
  scoped from accepted layout behavior.
- Obtain one synchronized final-build Ninja Song objective capture before
  promoting that runtime boundary from static verification.
- Before acting on any old pending-review label above, refresh live code,
  knowledge, and user instructions; these records do not select work.

## Runtime comparison lifecycle

- Compare official NUN5 on the left with current NA2.28 on the right under
  matching game and emulator conditions.
- Check representative short, fitting, overflowing, selected, ordinary,
  one-line, and multiline rows for every changed caller family.
- Validate actual visible bounds, origin, breaks, line spacing, glyph height,
  and native style; successful compilation or hook application is not a visual
  result.
- Recheck previously accepted families after any shared-core change.
- Runtime-injected output is candidate evidence until its required integrated
  boundary is explicitly verified.
- Active inputs and runtime artifacts remain task-owned. Confirmed reusable
  findings are promoted to knowledge; disposable grids, logs, and workers are
  removed after their evidence is no longer needed.

Current execution commands, PCSX2 ownership, ISO isolation, validation, Git,
and epic behavior always come from live repository policies, not this context.

## Retired approaches and cleanup

- The monolithic July v1 renderer, its declarations, and disabled selections
  were removed; its useful formulas and failures remain in knowledge and Git
  history.
- Blind GF4/GF4C swaps, global tracking changes, global descriptor-height
  edits, threshold-only Controls fitting, and complete NUN5-renderer transplant
  were rejected.
- The Save confirmation absolute-position adapter was retired because NA2 and
  NUN5 use different modal dimensions; NA2 now retains its native positions.
- Aggregate resident Font blobs and superseded assembly-producing research
  scripts were removed after the composition-time C boundary was proven.
- Accepted epic grids were deleted after their reusable results were promoted.

## Detailed knowledge

- [Font renderer and asset findings](../../knowledge/localization/font/README.md)
- [2026-07-24 paired savestate analysis](../../knowledge/localization/font/savestate_analysis_2026-07-24.md)
