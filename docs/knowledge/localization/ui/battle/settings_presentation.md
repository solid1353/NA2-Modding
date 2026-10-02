# Battle and Practice settings presentation

Addresses below use the
[Game binary address conventions](../../../game/files/file_identities.md#address-conventions).
"Ghidra" addresses are preserved-export addresses.

## Research coverage

- **Assigned scope:** Native Battle and Practice Settings geometry, prompt
  placement, content viewports, and render resources in retail NA2
  (`SLPS-25837`), with NUN5 comparisons where noted.
- **Exploration depth:** The relevant NA2 and NUN5 draw paths, helpers,
  constructors, animation updates, model and part records, `PRAC.CCS` and
  `SETTING.CCS` resources, and live objects were inspected.
- **Confirmed coverage:** Practice content scrolling and clipping, text context,
  row windows, backing animation records, title model and atlas regions,
  vertex-color stream submission, resource construction, cursor, arrows, and
  VS prompt; Battle row and Handicap geometry, resources, and cursor; and both
  screens' footer legends.
- **Unresolved or untested:** The complete menu lifecycle and every animation
  phase were not exhaustively investigated.
- **Deliberate exclusions and overlap:** Setting storage, input, child state,
  resource lifetime, and gameplay effects belong to
  [Practice mode](../../../gameplay/practice_mode.md); localized Practice text
  layout belongs to
  [Practice screen layout](../../font/screen_layouts/practice.md); the shared
  2D draw owners belong to
  [2D draw owners](../../../runtime/draw_2d_owners.md).
- **Evidence limitations:** Runtime observations confirm the identified fields
  and layout effects but do not cover every original menu configuration.

## Practice content and contexts

Practice's content block runs from live `0x00882358` through the helper call
ending at `0x00882504`. It uses controller `+0x10` for backing/content and
`+0x14` for foreground text and arrow sprites. Both contexts have the viewport
`(0,70,512,210)`, initialized by resident `0x0037DAA0`. Their priorities are
`0xE8` and `0xE9`, respectively. The constructor portion containing this setup
lies in an undefined export gap at Ghidra `0x00880BD8..0x00880D64`.

The font renderer pointer is at `0x00607470`. Its context is a separate field
at `+0x6C`, assigned by `0x001866D0`; changing the global animation draw context
alone does not change text's viewport. Ghidra `0x00882238..0x00882244` binds
Practice's foreground context before drawing. Using the backing context for
text places it beneath the backing layer.

Controller `+0x44` is the scrolling displacement. The backing parent translates
by `-0.96 * scroll`; the text loop begins at `14 + scroll`, advances rows by
`28`, and inserts an `18`-unit section gap plus a heading row. Thus the section
heading moves with the content and is clipped by the viewport.

Rows `0..8` form the upper window and rows `9..16` the lower window. The
controller update maintains their window starts and eases `+0x44` toward
`-28 * upper_start` or `-270 - 28 * lower_start` (the `18`-unit gap plus nine
`28`-unit rows) by at most `20.0` per update; the window helper calls and
easing are owned by
[Practice mode](../../../gameplay/practice_mode.md#input-and-child-state-transitions).

### Backing animation and title

The backing is the `ANM_prac_cel` animation object at controller `+0x2C`. Its
18 animation records are reached through `object+0xFC`, and resident
`FUN_001BB790` draws a record only when `record+0x0A & 0x04` is nonzero. Record
`0` targets `OBJ_prac_title`, whose internal object links to `MDL_prac_title`;
it is the visible Practice Settings title. The nine player-row cells use record
`1` and records `10..17`; the eight opponent-row cells use records `2..9`. Each
record points to a render object at `+0x00`, which stores world Y at `+0x38`
and authored local Y at `+0x78`. The title therefore has its own record-level
draw boundary, separate from every row cell, and the backing's title-and-cells
structure is fixed independently of the text windows.

Live `0x00881AE0` advances the backing through resident `0x001BB210`, and live
`0x00881AEC` immediately composes its hierarchy through resident `0x001BB6F0`,
before the draw path runs.

`MDL_prac_title` has one rigid 28-vertex mesh. Its authored bounds, after the
model's `1/16` coordinate scale, are X `-179.9375..4.25` and vertical
`-13.5..13.5625`, for a `184.1875` by `27.0625` local-unit footprint.

The separate draw call for child `+0x18` uses rectangle `(1,1,126,30)` from
`TEX_prac_t01`. That region contains panel and arrow imagery, not the Practice
Settings title.

### Model colors and atlas regions

Resident `FUN_00190F40` draws the type-`0x0100` model at object `+0x94`. The
model stores its part count at `+0x16` and a pointer to `0x40`-byte part
records at `+0x08`. Each part record stores its vertex count at `+0x04`, its
vertex-color stream pointer at `+0x1C`, and its UV stream pointer at `+0x20`.
Resident `FUN_00198230` copies those fields into render scratch state before
`FUN_00193B50` emits the four-byte-per-vertex color stream. `FUN_00198230`
copies the color-stream pointer, not the colors, into render scratch at
`+0x238`, and `FUN_00193B50` emits DMA references to that source stream in
batches of up to 48 vertices, so a submitted draw reads the source colors when
the DMA transfer consumes them.

In retail NA2 `PRAC.CCS`, `MDL_prac_cel_a1`, `MDL_prac_cel_b1`, and
`MDL_prac_title` share `MAT_char_prac` and neutral `0x80808080` vertex colors.
Their yellow, olive, and orange appearances come from distinct `prac_t01`
atlas regions: the first 18 row vertices use U coordinates `0/32/74` for player
cells and `76/108/150` for opponent cells, while the title uses
`162/206/246/254`. Vertices `0..17` form the label panel; vertices `18..61`
form the divider and value panel. Retail NA2 `SETTING.CCS` uses the same
62-vertex player-row geometry with a separate `s_menu` atlas, which contains
the yellow row but no orange title or olive row region. The dominant opaque
fill is RGBA `(230,195,43,255)` in both NA2 and NUN5 `prac_t01`; the orange
title fill is `(245,134,32,255)` in both.

### Resource construction

The Practice child constructor at Ghidra `0x00880BA0` calls resident
`0x0037E1A0` at `0x00880BC0` with `prac.ccs`, stores the returned archive at
child `+0x04`, and gives the child's leading byte to the loader as its ownership
flag. Live `0x00880D70` creates the backing at child `+0x2C` by passing that
archive and `ANM_prac_cel` to resident `0x0037D5B0`. The resident constructor
allocates `0x120` bytes and performs an initial animation update and hierarchy
composition when records exist. Native destruction releases animation objects
through `0x001B7570` and releases an owned archive through `0x001A9790`.

## Cursor and arrows

The native resource bindings, confirmed by the constructor's GP-relative
references and live strings, are `ANM_prac_cel` at controller `+0x2C`,
`ANM_carsol01_a` at `+0x30`, and `ANM_prac_ca` at `+0x28`.
`ANM_prac_ca` is the camera animation, not the selection cursor.
The cursor update calls `0x001BB210` with its halfword at `+0x94`, then
`0x001BB6F0` to compose it before the draw helper applies its row translation.

Live `0x00882168` constructs float `0.939` and applies it to the cursor's
scroll component. Native cursor Y is `94 - 26.5 * row - 0.939 * scroll`, with
another `-40` after the fixed nine-row player section.

Practice's green arrow rectangle at live `0x008D1910` is `(52,69,15,14)`;
Battle's at `0x008D18A0` is `(81,61,18,18)`. Practice uses horizontal radius
`64 + 3*sin(pi*phase)` around X `356`; Battle uses `60 + 3*sin(pi*phase)`.
Practice's orange arrows share rectangle `0x008D1920` and local Y positions
`14 - 5*sin(pi*phase)` and `196 + 5*sin(pi*phase)`. Live `0x00882078` skips
the up-arrow body at `0x00882080` when the window-start flag is zero.

## Footer legends

| Role | Retail NA2 | NUN5 |
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
common compositor call. NA2 has no equivalent additions.

The similarly shaped VS confirmation prompt is a different call site at NA2
BTL file `0xCF70`; it does not belong to either Settings footer.

## Battle rows and Handicap

NA2 BTL `FUN_008801A0` spans file `0x1CC2E0..0x1CC7F7`, Ghidra
`0x008801A0..0x008806B7`, and live `0x008801E0..0x008806F7`. Its label loop
uses six native slots at `Y = 79 + 28 * slot`. The value loop treats slot `5`
as Handicap. Ghidra `0x0088031C` loads its value; file `0x1CC49C` / Ghidra
`0x0088035C` and file `0x1CC514` / Ghidra `0x008803D4` independently supply
fixed `Y = 257` to the red and blue value paths. Within this range, the
Handicap renderer branch is at live `0x00880350` (file `0x1CC450`), the
Handicap arrow branch at live `0x008805C8` (file `0x1CC6C8`), and the Handicap
cursor branch at live `0x008806D0` (file `0x1CC7D0`); the Battle Settings draw
calls the backing at live `0x008808AC` (file `0x1CC9AC`).

The native backing contains five ordinary row strips followed by the
double-height Handicap panel. The cursor and arrows derive their Y positions
from the selected slot, but the Handicap values and backing remain at the fixed
sixth position.

The Handicap value is a ten-segment graphic rather than text. The first loop
draws the selected Player 1 count with rectangle `0x008D18B0`
`(33,61,23,23)`; the second fills the remaining segments with rectangle
`0x008D18B8` `(57,61,23,23)`. Both call resident `0x0037BD00(x, y, scale_x,
scale_y, sprite, rectangle)` at `X = 128 + 28 * segment`, scale `0.9`, and
`Y = 257`, which is 38 below the Handicap label's `Y = 219`. The selected value
therefore controls the red-to-blue boundary while the total always remains ten
segments.

The Battle Settings constructor, Ghidra `FUN_0087F690`, uses the `setting.ccs`
archive at controller `+0x00`. It creates the value sprite at `+0x08` from
`TEX_s_menu` through resident `0x0037B670`, with capacity `0x14`, enabled flag
`1`, and the controller's `+0x14` render context. Through resident
`0x0037D5B0` it creates `ANM_setting01` at `+0x20`, `ANM_setting_ca` at
`+0x24`, `ANM_carsol01_a` at `+0x28`, and `ANM_carsol02_a` at `+0x2C`. The
Handicap loops pass the `+0x08` sprite to `0x0037BD00`. Practice's controller
`+0x08` is a different object.

`ANM_setting01` is the row backing: record `0` is the double-height Handicap
panel and records `1..5` are the ordinary strips for slots `0..4`. A composed
instance's objects carry their vertical translation at local `+0x78`: `0.0`
for the panel and `99.03`, `72.42`, `45.80`, `19.18`, and `-7.43` for records
`1..5`. The panel's geometry is therefore modeled `34.04` above the translation
a sixth ordinary strip would have. The animation's root matrix keeps its vertical
translation at `+0x78`; object `+0x38` held `0.0` for these records rather than
a composed position. The cursor
draw, Ghidra `FUN_008804B0`, places either cursor at
`Y = 100 - 26.5 * slot`. It uses `ANM_carsol02_a`, which frames only the label,
when slot `5` is selected, and `ANM_carsol01_a` otherwise. It draws no value
arrows for slot `5`.

The ordinary value loop retains row Y in `$f20`. Ghidra `0x00880434..0x00880448`
resolves the row's string, and `0x0088044C` copies `$f20` to `$f13` immediately
before drawing. The loop increments `$f20` by `28.0` after each row.

## VS Practice Settings prompt

NA2 `FUN_006C0CC0` uses rectangle `(1,281,112,22)` at BTL file `0x20C9D8`
and X=`60.0` at file `0xCFA0`. NUN5 `FUN_006D4170` selects its English
rectangle `(0,280,176,24)` through a localized table and passes X=`100.0`;
that rectangle places the English label and Square icon as a `176 x 24` sprite
at UV `(0,280)`.
