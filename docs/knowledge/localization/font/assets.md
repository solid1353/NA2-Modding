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

## Resident loader and auxiliary ruby atlas

Fresh static tracing against clean NA2 `SLPS_258.37`, SHA-256
`20C0A40D70EA412CD431993A2E189B37ECB6054D63AE93BE545470016E1627AF`,
resolves the complete five-file font load family. `FUN_00186050` queues
`SF1.BIN`, `SF1C.BIN`, `GF4.BIN`, `GF4C.BIN`, and `GRF4.BIN` through
`FUN_00184840`. The resident selector `FUN_00186510(renderer, mode)` installs
SF1 plus SF1C for mode 0 and GF4 plus GF4C for nonzero mode.

The common parser at `FUN_00184100` reads an 8-byte resource header and routes
type 1 to raster parser `FUN_00184240`, or type 2 to companion-table parser
`FUN_00184630`. GF4 and SF1 each expose two raster descriptors. Both 104-byte
companion files contain an 8-byte header followed by a `0x60`-byte record: a
32-byte filename and exactly 64 bytes of 16 RGBA entries. The type-2 parser
constructs a render-side CLUT object from those entries. `FUN_00189860`
installs the selected raw record and CLUT object in the renderer.

`GRF4.BIN` has a distinct, now-confirmed role. Its single type-1 descriptor at
file offset `0x30` declares 8×8 glyphs, 167 raster entries, and a 334-record
two-byte-code map. The raster stride is 32 bytes per glyph, exactly one 8×8
4-bpp cell. Its only renderer path is `FUN_00186C30`, reached from shared
string renderer `FUN_00188140` when inline markup enters the annotation arm
after a pipe character. The renderer counts two-byte annotation glyphs through
the closing `>`, centers their aggregate width over the base-text span in
horizontal layout (or beside it in vertical layout), and resolves each glyph
through the GRF4 code map. This establishes GRF4 as the small ruby/furigana
annotation atlas rather than a generic graphics-support file.

The clean GRF4 file closes exactly under that interpretation:

| File range | Size | Meaning |
| --- | ---: | --- |
| `0x0000..0x0007` | `0x08` | Common type-1 resource header |
| `0x0008..0x0027` | `0x20` | Padded `GRF4.BIN` name |
| `0x0028..0x002F` | `0x08` | Flags and alignment |
| `0x0030..0x004B` | `0x1C` | Single raster descriptor |
| `0x004C..0x152B` | `0x14E0` | `167 * 0x20` packed glyph bytes |
| `0x152C..0x1A63` | `0x538` | `334 * 4` code-map records |

The final byte is the end of the 6,756-byte file; no unexplained trailer is
left by the parsed counts.

The exact direct evidence is:

| Resource | Clean size | Loader type | Confirmed resident use |
| --- | ---: | ---: | --- |
| `GF4.BIN` | 906,678 | 1 | Mode-1 selectable font rasters and metrics |
| `GF4C.BIN` | 104 | 2 | GF4's 16-entry RGBA CLUT |
| `GRF4.BIN` | 6,756 | 1 | 8×8 inline ruby/annotation glyphs |
| `SF1.BIN` | 103,046 | 1 | Mode-0 selectable font rasters and metrics |
| `SF1C.BIN` | 104 | 2 | SF1's 16-entry RGBA CLUT |

This result is high-confidence static evidence from the clean file headers,
the allocation sizes in both parsers, the selector calls, and the annotation
branch's positioning math. The semantic names of every type-1 descriptor flag
remain unresolved; do not extrapolate those bits beyond the observed branches.

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
