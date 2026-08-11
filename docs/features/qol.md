# QoL

File-backed and resident quality-of-life behavior. Selectable nodes, guarded
binary edits, runtime hooks, and payload declarations are selected by
`na228_builder/catalog/qol.modcat`.

## Unlock all content without loading a save

`qol.content.unlock_all` selects the resident injection
`i__qol__content__unlock_all__availability`. Six guarded hooks replace only the
save-backed reads for characters, the Character Select R1-form gate, secondary
content, the 32-entry small table, the six grouped tables, and metadata-valid
jutsu. The injected helpers reproduce bounded fully unlocked values and the
native stable state for Collection figures; native wrappers, metadata checks,
and callers remain intact.

The feature performs no save-data writes. It therefore exposes characters and
their R1 forms, supports, stages, jutsu, Shop items, and Collection entries
without importing the reference save's settings, progress, currency,
inventory, statistics, or availability bytes. Disabling the setting restores
the native save-dependent readers.

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

## ELF-Q010: Use only first save

`ELF-Q010` changes the shared Save/Load slot-row renderer's loop limit from
three records to one at boot-ELF virtual address `0x001E6970` (file offset
`0xE6A70`). The three-slot occupancy scan, save data, and memory card remain
unchanged. Any fallback slot display therefore contains only its first record.
Two additional guarded edits replace the handler's Down and Up input-mask
results with zero before either movement branch, so vertical input cannot
change the selected slot or play the slot-navigation sound.

The upper frame is reduced from X/Y/width/height `58/10/400/224` to
`146/90/224/96`, placing a compact one-record panel above and visibly detached
from the unchanged lower instruction panel. Within it, the date/play-time block
moves from local X `108`, Y `14` to X `45`, Y `20`. The redundant slot-number
record moves outside the viewport, the row-separator condition is disabled, and
the now-meaningless independent slot-cursor model is not drawn. The lower
instruction panel and all of its contents remain unchanged.

The normal record-selection path is bypassed before its list update. The
guarded edit at runtime `0x001E5008` sets the child selection to record zero,
calls the existing `FUN_001e1e10` load operation when the controller mode is
`1`, and branches to the unchanged `FUN_001e1e50` save body for every other
mode. It then uses the controller's unchanged post-operation states.

The native `Load this data?` confirmation remains visible. Yes continues the
record-zero load. The guarded correction changes the No branch at
runtime `0x001E5474` (file offset `0xE5574`) from Save/Load state `4` to its
native completion state `8`, avoiding reconstruction of the removed record
list. The startup Continue result mapping at runtime `0x001E9FB8` (file offset
`0xEA0B8`) then maps that no-load completion to the existing success path, which
enters the main menu without loaded save data. The clean
instructions, replacement branch targets, and immediates are statically
verified, and user runtime validation confirmed the integrated behavior.

## ELF-Q009: Loading screen then first-save load

`ELF-Q009` replaces the four splash screens with a boot-safe loading
presentation while preserving the two native startup-loader checks. The QoL
runtime-injector hook replaces the splash update call at boot-ELF virtual
address `0x001E10A0` (file offset `0xE11A0`). It initializes the existing
boot-safe splash controller, holds its first draw slot active, and returns
splash completion to the unchanged startup loop.

A second guarded hook replaces the splash sprite draw call at virtual address
`0x001E10E0` (file offset `0xE11E0`). It suppresses the original logo sprite
and uses the same boot-safe solid-primitive renderer to draw a large two-digit
percentage, percent sign, and progress bar. Each rectangle is submitted as an
independent primitive so separate digit segments cannot be joined by the
renderer's triangle strip. At the game's 30 FPS startup rate, the counter maps
750 frames to the measured 25-second load and caps at `99%`; the real loader
flags, not the displayed estimate, determine when startup may continue.

After the required startup loaders complete, the common file-backed edits write
state `3` instead of state `2` at virtual address `0x001E11CC` (file offset
`0xE12CC`) and return native title result `2` (`Continue`) at virtual address
`0x001E1240` (file offset `0xE1340`). The unchanged caller enters main state
`4`, substate `2` and constructs the shared Save/Load controller in load mode.
`Skip opening` remains enabled as a second guard on the opening path.

The catalog exposes two disjoint literal branches at
`qol.startup.save_loading`:

- `"manual"` retains the full Save/Load controller. With
  `qol.save_load.display_only_first_save`, it shows the native record-zero
  confirmation; Yes loads the save and No enters the menu without loading.
- `"automatic"` replaces only Continue's per-frame visible-controller update
  with a silent generated-C driver for the same asynchronous memory-card
  worker. It scans port zero, requests record zero when present, internally
  resolves the native load confirmation as Yes, waits through checksum-verified
  load completion, and then lets Continue perform its unchanged cleanup,
  save-dependent setup, and main-menu loading. Its separate guarded no-op at
  file offset `0xEA0D0` prevents the Save/Load child from drawing.

The automatic branch treats no card, a wrong card type, an unformatted card, no
game directory, an empty first record, read/checksum failure, a card change, and
every other non-success terminal worker result as no-load completion. In all of
those cases the existing guarded result mapping enters the main menu without
loaded data. It does not synthesize a timeout while the native worker reports a
busy state.

The base configuration selects `"automatic"`; `"manual"` remains available as
the confirmed visible fallback. The sequence bypasses the notice, Bandai Namco,
Bandai, CRIWARE, opening, interactive title, Load list, card-status messages,
and load confirmation before the main-menu loading screen. Full development
build `20260811_054948_801_pid12700` succeeded, and user runtime validation on
2026-08-11 confirmed the integrated automatic behavior. The manual branch also
remains user-confirmed.
The complete disassembly findings, worker layout, outcome matrix, and state
machine are recorded in
[`../knowledge/game/startup.md`](../knowledge/game/startup.md).

`qol.save_load.display_only_first_save` remains an independent setting because
it controls the visible Save/Load interface and is not used by the automatic
startup driver.

## ELF-Q004: Remove Adventure mode

NUN6 A35 removes Adventure from the Mode Select carousel by storing the signed
sentinel `-1` in entry 0 of the boot ELF's seven-entry mode table. The menu setup
loop skips entries whose table value is negative, so the item is omitted rather
than displayed and blocked after selection.

The corresponding tables are:

- NA2: virtual address `0x005D51D0`, ELF offset `0x4D52D0`, values
  `(4, 2, 3, -1, 5, 6, 7)`.
- NUN5: virtual address `0x005DC300`, ELF offset `0x4DC480`, values
  `(4, 2, 3, -1, 5, 6, 7)`.
- NUN6 A35: the NUN5 address and offset, values
  `(-1, 2, 3, -1, -1, -1, 7)`.

`ELF-Q004` changes only NA2 entry 0 from `04 00 00 00` to `FF FF FF FF`.
NUN6's changes to entries 4 and 5 are unrelated and are intentionally not
ported. NUN5 is not a suitable byte donor because its entry 0 matches NA2; the
raw replacement is used because the desired behavior deliberately follows the
NUN6 variant. The source ELF remains untouched and the output size is preserved.

Runtime testing of the integrated Current ISO confirmed that Adventure is absent
and the remaining Mode Select entries work normally. `ELF-Q004` is therefore
enabled in the release configuration; its runtime proof is retained in documentation.

## ELF-Q008: Remove Shop

`ELF-Q008` applies the same filtered-carousel mechanism to Shop. Shop is entry
4 of the same seven-entry boot-ELF table, at virtual address `0x005D51E0` and
ELF offset `0x4D52E0`, where its clean value is `5`.

The patch changes only that entry from `05 00 00 00` to `FF FF FF FF`. The
menu setup loop therefore omits Shop while leaving Adventure, Free Battle,
Practice, Collection, Options, and the existing unused entry unchanged. The
source ELF remains untouched and the output size is preserved.

The canonical `Restore Shop` cheat writes value `5` back to `0x005D51E0`,
re-enabling Shop without changing the file-backed default. The table mapping
and patch guards are statically verified; integrated runtime validation remains
pending.
