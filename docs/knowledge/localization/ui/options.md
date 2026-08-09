# Shared frontend prompt layout

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
| NA2 | Mode Select draw | `FUN_00385c00` | `0x00385C00..0x00385EB0` |
| NUN5 | Mode Select draw | `FUN_003972e0` | `0x003972E0..0x003975C0` |

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

`ui_layout_common_prompts` copies all three official NUN5 records into the corresponding NA2
static slots. This preserves NA2's object ABI and compositor code while making
every shared case-4 caller use the same geometry as NUN5.

## Options-root OK and Back anchors

The Options-root draw uses the same common-prompt compositor but supplies its
OK and Back anchors from `FUN_0038c5f0`:

| Prompt | NA2 runtime / file offset | NUN5 runtime / file offset | Effective NUN5 X |
| --- | --- | --- | ---: |
| OK | `0x0038C778` / `0x28C878` | `0x0039E18C` / `0x29E30C` | `400 - 12 = 388` |
| Back | `0x0038C79C` / `0x28C89C` | `0x0039E1C0` / `0x29E340` | `470 - 8 = 462` |

NA2 loads X=`400` and X=`470` directly with `C843023C` and `EB43023C`.
The NUN5 homolog loads the same nominal values, converts its shared signed
regional globals, and adds `-12` for OK and `-8` for Back before calling
`FUN_0038bb10`. Those additions do not exist in the NA2 caller, so copying the
nominal donor loads would not move either prompt.

`ui_layout_common_prompts` therefore stores the equivalent NA2 values X=`388`
(`C243023C`) and X=`462` (`E743023C`) at the two guarded call sites. These are
authored ABI ports, not literal donor copies. A task-owned slot-1 savestate
patched with only those two words rendered the complete Cross/OK and
Triangle/Back groups at the NUN5 positions. The existing Cancel records,
option values, input handling, and text/font rendering were unchanged.

## Shared Controls and Music footer anchors

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

`ui_layout_options_footers` copies all four NUN5 `4843023C` instructions over NA2's guarded
`6643023C` instructions. This moves the two complete Select groups together by
30 logical pixels while preserving their internal spacing.

Later paired Music Settings and Control Settings states expose the OK and Back
groups in both homologous functions. NA2 loads nominal X=`400` and X=`470`
directly at Music runtime/file addresses `0x0038A468`/`0x28A568` and
`0x0038A48C`/`0x28A58C`, and at Controls addresses
`0x00388C5C`/`0x288D5C` and `0x00388C80`/`0x288D80`. NUN5 loads the same
nominal values in both homologs, then converts the same two signed regional
globals and adds `-12` and `-8`. Its effective anchors are therefore X=`388`
and X=`462` on both screens.

The NUN5 GP-relative loads are not ABI-compatible with NA2. `ui_layout_options_footers`
extends the already-owning shared footer patch with two authored same-register
constants per function (`C243023C` and `E743023C`) rather than duplicating
logic or copying unsafe global accesses. Each guarded task-owned state changed
only its two function-local words and aligned the complete Cross/OK and
Triangle/Back groups with the NUN5 reference. This proves shared geometry but
separate call sites: the implementation belongs to one patch, while each
resident renderer still needs its own guarded pair of constants.

## Mode Select footer

The Mode Select functions are homologous full-screen draws. Their half-open
runtime/file ranges are:

| Game | Runtime range | ELF file range | Only direct caller |
| --- | --- | --- | --- |
| NA2 | `0x00385C00..0x00385EB0` | `0x285D00..0x285FB0` | `0x001EA59C` |
| NUN5 | `0x003972E0..0x003975C0` | `0x297460..0x297740` | `0x001F04C8` |

The footer portion reduces to:

```cpp
void draw_mode_select_footer(ModeSelectScreen *screen) {
    draw_common_prompt(effective_ok_x(), 362.0f, screen->common, OK, true);
    draw_common_prompt(effective_back_x(), 362.0f, screen->common, BACK, true);
    draw_start_label(150.0f, 362.0f, screen->labels, localized_start_rect());
}

// NA2 original:           OK=400, Back=470, START=130
// NUN5 effective result:  OK=388, Back=462, START=150
```

NA2 calls `FUN_0037c980` directly with literal X=`400` and X=`470` at
runtime/file addresses `0x00385DE0`/`0x285EE0` and
`0x00385E04`/`0x285F04`. NUN5 calls homolog `FUN_0038bb10` with nominal
X=`400` and X=`470`, but converts two signed regional globals to floats and
adds `-12` and `-8` first. Those additions are absent from NA2, so copying
NUN5's nominal load instructions would leave the visible mismatch unchanged.

`ui_layout_mode_select` therefore writes the equivalent effective NA2 constants
X=`388` (`C243023C`) and X=`462` (`E743023C`). These are authored behavior
ports rather than literal donor copies. They reproduce the official NUN5
result while retaining NA2's register flow and shared compositor ABI. The
existing two edits in the same patch copy NUN5's exact START rectangle and
port its X anchor to `150`; no duplicate footer patch is introduced.

The draw functions call the shared prompt compositor, submit the START
companion through `FUN_0037bc40`/`FUN_0038ad00`, and finally commit the prompt
sprite objects through `FUN_001cc070`/`FUN_001d1180`. They update transient
sprite geometry and draw queues only; the selected mode, input state, and menu
controller transitions are untouched.

A guarded copy of paired slot 1 changed only the two NA2 instruction words.
The hidden, muted task-owned clone rendered both OK and Back at
`dx=+1,dy=+1` versus NUN5. The shared one-pixel delta is normal prompt pulse
timing, and neither legend is clipped. The user accepted the final Mode Select
footer on 2026-07-26. Confidence is **verified**.

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
- A separate guarded slot-1 proof changed only the Options-root OK/Back load
  words to their effective NUN5 anchors. Both groups match the reference; this
  is the same regional-offset family as Mode Select and Settings, but a
  distinct caller pair rather than a duplicate write.
- The unrelated X/Y text spacing and the separate OK prompt were deliberately
  untouched.
- A first guarded Music Options probe copied NUN5 common-prompt records 0 and
  1 into the NA2 table. It did not move the reported legend because these
  screens use common-prompt case 3 plus a dedicated legend record, not the
  case-5 two-record compositor. That probe was discarded and is not canonical.
- The preserved Music Options pair showed NA2's static
  `SELECT button: Return to Defaults` legend 30 logical pixels to the right of
  NUN5. A guarded state containing all four instruction copies moved the
  complete legend to the NUN5 X position; vertical placement and internal
  spacing remained unchanged.
- A newer paired Music Settings state then isolated the remaining OK/Back
  mismatch in the same renderer. Guarded X=`388`/`462` writes aligned both
  groups; this is an extension of the existing `ui_layout_options_footers` ownership, not a
  second implementation.
- The overflowing Music Options help sentence is emitted through the text/font
  renderer and is outside this texture-layout correction.

Confidence is **verified**: complete-function comparison establishes the shared
algorithms and caller anchors, all destination and donor ranges match the clean
binaries, and the exact donor Select instructions plus the bounded effective
Music constants reproduce the NUN5 geometry at runtime.

## Options labels and difficulty values

Importing complete NUN5 `OPTION.CCS` does not change the boot-ELF rectangle
tables consumed by the Options renderer. NA2 `FUN_0038c160` reads five menu
labels at EE `0x005D52E0` and six difficulty labels at `0x005D5310`; NUN5
`FUN_0039dba0` obtains the homologous English records through localized table
accessors.

`ui_layout_options_labels` copies the complete 96-byte official block—five
menu labels, an eight-byte zero separator, and six difficulty labels—from NUN5
ELF file `0x4DDD10` to NA2 file `0x4D53E0`. Positions, `0.9` scales, and the
byte-identical arrow rectangle remain unchanged.

The widest difficulty value also needs NUN5's alternate sprite routing. NA2
selects that object for indices `{0,5}`, while NUN5 selects `{0,4,5}`.
`ui_layout_difficulty_sprite` replaces NA2's `index == 5` test at ELF file
`0x28C40C` with `index >= 4` while retaining the following `index == 0` test.
For the proven domain `0..5`, this yields the exact donor set. Guarded runtime
readback passed, and `INSANE`, `HARD`, `EASY`, and `SIMPLE` rendered cleanly.

## Controls Vibration label

The NUN5 `CMN/GAUGE.CCS` import supplies English `TEX_xmenu`, but NA2's
boot-ELF table still selects Japanese rectangle `(1,69,42,22)` at file
`0x4D53C0`. `ui_layout_controls_vibration` copies the official NUN5 rectangle
`(64,88,64,20)` from file `0x4DEA28` into the homologous NA2 slot. The edit
changes only the graphical Vibration label selection; surrounding OFF/On text
and font rendering remain separate.
