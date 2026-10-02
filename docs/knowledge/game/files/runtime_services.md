# Resident file and archive services

Static evidence for the resident file-location cache, ROFS mount and directory
index, `GZLIST.TXT`, resource-path routing, sector I/O wrappers, and the
AFS partition loader, plus the memory-card use of `ICON.BIN`.

The evidence is the clean retail NA2 (`SLPS-25837`) resident ELF and the
clean extracted `FLIST.DIR`, `GZLIST.TXT`, and `ICON.BIN`, identified in
[Retail game file identities](file_identities.md); overlay address conversion
follows its [address conventions](file_identities.md#address-conventions).
Resident addresses below are live EE addresses; GP is `0x0060A9F0`. Findings
below are static unless stated otherwise.

## Research coverage

- **Assigned scope:** the resident file/archive layer outside CCS object
  parsing: `FLIST.DIR` location caching, `DATA.CVM`/ROFS startup, `GZLIST.TXT`,
  logical and explicit path routing, sector reads, gzip transport, and resident
  background loading, including lower handle/status ownership and AFS partition
  selection. The memory-card use of `ICON.BIN` was followed only far
  enough to establish its file contract.
- **Exploration depth:** coverage is bounded to the named fixed parsers,
  tables, resident service families, and selected direct callers.
  - The complete 40-slot FLIST layout and all eight clean entries, all 21
    GZLIST directory records and 2,332 listed children, and the ROFS root and
    recursive child-directory loads were checked; clean file sizes, hashes,
    padding and fixed capacities were verified directly.
  - The open/read/seek/size wrappers, one-shot loader, `ccUngzip`, persistent
    16-entry pipeline, and FIFO `LoadBg` queue were followed through
    allocation, completion, cleanup, and visible failure branches, including
    scheduler callback ownership and retirement, boot initialization, and
    direct GP stores of every width.
  - The lower ADXF handle pool, read/status pump, synchronous and asynchronous
    stops, seek/close, stream open, device and mounted-volume
    selection/removal, registered removal descriptors, finalization gates, and
    all four direct FLIST-cache consumers were traced, with callback-table and
    instruction bytes where the analysis has no function definition or drops
    tail-call arguments.
  - The AFS partition-load wrappers, shared metadata parser, member-index
    resolver/open, cancellation and interrupted cleanup, four top-level
    startup archives, and the nested-partition startup caller were covered.
  - Battle queue coverage is limited to the per-side request/adopt helpers
    and selected resident fence handlers.
- **Confirmed coverage:** the fixed FLIST/GZLIST layouts, ROFS startup and
  directory-preload behavior, path-routing split, sector-I/O contract, gzip
  transport, persistent pipeline, background queue, and `ICON.BIN` save-icon
  role are documented from those checks. Additional confirmed facts include
  lower handle/adapter ownership, status advancement by the pump, cache-miss
  disc lookup, mounted-volume registration/removal and backing-file ownership,
  the retail host-route null store, AFS member-position reconstruction and
  metadata modes, and ring-based cancellation/transport teardown. Registered
  volume deletion bypasses the backing-close wrapper; AFS metadata survives
  transport cancellation; nested parsing copies the pathname into child
  metadata; and queue inactivity precedes descriptor retirement. Boot's wide
  zero writes and start's zero byte initialize the queue cleanup mode.
- **Unresolved or untested:** the exact vendor names of several ADXF/ROFS
  wrappers, lower I/O status names, the purpose of the dynamically allocated
  GZLIST root buffer, the secondary gzip magic, retail caller reachability of
  the volume-removal wrapper, and reachability of the dormant background-cleanup
  mode remain unresolved. Indirect callers outside the documented families
  were not exhaustively classified. The queue audit covers the described direct
  stores and local address constructions, not unrestricted aliases, distant
  register flows, or every general memory-writing caller. Retail recovery from
  partial AFS metadata, release of the startup owner's metadata allocations,
  and finalizer reachability remain unresolved. AFS parser behavior with
  malformed counts, nonpacked offsets, undersized metadata, or interrupted
  partitions is established only by the described branches, not by execution.
- **Deliberate exclusions and overlap:** CCS payload semantics, overlay
  selection, Adventure, and general save/load behavior were deliberately
  excluded. CCS publication/registry ownership belongs to
  [Resident CCS runtime](ccs_runtime.md); fighter resource tables belong to
  [Character assets](../character_assets.md) and per-side resource sharing to
  [Asset dependency graphs](asset_dependencies.md#all-nine-per-side-selection-slots);
  battle sequencing belongs to [Battle lifecycle](../../gameplay/battle_lifecycle.md). AFS content
  and codecs remain with [Disc files](disc_files.md) and the media documents.
- **Evidence limitations:** no corrupt-file, short-read, allocation-failure,
  cancellation-race, or runtime mount/load experiment was performed, so failure
  and concurrency conclusions are static. Callback registration and numeric
  state transitions establish library contracts, not execution of every branch
  or exact vendor enum names. Address-construction windows and searched
  encodings are bounded evidence, not a whole-game reachability proof.

## `FLIST.DIR` cache capacity and normalization

Startup enters `FUN_001BD380` from `FUN_001C13F0` at `0x001C145C`. The
bootstrap describes `FLIST.DIR` at `DAT_0061EA50` with maximum name length
`0x20`, storage at `0x0061E3E0`, and total storage size `0x668`, then reaches
the parser through `FUN_001336B8 -> FUN_00143D98`.

The parser derives exactly 40 slots from `0x668 / (0x20 + 9)`. The backing
layout is:

| Range | Meaning |
| --- | --- |
| `0x000..0x13F` | Forty 8-byte location tuples |
| `0x140..0x667` | Forty 33-byte normalized-name slots |

`FUN_00143618` records the table pointer, parsed count, capacity, and maximum
name length in `DAT_003E7940/44/48/4C`. `FUN_00143938` resolves each listed
path and fills its location tuple. Cache lookup is `FUN_00143AC8`, reached by
the public-side wrapper at `FUN_00143CB8`.

Normalization is deliberately broader than the later ROFS tree lookup:
`FUN_00142A08` uppercases ASCII and converts `/` to `\`, while
`FUN_001434F0` and `FUN_00143580` compare case-insensitively and accept either
slash style. The clean 124-byte file has eight lines, leaving 32 unused table
slots. More than 40 lines are not parsed.
A name longer than 32 characters is not rejected before copying and can cross
the reserved per-name stride, so the spare capacity does not make long entries
safe.

`FLIST.DIR` remains a location cache rather than an authoritative file list.
The separate explicit-device route described below can open files that are not
listed.

The complete resident direct-consumer set of `FUN_00143CB8` is `FUN_00142A80` (existence/openability query), `FUN_00142B08` (file size),
`FUN_00143230` (file size), and `FUN_00144060` (cached location predicate).
The first three treat a zero cached byte size as a miss, construct a normalized
disc pathname through `FUN_00143448`, and call
`FUN_00142808 -> FUN_00172600` for physical disc search. Path construction
uses the configured current-directory string at `0x003E7960`, inserts a
separator as needed, appends `;1` when absent, uppercases ASCII, and converts
slashes. `FUN_00144060` instead returns whether the cached LSN is nonzero; it
does not search the disc. Thus its false result does not establish absence.

`FUN_00143CB8` also accepts an exact 17-character location string with `.` at
byte 8. `FUN_00143BF8` parses its two parts as hexadecimal LSN and sector
count; the wrapper converts the count to bytes. The shape check does not
validate the two eight-character parts as hexadecimal before parsing.
Literal `DVD-ROM` is separate: it produces LSN zero and size `-1`.
`FUN_00143B90` clears the four cache-control words, and `FUN_00143F18` clears
old cache state before replacement initialization. A miss does not insert a
new FLIST entry.

## `DATA.CVM` mount and root directory

`FUN_001BDEB0`, called only by `FUN_001BD380`, performs the resident mount
sequence:

1. retry `FUN_0011D3D8` until ROFS initialization succeeds;
2. initialize the ADXF/ROFS wrapper through `FUN_001295D0(0)`;
3. retry `FUN_00129670("VOL", "CDV:data/data.cvm", "cc2fuku")` until it
   returns zero;
4. select `VOL` through `FUN_001298A8("VOL")`;
5. register `LAB_001BDFA0` as the `ROFS_EntryErrFunc` callback; the callback is
   only `jr ra; nop`;
6. retry `FUN_0011C610("VOL:/", 0x0061B7F0, 0x44)` until success.

The embedded banner identifies ROFS 1.80, built 2005-11-29 13:28:55.
Embedded `rofs_if.c` and `ROFS_LoadDir` strings identify `FUN_0011C610` as the
directory loader. Its final argument is capacity 68: a directory buffer is
`0x18 + capacity * 0x30` bytes, exactly matching the fixed `0xCD8` root buffer
before the next object at `0x0061C4D0`.

Initialization, mount, and root-directory failure all cause indefinite retry.
This sequence has no alternate CVM or host fallback. Exact vendor names for
the three wrappers at `0x001295D0`, `0x00129670`, and `0x001298A8` are not
embedded, so their narrower roles are kept descriptive rather than guessed.

## `GZLIST.TXT` grammar and resident tree

`FUN_001BDA50`, called by the startup controller at `0x001E0F20`, reads all of
`gzlist.txt` and builds an in-memory directory/file tree. The clean file is
103,848 bytes.

The first section contains 21 directory records: the root plus 20 child
directories. Their listed counts sum to 2,332, representing 2,312 files and 20
child directories. The files are the 2,310 CCS members plus `GZLIST.TXT` and
`ICON.BIN`. For each directory record, the parser reserves four spare entries
and allocates `0x18 + (listed_count + 4) * 0x30` bytes.

The parser builds these nodes:

| Object | Size | Fields |
| --- | ---: | --- |
| Directory node (`FUN_001BCBB0`) | `0x34` | `+0x00` sibling, `+0x04` 32-byte name, `+0x24` file head, `+0x28` child head, `+0x2C` ROFS capacity, `+0x30` directory buffer |
| File node (`FUN_001BC810`) | `0x28` | `+0x00` next, `+0x04` 32-byte name, `+0x24` decompressed size |

Each second-section row is `path compressed_size gzip_size`. The parser reads
both numbers but discards `compressed_size`; only `gzip_size` is stored at
file-node `+0x24`. `FUN_001BE9B0` looks up a path and returns that field. Its
callers use zero as the raw-file marker and a nonzero value as both the gzip
marker and required output allocation size. Actual compressed read length
comes from ROFS, not the discarded column.

Directory components in this tree use bytewise comparisons with no ASCII case
fold. Both slash styles parse, but spelling and case must match. The parser
also allocates a buffer for the root node; known root paths use fixed buffer
`0x0061B7F0`, and no consumer of the dynamic root-node `+0x30` allocation has
been proven.

## Directory-metadata preload

Startup creates the worker at `FUN_001BD970` with
`FUN_001D0090(0x001BD970, 0x28, 0x4000)`. `FUN_001BD850` signals it through
start byte `0x0060749C`; completion byte `0x006074A0` is polled by
`FUN_001BD870` and participates in the startup barrier.

The worker is named `Load ROFS_Data`. After its start signal and a scheduler
yield, it recursively calls `FUN_001BD880` for every child directory beginning
at `DAT_0061EA88`. Each node retries
`ROFS_LoadDir(path, node->buffer, node->capacity)` with yields, then visits its
child and sibling. The root has already been loaded synchronously.

This eagerly loads directory metadata, not the 2,310 CCS payloads. All 21
dynamically allocated directory buffers total 116,472 bytes (`0x1C6F8`); the
20 child buffers total `0x1BD80` when the unproven root allocation is excluded.

## Logical and explicit path routes

`FUN_001BE450` is the generic resident open wrapper. Its resolver
`FUN_001BE1F0` recognizes two device classes and two API spellings:

| Class | CRI spelling | EE file-I/O spelling |
| --- | --- | --- |
| Host | `HST:` | `host0:` |
| Optical disc | `CDV:` | `cdrom0:` |

Recognition uses case-sensitive substring search `FUN_0017CAF8`, not a check
restricted to the start of the path. Once recognized, the resolver removes
everything through the first `:` and selects the requested output spelling.
The four literal strings and their pointer cells occupy
`0x00602B30..0x00602B6B`.

An unrecognized path takes the logical route. `FUN_001BDFB0` separates the final
component, `FUN_001BCD60` finds a preloaded directory handle, and the leaf name
is opened relative to that handle. A leading slash begins at fixed root handle
`0x0061B7F0`; a plain filename uses handle zero.

An explicit disc device is rewritten to the selected spelling and passed as a
complete path to `FUN_0012ACB0` with handle zero. This bypasses the GZLIST
directory tree. Host spelling is recognized, but its branch executes
`sw zero,0(zero)` at `0x001BE390` before copying the rewritten prefix. The
bytes there are `00 00 00 AC`. A usable host open through this retail wrapper
is therefore not established; the null store is present independently of any
later open failure.

Both open branches treat failure as fatal: the wrapper stores through address
zero and retries rather than returning a recoverable error.

### Device registry and mounted-volume selection

The lower stream open is not a direct ROFS call:
`FUN_0012AC00 -> FUN_00131EE0 -> FUN_00131F50` requests stream open and pumps
until stream byte `+0x45` clears. `FUN_001328C8` handles that pending open
through `FUN_0013E800(path,directory_handle,0)`, marks stream state 4 on open
failure, and settles the file bounds before permitting reads.
The generic handle returned by `FUN_0013E800` is an eight-byte
`{device_callback_table, device_file_handle}` pair from a 40-slot pool at
`0x0060AEE8`. The lower stream owns this pair; close
`FUN_0013EB50` invokes device callback `+0x14` and then clears both words.

`FUN_0013E9A0` splits a device at `:` and uppercases only the device name;
the remaining filename is not normalized there. The registered-device table
has 32 entries of `0x10` bytes at `0x0060B028`, each containing a callback
pointer and inline name. `FUN_0013E430` chooses a registered table.
`FUN_0013E758` applies the selected default when no device was supplied and
also retries device selection with that default when an explicit device is
unregistered. In the latter case it restores the original full pathname for
the default device. This is a lower device-selection branch; it does not
establish successful access to an unknown device or an alternate CVM.

The default device string is at `0x0060B228`. `FUN_0013E600` sets it only
after finding a registered name; an empty name clears it.
`FUN_0013FFC0` queries device control operation 100. When it returns 1, it
rebuilds the filename with the device name using the format at `0x005B9250`.
The ROFS adapter returns 1 for that operation, so mounted-volume identity
survives the split and reaches its open callback.

Startup registers `ROFS` using `FUN_001295D0 -> FUN_00129600` and constructor
`FUN_00122440`, whose banner identifies ROCI 1.15, built 2005-11-29 13:28:57.
Its callback table is `0x003D1A48`. Mount
`FUN_00129670 -> FUN_001296C8` first opens the backing `CDV:data/data.cvm`
through the generic device layer, then calls ROFS control operation 2 through
`FUN_0013FC18`. `FUN_00122770` validates a non-`ROFS` volume name of at most
eight bytes, registers that name through constructor `0x00122470`, and passes
the backing handle and password to `FUN_0011BF90`. The mounted-volume
callback table is `0x003D1AB0`; its ordinary file operations match the ROFS
table, but its first callback is null. The ROFS table's first callback at
`0x00122480` tail-jumps to `FUN_0011C330`, which dispatches the service pump
at `FUN_0011E4F0`; it is not an initialization callback. Failed mounting
unregisters the volume except for result `-0x68`. In initialized ROFS,
`FUN_0011D8E0` produces that result when `FUN_0011CDA8(name,0)` finds an
existing volume record, before allocating or reading another archive.
The outer mount wrapper closes the backing generic handle on a negative mount
result; on success it leaves it with the mounted archive.

`FUN_001298A8 -> FUN_001298D8` makes `VOL` the default device, queries its
volume information through operation 5, and invokes operation 6 on success.
These reach `FUN_0011C590` (`ROFS_GetVolumeInf`) and `FUN_0011C0B0`
(`ROFS_SetDefVolume`), identified by embedded names at
`0x005B5D48` and `0x005B5CD0`. The information callback `FUN_0011E968`
returns two words: a borrowed pointer to the volume name at record `+0x16`
and the backing generic file handle at record `+0x00`. A missing volume clears
both words and returns `-0x69`. Default-volume callback `FUN_0011DE38`
stores the selected volume-record pointer at ROFS context `+0x2C`.

The mounted-volume ordinary open callback `0x001224B8` tail-jumps to
`FUN_0011C188(path,directory_handle)`;
close `0x001224D0` tail-jumps to `FUN_0011C298`, which frees the ROFS file
handle through `FUN_0011B778`. It does not unmount or close the backing CVM.
The callback-table pointers and `0x001224B8..0x001224E7` instruction bytes
establish those edges even though the analysis has no function definitions
for the two thin callbacks.

### Volume removal and backing-file close

`FUN_00129788 -> FUN_001297B8` first queries volume information through
operation 5. On a nonnegative result it requests removal through operation 3
(`FUN_0013FD20`), then closes the saved backing generic handle through
`FUN_0013EB50`. It ignores the removal result; instructions at
`0x001297F4..0x00129800` confirm the unconditional close after that call.
Thus this wrapper does not preserve the backing handle when removal fails.
`0x00129788` has no direct resident references; indirect retail reachability remains unknown.

Operation 3 reaches `FUN_00122710 -> FUN_0011C040` (`ROFS_DelVolume`,
embedded name at `0x005B5CC0`) and backend `FUN_0011DC90`. The adapter
rejects the literal `ROFS` and unregisters the device name only after a zero
backend result. The backend finds the volume and examines the ROFS file pool
at context `+0x108C`, using the count at context `+0x04`. For an in-use file
with a nonnull volume link and the same backing handle, it calls
`FUN_0011B778`. That release calls `FUN_0011BD38` when file state `+0x38`
is 2; backend stop is invoked only when operation field `+0x36` is also 1.
The release then clears `+0x36` and in-use field `+0x34`.
It releases a file slot, not the backing archive.

The pool scan does not necessarily visit every slot. Instructions
`0x0011DDB8..0x0011DE04` advance the row pointer by `0x3C` only after
encountering an in-use row with a nonnull volume link; an unused or unlinked
row advances only the loop counter and is inspected repeatedly. Later rows
are therefore skipped in that branch. After the scan,
`FUN_0011CFE8` zeroes the `0x34`-byte volume record and clears the default
volume pointer if it selected that record. This is static evidence of the
cleanup limitation, not an observed stale-handle or cancellation outcome.

#### Registered removal callback and wrapper reachability

Both device tables store `0x00122770` at `+0x60`. Generic control helper
`FUN_0013FD20` resolves the registered device, requires a nonnull volume name,
and builds a five-word descriptor with that name at `+0x04`; it calls the
table entry with operation 3. The dispatcher requires a nonnull descriptor and
name, then tail-jumps directly to `FUN_00122710` at `0x00122884`. The mount
branch instead tail-jumps to `0x00122668` at `0x00122864`. The decompiler merges that
mount continuation into the dispatcher's decompilation; callback-table bytes
at `0x003D1A48..0x003D1B17` and instructions at
`0x00122840..0x00122888` establish the separate routes.

The registered removal callback therefore reaches backend volume deletion,
not outer wrapper `FUN_00129788` or inner wrapper `FUN_001297B8`. The latter
adds the separate information query and backing-file close. Device-name
unregistration `FUN_0013E528` only clears the matched registration's first
name byte; it calls no close, destructor, or removal callback and leaves its
callback-table word intact. Registration
`FUN_0013E358` obtains a table through the supplied constructor and stores it
in the first empty-name slot when no existing name matches.

Searches in the resident ELF, BTL, and ETC for pointer bytes
`88 97 12 ??` and `B8 97 12 ??` returned no matches. Direct `jal` bytes for
the outer wrapper also had no match; the inner target appeared only in its
outer wrapper at `0x0012979C` and the mapped copies of those instructions.
The `addiu` low-part searches `88 97 ?? 24` and `B8 97 ?? 24` added no
wrapper-address construction: the single BTL hit at imported `0x008535B8`
is preceded by `lui a0,0x8C`, constructing `0x008B97B8`, not the resident
wrapper. No search reached its 300-result bound. The resident outer wrapper
still has no direct reference, while control helper `FUN_0013FD20` has only
the inner wrapper's call at `0x001297F4` in the inspected reference set.
These findings exclude the searched encodings and literal entries; computed
function pointers, other address-building forms, unrestricted aliases, and
uninspected callers remain unresolved. The registered callback's availability
is not evidence that retail invokes removal.

#### Other teardown lifetimes

Backend teardown `FUN_0011D6A8` acts only when ROFS context `0x003D1938` is
nonnull and its first word is 1. It releases every file slot, clears every
volume record through `FUN_0011CFE8`, invokes the physical-driver table's
`+0x04` callback, zeroes the context storage, and clears the context pointer.
The selected driver table at `0x005B61E8` contains `0x001200F0` at `+0x04`;
Bytes `0x001200F0..0x001200F7` are only `jr ra; nop`. Neither the volume
record clear nor that selected driver callback closes the backing generic
file handle. Backend initialization `FUN_0011D410` invokes this teardown
before initializing a new context. This establishes reinitialization's
library contract, not a retail unmount event.

Generic device-layer teardown `FUN_0013E218` has a different gate: its
initialization count `0x003E5784` must become zero after decrement. It invokes
each allocated generic handle's own table `+0x14` close callback across all
40 slots, then clears the handle pool, device registrations, and default
name. The resident 300-result reference query found no direct caller for
this finalizer. Ordinary generic close `FUN_0013EB50` likewise dispatches
through the handle's saved table pointer and clears the two-word handle; it
does not resolve the device name again. Clearing a registered name therefore
does not itself invalidate or close an already allocated handle. The outer
volume-removal wrapper, ROFS context teardown, name unregistration, and generic
pool teardown have distinct responsibilities. Their separate gates do not
establish a retail shutdown sequence.

The outer volume wrappers' enter/leave functions `0x00129948` and
`0x00129950` are both `jr ra; nop` in retail bytes. They provide no locking
around the information-query, removal, and close sequence. This does not
establish a concurrent outcome or the behavior of locks inside lower layers.

## AFS partition selection and member opens

AFS partitions use a separate 256-pointer registry at `0x003D3690`.
`FUN_00129A38` accepts only IDs `0..255` and nonnull caller metadata.
The metadata is borrowed: the loader stores its pointer in the registry and
fills it, while temporary ADXF handle cleanup does not free that allocation.
The in-progress parser is a singleton with globals
`0x003D3BBC..0x003D3BD4`, including member cursor, temporary ADXF handle,
partition ID, status, input buffer, and input sector count.

`FUN_0012A278` is the shared load entry for explicit archive paths and nested
archive members. It rejects another load while partition state is 2. It
requires nonnull temporary storage and positive byte capacity, records the
caller metadata, opens an ADXF handle, then reads sector chunks into the
temporary buffer. The ordinary wrappers provide a 64-byte-aligned
`0x800`-byte buffer at `0x003D3C40`. Parser
`FUN_0012A610 -> FUN_0012A648 -> FUN_0012A698` samples ADXF status, handles
the completed chunk, and issues the next read until every member size has been
recorded. The parser explicitly sets state 3 after recording all member
sizes; state 4 marks its visible format, count, member-size-limit, and
read-start failure branches. The lower-status copies described below are
separate from those explicit parser transitions.

| Partition metadata field | Observed role |
| --- | --- |
| `+0x04` | Computed metadata byte size |
| `+0x08`, `+0x0C` | Member count, word and halfword copies of the parsed low 16 bits |
| `+0x0F` | Size representation: 1 exact byte sizes, 0 sector counts |
| `+0x10..+0x10F` | Archive pathname |
| `+0x110` | Underlying directory handle |
| `+0x114` | Archive's base sector within the backing file |
| `+0x118` | First member offset: a word of bytes in mode 1, halfword sectors in mode 0 |
| `+0x11C` in mode 1 | One word of exact byte size per member |
| `+0x11A` in mode 0 | One halfword of rounded sector count per member |

The parser checks only the first three magic bytes against `AFS`, reads the
32-bit little-endian count, and compares it as signed against `0x10000`.
The accepted count is then rebuilt from only bytes 4 and 5 and stored at
`+0x08/+0x0C`. Thus exactly `0x10000` is accepted by the comparison but becomes
zero in metadata; high-bit malformed counts are not rejected by that signed
upper-bound test. Instructions and bytes `0x0012A7B8..0x0012A834` establish
the signed `slt` and subsequent two-byte rebuild. This is a parser limitation,
not evidence that such an archive is usable.

Only the first stored member offset is retained. The parser skips all later
offset words and records their adjacent size words. In mode 1 it preserves
byte sizes; in mode 0 it calls `FUN_0012C748` to sector-round them and rejects
a result outside 16 bits. For a nonnegative size this requires
`ceil(bytes / 0x800) <= 0xFFFF`, or at most `0x07FFF800` bytes.
The diagnostic describes this as the AFS 128-MB limit, but the actual rounded
bound is one sector below that number. The first offset in mode 0 is instead
shifted down to sectors without the member-size ceiling check.

Member resolver `FUN_0012C200` validates the partition and member index through
`FUN_0012C050`, then reconstructs the member's sector start as archive base
plus the first offset plus the rounded sizes of all preceding members. It
returns the selected rounded size and either the exact byte size (mode 1) or
rounded byte size (mode 0). It does not consult the selected member's original
offset word. Consequently this resolver assumes sequential sector-packed
members; gaps or independently authored offsets are not represented in its
metadata. Archive-content inventory remains in [Disc files](disc_files.md).

`FUN_0012B018 -> FUN_0012B060 -> FUN_0012AF40` opens a selected partition
member, obtaining the stored pathname through `FUN_0012C3C8` and applying its
sector start and length to the lower stream. It retains a borrowed pointer
into the partition metadata, so that metadata must outlive the open member.
Ordinary ADXF close frees the member's handle/stream, not its partition.
`FUN_0012AE18 -> FUN_0012AE80 -> FUN_0012AD98` is the corresponding explicit
pathname plus directory/start/count variant. These two public open wrappers have no direct resident
references; the shared parser invokes the internal member opener for nested
archives, and indirect callers are not excluded.

Startup `FUN_001D6550` loads four top-level partitions serially through
`FUN_001D6B60`. Literal table `0x003FD770` supplies `sound.afs`, `stream.afs`,
`rpgvoice.afs`, and `plvoice.afs`; `CDV:data/` is prefixed. Halfword table
`0x00602C48` supplies IDs `255`, `254`, `253`, and `252` in that order.
`sound.afs` takes `FUN_00129E18 -> FUN_00129E80 -> FUN_0012A160`, which
passes metadata mode 1. The other three take
`FUN_00129BF0 -> FUN_00129C58 -> FUN_00129FC0`, which passes mode 0.
The decompilation misrepresents the packed ID table and loses these mode and
buffer arguments; the halfword loads in `0x001D6BB8..0x001D6C24`, tail-call
instructions `0x00129E80..0x00129EA4`, and mode stores at
`0x0012A1A0`/`0x00129FFC` establish them.

The same startup caller follows its three configured nested-partition arrays
through `FUN_001D6C70 -> FUN_00129D88`, using the top-level partition ID and
member index to parse another archive into a supplied metadata buffer. Both
retail startup helpers yield until partition state 3 only; they do not break
on state 4. The library's separate blocking helper `FUN_00129B70` does return
`-1` on state 4, but those startup helpers do not use it.

Successful metadata completion and the parser's format, count, size-limit,
and subsequent read-start failure branches call `FUN_0012A528`, which
closes the temporary ADXF handle and clears it, the member cursor, and read
sector count. It leaves the partition registry pointer and metadata intact.
Explicit parser cancellation `FUN_0012A568 -> FUN_0012A590` synchronously
stops a non-idle handle, sets partition state 1, and invokes the same cleanup.
It does not unregister or erase partially built metadata. Member-index
validation checks that metadata exists and the index is within its recorded
count; it does not verify that partition parsing completed. No use of canceled
partial metadata is established by the scoped startup callers.

### Interrupted partition ownership and library teardown

The parser's admission gate is its singleton state, not a per-partition
completion flag. `FUN_0012A278` refuses state 2 before replacing anything.
Otherwise it closes any leftover temporary handle, resets the current
partition ID to `-1` and state to 1, then validates temporary storage and the
new metadata pointer. Validator `FUN_00129A38` checks only ID range and
nonnull metadata; it does not reject a populated registry slot. Once admitted,
the loader sets state 2, clears only the metadata's first `0x11C` bytes, and
replaces the selected registry pointer before opening the archive. It does
not free the previous metadata allocation or check for member handles that
borrow its pathname.

Cancellation `FUN_0012A590` acts only while the temporary handle is nonzero
and the recorded partition ID is nonnegative. It synchronously stops that
handle when its numeric status differs from 1, sets parser state 1, and closes
the transport through `FUN_0012A528`. Instructions
`0x0012A528..0x0012A564` clear only the temporary handle, member cursor, and
input-sector count. The partition ID, registry entry, caller metadata, and
input-buffer pointer survive. Consequently a subsequent load may replace the
same registry entry, but cancellation itself does not release or unregister
the metadata. This is an ownership distinction; use of such partial metadata
and concurrent replacement outcomes remain unproven.

Failure cleanup is branch-specific. In `FUN_0012A698`, a sampled lower
handle status other than 3 is copied into parser state and returned before
metadata consumption or `FUN_0012A528`. In particular, lower status 4 alone
does not close or clear the temporary handle there. At initial admission,
`FUN_0012A278` closes the handle after a rejected first read but leaves its
global pointer nonzero; an archive-open failure instead stores a zero handle
while leaving the newly installed metadata pointer registered. All of these
paths leave caller metadata allocated. After issuing another chunk read,
the parser copies handle status again at `0x0012AA80..0x0012AA88`; it does
not return a separately named metadata-completion enum. These numeric status
copies must be distinguished from the explicit all-members-recorded branch
at `0x0012A9EC..0x0012A9FC`, particularly for malformed or truncated input.

After cancellation, polling the recorded ID with no temporary handle returns
state 1 without reparsing. Polling a different ID returns `-3` before that
check. Member validator `FUN_0012C050` checks only ID range, registry presence,
and `0 <= index < metadata->count`; it reads no singleton completion state.
Member open `FUN_0012AF40` saves the pathname pointer obtained from
`FUN_0012C3C8` at ADXF handle `+0x3C`, as confirmed by
`0x0012AF94..0x0012AFC8`. Replacing a registry pointer does not retarget that
borrowed pointer. Whether a caller opens unfilled member sizes or frees old
metadata while a member handle survives remains unresolved.

Library initialization `FUN_00129430` increments count `0x003D3208`; only
its zero-count entry initializes the handle pool and partition registry.
Finalization `FUN_00129508` decrements that count and performs teardown only
when it reaches zero. It closes every in-use ADXF handle through
`FUN_0012B258 -> FUN_0012B280`, resets parser state and ID, then clears the
registry and handle pool. There is no free of the caller metadata allocations
in that path. The close-all helper has no partition-registry operation; it
releases transport handles independently of metadata registration. The final
library function has no direct resident reference, so this static teardown contract does not establish a retail
shutdown path.

The public cancellation entry `0x0012A568` likewise has no direct resident
reference; its inner implementation is referenced only by that wrapper. These are library operations available in the
resident image, with retail admission and execution still unresolved.

### Nested metadata allocation and pathname ownership

The selected startup owner is allocated as a `0x718`-byte manager by
`FUN_001D7A30`, called immediately before partition startup in
`FUN_001D9650`. `FUN_001D6AA0 -> FUN_001D6190` allocates caller metadata
through `FUN_00117700`. The four top-level metadata pointers are manager
`+0xF4`, `+0xFC`, `+0x104`, and `+0x10C`, each followed by its allocated
byte capacity. Nested records are separate pointer/capacity pairs in the
manager; a configured zero member count leaves both words zero. The load
helper `FUN_001D6C70` skips a null nested metadata pointer before entering
the parser. The manager allocation, metadata allocations, parser transport,
and registry entries are therefore separate objects.

One concrete path is the first sound partition. The 13 records beginning at
`0x003FDCD0` cause a `0x154`-byte top-level allocation at manager `+0xF4`;
the first record's count `0x004E` causes a separate `0x1B8`-byte nested
allocation at `+0x114`. After top-level ID 255 completes, instructions
`0x001D65A0..0x001D65C0` load destination ID 0 from that first record,
source ID 255 from the packed ID table, member index 0, and the nested
metadata pointer. This path uses distinct source and destination registry
slots. The helper performs no cancellation or recovery action while waiting
for state 3; those interrupted outcomes remain untested.

Nested admission first opens the parent member through `FUN_0012B060`, whose
ADXF handle borrows the parent's pathname. It then calls `FUN_0012C200` with
child metadata `+0x10` as the output pathname buffer. The resolver copies up
to `0x100` pathname bytes into that buffer and returns the parent's directory
handle and reconstructed member start; admission stores those at child
`+0x110/+0x114`. Thus the temporary member handle borrows a parent pointer,
while child metadata receives its own pathname copy and base sector. Closing
the temporary handle neither frees the parent nor the child metadata. A
release path for these manager-owned metadata allocations has not been
established by this selected startup trace.

## Sector I/O contract

The resident wrappers are sector-oriented:

- `FUN_001BE560` starts a read for signed `length >> 11` sectors, polls the
  lower request, and returns the original requested length. A positive tail
  smaller than `0x800` bytes is not transferred, so callers must sector-round.
- `FUN_001BE740` rounds a byte offset upward with `(offset + 0x7FF) >> 11`.
- `FUN_001BE7C0` reports lower size in bytes by shifting its sector count left
  11.
- If the resident pause flag at `*(object@0x006073FC + 0x504)` appears during a
  transfer, `FUN_001BE560` seeks back to the saved sector and retries. Lower
  request state 4 also retries. The binary does not name the lower state enum,
  so states 1, 3, and 4 remain numeric.

GZLIST consumers use the sector-rounded size returned by `FUN_001BE7C0`.
The icon-copy path independently demonstrates the contract by reading a
`0xE920` payload through a `0xF000` request.

### Lower ADXF handle and request ownership

The sector wrappers call a lower ADXF family. Embedded diagnostics identify
`FUN_0012B590` as `adxf_ReadNw32`, its 64-byte-alignment wrapper
`FUN_0012B778` as `adxf_ReadNw`, and `FUN_0012B7F0` as `adxf_Stop`.
These names come from literal diagnostics at `0x005B7128..0x005B725F`, not
from inferred vendor symbols. Public wrappers enter and leave the library
critical section through `FUN_0012C770`/`FUN_0012C788`.

`FUN_0012AB10` allocates the first free slot from 16 inline `0x48`-byte
handles at `0x003D3210`; `FUN_0012AB68` constructs its stream object through
`FUN_00131CE0(0,0x100)`. This pool is separate from the persistent player's
16 request rows and the unbounded linked `LoadBg` list.

| ADXF handle field | Observed role |
| --- | --- |
| `+0x00` | Slot in use, set to 1 after stream construction |
| `+0x01` | Request state: initially 1, active read 2, terminal 3 or 4 |
| `+0x02` | Borrowed-stream marker; zero for the direct-buffer read path |
| `+0x03` | Asynchronous stop pending |
| `+0x04` | Owned lower stream handle |
| `+0x08` | Destination-stream adapter; destroyed when owned |
| `+0x0C` | File size in sectors |
| `+0x18` | Current logical sector position |
| `+0x1C`, `+0x20` | Requested start and clamped sector count |
| `+0x24` | Sectors transferred relative to the request's starting position |
| `+0x28`, `+0x2C` | Borrowed destination buffer and its byte capacity |
| `+0x38`, `+0x3C` | Directory handle and borrowed pathname used for open |

Open `FUN_0012ACB0 -> FUN_0012ACF8 -> FUN_0012AC00` allocates a slot,
opens the stream, and records its size and position. If the lower stream
reports state 4, it is closed and the ADXF slot is cleared before zero is
returned. Pool exhaustion likewise returns zero after a diagnostic; the outer
resident open wrapper does not propagate it.

Read `FUN_0012B720 -> FUN_0012B778 -> FUN_0012B590` rejects an unaligned
destination with `-3`. The inner function rejects null handle, negative sector
count, or null buffer with `-3`, returns zero without replacing an already
state-2 request, and returns `-1` for a nonnull existing adapter or `-2` if
adapter construction fails. A new adapter wraps the caller's buffer; the file
layer does not own that buffer allocation.

`FUN_0012B2E0` clamps the sector request to `file_size - position`. An empty
request becomes state 3 immediately. A nonempty request becomes state 2 and
starts the lower stream. The resident pump
`FUN_0012C7A0 -> FUN_0012C7C8 -> FUN_0012BAA8 -> FUN_0012BAD0` scans all 16
in-use handles. For state 2, `FUN_0012B9E0` copies the lower state and
transferred count. On terminal state 3 or 4 it advances logical position and
calls `FUN_0012B100` to clear/destroy an owned adapter. The exact
`(state - 3) < 2` unsigned terminal test is corroborated by instructions
`0x0012BA20..0x0012BA44`.

`FUN_0012BFE8 -> FUN_0012C020` only returns handle byte `+0x01`; polling
alone does not advance the request. `FUN_001BE560` pumps before polling and
returns the caller's original byte length on lower state 1 or 3. It retries
state 4. It ignores the initial read function's return value and never
compares the transferred-sector count with the requested length. Therefore
its byte-count return is not proof of a full transfer, particularly after a
rejected or EOF-clamped request. This is a static consequence of the control
flow, not a measured short-read result.

Synchronous stop `FUN_0012B7F0` stops the lower stream, samples the transferred
count, releases an owned adapter, and returns the handle to state 1.
Asynchronous stop `FUN_0012B8E0 -> FUN_0012B918` asks the lower stream to stop
and sets `+0x03`; the pump releases the adapter and clears this latch when the
lower state becomes 1. An already-complete state 3 instead resets directly to
1. Seek `FUN_0012BB88` synchronously stops state 2 before applying absolute,
current-relative, or end-relative sector movement and clamps the result to
`0..file_size`.

Close `FUN_001BE540 -> FUN_0012B170 -> FUN_0012B1A0` synchronously stops
state 2, closes and destroys the lower stream, and clears the entire
`0x48`-byte slot. It does not free the caller's read buffer. This lower stop
family is distinct from cooperative CCS-wrapper cancellation and from task
termination; container publication and cancellation ownership belong to
[Resident CCS runtime](ccs_runtime.md#loading-and-cancellation).

## `ICON.BIN` memory-card role

`FUN_001C1C50` copies the CVM member `icon.bin` into each PS2 save directory as
`icon00.icn`. Its one-record table supplies source offset zero, payload length
`0xE920`, and destination name `icon00.icn`. The function opens the source
through `FUN_001BE450`, reads the sector-rounded `0xF000` bytes, opens the
memory-card destination with mode `0x203`, writes exactly `0xE920`, and closes
it.

The clean source is 61,440 bytes (`0xF000`).
The final 1,760 bytes, `0xE920..0xEFFF`, are all `0xFF` padding, exactly
matching the rounded-read and short-write behavior.

`FUN_001C2680` separately creates the `0x3C4`-byte `icon.sys`, begins it with
`PS2D`, and writes `icon00.icn` into all three icon-name fields at
`+0x14C`, `+0x18C`, and `+0x1CC`. The source file's role is therefore
confirmed. Its internal visual and animation fields have not yet been decoded.

## Payload transport, gzip stage, and background requests

### One-shot loader

`FUN_001CF3F0` owns the synchronous orchestration around a `0x34`-byte load
state initialized by `FUN_001CF2B0`:

| Offset | Meaning |
| --- | --- |
| `+0x00` | ROFS handle |
| `+0x04` | GZLIST decompressed size; zero selects the raw path |
| `+0x08` | compressed-source ring |
| `+0x0C` | decoded or raw consumer ring |
| `+0x10` | `ccUngzip` object |
| `+0x14` | gzip task |
| `+0x18`, `+0x1C` | input and output chunk sizes, both `0x10000` |
| `+0x20`, `+0x22` | input and output slot counts, both four |
| `+0x24` | backing allocation |
| `+0x28` | cancellation byte |
| `+0x2C..+0x2E` | read, gzip, and consumer completion bytes |
| `+0x30` | downstream object handed to the consumer/registry |

The reader is `FUN_001CF060`, gzip worker is `FUN_001CF190`, and consumer
handoff begins at `FUN_001CF210`. A zero GZLIST size connects the reader
directly to `+0x0C`; a nonzero size connects reader -> `+0x08` -> `ccUngzip`
-> `+0x0C`. The tasks are named `LoadRead`, `LoadGzip`, and `LoadDecode`, with
priorities `0x74`, `0x7E`, and `0x7F` respectively. The orchestrator waits for
consumer and reader completion, closes the file, and for compressed transient
loads separately waits for gzip completion before destroying the source ring.
It exposes no load-status return value.

Visible callers use exactly two flag values:

- `0` is transient streaming. Input/raw storage is a `0x80`-aligned
  `0x10000 * 4` allocation at `+0x24`; the compressed decoded ring owns its
  own output backing. The orchestrator frees all transient transport state.
- `0x100` materializes retained data. Raw allocation is the sector file size
  rounded upward to a whole input chunk;
  gzip allocation is the GZLIST decompressed size, rounded to the output chunk
  size. The rings and `+0x24` survive until `FUN_001CF300` destroys transport
  state. That destructor deliberately does not destroy `+0x30`; downstream
  ownership has already transferred.

The ring constructor/configuration family is `FUN_001CA710`, `FUN_001CA8A0`,
`FUN_001CA8F0`, and `FUN_001CA920`; cleanup is `FUN_001CA9F0`. Descriptors are
`0x0C` bytes (`count`, data pointer, state). Ring byte `+0x31` distinguishes
owned from external data. External retained setup computes
`(total + chunk) / chunk`, intentionally reserving a sentinel descriptor when
the total is an exact multiple of the chunk size.

Retention allocation tests `flags == 0x100`, while transient cleanup tests
`(flags & 0x100) == 0`.
No mixed-bit caller was found. Allocation and open failures are not checked.

### Transport close, drain, and cancellation

The ring descriptor's state word at `+0x08` is 0 for an available/empty slot,
1 for an ordinary committed chunk, and 2 for the producer's final descriptor.
`FUN_001CAC10` obtains writable space, sleeping while a descriptor is occupied;
`FUN_001CADD0` advances the current write pointer. The following writable-space
request commits a full previous descriptor as state 1. `FUN_001CAB00` instead
commits the current partial descriptor as state 2, clears ring abort byte
`+0x32`, and wakes a waiting consumer. It finalizes a stream; it does not
destroy the ring or its buffer.

`FUN_001CADF0` drains/discards ordinary descriptors until it reaches state 2.
On reaching an empty descriptor before that terminator, it sets ring `+0x32`,
wakes a waiting producer, and sleeps until the producer supplies a descriptor.
`FUN_001CAAF0` reads that abort byte. Thus draining can stop a producer before
the remaining file has been read, but still waits for the producer's final
descriptor; a cancellation request is not an immediate file-handle close.
Retained ring mode leaves consumed descriptors intact, whereas transient mode
clears them for reuse. `FUN_001CAF70` releases the consumer's current span and
wakes a producer; it is neither ring destruction nor task termination.

The one-shot reader checks ring `+0x32` between chunk reads, then calls
`FUN_001CAB00` and sets wrapper read-completion byte `+0x2C`. It has no direct
wrapper-cancel test. For gzip, `FUN_001D0800` checks the destination ring's
abort byte between inflate blocks and returns `-1` when set. On that result,
`FUN_001D2100` finalizes the destination, drains/releases the source, frees
scratch output, and returns the partial produced count. This propagates a
consumer drain backward through gzip to the disc reader without treating the
partial count as a load-status error.

Wrapper cancel `FUN_001CF3D0` only sets wrapper `+0x28` and, if a container
already exists, its `+0xB0`. The decode worker skips parsing and drains its
ring when the wrapper byte was already set; parser cancellation and the
already-published-container case are owned by
[Loading and cancellation](ccs_runtime.md#loading-and-cancellation).
The coordinator still waits for read and decode completion before closing the
file. Its serialization byte becomes zero immediately after that close;
ordinary compressed cleanup waits for gzip completion afterward. Consequently
the gate does not cover the whole gzip-cleanup tail or retained-ring lifetime.

`FUN_001CF300` destroys nonzero rings, gzip object/task, and backing allocation,
but neither closes wrapper `+0x00` nor destroys downstream `+0x30`. It does
not clear the destroyed pointers. It is a one-use transport destructor reached
after orchestration, not a cancel, reset, or join operation. Ring cleanup
`FUN_001CA9F0` frees descriptors and owned backing without checking sleeping
producers or consumers. The task operation `FUN_001D01B0` sets termination mask
`0x0002` at task `+0x10` only when task `+0x12` bit 0 is clear and that mask
was not already set; a newly marked task sleeps if it is the caller.
The function contains no join or completion wait. Existing completion flags and caller ordering, rather
than the destructor itself, establish when transport can be freed.

### `ccUngzip`

`FUN_001D2430` constructs the `0x44`-byte `ccUngzip` object. The relevant
engine is:

- `FUN_001D1EC0`: gzip header parser;
- `FUN_001D20A0`: CRC32;
- `FUN_001D2100`: whole-stream decode;
- `FUN_001D2350`: input-byte fetch;
- `FUN_001D23C0`: source/destination ring link;
- `FUN_001D23D0`: destructor;
- `FUN_001D0800`: inflate driver.

The parser accepts normal `1F 8B` magic and a literal secondary `1F 1F`
comparison, requires compression method 8, reads MTIME, and handles FEXTRA,
FNAME, and FCOMMENT. It does not consume FHCRC and does not visibly reject
reserved flag bits. Invalid magic reaches an intentional null store; a
positive non-8 method reaches a no-op diagnostic callback.

Unless the destination ring is mode 2, decode allocates one output-chunk-sized
scratch buffer, commits output chunks to the destination, and frees the
scratch buffer on every normal or abort exit. It returns the produced-byte
count, but both resident callers ignore it.

After inflate, the engine reads the eight-byte gzip trailer and compares CRC32
and ISIZE with its computed values. All embedded error paths -- out of memory,
format violation, invalid method, CRC mismatch, and length mismatch -- call
`FUN_001D2480`, whose body is only `return`. The stream then closes and the
partial or corrupt produced-byte count is returned without a propagated
failure. GZLIST allocation size is not compared with produced length. Thus an
undersized corrupt GZLIST entry can make retained output capacity unsafe; this
last consequence is an inference, not a corrupt-file runtime test.

### Persistent three-task pipeline

`FUN_001CDAD0` initializes the persistent loader used by `FUN_001CE8A0`; its
destructor is `FUN_001CDE10`.
The object owns `PlayRead`, `PlayGzip`, and `PlayDecode` tasks, decoded/raw ring
at `+0x08`, compressed ring at `+0x48`, and resident `ccUngzip` at `+0x28C`.

Its request array has 16 entries of `0x14` bytes at object `+0x130`:

| Offset | Meaning |
| --- | --- |
| `+0x00` | path |
| `+0x04` | downstream/result pointer |
| `+0x08` | retention counter/type byte |
| `+0x0C` | flags |
| `+0x10` | decompressed-size sentinel: `-1` unknown, zero raw, nonzero gzip |

`FUN_001CDF40` opens the file at `0x001CE068`, performs the GZLIST lookup,
records sector size, and streams into the raw or compressed ring.
`FUN_001CE270` waits for the lookup result, skips raw entries, and decodes
compressed entries from `+0x48` into `+0x08`. A compressed-to-raw transition
waits for the gzip index to catch up, preventing the shared decoded ring from
interleaving entries. The persistent pipeline holds serialization byte
`0x006074E8` with value 2; the one-shot loader uses value 1.

`FUN_001CDE10` requests termination of all three tasks and tears down rings and
owned buffers. The task operation is a termination request, not a join; normal
orchestration separately waits for completion flags before teardown.

### `LoadBg` queue

The background queue consists of `FUN_001CF9E0` (enqueue), `FUN_001CFAE0`
(aggregate percent), `FUN_001CFB50` (worker), `FUN_001CFCD0` (start),
`FUN_001CFD70` (active predicate), and `FUN_001CFD90` (cleanup). Its globals
occupy `0x006074EC..0x00607500`; the task is named `LoadBg` and runs at priority
`0x73` with requested stack size `0x1000`.

Each `0x48`-byte FIFO node contains next pointer `+0x00`, path `+0x04`, flags
`+0x08`, 16-bit status `+0x0C`, pre-scanned sector bytes `+0x10`, and an
embedded one-shot state at `+0x14`. Status values are:

| Value | Meaning |
| ---: | --- |
| `0` | queued |
| `1` | one-shot loader running |
| `2` | loader returned |
| `3` | resource was already resident |

Duplicate paths are suppressed. The worker is asynchronous relative to its
caller but processes requests serially, marking status 2 unconditionally
because the one-shot loader has no failure result. Cancellation is checked
only between nodes.

The queue holds the caller's path pointer without copying it, and returns the
new node pointer or zero for an exact case-sensitive duplicate. The duplicate
search covers every linked node regardless of status, so it also suppresses a
repeat of a completed or already-resident request until cleanup. Its comparison
is separate from container lookup's normalized basename identity, owned by
[Resident CCS runtime](ccs_runtime.md#handle-layers). The worker does not
attach an already-resident container to the node: status 3 leaves embedded
result `+0x44` zero. Status 2 may have a newly
produced container there, but the worker does not check its publication.

Task `+0x28` identifies the current node only during the blocking one-shot
call, task `+0x2C` is the between-node stop field, and task `+0x30` selects
progress accounting. Completed nodes remain linked after global worker handle
`0x006074F4` is cleared. `FUN_001CFD70` therefore supplies a worker fence,
not a per-node status, successful-load predicate, or empty-queue predicate.
`FUN_001CFCD0` returns without starting another worker while this handle is
nonnull; it neither resets existing node statuses nor removes nodes.

The worker callback belongs to a `0x4C`-byte scheduler descriptor allocated
by `FUN_001D0090` and linked into the scheduler list. Constructor
`FUN_001CFE50` stores the entry function at descriptor `+0x0C`, initializes
callback argument `+0x20` and retirement callback `+0x24` to zero, and clears
the eight caller fields at `+0x28..+0x44`. Queue start supplies
`0x001CFB50`, replaces the descriptor name with `LoadBg`, and initializes
only its current-node, stop, and progress fields; it registers no queue
retirement callback. The sole resident reference to the worker entry is
that constructor argument at `0x001CFCF4` in the inspected 300-result query.
The constructor adds `0x400` to the requested stack size, allocates that
`0x1400`-byte backing, and records it at descriptor `+0x18/+0x1C` for thread
creation and eventual retirement.

On normal exit, worker instructions `0x001CFC9C..0x001CFCA8` save the task
pointer, clear the global worker handle, then call `FUN_001D01B0` with the
saved pointer. The scheduler later processes termination bit `0x0002` in
two passes: `FUN_001D0590` first adds `0x0004`, then unlinks the descriptor,
calls a nonnull `+0x24` callback, terminates/deletes its thread, and frees its
stack and descriptor. Thus queue inactivity precedes scheduler retirement;
the active predicate is not a thread join. In the registered queue path,
retirement releases only the task descriptor and stack. It does not walk
queue nodes or invoke `FUN_001CFD90`. Other code can obtain tasks through
the generic name lookup `FUN_001D0440`, but the inspected direct GP name
construction `20 82 ?? 27` reaches `LoadBg` only in queue start; no concrete
name-based queue stop or cleanup caller was established.

Optional pre-scan mode sums nonresident sector sizes. Reported progress is
`completed * 100 / total`, advances only after a whole request, returns `-1`
when total is zero, and is reset immediately when the worker exits; a durable
100 percent value is therefore not guaranteed. Normal cleanup preserves
registered downstream objects and frees only transport nodes. A dormant
alternate branch would delete downstream objects, but no nonzero writer for
its mode byte was found. The inspected fence callers observe the active
predicate before cleanup; cleanup itself has no active-task guard.

The cleanup mode byte is `0x006074F8` (`gp-0x34F8`). Starting a new worker
clears it at `0x001CFCEC`. Start argument 1 selects descriptor `+0x30` progress
accounting; it does not select result deletion. An already nonnull worker
handle returns before that zero store. Thus this entry supplies no way to
enable the alternate cleanup branch. The stop field is checked only by the
worker between one-shot calls; this family has no proven public
cancel-current-node API.

#### Queue-global writes and rebasing bounds

Only two stores write the cleanup mode byte `0x006074F8`, both zero: the
boot `entry` clear of `0x00607380..0x008DD080` in 16-byte steps
(`sq zero,0(v0)` at `0x00100160`, which also initializes the other queue
globals before GP setup), and the worker-start byte store at `0x001CFCEC`.
No nonzero writer was found. The search covered every aligned resident GP
store of each width in the `CAxx`/`CBxx` displacement pages, GP-based
address constructions and `lui register,0x60` sequences, literal and exact
mode-pointer bytes in the resident ELF, BTL and ETC, and BTL/ETC stores. The
queue-range word writes are confined to enqueue, worker, start, and cleanup:

| Global | Confirmed word-write role |
| --- | --- |
| `0x006074EC` | Enqueue installs the first node; cleanup clears the head |
| `0x006074F0` | Enqueue updates the tail; cleanup clears it |
| `0x006074F4` | Start publishes the worker descriptor; worker exit clears it |
| `0x006074FC` | Worker initializes, accumulates, and clears total bytes |
| `0x00607500` | Worker initializes, accumulates, and clears completed bytes |

The eight resident loads of the worker handle all lie inside the queue family
(none in BTL/ETC) and identify no separate handle-based stop writer.
These searches do not trace register copies, distant continuations, general
memory-clear callers, computed pointers or aliases, so a nonzero writer and
retail admission to result-deleting cleanup remain unproven rather than
excluded.

Normal `FUN_001CFD90` clears result `+0x44`, destroys only embedded transport,
then frees the outer node. Its alternate mode destroys a nonzero result first.
Neither branch checks status or worker activity, and cleanup resets head and
tail only after walking the entire list. It does not stop the worker or wait
for the active one-shot load. Callers must reach the inactive fence before
freeing nodes; the destructor cannot enforce that ordering.

Resident battle fence `FUN_001EDA50` observes an inactive `FUN_001CFD70`
before queue cleanup and then adopts both sides' published containers, as
recorded under
[Adoption and cache reset](asset_dependencies.md#adoption-and-cache-reset);
battle ordering belongs to
[Battle lifecycle](../../gameplay/battle_lifecycle.md#resident-setup-order).

## Useful negative results

- Startup does not eagerly read or decompress all CCS payloads.
- The GZLIST compressed-size column is not used by the resident parser.
- The GZLIST directory tree does not case-fold path components.
- Resident startup retries mount failures; resident open does not return a
  recoverable error.
- No consumer of the dynamically allocated root-node directory buffer is
  currently proven.
- Gzip format, CRC, ISIZE, and inflate-memory diagnostics do not propagate a
  load failure.
- `LoadBg` does not parallelize requests and has no failure status or retry.
