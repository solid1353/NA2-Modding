# EE address space

Static and runtime findings for the retail NA2 (`SLPS-25837`) EE address space.
All ranges are end-exclusive.

## Research coverage

- **Assigned scope:** identify the resident, overlay, allocator, and
  high-memory ranges and their native owners.
- **Exploration depth:** the retail executable's program headers and startup
  code, all three overlay kinds, allocator sentinels, the `malloc` layer, the
  largest static objects in the zero-filled resident range, and sampled
  high-memory states were examined.
- **Confirmed coverage:** the resident ELF, overlay window, vanilla heap, the
  `malloc` layer below the main-thread stack, and the largest static buffers
  are located, and their relevant lifetimes are established.
- **Unresolved or untested:** ownership of the smaller objects in
  `0x00607380..0x006200A0` and `0x006B21C0..0x006B3F00`, and byte-level use of
  the main-thread stack.
- **Deliberate exclusions and overlap:** allocator internals belong to
  [Allocator and capacity](allocator_and_capacity.md); overlay lifetimes belong
  to [Runtime lifetimes](runtime_lifetimes.md).
- **Evidence limitations:** zero or stable bytes do not establish unused memory;
  classifications rely on file layout, owners, and observations across the
  sampled states. The static-object map comes from absolute and `gp`-relative
  address references, so objects reached only through computed pointers can be
  merged into a neighbouring span.

## Address-space map

| Address range | Size | Native owner |
| --- | ---: | --- |
| `0x00000000..0x00100000` | `0x100000` | Low system/runtime region outside the NA2 ELF image. |
| `0x00100000..0x00607380` | `0x507380` | Resident NA2 ELF code and static data. The load segment is RWX and contains six static thread stacks. |
| `0x00607380..0x006B3F00` | `0xACB80` | Zero-filled resident ELF tail containing BSS, allocator globals, and other mutable state. |
| `0x006B3F00..0x008DD080` | `0x229180` | Shared MWo3 overlay window for `BTL.BIN`, `ADV.BIN`, and `ETC.BIN`. |
| `0x008DD080..0x008DD090` | `0x10` | `malloc` chunk header and alignment before the vanilla allocator sentinel. |
| `0x008DD090..0x01FF6000` | `0x1718F70` | Vanilla game allocator arena including both sentinels. |
| `0x01FF6000..0x01FF8000` | `0x2000` | Remainder of the `malloc` area above the arena. |
| `0x01FF8000..0x02000000` | `0x8000` | Main-thread stack. |

The vanilla allocator user base is `0x008DD0A0`; the end sentinel begins at
`0x01FF5FF0`. The overlay effective ends and phase-specific slack are documented
in [runtime lifetimes](runtime_lifetimes.md). The `malloc` layer and the
stack-placement inference are documented in
[the allocator document](allocator_and_capacity.md#system-memory-layer).

The executable's own program headers declare this layout. Segment 0 loads
`0x507380` file bytes at `0x00100000` with memory size `0x5B3F00`. Three
zero-file-size headers at `0x006B3F00` have memory sizes `0x229180`,
`0x213300`, and `0x30F00`, ending at `0x008DD080`, `0x008C7200`, and
`0x006E4E00`, which are the BTL, ADV, and ETC effective ends. A final empty
header marks `0x008DD080`. The startup routine zero-fills
`0x00607380..0x008DD080` and starts the `malloc` area at `0x008DD080`.

## Large static objects in the zero-filled range

| Address range | Size | Owner |
| --- | ---: | --- |
| `0x00607380..0x006073C8` | `0x48` | Allocator, placement-scope, and secondary-pool globals |
| `0x00607B50..0x00608B70` | `0x1020` | Two allocator free-bin families |
| `0x006200A0..0x0067464C` | `0x545AC` | Three `0x1C1E4`-byte stereo ADX stream-player work areas |
| `0x00674650..0x006A91BC` | `0x34B6C` | Three `0x11924`-byte mono ADX stream-player work areas |
| `0x006A91C0..0x006B21C0` | `0x9000` | Three `0x3000`-byte buffers attached to the mono players |
| `0x006B3B00..0x006B3D00` | `0x200` | Short-string buffer of the text-draw routine `FUN_00379FE0` |

`FUN_001D7A30` allocates a `0x718`-byte sound controller, stores it at
`0x00607558`, and `FUN_001D66B0` assigns the work areas above. `FUN_001D6810`
passes each area and its size to the CRI ADXT creation wrapper `FUN_00133B88`
with channel count 2 or 1; the executable contains the `ADXT/PS2EE Ver.9.69`
library banner. **Inference (high confidence):** these `0x92120` bytes, about
585 KiB, are permanent streaming-audio work memory and are never reusable.

## Heap-relative rendering state

In retail NA2, the persistent rendering state's horizontal scale field is at
`0x00AF3694`, the first `1.0f` field in the stable structure context
`0000BF01 00000000 00000045 FFFFFF44 0000803F 0000803F 00008043 00004043`.
The structure is allocated at a fixed displacement from the heap boundary, so
its absolute address is not a permanent game constant and moves with that
boundary.
