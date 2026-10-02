# NUN3 and NUN4 item inventories

This document records the five-slot battle-item inventories of retail NUN3
and NUN4: NUN3's item panel, slot objects, cache, compacting removal and HUD
list, and NUN4's item-wheel layout, item placement, fading and item-select
badges. Retail NA2 (`SLPS-25837`) uses a three-slot inventory, recorded in
[Battle item inventory](battle_item_inventory.md).

Addresses use `D/L/F`: preserved Ghidra address, live runtime address, and
complete-file offset, as defined in
[address conventions](../game/files/file_identities.md#address-conventions).
NUN3 BATTLE.BIN live addresses use the overlay base recorded there.
NUN4 addresses without a `D` form are live memory.

## Research coverage

- **Assigned scope:** NUN3's item manager and panel layout, slot objects,
  five-slot routines, cache, compacting removal and HUD list; NUN4's item-wheel
  layout tables, item-step offsets, height interpolation, scale, opacity and
  item-select badges.
- **Exploration depth:** NUN3 was examined in its item-manager constructor,
  panel constructor, cache build and restore, removal, and HUD routines only.
  NUN4's item-step, height lookup, item draw, badge and sprite wrappers were
  read from retail BATTLE.BIN disassembly and live memory.
- **Confirmed coverage:** NUN3's manager and panel layouts, slot object
  fields, five-slot loops, cache layout, compacting removal, HUD layout routine
  structure, horizontal step offsets, per-side height records and frame-scale
  table. NUN4's live layout tables, horizontal item offsets, height
  interpolation, scale, count-dependent opacity formula and badge opacity.
- **Unresolved or untested:** NUN3 item addition and selection input; the key
  field of NUN3's per-side height records and its count-keyed table; the NUN4 routine that reads the wheel bases and
  shared `x` value.
- **Deliberate exclusions and overlap:** Retail NA2's inventory belongs to
  [Battle item inventory](battle_item_inventory.md). File identities and
  overlay bases belong to
  [Retail game file identities](../game/files/file_identities.md).
- **Evidence limitations:** NUN3 findings are static except for one battle
  screenshot that corroborates the list shape and badge placement. NUN4
  (`SLUS-21862`) table values were read from live memory of one battle state
  with screenshots; its retail BATTLE.BIN disassembly establishes the
  item-step, placement and fading formulas. No runtime trace confirmed NUN3
  animation or other NUN3 behavior.

## NUN3 five-slot inventory

NUN3 uses a manager-and-panel structure homologous to retail NA2's, with
different offsets. Resident item-manager constructor `0x00291120` allocates two
`0x90`-byte panels, runs wrapper `L 0x008294C0` with the side, and stores them
at manager `+0x84` and `+0x88`.

| Panel offset | Content |
| ---: | --- |
| `+0x2C..+0x3C` | Pointers to five 32-byte slot objects |
| `+0x40` | Selected slot index |
| `+0x44` | Side |
| `+0x48` | Occupied slot count |
| `+0x50` | Base position from a per-side table |
| `+0x70` | Float list scroll value |

A slot object holds an occupied byte at `+0`, its fixed index at `+4`, a
32-bit item code at `+8`, the count at `+0xC`, list position
`index * 32 + 16` as a float at `+0x10`, an animated position at `+0x14`, and
animation state at `+0x18/+0x1C`.

| D/L/F | Role |
| --- | --- |
| `00829520/00829560/6DD60` | Panel constructor; allocates five slots |
| `0082A700/0082A740/6EF40` | Cache build over five slots |
| `0082A830/0082A870/6F070` | Cache restore over five slots |
| `0082ACD0/0082AD10/6F510` | Remove the selected item, compact the remaining items, and decrement `+0x48` |
| `0082B1D0/0082B210/6FA10` | Move a slot range and restart its slide animation |
| `0082B520/0082B560/6FD60` | HUD layout: derives a list index from `+0x70 / 32`, then a 6-case table at `L 0x0093B270` selects the frames and slots drawn for occupied counts `0..5` |
| `0082B7D0/0082B810/70010` | Draw one frame at a relative position `-3..3` |
| `0082B8C0/0082B900/70100` | Draw one slot through five item-draw calls with selectors `-2..2` |
| `0082BB20/0082BB60/70360` | Draw one item |

The cache at `L 0x00946050` stores five 8-byte `(code, count)` entries per
side, stride `0x28`. Removal keeps occupied items contiguous. The HUD is a
scrolling list driven by slot positions `index * 32 + 16` and scroll `+0x70`.
Selector routine `D/L 0082B990/0082B9D0` returns the horizontal offset for a
relative position: `35.2` one step away and `28.8 + 35.2 = 64.0` two steps
away, negated for negative positions.

The item draw reads per-side tables of seven 16-byte records at
`L 0x00919850` (`0x70` bytes per side) and a table keyed by occupied count at
`L 0x00919950`. The side-0 records hold heights `-25, -25, -9, 0, 8, 7, 7`
from left to right; side 1 holds `7, 7, 8, 0, -9, -25, -50`. Frame scale comes
from a seven-entry table at `L 0x00919930` holding
`0.6, 0.8, 1.0, 1.2, 1.0, 0.8, 0.6` for relative positions `-3..3`.

A retail NUN3 battle screenshot matches this shape: with the selection in the
wheel, P1's left neighbors rise and its right neighbors stay level, P2 is
mirrored, and the two item-select badges sit below the wheel on either side.

## NUN4 item wheel

NUN4 keeps NUN3's five-slot structure. Its HUD routines are at live
`0x006F0C80` (frame draw), `0x006F0D70` (five-position slot draw),
`0x006F0E40` (item step), `0x006F0F20` (layout search), and `0x006F0FD0`
(item draw). Its live layout tables hold the keys that are zero in NUN3's file
copy:

| Table | Live address | Values |
| --- | --- | --- |
| Side 0 layout `(x, y)` | `0x0083C810` | `(-85,-25) (-60,-25) (-42,-9) (0,0) (43,8) (70,7) (100,7)` |
| Side 1 layout `(x, y)` | `0x0083C880` | `(-100,7) (-70,7) (-43,8) (0,0) (42,-9) (60,-25) (85,-50)` |
| Frame scale by position `-3..3` | `0x0083C8F0` | `0.6, 0.8, 1.0, 1.2, 1.0, 0.8, 0.6` |
| Visible `x` ranges by count `2..5` | `0x0083C930` | `(-35,-10,35,60) (-60,-35,35,60) (-65,-40,47,75) (-75,-45,47,75)` |
| Wheel base by side | `0x0083C970` | `(10,340)`, `(367.2,340)` |
| Shared `x` value after the bases | `0x0083C990` | `67.4` |
| Count offset by side | `0x0083C9E0` | `(0,27)`, `(0,27)` |
| First badge by side | `0x0083C9A0` | `(-60,30)`, `(-50,30)` |
| Second badge by side | `0x0083C9C0` | `(50,30)`, `(60,30)` |

A NUN4 battle screenshot places the wheel centers near `x = 77` and `435` in
the 512-unit HUD space, which matches each base plus `67.4`; the routine that
reads these values was not traced. The frame draw at `0x006F0C80` reads the
position-indexed scale table, and frames are drawn at the layout points.

The item-step routine `D/L 006F0E00/006F0E40` returns signed offsets `0`,
`35.2`, and `28.8 + 35.2 = 64` for steps `0`, `1`, and `2`. Item draw
`D/L 006F0F90/006F0FD0` adds that offset to the slot's current horizontal
displacement and interpolates its height between the neighboring layout
records. Its tail at `D 0x006F10D8..0x006F127C` computes `d = |x|`, scale
`1.2 - 0.6 * d / 96`, and count-dependent opacity. Opacity is `1` inside the
inner boundary, `0` beyond the outer boundary, and
`1 - (d - inner) / (outer - inner)` between them. Negative `x` uses the first
two range-table values (absolute outer, inner); positive `x` uses the last two
(inner, outer). For five items this gives negative-side boundaries `45..75`
and positive-side boundaries `47..75`, making the items at distance `64`
partially transparent even at rest. An unusable-item marker receives
`0.8 * opacity`, and the item sprite receives the full opacity through
wrappers `L 0x006F27A0` and `L 0x006F2770` respectively.

The visible ranges place the extra item on the positive-`x` side when the
count is even. By user observation, Item Select in NUN4 and in retail NUN5
moves P1's selection to the item on the left. Inference: the positive-`x`
side therefore holds earlier items in selection order.

A NUN4 battle screenshot shows the first badge as L2 on the left and the
second as R2 on the right for both players. The badge objects are built at
`0x006EEA08` and `0x006EEA48` from the side-indexed badge tables. Each is one
button sprite with no separate frame. The HUD draw at `0x006F08B0` draws both
badges through `0x006F2630`, which passes opacity `0.2` to sprite draw
`0x003AC890` while panel `+0x40` is below `2` and `1.0` otherwise, with the
press scale at badge `+0x30`.
