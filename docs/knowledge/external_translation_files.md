# External Translation Files

Status: static-analysis result, 2026-07-19. No NA2 binary, ISO, profile, or
translation mapping was changed, and the proposed loader has not been tested at
runtime.

## Conclusion

NA2 can plausibly support external translation data without expanding the ISO
image or adding a renderer hook. The intended architecture is exactly two files
under `PRG/`:

- `MOD.BIN`: resident MWO3 code containing the external-text bootstrap and any
  later translation-specific runtime logic;
- `TEXTENG.BIN`: resident MWO3 data containing a deterministic CP932 string
  pool.

This is not a proposal to replace those files with one combined file. The first
implementation should externalize only the messages needed to eliminate the 33
enabled `[S]` `shorten` mappings. All 33 are statically addressable: 30 rows have
direct address references and three continuation rows are covered through their
containing full-message pointer. The inventory resolves to 35 distinct pointer
words because two strings have three references each, two continuation rows
share their already-recorded parent pointer, and the M0825 continuation adds the
M0823 parent pointer. Consequently, the initial design does not need to hook the
renderer or rewrite pointers after BTL/ETC loads.

The design is feasible on static evidence, but it depends on controlled ISO file
insertion that the current profile compositor deliberately does not support. It
also needs runtime validation of the new memory reservation, boot hook, file
lookup, and mode transitions before it can become an enabled module.

## Evidence and provenance

The source artifacts remained read-only. The principal artifacts inspected were:

| Game | Artifact | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| NA2 | `@source/NA2.iso.files/SLPS_258.37` | 5,273,256 | `20C0A40D70EA412CD431993A2E189B37ECB6054D63AE93BE545470016E1627AF` |
| NA2 | `@source/NA2.iso.files/PRG/BTL.BIN` | 2,237,184 | `56FD042740221E3CC91417194F147142799D51FE70642273F4E97BD389D5D63C` |
| NA2 | `@source/NA2.iso.files/PRG/ETC.BIN` | 200,448 | `8FF3C6E1ED5CE2B093B0934C898C40D1CEEA0C20778C49CDA5591AAD02375C74` |
| NUN5 | `@source/NUN5.iso.files/SLES_556.05` | 5,340,912 | `20A43677397731A2A20899336D1165ACE5B436906B9B89BE90FB10F4558DD19D` |
| NUN5 | `@source/NUN5.iso.files/PRG/TEXTENG.BIN` | 199,936 | `3E42D2DDFFE770B05DD41E2C5937380133E255C9CE32CA2F037E34C65A8E571E` |
| NUN6 A35 | `@source/NUN6 A35.iso.files/SLUS_556.06` | 5,340,912 | `47C40141A3E1AEB0C96BC28E8DC311938B284D54FD21F4D8BA953C2E16234809` |
| NUN6 A35 | `@source/NUN6 A35.iso.files/PRG/MOD.BIN` | 804,320 | `6EAB9760D2BD6583630D096EB08FB7F09E299F5E2FB64DF2413E5DC2ED182998` |
| NUN6 A35 | `@source/NUN6 A35.iso.files/PRG/TEXTBRA.BIN` | 312,064 | `07E30831DC9E88BA4E0DDB1B4F3FD8EDD0D8C4D1CF170BD59BFCB17C09E256BF` |

Methods and tools:

- maintained Ghidra 12.1.2 projects/exports under
  `@analysis/disassembly/NA2/`, `@analysis/disassembly/NUN5/`, and
  `@analysis/disassembly/NUN6/`;
- `scripts/research/menu_input/find_mips_address_refs.py` and
  `scripts/research/menu_input/disassemble_mips32_range.py`;
- quote-aware parsing of
  `na2_patcher/modules/translation/mappings.tsv`;
- aligned little-endian pointer scans plus PowerShell size, hash, ISO-layout,
  and byte inspection.

`ADV.bin` was neither inspected nor changed for this research.

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
raw-memory/file-offset formula. Any future implementation must state which
convention it uses and verify raw bytes before writing a jump or pointer.

## NA2 loader and memory layout

NA2's generic PRG loader `FUN_001be7f0(slot, filename)`:

1. reads the destination from the table at runtime `0x006029C0` (ELF file
   offset `0x00502AC0`);
2. constructs `cdrom0:\PRG\<filename>`;
3. opens and reads the file directly;
4. passes the loaded MWO3 image to `FUN_00100270` for cache maintenance, BSS
   clearing, and constructor processing.

The destination table currently has slot 0 = `0x00100000`, slot 1 =
`0x006B3F00`, and zeroes thereafter. A future guarded patch can assign:

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

The NUN6-compatible candidate reservation is:

| Region | Base | Maximum bytes | End |
| --- | ---: | ---: | ---: |
| Existing NA2 overlays | `0x006B3F00` | `0x229180` | `0x008DD080` |
| Safety gap | `0x008DD080` | `0x16C80` | `0x008F3D00` |
| `TEXTENG.BIN` envelope | `0x008F3D00` | `0x4C300` | `0x00940000` |
| `MOD.BIN` envelope | `0x00940000` | `0xE8900` | `0x00A28900` |

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
pairs and final marker to `0x00A28900`, which is strong donor evidence that all
sites must move together. Runtime safety in NA2 is still unproved: this change
reduces the heap by approximately `0x14B880` bytes.

## Fixed two-file bootstrap

The smallest coherent bootstrap is:

1. Patch the existing call at runtime `0x001E0F20` in NA2 constructor
   `FUN_001e0ee0` to a tiny resident ELF stub.
2. The stub preserves the constructor argument and return address, calls
   `FUN_001be7f0(2, "MOD.BIN")`, invokes a fixed, documented MOD bootstrap
   entry, calls the original `FUN_001bda50`, and returns normally.
3. The MOD bootstrap calls `FUN_001be7f0(3, "TEXTENG.BIN")` and returns.
4. Static guarded patches redirect every selected SLPS/BTL/ETC pointer to its
   generated `TEXTENG.BIN` string address.

A candidate stub/string cave exists at ELF file range
`0x00507414-0x0050747F` (runtime `0x00607314-0x0060737F`): 108 zero bytes at the
end of the main load segment. An aligned exact-pointer scan of SLPS, BTL, and ETC
found no reference into it. This remains a hypothesis until control-flow and
runtime testing confirm the range is safe.

`TEXTENG.BIN` should be deterministic and reproducible:

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

The three continuation mappings are M0812 through parent M0810, M0820 through
parent M0818, and M0825 through parent M0823. M0823 is an enabled `slot` row,
not an `[S]` row, but the external pool must emit its complete official message
to make the M0825 continuation reachable through that one parent pointer. The
complete reusable inventory is in `external_translation_shortening_refs.tsv`.

BTL and ETC themselves contain the applicable pointer words. A static patch to
those files is therefore restored whenever the overlay loads; no post-load
runtime rewrite is required. Strings resident above the largest overlay remain
outside the BTL/ETC overwrite region.

## Future module boundary

This should be a separate project-side `external_translation` module, not a
change to the existing translation builder, mapping schema, mapping values,
defaults, migration behavior, or enabled-state behavior. Its pinned inputs
should include the exact current `mappings.tsv` hash and the official NUN5
source artifacts already resolved through the shared project-path loader.

The module should own:

- deterministic generation and validation of `MOD.BIN` and `TEXTENG.BIN`;
- guarded SLPS/BTL/ETC pointer edits and the loader/memory structural edits;
- a machine-readable patch log for every binary write;
- requests for the two new ISO paths through the general compositor interface.

The existing translation module should continue applying all current inline
translations first. The external module then redirects only the selected
shortening cases; the now-unreferenced shortened inline bytes remain harmless
and preserve current behavior when the external module is disabled. `ADV.bin`
is outside this module and remains excluded.

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

The current compositor intentionally rejects file-size changes, requires the
result tree to match the source tree plus the identity rename, and exposes only
read-only ISO 9660 parsing. Implementation therefore has a Project-workstream
dependency: add general, validated ISO-file insertion support that can write the
two records, update the PRG `.` and root/parent directory-size metadata, allocate
verified extents, and revalidate the final tree and unchanged ISO size. This
must not be implemented as a translation-only byte hack.

NA2's `FLIST` does not list either external file. NUN6 adds `prg\MOD.BIN` to
its `FLIST` but does not add `TEXTBRA.BIN`. NA2's generic loader opens explicit
`cdrom0:\PRG\...` paths, and the inspected FLIST path only normalizes name
case and separators. The minimal proof of concept should therefore omit an
FLIST edit initially and treat successful direct loading as a runtime test. Add
an FLIST record only if that test proves it necessary.

## Required implementation gates

Before this architecture can be enabled, a future task must verify all of the
following:

1. The Project-owned compositor can add both files while preserving ISO size,
   existing files, directory validity, and source immutability.
2. The final marker and every hardcoded boundary site are changed together and
   pass boot, frontend, battle, result, save/load, and repeated mode-transition
   testing.
3. The selected PS2/R5900 assembler or toolchain is documented and
   reproducible. No suitable compiler/assembler was present on PATH during this
   research.
4. `MOD.BIN` is within `0xE8900` bytes, `TEXTENG.BIN` is within `0x4C300` bytes,
   and every emitted pointer lies within the declared text image.
5. Generation resolves all 33 selected mappings as 30 direct rows and three
   parent-message continuations, produces the expected 35 distinct pointer
   writes, and refuses any count or original-byte mismatch.
6. Both ISO entries exist with the expected names, lengths, hashes, and extents
   before launch; missing-file behavior is never left to the loader's retry
   loop.
7. Runtime testing confirms that direct loading works without an FLIST entry;
   if not, the FLIST requirement is documented and implemented explicitly.
