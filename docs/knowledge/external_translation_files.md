# External Translation Files

Status: generated module and profile integration implemented, 2026-07-19;
initial real-ISO boot and direct external-file loading confirmed, 2026-07-20;
broader runtime coverage remains pending. The canonical translation mapping is
unchanged.

## Conclusion

The implemented architecture uses exactly two generated files under `PRG/`
without expanding the ISO image or adding a renderer hook:

- `MOD.BIN`: resident MWO3 code containing the external-text bootstrap and any
  later translation-specific runtime logic;
- `TEXTENG.BIN`: resident MWO3 data containing a deterministic CP932 string
  pool.

These files are deliberately not combined. The first implementation
externalizes only the messages needed to eliminate the 33
enabled `[S]` `shorten` mappings. All 33 are statically addressable: 30 rows have
direct address references and three continuation rows are covered through their
containing full-message pointer. The inventory resolves to 35 distinct pointer
words because two strings have three references each, two continuation rows
share their already-recorded parent pointer, and the M0825 continuation adds the
M0823 parent pointer. Consequently, the initial design does not need to hook the
renderer or rewrite pointers after BTL/ETC loads.

The generator, guarded edit plan, profile module type, and controlled ISO-file
insertion are implemented and unit-tested. Runtime validation of the new memory
reservation, boot hook, direct file lookup, and mode transitions is still
required.

## Evidence and provenance

The source artifacts remained read-only. The principal artifacts inspected were:

| Game | Artifact | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| NA2 | `@source_na2/SLPS_258.37` | 5,273,256 | `20C0A40D70EA412CD431993A2E189B37ECB6054D63AE93BE545470016E1627AF` |
| NA2 | `@source_na2/PRG/BTL.BIN` | 2,237,184 | `56FD042740221E3CC91417194F147142799D51FE70642273F4E97BD389D5D63C` |
| NA2 | `@source_na2/PRG/ETC.BIN` | 200,448 | `8FF3C6E1ED5CE2B093B0934C898C40D1CEEA0C20778C49CDA5591AAD02375C74` |
| NUN5 | `@source_nun5/SLES_556.05` | 5,340,912 | `20A43677397731A2A20899336D1165ACE5B436906B9B89BE90FB10F4558DD19D` |
| NUN5 | `@source_nun5/PRG/TEXTENG.BIN` | 199,936 | `3E42D2DDFFE770B05DD41E2C5937380133E255C9CE32CA2F037E34C65A8E571E` |
| NUN6 A35 | `@source_nun6/SLUS_556.06` | 5,340,912 | `47C40141A3E1AEB0C96BC28E8DC311938B284D54FD21F4D8BA953C2E16234809` |
| NUN6 A35 | `@source_nun6/PRG/MOD.BIN` | 804,320 | `6EAB9760D2BD6583630D096EB08FB7F09E299F5E2FB64DF2413E5DC2ED182998` |
| NUN6 A35 | `@source_nun6/PRG/TEXTBRA.BIN` | 312,064 | `07E30831DC9E88BA4E0DDB1B4F3FD8EDD0D8C4D1CF170BD59BFCB17C09E256BF` |

Methods and tools:

- maintained Ghidra 12.1.2 projects/exports under
  `@analysis/disassembly/NA2/`, `@analysis/disassembly/NUN5/`, and
  `@analysis/disassembly/NUN6/`;
- `scripts/research/menu_input/find_mips_address_refs.py` and
  `scripts/research/menu_input/disassemble_mips32_range.py`;
- quote-aware parsing of
  `na2_patcher/modules/translation_importer/mappings.tsv`;
- aligned little-endian pointer scans plus PowerShell size, hash, ISO-layout,
  and byte inspection.

`ADV.bin` was neither inspected nor changed by the research or implementation.

## Donor behavior

### NUN5

NUN5 ships five MWO3 localization data files: `TEXTENG.BIN`, `TEXTFRN.BIN`,
`TEXTGER.BIN`, `TEXTITA.BIN`, and `TEXTSPA.BIN`. Its boot ELF selects a language,
loads the corresponding file at `0x008F3D00`, and exposes language-indexed string
accessors. Relevant established functions are:

- `FUN_003d3e50`: maps the system language and begins localization loading;
- `FUN_003d3ef0`: loads the selected `TEXT*.BIN` at `0x008F3D00`;
- `FUN_003d4000`, `FUN_003d4040`, and `FUN_003d4110`: language setter,
  reload, and getter paths;
- `FUN_001e6b20`: constructor path that invokes localization before its normal
  initialization;
- `FUN_00100300`: MWO3 loader.

The NUN5 filename block begins at runtime `0x005BB228`, its pointer table at
`0x005BB280`, and its path prefix at `0x005BB298`.

### NUN6 A35

NUN6 A35 is a Brazilian modification of NUN5. It retains the five language
slots but makes only the first slot non-null (`TextBra.bin`). It also adds
`MOD.BIN`, redirects the NUN5 loader's filename and destination to that module,
and transfers control into resident MOD code.

Its relevant MWO3 envelopes are:

| File | Kind | Load base | File bytes | Reserved end |
| --- | ---: | ---: | ---: | ---: |
| `TEXTBRA.BIN` | 4 | `0x008F3D00` | `0x4C300` | up to `0x00940000` |
| `MOD.BIN` | 8 | `0x00940000` | `0xC45E0` | below `0x00A28900` |

NUN6 also changes four NUN5 metadata pointers into MOD-resident data:

| Runtime pointer location | NUN5 value | NUN6 value |
| ---: | ---: | ---: |
| `0x005BB2B0` | `0x005DDA10` | `0x00968E80` |
| `0x005BB490` | `0x005DDC50` | `0x0095A2A0` |
| `0x005BB870` | `0x005DE550` | `0x0095B2A0` |
| `0x005BB930` | `0x005DE8B0` | `0x0095AAA0` |

The NUN6 boot patch is valuable precedent, not directly reusable NA2 code.
NUN6 and NUN5 share a different main/overlay layout from NA2.

### MWO3 address convention

MWO3 files begin with a `MWo3` header. For loaded data and pointers, raw file
offset maps as `load_base + file_offset`; the header occupies the first `0x40`
bytes in memory. Some existing Ghidra MOD imports map file offset `0x40` to the
displayed load base, so their displayed code labels are `0x40` lower than the
raw-memory/file-offset formula. The implementation uses the raw formula and
verifies every generated jump, pointer, and source byte.

## NA2 loader and memory layout

NA2's generic PRG loader `FUN_001be7f0(slot, filename)`:

1. reads the destination from the table at runtime `0x006029C0` (ELF file
   offset `0x00502AC0`);
2. constructs `cdrom0:\PRG\<filename>`;
3. opens and reads the file directly;
4. passes the loaded MWO3 image to `FUN_00100270` for cache maintenance, BSS
   clearing, and constructor processing.

The clean destination table has slot 0 = `0x00100000`, slot 1 =
`0x006B3F00`, and zeroes thereafter. The guarded module assigns:

- slot 2 = `0x00940000` for `MOD.BIN`;
- slot 3 = `0x008F3D00` for `TEXTENG.BIN`.

The loader has no observed slot bounds check and retries failed reads. Missing,
misnamed, or truncated external files may therefore hang rather than fail
cleanly. Build-time validation of both files and both ISO directory records is
mandatory.

NA2's ELF currently describes:

- the main resident image from `0x00100000` to `0x006B3F00`;
- mutually exclusive overlays based at `0x006B3F00`, with the largest ending at
  `0x008DD080`;
- a final zero-size marker at `0x008DD080`.

The implemented minimal reservation is:

| Region | Base | Maximum bytes | End |
| --- | ---: | ---: | ---: |
| Existing NA2 overlays | `0x006B3F00` | `0x229180` | `0x008DD080` |
| Safety gap | `0x008DD080` | `0x16C80` | `0x008F3D00` |
| `TEXTENG.BIN` envelope | `0x008F3D00` | `0x4C300` | `0x00940000` |
| `MOD.BIN` envelope | `0x00940000` | `0x100` | `0x00940100` |

Moving the final marker is a structural patch, not merely a program-header
edit. Four NA2 instruction pairs construct the current `0x008DD080` boundary:

| ELF file offsets | Runtime site/purpose |
| --- | --- |
| `0x00000220`, `0x00000228` | startup boundary reference at `0x00100120` |
| `0x000002D0`, `0x000002D8` | startup boundary reference at `0x001001D0` |
| `0x0001885C`, `0x00018860` | heap-size calculation in `FUN_00118730` |
| `0x004D6908`, `0x004D690C` | upper-memory marker write near `0x005D6800` |

The corresponding structural occurrences also include program-header words at
file offsets `0xBC` and `0xC0`, a literal pointer at `0x2F79F4`, and a section
header address at `0x50763C`. NUN6 changes the equivalent four instruction
pairs and final marker together; the module follows that structural precedent
but moves only to its actual fixed end at `0x00940100`. Runtime safety in NA2 is
still unproved; the implemented change reduces the heap by `0x63080` bytes.

## Fixed two-file bootstrap

The generated bootstrap is:

1. Patch the existing call at runtime `0x001E0F20` in NA2 constructor
   `FUN_001e0ee0` to a tiny resident ELF stub.
2. The stub preserves the constructor argument and return address, calls
   `FUN_001be7f0(2, "MOD.BIN")`, invokes a fixed, documented MOD bootstrap
   entry, calls the original `FUN_001bda50`, and returns normally.
3. The MOD bootstrap calls `FUN_001be7f0(3, "TEXTENG.BIN")` and returns.
4. Static guarded patches redirect every selected SLPS/BTL/ETC pointer to its
   generated `TEXTENG.BIN` string address.

A 76-byte stub/string payload uses the start of ELF file range
`0x00507414-0x0050747F` (runtime `0x00607314-0x0060737F`), which contains 108
guarded zero bytes at the end of the main load segment. An aligned exact-pointer
scan of SLPS, BTL, and ETC found no reference into it. Runtime testing must still
confirm that the cave is safe.

`TEXTENG.BIN` generation is deterministic and reproducible:

- use a stable mapping-ID order and CP932 encoding;
- obtain the exact official string through each mapping's existing
  `source_ref` and transform metadata;
- keep the current mapping table unchanged; a separate project-side external
  translation module consumes it;
- emit one full official message for each continuation group, rather than
  separately addressing the continuation fragments;
- deduplicate byte-identical strings only when every affected pointer is
  deliberately recorded;
- emit a guarded patch plan that records each pointer's original bytes and new
  address.

The generated outputs are:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `PRG/MOD.BIN` | 256 | `C00D69E124E425741745B7B61A2FE07B48AFD729806F96113C6FF81D957706DA` |
| `PRG/TEXTENG.BIN` | 200,192 | `AA5E7C6ADCDFDC3A7695AF295DD488EA91D926B01ED9DDD191550C98E3F4EAB9` |

The text output copies the official NUN5 file exactly after its updated MWO3
header and appends only four mapping-derived strings at offsets `0x30D00`,
`0x30D3C`, `0x30D74`, and `0x30D98`.

The three continuation mappings are M0812 through parent M0810, M0820 through
parent M0818, and M0825 through parent M0823. M0823 is an enabled `slot` row,
not an `[S]` row, but the external pool must emit its complete official message
to make the M0825 continuation reachable through that one parent pointer. The
complete reusable inventory is now canonical module data in
`na2_patcher/modules/external_translation/pointer_refs.tsv`.

BTL and ETC themselves contain the applicable pointer words. A static patch to
those files is therefore restored whenever the overlay loads; no post-load
runtime rewrite is required. Strings resident above the largest overlay remain
outside the BTL/ETC overwrite region.

## Module boundary

This is a separate project-side `external_translation` module, not a change to
the translation importer, mapping schema, mapping values, defaults, migration
behavior, or enabled-state behavior. Its manifest pins the exact current
`mappings.tsv` hash and all source/output hashes; source artifacts are resolved
through the shared project-path loader.

The module owns:

- deterministic generation and validation of `MOD.BIN` and `TEXTENG.BIN`;
- guarded SLPS/BTL/ETC pointer edits and the loader/memory structural edits;
- a machine-readable patch log for every binary write;
- requests for the two new ISO paths through the general compositor interface.

The translation importer first produces validated rows and `string_patcher`
applies all selected inline translations through `binary_patcher`. The external
module then redirects only the selected shortening cases and restores their
now-dead inline slots to exact clean NA2 bytes. When the external module is
disabled, `string_patcher` still produces the current `[S]` fallback text.
`ADV.bin` is outside this module and remains excluded.

## ISO integration constraint

The NA2 ISO is 1,928,429,568 bytes (941,616 sectors). Its `PRG` directory is at
extent 265 / byte offset `0x84800`, has a logical size of 264 bytes, and occupies
one 2,048-byte sector. Adding ISO 9660 records for `MOD.BIN;1` and
`TEXTENG.BIN;1` requires 42 and 46 bytes respectively, so the directory remains
within that existing sector with a new logical size of 352 bytes.

The static layout has a 10,255-sector (21,002,240-byte) tail after the last
allocated file. It is zero except for 14 bytes in the final sector. The two
payload extents fit without increasing the ISO byte length, but an allocator
must preserve the final nonzero bytes and validate every selected sector rather
than assuming the whole tail is disposable.

The Project compositor now has general validated hybrid-filesystem insertion
support. It mirrors both records into the primary ISO9660 and UDF trees, updates
their directory and file-entry metadata, allocates payloads and new UDF file
entries only in verified-zero extents, updates the UDF integrity file count,
and mirrors the boot-ELF rename into UDF. It rejects a stale or divergent bridge
before writing, then reparses both filesystems and requires identical paths,
types, extents, sizes, payload hashes, source preservation, and unchanged ISO
size. This remains general compositor behavior rather than a translation-only
byte hack.

NA2's `FLIST` does not list either external file. NUN6 adds `prg\MOD.BIN` to
its `FLIST` but does not add `TEXTBRA.BIN`. NA2 startup uses FLIST as a
cache-warming manifest: it resolves each normalized path to an in-memory LSN and
size entry, while a cache miss falls back to ordinary disc search. The external
files are each loaded once through explicit `cdrom0:\PRG\...` paths, so adding
them would only move the same lookup work earlier. On 2026-07-20, the user
confirmed that the integrated ISO works in-game with the original NA2 FLIST
unchanged; no FLIST edit is required or included.

## Validation gates

Implemented and covered by focused tests:

1. A dependency-free MIPS encoder generates the two fixed bootstrap routines;
   exact instruction-word tests verify their calls and returns.
2. `MOD.BIN` is exactly `0x100` bytes, `TEXTENG.BIN` is `0x30E00` bytes, and
   every emitted pointer lies within the declared text image.
3. Generation resolves all 33 selected mappings as 30 direct rows and three
   parent-message continuations, produces 35 distinct pointer writes and 35
   inline reversals, and refuses any count or original-byte mismatch.
4. The final marker and every hardcoded boundary site change together in one
   guarded 85-edit plan.
5. The Project-owned compositor validates both ISO9660/UDF insertions, their
   records, extents, bytes, hashes, fixed image size, original files, and final
   mirrored tree.

Confirmed at runtime:

1. The integrated ISO loads both external PRG files and works in-game without
   adding either path to `FLIST.DIR`.

Still required at runtime:

1. Exercise frontend, battle, result, save/load, and repeated mode transitions
   to test the smaller heap and resident-memory boundary.
2. Visit representative shortened-string screens and confirm the full official
   strings render from external memory.
