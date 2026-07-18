# UI translation raw-binary patch set

This patch set holds size-preserving executable changes that are inseparable from
the NUN5 UI container import but do not belong inside `DATA.CVM`.

## UI-BTL-001: one-part OUGI label

NA2's Ultimate Jutsu banner uses two 64x64 label halves. The official English NUN5
and Brazilian NUN6 versions both use one 128x64 label and the same one-iteration
construction loop. The whole-container `OUGI.CCS` import supplies that one-part
model, UV, texture, and animation layout.

At BTL file offset `0xB5E80`, NA2 contains `02 00 42 2A`
(`slti v0,s2,2`). NUN5 and NUN6 contain `01 00 42 2A`
(`slti v0,s2,1`) at the structurally equivalent instruction. `UI-BTL-001` makes
that exact four-byte replacement. It preserves the file size and is disabled by
default until the combined texture/code build is runtime-tested.

Validate and inspect the planned edit from the repository root:

```powershell
python -m na2_patcher.modules.raw_binary.engine validate `
  --package na2_patcher/modules/raw_binary/patch_sets/ui_translation `
  --root na2=@source/NA2.iso.files

python -m na2_patcher.modules.raw_binary.engine plan `
  --package na2_patcher/modules/raw_binary/patch_sets/ui_translation `
  --root na2=@source/NA2.iso.files `
  --patch UI-BTL-001
```

Evidence and the broader container/layout analysis are recorded in
`docs/plans/ui_translation.md`.

## UI-BTL-002: localized stage-name rectangles and width fitting

NA2 and NUN5 store the same 24 `(stage_id, index)` pairs in the same order:

- NA2 BTL file offset `0x20FC10`: 24 records of 16 bytes, with an inline
  `(u, v, width, height)` rectangle after the two key words;
- NUN5 BTL file offset `0x215680`: 24 records of 8 bytes containing the two
  matching key words.

NUN5 obtains the localized rectangle separately through `FUN_003d4120`. Its
English language table is the 24-entry rectangle range at NUN5 ELF file offset
`0x4DDB90`. The NUN5 draw path also fits names wider than 214 pixels with
`min(1.0, 214.0 / width)`; copying only the rectangles would therefore preserve
the clipping visible in NA2.

`UI-BTL-002` reproduces both parts without adding a jump or overwriting a code
cave. In the NA2 table, every second key word is exactly the matched loop index.
The only other code consumer at BTL file offset `0x606BC` is changed from loading
that redundant word to `move s0,s1`. The freed word in each record stores the
precomputed single-precision NUN5 scale. At BTL file offset `0x6156C`, the
original `1.0` initialization becomes `lwc1 f14,4(v1); nop`. The remaining 24
rectangle fields are copied from the hash-pinned NUN5 ELF table.

The patch is 50 individually guarded edits. A temporary application verified
that all 24 stage keys remain unchanged and match NUN5, every rectangle equals
the official English table, every scale equals the NUN5 formula, all changed
bytes stay inside declared ranges, and the 2,237,184-byte BTL size is unchanged.
Runtime comparison is still required before promotion from `approved_for_test`.

## UI-ELF-001: localized character-name atlas rectangles

The character-select renderer does not obtain character-name rectangles from
`CHARSEL1.CCS`. Its paired helper functions read homologous 96-entry tables in
the boot ELF:

- NA2 `FUN_0037d410`: EE `0x005D4E70`, ELF file offset `0x4D4F70`;
- NUN5 `FUN_0038c3a0`: EE `0x005DBFA0`, ELF file offset `0x4DC120`.

Each record is four signed 16-bit values `(u, v, width, height)`. All 96 records
differ: NA2 uses variable Japanese rectangles, while NUN5 uses the official
localized grid consumed by the complete NUN5 `CHARSEL1.CCS` atlas. Copying the
entire 768-byte NUN5 table is therefore the minimal complete fix; isolated
per-character corrections would preserve wrong records elsewhere. The edit is
range-hash guarded at both source and destination and preserves the ELF size.

## UI-ELF-002: localized Options label rectangles

Importing the complete NUN5 `OPTION.CCS` is not sufficient by itself. The main
Options renderer supplies atlas rectangles from the boot ELF:

- NA2 `FUN_0038c160` reads five menu-label records at EE `0x005D52E0` and
  six difficulty-label records at EE `0x005D5310`;
- NUN5 `FUN_0039dba0` obtains the homologous English records through
  `FUN_003d43a0` and `FUN_003d43f0`, whose English tables begin at EE
  `0x005DDB90` and `0x005DDBC0`.

Both renderers use the same five screen positions and `0.9` scales. Their arrow
rectangle is also byte-identical. The remaining difference is the 96-byte
rectangle block: five menu labels, an eight-byte zero separator, and six
difficulty labels. `UI-ELF-002` copies that complete official English block from
NUN5 ELF file offset `0x4DDD10` to NA2 ELF file offset `0x4D53E0`. Source and
destination ranges are hash guarded and the ELF size is preserved.

Inspect all four approved-for-test patches together:

```powershell
python -m na2_patcher.modules.raw_binary.engine validate `
  --package na2_patcher/modules/raw_binary/patch_sets/ui_translation `
  --root na2=@source/NA2.iso.files `
  --root nun5=@source/NUN5.iso.files

python -m na2_patcher.modules.raw_binary.engine plan `
  --package na2_patcher/modules/raw_binary/patch_sets/ui_translation `
  --root na2=@source/NA2.iso.files `
  --root nun5=@source/NUN5.iso.files `
  --patch UI-BTL-001 `
  --patch UI-BTL-002 `
  --patch UI-ELF-001 `
  --patch UI-ELF-002
```
