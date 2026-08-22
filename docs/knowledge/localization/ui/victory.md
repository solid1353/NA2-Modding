# Victory artwork

## Scope and source identity

The paired Generic Slot 1 checkpoint showed two texture defects on the battle
Victory screen: NA2 still rendered its Japanese `WINNER` emblem and Japanese
character-name artwork, while NUN5 rendered the English equivalents. The
canonical source members are under the configured `@source_na2/` and
`@source_nun5/` extractions; exact identities for every selected member remain
machine-verifiable in
`@builder/localization/texture_patcher/containers.tsv`.

The shared emblem and the two fixed-capacity character exceptions have these
raw gzip identities:

| Container | NA2 SHA-256 / size | NUN5 SHA-256 / size |
| --- | --- | --- |
| `3EYE/ENDDEMO.CCS` | `FB9DAF4CE604B0986F2D2F66D6E61EA61B96AE5A1192DF125D672E9F806C4E7E` / 74,520 | `8819196236C61D6CC95AABF602451EEC4869B15710A3B6372E0373252AFC2252` / 79,749 |
| `3EYE/3HAK3PCT.CCS` | `3E8D2824415B78D08363B3A28C8354ADDBA99D17DA96C00CECAB83D7263349D9` / 9,978 | `9C1622B53B098EDC6F38435A858B12BE2833666F8043252A0A56617B3E7036F2` / 10,947 |
| `3EYE/3SKN3PCT.CCS` | `2BFE5B4EF601F06057D5F56D73D92A8F10DBDEC95B9A08CB7E92B4D0F2F7977C` / 14,794 | `3618E055EBF19B2A48C1657955A8E6539AE9C96BB486BBA8EAD7AE217E14B722` / 15,922 |

## CCS ownership and implementation

`3EYE/ENDDEMO.CCS` owns three decoded textures. `TEX_enddemo01` is the
512x512 background atlas containing the complete Victory artwork and localized
emblem; `TEX_enddemo02` and `TEX_enddemo03` are unrelated 64x64 background
textures. NA2 stores the selected TEX/CLT at payload offsets `0x8060` and
`0x7C44`; NUN5 stores the homologues at `0x9194` and `0x8D78`. Their component
signatures are identical. `UI-VICTORY-001` therefore copies only the complete
NUN5 `enddemo01` TEX/CLT data into NA2's existing CCS structure. The other two
textures and every nonselected target byte remain unchanged.

The canonical NA2 and NUN5 filesystems both contain 78 matching
`3EYE/3???3PCT.CCS` resources. Seventy-four contain exactly one `TEX_name`
visual in both games; the four structural variants `3GUY3PCT`, `3ITC3PCT`,
`3KKS3PCT`, and `3KSM3PCT` contain no `TEX_name` in either game and are
excluded from the Victory import. Pairing textures by object identity rather
than internal filename proves that the only decoded NA2/NUN5 visual
differences in each selected resource are `TEX_name` and any already-reviewed
`TEX_mode1name*` ordinary-awakening labels.

The former generator selected only the 61 resources already present in its
package inventory. It therefore silently omitted 13 valid name-bearing
variants. Paired ss7 memory contains the Japanese `TEX_name` body at EE
`0x01607140`; its exact 16,384-byte body SHA-256
`1DB17B6335F272F42F7B965742D195C01351900FE831D5BC981C3F2FBFD6DAA0`
matches on-disc `3EYE/3SSV3PCT.CCS`, proving the missed Sasuke resource rather
than a stale-state or renderer defect. The corrected generator enumerates the
canonical source filesystems and admits all 74 name-bearing resources.

Seventy-two complete NUN5 payloads fit their unchanged NA2 member capacities,
with 13 to 2,253 bytes of verified gzip padding. Those containers now use
complete donors so the English name, awakening label where present, internal
names, and texture dimensions remain coupled.

Two members require deterministic mapped exceptions:

- `3HAK3PCT.CCS`: the complete NUN5 payload exceeds the fixed NA2 member by
  348 bytes. NUN5's 256x128 Haku name has nontransparent bounds
  `(4,4)..(116,51)`; the entire right 128 pixels and lower 64 pixels are
  transparent. The transform imports the top-left 128x64 donor canvas, maps
  antialias colors to the nearest values in the existing NUN5 palette subset
  `0,1,2,3,4,7,14`, and retains the exact NUN5 awakening label. It changes 512
  of 8,192 cropped pixels, all in antialias shading; the visible bounds become
  `(5,5)..(116,50)`. The pinned gzip stream fills the 9,978-byte member exactly.
- `3SKN3PCT.CCS`: the complete donor exceeds the fixed member by 72 bytes even
  though its structure is compatible. The mapped result keeps every NUN5 name
  palette entry except index 8, a very faint `(255,255,255,15)` antialias
  shade used by 156 pixels, which maps to the nearest retained donor color.
  Visible bounds remain exactly `(3,4)..(232,115)`, and the result has nine
  bytes of verified padding.

No replacement CCS blob or authored raster asset is stored. The maintained
generator
`@scripts/research/ui_translation/generate_victory_texture_mappings.py`
enumerates all 78 family members from both canonical source filesystems,
requires their inventories to match, structurally excludes only the four
members without `TEX_name`, rejects any unclassified decoded visual
difference in the remaining 74, derives the three exceptional mappings, and
records every resulting payload and replacement identity.

## Victory-name rectangle construction

The character-name renderer is split between the resident boot ELF and
`PRG/BTL.BIN`. The exact binaries used for this comparison are:

| Game / binary | Size | SHA-256 |
| --- | ---: | --- |
| NA2 `SLPS_258.37` | 5,273,256 | `20C0A40D70EA412CD431993A2E189B37ECB6054D63AE93BE545470016E1627AF` |
| NA2 `PRG/BTL.BIN` | 2,237,184 | `56FD042740221E3CC91417194F147142799D51FE70642273F4E97BD389D5D63C` |
| NUN5 `SLES_556.05` | 5,340,912 | `20A43677397731A2A20899336D1165ACE5B436906B9B89BE90FB10F4558DD19D` |
| NUN5 `PRG/BTL.BIN` | 2,253,184 | `7E8518DA7BD4957AF18CB0ABABE67F0E9B37C42C6551375201B15997F0A3DFE3` |

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

`ui_layout_victory_names` preserves NA2's pointer-return ABI and uses equivalent
prebuilt records instead of replacing the renderer. The maintained read-only
`generate_victory_layout_patch.py` check verifies all four source identities,
reads every NA2 pointer and NUN5 English row, derives each complete 24-byte
replacement from the appropriate official NUN5 frame template plus the donor
width, and compares the result with the stored fixed-stride table. Its 77
semantic record patches expand to 78 concrete records because one patch has
two record indices. Repeated NA2 pointers are deduplicated; all nineteen
apparent alias conflicts are zero-versus-one-valid NUN5 row, never two
conflicting nonzero widths. Records referenced only by zero-width NUN5 rows
remain untouched so NA2-only or unused forms are not blanked without a donor
equivalent.

A direct donor copy cannot express this change: NUN5 stores zero-width
templates plus a separate localized table and synthesizes the final record at
runtime, while NA2 consumes pointer-addressed final records. The generated
replacement records are therefore the narrowest behavior-equivalent port,
not hand-tuned placement guesses.

## Behavior, negative results, and confidence

The change affects only the Victory emblem plus character-name and
ordinary-awakening artwork. It does not change character selection, battle
logic, text strings, fonts, BTL code, or file/member sizes. It does replace the
BTL-owned prebuilt Victory rectangle data described above. Existing battle-HUD
name fitting remains a separate consumer and is not duplicated here.

Complete-donor recompression was rejected only for Haku and Shikamaru because
it exceeded their fixed member capacities. Compression-parameter changes alone
could not make Haku fit; the nearest-palette transformations are explicit
NA2-capacity adaptations derived from NUN5 pixels and palettes rather than
stored replacement art.

The preserved NA2 state resumes into a different name-animation phase than its
embedded screenshot, and PCSX2 texture replacement swaps only raster uploads;
it does not reload the donor CCS or recreate the saved object state. A
same-delay capture therefore cannot prove the integrated final layout and is
retained only as a rejected validation method. Static CCS ownership,
visual-difference classification, complete renderer equivalence, source
provenance, fixed-capacity derivation, generated rectangle parity, and
preservation of unrelated `ENDDEMO` data are **high confidence**. The final
integrated Victory screen remains `approved_for_test` until it is reached
normally from the rebuilt ISO and compared with NUN5.
