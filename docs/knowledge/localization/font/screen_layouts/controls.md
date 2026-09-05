# Controls Font layouts

## Research coverage

- **Assigned scope:** compare clean NA2 and NUN5 Command Chart, Pause Controls, and Special Controls text layout.
- **Exploration depth:** the relevant native callers, records, and coordinates
  were inspected.
- **Confirmed coverage:** the documented owners and cross-game geometry
  differences are established.
- **Unresolved or untested:** callers and states not explicitly covered below.
- **Deliberate exclusions and overlap:** feature hooks and behavior belong to
  [Font](../../../../features/localization/font.md).
- **Evidence limitations:** bounded states do not cover every string or
  animation phase.

Font-owned layout evidence for Command Chart relationship rows, Pause Controls, and Special Controls.

## Command Chart relationship rows

The structural NUN5 homolog is `FUN_00896E70`. Its branch at
`LAB_008977BC` resolves selector `+4` through `SUB_003D16C0`, copies the
result into a 0x100-byte stack buffer, resolves and appends selector `+5` when
present, then draws the complete buffer once through `SUB_00393ED0`. The
request passes right edge `308`, height `32`, line limit `2`, and style `9`.
`SUB_00393ED0` folds its already composed X input into that right edge before
calling the word wrapper. The sole NUN5 BTL float pair at file `0x1FAD34` is
title-local X `4` followed by relationship-local X `20`; a 16-unit container
term reaches the outer wrapper with those values, and the object contributes
the final 8 units to visible origins `28` and `44`. The word wrapper therefore
receives `308 - (16 + 4) = 288` for titles but
`308 - (16 + 20) = 272` for relationships. A runtime probe
at the exact `FUN_0018C4F0` call confirmed both widths with tracking `0`, scale
X/Y `1`, and descriptor `0x00B592D0`. The former `288` relationship result
subtracted only the stored row-local value and omitted the already composed
container term. The native row formula also separates relationship and icon
placement: after the title it draws the combined relationship from
`fVar17 + 4` and the icons from `fVar17 + 44`, while NA2 advances its shared
row coordinate by `30` before the relationship and then draws icons only `20`
units below it. This explains both refreshed cases: the long relationship needs
one jointly wrapped two-line block, while all three single-line rows and their
icons share the same repeatable vertical correction.
