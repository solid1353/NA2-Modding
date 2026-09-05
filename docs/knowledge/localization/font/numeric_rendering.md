# Numeric and settings text rendering

Clean NA2 and NUN5 formatting and layout differences for Save/Load, Battle and
Practice Settings, Jutsu rows, and Ninja Song values.

## Research coverage

- **Assigned scope:** identify native numeric formatters, caller ABIs, padding
  modes, special-value branches, and the relevant boxed-layout contracts.
- **Exploration depth:** all six Save/Load calls, the Battle time branch, five
  Ninja Song formatter calls, settings loops, Jutsu-row draw, and Ninja Song
  templates were compared.
- **Confirmed coverage:** fullwidth-versus-ASCII ownership, decimal padding,
  the Battle infinity branch, Jutsu wrapping box, and data-driven Ninja Song
  layouts are established.
- **Unresolved or untested:** numeric callers outside these families and every
  possible fight-dependent Ninja Song row.
- **Deliberate exclusions and overlap:** NA228 formatting hooks and validation
  belong to [Font](../../../features/localization/font.md); translation wording
  belongs to the translation importer.
- **Evidence limitations:** paired screens cover representative values; unseen
  values share the established formatter paths but were not all displayed.

## Save/Load numeric fields

NA2 emits fullwidth CP932 digits for its date and Play Time fields, whereas
NUN5 emits ordinary ASCII digits and punctuation. NA2 `FUN_001E6370` owns six
calls for year, month, day, hour, minute, and second through
`FUN_00378510`. Their ELF offsets are `0xE660C`, `0xE6650`, `0xE6694`,
`0xE67A4`, `0xE67E8`, and `0xE682C`.

NUN5's homolog uses ASCII decimal. Day and month use `%02d`, year uses `%d`,
and hour follows `hour < 100 ? hour : 99` before `%02d`. Native timer divisors
are 108,000, 1,800, and 30. The Save/Load colon is a separate fullwidth string
at NA2 ELF offset `0x503134`.

## Battle Settings time

`FUN_008801E0` renders Battle Settings rows. Values below 100 use the
fullwidth formatter through the 24-byte block at BTL offset `0x1CC3D8`.
Value 100 takes a separate infinity-symbol branch. The NUN5 homolog is
`FUN_0089CBD0` and emits ordinary decimal while preserving the infinity case.

## Ninja Song numbers

NA2 `FUN_00718920` renders the arithmetic expression and `FUN_00718C60` renders
later details. Five calls reach the same fullwidth formatter:

| BTL offset | Field | Width | Mode |
| ---: | --- | ---: | ---: |
| `0x64B28` | left factor | 3 | 0 |
| `0x64BA8` | right factor | 3 | 0 |
| `0x64CE4` | total | 5 | 0 |
| `0x64E4C` | inline value | 4 | 1 |
| `0x64ED4` | detail score | 4 | 0 |

The NUN5 homolog emits ASCII decimal with the same ABI: mode 0 left-pads with
spaces, mode 1 is unpadded, and mode 2 left-pads with zeroes. The multiplication
separator is an independent string containing `" * "`.

## Jutsu-selector row

NA2 `FUN_006BCB70` calls the ordinary text renderer directly at BTL file
`0x90DC`, using points `(30 + f21, 16 + f20)` and
`(310 - f21, 16 + f20)`. It supplies no width or line limit, so long English
names remain on one line and overflow.

NUN5 `FUN_006CFE70` instead passes a `186 x 32` box, two-line limit, start
horizontal placement, centered vertical placement, and wrapping. Relative to
the NA2 points, its box begins seven units left on side one, four units left on
side two, and ten units above on both sides.

## Settings page templates

Battle and Practice Settings are loop-rendered templates, not collections of
row-specific draw calls. Battle uses one label call at BTL `0x1CC368` and value
branches at `0x1CC424` and `0x1CC598`. Practice uses heading, label, and value
calls at `0x1CE528`, `0x1CE56C`, and `0x1CE5D4`.

NUN5 ordinary values use a centered `104`-unit box beginning at X `304` on
both pages. Its special Battle time branch selects the ASCII-font bit for value
100 and clears it for ordinary decimal values; NA2 clears the bit for both.

## Ninja Song templates

NUN5's expanded arithmetic layout places factor columns at X `30`, `90`, and
`120`, the unit resource in box `(176,-6,52,32)`, equals at X `226`, and the
total in `(256,0,64,20)`. The native row table selects expanded arithmetic,
total-only, or N/A output.

The objective row uses index X `80`, prose X `112`, prose Y `rowY - 6`, and a
`320 x 32` two-line box. Post-objective bonus rows are data-driven 12-byte
records. NUN5 uses a shared `288 x 32` two-line label box and a `96 x 20`
right-aligned total box. Rows 17, 18, 22, 25, 26, and 27 insert an unpadded
inline number into the label; other rows format their descriptor directly.
