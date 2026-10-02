# Battle Command List and move chart

This document records how retail NA2 (`SLPS-25837`) draws the battle Command
List and the character move chart: how configured bindings become icon
tokens, how rows are built from the command table and the fighter's action
arrays, which texture or text each token uses, and the native category and
input-condition labels.

Address conventions follow
[Retail game file identities](../../../game/files/file_identities.md#address-conventions).
Addresses below are live; a preserved export label (`FUN_...`) is the live
address minus `0x40`.

## Research coverage

- **Assigned scope:** the battle Command List and character move chart
  presentation: binding-to-icon conversion, row construction, token
  renderers, and the native category and input-condition text they draw.
- **Exploration depth:** read the Command List builder and renderer, the
  move-chart row builder, binding converter and renderer, the other resident
  and BTL binding-presentation readers, the command table, the sprite records,
  and both text pointer tables.
- **Confirmed coverage:** token values and binding mappings; row layouts and
  counts; the texture layer or text table selected for each token range; the
  move chart's row filter and its command-token derivation from action
  records; and the native labels listed below.
- **Unresolved or untested:** full chart sequences for every named action;
  whether the rear-direction label corresponds to every object-relative
  direction selector in the input interpreter; the visible result was not
  captured.
- **Deliberate exclusions and overlap:** [Action commands](../../../gameplay/combat/action_commands.md)
  owns bindings, logical input, action records and selection;
  [Battle UI selectors and prompts](selectors_and_prompts.md#command-menu-and-command-chart-scroll-indicators)
  owns the shared scroll indicators drawn by the same renderer.
- **Evidence limitations:** static code and data. The chart's display scan is
  not the action-state validator, so a shown row does not establish that the
  action is currently executable.

## Binding presentation readers

Battle input tests each configured binding as a full 16-bit mask
([Action commands](../../../gameplay/combat/action_commands.md#native-pad-domain-and-battle-bindings)).
The presentation readers instead map bindings to fixed button sets:

| Reader | Mapping |
| --- | --- |
| resident `FUN_0020ce10` | one binding to a prompt index for the eight face and shoulder masks; any other value returns `0x1E` |
| resident `FUN_00387950` | Options Controls row reconstruction from the eight masks at `0x005D5230` |
| BTL `0x00796990`, `0x007FDD00`, `0x00804D40`, `0x0071CB30` | binding glyphs resolved through BTL `0x006B4110` |
| BTL `0x00877FB0` | Command List builder; see [Command List rows](#command-list-rows) |
| BTL `0x008793A0` | move-chart binding converter; see [Binding icons](#binding-icons-and-direction-tokens) |

## Command List rows

The battle Command List's builder is BTL `0x00877FB0`. It maps the side's
eight configured bindings to icon tokens: Circle `4`, Triangle `5`, Square
`6`, Cross `7`, L1 `9`, R1 `10`, L2 `11`, R2 `12`. Any other mask, including
zero, leaves its stack slot unassigned. It then fills 18 rows of stride `0x34`
from the command table at `0x008D1550` (16-byte entries: name pointer, up to
five halfword tokens, `-1` ending the list), writing tokens at row `+0x08`
and their count at row `+0x30`, and finally stores 18 at list `+0x2C`
(`0x008784F4`). Table tokens below 26 are copied; 27 through 32 select
bindings 1 through 6 (default Circle, Cross, Square, L1, R1 and L2). For
bindings 3 and 6, an L2 or L1 token expands to L2 `+` R2 or L1 `+` R1. The
guard row and the substitution row's button both use token 31.

The renderer, `0x00878860` (`FUN_00878820`), draws tokens 0 through 3
(d-pad directions) and 4 through 8 (face buttons and plus) from texture layer
0, `TEX_xcommand`; 13 through 25 as text through the pointer table at
`0x008BD510`; and 9 through 12 from texture layer 1, `TEX_xcommand02`, using
the 8-byte records at `0x008D14C0`, whose width advances the next token. Its
checks are `slti 13` and `slti 26` for text at `0x00878AD0` and `0x00878ADC`,
and `slti 13` for the shoulder branch at `0x00878AF4`. The shoulder branch
loads the record base at `0x00878C1C` and the width base at `0x00878C40`, and
draws at `0x00878C38`; the text branch loads its table base once at
`0x00878C70`. It draws list `+0x30` rows from the scroll position at list
`+0x2E`, wrapping at the row count in list `+0x2C`, and passes `+0x2E` and
`+0x2C` to the scroll bar.

Its input-condition text tokens include token 13 `（ジャンプ中）` at
`0x008BD230`, token 15 `後側方向キー` at `0x008BD280`, token 20
`（しばらく押す）` at `0x008BD400`, and token 21 `（地上で）` at
`0x008BD420`: while jumping, rear-direction key, hold for a while, and on the
ground. Text tokens 16 and 23 are the substitution condition,
「（相手の攻撃の当たる瞬間）」 with ruby, and the Linked Attack condition,
「（マニュアル：出現後もう一度押すと攻撃）」 with ruby; row 8's name,
「変わり身の術（チャクラ消費）」, includes the chakra suffix.

## Character move chart

The character move chart derives its rows from the fighter's current action
arrays rather than the two static `ccCommand` sequences.

### Row construction

The row builder is BTL `0x008794B0` (`FUN_00879470`). It walks indices below
fighter `+0xA38` and resolves each through resident `FUN_00217930` (`+0xA54`)
and `FUN_00217990` (`+0xA58`). A zero category or category bits in `0xF002`
omit the row. Nonempty record display strings at `+0x08` become visible
names; empty names accumulate command tokens for later named continuation
entries. Record byte `+0x19` controls that command prefix handling.

Generated rows have stride `0x34`, starting at chart object `+0x40`:

| Row field | Display use |
| ---: | --- |
| `+0x00` | action-name pointer |
| `+0x04/+0x05` | condition/category text indices |
| `+0x08..+0x2C` | ten command-icon token slots |
| `+0x30` | last token index; renderer examines this value plus one tokens |

### Binding icons and direction tokens

Binding converter `0x008793A0` (`FUN_00879360`) reads the first four
configured bindings through resident `FUN_001f3f10` and stores their tokens
at object `+0x20..+0x2C`. Native masks `0x10/0x20/0x40/0x80`
(Triangle/Circle/Cross/Square) become tokens `5/4/7/6`; any other mask stores
token 0, the up d-pad. A configured binding change therefore also changes the
chart's button icon.

For ordinary records the chart emits direction token 0 for signature bit
`0x200`, token 1 for `0x400`, a side-dependent token 2/3 for any bit in
`0x5000`, and the opposite token for any bit in `0xA000`, in that priority
order. It inserts separator token 8 after a direction. Signature family
`0x00100000` appends binding 1's icon; otherwise `0x01000000` appends
binding 2's. In the rapid-press/charge branch, category bit `0x4` takes
priority over `0x10`; either appends another binding-1 icon and selects its
label, with airborne variants when signature bit 4 is set. The chart thus
interprets record fields for presentation; it is not a literal dump of the
hold/release sequencer's logical bits.

The chart renderer, `0x0087A740` (`FUN_0087a700`), draws every token with its
layer-0 sprite, `TEX_xcommand`, using the eight-byte sprite records at
`0x008D14C0`: tokens below 4 at the row's icon line and the rest 4 units
lower, through the record base at `0x0087AA44` and the draw at `0x0087AA68`.
Shoulder tokens 9 through 12 would therefore sample d-pad texels there.

### Category text

The category-text pointer table is at `0x008BD1D0`. Relevant native labels,
with reading markup omitted, are:

| Index | String | Native label | Meaning |
| ---: | ---: | --- | --- |
| 9 | `0x008BCF90` | `連打技` | rapid-press technique |
| 10 | `0x008BCFB0` | `溜め技` | charge technique |
| 11 | `0x008BCFD0` | `空中連打技` | airborne rapid-press technique |
| 12 | `0x008BD000` | `空中溜め技` | airborne charge technique |

The input-condition wording listed under [Command List rows](#command-list-rows)
is drawn by the related generic renderer `0x00878860`. It does not connect the
rear-direction label to every object-relative direction selector in the input
interpreter.
