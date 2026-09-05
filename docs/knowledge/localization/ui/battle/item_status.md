# Battle item-status presentation

## Research coverage

- **Assigned scope:** compare clean NA2 and NUN5 battle item-status renderers and atlas bindings.
- **Exploration depth:** the relevant binaries, native callers, records, and
  paired screen states were examined.
- **Confirmed coverage:** the documented owners, structures, and cross-game
  differences are established.
- **Unresolved or untested:** callers and states not explicitly covered below.
- **Deliberate exclusions and overlap:** feature imports, hooks, and validation
  belong to [UI layout](../../../../features/localization/ui_layout.md) or
  [UI textures](../../../../features/localization/ui_textures.md).
- **Evidence limitations:** bounded states do not cover every animation phase or
  indirect caller.

Binary identities and address conventions are defined in the
[Standard game file identities](../../../game/files/file_identities.md).

## Paired item-status labels

### Identity and address map

| Role | NA2 | NUN5 |
| --- | --- | --- |
| Pair factory | file `0x596F0`, Ghidra `FUN_0070D5B0`, archived live `0x0070D5F0` | file `0x5B940`, archived live `0x00722640` |
| Shared update | file `0x59EA0`, Ghidra `FUN_0070DD60`, archived live `0x0070DDA0` | file `0x5C110`, archived live `0x00722E10` |
| Pair draw | file `0x5ADC0`, Ghidra `FUN_0070EC80`, archived live `0x0070ECC0` | file `0x5D3F0`, archived live `0x007240F0` |
| Rank offsets | file `0x1E4C90`, archived live `0x00898B90` | file `0x1ED870`, archived live `0x008B4570` |

NUN5 `SLES_556.05` ranges `0x4B86F8..0x4B874B` and
`0x4B8794..0x4B87AB` correspond to homologous NA2 `SLPS_258.37` ranges
`0x4B1208..0x4B125B` and `0x4B12A4..0x4B12BB`. These are item codes
`0x8E..0x94` and `0x9B..0x9C`. The corresponding BTL rank table occupies
24 bytes.

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

Relative to the native transformed position, the class-foreground origin
changes from NA2 `(-33,-42)` to `(0,-33)`; the bubble stays at the unshifted
native position.
The complete NUN5 rank offsets are `(20,-30)`, `(-64,-63)`, and `(0,-96)`;
NA2 had `(50,-20)`, `(-16,-62)`, and `(30,-104)`.

### Shared foreground renderer difference

Paired, numeric, and fixed foregrounds use NUN5's anisotropic sprite
behavior; single labels use the native uniform wrapper. The relevant boot-ELF
homologs are:

| Role | NA2 | NUN5 |
| --- | --- | --- |
| Resident renderer | `SLPS_258.37` file `0x277160`, runtime `FUN_00377060` | `SLES_556.05` file `0x284280`, runtime `FUN_00384100` |
| Centered-offset instruction | file `0x2772F4`, runtime `0x003771F4`, `87A80046` / `neg.s f2,f21` | file `0x284418`, runtime `0x00384298`, `87B00046` / `neg.s f2,f22` |

Both homologs receive horizontal scale, alpha, and rotation separately. NUN5
keeps scale in `f22`, alpha in `f21`, and rotation in `f20`; it scales the
sprite dimensions with `f22` and stores `f21` as alpha. Reusing NA2's
centered-offset instruction after adopting that register allocation instead
rebuilds the offsets from alpha:

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

That register mismatch makes the foreground offsets vary with alpha. In a
controlled paired fade, intended offsets `-7`, `-23`, and `-5` became
`-4.2`, `-13.8`, and `-3.0` at alpha `0.6`. Using NUN5's scale register
retained the intended offsets through fade-in and alpha `0.0` fade-out.

Changing the BTL wrapper's anisotropic argument order moved the bubbles and
did not correct the foreground transition. The centered-offset register is the
isolated cause; no object-field, timing, atlas, or item-effect change is
required. Both preserved ELF exports, exact source bytes, saved object fields,
and isolated runtime captures verify the finding.

### Evidence and limits

Evidence consists of paired BTL/ELF disassembly, unique source byte ranges,
live-memory reconstruction, and a paired raster comparison. Both foreground
labels and the white-bubble bounds match NUN5; a one-pixel bubble-top difference
tracks normal pulse timing. Other item classes have different constructors and
geometry, so the paired draw path cannot be transplanted wholesale. Confidence
in the paired-class mapping is **verified**.

## Numeric item-status labels and recovery values

### Identity and address map

| Role | NA2 | NUN5 |
| --- | --- | --- |
| Numeric factory | file `0x5A1D0`, Ghidra `FUN_0070E0D0` | file `0x5C530`, Ghidra `FUN_00723230` |
| Numeric draw | file `0x5A290`, live `0x0070E190`, Ghidra `FUN_0070E150` | file `0x5C5B0`, Ghidra `FUN_007232B0` |
| Top localized label | file `0x5A300`, Ghidra `FUN_0070E200` | file `0x5C660`, Ghidra `FUN_00723360` |
| Lower Recovery label | file `0x5A450`, Ghidra `FUN_0070E350` | file `0x5C870`, Ghidra `FUN_00723570` |
| Numeric value draw | file `0x5A760`, Ghidra `FUN_0070E660` | file `0x5CC30`, Ghidra `FUN_00723930` |

The three relevant boot-ELF item records occupy these homologous ranges:

| Record | NA2 `SLPS_258.37` | NUN5 `SLES_556.05` |
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

The NUN5 digit path establishes a negative-50 X origin and then adds
`14/23/32`, `18/28`, or `24` for three-, two-, or one-digit values. The
resulting positions are `-36/-27/-18`, `-32/-22`, and `-26`. NA2's object
layout and renderer ABI differ, so copying the complete NUN5 functions is
unsafe. The donor origin must be applied exactly once; applying it before
literal donor position edits would apply the origin twice.

### Evidence and limits

The traced draw paths select records and presentation geometry. They do not
own item values, recovery arithmetic, effect timing, allocation, object links,
or atlas content. NUN5's object `+0x40` scale field is incompatible with the
NA2 next-object pointer at the same offset.

Evidence includes complete NA2/NUN5 BTL decompilation and instruction
exports, exact boot-ELF record bytes, live numeric-object fields, and runtime
captures containing simultaneous Health and Chakra labels with Recovery
values. Numeric and paired foreground and bubble geometry match NUN5 at
640x480; remaining subpixel differences follow animation timing. Confidence is
**verified**.

## Single item-status labels

### Identity and address map

| Role | NA2 | NUN5 |
| --- | --- | --- |
| Single constructor | file `0x5AB20`, Ghidra `FUN_0070e9e0` | file `0x5D030`, Ghidra `FUN_00723cf0` |
| Single draw | file `0x5AB90`, live `0x0070EA90`, Ghidra `FUN_0070ea50` | file `0x5D0A0`, live `0x00723DA0`, Ghidra `FUN_00723d60` |
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

The complete official NUN5 record range `0x96..0x9A` occupies NUN5 ELF file
`0x4B8758..0x4B8793`; its homologous NA2 range is
`0x4B1268..0x4B12A3`.

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

The NUN5 `+0x40` scale field cannot be copied into NA2 because the
homologous NA2 field is a next-object pointer. NUN5 uses width scale `1.90625`
for object code `0x09` and `1.0` for every other single record. Record
`0x82` and `0x99` use a quarter-turn; the other mapped records use zero
rotation. The class retains its distinct uniform sprite wrapper.

A direct call to the lower anisotropic renderer produced no foreground
because it bypassed the uniform wrapper's argument shuffle. The two renderer
interfaces are therefore not interchangeable.

### Evidence and limits

The traced native differences concern record data, foreground origin, bubble
width, and record-specific rotation. Effect selection, duration, gameplay
status, damage, allocation, object links, and resource identity are outside
these draw paths.

Evidence consists of both complete BTL functions, identical mapping tables,
unique boot-ELF record ranges, live vtable and object inventories, and runtime
captures of simultaneous single/status notifications. The observed states
match NUN5 bubble bounds, label centers, clipping, and row placement.

## Substitution-doll pickup atlas binding

### Identity and address map

The complete resident item-record tables begin at NA2 runtime
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

### Reconstructed behavior

Matched NA2 and NUN5 runtime states reduce the selection to:

```cpp
// Shared logical pickup code in both live objects:
recordId = 0x0A;
drawResidentItemSprite(recordTable[recordId]);
```

Both runtime sprites use `TEX_xselect`, retain 30x30 source dimensions and
flags `0xC127FFFF`, and differ in anchor by only three pixels at the observed
animation phase. NA2 record `0x0A` supplies `(161,193,30,30)`; NUN5 record
`0x0A` supplies `(161,225,30,30)`. Because the updater selects logical
record `0x0A` in both games, the same-index NUN5 record is the homologous
geometry source.

A cross-index substitution into NA2 record `0x2E` changed restored geometry
only; the next updater pass selected record `0x0A` again. Copying the complete
record table remains unsupported because other semantic record IDs are not
globally aligned. Exact source bytes and matched live objects verify the
same-index mapping.

## Fixed two-label item status

### Identity and address map

| Role | NA2 | NUN5 |
| --- | --- | --- |
| Fixed constructor | file `0x5B080`, Ghidra `FUN_0070ef40`, live `0x0070EF80` | file `0x5D840`, Ghidra `FUN_00724500`, live `0x00724540` |
| Fixed draw | file `0x5B0F0`, Ghidra `FUN_0070efb0`, live `0x0070EFF0` | file `0x5D8B0`, Ghidra `FUN_00724570`, live `0x007245B0` |
| Fixed width update | absent from the NA2 object ABI | file `0x5DB20`, Ghidra `FUN_007247e0`, live `0x00724820` |
| Fixed-class vtable | live `0x005DDE80` | live `0x005EB370` |

The class always draws record `0x8E` followed by record `0x8D`. Their
official NUN5 rectangles are the same records used by the paired and numeric
classes; the fixed class has no separate texture or table donor.

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

NUN5 centers each record from its live table width and applies Y offsets
`20` and `37`. Both draws use zero rotation, and the fixed bubble width scale
is `102/64 = 1.59375`. These values do not require changing the NA2 object
layout.

### Evidence and limits

A controlled class substitution exercised each game's native fixed-class
vtable. Both objects retained identical positions and NUN5 offsets, and the
NUN5 object received the traced `1.59375` scale. The native functions rendered
`Status Effect` and `Recovery` with matching label centers relative to the
bubble at 640x480. A four-pixel whole-object screen delta accompanied a
one-frame pulse difference and did not change internal placement.
