# Battle UI item-status paths

Binary identities and address conventions are defined in the [Battle UI index](README.md#binary-identities-and-address-convention).

## Current NA228 storage ownership

The behavior of the current committed NA228 build is the oracle for this
storage-only refactor. The native common updater beginning at BTL file
`0x59EA0` remains intact through the prefix immediately before file `0x59F30`.
A guarded jump at `0x59F30` enters
`localization_item_status_update_tail_bridge`; the hook delay preserves the
native object in `a0`, and the bridge supplies the native transformed position
at `sp+0x30` before calling resident C. C owns the clamp, smoothing, foreground
origin, width scale, variant, bubble draw, and class dispatch tail. The bridge
then rejoins the native restore/return epilogue at BTL file `0x5A098`, live
`0x0070DF98`.

The record-`0x80` bubble uses the native transformed position at `sp+0x30`.
The class foreground uses the separate `sp+0x20` copy plus `(0,-33)`. Keeping
those pointers distinct preserves the accepted bubble-to-foreground spacing.
The bubble variant still comes from the native resource lookup at `0x00377CB0`
and preserves the native state-to-variant mapping; the refactor does not invent
a replacement resource identity or state rule.

The four class draws are resident C entries reached through guarded full-draw
hooks:

| Class | BTL file | Live | Ghidra | Resident entry |
| --- | ---: | ---: | ---: | --- |
| Numeric | `0x5A290` | `0x0070E190` | `0x0070E150` | `localization_item_status_numeric_draw` |
| Single | `0x5AB90` | `0x0070EA90` | `0x0070EA50` | `localization_item_status_single_draw` |
| Paired | `0x5ADC0` | `0x0070ECC0` | `0x0070EC80` | `localization_item_status_paired_draw` |
| Fixed | `0x5B0F0` | `0x0070EFF0` | `0x0070EFB0` | `localization_item_status_fixed_draw` |

Resident C owns the accepted per-class record mapping, geometry, width scales,
rotation, and native draw routing. Numeric, paired, and fixed foregrounds call
`localization_item_status_foreground_draw`, an exact 500-byte current-NA228
renderer body authored in `src/localization/ui/item_status_renderer.S` and
stored in `PRG/228.BIN`. Its SHA-256 is
`A39D248B11539514FA49523952E09755DA57649ED0A03A09CEBA2081C3011A2F`.
The single class retains the native uniform wrapper. No item-status executable
payload is stored in a BTL or boot-ELF code cave.

Exactly seven static item-status data edits remain:

- `e__localization__ui_layout__item_status_numeric` / `health_record`;
- `e__localization__ui_layout__item_status_numeric` / `chakra_record`;
- `e__localization__ui_layout__item_status_numeric` / `recovery_record`;
- `e__localization__ui_layout__item_status_paired` / `rank_offset_table`;
- `e__localization__ui_layout__item_status_paired` / `records_8e_through_94`;
- `e__localization__ui_layout__item_status_paired` / `records_9b_and_9c`;
- `e__localization__ui_layout__item_status_single` / `records_96_through_9a`.

The substitution-doll pickup record documented below belongs to its separate
feature and is not one of those seven item-status edits.

The historical runtime evidence below continues to verify the accepted NA228
behavior. The resident-storage refactor itself is uncommitted and currently
has static source/ABI, renderer-hash, catalog, and production-resolution
validation only. No runtime or E2E run has validated the refactored storage
path; that validation remains user-only.

## Paired item-status labels

### Identity and address map

| Role | NA2 | NUN5 |
| --- | --- | --- |
| Binary identity | `PRG/BTL.BIN`, SHA-256 `56FD042740221E3CC91417194F147142799D51FE70642273F4E97BD389D5D63C` | `PRG/BTL.BIN`, SHA-256 `7E8518DA7BD4957AF18CB0ABABE67F0E9B37C42C6551375201B15997F0A3DFE3` |
| Pair factory | file `0x596F0`, Ghidra `FUN_0070D5B0`, archived live `0x0070D5F0` | file `0x5B940`, archived live `0x00722640` |
| Shared update | file `0x59EA0`, Ghidra `FUN_0070DD60`, archived live `0x0070DDA0` | file `0x5C110`, archived live `0x00722E10` |
| Pair draw | file `0x5ADC0`, Ghidra `FUN_0070EC80`, archived live `0x0070ECC0` | file `0x5D3F0`, archived live `0x007240F0` |
| Rank offsets | file `0x1E4C90`, archived live `0x00898B90` | file `0x1ED870`, archived live `0x008B4570` |

The boot-ELF table records are copied from NUN5 `SLES_556.05`
`0x4B86F8..0x4B874B` and `0x4B8794..0x4B87AB` into the homologous NA2
`SLPS_258.37` ranges `0x4B1208..0x4B125B` and
`0x4B12A4..0x4B12BB`. These are item codes `0x8E..0x94` and
`0x9B..0x9C`. The BTL rank table is copied as one 24-byte donor range.

### Reconstructed behavior

The paired path can be summarized as:

```cpp
float widthScale = normalizeDonorWidth(itemCode);
Vec2 foregroundOrigin = {0.0f, -33.0f};
PairLayout layout = pairLayout(rank, row, widthScale);
drawBubble(transformed, widthScale, 1.0f, layout.rotation);
drawPairForeground(
    transformed + foregroundOrigin,
    layout.x,
    layout.y,
    widthScale,
    1.0f,
    layout.rotation
);
```

NUN5 carries independent horizontal and vertical scale values through its
sprite call. NA2's homolog originally reused one value and its object offset
`+0x40` is a next pointer rather than NUN5's scale field. Copying the NUN5
implementation wholesale would corrupt the NA2 object chain. The resident C
tail and paired draw entry therefore derive the accepted values without
changing the NA2 object layout. The exact anisotropic foreground renderer is
the resident assembly body identified above; the former BTL padding helpers
and constants are not current storage.

Relative to the native transformed position, the class-foreground origin
changes from NA2 `(-33,-42)` to `(0,-33)`; the bubble stays at the unshifted
native position.
The complete NUN5 rank offsets are `(20,-30)`, `(-64,-63)`, and `(0,-96)`;
NA2 had `(50,-20)`, `(-16,-62)`, and `(30,-104)`.

### Shared foreground fade correction

The Character Items transition uses the same anisotropic sprite behavior for
paired, numeric, and fixed foregrounds; single labels retain the native uniform
wrapper. The boot-ELF homologs from which the accepted foreground behavior was
reconstructed are:

| Role | NA2 | NUN5 |
| --- | --- | --- |
| Resident renderer | `SLPS_258.37` file `0x277160`, runtime `FUN_00377060` | `SLES_556.05` file `0x284280`, runtime `FUN_00384100` |
| Centered-offset instruction | file `0x2772F4`, runtime `0x003771F4`, `87A80046` / `neg.s f2,f21` | file `0x284418`, runtime `0x00384298`, `87B00046` / `neg.s f2,f22` |

Both homologs receive horizontal scale, alpha, and rotation separately. The
ported NA2 prologue places scale in `f22`, alpha in `f21`, and rotation in
`f20`, matching NUN5. The renderer scales the sprite dimensions with `f22` and
stores `f21` at sprite offset `+0x40` as alpha. Its remaining NA2 instruction
then incorrectly rebuilt the centered local offsets from `f21`:

```cpp
sprite->localX = -(alpha * sprite->width) / 2.0f;
sprite->localY = -(alpha * sprite->height) / 2.0f;
sprite->alpha = alpha;
```

NUN5 instead uses `f22`, yielding:

```cpp
sprite->localX = -(scale * sprite->width) / 2.0f;
sprite->localY = -(scale * sprite->height) / 2.0f;
sprite->alpha = alpha;
```

This explains why Current NA2.28 looked like the foreground slid into and out
of the bubbles while NUN5 and clean NA2 faded in place. In the paired fade-in
state, the three representative local offsets were `-4.2`, `-13.8`, and
`-3.0`: exactly the intended `-7`, `-23`, and `-5` offsets multiplied by
alpha `0.6`. After copying NUN5's single instruction, a fresh rendered state
at alpha `0.7` retained the full `-7`, `-23`, and `-5` offsets. A fade-out
state retained those offsets through alpha `0.0`.

The earlier hypothesis that the BTL wrapper passed its anisotropic arguments
in the wrong order was disproven: changing that order moved the bubbles and
did not correct the foreground transition. No object field, timing, atlas, or
item-effect change is needed. The earlier accepted implementation copied the
single NUN5 instruction at boot-ELF file `0x2772F4`; current storage instead
preserves the complete accepted 500-byte renderer body in the exact resident
assembly fragment, so no static boot-ELF renderer edit remains. Confidence is
**verified** from both preserved ELF exports, exact clean-file bytes, paired
saved-memory fields, and fresh isolated runtime captures.

### Evidence and limits

Evidence consists of paired BTL/ELF disassembly, unique guarded byte ranges in
the canonical binaries, archived Slot 7 live-memory reconstruction, and the
accepted paired raster checkpoint. The final controller, both foreground
labels, and white-bubble bounds match NUN5; a one-pixel bubble-top difference
tracks normal pulse timing. A wholesale transplant into other item classes
remains invalid because those classes use different constructors and geometry;
the numeric class instead has the bounded port documented below. Confidence in
the paired-class mapping and patch is **verified**.

## Numeric item-status labels and recovery values

### Identity and address map

The binary identities and loaded overlay bases are the same as in the paired
section: NA2 BTL file offset `x` maps to EE `0x006B3F00 + x`; NUN5 BTL file
offset `x` maps to EE `0x006C6D00 + x`.

| Role | NA2 | NUN5 |
| --- | --- | --- |
| Numeric factory | file `0x5A1D0`, Ghidra `FUN_0070E0D0` | file `0x5C530`, Ghidra `FUN_00723230` |
| Numeric full-draw hook | file `0x5A290`, live `0x0070E190`, Ghidra `FUN_0070E150` | file `0x5C5B0`, Ghidra `FUN_007232B0` |
| Top localized label | file `0x5A300`, Ghidra `FUN_0070E200` | file `0x5C660`, Ghidra `FUN_00723360` |
| Lower Recovery label | file `0x5A450`, Ghidra `FUN_0070E350` | file `0x5C870`, Ghidra `FUN_00723570` |
| Numeric value draw | file `0x5A760`, Ghidra `FUN_0070E660` | file `0x5CC30`, Ghidra `FUN_00723930` |

The three complete boot-ELF item records are exact official donor copies:

| Record | NA2 `SLPS_258.37` destination | NUN5 `SLES_556.05` source |
| --- | ---: | ---: |
| Health `0x81` | `0x4B116C` | `0x4B865C` |
| Chakra `0x82` | `0x4B1178` | `0x4B8668` |
| Recovery `0x8D` | `0x4B11FC` | `0x4B86EC` |

### Reconstructed behavior

NUN5's numeric dispatcher calls its localized top and lower label paths with
different constants than NA2:

```cpp
void drawNumericItem(ItemObject *item, Vec4 position) {
    drawTopLabel(item, position, 22, 20);
    drawRecoveryLabel(item, position, 37, 37);
    drawRecoveryDigits(item, position);
}

void drawTopLabel(ItemObject *item, Vec4 position, int x, int y) {
    ItemRecord record = officialItemRecord(item->code);
    position.x -= record.width / 2;
    position.x += x;
    position.y += y;
    float angle = 0.0f;
    if (record.code == 0x82 || record.code == 0x99) {
        position.x -= 14.0f;
        position.y -= 14.0f;
        angle = PI / 2;
    }
    drawLocalizedRecord(record, position, angle);
}
```

The NUN5 digit path first establishes a negative-50 X origin and then adds
`14/23/32`, `18/28`, or `24` for three-, two-, or one-digit values. NA2's
object layout and renderer call ABI differ, so copying the complete NUN5
functions is unsafe. `ui_layout_item_status_numeric` instead:

- imports the three exact NUN5 records;
- enters resident C through the full-draw hook at BTL file `0x5A290`;
- reproduces the accepted top and lower record mapping, centering, anchors, and
  rotations before calling the exact resident foreground renderer;
- passes a negative-50 X origin to the retained native digit draw, producing
  the accepted `-36/-27/-18`, `-32/-22`, and `-26` positions.

Those transformed digit positions still equal the donor additions minus the
donor negative-50 origin. Current C owns that origin once, so the former six
individual digit-position instruction edits are no longer stored. Copying the
donor instructions literally would still apply the origin twice.

### Side effects, evidence, and confidence

The patch changes only record selection and geometry passed to the item sprite
renderer. It does not change item values, recovery arithmetic, effect timing,
object allocation, object links, or the atlas itself. Resident C keeps rotation
in its own draw state and never uses NUN5's incompatible object `+0x40` scale
field.

Evidence includes complete NA2/NUN5 BTL decompilation and instruction exports,
exact boot-ELF record bytes, the preserved numeric Slot 3 object inventory, a
fresh PINE savestate screenshot containing simultaneous Health and Chakra
labels plus Recovery values, and a settled paired Slot 7 regression capture.
The numeric and paired foregrounds and white-bubble geometry match their NUN5
references at 640x480; remaining subpixel/pulse differences are animation
timing. Confidence is **verified** and the correction is
**runtime-proven**.

## Single item-status labels

### Identity and address map

This section uses the same exact NA2/NUN5 BTL and boot-ELF identities listed
above. Complete-file BTL offsets map to live EE addresses as
`load_base + file_offset`; preserved Ghidra code labels remain `0x40` below
live code addresses because their imports omit the MWo3 header.

| Role | NA2 | NUN5 |
| --- | --- | --- |
| Single constructor | file `0x5AB20`, Ghidra `FUN_0070e9e0` | file `0x5D030`, Ghidra `FUN_00723cf0` |
| Single full-draw hook | file `0x5AB90`, live `0x0070EA90`, Ghidra `FUN_0070ea50` | file `0x5D0A0`, live `0x00723DA0`, Ghidra `FUN_00723d60` |
| Single width update | shared NA2 update at file `0x59EA0` | file `0x5D230`, Ghidra `FUN_00723ef0` |
| Object-code map | file/live `0x1E4CD0` / `0x00898BD0` | file/live `0x1ED8B0` / `0x008B45B0` |
| Single-class vtable | live `0x005DDEC0` | live `0x005EB3D0` |
| Uniform sprite wrapper | boot ELF `FUN_00377720` | boot ELF `FUN_00384800` |

The five object-code maps are byte-identical:

| Object code | Item record |
| ---: | ---: |
| `0x09` | `0x9A` |
| `0x0C` | `0x98` |
| `0x0D` | `0x99` |
| `0x13` | `0x97` |
| `0x12` | `0x96` |

`ui_layout_item_status_single` therefore copies only the complete official NUN5 record range
`0x96..0x9A`, from NUN5 ELF file `0x4B8758..0x4B8793` to NA2 ELF file
`0x4B1268..0x4B12A3`. No authored texture rectangle or mapping row is needed.

### Reconstructed behavior

The homologous draw paths reduce to:

```cpp
void drawSingleStatus(SingleItemObject *object, Vec4 input) {
    uint32_t record = singleRecordForObjectCode(object->code);
    Vec4 position = input;
    position.x += 0.0f;       // NA2 originally added 33
    position.y += 33.0f;      // NA2 originally added 42

    float angle = 0.0f;
    if (record == 0x82 || record == 0x99) {
        angle = 1.5707964f;
    }

    uint32_t resource = lookupItemResource(record);
    uint32_t variant = selectItemRenderVariant(resource, object->state);
    drawUniformItem(variant, record, &position, 1.0f,
                    object->renderParameter, angle);
}

float singleBubbleScale(const SingleItemObject *object) {
    return object->code == 0x09 ? 122.0f / 64.0f : 1.0f;
}
```

The NUN5 `+0x40` scale field cannot be copied into NA2 because the homologous
NA2 field is a next-object pointer. The resident common C tail derives
`1.90625` for object code `0x09` and `1.0` for every other single record; it
also selects the fixed class's exact donor width scale
`102/64 = 1.59375`. The single full-draw C entry uses the native mapping table
and resource lookup, applies pi/2 only to records `0x82` and `0x99`, and calls
the retained native uniform wrapper. The former record-aware rotation helper,
its call, and the two origin instruction edits are no longer stored.

An experimental direct call to the lower anisotropic renderer produced no
foreground because it bypassed the uniform wrapper's distinct argument
shuffle; that approach was rejected and is not an implementation parent.

### Side effects, evidence, and confidence

The patch changes only localized record data, foreground origin, bubble width
scale, and record-specific rotation. It does not change effect selection,
duration, gameplay status, damage, object allocation, object links, resource
identity, or the imported atlas.

Evidence consists of both complete BTL functions, the identical mapping tables,
the unique boot-ELF record ranges, live vtable/object inventories, and fresh
640x480 v31 captures. Paired Slot 10 contains simultaneous `Invisible` and
`Substitution Jutsu`; paired Slot 12 represents the shared poison/status path.
Both current captures match NUN5 bubble bounds, label centers, clipping, and
row placement. The numeric regression remains matched. The valid paired-class
execution slice and shared width behavior are preserved by the resident C
tail; a fresh-process capture can outlive that short notification and is not
used as placement evidence.

Visible single/status behavior is **runtime-proven** with **high confidence**.
Record `0x99` was absent from the captured set, so its quarter-turn remains a
high-confidence static result rather than a runtime-verified one. The exact
fixed-class scale is likewise statically traced until a fixed-class state is
captured.

## Substitution-doll pickup atlas binding

### Identity and address map

This finding uses the boot-ELF identities and file/runtime mappings declared
above. The complete resident item-record tables begin at NA2 runtime
`0x005B0A60` and NUN5 runtime `0x005B7ED0`; each entry is 12 bytes.

| Role | NA2 | NUN5 |
| --- | --- | --- |
| Resident uniform item renderer | file `0x277160`, runtime `FUN_00377060` | file `0x284280`, runtime `FUN_00384100` |
| Table record selected by the live doll effect | index `0x0A`, file `0x4B0BD8`, runtime `0x005B0AD8` | index `0x0A`, file `0x4B80C8`, runtime `0x005B7F48` |
| Active homologous `TEX_xselect` sprite | `0x00E384C0` | `0x00DB5040` |

The resident renderers index their tables by `recordId * 12`, copy the record's
U/V/width/height into the sprite, center it, and call `FUN_001cc350` in NA2 or
`FUN_001d1480` in NUN5. Their resource lookup callees are
`FUN_00376610` / `FUN_00383470` and `FUN_00375180` / `FUN_00381fb0`.
Both live objects retain logical code `0x0A` at sprite offset `+0x0C`. The
restored NA2 sprite initially contains U/V geometry matching record `0x2E`,
but the first resumed updater pass replaces it from record `0x0A`.

### Reconstructed behavior and correction

The matched Slot 4 states reduce the defect to:

```cpp
// Shared logical pickup code in the paired live objects:
recordId = 0x0A;
drawResidentItemSprite(recordTable[recordId]);

// NA2-compatible data port:
na2Record[0x0A] = nun5Record[0x0A];
```

Both active sprites occupy the same pool position, use `TEX_xselect`, retain
30x30 source dimensions and flags `0xC127FFFF`, and differ in anchor by only
three pixels at the captured animation phase. After one updater pass, Current
record `0x0A` supplies `(161,193,30,30)`, which selects the green `Recovery`
artwork from the imported NUN5 atlas. NUN5 record `0x0A` supplies
`(161,225,30,30)`, which selects the substitution doll.
The `ui_layout_item_pickup_doll` group, implemented by
`localization__ui_layout__item_pickup_doll`, therefore performs one guarded
same-index 12-byte copy from NUN5 ELF file `0x4B80C8` to NA2 ELF file
`0x4B0BD8`.

The rejected cross-index copy from NUN5 record `0x0A` to NA2 record `0x2E` is a
useful negative result. It altered only geometry serialized in the restored
frame; the live updater immediately selected record `0x0A` again, and the user
confirmed that a fresh normal build showed no visible change. An exact-guarded
task-owned conversion of NA2 record `0x0A`, resumed for 120 ms, replaced the
visible green label with the doll. Copying the whole table remains unsupported
because the games' other semantic record IDs are not globally aligned. The
bounded same-index donor changes no renderer code, item selection, item
behavior, effect lifetime, animation, or object allocation. The selection and
candidate result are **verified** from exact source bytes, both retained EE
images, and the resumed task-owned state; the integrated normal-build result
remains `approved_for_test` until a fresh post-change capture.

## Fixed two-label item status

### Identity and address map

This section uses the same exact NA2/NUN5 boot-ELF and BTL identities recorded
above. Complete-file BTL offsets map to live code at `load_base + file_offset`;
the preserved Ghidra labels remain `0x40` below the live addresses.

| Role | NA2 | NUN5 |
| --- | --- | --- |
| Fixed constructor | file `0x5B080`, Ghidra `FUN_0070ef40`, live `0x0070EF80` | file `0x5D840`, Ghidra `FUN_00724500`, live `0x00724540` |
| Fixed full-draw hook | file `0x5B0F0`, Ghidra `FUN_0070efb0`, live `0x0070EFF0` | file `0x5D8B0`, Ghidra `FUN_00724570`, live `0x007245B0` |
| Fixed width update | absent from the NA2 object ABI | file `0x5DB20`, Ghidra `FUN_007247e0`, live `0x00724820` |
| Fixed-class vtable | live `0x005DDE80` | live `0x005EB370` |

The class always draws record `0x8E` followed by record `0x8D`. Their complete
official NUN5 rectangles are already imported by `ui_layout_item_status_paired` and
`ui_layout_item_status_numeric`. Fixed behavior is now owned entirely by the
resident full-draw C hook and has no static edit group, texture, or table donor
of its own.

### Reconstructed behavior

The homologous draw paths reduce to:

```cpp
void drawFixedStatus(FixedItemObject *object, Vec4 input) {
    for (const Row row : {{0x8E, 20}, {0x8D, 37}}) {
        Vec4 position = input;
        position.x -= itemRecord(row.record).width / 2;
        position.y += row.yOffset;
        drawUniformItem(1.0f, object->renderParameter, row.record,
                        &position, selectVariant(object, row.record));
    }
}
```

NA2 originally used `(+38,+11)` for record `0x8E` and `(+18,+25)` for record
`0x8D`. NUN5 obtains each live donor width, halves it with signed integer
rounding, subtracts that value from X, then applies `+20` or `+37` to Y. The
NUN5 whole-function body cannot be copied safely because its fixed object owns
a scale at `+0x40`, where NA2 stores the next-object pointer, and it calls a
NUN5-only width-query helper.

The resident fixed C entry directly centers each record from its retained item
table width and applies Y=`20` and Y=`37`. Both draws use zero rotation and the
exact resident foreground renderer. The common C tail selects the exact fixed
bubble scale `102/64 = 1.59375` without touching the NA2 object layout.

### Side effects, evidence, and confidence

A controlled synthetic checkpoint changed the sole paired object in matched
Slot 7 to each game's real fixed-class vtable. Both retained identical
positions and NUN5 offsets; the NUN5 object also received the fixed class's
traced `1.59375` scale. This caused the real fixed draw functions to render
`Status Effect` and `Recovery`. At 640x480, each label has the same center
relative to the white bubble in NUN5 and Current NA2. A four-pixel whole-object
screen delta accompanies a one-frame update/pulse difference and does not
change internal placement.

An earlier experimental v32 helper was rejected before canonical promotion
because its proposed runtime address overlapped live BTL data. V33 established
the accepted geometry through a shared helper and two guarded draw blocks.
Current storage preserves that behavior in the resident common tail and fixed
full-draw C entry; neither the helper nor the two static draw-block edits
remain, and no BTL or boot-ELF code cave is used.

The fixed draw geometry is **runtime-proven** with **high confidence**. It is
not marked verified because the checkpoint transformed a live paired object
rather than capturing a naturally spawned fixed-class notification.
