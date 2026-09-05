# Shared Font style and matched-screen baseline

## Research coverage

- **Assigned scope:** compare clean NA2 and NUN5 selected style and shared screen geometry.
- **Exploration depth:** the relevant native callers, records, and coordinates
  were inspected.
- **Confirmed coverage:** the documented owners and cross-game geometry
  differences are established.
- **Unresolved or untested:** callers and states not explicitly covered below.
- **Deliberate exclusions and overlap:** feature hooks and behavior belong to
  [Font](../../../../features/localization/font.md).
- **Evidence limitations:** bounded states do not cover every string or
  animation phase.

Cross-screen evidence for the global selected-style dispatcher and the final matched-screen baseline.

## Global selected-style default

The complete boundary requires a function-level semantic scan, not a search
for one instruction encoding. Across clean `SLPS_258.37`, `ADV.BIN`,
`BTL.BIN`, and `ETC.BIN`, exactly six functions combine gray `0xFF808080`, an
X `-1.0`/Y `-2.0` selected pass, and the text renderer. All six are in the
boot ELF:

- `FUN_00379040` / runtime `0x00379040`: state-aware central primitive;
- `FUN_00379150` / runtime `0x00379150`: caller-colored central primitive;
- `FUN_00379C30` / runtime `0x00379C30`: fixed two-choice primitive;
- `FUN_001E6060` / runtime `0x001E6060`: shared two-record list component;
- `FUN_001E6370` / runtime `0x001E6370`: three-record save/load slot row;
- `FUN_001E6CE0` / runtime `0x001E6CE0`: shared Save/Load, overwrite, and
  return-to-title Yes/No component.

## Matched-screen baseline

Across 20 identical black-text samples, median NA2 differences from NUN5 were
-2 pixels in visible width, -2 pixels in visible height, `0.850782x` total
dark-ink pixels, and `1.018280x` dark-ink density inside the smaller bounds.
The font was therefore not a uniformly enlarged or uniformly heavier raster.
String-dependent width errors and caller-dependent vertical offsets proved
that one global scale, tracking, X, or Y correction could not establish
parity.
