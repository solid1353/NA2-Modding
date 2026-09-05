# Shared frontend prompt layout

## Research coverage

- **Assigned scope:** compare clean NA2 and NUN5 shared frontend prompts, Options labels, and Controls footer behavior.
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

The three NUN5 records correspond directly to the three NA2 static slots. Their
compatible structure allows the English geometry to be represented without
changing NA2's object ABI or compositor algorithm.

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

Later paired Music Settings and Control Settings states expose the OK and Back
groups in both homologous functions. NA2 loads nominal X=`400` and X=`470`
directly at Music runtime/file addresses `0x0038A468`/`0x28A568` and
`0x0038A48C`/`0x28A58C`, and at Controls addresses
`0x00388C5C`/`0x288D5C` and `0x00388C80`/`0x288D80`. NUN5 loads the same
nominal values in both homologs, then converts the same two signed regional
globals and adds `-12` and `-8`. Its effective anchors are therefore X=`388`
and X=`462` on both screens.

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

The draw functions call the shared prompt compositor, submit the START
companion through `FUN_0037bc40`/`FUN_0038ad00`, and finally commit the prompt
sprite objects through `FUN_001cc070`/`FUN_001d1180`. They update transient
sprite geometry and draw queues only; the selected mode, input state, and menu
controller transitions are untouched.

## Relationships and evidence

Confidence is **verified**: complete-function comparison establishes the shared
algorithms and caller anchors, all compared ranges match the clean binaries,
and runtime observation confirms the effective NUN5 geometry.

## Options labels and difficulty values

NUN5 `OPTION.CCS` does not contain the boot-ELF rectangle tables consumed by
the Options renderer. NA2 `FUN_0038c160` reads five menu
labels at EE `0x005D52E0` and six difficulty labels at `0x005D5310`; NUN5
`FUN_0039dba0` obtains the homologous English records through localized table
accessors.
