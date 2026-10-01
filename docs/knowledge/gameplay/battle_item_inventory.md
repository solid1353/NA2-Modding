# Battle item inventory

This document records how clean NA2 stores, selects, draws, and restores the
per-side battle-item inventory, and compares it with the five-slot inventories
of clean NUN3 and NUN4. Item effects applied on use are owned by
[Battle status effects and item-effect lifecycle](battle_items_and_status_effects.md#three-slot-battle-item-path-0x510x73).

Addresses use `D/L/F`: preserved Ghidra address, live runtime address, and
complete-file offset. Preserved overlay addresses are live minus `0x40`
([address conventions](../game/files/file_identities.md#address-conventions)).
Direct call targets and absolute data operands are live addresses.

## Research coverage

- **Assigned scope:** NA2 inventory panel layout, every BTL routine that walks
  its slots, the resident wrappers that reach them, item selection, the battle
  HUD item wheel, CPU item use, and the Practice item cache; plus the matching
  NUN3 and NUN4 structures used as five-slot references.
- **Exploration depth:** NA2 BTL `D 0x0070F420..0x00712840` was disassembled
  from raw bytes because preserved function boundaries there are unreliable.
  Every direct `jal` into the slot routines was searched in the NA2 ELF and BTL.
  The per-frame panel update was also read through GhidrAssist MCP.
  The resident wrapper block `0x00375570..0x003762F0` was mapped to its BTL
  targets. NUN3 was examined in its item manager constructor, panel
  constructor, cache, restore, removal, and HUD routines only. NUN4's item-step,
  height lookup, item draw, and sprite wrappers were read through GhidrAssist
  MCP. Its function boundaries split these routines, so missing instructions
  were read from MCP memory dumps.
- **Confirmed coverage:** NA2 panel allocation, owned objects, slot objects,
  slot-count constants, selection advance, wheel geometry, the root draw's
  call order including the support-gauge draw, CPU use of slot
  relations, and cache layout. NUN3 homologous manager and panel layouts, the
  five-slot loops, compacting removal, and the HUD layout routine structure.
  NUN4's horizontal item offsets, height interpolation, scale, and count-dependent
  opacity formula; NA2's sprite-opacity forwarding and auxiliary model draw.
- **Unresolved or untested:** Roles of resident `0x00375AA0` and
  `0x00375DF0` beyond their slot calls; the meaning of the fighter fields that
  key the constructor's seed tables; what follows the Practice cache in BSS;
  NUN3 add and selection input; the key field of NUN3's per-side height records
  and its count-keyed table; indirect calls into the panel; writes to the
  badge object's side field outside the panel constructor were not searched.
- **Deliberate exclusions and overlap:** Item effects, pickup metadata, and
  field-item selection belong to the status-effect document. Practice
  snapshot flow belongs to [Practice mode](practice_mode.md). CPU state
  dispatch belongs to [Battle AI](battle_ai.md). Label text belongs to
  [item-status presentation](../localization/ui/battle/item_status.md).
- **Evidence limitations:** Findings are static except for one user-supplied
  NUN3 battle screenshot, which corroborates the NUN3 list shape and badge
  placement, and one NUN4 (`SLUS-21862`) battle savestate and screenshot, from
  which the NUN4 values were read. NUN4 addresses are live memory from that
  savestate; NUN4's retail BATTLE.BIN disassembly additionally establishes the
  item-placement and fading formulas. No runtime trace confirmed NA2 wheel
  positions, animation timing, or other NUN3 behavior. NUN3 is a different
  engine generation, so homologous layouts are structural comparisons, not
  proof that NUN3 code can run in NA2.

## NA2 ownership

Resident item-manager constructor `0x00373AB0` allocates one `0x80`-byte panel
per side with `0x00117150`, runs base initializer `L 0x0070F460`, then panel
constructor `L 0x0070F740` with the side, and stores the panels at manager
`+0x6C` (side 0) and `+0x70` (side 1). Resident `0x00375A60` returns the panel
for a side.

## NA2 panel layout

| Offset | Content |
| ---: | --- |
| `+0x00,+0x04,+0x08` | Pointers to three separately allocated 8-byte slot objects |
| `+0x0C` | Owned 28-byte animation object |
| `+0x10` | Owned 48-byte object |
| `+0x14` | Owned 24-byte object; receives the selected item code each update |
| `+0x18` | Owned 16-byte list object |
| `+0x1C` | Owned 44-byte support-gauge controller |
| `+0x20` | Side |
| `+0x24` | Selected slot index |
| `+0x28` | Float wheel animation offset |
| `+0x30,+0x34` | Base screen position: X `66.0` for side 0 or `446.0` for side 1, Y `340.0` |
| `+0x40` | Vector added to `+0x30` by `L 0x0070FE40` |
| `+0x44` | Float animated toward `200.0` by `L 0x00711B40`; `L 0x0070FE60` returns it |
| `+0x50` | Wheel origin used by the HUD draw |
| `+0x60..+0x63` | State bytes; `+0x61` is set by activation and `+0x62` by advance |
| `+0x64` | Inline object initialized by the base initializer |

A slot object holds the item code byte at `+0` and signed count at `+4`. A slot
is occupied only when both are nonzero. Count `-1` is not decremented or
capped; other counts are clamped to `0..9`. Destructor `L 0x0070F4E0` frees the
three slot objects and the owned objects.

After allocating the slots, the constructor reads the side's fighter from
resident `0x003769C0` and seeds items in three steps. A table of 93 4-byte
`(s16 key, s8 code)` entries at `0x008A8D70` matched against fighter `+0x68`
can place a code in slot 0 with count `-1`. When resident
`0x00373970` reports `1`, the code from resident `0x00373980` is added with
count `3` if fighter `+0x68` is `0x54`, otherwise `1`. Finally, each of 26
4-byte `(s16 threshold, s8 code, s8 count)` entries at `0x008A8D00` whose threshold
does not exceed fighter `s16 +0x17E` is added.

The slot pointer array cannot grow in place: `+0x0C` and `+0x10` hold owned
object pointers. No unused words were proven inside the `0x80` bytes.

## NA2 slot routines

Routines that walk the slot pointers use a literal loop bound of `3`, and the
selection wrap uses literal `2` as the last index. The HUD draw also caps its
occupied count at `3`.

| D/L/F | Role |
| --- | --- |
| `0070F420/0070F460/5B560` | Base initializer; clears the three pointers |
| `0070F700/0070F740/5B840` | Constructor; allocates three slots and seeds starting items |
| `0070FB90/0070FBD0/5BCD0` | Can-add test: a known item with a same-code slot below 9, or fewer than three occupied slots |
| `0070FC40/0070FC80/5BD80` | Full test: occupied count at least 3 |
| `0070FD00/0070FD40/5BE40` | Find slot by item code |
| `00710000/00710040/5C140` | Add: stack onto a same-code slot, else fill the next empty slot if fewer than three are occupied |
| `00710260/007102A0/5C3A0` | Put a code in slot 0 with count `-1` and set `+0x61 = 3` |
| `00710290/007102D0/5C3D0` | Decrement by item code; reselect when the selected slot empties |
| `00710430/00710470/5C570` | Decrement the selected slot; reselect and bump `+0x28` when it empties |
| `00710580/007105C0/5C6C0` | Clear every slot whose item is not special category `6` |
| `00710690/007106D0/5C7D0` | Step `n` occupied slots from `+0x24`, wrapping `0..2` |
| `00710810/00710850/5C950` | Step `n` empty slots from `+0x24`, wrapping `0..2` |
| `007109B0/007109F0/5CAF0` | Build the Practice cache |
| `00710AC0/00710B00/5CC00` | Restore from the Practice cache |
| `00710C30/00710C70/5CD70` | Count occupied slots |
| `00710CB0/00710CF0/5CDF0` | Relation of a slot to the selection: `1` selected, `2` one step forward, `3` one step back, `0` otherwise |
| `00710DE0/00710E20/5CF20` | Item category of a slot |
| `00711180/007111C0/5D2C0` | Selected item code for use |
| `00711340/00711380/5D480` | Activation |
| `00711950/00711990/5DA90` | Selection advance |
| `00711E10/00711E50/5DF50` | HUD wheel draw |
| `00712340/00712380/5E480` | Per-frame panel update |

Resident wrappers reach these routines through the manager:
`0x00374190` pickup and `0x00374B30` add; `0x00375840` can-add;
`0x00375570` and `0x003755D0` advance; `0x00375630` selected item;
`0x00375690` activate; `0x003756F0` selected code; `0x003759B0` count;
`0x003759E0` relation; `0x00375A20` category; `0x00375FD0` cache; and
`0x00376050` restore. Resident `0x00375AA0` and `0x00375DF0` call count,
selected-slot decrement, and clear routines; their triggering events were not
investigated.

## NA2 selection

Fighter input gate `FUN_002366F0` calls resident `0x003755D0`, which reaches
advance `L 0x00711990`. Advance does nothing while panel state `+0x60` is `1`
or when fewer than two slots are occupied. Otherwise it sets `+0x62`, adds
`1.0` to `+0x28`, steps one occupied slot forward, stores the new index at
`+0x24`, and plays sound `42`. Selection only moves forward and skips empty
slots; slots are not compacted.

The BTL action translator at `D 0x006F0500..0x006F056C` maps native Use Item
(action bit `0x08`) to fighter input `0x01000000` and Item Select (`0x10`) to
`0x02000000`. Linked Attack (`0x20`) first sets `0x04000000`, then replaces it
with `0x20000000`, so player input never delivers `0x04000000`. The fighter
input gate still tests `0x04000000` after `0x02000000` and would call resident
`0x00375570`, whose only caller is that gate. `0x00375570` also reaches the
forward advance through wrapper `L 0x00711970`. No other producer of
`0x04000000` was found in BTL.

## NA2 HUD wheel

Draw `L 0x00711E50` counts occupied slots `n` (at most 3). It draws the panel
background at `+0x50`, then one empty-slot frame for each wheel position `k`
from `n` to `2`, then each occupied item at positions `k = -1..n-1` shifted by
the animation offset `+0x28`. For position `k`:

```text
x = -45 * sin(0.2 * pi * k)     (negated for side 1)
y = -20 * k
first factor  = 1 - 0.10 * |k|
second factor = 1 - 0.15 * |k| for k >= 0, else 1 - |k|
```

The root draw `L 0x007127B0` first stores `+0x30 + +0x40` at the wheel
origin `+0x50`. It draws the item-select button badge before the wheel, and
after the wheel it calls the `+0x18` and `+0x14` objects and the support-gauge
draw for `+0x1C` (`L 0x0071D270`, which updates the controller and draws the
support block while its visibility byte `+0x0A` is nonzero). Its object at panel `+0x10` holds the badge offset from the wheel
(`-38.0, 16.0`, with `x` negated for side 1) at `+0x10`, its scale at `+0x20`,
and the sprite at `+0x24`. Resident `0x00376F10(side, action)` reads the side's
binding for the action and maps it through six `(button mask, sprite)` pairs at
`0x005B00B0`: `R1 0x76`, `R2 0x77`, `L1 0x74`, `L2 0x75`, `L1+R1 0x74`,
`L2+R2 0x75`. The badge frame is sprite `0x7B`, and the button sprite is dimmed
to `0.8` when fewer than two slots are occupied. The draw passes the badge
object's `+0x00` as the side, but the panel constructor clears it to `0` for
both panels, so both show P1's binding. Byte `+0x28`, set to `1` by the
constructor, selects action `4` (Item Select); zero would select action `5`.
An action whose binding is not in the six-pair table maps to sprite `-1`, and
the frame is still drawn.

Position `0` is the selection, and later slots in selection order take
positions `1..n-1`. At rest the second factor is `0` at `k = -1`, so the
previous item is visible only while the animation offset is nonzero. Resting
positions are therefore `0..2`, and `x` is `0` again at `k = 5`. The selected
slot's count is drawn beside the wheel, with a separate element for count
`-1`. The per-frame update clamps `+0x28` to `-1..1` and moves it toward zero.
In `D 0x00712360..0x007123BC`, it reads and clamps the offset, then calls
`L 0x006C12A0` with target `0.0`, step `0.2` (float bits `0x3E4CCCCD`), and
the address of `+0x28`. The occupied-count loop starts afterward at
`D 0x007123C0`. Thus repeated advance calls can accumulate an offset beyond
one before this update, but the clamp discards that excess before drawing.

Item draw `D/L 00711BF0/00711C30` forwards its scale and opacity floats to
resident sprite draw `0x00377720`. The separate auxiliary draw
`D/L 00712BE0/00712C20` handles codes `0x51..0x73` through a model object;
its arguments contain scale and position but no opacity value.

## NA2 CPU item use

Battle AI state `25` handler `D/L/F 006F4ED0/006F4F10/41010` works in raw slot
indexes. With no target stored, it tries each index below the occupied count,
keeps the first whose category is `3`, `4`, or `6` on a 30% roll, and stores it
at AI work record `+0x58`. The loop bound is an occupied count, but the indexes
are raw slot positions. With a target stored, it asks relation
`L 0x00710CF0`: relation `1` can set input mask `0x01000000` (use) in record
`+0x10`, relations `2` and `3` set `0x02000000` (item select), and relation `0`
resets the state. The relation routine recognizes only one step in each
direction.

## NA2 Practice cache

The cache at `0x008D6A60` holds two sides of three 2-byte `(code, count)`
entries, `6` bytes per side. Build and restore use the literal side stride `6`
and loop bound `3`. The next direct BTL data reference after the cache is
`0x008D6A80`; no direct reference to `0x008D6A6C..0x008D6A7F` was found.
[Practice mode](practice_mode.md#discrete-practice-controller-reset) owns when
the cache is captured and restored.

## NUN3 five-slot inventory

NUN3 uses the same manager-and-panel design with shifted offsets. Resident
item-manager constructor `0x00291120` allocates two `0x90`-byte panels, runs
wrapper `L 0x008294C0` with the side, and stores them at manager `+0x84` and
`+0x88`. BATTLE.BIN addresses below use live base `0x007BB800`.

| NUN3 panel offset | Content |
| ---: | --- |
| `+0x2C..+0x3C` | Pointers to five 32-byte slot objects |
| `+0x40` | Selected slot index |
| `+0x44` | Side |
| `+0x48` | Occupied slot count |
| `+0x50` | Base position from a per-side table |
| `+0x70` | Float list scroll value |

A NUN3 slot object holds an occupied byte at `+0`, its fixed index at `+4`, a
32-bit item code at `+8`, the count at `+0xC`, list position
`index * 32 + 16` as a float at `+0x10`, an animated position at `+0x14`, and
animation state at `+0x18/+0x1C`.

| D/L/F | Role |
| --- | --- |
| `00829520/00829560/6DD60` | Panel constructor; allocates five slots |
| `0082A700/0082A740/6EF40` | Practice-style cache build over five slots |
| `0082A830/0082A870/6F070` | Cache restore over five slots |
| `0082ACD0/0082AD10/6F510` | Remove the selected item, compact the remaining items, and decrement `+0x48` |
| `0082B1D0/0082B210/6FA10` | Move a slot range and restart its slide animation |
| `0082B520/0082B560/6FD60` | HUD layout: derives a list index from `+0x70 / 32`, then a 6-case table at `L 0x0093B270` selects the frames and slots drawn for occupied counts `0..5` |
| `0082B7D0/0082B810/70010` | Draw one frame at a relative position `-3..3` |
| `0082B8C0/0082B900/70100` | Draw one slot through five item-draw calls with selectors `-2..2` |
| `0082BB20/0082BB60/70360` | Draw one item |

NUN3's cache at `L 0x00946050` stores five 8-byte `(code, count)` entries per
side, stride `0x28`. Removal keeps occupied items contiguous. The HUD is a
scrolling list driven by slot positions `index * 32 + 16` and scroll
`+0x70`, not NA2's wheel. Selector routine `D/L 0082B990/0082B9D0` returns the
horizontal offset for a relative position: `35.2` one step away and
`28.8 + 35.2 = 64.0` two steps away, negated for negative positions. The side-0
records at `L 0x00919850` hold heights `-25, -25, -9, 0, 8, 7, 7` from left to
right; side 1 holds `7, 7, 8, 0, -9, -25, -50`. A clean NUN3 battle screenshot
matches this shape: with the selection in the wheel, P1's left neighbors rise
and its right neighbors stay level, P2 is mirrored, and the two item-select
badges sit below the wheel on either side. Frame scale comes from a seven-entry table at
`L 0x00919930` holding `0.6, 0.8, 1.0, 1.2, 1.0, 0.8, 0.6` for relative
positions `-3..3`. The item draw also reads per-side tables of seven 16-byte
records at `L 0x00919850` (`0x70` bytes per side) and a table keyed by
occupied count at `L 0x00919950`.

## NUN4 item wheel

NUN4 uses the NUN3 design with NA2's larger wheel art. In the savestate its
HUD routines sit in live memory at `0x006F0C80` (frame draw), `0x006F0D70`
(five-position slot draw), `0x006F0E40` (step offset `35.2`, then
`28.8 + 35.2 = 64.0`), `0x006F0F20` (layout search), and `0x006F0FD0` (item
draw). Its live layout tables hold the keys that are zero in NUN3's file copy:

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
NA2's 512-unit HUD space, which matches each base plus `67.4`; the routine that
reads these values was not traced. Frame scale comes from the frame draw at
`0x006F0C80`, which reads the position-indexed scale table. Frames are drawn at
the layout points. Items are drawn at the step offset, with
their height interpolated from the layout by `x`. The visible ranges place the
extra item on the positive-`x` side when the count is even, and a NUN4 battle
screenshot shows the first badge as L2 on the left and the second as R2 on the
right for both players. By user observation, Item Select in NUN4 and in retail
NUN5 moves P1's selection to the item on the left, so the positive-`x` side
holds earlier items. The badge objects are built at `0x006EEA08` and
`0x006EEA48` from the side-indexed badge tables. Each is one button sprite with
no separate frame. The HUD draw at `0x006F08B0` draws both badges through
`0x006F2630`, which passes opacity `0.2` to the sprite draw while panel `+0x40`
is below `2` and `1.0` otherwise, with the press scale at badge `+0x30`. The
sprite draw `0x003AC890` has the same argument layout as NA2's `0x00377750`.

The retail item-step routine `D/L 006F0E00/006F0E40` returns signed offsets
`0`, `35.2`, and `28.8 + 35.2 = 64` for steps `0`, `1`, and `2`.
Item draw `D/L 006F0F90/006F0FD0` adds that offset to the slot's current
horizontal displacement and interpolates its height between the neighboring
layout records. Its tail at `D 0x006F10D8..0x006F127C` computes `d = |x|`,
scale `1.2 - 0.6 * d / 96`, and count-dependent opacity. Opacity is `1`
inside the inner boundary, `0` beyond the outer boundary, and
`1 - (d - inner) / (outer - inner)` between them. Negative `x` uses the
first two range-table values (absolute outer, inner); positive `x` uses the
last two (inner, outer). For five items this gives negative-side boundaries
`45..75` and positive-side boundaries `47..75`, making the items at distance
`64` partially transparent even at rest. An unusable-item marker receives
`0.8 * opacity`, and the item sprite receives the full opacity through
wrappers `L 0x006F27A0` and `L 0x006F2770` respectively.
