# Collection UI draw-path analysis

## Research coverage

- **Assigned scope:** compare clean NA2 and NUN5 Collection title, prompt, footer, and viewer draw paths.
- **Exploration depth:** the relevant binaries, native callers, records, and
  paired screen states were examined.
- **Confirmed coverage:** the documented owners, structures, and cross-game
  differences are established.
- **Unresolved or untested:** callers and states not explicitly covered below.
- **Deliberate exclusions and overlap:** feature imports, hooks, and validation
  belong to [UI layout](../../../features/localization/ui_layout.md) or
  [UI textures](../../../features/localization/ui_textures.md).
- **Evidence limitations:** bounded states do not cover every animation phase or
  indirect caller.

## Scope and binary identities

This record covers the Collection -> Characters title and page controls, the
Movie/Music titles and their shared Play control, and the four lower viewer
controls on the character-details screen. It was established from paired
NA2.28/NUN5 runtime states, canonical files, and the existing Ghidra
exports; no new disassembly was required.

The clean input identities and load mappings are listed in
[Standard game file identities](../../game/files/file_identities.md).

| Game | Canonical binary | Size |
| --- | --- | ---: |
| NA2 | `@source_na2/PRG/ETC.BIN` | 200,448 |
| NUN5 | `@source_nun5/PRG/ETC.BIN` | 171,776 |
| NUN5 | `@source_nun5/SLES_556.05` | 5,340,912 |

The reusable exports are
`@disassembly/NA2/exports/ETC.BIN/ETC.BIN.{c,txt}` and
`@disassembly/NUN5/exports/ETC.BIN/ETC.BIN.{c,txt}`. Those projects
map file offset zero 0x40 below the runtime addresses encoded by the MWo3
header, so an exported Ghidra function address is runtime address minus
`0x40`. The NUN5 boot-ELF export is
`@disassembly/NUN5/exports/SLES_556.05/SLES_556.05.{c,txt}`. Its
first load segment maps file offset `0x180` to runtime `0x00100000`, so the
localized title and Play records below have runtime address equal to file
  offset plus `0xFFE80`.

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

| Category | NA2 ETC record | NUN5 localized ELF record | Paired-screen effect |
| --- | --- | --- | --- |
| Characters | `(1,1,192,34)` | `(0,0,192,28)` | NA2 samples six pixels of the Movie row. |
| Movie | `(1,37,136,34)` | `(0,28,96,28)` | NA2 samples the Music row beneath Movie. |
| Music | `(1,83,80,37)` | `(0,56,96,28)` | NA2 starts below the NUN5 Music row, so the title is absent. |

The NUN5 `home03` atlas stores those English labels as consecutive 28-pixel
rows. The paired states establish that the positions already match and the
rectangle rows differ.

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
captured `Pl...` clipping on both Movie and Music. A later paired Music
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

## HOME action footer and localized state geometry

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

The NUN5 behavior reduces to:

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

Useful negative result: changing only the nominal `0x2E7E0` table cannot
express the helper's three distinct `-12`, `-24`, and `-8` state deltas. The
earlier Collection-root failure of this path proved only that
that screen uses `FUN_006c8290` and the separate `0x2F010` table; it did not
disprove the HOME helper for actual consumers such as Collection Music and
Collection Characters.

## Character viewer lower-control renderer

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
caller-provided position array. Paired Diorama captures confirm that second
consumer and its homologous position table. Confidence is high for the
table/function semantics and medium for the exact indirect parent edge.

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

The Diorama viewer supplies the later screen evidence for the second position
consumer. Its homologous NUN5 table keeps all four records at X `440`; NA2's
last two X values, `469` and `468`, clip Zoom In and Zoom Out at the right edge.
The four entries form one semantic position table rather than independent
constants.

NUN5 does not use the shared `ANM_home_vcr_ca` animation record for the
viewer-state prompt. Its localized accessor selects three English HOME-atlas
rectangles: Controls `(144,72,112,24)`, Hide `(208,96,48,24)`, and Display
`(132,96,76,24)`, drawn at `(374,309)` and `(414,324)`. NA2's substring
animation references instead resolve the suffix as the malformed `Cisplay`
label against that atlas.

Controls/Hide and Display are separate call sites in the handler's draw pair.
The visible-state call selects Controls or Hide, while the hidden-state call
selects Display.

The captured sprite renderer corroborates the table trace. After the second
draw, its width is 118 in NA2 and 144 in NUN5; its derived right-edge value is
respectively `220 + 118 = 338` and `233 + 144 = 377`.
