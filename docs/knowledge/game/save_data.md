# Save-data record format and lifecycle

This document describes the resident-ELF save implementation for NA2.28. It
covers the on-card file set, the `0x2400`-byte profile record, validation and
copy behavior, profile defaults, and the relationship between the three
visible slots and the UI-hidden fourth record. Adventure-mode field consumers are
deliberately out of scope.

## Research coverage

- **Assigned scope:** the clean NA2 `SLPS_258.37` save-record payload and its
resident save lifecycle: physical files and descriptors, record boundaries,
validation and checksum behavior, serialization and copy paths, fresh-profile
initialization, slot/backup relationships, and fields whose meanings could be
recovered without guessing.

- **Exploration depth:** coverage has three distinct depths:

  **Exhaustive within the bounded direct resident paths inspected:** the save
  task and worker (`FUN_001e1c60`, `FUN_001e2140`); indexed record and descriptor
  I/O (`FUN_001c19e0`, `FUN_001c1e60`, `FUN_001c1b20`, `FUN_001c1fa0`);
  descriptor initialization/validation, save-set creation, repair, and error
  classification (`FUN_001e1ef0`, `FUN_001e1f50`, `FUN_001c17c0`,
  `FUN_001c2e60`, `FUN_001c3670`); all three structured serializers
  (`FUN_001e30f0`, `FUN_001e2e20`, `FUN_001e2c90`) and the manual tail copy; and
  the snapshot/compare helpers (`FUN_001f7890`, `FUN_001f7920`). Direct clean-ELF
  references to the live record header and uses of the `0x2400` record-size
  literal were audited. This establishes byte coverage for the complete record
  `0x0000..0x23FF`, including the main block `0x0008..0x0DFB`, secondary block
  `0x0DFC..0x2393`, manual tail `0x2394..0x23FF`, and the seven structured-copy
  omissions at `0x0011`, `0x0032..0x0033`, `0x0966..0x0967`, and
  `0x21F6..0x21F7`. It also covers the four-entry descriptor table and every
  recovered native path involving `data01` through `data04`.
  **Bounded static coverage:** the actual fresh-profile path
  (`FUN_001f4360` -> `FUN_001f47d0`), settings and controller-map synchronization,
  currency, availability/status and ability-bit accessors, Survival-table
  initialization and result writers, and the typed accessors for the secondary
  block were traced far enough to establish the layouts and semantics reported
  below. The secondary block was partitioned across `0x0DFC..0x21F5`, with the
  aligned `0x21F8..0x2213` and `0x2214..0x2393` regions retained as opaque; the
  `0x2394..0x23FF` tail was likewise bounded but not semantically decoded.
  Relevant fixed data included the controller-map table at `0x005C06A0`, the
  initial character-status list at `0x005C06C0`, Survival factors/constants at
  `0x005C06F8`, `0x005C0710`, and `0x005C0730..0x005C0738`, and the 22-entry
  cross-bank mapping table at `0x005D53E0`.
  **Sampled runtime-data corroboration:** one historical local PS2 memory-card
  image was parsed read-only. Its descriptor table and four `0x2400`-byte files
  corroborated the checksum formula, three-primary-plus-rolling-backup model,
  header/settings values, timestamp behavior, and nonzero bytes in structured
  copy gaps. It is a single historical sample, not a controlled runtime test or
  evidence of current emulator state.

- **Confirmed coverage:** the three visible slots and shared
`data04` rolling backup; descriptor, checksum, serialization, scan, repair, and
partial-write contracts; fresh defaults and settings synchronization; the fact
that difficulty is not stored in this record; recoverable currency,
availability, ability-bit, progression-ordinal, controller-map, and Survival
fields; and typed-but-semantic-unknown secondary banks. Observations,
inferences, and unresolved meanings are kept separate throughout.

- **Unresolved or untested:** the semantic meaning of header `+0x0000`, descriptor
class values 1 through 4, character-status bit 1, most individual elements in
the secondary banks, exact Survival row/submode labels, the `+0x0DF4` flag word
and `+0x0DF8` scalar, and all opaque aligned/tail regions. Indirect calls and
overlay consumers were not exhaustively recoverable from resident direct-XREF
analysis.
- **Deliberate exclusions and overlap:** Adventure-mode consumers were deliberately excluded. Startup save UI workflow
belongs to [Startup sequence](startup.md), while availability propagation and
overlay consumers belong to
[Content availability and save-backed unlock state](content_availability.md);
this document records only the save-format facts needed to define those
interfaces.
- **Evidence limitations:** no controlled corruption, allocation-failure,
  short-I/O, power-loss/partial-write, or repair execution was performed, so
  those behaviors are static path conclusions rather than runtime fault-
  injection results. The clean disassembly and source media were inspected
  read-only and were not modified.

## Evidence, identity, and terminology

Static analysis uses the canonical Ghidra 12.1.2 exports for clean
`SLPS_258.37`:

- size: `5,273,256` bytes;
- SHA-256: `20C0A40D70EA412CD431993A2E189B37ECB6054D63AE93BE545470016E1627AF`;
- resident ELF mapping: file offset equals EE virtual address minus
  `0x000FFF00`.

Unless stated otherwise, offsets are absolute offsets from the start of one
`0x2400`-byte record. Function names are the original export names and the
addresses beside them are EE virtual addresses. Statements called
**observed** are direct code or byte observations. Statements called
**inferences** are interpretations supported by multiple observations. Shapes
such as an array length or aligned copy are not treated as field semantics.

A read-only parse on 2026-08-20 also inspected the historical local card image
`@pcsx2_files/games/NA2/NA2.ps2`:

- size: `17,301,504` bytes;
- SHA-256 before and after inspection:
  `997CC8D779A29C426ED6543ADD2E5EF80248A5F9090104AECD58D91478E829C8`;
- last-write time: 2026-08-14 20:52:53 local time.

That image corroborates the static contracts but is not evidence of current
runtime state. Its extracted-record hashes and relevant bytes are recorded in
[Historical-card corroboration](#historical-card-corroboration).

The related resident availability readers and their overlay consumers are
documented in [Content availability and save-backed unlock state](content_availability.md).
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

Because repair classifies a nonzero descriptor file as present, an existing
but structurally invalid `0x40`-byte table is not rebuilt from `data01..data04`.
The normal scan silently retains its reset/empty in-memory rows, and repair's
missing-descriptor case does not run. Intact payloads can therefore disappear
from the native slot UI without being automatically reconstructed.

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
roster availability. `FUN_001f5610` clears the complete status byte.

The six grouped-table labels are established by the native ETC content record
tables and their reader/writer call sites, not inferred from the byte counts.
Their established native byte lifecycle is 0 default/unowned, 1 offered or
announced but unowned, 2 owned and new/unviewed, and 3 owned and viewed/stable.
Individual consumers do not all use the same threshold, so arbitrary nonzero
values are not a safe generic "unlocked" encoding. The supporting overlay
consumers and category-specific behavior are documented in
[Content availability and save-backed unlock state](content_availability.md).

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
resident C export. This negative result supports leaving their semantics open;
it does not rule out indirect calls or consumers in overlays.

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
descriptor. Arbitrary edits are also trivial to authorize by updating the
descriptor's 16-bit sum. This is accidental-corruption detection, not an
authenticity or strong-integrity mechanism.

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
Tooling that recreates existing files byte-for-byte must not assume these bytes
are zero. Tooling that deliberately normalizes them to zero must recompute both
the embedded and descriptor checksums.

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
`FUN_005d82f0` initializes it to 3 at cold process start. `FUN_001f47d0`
copies that cached byte into a fresh record, `FUN_001f4120` changes both the
live record and cache (passing a port below 1 resets the mask to 3), and
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
path. The byte can remain active for the manager's lifetime, but manager
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

The non-Adventure controller identifies itself with Shift-JIS literal
`サバイバル戦闘` (Survival Battle) at `0x00404AF0`. Its result path gives these
tables bounded semantics:

- `FUN_001f24b0` (`0x001F24B0`), called by `FUN_001f27b0`, inserts the current
  character and a cumulative metric into the first block in ascending order
  for controller mode 5, but only while global eligibility value
  `0x00607670` is 1; otherwise it returns `-2` without changing the table.
  Lower is better and ties insert ahead. The metric is cumulative whole
  elapsed seconds. Battle timer `FUN_001eba80` maintains a
  Q8.24 elapsed value at `0x006B28D8`, adds fixed delta `0x00044444`
  (approximately 1/60 second) per active update, and caps its integer part at
  99. After a win, `FUN_001f2e70` adds `max(0, timer >> 24)` to the controller
  metric. `FUN_001f0b10` compares the same integer-second value with 31 and 61,
  establishing the game's at-most-30/at-most-60-second conditions. The saved
  entry is therefore a finite Survival course/category cumulative-time record;
  exact row names remain unproved.
- `FUN_001f2630` (`0x001F2630`), also called by `FUN_001f27b0`, inserts the
  current character and `controller + 4 - 1` into the second block in
  descending order for controller mode 4. The counter starts at 1 and advances
  after wins, establishing a Survival completed-win/streak record. The two
  exact row/submode names remain unproved.

Both insertion functions take their row index verbatim from
`controller + 0x10`. The resident controller initializer clears that word, but
the recovered direct call graph does not expose the later mode-selection owner
that assigns all row values. This is why the record shapes and score meanings
are established while the 25 and two individual row labels remain open.

Accessors `FUN_001f73c0`/`FUN_001f7400` and
`FUN_001f7430`/`FUN_001f7470` perform no row or slot bounds checks. The fixed
initialization filter excludes IDs
`0, 8, 9, 0x14..0x15, 0x17..0x21, 0x2C..0x2D, 0x4A, 0x58`; it does not consult
saved unlock state.

For word `0x0DF4`, the only recovered direct wrapper read is
`FUN_001f7530(manager, 0)` inside menu-selection function `FUN_00384760`
(`0x00384760`). A nonzero bit 0 diverts selected item 0 to
`FUN_003849a0` instead of its normal transition. The only direct setter call in
the clean resident export is the reset clear through `FUN_001f74a0`; no
trustworthy name for the gate is assigned. Scalar `0x0DF8` likewise has only a
direct reset-to-zero wrapper call (`FUN_001f7560`) and no recovered direct
caller of getter `FUN_001f7590`.

## Snapshot and change detection

`FUN_001f7890` (`0x001F7890`) lazily allocates a `0x2400`-byte snapshot and
raw-copies the complete live record into global `0x00607628`. It does not
refresh an existing snapshot. Its four recovered call sites are
`0x001EAAA4`, `0x001EADD4`, `0x001EB1E4`, and `0x001EB4FC`. Paired
`FUN_001f78e0` (`0x001F78E0`) releases it at `0x001EAB2C`, `0x001EAEF0`,
`0x001EB314`, and `0x001EB5D0`.

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

## Creation, repair, and negative results

`FUN_001c17c0` (`0x001C17C0`) creates all four record files filled with
`0xFF`, obtains timestamps, and writes the descriptor table. Worker operation
`0x0C` then explicitly resets all four descriptors to empty and writes the
table again. The all-`0xFF` header supplies repair's `u16 +0x0000 == 0xFFFF`
empty-file sentinel.

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

Worker operation `0x0E` does not consume `FUN_001c2e60`'s return value. It sets
an internal repair-in-progress flag, calls the routine, then chooses its final
status from fresh `FUN_001c20a0` and `FUN_001c3670` classification results.

If the descriptor file itself is missing, repair reads `data01` through
`data04`. Header value `0xFFFF` produces occupied/class/checksum/play-time
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
  buffer have the same unchecked-allocation behavior;
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
`0x2400`-byte records. Extracted SHA-256 values were:

| File | SHA-256 |
| --- | --- |
| Descriptor table | `cd1669918aabb4e00dda83509b40a03fbd76bc7157c49cdf3b8b4975fffeed8f` |
| `data01` | `7521bbd17de879de551533a12ae1a42c98c65e9926c87a1fc60880a180b0b173` |
| `data02` | `e781e89bd40d398dda741f920350558790137bf70773e91d5b376b29549bce7e` |
| `data03` | `42eca5c5a9d6fb058200ee70c07a395731a09ceb1faed2d2ad9c31e125b8cb29` |
| `data04` | same as `data01`, byte-for-byte |

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
0 and 3 timestamp the byte-identical `data01`/`data04` payloads at
2026-07-26 16:40:37 and 16:40:38 respectively, corroborating two separate file
writes and timestamp queries.

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
| `FUN_001c17c0` | `0x001C17C0` | Create four all-`0xFF` record files |
| `FUN_001c19e0` | `0x001C19E0` | Indexed record write |
| `FUN_001c1e60` | `0x001C1E60` | Indexed record read |
| `FUN_001c2e60` | `0x001C2E60` | Missing-file/descriptor repair |

Resident globals observed in this chain are worker pointer `0x006075F4`, direct
record pointer `0x006075F8`, manager pointer `0x00607600` (live record at
manager `+0x04`), vibration cache byte `0x00607608`, and snapshot pointer
`0x00607628`. `FUN_001e0ee0` allocates the worker and direct record separately;
`FUN_001f4360` later assigns manager `+0x04` from `0x006075F8`, so the manager
and save worker refer to the same live `0x2400` allocation rather than
maintaining two profile copies.
