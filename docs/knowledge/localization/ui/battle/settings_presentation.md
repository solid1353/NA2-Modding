# Battle and Practice settings presentation

Addresses below use the
[Game binary address conventions](../../../game/files/file_identities.md).

## Research coverage

- **Assigned scope:** Native Battle and Practice Settings geometry, prompt placement,
  content viewports, and render resources.
- **Exploration depth:** The relevant NA2 and NUN5 draw paths, helpers,
  constructors, animation updates, and live objects were inspected; the Battle
  row layout was also checked with a reduced visible row set.
- **Confirmed coverage:** Practice content scrolling and clipping, text context,
  backing, cursor, arrows, and VS prompt; Battle row and Handicap geometry; and
  both screens' footer legends.
- **Unresolved or untested:** The complete menu lifecycle and every animation
  phase were not exhaustively investigated.
- **Deliberate exclusions and overlap:** Setting storage, input, and gameplay
  effects are outside this document.
- **Evidence limitations:** Runtime observations confirm the identified fields
  and layout effects but do not cover every original menu configuration.

## Practice content and contexts

Practice's content block runs from live `0x00882358` through the helper call
ending at `0x00882504`. It uses controller `+0x10` for backing/content and
`+0x14` for foreground text and arrow sprites. Both contexts have the viewport
`(0,70,512,210)`, initialized by resident `0x0037DAA0`. Their priorities are
`0xE8` and `0xE9`, respectively. The constructor portion containing this setup
is not exposed as a function by GhidrAssist; its raw bytes at Ghidra
`0x00880BD8..0x00880D64` supply that gap.

The font renderer pointer is at `0x00607470`. Its context is a separate field
at `+0x6C`, assigned by `0x001866D0`; changing the global animation draw context
alone does not change text's viewport. Ghidra `0x00882238..0x00882244` binds
Practice's foreground context before drawing. Using the backing context for
text places it beneath the backing layer.

Controller `+0x44` is the scrolling displacement. The backing parent translates
by `-0.96 * scroll`; the text loop begins at `14 + scroll`, advances rows by
`28`, and inserts an `18`-unit section gap plus a heading row. Thus the section
heading moves with the content and is clipped by the viewport.

## Cursor and arrows

The native resource bindings, confirmed by the constructor's GP-relative
references and live strings, are `ANM_prac_cel` at controller `+0x2C`,
`ANM_carsol01_a` at `+0x30`, and `ANM_prac_ca` at `+0x28`.
`ANM_prac_ca` is the camera animation, not the selection cursor.
The cursor update calls `0x001BB210` with its halfword at `+0x94`, then
`0x001BB6F0` to compose it before the draw helper applies its row translation.

Practice's green arrow rectangle at live `0x008D1910` is `(52,69,15,14)`;
Battle's at `0x008D18A0` is `(81,61,18,18)`. Practice uses horizontal radius
`64 + 3*sin(pi*phase)` around X `356`; Battle uses `60 + 3*sin(pi*phase)`.
Practice's orange arrows share rectangle `0x008D1920` and local Y positions
`14 - 5*sin(pi*phase)` and `196 + 5*sin(pi*phase)`. Independently timed captures
can therefore differ in orange-arrow Y without a different anchor.

## Footer legends

| Role | NA2 v2.28 | NUN5 |
| --- | --- | --- |
| Battle Settings draw | file `0x1CC8E0..0x1CCAC7`, Ghidra `FUN_008807A0`, live `0x008807E0..0x008809C7` | file `0x1D65C0..0x1D67CF`, Ghidra `FUN_0089D280`, live `0x0089D2C0..0x0089D4CF` |
| Practice Settings draw | file `0x1CE390..0x1CE70F`, Ghidra `FUN_00882250`, live `0x00882290..0x0088260F` | file `0x1D8470..0x1D8703`, Ghidra `FUN_0089F130`, live `0x0089F170..0x0089F403` |
| Common OK/Back/Select compositor | `SUB_0037C980` | `SUB_0038BB10` |
| Select companion renderer | `SUB_0037BC40` | `SUB_0038AD00` |

The footer call sites use these horizontal values:

| Screen / legend | NA2 file / live | NA2 value | NUN5 effective value |
| --- | --- | ---: | ---: |
| Battle / OK | `0x1CCA04` / `0x00880904` | 400 | 388 |
| Battle / Back | `0x1CCA28` / `0x00880928` | 470 | 462 |
| Battle / Select compositor | `0x1CCA4C` / `0x0088094C` | 230 | 200 |
| Battle / Select companion | `0x1CCA70` / `0x00880970` | 230 | 200 |
| Practice / OK | `0x1CE634` / `0x00882534` | 400 | 388 |
| Practice / Back | `0x1CE658` / `0x00882558` | 470 | 462 |
| Practice / Select compositor | `0x1CE67C` / `0x0088257C` | 230 | 200 |
| Practice / Select companion | `0x1CE6A0` / `0x008825A0` | 230 | 200 |

Both NUN5 Select calls load `200` directly. NUN5 loads nominal OK and Back
values `400` and `470`, then adds regional offsets `-12` and `-8` before the
common compositor call. NA2 has no equivalent additions, so copying only the
nominal NUN5 loads does not reproduce the NUN5 placement. The settings draw
functions otherwise retain their native menu state, input, texture, object,
and animation behavior.

The similarly shaped VS confirmation prompt is a different call site at NA2
BTL file `0xCF70`; it does not belong to either Settings footer.

## Battle rows and Handicap

NA2 BTL `FUN_008801A0` spans file `0x1CC2E0..0x1CC7F7`, Ghidra
`0x008801A0..0x008806B7`, and live `0x008801E0..0x008806F7`. Its label loop
uses six native slots at `Y = 79 + 28 * slot`. The value loop treats slot `5`
as Handicap. Ghidra `0x0088031C` loads its value; file `0x1CC49C` / Ghidra
`0x0088035C` and file `0x1CC514` / Ghidra `0x008803D4` independently supply
fixed `Y = 257` to the red and blue value paths.

The native backing contains five ordinary row strips followed by the
double-height Handicap panel. The cursor and arrows derive their Y positions
from the selected slot, but the Handicap values and backing remain at the fixed
sixth position.

The ordinary value loop retains row Y in `$f20`. Ghidra `0x00880434..0x00880448`
resolves the row's string, and `0x0088044C` copies `$f20` to `$f13` immediately
before drawing. Earlier changes to `$f13` cannot affect the final value Y. The
loop increments `$f20` by `28.0` after each row. A reduced five-row runtime
observation left one blank ordinary strip and kept Handicap in the sixth native
position, confirming that removing rows does not reposition the fixed panel or
value origins.

## VS Practice Settings prompt

NA2 `FUN_006C0CC0` uses rectangle `(1,281,112,22)` at BTL file `0x20C9D8`
and X=`60.0` at file `0xCFA0`. NUN5 `FUN_006D4170` selects its English
rectangle `(0,280,176,24)` through a localized table and passes X=`100.0`.
The rectangle and anchor are structurally compatible; together they place the
English label and Square icon as a `176 x 24` sprite at UV `(0,280)`.
