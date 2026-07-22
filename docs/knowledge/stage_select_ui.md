# Stage Select UI

This record preserves the reusable NA2/NUN5 Stage Select analysis behind
`UI-BTL-002`. It covers graphical layout and texture selection only; string and
font behavior are outside this patch.

## Binary identity and address mapping

- NA2 / SLPS-25837 `PRG/BTL.BIN`: 2,237,184 bytes, SHA-256
  `56FD042740221E3CC91417194F147142799D51FE70642273F4E97BD389D5D63C`.
- NUN5 / SLES-55605 `PRG/BTL.BIN`: 2,253,184 bytes, SHA-256
  `7E8518DA7BD4957AF18CB0ABABE67F0E9B37C42C6551375201B15997F0A3DFE3`.
- In paired Slot 3 memory, the complete files start at EE `0x006B3F00` for
  Current and `0x006C6D00` for NUN5. Runtime addresses are therefore file start
  plus file offset.
- The preserved Ghidra exports omit the files' first `0x40` bytes. Their labels
  are consequently `0x40` lower than paired live-memory addresses. File offsets
  in canonical patch data remain authoritative.

Evidence was obtained from the clean extracted files under `@source_na2` and
`@source_nun5`, the preserved Ghidra C/TXT exports under
`@analysis/disassembly/NA2/exports/BTL.BIN/` and
`@analysis/disassembly/NUN5/exports/BTL.BIN/`, Capstone 5 disassembly of ranges
omitted by Ghidra, and the paired archived Slot 3 memory/screenshots under
`@work/UI translation/runtime_cases/remaining_03_stage_select_total_mismatch/`.

## Stage records and preview construction

NA2 file range `0x20FC10..0x20FD8F` is 24 records of 16 bytes:

```cpp
struct Na2StageRecord {
    int32_t stage_id;
    int32_t preview_index; // repurposed by UI-BTL-002 as name_scale_x
    int16_t u, v, width, height;
};
```

NUN5 file range `0x215680..0x21573F` is 24 records of eight bytes:

```cpp
struct Nun5StageRecord {
    int32_t stage_id;
    int32_t preview_index;
};
```

Every stage ID and preview index matches by row, and every preview index equals
its row number `0..23`. NA2's selected-preview path is represented by Ghidra
`FUN_007144e0`; NUN5's structural twin is `FUN_00729f00`. Their relevant
function boundaries in the exports are `0x007144E0..0x007146BC` and
`0x00729F00..0x0072A0E0`. `UI-BTL-002` redirects the selected-preview read at
NA2 file offset `0x606BC` to the already matched row index.

Ghidra omitted a second, structurally matched preview-construction range. Its
relevant NA2 file range is `0x60378..0x60428`; the NUN5 twin is
`0x62F78..0x63028`. Both compute a row byte offset before choosing a preview
atlas cell:

```cpp
int row = find_stage_row(stage_id);
row = max(row, 0);
int row_offset = row * record_stride; // 16 in NA2, 8 in NUN5
int preview_index = stage_records[row].preview_index;
build_preview_atlas_cell(preview_index);
```

After the NA2 word is repurposed for `name_scale_x`, the final load interprets
IEEE-754 scale bits as an atlas index. At NA2 file offset `0x603B8`, the
size-preserving port changes `lw a0,0(v0)` to `srl a0,v1,4`; `v1` is still
`row * 16`, so the result is the exact canonical index `0..23`. NUN5 retains
the direct load because its eight-byte record still contains the index. This is
an intentional NA2-specific adaptation, not a donor-copy candidate.

## Localized stage names

NUN5 obtains 24 English rectangles from boot-ELF file range
`0x4DDB90..0x4DDC4F` and applies `min(1.0f, 214.0f / width)` horizontally.
`UI-BTL-002` copies those rectangles into the NA2 inline records and stores the
exact single-precision result in each repurposed second word. NA2 file offsets
`0x61570` and `0x6157C` keep vertical scale at `1.0` and load the stored value
only into horizontal scale.

The carousel transform functions, NA2 `FUN_00714D40` and NUN5
`FUN_0072A7A0`, are structural twins apart from relocated engine calls. Their
export boundaries are `0x00714D40..0x0071518C` and
`0x0072A7A0..0x0072AC2C`. No carousel-transform edit is required.

## Bottom prompt placement

NA2 `FUN_00715C80` and NUN5 `FUN_0072B770` are the Stage Select draw
dispatchers. Their export boundaries are `0x00715C80..0x00715E9C` and
`0x0072B770..0x0072B9AC`. They call the carousel, selected-stage, and
stage-name draw routines, then submit the bottom prompt objects.

NA2 uses X=`300.0f` for prompt item 3 and its companion sprite. NUN5 uses
X=`260.0f` for both. `UI-BTL-002` copies the exact NUN5 `lui v0,0x4382`
instructions from NUN5 BTL file offsets `0x64C50` and `0x64C78` into NA2 file
offsets `0x61F40` and `0x61F64`. The other visible bottom prompts already match.

## Side effects, callers, and negative results

- The preview constructors create/configure the selected preview and carousel
  sprites from `MAPSEL1.CCS`; the patch changes only their atlas index source.
- The draw dispatcher updates presentation objects and submits prompt sprites;
  the patch changes only two X constants.
- Whole NUN5 `MAPSEL1.CCS` is necessary because picture association, models,
  UVs, and layout are coupled, but it is not sufficient: BTL still controls the
  preview index and bottom-prompt position.
- The large selected image and localized stage-name plaque already match the
  reference and receive no additional edit.
- A NUN5-only extra argument found near a generic position setter lies on a
  failure path, not the successful stage draw path, and is unrelated.
- No code cave, absolute jump, file growth, text change, or font change is used.

Confidence is **high** for record topology, file/runtime mapping, both preview
consumers, stage-name scale behavior, and the two prompt constants. Runtime
visual acceptance of the final combined patch remains user-owned.
