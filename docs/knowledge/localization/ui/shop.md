# Shop UI layout

## Binary identity and mapping

This record compares the clean Japanese NA2 `PRG/ETC.BIN`
(`200448` bytes, SHA-256
`8FF3C6E1ED5CE2B093B0934C898C40D1CEEA0C20778C49CDA5591AAD02375C74`)
with the official English NUN5 `PRG/ETC.BIN` (`171776` bytes, SHA-256
`BDB6BDA1F9D335047586A263E478486C8E7924B91FA972B6F3E58CAEC5EA0778`).
Both are the hash-pinned `na2_etc` and `nun5_etc` binary-patcher targets.

The relevant homologous Shop render functions are:

| Game | Practical name | Ghidra range | Live EE range | File range |
| --- | --- | --- | --- | --- |
| NA2 | `ShopScreen::render` (`FUN_006D84A0`) | `0x006D84A0..0x006D8C10` | `0x006D84E0..0x006D8C50` | `0x245E0..0x24D50` |
| NUN5 | `ShopScreen::render` (`FUN_006EC7E0`) | `0x006EC7E0..0x006ECDE4` | `0x006EC820..0x006ECE24` | `0x25B20..0x26124` |

The preserved Ghidra projects map the overlay after stripping its `0x40`-byte
file header: NA2 Ghidra address = file offset + `0x006B3EC0`; NUN5 Ghidra
address = file offset + `0x006C6CC0`. Live EE memory retains that header, so
NA2 live address = file offset + `0x006B3F00` and NUN5 live address = file
offset + `0x006C6D00`. A failed guarded state probe at the Ghidra address
returned unrelated bytes and changed nothing; the `+0x40` live addresses then
matched and patched exactly.

The functions are reached through the Shop state dispatch, so the preserved
Ghidra export does not expose one ordinary direct caller. Their identity is
confirmed by the complete matching control flow, embedded
`ccShopBonusTarget`/`ccShopBonusShot` type names, the Shop-owned rectangle
tables, and paired runtime captures.

## Localized label path

The complete NUN5 `SHOP.CCS` donor already supplies the English artwork. NA2
still selects Japanese-size atlas rectangles and three regional placement
constants from `ETC.BIN`.

The draw path can be reconstructed as:

```cpp
void draw_shop_labels(ShopScreen *screen) {
    Rect money = shop_currency_rects.money;
    Rect ryo = shop_currency_rects.ryo;

    build_sprite(screen->currency_sprite, money);
    set_sprite_position(screen->currency_sprite, 254.0f, 28.0f, money);
    set_sprite_position(screen->currency_sprite, 380.0f, 50.0f, ryo);

    // Keep NA2's seven-digit money-value formatting and placement.
    draw_money_value(screen->currency_sprite, screen->money);

    Rect bonus_target = shop_bonus_rects.label;
    Rect bonus_shot = shop_bonus_rects.icon;
    set_sprite_position(screen->bonus_sprite, 105.0f, 310.0f, bonus_target);
    set_sprite_position(screen->bonus_sprite, 30.0f, 310.0f, bonus_shot);
}
```

NA2 uses the same draw order and callees but loads `250.0f`, `48.0f`, and
`100.0f` for the three highlighted coordinates. NUN5 uses `254.0f`, `50.0f`,
and `105.0f`.

## Canonical donor imports

`UI-ETC-001` uses five guarded NUN5 imports:

| Semantic data | NA2 file / Ghidra / live EE | NUN5 file / Ghidra / live EE | Change |
| --- | --- | --- | --- |
| Money and Ryo rectangles | `0x30308` / `0x006E41C8` / `0x006E4208` | `0x292F8` / `0x006EFFB8` / `0x006EFFF8` | Copy 16 bytes |
| Money X instruction | `0x249A4` / `0x006D8864` / `0x006D88A4` | `0x25E88` / `0x006ECB48` / `0x006ECB88` | `250.0f` to `254.0f` |
| Ryo Y instruction | `0x249CC` / `0x006D888C` / `0x006D88CC` | `0x25EB0` / `0x006ECB70` / `0x006ECBB0` | `48.0f` to `50.0f` |
| Bonus Game X instruction | `0x24BB0` / `0x006D8A70` / `0x006D8AB0` | `0x26094` / `0x006ECD54` / `0x006ECD94` | `100.0f` to `105.0f` |
| Bonus Game rectangles | `0x30340` / `0x006E4200` / `0x006E4240` | `0x29330` / `0x006EFFF0` / `0x006F0030` | Copy 16 bytes; label width `122` to `126` |

The label-position callee is `func_0x0037BC40` in NA2 and
`func_0x0038AD00` in NUN5. The money-value callees are `FUN_006CB360` and
`FUN_006DED30`, respectively. The patch does not replace those routines or
alter Shop currency, selection, purchase, input, or seven-digit formatting
state.

## Evidence and negative results

- The 16-byte rectangle import was already runtime-proven to show the complete
  English Money and Ryo artwork while preserving NA2's seven-digit value.
- A later paired capture showed that complete artwork was not placement parity:
  Money remained four logical pixels left of NUN5 and Ryo two pixels above it.
- The paired Bonus Game screenshots were captured at slightly different pulse
  phases. Treating the difference as pulse-only was not sufficient evidence:
  complete-function comparison proves a separate five-pixel X-anchor
  difference at the exact homologous instruction.
- The newer slot-7 review confirms that anchor but shows the rightmost four
  label pixels clipped. The two functions copy homologous 16-byte rectangle
  tables immediately before the Bonus Game draws. Their icon records are
  identical; the only difference is NA2 width `122` versus NUN5 width `126`.
- Copying `SHOP.CCS` alone cannot fix any of these constants because they are
  loaded by `ETC.BIN`.
- The money-value origin differs regionally because NUN5 formats fewer digits.
  Copying that origin would conflict with NA2's intended seven-digit layout, so
  it remains intentionally NA2-specific.
- The earlier worker ISO and guarded Shop state prove the three anchor imports
  and seven-digit value behavior. A fresh hidden task-clone render used a
  guarded task-owned state with the exact `0x006E4240` table replacement and
  reproduced NUN5's complete Bonus Game right edge without moving its left
  anchor. The user accepted that final paired result on 2026-07-26.

Confidence is **verified**. The address mapping, clean-binary guards,
homologous copy loops, exact donor-table difference, task-owned runtime render,
and final user acceptance all agree.

## Intentional exclusion

Remaining UI differences inside the Shop minigame are intentionally not fixed.
The minigame is a rare, arbitrary side feature and does not justify further
localization work. This exclusion does not apply to the localized Shop-screen
labels and placement corrections documented above.
