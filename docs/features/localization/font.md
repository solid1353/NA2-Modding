# Native NUN5-derived Font

## Package baseline

This package starts from hash-verified clean NA2 and official NUN5 inputs. It
does not use `font_m01`, v22/v23, the rejected GF4C palette swap, or a whole
GF4 replacement as an implementation parent. The accepted build changes
`DATA/GF4.BIN` and `SLPS_258.37` without changing either file's size;
`DATA/GF4C.BIN` remains byte-identical to clean NA2.

## Core glyph and numeric components

The accepted native glyph component, independent Character Select modal
alignment, call-local numeric formatters, and reviewed v2 caller families are
enabled by default when Localization is enabled. The historical v1
autofit/layout implementation was removed after the independent v2
reimplementation made all ten of its resident fragments unreachable:

- `font_glyphs_native` installs native 14x20 NUN5 raster geometry and metrics
  for same-semantic English cells. Unsupported printable punctuation is
  reconstructed from clean NA2, preserving 95/95 printable-ASCII coverage.
  The shortened 123-cell secondary atlas is locally guarded. Its metric rows
  are packed into the value words of empty primary-map slots. Composition-time
  C in `src/localization/font/font_glyph_metrics.c` decodes them for both
  measurement and drawing; two guarded boot-ELF hooks provide the live
  context/register ABI and rejoin the native cleanup paths. The normal glyph
  emitter keeps descriptor width on the primary/fullwidth path and uses
  descriptor height only for the secondary quad, restoring its intended
  24x28 presentation without widening it.
- `font_layout_character_modal` loads independently measured X positions for the
  five character-select `Back to Game Mode Screen` rows while retaining the
  accepted local Y behavior. Its selected-path compensation prevents the
  shadow draw from shifting visible ink.
- `font_numeric_save_load` routes only the six Save/Load numeric blocks
  through compiled C and keeps their call sites as argument setup plus
  symbolic hooks. The first C entry returns the record's year for the proven
  `s6` lifetime while rendering day; later entries preserve EU `DD/MM/YYYY`,
  two-digit time, timer math, and NUN5's 99-hour cap. The Save/Load-only ASCII
  colon remains the local declarative `font_numeric_save_load_separator`
  patch.
- `font_numeric_battle_settings` routes only the ordinary Battle Settings
  Time branch through the compiled C decimal entry. Its adjacent exact guard
  preserves the separate value-100 infinity path and leaves the other five
  rows and every unrelated numeric caller unchanged.
- `font_numeric_ninja_song` redirects exactly five guarded BTL formatter
  calls shared by the supplied ss2–ss5 Ninja Song screens to one resident
  ASCII-decimal helper. It preserves NUN5's right-aligned widths 3, 3, 5, and
  4 plus the unpadded inline mode. The reachable multiplication separator
  remains canonical mapping T2195's ASCII `" * "` and is guarded rather than
  rewritten by this patch. The user built and tested the integrated ss2–ss5
  result and declared the task done; unseen decimal values use these same
  guarded calls rather than separate string mappings.

## v2 layout core and selected style

The removed v1 implementation consisted of nine relocatable code fragments,
one linked metric table, eight disabled runtime hook edits, and four disabled
binary tracking/alignment edits. Although its hooks were disabled, the generic
injector still linked all declared fragments whenever any active resident edit
existed. Retiring the declarations and generated blob removes 1,856 aligned
bytes from `PRG/228.BIN`. Git history and the [Font knowledge index](../../knowledge/localization/font/README.md)
route to its formulas, validation, and negative integration result.

An independent `localization.font.v2.*` implementation is enabled for the
accepted Controls family and does not target any retained symbol above. Its
separate generated
resident asset contains the accepted 95-entry width table, exact
printable-ASCII measurement with explicit `<br>`/newline recognition,
shrink-only scale preparation, horizontal/vertical box positioning, and five
renderer hooks guarded by one zero-initialized active-session pointer. Every
null-session branch restores the temporary `v0`/`v1` use and executes the
displaced NA2 instructions before resuming, so selecting the core alone cannot
alter a screen. Its generic call adapter prepares one caller-owned 104-byte
session, publishes it only around one native callback, and restores the prior
session pointer, renderer tracking, horizontal scale and callback result
through one cleanup path.

The separate `font_layout_global_selected_style` patch changes NA2's complete
gray-shadow selected-renderer family rather than compensating individual
screens. A function-level scan of clean `SLPS_258.37`, `ADV.BIN`, `BTL.BIN`,
and `ETC.BIN` finds six implementations, all in the boot ELF: central
state-aware runtime `0x00379040`, central caller-colored runtime `0x00379150`,
fixed two-choice runtime `0x00379C30`, and record-based runtimes `0x001E6060`,
`0x001E6370`, and `0x001E6CE0`. No overlay defines another implementation.

All six use one rule: the shadow is drawn at `(x+1,y+2)` and the colored glyph
at the ordinary `(x,y)` origin. The two central primitives retain their guarded
files `0x279168` and `0x279278` and share the 48-byte `f21/f20` adapter. Seven
gray calls inside the three record-based components share one 56-byte adapter
that moves the pointed record before its native shadow draw; each untouched
native `(-1,-2)` step restores that record before the colored draw. The fixed
two-choice primitive at file `0x279D30` delegates its selected row to the
corrected central primitive and its other row to the native ordinary
primitive, retaining its context, record pointers, draw order, and colors.
No text bytes, scales, or screen-specific coordinates are changed. All
screen-specific Font patches remain temporarily disabled for isolated user
verification.

## Caller-specific layout layers

### Control Settings

The first thin caller layer, `font_layout_controls`, redirects the shared
first-eight-label call in Control Settings `FUN_003885b0`. It builds NUN5's 128-unit box, keeps
fitting labels at scale `1`, applies `128 / 178` to
`Ultimate Jutsu Prep`, derives NUN5's exact box left as the native NA2 caller
center minus `64`, and converts the prepared left edge back to NA2's
centered-renderer ABI. The first eight labels and required v2 core are
runtime-proven from the matched review and real title-to-Load transition. Its
ninth call at ELF file `0x2888D4` draws the unrelated vibration row and remains
native.

`font_layout_on_off_context` now contains only the user-verified Practice
Settings split. Its three BTL row-table pointers at files `0x20B498`,
`0x20B49C`, and `0x20B4A0` select the existing title-case table at runtime
`0x00604658`, preserving the original Off-then-On selector order. Canonical
mappings T1956/T1957 convert that table's clean Shift-JIS `オフ`/`オン` slots
to ASCII `Off`/`On`.

### Practice and Special Controls selector

Special Controls uses distinct fullwidth Shift-JIS slots at SLPS files
`0x505AF0`/`0x505AF8`, proven by the remade ss1 draw telemetry. Canonical
mappings T2203/T2204 convert them to official NUN5 ASCII `ON`/`OFF` donors.
The fresh mapping-only capture proves the NA2 and NUN5 list records already
share X/Y, row-step, count, selection, and owner geometry. Placement is
therefore handled by extending the already-installed selected/unselected
quit-confirmation adapters at ELF files `0x283914` and `0x283A60`: when the
quit scope is inactive, exact runtime text pointers `0x006059F0` and
`0x006059F8` select local coordinates `(66,31)` and `(59,49)`. Every other
caller remains a native tail call, so this adds no overlapping hook and does
not alter the accepted quit-confirmation behavior.

The 2026-08-01 replacement ss1 pair shows that the mapped Current `ON` and
`OFF` ink was still two pixels shorter than NUN5 to the right and bottom. The
same two hooks now apply geometry by native draw state, never by row: selected
text adds local X `1.0` and uses horizontal scale `1.02`, ordinary text uses
scale `1.01`, and both use glyph height `26` inside one 104-by-20 one-line box.
Both exact pointers are accepted by both paths, so the formulas remain valid
when selection swaps. The adapters change only scoped font state and restore it
after the native callback; they do not write displayed text. The guarded hidden
worker comparison aligns the selected and ordinary core-glyph bounds with NUN5;
integrated user acceptance remains pending.

### Command Chart and Practice titles

The second thin caller layer, `font_layout_titles`, replaces only two guarded BTL
draw calls: Command Chart file `0x1C6A28` and Practice file `0x1C4B98`.
Two explicit mode entrypoints tail-call one configurable title adapter, which
uses the proven 288-by-20 and 352-by-20 boxes respectively and delegates
measurement, shrink-only scale and restoration to the same v2 core. The
adapter returns through NA2's native `0x00382310` draw ABI. This title layer
does not select Practice explanations or either subsequent Command Chart
auxiliary-string call; each remains a separate caller family. The title layer
is enabled and runtime-proven in isolated matched Command Chart and
Practice captures. The user accepted the Command Chart result on 2026-07-27;
the Practice title result remains agent-validated and awaiting acceptance.

### Pause Controls

The dedicated Pause Controls layer, `font_layout_pause_controls`, replaces the
normal list-row call at BTL file `0x1C97D8` and the selected list-row call at
`0x1C9794`. Their clean guards are the native `jal 0x00382470` and
`jal 0x003827A0` instructions plus NOP delay slots. Both adapters use the same
shared v2 shrink-only formula inside a 216-by-20 single-line box and move the
native Y origin upward four units. The selected adapter preserves the native
red style, bridges the integer-coordinate ABI, and applies the previously
proven two-unit selected-helper X compensation so selection does not move the
row. The normal ss2 state and corrected selected ss3 state are user-verified,
so the layer is `runtime_proven`. It does not restore the retired v1
`font_layout_wrappers` multiplexer or select any ss4 confirmation-body or
Yes/No call.

### Battle and Practice quit confirmation

The dedicated ss4 layer, `font_layout_quit_confirmation`, authors no newline in
canonical translation mappings. Its exact BTL list call at file `0x1C4048`
publishes a transient scope only around native `0x00383600`; the selected and
unselected calls inside that helper are redirected at ELF files `0x283914`
and `0x283A60`. They map Yes and No while that scope is active; outside it,
both hooks recognize both exact Special Controls ON/OFF pointers. ON therefore
retains local `(66,31)` and OFF retains `(59,49)` when selection swaps which
helper renders each row; all other rows tail-call native behavior. The exact
body call at BTL file
`0x1C407C` copies at most 255 bytes to the adapter stack, greedily wraps that
copy inside a 420-by-40 two-line box, and draws from X `48`, Y `12`.
Neither the formatted source buffer nor canonical mappings receive newline
bytes. Fresh user pairs across all four Battle/Practice and Game
Mode/Character Select combinations prove that this first X value starts every
Current body at screenshot X `101`, versus NUN5 X `72`, while Y already
matches. The shared local X is therefore corrected to `19` with Y `12`
unchanged. String Translation separately owns the exposed wrong dynamic
content and corrected it in `277ecc1`. The user verified the combined
fresh-build result across all four Battle/Practice and Game Mode/Character
Select combinations on 2026-07-27, so the layer is `runtime_proven`.

### Mode Select confirmation

The separate `font_layout_mode_select_confirmation` caller layer reuses the
same C-owned scope, coordinate map, and native body adapter without adding
another renderer engine. Mode Select `FUN_00385C00` draws the confirmation
body through `FUN_003825B0` at boot-ELF file `0x285E68` / runtime
`0x00385D68`, then draws the live choice object `+0xCC` through
`FUN_00383600` at file `0x285E98` / runtime `0x00385D98`. The body call has
clean guard `6C090E0C00000000`; the choice call has clean guard
`800D0E0C00000000`.

The first hook routes only the exact `Return to Title Screen?` body through a
420-by-40 single-line box at local `(24,12)`. This changes native Y `16` to
`12` and activates the accepted tracking-zero/plain-space renderer state
without scaling glyphs or publishing Collection choice scope. The second hook
retains `localization.font.v2.quit_choices_scope`, whose top Yes/No result was
user-verified on 2026-07-29. Fresh native-resolution NUN5 and runtime-injected
NA2 body captures have identical black-ink bounds X `194..909`, Y
`1042..1078`. The user verified the exact live body result on 2026-07-31, so
the complete Mode Select confirmation layer is `runtime_proven`.

### Collection confirmation

The separate `font_layout_collection_confirmation` layer owns three clean ETC
calls. Files `0x12680` and `0x148C8` are the two body consumers and both route
through `localization.font.v2.collection_body_adapter`; file `0x126A0` scopes
only the complete choice object through
`localization.font.v2.quit_choices_scope`. Live tracing proved the later
render-state body call at runtime `0x006C87C8` produces the visible prompt,
while changing only the earlier duplicate leaves it unchanged. The shared
adapter uses the native UI-draw ABI, local `(24.8,12)`, native horizontal
scale, and a 400-by-60 two-line box. Collection's native Yes/No source Y values
24/56 map to Collection-local Yes `(64.2,29.85)` and No `(68.1,48.2)`.
Native-resolution comparison matches NUN5's black bounds exactly and its red
bounds within one pixel; the user verified the live result on 2026-07-31.
Every unrelated ETC body/list caller remains native.

### Collection lists

The separate `font_layout_collection_lists` layer owns the shared Collection
row draw in ETC `FUN_006B4D30`, file `0xFD8` (clean guard
`10E40D0C00000000`). Its C entry accepts only the exact Movie-title range and
the two verified character-detail pointer families; every unrelated row
immediately executes the displaced native draw. Movie and relationship titles
use NUN5's 192-by-32 box, while the narrower character-move list uses its
152-by-32 box. All selected rows are rendered at native X and native Y minus
10. The list owner keeps fixed row cadence, and each transient line is drawn
separately at a 16-unit interval because NA2's native newline path advances 25
units on these screens. Replacement-batch ss8-ss10 proves the exact NUN5
breaks and origins for every visible long title while short titles, selection
style, and unrelated ETC rows remain native. The layer is
`approved_for_test` pending explicit user acceptance.

### Character Select modal

The `font_layout_character_select_modal` layer owns four exact main-ELF
callers rather than broad modal behavior. Files `0x2BC984` and `0x2BC9BC`
route only the selected and ordinary five-row entries through the same
240-unit NUN5-metric session and five-local-unit X correction. Their distinct
native callbacks retain the red selected style and black ordinary style, while
the accepted row table continues to own every Y coordinate. File `0x2BCB54`
routes only the return-confirmation body through the accepted
secondary-renderer 368-by-24 box. Replacement-batch ss1 isolates the complete
top Yes/No list at file `0x2BCAAC`, clean guard `800D0E0C00000000`; that call reuses
`localization.font.v2.quit_choices_scope`, so its rows receive the same
relative modal offsets as NUN5 without adding another renderer formula. The
lower body is user-accepted and the top selector is user-verified.
Supplemental ss1 proves the ordinary-row session preserves all native Y bounds
while matching NUN5 horizontal bounds. The refreshed five-row result remains
`approved_for_test` pending explicit user acceptance. Linked Mode and every
unrelated main-ELF list/body caller stay isolated.

### Linked Mode

The declarative `font_layout_linked_mode_modal` layer owns only main-ELF
`FUN_003B8F40`, the center-screen Linked Mode selector. It changes the title
constant at file `0x2B90E0` from local Y `12` to `8`, the choice interval at
file `0x2B9190` from `26` to `20`, and the base at file `0x2B91A4` from `48`
to `46`. No selected-only delay-slot compensation remains. Supplemental
Manual-selected ss2 gives exact NUN5/current Y bounds for the title, selected
Manual, and ordinary Auto; the native draw calls, text pointers, X geometry,
and every other modal remain untouched. The layer is `approved_for_test`
pending explicit user acceptance.

### Jutsu selector

The separate `font_layout_jutsu_selector` layer owns only the final Jutsu-row
text call at BTL file `0x90DC`. Its C entry first applies the native 186-unit
word-wrap measurement to a bounded copy. A one-line result immediately invokes
the exact displaced native renderer with the original text and unchanged
renderer state. Only a result that actually wraps enters the 186-by-32,
two-line session with its scoped 16-unit line advance and 20-unit secondary
glyph bottom. Supplemental ss3 matches the selected two-line NUN5 bounds while
the short `Great Ball Rasengan` row retains its exact native baseline bounds.
The layer is enabled and `approved_for_test`; explicit user acceptance remains
pending.

### Special Controls explanatory body

The separate `font_layout_special_controls_body` layer completes the explanatory
block on the same ss1 Special Controls screen. Exact telemetry identifies only
the native UI-body call at BTL file `0x1C3D38` (runtime `0x00877C38`, clean
guard `jal 0x003825B0` plus NOP). NUN5 retains T1880 as one unbroken source
string, copies it to a transient buffer, and wraps it before `for` inside a
400-by-60 box with a two-line limit. The dedicated adapter reproduces that
draw-time behavior at local X `24`, Y `12`, with 20-unit line height by
parameterizing the same v2 body builder used by the accepted quit modal. It
does not hook the shared UI renderer, add a newline to T1880, or alter another
body caller. An exact-guarded converted ss1 capture matches NUN5's break and
line origins, so the layer is `runtime_proven`; user acceptance of the whole
ss1 case remains separate.

### Practice explanations

The third thin caller layer, `font_layout_practice_explanations`, replaces only the
Practice per-token explanation loop at BTL file `0x1C4BA0`. It assembles one
bounded 512-byte mixed text/tag buffer, applies unlimited word wrapping inside
the proven 364-by-48 box, and installs call-local metric and draw callbacks for
the native 13-token controller-icon table. Matched supplied slots 2-7 prove
NUN5-equivalent one-, two-, and three-line wrapping, line spacing, placement,
and D-pad, face, plus, and shoulder icons. Controls and Command Chart
regressions remain intact. This layer is enabled and runtime-proven;
the grouped Practice grids still await user acceptance.

## Compiled-C migrations

The accepted step-1 C migration preserves those public symbols,
hooks, constants, and patch selections while compiling all remaining
behavioral layout policy—Pause sessions, Quit scope and coordinate mapping,
native measurement/wrapping, both body adapters, and Practice text/icon
flow—from `font_v2_core.c`. Assembly is retained only for native renderer tail
calls, live-register entry capture, the scoped native Quit-list call, and the
five displaced renderer hooks. The generated v2 asset is 5,924 bytes with
SHA-256
`7F021178787EA9A845EED8AE348B731345C3459BF1AF29D48CA02B26E84D5F28`.
The user manually regressed every affected caller on Current CRC `12369AA2`
and reported `no diff`. Permanent coverage added after that acceptance protects
the documented EE entry ABI and required symbolic dependency chains without
freezing compiler hashes or obsolete instruction layouts.

The accepted step-2 numeric migration preserves the
`localization.font.ninja_song_ascii_number` symbol and all five Ninja Song BTL
hooks while compiling padding and copying policy from `font_numeric.c`. Its
only assembly fragment is a 20-byte bridge to NA2's native
`sprintf(destination, "%d", value)` ABI. The 184-byte C fragment and bridge
form a 204-byte asset with SHA-256
`8043B1393F6D901FC91DF6BB4BFC8AB4D2800F7FD9E17CA4EEE2C4C34992A9F6`.
The user manually accepted the Ninja Song ss2–ss5 result on Current CRC
`12369A62`; permanent coverage now protects its public symbol, EE `t0`
argument, native formatting bridge, guarded callers, and padding modes.

The same production `font_numeric.c` now owns the six accepted Save/Load
date/time fields and ordinary Battle Settings Time values. The first
consolidated build incorrectly used non-linking `j26` hooks and broke Load;
the corrected seven call sites use `jal26`, preserving the native return path.
After a fresh corrected build, the user verified Load, Save, the ordinary
Battle Settings value, and its separate 100/infinity path. Both compiled-C
families are runtime-proven, and permanent coverage protects the linking-call
contract independently of payload addresses.

## Composition and verification

The live v2 auto-fit and layout components require `font_glyphs_native` because
their positions and fit decisions are tuned to its metrics. They otherwise
remain independently selectable through their patch rows. Setting a resident
patch's `enabled=0`, or setting its owning group's `enabled=0`, removes its
hooks from normal composition; the current runtime-injector contract still
links all declared fragments whenever any resident Font patch remains active,
so obsolete implementations must not remain as declarations.
The rejected shared `font_vertical_quad_height` component was removed from
executable inputs because it stretched both axes to 28x28. Its exact negative result remains in
[Font experiments](../../knowledge/localization/font/experiments.md) and Git history;
the accepted secondary-only height helper is part of `font_glyphs_native`.

Matched Controls, Practice, Save/Load, and character-modal captures established
the historical rendering behavior before its resident relocation. The final
guarded Controls capture retained the accepted horizontal metrics, spacing,
bearings, and shrink-only fit while reducing the median height and center-Y
deltas against NUN5 to zero. The user accepted the font itself as almost
pixel-for-pixel. The user also accepted the exact v2 Controls family after its
matched comparison and title-to-Load regression. Fullwidth Shift-JIS Save/Load digits use a different glyph path
and were not a halfwidth-Latin parity target; the independent Save/Load
formatter patch now emits those six fields as ASCII instead. The user later
rejected the combined autofit/layout selection as unstable. The font itself,
independent Character Select modal alignment, call-local numeric formatters,
and the accepted v2 Controls/core pair are now enabled while the remaining
layout families are rebuilt sequentially. The isolated v2 title layer is also
enabled and runtime-proven: Command Chart is user-accepted, while Practice
title acceptance remains pending.

`scripts/research/localization/generate_font_assets.py` deterministically
regenerates and verifies the two native glyph/metric data blobs from configured
`@source_na2/` and `@source_nun5/` inputs. Executable metric behavior is
compiled from C during composition and is not stored as an asset.
`scripts/research/localization/verify_font_renderer.py` deterministically
reconstructs the accepted v2 renderer, numeric formatter, and retained ABI-shim
fragments as an independent verifier. Normal composition does not persist its
aggregate outputs: `catalog/implementation/injections.json` payload
declarations own the three canonical C
units under `src/localization/font/`, compile them with the pinned EE toolchain, and
converts their sections and relocations directly into normalized fragments.
Static ABI/data fragments remain in their owning injection payload; the shared payload
builder links both kinds into the final `228.BIN`. The only retained generated
MIPS in the numeric layer is the pair of typed-to-variadic native `sprintf`
bridges and the minimal call-site register setup.
ABI and purpose metadata lives on the owning emitted fragment or static adapter
and is used by `scripts/injection/build.py` for development entry selection.
`scripts/research/localization/generate_ninja_song_ascii_numbers.py`
deterministically verifies the five shared clean-BTL formatter calls, emits
their symbolic redirects, and guards the canonical ASCII multiplication
mapping. Its resident helper is declared by the canonical runtime-injector
package and independently reconstructed by
`scripts/research/localization/verify_font_renderer.py`.
Exact static and symbolic hooks, guards, replacement templates, and reasons are
recorded in `catalog/implementation/edits.json` and
`catalog/implementation/injections.json`; the Font knowledge
[index](../../knowledge/localization/font/README.md) routes to confirmed evidence
and negative results.
