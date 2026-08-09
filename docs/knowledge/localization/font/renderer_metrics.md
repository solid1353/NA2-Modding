# Font renderer metrics and spacing

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
as recorded by `localization__font__glyphs__native_data_gf4_bin_at_0000004e`, but NA2 therefore presents its normal
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

### Unresolved selective palette refinement

Clean NA2's primary GF4 raster and the accepted secondary raster both use
palette indices 13 and 14 zero times. Those two GF4C entries may therefore be
candidates for exact NUN5 white-alpha levels without changing any currently
referenced primary pixel. This remains a bounded asset lead only if a matched
review still finds a halfwidth-Latin weight difference.

No palette bytes or raster indices have been changed or runtime-tested for this
lead. Any experiment must start from the accepted native package and remain a
small, call-local or asset-local, script-generated change. A full NUN5 text
renderer transplant is outside its scope.


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

The existing `route_inline_markup_half_space_advance` hook at ELF offset `0x88B7C`
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
