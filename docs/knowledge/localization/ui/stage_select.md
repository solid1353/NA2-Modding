# Stage Select UI

## Research coverage

- **Assigned scope:** compare clean NA2 and NUN5 Stage Select records, draw paths, and geometry.
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

## Binary identity and address mapping

Evidence was obtained from the clean extracted files under `@source_na2` and
`@source_nun5`, the preserved Ghidra C/TXT exports under
`@disassembly/NA2/exports/BTL.BIN/` and
`@disassembly/NUN5/exports/BTL.BIN/`, Capstone 5 disassembly of ranges omitted
by Ghidra, and paired runtime memory and screenshots.

## Stage records and preview construction

NA2 file range `0x20FC10..0x20FD8F` is 24 records of 16 bytes:

```cpp
struct Na2StageRecord {
    int32_t stage_id;
    int32_t preview_index;
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

Both native preview consumers continue to load that word directly, including
the second consumer at NA2 file offset `0x603B8`.

## Localized stage names

The carousel transform functions, NA2 `FUN_00714D40` and NUN5
`FUN_0072A7A0`, are structural twins apart from relocated engine calls. Their
export boundaries are `0x00714D40..0x0071518C` and
`0x0072A7A0..0x0072AC2C`. No carousel-transform edit is required.

## Bottom prompt placement

NA2 `FUN_00715C80` and NUN5 `FUN_0072B770` are the Stage Select draw
dispatchers. Their export boundaries are `0x00715C80..0x00715E9C` and
`0x0072B770..0x0072B9AC`. They call the carousel, selected-stage, and
stage-name draw routines, then submit the bottom prompt objects.

```cpp
ok_x = 388.0f;   // NUN5 400.0f - 12.0f
back_x = 462.0f; // NUN5 470.0f - 8.0f
```
