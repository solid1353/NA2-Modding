# Stage Select UI

## Research coverage

- **Assigned scope:** compare retail NA2 (`SLPS-25837`) and NUN5 Stage Select
  records, draw paths, and geometry.
- **Exploration depth:** the relevant binaries, native callers, records, and
  paired screen states were examined.
- **Confirmed coverage:** the documented owners, structures, and cross-game
  differences are established.
- **Unresolved or untested:** callers and states not explicitly covered below.
- **Deliberate exclusions and overlap:** NA2 Stage Select behavior and records
  belong to [Native Stage Select](../../game/stage_select.md), stage loading to
  [Stages](../../gameplay/stages/stages.md); the shared OK and Back compositor
  belongs to [Shared frontend prompt layout](options.md).
- **Evidence limitations:** bounded states do not cover every animation phase or
  indirect caller.

## Binary identity and address mapping

Evidence comes from the retail extracted files under `@source_na2` and
`@source_nun5`, their preserved BTL exports, raw disassembly of ranges the
exports omit, and paired runtime memory and screenshots.

## Stage records

NA2's 24 sixteen-byte records add the stage-name rectangle to the logical ID
and preview index; they are described in
[Native Stage Select](../../game/stage_select.md#stage-records). NUN5 file range
`0x215680..0x21573F` is 24 records of eight bytes with only the two words:

```cpp
struct Nun5StageRecord {
    int32_t stage_id;
    int32_t preview_index;
};
```

The TV preview builders are structural twins: NA2 file range
`0x60378..0x60428` and NUN5 `0x62F78..0x63028` differ in the record stride,
16 in NA2 and 8 in NUN5.

## Localized stage names

The carousel transform functions, NA2 `FUN_00714D40` and NUN5
`FUN_0072A7A0`, are structural twins apart from relocated engine calls. Their
export boundaries are `0x00714D40..0x0071518C` and
`0x0072A7A0..0x0072AC2C`.

## Bottom prompt placement

NA2 `FUN_00715C80` and NUN5 `FUN_0072B770` are the Stage Select draw
dispatchers. Their export boundaries are `0x00715C80..0x00715E9C` and
`0x0072B770..0x0072B9AC`. They call the carousel, selected-stage, and
stage-name draw routines, then submit the bottom prompt objects.

```cpp
ok_x = 388.0f;   // NUN5 400.0f - 12.0f
back_x = 462.0f; // NUN5 470.0f - 8.0f
```
