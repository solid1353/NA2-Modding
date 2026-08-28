# General

Project-wide selectable behavior that does not belong to gameplay, rendering,
localization, or quality-of-life categories. Selectable nodes and guarded edits
are owned by `features.general` in `@builder/catalog/catalog.modcat`.

## Unlock all content without loading a save

`features.general.unlock_all` selects the resident injection
`i__qol__content__unlock_all__availability`. Seven guarded hooks replace only the
save-backed reads for characters, the Character Select R1-form gate, secondary
content, the 32-entry small table, the six grouped tables, and metadata-valid
jutsu, plus progress slot `0x6A`, which gates Ultimate difficulty. The injected
helpers reproduce bounded fully unlocked values and the native stable state for
Collection figures; the progress helper returns available only for slot `0x6A`
and preserves every other native progress read. Native wrappers, metadata
checks, and callers remain intact.

The feature performs no save-data writes. It therefore exposes characters and
their R1 forms, supports, stages, jutsu, and Collection entries plus Ultimate
difficulty without importing the reference save's settings, progress,
currency, inventory, statistics, or availability bytes. Disabling the setting
restores the native save-dependent readers.

The first character candidate used an invalid mask derived through the wrong
global and produced an incorrect, displaced roster. The corrected helper makes
all 94 stored character IDs available and leaves native roster filtering to
the existing callers. User runtime testing on 2026-08-10 confirmed the
correction. The reader contracts, stored values, hook seams, evidence, and
rejected-mask failure are recorded in
[`../knowledge/game/content_availability.md`](../knowledge/game/content_availability.md).

User runtime testing on 2026-08-11 confirmed that R1 forms remain accessible
without a loaded save and that Collection figure pedestals render when
`unlock_all` is enabled. The R1 hook supplies only the gate's fully unlocked
progress value `0x66`; grouped Collection reads return their native stable
viewed-and-unlocked state `3`.

User runtime testing on 2026-08-21 confirmed that Ultimate difficulty remains
selectable with `unlock_all` in NA2 and with the regular NUN5 PNACH port.

## Imported game title

`general.replace_imported_game_title` replaces the imported NUN5 title
`Naruto Shippuden: Ultimate Ninja 5` with root `settings.title` before the
string patcher decides which strings stay inline and which use linked external
storage. Its catalog definition guards the known six mappings and seven total
occurrences. Setting it to `false` leaves the imported title unchanged. It is
independent of the settings under `features.memory_card`.
