# Font renderer and asset findings

This directory preserves confirmed visual, structural, and byte-level Font
evidence in this file and the focused matched-savestate report. Raw schema-v1
replicas of retired m01/v22/v23 packages and the rejected palette experiment
were removed after their reusable conclusions were consolidated here. They
remain recoverable from Git commit `69da715`; they are not implementation
parents or active patch inputs.

## Current savestate comparison

The [2026-07-24 matched savestate analysis](savestate_analysis_2026-07-24.md)
compares ten NUN5/NA2 pairs and separates raster/metric, call-local position,
generic-modal, and missing-wrap defects. It confirms that Control Settings is
the only boxed-fit path proven correct by this sample and that multiple other
callers require layout behavior that a font-asset refinement alone cannot
provide.

## 2026-07-25 stage-by-stage autofit reset

The user retained the accepted native font and generic resident-patcher
infrastructure but rejected the combined July 24-25 autofit/layout selection as
unstable. The implementation remains recoverable in place; only its default
selection changed. These five module/patch rows are now disabled:

- binary `font_renderer_metrics`;
- binary `font_controls_auto_fit`;
- resident `font_renderer_metrics`;
- resident `font_controls_auto_fit`;
- resident `font_layout_wrappers`.

`font_nun5_glyphs` remains enabled. Binary `font_modal_alignment` also remains
enabled because it is the independently reviewed Character Select `Back to
Game Mode Screen` row alignment, not the Save/Load lower modal described
below. The resident fragments, metric table, relocations, hook declarations,
and generated blobs were not deleted. Their confirmed formulas and rejected
integration behavior remain evidence for selective reimplementation rather
than an enabled baseline.

The user identified `ss9` as the current broken Save/Load modal. Its protected
state was copied read-only from
`@pcsx2_user/sstates/SLOP-NA228 (D61F4C01).09.p2s` to the Font-owned input
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

The `font_v2_layout_core` selection remains default-disabled and no caller
family targets the adapter yet. Every hook therefore observes a null session
in normal composition, restores its temporary `v0`/`v1` use, executes the exact
displaced NA2 operations and resumes the original path. Static linked-package
validation confirms the five hook targets, adapter ABI/state restoration,
internal branch bounds, the `Ultimate Jutsu Prep` denominator of 178, and the
unchanged retained-v1 blob. The separate v2 asset is 1,508 bytes with SHA-256
`745C90608C414B3C32C0E7BD08D18C026C3919EBA92E41A49B009C66C25C0569`.
Automatic word wrapping and caller-native coordinate records remain later
family work; these two foundations change no screen.

## Accepted native 14x20 integration

The current patch set builds on the accepted version 5 baseline. Its former
standalone profile module pin was
`9FC3C4905DFF6D14BAAA848C56E6C17D1DE4E79EEFAB2E1A7A74FAD6A25013F8`,
and its former standalone feature pin was
`23A2CFDD285FF00A40F35AC42D0656580E4D9DE5884F2CF568453A20E93AA3A7`.
The current profile now covers it through the complete Localization feature pin
`F68B5DB40A78F46CFCEB429F09E434CA4A106BD731420E76A7324415CD817BD8`.
It is a new, deterministic donor built from hash-verified clean NA2 and
official NUN5 inputs; it is not based on m01, v22/v23, the rejected semantic
palette swap, the 10x22 resample, or a whole-file GF4 replacement.

`font_nun5_glyphs` installs native NUN5 14x20 geometry and metrics for
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
  `6F691015E5BA54EA87B2976970D828863E274BB543CC3D531D93800018EB7A5E`;
- decoder: 316 bytes, SHA-256
  `C65B283CCBF7A8CCFF59DB7D96CC2A87731B6AD2BE142E37A088BEE6BFF9D70F`;
- measurement hook: 24 bytes, SHA-256
  `8B7A75C0FDFD2F055ACFC1FCF90996E298CE363E112659579513A89606FE7C1C`;
- resident renderer blob: 1,360 bytes, SHA-256
  `BD2889358F17B8FFF732842CD701D0F4C48F9CCB8A84A766E2710D4D56B3F2D6`.

The current runtime-reviewed result contains 24 static binary-patcher Font
declarations and eight linked resident-patcher hooks. The resident blob exports
nine code fragments for shared metrics, Controls fitting and horizontal
scaling, selected-choice layout, shared UI layout, and the two displaced-code
trampolines.
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
through ASCII formatted output. The first implementation stage therefore
changes only the six guarded call blocks at ELF file offsets `0xE660C`,
`0xE6650`, `0xE6694`, `0xE67A4`, `0xE67E8`, and `0xE682C` to call NA2's
existing `sprintf` at runtime `0x0017BCA0`. Existing immutable format strings
`%d` and `%02d` preserve the date, minute, and second widths. The hour call
uses `%02d` and reproduces NUN5's signed `hour < 100 ? hour : 99` cap inside
the same guarded 28-byte call block. The
Save/Load-only fullwidth colon at ELF file offset `0x503134` becomes ASCII
colon.

This call-local stage deliberately preserves `YYYY/MM/DD`, timer divisors
`108000`, `1800`, and `30`, and every formatter caller outside
`FUN_001e6370`. The ASCII conversion is runtime-proven; the later NUN5
two-digit hour and 99-hour cap are statically verified and await runtime
confirmation. Date reordering and visual positioning remain separate
reviewable stages. The deterministic generator is
`scripts/research/localization/generate_save_load_ascii_digits.py`.

The isolated worker build retained at
`work/Font/build/save-load-ascii-digits.iso` has boot CRC `F9FC3002`. After a
clean manual launch in the Font-owned PCSX2 copy, the user confirmed that the
Save/Load date and Play Time fields render correctly as ASCII. The patch is
therefore proven for its original ASCII-conversion stage; no date-order,
width, timer, or positioning change was included in that acceptance.

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

`font_battle_settings_ascii_digits` changes only that ordinary-value block to
call NA2's existing ASCII `sprintf` at runtime `0x0017BCA0` with the immutable
`%d` format at `0x006042D3`. The adjacent 40-byte branch ending at the edit
site is independently guarded, so value `100` continues to render the native
infinity symbol. Selector state, the stored timer value, the other five
settings rows, and every other fullwidth formatter caller remain unchanged.
The deterministic generator is
`scripts/research/localization/generate_battle_settings_ascii_digits.py`.
The patch remains `approved_for_test` until a worker ISO reproduces the
slot-1 screen.

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
as recorded by `font_nun5_glyphs_01`, but NA2 therefore presents its normal
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

### Shared renderer-metric and layout-wrapper port

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

Commit `3d52a14` placed the complete helper block at runtime
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
overflow remain separate unresolved caller families; their unchanged defects
are not regressions from this port. Confidence is **high** for the shared
measurement formula, hook boundaries, caller guards, and matched horizontal
result. That regression did not cover entry into Save/Load and therefore did
not establish persistent ownership of the helper interval.

### 2026-07-25 confirmed Load-screen helper erasure

The user captured a state after the game froze while entering the Load screen.
The source was read from
`@pcsx2_user/sstates/SLOP-NA228 (682CC5FB).01.p2s`, copied without modifying
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
`resident_patcher` fragments linked by the shared payload builder into
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
- `font_modal_alignment` uses measured X values `84, 79, 79, 75, 13`, moves
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
`@logs/na2/builds/20260719_202514_393_pid36044/`. It selected the two accepted
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
remain recoverable from commit `69da715`.

Surrounding confirmed observations:

- NA2 and NUN5 `GF4C.BIN` are both 104 bytes but diverge from offset `0x28`; the v22 and v23 experiments used the NUN5 variant. Its independent functional significance remains unproven.
- Replacing NA2 GF4 with the exact NUN5 GF4, padded or unpadded, produced broad spacing but patchy glyph rendering and could disrupt PNACH behavior. Do not repeat that direct swap as a new hypothesis.
- The v22 state was clean and closer to NUN5, but glyphs could touch or overlap and long text still clipped.
- The retired declarative m01, m02, v22, v23, and semantic-palette records are
  recoverable from commit `69da715`. Their useful conclusions are consolidated
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
