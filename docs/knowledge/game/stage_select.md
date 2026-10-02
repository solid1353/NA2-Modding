# Native Stage Select

This document records the native Stage Select screen of retail NA2
(`SLPS-25837`): its selection object, choice list, per-stage records, preview
and name resources, browsing, Random, and the result it hands to battle setup.

## Research coverage

- **Assigned scope:** the BTL Stage Select object built by resident outer
  state 9: construction, choice-list construction, preselection, input states,
  browsing, Random, carousel and selected-stage drawing, stage records,
  `MAPSEL1.CCS` preview and name resources, destruction, and every fixed
  stage-count assumption in that code.
- **Exploration depth:** every function in live BTL `0x00713A50..0x00715EC0`
  was read instruction by instruction, together with the 24-row record table,
  the eight-entry state table, the resident caller, the resident fallback-name
  table, and the decoded `MAPSEL1.CCS` preview textures.
- **Confirmed coverage:** the object fields used by Stage Select, the choice
  list and its capacity, the per-slot TV objects, record lookup, both preview
  cell layouts and their texture capacity, the name sprite, the fallback path,
  the counters, browsing and Random bounds, the state machine, and the
  confirmation handoff.
- **Unresolved or untested:** the button identities of the input bits, the
  meaning of the two input records selected by `+0x04`, the content of the
  unused big-preview cells, and the visual effect of the per-entry draw
  parameter in the carousel. No runtime observation was made.
- **Deliberate exclusions and overlap:** the slot bitset and its initializer
  belong to [Content availability](content_availability.md#resident-stage-slot-availability);
  writes of the confirmed slot to the battle manager, the logical-ID mapper,
  and stage loading belong to
  [Stages](../gameplay/stages/stages.md#stage-identity-and-resource-mapping);
  the settings parent at `+0xA8` and the outer-state lifetime belong to
  [Practice mode](../gameplay/modes/practice_mode.md); NA2/NUN5 layout and
  localization differences belong to
  [Stage Select UI](../localization/ui/stage_select.md).
- **Evidence limitations:** static evidence from retail `BTL.BIN`, the resident
  ELF, and retail `DATA.CVM` `MAPSEL1.CCS`. Ghidra defines no functions over
  several of these BTL ranges, including the constructor at live `0x00713A50`,
  so the instruction bytes of the retail file were disassembled directly.
  Direct-reference inventories cover this code range, not every indirect caller.

## Binary identity and address conventions

Addresses are live BTL addresses unless stated. BTL file offsets are
`live - 0x006B3F00`; preserved Ghidra addresses are `live - 0x40`. Identities
and conversions follow
[Retail game file identities](files/file_identities.md#address-conventions).

## Lifetime

Resident outer state 9, `FUN_001ED6D0`, allocates the `0x16C`-byte object
with `FUN_00117150(0x16c)`, calls the clearing constructor live `0x00713A50`
and the initializer live `0x00713DC0`, then calls the setter live
`0x007147C0`. Each invocation calls update live `0x00715830` and, while the
result is neither `1` nor `-1`, draw live `0x00715CC0`. On `1` it stores the
getter's result at manager `+0x98`; on either result it calls destructor live
`0x00713B20` and frees the object. The surrounding outer states are described
in [Practice mode](../gameplay/modes/practice_mode.md#resident-scheduling-and-controller-lifetime).

## Object fields

| Offset | Contents |
| ---: | --- |
| `+0x00` | state, `0..7` |
| `+0x04` | input source: `0` first record, `1` second record, `2` both ORed |
| `+0x08` | reinitialization request; nonzero makes update call live `0x00714700` |
| `+0x0C` | preselected slot passed to the initializer; negative means none |
| `+0x10` | choice count |
| `+0x14..+0x73` | choice array, 24 words, each a raw load slot |
| `+0x74` | current choice index |
| `+0x78` | float carousel displacement |
| `+0x80` | fade handle |
| `+0x84` / `+0x88` | final result and its countdown |
| `+0x8C` / `+0x90` / `+0x94` | Random tick counter, capped update counter, float Random phase |
| `+0x9C` / `+0xA0` / `+0xA4` | input words copied each update |
| `+0xA8` | `0x54`-byte settings parent |
| `+0xAC` | `mapsel1` container |
| `+0xB0..+0xDC` | draw lists, sprites, and animation objects |
| `+0xE0` / `+0xE4` | `CMP_titlebox` and `CMP_sirinder1` objects |
| `+0xE8..+0x147` | 24 TV objects, indexed by raw slot |
| `+0x148` | `MDL_circle0` node of the big preview |
| `+0x14C..+0x158` | `TEX_mappure01..04` |
| `+0x15C`, `+0x160..+0x168` | arrow animations and their trigger bytes |

The constructor clears the TV array with a 24-iteration loop:

```text
0x00713A94  sll   v1,a1,0x2
0x00713A9C  sw    zero,232(v1)
0x00713AA8  slti  v1,a1,24
```

The initializer at `0x00713DC0` stores the preselected slot at `+0x0C`,
chooses `+0x04` from manager `+0x1C` (`5` or `2` select `1`, `4` or `1` select
`0`, others `2`), builds the choice list, calls the setter with manager
snapshot byte `+0x114`, loads resources through live `0x00713ED0`, and calls
the reinitializer at `0x00714700`.

## Choice list

Live `0x00714460` clears the count and appends every slot `0..23` that resident
`FUN_001F58B0` admits, in ascending order:

```text
0x00714490  lw    a0,0x10(s1)
0x0071449C  sll   v1,a0,0x2
0x007144A4  sw    s0,0x14(v1)
0x007144B0  slti  v1,s0,0x18
```

The array therefore holds exactly 24 words and is followed directly by the
current index at `+0x74`. A 25th append would overwrite the index.

The setter `0x007147C0` clears `+0x74` and `+0x78`, then scans entries
`0..count-1` for the requested slot and stores its index; an absent slot leaves
index 0. The getter `0x00714810` returns `choices[+0x74]`. The on-screen order
is the array order.

## Stage records

The record table holds 24 sixteen-byte rows at live `0x008C3B10`, file
`0x20FC10`:

| Offset | Field |
| ---: | --- |
| `+0x00` | `int32` logical stage ID |
| `+0x04` | `int32` preview index |
| `+0x08..+0x0E` | `int16` `u`, `v`, `w`, `h` of the name in `TEX_mapname01` |

Retail rows are in load-slot order: row `n` has the logical ID of slot `n`
and preview index `n`. The eight-word state table at `0x008C3C90` follows the
last row immediately.

Three routines find a row with the same 24-row loop: `0x007143D0(object, slot)`,
and the inline loops in `0x00714520` and `0x007151D0`. Each compares row word 0
with the logical-ID mapper live `0x006C14E0(slot)`:

```text
0x00714404  lw    s2,0(v0)        ; row logical ID
0x0071440C  jal   0x006C14E0
0x00714414  bne   s2,v0,...
0x00714430  slti  v0,s0,24
```

A slot with no matching row returns `-1`; the two preview builders then use
row 0, and the selected-stage draw takes the fallback below.

## Preview images

Both preview paths read the record's preview index `p`.

**TV objects.** Live `0x007141C0` creates, for every slot `0..23`, a
`0xA0`-byte object from `CMP_sirinder_tv` and `MDL_sirinder_tv` and stores it
at `+0xE8 + 4 * slot` (`0x00714398 sw s1,232(v1)`, loop bound
`0x007143A0 slti v1,s3,24`). It converts the cell origin
`u = (p % 5) * 96`, `v = (p / 5) * 72 + 96` through `0x0037DA40` with a
512×512 size and passes it to the model through `0x00198840`.

**Inference (high confidence):** the TV cells are 96×72 cells of
`TEX_mappure04`. The code does not name the texture, but that texture's image
data fills exactly a 5×5 grid of 96×72 cells at `v = 96..455`. Its cells 0–23
contain images and cell 24 contains a single color.

**Big preview.** The refresh at `0x00714520` binds `TEX_mappure0(1 + p / 9)` to
the `MDL_circle0` node and offsets its UV to a 168×168 cell at
`u = (q % 3) * 168`, `v = (q / 3) * 168`, where `q = p % 9`. Four textures
give 36 indices; indices 0–23 are the retail previews, indices 24–26 are the
remaining cells of `TEX_mappure03` and contain image data, and indices 27–35
fall in `TEX_mappure04`, the TV atlas.

The four preview textures are 512×512 indexed images stored bottom-up: the
TV grid's `v = 96..455` occupies stored rows `56..415`.

## Stage name and counters

The selected-stage draw `0x007151D0` draws the name sprite built from
`TEX_mapname01` (`+0xBC`) with the matched row's rectangle at `(380, 298)`:

```text
0x00715478  addiu a1,v1,8         ; &row.u
0x00715480  jal   0x0037BD00
```

When no row matches, it instead draws a `(20,340,200,40)` box with color
`0x7F000000` and text from the resident table at `0x005C04C0`, indexed by the
choice's raw slot. That table holds 24 pointers to Shift-JIS stage names;
the following word, `0x005C0520`, is zero.

It also draws two two-digit counters through `0x00715630`: the current index
plus one at `(192, 270)` and the choice count at `(218, 288)`.

## Carousel

The carousel draw `0x00714D40` visits offsets `-3..3` around `+0x74`, wraps
each index into `0..count-1`, and draws the TV object of the slot stored at
that index:

```text
0x00715008  lw    v0,20(v0)       ; choices[index]
0x0071500C  sll   v0,v0,0x2
0x00715014  lw    s1,232(v0)      ; tv[slot]
```

Each offset is placed on a ring at `0.62832` radians per step plus the
displacement `+0x78` and, in state 3, the Random phase `+0x94`.

## States and input

Update `0x00715830` copies three input words to `+0x9C/+0xA0/+0xA4` according
to `+0x04` and dispatches `+0x00` through the table at `0x008C3C90`:

| State | Handler | Behavior |
| ---: | --- | --- |
| 0 | `0x00715A98` | stores to address zero |
| 1 | `0x00715944` | waits for the fade, then state 2 |
| 2 | `0x0071596C` | browsing, `0x00714830` |
| 3 | `0x00715980` | Random, `0x00714AD0` |
| 4 | `0x007159C8` | settings parent `+0xA8`; its `1` gives result `1` |
| 5 | `0x00715A00` | cancel: result `-1` after the fade unless `+0x0C >= 0` |
| 6 | `0x00715994` | confirm: after the fade, state 4 |
| 7 | `0x00715A6C` | returns the result when the countdown ends |

The reinitializer `0x00714700` enters state 4 directly when `+0x0C >= 0` and
otherwise starts a fade and enters state 1. A `-1` from the settings parent
with no preselection reinitializes Stage Select instead of cancelling.

**Browsing** (`0x00714830`): `+0x9C` bit `0x20` confirms (state 6), `0x40`
cancels (state 5), and `0x10` enters Random when the count is at least 2.
`+0xA4` bit `0x4000` adds one to the index while the displacement is at most
`0.1`; `0x1000` subtracts one while it is at least `-0.1`. The index then wraps
by the count:

```text
0x00714A88  lw    v1,16(s0)
0x00714A8C  addu  v1,a1,v1        ; negative index + count
0x00714AAC  subu  v1,a1,a0        ; index - count
```

**Random** (`0x00714AD0`): every second update it draws resident
`0x00180210(count - 1)` until the result differs from the current index and
stores it. `0x20` confirms the current entry; `0x40` or `0x10` returns to
browsing.

Choice-list size enters these paths only through the count at `+0x10`.

## Destruction

The destructor `0x00713B20` releases the sprites, animation objects, both
clumps, all 24 TV objects (`0x00713D00 slti v1,s0,24`), the arrow
animations, and the settings parent.

## Fixed stage-count limits

| Limit | Location |
| --- | --- |
| Choice array of 24 words before `+0x74` | `0x00714460`, object `+0x14..+0x73` |
| Slot scan `0..23` | `0x007144B0` |
| TV objects for slots `0..23` at `+0xE8 + 4 * slot`; slot 24 would address `+0x148` | `0x00713A50`, `0x007141C0`, `0x00713B20`, `0x00715014` |
| 24 records followed by the state table | `0x008C3B10..0x008C3C8F` |
| 24-row record searches | `0x007143D0`, `0x00714520`, `0x007151D0` |
| 24 fallback names | resident `0x005C04C0` |
| 25 TV cells and 36 big-preview indices | `TEX_mappure01..04` |
