# QoL

File-backed quality-of-life patches for the NA2 boot ELF. The original three
patches are exact static migrations of the canonical PNACH `QoL` section. Each
row in `patches.tsv` is an atomic patch and its rows in `edits.tsv` are the
guarded binary edits.

## ELF-Q010: Display only first save

`ELF-Q010` changes the shared Save/Load slot-row renderer's loop limit from
three records to one at boot-ELF virtual address `0x001E6970` (file offset
`0xE6970`). The three-slot occupancy scan, selection handler, save data, and
memory card remain unchanged. The modal therefore displays only its first save
record while retaining the native modal frame and first-row behavior.

The guarded edit is statically verified against the clean instruction
`slti v1,s2,3`. Integrated runtime validation remains pending, so the patch is
enabled with status `approved_for_test`.

## ELF-Q009: Loading screen then main menu

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
sequence. At `0x001E1340`, it returns the same result produced by pressing
Start, so the unchanged caller enters main-menu state `4`, substate `1`.
`Skip opening` remains enabled as a second guard on the opening path.

The notice, Bandai Namco, Bandai, CRIWARE, opening, and interactive title screen
are therefore bypassed. The source ELF and file size remain unchanged. Static,
supplied-savestate, and rejected-candidate evidence is recorded in
`docs/knowledge/game/startup.md`; integrated runtime validation remains pending.

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
enabled by default with status `runtime_proven`.

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
pending, so `ELF-Q008` is enabled by default with status `approved_for_test`.
