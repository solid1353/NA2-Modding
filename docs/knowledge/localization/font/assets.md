# Font assets

This document records retail NA2 (`SLPS-25837`) and NUN5 raster, glyph-cell,
descriptor, and palette findings.

## Research coverage

- **Assigned scope:** identify native font resources, loaders, atlas structures,
  glyph semantics, and NA2/NUN5 cell and palette differences.
- **Exploration depth:** all five retail NA2 font resources, their parsers,
  selectors, descriptor counts, raster cells, and relevant palettes were
  inspected; the NUN5 GF4 raster and GF4C palette were compared with them.
- **Confirmed coverage:** GF4/SF1 raster ownership, GF4C/SF1C palette ownership,
  GRF4 ruby-atlas behavior, and the NA2/NUN5 cell-semantic and palette
  differences are established.
- **Unresolved or untested:** semantic names for every descriptor flag.
- **Deliberate exclusions and overlap:** renderer math belongs to
  [Renderer metrics](renderer_metrics.md); screen placement belongs to the
  screen layout documents, starting with
  [Shared Font style](screen_layouts/shared_style.md).
- **Evidence limitations:** static cell and palette comparisons establish data
  differences, not rendered appearance.

## Resident loader and auxiliary ruby atlas

Static tracing of the retail resident ELF identified in
[Standard game file identities](../../game/files/file_identities.md)
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

`GRF4.BIN` has a distinct role. Its single type-1 descriptor at
file offset `0x30` declares 8×8 glyphs, 167 raster entries, and a 334-record
two-byte-code map. The raster stride is 32 bytes per glyph, exactly one 8×8
4-bpp cell. Its only renderer path is `FUN_00186C30`, reached from shared
string renderer `FUN_00188140` when inline markup enters the annotation arm
after a pipe character. The renderer counts two-byte annotation glyphs through
the closing `>`, centers their aggregate width over the base-text span in
horizontal layout (or beside it in vertical layout), and resolves each glyph
through the GRF4 code map. This establishes GRF4 as the small ruby/furigana
annotation atlas rather than a generic graphics-support file.

The retail GRF4 file closes exactly under that interpretation:

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

| Resource | Retail size | Loader type | Confirmed resident use |
| --- | ---: | ---: | --- |
| `GF4.BIN` | 906,678 | 1 | Mode-1 selectable font rasters and metrics |
| `GF4C.BIN` | 104 | 2 | GF4's 16-entry RGBA CLUT |
| `GRF4.BIN` | 6,756 | 1 | 8×8 inline ruby/annotation glyphs |
| `SF1.BIN` | 103,046 | 1 | Mode-0 selectable font rasters and metrics |
| `SF1C.BIN` | 104 | 2 | SF1's 16-entry RGBA CLUT |

This result is high-confidence static evidence from the retail file headers,
the allocation sizes in both parsers, the selector calls, and the annotation
branch's positioning math. The semantic names of every type-1 descriptor flag
remain unresolved; do not extrapolate those bits beyond the observed branches.

## Retail NA2 10x22 baseline

Retail NA2 contains a coherent 10x22 bitmap font with 157
cells and complete printable-ASCII coverage: 95 of 95 semantic slots exist and
94 of 94 non-space slots contain visible raster data. Its median visible glyph
box is 6x14 pixels, with median top 4 and bottom 17.

NA2's native secondary-byte decoder `FUN_001873E0` subtracts `0x20` below
`0xA0` and `0x43` otherwise. Byte `0xAE` therefore selects cell `107`, the
halfwidth small katakana yo (`ョ`), rather than the Windows-1252 registered
sign. Inspection of the NUN5 GF4 raster identifies the registered sign
at cell `142`, with metric bytes `00 04 00 03`, and the middle dot at cell
`151`, with metric bytes `05 09 04 06`. The middle dot's Windows-1252 byte
`0xB7` selects NA2 secondary cell `116`. These are static decoder and
raster observations.

## NA2 and NUN5 cell and palette differences

The two GF4 rasters do not share cell semantics throughout their first 123
cells: NUN5 cells `59..64` and `91..94` are blank or have different semantics
from the NA2 cells at the same indices, and NUN5 stores the at-sign in cell
`63` while NA2 printable ASCII addresses cell `32`.

Retail NA2's primary GF4 raster uses palette index 15 for 265,344 of 1,746,272
pixels (`15.194884%`). NA2's GF4C maps index 15 to opaque white, while NUN5's
maps it to black. The same NA2 raster uses palette indices 13 and 14 zero times.
