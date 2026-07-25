# Battle UI draw-path mappings

This record preserves the paired NA2/NUN5 battle-overlay findings used by the
texture-only UI correction pass. It covers executable layout and atlas-selection
behavior; command-name text, font metrics, and gameplay input semantics are
outside this boundary.

## Binary identities and address convention

| Game | Binary | Size | SHA-256 | Archived live base |
| --- | --- | ---: | --- | ---: |
| NA2 v2.28 | `@source/NA2.iso.files/PRG/BTL.BIN` | 2,237,184 | `56FD042740221E3CC91417194F147142799D51FE70642273F4E97BD389D5D63C` | `0x006B3F00` |
| NUN5 SLES-55605 | `@source/NUN5.iso.files/PRG/BTL.BIN` | 2,253,184 | `7E8518DA7BD4957AF18CB0ABABE67F0E9B37C42C6551375201B15997F0A3DFE3` | `0x006C6D00` |
| NA2 v2.28 | `@source/NA2.iso.files/SLPS_258.37` | 5,273,256 | `20C0A40D70EA412CD431993A2E189B37ECB6054D63AE93BE545470016E1627AF` | `0x00100000` |
| NUN5 SLES-55605 | `@source/NUN5.iso.files/SLES_556.05` | 5,340,912 | `20A43677397731A2A20899336D1165ACE5B436906B9B89BE90FB10F4558DD19D` | `0x00100000` |

The focused exports are under
`@analysis/disassembly/NA2/exports/BTL.BIN/` and
`@analysis/disassembly/NUN5/exports/BTL.BIN/`. Those projects omit the
40-byte BTL file header when mapping code, so a Ghidra address is the archived
live address minus `0x40`. File offsets below always refer to the complete
source file. For the boot ELFs, the relevant `PT_LOAD` mappings place NA2 file
offset `0x100` and NUN5 file offset `0x180` at runtime `0x00100000`.

## Ordinary awakening-label composition

| Game | Method | ELF file range | Runtime range |
| --- | --- | --- | --- |
| NA2 | `FUN_00303aa0` | `0x203BA0..0x203E3F` | `0x00303AA0..0x00303D3F` |
| NUN5 | `FUN_0030e250` | `0x20E3D0..0x20E68F` | `0x0030E250..0x0030E50F` |

These boot-ELF homologues build the ordinary awakening-name panel. Their
practical behavior is:

```cpp
void buildOrdinaryAwakeningLabel(
    AwakeningPanel *panel,
    int characterIndex,
    int playerSide,
    int activationType
) {
    int textureSlot = lookupTextureSlot(activationType); // 13-entry table
    if (textureSlot < 0) {
        panel->state = 10;
        return;
    }

    panel->playerSide = playerSide;
    panel->activationType = activationType;
    Resource *common = loadMode1CommonResource();
    panel->labelObject = instantiateCharacterLabel(common, characterIndex);
    panel->animationObject =
        instantiate(common, "ANM_mode1name_ca");

    Resource *character = loadCharacterResource(characterIndex + 1, 4);
    Model *panelModel = findModel(panel->labelObject, "MDL_mn_panel");
    Material *material = findMaterial(panelModel, "MAT_joutai");
    Texture *label = findTexture(
        character,
        {"TEX_mode1name1", "TEX_mode1name2", "TEX_mode1name3"}[textureSlot]
    );
    replaceMaterialTexture(material, label);
}
```

The direct callers are NA2 `FUN_00305c30` and NUN5 `FUN_00310580`, through
their character-state construction paths. Important homologous callees include
the common-resource accessors `FUN_001e9220` / `FUN_001ef130`, character
resource lookups `FUN_001e8920` / `FUN_001ee750`, texture lookups
`FUN_001a8f00` / `FUN_001ac950`, and the final texture-copy helpers
`FUN_001988d0` / `FUN_0019be20`.

The complete canonical CVM inventory contains 61 character
`3EYE/3???3PCT.CCS` containers with 72 ordinary awakening textures: 50
containers have one `TEX_mode1name` texture and 11 have two. No third texture
is present in the current inventory, although both executables support
`TEX_mode1name3`. Every used NA2/NUN5 TEX/CLT component signature is compatible.
Three equivalent donor entries use different internal path names:

- NA2 `x\mode1\tex\hnt\mode1name1.bmp` maps to NUN5
  `x\mode1\tex\hnw\mode1name1.bmp`;
- NA2 `x\mode1\tex\row\mode1name1.bmp` maps to NUN5
  `x\mode1\tex\roc\mode1name1.bmp`;
- NA2 `x\mode1\tex\tnd\mode1name2.bmp` maps to NUN5
  `x\mode1\tex\tnw\mode1name2.bmp`.

`MODENAME/MODE1CMN.CCS` supplies the shared animation, model, and placeholder
material. Its NA2 and NUN5 non-texture sections are byte-identical; only the
placeholder TEX/CLT data differs. The game already substitutes the
character-specific texture at runtime, so the localized implementation imports
only the 72 official NUN5 TEX/CLT component ranges into their 61 fixed-size NA2
containers. No stored texture blobs, whole-container replacement, executable
layout patch, or `MODE1CMN.CCS` replacement is required.

Evidence: the exact boot-ELF identities above, the preserved C/TXT exports at
`@analysis/disassembly/NA2/exports/SLPS_258.37/` and
`@analysis/disassembly/NUN5/exports/SLES_556.05/`, a complete canonical CVM
inventory, decoded RGBA equality for all 72 mappings, component-range diff
containment, and exact fixed-size recompression of all 61 targets. The
compositor interpretation and donor coverage have **high confidence**;
in-game runtime acceptance remains pending.

## Open VS Jutsu selector

### Homologous methods

| Game | Method | File range | Ghidra range | Archived live range |
| --- | --- | --- | --- | --- |
| NA2 | `FUN_006bd4d0` | `0x9610..0x9C5F` | `0x006BD4D0..0x006BDB1F` | `0x006BD510..0x006BDB5F` |
| NUN5 | `FUN_006d0850` | `0x9B90..0xA1BF` | `0x006D0850..0x006D0E7F` | `0x006D0890..0x006D0EBF` |

Both methods render the open two-row Jutsu selector. They are reached through
the confirmation-screen state object's indirect method dispatch, so the
exports do not expose a single direct caller. Their closed-selector siblings
are NA2 `FUN_006bd0f0` and NUN5 `FUN_006d0470`. Important callees are the
regional row compositor (`FUN_006bcb70` / `FUN_006cfe70`), the animation pulse
helper (`func_0x0016f2e8` / `func_0x001700a8`), and the native sprite draw
routine (`func_0x0037bc40` / `func_0x0038ad00`).

NUN5's stable behavior is equivalent to:

```cpp
void drawOpenJutsuSelector(Selector *self) {
    drawRowsAndSelectedEntry(self);

    if (self->selectedRowHasAtLeastThreeJutsu()) {
        Sprite *sprite = self->arrowSprite;
        float centerX = self->playerSide == 0 ? 115.0f : 409.0f;
        float centerY = self->selectedRow * 68.0f + 210.0f;
        float pulse = animationPulse(self->pulseState) * 6.0f;

        // NUN5 has no closed-selector horizontal-arrow draw here.
        sprite->flags &= ~FLIP_VERTICAL;
        sprite->rotation = +PI / 2.0f;
        drawSprite(centerX, centerY - 56.0f - pulse,
                   sprite, localizedGreenArrow);
        sprite->rotation = 0.0f;

        sprite->flags |= FLIP_VERTICAL;
        sprite->rotation = -PI / 2.0f;
        drawSprite(centerX, centerY + 56.0f + pulse,
                   sprite, localizedGreenArrow);
        sprite->rotation = 0.0f;
        sprite->flags &= ~FLIP_VERTICAL;
    }
}
```

NA2 differs in three related ways:

1. it calls the closed-selector horizontal-arrow draw twice at file offsets
   `0x9AE4` and `0x9B1C` even while the selector is open;
2. it never writes either `+pi/2` or `-pi/2` before the vertical draws at
   `0x9BA0` and `0x9BFC`;
3. its static rectangle at `0x20C9E0` is `(139,257,38,22)`, whereas NUN5's
   localized accessor `FUN_003d4760(0)` resolves to the official English ELF
   record `(145,385,22,38)` at file offset `0x4DE0F0`.

The original NA2 atlas coordinate contains a vertical green triangle. After
the complete official NUN5 `VS.CCS` import, that coordinate samples lettering;
NUN5's replacement record points right and relies on opposite rotations.

### Rejected unscoped ports

The first port copied the NUN5 rectangle and angle loads, redirected both draws
through a reset wrapper, and wrote the angle in each call delay slot. Guarded
live-memory reconstruction proved why that was insufficient:

- NA2's active arrow sprite was at `0x00C7B820`; its rotation field at
  `+0x4C` (`0x00C7B86C`) read back the exact `-pi/2` bit pattern after the
  lower draw, yet the captured arrow still pointed right;
- NUN5's corresponding object was at `0x00BFC420` and consumed the rotation;
- cloning the NUN5 object control fields persistently suppressed unrelated UI;
  partial draw-scoped field tests either had no effect or produced malformed
  sampling;
- disabling the rotation reset did not change the rendered direction.

These are useful negative results: writing a valid rotation float is not enough
to enable rotation while the NA2 sprite remains in mode 0, and NUN5's mode
fields cannot safely remain enabled across the shared object lifetime. A
temporary texture graft that restored NA2's old vertical pixels rendered the
arrows but deliberately diverged from the canonical NUN5 asset, so it was also
rejected rather than retained as a special texture-engine transform.

### Accepted draw-scoped compatibility port

`UI-VS-001` remains a byte-for-byte whole NUN5 donor. `UI-BTL-007` replaces the
now-unwanted horizontal blocks at file `0x9ABC..0x9B23` with a branch over a
compact helper stored inside those same dead blocks. The main path resumes at
file `0x9B38`; no shared BTL-header cave is used. The upper and lower paths copy
NUN5's exact angle loads from `0xA06C/0xA070` and `0xA0F4/0xA0F8`, store the
angle in the sprite, and call the helper from `0x9BA0` and `0x9BFC`. The exact
NUN5 record `(145,385,22,38)` is copied from ELF `0x4DE0F0` to BTL `0x20C9E0`.

The helper's practical reconstruction is:

```cpp
void drawLocalizedSelectorArrow(Sprite *sprite) {
    configureSpriteMode(sprite, 10, 1);       // NA2 FUN_001cbe40
    if (bit_cast<int>(sprite->rotation) < 0)
        sprite->flags |= 0x40;                // lower-arrow flip
    drawSpriteRecord(sprite, (Rect *)0x008C08E0); // FUN_0037bc40
    flushSprite(sprite);                      // FUN_001cc070
    configureSpriteMode(sprite, 10, 0);
}
```

The crucial behavior is the flush while mode 1 is still active; restoring mode
0 before flushing loses or corrupts the queued rotated primitive. The helper
uses only `s0` and `s3`, which are dead at both completed loop call sites, to
preserve the sprite and return address without a stack frame. Its only lasting
state change is the existing lower-arrow flip expected by the surrounding
method. The closed sibling `FUN_006bd0f0` and every other VS object remain
untouched.

The final hidden, muted isolated run produced correct upper and lower arrows,
no horizontal arrows, and no bottom fragment. The user accepted the paired
screen as perfect. The NUN5 screenshot SHA-256 is
`46A1A578B45019A0A59FD00DA559AD666637A7BAFB288D5D652FC78CDB7A3FFD`;
the corrected NA2 screenshot SHA-256 is
`230102B88B21B3AFB9CB9BF75E0D6BD017F64B56F4756427E204DA7C051962A8`.
Evidence also includes paired EE memory, exact Ghidra structural comparison,
canonical file-byte guards, decoded atlases, and guarded PINE readback.
Confidence and runtime acceptance are **verified**.

## VS confirmation prompts and bottom legends

NA2 `FUN_006c0cc0` and NUN5 `FUN_006d4130` are the homologous confirmation
draw methods. Both draw the selection prompts and then reuse one sprite for the
bottom OK and Back legends. Their practical ending is:

```cpp
drawOk(anchorOk, 356.0f, promptSprite, 0);
drawBack(anchorBack, 356.0f, promptSprite, 1);
```

NUN5's boot-ELF table at file `0x4DE9F0` (runtime `0x005DE870`) contains the
complete Cross/OK `(1,1,56,22)` and Triangle/Back `(1,25,64,22)` records. NA2's
homologous table at file `0x4D4790` (runtime `0x005D4690`) instead contains two
70x22 regional records and `FUN_0037c980` optionally draws a separate input
glyph before each label. `UI-BTL-005` copies the complete 16-byte NUN5 table and
sets the two call-site glyph arguments to zero at BTL `0xD014` and `0xD038`.

The wrapper implementations are not byte-equivalent: their queued-sprite
advancement makes NUN5's nominal anchors `400/470` render differently when
inserted unchanged into NA2. Two measured NA2 calibrations established the
exact compatible anchors. `400/470` rendered the imported records 15/10 pixels
right of the reference; `384/460` rendered them 5/3 pixels left. The converged
NA2 constants `388/462`, at BTL `0xCFFC` and `0xD020`, match both NUN5 legends
at `dx=0, dy=0`.

The same patch now copies only the X-immediate halfword of NUN5's X=`260`
Customize Jutsu instruction from BTL `0xD6A8` into NA2 `0xCF70`, retaining
NA2's destination register. Contrary to the earlier provisional conclusion,
X=`260` does not wrap once the selector state is corrected; it places the full
Circle prompt exactly like NUN5. Text and font rendering are not modified.

Evidence: complete-function comparison, boot-ELF `PT_LOAD` mapping, guarded
live records and instructions, v19/v20/v21 paired raster calibration, and the
same accepted screenshot hashes above. Confidence and runtime acceptance are
**verified**.

## Command Menu and Command Chart scroll indicators

### Shared renderer and record

| Game | Method | File range | Ghidra range | Archived live range | Rectangle record |
| --- | --- | --- | --- | --- | --- |
| NA2 | `FUN_00878820` | `0x1C4960..0x1C530F` | `0x00878820..0x008791CF` | `0x00878860..0x0087920F` | file `0x21D648`, live `0x008D1548` |
| NUN5 | `FUN_00894f60` | `0x1CE2A0..0x1CEC1F` | `0x00894F60..0x008958DF` | `0x00894FA0..0x0089591F` | file `0x2214D8`, live `0x008E81D8` |

These methods are draw callbacks beneath the shared Practice/Free Battle
command controller (`ccStartMenuPrivateCmd`, tracked as `BTL-N001`). Their
direct caller is indirect in the exported state-object dispatch. Important
callees are the row/text compositors, texture-layer accessor
`FUN_0087c3d0` / `FUN_00898c40`, native sprite draw
`func_0x0037bc40` / `func_0x0038ad00`, and sprite release helper
`func_0x001cc070` / `func_0x001d1180`.

The lower part of both methods is equivalent to:

```cpp
Sprite *arrow = getTextureLayer(3);
arrow->rotation = PI;
drawSprite(256.0f, 32.0f + pulse, arrow, scrollArrowRect);
arrow->rotation = 0.0f;
drawSprite(256.0f, 348.0f - pulse, arrow, scrollArrowRect);
releaseSprite(arrow);
```

NA2 and NUN5 already agree on this behavior. Only the shared rectangle differs:

- NA2: `(194,195,20,20)`, bytes `C200C30014001400`;
- NUN5: `(1,225,20,22)`, bytes `0100E10014001600`.

With the imported NUN5 `TEX_xselect`, the NA2 rectangle selects green text
fragments, while the NUN5 rectangle selects the orange vertical-scroll
triangle. Paired Slots 5 and 6 reuse the same Current object at `0x00E6A500`
and the same NUN5 object at `0x00DEA000`; only their pulse-dependent Y position
differs. `UI-BTL-008` therefore performs one exact eight-byte NUN5 BTL copy.
No code, position, pulse, command text, or font data is changed.

Evidence: paired Slots 5 and 6 screenshots and EE memory, identical live object
identity across both views, unique rectangle-byte searches in both canonical
BTL files, decoded `TEX_xselect` crops, and complete-function comparison.
The user then verified the integrated Current build on both Command Menu and
Command Chart and accepted both screens as good. Confidence is **verified** and
the shared correction is **runtime-proven**.

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
Vec2 origin = {-33.0f, -33.0f};
PairLayout layout = pairLayout(rank, row, widthScale);
drawBubble(origin, widthScale, 1.0f, layout.rotation);
drawPairForeground(layout.x, layout.y, widthScale, 1.0f, layout.rotation);
```

NUN5 carries independent horizontal and vertical scale values through its
sprite call. NA2's homolog originally reused one value and its object offset
`+0x40` is a next pointer rather than NUN5's scale field. Copying the NUN5
implementation wholesale would corrupt the NA2 object chain. `UI-BTL-009`
therefore ports the anisotropic renderer contract into NA2's resident renderer
and uses verified zero padding at BTL file `0x2119E4..0x211C1F` for ABI-safe
helpers and constants. Callers pass derived values without changing the NA2
object layout. The foreground helper takes explicit caller-owned X adjustment,
Y adjustment, row selector, and angle-output storage. Paired callers pass
neutral adjustments; the numeric class supplies its separate donor-derived
layout through the same ABI-safe helper. Fixed callers still explicitly clear
the added rotation argument.

The common origin is changed from NA2 `(-33,-42)` to NUN5 `(-33,-33)`.
The complete NUN5 rank offsets are `(20,-30)`, `(-64,-63)`, and `(0,-96)`;
NA2 had `(50,-20)`, `(-16,-62)`, and `(30,-104)`.

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
| Numeric draw dispatcher | file `0x5A250`, Ghidra `FUN_0070E150` | file `0x5C5B0`, Ghidra `FUN_007232B0` |
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
functions is unsafe. `UI-BTL-010` instead:

- imports the three exact NUN5 records;
- calls the existing NA2-compatible item helper with the NUN5 `22/20` and
  `37/37` anchor contract and caller-owned angle storage;
- ports the six digit positions into NA2's already-corrected coordinate frame
  as `-36/-27/-18`, `-32/-22`, and `-26`.

The transformed digit constants are intentionally authored binary-patcher
replacements rather than byte copies: they equal the donor additions minus the
donor negative-50 origin, which is represented elsewhere in the NA2 port.
Copying the donor instructions literally would apply the origin twice.

### Side effects, evidence, and confidence

The patch changes only record selection and geometry passed to the item sprite
renderer. It does not change item values, recovery arithmetic, effect timing,
object allocation, object links, or the atlas itself. The shared helper writes
its angle only to caller-owned stack storage; it never uses NUN5's incompatible
object `+0x40` scale field.

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
| Single draw | file `0x5AB90`, live `0x0070EA90`, Ghidra `FUN_0070ea50` | file `0x5D0A0`, live `0x00723DA0`, Ghidra `FUN_00723d60` |
| Single width update | shared NA2 update at file `0x59EA0` | file `0x5D230`, Ghidra `FUN_00723ef0` |
| Object-code map | file/live `0x1E4CD0` / `0x00898BD0` | file/live `0x1ED8B0` / `0x008B45B0` |
| Single-class vtable | live `0x005DDEC0` | live `0x005EB3D0` |
| Uniform sprite wrapper | boot ELF `FUN_00377720` | boot ELF `FUN_00384800` |
| Added rotation helper | BTL file `0x211C20`, live `0x008C5B20` | not applicable |
| Existing pi/2 constant | BTL file `0x1EE630`, live `0x008A2530` | inline in the donor draw function |

The five object-code maps are byte-identical:

| Object code | Item record |
| ---: | ---: |
| `0x09` | `0x9A` |
| `0x0C` | `0x98` |
| `0x0D` | `0x99` |
| `0x13` | `0x97` |
| `0x12` | `0x96` |

`UI-BTL-011` therefore copies only the complete official NUN5 record range
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
NA2 field is a next-object pointer. The existing NA2-compatible common helper
instead derives `1.90625` for object code `0x09` and `1.0` for every other
single record. The same bounded edit replaces the fixed class's approximate
`1.6` with its exact donor width scale `102/64 = 1.59375`; the accepted pair
path and shared store remain at their previous addresses.

The rotation helper runs after resource lookup because that call may clobber
caller-saved floating-point registers. Its call delay clears `f14`; the helper
loads pi/2 only for records `0x82` and `0x99`, preserves the renderer variant in
`v0`, and restores `a0` in the return delay slot. The original uniform wrapper
is retained. An experimental direct call to the lower anisotropic renderer
produced no foreground because it bypassed the wrapper's distinct argument
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
execution slice and shared store are unchanged from its accepted helper; a
fresh-process capture can outlive that short notification and is not used as
placement evidence.

Visible single/status behavior is **runtime-proven** with **high confidence**.
Record `0x99` was absent from the captured set, so its quarter-turn remains a
high-confidence static result rather than a runtime-verified one. The exact
fixed-class scale is likewise statically traced until a fixed-class state is
captured.

## Fixed two-label item status

### Identity and address map

This section uses the same exact NA2/NUN5 boot-ELF and BTL identities recorded
above. Complete-file BTL offsets map to live code at `load_base + file_offset`;
the preserved Ghidra labels remain `0x40` below the live addresses.

| Role | NA2 | NUN5 |
| --- | --- | --- |
| Fixed constructor | file `0x5B080`, Ghidra `FUN_0070ef40`, live `0x0070EF80` | file `0x5D840`, Ghidra `FUN_00724500`, live `0x00724540` |
| Fixed draw | file `0x5B0F0`, Ghidra `FUN_0070efb0`, live `0x0070EFF0` | file `0x5D8B0`, Ghidra `FUN_00724570`, live `0x007245B0` |
| Fixed width update | absent from the NA2 object ABI | file `0x5DB20`, Ghidra `FUN_007247e0`, live `0x00724820` |
| Fixed-class vtable | live `0x005DDE80` | live `0x005EB370` |
| Shared NA2 width helper | BTL file `0x211B54`, live `0x008C5A54` | not applicable |
| First adapted draw block | BTL file `0x5B128`, live `0x0070F028` | behavior inside `FUN_00724570` |
| Second adapted draw block | BTL file `0x5B1F0`, live `0x0070F0F0` | behavior inside `FUN_00724570` |

The class always draws record `0x8E` followed by record `0x8D`. Their complete
official NUN5 rectangles are already imported by `UI-BTL-009` and
`UI-BTL-010`; `UI-BTL-012` therefore contains only two NA2 ABI adaptations and
no new texture or table donor.

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

The NA2 port instead reuses the runtime-proven `UI-BTL-009` width helper. Both
call sites pass zero X bias. The first selects the helper's 18-unit top row and
adds two units; the second selects its 20-unit lower row and adds 17 units. The
fixed renderer does not consume the helper's angle output, so its original
uniform wrapper and rotation behavior remain unchanged. The exact fixed bubble
scale `102/64 = 1.59375` is already selected by the shared common helper.

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
because its proposed runtime address overlapped live BTL data. V33 reuses the
existing proven helper and changes only the two guarded draw blocks; no new
code cave or data overwrite remains.

The fixed draw geometry is **runtime-proven** with **high confidence**. It is
not marked verified because the checkpoint transformed a live paired object
rather than capturing a naturally spawned fixed-class notification.
