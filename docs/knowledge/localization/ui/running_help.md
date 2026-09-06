# Running help

## Research coverage

- **Assigned scope:** the shared native running-help queue, text extent,
  movement, repeat behavior, spacing, and placement in clean NA2 and NUN5
  menu callers.
- **Exploration depth:** the resident enqueue, update, drawing, reset, and
  construction functions were compared through read-only GhidrAssist MCP.
  Direct menu callers were traced in the resident ELF and BTL, with raw-byte
  checks for gaps in Ghidra's existing function analysis. A supplied NUN5
  Mode Select savestate was inspected offline for queue and renderer evidence.
- **Confirmed coverage:** NA2 reserves travel distance from a character count;
  NUN5 uses measured text width and a short-string minimum. Both updates advance
  the same queue-offset field and retire nodes using the reserved extent.
- **Unresolved or untested:** numeric icon extents across callers, elapsed cycle
  timing, and runtime confirmation of all caller families. The buffered
  SPBATTLE help's exact screen ownership remains unresolved.
- **Deliberate exclusions and overlap:** this document owns retail running-help
  behavior. Mod integration belongs in feature documentation; general glyph
  metrics remain in the neighboring font knowledge documents. Only menu
  families within the project's scope are described.
- **Evidence limitations:** static code and a saved NUN5 frame establish the
  documented mechanisms and one selected string, not elapsed repeat timing
  or visual coverage of every menu.

## Shared implementation

| Responsibility | NA2 resident | NUN5 resident |
| --- | --- | --- |
| Construct | `0x0037ED00` | `0x0038DD10` |
| Reset queued text | `0x0037EEE0` | `0x0038DF00` |
| Calculate extent and enqueue | `0x0037F760` | `0x0038E790` |
| Append queue node | `0x0037F590` | `0x0038E5C0` |
| Update | `0x0037F7F0` | `0x0038E860` |
| Draw | `0x0037F900` | `0x0038E980` |

The help object contains the queue head at `+0x2C`, current displacement at
`+0x30`, speed at `+0x34`, initial hold limit at `+0x38`, and hold counter at
`+0x3A`. Each 16-byte queue node stores its text pointer at `+4`, reserved
extent at `+8`, and next pointer at `+0xC`. The horizontal viewport width is
object `+0`; byte `+0x24` selects horizontal or vertical movement.

## Extent calculation

NA2 `0x0037F760` calls `0x003798E0(text, -1)`. That wrapper selects the
character-count output of `0x001859A0`, backed by parser `0x00184E60`, rather
than its width output. If the caller supplies unit `u` and gap count `g`, the
queued extent is:

```text
L_NA2 = u * (character_count + g)
```

NUN5 `0x0038E790` selects the measurement font through `0x0018AAE0`, then
calls `0x00386090(text, 0)` to select width. Its instructions at
`0x0038E7F8..0x0038E820` establish:

```text
L_NUN5 = measured_width + u * g
if L_NUN5 < 512:
    L_NUN5 = 512 + u
```

This is a strict comparison with 512, not a general `max(width + gap, 512 + u)`.
The width parser is `0x00185DA0`, reached through `0x001869B0`. It accounts
for proportional glyph margins and ordinary-space handling. Its icon-token
branch obtains an advance from `0x00187D40`; NA2's corresponding branch in
`0x00184E60` adds an icon advance to width but does not increment the character
count selected by its help setter. Thus a character count is not an adequate
replacement for rendered extent even when visible text contains icons.

NA2 token classifier `0x00185CA0` distinguishes ordinary/fullwidth spaces,
line breaks, ruby text, raw colors, icons, named color/kerning controls, and
comments. Named controls report a prefix length excluding the closing byte;
the draw loop consumes that byte separately. Some controls also change the
global renderer during parsing. Native double-byte classifier `0x00184D90`
recognizes both the game's percent codes and its two-byte character ranges.
Icon measurement `0x00186A80` invokes the active renderer's callback at `+0x7C`
with the selector at `0x00602A3C`, so icon width belongs to the installed
callback rather than a universal character-cell width.

## How the extent affects visibility

For horizontal movement, the draw function places the first queued string at
`viewport_width - displacement`. Later strings are placed after the sum of
preceding queue extents. Each update after the initial hold increments
displacement by speed. The first node is removed when displacement reaches
`node_extent + viewport_width`; its extent is subtracted from displacement.

The append function accepts another node when the sum of current node extents
is no greater than displacement. Repeated caller submissions can therefore
queue the next copy before the first node is removed. The reserved extent
controls spacing between copies, independently of the actual drawn text width.

Consequently, a count-derived extent larger than the actual rendered width
adds empty travel. The difference can vary with a string's character count and
glyph widths. This is a code-level explanation for string-dependent spacing;
matching it to observed elapsed blank time still requires caller and runtime
evidence.

For a continuously resubmitted, unchanged horizontal string, let `W` be the
viewport width, `R` the rendered horizontal extent, `L` the reserved extent,
and `v` the distance advanced per update. Ignoring update quantization and
glyph edge bearings, the completely blank part of a steady repeat is:

```text
blank_updates = max(0, L - R - W) / v
```

This follows from the previous copy's trailing edge crossing the left clip
boundary before the next copy's leading edge enters the right boundary. An
inter-string gap is not necessarily an entirely blank viewport.

For a 512-unit viewport and measurement matching rendered extent, NUN5's
ordinary branch leaves only `u * g` between copies. Its short-string branch
gives `max(0, u - R) / v` blank updates.
The count-based NA2 calculation can instead leave a blank interval that grows
with the difference between `u * character_count` and the rendered extent.
These are derived geometric relationships, not measured wall-clock timings.

## Saved NUN5 Free Battle example

The supplied C071D4C1 Mode Select state contains help object `0x00BF83F0`,
node `0x00BF2600`, and text at `0x008F5790`:

```text
<color00FFFF>Free Battle<WHITE> allows you to use any character to fight how you like.
```

Its extent is 788, width 512, speed 2, displacement approximately 460.8,
and hold counter/limit 30/30. The renderer at `0x00B3F220`, referenced by
`0x00617B70`, retains start `(51,20)` at `+0x4BC/+0x4C0` and final pen
`(653,20)` at `+0x14/+0x18`. The 602-unit advance is independently reproduced
from the GF4 descriptor at `0x00B592D0`, its metric table at `0x00B60ED0`,
zero tracking, and eight-unit ordinary spaces.

The setter's measured width is 612 (`788 - 22 * 8`), ten units above that
advance. Parser `0x00186CC0` classifies `<WHITE>` as type 5 with length 6.
Measurement parser `0x00185DA0` skips those six bytes and then measures the
remaining `>` as a glyph; its saved margins `[2,7,2,3]` give width 10.
Draw parser `0x00189640` also skips the closing byte in its type-5 branch,
so that glyph is not drawn. Thus this retail example has a 186-unit effective
gap, not exactly 176. The whole viewport still never becomes empty under the
steady-repeat geometry above. A measured-width setter does not by itself
prove that measurement and drawing consume every markup token identically.

## Placement and spacing

The shared help draw functions set origin from displacement and the style's
local Y, but inherit the selected font and tracking. NA2 Mode Select draw
`0x00385C00` selects the secondary font through `0x00186510(...,1)` before
its help draw at `0x00385DA4`. The native secondary spacing differences are
owned by [Renderer metrics](../font/renderer_metrics.md).

Style application `0x0037F460` configures separate text and background
viewports through `0x0010E460`. Viewport fields `+0x284..+0x290` hold logical
X, Y, width, and height. The saved NUN5 text viewport at `0x00BF87A0` holds
`(0,300,512,48)`; text starts at local `(51,20)`. These are structural
positions, distinct from glyph ink bearings and accumulated word spacing.

## Initial hold and short first entries

The constructor initializes the hold limit and counter to zero. The Mode Select,
Control Settings, Sound Settings, and Options constructors set the hold limit
to 30 updates and enable byte `+0x3D`. Their constructor functions are
`0x00383F80`, `0x00387650`, `0x003890F0`, and `0x0038B140`, respectively.
Their NUN5 counterparts `0x00395580`, `0x00398E10`, `0x0039A9E0`, and
`0x0039CAF0` set the same limit and flag.

Battle and Practice likewise select style 3 and set a 30-update hold in both
games. The relevant constructor blocks are NA2 BTL `0x0087F790..0x0087F818`
and `0x00880E50..0x00880ED4`; NUN5 BTL has the matching constructor calls at
`0x0089C150` and `0x0089D9D0`. Their bytes were read through MCP because the
preserved analysis stops these constructors at the allocation call and omits
the following configuration from decompilation.

When appending the first node to an empty queue with a nonzero hold limit,
both games set displacement to `0.9 * W` and clear the hold counter. With
`+0x3D` enabled, that first node's extent is raised to `0.9 * W + 20` if
necessary. The initial text origin is therefore `0.1 * W`, already inside the
viewport. This hold is distinct from excess travel between repeated copies.
The first-node minimum also differs from NUN5's minimum in the shared setter,
which applies to every submission.

The four 36-byte native style records at NA2 `0x005B16E0` and NUN5
`0x005B87E0` are byte-identical. They all specify a 512-unit horizontal
viewport, a 48-unit height, and speed 2 units per update. This does not prove
that every caller leaves its style unchanged.

## Menu caller families

The paired setters receive the same unit and gap count in these callers:

| Caller family | NA2 function | NUN5 function | Unit | Gap count |
| --- | --- | --- | ---: | ---: |
| Mode Select | ELF `0x003854F0` | ELF `0x00396B90` | 22 | 8 |
| Control Settings update | ELF `0x003889E0` | ELF `0x0039A280` | 20 | 8 |
| Control Settings edit/reset | ELF `0x00387E10` | ELF `0x00399610` | 20 | 8 |
| Sound Settings | ELF `0x00389550` | ELF `0x0039AE40` | 20 | 8 |
| Options and embedded Controls | ELF `0x0038BBF0` | ELF `0x0039D5F0` | 20 | 8 |
| Battle Settings update | BTL `0x0087FF20` | BTL `0x0089C900` | 20 | 8 |
| Practice Settings update | BTL `0x00881AB0` | BTL `0x0089E650` | 20 | 8 |
| Ultimate Battle menu help | BTL `0x006DEC40`, `0x006DEC90` | BTL `0x006F29B0`, `0x006F2A00` | 20 | 8 |
| Ultimate Battle level/rank help | BTL `0x006E0910` | BTL `0x006F4720` | 20 | 8 |
| SPBATTLE buffered help | BTL `0x006E7F70` | BTL `0x006FC180` | 20 | 8 |
| Continue entry | ELF `0x001FBA30` | ELF `0x00202690` | 22 | 4 |

BTL function addresses in this document are Ghidra/export addresses; their
live addresses are 0x40 higher. Embedded operands already contain live
addresses. The same 0x40 distinction applies to the examined TEXTENG data.

The Ultimate Battle family is identified by NUN5 accessor `0x003D31A0`, its
English table at live `0x0091AF30`, and strings naming Ultimate Battle Series,
Epic Survival, and Customized Battle. The level/rank family uses
`0x003D3240(5..7)` and its English table at live `0x0091B2D0`. The buffered
SPBATTLE caller submits the object's text buffer at `+0x22`; no specific
screen name is inferred from the resource name alone.

Selection/value/reset branches use the same shared setter. NA2 BTL calls at
`0x0087FC60`, `0x00881734`, `0x00881850`, and `0x00881898`, omitted from
the existing function cross-references, also load unit 20 and gap count 8.
Those byte windows were checked through MCP rather than treating the missing
decompilation as missing behavior.

## Evidence coverage

GhidrAssist `xrefs` and `search_bytes` were used together. A raw `jal` byte
search found four extra help-setter calls in BTL that its existing function
analysis had not exposed as references. The constructor calls in BTL likewise
exist in bytes despite missing cross-references. Missing Ghidra references
therefore do not establish that an overlay does not use the shared component.

In the resident ELF, BTL, and ETC, direct calls to the lower-level append
function occur only inside the shared extent setter. This supports that setter
as the common owner for the direct call paths examined; it does not rule out
unresolved indirect calls. Searches for a direct tail jump to the setter and
its stored absolute pointer found no matches in these binaries. The ELF's
mirrored memory segments were not counted as additional callers.

Preserved exports were consulted only after MCP could not decompile selected
BTL constructor/reset blocks. They omit the same undefined spans, so MCP
`get_data_at` byte windows supply the missing instruction evidence instead.
