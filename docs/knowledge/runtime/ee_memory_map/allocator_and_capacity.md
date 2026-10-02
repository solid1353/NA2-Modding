# EE allocator

Static and runtime findings for the retail NA2 (`SLPS-25837`) EE allocator.

Resident addresses below refer to retail NA2 `SLPS_258.37`. Complete-file
identities and overlay address conventions are owned by
[Retail game file identities](../../game/files/file_identities.md#address-conventions).

## Research coverage

- **Assigned scope:** identify the allocator's initialization, metadata, linked
  structure, placement policy, entry points, counters, free-space measures,
  secondary pools, load-time costs, and sampled retail capacity.
- **Exploration depth:** the startup code, the system `sbrk`/`malloc` layer,
  heap initialization, every resident allocator entry point, the free, resize,
  and deferred-free paths, the placement-direction scopes, the resident file
  directory, the CCS load pipeline's allocations, and CCS texture storage were
  traced statically. Allocation call sites were enumerated by `jal` encoding
  across the ELF and the battle/menu overlays. Static analysis also covered
  all 32 non-image object/control routes in `FUN_001AC8A0`, directory
  sorting, dependency finalization, and the four reachable model-part parser
  families, inflate tables, texture/palette variants, and peak-counter writes.
  It establishes direct requests and lifetimes, rather than whole-file totals
  for the retail corpus. Complete linked-list walks were checked in the six
  sampled retail states listed under
  [Sampled retail capacity](#sampled-retail-capacity).
- **Confirmed coverage:** arena bounds, sentinels, globals, node format, flag
  bits, the two-ended placement policy and its per-thread scopes, deferred
  free, accounting behavior, the 2 MiB per-frame pool, the resident file
  directory, CCS transport costs, directory expansion and sorting scratch,
  non-image allocation formulas and discarded directives, model conversion
  overlaps, texture/palette storage, variable inflate scratch, and sampled
  retail free-space measurements are established. Decompressed length is not a fixed
  resident-cost multiplier; the tracked peak is not a battle-load measurement.
- **Unresolved or untested:** per-asset allocation totals from a retail heap
  walk (which nodes belong to the stage, each fighter, the HUD, and effects),
  complete per-file totals and actual model conversion counts across the retail
  corpus, later scene-instance costs, and the retail peak during a battle load.
- **Deliberate exclusions and overlap:** CCS parsing and container ownership belong to
  [Resident CCS runtime](../../game/files/ccs_runtime.md); task records and
  thread stacks belong to [Task system](../task_system.md).
- **Evidence limitations:** capacity values describe sampled states, not a
  guaranteed lower bound for every game state or allocation sequence. No
  identified allocation/lifetime trace separates the battle load or attributes
  live nodes to individual assets. The cost formulas below are static; the
  end-state samples do not measure their load-time overlaps.

## System memory layer

The startup entry at `0x00100008` zero-fills `0x00607380..0x008DD080`, which is
the ELF's full zero-filled range including the overlay window. It then calls
kernel `InitMainThread` (syscall `0x3C`) with `gp = 0x0060A9F0`, stack `-1`, and
stack size `0x8000`, and kernel `InitHeap` (syscall `0x3D`) with heap start
`0x008DD080` and size `-1`.

The `sbrk` routine at `0x0015E3E0` keeps its break in `0x003F78F4`, whose
initial value is `0x008DD080`, and refuses growth beyond kernel `EndOfHeap()`.
The only `malloc` wrapper, `FUN_00179850`, serializes the newlib-style
`_malloc_r` (`FUN_00179B48`) with a semaphore. It has two callers:

- `FUN_00118730`, which obtains the game arena once at startup; and
- `FUN_00379FE0`, a text-draw routine that copies strings of `0x200` bytes or
  more into a temporary `malloc` block and frees it after drawing. Shorter
  strings use the resident `0x200`-byte buffer at `0x006B3B00`.

**Inference (high confidence):** With stack `-1`, the kernel places the
`0x8000`-byte main-thread stack at the top of the 32 MiB RAM, at
`0x01FF8000..0x02000000`, and `EndOfHeap()` returns that stack base. The game
arena request of `0x1718F70` bytes succeeds at the first attempt: the first
`malloc` chunk begins at the initial break, its user pointer is `0x008DD088`,
and 16-byte alignment gives the documented base sentinel `0x008DD090`. The
arena therefore ends at `0x01FF6000`, leaving `0x01FF6000..0x01FF8000` to the
`malloc` layer for its own top chunk and later `malloc` calls.

## Allocator model

`FUN_00118730`, called from the main routine `FUN_001C13F0`, requests
`0x1718F70` bytes from `malloc` and backs the request down in `0x100` steps
until it succeeds. It aligns the returned base, installs two 16-byte sentinels,
initializes two free-bin structures, caches the largest free gap, and clears
the placement-scope list.

| Address | `gp` offset | Meaning |
| ---: | ---: | --- |
| `0x00607380` | `-0x3670` | low-placement boundary; initialized to the first user address and lowered only when the topmost low block is freed or shrunk |
| `0x00607384` | `-0x366C` | high-placement boundary; initialized to the end sentinel and raised only when the lowest high block is freed |
| `0x00607388` | `-0x3668` | current tracked bytes |
| `0x0060738C` | `-0x3664` | peak tracked bytes |
| `0x00607390` | `-0x3660` | live allocation count |
| `0x00607394` | `-0x365C` | deferred-free list head |
| `0x00607398` | | base sentinel |
| `0x0060739C` | | end sentinel |
| `0x006073A0` | `-0x3650` | cached predecessor of the largest gap |
| `0x006073A4` | `-0x364C` | cached largest-gap size |
| `0x006073A8` | `-0x3648` | per-thread placement-scope list head |
| `0x006073AC` | `-0x3644` | one-shot placement byte |

No resident or overlay instruction reads the two boundary words except the
free and resize routines that maintain them, so they do not limit allocation.

Each allocated node has a 16-byte header containing the previous node, next
node, aligned allocation size, and a flags byte. `FUN_001180D0(alignment,
size, flags)` rounds a request plus its header to 16 bytes. Two segregated-bin
families serve gaps below `0x1000` in 16-byte size classes; a general ordered
list serves larger gaps, with fallback to the cached largest gap.

Each indexed free gap stores its next link, previous link, gap size, and
preceding allocated node in the first 16 bytes of the gap. The general-list
sentinels are `0x00608350` for the first bin family and `0x00608B60` for the
second. `FUN_00118B20` follows the selected sentinel's next links until it
finds a gap large enough for the request.

### Flags and placement

| Flags bits | Meaning |
| --- | --- |
| `0x3` | Placement class. `0` places the block at the low end of the chosen gap and indexes leftover gaps in the `0x00607B50` family; `1` places it at the high end of the gap and uses the `0x00608360` family. |
| `0x4` | Untracked: the block is excluded from the tracked-byte counters. |
| `0x8` | Nullable: failure returns zero. Without it, `FUN_001180D0` executes a trap on failure. |
| `0xF0` | Deferred-free countdown, used only while the block is on the deferred-free list. |

The ordinary flag values are therefore `0` low trapping, `1` high trapping,
`8` low nullable, and `9` high nullable.

Placement comes from a per-thread scope list at `0x006073A8`. `FUN_00118F40`
pushes a 16-byte stack record carrying the current thread ID and a direction;
`FUN_00118EE0` removes it; `FUN_00118E60` returns the current thread's
innermost direction or `3` when it has none. Only two resident scopes exist:

| Scope | Direction | Covered work |
| --- | ---: | --- |
| `FUN_001CF3F0` | 0, low | CCS file-load coordinator: transport buffers, readers, and worker records |
| `FUN_001A9060` | 1, high | CCS container parsing on the decode worker thread |

Without a scope, the default entry points consume the one-shot byte at
`0x006073AC`, clearing it on every call; a nonzero value selects high placement.
Resident code sets it before selected allocations; the direct-writer census
found no writer in `BTL.BIN` or `ETC.BIN`.

**Observation:** CCS parsing requests high placement, while the transport
coordinator requests low placement. The container descriptor is allocated
before the parser's high scope. Fallback can place a block on the opposite
side, so the scopes establish a preference rather than a guarantee that all
container-related blocks occupy one end.

### Entry points

| Function | Arguments | Direction choice | Try, then fallback | Calls (ELF/BTL/ETC) |
| --- | --- | --- | --- | ---: |
| `FUN_00117030` | size | scope, else one-shot byte | preferred side nullable, other side trapping | 117/52/1 |
| `FUN_00117150` | size | same as `FUN_00117030` | same | 933/863/147 |
| `FUN_00117500` | size | scope only; none selects high | preferred side nullable, other side trapping | 7/0/0 |
| `FUN_00117270` | alignment, size | scope only; none selects high | same | 6/0/0 |
| `FUN_00117370` | alignment, size | scope `1` selects high, otherwise low | same | 25/0/0 |
| `FUN_00117700` | size | same as `FUN_00117370` | same | 126/20/0 |
| `FUN_00117600` | size | same as `FUN_00117370` | both sides nullable; may return zero | 12/0/0 |
| `FUN_00117470` | size | always low first | low untracked nullable, then high untracked trapping | 1/0/0 |

Frees use `FUN_00117C40`, directly or through the one-instruction wrapper
`FUN_00117000` (740/666/97 ELF/BTL/ETC calls). A free unlinks the node, merges the
neighbouring gaps into its predecessor's gap, and reindexes that gap in the
family matching the freed block's class.

`FUN_00117800(pointer, size)` changes a block's recorded size in place and
reindexes the following gap. It does not check that growth fits. Its only call
site, animation construction `FUN_001A29D0`, sets the block's size to the end
of the parsed track data. `FUN_00117BB0(pointer, frames)` queues a block for
deferred release; the frame routine `FUN_00108490` calls `FUN_00117AD0`, which
decrements every queued countdown and frees blocks that reach zero. The only
deferred-free caller is `FUN_00110AB0`.

Complete list walks in every sampled state established that:

- forward and backward links are consistent and acyclic;
- the walked node count equals `0x00607390`;
- walked tracked bytes equal `0x00607388`;
- the cached largest gap and predecessor match the computed maximum;
- one flag-12 allocation of `0x10010` bytes is excluded from tracked bytes.

The flag-12 block is the `0x10000`-byte buffer that `FUN_001114A0` obtains
through `FUN_00117470`, the only untracked allocation site.

The tracked peak is initialized to zero at `0x0011885C` and updated by the
core allocator at `0x0011853C..0x00118564` after adding a tracked node's
recorded bytes to the current total. A direct `gp`-relative store scan of
the resident ELF, `BTL.BIN`, and `ETC.BIN` found only those two writers;
the resident aliases contain copies of the same instructions. This scan
does not exclude an indirect write. Resize `FUN_00117800` changes current
tracked bytes at `0x00117A64..0x00117A74` without updating the peak.
The peak therefore records allocation high-water history since arena
initialization, excludes untracked nodes and remaining free gaps, and has
no battle-load reset in the inspected direct-writer paths.

`total_free` is the sum of gaps between live nodes. `largest_free` is the
largest single gap and therefore the limit for one ordinary allocation.
`fragmentation_bytes` is `total_free - largest_free`.

## Resident secondary pool

During display initialization, `FUN_00107F80` allocates a `0x14`-byte pool
descriptor and `FUN_00110B30` gives it a `0x200000`-byte block from
`FUN_00117700`. The descriptor is stored at display object `+0x1C8` and linked
into the pool list at `0x006073B4`. `FUN_001104A0` serves first-fit requests
from the pools on that list for about 36 resident renderer routines. The frame
routine `FUN_001081B0` calls `FUN_00106500`, whose final step `FUN_00110770`
releases the frame's pool entries.

**Observation:** This 2 MiB block is allocated once at startup and remains
live. It is unavailable to the general arena in every mode.

## Resident file directory

`FUN_001BDA50`, called from front-end startup `FUN_001E0EE0`, reads
`gzlist.txt` whole into a `FUN_00117270` block and parses it. For each of its
21 directories it allocates a table of `(files + 4) * 0x30 + 0x18` bytes
through `FUN_00117700`, and for each file it stores the listed decompressed
size at directory-entry `+0x24`. A zero size takes the null-store failure path.
The routine frees only its `0x12C`-byte parse record; it advances the text
pointer while parsing and never frees the text block.

**Observation:** The retail list is `0x195A8` bytes. Its header declares 21
directories with 2,332 file slots, so this directory permanently holds about
`0x195C0` bytes of text plus `0x1C6F8` bytes of tables, about 216 KiB, before
per-directory node overhead. Its 2,310 file rows each match the extracted
file's compressed size and gzip-trailer decompressed size. With no
placement scope active, the text block goes to the high end and the tables to
the low end.

`FUN_001BE9B0` returns an entry's `+0x24` value to the load coordinator. It is
the decompressed size, so a nonzero value selects the gzip path and sizes the
whole-file buffer of a flags-`0x100` load. `FUN_001BCA00` resolves a path
through this directory and takes the null-store failure path for a directory
or file it does not list.

## CCS load cost

`FUN_001CF3F0` opens the file, pushes a low-placement scope, and allocates its
buffers according to the file-list metadata and flags:

| Path | Transient allocations |
| --- | --- |
| Uncompressed, flags `0` | one `0x40000`-byte transport ring (four `0x10000` blocks, alignment `0x80`) and a `0x40`-byte reader |
| Compressed, flags `0` | a `0x40000`-byte input ring, a `0x40000`-byte output ring, a `0x10000`-byte decompression block, two readers, a `0x44`-byte bridge, and the `LoadGzip` task with a `0x10400`-byte stack |
| Flags `0x100` | a buffer for the whole file, or for the whole decompressed size plus a `0x40000`-byte input ring when compressed, rounded up to whole blocks; retained until the owner releases the wrapper |

Every path also starts `LoadRead` and `LoadDecode` tasks with `0x1400`-byte
stacks and `0x4C`-byte records. With flags `0`, the coordinator frees the
transport buffer and the parser-facing reader with its ring once reading and
decoding finish. On the compressed path it then waits for the gzip worker and
destroys the input reader before returning.

Every retail CCS file in `DATA.CVM` is gzip-compressed and listed with a
nonzero decompressed size in the [resident file directory](#resident-file-directory),
which rejects zero sizes and unlisted paths. **Inference (high confidence):**
retail loads always take the compressed path.

**Observation:** The ordinary compressed path's two rings, decompression
block, and three worker stacks request `0xA2C00` payload bytes: roughly
`0xA3000` bytes (650 KiB) before the smaller records, node headers, alignment
gaps, and variable inflate tables. This is a fixed-buffer subtotal, not the
complete transient requirement. The decompression block size is read from
the output ring's block size, `0x10000` on this path. With flags `0`, the file
is streamed rather than held whole. Parsing builds the retained allocations
described below.

`FUN_001CA920` additionally allocates one `0xC * block_count` descriptor
array per ring, aligned to `0x80`; an ordinary four-block ring therefore adds
a `0x30`-byte request. These arrays are distinct from each ring's byte buffer.

Inflate table builder `FUN_001D1830` allocates each Huffman subtable through
`FUN_00117700` with request `8 * (2^k + 1)`, where `k` is the subtable's
selected bit width. Instructions `0x001D1B58..0x001D1B68` construct that
request; the extra eight bytes hold the table-list prefix.
`FUN_001D17E0` follows the prefix links and frees every table block. The
dynamic-block decoder `FUN_001D09E0` first builds and frees a code-length
table, then holds the literal/length and distance tables together while
decoding. The fixed-block decoder `FUN_001D1010` also builds and frees its
two tables for each block. Their heap cost is additional to the worker stack
and varies with the compressed block's codes; the code-length work arrays
are already inside that stack.

Decompressed sizes establish the input scale, not resident allocation totals.
The directory alone expands every file record and allocates additional hash
storage, as shown below. Texture pixel data is separately copied into decoded
storage; other type-specific costs and the whole-file total need their own
accounting. Retail decompressed sizes from the resident file directory are:

| Family | Files | Decompressed median | Decompressed maximum |
| --- | ---: | ---: | ---: |
| `STAGE/S??.CCS` | 24 | `0x119CFA` | `0x143334` |
| `PL/1???BOD1.CCS` | 86 | `0x082742` | `0x0AA0EC` |
| `PL/2???BOD1.CCS` | 149 | `0x07C410` | `0x1AF14C` |
| `PL/2???CHA0.CCS` | 76 | `0x036EE0` | `0x065A7C` |
| `PL/2???CHA1.CCS` | 77 | `0x01BEE8` | `0x060A30` |
| `3EYE/3???3PCT.CCS` | 78 | `0x00CF0C` | `0x01018C` |
| `3EYE/3???3EYE.CCS` | 78 | `0x0119E0` | `0x08DA78` |
| `CMN/*.CCS` | 6 | `0x037AC4` | `0x1693DC` |

### Directory and finalization cost

For an ordinary 16-byte-aligned allocation, define
`Q(n) = (n + 0x1F) & ~0xF`. `FUN_001180D0` records this many bytes, including
the 16-byte node header; even a zero-byte request records `0x10` bytes.
Higher requested alignment can leave additional free gaps, so `Q` describes
node bytes rather than a fragmentation allowance.

Let `F` be the namespace count and `N` the object-record count read by
`FUN_001AC6C0`. The fixed retained container/directory node cost is:

```text
Q(0xC0) + Q(0x20 * F) + Q(0x38 * N) + Q(4 * N)
```

`FUN_001CF210` allocates the container before entering `FUN_001A9060`'s
high-placement scope. The other three blocks are namespace strings, records,
and hash buckets. A file record occupies `0x20` bytes in the stream but `0x38`
bytes in the directory and another 4 bytes in the hash table: `0x1C` extra
payload bytes per record before node headers and rounding. Namespace rows
retain their original `0x20`-byte width. A caller-created owned reader adds
`Q(0x40)`; an ordinary load borrows its transport reader, whose cost belongs
to the transient pipeline instead. Container ownership is described in
[Resident CCS runtime](../../game/files/ccs_runtime.md#ccs-memory).

`FUN_001ACDB0` first allocates two temporary `4 * N` arrays. For `N > 2`, its
sort helper `FUN_001AC420` additionally allocates `8 * N` bytes, split into
two word arrays. During sorting, the extra node cost is therefore
`2 * Q(4 * N) + Q(8 * N)`; the hash bucket block has not yet been allocated.
The helper frees its scratch block before the finalizer allocates the retained
`4 * N` hash buckets. At that later point the two `4 * N` temporary arrays
still overlap the buckets; the finalizer then frees both temporaries before
dependency finalization. These are two different transient phases, not four
simultaneously retained arrays.

**Observation:** Directory expansion and sort scratch depend on record count,
which decompressed byte length alone does not reveal. Adding only the
fixed-buffer subtotal to the final container cost omits inflate tables,
this parse-time scratch, and conversion overlaps, and does not establish
the load's peak.

### Non-image objects and discarded data

The following costs are additional to the container/directory blocks. `Q` is
the node cost defined above. These are allocation consequences of the resident
parsers, not recovered class names; tag identities and payload layouts belong
to [Resident CCS object-type identities](../../game/files/ccs_object_types.md).
For conditional constructors, the row applies when a new object is built;
reusing an already constructed record does not incur that request again.

| File tag | Node cost or direct request | Evidence and lifetime |
| ---: | --- | --- |
| `0x0100` | `Q(0x24)` | `FUN_001B2670`; replaces and frees a preceding `0x2000` placeholder. |
| `0x0200` | `Q(0x18) + Q(0x1C)` | `FUN_001B3450` constructs the descriptor; `FUN_001AD9C0` adds its secondary object during finalization. |
| `0x0500` | `Q(8)` | `FUN_001B35B0`; camera materialization is later and separate. |
| `0x0600` | `Q(0xC)` plus `Q(0xE0)`, `Q(0x160)`, `Q(0x160)`, or `Q(0xD0)` for selector 1, 2, 3, or 4 | `FUN_001B3600` and finalizer `FUN_0019B240`; an unknown selector produces no secondary. The constructors initialize inline state without further allocations. |
| `0x0A00` | `Q(0x20)` | `FUN_001B2800`; replaces and frees a preceding `0x2000` placeholder. |
| `0x0C00` | `Q(0x40)` while parsing; zero retained block | `FUN_001ADBF0`; `FUN_001AD240` applies the directive, clears its record pointer, and frees the block. |
| `0x0D00` | `Q(0xC)` | `FUN_001B1890`. |
| `0x1300`, `0x1400` | `Q(0x20)`, `Q(0x30)` respectively | `FUN_001B36A0`, `FUN_001B3730`; their stream payloads are only `0x10` and `0x1C` bytes. |
| `0x1800` | `Q(0x18)` for a new explicit record | `FUN_001B1FF0`; record ID zero updates an existing default descriptor instead. Later play-object materialization is separate from this resource block. |
| `0x1900` | `Q(8)` | `FUN_001B2190`. |
| `0x1A00`, `0x1B00`, `0x1C00` | `Q(0x10)` each | `FUN_001B4600`, `FUN_001B4820`, `FUN_001B4920`. |
| `0x1D00` | `Q(8)` | `FUN_001B4A20`. |
| `0x2000` | `Q(0x14)` only for a not-yet-typed record | `FUN_001B2510`; existing `0x0100`, `0x0A00`, or `0x0E00` objects are updated in place. |
| `0x0003`, `0x1000`, `0x1100`, `0x1200` | no new object block | `FUN_001ADA90`, `FUN_001ADB70`, `FUN_001ADB20`, `FUN_001ADAA0`. The latter three consume their payloads without retaining them; `0x1000` consumes `8 + 4 * count` bytes and `0x1200` consumes `8 + 8 * count` bytes. |

Counted and length-driven routes add these costs:

| File tag | Cost variables and allocation consequence | Evidence |
| ---: | --- | --- |
| `0x0700` | Initial request `0x2C + 4 * W`, where `W` is the declared track-word budget. After parsing, resize records `Q(A(end - start))`, with `A(n) = (n + 0xF) & ~0xF`; two retained index blocks add `Q(8 * R) + Q(2 * R)` for the collected reference count `R`. | `FUN_001B1470`, `FUN_001A29D0`, `FUN_00117800`. The initially larger block can affect the peak even though it is later shrunk. |
| `0x0800` | For nonzero part count `P`, a model requests `0x60 + 0x40 * P`. A nonzero header byte-table count additionally requests `0x40`, independent of that count. Per-part geometry and generated packets are additional. | `FUN_001B0C40`; part families are discussed below. |
| `0x0900` | For child count `C`, the initial block is `Q(A(0x1C) + A(4 * C) + A(0x30 * C))`. Retained dependency groups add `Q(2 * C)` during finalization. | `FUN_001B1560`, rounding helper `FUN_001AF100`, `FUN_001AD240`. The special first-child `0x0E00` path clears the record and frees this provisional block through `FUN_001A9450`. |
| `0x0B00` | For a nonzero group count, `Q(0x10) + Q(0x40 + 0xA0 * T)`, where `T` is the header's total vertex count divided by 3. | `FUN_001B3040`; allocation operands at `0x001B30B4..0x001B313C` and per-triangle stride `0xA0` at `0x001B32EC` were checked in disassembly. |
| `0x0D80` | `Q(B + 4 + 4 * K)`, where `B` is the header length in bytes and `K` is the packet count. | `FUN_001B1920`; `0x14`-byte file packet descriptors become `0x18`-byte runtime descriptors. |
| `0x0D90` | `Q(0x70 + 0x30 * U + 0xC * V)`, where `U` is the low nibble of payload byte `+0xA` and `V` is the high nibble of byte `+9`. | `FUN_001B1B30`; the parser frees this block and clears its record pointer when `V` is zero. |
| `0x0E00` | `Q(0x34 + 8 * C)`, where `C` is the halfword count at payload `+0xE`. | `FUN_001B2E50`; replaces and frees a preceding `0x2000` placeholder. The descriptor expands the `0x24`-byte file header by `0x10` bytes and retains the eight-byte rows. |
| `0x1700` | Temporary `Q(8 * rows)`, retained `Q(0x10)` root, and individual `Q(8)` or `Q(0x18)` controller descriptors, including missing default slots. | `FUN_001B2220`; the temporary row table is freed on return. An already constructed extended descriptor is reused. Root constructor `FUN_001B20F0` adds no allocation. |
| `0x1F00` | Temporary `Q(B)` plus the exact converted allocation `Q(output_size)`; both are live during conversion. | `FUN_001B2930`; the input block is freed before return. Its nested count/packing rules are owned by the object-type document. |
| `0x2200` | No new parser-owned object block; payload is copied into an existing ring manager or consumed and discarded when no ring slot is available. | `FUN_001B44B0`; manager lookup `FUN_001B45E0` and slot acquisition `FUN_001090C0` are separate from CCS object allocation. |
| `0x2300` | Temporary `Q(B)` input blocks persist until dependency finalization. A resolved target adds `Q(0xC)` and, for nonzero source counts `U`/`V`, `Q(0x10 * U)` / `Q(0x1C * V)`. | `FUN_001B4B40`, `FUN_001AD240`; arrays are allocated for the source counts, even when only a smaller subset resolves. Input blocks are then freed; pointer-vector capacity is accounted for below. |
| `0x2400` | `Q(B + 4)`; the retained blob has `B - 4` data bytes after an eight-byte descriptor. | `FUN_001B4BC0`; the first four file bytes are the record ID. |

`B` above is four times the block-header length dword. Dispatcher instructions
`0x001AC910..0x001AC924` read that word and place its byte length in `a1`;
the calls at `0x001ACC88`, `0x001ACCA8`, `0x001ACCB8`, and `0x001ACCC8`
preserve it into the `0x1F00`, `0x0D80`, `0x2300`, and `0x2400` handlers.
These handlers use it for their requests even though other parsers consume
payloads according to their own count fields.

For `G > 0` blocks of type `0x2300`, the container's pointer vector at
`+0x6C` additionally retains `Q(4 * K)`, where `K` is the smallest power of
two at least `G`. Constructor `FUN_001AA640` initializes the vector through
`FUN_001AA690..FUN_001AA7B0` with zero capacity, length, and data pointer.
Append `FUN_001AA970` calls `FUN_0019F850`, which grows capacity from 1 by
doubling and allocates the new backing block before freeing the old one.
During growth, both backing blocks therefore overlap the input blocks.
After freeing each input, `FUN_001AD240` calls `FUN_001A9C60`, which clears
only the vector length at `+4`; it does not release the capacity block.
For `G == 0`, this vector has no backing allocation.

The `0x1800` resource illustrates the distinction between parsing and play
materialization. `FUN_001A0B80` requests a primary `Q(0x180)` play block
and calls `FUN_0018B570`. Its ordered-controller initializer
`FUN_0010A1D0` borrows the supplied render-environment pointer, or requests
`Q(0x2B0)` and invokes `FUN_0010F2E0` when that pointer is zero. These are
later costs, separate from the parser's `Q(0x18)` descriptor; the primary
request alone does not establish all nested environment or scene costs.
The controller's behavior is owned by
[the object-type document](../../game/files/ccs_object_types.md#0x1800-descriptor-fields-and-off-screen-pass).

**Observation:** Non-texture storage can expand, contract, or disappear during
finalization. For example, `0x0B00` consumes two sets of three 3D points per
triangle (`0x48` bytes), builds a `0xA0`-byte runtime triangle, and retains only
the processed representation; the second point set is consumed without being
retained. Conversely, the file-block `0x1000` payload creates no object block.
Thus no single decompressed-to-resident ratio follows from the parser. The
allocation sum requires actual type/count/flag data and the relevant lifetime.

### Model-part allocation and conversion

`FUN_001B0C40` dispatches model parts by `(file_flags >> 1) & 7` to four
parser families: 0 to `FUN_001B0790`, 2 to `FUN_001AFF20`, 3 to
`FUN_001ADD80`, and 4 to `FUN_0018D740`. Their costs below are additional to
the model's `Q(0x60 + 0x40 * part_count)` block. Let `V` be the part's
vertex count, `E` its count at `+0x2C`, `f` the flags supplied to the part
parser, and `A(n) = (n + 0xF) & ~0xF`.

| Family | Retained allocations |
| --- | --- |
| 0 | Vertex-marker block `Q(A(V))` at part `+0x24`, positions `Q(A(6 * V))` at `+0x14`, and conditional four-byte-per-vertex blocks at `+0x18`, `+0x1C`, and `+0x20`, plus a generated packet at `+0x10`. |
| 3 | When `E == 0`, positions `Q(A(6 * V))`; otherwise an eight-byte-entry block `Q(8 * E)` at `+0x28`. Both paths retain `Q(A(4 * (E == 0 ? V : E)))` at `+0x18` and `Q(A(4 * V))` at `+0x20`. No generated packet is allocated by this parser. |
| 2 | A `Q(0x10)` descriptor at `+0x30` and its converted packet. Input attribute arrays are temporary and freed after packet construction. |
| 4 | A generated packet at `+0x34` when construction succeeds; the geometry and edge-building arrays are temporary and freed before return. |

For family 0, `+0x18` is allocated when `f & 0x40` is zero, `+0x1C` when
both `f & 0x200` and `f & 1` are zero, and `+0x20` when `f & 0x400` is
zero. When `f & 0x200` is zero but `f & 1` is set, the corresponding file
words are consumed without retaining that attribute block. Size helper
`FUN_00194110` gives the generated packet request:

```text
16 * (ceil(V / 48) * (7 + I(!(f & 0x40)) + I(!(f & 1))
                         + 2 * I(!(f & 0x400))) + 2)
```

`I(condition)` is 1 when true and 0 otherwise. If model flags `+0x48` have
`0x02000000` set and `0x04000000` clear, `FUN_001B0140` may insert duplicate
vertices according to the strip markers. It allocates replacements for every
present attribute block at the expanded count before freeing the old blocks.
The packet is then sized from that expanded count. Final retained size alone
therefore misses an overlap of the old and new attribute arrays.

Family 2's non-indexed path (`E == 0`) temporarily holds
`Q(6 * V) + 2 * Q(4 * V)` through `FUN_001AF1F0`. Its strip conversion
`FUN_001AF450` can allocate all three replacements before freeing the old
arrays. With `M` the resulting count and `r = M % 54`, packet builder
`FUN_001AF9D0` requests:

```text
A(4 * (289 * floor(M / 54) + 1 + (r == 0 ? 0 : 5 * r + 19)))
```

The indexed path temporarily holds
`Q(8 * E) + Q(4 * E) + Q(4 * V) + Q(0x10 * V)` through `FUN_001AE190`.
`FUN_001AE430` can replace the last array at the expanded vertex count before
freeing its predecessor. `FUN_001AE950` groups the resulting records with
`FUN_001AE770` and sums their entry counts with `FUN_001AE7D0`. For a batch
of `q` records containing `s` entries, its packet contribution is
`4 * (4 * s + ceil(3 * s / 2) + 20 + q)` bytes; the sum over all batches
is rounded with `A`. Instructions `0x001AE974..0x001AEA08` establish the
count arguments and allocation arithmetic. Both family-2 paths use nullable
packet allocation and then free their input arrays through `FUN_001AF150`
or `FUN_001AE0E0`. The packet and descriptor remain.

For family 4, let `U` be the unique-vertex count read by `FUN_0018D740`,
`W` its index count, and `T = W / 3`. For nonzero `U`, its initial scratch
nodes are:

```text
Q(0x140) + Q(0x20 * W) + Q(8 * T) + 2 * Q(0x10 * T)
         + Q(8 * U) + Q(0x3C * U)
```

One `0x10 * T` work array is freed before the construction checks, and the
`0x20 * W` array is freed before allocating the successful output packet.
Let `H` and `S` be the resulting normal and edge counts at the scratch
context's `+0x126` and `+0x12C`. The packet request is:

```text
16 * H + 48 * ceil(T / 24) + 24 * T
       + 48 * ceil(S / 24) + 80 + 16 * S
```

The other scratch nodes remain live during that allocation and are freed
afterward. `FUN_0018E240` and `FUN_0018E530` build the edge and normal data
in these preallocated arrays. The zero-vertex and unsuccessful construction
paths retain no generated packet. Thus the file's geometry counts, strip
markers, and conversion family determine both its retained cost and its
temporary overlaps.

## Texture and palette storage

The ordinary texture path in `FUN_001B3C70`, with file flags `0x20` clear,
builds a `Q(0x48)` texture through `FUN_001B4470` and `FUN_0019EAB0`.
When constructor flags `0x40` are clear, it additionally allocates a level
table `Q((mip_count + 1) * 0x20 + 0x10)` and calls `FUN_0010FEE0` for the
base level and each mip level. With no source pointer, each level requests
`16 * ceil(bits_per_pixel * width * height / 128)` pixel bytes through
nullable `FUN_00117600`, with its own node overhead. The parser copies the
file's pixel dwords into that buffer and fills any remainder with
`0xFFFFFFFF`. When the payload is larger than the buffer, it copies nothing
and fills the whole buffer with `0xFFFFFFFF`.

The file-flags-`0x20` path instead consumes the pixel words without retaining
them, clears the mip count, sets constructor flags `0x58`, and allocates a
`Q(0x50)` object through `FUN_0019E080`. Constructor `FUN_0019EAB0` sees
`0x40` and omits the level table and pixel allocations. Thus a texture tag
does not invariably imply retained decoded pixels. Ordinary owned pixel
buffers prefer the high end inside the parser's placement scope.

When a level's pixel allocation fails, `FUN_0010FEE0` shrinks that level to
8×8 and allocates the smaller buffer through trapping `FUN_00117700`; the
parser then fills it with `0xFFFFFFFF` instead of the payload.
**Inference (high confidence):** near exhaustion, affected texture levels
become 8×8 blocks of `0xFFFFFFFF` before the game stops. Most other
allocations use the default entry points, which trap after both placement
sides fail.

Palette parser `FUN_001B3810` requests a `Q(0x28)` descriptor when creating
a new `0x0400` record. `FUN_0019EC60` adds a `Q(0x20)` level descriptor and,
through `FUN_0010FEE0`, a pixel block sized from the palette format and its
16×16 or 8×2 dimensions. Its nullable allocation uses the palette branch,
which has no texture-style 8×8 retry. When the palette's `+0x18` flag bit 1
is clear, the parser calls `FUN_0010F860` to submit the pixels, then
`FUN_0019EBE0` frees the level and owned pixel blocks. When that bit is set,
those blocks remain. Consequently this path's construction-time allocations
can exceed its retained descriptor cost.

Texture and palette name bindings also materialize shared image-transfer groups:
`FUN_0019E770` / `FUN_0019EDE0` reuse a matching controller or create a
`Q(0x38)` controller through `FUN_0019D2D0`; each binding adds a `Q(8)`
list node through `FUN_0019D180` / `FUN_0019D130`. This indirect construction
is distinct from the `0x1000` file-block parser, which discards its payload.

## Sampled retail capacity

The arena's usable span between the sentinels is `0x1718F50` bytes. Occupied
bytes are that span minus total free, including node headers, alignment, and
the 2 MiB secondary pool. Fragmentation is total free minus largest free.

| Screen | Overlay | Total free | Largest free | Occupied | Fragmentation |
| --- | --- | ---: | ---: | ---: | ---: |
| Title | BTL | `0x101F7F0` | `0x1018330` | `0x06F9760` | `0x0074C0` |
| Mode select | BTL | `0x0B0B940` | `0x0A6B290` | `0x0C0D610` | `0x0A06B0` |
| Character select | BTL | `0x0CD1560` | `0x0AFD2E0` | `0x0A479F0` | `0x1D4280` |
| Active battle | BTL | `0x0866FB0` | `0x084E210` | `0x0EB1FA0` | `0x018DA0` |
| Collection | ETC | `0x0C89CB0` | `0x0A7EB80` | `0x0A8F2A0` | `0x20B130` |
| Options | BTL | `0x0B09660` | `0x0A96680` | `0x0C0F8F0` | `0x072FE0` |

The active-battle sample recorded peak tracked bytes `0xFCE500`. The same
peak also appears in the sampled Character Select, Collection, and Options
states, so it cannot be attributed to the sampled battle's load. The
accumulated counter does not identify when or for which load the maximum
occurred.

**Observation:** The sampled active battle had about 14.7 MiB occupied and one
free gap of `0x084E210` bytes, about 8.3 MiB, holding all but `0x18DA0` bytes
of the free space. An ordinary compressed CCS load adds the fixed transport
subtotal, inflate tables, and parsing/conversion scratch described above;
the sample alone does not show their simultaneous peak or placement.

**Inference (medium confidence):** The two-ended placement preference is
consistent with the sampled battle's large central free gap. That end-state
measurement does not establish the allocation history that produced it or a
minimum capacity across battles.
