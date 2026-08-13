# Collection UI draw-path analysis

## Scope and binary identities

This record covers the Collection -> Characters title and page controls, the
Movie/Music titles and their shared Play control, and the four lower viewer
controls on the character-details screen. It was established on 2026-07-22
from paired NA2.28/NUN5 savestates, canonical files, and the existing Ghidra
exports; no new disassembly was required.

| Game | Canonical binary | Size | SHA-256 | MWo3 load base |
| --- | --- | ---: | --- | ---: |
| NA2 | `@source_na2/PRG/ETC.BIN` | 200,448 | `8FF3C6E1ED5CE2B093B0934C898C40D1CEEA0C20778C49CDA5591AAD02375C74` | `0x006B3F00` |
| NUN5 | `@source_nun5/PRG/ETC.BIN` | 171,776 | `BDB6BDA1F9D335047586A263E478486C8E7924B91FA972B6F3E58CAEC5EA0778` | `0x006C6D00` |
| NUN5 | `@source_nun5/SLES_556.05` | 5,340,912 | `20A43677397731A2A20899336D1165ACE5B436906B9B89BE90FB10F4558DD19D` | first `PT_LOAD` at `0x00100000` |

The reusable exports are
`@disassembly/NA2/exports/ETC.BIN/ETC.BIN.{c,txt}` and
`@disassembly/NUN5/exports/ETC.BIN/ETC.BIN.{c,txt}`. Those projects
map file offset zero 0x40 below the runtime addresses encoded by the MWo3
header, so an exported Ghidra function address is runtime address minus
`0x40`. The NUN5 boot-ELF export is
`@disassembly/NUN5/exports/SLES_556.05/SLES_556.05.{c,txt}`. Its
first load segment maps file offset `0x180` to runtime `0x00100000`, so the
localized title and Play records below have runtime address equal to file
offset plus `0xFFE80`. The canonical binary-patcher edits use file offsets
directly.

## Homologous class and draw methods

The paired live snapshots contain the following factory records and active
objects:

| Field | NA2 | NUN5 |
| --- | ---: | ---: |
| `ccHomeIspSelectChar` class string | `0x006E3070` | `0x006EF6E0` |
| factory record | `0x006028B0` | `0x0060FDD0` |
| type descriptor | `0x006E4BB8` | `0x006F0998` |
| destructor | `0x006C8EE0` | `0x006DC800` |
| initialize | `0x006B5810` | `0x006C8880` |
| update | `0x006B6E30` | `0x006C9ED0` |
| draw | `0x006B6F20` | `0x006C9FD0` |
| Ghidra draw name | `FUN_006b6ee0` | `FUN_006c9f90` |
| captured object | `0x00C744C0` | `0x00BF4230` |

In both captures, object offset `+0x08` points to the factory record,
`+0x0C` is state `1`, and `+0xC0` points to the reusable sprite renderer. The
draw-method pair first dispatches the state-specific Collection character-grid
renderer and then, for states other than 0, 3, and 4, draws the two page
controls. The state-1 callees are NA2 `FUN_006b6390` and NUN5
`FUN_006c9450`; the other states use NA2 `FUN_006b68d0` and NUN5
`FUN_006c9980`. The page controls then call the common sprite routines
`SUB_0037bc40` / `SUB_0038ad00` and finish through `SUB_001cc070` /
`SUB_001d1180`.

A practical reconstruction of the stable part is:

```c
typedef struct { float x, y, z, w; } PagePromptPosition;
typedef struct { uint16_t u, v, width, height; } PagePromptRect;

void draw_collection_character_select(CollectionCharacters *self) {
    draw_state_specific_content(self);
    if (self->state != 0 && self->state != 3 && self->state != 4) {
        for (unsigned i = 0; i < 2; ++i) {
            draw_sprite(page_prompt_position[i].x,
                        page_prompt_position[i].y,
                        self->page_prompt_renderer,
                        &page_prompt_rect[i]);
        }
        finish_sprite(self->page_prompt_renderer);
    }
}
```

The first array entry is `Previous Page`; the second is `Next Page`. The draw
path is read-only with respect to Collection state. Its observable side effect
is submitting two sprites through the shared renderer.

## Collection category-title helper

The title uses a second homologous helper pair:

- NA2 `FUN_006c7c30` (runtime `0x006C7C70`) passes the requested category
  index to the static ETC rectangle array at runtime `0x006E4390` and the
  position array at `0x006E2F20`.
- NUN5 `FUN_006db410` (runtime `0x006DB450`) obtains the localized rectangle
  from boot-ELF accessor `FUN_003d4170` and uses the position array at
  `0x006EF570`.
- `FUN_003d4170` reads the locale index through `FUN_003d4110`, selects a base
  from pointer table `0x005BB2D0`, and returns `base + index * 8`. In the
  captured NUN5 state, locale 0 points to `0x005DDAD0`, whose file-backed
  source begins at NUN5 ELF offset `0x4DDC50`.

All three placement records are byte-identical across the games:
`(305,13,0,0)`, `(340,13,0,0)`, and `(345,23,0,0)`. No category-title
placement patch is justified. The source rectangles differ:

| Category | NA2 ETC record | NUN5 localized ELF record | Paired-screen effect |
| --- | --- | --- | --- |
| Characters | `(1,1,192,34)` | `(0,0,192,28)` | NA2 samples six pixels of the Movie row. |
| Movie | `(1,37,136,34)` | `(0,28,96,28)` | NA2 samples the Music row beneath Movie. |
| Music | `(1,83,80,37)` | `(0,56,96,28)` | NA2 starts below the imported Music row, so the title is absent. |

The imported NUN5 `home03` atlas stores those English labels as consecutive
28-pixel rows. Paired Characters, Movie, and Music states therefore justify
copying all three localized rectangles while retaining the already-matching
positions.

## Shared Play prompt helper

The Movie and Music screens call the common HOME action-prompt compositor:

- NA2 `FUN_006b44b0` uses ETC static rectangle `0x006E2690` when its state
  argument is `2`.
- NUN5 homolog `FUN_006c7250` calls boot-ELF accessor `FUN_003d4210(0)` for
  the same state. `FUN_003d4210` selects a locale base through pointer table
  `0x005BB310`; locale 0 points to `0x005DDAF0`, backed by ELF offset
  `0x4DDC70`.

A practical reconstruction of the relevant branch is:

```c
void draw_home_action_prompt(Sprite *icon, Sprite *label, int state) {
    if (state == 2) {
        draw_button_icon(icon);
        draw_sprite(label, localized_play_rect);
    } else if (state == 4) {
        draw_button_icon(icon);
        draw_sprite(label, localized_stop_rect);
    }
    finish_sprite(icon);
    finish_sprite(label);
}
```

NA2's Play record is `(120,24,72,24)`, while the NUN5 HOME atlas and localized
record use `(144,24,72,24)`. The 24-pixel U-coordinate mismatch produces the
captured `Pl...` clipping on both Movie and Music. The later paired ss10 Music
capture reviews the adjacent state-4 Stop record as well: NA2 uses
`(120,48,72,24)`, while NUN5 uses `(144,48,76,24)`.

## Collection state footer positions

The Collection state renderer owns another pair of Cross/Triangle prompt
positions. It is separate from the HOME action-prompt helper above:

| Field | NA2 | NUN5 |
| --- | --- | --- |
| exported function range | `FUN_006c8290`, `[0x006C8290,0x006C8900)` | `FUN_006dbaa0`, `[0x006DBAA0,0x006DC200)` |
| file range | `[0x14390,0x14A00)` | `[0x14DA0,0x15500)` |
| position table file/live | `0x2F010` / `0x006E2F10` | `0x28860` / `0x006EF560` |
| nominal positions | `(380,360)`, `(460,360)` | `(380,360)`, `(460,360)` |
| effective X | `380`, `460` | `380-12=368`, `460-8=452` |
| sprite compositor | `SUB_0037c980` | `SUB_0038bb10` |

Both state switches copy the same two nominal position records to the stack
and submit one or both prompts according to the active Collection state. NUN5
then converts two signed regional globals and adds `-12` to the first X and
`-8` to the second X before the compositor calls. NA2 has neither addition.
A practical reconstruction of the localized behavior is:

```cpp
void draw_collection_state_footer(CollectionState *state) {
    PromptPosition first = collection_footer_position[0];
    PromptPosition second = collection_footer_position[1];
    first.x += regional_cross_offset;     // NUN5 English locale: -12
    second.x += regional_triangle_offset; // NUN5 English locale: -8
    draw_state_prompts(state, first, second);
}
```

The NUN5 table is byte-identical to NA2, so copying donor bytes cannot port the
behavior. `ui_layout_common_prompts` instead stores the equivalent effective X values
`368` (`0000B843`) and `452` (`0000E243`) at NA2 ETC offsets `0x2F010` and
`0x2F018`; the Y values and every other state field remain unchanged. A
guarded task-owned Slot 2 savestate and hidden worker render moved both
Collection-root prompt groups to the NUN5 positions. Image correlation found
only a one-pixel X/Y difference, consistent with the known pulse timing.

The byte-identical NA2 table at `0x2E7E0` is not the Slot 2 consumer. Patching
it or redirecting its owner `FUN_006b44b0` therefore left Slot 2 unchanged
under both recompiler and interpreter execution. That negative result is
screen-specific: the later Slot 3 Music capture proves that the same HOME
helper and table own a different shared action footer, documented below.

## HOME action footer and localized state geometry

Collection Music exposes a second shared footer implementation whose nominal
table matches the Collection-root values but whose state behavior differs.
The evidence uses clean, hash-pinned NA2 `ETC.BIN`
`8FF3C6E1...02375C74`, official NUN5 `ETC.BIN`
`BDB6BDA1...C5EA0778`, their maintained Ghidra exports, and guarded writes to
the task-owned paired Slot 3 state.

| Field | NA2 | NUN5 |
| --- | --- | --- |
| preserved helper | `FUN_006b44b0`, `[0x006B44B0,0x006B46B0)` | `FUN_006c7250`, `[0x006C7250,0x006C75E0)` |
| prompt table file/load address | `0x2E7E0` / `0x006E26E0` | `0x28070` / `0x006EED70` |
| nominal positions | `(380,360)`, `(460,360)` | `(380,360)`, `(460,360)` |
| common compositor | `SUB_0037c980` | `SUB_0038bb10` |
| state 1 effective X | `380` | `380-12=368` |
| state 2 effective X | `380` | `380-44+56-(72/2)=356` |
| state 3 effective X | `460` | `460-8=452` |
| state 4 prompt X | `460` | `460+(76-64)/2-8=458` |
| state 4 label X | `460-35=425` | `458-(76/2)=420` |

The official NUN5 helper reads signed regional globals for states 1 and 3.
State 2 instead asks the localized rectangle accessor for its 72-pixel width
and centers the pair with `(x - 44 + 56) - width/2`. Its paired label position
uses the same calculation plus the existing `-35` local offset, yielding
`321`. NA2 has no language globals or rectangle accessors in this helper and
calls its compositor at the unadjusted anchors; its label therefore starts at
`380-35=345`.

A practical reconstruction of the port is:

```cpp
void draw_home_action_prompt(HomePromptState state) {
    float icon_x = state == CROSS ? 380.0f - 12.0f
                 : state == PLAY  ? 380.0f - 24.0f
                 : state == BACK  ? 460.0f - 8.0f
                 : /* STOP */       460.0f - 2.0f;
    draw_common_prompt(icon_x, original_y, state);

    if (state == PLAY) {
        draw_label_at(380.0f - 59.0f, original_label_y);
    } else if (state == STOP) {
        draw_label_at(460.0f - 40.0f, original_label_y);
    }
}
```

`ui_layout_common_prompts` implements this once for every caller of the NA2 helper:

- ETC file `0x30`, load address `0x006B3F30`: replace 16 zero padding bytes
  retained in the loaded MWO3 image with a four-instruction wrapper. It moves
  a caller-supplied float delta from `v1` to `f0`, adds it to `f12`, and
  tail-calls NA2's existing compositor.
- ETC file/load `0x6B0` / `0x006B45B0`: state 1 redirects through the wrapper
  with `-12.0`.
- ETC file/load `0x6D4` / `0x006B45D4`: state 2 redirects through the wrapper
  with `-24.0`.
- ETC file/load `0x738` / `0x006B4638`: state 3 redirects through the wrapper
  with `-8.0`.
- ETC file/load `0x2E7F0` / `0x006E26F0`: state 2 changes only its first
  label-local X offset from `-35.0` to `-59.0`.
- ETC file `0x2E798`: copy the exact NUN5 localized Stop rectangle
  `(144,48,76,24)` from SLES file `0x4DDC78` over NA2's
  `(120,48,72,24)` rectangle.
- ETC file/load `0x764` / `0x006B4664`: state 4 redirects through the same
  wrapper with `-2.0`, the exact result of NUN5's
  `(76-64)/2-8` centering arithmetic.
- ETC file/load `0x2E7F8` / `0x006E26F8`: state 4 changes its label-local X
  offset from `-35.0` to `-40.0`, reproducing NUN5 label X=`420`.

The NUN5 helper code itself is not a safe byte donor: it calls different
language accessors and reads build-specific GP-relative regional globals.
The wrapper is therefore an authored ABI-preserving port of the verified NUN5
arithmetic. The pristine zero range, all four call guards, and both data guards
were confirmed in the clean source and task-owned states. The guarded Slot 3
Music render aligns Play and Back with the official NUN5 capture. A newer
paired Slot 2 Collection Characters state independently passed the five
earlier guards; applying the already-canonical helper rows aligned its OK/Back
groups with NUN5 without any new binary edit. The ss10 Stop extension is
verified from the owned paired state, live NUN5 English regional offsets
`-12`/`-8`, live 64-pixel Triangle and 76-pixel Stop records, and the bounded
homologous helper disassembly. A guarded task-owned runtime state with the
three exact canonical edits renders the complete Triangle/Stop group at the
NUN5 footer anchor while leaving Cross/Play unchanged. The user explicitly
accepted that final ss10 comparison on 2026-07-27. Confidence is high for the
shared helper arithmetic.

Useful negative result: changing only the nominal `0x2E7E0` table cannot
express the helper's three distinct `-12`, `-24`, and `-8` state deltas. The
earlier original Slot 2 Collection-root failure of this path proved only that
that screen uses `FUN_006c8290` and the separate `0x2F010` table; it did not
disprove the HOME helper for actual consumers such as Collection Music and
Collection Characters.

## Character viewer lower-control renderer

The new paired slot-1 capture shows only the four lower-left viewer controls as
defective. NA2 lays `Zoom In`, `Zoom Out`, `Move`, and `Rotate` across one
bottom row, causing the imported English labels to collide and clip. NUN5 uses
the same four semantic records in a two-by-two layout. `Back`, the model, and
all name/jutsu text are separate accepted paths and are outside this edit.

The exact homologous renderer pair is:

| Field | NA2 | NUN5 |
| --- | ---: | ---: |
| exported function range | `FUN_006bafc0`, `[0x006BAFC0,0x006BB550)` | `FUN_006ce150`, `[0x006CE150,0x006CE700)` |
| runtime range | `[0x006BB000,0x006BB590)` | `[0x006CE190,0x006CE740)` |
| position table | file `0x2EB40`, runtime `0x006E2A40` | file `0x283D0`, runtime `0x006EF0D0` |
| rectangle table | file `0x30AB0`, runtime `0x006E49B0` | file `0x29A90`, runtime `0x006F0790` |
| sprite draw callee | `SUB_0037bc40` | `SUB_0038ad00` |
| finish callee | `SUB_001cc070` | `SUB_001d1180` |

Both functions copy the four 16-byte position records to their stack, iterate
four times over paired position/rectangle records, submit a sprite, and finish
the shared renderer. Their observable side effect is renderer submission; they
do not mutate Collection selection state. A practical reconstruction is:

```c
typedef struct { float x, y, z, w; } ViewerControlPosition;
typedef struct { uint16_t u, v, width, height; } ViewerControlRect;

void draw_collection_viewer_controls(CollectionViewerOverlay *self) {
    for (unsigned i = 0; i < 4; ++i) {
        draw_sprite(viewer_control_position[i].x,
                    viewer_control_position[i].y,
                    self->sprite_renderer,
                    &viewer_control_rect[i]);
    }
    finish_sprite(self->sprite_renderer);
}
```

The record order is Rotate, Move, Zoom In, Zoom Out. NA2 uses positions
`(344,360)`, `(232,360)`, `(66,360)`, `(148,360)`. NUN5 uses
`(206,364)`, `(99,364)`, `(97,339)`, `(207,339)`, which produces bottom-row
Move/Rotate and top-row Zoom In/Zoom Out exactly as seen in the paired capture.
The first two rectangles are already identical. NUN5 widens the two Zoom
records from 108 to 112 pixels and moves Zoom Out's U coordinate from 120 to
144 for its English atlas location.

The parent character-viewer class aligns as `ccHomeIspDiorama`: NA2 exported
class-string address `0x006E2FE0`, exported factory/type reference
`0x00602820`, captured object `0x00CE5E40`; NUN5 exported
class-string address `0x006EF650`, exported reference `0x0060FD40`, and
captured object `0x00C1C810`. Its main draw pair is NA2
`FUN_006c11e0` and NUN5 `FUN_006d4530`. The lower-control renderer is reached
indirectly as a child/virtual overlay draw; no direct JAL cross-reference is
present in the exports. A second pair, NA2 `FUN_006bdaa0` and NUN5
`FUN_006d0d10`, consumes the same four rectangle records with a different
caller-provided position array. The later maintained Diorama captures provide
that second consumer's screen evidence, so its complete homologous position
table is now copied. Confidence is high for the table/function semantics and
medium for the exact indirect parent edge.

## Exact paired tables

| Table | NA2 file/runtime | NA2 values | NUN5 file/runtime | NUN5 values |
| --- | --- | --- | --- | --- |
| centers | `0x2E930` / `0x006E2830` | `(100,360,0,0)`, `(220,360,0,0)` | `0x281C0` / `0x006EEEC0` | `(87,360,0,0)`, `(233,360,0,0)` |
| atlas rectangles | `0x30A80` / `0x006E4980` | `(1,1,118,24)`, `(1,24,118,24)` | `0x29A60` / `0x006F0760` | `(1,1,144,24)`, `(1,24,144,24)` |
| Characters rectangle | `0x30490` / `0x006E4390` | `(1,1,192,34)` | NUN5 ELF `0x4DDC50` / `0x005DDAD0` | `(0,0,192,28)` |
| Movie rectangle | `0x30498` / `0x006E4398` | `(1,37,136,34)` | NUN5 ELF `0x4DDC58` / `0x005DDAD8` | `(0,28,96,28)` |
| Music rectangle | `0x304A0` / `0x006E43A0` | `(1,83,80,37)` | NUN5 ELF `0x4DDC60` / `0x005DDAE0` | `(0,56,96,28)` |
| Play rectangle | `0x2E790` / `0x006E2690` | `(120,24,72,24)` | NUN5 ELF `0x4DDC70` / `0x005DDAF0` | `(144,24,72,24)` |
| Stop rectangle | `0x2E798` / `0x006E2698` | `(120,48,72,24)` | NUN5 ELF `0x4DDC78` / `0x005DDAF8` | `(144,48,76,24)` |
| viewer-control positions | `0x2EB40` / `0x006E2A40` | `(344,360)`, `(232,360)`, `(66,360)`, `(148,360)` | `0x283D0` / `0x006EF0D0` | `(206,364)`, `(99,364)`, `(97,339)`, `(207,339)` |
| Diorama viewer-control positions | `0x2EBD0` / `0x006E2AD0` | `(440,290)`, `(440,266)`, `(469,218)`, `(468,242)` | `0x28460` / `0x006EF160` | `(440,290)`, `(440,266)`, `(440,218)`, `(440,242)` |
| viewer-control rectangles | `0x30AB0` / `0x006E49B0` | `(1,72,108,24)`, `(1,48,108,24)`, `(1,96,108,24)`, `(120,1,108,23)` | `0x29A90` / `0x006F0790` | `(1,72,108,24)`, `(1,48,108,24)`, `(1,96,112,24)`, `(144,1,112,23)` |

The whole NUN5 `HOME.CCS` donor supplies 144-pixel English page-prompt art,
but it cannot change these ETC-owned tables. NA2 therefore clipped the first
rectangle to 118 pixels, displaying `Previous Pa`. NUN5 widens both entries to
144 and moves their centers outward by 13 pixels, preserving the paired layout
without overlap. `ui_layout_collection_submenu` consequently copies both complete page-prompt
tables, all three reviewed category-title records, and the reviewed Play
record. The viewer-control correction copies the complete four-record position
and rectangle blocks rather than splitting their semantic unit. It contains no
authored replacement bytes and changes no text or font data.

The Diorama viewer supplies the later screen evidence for the second position
consumer. Its homologous NUN5 table keeps all four records at X `440`; NA2's
last two X values, `469` and `468`, clip Zoom In and Zoom Out at the right edge.
The complete 64-byte second table is therefore copied as one semantic block.

NUN5 also stopped using the shared `ANM_home_vcr_ca` animation record for the
viewer-state prompt. Its localized accessor selects three official English
HOME-atlas rectangles: Controls `(144,72,112,24)`, Hide `(208,96,48,24)`, and
Display `(132,96,76,24)`. The Diorama draw adapter ports those exact records
and NUN5's exact `(374,309)` and `(414,324)` positions into NA2's compatible
sprite helper. This prevents the imported NUN5 HOME container from resolving
NA2's substring animation references as the malformed `Cisplay` label.

The viewer-state handler pair is NA2 `FUN_006bd740` and NUN5
`FUN_006d0980`; both store the visible/hidden flag at object offset `+0xB8`.
NA2 tests masks `0x40` and `0x10` at ETC file offsets `0x9894` and `0x990C`;
NUN5 tests `0x10` and `0x80` at `0x9CD4` and `0x9D4C`. Both exact NUN5
instructions are required: the first changes Back from Cross to Triangle, and
the second changes the visibility toggle to Square. Removing the first returns
the replay to the Characters list before Misc capture `020`; removing the
second leaves controls visible at capture `022`. The retained pre-fix state
proves the complete pair: its current object has `+0xB8 = 0`, matching NUN5,
while its image still shows the malformed Display substring. A disposable
probe around movie frames `6683` through `6695` further observes the Square
edge as action bit `0x80` and the `+0xB8` transition. The two former
`unclassified` copies are therefore retained as separately named, documented
Collection Diorama edits rather than treated as a blind regional family.

Controls/Hide and Display are separate call sites in the handler's draw pair.
They consequently use separate adapters: the shared visible-state adapter
selects the official Controls or Hide record from the native call position,
while the hidden-state adapter selects the official Display record directly.
Treating all suffix calls as Hide made a correctly hidden state impossible to
label faithfully.

The nine guarded copy operations cover 240 bytes; thirty-three bytes differ in
the destination.

The captured sprite renderer corroborates the table trace. After the second
draw, its width is 118 in NA2 and 144 in NUN5; its derived right-edge value is
respectively `220 + 118 = 338` and `233 + 144 = 377`.

## Evidence and negative results

- Paired slot-1 state hashes are
  `87CDE7ABEA8DE6DADAA98D30BA2B749B3E23B0B4D25D221812FE0394D8FAC4F2`
  (NA2.28) and
  `3033EF799CE55882F5363C5A7CF7D6C567456A102688B1D64C02921EDDD6E19A`
  (NUN5). Their embedded screenshot hashes are
  `61E60F6FB91C8B200FB00669FC4A706BF1BE29ED214CFBDF9C5233426236E1A3`
  and `B7DF3E9B4333E068336531E2073796B2CF72AC08A31ABED88DBD71144EE7163B`.
  The retained working copies remain under
  `work/UI translation/temp/slot1_20260722_063419/` until runtime acceptance.
- The paired Movie state hashes are
  `0C35717E24EA1827FAB6A364969A13FAC82FD5CAB0D89471E368FA3A4B7F864D`
  (NA2.28) and
  `2912E06CF87386BAED5D5C49BC51B942B7B1188189F90BDE4DDEB87D43D4A6CA`
  (NUN5); their embedded screenshot hashes are
  `5F1C093B41E6F91B52A5A0CC8A7762CB118D462CAAED77BB67554CCE1648E82A`
  and `73D0038806B059A5F48ED99034E785055AC8847C809EC122E5450AE1341B502A`.
  The paired Music state hashes are
  `67276DBD1751A692056A1AE0C58FE3C399B1C9C9570DC8107840184F83B48332`
  and `FF8DBB088BF28405E749510F5E547886CD673A6E7DB9E35AA8C560EE98F540D6`;
  their screenshot hashes are
  `754BBB6F4F7E5041E6DE1A8614123E94DA6F8B8FED5D91CE1B1FA27F14558035`
  and `47226A13B272A6532798F27CC22D0F41290E596A122DD5854F385839F876687E`.
  Their retained copies are under
  `work/UI translation/temp/slots2_3_20260722_0745/` until runtime acceptance.
- The later paired character-viewer slot-1 state hashes are
  `7A90746FC65D62F2027F11AFEB3847FCBEAB92C5FF797C60C33904698814CAD9`
  (NA2.28) and
  `9748C0801572E6DE00D03EBF39DC9AE28540EAECE10EC1D52D1ED4C7955FFE3F`
  (NUN5). Their embedded screenshot hashes are
  `97451AFCF15483D9D1A7DDA232EFE48F2F2C5697A740D730D12A47556C7F02FB`
  and `981AC4171CFC7B54D56326616E90EEB8AAE7D03C639CF8A62980E26BB9DFD14B`;
  extracted EE-memory hashes are
  `9E8DDA2E5C8511178DAE758606BB13D7FB18117AF16F5119CFDA2EE4F6827532`
  and `9BC30D17F76EC79E172AC373880742CEB8EFC0BB0ADA04D3016192AD46CA994B`.
  Working copies remain under
  `work/UI translation/temp/slot1_20260722_0827_down_labels/` until runtime
  acceptance; the original PCSX2 states were not modified.
- The isolated eight-edit `ui_layout_collection_submenu` apply preserves the 200,448-byte ETC
  size and produces SHA-256
  `E6054FCD42A3834197AE638D3EF77E10BE86633A997C6CF9F18887FA788A298A`.
  Exactly 30 bytes differ from canonical NA2 ETC, all inside the declared
  ranges. The adjacent Stop record at `0x2E798` remains `(120,48,72,24)`;
  Back and every text/font byte remain outside the patch. Package validation
  reports 7 targets, 9 groups, 86 patches, and 252 edits; the 33 focused
  UI/profile tests and full 127-test suite pass. The matching Localization
  feature pin at that checkpoint was
  `CF173194E0BB28DB3CC516B176DB9F90F1103749890F5EE4AF6BD6CCC9CBDB56`.
- A historical NA2 screenshot from the preserved Previous ISO has the same
  clipping, so this defect predates the current donor conversion.
- All three title placement records are identical across NA2 and NUN5.
  Patching title coordinates would be unsupported; the visible fragments and
  missing Music label come from the NA2 source rectangles.
- `TEXTENG.BIN` does not own texture rectangles or placement for this path.
- NA2 `FUN_006b44b0` / NUN5 `FUN_006c7250` and the NUN5 localized accessor
  `FUN_003d4210` do not draw the Previous/Next Page controls. They are the
  separate common Play/Stop prompt family, and their state-2 Play branch is
  now covered by `ui_layout_collection_submenu`.
- NA2 `FUN_006b7c30` / NUN5 `FUN_006cad20` and accessor `FUN_003d41c0`
  render character-grid selection markers, not page controls.
- Searching for an isolated `(0,0,144,24)` rectangle was a false boundary:
  the authoritative records are the two `(1,v,144,24)` entries referenced by
  the homologous draw loops.
- Movie/Music list wording, wrapping, and font spacing differ in the paired
  screenshots, but they are text-rendering behavior rather than HOME texture
  rectangles and remain outside this texture-only correction.
- The original submenu captures did not expose the Controls/Display/Hide
  prompt records. The later maintained Diorama family does: its twelve paired
  captures establish the official localized records, both viewer states, and
  their positions without extending the earlier submenu inference.
- The accepted `Back` prompt is drawn by the common action-prompt family, not
  the four-item viewer-control renderer, and remains untouched.
- The second four-rectangle consumer `FUN_006bdaa0` / `FUN_006d0d10` uses a
  different position source. The maintained Diorama captures now demonstrate
  its defect, and the complete homologous NUN5 table is applied as described
  above.

## Confidence

**High, static, paired-memory, and E2E proven; batch user acceptance pending.** The
class factories, state, draw functions, localized accessors, exact
source/destination ranges, table semantics, and paired visual failures all
agree across canonical binaries and captured memory. The global Collection E2E
candidate `20260813_053803_998_pid39812.iso` passed all six suites; the complete
43-capture Figures and 22-capture Miscellaneous artifact sets were reviewed.
The only uncompleted evidence is the user's planned batch visual review after
every Collection section is finished.
