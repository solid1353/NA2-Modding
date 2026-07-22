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
