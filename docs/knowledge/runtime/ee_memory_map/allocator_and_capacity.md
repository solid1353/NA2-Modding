# EE allocator

Static and runtime findings for the unmodified NA2 allocator.

## Research coverage

- **Assigned scope:** identify the allocator's initialization, metadata, linked
  structure, placement policy, entry points, counters, free-space measures,
  secondary pools, load-time costs, and sampled vanilla capacity.
- **Exploration depth:** the startup code, the system `sbrk`/`malloc` layer,
  heap initialization, every resident allocator entry point, the free, resize,
  and deferred-free paths, the placement-direction scopes, the resident file
  directory, the CCS load pipeline's allocations, and CCS texture storage were
  traced statically. Allocation call sites were enumerated by `jal` encoding
  across the ELF and all three overlays. Other CCS object parsers were not
  audited for their allocation sizes. The complete linked list was validated
  in seven retail runtime states.
- **Confirmed coverage:** arena bounds, sentinels, globals, node format, flag
  bits, the two-ended placement policy and its per-thread scopes, deferred
  free, accounting behavior, the 2 MiB per-frame pool, the resident file
  directory, the transient cost of a CCS load, texture storage and its
  allocation-failure fallback, and vanilla free-space measurements are
  established.
- **Unresolved or untested:** per-asset allocation totals from a retail heap
  walk (which nodes belong to the stage, each fighter, the HUD, and effects),
  the ratio between a CCS file's decompressed size and its resident cost for
  non-texture objects, and the retail peak during a battle load.
- **Deliberate exclusions and overlap:** NA228 reservation costs and payload
  capacity belong to [Runtime injection](../../../features/runtime_injection/implementation.md);
  CCS parsing and container ownership belong to
  [Resident CCS runtime](../../game/files/ccs_runtime.md); task records and
  thread stacks belong to [Task system](../task_system.md).
- **Evidence limitations:** capacity values describe sampled states, not a
  guaranteed lower bound for every game state or allocation sequence. No
  retail savestate was available after the original seven samples, so the
  per-asset cost model below is static and unmeasured.

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
Resident code and `ADV.BIN` set it before selected allocations; `BTL.BIN` and
`ETC.BIN` never write it.

**Observation:** CCS container objects are therefore allocated downward from
the top of the arena, while ordinary objects and load transients are allocated
upward from the bottom. The largest free gap normally lies between the two
regions.

### Entry points

| Function | Arguments | Direction choice | Try, then fallback | Calls (ELF/BTL/ADV/ETC) |
| --- | --- | --- | --- | ---: |
| `FUN_00117030` | size | scope, else one-shot byte | preferred side nullable, other side trapping | 117/52/72/1 |
| `FUN_00117150` | size | same as `FUN_00117030` | same | 933/863/978/147 |
| `FUN_00117500` | size | scope only; none selects high | preferred side nullable, other side trapping | 7/0/0/0 |
| `FUN_00117270` | alignment, size | scope only; none selects high | same | 6/0/0/0 |
| `FUN_00117370` | alignment, size | scope `1` selects high, otherwise low | same | 25/0/1/0 |
| `FUN_00117700` | size | same as `FUN_00117370` | same | 126/20/9/0 |
| `FUN_00117600` | size | same as `FUN_00117370` | both sides nullable; may return zero | 12/0/0/0 |
| `FUN_00117470` | size | always low first | low untracked nullable, then high untracked trapping | 1/0/0/0 |

Frees use `FUN_00117C40`, directly or through the one-instruction wrapper
`FUN_00117000` (740/666/728/97 calls). A free unlinks the node, merges the
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

**Inference (high confidence):** An ordinary CCS load needs about `0xA3000`
bytes (about 650 KiB) of low-end transient memory, including task stacks, in
addition to its resident container, and the file is never held whole in
memory. The decompression block size is read from the output ring's block
size, `0x10000` on this path. The resident cost of a file is the high-end
allocation set built by `FUN_001A9060` from the decompressed stream.

**Hypothesis:** A file's resident cost is close to its decompressed size plus
per-object runtime overhead. Texture pixel data is copied into allocations of
its decoded size, as shown in
[texture storage](#texture-storage-and-allocation-failure); other object types
and the whole-file total have not been measured. Retail decompressed sizes
from the resident file directory give the scale:

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

## Texture storage and allocation failure

The CCS texture parser `FUN_001B3C70` builds a `0x48`-byte texture through
`FUN_001B4470` and `FUN_0019EAB0`. The texture allocates a
`(mip_count + 1) * 0x20 + 0x10`-byte level table and calls `FUN_0010FEE0` for
the base level and each mip level with no source pointer. Each level then
allocates its own pixel buffer of `ceil(bits_per_pixel * width * height / 128)`
quadwords through nullable `FUN_00117600`. The parser copies the file's pixel dwords into that
buffer and fills any remainder with `0xFFFFFFFF`. When the payload is larger
than the buffer, it copies nothing and fills the whole buffer with
`0xFFFFFFFF`.

**Observation:** A texture's resident cost is therefore its decoded pixel
storage, not a reference into a retained file buffer. Inside the parser's
high-placement scope, pixel buffers are taken from the high end first.

When a level's pixel allocation fails, `FUN_0010FEE0` shrinks that level to
8×8 and allocates the smaller buffer through trapping `FUN_00117700`; the
parser then fills it with `0xFFFFFFFF` instead of the payload.
**Inference (high confidence):** near exhaustion, affected texture levels
become 8×8 blocks of `0xFFFFFFFF` before the game stops. Most other
allocations use the default entry points, which trap after both placement
sides fail.

## Sampled vanilla capacity

The arena's usable span between the sentinels is `0x1718F50` bytes. Occupied
bytes are that span minus total free, including node headers, alignment, and
the 2 MiB secondary pool. Fragmentation is total free minus largest free.

| Screen | Overlay | Total free | Largest free | Occupied | Fragmentation |
| --- | --- | ---: | ---: | ---: | ---: |
| Title | BTL | `0x101F7F0` | `0x1018330` | `0x06F9760` | `0x0074C0` |
| Mode select | BTL | `0x0B0B940` | `0x0A6B290` | `0x0C0D610` | `0x0A06B0` |
| Active Adventure | ADV | `0x07B2D30` | `0x0509600` | `0x0F66220` | `0x2A9730` |
| Character select | BTL | `0x0CD1560` | `0x0AFD2E0` | `0x0A479F0` | `0x1D4280` |
| Active battle | BTL | `0x0866FB0` | `0x084E210` | `0x0EB1FA0` | `0x018DA0` |
| Collection | ETC | `0x0C89CB0` | `0x0A7EB80` | `0x0A8F2A0` | `0x20B130` |
| Options | BTL | `0x0B09660` | `0x0A96680` | `0x0C0F8F0` | `0x072FE0` |

The vanilla peak-tracked global reached `0xFCE500` in these observations.
Matched NA228 measurements are retained with their owning feature in
[`observations.tsv`](../../../features/runtime_injection/observations.tsv).

**Observation:** The sampled active battle had about 14.7 MiB occupied and one
free gap of `0x084E210` bytes, about 8.3 MiB, holding all but `0x18DA0` bytes
of the free space. An ordinary CCS load during battle first takes about
`0xA3000` bytes of that gap for its transients.

**Inference (medium confidence):** Battle's low fragmentation follows from the
two-ended policy: CCS containers stack from the top and ordinary objects from
the bottom. Adventure, the only overlay that writes the one-shot placement
byte, had the most fragmented sample.
