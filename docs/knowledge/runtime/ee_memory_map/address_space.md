# EE address space

Static and runtime findings for the unmodified NA2 EE address space. All ranges
are end-exclusive.

## Research coverage

- **Assigned scope:** identify resident, overlay, allocator, and high-memory
  ranges that constrain runtime code and data placement.
- **Exploration depth:** the clean executable layout, all three overlay kinds,
  allocator sentinels, and sampled high-memory states were examined.
- **Confirmed coverage:** the resident ELF, overlay window, vanilla heap, and
  protected high-memory tail are located and their relevant lifetimes are
  established.
- **Unresolved or untested:** byte-level ownership throughout the high-memory
  tail and every allocation within the resident ELF's zero-filled segment.
- **Deliberate exclusions and overlap:** NA228 reservations and injection
  behavior belong to [Runtime injection](../../../features/runtime_injection/implementation.md);
  allocator internals and overlay lifetimes remain in their neighboring
  knowledge documents.
- **Evidence limitations:** zero or stable bytes do not establish unused memory;
  classifications rely on file layout, owners, and observations across the
  sampled states.

## Address-space map

| Address range | Size | Native owner | Constraint |
| --- | ---: | --- | --- |
| `0x00000000..0x00100000` | `0x100000` | Low system/runtime region outside the NA2 ELF image. | Protected; not free. |
| `0x00100000..0x00607380` | `0x507380` | Resident NA2 ELF code and static data. The load segment is RWX and contains six static thread stacks. | Use only individually proven caves. |
| `0x00607380..0x006B3F00` | `0xACB80` | Zero-filled resident ELF tail containing BSS, allocator globals, and other mutable state. | Zero at load does not make it free. |
| `0x006B3F00..0x008DD080` | `0x229180` | Shared MWo3 overlay window for `BTL.BIN`, `ADV.BIN`, and `ETC.BIN`. | Never persistent storage. |
| `0x008DD080..0x008DD090` | `0x10` | Alignment before the vanilla allocator sentinel. | Preserve. |
| `0x008DD090..0x01FF6000` | `0x1718F70` | Vanilla game allocator arena including both sentinels. | Dynamic allocation only. |
| `0x01FF6000..0x02000000` | `0xA000` | System and stack working tail outside the game allocator. | Protected; not free. |

The vanilla allocator user base is `0x008DD0A0`; the end sentinel begins at
`0x01FF5FF0`. The overlay effective ends and phase-specific slack are documented
in [runtime lifetimes](runtime_lifetimes.md).

## Heap-relative rendering state

The official clean-NA2 widescreen write targets `0x00AF3694`, the first `1.0f`
field in the stable structure context
`0000BF01 00000000 00000045 FFFFFF44 0000803F 0000803F 00008043 00004043`.
The structure is allocated at a fixed displacement from the heap boundary, so
its absolute address is not a permanent game constant. Any implementation that
changes the heap boundary must relocate and revalidate the target. The current
NA228 implementation belongs to [Rendering](../../../features/rendering.md).
