# Resident file and archive services

Static evidence for the resident file-location cache, ROFS mount and directory
index, `GZLIST.TXT`, resource-path routing, sector I/O wrappers, and the
memory-card use of `ICON.BIN`.

The trace uses clean NA2 `SLPS_258.37`, size 5,273,256 bytes and SHA-256
`20C0A40D70EA412CD431993A2E189B37ECB6054D63AE93BE545470016E1627AF`,
through the maintained Ghidra 12.1.2 exports. Its GP is `0x0060A9F0`.
The clean extracted `FLIST.DIR`, `GZLIST.TXT`, and `ICON.BIN` were checked
directly. Findings below are static unless stated otherwise.

## Research coverage

- **Assigned scope:** the resident file/archive layer outside CCS object
parsing: `FLIST.DIR` location caching, `DATA.CVM`/ROFS startup, `GZLIST.TXT`,
logical and explicit path routing, sector reads, gzip transport, and resident
background loading. The memory-card use of `ICON.BIN` was followed only far
enough to establish its file contract.

- **Exploration depth:** coverage is exhaustive within the named fixed parsers, tables, and direct
resident service families. The complete 40-slot FLIST layout and all eight
clean entries were checked; all 21 GZLIST directory records and 2,332 listed
children were accounted for; the ROFS root and recursive child-directory
loads were traced; and the open/read/seek/size wrappers, one-shot loader,
`ccUngzip`, persistent 16-entry pipeline, and FIFO `LoadBg` queue were followed
through allocation, completion, cleanup, and visible failure branches. Clean
file sizes, hashes, padding, and fixed capacities were verified directly.

- **Confirmed coverage:** the fixed FLIST/GZLIST layouts, ROFS startup and
  directory-preload behavior, path-routing split, sector-I/O contract, gzip
  transport, persistent pipeline, background queue, and `ICON.BIN` save-icon
  role are documented from those checks.
- **Unresolved or untested:** the exact vendor names of several ADXF/ROFS wrappers, lower I/O status names,
the purpose of the dynamically allocated GZLIST root buffer, the secondary
gzip magic, and reachability of the dormant background-cleanup mode remain
unresolved. Indirect callers outside the documented families were not
exhaustively classified.
- **Deliberate exclusions and overlap:** CCS payload semantics, overlay
  selection, Adventure, and general save/load behavior were deliberately
  excluded.
- **Evidence limitations:** no corrupt-file, short-read, allocation-failure,
cancellation-race, or runtime mount/load experiment was performed, so failure
and concurrency conclusions are static.

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
slash style. The clean 124-byte file has SHA-256
`4F500B226613858648E2502F04FA84E04D3420DBE066B86E019EC7E10E90AA0C` and
eight lines, leaving 32 unused table slots. More than 40 lines are not parsed.
A name longer than 32 characters is not rejected before copying and can cross
the reserved per-name stride, so the spare capacity does not make long entries
safe.

`FLIST.DIR` remains a location cache rather than an authoritative file list.
The separate explicit-device route described below can open files that are not
listed.

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
103,848 bytes with SHA-256
`40912F3C8999BCC7754757271CFF35F8C22FB9797EE5D008B10AB60FE48B97CE`.

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

An unprefixed path takes the logical route. `FUN_001BDFB0` separates the final
component, `FUN_001BCD60` finds a preloaded directory handle, and the leaf name
is opened relative to that handle. A leading slash begins at fixed root handle
`0x0061B7F0`; a plain filename uses handle zero.

An explicit host or disc prefix is rewritten to the selected spelling and
passed as a complete path to `FUN_0012ACB0` with handle zero. This bypasses the
GZLIST directory cache and is the clean route when cached directory case or
membership is unsuitable.

Both routes treat open failure as fatal: the wrapper stores through address
zero and retries rather than returning a recoverable error. Mods should not
use this API for an optional file unless they establish existence separately.

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

## `ICON.BIN` memory-card role

`FUN_001C1C50` copies the CVM member `icon.bin` into each PS2 save directory as
`icon00.icn`. Its one-record table supplies source offset zero, payload length
`0xE920`, and destination name `icon00.icn`. The function opens the source
through `FUN_001BE450`, reads the sector-rounded `0xF000` bytes, opens the
memory-card destination with mode `0x203`, writes exactly `0xE920`, and closes
it.

The clean source is 61,440 bytes (`0xF000`) with SHA-256
`80D7F62704FC9F59DEF83ED8AF68C0A26609215C2C398F2CA2EBBB99057CF017`.
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
- `0x100` materializes retained data. Raw allocation is the sector file size;
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

The flag contract is exact rather than bitwise throughout: allocation tests
`flags == 0x100`, while transient cleanup tests `(flags & 0x100) == 0`.
No mixed-bit caller was found. Allocation and open failures are not checked.

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
`0x73` with a `0x1000` stack.

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

Optional pre-scan mode sums nonresident sector sizes. Reported progress is
`completed * 100 / total`, advances only after a whole request, returns `-1`
when total is zero, and is reset immediately when the worker exits; a durable
100 percent value is therefore not guaranteed. Normal cleanup preserves
registered downstream objects and frees only transport nodes. A dormant
alternate branch would delete downstream objects, but no writer for its mode
byte was found. Callers observe the active predicate before cleanup; cleanup
itself has no active-task guard.

## Useful negative results

- Startup does not eagerly read or decompress all CCS payloads.
- The GZLIST compressed-size column is not used by the resident parser.
- The GZLIST directory tree does not case-fold path components.
- Generic open and mount failures do not produce a recoverable return path.
- No consumer of the dynamically allocated root-node directory buffer is
  currently proven.
- Gzip format, CRC, ISIZE, and inflate-memory diagnostics do not propagate a
  load failure.
- `LoadBg` does not parallelize requests and has no failure status or retry.
