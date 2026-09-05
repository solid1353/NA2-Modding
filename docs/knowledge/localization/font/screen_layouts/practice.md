# Practice Font layouts

## Research coverage

- **Assigned scope:** compare clean NA2 and NUN5 Practice explanation and Settings text layout.
- **Exploration depth:** the relevant native callers, records, and coordinates
  were inspected.
- **Confirmed coverage:** the documented owners and cross-game geometry
  differences are established.
- **Unresolved or untested:** callers and states not explicitly covered below.
- **Deliberate exclusions and overlap:** feature hooks and behavior belong to
  [Font](../../../../features/localization/font.md).
- **Evidence limitations:** bounded states do not cover every string or
  animation phase.

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
