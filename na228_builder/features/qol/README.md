# QoL

File-backed quality-of-life patches for the NA2 boot ELF. The original three
patches are exact static migrations of the canonical PNACH `QoL` section. Each
row in `patches.tsv` is an atomic patch and its rows in `edits.tsv` are the
guarded binary edits.

## ELF-Q009: Boot directly to main menu

`ELF-Q009` bypasses the four-screen splash controller while retaining its
native completion path. At boot-ELF virtual address `0x001E11A0` (file offset
`0xE11A0`), the normal code calls the splash update function and then tests its
boolean completion result. The patch replaces only that call with
`addiu v0, zero, 1`; the existing delay-slot `nop` and following result test
remain unchanged.

The caller still waits for the native ROFS/data and startup-resource readiness
flags, then performs the normal splash cleanup. The patch changes the following
state assignment at `0x001E12CC` from title-animation state `2` to title-input
state `3`. At `0x001E1340`, it replaces the title update call with
`addiu v0, zero, 1`, the same result produced when Start is accepted. The
unchanged caller converts that result into main-menu state `4`, substate `1`.

The notice, Bandai Namco, Bandai, CRIWARE, title animation, and interactive
title screen are therefore bypassed. Required loading is deliberately retained
and may appear as a black screen. The independent `Skip CC2 intro` and
`Skip opening` patches are unchanged. The source ELF and file size remain
unchanged. Static and supplied-savestate evidence is recorded in
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
