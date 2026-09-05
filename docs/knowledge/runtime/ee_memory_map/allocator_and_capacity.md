# EE allocator

Static and runtime findings for the unmodified NA2 allocator.

## Research coverage

- **Assigned scope:** identify the allocator's initialization, metadata, linked
  structure, counters, free-space measures, and sampled vanilla capacity.
- **Exploration depth:** initialization and allocation metadata were traced
  statically, and the complete linked list was validated in seven runtime
  states.
- **Confirmed coverage:** arena bounds, sentinels, globals, node format,
  accounting behavior, and vanilla free-space measurements are established.
- **Unresolved or untested:** semantic names for the two small-block bin
  families and flag classes `0`, `1`, `8`, and `9`.
- **Deliberate exclusions and overlap:** NA228 reservation costs and payload
  capacity belong to [Runtime injection](../../../features/runtime_injection/implementation.md).
- **Evidence limitations:** capacity values describe sampled states, not a
  guaranteed lower bound for every game state or allocation sequence.

## Allocator model

`FUN_00118730` first requests `0x1718F70` bytes from the lower-level system
allocator and backs the request down in `0x100` steps until it succeeds. It
aligns the returned base, installs two 16-byte sentinels, initializes two
free-bin structures, and caches the largest free gap.

| Address | Meaning |
| ---: | --- |
| `0x00607380` | user allocation base |
| `0x00607384` | heap end |
| `0x00607388` | current tracked bytes |
| `0x0060738C` | peak tracked bytes |
| `0x00607390` | live allocation count |
| `0x00607394` | unresolved allocator global |
| `0x00607398` | base sentinel |
| `0x0060739C` | end sentinel |
| `0x006073A0` | cached predecessor of the largest gap |
| `0x006073A4` | cached largest-gap size |

Each allocated node has a 16-byte header containing the previous node, next
node, aligned allocation size, and low-nibble flags. `FUN_001180D0` rounds a
request plus its header to 16 bytes. Two segregated-bin families at
`0x00607B50` and `0x00608360` serve gaps below `0x1000` in 16-byte size classes;
a general ordered list serves larger gaps, with fallback to the cached largest
gap. Flag bit `0x4` controls whether a block contributes to tracked bytes.

Complete list walks in every sampled state established that:

- forward and backward links are consistent and acyclic;
- the walked node count equals `0x00607390`;
- walked tracked bytes equal `0x00607388`;
- the cached largest gap and predecessor match the computed maximum;
- one flag-12 allocation of `0x10010` bytes is excluded from tracked bytes.

`total_free` is the sum of gaps between live nodes. `largest_free` is the
largest single gap and therefore the limit for one ordinary allocation.
`fragmentation_bytes` is `total_free - largest_free`.

## Sampled vanilla capacity

| Screen | Overlay | Total free | Largest free |
| --- | --- | ---: | ---: |
| Title | BTL | `0x101F7F0` | `0x1018330` |
| Mode select | BTL | `0x0B0B940` | `0x0A6B290` |
| Active Adventure | ADV | `0x07B2D30` | `0x0509600` |
| Character select | BTL | `0x0CD1560` | `0x0AFD2E0` |
| Active battle | BTL | `0x0866FB0` | `0x084E210` |
| Collection | ETC | `0x0C89CB0` | `0x0A7EB80` |
| Options | BTL | `0x0B09660` | `0x0A96680` |

The vanilla peak-tracked global reached `0xFCE500` in these observations.
Matched NA228 measurements are retained with their owning feature in
[`observations.tsv`](../../../features/runtime_injection/observations.tsv).
