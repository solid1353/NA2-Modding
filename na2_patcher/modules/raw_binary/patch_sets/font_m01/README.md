# Historical font m01 experiments

This package preserves the old m01 line as historical evidence. It is no
longer selected by the current profile and is not a parent for clean-source
Font work. One atomic `font_m01` patch can still reproduce the former baseline
from clean NA2 inputs:

- `DATA/GF4.BIN`: six verified replacement ranges; output SHA-256
  `7E01BB6101431F1628F8ECF541ACA1D71AB1A42F27A2E20E01C951CE15CB49AF`.
- `SLPS_258.37`: two verified replacement ranges; output SHA-256
  `5541FB6C3CFFE15B318AC68C49E2254BE52E3C8BC99AC5B823CFE53FD7BEB01F`.

The source package SHA-256 was
`FC345460BBC22A263C6D0AB8A728A156273BB226707BFC64B3D3C813753E7410`.
The archive and conversion tooling are retained only in Git history. The
declarative TSVs are the active source of truth.

## Rejected semantic NUN5 appearance experiment

`font_nun5_appearance` is retained disabled with `runtime_failed` status. It
preserves the m01 14x20 descriptor, 123-cell limit, ELF coverage route, output
marker, and every file size, but it must not be selected for a normal build or
used as the basis of a new patch.

The patch imports exact official NUN5 bitmap cells and metric rows for
same-semantic ranges `0..31`, `33..58`, `65..90`, and `95..122`. NUN5 stores
the literal at-sign in cell `63`, so that exact bitmap and metric row are
relocated to NA2 printable-ASCII cell `32`. The ten printable ASCII additions
in cells `59..64` and `91..94` have no matching NUN5 glyphs; their m01 shapes
and metrics are retained, with bitmap palette indices converted for the NUN5
GF4C palette. This preserves `[S]` and the rest of printable English coverage.

The experiment also copied the coupled NUN5 palette from
`GF4C.BIN[0x28:0x68]`. Expected historical outputs from clean, hash-verified
inputs are:

- `DATA/GF4.BIN`: `690D0E53F30BD150C64F609DB8951D313A90F341F39B7486A8ED6A5E943A2FFE`.
- `DATA/GF4C.BIN`: `C6C889B795BB6137120252FAE887B48CB4304A0854A761F5942B50818D9D2FBD`.
- `SLPS_258.37`: `5541FB6C3CFFE15B318AC68C49E2254BE52E3C8BC99AC5B823CFE53FD7BEB01F`.

The independently rejected direct first-123 copy would blank or mis-map printable
punctuation, including the brackets visible in `[S]Ult Prep`; do not restore
it. The failed experiment conflicts with `font_m01`, so never select both. It
is not the previous v22 layout: it does not reuse v22's shifted destination,
95-cell count, pointer tokens, or renderer-width edit, and it is not a
whole-file GF4 replacement. Exact NUN5 rows `95..122` may also regress eight
populated m01 halfwidth-kana cells.

Runtime review rejected this experiment. Ordinary letters were not materially
improved, while outline and alpha behavior was damaged, most visibly on
numbers. Byte-level audit explains why: the GF4 cell masks were already
equivalent for the compared same-semantic printable glyphs, whereas the GF4C
swap changed the interpretation of palette indices used by untouched NA2
raster data. In clean NA2 primary raster data, palette index 15 alone occurs
265,344 times out of 1,746,272 pixels (15.194884%); NA2 maps that index to
opaque white while NUN5 maps it to black. The damage is therefore deterministic,
not an alignment fix. Current work begins from clean NA2 GF4/GF4C and changes
renderer behavior independently.
