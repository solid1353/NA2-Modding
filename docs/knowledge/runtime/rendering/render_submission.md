# Render submission and buffers

This document owns the render packet allocator, render-list ownership,
ordering, submission, and reuse contracts of retail NA2 (`SLPS-25837`).
Addresses are resident `SLPS_258.37` EE addresses; see
[address conventions](../../game/files/file_identities.md#address-conventions).

## Research coverage

- **Assigned scope:** Render packet allocation, list ownership, ordering, buffer swap/reuse, packet lifetime and static capacity/failure contracts; follow submission to DMA/VIF/GS where evidence establishes it.
- **Exploration depth:** The resident pool/list helper family, renderer priority
  insertion and ordering-tree producer/consumer paths, frame-worker ordering,
  DMA submission/continuation/completion, and display/draw buffer selection have
  been traced. Principal bodies were confirmed whole: initialization
  `0x00107F80..0x00108163`, frame begin `0x001081B0..0x0010838F`, frame wait
  `0x00108490..0x00108677`, pool constructor `0x00110B30..0x00110C6B`, and
  graphics synchronization `0x0014F728..0x0014FA3B`; narrower instruction
  ranges establish allocator return, strict-fit, split and ordering-depth
  decisions without relying on recovered types. Five direct ordered-submission
  call sites and representative allocation/chain consumers are bounded below.
- **Confirmed coverage:** The display creates a `0x200000`-byte pool; packet
  blocks retain list ownership; each render list has two embedded heads; the
  frame boundary links renderer chains into a parity-selected master chain and
  starts VIF1 source-chain DMA. The shared ordering pool has 1024 nodes and
  insertion depth at most 50; completed/aborted transfers precede reuse in the
  traced frame worker; GS display selection and GIF draw-environment submission
  use paired environments separate from the EE packet lists.
- **Unresolved or untested:** The deferred-release array's declared capacity
  is not established. Nonzero renderer byte `+0x06` bypasses ordinary rotation
  through the empty `FUN_00109D00`; its setters and caller-owned lifetime are
  unresolved. The synchronization path checks DMA/VIF/VU/GIF state, but a final
  GS FINISH fence is not established. Indirect producer coverage is incomplete.
  Allocation-failure frequency and rendering cost are not established.
- **Deliberate exclusions and overlap:** Coordinate transforms belong to
  [Renderer and coordinate systems](renderer_coordinates.md), resource binding
  to [Texture palette and material runtime](texture_material_runtime.md), and
  draw ownership to [Full-screen and bounded 2D draw ownership](draw_2d_owners.md).
  The VU microcode carried by the frame prefix and model uploads belongs to
  [Model VU programs](model_vu_programs.md#initial-upload-boundaries).
  General heap allocation belongs to [Allocator and capacity](../ee_memory_map/allocator_and_capacity.md).
- **Evidence limitations:** This is static retail-code evidence. It establishes
  instructions and bounded paths, not measured performance or the frequency of
  allocation failures. Preserved decompiler signatures can omit live register
  returns; relevant instruction checks are identified below. Queue indexing and
  the zero-filled memory around `0x00608DB0` do not delimit the deferred queue's
  declared capacity.

## Pool and block ownership

**Observed, high confidence.** Display initialization `FUN_00107F80` requests
a `0x14`-byte pool descriptor and calls `FUN_00108170(descriptor, 0x200000)`.
That wrapper calls `FUN_00110B30(descriptor, 0, size)`, which obtains backing
memory through `FUN_00117700`, marks descriptor flag bit 0, initializes one
free block covering the requested size, and appends the descriptor to a global
pool list. With a nonzero supplied backing pointer, the same constructor uses
that memory and clears flag bit 0. Destruction `FUN_00110A10` removes the
descriptor from the pool list and releases backing memory only for flag bit 0.

| Pool descriptor offset | Contract |
| --- | --- |
| `+0x00` | Next pool descriptor |
| `+0x04` | Search-start block pointer |
| `+0x08` | Backing-memory base / first block |
| `+0x0C` | Exclusive backing end |
| `+0x10` bit 0 | Pool owns backing allocation |

Blocks have a `0x10`-byte header before their payload. Header `+0x00` links
blocks belonging to an allocation list; `+0x04` is the owning list-head address
or zero for a free block; `+0x08` is the total block size including the header.
`FUN_00110600` prepends a block to its owner list and records that owner address.
`FUN_001109D0` traverses a block list and clears only ownership at `+0x04`;
`FUN_00110870` coalesces physically adjacent blocks whose ownership is zero.
The block header is allocator metadata, separate from the DMA tags in payload.

Renderer packet allocation `FUN_001097D0(renderer, bytes)` uses the list-head
address at renderer `+0x08`. Instructions `0x001097D8..0x00109850` establish the
pointer return despite the preserved decompiler's `void` signature. When a
shared current block has enough remaining payload and the owner matches, it
returns the old bump pointer in `v0` and advances it by `bytes`; otherwise it
calls `FUN_001103B0` to change owners within that block, or `FUN_001104A0` to
find another pool block. No size rounding or alignment repair occurs in these
three routines: inspected render producers request multiples of `0x10`.

**Observed allocation limits.** `FUN_00110620` scans each pool's physical
blocks and accepts only an unowned block, excluding the active bump block,
whose total size is **strictly greater** than `bytes + 0x10`. An exact-size
free block is therefore rejected. `FUN_001104A0` visits pool descriptors in
registration order and returns zero if none qualifies. The ordinary wrapper
passes the current remaining-payload count in `a2`; the callee preserves this
third argument as its tail-reservation threshold. A tail larger than `0x20`
can become a free block; an adequate tail becomes the new shared bump region.
`FUN_001103B0` finalizes the previous owner's block at the bump pointer and
starts a new `0x10`-byte header for the next owner. If its remaining tail is
at most `0x20`, it disables the shared bump region. These rules are established
by instructions `0x001103CC..0x00110460`, `0x001104C8..0x001105C0`, and
`0x00110658..0x00110738`.

Recycle `FUN_00110770` releases queued lists, resets the 16-bit queue count,
turns unused active-bump capacity into a free block, clears the active remaining
count/block pointer, and coalesces each registered pool. It does not clear
packet payloads. A released packet address can consequently still contain old
bytes until a later allocation overwrites them; ownership, not contents,
determines whether the allocator may reuse it.

## Two heads per render list

`FUN_00110340` initializes a `0x20`-byte list object. Object `+0x00` points to
the head at `+0x08`; object `+0x04` points to the head at `+0x14`. Each embedded
head has three words: owned allocation blocks, first DMA packet, and final DMA
packet. Renderers embed this list object at renderer `+0x08`.

`FUN_00110210` clears the packet endpoints and releases allocation ownership
of the old submission head, makes that head the new construction head, then
selects the other embedded head for submission. Thus the role rotates; the
addresses of the two heads themselves remain stable. `FUN_001101B0` uses the
submission head's packet endpoints to insert its DMA chain at a supplied
master-chain insertion tag. List destruction `FUN_001102C0` immediately clears
ownership of the construction head's blocks and registers the other head's
blocks through `FUN_00110930` for later release by `FUN_00110770`.

Renderer destruction `FUN_0010A0F0` unregisters the renderer and then uses this
list destructor. The deferred queue starts at `0x00608DB0`; registration
`FUN_00110930` stores one list pointer at `base + 4 * count` and retargets every
block's owner field to that queue entry before incrementing its 16-bit count.
There is no capacity comparison in `0x0011093C..0x001109B4`. The physical array's
declared capacity has not been established; the counter width is not a safe
capacity bound.

## Packet ordering

Renderer registration `FUN_00109C70` inserts into a linked list in descending
signed 16-bit priority order, with a new equal-priority renderer after existing
ones. `FUN_0010A0A0` unregisters, changes priority, and reinserts. Frame assembly
visits that list and repeatedly inserts each renderer chain at the same master
tag. **Inference, high confidence from the link writes:** resulting chain order
is ascending priority, and equal-priority renderer chains occur in reverse
registration order. This describes chain ordering, not whether a particular
primitive visibly overwrites another.

Within a construction head, `FUN_00109740` appends a packet to the current
tail; `FUN_00109930` also initializes the packet tag from rounded quadword count
before appending. `FUN_00109E70` prepends instead. `FUN_001097B0` initializes a
NEXT-style tag with QWC `(bytes - 0x10) >> 4`; these helpers neither allocate
payload memory nor check capacity.

Ordered work uses a separate tree at renderer `+0x28` (root) / `+0x2C` (maximum
depth). Startup `FUN_00105FC0` calls `FUN_00106240(0x400)`, allocating `0x5000`
bytes for 1024 shared `0x14`-byte nodes. Node allocation checks its bump pointer
against the exclusive end, then advances before attempting tree insertion.

| Node offset | Contract |
| --- | --- |
| `+0x00` | Float ordering key |
| `+0x04` | Left child |
| `+0x08` | Right child |
| `+0x0C` | First packet of chain |
| `+0x10` | Final packet of chain |

Instructions in `FUN_0010A2C0` compare `new_key <= existing_key`: true goes
left, false goes right. For finite keys, equal keys go left; unordered float
comparisons also take the right branch. The root has depth 1. The insertion
loop increments depth before checking `< 0x33`, so it abandons an insertion
requiring depth 51. The already-reserved node remains consumed until reset,
and its packets are not linked by that abandoned insertion. Exhaustion of all
1024 nodes returns without registering the supplied chain. Neither case reports
an error or falls back to direct append in this helper.

`FUN_00109F20` supplies both the root and embedded render list to recursive
`FUN_0010A420`, which visits left child, node, then right child. `FUN_0010A4B0`
appends each node's chain to the list. For finite keys this gives ascending
keys, with later equal-key insertions visited first. `FUN_00109FB0` clears each
renderer's tree root/depth during next-frame preparation; `FUN_00108390`
resets the shared node bump pointer to its base afterwards. Tree nodes are
construction metadata and do not become DMA payload.

## Frame chain and VIF1 submission

**Observed, high confidence.** `FUN_00109D50` walks the renderer linked list.
For each renderer it finalizes ordered work through `FUN_00109F20`, conditionally
prepends a `0x30`-byte packet, rotates the embedded lists when renderer byte
`+0x06` is zero, and inserts the submission head into the master chain through
`FUN_001101B0`. `FUN_0010FC60` copies the insertion tag's old next address to
the inserted chain's final tag and replaces the insertion tag's next address
with the inserted chain's first packet. For DMA tag IDs 0, 3, 4, and 5 it first
steps over `(QWC + 1) * 0x10` bytes to the linking tag; for other IDs it uses
the supplied tag itself.

Display `FUN_001079C0` selects one of two `0x60`-byte master-chain templates
using display word `+0x194 & 1`. They begin at display `+0x1E0` and `+0x240`.
It publishes the selected head at `+0x1D0` and insertion tag at `+0x1D4`, and
initializes the tag sequence with bytes `0x30`, `0x10`, `0x20`, `0x70`, `0x70`.
The first tag references resident packet data at `0x003CEA30` with QWC `0x27B`.
Instructions `0x00107A04..0x00107A30` derive that count from the exclusive end
`0x003D11E0`. That frame prefix installs shared VU1 instruction regions; its
uploads are decoded in
[Model VU programs](model_vu_programs.md#initial-upload-boundaries). The next template slot copies one REF tag from display `+0x1D8`;
`FUN_00107AB0` creates that display-owned packet and releases/replaces it when
regenerating the display setup. Its request is
`0x140 + 0x40 * floor(display_width / 64)`, outside the per-frame render pool.

`FUN_001081B0` increments display `+0x194`, finalizes the current renderer
chains, and, when signed display byte `+0x2AC` is negative, calls
`FUN_001078E0` to submit the selected master chain. Submission records the
chain at display `+0x1CC`, sets VIF1 QWC and MADR to zero, writes the chain
address masked to 28 bits to VIF1 TADR, acknowledges DMAC status bit 1,
flushes cache, marks transfer state, and writes VIF1 CHCR `0x145` inside the
interrupt-disabled section. The caller subsequently enables DMAC channel 1.

After submission, `FUN_001081B0` calls `FUN_00106500`, which initializes the
next parity-selected master chain, resets renderer per-frame state through
`FUN_00109F60`, and calls pool recycle `FUN_00110770`. This proves the
construction/submission rotation and next-chain preparation order.

## Completion and packet lifetime

The frame worker `FUN_001D0590` calls `FUN_001081B0` at the beginning of each
iteration, schedules and waits for its worker list, then calls `FUN_00108490`
before sleeping. `FUN_00108490` repeatedly calls `FUN_0014F728(0, 0)` and waits
while the transfer-active byte at `0x00607400` is 1. A nonzero return runs the
graphics recovery/reset sequence and clears that byte.

Blocking `FUN_0014F728` checks, in order, VIF1 CHCR bit `0x100`, GIF CHCR bit
`0x100`, VIF1 STAT mask `0x1F000003`, VU control register 29 bit `0x100`, and
GIF STAT mask `0xC00`. One poll counter is shared across these checks; exceeding
`0x1000000` prints register diagnostics and returns `0xFFFFFFFF`. Passing all
checks returns zero. Its nonblocking branch returns bits 0..4 for these same
five busy conditions. Instructions `0x0014F738..0x0014F87C` establish the
blocking sequence; raw instruction `0x4846E800` at `0x0014F80C` confirms the
control-register index despite Ghidra's `vc13` register spelling. This is a
poll-count bound, not an elapsed-time limit.

The DMAC handler record at `0x00602A08` contains enabled count 1, channel 1,
and handler `0x00108BA0`. Initialization `FUN_001089A0` registers it.
`FUN_00108BA0` accepts a 16-byte-aligned VIF1 MADR in
`0x00100000..0x01FFFFFF` and tag-ID state 0 or 7, then examines the preceding
tag through `FUN_00108D90`. If that tag's address word `+0x04` is zero,
`FUN_00108D90` records the completion counter, disables the channel interrupt,
and clears transfer-active. Otherwise it can invoke a callback at `+0x18`
with argument `+0x1C`, then resume at a NEXT tag (`+0x13 == 0x20`) or unwind
a RET tag (`+0x13 == 0x60`) using VIF1 ASR registers. Unsupported tag state or
RET with an empty return stack rejects continuation. The handler runs its
graphics reset sequence and clears transfer-active when its validation or
continuation check fails.

**Inference, high confidence for the traced frame worker.** While chain N is
submitted, construction switches to the alternate list head and alternate
master-chain template. The rotation releases blocks from N-1, which the previous
iteration's end-of-frame wait has already finished or aborted. Newly submitted
N remains owned until the following rotation. The pool is shared between the
heads, rather than split into two fixed 1 MiB halves. Deferred destruction
preserves submitted-head blocks until next-frame recycle. This is a DMA packet
lifetime contract; it does not independently establish that all GS rendering
has completed at the instant the DMAC handler clears the byte.

## Display and draw environments

The EE packet-list rotation, master-chain parity, and GS buffer selector are
separate state. Display byte `+0x2AF` selects paired GS environments; display
`+0x194` selects EE master-chain templates. In `FUN_001081B0`, ordinary
`+0x2AD == 0` and negative `+0x2AC` call
`FUN_00107590(display, selector ^ 1)` before renderer-chain submission. The
alternate `+0x2AD != 0` branch toggles `+0x2AF` without that environment call.
Display setup `FUN_001065A0` regenerates the environments when `+0x2AC` is
nonnegative and finishes by restoring it to `0xFF`.

`FUN_00107590` writes DISPFB1 from display `+0x2C0 + 0x28 * selector` and
DISPLAY1 from `+0x4E0 + 0x10 * selector` when byte `+0x2AE` is zero. With
nonzero `+0x2AE`, it adjusts the selected draw environment through
`FUN_00150618`, using the observed GS field bit. It then calls
`FUN_0014F630(display + 0x2B0, selector)` and saves the selector.

`FUN_0014F630` selects a `0x28`-byte display environment and separately sends
the draw-environment packet at argument `+0x50` (selector 0) or `+0x140`
(selector 1). These are display `+0x300` and `+0x3F0`.
`FUN_0014EE38` writes the selected display environment to privileged GS
registers. `FUN_0014F2B0` waits for GIF DMA channel 2 to be idle, sets GIF QWC
to `(first_word & 0x7FFF) + 1`, masks MADR to 28 bits while preserving the
scratchpad flag for a `0x7xxxxxxx` pointer, and starts normal DMA with CHCR
`0x101`. Timeout reports failure as `0xFFFFFFFF`; the environment wrapper does
not propagate that result. This GIF path submits draw state separately from
the renderer's VIF1 source chain. Neither path in this section waits for a GS
FINISH event; the stronger claim that every primitive has finished rasterizing
is consequently not established by these routines.

## Bounded producer and consumer coverage

The five resident direct calls to `FUN_0010A2C0` were found both in xrefs and
by their exact JAL instruction bytes. The same bytes were searched in exposed
`BTL.BIN` and `ETC.BIN`, with no additional direct match. That is a bounded
direct-call result; it does not exclude indirect calls, inlined insertion, or
other algorithms.

| Resident producer / call site | Packet-list contract established |
| --- | --- |
| `FUN_0018FFB0`, `0x00190B28` | Model packet chain uses the ordinary shared allocator, returns without submitting on allocation failure, then selects direct append or float-keyed insertion; the ordered key is negative draw-context depth. Geometry payload ownership belongs to [Model runtime](model_runtime.md). |
| `FUN_001910E0`, `0x00191B34` / `0x00191EF4` | Two model-chain paths submit first/final packet pairs to the renderer tree with negative draw-context depth. The second can instead append directly. Transform and material calculations are outside this document. |
| `FUN_00195A90`, `0x00195DB8` | Effect draw reserves `0x1B0` bytes and omits submission if allocation fails. Its ordered path supplies key `projected_z / projected_w`, first tag at packet base and final tag at base `+0x10`; other branches append directly. |
| `FUN_002088B0`, `0x00208A34` | Batched strip finalization submits to the current renderer's tree only for more than one accumulated strip. The key is accumulated float depth divided by twice the strip count. Instructions preserve the same packet-base address in both first/final arguments. |
| `FUN_0010FA10` | Transfer descriptor consumes `0x90` bytes from a renderer's ordinary allocation list; on success it appends the generated transfer chain or splices it at a supplied insertion tag. On failure it returns without submitting. Source payload is referenced through the descriptor/override pointer, rather than copied by this wrapper. Transfer-resource interpretation belongs to [Texture palette and material runtime](texture_material_runtime.md). |
| `FUN_00109430`, `FUN_00109A10`, `FUN_0010A520` | These inspected state/2D producers check the packet-allocation result before writing/appending; their requests are `0x110`, `0x90`, and `0x150` or `0x2B0`, respectively. Their coordinate/material algorithms belong to neighboring owners. |

Strip builder `FUN_00208570` clears count/depth, toggles its local half index,
and reserves `(4 * requested_strip_count + 6) * 0x20` bytes from the current
renderer allocation list. Each half is `(4 * requested_strip_count + 6)`
quadwords. `FUN_00208630` writes one `0x40`-byte strip entry and increments
the accumulated count; it has no local count-vs-reservation check.
`FUN_002103C0` and `FUN_002D7A50` count the requested entries first, gate filling
on allocation success, then finalize through `FUN_002088B0`. This paired local
reservation is contained within the ordinary per-frame renderer ownership;
its toggling field does not create an independent persistent packet lifetime.

## Capacity and failure summary

| Storage / operation | Established bound or failure behavior |
| --- | --- |
| Display-created render pool | `0x200000` total backing bytes including block headers; shared by all registered renderer lists |
| Pool block search | Strictly larger-than-requested free block required; no matching block across registered pools returns zero |
| Packet bump allocation | No local alignment repair; same-owner bytes share a block; changing owner creates a new header |
| Ordering nodes | 1024 global nodes, reset per frame; exhaustion omits insertion |
| Ordering depth | At most 50, including root; an abandoned depth-51 insertion consumes its node |
| Deferred list queue | 16-bit count, base `0x00608DB0`, unchecked registration; declared array capacity unresolved |
| Strip reservation | Formula above; population helper has no local overrun guard; inspected callers pre-count entries |
| Blocking graphics synchronization | Shared `0x1000000` poll threshold; diagnostic failure returns `0xFFFFFFFF` and frame wait recovers/reset-clears active state |
| GIF draw-state submission | Separate bounded idle wait; its caller ignores the returned timeout result |

No measured utilization, transfer duration, frame budget, or safe additional
packet count follows from these static capacities. The render pool is not a
fixed primitive-count array: packet sizes, block headers, owner switches,
reserved tails, and still-owned submitted lists all affect available capacity.
