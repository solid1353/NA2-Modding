# Battle Mash prompts

Addresses use the
[Game binary address conventions](../../../game/files/file_identities.md).

## Research coverage

- **Assigned scope:** The Battle Mash main-label objects, rectangle tables, and
  regional selection behavior in NA2 and NUN5.
- **Exploration depth:** Both draw paths, the NUN5 regional accessor, the paired
  live objects, and the two adjacent NA2 tables were inspected; both candidate
  table ranges were tested independently.
- **Confirmed coverage:** Main-label object fields, the complete seven-record
  table, the prompt-zero rectangle difference, and the separation between main
  prompts and controller glyphs.
- **Unresolved or untested:** Main prompt IDs other than Mash were not each
  exercised visibly at runtime.
- **Deliberate exclusions and overlap:** Supplemental button glyph rendering and
  Mash gameplay behavior are outside this document.
- **Evidence limitations:** Runtime comparison directly confirms the Mash record
  and table identity; compatibility of the other six records follows from the
  complete table structure and homologous NUN5 accessor.

## Objects and address map

The active paired Mash objects are at NA2 live addresses `0x00E4F3D0` and
`0x00E4F950`, and NUN5 live addresses `0x00DCE550` and `0x00DCEAD0`. Their
`0x580`-byte stride, player-side field at `+0x28`, main prompt ID at `+0x2F`,
and supplemental prompt list beginning at `+0x30` agree. Main prompt ID `0`
means Mash; supplemental ID `0x0C` selects the Cross glyph.

| Role | NA2 | NUN5 |
| --- | --- | --- |
| Main-label renderer | BTL file `0x25C0`, Ghidra `FUN_006B6480`, live `0x006B64C0` | BTL file `0x27E0`, Ghidra `FUN_006C94A0`, live `0x006C94E0` |
| Complete main-prompt rectangle table | BTL file `0x1DB730`, live `0x0088F630` | English regional table in boot ELF file `0x4DE630`, live `0x005DE4B0` |
| Regional accessor | absent; the BTL table is addressed directly | boot ELF file `0x2D4FC0`, runtime `FUN_003D4E40` |
| Adjacent controller-glyph table | BTL file `0x1DB770`, live `0x0088F670` | separate from the regional main-prompt table |

NUN5 `FUN_003D4E40` obtains the active language index and returns
`regionalTable[language] + promptId * 8`. `FUN_006C94A0` uses it for main
prompt IDs below seven and uses the returned width and height. NA2 has no
regional accessor and directly indexes the Japanese table embedded in BTL.

The seven entries are contiguous eight-byte little-endian rectangles:

```cpp
struct PromptRect {
    uint16_t u;
    uint16_t v;
    uint16_t width;
    uint16_t height;
};

const PromptRect *mainPromptRect(uint8_t promptId) {
    return promptId < 7 ? &regionalPromptRects[promptId]
                        : &battleStaticPromptRects[promptId];
}
```

For prompt ID zero, NA2 selects `(0,24,48,24)`, which samples English Mash
artwork vertically and clips it. The official NUN5 English record is
`(0,84,64,20)`. Replacing NA2 live range `0x0088F630..0x0088F667` with the
complete NUN5 English range produced the NUN5 label dimensions and placement
while leaving the Cross panels independently controlled. Both ranges are 56
bytes, so the tables are structurally compatible.

## Negative finding

The adjacent NA2 range `0x0088F670..0x0088F6A7` is not an alternate main-label
table. Replacing it left Mash vertical and turned the Cross panels into
incorrect controller glyph rows. Instructions in `FUN_006B6480` directly
reference `0x0088F630`, confirming that `0x0088F670` owns controller glyphs and
must not be treated as the main-prompt table.
