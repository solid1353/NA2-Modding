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
