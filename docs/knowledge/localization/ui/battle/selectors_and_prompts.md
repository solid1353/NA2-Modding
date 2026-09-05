# Battle UI selectors and prompts

## Research coverage

- **Assigned scope:** compare clean NA2 and NUN5 battle selectors, prompts, indicators, and labels.
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

Evidence: the exact boot-ELF identities above, the preserved C/TXT exports at
`@disassembly/NA2/exports/SLPS_258.37/` and
`@disassembly/NUN5/exports/SLES_556.05/`, a complete canonical CVM
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

### Arrow-state negative findings

- NA2's active arrow sprite was at `0x00C7B820`; its rotation field at
  `+0x4C` (`0x00C7B86C`) read back the exact `-pi/2` bit pattern after the
  lower draw, yet the captured arrow still pointed right;
- NUN5's corresponding object was at `0x00BFC420` and consumed the rotation;
- cloning the NUN5 object control fields persistently suppressed unrelated UI;
  partial draw-scoped field tests either had no effect or produced malformed
  sampling;
- disabling the rotation reset did not change the rendered direction.

These results establish that writing a valid rotation float is insufficient
while the NA2 sprite remains in mode 0, and that NUN5's mode fields cannot stay
enabled across the shared object lifetime. Reusing NA2's vertical arrow pixels
also diverges from the NUN5 atlas rather than reproducing its state behavior.

## VS confirmation prompts and bottom legends

NA2 `FUN_006c0cc0` and NUN5 `FUN_006d4130` are the homologous confirmation
draw methods. Both draw the selection prompts and then reuse one sprite for the
bottom OK and Back legends. Their practical ending is:

```cpp
drawOk(anchorOk, 356.0f, promptSprite, 0);
drawBack(anchorBack, 356.0f, promptSprite, 1);
```

The wrapper implementations are not byte-equivalent: their queued-sprite
advancement makes NUN5's nominal anchors `400/470` differ from NA2's effective
coordinates. Paired measurements establish corresponding NA2 anchors
`388/462`.

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

NA2 and NUN5 already agree on this behavior. Only the shared rectangle differs:

- NA2: `(194,195,20,20)`, bytes `C200C30014001400`;
- NUN5: `(1,225,20,22)`, bytes `0100E10014001600`.

## Unresolved Jutsu-name display lead

An old note near EE `0x001F64A4` proposes forcing part or all of `v0` to zero
in a branch delay slot. The intended bit or byte and the affected screen
behavior are unspecified.

## Ultimate Jutsu one-part label

NA2's Ultimate Jutsu banner uses two 64x64 label halves. Official NUN5 uses one
128x64 label and one-part construction behavior; its `OUGI.CCS` contains the
corresponding model, UV, texture, and animation layout.

## Round label

NA2 constructs `Round` from two Japanese 38x38 glyph rectangles at X=`216`,
Y=`44`, and scale `1.4`. NUN5 uses one English 94x30 rectangle at X=`256`,
Y=`24`, with scale `1.2` and a Y=`64` render constant.
