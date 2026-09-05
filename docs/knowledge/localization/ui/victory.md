# Victory artwork

## Research coverage

- **Assigned scope:** compare clean NA2 and NUN5 Victory artwork ownership and rectangle construction.
- **Exploration depth:** the relevant binaries, native callers, records, and
  paired screen states were examined.
- **Confirmed coverage:** the documented owners, structures, and cross-game
  differences are established.
- **Unresolved or untested:** callers and states not explicitly covered below.
- **Deliberate exclusions and overlap:** feature imports, hooks, and validation
  belong to [UI layout](../../../features/localization/ui_layout.md) or
  [UI textures](../../../features/localization/ui_textures.md).
- **Evidence limitations:** bounded states do not cover every animation phase or
  indirect caller.

## Scope and source identity

The shared emblem and the two fixed-capacity character exceptions have these
raw gzip identities:

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

## Victory-name rectangle construction

The character-name renderer is split between the resident boot ELF and
`PRG/BTL.BIN`. The exact binaries used for this comparison are:

The NA2 and NUN5 resident and BTL inputs are identified in
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

The regional difference is the `victory_rect` provider:

- NA2 BTL runtime `0x0076B9F0..0x0076BA68` (file
  `0xB7AF0..0xB7B68`) validates character IDs `0..93` and frame IDs
  `0..1`, then returns one pointer from the 188-entry table at runtime
  `0x008A5C40` / file `0x1F1D40`. Those pointers address prebuilt
  24-byte Japanese rectangle records in the BTL data pool.
- NUN5 BTL full entry `0x007832A0..0x00783500` / file
  `0xBC5A0..0xBC800` validates the same IDs. Its internal fast entry at
  runtime `0x007832E0` calls resident localized accessor
  `FUN_003D4F80(character_id)`, selects the empty, first, or second frame
  template at BTL file `0x21B9A0`, `0x21B9C0`, or `0x21B9E0`, and replaces
  the template width with the selected English atlas width minus two.
- The NUN5 English 94-row width table is at ELF runtime `0x005DE550` /
  file `0x4DE6D0`. Each eight-byte row begins with the first and second
  unsigned widths. Naruto's row is `156, 192`, yielding renderer widths
  `154, 190`; NA2's prebuilt Naruto records instead contain `236, 173`.

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
