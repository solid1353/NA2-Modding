# Character Select UI layout

## Research coverage

- **Assigned scope:** compare clean NA2 and NUN5 Character Select name records and footer geometry.
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
`@source_nun5/SLES_556.05`. Both executable text segments use a fixed
runtime-to-file mapping within the functions below:

| Game | Function | Runtime range | Relevant file offsets |
| --- | --- | --- | --- |
| NA2 | `FUN_003bc470` | `0x003BC470..0x003BC63C` | `0x2BC5B8`, `0x2BC5DC`, `0x2BC600`, `0x2BC624` |
| NUN5 | `FUN_003cf0d0` | `0x003CF0D0..0x003CF290` | `0x2CF218`, `0x2CF24C`, `0x2CF300`, `0x2CF324` |

`CHARSEL1.CCS` contains the localized artwork and model data, but the
character-name renderers obtain their rectangles elsewhere.

## Shared character-name rectangle table

The character-name renderers do not obtain their rectangles from
`CHARSEL1.CCS`. NA2 `FUN_0037d410` reads a 96-entry table at runtime
`0x005D4E70` (ELF file `0x4D4F70`). NUN5's corresponding helper
`FUN_0038c350` calls localized accessor `FUN_003d45d0`; English language index
zero resolves to runtime `0x005DDC50` (ELF file `0x4DDDD0`).

The nearby NUN5 range at ELF file `0x4DC120` is a separate uniform 38x46
portrait grid used by `FUN_0038c3a0`, not the localized name table. The
localized accessor and homologous call sites disprove using it as a source for
character-name rectangles.

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

| Control | NA2 offset / bytes | NUN5 offset / bytes |
| --- | --- | --- |
| Random | `0x2BC600` / `9643023C` | `0x2CF300` / `8243023C` |
| Select Color | `0x2BC624` / `2043023C` | `0x2CF324` / `C842023C` |

The common OK and Back calls use separate code and resources. NUN5's added
GP-relative global loads are not ABI-compatible with NA2, so its nominal `lui`
instructions do not by themselves express the effective prompt anchors.

## Relationships and evidence

Confidence is **verified**: both complete functions are homologous, the exact
source/destination words match the clean binaries, and the paired runtime
result matches NUN5 within normal pulse timing without touching neighboring
controls.
