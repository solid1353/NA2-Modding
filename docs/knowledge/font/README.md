# Font v23 Negative Result

This directory preserves the visual and byte-level evidence for the font v23 tracking experiment performed on 2026-07-13.

## Experiment

The test changed `SLPS_258.37` at file offset `0x866E0` from `80 BF 02 3C` to `00 00 02 3C`. The intended effect was to match the NUN5 ASCII-mode horizontal-tracking initialization (`0.0` instead of NA2's `-1.0`). The exact operation is retained in `font_v23_patch_log.tsv` and canonically normalized as `font_v23_elf_zero_tracking` in `na2_patcher/modules/raw_binary/patch_sets/font_elf_history/`.

## Observed result

The user observed no meaningful visual improvement over the preceding v22 state. English text remained oversized/chunky, spacing remained inconsistent, and long Controls-menu entries remained clipped. `font_v23_no_visible_change.png` is the final comparison screenshot.

This is a useful negative result: do not repeat this single-field tracking patch as a new proposed fix. It does not prove that tracking or `FUN_00186510` is irrelevant, only that changing this one initialization value did not solve the visible problems in the tested build.

## Surrounding confirmed observations

- NA2 and NUN5 `GF4C.BIN` are both 104 bytes but diverge from offset `0x28`; the v22 and v23 experiments used the NUN5 variant. Its independent functional significance remains unproven.
- Replacing NA2 GF4 with the exact NUN5 GF4, padded or unpadded, produced broad spacing but patchy glyph rendering and could disrupt PNACH behavior. Do not repeat that direct swap as a new hypothesis.
- The v22 state was clean and closer to NUN5, but glyphs could touch or overlap and long text still clipped.
- `na2_patcher/modules/raw_binary/patch_sets/font_m01/` canonically reconstructs the accepted clean-coverage font state. Historical ELF experiments, including v23, are normalized under `font_elf_history/`.

The remaining font work still separates into glyph appearance, positioning/advance behavior, and missing NUN5-style auto-fit/squish. Reuse applicable historical evidence from Git history and maintain current analysis under `@analysis/disassembly/NA2/` and `@analysis/disassembly/NUN5/`, never under `@source/`.

Relevant static-analysis leads retained from the investigation:

- NA2 ASCII setup: `FUN_00186510`.
- NUN5 counterpart: `FUN_001878e0`.
- NUN5 boxed auto-fit: `FUN_00389df0` and `FUN_0018b1b0`.
- NA2 menu path: `FUN_003885b0`, which calls `FUN_00379240` and appeared to draw/center without the corresponding 128-pixel auto-fit path.
