# Font renderer and asset findings

This directory preserves confirmed visual, structural, and byte-level Font
evidence, including accepted implementations and rejected historical tests.

## 2026-07-20 accepted native 14x20 integration baseline

The current patch set is version 5 with module hash
`9FC3C4905DFF6D14BAAA848C56E6C17D1DE4E79EEFAB2E1A7A74FAD6A25013F8`.
It is a new, deterministic donor built from hash-verified clean NA2 and
official NUN5 inputs; it is not based on m01, v22/v23, the rejected semantic
palette swap, the 10x22 resample, or a whole-file GF4 replacement.

`font_nun5_glyphs` installs native NUN5 14x20 geometry and metrics for
same-semantic English cells. Unsupported punctuation is reconstructed from
clean NA2, retaining 95/95 printable-ASCII coverage. The 123-cell secondary
atlas is locally bounded; packed metric rows occupy only value words of empty
primary-map slots and are decoded by secondary-only draw and measurement
hooks. Clean NA2 GF4C remains untouched. The deterministic generator verifies
these referenced blobs:

- atlas: 17,220 bytes, SHA-256
  `6E4B988E512568F0A91E0226A8A4046362C1A4EF078E50BBF630BEEF90333736`;
- packed map: 1,736 bytes, SHA-256
  `6F691015E5BA54EA87B2976970D828863E274BB543CC3D531D93800018EB7A5E`;
- decoder: 316 bytes, SHA-256
  `06406ABC5E10AD85A13ECFA4396064354CC0FD85EE090FA5AEEA4040EE62D8F7`;
- measurement hook: 24 bytes, SHA-256
  `8B7A75C0FDFD2F055ACFC1FCF90996E298CE363E112659579513A89606FE7C1C`.

The runtime-reviewed `native_final_v2` result contains exactly 19 edits: seven
glyph edits, nine Controls fit/alignment edits, and three character-modal
alignment edits. All four preserved NA2 savestates contain the same payload.
The canonical patch set was recovered byte-for-byte from those states before
closeout; a later unreviewed modal-scaling experiment was removed. Matched
Controls, Practice, Save/Load, and character-modal comparisons were presented
to the user, who accepted the result as good while noting that halfwidth Latin
glyphs remain noticeably bolder than NUN5. That weight difference is the next
refinement target. Fullwidth Shift-JIS Save/Load digits use a different glyph
path and are excluded from Latin-weight comparison.

Controls retains full-width `Linked Attack`, fits the official 19-byte
`Ultimate Jutsu Prep` probe, leaves `OFF` on the ordinary renderer, and
restores local scale immediately after a fitted draw. Its labels move one
local X unit without moving selection markers. The character modal uses local
X values `81.75, 73.375, 72.375, 63.5, 3.5`; reviewed ordinary-row centers are
within one pixel of NUN5 and the long fifth row fits inside the modal.

A clean file-backed apply preserved both file sizes and produced:

- `DATA/GF4.BIN`: 906,678 bytes, SHA-256
  `79BA614746E667A70A068A0A889085D028D8019884182E78041026A77971AA25`;
- `SLPS_258.37`: 5,273,256 bytes, SHA-256
  `EF0A61F163C22D25B4C4C28E6D9AC543EC6E3B93BC66E1087C33C7F1A0F791E6`.

The verification output and complete patch log are retained under
`work/Font/verification/font_package_v5_reviewed/` and
`work/Font/verification/font_package_v5_reviewed_log/`. The integrated profile
gate at `@logs/na2/builds/20260720_011314_550_pid31820/` passed the full 80-test
suite, selected the same three Font patches and 19 edits, reproduced both
documented file hashes, updated Current, and rotated Previous. The final ISO's
boot ELF CRC is `1852E63F`; a controlled hidden 15-second PCSX2 boot reported
the same CRC. The build left no `.building` ISO or PCSX2 process behind.

## 2026-07-19 superseded clean-font baseline

This earlier baseline started from clean NA2, not from m01, v22, v23, or the
rejected semantic-palette candidate. Static inspection established a
coherent 10x22 bitmap font with 157 cells and complete printable-ASCII
coverage: 95/95 semantic slots exist and 94/94 non-space slots contain visible
raster data. The median visible glyph box is 6x14 pixels, with median top 4 and
bottom 17. Matched runtime captures confirmed that this asset was serviceable,
but the later accepted native baseline superseded its unchanged-GF4 result.

The isolated descriptor-height experiment at ELF file offset `0x88064` is
rejected. Changing `0C 00 20 C6` to `10 00 20 C6` did not make a Y-only
correction. With the clean descriptor it produced a 28x28 quad instead of the
untouched 24x24 quad, stretching both axes by 16.7 percent while logical
measurement stayed unchanged. Runtime captures showed damaged outlines and
no useful alignment improvement. The exact edit remains disabled as
`font_vertical_quad_height` with `runtime_failed` status.

The accepted patch set has two independent `runtime_proven` components:

- `font_controls_auto_fit` affects only the first eight Controls action-label
  calls plus the local Controls row origin. Clean plain-ASCII measurement is
  `9.5 * byte_count + 1`; strings below 14 bytes retain horizontal scale
  `1.0`. `Linked Attack` is 13 bytes and therefore stays full width. For an
  overflowing string the helper applies `128 / measured_width`, corrects the
  centered origin, draws through the original helper, and restores scale
  `1.0`. The ninth `OFF` call remains on the ordinary renderer. The row origin
  changes from 48 to 50, retaining the original 26.8-unit interval.
- `font_modal_alignment` uses measured X values `84, 79, 79, 75, 13`, moves
  the first four rows down one local unit, places the red row at local Y 117,
  and compensates the selected shadow path by two X units.

The official 19-byte `Ultimate Jutsu Prep` runtime probe measures 181.5 units
and uses scale `256 / 363`, approximately `0.705234`. Its final clean-NA2 ink
box is `(74,98)-(236,114)`, center `(154.5,105.5)`, compared with NUN5
`(76,99)-(233,115)`, center `(154,106.5)`. It fits without clipping; the
remaining five-pixel width difference is clean glyph appearance rather than
placement. `Linked Attack` retains width 147 and `OFF` width 30, with no
horizontal scaling.

The four ordinary character-modal centers are `(318.5,182)`, `(319,212)`,
`(317,242)`, and `(318.5,272)`; NUN5 is `(318,182)`, `(318,212)`,
`(318,242)`, and `(318,272)`. The selected red row is exact at
`(319,314.5)` in both. The accepted compact-table capture is byte-identical to
the independently tested dynamic-centering proof.

The patch set preserves the 5,273,256-byte ELF size. Applying it to the verified
clean ELF produces SHA-256
`3338654A24BCFCC5E101654A93E585335A9A9ECEE607AC018F43D0E54FD14217`.
The Controls helper SHA-256 is
`B26071C654C90085B78BC528E187E2D7BD74CE78363319C21CE30E45B54A13F3`;
the tail derivation SHA-256 is
`BF51639A21D85CD8A09D411B5F069099871E523E56736A06B363F7F785B65C0E`.
The exact guarded captures and generated measurements remain under
`work/Font/analysis/runtime_compare/`, and the clean apply log remains under
`work/Font/verification/font_package_v2_log/`.

The integrated profile build is retained at
`@logs/na2/builds/20260719_202514_393_pid36044/`. It selected the two accepted
Font patches, preserved the QoL module hash, promoted an updated Current ISO,
and recorded Font's clean-to-patched ELF hashes above. The resulting Current
ISO SHA-256 is
`4273E20D03642CB287C4F3F7ECCA56E46B4CE412E627D6C006980A9EE61B45AB`.
A controlled clean boot reported `SLPS-22228`, CRC `F3F4C52B`; read-only PINE
verification matched all 78 changed Font words and confirmed the rejected
quad-height word was absent.

## Experiment

The test changed `SLPS_258.37` at file offset `0x866E0` from `80 BF 02 3C` to `00 00 02 3C`. The intended effect was to match the NUN5 ASCII-mode horizontal-tracking initialization (`0.0` instead of NA2's `-1.0`). The exact operation is retained in `font_v23_patch_log.tsv` and canonically normalized as `font_v23_elf_zero_tracking` in `docs/knowledge/font/history/font_elf_history/`.

## Observed result

The user observed no meaningful visual improvement over the preceding v22 state. English text remained oversized/chunky, spacing remained inconsistent, and long Controls-menu entries remained clipped. `font_v23_no_visible_change.png` is the final comparison screenshot.

This is a useful negative result: do not repeat this single-field tracking patch as a new proposed fix. It does not prove that tracking or `FUN_00186510` is irrelevant, only that changing this one initialization value did not solve the visible problems in the tested build.

## Surrounding confirmed observations

- NA2 and NUN5 `GF4C.BIN` are both 104 bytes but diverge from offset `0x28`; the v22 and v23 experiments used the NUN5 variant. Its independent functional significance remains unproven.
- Replacing NA2 GF4 with the exact NUN5 GF4, padded or unpadded, produced broad spacing but patchy glyph rendering and could disrupt PNACH behavior. Do not repeat that direct swap as a new hypothesis.
- The v22 state was clean and closer to NUN5, but glyphs could touch or overlap and long text still clipped.
- `docs/knowledge/font/history/font_m01/` preserves the declarative reconstruction of the accepted clean-coverage font state. Historical ELF experiments, including v23, are normalized under `docs/knowledge/font/history/font_elf_history/`. Neither directory is an active patch set.

The remaining font work still separates into glyph appearance, positioning/advance behavior, and missing NUN5-style auto-fit/squish. Reuse applicable historical evidence from Git history and maintain current analysis under `@analysis/disassembly/NA2/` and `@analysis/disassembly/NUN5/`, never under `@source/`.

Relevant static-analysis leads retained from the investigation:

- NA2 ASCII setup: `FUN_00186510`.
- NUN5 counterpart: `FUN_001878e0`.
- NUN5 boxed auto-fit: `FUN_00389df0` and `FUN_0018b1b0`.
- NA2 menu path: `FUN_003885b0`, which calls `FUN_00379240` and appeared to draw/center without the corresponding 128-pixel auto-fit path.

## 2026-07-19 Controls auto-fit negative result

A temporary size-preserving ELF experiment applied NUN5's shrink-only
`128 / measured_width` rule to the two text calls in NA2
`FUN_003885b0`. The test used a Controls-only wrapper plus shared horizontal
renderer hooks for the leading bearing, glyph X geometry, space advance, and
normal glyph advance. It changed no GF4 or GF4C bytes. The composed test ELF
was 5,273,256 bytes with SHA-256
`483CE707B4B42C0194A696F78EB99FB291D11BF4E038FE4B3DAC2DAD2D48420C`.

Runtime comparison rejected the experiment. NA2 visibly narrowed
`Linked Attack`, while the same exact text remains full width in NUN5. NUN5
does not special-case that label: its first eight Control Settings action
labels all use a 128-pixel box through
`FUN_00399df0 -> FUN_00389df0 -> FUN_0018b1b0 -> FUN_0018ca40`.
NUN5 measures horizontal text through `FUN_0018b7f0`; the temporary NA2
wrapper instead used the legacy
`FUN_003798e0 -> FUN_001859a0 -> FUN_00184e60` measurement path. Copying the
box threshold and scale formula therefore made a different fit decision.
NUN5 also renders the final `OFF` row through ordinary `FUN_00385df0`, while
the rejected experiment routed both NA2 call families through its wrapper.

The captured NA2 screen also confirms that visible font alignment is not yet
equivalent to NUN5. Vertical baseline errors are mostly independent of a
horizontal width test, but left bearings, tracking, glyph advances, and
centering directly affect both the logical measured width and its relationship
to visible glyph bounds. The temporary rows and profile selection were removed
after that review.

The accepted implementation above resolves this negative result without
reusing its legacy measurement call. It proves the clean fixed-ASCII formula,
keeps the 13-byte threshold decision correct, scales the three horizontal draw
surfaces through one per-call factor, and restores that factor immediately.
The failed threshold-only wrapper remains useful evidence: do not reinstate it
or treat a box constant alone as a valid fit port.

## 2026-07-19 rejected semantic NUN5 appearance experiment

Matched 1708x1281 captures of the Control Settings screen separate the current
defects. For the same `Attack`, `Item Use`, `Item Select`, and `Linked Attack`
labels, visible widths are already close to NUN5, but the NA2 main-row ink is
31 pixels high instead of 36, its bottom edge is consistently 8 pixels too
high, and its horizontal center drifts farther left as the string grows. The
four-label center error fits approximately `8.6 - 7.38 * character_count`
pixels (`R^2` about 0.98). The static `SELECT button: Return to Defaults`
legend is essentially the same 832x38 versus 831x38 appearance but is 99
pixels farther right in NA2. These measurements identify separate raster,
vertical-placement, and logical-advance/centering problems; fixing weight
alone cannot establish alignment parity.

Static structure establishes a safe size-preserving NUN5 data experiment.
NUN5's single GF4 descriptor contains 223 14x20 cells with a 140-byte stride;
the accepted m01 descriptor reserves 123 cells at NA2 `0xD9240`. A literal
copy of NUN5 cells `0..122` is nevertheless invalid. Both parsers map printable
ASCII directly as `byte - 0x20`, but NUN5 cells `59..64` and `91..94` are blank
or have different semantics. That blind copy would remove the brackets used
by `[S]` mappings and other translated-English punctuation. NUN5 also stores
the literal at-sign in cell `63`, while NA2 printable ASCII addresses cell
`32`. The direct first-123 candidate with GF4 SHA-256
`8E426B252D45B735D78A3D64657BE8E37F4856150D454314F67DAFF8D48C203D`
was therefore rejected statically and must not be restored.

The corrected `font_nun5_appearance` patch imports exact official NUN5 cells
and metric rows for the same-semantic ranges `0..31`, `33..58`, `65..90`, and
`95..122`. It relocates exact NUN5 source cell and metric row `63` to NA2
destination cell `32`. Cells `59..64` and `91..94` retain their accepted m01
glyph shapes and metrics. Their bitmap indices are deterministically converted
from the m01 palette to the NUN5 palette with this mapping:

`0->0, 1->1, 2->2, 3->3, 4->4, 5->5, 6->8, 7->7, 8->8, 9->B, A->A, B->C, C->F, D->F, E->E, F->E`.

The exact official raster and metric operations are:

- cells `0..31`: NUN5 raster `0x4C..0x11CC` to NA2
  `0xD9240..0xDA3C0`; NUN5 metrics `0x7BE8..0x7C68` to NA2
  `0xD59E0..0xD5A60`;
- cell `32` from source cell `63`: raster `0x22C0..0x234C` to
  `0xDA3C0..0xDA44C`; metric `0x7CE4..0x7CE8` to
  `0xD5A60..0xD5A64`;
- cells `33..58`: raster `0x1258..0x2090` to `0xDA44C..0xDB284`;
  metrics `0x7C6C..0x7CD4` to `0xD5A64..0xD5ACC`;
- cells `65..90`: raster `0x23D8..0x3210` to `0xDB5CC..0xDC404`;
  metrics `0x7CEC..0x7D54` to `0xD5AE4..0xD5B4C`;
- cells `95..122`: raster `0x3440..0x4390` to `0xDC634..0xDD584`;
  metrics `0x7D64..0x7DD4` to `0xD5B5C..0xD5BCC`;
- GF4C palette `0x28..0x68` to the same NA2 range, with source SHA-256
  `499B64CDF2DFEA7C29D89834491A9C307B9653D4FFC217EC20CF8F358DAC0D3C`.

The corrected expected outputs are GF4
`690D0E53F30BD150C64F609DB8951D313A90F341F39B7486A8ED6A5E943A2FFE`,
GF4C `C6C889B795BB6137120252FAE887B48CB4304A0854A761F5942B50818D9D2FBD`,
and ELF `5541FB6C3CFFE15B318AC68C49E2254BE52E3C8BC99AC5B823CFE53FD7BEB01F`.
The independent generator and raw-binary engine produced byte-identical GF4
and GF4C outputs. The 123-cell bitmap-block SHA-256 is
`4EBB5F0753717718024F159D1D1B0612FDA566FA4B36F8B2F4E3A819F5E3C907`;
the 123-row metric-block SHA-256 is
`A6C51E67E25634CC3B9F128A75C694B274485CD45D3ACD36379A3385B9D55458`.

Exact NUN5 cells `95..122` are outside printable ASCII and best satisfy the
appearance-parity objective, but eight of those NUN5 cells are blank where m01
had data. Runtime review must therefore include untranslated Japanese or
halfwidth text in addition to translated English. A fallback that preserves
those m01 cells is statically defined by the investigation but is not enabled.

This historical experiment is mutually exclusive with `font_m01` and is now
`runtime_failed`. It is not v22: it uses the confirmed m01 destination
`0xD9240`, retains 123 cells and m01 ELF behavior, does not import v22 pointer
tokens or its renderer-width edit, and is not a padded or unpadded whole-file
swap.

Runtime review on 2026-07-19 rejected this candidate. It did not materially
improve ordinary letters and damaged outline and alpha behavior, most visibly
on numeric glyphs. A byte-level audit found that all 84 same-semantic visible
printable cells compared between the candidate and its m01 parent retained
identical visible masks and metrics; the meaningful difference was palette
interpretation rather than improved geometry.

The coupled GF4C swap is unsafe for untouched NA2 raster data. Clean NA2's
primary raster uses palette index 15 for 265,344 of 1,746,272 pixels
(15.194884%). NA2 maps index 15 to opaque white, while NUN5 maps it to black.
Changing GF4C therefore reinterprets a large existing pixel population and
explains the deterministic outline damage. The patch is now classified
`runtime_failed`, remains disabled as negative evidence, and must not be used
as a donor or implementation parent. The accepted native baseline changes only
the bounded secondary GF4 data and keeps clean NA2 GF4C unchanged.

The fresh matched modal captures also give a concrete overflow reference. At
1708x1281, the visible red instructional-text ink spans approximately
`(455,822)-(1248,859)` in NUN5 and `(525,833)-(1278,865)` in the rejected NA2
build, whose right edge is clipped. Because that NA2 capture also contains the
failed asset/palette state, it is evidence for the screen and overflow symptom,
not a clean-source renderer acceptance image.
