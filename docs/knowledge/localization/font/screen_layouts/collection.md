# Collection Font layouts

Font-owned layout evidence for Collection lists and structural renderer families. The initial grouped findings were established on 2026-07-24; later evidence dates are recorded with their sections.

## Collection fixed-cadence list wrapping

The replacement 2026-07-30 ss8-ss10 pairs isolate the Collection Movie and
character-detail lists. Bounded NA2 ETC inspection identifies
`FUN_006B4D30`; its shared active row draw is runtime `0x006B4ED8`, file
`0xFD8`, guarded by
`10E40D0C00000000` (`jal 0x00379040` plus NOP). The NUN5 homolog
`FUN_006C7CA0` replaces the corresponding draw at ETC file `0x1164` with its
boxed renderer at `0x0038A210`.

NUN5 stores the active box width and height in each list structure at
`+0x14/+0x18`. The supplied states prove a 192-by-32 box for ss8 Movie titles,
a 152-by-32 box for the ss9 move list, and a 192-by-32 box for the ss10
relationship list. Every family uses native X, native Y minus 10, two lines,
and a 16-unit line interval. The outer list retains fixed row cadence; wrapped
titles occupy two lines inside their existing row rather than increasing later
row positions. Exact visible breaks include:

- `Sealing Jutsu: Nine` / `Phantom Dragons`;
- `People of Endless` / `Darkness`;
- `Ninja Art: Beast` / `Scroll Replicas`;
- `Fourth Awakened` / `Mode`;
- `Shadow Clone` / `Jutsu`;
- `Unchanging` / `Relationship`.

NA2's ss9 parent at `0x00C8D110` points to list head `0x00C75C00`; the visible
text pointers are `0x006D9BD8` (`Right!`), `0x006D9C00`
(`Shadow Clone Jutsu`), and `0x006D9C40` (`Running Wild`). Its ss10 parent at
`0x00C9BDE0` points to list head `0x00C79EE0`; the visible text pointers are
`0x006DC340`, `0x006DC370`, `0x006DC3A0`, and `0x006DC3C0`. The corresponding
NUN5 parents are `0x00C0BCA0` with width 152 and `0x00C1C630` with width 192.
The NA2 structures do not retain homologous usable box fields at the NUN5
offsets, so copying those offsets is not a valid implementation.

The bounded implementation accepts Movie-title pointers in
`0x003FFAA0..0x003FFC10` plus only the seven exact ss9/ss10 character-detail
pointers above, copies the source to a transient buffer, and reuses
`font_v2_wrap_native` with a two-line limit. It draws each resulting line
through the displaced native renderer at a 16-unit interval. That separate
line draw is required because passing the inserted newline to NA2's native
renderer produces a 25-unit interval on these screens. Short titles, the
highlighted red style, fixed caller cadence, source mappings, and every
other pointer through the shared renderer remain native.

The first shared implementation nevertheless published a 20-unit glyph-quad
override for every recognized pointer. It also exposed the flag-aware
right-edge shim defect described below. The compatible task ISO's payload
SHA-256
`74A2A4BD0E66C0F4C55C5A0F67A2342D2E0DE01768D2D2416B945E64D2C0EB39`
still used the older 88-byte shim at runtime `0x008F57B8`, while rejected
integrated build record `20260730_162124_431_pid9072` linked the 128-byte
flag-aware shim at `0x008F5E30`. The older shim ignored flag `0x40`, so direct
injection appeared correct while the integrated payload squeezed the same
rows. This was a resident-hook difference, not a screenshot-composition
difference or a change in the Collection caller.

The corrected Movie-only branch now returns directly to the displaced native
draw when wrapping produces one line. When wrapping produces two lines, it
retains the proven 192-unit width, native X, Y-minus-10 origin calculation, and
16-unit line interval but does not publish the glyph-quad override. The fixed
right-edge shim now makes that clear flag effective. A supplied-ss8 regression
through the fixed shim reproduced the complete retained accepted right text
panel pixel-for-pixel.

The corrected character-detail branch uses the same separation. It retains
`glyph_height = 20.0` solely in `font_v2_prepare`'s two-line
`rendered_height` calculation, which preserves the accepted vertical centering,
but no longer publishes flag `0x40`; the glyph quads therefore remain native.
Fresh supplied-ss9 and ss10 direct-injection captures through the corrected
shim reproduce the accepted ss9 target and retained ss10 target exactly for
every text group. ss9 target/corrected bounds and dark/red glyph-pixel counts
are identical: `Right!` `(646,241)..(734,267)`, `Shadow Clone Jutsu`
`(648,296)..(871,345)`, and `Running Wild`
`(648,376)..(843,401)`. ss10 likewise matches exactly for
`Great Ball Rasengan`, `Overflowing Power`, `Nine-Tail's Cloak`, and
`Unchanging Relationship`. Non-text animation pixels may differ between fresh
frames; the text evidence is native-resolution. The user explicitly accepted
the ss9 target appearance on 2026-07-30; exact integrated-ISO confirmation of
the corrected payload remains pending.

The supplied ss8 state was reloaded through the standard task-owned direct-PINE
workflow after compiling the canonical C. The retained runtime-injected
candidate at
`work/Font/artifacts/priority5_movie_list/rework_2026-07-30/`
shows the four exact breaks above, native-height one-line rows, and native
glyph geometry on the wrapped rows. Its screenshot SHA-256 is
`E26CA0B3F66E413CE55EBA562C7760E6EF539CE6A6096D327D6006510E0391E5`;
the injected fragment SHA-256 is
`1BBA7F25F2CEB3E887B8AB101D36BAF80AD7B531667DC01566F657E1BE7DC06C`.
The user subsequently verified the exact integrated-ISO result on 2026-07-30.
Confidence is **verified** for the bounded Movie branch and runtime appearance;
status is **runtime proven**. The character-detail branch is
**runtime-injected candidate validated** with a user-accepted target and still
awaits exact integrated-ISO confirmation.


## Structural Collection-family completion

Evidence date: 2026-08-02.

Collection uses these relevant list families:

- ordinary characters: Figure, Ultimate Jutsu, and character-specific Music;
- legacy characters: Ultimate Jutsu only;
- Diorama;
- Movie;
- global Music;
- the Characters index where applicable.

Figure remains the only narrow character-detail list and uses the `152`-unit
profile. Relationship and Movie rows use the wider `192`-unit profile. The
Collection Opponents index uses that same wide profile at its exact native draw
X origin `30.0`; its child record stores doubled geometry at `60.0`, which is
not the renderer argument. All other target lists begin to the right of
`256.0`.
One shared ETC hook classifies them from native call geometry; no character,
row, or string whitelist remains. Fitting rows enter the same bounded renderer
session at the native family X and one-line Y `-4.0`, with zero tracking and
fixed horizontal scale `1.0`; they do not publish a glyph-height override, so
their native vertical glyph size remains unsquished. Only measured overflow
enters the two-line compositor. The complete Collection replay established
that the former `+1.2` X correction rasterized every target list one output
pixel too far right. Removing it corrected Figure, Movie, Music, Opponents,
Ultimate Jutsu, and Voice list rows as one structural family while leaving all
top-plaque character names on their separate centered adapter. The later
top-plaque analysis below supersedes the initial assumption that Figure/Music
and Ultimate Jutsu needed separate origin formulas.

The `font/music` E2E batch exposed why this session boundary must include
fitting one-line rows: the previous direct native-draw return measured with
NUN5 proportional metrics but retained NA2's extra renderer tracking, causing
progressive horizontal divergence and clipping the longest titles. Routing
those rows through the session removes only that tracking. Across all seven
paired captures, selected-row top and bottom bounds remain unchanged from the
pre-change NA2 captures; selected-row widths match NUN5 exactly or differ by
one antialiasing pixel. The complete normal/padded `font/music` replay passes.

Raw NUN5 ETC records are not safe byte donors: homologous list records assign
different meanings to fields at `+0x14/+0x18` and shift live resource fields.
Port NUN5 classification and layout semantics instead of entire records or
tables.

The Opponents family was added from the maintained 19-capture E2E set on
2026-08-13. Its unmodified English records prove that wrapping belongs to the
renderer rather than to stored newline bytes. In paired capture `0017`, the
NA2 list object at `0x00CE5C40` and NUN5 homolog at `0x00C1C450` both store
doubled list geometry X `60.0`, while their shared renderer is called at X
`30.0`. NUN5 stores a `192.0` by `32.0` text box at `+0x14/+0x18`, whereas NA2
stores live pointers in those fields. The structural port therefore classifies
only the exact native draw X `30.0` caller and applies the existing wide-list
layout instead of copying an incompatible donor object or matching individual
English strings. Official two-line results include `Granny Chiyo` / `(Taijutsu)`,
`Nine-Tailed Fourth` / `Awakened State`, `Naruto Uzumaki` / `(Nine-Tailed)`,
and selected Second Stage forms.

The earlier representative paired batch is retained at
`work/Font/inputs/sstates/batches/2026-07-31-collection-ss4-8/`, with hashes and
source aliases in `provenance.tsv`:

- ss4: Naruto character-specific Music;
- ss5: Naruto Classic Ultimate Jutsu;
- ss6: Diorama;
- ss7: global Music;
- ss8: Sasori ordinary-character Ultimate Jutsu.

Matching screenshots are under
`work/Font/inputs/screenshots/batches/2026-07-31-collection-ss4-8/`. That tree
also retains `character-index_NA228.png`; the earlier single-screen review
reported no large Font defect on the Characters index, so it remained
reference-only at that checkpoint. Synchronized final-red font2 cases 1-7
cover Sakura and legacy-character variants plus Movie without a large Font
defect; later desynchronized cases are excluded from evidence.


## Collection Characters selected-name boxed positioning

Evidence date: 2026-08-13.

The maintained `collection/characters` E2E suite provides 31 paired official
NUN5/current captures. In every original pair, the selected-name glyphs begin
at capture Y `394` in NUN5 and Y `402` in current NA2, while the surrounding
name plaque and portrait remain aligned. The names are also shifted right
relative to their NUN5 placement, by differing amounts across the complete
set. The initial candidate corrected only the uniform vertical delta. Matching
the top Y was insufficient: it retained NA2's incompatible point-centering and
therefore left every name horizontally misplaced inside the plaque.

The homologous ETC draw functions are NA2 exported `FUN_006B8210` and NUN5
exported `FUN_006CB310`. NA2's selected-name call is exported address
`0x006B832C`, runtime `0x006B836C`, file offset `0x446C`; its guarded bytes are
`90E40D0C00000000` (`jal 0x00379240` plus NOP). It passes the record origin plus
both half-extents to NA2's point-centered renderer. Live current state records
the half-extents as `95.0` and `16.0`. NUN5 instead calls its boxed renderer
`FUN_00385DF0` with the record's X origin, Y origin plus `4.0`, and the doubled
half-extents: a `190`-by-`32` box. That renderer measures each complete string,
centers the resulting extent within the plaque, and uses NUN5's tracking and
ordinary-space behavior.

The first candidate routed only the NA2 call at ETC file `0x446C` through a
Y-offset adapter. Subtracting `6.4` game units rasterized nine pixels upward and
one pixel above the reference; the corrected `5.6`-unit value moved it down one
output pixel and matched all 31 top Ys. It still called `FUN_00379240`, so that
result was rejected after visual review exposed the uncorrected horizontal
placement.

The replacement reconstructs the `190`-by-`32` plaque from NA2's midpoint
arguments and routes the selected name through the existing v2 layout
session. It uses the shared NUN5-compatible printable-ASCII measurement,
tracking-zero and ordinary-space behavior, centered horizontal alignment, and
shrink-only overflow handling, then performs one left-origin draw.

NUN5 first remaps the selected record ID before resolving its localized string.
For capture `0020`, the live record stores ID `24`; NUN5's remap row at
`0x006ED190` maps it to localized row `62`. English row `62` stores
`Granny Chiyo` as its primary pointer and `Granny Chiyo `, with a terminal
space, as the pointer returned to this caller. In NA2, ETC pointer field
`0x25A68` selects the shared Japanese slot at `0x251E0`; the other references
to that slot at `0x281DC`, `0x2AADC`, and `0x2D818` belong to different record
families and must retain the unpadded primary form.

The importer therefore keeps the ordinary inline mapping on exact NUN5 donor
`TEXTENG.BIN` `0x508` and links only ETC pointer field `0x25A68` to alias
`T2209`, whose exact donor is the secondary Collection string at `0x518`.
That donor includes the terminal space. Characters now calls the same shared
top-plaque adapter as the other non-Figurine families; no renderer wrapper
recognizes `Granny Chiyo`, changes its measured width, or otherwise branches on
displayed text.

The integrated global replay on 2026-08-13 passed all six Collection suites:
`characters` 31 captures, `opponents` 19, `misc` 22, `ultimates` 61, `voice`
31, and `figures` 43, for 207 captures total. In `characters`, the measured
selected-name glyph bounding boxes match the official reference exactly in X
and Y for all 31 cases. The exact secondary-record alias also makes capture
`0020` match in the Characters, Ultimate Jutsu, and Voice top plaques without
changing the other three users of the shared Japanese slot.

## Shared Collection character-name plaques

Evidence date: 2026-08-13.

The later full-family comparison establishes that the Characters result is not
a caller-specific positioning trick. NA2 uses point draw `FUN_00379240` for all
seven top-plaque branches in `FUN_006C11E0` and for the Music header in
`FUN_006C3020`. Their exact exported calls are `0x006C1374`, `0x006C14DC`,
`0x006C1638`, `0x006C173C`, `0x006C1870`, `0x006C19CC`, `0x006C1AC0`, and
`0x006C3178`; the injection file offsets are respectively `0xD4B4`, `0xD61C`,
`0xD778`, `0xD87C`, `0xD9B0`, `0xDB0C`, `0xDC00`, and `0xF2B8`.

NUN5's one-to-one homologs at exported `0x006D46E4`, `0x006D4864`,
`0x006D49D8`, `0x006D4AF4`, `0x006D4C40`, `0x006D4DB4`, `0x006D4EC0`, and
`0x006D6464` all call boxed renderer `FUN_00385DF0`. Record-backed branches
pass record X, record Y plus `4.0`, and twice the stored half-extents. The two
fixed `Opponent` branches pass X `30.0`, Y `72.0`, and the same doubled
half-extents. This is the same `190`-by-`32` centered, shrink-only contract as
the accepted Characters selected-name plaque.

The structural port routes every character-name homolog through one shared
plaque adapter. The common-Figurine character header at ETC
file `0x7640` is a ninth homolog and now uses that same adapter; its previous
fixed `+1.6/-5.0` direct-draw correction left all 31 names two output pixels
low and produced a string-width-dependent horizontal error. The adapter
reconstructs the box from NA2's
midpoint arguments, applies the accepted `-5.6` raster-origin correction,
measures with the NUN5-compatible zero-tracking metrics, centers the full
extent, and shrinks only overflow. Exact localized
record aliases own donor-specific string distinctions before rendering, so
there are no per-screen, per-character, or per-string layout exceptions in the
shared adapter.

The final global replay passed all 207 Collection captures. Before the exact
secondary-record alias, objective glyph-bound comparison found all captured
Opponent fields and all top-plaque names except `Granny Chiyo` aligned with
NUN5; after the alias, regenerated capture `0020` matches in Characters,
Ultimate Jutsu, and Voice as well. The later Figure replay replaces the stale
common-Figurine direct-origin result with the shared boxed layout above.

That corrective global replay on 2026-08-13 again passed all six suites and
all 207 captures. A dark-ink bound comparison over Figure captures `001`–`031`
found exact reference/current equality for left, top, right, and bottom in all
31 names. The complete 43-pair Figure grid was then reviewed; the shared name
change left captures `032`–`043` on their existing Diorama layout path.

## Collection Figures Diorama boxed titles

Evidence date: 2026-08-13.

The 12 maintained Diorama captures use NA2 exported draw function
`FUN_006BDD70` and NUN5 homolog `FUN_006D0F90`. NA2's title call at ETC file
offset `0xA31C` passes the record origin plus half-extents to the point-centered
`FUN_00379240`. NUN5 instead passes the record origin, Y plus `4.0`, doubled
half-extents, a two-line limit, and the selected title to boxed renderer
`FUN_0038A4F0`. Clean NUN5 boot-ELF data at `gp-0x4470` and `gp-0x446C`
contains half-width `95.0` and half-height `16.0`; the call doubles them before
entering the wrapper. The exact NUN5 title box is therefore `190` by `32`
units, not `200` by `40`.

The NA2 call is therefore routed through a bounded Font v2 adapter that
reconstructs the official horizontal box from the midpoint arguments, wraps
to at most two lines, centers the block and every individual line, and uses the
shared tracking-zero and ordinary-space measurement. The wrapper receives the
exact `190`-unit NUN5 width for both line breaking and shrink-only overflow;
its returned post-wrap maximum line width is also the draw scale denominator.
The family boundary is reproduced from the official titles and exact NUN5
logical measurements:
`Team Kurenai Unites`, the longest one-line title, measures `182`, while
`Naruto Returns Home`, the shortest wrapped title, measures `191`. The adapter
therefore reproduces NUN5's strict-overflow boundary directly rather than
selecting an empirical threshold between those strings. Its local vertical
layout remains `40` units tall, with a `16`-unit line advance and `22`-unit
layout glyph height. Those values affect placement only; no glyph-height
override is published, so the intentionally non-collapsed native height is
preserved instead of squeezing it to NUN5's nominal `32`-unit rectangle. The
non-collapsed raster requires a family-local Y correction of `-5` units for
one-line titles and no additional correction for wrapped titles. Every title
in the family uses the same structural renderer path; no title whitelist,
literal replacement text, or title-specific scale is involved.

The final global replay passed all 12 maintained Diorama captures. In capture
`0033`, `The Boar-Deer-Butterfly` and `Trio` now wrap and compact to the same
horizontal extents as NUN5. The current raster remains intentionally taller,
as required; the correction changes the official horizontal box and wrapping
contract rather than collapsing the font height.

## Collection Misc confirmation choices

Evidence date: 2026-08-13.

Maintained Misc captures `002` and `003` exercise both selected states of the
Collection exit selector. Cross-state differencing separates each glyph raster
from the translucent dialog and establishes that both Yes states were one
output pixel right and one output pixel low. The No X origin was already exact;
its unselected Y was exact, while its selected style was one output pixel high.

The existing confirmation mapper already scopes Collection through the
body-to-choice interval, so this does not introduce a screen- or string-based
hook. Collection Yes uses local origin `(63.2, 28.85)` and retains the shared
selected-style `-0.8` Y residual. Collection No retains `(68.1, 48.2)` and skips
that residual only while the Collection confirmation scope is active. Other
quit, return, Character Select, and Special Controls consumers retain their
existing geometry. The global replay passed both Misc captures with the four
Yes/No states aligned to the official reference.
