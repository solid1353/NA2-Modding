# English UI integration

The `localization.ui` catalog leaf atomically imports the matching English UI
textures and applies the geometry, atlas selection, visibility, and draw
behavior they require. Its texture-patcher input and layout/runtime mechanisms
cannot be selected independently. `features.localization.ui` selects unified
patch `localization.ui` in `@builder/catalog.modcat`; its guarded bytes, hooks,
payloads, and `texture_patcher` module requirement are owned together by
`@builder/patches/localization.json`.

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

## Validation

- Compare official NUN5 with current NA2.28 under matching game and emulator
  conditions. Treat ordinary pulse-phase differences as capture noise, but
  treat semantic mismatch, clipping, artwork, ordering, visibility, animation,
  and placement differences as defects.
- Runtime-injected output remains candidate evidence until reproduced through
  the integrated build.

## Current behavior groups

| Domain | Shipped behavior | Knowledge |
| --- | --- | --- |
| Battle HUD names | Official NUN5 rectangles, mirrored X anchor, and shrink-only width fitting | [Character names](../../knowledge/localization/ui/battle/character_names.md) |
| Battle selectors and prompts | Ultimate-Jutsu label, VS confirmation, Round label, Jutsu-selector arrows, and command-list scroll arrows | [Selectors and prompts](../../knowledge/localization/ui/battle/selectors_and_prompts.md) |
| Battle items | Paired, numeric, single, fixed, and substitution-doll item-status presentation | [Item status](../../knowledge/localization/ui/battle/item_status.md) |
| Battle Mash prompts | Complete official NUN5 English main-prompt rectangles | [Mash prompts](../../knowledge/localization/ui/battle/mash_prompts.md) |
| Battle settings | Footer legends, Battle row and Handicap geometry, and the VS Practice Settings prompt | [Settings presentation](../../knowledge/localization/ui/battle/settings_presentation.md) |
| Battle Results | Summary geometry, moving clouds, rank stamps, details footers, objectives, and totals | [Battle Results](../../knowledge/localization/ui/battle/battle_results.md) |
| Stage Select | English stage rectangles, width fitting, thumbnails, labels, Random prompt, and footer | [Stage Select](../../knowledge/localization/ui/stage_select.md) |
| Character Select | Character-name rectangles, Select Color/Random placement, and footer anchors | [Character Select](../../knowledge/localization/ui/character_select.md) |
| Collection | Category titles, page prompts, Play/Stop, viewer controls, common prompts, and submenu geometry | [Collection](../../knowledge/localization/ui/collection.md) |
| Options and shared frontend prompts | Localized labels, difficulty routing, Controls Vibration, common Cancel records, and Options/Settings footer anchors | [Options](../../knowledge/localization/ui/options.md) |
| Victory | Complete localized winner-name layout set | [Victory](../../knowledge/localization/ui/victory.md) |

## Battle item-status presentation

The Battle item-status implementation covers paired, numeric, single, and
fixed foregrounds plus the substitution-doll pickup. Compatible official NUN5
item records and paired-rank offsets remain guarded data imports. NA2-specific
resident code owns the common update tail and the four class draw entries
because the NUN5 object layouts and renderer calling conventions cannot be
copied directly.

Numeric, paired, and fixed foregrounds share the resident anisotropic renderer;
single foregrounds retain the native uniform wrapper. The implementation keeps
the shared renderer and class entries in `PRG/228.BIN`, preserves NA2 object
links and lifetimes, and does not change item selection, values, effects, or
timing. Exact source and donor relationships are documented in
[Battle item-status presentation](../../knowledge/localization/ui/battle/item_status.md).

## Battle prompts, settings, and results

Mash prompts use the complete seven-record NUN5 English main-prompt table while
retaining NA2's renderer, object layout, and separate controller-glyph table.
Battle and Practice Settings use NA2-compatible effective prompt anchors; their
menu state, input, and animation behavior remain native.

Battle Results uses the official NUN5 label, cloud, and rank geometry with
NA2-compatible placement code where regional helpers are not ABI-compatible.
The implementation preserves result values, rank selection, reveal timing,
input, sound, and animation behavior. Exact cross-game mappings and negative
findings are recorded in [Mash prompts](../../knowledge/localization/ui/battle/mash_prompts.md),
[Settings presentation](../../knowledge/localization/ui/battle/settings_presentation.md),
and [Battle Results](../../knowledge/localization/ui/battle/battle_results.md).

The VS confirmation prompt uses effective NA2 anchors X=`388` for OK and
X=`462` for Back. Collection's character viewer selects Controls or Hide at the
shared visible-state call and Display at the separate hidden-state call; it
does not route all three suffix labels through one shared selection.

The Jutsu-selector arrow helper enables sprite mode 10 for the draw, applies
the signed quarter-turn and lower-arrow flip, flushes the sprite, and restores
mode 10 to its native disabled state. The NUN5 mode fields are never left active
across the shared sprite object's lifetime.

## Composition boundary

Compatible records, tables, and isolated constants remain guarded binary
edits. Source-owned runtime behavior is declared inside `localization.ui`; its
fragments compose into the shared
`PRG/228.BIN` resident payload alongside Font contributions. Shared placement
infrastructure does not transfer ownership to the Font feature. The UI
selection remains responsible for matching graphical assets, rectangles,
anchors, visibility, ordering, and ABI-safe draw-path adaptations. Text content
belongs to the translation importer, glyph measurement and wrapping belong to
Font, and regional button behavior belongs to
`localization.regional_input`.

Exact source/donor identities, offsets, function relationships, negative
results, runtime observations, and confidence belong only in the linked
knowledge documents.
