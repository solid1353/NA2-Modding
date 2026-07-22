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

The focused exports are under
`@analysis/disassembly/NA2/exports/BTL.BIN/` and
`@analysis/disassembly/NUN5/exports/BTL.BIN/`. Those projects omit the
40-byte BTL file header when mapping code, so a Ghidra address is the archived
live address minus `0x40`. File offsets below always refer to the complete
source file.

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

The stable behavior is equivalent to:

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

The original NA2 atlas coordinate contains a downward green triangle, which
explains why the Japanese renderer did not require rotation. After the whole
NUN5 `VS.CCS` import, the same coordinate samples lettering instead. A
rectangle-only transplant is also insufficient because the NUN5 source graphic
points right and relies on the two explicit rotations. `UI-BTL-007` therefore
copies the exact NUN5 rectangle and four angle-load instructions and removes
only the two open-state horizontal draws. Each redirected call's delay slot
writes the loaded angle into the sprite. A compact 20-byte NA2 wrapper at file
offset `0x6C` calls the unchanged native draw routine and then clears rotation;
at these call sites, the completed loops leave `s0` and `s3` dead, so the
wrapper safely uses those callee-saved registers for the sprite pointer and
return address without a stack frame.

The canonical BTL header contains one aligned 80-byte zero cave at
`0x30..0x7F`. Full-profile composition exposed that the first implementation's
44-byte `0x40` wrapper collided with the already accepted stage-width helper.
The corrected packing keeps that stage helper byte-identical at `0x40..0x6B`,
moves the byte-identical 16-byte Jutsu-label helper from `0x70` to `0x30`, and
uses the final `0x6C..0x7F` bytes for the compact selector wrapper. The two
relocated call targets are adjusted accordingly; all three ranges were
zero-filled in the canonical NA2 file and are mutually disjoint.

Side effects are confined to the open-selector arrow sprite's rotation and two
draw calls. The wrapper preserves the sprite pointer and clears rotation after
each draw. The closed confirmation screen and its accepted horizontal control
remain on `FUN_006bd0f0` and are not changed.

Evidence: paired Slot 4 screenshots and extracted EE memory, exact Ghidra
structural comparison, canonical file-byte verification, decoded
`TEX_vs_t01` atlas crops, and live sprite-object reconstruction. Confidence is
**high** for the static correction; runtime acceptance remains pending.

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
Confidence is **high** for the shared static correction; runtime acceptance
remains pending.
