# English UI integration

The internal `localization.ui` patch atomically imports the matching English UI
textures and applies the geometry, atlas selection, visibility, and draw
behavior they require. Its texture-patcher input and layout/runtime mechanisms
are included together by `localization.en`, selected through
`features.localization: "en"`; its guarded bytes, hooks,
payloads, and `texture_patcher` module requirement are owned together by
`@builder/patches/localization/localization.json`.

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
| Victory | Coupled NUN5 WINNER artwork and width-driven character-name construction | [Victory](../../knowledge/localization/ui/victory.md) |

## Screen Settings text

The Screen Settings modal imports NUN5's ASCII `X:` and `Y:` records. Its two
labels and two formatted numeric values draw through one scoped wrapper that
selects the secondary ASCII font mode, zero tracking, and zero extra spacing
used by NUN5. It also scopes the existing NUN5 eight-unit ordinary-space
advance needed by the formatter's leading spaces, then restores the prior
renderer state. The native four anchors, numeric formatter, color, modal
object, and every unrelated text draw remain unchanged.

## Battle item-status presentation

The Battle item-status implementation covers paired, numeric, single, and
fixed foregrounds plus the substitution-doll pickup. Compatible official NUN5
item records and paired-rank offsets remain guarded data imports. NA2-specific
resident code owns the common update tail and the four class draw entries
because the NUN5 object layouts and renderer calling conventions cannot be
copied directly.

Numeric, paired, and fixed foregrounds share the resident anisotropic renderer;
single foregrounds retain the native uniform wrapper. The implementation keeps
the shared renderer and class entries in `228/228.BIN`, preserves NA2 object
links and lifetimes, and does not change item selection, values, effects, or
timing. Exact source and donor relationships are documented in
[Battle item-status presentation](../../knowledge/localization/ui/battle/item_status.md).

The two games' anisotropic renderers build centered offsets from different
registers; see
[Shared foreground renderer difference](../../knowledge/localization/ui/battle/item_status.md#shared-foreground-renderer-difference).
Reusing NA2's centered-offset instruction after adopting NUN5's register
allocation rebuilds the offsets from alpha:

```cpp
sprite->localX = -(alpha * sprite->width) / 2.0f;
sprite->localY = -(alpha * sprite->height) / 2.0f;
sprite->alpha = alpha;
```

That register mismatch makes the foreground offsets vary with alpha. In a
controlled paired fade, intended offsets `-7`, `-23`, and `-5` became
`-4.2`, `-13.8`, and `-3.0` at alpha `0.6`. Using NUN5's scale register
retained the intended offsets through fade-in and alpha `0.0` fade-out.
Changing the BTL wrapper's anisotropic argument order moved the bubbles and
did not correct the foreground transition. The centered-offset register is the
isolated cause; saved object fields and isolated runtime captures verify the
finding.

Further implementation evidence:

- A paired raster comparison shows both paired foreground labels and the
  white-bubble bounds matching NUN5; a one-pixel bubble-top difference tracks
  normal pulse timing.
- Runtime captures containing simultaneous Health and Chakra labels with
  Recovery values show numeric and paired foreground and bubble geometry
  matching NUN5 at 640x480; remaining subpixel differences follow animation
  timing. Confidence is **verified**.
- A direct call to the lower anisotropic renderer for single labels produced no
  foreground because it bypassed the uniform wrapper's argument shuffle; the two
  renderer interfaces are not interchangeable. Runtime captures of simultaneous
  single/status notifications match NUN5 bubble bounds, label centers,
  clipping, and row placement.
- A cross-index substitution of the substitution-doll pickup into NA2 record
  `0x2E` changed restored geometry only; the next updater pass selected record
  `0x0A` again.
- A controlled class substitution exercised each game's native fixed-class
  vtable. Both objects retained identical positions and NUN5 offsets, and the
  NUN5 object received the traced `1.59375` scale. The native functions
  rendered `Status Effect` and `Recovery` with matching label centers relative
  to the bubble at 640x480. A four-pixel whole-object screen delta accompanied a
  one-frame pulse difference and did not change internal placement.

## Victory presentation

The large WINNER emblem imports NUN5's matching texture,
two meshes, and two animation records into the fixed-size ENDDEMO asset.
Object references are remapped to NA2; unrelated scene resources stay native.
The separate small win-count renderer is unchanged.

Character names use NUN5's complete 94-row English width set and its empty,
first-frame, and second-frame template rules. Both the resident draw helper
and the battle scene initializer use that provider. The battle hook replaces
the inlined Japanese rectangle lookup before the native combined-width
centering code. A zero width produces an empty frame for that character;
no character-specific position adjustment or shared-descriptor edit is used.

## Battle prompts, settings, and results

Pending acceptance: the Practice completed-move plate uses the official NUN5
English OK-stamp rectangle and rotation with the existing imported atlas.
Its native anchor, animated scale, alpha, and lifetime remain unchanged.
Runtime appearance remains unverified. The paired title layouts and donor
evidence are recorded in [Practice layouts](../../knowledge/localization/font/screen_layouts/practice.md).

Mash prompts use the complete seven-record NUN5 English main-prompt table while
retaining NA2's renderer, object layout, and separate controller-glyph table.
NA2's prompt-zero record samples the English Mash artwork vertically and clips
it. Replacing NA2 live range `0x0088F630..0x0088F667` with the complete NUN5
English range produced the NUN5 label dimensions and placement while leaving
the Cross panels independently controlled. Replacing the
[adjacent controller-glyph range](../../knowledge/localization/ui/battle/mash_prompts.md#adjacent-controller-glyph-table)
`0x0088F670..0x0088F6A7` instead left Mash vertical and turned the Cross panels
into incorrect controller glyph rows. Main prompt IDs other than Mash were not
each exercised visibly at runtime.
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
X=`462` for Back with the imported NUN5 legend records. Paired calibration
against NUN5 found that the shared native anchors `400/470` rendered the
records 15/10 pixels right of NUN5, `384/460` rendered them 5/3 pixels left,
and `388/462` matched both legends at `dx=0, dy=0`; the native wrapper
difference is recorded in
[VS confirmation prompts](../../knowledge/localization/ui/battle/selectors_and_prompts.md#vs-confirmation-prompts-and-bottom-legends).
Collection's character viewer selects Controls or Hide at the
shared visible-state call and Display at the separate hidden-state call; it
does not route all three suffix labels through one shared selection.

With the English HOME atlas, NA2's native
[Collection category-title records](../../knowledge/localization/ui/collection.md#collection-category-title-helper)
sample the wrong rows: Characters samples six pixels of the Movie row, Movie
samples the Music row beneath it, and Music starts below the NUN5 Music row, so
that title is absent. NA2's Play record's 24-pixel U-coordinate difference
produces `Pl...` clipping on both Movie and Music, and NA2's substring
animation references resolve the viewer suffix as the malformed `Cisplay`
label. In the Diorama viewer, NA2's native
[viewer-control positions](../../knowledge/localization/ui/collection.md#exact-paired-tables)
place the English Zoom In and Zoom Out controls at X `469` and `468`, clipping
both at the right edge; NUN5 draws all four controls at X `440`.

The Jutsu-selector arrow helper enables sprite mode 10 for the draw, applies
the signed quarter-turn and lower-arrow flip, flushes the sprite, and restores
mode 10 to its native disabled state. The NUN5 mode fields are never left active
across the shared sprite object's lifetime. Arrow-state tests established this
contract:

- NA2's active arrow sprite was at `0x00C7B820`; its rotation field at
  `+0x4C` (`0x00C7B86C`) read back the exact `-pi/2` bit pattern after the
  lower draw, yet the captured arrow still pointed right;
- NUN5's corresponding object was at `0x00BFC420` and consumed the rotation;
- cloning the NUN5 object control fields persistently suppressed unrelated UI;
  partial draw-scoped field tests either had no effect or produced malformed
  sampling;
- disabling the rotation reset did not change the rendered direction.

These results establish that writing a valid rotation float is insufficient
while the NA2 sprite remains in mode 0, and that NUN5's mode fields cannot stay
enabled across the shared object lifetime. The native rotation and rectangle
differences are recorded in
[Open VS Jutsu selector](../../knowledge/localization/ui/battle/selectors_and_prompts.md#open-vs-jutsu-selector).

## Composition boundary

Compatible records, tables, and isolated constants remain guarded binary
edits. Source-owned runtime behavior is declared inside `localization.ui`; its
fragments compose into the shared
`228/228.BIN` resident payload alongside Font contributions. Shared placement
infrastructure does not transfer ownership to the Font feature. The UI
selection remains responsible for matching graphical assets, rectangles,
anchors, visibility, ordering, and ABI-safe draw-path adaptations. Text content
belongs to the translation importer, glyph measurement and wrapping belong to
Font, and regional button behavior belongs to
`localization.regional_input`.

Retail source/donor identities, offsets, and function relationships belong in
the linked knowledge documents. Implementation experiments and measurements of
modified screens stay with the behavior they support in this document.
