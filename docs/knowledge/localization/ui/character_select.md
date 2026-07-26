# Character Select UI layout

## Binary identity and mapping

This record compares the clean Japanese NA2 boot ELF
`@source_na2/SLPS_258.37` with the official English NUN5 boot ELF
`@source_nun5/SLES_556.05`. Both executable text segments use a fixed
runtime-to-file mapping within the functions below:

| Game | Function | Runtime range | Relevant file offsets |
| --- | --- | --- | --- |
| NA2 | `FUN_003bc470` | `0x003BC470..0x003BC63C` | `0x2BC4B8`, `0x2BC4DC`, `0x2BC600`, `0x2BC624` |
| NUN5 | `FUN_003cf0d0` | `0x003CF0D0..0x003CF290` | `0x2CF118`, `0x2CF14C`, `0x2CF300`, `0x2CF324` |

The complete `CHARSEL1.CCS` payload is already imported from NUN5. Its
localized artwork and model data are therefore not the remaining cause.

## Character Select footer compositor

The parent Character Select draw routine calls this compositor once after
drawing both player selectors. The relevant behavior is:

```cpp
void draw_character_select_footer(Screen *screen) {
    draw_common_prompt(ok_x, 362.0f, screen->common_prompts, 0);   // OK
    draw_common_prompt(back_x, 362.0f, screen->common_prompts, 1); // Back

    // CHARSEL1.CCS records:
    draw_charsel_record(random_x, 362.0f, screen->charsel_sprites, random_rect);
    draw_charsel_record(select_color_x, 362.0f,
                        screen->charsel_sprites, select_color_rect);
}
```

NA2 uses `random_x=300.0f`, `select_color_x=160.0f`, `ok_x=400.0f`, and
`back_x=470.0f`. NUN5 uses `random_x=260.0f` and
`select_color_x=100.0f`; its OK/Back paths start from the same nominal
`400.0f`/`470.0f` values and then add signed regional globals `-12`/`-8`.
The artwork loads have the same destination register and equivalent call
sites, so `UI-ELF-007` copies the official NUN5 instruction words directly:

| Control | NA2 offset / bytes | NUN5 offset / bytes |
| --- | --- | --- |
| Random | `0x2BC600` / `9643023C` | `0x2CF300` / `8243023C` |
| Select Color | `0x2BC624` / `2043023C` | `0x2CF324` / `C842023C` |

The common OK and Back calls use separate code and resources. NUN5's added
GP-relative global loads are not ABI-compatible with NA2, so copying only its
nominal `lui` instructions would preserve the defect. Two authored
same-register ports instead encode the official effective anchors:

| Control | NA2 offset / original | Replacement | NUN5 behavior |
| --- | --- | --- | --- |
| OK | `0x2BC4B8` / `C843023C` | `C243023C` (X=`388`) | `400 + (-12)` |
| Back | `0x2BC4DC` / `EB43023C` | `E743023C` (X=`462`) | `470 + (-8)` |

## Relationships and evidence

- Caller: NA2 Character Select parent draw path at `FUN_003bce90`; NUN5
  homolog at `FUN_003cfaf0`.
- Callees: NA2 `FUN_0037bc40` / NUN5 `FUN_0038ad00` draw the two
  `CHARSEL1.CCS` records. The common-prompt callees are separate.
- Side effects: the function submits footer sprites and temporarily adjusts
  opacity for join-state feedback; the anchor instructions do not mutate game
  state.
- Runtime evidence before the patch: paired 640x480 captures show all four NA2
  footer records displaced right.
- Runtime evidence after the patch: a guarded task-owned savestate copy applied
  the same two resident words before redraw. In the resulting hidden-clone
  capture, the dark-pixel bounds were `48..199,442..462` for Select Color and
  `262..386,439..465` for Random, versus NUN5 bounds
  `47..198,441..461` and `261..385,438..465`. A second guarded Slot 4 capture
  applies X=`388`/`462` to the separate OK/Back calls and aligns them with the
  reference. The remaining one-pixel phase variance is normal prompt
  pulsation; no label is clipped.
- Negative result: importing the complete NUN5 `CHARSEL1.CCS` alone does not
  change these anchors because they are supplied by executable code. Literal
  NUN5 OK/Back instruction copies are also insufficient because the effective
  offset is calculated by extra region-specific instructions absent from NA2.

Confidence is **verified**: both complete functions are homologous, the exact
source/destination words match the clean binaries, and the paired runtime
result matches NUN5 within normal pulse timing without touching neighboring
controls.
