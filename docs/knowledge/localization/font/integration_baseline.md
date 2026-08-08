# Font integration baseline

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
without rebuilding an ISO. A replacement ss1 pair from Current CRC `2DA77DC7`
and NUN5 CRC `C071D4C1` proves that both Current words retained ink two pixels
shorter than NUN5 even though the row coordinates were already correct. The
font-only refinement therefore keeps the pointer-specific row coordinates and
uses two renderer-state formulas rather than row-specific exceptions: selected
text receives X `+1.0`, horizontal scale `1.02`, and glyph height `26`; ordinary
text receives horizontal scale `1.01` and glyph height `26`. Both use the same
104-by-20 one-line box and 20-unit line height. Neither path writes or replaces
displayed text. An isolated hidden-worker run matches the NUN5 selected and
ordinary dark-glyph bounds in the retained 8x comparison; user acceptance of
the integrated result remains pending. Confidence is **high** for the pointer
guards, hook isolation, placement, and shared draw-state geometry.

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
The then-current profile covered it through the complete Localization feature pin
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
