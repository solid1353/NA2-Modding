# Save-data record format and lifecycle

This document describes the resident-ELF save implementation of retail NA2
(`SLPS-25837`). It covers the on-card file set, the `0x2400`-byte profile
record, validation and copy behavior, profile defaults, and the relationship
between the three visible slots and the UI-hidden fourth record. Embedded
card-service modules establish lower descriptor reclamation and directory
ordering. BTL field consumers establish part of the secondary counter bank.
Adventure-mode field consumers are deliberately out of scope.

## Research coverage

- **Assigned scope:** the clean NA2 `SLPS_258.37` save-record payload and its
  resident save lifecycle: physical files and descriptors, record boundaries,
  validation and checksum behavior, serialization and copy paths, fresh-profile
  initialization, slot/backup relationships, and fields whose meanings could be
  recovered without guessing.
- **Exploration depth:**
  - Exhaustive within the direct resident paths inspected: the save task and
    worker (`FUN_001e1c60`, `FUN_001e2140`); indexed record and descriptor I/O
    (`FUN_001c19e0`, `FUN_001c1e60`, `FUN_001c1b20`, `FUN_001c1fa0`);
    descriptor initialization/validation, save-set creation, repair, and error
    classification (`FUN_001e1ef0`, `FUN_001e1f50`, `FUN_001c17c0`,
    `FUN_001c2e60`, `FUN_001c3670`); icon creation/regeneration
    (`FUN_001c1c50`, `FUN_001c2680`); open/read/write/flush/close wrappers and
    their empty error hook (`FUN_001c2870..FUN_001c2b70`); all three structured
    serializers and the manual tail copy; and the snapshot/compare helpers
    (`FUN_001f7890`, `FUN_001f7920`). Direct references to the live record
    header and the `0x2400` record-size literal were audited, giving byte
    coverage of the complete record `0x0000..0x23FF`, its seven structured-copy
    omissions, the four-entry descriptor table and every native path involving
    `data01` through `data04`.
  - Bounded static coverage: the fresh-profile path
    (`FUN_001f4360` -> `FUN_001f47d0`), settings and controller-map
    synchronization, currency, availability/status and ability-bit accessors,
    Survival-table initialization and result writers, and the typed
    secondary-block accessors, with their fixed data tables. The secondary
    block was partitioned across `0x0DFC..0x21F5`; the aligned
    `0x21F8..0x2393` regions and the `0x2394..0x23FF` tail were bounded but
    not semantically decoded. BTL's six byte-bank getter/setter call pairs and
    five-entry group-counter mapping were inspected, and BTL/ETC were searched
    for direct calls to the secondary-bank wrappers and accessors, raw
    character-status reader, `+0x0DF4` wrappers and snapshot helpers.
  - The card submission/completion family was followed through its indirect
    callbacks and request-packet release; embedded `mcserv`/`mcman`
    instructions were traced for descriptor-slot invalidation, flush cleanup,
    close and teardown, and directory-entry enumeration order. The cached
    directory comparator was decoded completely.
  - All four snapshot owners were traced through entry and normal exit, with
    the Options comparison and save-dialog No path.
  - One historical local PS2 memory-card image was parsed read-only. It
    corroborated the checksum formula, three-primary-plus-rolling-backup
    model, header/settings values, timestamp behavior, and nonzero bytes in
    structured-copy gaps; it is a single sample, not a controlled runtime test.
- **Confirmed coverage:** the three visible slots and shared `data04` rolling
  backup; descriptor, checksum, serialization, scan, repair, and partial-write
  contracts; fresh defaults and settings synchronization; the fact that
  difficulty is not stored in this record; recoverable currency, availability,
  ability-bit, progression-ordinal, controller-map, and Survival ranking
  fields; secondary byte-counter update and clamp rules; typed but
  semantically unknown secondary banks; exact native icon-file lengths;
  file-error flattening, missing EE close after failed transfers, and the lower
  manager's distinct reclamation branches; directory-entry storage order and
  short/error-query buffer residue; the timestamp-triggered reconstruction of
  an existing descriptor; and Options' comparison with its entry snapshot and
  lack of rollback when its save is declined.
- **Unresolved or untested:** the semantic meaning of header `+0x0000`,
  descriptor class values 1 through 4, character-status bit 1, most individual
  elements in the secondary banks, the `+0x0DF4` flag word and `+0x0DF8`
  scalar, and all opaque aligned/tail regions. Indirect calls and overlay
  consumers are not exhaustively recoverable from resident direct references.
  Actual early-failure/card-probe conditions and eventual teardown after an EE
  submission failure remain unestablished. The comparator's assumed filenames
  at fixed directory indices are not guaranteed on arbitrary cards; it does
  not verify them or compare month/year.
- **Deliberate exclusions and overlap:** Adventure-mode consumers are
  excluded; scalar-field branches that reach an excluded component are not
  interpreted. Startup save UI workflow belongs to
  [Startup sequence](startup.md), content-availability propagation and its
  overlay consumers to
  [Content availability and state ownership](content_availability.md), and
  Survival controller modes, courses, ranking display and the row-1 producer
  search to [Survival](../gameplay/survival.md); this document records only
  the save-format facts needed to define those interfaces. Disc transport,
  module-loading mechanics, and icon-source transport belong to
  [Runtime file services](files/runtime_services.md) and
  [Startup sequence](startup.md); only the embedded card-service instructions
  needed for save ownership and directory ordering are interpreted here.
- **Evidence limitations:** no controlled corruption, allocation-failure,
  short-I/O, power-loss/partial-write, or repair execution was performed, so
  those behaviors are static path conclusions rather than runtime
  fault-injection results. Preserved function boundaries and indexed
  cross-references omit some direct BTL calls; those counter paths were
  corroborated with instruction bytes. Embedded card modules have no separate
  preserved function analysis; their instruction traces use module-relative
  addresses.

## Evidence, identity, and terminology

Static analysis uses the clean resident ELF, BTL and ETC overlays, the embedded
card-service modules in `MODULES.BIN`, and conventions in
[Retail game file identities](files/file_identities.md#address-conventions).

Unless stated otherwise, offsets are absolute offsets from the start of one
`0x2400`-byte record. Function names are the preserved analysis/export names.
Resident addresses are live EE virtual addresses. BTL symbols use analysis
addresses; an explicit export/live pair lists the analysis address first and
the live address second. Statements called
**observed** are direct code or byte observations. Statements called
**inferences** are interpretations supported by multiple observations. Shapes
such as an array length or aligned copy are not treated as field semantics.

A read-only parse of one historical local card image corroborates the static
contracts but is not evidence of current
runtime state. Its relevant bytes are recorded in
[Historical-card corroboration](#historical-card-corroboration).

The related resident availability readers and their overlay consumers are
documented in [Content availability and state ownership](content_availability.md).
The startup UI and 30 Hz play-time presentation are documented in
[Startup sequence](startup.md).

## On-card files and visible-slot model

The native save directory is `BISLPS-25837NARUTO5`. Its expected-entry table at
`0x003FBB20` names:

```text
icon00.icn
data01
data02
data03
data04
BISLPS-25837NARUTO5
icon.sys
```

`data01` through `data04` are each exactly `0x2400` bytes. The file whose name
matches the directory is a `0x40`-byte descriptor table containing four
`0x10`-byte descriptors. Indexed record I/O in `FUN_001c19e0` (`0x001C19E0`)
and `FUN_001c1e60` (`0x001C1E60`) is generic enough to name `data01` through
`data13`, but every recovered NA2 create, scan, save, repair, and UI path uses
only indices 0 through 3. The generic bound is not evidence of thirteen game
slots.

The remaining file-size contracts come directly from the native writers:

| File | Written size | Observed source |
| --- | ---: | --- |
| `icon00.icn` | `0xE920` (59,680) | Source offset 0 of disc resource `icon.bin` |
| `icon.sys` | `0x3C4` (964) | Regenerated in card context `+0x48..+0x40B` |
| `BISLPS-25837NARUTO5` | `0x40` (64) | Four raw descriptors |
| Each `data01..data04` | `0x2400` (9,216) | Raw record buffer |

Icon creator `FUN_001c1c50` uses the offset/length pair `0, 0xE920` at
`0x00602B78..0x00602B7F`. It allocates with `0x40` alignment and rounds its
disc read to `0xF000`, but passes the unrounded `0xE920` count to the card
writer. The complete disc resource therefore includes bytes not written to
`icon00.icn`; its identity is owned by
[Retail game file identities](files/file_identities.md#na2-supporting-files).

`FUN_001c2680` clears all `0x3C4` bytes before rebuilding `icon.sys` from the
fixed `PS2D` header, title, settings, and icon tables. All three icon filename
fields (output offsets `0x104`, `0x144`, and `0x184`) receive `icon00.icn`. The
descriptor writer calls this generator after successfully closing the
descriptor file. No saved profile field is copied into `icon.sys`, and no
payload checksum is stored there. The seven regular files require 97 rounded
1 KiB blocks; adding the directory-overhead formula for nine entries gives
103, matching context `+0x434`'s native expected total. That arithmetic assumes
the expected seven files plus the two directory entries; it is not a measured
allocation report for an arbitrary card.

The `dataNN` file is the raw little-endian record itself. There is no outer
record header, compression, encryption, or container layer between file offset
zero and record offset zero; the worker reads and writes exactly `0x2400`
bytes.

The UI exposes exactly three primary slots:

- `FUN_001e5b60` (`0x001E5B60`) maps UI rows only to descriptors 0, 1, and 2;
- `FUN_001e6370` (`0x001E6370`) renders three rows;
- `FUN_001e69b0` (`0x001E69B0`) wraps selection over 0 through 2;
- `FUN_001e59b0` (`0x001E59B0`) counts only those three descriptors.

On every successful save, the same serialized buffer is written first to the
selected `data01`/`data02`/`data03` and then to `data04`. The selected
descriptor and descriptor 3 receive the same occupied flag and checksum. The
worker samples the still-live play-time field separately for each row, and each
file receives its own directory timestamp. It updates fields independently
rather than copying the entire selected descriptor: each row's existing class
byte remains in place, and the timestamps can differ. There is no source-slot
or provenance field in descriptor 3.

**High-confidence inference:** `data04` is one UI-hidden rolling copy of the most
recently saved visible slot. It is neither a fourth visible slot nor one backup
per primary. Exact `data01 == data04` bytes in the inspected historical card
independently corroborate this interpretation.

## Descriptor table

Each descriptor has this observed layout. Multi-byte values are little-endian.

| Descriptor offset | Size | Observed role |
| ---: | ---: | --- |
| `0x00` | 1 | Occupied flag, required to be exactly 0 or 1 |
| `0x01` | 1 | Signed class value; an occupied row accepts 0 through 4 |
| `0x02` | 2 | Record checksum |
| `0x04` | 4 | Displayed play-time sample |
| `0x08` | 1 | Reserved timestamp byte |
| `0x09` | 1 | Seconds |
| `0x0A` | 1 | Minutes |
| `0x0B` | 1 | Hours |
| `0x0C` | 1 | Day |
| `0x0D` | 1 | Month |
| `0x0E` | 2 | Year |

`FUN_001e1ef0` (`0x001E1EF0`) initializes four descriptors with occupied,
class, checksum, and time equal to zero and timestamp bytes `+0x09..+0x0F`
equal to `0xFF`. It does not initialize reserved byte `+0x08`.

The worker's `0x60`-byte allocation is not guaranteed to be cleared before
that initializer. Consequently an empty row's reserved byte can retain heap or
previous-row state and is included when the raw `0x40` table is written.
Neither structural validation nor the slot renderer consumes it. The
historical table happens to contain zero in all four reserved bytes, but that
single image is not a format invariant.

Timestamp refresher `FUN_001c2c80` has a related malformed-list edge. It
searches only the four directory entries cached at `0x0061F760`; if no matching
`dataNN` name is found, it branches directly to the descriptor writes without
initializing its four timestamp stack halfwords. Normal save calls it only
after both record writes and a successful four-entry directory query, so the
name should ordinarily be present. The no-match behavior is nevertheless an
observed uninitialized-timestamp path; it was not forced at runtime.

`FUN_001e1f50` (`0x001E1F50`) performs only structural validation:

- occupied must be 0 or 1;
- an empty row requires class, checksum, and play time all to be zero;
- an occupied row requires signed class 0 through 4 and signed play time from
  zero through `0x066FF2E2` inclusive.

`0x066FF2E2` is the 30 Hz representation of 999:59:59. The validator does not
validate either checksum against a record and does not validate timestamp
bytes. The table has no separate magic, version, aggregate checksum, or trailer;
the four raw rows are the complete `0x40`-byte file.

No other direct reader or writer of descriptor class byte `+0x01` was found in
the clean resident export. Native initialization and descriptor reconstruction
write zero, normal save preserves the existing byte, and the slot renderer
does not consume it. Values 1 through 4 are therefore structurally accepted
but have no recovered resident meaning.

The scan entry `FUN_001e1da0` (`0x001E1DA0`) resets descriptors, then requests
worker operation 3. `FUN_001e2140` reads the full table through
`FUN_001c1fa0` (`0x001C1FA0`) and copies all four rows only if
`FUN_001e1f50` accepts them. A structurally invalid table is nevertheless
reported as a successful scan result while the reset/empty rows remain. Scan
does not open the payload files or recompute record checksums, so a corrupted
record can still appear occupied until it is loaded.

Validation and copy are all-or-nothing across all four rows. A structural
error confined to UI-hidden descriptor 3 therefore rejects the complete table:
otherwise valid descriptors 0 through 2 are not copied and all visible slots
remain reset/empty in memory.

Repair initially classifies a nonzero descriptor file as present, but its
separate cached-timestamp test can force descriptor reconstruction even when
that file exists. If that test returns 1, an existing structurally invalid
`0x40`-byte table is not rebuilt from `data01..data04`: normal scan silently
retains its reset/empty rows. Intact payloads can therefore disappear from the
native slot UI without automatic reconstruction. The exact timestamp test and
its limitations are described under
[Card-error ownership and cached timestamp classification](#card-error-ownership-and-cached-timestamp-classification).

## Record layout

### Header, settings, and resident availability state

| Record range | Size/count | Observed contract |
| --- | ---: | --- |
| `0x0000..0x0001` | 2 | Unknown header/discriminator; fresh value 3 |
| `0x0002..0x0003` | 2 | Embedded additive checksum |
| `0x0004..0x0007` | 4 | Play time in 30 Hz ticks |
| `0x0008..0x0009` | 2 | Signed horizontal display offset |
| `0x000A..0x000B` | 2 | Signed vertical display offset |
| `0x000C..0x000D` | 2 | Audio volume, range observed up to `0x0100` |
| `0x000E..0x000F` | 2 | Audio-output mode; high-confidence mapping 0 mono, 1 stereo |
| `0x0010` | 1 | Vibration-enable mask; bits 0 and 1 are controller ports 1 and 2 |
| `0x0011` | 1 | Omitted by structured copy |
| `0x0012..0x0021` | 8 x `u16` | Controller-port-1 button mapping |
| `0x0022..0x0031` | 8 x `u16` | Controller-port-2 button mapping |
| `0x0032..0x0033` | 2 | Omitted by structured copy |
| `0x0034..0x0037` | 4 | Ryo currency counter; maximum 9,999,999 |
| `0x0038..0x0907` | 94 x `0x18` | Per-character 192-bit jutsu/ability availability records |
| `0x0908..0x0965` | 94 bytes | Per-character status bytes; bit 0 is roster availability |
| `0x0966..0x0967` | 2 | Omitted by structured copy |
| `0x0968..0x096F` | 64 bits | Secondary availability bitset |
| `0x0970..0x098F` | 32 bytes | Small availability table |
| `0x0990..0x09EC` | 93 bytes | Grouped availability 0: Figures/Dolls |
| `0x09ED..0x0A15` | 41 bytes | Grouped availability 1: Music |
| `0x0A16..0x0AB0` | 155 bytes | Grouped availability 2: Voice |
| `0x0AB1..0x0B58` | 168 bytes | Grouped availability 3: Skills/Ultimate Jutsu |
| `0x0B59..0x0B5F` | 7 bytes | Grouped availability 4: Movies |
| `0x0B60..0x0B6B` | 12 bytes | Grouped availability 5: Dioramas |
| `0x0B6C..0x0DC3` | 25 x 3 x 8 | Survival records: rows of three `{s32 character_id, s32 cumulative_seconds}` pairs |
| `0x0DC4..0x0DF3` | 2 x 3 x 8 | Survival records: rows of three `{s32 character_id, s32 completed_wins}` pairs |
| `0x0DF4..0x0DF7` | 4 | Bitset word; reset explicitly clears bit 0 |
| `0x0DF8..0x0DFB` | 4 | Scalar; reset to zero |

The role of `0x0034` is observed through getter/setter
`FUN_001f6f60`/`FUN_001f6f00` (`0x001F6F60`/`0x001F6F00`): writes are capped
at 9,999,999, a debug path grants 100,000, reward paths add to it, and UI paths
format it. `FUN_001fb3e0` formats the getter result with the clean resident
Shift-JIS string at `0x00406680`, `%s<ruby両|りょう>`, which directly
identifies the unit as ryo (`両`).

The cap is a setter-path upper bound, not record validation.
`FUN_001f6f00` has no lower clamp, and normal load copies the stored word
without calling the setter. A checksum-valid edited file can therefore load a
value outside the native `0..9,999,999` range until some later writer replaces
or normalizes it.

The 94 character records are addressed through
`FUN_001f7180`/`FUN_001f7210`/`FUN_001f72d0` and the bit-record functions
`FUN_001ff670`/`FUN_001ff760`/`FUN_001ff7c0`. The 94 status bytes are accessed
through `FUN_001e3730`/`FUN_001e3740` and manager wrappers
`FUN_001f54c0`/`FUN_001f5500`. When a previously unavailable target is
unlocked, `FUN_001f5500` sets its bit 0 and calls `FUN_001f5640` to set its bit
1. If requested, it also resolves a linked form through `FUN_001f7c80` and
sets only that linked ID's bit 0. No direct clean-resident reader of status bit
1 was found, so its meaning is not assigned; only bit 0 is established as
roster availability. `FUN_001f5610` clears the complete status byte. Full BTL
and ETC byte searches additionally find no direct `jal` to raw status reader
`0x001E3740`; the overlay audit therefore supplies no bit-1 consumer. It does
not exclude inlined reads or indirect calls.

The six grouped-table labels are established by the native ETC content record
tables and their reader/writer call sites, not inferred from the byte counts.
Their established native byte lifecycle is 0 default/unowned, 1 offered or
announced but unowned, 2 owned and new/unviewed, and 3 owned and viewed/stable.
Individual consumers do not all use the same threshold, so arbitrary nonzero
values are not a safe generic "unlocked" encoding. The supporting overlay
consumers and category-specific behavior are documented in
[Content availability and state ownership](content_availability.md).

`FUN_0038e6e0` and `FUN_0038e780` mirror 22 fixed pairs of entries between the
small table at `0x0970` and the byte bank at `0x2100`, using the pair table at
`0x005D53E0`. `FUN_00373830` resolves the pair-table IDs through the 22-entry
lookup at `0x005B03F0`. After that resolution, the mapping is a permutation of
all small-table indices 0 through 21 onto bank indices:

```text
small index:  0, 1, 2, 3, 4, 5, 6, 7, 8, 9,10,11,12,13,14,15,16,17,18,19,20,21
bank index:   3,21, 7, 8, 9,10,11,12,13,14,15,16,17,18,20, 0, 1, 2, 4, 5, 6,19
```

The two functions copy bytes in opposite directions. This proves the exact
relationship between those 22 entries, not their wider semantics; bank indices
22 through 245 are not touched by this mirror.

### Secondary block and opaque tail

Let `S = record + 0x0DFC`. `FUN_001e2c90` and the independent bulk-copy pair
`FUN_0038f2a0`/`FUN_0038f540` agree on the following boundaries:

| Record range | Relative to `S` | Size/count | Observed storage shape |
| --- | ---: | ---: | --- |
| `0x0DFC..0x114D` | `+0x0000` | 850 bytes | Byte bank via `FUN_001e3c60`/`FUN_001e3c70` |
| `0x114E..0x17F1` | `+0x0352` | 850 x `u16` | Halfword bank via `FUN_001e3c80`/`FUN_001e3ca0` |
| `0x17F2..0x1B43` | `+0x09F6` | 850 bytes | Byte bank via `FUN_001e3cc0`/`FUN_001e3cd0` |
| `0x1B44..0x1C5B` | `+0x0D48` | 70 x `u32` | Word bank via `FUN_001e3ce0`/`FUN_001e3d00` |
| `0x1C5C..0x20FF` | `+0x0E60` | 297 x `u32` | Word bank via `FUN_001e3d20`/`FUN_001e3d40` |
| `0x2100..0x21F5` | `+0x1304` | 246 bytes | Byte bank via `FUN_001e3d60`/`FUN_001e3d70` |
| `0x21F6..0x21F7` | `+0x13FA` | 2 | Omitted by structured copy |
| `0x21F8..0x2213` | `+0x13FC` | `0x1C` | Opaque seven-word aligned region |
| `0x2214..0x2393` | `+0x1418` | `0x180` | Opaque 96-word aligned region |
| `0x2394..0x23FF` | outside `S` copy | `0x6C` | Opaque tail copied manually as 54 two-byte iterations |

The accessors do not bounds-check indices. The compiler's use of
`lwc1`/`swc1` to copy `0x21F8..0x2213` is not evidence that those words are
floating-point fields. Likewise, the two-word loop for `0x2214..0x2393` does
not prove a record structure.

Manager wrappers `FUN_001f75d0` through `FUN_001f7720`, covering the first
four typed banks, have no recovered direct call sites elsewhere in the clean
resident C export. Full BTL and ETC byte searches find no direct `jal` to any
of those eight wrappers or their eight low-level accessor entries
`0x001E3C60`, `0x001E3C70`, `0x001E3C80`, `0x001E3CA0`, `0x001E3CC0`,
`0x001E3CD0`, `0x001E3CE0`, and `0x001E3D00`. This is a bounded negative
result for explicit calls, not a conclusion that the banks are unused; inlined
access and indirect calls remain outside that inventory.

No dedicated clean-resident semantic reader or writer of the final
`0x2394..0x23FF` tail was recovered; its only established resident handling is
whole-record comparison and the normal save/load copy loop. The earlier opaque
ranges at `0x21F8..0x2393` are additionally moved by the independent bulk-copy
pair, but that copy alone does not name them.

The first word in the 297-word bank, absolute offset `0x1C5C`, is a
high-confidence main-progression ordinal. `FUN_001f7780` exposes it;
`FUN_001f7fb0` tests it against `0x65`; `FUN_001ffb30` selects assets at
thresholds `0x3E` and `0x66`; and several presentation objects range-test it.
This evidence does not justify assigning individual story chapters. Index
`0x6A` in the same bank is independently used as a Boolean gate for an extra
menu entry. Other entries remain semantically unresolved.

The bulk snapshot/restore pair copies the secondary block through
`0x2393`, including the two opaque aligned ranges, but excludes the final
`0x6C`-byte tail. Its overlay cross-reference is Adventure-owned; Adventure
logic was not inspected. No resident semantic reader for
`0x21F8..0x23FF` was recovered.

### Battle-result counters in the byte bank at `0x2100`

Resident `FUN_001f77b0`/`FUN_001f77e0` write/read byte-bank index `i` at
record `+0x2100 + i`. The bank contains counters as well as the 22 mirrored
entries described above. The BTL result processor begins at export/live
`0x006EC290/0x006EC2D0`. It selects a
[Survival course record](../gameplay/survival.md#course-table) using its
object's word `+0x48`, then processes its numeric result-kind argument as follows:

| Result kind | Observed byte-bank update |
| ---: | --- |
| 0 | Unless the ranking/result word `object + 0x0C` is `-2`, add the selected course record's signed byte `+0x0C` to the counter ID in its halfword `+0x0A` |
| 4 | Apply the same course-selected signed increment without that `-2` gate |
| 5 | Increment the group counter selected by the course record's byte `+0x01` |
| 6 | Increment that group counter and aggregate index `0x6C` |

Every listed writer clamps its result to `0..99`. This is a writer contract,
not validation of loaded bank bytes. The five group-to-counter IDs come from
the first halfword of each eight-byte row at BTL live
`0x008C25F0..0x008C2617` (complete-file offsets `0x20E6F0..0x20E717`):

```text
course group:   0,    1,    2,    3,    4
bank index:    0x68, 0x69, 0x6A, 0x6B, 0x65
record offset: 2168, 2169, 216A, 216B, 2165 (hex)
aggregate:     bank 0x6C, record 0x216C
```

The processor calls the small-table-to-bank mirror `FUN_0038e6e0` before its
updates and the reverse mirror `FUN_0038e780` afterward. This keeps changes to
counter IDs in the mirrored subset visible through both saved representations.
Two additional result branches at export/live `0x006EB9E4/0x006EBA24` and
`0x006ED974/0x006ED9B4` increment an indirectly selected byte-bank index by one
and cap it at 99. Both select the index through an object callback and skip
`-1`. Their content labels
are not established by these numeric update paths.

The byte-bank index `0x6A` here is absolute record offset `0x216A`; it is a
different field from word-bank index `0x6A` at `0x1E04`.

## Checksum and normal load/save

The save-system task `FUN_001e1c60` calls the persistent worker
`FUN_001e2140` (`0x001E2140`) at `0x001E1C90`. The normal checksum is exactly:

```text
temporary[0x0002] = 0
temporary[0x0003] = 0
C = sum(temporary[0x0000..0x23FF]) modulo 65536
```

The assembly loop truncates after every byte addition, which is equivalent to
the final modulo shown above. There is no CRC, hash, salt, or per-section
checksum.

As a direct mathematical consequence, byte permutations and compensating byte
changes with the same total sum are undetectable, even without changing the
descriptor. The descriptor's 16-bit sum is the only integrity check, so any
record whose descriptor sum matches is accepted. This is accidental-corruption
detection, not an authenticity or strong-integrity mechanism.

### Load path

The worker reads exactly `0x2400` bytes with `FUN_001c1e60`, overwrites the
temporary record's checksum halfword with zero, computes `C`, and compares it
only with descriptor `[selected].checksum`. If they match, structured copy
moves the temporary into the live record.

Consequences are directly observed:

- the embedded checksum read from the record is destroyed before validation
  and is never compared independently;
- corruption confined to bytes `0x0002..0x0003` is ignored;
- successful load copies zero into live record `+0x0002`;
- record `+0x0000` is not validated on normal load. A value other than the
  fresh-profile constant 3 is accepted if the descriptor checksum matches.

Record play time `+0x0004` is not compared with descriptor play time and has no
separate range check. The descriptor's `0..0x066FF2E2` constraint therefore
protects only the UI/table sample, not the value copied into the live record.
The historical 32-to-34-tick drift is a native example of the two values being
different, although both remain in their ordinary range.

The only observed semantic test of record `+0x0000` is repair's
`== 0xFFFF` erased-file test. The only observed consumer of an on-record
checksum outside normal save/load is descriptor reconstruction, which copies
it without recomputing it. Thus the embedded checksum becomes indirectly
authoritative only if the descriptor table must be rebuilt.

### Save path and ordering

Save preflight operation 8 reads the selected descriptor's occupied byte and
reports status `0x1A` for empty or `0x1B` for occupied. `FUN_001e3120` maps the
confirmed choice to operation 9 or 10 respectively; both operations share one
implementation. The worker allocates an
uncleared `0x2400`-byte temporary through `FUN_00117700`, performs structured
copy from the live record, zeroes the temporary checksum, computes `C`, writes
`C` into the temporary, and writes that same buffer to the selected primary
and then to `data04` through `FUN_001c19e0`.

Only after both payload writes succeed does it update the selected descriptor
and descriptor 3, obtain timestamps through `FUN_001c2c80`, and write the
whole descriptor table through `FUN_001c1b20` (`0x001C1B20`). That helper also
rewrites `icon.sys` through `FUN_001c2680`: it opens, writes, and closes the
same-name `0x40`-byte descriptor file first, then performs the icon rewrite.
Descriptor class byte `+0x01` is not changed by this path.

The operation is not transactional at the game-file level: payloads are
written before descriptor/icon metadata, and there is no rollback if a later
write fails. Both payload writes are attempted even if the selected-primary
write reports failure. If either payload write, the following directory query,
or the metadata helper fails, the worker reports failure without restoring any
file already changed. Depending on the failing step, one or both payloads can
contain the new record while the on-card descriptor table is still old. If the
final `icon.sys` rewrite fails, both payloads and the descriptor table are
already new even though the save operation reports failure. Normal load has no
`data04` checksum fallback for any of these states.

Ignoring the additional possibility of a lower-layer partial transfer, the
reported-outcome cases are:

| Selected write | `data04` write | Later step | Possible persistent state |
| --- | --- | --- | --- |
| success | failure | metadata skipped | New primary payload with old selected descriptor; old/failed backup |
| failure | success | metadata skipped | Old/failed primary; new `data04` payload with old descriptor 3 |
| success | success | directory/table failure | Both new payloads with old or partially written descriptor metadata |
| success | success | descriptor succeeds, icon fails | Both payloads and descriptor table new, `icon.sys` old/failed, operation reported failed |

The second case can undermine later recovery: missing-primary repair copies the
new `data04` bytes together with old descriptor 3 and does not recompute their
checksum, so the restored primary can immediately fail normal-load validation.

The serialized record receives play time when it is cloned. Descriptor play
time is sampled from the still-live record after the payload writes, once for
the selected row and again for descriptor 3 after the first timestamp refresh.
Because
`FUN_001f7810` (`0x001F7810`) continues incrementing live `+0x0004` while the
manager exists and manager flag-byte bit 0 is set, the two values are not
guaranteed to match the serialized value or each other. Each call adds one tick
and saturates at `0x066FF2E2`. The historical card shows descriptor values 32
through 34 ticks later than their records; its selected/backup pair happens to
have equal descriptor time despite the independent loads.

## Structured serialization and omitted bytes

`FUN_001e2140` serializes/deserializes the record in four pieces:

| Piece | Function or loop | Record span | Load call/loop | Save call/loop |
| --- | --- | --- | ---: | ---: |
| Header | `FUN_001e30f0` (`0x001E30F0`) | `0x0000..0x0007` | `0x001E26C8` | `0x001E2844` |
| Main | `FUN_001e2e20` (`0x001E2E20`) | nominally `0x0008..0x0DFB` | `0x001E26D8` | `0x001E2854` |
| Secondary | `FUN_001e2c90` (`0x001E2C90`) | nominally `0x0DFC..0x2393` | `0x001E26E8` | `0x001E2864` |
| Tail | worker loop | `0x2394..0x23FF` | `LAB_001E26FC` | `LAB_001E2878` |

The nominal spans cover the full record, but fieldwise copy transfers only
`0x23F9` of `0x2400` bytes. Exactly seven absolute bytes are omitted in both
directions:

```text
0x0011
0x0032..0x0033
0x0966..0x0967
0x21F6..0x21F7
```

This omission has asymmetric side effects:

- load validates all `0x2400` file bytes, including the seven gaps, but leaves
  the corresponding live bytes unchanged;
- save checksums and writes all `0x2400` temporary bytes, but the non-clearing
  allocator and structured copy never initialize the seven gaps.

Whole-record construction/reset clears the live gaps to zero, normal load
leaves them untouched, and no dedicated clean-resident writer for them was
recovered. Their live values therefore remain zero in the established normal
initialization/load paths even when their on-card counterparts are nonzero.

**High-confidence inference:** the gaps are alignment/padding and their saved
values are stale allocator contents, not live profile fields. The historical
card contains varying nonzero gap bytes, strongly corroborating this inference.
In practical terms, each native save can persist up to seven bytes of unrelated
prior heap state in both the selected record and `data04`; the particular
source allocation cannot be reconstructed from the card bytes alone.
The positions match the alignment transitions exactly: `0x0011` precedes the
halfword maps at `0x0012`, `0x0032..0x0033` precedes the word at `0x0034`,
`0x0966..0x0967` precedes the aligned 64-bit availability field at `0x0968`,
and `0x21F6..0x21F7` precedes the word-aligned region at `0x21F8`.

Because one temporary buffer is reused for both writes in a save operation,
the selected primary and `data04` receive identical gap bytes and checksum.
Across separate saves, however, two semantically identical live records can
produce byte-different files and checksums if the allocator supplies different
residue in a gap. `FUN_001f7920` cannot detect that variation: it compares live
records, while the varying bytes arise later in the serialization temporary.

## Fresh-profile initialization

The raw record constructor `FUN_001e34f0` (`0x001E34F0`) calls
`FUN_001e79d0(record + 8)`, constructs 94 `0x18`-byte objects through
`FUN_001e35c0` and `FUN_001ff670`, calls `FUN_001e7b90`, and then calls
`FUN_001e3690` (`0x001E3690`) to zero all `0x2400` bytes. Consequently, any
earlier subconstructor defaults do not survive.

Actual new/reset profile initialization is `FUN_001f47d0` (`0x001F47D0`),
called by `FUN_001f4360` at `0x001F43B4`. Startup reaches it through
`FUN_001e9980 -> FUN_001f4200 -> FUN_001f4360`. It clears the record and then
applies these observed defaults:

| Field | Fresh/reset value |
| --- | --- |
| Header `+0x0000` | `u16 3`; meaning unproven |
| Embedded checksum `+0x0002` | 0 |
| Play time `+0x0004` | 0 |
| Display X/Y `+0x0008/+0x000A` | Cold-start values 0/0 |
| Volume `+0x000C` | Cold-start value `0x0100` |
| Audio mode `+0x000E` | Cold-start value 1 |
| Vibration mask `+0x0010` | Cold-start value 3 |
| Resource counter `+0x0034` | 0 |
| Secondary bitset, small table, and grouped availability banks | 0 |
| Bitset `+0x0DF4` | Bit 0 explicitly cleared; word remains zero |
| Scalar `+0x0DF8` | 0 |
| Secondary block and opaque tail | 0 before later initialization/runtime writes |

The settings reset can copy the current display, audio, and vibration globals,
so a later reinitialization need not reproduce cold-start values. After load,
`FUN_001e9eb0` applies saved X/Y through `FUN_001076c0`, audio through
`FUN_001e36c0 -> FUN_001d7a90/FUN_001d7c00`, and controller maps through
`FUN_001f4030`.

The display-position editor `FUN_0038a8b0` constrains values it creates to
horizontal `-48..+48` in steps of 3 and vertical `-16..+16` in steps of 1.
These are UI-produced ranges, not load validation: normal record load accepts
any checksum-valid `s16` pair and passes it onward.

The audio options controller `FUN_00389550` establishes the encoding without
requiring the rendered Japanese labels: option choice 0 calls `FUN_001d7c00(1)`
and stores save value 1, while choice 1 calls `FUN_001d7c00(0)` and stores save
value 0. Reset selects choice 0, volume `0x0100`, and therefore saved audio-mode
value 1. The clean asset-pointer table binds choice 0 to
`ANM_on_speaker2` and choice 1 to `ANM_on_speaker1`. This strongly supports
interpreting saved 1 as stereo/two-speaker output and saved 0 as mono/one-
speaker output; those semantic names are inferred from the assets rather than
recovered enum symbols. `FUN_001d7c00` rejects inputs other than 0 and 1.

The same options controller keeps UI-produced volume in `0..0x0100` and moves
it in steps of 2. `FUN_001d7a90` itself does not clamp a loaded halfword before
scaling it. More generally, the normal load path performs no per-setting
sanity checks after the whole-record checksum succeeds. Vibration predicates
consume only mask bits 0 and 1; other stored bits are preserved but have no
recovered effect in that predicate.

The vibration value also has an in-process cache at `0x00607608`.
`FUN_005d82f0` initializes it at cold process start from byte `0x005C06B0`,
which directly follows the default binding table, as `b | (b << 1)`; the clean
byte is `1`, giving mask 3. `FUN_001f47d0`
copies that cached byte into a fresh record, `FUN_001f4120` changes both the
live record and cache (passing a port below 1 resets the mask to 3, but its only
caller, Controls confirmation at `0x00387FE4`, passes port 1 or 2), and
manager teardown `FUN_001f4680` copies the live `+0x0010` byte back to the
cache. Consequently, 3 is the cold-start default, while a later new/reset
profile in the same process can inherit a previously active profile's
vibration mask. `FUN_001f41a0` suppresses vibration entirely when no manager
exists or its state is 8 or 9; otherwise it tests the requested mask against
the saved byte.

Difficulty is an important non-field. The Options root obtains it through
`FUN_001f6d50(manager, 0x0B)` and commits it through
`FUN_001f6d30(manager, 0x0B, value)`, but those functions access byte
`manager + 0x0A13`, not the manager's record pointer. That byte is member 7 of
the third 12-byte runtime battle-options object at `manager + 0x0A0C`;
`FUN_001e7a80` initializes it to 2 (the observed Normal default). On leaving
Options, `FUN_0038b710` writes this manager-local byte and only then calls
`FUN_001f7920`, whose comparison is confined to record offsets
`0x0008..0x23FF`. A difficulty-only change therefore does not make the save
payload dirty, and no difficulty value is serialized by the native record
path. The mirror setter has exactly two callers: the general settings setter at
live `0x001F63EC` and the Options controller at live `0x0038B81C`. The byte can
remain active for the manager's lifetime, but manager
construction resets it independently of an on-card load.

`FUN_001f45b0` copies two default controller maps into `0x0012..0x0031`.
`DAT_005C06A0` contains these eight `u16` masks for each port:

```text
0010 0020 0040 0080 0004 0008 0001 0002
```

The array is ordered by logical action, while each stored halfword identifies
the physical control currently assigned to that action:

| Saved index | Logical action |
| ---: | --- |
| 0 | Ultimate Jutsu Prep |
| 1 | Attack |
| 2 | Jump |
| 3 | Item Use |
| 4 | Item Select |
| 5 | Linked Attack |
| 6 | Guard slot 1 |
| 7 | Guard slot 2 |

| Physical control | Stored mask |
| --- | ---: |
| Circle | `0x0020` |
| Triangle | `0x0010` |
| Square | `0x0080` |
| Cross | `0x0040` |
| L1 | `0x0004` |
| R1 | `0x0008` |
| L2 | `0x0001` |
| R2 | `0x0002` |

This mapping is observed jointly in `FUN_00387950`, the mask table at
`0x005D5230`, the control-settings screen, and the historical record bytes.
The fixed array above therefore decodes as Triangle/Circle/Cross/Square for
the first four logical slots, L1 for Item Select, R1 for Linked Attack, and
L2/R2 for the two Guard slots.

This map copy is not inside `FUN_001f47d0`: the whole-record clear initially
leaves those 32 bytes zero. On first manager creation, `FUN_001e9980` calls
`FUN_001f4200 -> FUN_001f4360 -> FUN_001f47d0`. Before that new manager is
published globally, `FUN_001f4360` calls `FUN_001f3dc0(-1, 0)`, resetting all
global maps from `DAT_005C06A0`; its attempted global-to-save sync is then a
no-op because the manager global is still null. `FUN_001e9980` next publishes
the manager and immediately calls `FUN_001f45b0`, which copies the fixed
defaults at `0x006B2B20` and `0x006B2B30` into the two saved maps.
`FUN_001f3f40` is the later global-to-save sync; `FUN_001f4030` performs
save-to-global sync after load.

The native controller editor `FUN_00387950` treats each eight-halfword map as
a permutation of exactly these recognized masks, in its display-scan order:

```text
0020 0010 0080 0040 0004 0008 0001 0002
```

Its edit/swap logic preserves that permutation, and `FUN_00387e10` reconstructs
the saved action-order array on confirmation. Normal load does not validate
that each recognized mask occurs exactly once. If a checksum-valid edited map
contains missing, duplicate, or foreign values, `FUN_00387950` can leave one
or more editor selections at `-1`; the confirmation loop later uses those
selection values as indices into an eight-halfword stack array. This malformed-
map path was not exercised at runtime, so no stronger consequence is claimed.

The editor's shoulder selector `FUN_003881F0` cycles action indices `4..6`.
Its label renderer `FUN_003885B0` indexes the eight-pointer table at
`0x005B2590`; the first entry points to the Ultimate Jutsu Prep string.
On confirmation, `FUN_00387E10` uses each selected action index to fill the
eight-halfword save map. Its array size follows the eight native actions.

Character status reset zeroes all 94 bytes, then writes `0x03` for exactly 22
IDs from `DAT_005C06C0`:

```text
0x39..0x3D, 0x41..0x46, 0x49, 0x4E..0x57
```

For character `i`, jutsu/ability reset zeroes the associated 192-bit record,
then sets bits `2*i` and `2*i+1`; character `0x46` additionally receives bit
`0x34`.

Secondary-availability reset `FUN_001f56a0` examines one initializer byte at
`DAT_005C06D8`. That byte is the sentinel `0x24`, and the function deliberately
skips it, leaving the complete 64-bit field at `0x0968` clear.

`FUN_001f7390 -> FUN_001e7bf0` initializes the pair tables at
`0x0B6C..0x0DF3`, so a new profile is not wholly deterministic despite the
initial clear. In the first 25-by-three block, each character ID is an
independent RNG result modulo 94 rejected while fixed filter
`FUN_001f7aa0` says it is ineligible. `FUN_001f7bb0`, despite appearing in the
same rejection condition, returns zero. There is no duplicate avoidance or
saved-unlock lookup. The associated metrics are the row factor byte at
`0x005C0710` multiplied by slot constants 60, 75, and 90. The 25 row factors
are:

```text
2,3,3,3,3,3,2,3,3,3,3,3,4,5,5,3,3,5,5,5,5,5,5,5,5
```

The second two-by-three block uses the same independent random-ID process and
metrics 10, 8, and 5 in each row. Static initializer `FUN_005d82f0`
(`0x005D82F0`, initialization-table reference `0x005D9D18`) copies constants
at `0x005C0730`, `0x005C0734`, and `0x005C0738` into the metric scratch words;
`FUN_001e7bf0` refreshes the adjacent ID words and copies the three pairs into
both rows.

Reset therefore consumes at least 81 calls to `FUN_001801b0` for the 81
accepted IDs, plus one additional call for every rejected ID. The initializer
does not reseed the RNG. Advancing global RNG state is an observed side effect
of constructing/resetting these otherwise save-local rankings. Manager
construction runs this initializer before a selected on-card record is loaded,
so even an eventual successful load consumes the RNG calls and then overwrites
the freshly seeded rankings with saved values.

These pair tables are the Survival rankings. The first block holds 25 course
rows of cumulative-time records, filled by finite-course controller mode 5
in ascending order of whole elapsed seconds; the second block holds two rows
of completed-win records, filled by mode 4 in descending order, whose native
path uses only row 0. Both insertion functions take their row index verbatim
from the controller. Controller modes, the course table, ranking display,
Records navigation and the row-1 producer search are recorded in
[Survival](../gameplay/survival.md).

Accessors `FUN_001f73c0`/`FUN_001f7400` and
`FUN_001f7430`/`FUN_001f7470` perform no row or slot bounds checks. The fixed
initialization filter excludes IDs
`0, 8, 9, 0x14..0x15, 0x17..0x21, 0x2C..0x2D, 0x4A, 0x58`; it does not consult
saved unlock state.

### Bitset `0x0DF4` and scalar `0x0DF8`

For word `0x0DF4`, the only recovered direct wrapper read is
`FUN_001f7530(manager, 0)` inside menu-selection function `FUN_00384760`
(`0x00384760`). A nonzero bit 0 diverts selected item 0 to
`FUN_003849a0` instead of its normal transition. The only direct setter call in
the clean resident export is the reset clear through `FUN_001f74a0`; no
trustworthy name for the gate is assigned. BTL and ETC contain no direct
`jal` to its reset, setter, or getter wrappers `0x001F74A0`, `0x001F7500`,
and `0x001F7530`. Scalar `0x0DF8` has a resident reset-to-zero wrapper call
(`FUN_001f7560`) but no recovered resident direct caller of getter
`FUN_001f7590`; no semantic meaning is established within this document's
in-scope consumers.

Direct calls to the raw `+0x0DF4` accessor pair `0x001E3B30/0x001E3BE0` and
raw `+0x0DF8` pair `0x001E3C40/0x001E3C50` occur only in the four resident
manager wrappers; BTL and ETC have none. BTL also has no calls to the scalar
manager wrappers `0x001F7560/0x001F7590`. ETC's scalar-wrapper call sites lie
in a branch that reaches an excluded component. No semantic name for the
scalar or an ordinary battle/Records producer is established by those calls.
The no-match results apply to explicit calls, not all possible pointer
arithmetic or inlined accesses.

## Snapshot and change detection

`FUN_001f7890` (`0x001F7890`) lazily allocates a `0x2400`-byte snapshot and
raw-copies the complete live record into global `0x00607628`. It does not
refresh an existing snapshot. Paired `FUN_001f78e0` (`0x001F78E0`) releases
the allocation and clears the global pointer. Their four recovered entry/exit
call pairs are listed below.

`FUN_001f7920` (`0x001F7920`), called at `0x0038B824`, returns 1 only when the
manager exists, manager state `+0x0C` is 4 through 7, the snapshot exists, and
`FUN_0017a388(snapshot + 8, live + 8, 0x23F8)` reports a difference. The exact
comparison interval is therefore record `0x0008..0x23FF`: it excludes the
header/discriminator, checksum, and continuously advancing play time, while
including all seven structured-copy gaps.

Its sole caller is settings-menu controller `FUN_0038b710`. On menu exit, a
zero result follows the direct exit transition, while a nonzero result enters
the intermediate save-confirm transition. This establishes the function as
save-backed settings change/dirty detection; only the descriptive name is
inferred.

The main resident dispatcher `FUN_001e9980` establishes the snapshot owners
without relying on their menu names. While manager phase `+0x08` is 4, manager
substate `+0x0C` selects these four lifecycle controllers:

| Manager substate | Controller | Capture | Release |
| ---: | --- | ---: | ---: |
| 4 | `FUN_001ea9c0` | `0x001EAAA4` | `0x001EAB2C` |
| 5 | `FUN_001eacb0` | `0x001EADD4` | `0x001EAEF0` |
| 6 | `FUN_001eb120` | `0x001EB1E4` | `0x001EB314` |
| 7, Options | `FUN_001eb440` | `0x001EB4FC` | `0x001EB5D0` |

Each captures during entry and releases on its normal exit before returning
the manager substate to 1. The Options path creates `FUN_0038afb0`'s child
first, then captures, and eventually destroys that child before releasing the
snapshot. The gate in `FUN_001f7920` therefore covers exactly those four
substates, but this is not evidence that every owner calls change detection:
only Options has the recovered comparator call. BTL and ETC contain no
direct `jal` encodings to capture (`24DE070C`) or compare (`48DE070C`). This bound does not exclude indirect or
inlined consumers, and the other owners' gameplay is not interpreted here.

The snapshot supplies a byte-comparison baseline. Changes reversed to its
byte values before exit yield no
difference. Advancing play time alone cannot produce one. Conversely, any
changed byte in the compared interval can trigger the prompt, even outside the
named settings. Capture never refreshes an existing snapshot, and the normal
save path does not copy back into it. The next entry obtains a new baseline
only after the previous owner releases it.

Options save-confirm state 2 in `FUN_0038bbf0` constructs the shared Save/Load
parent and invokes `FUN_001e3f00(parent, 0)`. Any nonzero returned result
destroys that parent and advances Options to exit state 3. In the shared
controller `FUN_001e3f20`, the initial No choice returned by `FUN_001e70b0`
advances through states 10 and `0x0C` to parent result 2. Neither that branch,
the Options completion branch, nor snapshot release copies old snapshot bytes
into the live record or reapplies old settings. Options destruction
`FUN_0038b370` and its Controls/Audio/Display cleanup functions
`FUN_003874c0`, `FUN_00388e50`, and `FUN_0038a560` release UI resources without
writing saved settings. **Static conclusion:**
declining this save leaves the edited live settings active; it skips their
card write. That conclusion is limited to these inspected paths. The save
prompt does not itself prove a persistent dirty flag or a general rollback
contract for other controllers.

## Save/Load dialog text and confirmations

`FUN_001e3f00` calls visible controller `FUN_001e3f20` at `0x001E3F08`.
The controller's word at `+0x24` points to its UI object. The UI's `+0x40`
field is a text pointer, not an animation state: `FUN_001e5b20` obtains it
through the status lookup `FUN_001e34d0` and stores it there.

`FUN_001e5ba0` invokes `FUN_001e6060(ui, 4)`. When UI byte `+1` is set,
that renderer draws four consecutive NUL-terminated strings, advancing past
each terminator. The first line uses local X/Y `22/18`; subsequent lines add
30 to Y. It does not split one long string into lines.

`FUN_001e6ce0` draws and updates Yes/No at local Y `80`. UI word `+0x14`
selects Yes (`0`) or No (`1`). It returns `1` for Yes, `2` for No, `3` for
the back button, `0` while waiting, and `-1` while the panel is not ready.
It clears UI byte `+2`, avoiding duplicate choice handling by the later
renderer. `FUN_001e5dc0(ui, 0)` draws Next and returns `1` on acknowledgment.
These text and choice layouts were established from the clean resident code
and its fixed position records.

## Creation, repair, and negative results

### Card-error ownership and cached timestamp classification

The resident card-context wrappers and save worker retain different kinds of
results. `FUN_001c2870` opens a file and stores its returned handle in card
context `+0x44`. `FUN_001c2a30` reads, `FUN_001c2910` writes and flushes, and
`FUN_001c2ad0` closes; these helpers return only 0/1. Their failure calls to
`FUN_001c2e50` pass stage numbers and, on some branches, the lower-level result,
but that function is exactly `jr ra; nop` (bytes `0800E003 00000000` at
`0x001C2E50`). It neither records nor transforms the error. Its arguments are
therefore not a persistent native error log.

The lower submission functions for open (`0x00175AC0`), close (`0x00175C20`),
read (`0x00175E70`), write (`0x00175F88`), card info (`0x00176220`), and flush
(`0x00176920`) all use the same request semaphore at `0x003FAC5C` and pending
command word at `0x003FAC58`. Their observed immediate return values are:

| Return | Observed submission condition |
| ---: | --- |
| 0 | RPC submission succeeds; the pending command word is set |
| `-100` | Initialized-state word `0x00616064` is zero |
| `-200` | Polling the request semaphore returns a negative result |
| `-91` | The RPC submitter returns nonzero; the request semaphore is released |
| `-210`, open only | Path pointer is null or points to an empty string; the semaphore is released |

Pending command values are 2/3/5/6/1/10 respectively. These are queue-state
values, not saved fields or worker UI statuses. `FUN_00176100(0, 0, result)`
waits for the completion semaphore at `0x003FAC60`, clears the pending word,
copies the completed value from `0x00617600` into `result`, and releases the
request semaphore. When no command is pending it returns `-1` without writing
the result destination. Resident wait wrapper `FUN_001c2b70` forwards those
arguments but none of its inspected card-context callers checks that wait
return before using their result destination. This is an observed interface
limit; it does not establish that an ordinary successful submission can leave
the destination unwritten.

The indexed record and descriptor wrappers flatten open, transfer, flush, and
close failures into read result 6 or write result 7. A successful read whose
close fails is still result 6; a successful write/flush whose close fails is
still result 7. No byte-count or failure-stage detail reaches the worker from
these return values. The worker separately stores directory/card preflight
classification at `worker +0x58`; that field is not the most recent raw file-I/O
result. Normal record-read failure becomes status `0x14`/result class 2, and
record-write, directory-refresh, descriptor-write, or icon-rewrite failure
becomes status `0x19`/result class 2. These statuses alone cannot distinguish
which lower operation failed.

The read/write wrappers call close only after a successful transfer (and, for
writes, flush). A transfer/flush failure branches directly to the common
return without submitting close. The same pattern occurs in descriptor I/O.
Successful close resets context `+0x44` to `-1`; failed close does not. Thus
these paths have no observed close-on-failure cleanup, and a following open
can overwrite the stored handle. The lower service invalidates some failed
handles independently, as detailed below; the missing EE close alone cannot
establish that a particular error leaks one.

#### EE completion and teardown ownership

The bounded indirect completion path distinguishes an RPC request from the
card file descriptor carried inside it. Submitter `FUN_00161c28` stores the
callback at client `+0x1C`, its argument at `+0x20`, and the current `gp` at
`+0x18`. Completion dispatcher `FUN_001615a0` restores that `gp`, calls the
callback through `jalr` at `0x0016160C`, then calls `FUN_00161510` on the RPC
packet and clears client `+0x00`. The packet release only clears packet
`+0x18` and allocation bit 0 at `+0x10`. It does not issue a card close or
interpret the card result. This is request-packet reclamation, not reclamation
of the file handle stored in the request payload at `0x006160C0`.

Read uses callback `0x00175DC0`; write, flush, close, and directory enumeration
use `0x00175930`. The latter's complete instruction bytes at
`0x00175930..0x0017593F` are `4000023C 44770508 60AC448C 00000000`:
load completion semaphore `0x003FAC60` into `a0` and tail-call `iSignalSema`
at `0x0015DD10`. The read callback's bytes at `0x00175DC0..0x00175E6F`
copy the two optional edge fragments from the uncached response structure,
then tail-call the same signal routine. Neither callback tests the completed
result, maintains a list of open handles, or submits a close. Preserved
analysis has no function definition for these two callbacks, so their complete
bodies were read as raw instructions.

`FUN_00176100` subsequently consumes completion, clears the pending-command
word, returns the completed value, and releases the submission semaphore.
Thus an error completion frees the one-request gate just as a successful
completion does; it does not itself close the card file. Library teardown
`FUN_001758D8` waits through `FUN_00176100(0, 0, 0)`, deletes the two
semaphores, and sets the submission-semaphore ID to `-1`. Its body has no
handle walk or close. A full resident-byte search for its direct `jal`
encoding `36D6050C` returned zero matches; this does not exclude indirect
invocation. These observations establish the absence of cleanup in the
inspected EE completion/teardown paths.

#### IOP descriptor reclamation

The retail `MODULES.BIN` contains the card manager at complete-file offset
`0xD000` and card RPC server at `0x24800`. Their loadable segments begin at
member offset `0xA0`, with link address zero. Addresses in this subsection
and the IOP directory trace below are **module-relative link addresses**, not
the relocated IOP execution addresses. The maintained `/MODULES.BIN` program
defines functions only for its first member; it retains these later members
as `unallocated_0` bytes, from which their ELF headers, export/import tables,
and instructions were read. Its `unallocated_0` starts at complete-file offset
`0x19F1`; an instruction at manager address `A` is therefore exposed at
`unallocated_0::(0xB6AF + A)`, and a server instruction at `A` at
`unallocated_0::(0x22EAF + A)`.

The server binds RPC ID `0x80000400` at `0x0300..0x0324` and dispatches
commands 2/3/5/6/10/13 to open/close/read/write/flush/directory handlers.
Its `mcman` import stubs name exports 6/7/8/9/14/12 respectively. The
manager export table resolves those to `0x0C00`, `0x0D20`, `0x1188`,
`0x1340`, `0x0EE0`, and `0x14F8`. These table relationships, rather than
guessed SDK names or host-library behavior, identify the lower routines.

The manager has three shared descriptor slots of `0x30` bytes at link
address `0x261F0`. Byte `+0` is their in-use gate; bytes `+1/+2` gate
writing/reading; signed halfwords `+6/+8` retain port/slot. PS2 open's
`0x6B88..0x6BBC` loop selects the first slot with byte `+0 == 0`; if all
three are occupied, `0x6BC0..0x6BC4` returns `-7`. Successful open marks
the chosen slot occupied. The complete relevant reclamation paths are:

| Lower operation | Confirmed in-use-byte behavior |
| --- | --- |
| Read, `0x1188..0x133F` | Invalid index, inactive slot, missing read permission, or a nonzero preliminary card-gate result returns before the local clearing branch. A negative backend read result clears this slot at `0x12C4`; nonnegative short/full results do not. |
| Write, `0x1340..0x14F7` | The corresponding early validation/card-gate exits precede clearing. A negative backend write result clears this slot at `0x147C`; nonnegative results do not. |
| Flush, `0x0EE0..0x10AF` | The initial card-gate exit at `0x0F44` does not locally clear. Nonzero first cache-flush result goes through `0x0F94..0x0F98`, a nonzero dirty-file update result takes the same path, and a negative final cache-flush result clears at `0x1068`. |
| Close, `0x0D20..0x0EDF` | After validating index/activity, it clears byte `+0` at `0x0D7C`, before the preliminary card gate and later flush/update calls. A subsequently failed close therefore still releases this descriptor slot. |

Read/write results below `-9` additionally invoke `0x068C` and `0xD204`
for the descriptor's port/slot. `0x068C` scans all three slots and clears
the in-use byte of each matching port/slot, not merely the failing descriptor.
`0xD204` invalidates matching cache entries; it is not another descriptor
allocator. The common card gate at `0x0768..0x09B3` can also clear the
card-type state and call that pair when probing fails and a card type had
previously been recorded (`0x0958..0x0990`). Thus the early card-gate exits
in the table are not a guarantee that the slot stays occupied: that callee
can already have invalidated every matching slot.

There is also a bounded full-close path at `0x06E8..0x0767`: it visits each
occupied slot and invokes close `0x0D20`. The manager's negative-argument
module-entry path reaches it at `0x0228` after the unregister result is zero
or `-213`; two other direct calls occur at `0xFE60` and `0xFED8` in the
manager's device lifecycle. This establishes lower teardown reclamation but
does not establish that a normal NA2 save failure requests that teardown.
The server's read/write handlers return errors through their ordinary result
path without calling close; no cancellation command is present in the bounded
command-2/3/5/6/10 handlers.

The RPC server's own stop path is distinct from manager teardown. Dispatcher
`0x0358..0x0364` sets its active flag at link `0x375C` before handling a
command, and the common result path clears it at `0x0640..0x0644`. The
negative-argument module-entry stop routine `0x0170..0x0217` returns 2 when
that flag is nonzero (`0x0180 -> 0x0204`), rather than cancelling the active
command. Once idle, an unregister result of zero or `-213` allows the
server-thread and RPC removal calls at `0x01C4`, `0x01D4`, `0x01EC`, and
`0x01F4`. This bounded stop path has no call to the manager's close import;
the manager's separate full-close path is the teardown evidence for file
descriptors.

**Static conclusion:** backend-negative read/write and the listed flush/close
paths release or invalidate descriptor ownership despite the EE context
retaining its numeric handle. Errors before those branches, including EE
submission failure after an earlier successful open, do not themselves prove
reclamation. Conversely the inspected code does not prove a permanent leak:
card invalidation and lower teardown can later reclaim matching slots. Which
early failure conditions occur on an actual card remains unestablished.

#### Directory-query producer and cached-buffer lifetime

`FUN_00176410(port, slot, pattern, mode, maximum_rows, destination)` packages
RPC command `0x0D` using request fields at `0x006160F0`: port/slot at
`+0/+4`, mode at `+8`, limit at `+0x0C`, destination at `+0x10`, and the
NUL-terminated pattern at `+0x14`. It prepares `maximum_rows * 0x40` bytes
of the destination for DMA and submits the common signal-only callback. It
neither clears nor sorts the destination. The returned count and rows come
from the lower card service; the EE wrapper does not define their order.

All six indexed direct calls to this submitter write the same buffer
`D = 0x0061F740`. The preflight `FUN_001C20A0` first queries the save-directory
path with mode 0/limit 8, changes to the matched directory through RPC
command `0x0C` (`FUN_001765F0`), and queries `*` with mode 0/limit `0x18`.
Repair `FUN_001C2E60` similarly queries the path, changes directory, and
requests `*` with limit `0x0C`. The latter two calls receive the shared
wildcard at `0x00602BFC`. There is no EE filename-based rearrangement before
the cached comparator reads fixed indices 3 through 7.

The other important producer is `FUN_001C2BA0`, which concatenates its path
and suffix and makes a mode-0 query into that same `D`. Creation calls it
with `/data??` and limit 4 at `0x001C192C`; normal save uses the same suffix
at `0x00603008` and limit 4 at `0x001E295C`. These queries supply timestamp
refresher `FUN_001C2C80`, which searches the first four returned rows by
filename. They can overwrite `D`'s first four rows without clearing its
remaining rows. Consequently `D` is shared query state, not a permanently
ordered save-directory snapshot. The comparator's load/repair paths follow
their own full `*` refresh; its indices cannot be interpreted from the buffer
address alone. The EE path alone supplies no directory ordering or short/error
overwrite guarantee.

The embedded server and PS2 manager establish the normal enumeration
ordering. Server directory handler `0x0AE8..0x0C3F` requests one manager row
at a time, first with the supplied mode and then mode 1, DMA-copies each
`0x40` row to successive destination addresses, and returns the accumulated
count. It performs no name or timestamp sort. PS2 manager enumeration
`0x8040..0x8503`, reached through export 12 at `0x15D4`, resets its shared
cursor on mode 0, resolves the parent directory, and walks its entry indices
upward. Each call to entry reader `0xE368` receives that cursor; it is
incremented at `0x82D0..0x82D8` before filtering. Inactive entries are skipped
by attribute bit `0x8000`, and the wildcard is matched against the filename
at entry `+0x40` through `0x0528`. Accepted rows are appended, not reordered.
The entry reader uses the entry index to select a directory-chain sector and
the `0x200`-byte entry within it (`0xE3D8..0xE410`,
`0xE5B0..0xE5EC`). This is directory-entry storage order.

For a non-root directory the initial cursor is zero; root enumeration
explicitly starts at 2 (`0x8220..0x8254`). The non-root `*` query therefore
does not discard its first two active entries. The output synthesizes the
special `.`/`..` names for those entries through the branches at
`0x8344..0x8440`, while ordinary names are copied from entry `+0x40`.
The comparator's expected payload rows 3..6 and descriptor row 7 are
consistent with the native creation sequence in a directory laid out in that
sequence. They are **not an arbitrary-card ordering guarantee**: deleted,
inactive, differently placed, or extra matching entries change the compacted
row indices. Neither the server nor EE wrapper repairs that assumption.

Only accepted rows are written. A short enumeration leaves the destination
suffix from earlier queries. Moreover, if a later one-row manager request
returns a negative result, server `0x0B8C` returns that error without rolling
back rows already DMA-copied. Cached `D` can then contain a newly written
prefix and an older suffix even though the query reported failure. These
byte/lifetime conclusions do not require assuming a card's filenames or
insertion history, and do not establish the contents of any particular card.

`FUN_001c15f0` obtains two consecutive card-info responses and repeats until
their type, free-space, format, and completed-result words agree. Both the
submission-retry and disagreement loops have no attempt bound in this
function. Ghidra declares it `void`, but instructions `0x001C1730..0x001C175C`
leave the final cached completed-result word in `v0`; callers use that word.
`FUN_001e2140` clears its repair-attempt flag at global `0x006075F0` when this
result is nonzero. This flag describes repair history, not changed save bytes.

`FUN_001c3670` is specifically a cached directory-timestamp comparison, not
a checksum or descriptor validator. Let `D = 0x0061F740` be the shared
directory-entry buffer, with `0x40`-byte rows. Its complete observed rule is:

```text
T(row) = byte[row + 9]
       | byte[row + 10] << 8
       | byte[row + 11] << 16
       | byte[row + 12] << 24
return 0 if any T(D + i*0x40), i = 3..6, exceeds T(D + 7*0x40)
return 1 otherwise
```

Those four bytes are the second, minute, hour, and day within the modification
timestamp copied by `FUN_001c2c80`. Month, year, reserved byte, filename, file
size, and the number of valid cached entries do not participate. Native set
creation writes the icon, four records, then descriptor and `icon.sys`; with
the expected directory enumeration including `.` and `..`, rows 3..6 are the
four payloads and row 7 is the descriptor. **Inference:** the intended check
is whether a payload appears newer than its descriptor. The code does not
verify that ordering, and its day-only calendar portion cannot establish
chronological order across months or years. Shorter or differently ordered
directory results are likewise not checked by this comparator.

Its three indexed callers are repair at `0x001C3090`, normal-load checksum
mismatch at `0x001E2744`, and post-repair classification at `0x001E2BF4`.
After a checksum mismatch, comparator result 0 selects status `0x2C`/class 3,
allowing the repair confirmation; result 1 selects status `0x2A`/class 1.
Repair result 0 clears its local descriptor-presence entry even if the table
file was found with nonzero length, thereby selecting reconstruction from all
four payloads. This is a second reconstruction trigger in addition to a
missing/zero-size descriptor. It does not recompute any payload checksum.

After repair, the worker ignores the repair routine's return and reports
status `0x2E`/class 5 if fresh directory classification is 0, 5, or `0x0B`,
or if the timestamp comparator returns 0; otherwise it reports `0x2F`/class 5.
The assembly at `0x001E2BC0..0x001E2C60` corroborates the discarded return and
both decision inputs. Consequently `0x2F` does not prove that every attempted
repair I/O succeeded or that reconstructed descriptors match recomputed
payload sums.

### Allocation, creation, and repair limits

Before checking file allocation, `FUN_001c20a0` queries the directory path
stored at the start of the card context and compares returned names with that
path without its leading slash. A missing match returns `4` when free space
meets the expected allocation, or `3` otherwise. The same results can follow
a nonpositive directory-query result other than the separately handled card
errors; result `4` alone does not establish why the directory was not found.
In load mode, `FUN_001e2140` maps either `3` or `4` to status `0x29`, result
`1`, and idle operation `1`, returning before descriptor or profile reads.
These branches were confirmed in the decompilation of both functions.

`FUN_001c20a0` checks the complete directory allocation before descriptor scan
or profile read. It sums `(file_size + 0x3FF) >> 10` for every returned entry,
then adds `(entry_count - 1) / 2 + 2` blocks. The expected total is stored at
card context `+0x434`; `FUN_001c14f0` initializes it to 103. A mismatch returns
`0x0B` when there is enough free space, or `3` when the deficit exceeds free
space. `FUN_001e2140` calls this check at `0x001E21F8` before dispatching the
requested operation. Result `0x0B` can produce worker status `0x2C`, result `3`,
and return without reading either the descriptor table or a profile. Thus a
directory-size failure cannot be diagnosed solely at the indexed record reader.
The directory entries begin at `0x0061F740`, have stride `0x40`, and store
file length at `+0x10` and filename at `+0x20`.

The preflight call reloads operation, status, and result from the worker after
returning. Operation `1` is idle; it prevents the following operation switch
from running. The recovery branch is not limited to load mode: an initial
directory mismatch in save mode also produces status `0x2C`/result `3`.
`FUN_001e3120` accepts that confirmation by scheduling operation `0x0E`.
After a failed repair, the retained repair flag changes the next mismatch to
status `0x2A`/result `1`.

`FUN_001c17c0` (`0x001C17C0`) creates all four record files filled with
`0xFF`, obtains timestamps, and writes the descriptor table. Worker operation
`0x0C` then explicitly resets all four descriptors to empty and writes the
table again. The all-`0xFF` header supplies repair's `u16 +0x0000 == 0xFFFF`
empty-file sentinel.

The creation routine also accepts the directory-create result `-4` (directory
already exists) and proceeds to rewrite its files. The indexed writer
`FUN_001c19e0` opens the named record with flags `0x203`, writes the requested
byte count, and closes it. Creation can therefore rewrite an existing set;
it does not require the directory to be deleted first.

The all-`0xFF` file is deliberately not a checksum-valid profile. After its
checksum bytes are forced to zero, the additive formula yields `0xDA02`, while
the physical file still contains embedded `0xFFFF` and its empty descriptor
has checksum zero. Native emptiness is therefore represented by descriptor
occupancy plus repair's header sentinel, not by a canonical checksum-valid
empty record.

Creation is also a sequence of independent file operations, not an atomic set
replacement. `FUN_001c17c0` writes the four all-`0xFF` records in index order
and returns on the first reported record-write failure without removing files
already created. Its descriptor/icon write can likewise fail after all four
records exist, and worker operation `0x0C` performs a second descriptor/icon
write after clearing the rows. There is no rollback for any earlier creation
step.

`FUN_001c2e60` (`0x001C2E60`), reached only by worker operation `0x0E`, handles
repair:

- for a missing or zero-size `data01`, `data02`, or `data03`, if `data04`
  exists, it validates the descriptor table structurally, copies descriptor 3
  onto the missing primary row, writes the exact `data04` bytes to that
  primary, and rewrites the table;
- several missing primaries can consequently become duplicates of the same
  rolling copy;
- missing `data04` has no corresponding repair case;
- an existing but checksum-corrupt primary is not replaced. The normal-load
  mismatch branch calls classifier `FUN_001c3670` (`0x001C3670`) and reports
  failure without reading `data04`;
- repair never recomputes or validates `data04` before copying it;
- a missing `icon00.icn` is recreated through `FUN_001c1c50`, and a missing
  `icon.sys` is rebuilt through `FUN_001c2680`.

The copied primary descriptor includes descriptor 3's timestamp. This branch
does not call `FUN_001c2c80` to refresh the primary row after writing the
replacement file, so the UI-visible descriptor date remains the backup's save
date rather than the repaired file's new directory modification time. Several
restored primaries receive the same timestamp as well as the same payload.

On one checksum-mismatch classification, normal load reports worker status
`0x2C`; accepting that UI path makes `FUN_001e3120` request repair operation
`0x0E`. The existing nonzero corrupt primary still does not qualify as missing,
so this user-confirmed repair route does not substitute `data04` for checksum
corruption.

The expected-entry pass treats a file as present whenever its reported length
is nonzero; it does not require `0x2400` for a record or `0x40` for the
descriptor file. A nonzero but wrong-size primary is consequently not replaced
by `data04`. A wrong-size backup reaches a request for `0x2400` bytes; a
lower-layer error fails the operation, while a nonnegative short result is
accepted as described next.

The low-level wrappers do not actually enforce exact transfer counts.
`FUN_001c2a30`, used by `FUN_001c1e60` and `FUN_001c1fa0`, treats every
nonnegative asynchronous read result as success without comparing it with the
requested length. Normal load allocates an uncleared `0x2400` buffer, so a
nonnegative short record read causes the checksum loop to include the untouched
heap tail. Descriptor scan pre-fills its `0x40` stack destination with `0xFF`,
so a nonnegative short table read validates the bytes received plus that
`0xFF` remainder. Descriptor reconstruction has the same short-record-read
issue. Conversely, `FUN_001c2910` treats every nonnegative asynchronous write
result as success and does not verify that the requested record or table length
was written. These are static malformed/partial-I/O behaviors; short successful
transfers were not induced on a card at runtime.

The lower interface exposes the exact count that these wrappers discard.
`FUN_00175e70(handle, destination, size)` submits a read and
`FUN_00175f88(handle, source, size)` submits a write; submission result zero
means queued. `FUN_001c2b70(context, result_pointer)` waits through
`FUN_00176100(0, 0, result_pointer)`. The completed result is the byte count or
a negative error. After a nonnegative write, the native wrapper submits
`FUN_00176920(handle)` and waits again, requiring the flush result to be zero.
`FUN_001c2ad0(context, handle)` closes the handle. The indexed read and write
wrappers return `-777` on success, `6` for read failure, and `7` for write
failure; these success codes do not prove a full transfer.

Restoration is gated by `data04` file presence/nonzero size, not by descriptor
3 being occupied. A structurally valid empty descriptor 3 can therefore be
copied alongside the physical backup bytes, leaving the restored primary
logically empty. This also preserves an old descriptor if an earlier partial
save changed payload files but failed before metadata update.

There is an additional observed invalid-table edge in `FUN_001c2e60`.
After reading the descriptor table into stack buffer `sp + 0x140`, the assembly
at `0x001C31CC` calls `FUN_001e1f50`. A valid result copies the table to global
storage and places that global pointer in `s0`. An invalid result at
`LAB_001C32B8` leaves `s0 == 0`, but execution still writes the physical
`data04` buffer to the missing primary and calls `FUN_001c1b20` at
`0x001C3318` with `a3 == 0` as the descriptor-data source. The called writer
passes that pointer and length `0x40` to its low-level write path. Runtime
consequences were not tested, so this document records the null-source call
rather than asserting a particular crash or card result.

If the descriptor file is missing/zero-size, or the cached timestamp comparison
forces reconstruction, repair reads `data01` through `data04`. Header value
`0xFFFF` produces occupied/class/checksum/play-time
fields of zero; every other value produces occupied 1, class 0, checksum copied
directly from record `+0x0002`, and play time copied from `+0x0004`. In both
cases the row receives that `dataNN` file's directory-entry timestamp. It does
not recompute the copied checksum.

That rebuild requires all four record files to be readable. The two repair
strategies are not composed: if a primary and the descriptor file are both
missing, the earlier missing-primary branch tries to read the absent descriptor
and returns before reaching descriptor reconstruction, even when `data04`
exists. Likewise, a missing `data04` makes the later four-record rebuild fail.
The routine does not first synthesize the missing record from the rolling copy
and then rebuild the table.

A concrete consequence is that an all-zero `0x2400` record is reconstructed as
occupied rather than empty: header zero is not `0xFFFF`, embedded checksum and
play time are copied as zero, descriptor structural validation accepts the
row, and the later normal checksum sum is also zero. No native header/default
validation prevents that non-native profile from loading. This is a deduction
from the observed branches and checksum formula; the malformed case was not
written to a card for runtime testing.

No per-slot delete flow was recovered. Occupied slots are overwritten.
`FUN_00176800` (`0x00176800`) packages the memory-card path-delete command but
has no recovered clean-ELF callers. Worker operation `0x0B` calls
`FUN_001c1760 -> FUN_00176730`, which is the full memory-card format path, not
a selected-slot delete; operation `0x0C` recreates the complete NA2 save set.

Other useful negative results:

- normal load, normal save, and `FUN_001f7890` do not null-check their
  `0x2400` temporary/snapshot allocations before passing them to I/O or copy
  routines; the all-`0xFF` creation buffer and missing-primary restoration
  buffer have the same unchecked-allocation behavior, as does `FUN_001c1c50`'s
  aligned icon buffer before its disc read and card write;
- normal load does not validate record header `+0x0000` or the embedded
  checksum independently;
- descriptor scan does not read record data;
- descriptor structural validation ignores timestamps and does not recompute
  checksums;
- the six grouped tables have established content-category labels, but this
  investigation did not duplicate their per-value lifecycle analysis; most of
  the secondary banks and `0x21F8..0x23FF` remain semantically unresolved;
- no evidence supports treating the aligned opaque regions as floats or
  fixed-size semantic records;
- no Adventure-derived meaning is included here.

## Historical-card corroboration

The inspected card contained a 64-byte descriptor file and four exact
`0x2400`-byte records. `data01` and `data04` were byte-for-byte identical.

The raw descriptor table was:

```text
01002b6189532e00002528101a07ea07
010052631d942d00001a21041107ea07
0100636229962d00002c21041107ea07
01002b6189532e00002628101a07ea07
```

All four records had header value 3, display offsets 0/0, volume `0x0100`,
audio mode 1, Ryo 9,999,999, and progression word `0x1C5C == 0x66`.
`data01`/`data04` had vibration mask 1, while `data02`/`data03` had mask 0.
Their controller arrays were:

| Records | Port 1 action array | Port 2 action array |
| --- | --- | --- |
| `data01`/`data04` | `0010 0020 0040 0080 0004 0008 0001 0002` | `0010 0020 0040 0080 0001 0002 0004 0008` |
| `data02`/`data03` | `0010 0020 0040 0080 0001 0002 0004 0008` | `0010 0020 0040 0080 0001 0002 0004 0008` |

The first sequence is the fixed native default. In the second, the four
shoulder assignments are permuted so Item Select uses L2, Linked Attack uses
R2, and Guard uses L1/R1. The `data01` pair exactly matches the independently
captured control-settings screen: default port 1 and shoulder-permuted port 2.
The additive checksum formula reproduced each embedded and descriptor checksum
exactly:

| Record | Checksum | Serialized play time | Descriptor play time | Difference |
| --- | ---: | ---: | ---: | ---: |
| `data01` | `0x612B` | 3,036,008 | 3,036,041 | +33 ticks |
| `data02` | `0x6352` | 2,987,003 | 2,987,037 | +34 ticks |
| `data03` | `0x6263` | 2,987,529 | 2,987,561 | +32 ticks |
| `data04` | `0x612B` | 3,036,008 | 3,036,041 | +33 ticks |

`data02` and `data03` differ only at record offsets `0x0002..0x0005`, covering
the checksum and the low two bytes of their play-time values. Descriptor rows
0 and 3 give the byte-identical `data01`/`data04` payloads distinct timestamps,
corroborating two separate file writes and timestamp queries.

The seven checksum-covered structured-copy gaps were:

| Offset | `data01`/`data04` | `data02` | `data03` |
| ---: | ---: | ---: | ---: |
| `0x0011` | `BF` | `00` | `00` |
| `0x0032` | `C7` | `7F` | `7F` |
| `0x0033` | `00` | `45` | `45` |
| `0x0966` | `8D` | `30` | `30` |
| `0x0967` | `42` | `BF` | `BF` |
| `0x21F6` | `00` | `00` | `00` |
| `0x21F7` | `00` | `00` | `00` |

The values demonstrate that those bytes are not reliably zero. In combination
with the proven copy omissions and non-clearing temporary allocation, their
variation strongly supports the stale-allocation inference; one historical
image alone would not establish provenance.

All four records shared identical Survival-table and late opaque-region bytes.
The table values corroborate both insertion directions and seed metrics. For
example, first-block row 9 contains metrics `128, 180, 225`, consistent with
inserting 128 ahead of the factor-3 seeds `180, 225, 270`; row 12 contains
`108, 240, 300` against factor-4 seeds `240, 300, 360`. Second-block row 1
retains `10, 8, 5`, while row 0 has `10, 10, 8`, consistent with a score of 10
being inserted ahead of the seed tie. These are consistency observations, not
proof of the individual play events that produced the historical file.

`0x21F8..0x2213` contained 8 nonzero bytes and `0x2214..0x2393` contained 151,
confirming that the aligned opaque ranges are runtime-populated rather than
padding, without establishing their meanings. The final `0x6C`-byte tail was
all zero in all four records; one card is insufficient to conclude that the
tail is unused. Words `0x0DF4` and `0x0DF8` were zero in every record.

## Key resident function map

| Export symbol | EE virtual address | Observed role |
| --- | ---: | --- |
| `FUN_001e0ee0` | `0x001E0EE0` | Allocate save worker (`0x60`) and direct record (`0x2400`) |
| `FUN_001e1c60` | `0x001E1C60` | Persistent save-system task |
| `FUN_001e2140` | `0x001E2140` | Worker dispatcher; normal scan/load/save implementation |
| `FUN_001e2c90` | `0x001E2C90` | Structured secondary-block copy |
| `FUN_001e2e20` | `0x001E2E20` | Structured main-block copy |
| `FUN_001e30f0` | `0x001E30F0` | Eight-byte header copy |
| `FUN_001e34f0` | `0x001E34F0` | Raw record construction followed by full clear |
| `FUN_001e3690` | `0x001E3690` | Clear all `0x2400` record bytes |
| `FUN_001f4360` | `0x001F4360` | Manager construction and new-profile call |
| `FUN_001f47d0` | `0x001F47D0` | Actual fresh/reset profile initialization |
| `FUN_001f7810` | `0x001F7810` | Increment capped play-time field |
| `FUN_001f7890` | `0x001F7890` | Capture one full raw snapshot |
| `FUN_001f7920` | `0x001F7920` | Compare saved payload excluding eight-byte header |
| `FUN_001c15f0` | `0x001C15F0` | Repeat card-info requests until two responses agree |
| `FUN_001c17c0` | `0x001C17C0` | Create four all-`0xFF` record files |
| `FUN_001c19e0` | `0x001C19E0` | Indexed record write |
| `FUN_001c1c50` | `0x001C1C50` | Copy disc icon into `0xE920`-byte `icon00.icn` |
| `FUN_001c1e60` | `0x001C1E60` | Indexed record read |
| `FUN_001c2680` | `0x001C2680` | Regenerate and write `0x3C4`-byte `icon.sys` |
| `FUN_001c2e50` | `0x001C2E50` | Empty hook called on file-I/O failures |
| `FUN_001c2e60` | `0x001C2E60` | Missing-file/descriptor repair |
| `FUN_001c3670` | `0x001C3670` | Compare cached directory rows' second/minute/hour/day bytes |

Resident globals observed in this chain are worker pointer `0x006075F4`, direct
record pointer `0x006075F8`, manager pointer `0x00607600` (live record at
manager `+0x04`), vibration cache byte `0x00607608`, and snapshot pointer
`0x00607628`. `FUN_001e0ee0` allocates the worker and direct record separately;
`FUN_001f4360` later assigns manager `+0x04` from `0x006075F8`, so the manager
and save worker refer to the same live `0x2400` allocation rather than
maintaining two profile copies.
