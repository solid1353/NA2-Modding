# Battle UI settings and results

Binary identities and address conventions are defined in the [Battle UI index](../battle.md#binary-identities-and-address-convention).

## Battle Mash prompt rectangles

### Identity and address map

This section uses the exact binary identities and address conventions recorded
above. The active paired Mash objects are at NA2 live addresses `0x00E4F3D0`
and `0x00E4F950`, and NUN5 live addresses `0x00DCE550` and `0x00DCEAD0`.
Their `0x580`-byte stride, player-side field at `+0x28`, main prompt ID at
`+0x2F`, and supplemental prompt list beginning at `+0x30` agree across both
games. In the paired state, main prompt ID `0` means Mash and supplemental ID
`0x0C` selects the Cross glyph.

| Role | NA2 | NUN5 |
| --- | --- | --- |
| Main-label renderer | BTL file `0x25C0`, Ghidra `FUN_006b6480`, live `0x006B64C0` | BTL file `0x27E0`, Ghidra `FUN_006c94a0`, live `0x006C94E0` |
| Complete main-prompt rectangle table | BTL file `0x1DB730`, live `0x0088F630` | English regional table in boot ELF file `0x4DE630`, live `0x005DE4B0` |
| NUN5 regional accessor | absent; NA2 directly addresses its BTL table | boot ELF file `0x2D4FC0`, runtime `FUN_003d4e40` |
| Adjacent controller-glyph table | BTL file `0x1DB770`, live `0x0088F670` | separate from the regional main-prompt table |

NUN5 `FUN_003d4e40` obtains the active language index and returns
`regionalTable[language] + promptId * 8`. `FUN_006c94a0` uses it for main
prompt IDs below seven; the NUN5 draw path also uses the returned width and
height. NA2's homolog has no regional accessor and directly indexes the
Japanese table embedded in BTL.

The seven records are ordinary four-field little-endian rectangles:

```cpp
struct PromptRect {
    uint16_t u;
    uint16_t v;
    uint16_t width;
    uint16_t height;
};

const PromptRect *mainPromptRect(uint8_t promptId) {
    return promptId < 7 ? &englishPromptRects[promptId]
                        : &battleStaticPromptRects[promptId];
}
```

For prompt ID zero, NA2 selected `(0,24,48,24)`, which samples the imported
English Mash artwork vertically and clips it. The official NUN5 English record
is `(0,84,64,20)`. `ui_layout_mash_prompts` copies all seven contiguous English records
from the canonical NUN5 boot ELF to NA2's complete BTL table. This preserves
the existing renderer and object ABI while covering every prompt handled by
the NUN5 regional accessor.

### Evidence, negative result, and confidence

A guarded savestate write replaced only live range
`0x0088F630..0x0088F667`. Both Mash labels then rendered horizontally with
the NUN5 source dimensions and screen placement; the Cross panels and their
supplemental record remained independently controlled. The canonical donor
copy has the same 56-byte source and destination ranges and preserves BTL size.

An earlier hypothesis wrote the donor records to adjacent live range
`0x0088F670..0x0088F6A7`. Mash remained vertical while the Cross panels became
rows of incorrect controller glyphs. Runtime instruction bytes in
`FUN_006b6480` then proved its absolute main-table address is `0x0088F630`;
the rejected address is the separate controller-glyph table and must remain
untouched.

Evidence consists of both complete BTL draw paths, NUN5 boot-ELF accessor
`FUN_003d4e40`, the paired live object inventory, exact canonical file bytes,
the guarded negative test, and the corrected 640x480 paired checkpoint.
The table identity, donor mapping, and visible result are **runtime-proven**
with **verified confidence**.

## Battle and Practice Settings footer legends

### Function and address map

This finding uses the BTL identities and `+0x40` Ghidra/live convention recorded in the [Battle UI index](../battle.md#binary-identities-and-address-convention).

| Role | NA2 v2.28 | NUN5 |
| --- | --- | --- |
| Battle Settings draw | file `0x1CC8E0..0x1CCAC7`, Ghidra `FUN_008807a0` (`0x008807A0..0x00880987`), live `0x008807E0..0x008809C7` | file `0x1D65C0..0x1D67CF`, Ghidra `FUN_0089d280` (`0x0089D280..0x0089D48F`), live `0x0089D2C0..0x0089D4CF` |
| Practice Settings draw | file `0x1CE390..0x1CE70F`, Ghidra `FUN_00882250` (`0x00882250..0x008825CF`), live `0x00882290..0x0088260F` | file `0x1D8470..0x1D8703`, Ghidra `FUN_0089f130` (`0x0089F130..0x0089F3C3`), live `0x0089F170..0x0089F403` |
| Battle Settings caller | Ghidra `0x006C11FC` | Ghidra `0x006D46BC` |
| Practice Settings callers | Ghidra `0x006C1210`, `0x00875B1C` | Ghidra `0x006D46D0`, `0x00891AEC` |
| Common OK/Back/Select compositor | `SUB_0037c980` | `SUB_0038bb10` |
| Select companion renderer | `SUB_0037bc40` | `SUB_0038ad00` |

The eight footer X-coordinate instructions map as follows:

| Screen / legend | NA2 file / live | Original NA2 | NUN5 file / Ghidra | Required NA2 result |
| --- | --- | ---: | --- | ---: |
| Battle / OK | `0x1CCA04` / `0x00880904` | 400 | `0x1D66E8` / `0x0089D3A8` | 388 |
| Battle / Back | `0x1CCA28` / `0x00880928` | 470 | `0x1D671C` / `0x0089D3DC` | 462 |
| Battle / Select compositor | `0x1CCA4C` / `0x0088094C` | 230 | `0x1D6750` / `0x0089D410` | 200 |
| Battle / Select companion | `0x1CCA70` / `0x00880970` | 230 | `0x1D6778` / `0x0089D438` | 200 |
| Practice / OK | `0x1CE634` / `0x00882534` | 400 | `0x1D8604` / `0x0089F2C4` | 388 |
| Practice / Back | `0x1CE658` / `0x00882558` | 470 | `0x1D8638` / `0x0089F2F8` | 462 |
| Practice / Select compositor | `0x1CE67C` / `0x0088257C` | 230 | `0x1D866C` / `0x0089F32C` | 200 |
| Practice / Select companion | `0x1CE6A0` / `0x008825A0` | 230 | `0x1D8694` / `0x0089F354` | 200 |

### Reconstructed behavior and cross-game difference

The footer portion reduces to:

```cpp
void drawSettingsFooter(SettingsScreen *screen) {
    drawCommonPrompt(screen->common, effectiveOkX(), 356.0f, OK, true);
    drawCommonPrompt(screen->common, effectiveBackX(), 356.0f, BACK, true);
    drawCommonPrompt(screen->common, selectX(), 356.0f, SELECT, false);
    drawSelectCompanion(screen->selectCompanion, selectX(), 356.0f);
}

// NA2 original:             400, 470, 230
// NUN5 effective anchors:   388, 462, 200
```

Both NUN5 Select calls load X=`200` directly, with the same destination register
as the NA2 X=`230` instructions. Those two instructions are safe exact donor
copies. NUN5 instead loads nominal OK/Back values X=`400` and X=`470`, converts
two signed per-call global values to floats, and adds `-12` and `-8` before
calling its common compositor. NA2 calls its compositor immediately after the
nominal loads and has no equivalent additions. Copying the nominal NUN5
instructions would therefore preserve the visible NA2 mismatch.

`ui_layout_settings_footers` expresses the equivalent behavior with NA2-specific effective
constants X=`388` and X=`462`, plus four exact X=`200` NUN5 donor copies. The
same effective OK/Back constants are independently runtime-proven in
`ui_layout_vs_confirmation`; this patch changes only the distinct Battle and Practice Settings
functions.

### State behavior, evidence, and confidence

The draw function updates menu animation and invokes existing sprite/compositor
objects; the four edits change only call-site X coordinates. They do not change
menu input, selected setting, texture identity, prompt records, object layout,
animation timing, font rendering, or the accepted VS confirmation /
Customize Jutsu path.

Evidence consists of both pairs of complete homologous functions, their callers
and callees, exact source bytes, paired slot-6 and slot-10 `eeMemory` images,
active sprite objects, and guarded task-owned savestates in which each screen's
four live instructions were changed together. The resulting 640x480 captures
align Select, OK, and Back with NUN5; remaining one-pixel differences are normal
pulse-frame variation. The user accepted both the Practice Settings slot-6 and
Battle Settings slot-10 results.

An earlier candidate at NA2 BTL file offset `0xCF70` belongs to the separate
VS confirmation Customize Jutsu call and is not part of this screen. It was
rejected for this defect and remains untouched. The mapping and visible result
are **runtime-proven** with **verified confidence**.

## Battle Results summary, moving clouds, and rank stamps

### Function and address map

This finding uses the BTL identities and `+0x40` Ghidra/live convention recorded in the [Battle UI index](../battle.md#binary-identities-and-address-convention).

| Role | NA2 v2.28 | NUN5 |
| --- | --- | --- |
| Results frame/layout | file `0x62A30..0x62CFF`, Ghidra `FUN_007168F0` (`0x007168F0..0x00716BBF`), live `0x00716930..0x00716BFF` | file `0x65780..0x65A6F`, Ghidra `FUN_0072C440` (`0x0072C440..0x0072C72F`), live `0x0072C480..0x0072C76F` |
| Results reveal/row animation | file `0x62FD0..0x636AF`, Ghidra `FUN_00716E90` (`0x00716E90..0x0071756F`), live `0x00716ED0..0x007175AF` | file `0x65D40..0x6641F`, Ghidra `FUN_0072CA00` (`0x0072CA00..0x0072D0DF`), live `0x0072CA40..0x0072D11F` |
| Title controller | Ghidra `FUN_00719D40`, live start `0x00719D80` | Ghidra `FUN_0072FBC0`, live start `0x0072FC00` |
| Centered scaled-sprite helper | resident `FUN_0037BD00` | resident `FUN_0038ADC0` |
| Rank rectangle accessor | direct boot-ELF table at file `0x4B14A0`, live `0x005B13A0` | localized `FUN_003D5160` |
| Rank width-fit helper | absent on this path | `FUN_003D5700` |
| Result label table | BTL file `0x210030`, live `0x008C3F30` | boot ELF file `0x4DDCA0` |
| Title/cloud rectangles | BTL file `0x2100D8`, live `0x008C3FD8` | BTL file `0x2158E0` |
| Moving-cloud table | BTL file `0x1E5CC0`, live `0x00899BC0` | BTL file `0x1EE1F0`, live `0x008B4EF0` |
| Shared rank call site | BTL file `0x634E8`, Ghidra `0x007173A8`, live `0x007173E8` | equivalent block inside `FUN_0072CA00` |

`ui_layout_battle_hud_name_rectangles` already copies the complete official 95-entry NUN5 English
battle-HUD rectangle table from NUN5 ELF file `0x4DEA30` to NA2 file
`0x4B14A0`. Its first five entries are the shared rank values:

| Value | Rectangle `(u,v,w,h)` |
| --- | --- |
| `Outstanding!` | `(0,48,80,24)` |
| `Nicely done!` | `(80,48,80,24)` |
| `Good job!` | `(200,168,48,24)` |
| `Keep trying` | `(160,48,72,24)` |
| `Try harder!` | `(128,120,112,24)` |

The selector remains `result_rank - 1`; no value-specific code or authored
texture is required.

### Reconstructed behavior and cross-game difference

The moving background loop is structurally identical in both games:

```cpp
for (int i = 0; i != 5; ++i) {
    cloud[i].x += cloud[i].speed;
    if (cloud[i].x >= 512.0f)
        cloud[i].x = -cloud[i].width;
    draw(sharedCloudSprite,
         cloud[i].x, cloud[i].y, cloud[i].width, cloud[i].height);
}
```

The X/Y/speed/height fields already match. NA2's five widths are
`156.4, 102, 136, 102, 136`; NUN5 uses
`293.25, 191.25, 255, 191.25, 255`. With the whole NUN5 `XNINKA.CCS`
atlas imported, the NA2 widths traverse the neighboring `Ninja Song` letters,
so animated `g` fragments appear where moving clouds belong. Copying the
complete NUN5 table restores cloud artwork without changing motion.

The shared five-value rank path differs more substantially:

```cpp
Rect rank = englishRankRects[resultRank - 1];
float scale = 1.35f;

// NA2 original: uncentered sprite at animatedX + 90, rowY - 1.
// NUN5 behavior:
drawCenteredScaled(
    rankSprite,
    animatedX + 140.0f,
    rowY - 1.0f + rank.h * scale * 0.6f,
    scale,
    scale,
    rank
);
```

NUN5 reaches that behavior through localized accessor `FUN_003D5160`, width-fit
helper `FUN_003D5700`, and centered renderer `FUN_0038ADC0`. Those functions
and their call ABI do not exist on the NA2 path. All five English records are
at most 112 pixels wide, so their scaled widths are already below NUN5's
220-pixel fit ceiling. `ui_layout_battle_results` therefore retains NA2's imported donor
table and selector, but replaces the 208-byte inline uncentered block with a
call to existing NA2 centered renderer `FUN_0037BD00`. The port supplies the
NUN5 effective X/Y anchors and the same 1.35 anisotropic arguments; unused
bytes in the replaced block are explicit `nop`s.

For `Outstanding!`, the pre-fix live NA2 object was:

```text
pivot=(0, 0), anchor=(358, 64), display=(108, 32.399998)
```

The NUN5 object and the guarded NA2 port are bit-identical:

```text
pivot=(-54, -16.199999), anchor=(408, 83.439995),
display=(108, 32.399998)
```

The other four table-driven candidates use the same call and differ only by the
selected donor rectangle. Later guarded runtime probes proved that this object
is not the visible rank-label layer, so its matching fields do not establish
the placement of any of the five visible labels.

### State behavior, evidence, and confidence

`FUN_007168F0` updates the five cloud positions every frame and draws the common
footer. `FUN_00716E90` owns the row reveal and rank-stamp sprite state. The
patch changes atlas geometry, anchors, and the rank sprite pivot only; it does
not change result values, rank selection, tally timing, input, sound, stamp
rotation, texture identity, or the common title pulse. NA2 and NUN5 title
controllers call the same pulse algorithm, so static title-size differences
between independently timed screenshots are expected phase differences.

Evidence consists of the complete paired BTL functions, the NUN5 boot-ELF
helpers, exact canonical bytes, task-owned slot-1-to-screen-2 transitions, and
live sprite-object fields. A useful negative result is that patching the static
tables into an already-constructed screen-2 savestate leaves the old cloud
sprite geometry resident; the visual proof must enter screen 2 fresh from slot
1. The fresh transition removes every animated `Ninja Song` fragment.

The donor tables, result-label geometry, title, footer, and cloud behavior are
**runtime-proven** with **verified confidence**. The rank-label placement is
still unresolved and must not be described as accepted or fully runtime-proven.

### 2026-07-26 visible rank layer and donor-column adaptation

A zoomed user runtime capture proved that the red rank text remains about 11
source rows too low inside the rotated stamp. `Outstanding!` is only one value;
the official atlas packs all five values into a shared 96-by-220 column.

The paired settled candidate objects were located by the exact
`display=(108,32.399998), rect=(0,48,80,24)` signature:

| Game | Object | Pivot | Anchor | Display |
| --- | --- | --- | --- | --- |
| NUN5 `SLES-55605 (C071D4C1).02.p2s` | `0x00BED7B0` | `(-54,-16.199999)` | `(408,83.439995)` | `(108,32.399998)` |
| Current `SLOP-NA228 (D61F4C01).09.p2s` | `0x00C6E140` | `(-54,-16.199999)` | `(408,83.439995)` | `(108,32.399998)` |

Their scalar fields and corresponding parent scalar fields match. Two guarded
task-clone trials then disproved the assumption that this object controls the
visible label:

- changing both the `localization__ui_layout__battle_results_na2_btl_at_002100b0` live Y constant at `0x007173E8` and the
  object's anchor Y at `0x00C6E194` by `-16` pixels persisted in a fresh state
  but changed zero visible rank pixels;
- changing the first donor rectangle U at `0x005B13A0` from `0` to `80` and
  the object's U field at `0x00C6E1A8` from `0` to `80 << 4` still displayed
  `Outstanding!` unchanged.

The task clone produced different 750-millisecond and 3-second frames, proving
that these were fresh renders rather than stale embedded screenshots. The
object is therefore a hidden, occluded, or secondary layer and must not be used
as placement evidence.

The current state contains the exact official NUN5 indexed TEX body at
`0x01C59200`; the paired NUN5 state contains the same body at `0x01C69400`.
The clean NA2 TEX body is absent. The visible mismatch is therefore not a
failed donor import. Decoding the 512-by-256 donor atlas locates the five red
labels in visual top-left region X=`416..511`, Y=`0..219`. Its first 11 rows
are fully transparent.

A guarded state-only trial moved that complete donor region upward by 11 rows
and cleared the vacated bottom rows with the donor's transparent palette
index. `Outstanding!` then matches the NUN5 stamp placement. The production
mapping `UI-NINKA-001` expresses the same operation as
`indexed_shift_region_up_11_416_0_96_220`: it begins with the complete official
NUN5 `XNINKA.CCS`, rejects non-indexed layouts or out-of-bounds regions, and
rejects any source whose discarded top rows contain visible pixels. No stored
replacement asset is used.

Per user instruction, this canonical change was left for the normal pipeline
and no ISO was built in this iteration. The donor identity, loaded texture
identity, hidden-object negative result, and `Outstanding!` state-only trial
are **runtime-proven** with **high confidence**. The full five-value production
result remains **awaiting normal-build runtime validation** and is not
user-accepted.

### 2026-07-26 matched five-value baseline reset

The user directed a clean matched capture after the whole-column trial mixed
neighboring 44-row label cells. The canonical baseline therefore removes only
rank-specific interventions: `localization__ui_layout__battle_results_na2_btl_at_002100b0` no longer replaces the NA2 rank
renderer, and `UI-NINKA-001` now uses `transform=copy`, preserving the complete
official NUN5 `XNINKA.CCS` payload and its atlas unchanged. The other twelve
`ui_layout_battle_results` edits remain active.

This reset does not reject the donor container or the five one-to-one atlas
cells. It removes the two corrections that obscured untouched behavior so five
matched NUN5/NA2.28 savestate pairs can establish the per-value geometry. The
previous whole-column production claim is superseded; its `Outstanding!`
single-value trial remains useful historical evidence only.

The resulting normal-pipeline baseline was captured as matched ss2-ss6:

| Slot | Rank artwork | Current baseline |
| --- | --- | --- |
| 2 | `Outstanding!` | correct label identity; untouched placement |
| 3 | `Try harder!` | mixed neighboring atlas area |
| 4 | `Keep trying` | mixed neighboring label cells |
| 5 | `Good job!` | mixed `Good job!` / `Keep` artwork |
| 6 | `Nicely done!` | correct label identity; untouched placement |

The source/copy hashes are recorded under
`@work/UI translation/inputs/sstates/battle_results_rank_baseline_ss02_06_20260726/`.
All ten protected-library copies verified byte-identical. This five-value
baseline is **user-supplied runtime evidence** with **high confidence**; the
replacement geometry is resolved by the following selector-table finding.

### 2026-07-26 visible rank-stamp selector table

The visible rotated red stamp is a second rank path, separate from the hidden
table-driven sprite documented above. The matched states identify the complete
selector sequence and its stable controller:

| Game | Controller | Animation pointer | `rank` byte at `+0x15C` across ss2-ss6 |
| --- | --- | --- | --- |
| NUN5 | `0x00BD98A0` | `0x00BEDBA0` | `4,0,1,2,3` |
| NA2.28 | `0x00C6F2A0` | `0x00C6F0B0` | `4,0,1,2,3` |

Those indices map to `Outstanding!`, `Try harder!`, `Keep trying`,
`Good job!`, and `Nicely done!` in the supplied slot order. The underlying
tables are:

| Game/table | Index 0 | Index 1 | Index 2 | Index 3 | Index 4 |
| --- | --- | --- | --- | --- | --- |
| NA2 BTL file `0x2100B0`, live `0x008C3FB0` | `(352,200,64,56)` | `(416,168,64,56)` | `(416,112,64,56)` | `(416,56,64,56)` | `(416,0,64,56)` |
| NUN5 English SLES file `0x4DDCE0`, live `0x005DDB60` | `(416,176,96,44)` | `(416,132,96,44)` | `(416,88,96,44)` | `(416,44,96,44)` | `(416,0,96,44)` |

NUN5's language-pointer table at live `0x005BB390` addresses five copies of
the same rank records at `0x005DDB60`, `0x005DEE90`, `0x005E14F0`,
`0x005E01C0`, and `0x005E2820`. The first canonical copy occurs at SLES file
`0x4DDCE0`. In NA2 ss2, the pointer stored at live `0x00604CF4` is
`0x008C3FC8`, proving that index 3 is the subtraction baseline.

The exact visible-stamp functions are:

| Role | NA2 v2.28 | NUN5 |
| --- | --- | --- |
| Rank-stamp selector/draw | BTL file `0x63B60`, Ghidra `FUN_00717A20` | BTL file `0x668F0`, Ghidra `FUN_0072D5B0` |
| Rectangle normalization | resident `FUN_0037DA40` | resident `FUN_0038C9C0` |
| Animation object lookup | resident `FUN_001BAB40` | resident `FUN_001BF290` |
| Per-model texture offset | resident `FUN_00198840` | resident `FUN_0019BD70` |

Practical reconstruction:

```cpp
Rect selected = rankRects[result->rank_15c];
Rect baseline = rankRects[3];
float u = float(selected.x - baseline.x) / 512.0f;
float v = 1.0f - float(selected.y - baseline.y) / 256.0f;
Model *stamp = findAnimationModel(result->stampAnimation_11c);
setModelTextureOffset(stamp, fixed12(u), fixed12(v), 0, 0);
```

The NA2 C export ends after `FUN_001BAB40`, but that is an export gap rather
than missing game code. Raw BTL bytes continue with the same float-to-fixed12
conversion and call the exact NA2 homolog `FUN_00198840`. A renderer port,
code cave, or authored call sequence is therefore unnecessary and would
duplicate existing behavior.

The complete official NUN5 `XNINKA.CCS` remains the internally coherent donor.
Its stamp animation has 21 frames and no material/UV controller; its stamp
model uses the same UVs as NA2 but English-aspect geometry. Selection belongs
to the BTL rectangle table, not the model defaults. `localization__ui_layout__battle_results_na2_btl_at_002100b0` therefore
copies exactly the five NUN5 records from SLES file `0x4DDCE0` to NA2 BTL file
`0x2100B0`. Because index 3 is copied with the other records, the existing
delta calculation stays coherent. The edit changes no result value, selector
index, animation, position, rotation, timing, input, or model code.

The table identity, controller/index sequence, function homologs, and guarded
donor bytes are **statically verified with high confidence**. The user
explicitly verified the normal-pipeline result for all five rank stamps on
2026-07-26, so the canonical correction is **runtime-proven and
user-accepted**.

### 2026-07-26 Ninja Song details-footer regional anchors

The Ninja Song details screen has its own footer renderer; it is not the
already-correct Battle Results summary footer:

| Game | Function | Runtime range | BTL file range |
| --- | --- | --- | --- |
| NA2 | `FUN_007182E0` | `0x007182E0..0x00718920` | `0x64420..0x64A60` |
| NUN5 | `FUN_0072DEA0` | `0x0072DEA0..0x0072E5B0` | `0x671E0..0x678F0` |

Both functions draw the same two semantic prompt groups at Y=`348`. NA2 loads
literal X=`395` and X=`470`. NUN5 loads the same nominal values, then adds its
resident regional globals before calling the homologous common compositor:

```cpp
draw_common_prompt(395.0f - 20.0f, 348.0f, prompts, NEXT, true);
draw_common_prompt(470.0f - 8.0f, 348.0f, prompts, BACK, true);
```

The paired task-owned ss8 screenshots independently measure the NA2 groups
`+25` and `+10` output pixels right of NUN5. At the games' 512-logical-pixel
width rendered to 640 pixels, those are exactly `+20` and `+8` game units.
The complete paired functions provide the same result: NUN5 reads
`iGpffff9a7c` before the nominal 395 call and the already-established
`iGpffff9a78=-8` before the nominal 470 call. NA2 has neither addition.

`localization__ui_layout__battle_results_na2_btl_at_000649cc` replaces the NA2 instruction pair at file `0x649CC`
(`0x0071888C`) with X=`375` (`BB43023C00804234`).
`localization__ui_layout__battle_results_na2_btl_at_000649f4` replaces the word at file `0x649F4` (`0x007188B4`) with
X=`462` (`E743023C`). These are authored same-register ports because NUN5's
GP-relative globals are not ABI-compatible with NA2. The proven summary-footer
call sites at `0x62B24..0x62B5B` remain untouched.

A useful negative result is that the ss8 state already contained the complete
earlier `ui_layout_battle_results` summary-footer bytes, including X=`287`, Y=`356`, and the
localized record-2 geometry. Reapplying or changing those rows would target
the wrong screen. The two new rows are **statically verified with high
confidence** and remain **awaiting normal-build runtime and user validation**.
