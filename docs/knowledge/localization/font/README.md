# Font renderer and asset findings

This directory preserves confirmed visual, structural, and byte-level Font
evidence in this file and the focused matched-savestate report. Raw schema-v1
replicas of retired m01/v22/v23 packages and the rejected palette experiment
were removed after their reusable conclusions were consolidated here. They
remain recoverable from Git commit `55d1163`; they are not implementation
parents or active patch inputs.

## Current savestate comparison

The [2026-07-24 matched savestate analysis](savestate_analysis_2026-07-24.md)
compares ten NUN5/NA2 pairs and separates raster/metric, call-local position,
generic-modal, and missing-wrap defects. It confirms that Control Settings is
the only boxed-fit path proven correct by this sample and that multiple other
callers require layout behavior that a font-asset refinement alone cannot
provide.

## 2026-07-25 stage-by-stage autofit reset

The user retained the accepted native font and generic runtime-injector
infrastructure but rejected the combined July 24-25 autofit/layout selection as
unstable. These five module/patch rows were disabled at that boundary:

- binary `font_renderer_metrics`;
- binary `font_controls_auto_fit`;
- resident `font_renderer_metrics`;
- resident `font_controls_auto_fit`;
- resident `font_layout_wrappers`.

`font_glyphs_native` remains enabled. Binary `font_layout_character_modal` also remains
enabled because it is the independently reviewed Character Select `Back to
Game Mode Screen` row alignment, not the Save/Load lower modal described
below. Their confirmed formulas and rejected integration behavior remained
evidence for the independent v2 reimplementation rather than an enabled
baseline.

### 2026-07-28 v1 executable retirement

After the v2 caller families became the only active implementation, a complete
symbol-relocation closure from all enabled resident hook roots reached all 37
v2 fragments and the numeric formatter, but none of the ten v1 fragments.
The generic runtime injector validates all declarations and contributes every
declared fragment whenever any resident edit is active, so the unreachable
1,847-byte v1 blob was still physically linked into each current `228.BIN`.
An in-memory payload build measured 1,856 bytes of actual linked size after
alignment.

The obsolete v1 fragments, relocations, disabled patch/edit rows, generated
blob, generator-only assembly builders, and v1-specific tests were therefore
removed. The paired binary-patcher tracking/alignment rows were removed with
them. Git history is the executable archive; the detailed findings below
remain canonical historical evidence. The live v2 renderer, numeric formatter,
native glyph data, and independent binary patches were unchanged.

The user identified `ss9` as the current broken Save/Load modal. Its protected
state was copied read-only from
`@pcsx2_stable/sstates/SLOP-NA228 (D61F4C01).09.p2s` to the Font-owned input
tree. The state SHA-256 is
`5EE0E06A4B31EDD2F81F77A10B447C504620864DD1D5D9A8D410A940B65E1335`;
the embedded screenshot SHA-256 is
`BAED2975F367ABF0D0C36272159FA94E64F794BD2492B37E109CE232F64BFCD4`.
No matching NUN5 slot-9 state was supplied, so the comparison uses the retained
640x480 NUN5 Save/Load capture with SHA-256
`55626DB58BB0316F2502A20B2B825AABD25C94D343A427242F15C12A3343B2DC`.
Exact task-owned paths and source provenance are recorded in
`work/Font/inputs/sstates/autofit_positions/modal/provenance.json`; the
comparison grid is retained as the task artifact
`work/Font/artifacts/autofit_positions/save_load/pre_reset-slot-09.png`.

At 640x480, NUN5's lower-panel orange borders occupy `y=289..293` and
`y=460..464`; current NA2 uses `y=296..299` and `y=449..452`. NUN5's
instruction ink bounds are `(41,318)-(341,331)`, while current NA2 uses
`(61,332)-(361,345)`: 20 pixels farther right and 14 pixels lower. NUN5's
action row occupies `(422,421)-(590,444)`, while current NA2 uses
`(405,407)-(572,433)`, about 13 pixels higher. The panel is therefore shorter
and vertically compressed, with its two text regions moving in opposite
directions.

This is a user-reported broken baseline, not yet a proven causal attribution.
An earlier retained NA2 capture shows the same panel geometry, so a post-reset
capture is required before deciding whether any newest wrapper caused it or
whether it is a pre-existing unresolved caller mismatch. Reimplementation now
proceeds sequentially, one proven caller family per accepted commit, while
shared behavior is ported only once when cross-screen evidence supports it.

### 2026-07-26 independent v2 layout foundations

The replacement architecture begins with a separate generated resident asset
and unique `localization.font.v2.*` symbols; it does not reuse the retained
July helper symbols or monolithic return-address dispatcher. The first
foundation exports:

- one zero-initialized active-session pointer;
- the accepted 95-entry proportional-width table;
- guarded printable-ASCII measurement with optional explicit `<br>` and
  newline-byte line counting;
- shrink-only horizontal fit plus left/center/right and
  top/center/bottom box positioning;
- separate ordinary-space, newline, right-edge, inline-half-space and
  glyph-advance hooks.

The second foundation adds `localization.font.v2.adapter_call`. A caller-owned
104-byte record carries the text, container, requested alignment, four native
callback arguments and calculated scale/origin. The adapter validates and
prepares the request before publishing it, saves the previous session pointer,
renderer tracking and horizontal scale, invokes exactly one native callback,
then restores that state and the callback result through one cleanup path.
Nested callbacks use distinct caller records and restore the prior active
session.

The first family-specific fragments are now
`localization.font.v2.controls_adapter` and
`localization.font.v2.controls_callback`. The guarded call at NA2 runtime
`0x00388748` / ELF file `0x288848` is shared by only the first eight Controls
action labels. The adapter constructs one stack-local session with NUN5's
128-unit width, scale `1` for fitting labels, `128 / 178` for
`Ultimate Jutsu Prep`, and the proven caller-native origin formula. NUN5
`FUN_00399df0` passes box-left `60` for 1P and `324` for 2P, while NA2
`FUN_003885b0` passes native centers `124` and `388`; both pairs prove
`box_left = caller_center - 64` with no empirical correction. The first
normalized candidate used box-left `59` and placed all eight NA2 bounds one
output pixel left of NUN5. The pushed follow-up candidate used box-left `58`
and moved them another one to two pixels left, confirming the sign before
rejection. Its callback converts the prepared left edge back to the exact
center argument expected by NA2's native `FUN_00379240`, so NA2's internal
legacy measurement cancels without replacing the v2 box position.

The core and first-eight-label path are runtime-proven from the matched
Controls review. The final 640x480 pair matches those eight NUN5 label bounds
and centers, keeps `Linked Attack` full width, and fits
`Ultimate Jutsu Prep` with the exact 178-unit denominator. The user explicitly
accepted that result on 2026-07-26. The accepted first-eight hook at
`0x288848` is unchanged. The later call at runtime `0x003887D4` / ELF file
`0x2888D4` is the separate Control Settings vibration row, not the battle
Special Controls modal; its provisional adapter hook is removed.

## Contextual Special Controls / Practice Settings ON/OFF

The remade paired ss1 states are retained under
`work/Font/inputs/sstates/special-controls-on-off/remade-ss1-20260727/`.
Their embedded frames show compact uppercase NUN5 `ON`/`OFF` and oversized,
widely spaced NA2 fullwidth text. Exact-guarded draw telemetry from the copied
NA2 state is retained under
`work/Font/artifacts/special-controls-on-off/remade-ss1-20260727/draw-telemetry/`.

The telemetry proves that the selected row reads runtime string
`0x006059F0`, bytes `82 6E 81 40 82 6D 00` (`Ｏ　Ｎ`), from callers
`0x003791B8` and `0x00379214`; the unselected row reads runtime string
`0x006059F8`, bytes `82 6E 82 65 82 65 00` (`ＯＦＦ`), from caller
`0x00379BFC`. Clean SLPS file offsets `0x505AF0` and `0x505AF8` contain the
same guarded slots. The official NUN5 uppercase donors are SLES file
`0x513E68` (`ON`) and `0x513E6C` (`OFF`).

Canonical mappings T2203/T2204 therefore convert only those two modal-specific
Shift-JIS slots to ASCII. This corrects glyph selection and removes the
fullwidth internal advance without changing the accepted first-eight Control
Settings hook or Practice Settings pointer split.

The fresh mapping-only state proved that encoding was not the remaining
placement cause. NA2 and NUN5 both store list-local X `48`, Y `24`, extra row
step `12`, count `2`, and selected index `0`; their owning modal transforms
also match at `168`, `64`, `176`, and `112`. NA2 renders the list through
`FUN_00383600`, whose selected call is runtime `0x00383814` / ELF file
`0x283914` and whose unselected call is runtime `0x00383960` / ELF file
`0x283A60`. NUN5's structurally homologous `FUN_003923A0` uses its distinct
selected and ordinary renderer paths. The mismatch is therefore in those
renderer coordinate semantics, not the modal's list geometry.

Those two NA2 call sites are already owned by the accepted quit-confirmation
adapters. The bounded implementation extends the existing adapters instead of
installing overlapping hooks: outside the quit scope, selected text pointer
`0x006059F0` maps to local `(66,31)`, unselected record text pointer
`0x006059F8` maps to `(59,49)`, and every other caller tail-calls native
behavior. Exact-guarded task-state trials established those coordinates
without rebuilding an ISO. At 640x480, the final current ON center matches
NUN5 exactly; the OFF center differs by half a pixel because the retained
current glyph ink is two pixels shorter. That small raster mismatch remains a
separate Font refinement and is not compensated by further layout movement.
Confidence is **high** for the pointer guards, hook isolation, and placement.

The earlier identification of `FUN_003885B0` and its call at runtime
`0x003887D4` / ELF file `0x2888D4` as this ss1 modal was incorrect. Retained
telemetry identifies that path as Control Settings, with the ninth call drawing
its vibration row. The provisional second `font_layout_controls` hook is removed;
the runtime evidence is a useful negative result against reusing that call site
for Special Controls.

Practice Settings has three independent uppercase `[OFF, ON]` arrays at
runtime `0x00605AC0`, `0x00605AD0`, and `0x00605AD8`. The BTL row table points
to those arrays from files `0x20B498`, `0x20B49C`, and `0x20B4A0` for Commands,
Damage, and Guide Ninja Sound. Each row pointer is redirected to the existing
title-case table `0x00604658`, preserving the original Off-then-On index order.
The user verified Practice Settings working. No string bytes, global glyph
metrics, spacing logic, scale, or renderer calls change. The deterministic
guard generator is
`scripts/research/localization/generate_on_off_context_split.py`; it now
generates and verifies only these three runtime-proven Practice pointer edits.

The supplied title-to-Load `ss1` has boot CRC `A8A3C694`, state SHA-256
`B35AFFF69FDCDDF5478B6AE86DC9BF909469512F52E5268471FC9CF524EF1AF4`,
and an embedded 640x480 frame SHA-256
`16B7D32AB84C3B6CCECD60474CFF8E625C1224DC053AC9EE397DDE68F3947721`.
It shows all three Load rows plus the complete instruction/action panel, proving
that the accepted worker ISO survives the real transition without the former
helper-erasure freeze. Exact provenance is retained under
`work/Font/inputs/sstates/autofit_v2/controls/load-transition/`.

Static linked-package validation confirms the five core hook targets, the
two eight-byte Controls redirects, both adapter ABIs, state restoration,
internal branch bounds, the `Ultimate Jutsu Prep` denominator of 178, and the
unchanged retained-v1 blob. The separate v2 asset is 1,760 bytes with SHA-256
`AA56FE2A0D6BCB6FFEC7715D69D8CA17BFB76CE5CCB16A0597BF68F60BC645B8`.
Automatic word wrapping and remaining caller-native coordinate records remain
later family work.

## Accepted native 14x20 integration

The current patch set builds on the accepted version 5 baseline. Its former
standalone profile module pin was
`9FC3C4905DFF6D14BAAA848C56E6C17D1DE4E79EEFAB2E1A7A74FAD6A25013F8`,
and its former standalone feature pin was
`23A2CFDD285FF00A40F35AC42D0656580E4D9DE5884F2CF568453A20E93AA3A7`.
The current profile now covers it through the complete Localization feature pin
`175401CC76981D5E5AD8A3B07E526DB9AB4DE0903144C78E4CFDFB9A96AA30F4`.
It is a new, deterministic donor built from hash-verified clean NA2 and
official NUN5 inputs; it is not based on m01, v22/v23, the rejected semantic
palette swap, the 10x22 resample, or a whole-file GF4 replacement.

`font_glyphs_native` installs native NUN5 14x20 geometry and metrics for
same-semantic English cells. Unsupported punctuation is reconstructed from
clean NA2, retaining 95/95 printable-ASCII coverage. The 123-cell secondary
atlas is locally bounded; packed metric rows occupy only value words of empty
primary-map slots and are decoded by secondary-only draw and measurement
hooks. A glyph-owned normal-path helper keeps descriptor width for
primary/fullwidth glyphs and selects descriptor height only for the secondary
quad, restoring its intended 24x28 presentation without changing horizontal
geometry. Clean NA2 GF4C remains untouched. The two deterministic generators
verify these referenced blobs:

- atlas: 17,220 bytes, SHA-256
  `6E4B988E512568F0A91E0226A8A4046362C1A4EF078E50BBF630BEEF90333736`;
- packed map: 1,736 bytes, SHA-256
  `6F691015E5BA54EA87B2976970D828863E274BB543CC3D531D93800018EB7A5E`.

The former 316-byte decoder and 24-byte measurement-hook blobs are retained
only in Git history. Their accepted behavior is now expressed by
composition-time C and guarded symbolic hooks, documented in the 2026-07-28
cutover record below.

The current runtime injector compiles Font behavior from canonical C units and
links retained ABI shims directly from declarative fragments; it stores no
aggregate executable Font blob in Git.
The original 19-edit `native_final_v2` state established the atlas, metrics,
fit, and modal baseline; the later bearing and secondary-height work promoted
the remaining proven behavior into canonical guarded locations. Matched
Controls, Practice, Save/Load, and character-modal comparisons were presented
to the user. After the final secondary-height capture, the user accepted the
font itself as almost pixel-for-pixel. Fullwidth Shift-JIS Save/Load digits use
a different glyph path and were excluded from halfwidth-Latin comparison.

## Save/Load ASCII numeric fields

The matched slot-6 pair is preserved under
`work/Font/inputs/sstates/sjis_digits/slot-06/`. Its embedded screenshots and
EE-memory payloads establish that NA2 emits fullwidth CP932 digits for
`２０２６/０７/１７` and `Play Time ０２７：３９：４５`, while NUN5 emits
ordinary ASCII digits and punctuation.

NA2 `FUN_001e6370` owns all six visible numeric calls. It routes year, month,
day, hour, minute, and second through the fullwidth formatter
`FUN_00378510`; the NUN5 homolog `FUN_001ec0b0` routes its numeric fields
through ASCII formatted output. The compiled-C implementation changes only the
six guarded call blocks at ELF file offsets `0xE660C`, `0xE6650`, `0xE6694`,
`0xE67A4`, `0xE67E8`, and `0xE682C`. Each block now contains argument setup,
a symbolic runtime-injector call, and unavoidable year-return preservation;
all formatting behavior lives in `font_numeric.c`.

The first C entry reads day and year directly from the live record, formats
day through immutable `%02d`, and returns year in `v0`; the hook moves that
return to callee-saved `s6`. The month uses the same C two-digit entry, the
third entry emits the preserved year through `%d`, and the hour C entry
reproduces NUN5's signed `hour < 100 ? hour : 99` rule before `%02d`.
Canonical liveness shows `s6` is saved in the prologue and otherwise unused
until the later seconds calculation, so it safely survives the intervening
native formatting calls. Timer divisors `108000`, `1800`, and `30`, all six
guarded block sizes, and every formatter caller outside `FUN_001e6370` remain
unchanged. The Save/Load-only fullwidth colon at ELF file offset `0x503134`
remains a declarative ASCII-colon edit.

The pre-migration behavior is runtime-proven: the user confirmed correct
`DD/MM/YYYY`, including the four-digit year, on Current CRC `55739D20`.
The first consolidated C candidate at commit `1d796a5` was runtime-rejected on
Current CRC `8A663AA9`: user `ss1` records the menu immediately before Load,
and `ss2` records the broken Load screen. Their task-owned copies and hashes
are retained under
`work/Font/inputs/sstates/c-migration-load-regression-2026-07-28/`.

Static control-flow comparison identifies the exact defect with high
confidence. All six guarded blocks are mid-function replacements for native
`jal sprintf` calls, but the rejected symbolic rows used non-linking `j26`.
Each compiled C entry returns with `jr ra`; without a new link address, it
returns to the surrounding formatter's caller instead of resuming after the
hook. The corrected candidate uses `jal26` at relocation offset `0x8`, so the
C entry returns to the next instruction and the surrounding Save/Load function
continues. The argument setup, C object, returned-year move into `s6`, block
sizes, and every formatter outside this family remain unchanged. Runtime
acceptance is complete: after the fresh corrected build, the user verified
that Load and Save open without freezing and retain the accepted date/time
presentation. Independent fragment reconstruction is retained in
`scripts/research/localization/verify_font_renderer.py`. Permanent coverage now
protects the independently established linking-call contract for all six
Save/Load hooks.

The isolated worker build retained at
`work/Font/build/save-load-ascii-digits.iso` has boot CRC `F9FC3002`. After a
clean manual launch in the Font-owned PCSX2 copy, the user confirmed that the
Save/Load date and Play Time fields render correctly as ASCII. The patch is
therefore proven for its original ASCII-conversion stage. The later EU date
ordering is separately user-confirmed on Current CRC `55739D20`.

## Battle Settings ASCII time value

The matched slot-1 pair copied read-only from the user's PCSX2 is preserved
under
`work/Font/inputs/sstates/sjis_digits/slot-01-20260726_115913/` with source
timestamps and SHA-256 provenance. Both embedded screenshots show Battle
Settings with `Time 99`; NA2 emits the value through its fullwidth numeric
path, producing visibly wider digit spacing than NUN5's ordinary ASCII value.

NA2 `FUN_008801e0` is the Battle Settings row sub-renderer called by
`FUN_008807a0`. For the Time row, value `100` takes a separate infinity-symbol
branch. Every other value reaches the fullwidth formatter through the guarded
24-byte BTL call block at file offset `0x1CC3D8` (Ghidra `0x00880298`,
runtime `0x008802D8`). The NUN5 homolog is `FUN_0089cbd0`, called by
`FUN_0089d280`.

`font_numeric_battle_settings` changes only that ordinary-value block to
set up the value and stack buffer, then call the compiled C entry through a
linking `jal26` runtime-injector hook. The rejected consolidated candidate used
the same non-linking `j26` control-flow error as Save/Load; the correction
changes only the hook encoding. C uses the immutable `%d` bridge. The adjacent
40-byte branch ending at the edit site is independently guarded, so value
`100` continues to render the native infinity symbol. Selector state, the
stored timer value, the other five settings rows, and every other fullwidth
formatter caller remain unchanged. Independent fragment reconstruction is
retained in `scripts/research/localization/verify_font_renderer.py`. After the
corrected fresh build, the user verified the ordinary below-100 value and the separate
100/infinity behavior. The patch is therefore `runtime_proven`, and permanent
coverage protects its linking-call contract.

## Ninja Song ASCII dynamic numbers

The paired ss2–ss5 states are copied read-only under
`work/Font/inputs/sstates/ninja-song/ss2-5/` with exact source filenames,
timestamps, sizes, and SHA-256 provenance. Together they cover the dynamically
generated arithmetic factors, arithmetic total, inline numeric placeholder,
and detail score used by the Ninja Song screens.

NA2 BTL `FUN_00718920` (file function offset `0x64A60`) renders the arithmetic
expression, and `FUN_00718C60` renders the later detail fields. Their NUN5
homologs are `FUN_0072E5B0` and `FUN_0072E9C0`. Five calls in those two NA2
functions reach the same fullwidth CP932 formatter `FUN_00378510`:

- `0x64B28`: left factor, width 3, mode 0;
- `0x64BA8`: right factor, width 3, mode 0;
- `0x64CE4`: total, width 5, mode 0;
- `0x64E4C`: inline value, width 4, mode 1;
- `0x64ED4`: detail score, width 4, mode 0.

The NUN5 formatter homolog preserves the caller ABI but emits ASCII decimal.
Mode 0 left-pads with ASCII spaces to the requested width, mode 1 emits an
unpadded value, and mode 2 left-pads with ASCII zeroes. The shared
`localization.font.ninja_song_ascii_number` helper reproduces those modes
behind NA2's existing ABI and calls the immutable `%d` formatter at runtime
`0x0017BCA0`. Exactly the five guarded BTL JAL instructions above redirect to
it; no per-screen duplicate formatter is introduced.

The multiplication separator remains reachable. In the copied ss2 runtime
state, its pointer resolves to bytes `20 2A 20` (`" * "`), already supplied by
canonical translation mapping T2195 from `NA2_SLPS@0x504DA0`. The Font patch
therefore guards that mapping but does not rewrite the separator. On
2026-07-27, the user built and tested the integrated change across ss2–ss5 and
declared the task done. Some runtime numeric values were not observed, but
they are not separate strings: all values pass through the same five guarded
call sites and width-aware decimal helper. The patch is therefore
`runtime_proven`; arbitrary unseen decimal values retain the same mode and
padding behavior. Deterministic verification is provided by
`scripts/research/localization/verify_font_renderer.py` and
`scripts/research/localization/generate_ninja_song_ascii_numbers.py`.

Controls retains full-width `Linked Attack`, fits the official 19-byte
`Ultimate Jutsu Prep` probe through the shared NUN5 logical-width helper,
leaves `OFF` on the ordinary renderer, and restores local scale immediately
after a fitted draw. Its labels move one local X unit without moving selection
markers. Shared layout wrappers also reproduce the reviewed confirmation
choices, Practice pause-list box and Y origin, confirmation-body placement,
and character-return box. The character modal keeps its independent local X
values `81.75, 73.375, 72.375, 63.5, 3.5`; reviewed ordinary-row centers are
within one pixel of NUN5 and the long fifth row fits inside the modal.

A clean glyph derivation preserves the GF4 and GF4C file sizes and produces:

- `DATA/GF4.BIN`: 906,678 bytes, SHA-256
  `79BA614746E667A70A068A0A889085D028D8019884182E78041026A77971AA25`.

Executable Font output no longer has an independent final ELF hash: the shared
payload builder assigns its runtime addresses together with every other
resident contribution, then materializes its guarded boot-ELF hooks. The
resident-relocation gate below records the integrated worker result.

## 2026-07-24 weight and spacing refinement

The accepted native baseline remains canonical. The task-local bitmap
stretch/gamma candidate that presented the halfwidth-Latin cells at `1.20`
around the established 15-pixel baseline and applied alpha gamma `1.65` is
runtime-rejected. Although its aggregate bounds and density moved numerically
closer to NUN5, matched zoom review showed worse letterforms and outlines. It
must not be used as an implementation parent. Fullwidth Shift-JIS Save/Load
digits remain outside the halfwidth-Latin comparison.

Several task-local spacing tests have already ruled out or constrained
candidates:

- increasing every printable glyph's integer metric advance by one unit is too
  coarse. It moves the median width from two pixels short to three pixels wide;
  `Item Select` and `Linked Attack` overshoot by 12 and 13 pixels;
- reducing the packed metric row for the blank cell by 6, 10, or 12 units
  changes centered placement but does not reduce the drawn inter-word gap by
  the corresponding amount. The current secondary measurement and draw paths
  therefore do not share a usable blank-advance control through that row;
- the earlier task-local tracking candidates `0.5`, `1.0`, and `1.5` are
  inconclusive rather than evidence that secondary tracking is ineffective.
  Their state generator changed the active context temporarily and patched
  runtime `0x00186694`, which is the `param_2 == 0` primary-font initializer.
  The next secondary-font setup overwrote the active field from the untouched
  `param_2 != 0` initializer at `0x001865E0`. Their identical screenshots are
  therefore explained by the wrong branch and must not reject a guarded
  secondary-tracking test.

Focused decoding of the installed 316-byte helper gives reusable boundaries.
Runtime `0x00187274..0x00187330` walks the packed metric payload for the current
secondary cell, subtracts the selected leading bearing from the active draw
coordinate, and stores the trailing trim in the font context. Runtime
`0x00187330..0x00187390` bounds a plain secondary byte to cells `0..122`,
retrieves the same packed row, and returns its expanded measurement pair.
These results explain why integer glyph metrics affect both placement and
measurement strongly, while the blank-cell experiments do not provide the
required fractional letter-spacing correction.

### Renderer-geometry root cause

Fresh static comparison uses clean `@source_na2/SLPS_258.37`, SHA-256
`20C0A40D70EA412CD431993A2E189B37ECB6054D63AE93BE545470016E1627AF`,
and clean `@source_nun5/SLES_556.05`, SHA-256
`20A43677397731A2A20899336D1165ACE5B436906B9B89BE90FB10F4558DD19D`.
The preserved Ghidra exports under `@analysis/disassembly/NA2/` and
`@analysis/disassembly/NUN5/` were reused; neither binary was disassembled
again.

NA2 glyph emitter `FUN_00187cc0`
`[0x00187CC0,0x00188140)` computes the normal quad at
`0x00187F64..0x00187F7C` (ELF file offsets
`0x88064..0x8807C`). It loads descriptor field `+0x0C` for both axes:

```c
right  = x + (float)descriptor->output_width;
bottom = y + (float)descriptor->output_width;
```

NUN5 counterpart `FUN_001891a0`
`[0x001891A0,0x00189640)` instead reconstructs:

```c
right  = x + (float)descriptor->output_width  * scale_x;
bottom = y + (float)descriptor->output_height * scale_y;
```

The accepted NA2 secondary descriptor retains its original 24x28 output quad,
as recorded by `font_glyphs_native_01`, but NA2 therefore presents its normal
glyph as 24x24. NUN5 uses all 28 vertical pixels. This matches the reviewed
median two-to-three pixel height deficit and explains why the rejected
file-offset `0x88064` experiment was wrong: changing the shared width load from
24 to 28 produced 28x28 and stretched both axes. The evidence supports a
secondary-only Y correction that leaves horizontal metrics unchanged and
continues using the original width field on the primary/fullwidth path.
Confidence is **high** for the function ranges, field use, and cross-game
difference.

The guarded task-local Y-only precursor is
`work/Font/artifacts/font_match_v1/renderer_geometry_v1_secondary_24x28.p2s`
(SHA-256
`629180D28C75881CF7D7E5149AE38B935BD3F322160AB9D706DF94B06A7168F2`).
It changes only copied savestate memory through
`work/Font/analysis/font_match_v1/prepare_renderer_geometry_state.py`. Its
accepted behavior is now canonical in two guarded ELF edits:

- file offset `0x2F8840`, original 32 zero bytes, installs
  `08006330020060100C0021C6100021C660088046000D0046E01F06086CCA848F`;
- file offset `0x88078`, original `000D00466CCA848F`, installs
  `D0E10F0870002392`.

The helper reads the existing secondary-font mode bit, selects descriptor
`+0x10` height only for secondary glyphs or `+0x0C` width otherwise, computes
the normal quad bottom edge, and rejoins the untouched path at runtime
`0x00187F80`. It leaves X geometry, primary/fullwidth glyphs, spaces, logical
measurement, and row positions unchanged.

Final guarded runtime validation on the matched Control Settings state confirms
the canonical result. Exact reads matched the secondary-only hook and helper,
the accepted bearing helper, the Controls fit helper, the ordinary-space hook,
and the restored `1.0` local scale before capture. Across `Attack`, `Ultimate
Jutsu Prep`, `Item Use`, `Jump`, `Guard`, `Item Select`, and `Linked Attack`,
the median width, height, and center-Y deltas against NUN5 are all zero; median
center-X delta remains the accepted -1.5 pixels. Three labels are one native
raster pixel shorter, so no speculative per-row or per-glyph positioning was
added. The user accepted the font itself as almost pixel-for-pixel. The fresh
capture, structured operation result, and nearest-neighbor comparison are
retained under
`work/Font/artifacts/font_match_v1/renderer_runtime_v1/`.

The accepted palette conversion is not the source of the heavier appearance.
Across the 85 exact NUN5 donor cells used by the accepted atlas, containing
23,800 source samples, NUN5 alpha mass maps to clean NA2 GF4C at a ratio of
`0.993762` (mean alpha `19.170336` becomes `19.050756`). The conversion is
therefore fractionally lighter in aggregate, not bolder. This further isolates
the compact 24-pixel presentation as the first weight-related behavior to test.
After the Y-only correction, median visible-ink density is `0.993682` times
NUN5, while visible-ink mass is `0.965854`; the remaining horizontal deficit
is therefore advance/spacing behavior rather than excess palette weight.
Confidence is **high** for the byte-level palette and guarded runtime results.

### Native NA2 selected-row offset behavior

Using the same clean NA2 and NUN5 ELF identities and preserved exports above,
the shared selected-row paths intentionally differ. NA2 `FUN_00379040` first
draws the gray shade at the caller's input origin, then draws the red foreground
after subtracting one local X unit and two local Y units. Selection therefore
changes the apparent text position for every caller that uses this helper.
NUN5 counterpart `FUN_00389B30` instead enables the renderer's shadow state and
draws the red foreground without changing its input geometry.

The resulting NA2 text jump is native game behavior, not a localization,
font-asset, autofit, or positioning regression. It is accepted as a known
NA2/NUN5 presentation difference and requires no correction. Do not compensate
for it in caller layout or classify it as an unresolved Font defect unless the
user explicitly selects a separate NUN5-parity change. This conclusion is
bounded to callers using these shared helpers; other selected-text paths retain
their own verified behavior. Confidence is **high** from the cross-game
function comparison and matching runtime presentation.

### Ordinary tracking and plain-space root cause

NA2 initializer `FUN_00186510`
`[0x00186510,0x001866D0)` stores secondary tracking `-1.0` at context
`+0x3C`. NUN5 counterpart `FUN_001878e0`
`[0x001878E0,0x00187AE0)` stores tracking `0.0`, horizontal and vertical
scales `1.0` at `+0x80/+0x84`, and extra spacing `0.0` at `+0x88`.

In NA2 string renderer `FUN_00188140`
`[0x00188140,0x00189740)`, the actual horizontal plain-space case is
`0x001892C0..0x00189300` (ELF file offsets
`0x893C0..0x89400`). With the accepted secondary width 14 and tracking -1,
its ordinary formula advances a space by 13 units. NUN5 renderer
`FUN_00189640` `[0x00189640,0x0018AAE0)` uses
`0x0018A3CC..0x0018A434`:

```c
x += scale_x * (extra_spacing + cell_width + tracking - 6.0f);
```

At the initialized secondary values, NUN5 therefore advances a plain space by
8 units. NUN5 also applies `scale_x` to the ordinary glyph-advance path at
`0x0018AA48..0x0018AAA8`; NA2's corresponding path is
`0x001896A0..0x001896E8`. Accepted NA2 telemetry records tracking `-1.0` and
ordinary secondary advance `(14 - trailing_trim) - 0.5`. NUN5's tracking zero
adds 0.5 per visible glyph, while its five-unit narrower space compensates most
of that expansion. For `Linked Attack`, twelve visible glyphs gain six units
and its one space loses five, predicting a net one-unit width increase while
correcting the visibly compressed letters and oversized word gap.

The existing `font_controls_auto_fit_05` hook at ELF offset `0x88B7C`
(runtime `0x00188A7C`) is not this branch. It lies in the inline-markup
half-space case at `0x00188A20..0x00188A84`, so it does not scale ordinary
Control Settings spaces. This is a confirmed classification error in the
accepted patch description. The historical v23 edit did change the correct
secondary initializer at runtime `0x001865E0`, so it remains a valid negative
result when applied alone; the newly justified hypothesis is the inseparable
NUN5 pair of tracking zero plus the real eight-unit, per-call-scaled
plain-space branch.

The guarded combined state is
`work/Font/artifacts/font_match_v1/renderer_geometry_spacing_v1_nun5.p2s`
(SHA-256
`6C4D5EA11A0D22A8763EAF26394844A61EA0FEDBF9D297D3896A7927539499CF`).
It was generated by
`work/Font/analysis/font_match_v1/prepare_renderer_geometry_spacing_state.py`
and uses the documented Current-only fixed gap only as a short-lived
savestate hypothesis. That address is explicitly not a canonical placement.
The primary/fullwidth path is guarded out.

Guarded runtime comparison confirms the ordinary-spacing part of the
hypothesis. At native screenshot scale, NUN5 and the combined candidate have
these visible widths:

| Label | NUN5 | Combined candidate |
| --- | ---: | ---: |
| `Attack` | 72 | 72 |
| `Item Use` | 94 | 94 |
| `Jump` | 51 | 51 |
| `Guard` | 58 | 59 |
| `Item Select` | 123 | 123 |
| `Linked Attack` | 150 | 150 |

Median width, height, and center-Y deltas are all zero. The visible word gaps
also agree to within one pixel: `Item Use` is 14/14, `Item Select` is 14/13,
and `Linked Attack` is 14/14 for NUN5/candidate. This establishes tracking zero
plus the real plain-space path as the correct ordinary horizontal behavior.
It does not yet make the complete Controls path correct: the existing local
auto-fit helper shrinks `Ultimate Jutsu Prep` to 139 visible pixels while NUN5
renders it at 157.

Exact guarded NA2/NUN5 advance telemetry isolates that remaining discrepancy.
For `Ultimate Jutsu Prep`, NUN5 uses horizontal scale `0.719101`, exactly
`128 / 178`, while accepted NA2 uses `0.705234`, exactly `128 / 181.5`.
NUN5 begins the fitted draw at local X `59.280899`; accepted NA2 begins at
`61.0`. Ordinary labels confirm the paired renderer-state difference:
accepted NA2 records tracking `-1.0`, whereas NUN5 records tracking `0.0`.
The telemetry parser's contextual space discontinuities are about `11.5` or
`12.5` in accepted NA2 and `6` or `7` in NUN5; these values include surrounding
bearing semantics and are not direct replacements for the static eight-unit
plain-space formula.

The accepted helper's `9.5 * byte_count + 1` approximation is therefore not a
NUN5-equivalent measurement function. Its 181.5-unit denominator happened to
fit the old presentation but becomes visibly too narrow after ordinary
tracking and spacing are corrected. The next implementation step is to
reproduce NUN5's 178-unit logical measurement and centering for the overflowing
boxed label, while keeping ordinary labels unscaled. Confidence is **high**
for the runtime widths, scales, tracking values, and fit-denominator
discrepancy; the exact per-character reconstruction of NUN5 measurement remains
under analysis.

### Exact boxed measurement and missing leading-bearing scale

Static reconstruction now removes the approximate denominator. With secondary
tracking zero, patched NA2 measurement already returns the same trimmed visible
glyph widths as NUN5. Its remaining difference is ordinary ASCII space:
the legacy path counts the full 14-unit cell, whereas NUN5 advances eight
units. The equivalent NUN5 logical width is therefore:

```text
patched_NA2_width_at_tracking_zero - 6 * ordinary_ASCII_space_count
```

For `Ultimate Jutsu Prep`, patched NA2 returns 190 and the two spaces subtract
12, producing the exact NUN5 width 178 and scale `128 / 178 =
0.7191011236`. A guarded v2 state used that scale and kept every ordinary label
at scale 1.0.

Per-glyph telemetry then isolated a second, independent renderer omission. The
v2 and NUN5 fitted calls have the same scale (`0.719101`) and the same sum of
scaled visible-glyph advances (`145.977525`). Nevertheless, v2 begins at local
X `59.0` instead of `59.280899`, and its recorded span is `117.483110`
instead of NUN5's `128.719072`. Each origin-step deficit is an integer glyph
bearing multiplied by `1 - scale`, proving that the glyph widths are correct
but the leading-bearing displacement remains unscaled.

The disassembly agrees exactly. The imported NA2 semantic metric decoder at
runtime `0x0018731C` subtracts the decoded bearing directly:

```c
coordinate -= leading_bearing;
```

NUN5's ordinary secondary loader `FUN_00188270`, at
`0x001887B0..0x001887D8`, instead performs the horizontal operation:

```c
x -= leading_bearing * scale_x;
```

Its vertical and alternate-glyph paths remain separate. This missing
horizontal multiply explains both the `0.280899` first-origin difference and
the accumulated fitted-label narrowing without implicating the donor raster,
palette, ordinary tracking, or the now-exact width calculation. Confidence is
**high** because the static instruction difference predicts the exact guarded
telemetry deltas.

The register-safe v4 state is retained at
`work/Font/artifacts/font_match_v1/renderer_geometry_spacing_fit_v4_nun5.p2s`.
Its guarded runtime run loaded the state, matched every expected code byte,
captured slot 95, and closed only the authenticated task-owned PCSX2 instance.
`Ultimate Jutsu Prep` then matched NUN5's visible `157x17` bounds and center
exactly. A deterministic replay of every accepted metric row predicts total
advance `128.719070` versus NUN5 `128.719072`, with maximum per-glyph origin
error `0.000002`.

The runtime-proven correction now lives inside the deterministic 316-byte
semantic metric decoder. Its formerly unused final 32 bytes hold the
register-safe helper, so no temporary runtime gap or separately placed payload
is retained. The helper scales only the decoder's horizontal leading-bearing
path through the existing local renderer factor, preserves the vertical path
and live `v0` return value, and leaves the factor at `1.0` outside fitted calls.
The follow-up guarded v5 run on worker ISO CRC `6FD5D698` read back the exact
hook at runtime `0x0018731C`, the exact helper at `0x00187390`, a zeroed former
task-local gap at `0x008DD1D0`, and the initialized `1.0` scale word at
`0x0060737C`; its matched Controls measurements were identical to v4.
The preceding v3 helper remains rejected because it clobbered that return
register and produced no usable capture.

### Retired v1 shared renderer-metric and layout-wrapper port

The following describes the superseded July v1 implementation for historical
and reverse-engineering reference. None of these symbols or hook declarations
remain executable inputs after the 2026-07-28 retirement.

The exact boxed result is now implemented as shared renderer behavior rather
than another screen-local denominator. The canonical port makes these guarded
boot-ELF changes:

- secondary initializer runtime `0x001865E0` (file `0x866E0`) now stores NUN5
  tracking `0.0` instead of NA2 `-1.0`;
- ordinary ASCII-space runtime `0x001892EC` (file `0x893EC`) routes through
  resident symbol `localization.font.plain_space` and evaluates
  `(cell_width + tracking - 6) * scale_x`;
- newline runtime `0x00188604` (file `0x88704`) routes through resident symbol
  `localization.font.newline_advance`, retaining NA2 descriptor height and line
  spacing while removing its four-unit excess and skipping the second
  alternate-font height;
- resident symbol `localization.font.measure` calls the accepted NA2 metric
  path once and preserves that legacy result in `v1`. Pure printable ASCII is
  measured in `v0` through the 95-entry NUN5-derived proportional-width table
  packed beside the resident code. Tagged, multiline, or non-ASCII input keeps
  the legacy path with the proven six-unit ordinary-space correction.

The Controls wrapper remains a distinct 128-unit container, but its helper at
resident symbol `localization.font.controls_fit` consumes that shared
denominator.
The old cave at file `0x2BDDFC` is no longer patched; the superseded
`9.5 * byte_count + 1` approximation is no longer executable. On the matched
`Ultimate Jutsu Prep` crop, NUN5 is `157x16` with center X `154.0` and the
current result is `157x17` with center X `154.0`. The one-pixel vertical raster
difference is outside the horizontal fit decision.

Shared layout behavior is ported once behind exact caller guards. The selected
choice primitive at runtime `0x00379150` routes to resident symbol
`localization.font.selected_helper`; the UI wrapper at `0x00379A20` routes to
`localization.font.ui_helper`. They map the reviewed confirmation positions.
The same UI helper applies the 216-unit shrink-only box and four-unit Y
correction to the Practice pause list, aligns Practice and Collection
confirmation bodies, and routes the character-return body through a centered
368-unit box after selecting the accepted secondary renderer. Unrelated
callers resume through the resident displaced-code trampolines.

### Command Chart and Practice title boxes

The Command Chart and Practice command-title rows share the same boxed-fit
logic but not the same container geometry. NUN5 wrapper telemetry at caller
`0x003882D0` establishes these separate records:

- Command Chart titles: X `28`, Y `17/117/217`, width `288`, height `20`;
- Practice titles: X `32`, Y `14/114/214`, width `352`, height `20`;
- Practice explanations remain a separate caller family at X `40`, Y
  `42/142/242`, width `364`, height `48`, vertical alignment `1`.

A guarded task-owned NUN5 state probe recorded `FUN_0018ca40`'s live horizontal
denominators before scaling. `Susanoo's Blade` is `142`, `Reverse Halo` is
`115`, and `Fire Style: Phoenix Flower Jutsu @Petal Shower@` is `440`.
Those values exactly equal the sums from the 95-entry packed metric table.
This runtime result rejects both the legacy NA2 results (`135`, `110`, `417`)
and the temporary constant-eight interpretation. The resident helper now
validates plain ASCII once, consumes the shared table, applies the caller's
`box_width / measured_width` factor only on overflow, and restores scale after
the draw.

NA2 reaches the shared UI wrapper at return address `0x00382454`; exact outer
return-address guards distinguish Command Chart `0x0087A930`, Practice title
`0x00878AA0`, and the pre-existing character-body caller. The final current
origins use a common `-0.8` logical-unit visible-ink compensation:
Command Chart X `27.2` with Y offset `-3.8`, and Practice X `31.2` with Y
offset `-6.8`. The width constants remain the exact NUN5 `288` and `352`.

Matched 640x480 captures on worker CRC `D64F4D9F` show:

| Title row | NUN5 ink bounds | Current ink bounds |
| --- | --- | --- |
| Command Chart: `Susanoo's Blade` | `(141,87)-(314,100)` | `(141,87)-(314,99)` |
| Command Chart: `Reverse Halo` | `(141,212)-(279,225)` | `(140,212)-(279,224)` |
| Command Chart: long Petal Shower title | `(141,337)-(488,353)` | `(141,337)-(496,353)` |
| Practice: `Shadowbur Extra Hit` | `(96,83)-(326,96)` | `(96,83)-(325,96)` |
| Practice: `Guard` | `(96,208)-(153,221)` | `(96,208)-(153,221)` |
| Practice: `Linked Attack` | `(96,333)-(245,346)` | `(96,333)-(245,346)` |

The long current title is complete and unclipped. Its eight-pixel right-edge
difference is not a fit error: official NUN5 bytes `0x40` render quote-shaped
glyphs, while the accepted NA2 atlas deliberately preserves literal at-signs.
The occasional one-pixel short-title height or leading-bearing difference is
likewise accepted raster/metric residue, not a container offset. The NUN5
reference screenshot hashes are
`E602195AF1CC4EFD122735DD7F7D08A15ECCC38B88DB1FCF85C5CD966E70E9DE`
and
`983AC7C636C3F5CF47492E87795899592C2B4B50EFA1EE556AC4095052F4CF2E`;
the matched current hashes are
`FE37ABB125396BA6786230A6B580DE4C59EEF20527A4FD5B49B52D98BCC15598`
and
`D10643D42B96D0135C4E25F636EB517042C6ABE28822BEB56DFFD0AE5D084C8F`.
Confidence is **high** for the denominators, caller guards, fit thresholds,
origins, and separation from the unresolved Practice explanation family.

The stage-by-stage v2 reimplementation no longer depends on those retained
outer-return guards. Bounded BTL inspection identifies the actual title-only
draw calls directly. The supplied states independently confirm that the live
MWo3 image begins at `0x006B3F00`, so these file offsets map without the
`-0x40` Ghidra-header adjustment:

- Practice runtime `0x00878A98`, BTL file `0x1C4B98`;
- Command Chart runtime `0x0087A928`, BTL file `0x1C6A28`.

Both sites contain guarded bytes `C4080E0C00000000`, a `jal 0x00382310`
followed by its NOP delay slot. The Practice call occurs before its separate
explanation loop; the Command Chart call precedes two independently guarded
auxiliary-string draws. The v2 implementation therefore redirects only those
two calls to explicit mode entrypoints. Each entrypoint tail-calls one shared
title adapter, which selects the proven geometry above, creates one
single-line shrink-only v2 session, and invokes native `0x00382310` through a
common callback. No Practice explanation or auxiliary Command Chart call is
selected.

The generated v2 resident asset with this adapter is 2,020 bytes and has
SHA-256
`9561B62AAD1E0139B920AED058B2ECB066A9EB7D64092992ECAD60BC1581C8F6`.
Static tests decode both linked BTL hooks, both mode entrypoints, every title
constant, the callback ABI, and the shared-adapter relocations.

The first converted-state capture used the ELF/Ghidra mapping base
`0x006B3EC0` as though it were the live MWo3 base. It therefore wrote each BTL
edit `0x40` bytes too early and produced the hybrid Command word `0x4423D147`
instead of the linked `jal` word `0x0C23D147`. Exact clean context around both
supplied call sites proved that the complete live BTL image begins at
`0x006B3F00`. Corrected guarded states contain `jal 0x008F451C` at
`0x0087A928` and `jal 0x008F48B0` at `0x00878A98`; the failed capture was a
state-conversion error, not a rejected renderer hypothesis.

Hidden task-owned PCSX2 captures on boot CRC `A8A3C4FF` then covered preserved
Command Chart slot 3, all six Practice command slots 2-7, and the accepted
Controls regression. The worker ISO SHA-256 is
`0396D02B559EFC964B05520CC539F074432A57C3796BC1CA3063C3533E32FF1F`;
its 5,488-byte resident payload ends at `0x008F5270` and has SHA-256
`4BD20BE93EA0D0A217A790774C4813863F1F8303FA49117889A6D59D664D097D`.
The corrected Command capture reproduces the prior matched title bounds and
has SHA-256
`FE37ABB125396BA6786230A6B580DE4C59EEF20527A4FD5B49B52D98BCC15598`.
Every Practice page retains the NUN5 title origins while its later explanation
rows remain intentionally unchanged for their separate wrapping family.
Confidence is **high** for the direct hooks, shared adapter, shrink-only
behavior, distinct geometries, state restoration, and separation between
titles and explanations. The user explicitly accepted the Command Chart result
on 2026-07-27. The Practice title result remains agent-validated and awaiting
user acceptance.

### Command Chart relationship rows

Refreshed paired ss1 and ss2 isolate the auxiliary relationship text drawn
below each accepted Command Chart title. The preserved NA2 BTL export identifies
the owning row function as `FUN_0087A700`. For each 0x34-byte row record it
draws the title, reads optional text selectors from record bytes `+4` and `+5`,
and renders them independently through `SUB_00382310` at Ghidra addresses
`0x0087A930` and `0x0087A97C`. With the confirmed live BTL base
`0x006B3F00`, those are runtime `0x0087A970` / file `0x1C6A70` and runtime
`0x0087A9BC` / file `0x1C6ABC`. The separate calls cannot wrap the combined
English relationship and cause refreshed ss1 to overflow horizontally.

The structural NUN5 homolog is `FUN_00896E70`. Its branch at
`LAB_008977BC` resolves selector `+4` through `SUB_003D16C0`, copies the
result into a 0x100-byte stack buffer, resolves and appends selector `+5` when
present, then draws the complete buffer once through `SUB_00393ED0`. The
request uses width `308`, height `32`, line limit `2`, and style `9`. Its
native row formula also separates relationship and icon placement: after the
title it draws the combined relationship from `fVar17 + 4` and the icons from
`fVar17 + 44`, while NA2 advances its shared row coordinate by `30` before
the relationship and then draws icons only `20` units below it. This explains
both refreshed cases: ss1 needs one jointly wrapped two-line block, while all
three ss2 single-line rows and their icons share the same repeatable vertical
correction.

The bounded NA2 port therefore hooks only the first exact auxiliary call through
a 36-byte native-register shim, passes the row record and native Y to generated
C, and suppresses only the second exact draw. The C entry resolves both strings
from NA2's live table at `0x008BD1D0`, combines them without modifying canonical
mapping bytes, and wraps at spaces through the shared native-metric v2 helper.
The measured NA2-side request uses X `43.2`, native Y minus `11.5`, width `226`,
height `32`, line advance `30`, glyph height `14`, and a further `-8` Y bias
only when the wrapped result has one line. The native icon loop remains intact.
A first candidate changed its one shared `+20` float constant at BTL file
`0x1C6ACC` to `+16`; this matched rows with relationship text but was wrong for
rows without it. The reason is visible in both preserved homologs. NA2 leaves
its row coordinate at the title base for a plain row, or advances it by `30`
before drawing a relationship, then adds one shared icon offset. NUN5 starts
from a title base six units above NA2's, adds `8` only for a relationship row,
and then adds `44` for icons. Expressed at NA2's unchanged hook coordinate, the
NUN5 targets are therefore `+16` after a relationship and `+38` after a plain
title. The corrected port replaces only the two-instruction `+20` load at
runtime `0x0087A9CC` / BTL file `0x1C6ACC` with a native-register shim and
generated-C selector using record byte `+4`; both icon branches and the
existing additional `+4` for tokens 4 and above remain native.

The first relationship candidate also allocated
`FONT_V2_FLAG_SCALE_LINE_ADVANCE` at `0x10`, which was already owned by
`FONT_V2_FLAG_PREMEASURED`. Every premeasured caller therefore also scaled its
line advance, causing regressions outside Command Chart. The corrected flag is
`0x20`; the Command relationship request becomes `0x3D` instead of `0x1D`,
and the shared prepare check tests `0x20` independently. The user confirmed
that this isolation restores the previously working modal families. This flag
correction does not alter glyph metrics, fitting, wrapping, or any caller box.

Hidden task-owned runtime captures on Current CRC `092FEF8A` used the refreshed
ss1 and ss2 states and the production C hot-reload path for the first
relationship candidate. At 640x480, ss1's
relationship ink is `160,231-396,262` versus NUN5
`162,232-397,262`, and its first relationship icon is
`196,278-212,294` versus `196,278-212,295`. Across ss2, all three blue rows
remain within one raster row of NUN5 and the icon bounds match at Y
`153-170`, `278-294/295`, and `403-420`. A later isolated ss1 capture proves
that the row-aware `+38` plain-row path moves the final input sequence down by
the missing 22 local units and aligns it with the retained NUN5 reference.
Complete post-change ss1 and ss2 captures then exercised the relationship
adapter and row-aware icon selector together: ss1 retains the jointly wrapped
two-line relationship and aligns both relationship and plain input rows, while
all three ss2 relationships remain on one line without overflow and all three
input rows retain their NUN5 Y geometry. Titles, icon records, horizontal icon
spacing, and all other BTL callers remain native.

Those supplied `092FEF8A` states restore an older resident payload than the
later on-disc Current build. Offline `eeMemory.bin` signature recovery proves
that `localization.font.v2.adapter_call` remains stable at `0x008F4130`, but
`practice_append` is at `0x008F4D68` rather than Current `0x008F4F30`,
`title_callback` is at `0x008F5500` rather than `0x008F56E8`, and the
native-measure callback is at `0x008F4320` rather than `0x008F44C0`.
The earlier `wrap_native = 0x008F5510` identification was wrong: exact
disassembly of the compatible ISO's `228.BIN` places that address inside
`font_v2_prepare`. Calling it as a wrapper trapped the injected Movie-list
candidate, while a clean ss8 reload without injection rendered normally.
The same payload proves `font_v2_wrap_native` spans
`[0x008F5930,0x008F5B38)` (520 bytes) and makes its three measurement calls to
`font_v2_native_measure` at `0x008F4F38`. A corrected wrap-only probe and the
complete ss8 candidate both execute normally with `0x008F5930`. This is a
savestate-specific development constraint, not a production payload
requirement.

Confidence is **high** for the homolog, selectors, call sites, buffer
composition, shared one-/two-line geometry, conditional icon offsets, flag
ownership, and integrated ss1/ss2 runtime behavior. The patch remains
`approved_for_test` pending explicit user acceptance of the composed pair.

### Pause Controls list v2 callers

The retained disabled shared UI helper established the intended Pause Controls
behavior: a shrink-only 216-unit box and a four-unit upward Y correction.
Bounded NA2 BTL inspection isolates two adjacent row calls using the confirmed
live mapping `0x006B3F00 + file offset`:

- the normal row at runtime `0x0087D6D8`, BTL file `0x1C97D8`, guarded by
  `1C090E0C00000000` (`jal 0x00382470` plus NOP);
- the selected row at runtime `0x0087D694`, BTL file `0x1C9794`, guarded by
  `E8090E0C00000000` (`jal 0x003827A0` plus NOP).

NA2 passes normal coordinates in `f12/f13`, but selected coordinates as integer
`a1/a2`, the text in `a3`, and red style `0xFF0000B4` in `t0`. The NUN5
homolog keeps the same row origin for both paths; selection changes style, not
position. The earlier accepted modal-alignment analysis independently proved
that NA2's selected shadow helper needs two local X units of compensation.

The v2 implementation hooks both BTL calls directly rather than re-enabling
the retained boot-ELF return-address multiplexer. Both adapters use
`caller_y - 4`, a 216-by-20 single-line left-aligned box, and the same
shrink-only fitting. The selected adapter also uses `caller_x + 2`, preserves
the native color, converts the prepared float origin back to the helper's
integer ABI, and tail-calls `0x003827A0`. The unchanged normal adapter
tail-calls `0x00382470`. The shared v2 core owns measurement, horizontal scale,
tracking, active-session publication, and restoration.
The accepted width table measures the two overflowing visible rows as
`Back to Game Mode Screen = 245` and `Back to Character Select = 231`, giving
scales `216/245` and `216/231`. The other four visible rows measure
`77`, `119`, `140`, and `124`, so they remain at scale `1`.

Deterministic generation produces separate normal and selected adapter/callback
fragments. Static tests verify both exact hook guards and targets, both callback
ABIs, the shared four-unit Y correction, selected two-unit X compensation,
216-unit width, 20-unit height/line height, preserved red style, and dependency
only on the accepted v2 core. At this accepted boundary no ss4
confirmation-body or Yes/No site was selected. Confidence is **high** for
caller isolation and the reconstructed contract. The user verified both the
normal ss2 state and corrected selected ss3 state on 2026-07-27; selection no
longer overflows or moves the row.

### Battle quit-confirmation ss4 callers

Clean NA2 BTL bytes and the task-owned ss4 state identify two distinct modal
draw calls. The clean BTL file uses `0x006B3F00 + file offset`:

- file `0x1C4048` / runtime `0x00877F48` is
  `800D0E0C00000000`, the native `jal 0x00383600` Yes/No list
  plus NOP;
- file `0x1C407C` / clean runtime `0x00877F7C` is
  `6C090E0C00000000`, the native `jal 0x003825B0` body draw
  plus NOP.

Earlier retained working notes named BTL `0x1C4008`/`0x1C403C` and ELF
`0x283814`/`0x283960`; direct clean-file guards prove those locations are one
displaced block early. Inside `0x00383600`, the exact selected and unselected
calls are instead ELF files `0x283914` and `0x283A60`, guarded by
`54E40D0C00000000` and `88E60D0C00000000`.

The modal object owns its Yes/No widget at `+0x110` and body widget at
`+0x114`. The list descriptor starts at X/Y `50/24`, uses row extra `12`, and
therefore draws its second row at Y `56`. Retained NUN5 measurements map Yes
to `(64.5,31.5)` and No to `(68.5,49)`. Because either row may be selected,
the smallest exact design scopes the complete list call, then adapts the two
shared inner calls only while that scope is active. The active word is saved
and restored, so nested drawing remains safe; both inner adapters are native
tail calls for every other screen.

The body helper builds its native record at X/Y `48/20`. NUN5 evidence retains
Y `12`; the accepted width table measures the Free Battle first line through
`and` as `420`, while adding `return` reaches `483`. A 420-unit, two-line
greedy wrapper therefore selects the observed break without storing an
authored newline in any canonical mapping. The adapter copies at most 255 source bytes to its
own stack, inserts newline bytes only into that draw-time copy, publishes the
v2 session around the native UI draw, and then discards the copy. Confidence
is **high** for offsets, guards, ABIs, isolation, and mapping neutrality.

Fresh post-change pairs cover all four Battle/Practice and Game
Mode/Character Select combinations. Every Current body starts at screenshot
X `101`, while every NUN5 body starts at X `72`; both first lines start at Y
`381`. Because the renderer uses the adapter's X directly inside the same
modal origin, the shared correction changes its local X from `48` to `19` and
leaves Y `12` unchanged. The same evidence exposes a separate dynamic
text-assembly defect: Battle says `Free Battle`, connective text is duplicated,
and the Japanese destination tail remains. String Translation corrected that
independent assembly in `277ecc1` by splitting the mode head, connective,
destination, and terminator; no canonical mapping gained an authored newline.
The user verified the combined fresh-build result across all four
Battle/Practice and Game Mode/Character Select combinations on 2026-07-27.
The shared quit-confirmation layer is therefore **runtime-proven** with high
confidence.

### Mode Select Return to Title confirmation caller

The 2026-07-29 remade ss1 pair isolates a second consumer of the accepted
C-owned Yes/No mapper. NA2 `FUN_00385C00` draws the confirmation sentence
through dedicated body renderer `FUN_003825B0` at boot-ELF file `0x285E68` /
runtime `0x00385D68`, then draws the live choice object `+0xCC` through
`FUN_00383600` at file `0x285E98` / runtime `0x00385D98`. The body call's
clean eight-byte guard is `6C090E0C00000000`; the choice call's is
`800D0E0C00000000`.

The earlier classification of object `+0xD0` as the visible body was wrong.
Live object inspection while the prompt was visible found its list empty.
Tracing forward identified `FUN_003825B0` as the first actual consumer: it
builds a four-word draw record from constants `DAT_005B1810` X `24` and
`DAT_005B1814` Y `16`, then calls native UI draw `FUN_00379A20`. This explains
why changes to the shared unselected-list adapter had no visible effect.

The existing scoped choice hook reuses Yes `(64.5,31.5)` and No
`(68.5,49)`; the user verified that normal-build top-selector result on
2026-07-29. The bounded body hook reuses the native-body C adapter only when
its exact text is `Return to Title Screen?`, selects a 420-by-40 one-line box
at local `(24,12)`, activates the accepted tracking-zero/plain-space state,
and applies no glyph scale. It deliberately leaves the Collection choice
scope inactive. In fresh 1750-by-1313 native screenshots, NUN5 body ink is
X `194..909`, Y `1042..1078`; unpatched NA2 is X `194..933`, Y
`1056..1091`; the runtime-injected result is X `194..909`, Y `1042..1078`.
Pixel counts are 6,049 versus 6,005, consistent with the small retained raster
difference while geometry is exact. The user verified the exact live body
result on 2026-07-31. Confidence is **verified** for the consumer, guard,
coordinates, and runtime geometry.

### Collection exit-confirmation body and choice list

The replacement 2026-07-30 ss7 pair isolates the Collection exit prompt in
clean NA2 `PRG/ETC.BIN` (200,448 bytes, SHA-256
`8FF3C6E1ED5CE2B093B0934C898C40D1CEEA0C20778C49CDA5591AAD02375C74`).
The retained Ghidra export identifies two body-draw paths and one bounded
choice-list path:

- clean address `0x006C6540`, file `0x12680`, calls the ordinary body renderer
  for object `+4`; its eight-byte guard is `6C090E0C00000000`;
- clean address `0x006C6560`, file `0x126A0`, calls the complete choice-list
  renderer for object `+8`; its guard is `800D0E0C00000000`;
- the render-state path repeats the body draw at clean address `0x006C8788`,
  file `0x148C8`, with the same `6C090E0C00000000` native-call guard.

The live ETC overlay includes a `0x40`-byte runtime header, placing the first
owner pair at `0x006C6580`/`0x006C65A0` and the render-state body call at
`0x006C87C8`. Editing only the first body hook left the visible prompt
pixel-identical. Exact live inspection then proved that `0x006C87C8` still
contained the native call; redirecting that second consumer through the same
C adapter moved the visible body immediately. Canonical edits therefore keep
both guarded body calls.

Normalized 640-by-480 captures measure Current's body ink at Y `386..401`
versus NUN5 `381..396`, with the same X origin. Current's selected Yes is at
X `282..317`, Y `123..136`, versus NUN5 X `299..336`, Y `131..144`;
Current's No is at X `284..306`, Y `166..178`, versus NUN5 X `306..334`,
Y `156..168`. Draw telemetry identifies the native Collection inputs as Yes
text `0x00604570` at local `(50,24)` and No text `0x00604568` at local
`(50,56)`. Their Y values are exactly the source keys already handled by the
accepted scoped mapper, whose retained targets are Yes `(64.5,31.5)` and No
`(68.5,49)`. Collection therefore needs no new choice formula.

The bounded implementation routes both body calls through one C adapter using
the native UI-draw ABI, local origin `(24.8,12)`, native horizontal scale, a
400-by-60 box, 20-unit line height, and a two-line limit. It preserves the
literal separator between differently colored words. The choice call scopes
the existing mapper with Collection-local Yes `(64.2,29.85)` and No
`(68.1,48.2)` targets. Every other ETC body/list caller and ordinary Yes/No
list remains native.

At the final 1769-by-1327 live-edit capture, scaled NUN5 black ink targets
X `196..680`, Y `1054..1096`; NA2.28 matches those bounds exactly. Scaled NUN5
red ink targets approximately X `350..649`, Y `1052..1090`; NA2.28 measures
X `350..648`, Y `1053..1089`. The user verified the exact live result on
2026-07-31. Status is **runtime-proven** with verified confidence.

### Collection fixed-cadence list wrapping

The replacement 2026-07-30 ss8-ss10 pairs isolate the Collection Movie and
character-detail lists. Bounded NA2 ETC inspection identifies
`FUN_006B4D30`; its shared active row draw is runtime `0x006B4ED8`, file
`0xFD8`, guarded by
`10E40D0C00000000` (`jal 0x00379040` plus NOP). The NUN5 homolog
`FUN_006C7CA0` replaces the corresponding draw at ETC file `0x1164` with its
boxed renderer at `0x0038A210`.

NUN5 stores the active box width and height in each list structure at
`+0x14/+0x18`. The supplied states prove a 192-by-32 box for ss8 Movie titles,
a 152-by-32 box for the ss9 move list, and a 192-by-32 box for the ss10
relationship list. Every family uses native X, native Y minus 10, two lines,
and a 16-unit line interval. The outer list retains fixed row cadence; wrapped
titles occupy two lines inside their existing row rather than increasing later
row positions. Exact visible breaks include:

- `Sealing Jutsu: Nine` / `Phantom Dragons`;
- `People of Endless` / `Darkness`;
- `Ninja Art: Beast` / `Scroll Replicas`;
- `Fourth Awakened` / `Mode`;
- `Shadow Clone` / `Jutsu`;
- `Unchanging` / `Relationship`.

NA2's ss9 parent at `0x00C8D110` points to list head `0x00C75C00`; the visible
text pointers are `0x006D9BD8` (`Right!`), `0x006D9C00`
(`Shadow Clone Jutsu`), and `0x006D9C40` (`Running Wild`). Its ss10 parent at
`0x00C9BDE0` points to list head `0x00C79EE0`; the visible text pointers are
`0x006DC340`, `0x006DC370`, `0x006DC3A0`, and `0x006DC3C0`. The corresponding
NUN5 parents are `0x00C0BCA0` with width 152 and `0x00C1C630` with width 192.
The NA2 structures do not retain homologous usable box fields at the NUN5
offsets, so copying those offsets is not a valid implementation.

The bounded implementation accepts Movie-title pointers in
`0x003FFAA0..0x003FFC10` plus only the seven exact ss9/ss10 character-detail
pointers above, copies the source to a transient buffer, and reuses
`font_v2_wrap_native` with a two-line limit. It draws each resulting line
through the displaced native renderer at a 16-unit interval. That separate
line draw is required because passing the inserted newline to NA2's native
renderer produces a 25-unit interval on these screens. Short titles, the
highlighted red style, fixed caller cadence, source mappings, and every
other pointer through the shared renderer remain native.

The first shared implementation nevertheless published a 20-unit glyph-quad
override for every recognized pointer. It also exposed the flag-aware
right-edge shim defect described below. The compatible task ISO's payload
SHA-256
`74A2A4BD0E66C0F4C55C5A0F67A2342D2E0DE01768D2D2416B945E64D2C0EB39`
still used the older 88-byte shim at runtime `0x008F57B8`, while rejected
integrated build record `20260730_162124_431_pid9072` linked the 128-byte
flag-aware shim at `0x008F5E30`. The older shim ignored flag `0x40`, so direct
injection appeared correct while the integrated payload squeezed the same
rows. This was a resident-hook difference, not a screenshot-composition
difference or a change in the Collection caller.

The corrected Movie-only branch now returns directly to the displaced native
draw when wrapping produces one line. When wrapping produces two lines, it
retains the proven 192-unit width, native X, Y-minus-10 origin calculation, and
16-unit line interval but does not publish the glyph-quad override. The fixed
right-edge shim now makes that clear flag effective. A supplied-ss8 regression
through the fixed shim reproduced the complete retained accepted right text
panel pixel-for-pixel.

The corrected character-detail branch uses the same separation. It retains
`glyph_height = 20.0` solely in `font_v2_prepare`'s two-line
`rendered_height` calculation, which preserves the accepted vertical centering,
but no longer publishes flag `0x40`; the glyph quads therefore remain native.
Fresh supplied-ss9 and ss10 direct-injection captures through the corrected
shim reproduce the accepted ss9 target and retained ss10 target exactly for
every text group. ss9 target/corrected bounds and dark/red glyph-pixel counts
are identical: `Right!` `(646,241)..(734,267)`, `Shadow Clone Jutsu`
`(648,296)..(871,345)`, and `Running Wild`
`(648,376)..(843,401)`. ss10 likewise matches exactly for
`Great Ball Rasengan`, `Overflowing Power`, `Nine-Tail's Cloak`, and
`Unchanging Relationship`. Non-text animation pixels may differ between fresh
frames; the text evidence is native-resolution. The user explicitly accepted
the ss9 target appearance on 2026-07-30; exact integrated-ISO confirmation of
the corrected payload remains pending.

The supplied ss8 state was reloaded through the standard task-owned direct-PINE
workflow after compiling the canonical C. The retained runtime-injected
candidate at
`work/Font/artifacts/priority5_movie_list/rework_2026-07-30/`
shows the four exact breaks above, native-height one-line rows, and native
glyph geometry on the wrapped rows. Its screenshot SHA-256 is
`E26CA0B3F66E413CE55EBA562C7760E6EF539CE6A6096D327D6006510E0391E5`;
the injected fragment SHA-256 is
`1BBA7F25F2CEB3E887B8AB101D36BAF80AD7B531667DC01566F657E1BE7DC06C`.
The user subsequently verified the exact integrated-ISO result on 2026-07-30.
Confidence is **verified** for the bounded Movie branch and runtime appearance;
status is **runtime proven**. The character-detail branch is
**runtime-injected candidate validated** with a user-accepted target and still
awaits exact integrated-ISO confirmation.

### Character Select modal selected row, return body, and choice list

The refreshed 2026-07-29 ss5-ss7 pairs isolate two main-ELF callers inside
the Character Select modal family, and the replacement 2026-07-30 ss1 pair
isolates its remaining return-confirmation list caller:

- file `0x2BC984` / runtime `0x003BC884`, guarded by
  `84090E0C00000000`, draws only the selected row in the five-row
  `Back to Game Mode Screen` modal;
- file `0x2BCAAC` / runtime `0x003BC9AC`, guarded by
  `800D0E0C00000000`, draws the complete top Yes/No list for the return
  confirmation;
- file `0x2BCB54` / runtime `0x003BCA54`, guarded by
  `C4080E0C00000000`, draws only the `Return to Game Mode Screen?`
  confirmation body.

The selected-row adapter uses a 240-by-20, single-line, shrink-only box at the
caller's Y and five local units to the right of its incoming X. The original
declarative selected-delay-slot compensation is removed because the symbolic
eight-byte hook replaces that call and delay slot atomically. The final ss5
red-ink bounds are `x=170..466`, exactly matching NUN5. The supplied ss6
Linked Mode state remains unchanged, proving that the selected hook does not
select the adjacent ordinary-row family.

NUN5 telemetry for the confirmation body is box `(8,8,368,24)`, horizontal
policy `2` (center), vertical policy `1`, and incoming scale `1`. A first C
candidate applied only those box dimensions while retaining NA2's existing
primary/direct renderer setup. It fit, but its letters stayed visibly smaller
and narrower than NUN5. That negative result proves that box math alone does
not select the expected glyph presentation.

The accepted sequence selects the secondary renderer through
`FUN_00186510(renderer,1)`, restores renderer fields `+0x28/+0x2C`, sets the
draw context from the modal object at `+0x74` through `FUN_001866D0`, then
uses the resident v2 measurement to compute the centered left edge inside the
368-unit box. The final callback draws from that prepared left edge through
native left draw `0x00379040`. Calling the native centered primitive instead
is rejected here: it remeasures with obsolete state and shifts the otherwise
correct result left.

For the exact accepted string, both NUN5 and NA2.28 black-ink bounds are
`(151,328)-(484,341)`; dark-pixel counts are `1209` and `1202`. The retained
comparison is
`work/Font/artifacts/priority3/ss7-secondary-renderer-left-edge-comparison.png`.
The user accepted that lower confirmation body as good enough on 2026-07-30.

The same replacement-batch ss1 proves that the body remains correct while the
native top Yes/No list does not share NUN5's relative placement. Redirecting
only file `0x2BCAAC` to the existing
`localization.font.v2.quit_choices_scope` reuses the already-proven Yes
`(64.5,31.5)` and No `(68.5,49)` map without introducing another C formula or
assembly fragment. A hidden direct-PINE trial loaded the supplied ss1,
installed only that guarded call, and produced a native 640x480 capture. The
modal boxes have different absolute X positions between games, but both
Current rows then have the same X/Y offsets from their respective modal
origins as NUN5. The accepted lower body remains unchanged. This selector
result is agent-validated and awaits explicit user acceptance.

Confidence is **verified** for the three call sites, renderer selection,
coordinate contracts, caller isolation, and supplied-state behavior. User
acceptance currently covers the lower confirmation body, not the new top
selector result.

### Practice explanation mixed-text wrapping

Bounded NA2/NUN5 BTL comparison identifies the Practice explanation loop as a
separate caller family from the title draw immediately before it. NA2 reaches
the loop at BTL file `0x1C4BA0` / runtime `0x00878AA0`; NUN5 instead assembles
one bounded mixed text/tag string, installs a call-local metric/draw callback
pair for controller tokens, and passes the complete result through its wrapping
renderer.

The v2 adapter follows that broad caller logic rather than patching individual
rows. It builds a single 512-byte buffer from the caller's text and token
records, word-wraps it with the accepted proportional metric table, and uses a
364-by-48 box at X `39.2` and caller Y plus `21.2`. The glyph height is 28 and
the independent line advance is 14. The line-count field is zero, meaning
unlimited: the supplied NUN5 `ss3` Flee row proves that this nominal 48-unit
box legitimately carries three explanation lines, so the earlier two-line cap
was rejected before promotion.

The callback map preserves all 13 Practice controller tokens. D-pad directions,
Circle, Triangle, Square, Cross, plus, L1, R1, L2, and R2 use NA2's native icon
table and native draw helper; the adapter selects the caller's primary or
secondary icon object exactly as the original path does and applies the
NUN5-proven per-token Y offsets. Metric and draw callbacks, both icon objects,
renderer tracking, horizontal scale, and the prior active session are restored
after every call.

Supplied Practice slots 2-7 were converted with exact source hashes and guarded
memory edits because a savestate restores its captured BTL overlay and resident
RAM over the worker ISO. The converted task-owned states and manifests are
under
`work/Font/artifacts/autofit_v2/practice_explanations/`. Hidden 640x480
captures show:

- `ss2`: the Manual Linked Attack explanation wraps to two lines;
- `ss3`: Flee wraps to three lines with D-pad, plus, and Cross intact;
- `ss4`: substitution, recovery, and extra-hit rows retain shoulder, face,
  D-pad, and plus icons;
- `ss5`: Circle and D-pad rows align; Current `Charge` versus NUN5
  `Charge Chakra` is a separate text-mapping difference;
- `ss6`: movement rows preserve D-pad, plus, and Cross alignment;
- `ss7`: Shadowblur wraps to two lines while Circle, shoulder, D-pad, and plus
  icons remain aligned.

Across all six pairs, wrapping, line spacing, X/Y placement, and inline-icon
alignment match the NUN5 reference. Separate Controls and Command Chart
captures retain their accepted label and title behavior. The blank 2P Controls
column reproduced from the untouched source state and remains known
state-resume behavior rather than a renderer regression.

The isolated worker ISO has SHA-256
`D624C39F0132FF5ED3BA4D60E99B78113AF85805D3870B072643B9400CC2B10B`
and boot CRC `A85C52F7`. Its 7,536-byte resident payload ends at `0x008F5A70`
and has SHA-256
`47EF54100642B25366FADF4A0D5C12B7255D3CF89456BD3F3DB5ACB056ED1101`.
The generated 4,084-byte v2 asset has SHA-256
`382AD202C1225326B59832BECE7A8AE61A2A69870B18B17D1F606B6C5152BE90`.
Deterministic fragment and relocation tables have SHA-256
`22F728E0C5E4AE279F8DE719636E1301CAB482891DDE6FAECA3BEDEE96D7EC84`
and
`CB45E870106EF9E95C29947922BEC5F4CC640DBCE044CC2AA9AEC8F60BA703C4`.
The grouped comparison sheets are
`work/Font/artifacts/autofit_v2/practice_explanations/report/practice-explanations-02-04.png`
and
`work/Font/artifacts/autofit_v2/practice_explanations/report/practice-explanations-05-07.png`.
The family is runtime-proven and enabled; the grids still await user
acceptance before work begins on another caller family.

Commit `e906ce0` placed the complete helper block at runtime
`0x003D3E00..0x003D4388` (file `0x2D3F00..0x2D4488`) inside the larger
common-zero interval `0x003D3DB6..0x003D5D30`. That interval is zero in the
clean ELF and was zero in all 16 states then sampled. A disposable ISO marker
audit also proved that markers at its start, middle, and end survive after a
fixed five-second boot settle. PINE becomes ready while the large boot ELF is
still being copied, so immediate reads of high file-offset caves can
transiently return zero and are not valid placement evidence. The later
Load-screen evidence below proves that boot-settle and sampled-screen survival
were nevertheless insufficient: the game clears this whole interval during a
transition that the original regression did not cover. Runtime scratch was
placed in the independently state-zero range `0x003FAD18..0x003FAE44`.

A full ten-state guarded regression covered Practice pause, Controls, Command
Chart, command explanation, Practice settings, Practice quit, character
return, Collection quit, Collection movie, and the no-memory-card prompt.
Controls and the wrapper-owned Practice/confirmation families retained their
matched results. Command explanation, Collection movie, and no-memory-card
overflow were separate unresolved caller families at that historical
boundary; their unchanged defects were not regressions from this port. The
later dedicated Collection Movie-list work resolves that family as documented
above. Confidence is **high** for the shared
measurement formula, hook boundaries, caller guards, and matched horizontal
result. That regression did not cover entry into Save/Load and therefore did
not establish persistent ownership of the helper interval.

### 2026-07-25 confirmed Load-screen helper erasure

The user captured a state after the game froze while entering the Load screen.
The source was read from
`@pcsx2_stable/sstates/SLOP-NA228 (682CC5FB).01.p2s`, copied without modifying
the user library to
`work/Font/inputs/sstates/load_freeze/user/SLOP-NA228 (682CC5FB).01.p2s`,
and has SHA-256
`67B9329411667E32211B4FAA319ADCF3EF255362FD26C8DF70AFA475D8937644`.
Its embedded screenshot shows the two Load-screen panels before any text was
drawn.

Offline comparison against the same-CRC pre-Load state
`work/Font/artifacts/load_freeze/crash_state/pre_load_same_crc.p2s`, SHA-256
`B20EF54A12952C0A30BD2907E2FD9B6B1B98961620E72658A62B2B2BC7001E0F`,
establishes the failure:

- the pre-Load state matches 19 of the 20 exact canonical Font ELF edits; its
  only mismatch is the separately initialized scale word at runtime
  `0x0060737C`;
- the frozen state still matches all permanent hooks and ordinary ELF edits,
  but all six injected helper/trampoline edits are entirely zero:
  `font_layout_wrappers_01..04`, `font_controls_auto_fit_10`, and
  `font_renderer_metrics_01`;
- the frozen state's zero run is exactly
  `0x003D3DB6..0x003D5D30`, 8,058 bytes, which is the whole clean-file
  common-zero interval containing every new helper;
- the UI scratch record at `0x003FAD20..0x003FAD60` is also zero, but no
  scratch corruption is needed to explain the freeze.

The permanent UI, selected-choice, ordinary-space, and newline hooks therefore
survive while their destinations at `0x003D3E00..0x003D4388` disappear. A
hook entering that range executes zeros instead of a returning helper, which
explains the blank Load screen and hang. Confidence is **high**: the
same-CRC before/after states distinguish transition-time erasure from an ISO
that never contained the blobs.

This rejects the helper interval as persistent executable storage. Do not
reuse it or select another boot-settled zero cave by sampling alone. The
matched renderer formulas and layout decisions remained valid and were
relocated through the shared resident payload as described below.

### 2026-07-25 resident relocation and regression

All executable Font helpers and trampolines are now feature-owned
`runtime_injector` fragments linked by the shared payload builder into
`PRG/228.BIN`. The feature declares symbols and relocations but no payload
offsets or final runtime addresses. The UI helper also replaces the former
global scratch record with a 64-byte call-local stack frame, so neither code
nor transient wrapper state depends on the erased ELF interval.

The canonical resident-only link at load base `0x008F3D00` places the nine
Font fragments in `0x008F3D50..0x008F42A0`. The complete profile then appends
its external-string fragments in the same shared image. Eight guarded boot-ELF
hooks target these symbols:

- ordinary space and newline at file offsets `0x893EC` and `0x88704`;
- normal right-edge, inline-markup half-space, and ordinary glyph advance at
  `0x88070`, `0x88B7C`, and `0x897D8`;
- the Controls wrapper at `0x288848`;
- selected-choice and shared-UI wrappers at `0x279250` and `0x279B20`.

The horizontal-scale fragment has three intentional entrypoints. The normal
right-edge hook targets the fragment start, the inline-markup half-space hook
targets `+0x18`, and ordinary glyph advance targets `+0x2C`. An initial
resident link incorrectly sent all three hooks to the fragment start. Runtime
bisection proved the first two hook families independently safe and isolated
the third as the crash trigger. Restoring addends `0x18` and `0x2C` fixed the
failure; canonical tests decode all three linked jump targets so this mistake
cannot recur.

Historical accepted states contain the old complete payload and cannot safely
receive a newly built whole-profile image at the same address: doing so
overwrites live external strings and unrelated state. For the relocation
regression, a Font-only 1,440-byte test image was linked after the old payload
at runtime `0x008F4500`, and only the eight exact Font hooks were converted.
This preserved every old string address while exercising the new helpers. A
broader state conversion was rejected after proving that nominal ELF file
offset `0x2F79F4` contains mutable live data in a running state and therefore
must not be treated as an immutable boot constant.

All ten matched Font states then loaded and rendered without a guest pause or
crash. The accepted Practice, Controls, character-return, and Collection
layouts were retained. Three apparent capture differences were reproduced by
loading the untouched original states under the same task clone: the blank 2P
Controls label column, the one-line Practice confirmation-body rerender, and
the no-memory-card state advancing to the Japanese safety screen. They are
state-resume behavior, not resident-code regressions.

A fresh canonical worker ISO independently survived entry from a current-build
title state into the real Load menu with the actual integrated `PRG/228.BIN`.
The final isolated ISO has SHA-256
`1390892232BFB3F90F4F069F6CB268271ED553FFE016608652ED989256F05DF5`
and boot CRC `D64F4AC7`; its 2,960-byte resident payload has SHA-256
`3874853A22B597E8B035041BB439EC6AB0F1A53B8808C9A4FC2C9522B11A2693`
and spans runtime `0x008F3D00..0x008F4890`. Five seconds after a recorded
Cross confirmation, the captured Load screen contains all three save rows,
dates, play times, and the instruction panel. PCSX2 reported no TLB miss,
guest crash, or unexpected pause before the recording reached its configured
frame limit. This proves that the replacement code remains resident across the
transition that erased the old ELF cave.

The integrated build record is
`work/Font/logs/builds/20260725_090026_130_pid29660/`; the fresh title state,
Cross recording, and Load capture are under
`work/Font/artifacts/load_freeze/resident_relocation/final_runtime/`. A state
captured after the old hook had already entered erased code cannot be repaired
by applying the new hooks after load; execution must start before that
transition.

The ten converted captures and the untouched-state controls are retained under
`work/Font/artifacts/load_freeze/resident_regression/` for comparison while the
remaining caller families are implemented.

### 2026-07-28 accepted remaining-layout C migration

The remaining v2 behavioral layout implementation can be expressed as ordinary
EE C without changing its canonical payload symbols or guarded game hooks.
The candidate compiles Pause Controls, Quit scope/choice mapping, native
measurement and greedy wrapping, Quit/Special Controls body construction, and
Practice mixed text/icon flow into relocatable runtime-injector fragments.
Native renderer tail calls, live-register entry capture, and the five
displaced-instruction hooks remain small assembly bridges because they encode
game-specific ABIs rather than layout policy.

Manual disassembly established a reusable EE compiler ABI requirement: this
toolchain passes integer arguments five and six in `t0` and `t1`. A first shim
draft incorrectly used caller-stack slots; it was rejected before canonical
generation. The corrected selected-Pause bridge leaves the live color in
`t0`, while the Practice bridge moves its secondary object into `t0` and the
native Y float bits into `t1`.

The accepted implementation contains 49 v2 fragments in 5,924 bytes, SHA-256
`7F021178787EA9A845EED8AE348B731345C3459BF1AF29D48CA02B26E84D5F28`.
The separate 188-byte numeric formatter is unchanged. Static evidence covers
compiler extraction, supported relocations, exact exported-symbol closure,
session/frame offset assertions, bounded buffers, package loading, and the
combined feature hash. The normal build promoted Current CRC `12369AA2`; the
user manually regressed every affected caller family and reported `no diff`.
Only after that explicit acceptance were permanent tests updated. They protect
the relocatable C and native-ABI safety contracts without freezing compiler
hashes or old assembly layouts; focused tests pass 11/11 and the full builder
suite passes 201/201.

## 2026-07-30 Linked Mode center-selector isolation

Replacement-batch ss2 identifies the center-screen `Linked Mode`, `Manual`,
and `Auto` selector as main-ELF `FUN_003B8F40`. This is not the adjacent
five-row character-modal family: trial changes to that family left ss2
unchanged, while three exact writes in `FUN_003B8F40` moved only the visible
center modal.

The title path loads local Y `12.0` at runtime `0x003B8FE0` (ELF file
`0x2B90E0`) before its ordinary renderer call. The choice loop loads base Y
`48.0` at runtime `0x003B90A4` (file `0x2B91A4`) and retains a native
`48 + 26*i` formula. Its selected renderer call is at runtime `0x003B90DC`
and its unselected call is at `0x003B90FC`.

NUN5 homolog `FUN_003CBAF0` uses one selected-state-aware
`FUN_00393210` call with local formula `36 + 22*i`. The helper semantics differ
from NA2's separate selected and ordinary renderers, so copying those two
constants directly is not coordinate-equivalent. Supplemental ss2 with
`Manual` selected supplies both NA2 paths in one frame. The earlier
`44 + 26*i` candidate plus selected-only `-2` compensation put selected Manual
five pixels too high and ordinary Auto five pixels too low at 640x480.

The corrected bounded formula is `46 + 20*i`, with no selected-only
compensation. The title remains at local Y `8`. Fresh pixel bounds are:

- title: NUN5 and Current both Y `138..151`;
- selected `Manual`: NUN5 and Current both Y `183..196`;
- ordinary `Auto`: NUN5 and Current both Y `211..223`.

The exact clean guards are title `4041023C`, interval `D041023C`, and base
`4042023C`; replacements are `0041023C`, `A041023C`, and `3842023C`.
No shared renderer or adjacent modal is changed. Confidence is high for caller
isolation and placement; explicit user acceptance remains pending.

## 2026-07-30 Character Select ordinary-row metric session

Supplemental ss1 reopens only the five-row player-mode list inside
main-ELF `FUN_003BC780`. NA2 draws its selected entry through
`FUN_00382610` at runtime `0x003BC884` and every ordinary entry through
`FUN_00382470` at runtime `0x003BC8BC` (ELF file `0x2BC9BC`, clean guard
`1C090E0C00000000`). NUN5 homolog `FUN_003CF3F0` instead routes both states
through one `FUN_00393210` helper, with native local Y values `0`, `24`, `48`,
`72`, and `106`.

The existing selected hook already enters the accepted 240-unit v2 metric
session and applies a five-local-unit X correction. Ordinary rows bypassed that
session, so their Y bounds were already exact but their visible widths were
eight or nine pixels too large and their left edges were six pixels too far
left. A second caller-specific C entry now gives only the ordinary draw the
same metric session and X correction, then returns through the original
ordinary callback. It does not alter the row table, selected renderer, Linked
Mode, or confirmation callers.

At 640x480, the three ordinary comparison rows now have exact NUN5 bounds:
`(259..377,206..219)`, `(257..379,236..249)`, and
`(246..390,266..279)`. The selected first row remains on its prior accepted
path. This proves that the discrepancy was session selection rather than
per-row Y drift or a need for individual scale constants. Confidence is high;
explicit user acceptance of the refreshed five-row list remains pending.

### 2026-07-28 accepted Ninja Song numeric C migration

The accepted Ninja Song formatter contract can also be expressed in ordinary
EE C without changing its five BTL callers or public payload symbol. The
native call sites supply the numeric value in `a1`, requested width in `a2`,
destination in `a3`, and padding mode as the fifth EE EABI integer argument in
`t0`. Compiled disassembly confirms the C entry saves those live values before
calling its only external dependency.

The sole retained assembly fragment is a 20-byte ABI bridge for NA2's native
variadic formatter: it moves the C callback's value from `a1` to `a2`, loads
the immutable ASCII `%d` string at `0x006042D3` into `a1`, and tail-calls
`sprintf` at `0x0017BCA0`. The 184-byte C fragment plus this bridge produce a
204-byte numeric asset with SHA-256
`8043B1393F6D901FC91DF6BB4BFC8AB4D2800F7FD9E17CA4EEE2C4C34992A9F6`.
The prior 188-byte handwritten implementation is superseded as executable
input but remains recoverable from Git history.

Static confidence is high: the compiler emits one explicit relocation to the
bridge; its 16-byte decimal buffer is disjoint from the saved-register area;
the accepted space, no-padding, and zero-padding modes are retained; and the
native decimal length remains the public return value. The normal build
promoted Current CRC `12369A62`; the user manually checked the supplied Ninja
Song ss2–ss5 screens and reported that the result is good. Permanent tests
were updated only after that acceptance.

This migration does not cover the separately accepted Save/Load date/time and
Battle Settings Time ASCII conversions. Those remain guarded in-place MIPS
instruction patches generated by their dedicated scripts. They are not
standalone resident helpers, but they do encode behavior; therefore the final
structural C cleanup must not classify them as migrated or remove their
generators without an explicit decision.

## 2026-07-19 superseded clean-font baseline

This earlier baseline started from clean NA2, not from m01, v22, v23, or the
rejected semantic-palette candidate. Static inspection established a
coherent 10x22 bitmap font with 157 cells and complete printable-ASCII
coverage: 95/95 semantic slots exist and 94/94 non-space slots contain visible
raster data. The median visible glyph box is 6x14 pixels, with median top 4 and
bottom 17. Matched runtime captures confirmed that this asset was serviceable,
but the later accepted native baseline superseded its unchanged-GF4 result.

The isolated descriptor-height experiment at ELF file offset `0x88064` is
rejected. Changing `0C 00 20 C6` to `10 00 20 C6` did not make a Y-only
correction. With the clean descriptor it produced a 28x28 quad instead of the
untouched 24x24 quad, stretching both axes by 16.7 percent while logical
measurement stayed unchanged. Runtime captures showed damaged outlines and
no useful alignment improvement. The rejected edit is retained in Git history
and is deliberately absent from the executable package.

The accepted patch set has two independent `runtime_proven` components:

- `font_controls_auto_fit` affects only the first eight Controls action-label
  calls plus the local Controls row origin. Clean plain-ASCII measurement is
  `9.5 * byte_count + 1`; strings below 14 bytes retain horizontal scale
  `1.0`. `Linked Attack` is 13 bytes and therefore stays full width. For an
  overflowing string the helper applies `128 / measured_width`, corrects the
  centered origin, draws through the original helper, and restores scale
  `1.0`. The ninth `OFF` call remains on the ordinary renderer. The row origin
  changes from 48 to 50, retaining the original 26.8-unit interval.
- `font_layout_character_modal` uses measured X values `84, 79, 79, 75, 13`, moves
  the first four rows down one local unit, places the red row at local Y 117,
  and compensates the selected shadow path by two X units.

The official 19-byte `Ultimate Jutsu Prep` runtime probe measures 181.5 units
and uses scale `256 / 363`, approximately `0.705234`. Its final clean-NA2 ink
box is `(74,98)-(236,114)`, center `(154.5,105.5)`, compared with NUN5
`(76,99)-(233,115)`, center `(154,106.5)`. It fits without clipping; the
remaining five-pixel width difference is clean glyph appearance rather than
placement. `Linked Attack` retains width 147 and `OFF` width 30, with no
horizontal scaling.

The four ordinary character-modal centers are `(318.5,182)`, `(319,212)`,
`(317,242)`, and `(318.5,272)`; NUN5 is `(318,182)`, `(318,212)`,
`(318,242)`, and `(318,272)`. The selected red row is exact at
`(319,314.5)` in both. The accepted compact-table capture is byte-identical to
the independently tested dynamic-centering proof.

The patch set preserves the 5,273,256-byte ELF size. Applying it to the verified
clean ELF produces SHA-256
`3338654A24BCFCC5E101654A93E585335A9A9ECEE607AC018F43D0E54FD14217`.
The Controls helper SHA-256 is
`B26071C654C90085B78BC528E187E2D7BD74CE78363319C21CE30E45B54A13F3`;
the tail derivation SHA-256 is
`BF51639A21D85CD8A09D411B5F069099871E523E56736A06B363F7F785B65C0E`.
The exact guarded captures and generated measurements remain under
`work/Font/analysis/runtime_compare/`, and the clean apply log remains under
`work/Font/verification/font_package_v2_log/`.

The integrated profile build is retained at
`@logs/na228/builds/20260719_202514_393_pid36044/`. It selected the two accepted
Font patches, preserved the QoL module hash, promoted an updated Current ISO,
and recorded Font's clean-to-patched ELF hashes above. The resulting Current
ISO SHA-256 is
`4273E20D03642CB287C4F3F7ECCA56E46B4CE412E627D6C006980A9EE61B45AB`.
A controlled clean boot reported `SLPS-22228`, CRC `F3F4C52B`; read-only PINE
verification matched all 78 changed Font words and confirmed the rejected
quad-height word was absent.

## Historical v23 zero-tracking negative result

The test changed `SLPS_258.37` at file offset `0x866E0` from
`80 BF 02 3C` to `00 00 02 3C`. The intended effect was to match the NUN5
ASCII-mode horizontal-tracking initialization (`0.0` instead of NA2's
`-1.0`). The user observed no meaningful visual improvement over the preceding
v22 state: English text remained oversized/chunky, spacing remained
inconsistent, and long Controls-menu entries remained clipped.

Do not repeat this single-field tracking patch as a standalone fix. It does
not prove that tracking or `FUN_00186510` is irrelevant; later analysis showed
that tracking zero must be paired with the correct ordinary-space and boxed
measurement behavior. The deleted one-row patch log and comparison screenshot
remain recoverable from commit `55d1163`.

Surrounding confirmed observations:

- NA2 and NUN5 `GF4C.BIN` are both 104 bytes but diverge from offset `0x28`; the v22 and v23 experiments used the NUN5 variant. Its independent functional significance remains unproven.
- Replacing NA2 GF4 with the exact NUN5 GF4, padded or unpadded, produced broad spacing but patchy glyph rendering and could disrupt PNACH behavior. Do not repeat that direct swap as a new hypothesis.
- The v22 state was clean and closer to NUN5, but glyphs could touch or overlap and long text still clipped.
- The retired declarative m01, m02, v22, v23, and semantic-palette records are
  recoverable from commit `55d1163`. Their useful conclusions are consolidated
  in this document; none is an active patch set or implementation parent.

The remaining font work still separates into glyph appearance, positioning/advance behavior, and missing NUN5-style auto-fit/squish. Reuse applicable historical evidence from Git history and maintain current analysis under `@analysis/disassembly/NA2/` and `@analysis/disassembly/NUN5/`, never under `@source/`.

Relevant static-analysis leads retained from the investigation:

- NA2 ASCII setup: `FUN_00186510`.
- NUN5 counterpart: `FUN_001878e0`.
- NUN5 boxed auto-fit: `FUN_00389df0` and `FUN_0018b1b0`.
- NA2 menu path: `FUN_003885b0`, which calls `FUN_00379240` and appeared to draw/center without the corresponding 128-pixel auto-fit path.

## 2026-07-19 Controls auto-fit negative result

A temporary size-preserving ELF experiment applied NUN5's shrink-only
`128 / measured_width` rule to the two text calls in NA2
`FUN_003885b0`. The test used a Controls-only wrapper plus shared horizontal
renderer hooks for the leading bearing, glyph X geometry, space advance, and
normal glyph advance. It changed no GF4 or GF4C bytes. The composed test ELF
was 5,273,256 bytes with SHA-256
`483CE707B4B42C0194A696F78EB99FB291D11BF4E038FE4B3DAC2DAD2D48420C`.

Runtime comparison rejected the experiment. NA2 visibly narrowed
`Linked Attack`, while the same exact text remains full width in NUN5. NUN5
does not special-case that label: its first eight Control Settings action
labels all use a 128-pixel box through
`FUN_00399df0 -> FUN_00389df0 -> FUN_0018b1b0 -> FUN_0018ca40`.
NUN5 measures horizontal text through `FUN_0018b7f0`; the temporary NA2
wrapper instead used the legacy
`FUN_003798e0 -> FUN_001859a0 -> FUN_00184e60` measurement path. Copying the
box threshold and scale formula therefore made a different fit decision.
NUN5 also renders the final `OFF` row through ordinary `FUN_00385df0`, while
the rejected experiment routed both NA2 call families through its wrapper.

The captured NA2 screen also confirms that visible font alignment is not yet
equivalent to NUN5. Vertical baseline errors are mostly independent of a
horizontal width test, but left bearings, tracking, glyph advances, and
centering directly affect both the logical measured width and its relationship
to visible glyph bounds. The temporary rows and profile selection were removed
after that review.

The accepted implementation above resolves this negative result without
reusing its legacy measurement call. It proves the clean fixed-ASCII formula,
keeps the 13-byte threshold decision correct, scales the three horizontal draw
surfaces through one per-call factor, and restores that factor immediately.
The failed threshold-only wrapper remains useful evidence: do not reinstate it
or treat a box constant alone as a valid fit port.

## 2026-07-19 rejected semantic NUN5 appearance experiment

Matched 1708x1281 captures of the Control Settings screen separate the current
defects. For the same `Attack`, `Item Use`, `Item Select`, and `Linked Attack`
labels, visible widths are already close to NUN5, but the NA2 main-row ink is
31 pixels high instead of 36, its bottom edge is consistently 8 pixels too
high, and its horizontal center drifts farther left as the string grows. The
four-label center error fits approximately `8.6 - 7.38 * character_count`
pixels (`R^2` about 0.98). The static `SELECT button: Return to Defaults`
legend is essentially the same 832x38 versus 831x38 appearance but is 99
pixels farther right in NA2. These measurements identify separate raster,
vertical-placement, and logical-advance/centering problems; fixing weight
alone cannot establish alignment parity.

Static structure establishes a safe size-preserving NUN5 data experiment.
NUN5's single GF4 descriptor contains 223 14x20 cells with a 140-byte stride;
the accepted m01 descriptor reserves 123 cells at NA2 `0xD9240`. A literal
copy of NUN5 cells `0..122` is nevertheless invalid. Both parsers map printable
ASCII directly as `byte - 0x20`, but NUN5 cells `59..64` and `91..94` are blank
or have different semantics. That blind copy would remove the brackets used
by `[S]` mappings and other translated-English punctuation. NUN5 also stores
the literal at-sign in cell `63`, while NA2 printable ASCII addresses cell
`32`. The direct first-123 candidate with GF4 SHA-256
`8E426B252D45B735D78A3D64657BE8E37F4856150D454314F67DAFF8D48C203D`
was therefore rejected statically and must not be restored.

The corrected `font_nun5_appearance` patch imports exact official NUN5 cells
and metric rows for the same-semantic ranges `0..31`, `33..58`, `65..90`, and
`95..122`. It relocates exact NUN5 source cell and metric row `63` to NA2
destination cell `32`. Cells `59..64` and `91..94` retain their accepted m01
glyph shapes and metrics. Their bitmap indices are deterministically converted
from the m01 palette to the NUN5 palette with this mapping:

`0->0, 1->1, 2->2, 3->3, 4->4, 5->5, 6->8, 7->7, 8->8, 9->B, A->A, B->C, C->F, D->F, E->E, F->E`.

The exact official raster and metric operations are:

- cells `0..31`: NUN5 raster `0x4C..0x11CC` to NA2
  `0xD9240..0xDA3C0`; NUN5 metrics `0x7BE8..0x7C68` to NA2
  `0xD59E0..0xD5A60`;
- cell `32` from source cell `63`: raster `0x22C0..0x234C` to
  `0xDA3C0..0xDA44C`; metric `0x7CE4..0x7CE8` to
  `0xD5A60..0xD5A64`;
- cells `33..58`: raster `0x1258..0x2090` to `0xDA44C..0xDB284`;
  metrics `0x7C6C..0x7CD4` to `0xD5A64..0xD5ACC`;
- cells `65..90`: raster `0x23D8..0x3210` to `0xDB5CC..0xDC404`;
  metrics `0x7CEC..0x7D54` to `0xD5AE4..0xD5B4C`;
- cells `95..122`: raster `0x3440..0x4390` to `0xDC634..0xDD584`;
  metrics `0x7D64..0x7DD4` to `0xD5B5C..0xD5BCC`;
- GF4C palette `0x28..0x68` to the same NA2 range, with source SHA-256
  `499B64CDF2DFEA7C29D89834491A9C307B9653D4FFC217EC20CF8F358DAC0D3C`.

The corrected expected outputs are GF4
`690D0E53F30BD150C64F609DB8951D313A90F341F39B7486A8ED6A5E943A2FFE`,
GF4C `C6C889B795BB6137120252FAE887B48CB4304A0854A761F5942B50818D9D2FBD`,
and ELF `5541FB6C3CFFE15B318AC68C49E2254BE52E3C8BC99AC5B823CFE53FD7BEB01F`.
The independent generator and binary-patcher engine produced byte-identical GF4
and GF4C outputs. The 123-cell bitmap-block SHA-256 is
`4EBB5F0753717718024F159D1D1B0612FDA566FA4B36F8B2F4E3A819F5E3C907`;
the 123-row metric-block SHA-256 is
`A6C51E67E25634CC3B9F128A75C694B274485CD45D3ACD36379A3385B9D55458`.

Exact NUN5 cells `95..122` are outside printable ASCII and best satisfy the
appearance-parity objective, but eight of those NUN5 cells are blank where m01
had data. Runtime review must therefore include untranslated Japanese or
halfwidth text in addition to translated English. A fallback that preserves
those m01 cells is statically defined by the investigation but is not enabled.

This historical experiment is mutually exclusive with `font_m01` and is now
`runtime_failed`. It is not v22: it uses the confirmed m01 destination
`0xD9240`, retains 123 cells and m01 ELF behavior, does not import v22 pointer
tokens or its renderer-width edit, and is not a padded or unpadded whole-file
swap.

Runtime review on 2026-07-19 rejected this candidate. It did not materially
improve ordinary letters and damaged outline and alpha behavior, most visibly
on numeric glyphs. A byte-level audit found that all 84 same-semantic visible
printable cells compared between the candidate and its m01 parent retained
identical visible masks and metrics; the meaningful difference was palette
interpretation rather than improved geometry.

The coupled GF4C swap is unsafe for untouched NA2 raster data. Clean NA2's
primary raster uses palette index 15 for 265,344 of 1,746,272 pixels
(15.194884%). NA2 maps index 15 to opaque white, while NUN5 maps it to black.
Changing GF4C therefore reinterprets a large existing pixel population and
explains the deterministic outline damage. The patch is now classified
`runtime_failed`, remains disabled as negative evidence, and must not be used
as a donor or implementation parent. The accepted native baseline changes only
the bounded secondary GF4 data and keeps clean NA2 GF4C unchanged.

The fresh matched modal captures also give a concrete overflow reference. At
1708x1281, the visible red instructional-text ink spans approximately
`(455,822)-(1248,859)` in NUN5 and `(525,833)-(1278,865)` in the rejected NA2
build, whose right edge is clipped. Because that NA2 capture also contains the
failed asset/palette state, it is evidence for the screen and overflow symptom,
not a clean-source renderer acceptance image.

## 2026-07-27 Special Controls explanatory-body wrapper

The remade paired ss1 state proves the selector and lower explanatory block are
one Special Controls acceptance case. Exact NA2 wrapper telemetry records only
the lower block at BTL file `0x1C3D38`, runtime `0x00877C38`: caller
`0x003825F8`, outer caller `0x00877C40`, text pointer `0x008BCD60`, style
pointer `0x00E5E430`, and native local coordinates X `24`, Y `16`. The clean
eight-byte guard is `6C090E0C00000000`, native `jal 0x003825B0` plus NOP.

NUN5 does not store a newline in the source string. Its source at
`0x008F47C0` is `A feature to display the special controls for the game.`,
while the live transient buffer at `0x00DE82E1` contains
`A feature to display the special controls\nfor the game.`. The associated
live record contains scale `1.0`, box width `400`, box height `60`, and line
limit `2`. The accepted v2 metric table measures the text through `controls`
as `370` units and through the following `for` as `405`, which independently
explains the exact NUN5 break before `for`.

The bounded implementation therefore redirects only BTL file `0x1C3D38` to a
caller-specific adapter generated from the same shared v2 body builder as the
accepted quit modal. It copies at most 255 bytes to its stack, wraps at draw
time inside a 400-by-60 two-line box, and draws at local X `24`, Y `12` with
20-unit line height. T1880 remains canonical and unbroken, and the shared UI
renderer remains untouched. An exact-guarded task-owned state installed the
linked trial payload at `0x008F6000`, redirected only the five session-aware
core hooks plus this body call, and produced the same break and line origins as
the supplied NUN5 reference. Confidence is high; user acceptance remains a
separate epic state.

The later matched OFF-highlight ss1 pair exposed a separate selector-state
regression in the already shared selected/unselected hooks. The first state
showed selected ON and unselected OFF, so the original guards recognized only
ON in the selected helper and only OFF in the unselected helper. Highlighting
OFF swaps those consumer roles: selected receives pointer `0x006059F8` and
unselected receives `0x006059F0`; both guards missed and fell back to native
placement. The corrected adapters recognize both pointers in both roles and
keep coordinates attached to the text row: ON `(66,31)`, OFF `(59,49)`.
An exact-guarded converted copy of the new state redirected only ELF calls
`0x283914` and `0x283A60` to a task-local linked payload and matched the NUN5
OFF-highlight selector while retaining the accepted wrapped body. Focused
tests now verify the branch target for each ON pointer loads X `66`, while
each OFF fallthrough loads X `59`; this prevents another role-swap regression.

## 2026-07-28 composition-time C cutover

The two accepted Font C units are now compiled during normal
`runtime_injector` package loading. `c_sources.tsv` declares the source and
namespace, `c_imports.tsv` binds its external symbols, and `c_fragments.tsv`
maps extracted object sections to stable payload symbols and global order.
Compiler objects exist only in a temporary directory. Retained native ABI/data
shims are represented directly in `fragments.tsv`; the payload builder links
all normalized fragments into the one final `PRG/228.BIN`.

This is an architecture-only cutover. Comparison against the preceding
canonical package produced the same 57 fragments, the same 6,480-byte
runtime-injector link with SHA-256
`48621B34B8183866BA2D420B7D6691D110825BE090424E7C44B3A305BF9332FF`,
and the same 7,968-byte complete profile payload with SHA-256
`56748DA8F0D3C2BFE3AC689B1899DBF4EA358D5316DC387F562165CCCDB9C99C`;
the linked memory end remains `0x008F5C20`. The removed aggregate blobs were
therefore redundant build intermediates, not runtime resources. Confidence is
high because equality covers compiled section bytes, relocations, fragment
order, and the final linked payload.

### Secondary metric decoder cutover

The accepted fixed-ELF decoder had two observable entry contracts. The draw
entry received the renderer context in `s3`, secondary cell in `v0`, and
native mode flags in `a2`; it selected the indexed empty primary-map value,
decoded four packed metric nibbles, applied the local horizontal factor only
to the horizontal leading bearing, selected top/bottom metrics for the native
vertical mode, stored trailing trim at context `+0x38`, and rejoined cleanup
at runtime `0x001873B4`. The measurement entry received the current byte
through `s2`, converted printable secondary codes to cells `0..122`, returned
the same expanded four-byte metric row, stored it through `s1`, and rejoined
cleanup at `0x00187B68`.

`font_glyph_metrics.c` now implements both contracts in expandable
`PRG/228.BIN`. The compiled lookup entry is 208 bytes and the draw-application
entry is 328 bytes; neither has an external relocation. Boot-ELF file
`0x87374` now contains only a 24-byte register-setup/link/cleanup hook to
`localization.font.glyph_metric_apply`; file `0x87B60` contains the analogous
24-byte hook to `localization.font.glyph_metric_lookup`. Static composition
places the candidate entries at runtime `0x008F3EE8` and `0x008F3DA0`
respectively, but these addresses are payload-builder results rather than
feature-owned constants. The complete candidate payload is 8,512 bytes,
SHA-256
`81DED6B73DAB6B2B72B52FC158FD7F3C9C4A05CE8654EB1A273C81779AAF6E2D`,
ending at runtime `0x008F5E40`.

The atlas, packed map, descriptor, secondary-cell guard, horizontal scale word,
and secondary-only quad-height path remain unchanged. The pre-generated
decoder and measurement blobs are removed. Static confidence is high from
clean-byte guards, bounded disassembly of both native contexts, compiler
instruction review, and resolved-hook inspection. Runtime status remains
`approved_for_test` until the user verifies representative secondary-font
drawing/fitting and an unaffected primary/fullwidth case.

## 2026-07-30 Battle Settings Jutsu-row renderer

The replacement ss3–ss6 batch isolates one Jutsu-selector caller family. Its
source identities are NA2 `PRG/BTL.BIN` SHA-256
`56FD042740221E3CC91417194F147142799D51FE70642273F4E97BD389D5D63C`
and NUN5 `PRG/BTL.BIN` SHA-256
`7E8518DA7BD4957AF18CB0ABABE67F0E9B37C42C6551375201B15997F0A3DFE3`.
The supplied visible ss5 and ss6 states restore with the selector objects
already constructed, and the final row draw executes after either state
resumes. They therefore validate this draw-time caller directly with no game
input. The user also supplied the exact constructor sequence ss3, Cross, ss4,
Circle, ss5, Cross, ss6, but it was not required for the bounded runtime pass;
ss3 and ss4 are precursors rather than separate defects.

NA2 row compositor `FUN_006BCB70` sets a point and calls the ordinary text
renderer directly. The exact call is BTL file `0x90DC`, Ghidra
`0x006BCF9C`, live MWo3 `0x006BCFDC`, guarded by
`5020060C00000000` (`jal 0x00188140`; NOP). Its left-side point is
`(30 + f21, 16 + f20)` and its right-side point is
`(310 - f21, 16 + f20)`. This path has no width, line-count, or wrapping
contract, which explains why long translated names remain on one line and
overflow.

The initially recorded file offset `0x9178` was wrong: clean BTL bytes there
are unrelated pointer setup, so normal profile composition correctly rejected
the conflicting guard. The preserved export maps Ghidra `0x006BCF9C` to clean
BTL file `0x90DC`; the live `+0x40` relocation affects the runtime address,
not that file offset.

An earlier uncommitted experiment intercepted three presumed Jutsu
constructor/list families independently through
`font_v2_jutsu_primary_entry`, `font_v2_jutsu_secondary_entry`, and
`font_v2_jutsu_list_entry`, with guessed 208-unit wrapping and separate
128-unit boxes. It was rejected and is not retained: those wrappers did not
own the final visible ss5/ss6 text draw. The exact row-compositor call above
supersedes all three and is the only hook required for this defect.

NUN5 homolog `FUN_006CFE70` replaces that direct draw with
`FUN_00389EA0` at Ghidra `0x006D02DC`. It passes a `186 x 32` box, line
limit `2`, horizontal policy `0`, vertical policy `1`, and wrapping mode `1`.
Relative to the NA2 native point, its box origin is X `-7` on the left, X
`-4` on the right, and Y `-10` on both sides. The callee copies the text,
wraps it to the requested width and line limit, and then delegates to
`FUN_0018B1B0`; that final renderer applies start-horizontal and
center-vertical placement and advances once per produced line.

The bounded C implementation therefore hooks only live `0x006BCFDC`, copies
the source into a 256-byte stack buffer, and measures/wraps that copy at 186
units and two lines. If the result remains one line, it immediately calls the
exact displaced native renderer with the original text and does not enter a
layout session. Only a produced line break keeps the native left/right branch
and draws through the accepted two-line session before restoring the caller's
position. The first fresh candidate proved the caller isolation:
`Naruto Uzumaki Combo Attack` became
`Naruto Uzumaki` / `Combo Attack`, but relying on the shared newline hook
produced an 18-pixel row step instead of NUN5's 20. The corrected callback
owns both line draws directly; a 16-unit game-space Y step produces the exact
20-pixel NUN5 step at 640x480.

The remaining vertical overflow was glyph-quad geometry rather than line
spacing. Setting the secondary descriptor or renderer mode before
`FUN_00188140` was ineffective because that draw path resets the selector
before the per-glyph emitter. The existing layout-session right-edge shim at
ELF file `0x88070`, runtime `0x00187F70`, is the correct bounded boundary.
Session flag `0x40` makes only a selected caller take its bottom edge from
`FontV2Session.glyph_height`. A 2026-07-30 differential check exposed that the
first flag-aware shim did not actually preserve the intended native path: its
conditional branch placed the session `glyph_height` load in the MIPS delay
slot, so that load executed even when flag `0x40` was clear. The corrected shim
leaves a NOP in that delay slot and loads `glyph_height` only after the branch
falls through. Every session without the flag now retains the displaced native
bottom edge and continues at `0x00187F78` through the accepted
primary/secondary helper.
The flagged path rejoins at `0x00187F80` and preserves displaced delay-slot
word `0x8F84CA6C` (`lw a0,-0x3594(gp)`). Omitting that load makes the row text
disappear, which was a useful rejected transport result rather than a renderer
hypothesis.

The replacement ss1–ss2 evidence supplied on 2026-07-31 refined the final
constants. The two-line block uses glyph height `22.0`, box Y offset `-6.5`,
and the already-correct 16-unit line interval. In the user's row-aligned
comparison before the final correction, NUN5's two visible lines measured
`624` and `276` composite-image pixels wide while NA2.28 measured `650` and
`288`; both ratios independently select a `0.96` horizontal multiplier.

Writing that multiplier only to `0x0060737C` around `FUN_00188140` produced no
visible change. The effective boundaries are the existing active-session
glyph-advance and right-edge hooks, which consume
`FontV2Session.scale_x`. Internal flag `0x80` therefore preserves an explicit
caller-provided scale through `font_v2_prepare` instead of deriving it only
from overflow. Both Jutsu branches publish the same `0.96` session scale.
Fitting one-line rows deliberately omit the glyph-height and separate-line
flags, so they receive the width correction without vertical squeezing or
multiline cadence. Wrapped rows additionally select the `22.0` glyph height
and 16-unit interval. Measurement and the 186-unit wrap decision occur before
the draw-only multiplier, preserving the verified
`Explosive Destruction` / `Formation` break.

The user verified the final whole-Font hot-reloaded Jutsu selector on
2026-07-31, including fitting one-line and wrapped two-line rows. Canonical
fragment reconstruction passed afterward. Confidence is high for this caller
family; this verification establishes the live displayed result and does not
claim a separate integrated-ISO runtime pass.

## 2026-07-31 Settings and Ninja Song page templates

The matched Font 3 ss1–ss3 batch uses NUN5, not NUN6, as the layout reference.
The Settings screens are loop-rendered page templates rather than collections
of unique rows. Battle Settings uses one label call at BTL file `0x1CC368` and
two native value branches at `0x1CC424` and `0x1CC598`; Practice Settings uses
one heading call at `0x1CE528`, one label call at `0x1CE56C`, and one value call
at `0x1CE5D4`. The guarded redirects therefore cover every row emitted by each
loop without identifying any translated string or visible row.

The shared Settings value adapter has two data-selected overflow templates.
A value containing no ASCII space uses the compact-token target; a value with
an ASCII space uses the descriptive-phrase target. This reproduces both the
96-pixel NUN5 `Unlimited` result and the exact `(381,216)-(507,229)` NUN5
`High Speed Move` result while leaving short values such as `Normal` at native
scale. Battle and Practice labels retain separate page baselines, plus one
shared selected-state offset. These are page/state formulas, not per-row
coordinates.

Ninja Song arithmetic is likewise one function-level redirect, not a set of
token or row hooks. NA2 `FUN_00718920` is replaced from BTL file `0x64A60` by
one call to `localization.font.v2.ninja_arithmetic_template`; the template
reads the native 12-byte row record and renders all fifteen entries. The full
15-entry live table confirms the native routine has three structural outputs:
expanded arithmetic, total-only, and N/A. NA2 carries the total-only routing
through its existing indices `9`, `10`, and `13`; the replacement preserves
that native routing inside the single page renderer rather than creating three
row patches. The shared geometry owns factor, multiplier, unit, equals, total,
and N/A placement once for every applicable row.

Fresh hidden-worker ss1–ss3 injection runs proved the Settings loops and the
continuously redrawn Ninja formulas. At 640x480, the final Practice phrase and
heading bounds match NUN5 exactly; short Settings values also match, and the
remaining ordinary-label differences are at most one raster pixel. The Ninja
factor/total columns and N/A row are within one pixel horizontally; their
retained current glyph ink is shorter than NUN5, so subpixel baseline changes
quantize to the neighboring output pixel rather than creating a stable
per-row correction.

The objective call at BTL file `0x64E98` uses a separate, necessary page
template because objectives are one- or two-line prose rather than arithmetic
rows. It copies the text, wraps to two lines, and applies the NUN5 `288 x 32`
box and two-line baseline. Supplied ss3 resumes after objective construction,
so that call does not execute after savestate load; the hook and wrapper are
statically verified, but the objective's post-hook visible result is not
runtime-proven by this state. This limitation does not apply to the arithmetic
renderer, which executes continuously after resume.
