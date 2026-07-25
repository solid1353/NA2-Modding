# Options UI layout

## Binary identity and mapping

This record compares the clean Japanese NA2 boot ELF
`@source_na2/SLPS_258.37` with the official English NUN5 boot ELF
`@source_nun5/SLES_556.05`. The relevant shared compositors and the
screen-position caller are:

| Game | Role | Function | Runtime range |
| --- | --- | --- | --- |
| NA2 | shared common-prompt compositor | `FUN_0037c980` | `0x0037C980..0x0037D14C` |
| NUN5 | shared common-prompt compositor | `FUN_0038bb10` | `0x0038BB10..0x0038C08C` |
| NA2 | screen-position draw | `FUN_0038adb0` | `0x0038ADB0..0x0038AFAC` |
| NUN5 | screen-position draw | `FUN_0039c730` | `0x0039C730..0x0039C94C` |
| NA2 | Controls footer draw | `FUN_00388b90` | `0x00388B90..0x00388D4C` |
| NUN5 | Controls footer draw | `FUN_0039a450` | `0x0039A450..0x0039A63C` |
| NA2 | Music Options footer draw | `FUN_0038a1f0` | `0x0038A1F0..0x0038A55C` |
| NUN5 | Music Options footer draw | `FUN_0039bb00` | `0x0039BB00..0x0039BE8C` |

NA2's single loadable segment maps the three destination records from ELF file
offsets `0x4D47B0`, `0x4D47B8`, and `0x4D47C0` to runtime addresses
`0x005D46B0`, `0x005D46B8`, and `0x005D46C0`. NUN5's corresponding
English-language records 4, 5, and 6 are at file offsets `0x4DEA10`,
`0x4DEA18`, and `0x4DEA20`, selected at runtime addresses `0x005DE890`,
`0x005DE898`, and `0x005DE8A0`.

## Shared Cancel compositor

Both screen-position callers request common-prompt case 4 at logical center
`X=170`, `Y=340`. The two case-4 implementations use the same draw order and
centering formula:

```cpp
void draw_cancel(float center_x, float center_y, Sprite *sprite) {
    Rect triangle = cancel_triangle;
    Rect label = cancel_label;
    Rect tail = cancel_tail;
    float x = center_x -
        (triangle.width + label.width + tail.width) * 0.5f;

    draw_rect(sprite, x, center_y - triangle.height * 0.5f, triangle);
    x += triangle.width;
    draw_rect(sprite, x, center_y - label.height * 0.5f, label);
    x += label.width;
    draw_rect(sprite, x, center_y - tail.height * 0.5f, tail);
}
```

NA2's Japanese static records total 182 logical pixels:

| Semantic record | NA2 file offset / bytes | Rectangle |
| --- | --- | --- |
| Triangle | `0x4D47C0` / `030019001A001600` | `(3,25,26,22)` |
| Cancel label | `0x4D47B0` / `0100310072001600` | `(1,49,114,22)` |
| Japanese-only tail | `0x4D47B8` / `010049002A001600` | `(1,73,42,22)` |

NUN5's localized records total 80 logical pixels:

| Semantic record | NUN5 file offset / bytes | Rectangle |
| --- | --- | --- |
| Triangle | `0x4DEA20` / `0200180018001800` | `(2,24,24,24)` |
| Cancel label | `0x4DEA10` / `0100310038001600` | `(1,49,56,22)` |
| Empty tail | `0x4DEA18` / `0000000000000000` | empty |

`UI-ELF-008` copies all three official NUN5 records into the corresponding NA2
static slots. This preserves NA2's object ABI and compositor code while making
every shared case-4 caller use the same geometry as NUN5.

## Shared Controls and Music Select legend

The Controls and Music Options footer functions have the same regional
structure. Each draws the normal OK and Back prompts, then draws the Select
button icon and the adjacent legend texture through two separate calls at one
shared X anchor:

```cpp
void draw_options_footer(FooterSprites &sprites) {
    draw_common_prompt(400.0f, 356.0f, sprites.prompts, OK, true);
    draw_common_prompt(470.0f, 356.0f, sprites.prompts, BACK, true);

    constexpr float select_x = 200.0f; // NUN5; clean NA2 used 230.0f
    draw_common_prompt(select_x, 356.0f, sprites.prompts, SELECT, false);
    draw_rect(select_x, 356.0f, sprites.legend, select_legend_rect);
}
```

NA2 loads `230.0f` with `lui v0,0x4366` for both calls in each function.
NUN5 uses the same register and instruction positions but loads `200.0f` with
`lui v0,0x4348`. The four exact instruction mappings are:

| Screen / call | NA2 runtime / file offset | NUN5 runtime / file offset |
| --- | --- | --- |
| Controls Select icon | `0x00388CA4` / `0x288DA4` | `0x0039A584` / `0x29A704` |
| Controls legend | `0x00388CC8` / `0x288DC8` | `0x0039A5AC` / `0x29A72C` |
| Music Select icon | `0x0038A4B8` / `0x28A5B8` | `0x0039BDE8` / `0x29BF68` |
| Music legend | `0x0038A4DC` / `0x28A5DC` | `0x0039BE10` / `0x29BF90` |

`UI-ELF-009` copies all four NUN5 `4843023C` instructions over NA2's guarded
`6643023C` instructions. This moves the two complete Select groups together by
30 logical pixels while preserving their internal spacing and every unrelated
footer prompt.

## Relationships and evidence

- The complete NUN5 `CMN/GAUGE.CCS` donor already supplies the localized
  artwork and models. Importing it alone cannot change the boot-ELF rectangle
  widths used by NA2's compositor.
- The screen-position draw functions call their homologous shared compositors
  with identical center coordinates and case ID, isolating the defect to the
  three regional records rather than to a screen-specific anchor.
- The compositor writes only transient sprite UV, size, origin, and draw
  fields, then submits the sprites. These records do not mutate option values
  or input state.
- Before correction, the Current NA2 Cancel ink occupied output bounds
  `99..201`; the preserved NUN5 reference occupied `164..258`.
- A guarded copy of the preserved NA2 savestate replaced exactly the three
  resident records. The hidden task-owned clone rendered Current NA2 bounds
  `165..259,412..438`, versus NUN5 `164..258,411..437`. The one-pixel phase
  difference is normal prompt pulsation.
- The unrelated X/Y text spacing and the separate OK prompt were deliberately
  untouched.
- A first guarded Music Options probe copied NUN5 common-prompt records 0 and
  1 into the NA2 table. It did not move the reported legend because these
  screens use common-prompt case 3 plus a dedicated legend record, not the
  case-5 two-record compositor. That probe was discarded and is not canonical.
- The preserved Music Options pair showed NA2's static
  `SELECT button: Return to Defaults` legend 30 logical pixels to the right of
  NUN5. A guarded state containing all four instruction copies moved the
  complete legend to the NUN5 X position; vertical placement, internal spacing,
  OK, and Back remained unchanged.
- The overflowing Music Options help sentence is emitted through the text/font
  renderer and is outside this texture-layout correction.

Confidence is **verified**: complete-function comparison establishes the shared
algorithms and caller anchors, all destination and donor ranges match the clean
binaries, and the exact donor records and instructions reproduce the NUN5
geometry at runtime.
