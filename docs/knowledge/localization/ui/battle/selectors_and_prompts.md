# Battle UI selectors and prompts

Binary identities and address conventions are defined in the
[Standard game file identities](../../../game/files/file_identities.md).

## Research coverage

- **Assigned scope:** compare retail NA2 (`SLPS-25837`) and NUN5 battle
  selectors, prompts, indicators, and labels.
- **Exploration depth:** the relevant binaries, native callers, records, and
  paired screen states were examined.
- **Confirmed coverage:** the documented owners, structures, and cross-game
  differences are established.
- **Unresolved or untested:** callers and states not explicitly covered below.
  The NA2 player-marker draw was not compared with NUN5. An unverified lead
  associates a branch delay slot near EE `0x001F64A4` with Jutsu-name display;
  the affected screen behavior is unspecified.
- **Deliberate exclusions and overlap:** Command List and move-chart rows
  belong to
  [Battle Command List and move chart](command_list_and_move_chart.md);
  awakening behavior belongs to [Awakening](../../../gameplay/characters/awakening.md);
  the Jutsu-selector row text belongs to
  [Numeric and settings text rendering](../../font/numeric_rendering.md#jutsu-selector-row).
- **Evidence limitations:** bounded states do not cover every animation phase or
  indirect caller.

## Player markers

NA2 BTL live `0x006BA870` (file `0x6970`) draws the marker above a fighter.
It returns without drawing when the marker's first halfword is `1` or when
resident `0x00375280` returns zero. Otherwise it selects a label and an arrow
from the battle HUD sprite-record table at live `0x008BFFB0`:

| Case | Label record | Arrow record |
| --- | ---: | ---: |
| Marker `+0x04` is `0` | `117` (`1P`) | `120` (red) |
| Marker `+0x04` is nonzero | `118` (`2P`) | `121` (blue) |
| COM test below passes | `119` (`COM`) | `122` (green) |

The COM row is taken when the fighter from resident `0x003769C0(marker[+0x04])`
has a nonzero field in halfword `+0x60` and resident `0x00376720` returns zero.
That this identifies a computer-controlled fighter is inferred from the label.

Each 12-byte record is `{x, y, width, height, texture slot, color}`. Records
`117..122` use texture slot `4`, `TEX_xmenu`, with rectangles `(129,1,34,26)`,
`(165,1,34,26)`, `(201,1,46,26)`, `(129,29,22,22)`, `(153,29,22,22)`, and
`(177,29,22,22)`. The function clamps the marker position to the screen and
draws the arrow, then the label, through resident `0x0037BD00`.

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

- NA2 `x\mode1\tex\hnt\mode1name1.bmp` maps to NUN5
  `x\mode1\tex\hnw\mode1name1.bmp`;
- NA2 `x\mode1\tex\row\mode1name1.bmp` maps to NUN5
  `x\mode1\tex\roc\mode1name1.bmp`;
- NA2 `x\mode1\tex\tnd\mode1name2.bmp` maps to NUN5
  `x\mode1\tex\tnw\mode1name2.bmp`.

Evidence: the exact boot-ELF identities above, both games' preserved boot-ELF
exports, a complete canonical CVM inventory, and decoded RGBA equality for all
72 mappings. The compositor interpretation and texture correspondence have
**high confidence**.

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

## VS confirmation prompts and bottom legends

NA2 `FUN_006c0cc0` and NUN5 `FUN_006d4130` are the homologous confirmation
draw methods. Both draw the selection prompts and then reuse one sprite for the
bottom OK and Back legends. Their practical ending is:

```cpp
drawOk(anchorOk, 356.0f, promptSprite, 0);
drawBack(anchorBack, 356.0f, promptSprite, 1);
```

Both games pass X anchors `400` for OK and `470` for Back; the NA2 immediates
are at BTL file offsets `0xCFFC` and `0xD020`. The wrapper implementations are
not byte-equivalent: NA2's legend table at ELF `0x4D4790` holds two 70x22
regional records, and its call sites at BTL `0xD014` and `0xD038` pass glyph
arguments that draw a separate input glyph before each label, whereas NUN5's
table at ELF `0x4DE9F0` holds combined Cross/OK `(1,1,56,22)` and
Triangle/Back `(1,25,64,22)` records. The two wrappers also advance the shared
queued sprite differently, so equal anchors do not place equal records at the
same raster position in both games.

## Command Menu and Command Chart scroll indicators

### Shared renderer and record

| Game | Method | File range | Ghidra range | Archived live range | Rectangle record |
| --- | --- | --- | --- | --- | --- |
| NA2 | `FUN_00878820` | `0x1C4960..0x1C530F` | `0x00878820..0x008791CF` | `0x00878860..0x0087920F` | file `0x21D648`, live `0x008D1548` |
| NUN5 | `FUN_00894f60` | `0x1CE2A0..0x1CEC1F` | `0x00894F60..0x008958DF` | `0x00894FA0..0x0089591F` | file `0x2214D8`, live `0x008E81D8` |

These methods are draw callbacks beneath the shared Practice/Free Battle
command controller (`ccStartMenuPrivateCmd`, NA2 `FUN_0087c370` / NUN5
`FUN_008d8be0`). Their direct caller is indirect in the exported state-object
dispatch. Important callees are the row/text compositors, texture-layer accessor
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

NA2 and NUN5 agree on this behavior. Only the shared rectangle differs:

- NA2: `(194,195,20,20)`, bytes `C200C30014001400`;
- NUN5: `(1,225,20,22)`, bytes `0100E10014001600`.

## Ultimate Jutsu one-part label

NA2's Ultimate Jutsu banner uses two 64x64 label halves. Official NUN5 uses one
128x64 label and one-part construction behavior; its `OUGI.CCS` contains the
corresponding model, UV, texture, and animation layout.

## Round label

NA2 constructs `Round` from two Japanese 38x38 glyph rectangles at X=`216`,
Y=`44`, and scale `1.4`. NUN5 uses one English 94x30 rectangle at X=`256`,
Y=`24`, with scale `1.2` and a Y=`64` render constant.
