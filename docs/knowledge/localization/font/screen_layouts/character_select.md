# Character Select Font layouts

## Research coverage

- **Assigned scope:** compare clean NA2 and NUN5 Character Select modal text layout.
- **Exploration depth:** the relevant native callers, records, and coordinates
  were inspected.
- **Confirmed coverage:** the documented owners and cross-game geometry
  differences are established.
- **Unresolved or untested:** callers and states not explicitly covered below.
- **Deliberate exclusions and overlap:** feature hooks and behavior belong to
  [Font](../../../../features/localization/font.md).
- **Evidence limitations:** bounded states do not cover every string or
  animation phase.

## Character Select modal selected row, return body, and choice list

The Menus suite established the shared row-family behavior. The row
loop in clean NA2 main-ELF `FUN_003BC780` supplies Y `8`, `32`, `56`, `80`,
and `120` before the selected call at file `0x2BC984` or the ordinary call at
file `0x2BC9BC`. The selected native helper accepts integer X, while the
ordinary helper accepts a floating-point X.

## Character Select ordinary-row metric session

Supplemental runtime evidence reopens only the five-row player-mode list inside
main-ELF `FUN_003BC780`. NA2 draws its selected entry through
`FUN_00382610` at runtime `0x003BC884` and every ordinary entry through
`FUN_00382470` at runtime `0x003BC8BC` (ELF file `0x2BC9BC`, clean guard
`1C090E0C00000000`). NUN5 homolog `FUN_003CF3F0` instead routes both states
through one `FUN_00393210` helper, with native local Y values `0`, `24`, `48`,
`72`, and `106`.
