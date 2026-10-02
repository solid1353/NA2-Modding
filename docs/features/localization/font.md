# Native NUN5-derived Font

The internal `localization.font` patches provide the English secondary-font
asset, proportional measurement, fitted and wrapped layout, caller-family
adapters, and numeric formatting. `features.localization: "en"` selects them
together through `localization.en`; `"jp"` selects no localized font replacements.
Exact edit and injection membership belongs to the localization patch store.

## Internal components

| Component | Current responsibility |
| --- | --- |
| `glyphs` | Install the accepted native 14x20 NUN5-derived secondary raster and metrics, preserve NA2 printable punctuation and GF4C semantics, and expose the shared metric data. |
| `layout` | Provide the shared v2 measurement/layout session, selected style, fitting, wrapping, alignment, renderer-state restoration, and ABI adapters for proven caller families. |
| `numeric_formatting` | Render Ninja Song, Save/Load, and Battle Settings values through their accepted native-compatible formatting paths. |

The payload-only `localization.font.core` contains the shared layout session,
ASCII widths, and measurement helpers. Both layout and Character Select support
selection include it, so mod-added support labels do not depend on selecting
English. It installs no native screen hooks by itself.

These components compose into the shared resident payload. The
payload builder assigns final addresses in `228/228.BIN`; catalog injections
declare fragments, relocations, symbols, and ABI metadata. Checked-in aggregate
MIPS payload blobs are not production inputs.

## Behavioral boundary

- NA2 retains its native glyph renderer, colors, shadows, markup, and
  controller-icon callbacks.
- Fitting is shrink-only and uses the same proportional metrics as drawing.
- One-line rows retain native glyph geometry. Multiline behavior is enabled
  only for caller families proven to require wrapping.
- Caller adapters own box geometry, alignment, callbacks, and genuine local
  exceptions; they do not duplicate shared measurement formulas.
- A null or inactive layout session preserves native NA2 behavior, and nested
  callbacks restore the preceding session state.
- Boot ELF and overlay changes are limited to guarded call-site hooks,
  displaced-instruction handling, and genuinely local constants.
- Font does not own translated wording, graphical UI rectangles, gameplay
  behavior, or regional input semantics.

## Maintenance and validation

Pending acceptance: `nun5_source_cell` owns donor glyph selection for both
atlas and metrics. It supplies NUN5's `®` cell 142 at NA2 cell 107, selected
by byte `0xAE`. All other glyphs and ASCII measurement retain the pre-change
baseline. Extend this existing lookup; do not add a separate symbol renderer.

- Broad Font layout analysis is complete. Repeat it only when new evidence
  proves the retained findings insufficient or indicates that a shared fix is
  better than separate caller corrections.
- During live editing, never attribute unchanged visible output to caching. If
  a requested metric or coordinate change does not visibly move, retain the
  current screen and trace forward from the proven live entry to the first
  incorrect value or consumer. Do not ask the user to reopen or reconstruct the
  same screen.
- Compare official NUN5 and current NA2.28 under matching conditions. Choose
  the broadest correction layer supported by evidence: shared core, repeated
  caller family, or genuinely local container.
- Validate visible bounds, origins, line breaks, spacing, glyph height, and
  native style. Compilation and hook application are not visual results, and
  runtime-injected output remains candidate evidence until reproduced through
  the integrated build.
- Recheck previously accepted caller families after a shared-core change.

The accepted layout baseline has no known large defect in its maintained
comparison cases. A small intentional raster-appearance mismatch against NUN5
remains. The synchronized Ninja Song objective, arithmetic, and fight-dependent
bonus renderers are runtime-proven.

## Resident implementation

All executable Font helpers and trampolines are feature-owned
`runtime_injector` fragments linked into the shared `228/228.BIN`. The feature
declares symbols, relocations, ABI metadata, and guarded hooks but no final
payload offsets. C owns layout policy and formatting; small assembly bridges
remain only where a native entry contract, displaced instruction, delay slot,
tail call, or rejoin requires them.

The shared core owns measurement, wrapping, active-session state, glyph
geometry, and restoration. Caller families contribute only their source
selection, box geometry, alignment, callbacks, and proven local exceptions.
The secondary metric decoder, glyph geometry bridges, and every layout family
use the same resident payload rather than fixed ELF caves or checked-in aggregate
MIPS blobs.

A fresh integrated build passed title-to-Load execution with the resident
payload present before the old helper cave could be overwritten. Matched
Practice, Controls, character-return, Collection, and Ninja Song cases then
loaded and rendered without a guest pause or crash. The fixed payload reservation
is owned by [Runtime injection](../runtime_injection/implementation.md).

## Covered layout families

The current layout component covers Control Settings; Practice and Special
Controls; Command Chart and related titles; Pause Controls; Battle, Practice,
Mode Select, Character Select, and Collection confirmations; Collection lists;
the Jutsu selector; Practice explanations; Settings rows; Ninja Song details;
and the shared selected-style paths proven by those callers.

## Caller-specific contracts

- Pending acceptance: memory-card status messages and fixed Save/Return
  questions share paragraph fitting. The localized
  lower window uses NUN5's `(8,230,496,144)` geometry, with body origin `(16,12)`,
  width `448`, and an 85-unit body box with a five-line limit. Short paragraphs
  retain 20-unit line spacing; taller blocks shrink their spacing and glyph
  height together to fit. The complete Yes/No group is centered with NUN5's
  five-space gap and bottom-aligned inside the padded content rectangle, giving
  local Y `96` for this panel. Next follows the window height. Explicit breaks are preserved,
  words wrap at spaces, and overflow widens the wrapping width before horizontal
  shrink-to-fit. Each resulting line is drawn at an explicit Y so native line
  advance cannot change the block height. The separate startup card check uses
  its original `(50,100)` origin and seven-fragment input limit; its choices
  remain at their native position. The ordinary lower caller retains four
  fragments. Neither adapter changes dialog transitions.

- Pending acceptance: Practice Settings section headings use the shared donor
  metrics to fit their existing 158-unit box. The correction applies to every
  heading through the shared adapter and preserves its X/Y placement.

- Pending acceptance: the Jutsu display and Practice completion plate share a
  two-line, individually centered title adapter. The Jutsu display uses the
  donor 208x30 box at its animated origin. The Practice plate retains its
  original 208-unit wrapping and fitting width and centers each line on the
  complete plate at X=256. It preserves its 28-unit glyph height and centers
  the visible text bounds on
  the plate's Y=300 center using existing top/bottom glyph metrics and line
  advances. Native shake is preserved. An offline check
  against raster bounds covered 1,065 enabled move-title entries and 2,992
  one/two-line arrangements; native integer positioning leaves at most a
  half-unit center error at rest. Runtime appearance remains unverified.

- Character Select centers the five player-mode rows in a shrink-only
  `(8, *, 240, 20)` box. Its selected helper receives an integer X; the
  ordinary helper retains a floating-point X. The first four source Y values
  remain structural, while the footer maps to Y `114`.
- Command Chart and Practice title fitting measures materialized quotation
  marks with the donor delimiter's 14-unit advance. Renderer color controls
  remain in the string but do not contribute to measured width.
- Practice explanation wrapping installs the controller-token metric and draw
  callbacks only for the active call, then restores both icon objects and all
  preceding renderer-session state. It reads condition texts from the
  [Command List](../controls.md#command-list-and-move-chart) text table and
  writes the Select, L3, and R3 tokens as `<iconSELECT>`, `<iconL3>`, and
  `<iconR3>`, whose native icon IDs 15, 8, and 9 draw as Control Settings
  pills. The resident implementation does not use the cleared boot-ELF
  interval that is overwritten during loading.
- Battle confirmation scopes the complete Yes/No list call and adapts its two
  shared inner calls only while that scope is active. Nested calls restore the
  preceding scope word.
- Collection Characters maps only the selected-name pointer to the secondary
  `Granny Chiyo ` donor string and uses the shared top-plaque layout family;
  other references to the primary string remain unchanged.

## Running-help integration

`localization.font.layout` routes the in-scope native menu
set/draw calls through `font_v2_running_help.c`. Its shared adapter selects GF4,
uses zero tracking and the existing layout session's narrower ordinary spaces,
and restores the preceding renderer, scale, icon selector, and layout session.
Native help-strip geometry, movement, initial hold, queue ownership, and resets
remain with the native component described in
[Running help](../../knowledge/localization/ui/running_help.md).

Measurement uses the native token classifier and per-glyph width calculation,
consumes complete formatting tags, and obtains icon advances from the installed
native metric callback. It measures only when the queue can accept a node.
The reserved extent is measured width plus `unit * gap_count`; an extent below
the viewport width becomes viewport width plus one unit, following NUN5's
short-string rule. Text drawing uses the same scoped glyph/space advances.

Both custom menu schemas select this setter when Font layout is enabled and
the original native setter when it is disabled. Their internal header is 84
bytes, with the selected function pointer at `+0x50`. Battle and Practice retain
unit `20.0`, gap count `8`, borrowed text, and their native page-change resets.
The integration covers the caller families in the linked knowledge document
without replacing the global native entry used by consumers outside scope.

### Supplied-state comparison before the correction

The supplied NA228 BF8401D4 slots 1 and 2 show Mode Select / Free Battle and
Practice Settings / Gauge Settings / Refill Time per Stock. The supplied
NUN5 C071D4C1 slot 1 shows the matching Free Battle selection. Offline memory
inspection identifies these horizontal help queues:

| Saved case | Help object | Text node | Reserved extent |
| --- | --- | --- | ---: |
| NA228 Free Battle | `0x00CC4430` | `0x00CC37A0` | 1628 |
| NUN5 Free Battle | `0x00BF83F0` | `0x00BF2600` | 788 |
| NA228 Refill Time per Stock | `0x00CC7170` | `0x00CC42E0` | 920 |

The Free Battle strings contain identical visible wording, 66 characters and
12 ordinary spaces; only their white-color markup differs. The custom help
is `Automatic recovery time for one stock.`, 38 characters and five spaces.
The saved NA228 setter instructions retain the native count-based formula:
`22 * (66 + 8) = 1628` and `20 * (38 + 8) = 920`.

All three objects have viewport `512x48`, speed `2`, displacement about
`460.8`, a 30-update initial hold, and a single queued node. Their saved
text origins are `(51,20)`, after native integer positioning. These states
establish matching initial local placement, not matching glyph spacing or
screen-space ink bounds. Renderer font selection is restored after drawing;
the final selected descriptor cannot stand in for the help draw's descriptor.

### Spacing, alignment, and blank travel

The supplied Free Battle glyphs have identical decoded margins in NA228's
packed primary-map values and NUN5's GF4 metric table. Their drawing rules
differ: NA228 uses native tracking `-1`, giving a half-unit reduction per
visible glyph and a 13.5-unit ordinary space; NUN5 uses zero tracking and
eight-unit spaces. The saved NA228 selector retains the native tracking
instructions, and the ordinary-space hook retains native advancement without
an active layout session.

For Free Battle, the complete pen advance is therefore 641 in NA228 and 602
in NUN5. Both are reproduced from saved metrics and independently match the
renderer start/end fields: `51 -> 692` and `51 -> 653`. The 39-unit difference
is `12 * 5.5 - 54 * 0.5`. For the custom Refill Time string, NA228's advance
is 372 (`51 -> 423`); the same glyphs with donor spacing would advance 361.
These are logical advances, not screenshot pixel widths.

Both Mode Select text/background viewports retain logical rectangle
`(0,300,512,48)` and identical saved clip bounds. In their 640x480 screenshots,
the yellow Free Battle text occupies thresholded bounds `(66,407)..(188,419)`
in NA228 and `(66,407)..(186,419)` in NUN5 (RGB red/green above 140, blue below
110). This supports matching left/vertical placement in this pair while word
positions diverge through accumulated spacing. It does not establish that all
reported alignment differences are the same issue. The Practice state's strip
is at logical Y=290, matching its separate native style; there is no supplied
matching NUN5 Practice frame for a pixel comparison.

Using logical advance as the text extent and ignoring edge bearings and update
quantization, the documented queue geometry predicts about 237.5 completely
blank updates for NA228 Free Battle: `(1628 - 641 - 512) / 2`. The custom
Refill Time string predicts 18: `(920 - 372 - 512) / 2`. NUN5 Free Battle
predicts none: `788 - 602 - 512 < 0`. These derived intervals explain the
string-dependent absence; they are not measured elapsed timings. The retail
NUN5 measurement/markup discrepancy is documented in the linked knowledge
document.

The supplied frames and memory establish the scrolling and spacing mechanisms
and the matched Mode Select placement. Other menus have static caller/style
coverage; their complete visual alignment and icon-bearing cases remain
unconfirmed. The correction retains those structural positions; it does not
apply a universal X/Y shift. Its runtime appearance remains unverified.

## Matched-screen measurements

Across 20 identical black-text samples, median NA2 differences from NUN5 were
-2 pixels in visible width, -2 pixels in visible height, `0.850782x` total
dark-ink pixels, and `1.018280x` dark-ink density inside the smaller bounds.
The font was therefore not a uniformly enlarged or uniformly heavier raster.
String-dependent width differences and caller-dependent vertical offsets show
that no single global scale, tracking, X, or Y correction accounts for the
cross-game differences.

Paired captures exercise both selected states of the Collection exit selector.
Cross-state differencing separates each glyph raster from the translucent
dialog and establishes that both Yes states were one output pixel right and
one output pixel low. The No X origin matched; its unselected Y matched, while
its selected style was one output pixel high.

## Rejected approaches

- Replacing NA2 GF4 with the exact NUN5 GF4, padded or unpadded, produced broad
  spacing and patchy glyph rendering. A direct first-123-cell copy is
  structurally invalid because of the
  [cell-semantic differences](../../knowledge/localization/font/assets.md#na2-and-nun5-cell-and-palette-differences);
  it would remove punctuation used by translated mappings.
- A later semantic import retained the mismatched punctuation cells, relocated
  NUN5 cell `63` to NA2 cell `32`, and imported same-semantic ranges. Runtime
  review still rejected it: ordinary letters did not materially improve, while
  numeric outlines and alpha behavior were damaged. All 84 compared visible
  printable cells retained identical masks and metrics relative to their
  parent; the meaningful difference was palette interpretation.
- A coupled NUN5 GF4C swap is unsafe for untouched NA2 raster data: NUN5 maps
  palette index 15, used by about 15.2 percent of NA2's primary raster pixels,
  to black instead of white, so the swap reinterprets that pixel population.
  Indices 13 and 14 are unused by that raster and could change without
  reinterpreting a referenced pixel, but their visual usefulness has not been
  tested; this is not a recommended palette change.
- The isolated descriptor-height experiment at ELF file offset `0x88064`
  changed `0C 00 20 C6` to `10 00 20 C6`. It produced a 28x28 quad instead of a
  Y-only correction, stretching both axes by 16.7 percent while logical
  measurement stayed unchanged. Runtime captures showed damaged outlines and no
  useful alignment improvement. Changing NA2's shared width load from 24 to 28
  likewise produces 28x28 and damages horizontal geometry; the
  [cross-game difference](../../knowledge/localization/font/renderer_metrics.md#glyph-geometry)
  is specifically secondary vertical extent.
- Changing only secondary tracking from `-1.0` to `0.0` leaves spacing and
  boxed measurement inconsistent; tracking must be considered with the
  [ordinary-space and fit paths](../../knowledge/localization/font/renderer_metrics.md#tracking-and-ordinary-spaces).
  Applying only NUN5's `128 / measured_width` threshold to the NA2 legacy
  measurement path also makes different fit decisions, including incorrectly
  shrinking `Linked Attack`. Neither isolated change represents the NUN5
  renderer contract.

## Knowledge

- [Font assets](../../knowledge/localization/font/assets.md)
- [Renderer metrics](../../knowledge/localization/font/renderer_metrics.md)
- [Numeric rendering](../../knowledge/localization/font/numeric_rendering.md)
- [Command Chart and Practice titles](../../knowledge/localization/font/screen_layouts/command_and_practice_titles.md)
- [Controls](../../knowledge/localization/font/screen_layouts/controls.md)
- [Practice](../../knowledge/localization/font/screen_layouts/practice.md)
- [Confirmations](../../knowledge/localization/font/screen_layouts/confirmations.md)
- [Collection](../../knowledge/localization/font/screen_layouts/collection.md)
- [Character Select](../../knowledge/localization/font/screen_layouts/character_select.md)
- [Shared style](../../knowledge/localization/font/screen_layouts/shared_style.md)
- [Running help](../../knowledge/localization/ui/running_help.md)

Those documents contain clean NA2/NUN5 renderer, metric, ABI, asset, and layout
findings. The catalog and implementation stores remain the executable
definition.
