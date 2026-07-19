# Font m01 clean coverage

This patch set is the declarative, size-preserving replacement for the retired
font m01 package. One atomic `font_m01` patch reproduces both modified files
from clean NA2 inputs:

- `DATA/GF4.BIN`: six verified replacement ranges; output SHA-256
  `7E01BB6101431F1628F8ECF541ACA1D71AB1A42F27A2E20E01C951CE15CB49AF`.
- `SLPS_258.37`: two verified replacement ranges; output SHA-256
  `5541FB6C3CFFE15B318AC68C49E2254BE52E3C8BC99AC5B823CFE53FD7BEB01F`.

The source package SHA-256 was
`FC345460BBC22A263C6D0AB8A728A156273BB226707BFC64B3D3C813753E7410`.
The archive and conversion tooling are retained only in Git history. The
declarative TSVs are the active source of truth.

## Semantic NUN5 appearance candidate

`font_nun5_appearance` is a separately selectable `approved_for_test`
alternative to `font_m01`. It preserves the accepted m01 14x20 descriptor,
123-cell limit, ELF coverage route, output marker, and every file size.

The patch imports exact official NUN5 bitmap cells and metric rows for
same-semantic ranges `0..31`, `33..58`, `65..90`, and `95..122`. NUN5 stores
the literal at-sign in cell `63`, so that exact bitmap and metric row are
relocated to NA2 printable-ASCII cell `32`. The ten printable ASCII additions
in cells `59..64` and `91..94` have no matching NUN5 glyphs; their m01 shapes
and metrics are retained, with bitmap palette indices converted for the NUN5
GF4C palette. This preserves `[S]` and the rest of printable English coverage.

The coupled NUN5 palette is copied from `GF4C.BIN[0x28:0x68]`. Expected
outputs from clean, hash-verified inputs are:

- `DATA/GF4.BIN`: `690D0E53F30BD150C64F609DB8951D313A90F341F39B7486A8ED6A5E943A2FFE`.
- `DATA/GF4C.BIN`: `C6C889B795BB6137120252FAE887B48CB4304A0854A761F5942B50818D9D2FBD`.
- `SLPS_258.37`: `5541FB6C3CFFE15B318AC68C49E2254BE52E3C8BC99AC5B823CFE53FD7BEB01F`.

The rejected direct first-123 copy would blank or mis-map printable
punctuation, including the brackets visible in `[S]Ult Prep`; do not restore
it. The semantic candidate conflicts with `font_m01`, so never select both.
It is not the previous v22 layout: it does not reuse v22's shifted
destination, 95-cell count, pointer tokens, or renderer-width edit, and it is
not a whole-file GF4 replacement. Runtime comparison is required before
promotion. Exact NUN5 rows `95..122` may regress eight populated m01
halfwidth-kana cells, so untranslated Japanese coverage must be checked during
runtime review.
