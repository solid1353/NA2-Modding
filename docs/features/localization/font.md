# Native NUN5-derived Font

The `localization.font` catalog subtree provides the English secondary-font
asset, proportional measurement, fitted and wrapped layout, caller-family
adapters, and numeric formatting. Exact edit and injection membership is owned
by `features.localization` in `@builder/catalog/catalog.modcat` and the
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
comparison cases. A small raster-appearance mismatch against NUN5 and one
synchronized final-build Ninja Song objective capture remain deferred.

## Covered layout families

The current layout component covers Control Settings; Practice and Special
Controls; Command Chart and related titles; Pause Controls; Battle, Practice,
Mode Select, Character Select, and Collection confirmations; Collection lists;
Linked Mode; the Jutsu selector; Practice explanations; Settings rows; Ninja
Song details; and the shared selected-style paths proven by those callers.

## Knowledge

- [Font assets](../../knowledge/localization/font/assets.md)
- [Integration baseline](../../knowledge/localization/font/integration_baseline.md)
- [Renderer metrics](../../knowledge/localization/font/renderer_metrics.md)
- [Screen layouts](../../knowledge/localization/font/screen_layouts/README.md)
- [Numeric rendering](../../knowledge/localization/font/numeric_rendering.md)
- [Runtime migration and composition](../../knowledge/localization/font/runtime_migration.md)

Those documents own exact offsets, formulas, call paths, hashes, negative
results, runtime evidence, and confidence. The catalog and implementation
stores remain the executable definition.
