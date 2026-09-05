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
