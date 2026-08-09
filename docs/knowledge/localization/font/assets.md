# Font assets

This document owns durable raster, glyph-cell, descriptor, and palette
findings for the native NUN5-derived secondary font. Renderer calculations and
screen placement remain in their respective domain documents.

## Accepted asset boundary

The accepted package imports NUN5 14x20 geometry and metrics only for
same-semantic English cells, reconstructs unsupported punctuation from clean
NA2, preserves printable-ASCII coverage, and keeps clean NA2 GF4C palette
semantics. The shortened secondary atlas remains confined to its own parser
path. Exact current integration and generation ownership are documented in the
[integration baseline](integration_baseline.md).

## Superseded clean 10x22 baseline

An earlier clean-NA2 baseline established a coherent 10x22 bitmap font with 157
cells and complete printable-ASCII coverage: 95 of 95 semantic slots existed
and 94 of 94 non-space slots contained visible raster data. Its median visible
glyph box was 6x14 pixels, with median top 4 and bottom 17. Matched runtime
captures showed that the asset was serviceable, but the later native 14x20
baseline superseded it.

The isolated descriptor-height experiment at ELF file offset `0x88064` is
rejected. Changing `0C 00 20 C6` to `10 00 20 C6` produced a 28x28 quad instead
of a Y-only correction, stretching both axes by 16.7 percent while logical
measurement stayed unchanged. Runtime captures showed damaged outlines and no
useful alignment improvement.

## Rejected donor-raster and palette combinations

Replacing NA2 GF4 with the exact NUN5 GF4, padded or unpadded, produced broad
spacing and patchy glyph rendering. A direct first-123-cell copy is also
structurally invalid: NUN5 cells `59..64` and `91..94` are blank or have
different semantics, and NUN5 stores the at-sign in cell `63` while NA2
printable ASCII addresses cell `32`. Such a copy would remove punctuation used
by translated mappings.

A later semantic import retained the mismatched punctuation cells, relocated
NUN5 cell `63` to NA2 cell `32`, and imported same-semantic ranges. Runtime
review still rejected it: ordinary letters did not materially improve, while
numeric outlines and alpha behavior were damaged. All 84 compared visible
printable cells retained identical masks and metrics relative to their parent;
the meaningful difference was palette interpretation.

The coupled GF4C swap is unsafe for untouched NA2 raster data. Clean NA2's
primary raster uses palette index 15 for 265,344 of 1,746,272 pixels
(`15.194884%`). NA2 maps index 15 to opaque white while NUN5 maps it to black,
so the swap reinterprets a large existing pixel population. Do not use the
whole NUN5 GF4 or GF4C as an implementation parent. The accepted native
baseline changes only bounded secondary GF4 data and leaves clean NA2 GF4C
unchanged.

The retired m01, m02, v22, v23, and semantic-palette records remain
recoverable from Git commit `55d1163`; none is an active patch set or
implementation parent.

## Unresolved selective palette refinement

Clean NA2's primary GF4 raster and the accepted secondary raster both use
palette indices 13 and 14 zero times. Those two GF4C entries may therefore be
candidates for exact NUN5 white-alpha levels without changing any currently
referenced primary pixel. This remains a bounded asset lead only if a matched
review still finds a halfwidth-Latin weight difference.

No palette bytes or raster indices have been changed or runtime-tested for this
lead. Any experiment must start from the accepted native package and remain a
small, call-local or asset-local, script-generated change. A full NUN5 text
renderer transplant is outside its scope.
