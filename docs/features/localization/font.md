# Native NUN5-derived Font

The `localization.font` catalog subtree provides the English secondary-font
asset, proportional measurement, fitted and wrapped layout, caller-family
adapters, and numeric formatting. Exact edit and injection membership is owned
by `features.localization` in `@builder/catalog.modcat` and the
catalog implementation
stores.

## Selectable contract

| Component | Current responsibility |
| --- | --- |
| `glyphs` | Install the accepted native 14x20 NUN5-derived secondary raster and metrics, preserve NA2 printable punctuation and GF4C semantics, and expose the shared metric data. |
| `layout` | Provide the shared v2 measurement/layout session, selected style, fitting, wrapping, alignment, renderer-state restoration, and ABI adapters for proven caller families. |
| `numeric_formatting` | Render Ninja Song, Save/Load, and Battle Settings values through their accepted native-compatible formatting paths. |

These components compose through `localization__shared_font_payload`. The
payload builder assigns final addresses in `PRG/228.BIN`; catalog injections
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
`runtime_injector` fragments linked into the shared `PRG/228.BIN`. The feature
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

- Pending acceptance: memory-card message bodies assemble their native source
  fragments into one paragraph and use the existing shared body-layout helper.
  The adapter retains local origin `(22,18)`, derives its width from the window
  interior with equal side margins, and keeps shared body spacing above a
  reserved 30-unit button row. Its hook replaces only the body-fragment loop.

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
  preceding renderer-session state. The resident implementation does not use
  the cleared boot-ELF interval that is overwritten during loading.
- Battle confirmation scopes the complete Yes/No list call and adapts its two
  shared inner calls only while that scope is active. Nested calls restore the
  preceding scope word.
- Collection Characters maps only the selected-name pointer to the secondary
  `Granny Chiyo ` donor string and uses the shared top-plaque layout family;
  other references to the primary string remain unchanged.

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

Those documents contain clean NA2/NUN5 renderer, metric, ABI, asset, and layout
findings. The catalog and implementation stores remain the executable
definition.
