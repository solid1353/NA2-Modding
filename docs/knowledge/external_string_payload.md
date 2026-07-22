# External String Payload

Status: initial two-file integration and runtime boot confirmed, 2026-07-20;
compact one-file integration and hidden boot confirmed, 2026-07-22. Broader
runtime and visual coverage of the compact build remains pending. Canonical
translation mappings remain importer-owned and hash-pinned.

## Conclusion

The current architecture uses exactly one generated file under `PRG/` without
expanding the ISO image or adding a renderer hook. `228.BIN` is a resident MWO3
type-8 code/data image: it has a return-only entry stub followed by the compact
official string pool.

It externalizes only the messages needed to eliminate the 33 enabled `[S]`
`shorten` fallbacks. All 33 are statically addressable: 30 rows have direct
address references and three continuation rows are covered through their
containing full-message pointer. The inventory resolves to 35 distinct pointer
words and 31 logical external messages at 30 distinct encoded locations.
Consequently, the design does not need a renderer hook or post-load pointer
rewrite.

The original two-file prototype copied the complete NUN5 `TEXTENG.BIN` and
loaded a separate 256-byte MOD bootstrap. That proved the loader, ISO insertion,
and resident-address strategy, but more than 99 percent of the copied text file
was unused. The compact design keeps only 1,512 encoded bytes plus alignment and
one small MWO3 envelope, for a deterministic `0x720`-byte `228.BIN`.

### What `TEXTENG.BIN` contains

The official NUN5 donor is not a flat string pool. It mixes zero-terminated
English strings with absolute in-image pointer tables that index whole strings
and, in some cases, interior fragments. The strings cover character and move
names, mode/menu labels, prompts, battle and Practice help, conditions,
collection text, story/mission prose, and save/load messages. They use an
ASCII-compatible Western single-byte encoding with markup such as `<br>` and
`<color...>`; the importer uses CP1252 for exact selected-string round trips.

The preserved Ghidra import identifies zero functions and zero instructions.
A separate aligned scan of the clean `0x30D00`-byte donor found 3,697 words in
the donor's own loaded-address range. Of those, 3,617 point exactly to 2,990
distinct printable, zero-terminated string starts. This establishes that the
file is structured localization data with extensive internal indexing, not
code and not merely concatenated text. The remaining 80 in-range words were not
classified and may include non-string structures or incidental values.

The current NA2 integration does not adopt NUN5's language accessor system or
consume the donor's pointer tables. The importer resolves the same 31 logical
messages from canonical mapping provenance, applies four existing transforms,
encodes them as CP1252 plus terminators, and packs the 30 distinct byte strings
at four-byte-aligned offsets. M2003 and M2065 share one byte-identical value.

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
  `na2_patcher/features/localization/translation_importer/mappings.tsv`;
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
`0x006B3F00`, and zeroes thereafter. The guarded string patcher assigns slot 2
= `0x008F3D00` for `228.BIN`; slot 3 remains zero.

The loader has no observed slot bounds check and retries failed reads. Missing,
misnamed, or truncated external files may therefore hang rather than fail
cleanly. Build-time validation of the file and its ISO directory record is
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
| Compact `228.BIN` envelope | `0x008F3D00` | `0x720` | `0x008F4420` |

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
but now moves only to the compact file's fixed end at `0x008F4420`. Compared
with the proven two-file boundary at `0x00940100`, this recovers `0x4BCE0`
bytes. Matched captures of the two-file build confirmed its exact `0x63080`
heap reduction and substantial allocator headroom in eight representative
states; see
[`ee_runtime_memory_map.md`](ee_runtime_memory_map.md). This is representative
capacity evidence, not proof of every result/save/transition peak.

## Compact one-file bootstrap

The generated bootstrap is:

1. Patch the existing call at runtime `0x001E0F20` in NA2 constructor
   `FUN_001e0ee0` to a tiny resident ELF stub.
2. The stub preserves the constructor argument and return address, calls
   `FUN_001be7f0(2, "228.BIN")`, invokes the documented module entry, calls the
   original `FUN_001bda50`, and returns normally.
3. The MOD entry is a return-only stub reserved for later string-runtime code.
4. Static guarded patches redirect every selected SLPS/BTL/ETC pointer to its
   compact MOD-resident string address.

A 76-byte stub/string payload uses the start of ELF file range
`0x00507414-0x0050747F` (runtime `0x00607314-0x0060737F`), which contains 108
guarded zero bytes at the end of the main load segment. An aligned exact-pointer
scan of SLPS, BTL, and ETC found no reference into it. Runtime testing must still
confirm that the cave is safe.

Compact MOD generation is deterministic and reproducible:

- use a stable mapping-ID order and CP1252 encoding;
- obtain the exact official string through each mapping's existing
  `source_ref` and transform metadata;
- keep the current mapping table unchanged; the importer passes its validated
  semantic data and pointer inventory directly to `string_patcher`;
- emit one full official message for each continuation group, rather than
  separately addressing the continuation fragments;
- deduplicate byte-identical strings only when every affected pointer is
  deliberately recorded;
- emit a guarded patch plan that records each pointer's original bytes and new
  symbolic target; the composer resolves the address after payload linking.

The generated output is:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `PRG/228.BIN` | 1,824 | `AD94B66F2916C0014A87D110F5807DC0F0F5D7E91615AE3F04EC970CFBA00E9F` |

The pool starts at file offset `0x100`. Thirty distinct terminated strings use
1,512 bytes before alignment, and the linked output rounds to `0x720`.

The three continuation mappings are M0812 through parent M0810, M0820 through
parent M0818, and M0825 through parent M0823. M0823 is an enabled `slot` row,
not an `[S]` row, but the external pool must emit its complete official message
to make the M0825 continuation reachable through that one parent pointer. The
complete reusable inventory is now canonical module data in
`na2_patcher/features/localization/translation_importer/references.tsv`.

BTL and ETC themselves contain the applicable pointer words. A static patch to
those files is therefore restored whenever the overlay loads; no post-load
runtime rewrite is required. Strings resident above the largest overlay remain
outside the BTL/ETC overwrite region.

## Module boundary

External placement is integrated across the existing importer/string-patcher
pipeline; there is no separate `external_translation` module. The importer owns
source resolution, provenance validation, and pointer references. The mapping
schema, values, defaults, migration behavior, and enabled state remain
unchanged. The shared payload builder owns final layout and global integration.

The resulting pipeline owns:

- deterministic linking and validation of compact `228.BIN` by `payload_builder`;
- symbolic SLPS/BTL/ETC pointer edits from `string_patcher`, resolved by the
  composer, plus infrastructure-owned loader/memory structural edits;
- a machine-readable patch log for every binary write;
- one insertion request through the general compositor interface.

The translation importer produces validated rows, resolved mapping/source data,
and the reference inventory. `string_patcher` filters the 33 `shorten` import
rows before they become binary edits, contributes 30 unique string fragments,
and declares 35 symbolic redirects. `payload_builder` links those fragments and
owns the 15 loader/layout edits; all concrete writes are delegated to
`binary_patcher`. Therefore there is no write-then-restore pass. The `[S]`
values remain canonical fallback/debt markers. `ADV.bin` remains excluded.

## ISO integration constraint

The NA2 ISO is 1,928,429,568 bytes (941,616 sectors). Its `PRG` directory is at
extent 265 / byte offset `0x84800`, has a logical size of 264 bytes, and occupies
one 2,048-byte sector. Adding the 42-byte ISO 9660 record for `228.BIN;1` keeps
the directory in that sector with a new logical size of 306 bytes.

The static layout has a 10,255-sector (21,002,240-byte) tail after the last
allocated file. It is zero except for 14 bytes in the final sector. The payload
extent fits without increasing the ISO byte length, but an allocator
must preserve the final nonzero bytes and validate every selected sector rather
than assuming the whole tail is disposable.

The Project compositor now has general validated hybrid-filesystem insertion
support. It mirrors inserted records into the primary ISO9660 and UDF trees, updates
their directory and file-entry metadata, allocates payloads and new UDF file
entries only in verified-zero extents, updates the UDF integrity file count,
and mirrors the boot-ELF rename into UDF. It rejects a stale or divergent bridge
before writing, then reparses both filesystems and requires identical paths,
types, extents, sizes, payload hashes, source preservation, and unchanged ISO
size. This remains general compositor behavior rather than a translation-only
byte hack.

NA2's `FLIST` does not list `228.BIN`. NUN6 adds `prg\MOD.BIN` to
its `FLIST` but does not add `TEXTBRA.BIN`. NA2 startup uses FLIST as a
cache-warming manifest: it resolves each normalized path to an in-memory LSN and
size entry, while a cache miss falls back to ordinary disc search. The external
file is loaded once through an explicit `cdrom0:\PRG\...` path, so adding it
would only move the same lookup work earlier. On 2026-07-20, the user confirmed
that the preceding two-file ISO worked in-game with the original NA2 FLIST
unchanged. The compact Candidate also completed a hidden boot without a FLIST
edit.

## Validation gates

Implemented and covered by focused tests:

1. A dependency-free MIPS encoder generates the payload-builder ELF bootstrap; exact
   instruction-word tests verify its loader, MOD-entry, constructor calls, and
   return.
2. `228.BIN` is exactly `0x720` bytes, has a pinned hash, and every emitted
   pointer lies within its declared compact string image.
3. Generation resolves all 33 selected mappings as 30 direct rows and three
   parent-message continuations, produces 35 distinct pointer writes, omits all
   33 inline fallback mappings, and refuses any count or original-byte mismatch.
4. The 35 string redirects and 15 infrastructure edits remain separately owned;
   the final marker and every hardcoded boundary site still change together.
5. The Project-owned compositor validates the ISO9660/UDF insertion, its record,
   extent, bytes, hash, fixed image size, original files, and final
   mirrored tree.

Confirmed at runtime:

1. The preceding two-file ISO loaded both external PRG files and worked in-game
   without adding either path to `FLIST.DIR`. The compact one-file Candidate
   completed a hidden 15-second PCSX2 boot with CRC `18BBBDC0`; representative
   visible shortened-string screens remain untested.
2. Eight matched vanilla/Current captures cover title, mode select, active
   Adventure, character select, active battle, Shop, Collection, and Options.
   The Current heap remains valid in all eight; active Adventure is the tightest
   observed state at `0x759260` total free and `0x52B4C0` largest contiguous.
   The full evidence is in
   [`ee_runtime_memory_map.md`](ee_runtime_memory_map.md).

Still required at runtime:

1. Exercise result, save/load, and repeated mode transitions to extend the
   smaller-heap stress coverage beyond the representative capture set.
2. Visit representative shortened-string screens and confirm the full official
   strings render from external memory.
