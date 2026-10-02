# Shared Font style

Cross-screen evidence for the global selected-style dispatcher.

## Research coverage

- **Assigned scope:** identify the retail NA2 (`SLPS-25837`) functions that
  apply the global selected text style.
- **Exploration depth:** a function-level semantic scan covered retail
  `SLPS_258.37`, `ADV.BIN`, `BTL.BIN`, and `ETC.BIN`.
- **Confirmed coverage:** the six functions that combine the selected style's
  gray shade, offset pass, and text renderer are established.
- **Unresolved or untested:** callers and states not explicitly covered below.
- **Deliberate exclusions and overlap:** the selected-row offset and glyph
  metrics belong to [Renderer metrics](../renderer_metrics.md); raster and
  palette findings belong to [Font assets](../assets.md).
- **Evidence limitations:** the scan identifies functions combining the
  documented constants and renderer; it does not enumerate their callers.

## Global selected-style default

The complete boundary requires a function-level semantic scan, not a search
for one instruction encoding. Across retail `SLPS_258.37`, `ADV.BIN`,
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
