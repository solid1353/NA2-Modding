# Battle Results presentation

Addresses use the
[Game binary address conventions](../../../game/files/file_identities.md).

## Research coverage

- **Assigned scope:** Native Battle Results summary, cloud, rank-stamp, Ninja
  Song footer, objective, arithmetic, and bonus presentation in NA2 and NUN5.
- **Exploration depth:** The paired BTL renderers, controllers, tables, regional
  helpers, visible rank controller, and representative runtime states for all
  five ranks and multiple Ninja Song result variants were inspected.
- **Confirmed coverage:** Cloud geometry, both rank paths, the visible rank
  selector table, footer ownership and anchors, objective layout, arithmetic
  routing, bonus rows, and unchanged controller clamping.
- **Unresolved or untested:** The purpose of the hidden shared-rank sprite and
  every possible Ninja Song descriptor or bonus row were not exhaustively
  established.
- **Deliberate exclusions and overlap:** Result calculation, rank assignment,
  input, sound, and non-results battle UI are outside this document.
- **Evidence limitations:** Runtime comparisons cover the five rank stamps and
  representative result layouts; conclusions for uncommon result combinations
  also rely on the paired static control flow.

## Summary, clouds, and shared-rank sprite

| Role | NA2 v2.28 | NUN5 |
| --- | --- | --- |
| Results frame/layout | file `0x62A30..0x62CFF`, Ghidra `FUN_007168F0`, live `0x00716930..0x00716BFF` | file `0x65780..0x65A6F`, Ghidra `FUN_0072C440`, live `0x0072C480..0x0072C76F` |
| Reveal/row animation | file `0x62FD0..0x636AF`, Ghidra `FUN_00716E90`, live `0x00716ED0..0x007175AF` | file `0x65D40..0x6641F`, Ghidra `FUN_0072CA00`, live `0x0072CA40..0x0072D11F` |
| Title controller | `FUN_00719D40`, live `0x00719D80` | `FUN_0072FBC0`, live `0x0072FC00` |
| Centered scaled-sprite helper | resident `FUN_0037BD00` | resident `FUN_0038ADC0` |
| Shared-rank rectangle accessor | boot-ELF table at file `0x4B14A0`, live `0x005B13A0` | localized `FUN_003D5160` |
| Shared-rank width-fit helper | absent on this path | `FUN_003D5700` |
| Result-label table | BTL file `0x210030`, live `0x008C3F30` | boot ELF file `0x4DDCA0` |
| Title/cloud rectangles | BTL file `0x2100D8`, live `0x008C3FD8` | BTL file `0x2158E0` |
| Moving-cloud table | BTL file `0x1E5CC0`, live `0x00899BC0` | BTL file `0x1EE1F0`, live `0x008B4EF0` |
| Shared-rank call site | BTL file `0x634E8`, Ghidra `0x007173A8`, live `0x007173E8` | equivalent block in `FUN_0072CA00` |

The first five entries of the NUN5 English battle-HUD rectangle table are the
shared-rank labels selected by `result_rank - 1`:

| Value | Rectangle `(u,v,w,h)` |
| --- | --- |
| Outstanding! | `(0,48,80,24)` |
| Nicely done! | `(80,48,80,24)` |
| Good job! | `(200,168,48,24)` |
| Keep trying | `(160,48,72,24)` |
| Try harder! | `(128,120,112,24)` |

The five-cloud loop is structurally identical in both games. Its X, Y, speed,
and height fields match; only width differs. NA2 uses
`156.4, 102, 136, 102, 136`, while NUN5 uses
`293.25, 191.25, 255, 191.25, 255`. With NUN5's `XNINKA.CCS`, the NA2 widths
cross neighboring atlas content. The complete NUN5 table restores the intended
cloud regions without changing their motion.

NUN5 draws the shared-rank rectangle at scale `1.35` through its localized
accessor, width-fit helper, and centered renderer. The five English records are
at most 112 pixels wide, so their scaled widths remain below the 220-pixel fit
ceiling. NA2 lacks the localized helpers but has the equivalent centered
renderer. The resulting NUN5 anchor calculation is:

```cpp
Rect rank = englishRankRects[resultRank - 1];
drawCenteredScaled(rankSprite,
                   animatedX + 140.0f,
                   rowY - 1.0f + rank.h * 1.35f * 0.6f,
                   1.35f,
                   1.35f,
                   rank);
```

Runtime probes showed that this shared-rank object is hidden, occluded, or a
secondary layer: changing both its rectangle and its live anchor changed no
visible rank pixels. Its object fields therefore cannot establish placement of
the visible rotated stamp.

`FUN_007168F0` updates cloud positions and draws the summary footer.
`FUN_00716E90` owns row reveal and rank-sprite state. The NA2 and NUN5 title
controllers use the same pulse algorithm, so independently timed still frames
can show different title sizes without a different static layout.

## Visible rotated rank stamps

The visible rotated red stamp uses a separate path. Its controller rank byte
selects the same sequence in both games, and the complete tables are:

| Game/table | Index 0 | Index 1 | Index 2 | Index 3 | Index 4 |
| --- | --- | --- | --- | --- | --- |
| NA2 BTL file `0x2100B0`, live `0x008C3FB0` | `(352,200,64,56)` | `(416,168,64,56)` | `(416,112,64,56)` | `(416,56,64,56)` | `(416,0,64,56)` |
| NUN5 English SLES file `0x4DDCE0`, live `0x005DDB60` | `(416,176,96,44)` | `(416,132,96,44)` | `(416,88,96,44)` | `(416,44,96,44)` | `(416,0,96,44)` |

NUN5's language-pointer table at live `0x005BB390` addresses equivalent copies
at `0x005DDB60`, `0x005DEE90`, `0x005E14F0`, `0x005E01C0`, and
`0x005E2820`. The first canonical English copy begins at SLES file `0x4DDCE0`.
Index `3` is the subtraction baseline used by the rendering path.

| Role | NA2 v2.28 | NUN5 |
| --- | --- | --- |
| Rank-stamp selector/draw | BTL file `0x63B60`, Ghidra `FUN_00717A20` | BTL file `0x668F0`, Ghidra `FUN_0072D5B0` |
| Rectangle normalization | resident `FUN_0037DA40` | resident `FUN_0038C9C0` |
| Animation-object lookup | resident `FUN_001BAB40` | resident `FUN_001BF290` |
| Per-model texture offset | resident `FUN_00198840` | resident `FUN_0019BD70` |

The visible-stamp selection reduces to:

```cpp
Rect selected = rankRects[result->rank_15c];
Rect baseline = rankRects[3];
float u = float(selected.x - baseline.x) / 512.0f;
float v = 1.0f - float(selected.y - baseline.y) / 256.0f;
Model *stamp = findAnimationModel(result->stampAnimation_11c);
setModelTextureOffset(stamp, fixed12(u), fixed12(v), 0, 0);
```

The NA2 decompiler export ends after the animation lookup, but raw BTL bytes
continue with the float-to-fixed conversion and call the NA2 texture-offset
homolog. This is an export gap, not missing game behavior. NUN5's stamp
animation has 21 frames and no material or UV controller; its model uses the
same UVs as NA2 but English-aspect geometry. Selection belongs to the BTL
rectangle table rather than the model defaults.

A whole-column upward atlas shift is invalid: the five labels occupy adjacent
44-row cells, so moving the shared 96-by-220 region mixes neighboring labels.
The five table records, including the index-3 baseline, must remain internally
coherent instead.

## Ninja Song details footer

The Ninja Song details screen has a distinct footer renderer; it is not the
Battle Results summary footer.

| Game | Function | Runtime range | BTL file range |
| --- | --- | --- | --- |
| NA2 | `FUN_007182E0` | `0x007182E0..0x00718920` | `0x64420..0x64A60` |
| NUN5 | `FUN_0072DEA0` | `0x0072DEA0..0x0072E5B0` | `0x671E0..0x678F0` |

Both functions draw Next and Back at Y=`348`. NA2 passes literal X=`395` and
X=`470`. NUN5 loads the same nominal values, then adds regional offsets `-20`
and `-8`, producing effective X=`375` and X=`462`:

```cpp
drawCommonPrompt(375.0f, 348.0f, prompts, NEXT, true);
drawCommonPrompt(462.0f, 348.0f, prompts, BACK, true);
```

The cross-game screen difference matches those offsets. Changes to the summary
footer do not affect this screen because the two footer paths have separate
owners.

## Ninja Song objectives and totals

The objective loops are NA2 Ghidra `0x00718430..0x007187B4` / BTL file
`0x64570..0x648F4` and NUN5 Ghidra `0x0072DFF0..0x0072E580` / BTL file
`0x67330..0x678C0`. Both begin with `rowY = 70 - scroll`, advance ordinary
rows by `36`, advance grouped content by `50`, and use visibility bounds
`-100..484`. NUN5 draws the objective index at X=`80`, prose at X=`112` and
Y=`rowY - 6`, and prose inside a `320 x 32` box.

Arithmetic is owned by NA2 `FUN_00718920` / BTL file `0x64A60` and NUN5
`FUN_0072E5B0` / BTL file `0x678F0`. NUN5 draws a localized unit at relative
`(176,-6)` in a `52 x 32` box and a right-aligned total in a 64-unit box at
relative X=`256`. Its routing supports expanded, total-only, and N/A rows.
Descriptor unit `2` selects the `timer counts` resource; unit `4` suppresses
the unit. Renderer selection is descriptor-based, not string-based.

The result-dependent bonus renderers are NA2 `FUN_00718C60` / BTL file
`0x64DA0` and NUN5 `FUN_0072E9C0`. They consume the selected 12-byte result
row, so both the bonus label and Y position can vary by fight. NUN5 wraps the
label in a `288 x 32` two-line box and right-aligns the total in a `96 x 20`
box. BODY's two-unit inter-digit advance participates in total-width
measurement.

NA2 controller Ghidra `0x00718FE0` / live `0x00719020` and NUN5 controller
Ghidra `0x0072EDD0` / live `0x0072EE10` both receive F12=`30.0` and implement
the same subtract/add, upper-limit, and zero clamps. Representative runtime
comparisons confirmed objective line breaks, arithmetic columns, the two-line
timer label, percent-unit suppression, N/A rows, dynamic bonus-label boxes,
and right-aligned totals.
