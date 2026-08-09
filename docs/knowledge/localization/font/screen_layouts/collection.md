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
profile. Relationship and Movie rows use the wider `192`-unit profile. One
shared ETC hook classifies them from native call geometry; no character, row,
or string whitelist remains. Fitting rows enter the same bounded renderer
session at family X `+1.2` and one-line Y `-4.0`, with zero tracking and fixed
horizontal scale `1.0`; they do not publish a glyph-height override, so their
native vertical glyph size remains unsquished. Only measured overflow enters
the two-line compositor. Figure/Music character headers share one origin
formula, and ordinary/legacy Ultimate Jutsu headers share another.

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
also retains `character-index_NA228.png`; the user reported no Font defect on
the Characters index, so it remains reference-only. Synchronized final-red
font2 cases 1-7 cover Sakura and legacy-character variants plus Movie without a
large Font defect; later desynchronized cases are excluded from evidence.
