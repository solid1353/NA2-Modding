# Victory artwork

## Research coverage

- **Assigned scope:** compare clean NA2 and NUN5 Victory emblem geometry,
  animation, and character-name rectangle construction.
- **Exploration depth:** the relevant binaries, native callers, records, and
  paired screen states were examined.
- **Confirmed coverage:** the documented owners, structures, and cross-game
  differences are established.
- **Unresolved or untested:** callers and states not explicitly covered below.
- **Deliberate exclusions and overlap:** feature imports, hooks, and validation
  belong to [UI layout](../../../features/localization/ui_layout.md) or
  [UI textures](../../../features/localization/ui_textures.md).
- **Evidence limitations:** bounded states do not cover every animation phase or
  indirect caller. GhidrAssist exposes fragmented BTL functions and maps their
  code 0x40 below the verified file/runtime addresses. Where it could not expose
  the initializer, read-only EE disassembly of the clean binaries supplied the
  instruction evidence. BTL addresses below use the verified runtime mapping.

## Scope and source identity

The clean container identities are listed in
[Standard game file identities](../../game/files/file_identities.md#ccs-research-inputs).

| Container | NA2 size | NUN5 size |
| --- | ---: | ---: |
| `3EYE/ENDDEMO.CCS` | 74,520 | 79,749 |
| `3EYE/3HAK3PCT.CCS` | 9,978 | 10,947 |
| `3EYE/3SKN3PCT.CCS` | 14,794 | 15,922 |

The canonical NA2 and NUN5 filesystems both contain 78 matching
`3EYE/3???3PCT.CCS` resources. Seventy-four contain exactly one `TEX_name`
visual in both games; the four structural variants `3GUY3PCT`, `3ITC3PCT`,
`3KKS3PCT`, and `3KSM3PCT` contain no `TEX_name` in either game. Pairing
textures by object identity rather than internal filename proves that the only
decoded NA2/NUN5 visual differences in the name-bearing resources are
`TEX_name` and, where present, `TEX_mode1name*` ordinary-awakening labels.

Paired runtime memory contains the Japanese `TEX_name` body at EE
`0x01607140`; its exact 16,384-byte body SHA-256
`1DB17B6335F272F42F7B965742D195C01351900FE831D5BC981C3F2FBFD6DAA0`
matches on-disc `3EYE/3SSV3PCT.CCS`, confirming the Sasuke resource identity.

Seventy-two complete NUN5 payloads fit the corresponding NA2 member capacities,
with 13 to 2,253 bytes of gzip padding.

Two members require deterministic mapped exceptions:

- `3HAK3PCT.CCS`: the complete NUN5 payload exceeds the fixed NA2 member by
  348 bytes. NUN5's 256x128 Haku name has nontransparent bounds
  `(4,4)..(116,51)`; the entire right 128 pixels and lower 64 pixels are
  transparent.
- `3SKN3PCT.CCS`: the complete donor exceeds the fixed member by 72 bytes even
  though its structure is compatible. Palette index 8 is a faint
  `(255,255,255,15)` antialias shade used by 156 pixels; the visible donor
  bounds are `(3,4)..(232,115)`.

## Large WINNER emblem

The large WINNER emblem belongs to `3EYE/ENDDEMO.CCS`, not the resident
win-count sprite renderer. Its atlas is `x\enddemo\tex\enddemo01.bmp`.
The atlas alone does not define its shape or placement:

| Object | NA2 | NUN5 |
| --- | --- | --- |
| `MDL_win` and `MDL_win_f` | four vertices, 120-byte sections | five vertices, 140-byte sections |
| `ANM_end_win01` | 592-byte section | 592-byte section with different transforms |
| `ANM_end_win02` | 872-byte section | 884-byte section including a rotation track |

The first `ANM_end_win01` root translation is `(-111, -15, 77.656845)` in
NA2 and `(-105, -15, 87)` in NUN5. Root rotation changes from `(0, 0, 0)`
to `(0, -10, 0)`; scale keys also differ. Both models carry the matching donor
vertex and UV geometry. `CMP_win` is equivalent after resolving object IDs.

Object IDs differ between the containers. Resolve mesh object/material
references and animation-controller targets by both TOC filename and object
name: object names alone are not unique. The relevant owners are
`x\enddemo\max\enddemo.max`, `x\enddemo\anm\end_win01.max`, and
`x\enddemo\anm\end_win02.max`.

## Small win-count label

The homologous Victory draw functions call the Winner renderer with the same
logical anchor, X `50` and Y `55`, but the regional renderers construct the
artwork differently.

NA2 `FUN_00202B50` draws a fixed `(0,96,32,32)` prefix at scale `1.2`, any
decimal count digits as 32x32 cells, and a fixed `(32,96,63,32)` suffix. NUN5
`FUN_00209A70` instead obtains localized record 0 through `FUN_003D5070(0)`.
The English record at `0x005DE860` is `(1,97,94,30)`. NUN5 draws that complete
rectangle at scale `1.2`, producing display dimensions `112.8 x 36`, then
places any count digits after it with advance `27.6`. It does not draw NA2's
separate trailing suffix.

NUN5 derives the Winner center X as
`anchor_x + (112.8 - 38.4) / 2`, uses the unchanged Y anchor, and assigns local
offsets `(-112.8 / 2, -36 / 2)`. The resulting left edge remains
`anchor_x - 19.2`; the formula reserves the same digit-cell half-width while
allowing the localized Winner rectangle to own its full dimensions.

## Victory-name rectangle construction

The character-name renderer is split between the resident boot ELF and
`PRG/BTL.BIN`. The NA2 and NUN5 inputs are identified in
[Standard game file identities](../../game/files/file_identities.md).

The homologous resident functions have the same state update, two-part
centering, animation, and draw behavior:

| Role | NA2 runtime / ELF file | NUN5 runtime / ELF file |
| --- | --- | --- |
| Victory state update | `0x002020D0..0x002023D0` / `0x1021D0` | `0x00208F80..0x002092A0` / `0x109100` |
| Victory draw | `0x002023D0..0x00202640` / `0x1024D0` | `0x002092A0..0x00209520` / `0x109420` |
| two-part name draw | `0x00202FC0..0x002032D0` / `0x1030C0` | `0x00209EB0..0x0020A1E0` / `0x10A030` |

Both draw helpers obtain two 24-byte rectangle records, center their combined
width around the requested X position, optionally halve their heights for the
entry animation, write the rectangle and transform fields into the shared
sprite object, and draw both parts. Their practical common behavior is:

```cpp
Rect first = victory_rect(character_id, 0);
Rect second = victory_rect(character_id, 1);
float left = -(first.width + second.width) / 2.0f;
first.draw_x += left;
second.draw_x += first.width + left;
apply_entry_height_mode(first, second, animation_mode);
draw(first, x, y, scale, rotation);
draw(second, x, y, scale, rotation);
```

The resident helpers differ in their `victory_rect` provider. The battle
initializer has a separate path, described below:

- NA2 BTL runtime `0x0076B9F0..0x0076BA68` (file
  `0xB7AF0..0xB7B68`) validates character IDs `0..93` and frame IDs
  `0..1`, then returns one pointer from the 188-entry table at runtime
  `0x008A5C40` / file `0x1F1D40`. Those pointers address prebuilt
  24-byte Japanese rectangle records in the BTL data pool.
- NUN5 BTL entry `0x007832E0..0x00783540` / file
  `0xBC5E0..0xBC840` validates the same IDs, then calls resident localized accessor
  `FUN_003D4F80(character_id)`, selects the empty, first, or second frame
  template at BTL file `0x21B9A0`, `0x21B9C0`, or `0x21B9E0`, and replaces
  the template width with the selected English atlas width minus two.
- The NUN5 English 94-row width table is at ELF runtime `0x005DE550` /
  file `0x4DE6D0`. Each eight-byte row begins with the first and second
  unsigned widths. Naruto's row is `156, 192`, yielding renderer widths
  `154, 190`; NA2's prebuilt Naruto records instead contain `236, 173`.
- Tenten uses character IDs `13` (Classic) and `66`. Both NUN5 rows are
  `160, 0`, so frame 0 uses width `158` and frame 1 uses the all-zero empty
  template. Clean NA2 points those
  frames at nonempty Japanese records of widths `128` and `122`; changing only
  the first shared record cannot reproduce NUN5's one-frame result.

Each nonempty NUN5 template has U `1`, V `1` or `65`, height `62`, local X
`0`, local Y `-31`, and zero initial display dimensions. The selected width
minus two replaces its width field. The empty template contains 24 zero bytes.

Equivalent pseudocode for the regional providers is:

```cpp
// NA2
const Rect* victory_rect(int character_id, int frame) {
    if ((unsigned)character_id >= 94 || (unsigned)frame >= 2)
        return nullptr;
    return na2_prebuilt_rects[character_id][frame];
}

// NUN5
bool victory_rect(Rect* out, int character_id, int frame) {
    if ((unsigned)character_id >= 94 || (unsigned)frame >= 2)
        return false;
    const EnglishWidths& widths = localized_widths(character_id);
    uint16_t width = frame == 0 ? widths.first : widths.second;
    if (width == 0) {
        *out = empty_template;
    } else {
        *out = frame == 0 ? first_template : second_template;
        out->width = width - 2;
    }
    return true;
}
```

## Battle Victory initialization

NA2 does not call the rectangle provider when initializing the battle Victory
scene. At runtime `0x0076CE8C` / BTL file `0xB8F8C`, it indexes the Japanese
pointer table directly and copies both 24-byte records into the scene context
at `+0x3C8` and `+0x3E0`. The character ID is in `s3`, and the context is in
`s4`. This path is independent of the resident two-part name draw helper.

NUN5 instead calls its rectangle constructor at `0x007849E0` and
`0x007849F8`, passing the signed 16-bit character ID and those same two
destination offsets. Construction follows the width/template rules above.

The following 216 bytes at NA2 `0x0076CFD4` and NUN5 `0x00784A00` are
identical. They derive float display dimensions from the two rectangles and
center their combined width: first local X is `-(w0 + w1) / 2`, and second
local X is `w0 - (w0 + w1) / 2`. Thus the clean Japanese Tenten pair centers
128 + 122 pixels; the English pair centers 158 + 0 pixels. The unchanged
centering formula needs the correct per-character frame pair, not a screen
coordinate correction.
