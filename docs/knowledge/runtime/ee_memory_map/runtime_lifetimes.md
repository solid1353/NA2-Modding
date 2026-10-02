# EE runtime lifetimes

Native lifetime and ownership evidence for overlays, stacks, the high-memory
tail, and the main heap-backed regions.

## Research coverage

- **Assigned scope:** establish which large EE memory ranges are resident,
  overlay-owned, allocator-owned, stack-owned, or otherwise unsafe for fixed
  storage, and when they are filled and released.
- **Exploration depth:** all native overlay kinds and the overlay loader, the
  overlays' static constructors, the six static CRI/ADX stacks, dynamic-thread
  allocation, the startup `malloc` layer, the per-frame pool release, CCS load
  transients, and sampled high-memory states were examined.
- **Confirmed coverage:** overlay loading and effective ends, phase-only
  slack, static stack ranges, dynamic-thread stack ownership, ownership of the
  high-memory tail at region level, and the lifetimes of the persistent pools
  and CCS load transients are established.
- **Unresolved or untested:** the heap-memory totals released when a battle,
  Adventure scene, or menu is torn down, and whether any overlay constructor's
  callees allocate heap memory.
- **Deliberate exclusions and overlap:** CCS container release belongs to
  [Resident CCS runtime](../../game/files/ccs_runtime.md); battle object
  teardown belongs to [Battle lifecycle](../../gameplay/session/battle_lifecycle.md).
- **Evidence limitations:** observed phase slack is temporary and cannot prove
  that an address remains unused across later transitions. Lifetime findings
  for heap regions are static.

## Overlay loading

`FUN_001BE7F0(destination, name)` reads a whole overlay file into the address
selected by the pointer table at `0x006029C0`. Destination 1 is `0x006B3F00`;
destination 0 is `0x00100000`. After a complete read it calls `FUN_00100270`,
which flushes the data and instruction caches, zero-fills the header's
`+0x14` byte count immediately after the file image, and runs the constructor
pointers from header `+0x18` up to `+0x1C`.

| Header offset | Meaning | BTL | ADV | ETC |
| ---: | --- | ---: | ---: | ---: |
| `+0x00` | `MWo3` magic | | | |
| `+0x04` | kind | 1 | 2 | 3 |
| `+0x08` | load base | `0x006B3F00` | `0x006B3F00` | `0x006B3F00` |
| `+0x0C`, `+0x10` | loaded sizes; their sum plus the `0x40`-byte header is the file size | `0x1DB6C0`, `0x46C00` | `0x14E0C0`, `0xC4E00` | `0x24E40`, `0xC080` |
| `+0x14` | zero-filled size after the image | `0x6E80` | `0x400` | `0` |
| `+0x18..+0x1C` | constructor list | 9 entries | 13 entries | none |
| `+0x20` | internal name | `BTL_product.bin` | `ADV_product.bin` | `ETC_product.bin` |

**Observation:** An overlay load uses no heap memory for the image itself. The
constructors call no allocator entry point directly. One BTL constructor and
one ADV constructor register destructors through `FUN_00119A60`. An
absolute- and `gp`-relative reference scan of the executable and all overlays
found no reader of that list head at `0x00609A00`, so overlay replacement runs
no destructors.

## Overlay lifetimes and phase-only space

Each loaded overlay begins with `MWo3` at `0x006B3F00`; header word 1 identifies
the kind.

| State at overlay base | Kind | Effective end | Temporarily unused before `0x008DD080` |
| --- | ---: | ---: | ---: |
| No overlay | 0 | `0x006B3F00` | `0x229180` |
| `BTL.BIN` | 1 | `0x008DD080` | `0x0` |
| `ADV.BIN` | 2 | `0x008C7200` | `0x15E80` |
| `ETC.BIN` | 3 | `0x006E4E00` | `0x1F8280` |

This slack is not persistent free memory. A later overlay transition can
overwrite it, and `BTL.BIN` consumes the complete window. A phase-local
experiment must guard overlay identity, load state, and lifetime.

## Stacks and thread-owned memory

Six resident CRI/ADX thread stacks are statically allocated inside the main
ELF:

| Range | Size |
| --- | ---: |
| `0x003D6B20..0x003D7320` | `0x800` |
| `0x003D7320..0x003D8320` | `0x1000` |
| `0x003D8320..0x003D9320` | `0x1000` |
| `0x003D9320..0x003DA320` | `0x1000` |
| `0x003DA320..0x003DC320` | `0x2000` |
| `0x003DC320..0x003DE320` | `0x2000` |

Their creation paths are `FUN_0012E6B0` through `FUN_0012E9B8`.
`FUN_001CFE50` separately enforces a requested dynamic-thread stack minimum of
`0x800`, adds `0x400`, and obtains the backing memory through the game
allocator. Those stacks therefore have thread-specific allocator lifetimes.

## High-memory tail

The `0x01FF6000..0x02000000` tail is outside the game allocator and changed
across sampled states. Startup code establishes its two owners:

- `0x01FF6000..0x01FF8000` remains with the `malloc` layer after the arena
  request. The text-draw routine `FUN_00379FE0` obtains and frees temporary
  blocks there for strings of `0x200` bytes or more.
- `0x01FF8000..0x02000000` is the `0x8000`-byte main-thread stack requested by
  `InitMainThread` with stack address `-1`.

The placement of the stack is an inference from the kernel call's arguments;
see [the allocator document](allocator_and_capacity.md#system-memory-layer).
Both parts must remain reserved.

## Heap-backed regions

| Region | Allocated | Released |
| --- | --- | --- |
| `0x200000`-byte renderer pool | once by display initialization `FUN_00107F80` | never; its entries are recycled every frame by `FUN_00110770` |
| `0x10000`-byte untracked buffer | once by `FUN_001114A0` | not observed |
| Sound controller | once by `FUN_001D7A30` | not observed |
| File-directory text and tables | once by `FUN_001BDA50` during front-end startup | never; the text pointer is not retained |
| `0x4D000`-byte IOP module staging buffer | by `FUN_001BD0B0` | before that routine returns |
| CCS load transients | by `FUN_001CF3F0` at the start of each load, at the low end | before a flags-`0` load returns; worker stacks follow their tasks' lifetimes |
| CCS containers | by the parser on the decode worker, at the high end | when their owner destroys the container |
| Deferred-free blocks | by their owner | when their frame countdown reaches zero in `FUN_00117AD0` |
