# Practice Font layouts

## Research coverage

- **Assigned scope:** compare clean NA2 and NUN5 Practice explanation, Settings
  text, the Jutsu display, and Practice completion plate presentation.
- **Exploration depth:** the relevant native callers, records, and coordinates
  were inspected.
- **Confirmed coverage:** the documented owners and cross-game geometry
  differences are established.
- **Unresolved or untested:** callers and states not explicitly covered below.
- **Deliberate exclusions and overlap:** feature hooks and behavior belong to
  [Font](../../../../features/localization/font.md).
- **Evidence limitations:** bounded states do not cover every string or
  animation phase. GhidrAssist exposes the completed-move renderer, but the
  Jutsu display function ends prematurely at a falsely nonreturning renderer
  initializer. Its missing tail was checked through bounded clean BTL bytes
  after MCP returned no function for the title call.

## Practice explanation mixed-text wrapping

Bounded NA2/NUN5 BTL comparison identifies the Practice explanation loop as a
separate caller family from the title draw immediately before it. NA2 reaches
the loop at BTL file `0x1C4BA0` / runtime `0x00878AA0`; NUN5 instead assembles
one bounded mixed text/tag string, installs a call-local metric/draw callback
pair for controller tokens, and passes the complete result through its wrapping
renderer.

The callback map covers all 13 Practice controller tokens. D-pad directions,
Circle, Triangle, Square, Cross, plus, L1, R1, L2, and R2 use NA2's native icon
table and draw helper. NUN5 applies token-specific Y offsets while selecting
between the caller's primary and secondary icon objects.

## Practice Settings left-column completion

Paired Practice Settings states select `Attack` and `Extra Hit Counter`.

NUN5's section-heading caller in `FUN_0089EA80` passes X `84`, width `158`,
and left alignment to `FUN_00389A80`. That helper selects the heading style
before `FUN_0018B1B0` applies shrink-only fitting through `FUN_0018CA40`.
The donor glyph advances for `Opponent Settings` total `164`, requiring
horizontal scale `158 / 164`.

## Jutsu display and Practice completion plate

The Jutsu display is a general gameplay overlay. The completed-move plate
belongs to Practice. Both are separate from Practice Settings section headings.
BTL addresses below are Ghidra addresses: add `0x40` for live code addresses.
File offsets are Ghidra address minus `0x006B3EC0` in NA2 and minus
`0x006C6CC0` in NUN5. ELF addresses are already live addresses.

The NA2 Jutsu display title block at `0x006B7D5C..0x006B7D9C` draws the string
at owner `s1 + 0x2F4` on one line. It positions X at `s2 + 4` and Y at `s0`.
The corresponding NUN5 block at `0x006CADD8..0x006CAE1C` calls the wrapped
renderer with `(s2, s0 - 11, 208, 30)`, two lines, individual horizontal
centering, and vertical centering. The registers retain the caller's animated
origin and its preceding `s2 -= 6`, `s0 += 27` adjustments.

NA2's completed-move renderer begins at `0x007282E0`. Its title block at
`0x00728468..0x007284D8` measures a single line and centers it at
`(248 + shakeX, 294 + shakeY)`. NUN5's corresponding renderer begins at
`0x0073E710` and passes `(144 + shakeX, 283 + shakeY, 208, 32)` to
`FUN_00389EA0`, again with two individually centered lines and vertical
centering. The title is read through the completed move record; it is not a
fixed Naruto string.

NUN5 `FUN_00389EA0` wraps at the box width, retries with a wider wrap when more
than two lines remain, and then shrinks to the box. `FUN_0018CAE0` fits the
20-unit secondary-font line advances vertically. `FUN_0018B1B0` centers each
line and advances it by the scaled 20 units. Glyph quads use the separate
28-unit output height, scaled by the same factor: two lines therefore use
15-unit advances / 21-unit quads in the Jutsu display and 16-unit advances /
22.4-unit quads in the completed plate. See [Renderer metrics](../renderer_metrics.md)
for the distinction between cell and output geometry.

The completed-move OK sprite uses the same shake-relative anchor `(356,303)`
and the same object scale in both games. NA2 reads `(209,1,46,62)` from ELF
`0x00604D58` and supplies rotation bits `0xBE99999A` at BTL `0x0072844C`.
NUN5's localized accessor `FUN_003D4580(0)` selects the English rectangle
`(80,0,48,64)` at ELF `0x005DDC48`; BTL `0x0073E88C` supplies rotation bits
`0x3FA2A974`. Rectangle selection and rotation both differ; moving the text
alone cannot correct this sprite.
