# UI translation layout patches

The `localization.ui_layout` catalog leaf ports the geometry, atlas selection,
visibility, and draw behavior required by the imported English UI assets. The
exact selected edit IDs are owned by
`na228_builder/catalog/localization.modcat`; guarded bytes and shared injection
units are owned by the catalog implementation stores.

## Contract

- Copy complete official NUN5 records or tables when their structure is
  compatible with NA2.
- Use narrow authored NA2 glue only when NUN5 code depends on incompatible
  object layouts, regional globals, load addresses, or calling conventions.
- Keep shared behavior shared. Repeated prompt, item-status, and font-assisted
  layout paths use one proven helper where their callers actually share it.
- Keep renderer-specific behavior separate when screens use different owners or
  state formulas, even when their visible prompts look similar.
- Preserve target sizes, unrelated state fields, gameplay behavior, selection
  state, input semantics, and native object lifetimes.
- Treat the catalog and implementation stores as the executable definition;
  this document does not duplicate offsets or patch rows.

## Maintenance and validation

- Broad UI analysis is complete. Repeat it only when new evidence proves the
  retained findings insufficient or indicates that a broader shared fix may be
  better than separate screen corrections.
- The user has standing authorization for exact-target deletion of confirmed
  disposable UI artifacts. Verify every target and keep protected sources,
  user-owned PCSX2 files, and unrelated task work out of scope.
- Compare official NUN5 with current NA2.28 under matching game and emulator
  conditions. Treat ordinary pulse-phase differences as capture noise, but
  treat semantic mismatch, clipping, artwork, ordering, visibility, animation,
  and placement differences as defects.
- Runtime-injected output remains candidate evidence until reproduced through
  the integrated build.

The declared UI Translation comparison work is complete, and no comparison
case is currently awaiting approval.

## Current behavior groups

| Domain | Shipped behavior | Knowledge |
| --- | --- | --- |
| Battle selectors and prompts | Ultimate-Jutsu label, VS confirmation, Round label, Jutsu-selector arrows, and command-list scroll arrows | [Selectors and prompts](../../knowledge/localization/ui/battle/selectors_and_prompts.md) |
| Battle items | Paired, numeric, single, fixed, and substitution-doll item-status presentation | [Item status](../../knowledge/localization/ui/battle/item_status.md) |
| Battle settings and results | Mash prompts, settings footers, summary geometry, title behavior, clouds, and rank stamps | [Settings and results](../../knowledge/localization/ui/battle/settings_and_results.md) |
| Stage Select | English stage rectangles, width fitting, thumbnails, labels, Random prompt, and footer | [Stage Select](../../knowledge/localization/ui/stage_select.md) |
| Character Select | Character-name rectangles, Select Color/Random placement, and footer anchors | [Character Select](../../knowledge/localization/ui/character_select.md) |
| Collection | Category titles, page prompts, Play/Stop, viewer controls, common prompts, and submenu geometry | [Collection](../../knowledge/localization/ui/collection.md) |
| Options and shared frontend prompts | Localized labels, difficulty routing, Controls Vibration, common Cancel records, and Options/Settings footer anchors | [Options](../../knowledge/localization/ui/options.md) |
| Victory | Complete localized winner-name layout set | [Victory](../../knowledge/localization/ui/victory.md) |

## Composition boundary

Most UI-layout changes are guarded binary edits. Helpers that need resident
code compose through `localization__shared_font_payload`; this is shared
placement infrastructure, not ownership transfer to the Font feature. UI
layout remains responsible for graphical rectangles, anchors, visibility,
ordering, and ABI-safe draw-path adaptations. Text content belongs to the
translation importer, glyph measurement and wrapping belong to Font, and
regional button behavior belongs to `localization.regional_input`.

Exact source/donor identities, offsets, function relationships, negative
results, runtime observations, and confidence belong only in the linked
knowledge documents.
