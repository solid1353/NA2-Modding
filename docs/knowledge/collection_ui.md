# Collection UI draw-path analysis

## Scope and binary identities

This record covers the Collection -> Characters title and page controls plus
the Movie/Music titles and their shared Play control. It was established on
2026-07-22 from paired NA2.28/NUN5 savestates, canonical files, and the
existing Ghidra exports; no new disassembly was required.

| Game | Canonical binary | Size | SHA-256 | MWo3 load base |
| --- | --- | ---: | --- | ---: |
| NA2 | `@source_na2/PRG/ETC.BIN` | 200,448 | `8FF3C6E1ED5CE2B093B0934C898C40D1CEEA0C20778C49CDA5591AAD02375C74` | `0x006B3F00` |
| NUN5 | `@source_nun5/PRG/ETC.BIN` | 171,776 | `BDB6BDA1F9D335047586A263E478486C8E7924B91FA972B6F3E58CAEC5EA0778` | `0x006C6D00` |
| NUN5 | `@source_nun5/SLES_556.05` | 5,340,912 | `20A43677397731A2A20899336D1165ACE5B436906B9B89BE90FB10F4558DD19D` | first `PT_LOAD` at `0x00100000` |

The reusable exports are
`@analysis/disassembly/NA2/exports/ETC.BIN/ETC.BIN.{c,txt}` and
`@analysis/disassembly/NUN5/exports/ETC.BIN/ETC.BIN.{c,txt}`. Those projects
map file offset zero 0x40 below the runtime addresses encoded by the MWo3
header, so an exported Ghidra function address is runtime address minus
`0x40`. The NUN5 boot-ELF export is
`@analysis/disassembly/NUN5/exports/SLES_556.05/SLES_556.05.{c,txt}`. Its
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
captured `Pl...` clipping on both Movie and Music. Only the reviewed Play
record is copied. The adjacent state-4 Stop record remains unchanged.

## Exact paired tables

| Table | NA2 file/runtime | NA2 values | NUN5 file/runtime | NUN5 values |
| --- | --- | --- | --- | --- |
| centers | `0x2E930` / `0x006E2830` | `(100,360,0,0)`, `(220,360,0,0)` | `0x281C0` / `0x006EEEC0` | `(87,360,0,0)`, `(233,360,0,0)` |
| atlas rectangles | `0x30A80` / `0x006E4980` | `(1,1,118,24)`, `(1,24,118,24)` | `0x29A60` / `0x006F0760` | `(1,1,144,24)`, `(1,24,144,24)` |
| Characters rectangle | `0x30490` / `0x006E4390` | `(1,1,192,34)` | NUN5 ELF `0x4DDC50` / `0x005DDAD0` | `(0,0,192,28)` |
| Movie rectangle | `0x30498` / `0x006E4398` | `(1,37,136,34)` | NUN5 ELF `0x4DDC58` / `0x005DDAD8` | `(0,28,96,28)` |
| Music rectangle | `0x304A0` / `0x006E43A0` | `(1,83,80,37)` | NUN5 ELF `0x4DDC60` / `0x005DDAE0` | `(0,56,96,28)` |
| Play rectangle | `0x2E790` / `0x006E2690` | `(120,24,72,24)` | NUN5 ELF `0x4DDC70` / `0x005DDAF0` | `(144,24,72,24)` |

The whole NUN5 `HOME.CCS` donor supplies 144-pixel English page-prompt art,
but it cannot change these ETC-owned tables. NA2 therefore clipped the first
rectangle to 118 pixels, displaying `Previous Pa`. NUN5 widens both entries to
144 and moves their centers outward by 13 pixels, preserving the paired layout
without overlap. `UI-ETC-002` consequently copies both complete page-prompt
tables, all three reviewed category-title records, and the reviewed Play
record. It contains no authored replacement bytes and changes no text or font
data. The six guarded copy operations cover 80 bytes; only sixteen bytes
differ in the destination.

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
- The isolated `UI-ETC-002` apply preserves the 200,448-byte ETC size and
  produces SHA-256
  `E83768B6B39264A97146BE384E3D0A245EE5CBBB288848D1A965934C66C28FFA`.
  Exactly 16 bytes differ from canonical NA2 ETC, all inside the declared
  ranges. The adjacent Stop record at `0x2E798` remains
  `(120,48,72,24)`. Package validation, 33 focused profile/UI tests, and the
  full 127-test suite pass.
- A historical NA2 screenshot from the preserved Previous ISO has the same
  clipping, so this defect predates the current donor conversion.
- All three title placement records are identical across NA2 and NUN5.
  Patching title coordinates would be unsupported; the visible fragments and
  missing Music label come from the NA2 source rectangles.
- `TEXTENG.BIN` does not own texture rectangles or placement for this path.
- NA2 `FUN_006b44b0` / NUN5 `FUN_006c7250` and the NUN5 localized accessor
  `FUN_003d4210` do not draw the Previous/Next Page controls. They are the
  separate common Play/Stop prompt family, and their state-2 Play branch is
  now covered by `UI-ETC-002`.
- NA2 `FUN_006b7c30` / NUN5 `FUN_006cad20` and accessor `FUN_003d41c0`
  render character-grid selection markers, not page controls.
- Searching for an isolated `(0,0,144,24)` rectangle was a false boundary:
  the authoritative records are the two `(1,v,144,24)` entries referenced by
  the homologous draw loops.
- Movie/Music list wording, wrapping, and font spacing differ in the paired
  screenshots, but they are text-rendering behavior rather than HOME texture
  rectangles and remain outside this texture-only correction.
- The adjacent Stop rectangle and the Controls/Display/Hide prompt records
  were not visible in these captures, so copying them would exceed the
  screen-by-screen evidence boundary.

## Confidence

**High, static and paired-memory proven; runtime acceptance pending.** The
class factories, state, draw functions, localized accessors, exact
source/destination ranges, table semantics, and paired visual failures all
agree across canonical binaries and captured memory. The only uncompleted
evidence is the user's visual review of a rebuilt NA2 ISO containing
`UI-ETC-002`.
