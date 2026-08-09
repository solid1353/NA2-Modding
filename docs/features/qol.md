# QoL

File-backed and resident quality-of-life behavior. Selectable nodes, guarded
binary edits, runtime hooks, and payload declarations are selected by
`na228_builder/catalog/qol.json`.

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

`ELF-Q009` replaces the four splash screens with the game's existing main-menu
presentation while preserving the two native startup-loader checks. The QoL
runtime-injector hook replaces the splash update call at boot-ELF virtual
address `0x001E11A0` (file offset `0xE11A0`). It initializes the existing
boot-safe splash controller, holds its first draw slot active, and returns
splash completion to the unchanged startup loop.

A second guarded hook replaces the splash sprite draw call at boot-ELF file
offset `0xE11E0`. It suppresses the original logo sprite and uses the same
boot-safe solid-primitive renderer to draw a large two-digit percentage, percent
sign, and progress bar. Each rectangle is submitted as an independent primitive
so separate digit segments cannot be joined by the renderer's triangle strip.
At the game's 30 FPS startup rate, the counter maps 750 frames to the measured
25-second load and caps at `99%`; the real loader flags, not the displayed
estimate, determine when startup may continue.

After the required startup loaders complete, the file-backed binary patch
writes state `3` instead of state `2` at `0x001E12CC`, bypassing the opening
sequence. The patch at `0x001E1340` returns native title result `2`
(`Continue`), so the unchanged caller enters main state `4`, substate `2`.
That substate constructs the shared Save/Load controller in mode `1`; the
`ELF-Q010` first-record dispatch retains the native Yes/No load confirmation.
Yes performs the native load before the normal main-menu loader continues; No
enters the main menu without loading. `Skip opening` remains enabled as a
second guard on the opening path.

The sequence bypasses the notice, Bandai Namco, Bandai, CRIWARE,
opening, interactive title, and Load-list screens. The source ELF and file size
remain unchanged. Static, supplied-savestate, and rejected-candidate evidence
is recorded in `docs/knowledge/game/startup.md`; user runtime validation
confirmed the integrated behavior.

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
pending, so the corresponding catalog node remains marked `proven: false`.
