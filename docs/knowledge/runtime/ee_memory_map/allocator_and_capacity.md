# EE allocator and resident capacity

Decision evidence for the stable resident reservation, allocator behavior, measured runtime capacity, and compact external-payload tradeoffs.

## Decision summary

The captured two-file `TEXTENG.BIN` build was **not a severe near-term handicap**
to code injection in the sampled states. Its structural reservation reduces the
game heap by exactly `0x63080` bytes (405,632 bytes, 396.125 KiB), while the
tightest Current capture still has:

- `0x759260` bytes (7.348 MiB) of total allocator free space;
- `0x52B4C0` bytes (5.169 MiB) in its largest contiguous allocator gap.

The whole donor is nevertheless architecturally wasteful for the current
direct-pointer integration. `TEXTENG.BIN` consumes `0x30E00` bytes (200,192),
but the 35 guarded pointer edits reach only 30 distinct string locations whose
encoded strings total 1,512 bytes including terminators. The file is a NUN5
type-4 MWo3 localization data image, not executable code; most of its strings,
indexes, and internal pointer tables are unused by the current NA2 design. See
[`external_string_payload.md`](../../localization/external_string_payload.md) for the
decompilation and integration evidence.

The original compact-boundary architecture therefore:

1. replaces the whole donor and separate bootstrap with one `0x720`-byte
   `228.BIN` at `0x008F3D00`;
2. moves the structural boundary down from `0x00940100` to `0x008F4420`,
   recovering `0x4BCE0` bytes for the heap;
3. retains the donor only as read-only source provenance, not as an emitted
   runtime file;
4. keeps later resident code/data expansion explicit rather than silently
   growing into the heap or overlay window.

The compact layout is structurally and unit validated but had not yet received
matched runtime captures when this map was updated. The table below therefore
continues to describe the measured two-file Current build, not the new compact
one-file reservation.

### Stable reservation update (2026-08-03)

The exact linked payload end is no longer the game heap boundary. The current
`18,512`-byte payload occupies `0x008F3D00-0x008F8550`, while the boot ELF keeps
the structural reservation fixed through `0x00940100`; the allocator user base
therefore remains `0x00940120`. This gives up `0x47BB0` bytes (293,808 bytes) of
the compact build's reclaimed heap, but reuses the previously runtime-tested
two-file boundary and prevents ordinary payload growth from perturbing global
game state.

This change followed a matched size-only experiment. Adding one 32-byte final
data fragment moved the former compact heap user base from `0x008F8570` to
`0x008F8590`. The allocator list eventually selected different reuse layouts;
VIF/GIF packet addresses moved and the EE wrote slightly different transform
matrix floats. VU1 microcode and GS local memory remained byte-identical, but
the changed XYZ and perspective ST values altered character and pedestal
rasterization in Font captures 10 and 19. The exact game-engine dependency
between heap layout and matrix inputs was not isolated because a stable
reservation removes it from the build-to-build testing contract.

The global `na228 e2e all -s` gate now prepares and replays fingerprinted normal
and 32-byte padded E2E Test builds in independent concurrent pipelines through
the shared portable PCSX2 installation, and compares raw replay
PNG hashes without publishing an alternate baseline. The original focused proof matched all 58 non-ignored `font/main`
captures byte-identically; seven established volatile save-data captures in
that suite's `ignore.txt` remain excluded. Detailed paired states, GS/VU
comparisons, heap reports, and the original probe build record are retained under
`@work/Font 3/investigation/heap-boundary-tail-probe/`.

### Fixed-boundary allocation-order divergence (2026-08-04)

A later `collection` replay exposed a narrower limitation of that contract.
Normal build `20260804_022113_427_pid33712` and padded build
`20260804_022113_646_pid59636` retained the same heap user base
`0x00940120`, heap end `0x01FF5FF0`, allocation count, tracked bytes, free
bytes, largest gap, and allocation-size/flag multiset at capture 39. The heap
arena therefore did not relocate. Their linked lists nevertheless differed
continuously from allocator index 2427 through 4304. At the first differing
address, `0x00CA5990`, normal held a `0x50`-byte allocation while padded held
a `0x90`-byte allocation. The same persistent ordering difference was already
present at capture 1 and remained at capture 173.

The retained capture-39 savestates were
`DBD18A0C129D1F88ED33F5241728EB66B7DE582DAEADF3E453CBA4FDE6175881`
for normal and
`532C5BC844B2BF67D8B20F40F703AF28F3C6FEF0B346C0C0E1821DF810E5F843`
for padded. Their complete fixed payload reservations differed in only four
bytes: the MWO3 data-size word and two memory-end words. The added
`0x008F8540-0x008F8560` range was zero in both states. PAD state and both VU
microcode images were identical. GS state differed in four bytes of the active
ST register at `0x144-0x149`; VU1 working memory and EE render inputs differed.
The resulting PNG changed 10,536 pixels, bounded to the 3D Choji model and
pedestal, while all other 172 normal/padded capture pairs matched exactly.

This establishes that the fixed reservation prevents direct heap-base movement
but does not by itself guarantee identical allocation order. The normal and
padded states contain the same allocation-size/flag multiset in a different
order, which is evidence of an execution-order perturbation rather than a
different resource set. The only established runtime input difference is the
MWO3 header's 32-byte-longer processed range. It is therefore a medium-confidence
inference that the extra loader/cache-processing work perturbed boot-time thread
ordering, which later changed the transform inputs used by the Collection 3D
viewer. The exact transition inside or after `FUN_00100270` remains untraced.

Direct inline patching alone is not an equivalent full-string alternative.
The selected inline NA2 slots are the reason shortening fallbacks exist; the
full official strings do not all fit. Full strings therefore still require
repointing to a pool or another shared resident data area.

## Allocator model

Static analysis identifies the allocator initializer as `FUN_00118730`. Clean
NA2 first requests `0x1718F70` bytes from the lower-level system allocator and
backs the request down in `0x100` steps until it succeeds. It aligns the returned
base, installs two 16-byte sentinels, initializes two free-bin structures, and
caches the largest free gap.

The resident globals are:

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

Each allocated node has a 16-byte header: previous node, next node, aligned
allocation size, and low-nibble flags. `FUN_001180D0` rounds a request plus its
header to 16 bytes. Two segregated-bin families at `0x00607B50` and
`0x00608360` serve gaps below `0x1000` in 16-byte size classes and a general
ordered list serves larger gaps; allocation can fall back to the cached largest
gap. Flag bit `0x4` controls whether a block contributes to the tracked-byte
counter. The meanings of the two bin families and flag classes 0/1/8/9 have not
been named beyond their observed selection behavior.

The analyzer walks the entire sorted linked list rather than trusting the
counters. In every capture it proved all of the following:

- forward and backward links were consistent and acyclic;
- walked live-node count equaled `0x00607390`;
- walked tracked bytes equaled `0x00607388`;
- the cached largest gap and predecessor matched the computed maximum;
- one flag-12 allocation totaling `0x10010` bytes was present but deliberately
  excluded from the tracked-byte counter.

`total_free` is the sum of gaps between live nodes. `largest_free` is the
largest single gap and is the relevant limit for one ordinary allocation.
`fragmentation_bytes = total_free - largest_free`.

## Runtime capacity observations

| Matched screen | Overlay | Vanilla total free | Current total free | Vanilla largest | Current largest | Current fragmentation |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Title | none in Current; BTL in vanilla | `0x101F7F0` | `0x0FBC7A0` | `0x1018330` | `0x0FB52B0` | `0x74F0` |
| Mode select | BTL | `0x0B0B940` | `0x0AAB0F0` | `0x0A6B290` | `0x0A14AF0` | `0x96600` |
| Active Adventure | ADV | `0x07B2D30` | `0x0759260` | `0x0509600` | `0x052B4C0` | `0x22DDA0` |
| Character select | BTL | `0x0CD1560` | `0x0C6F410` | `0x0AFD2E0` | `0x0A04F80` | `0x26A490` |
| Active battle | BTL | `0x0866FB0` | `0x080C050` | `0x084E210` | `0x0803E50` | `0x8200` |
| Collection | ETC | `0x0C89CB0` | `0x0C26C60` | `0x0A7EB80` | `0x0A3A3A0` | `0x1EC8C0` |
| Options | BTL | `0x0B09660` | `0x0AA7340` | `0x0A96680` | `0x09D0350` | `0xD6FF0` |

Current's peak-tracked global reached `0xFC95E0`; vanilla's reached `0xFCE500`.
Individual paired free-space differences do not always equal
`0x63080` because capture timing, live allocation sets, and fragmentation differ
slightly between instances. The structural heap-start difference is the correct
fixed cost of the reservation.

## Whole donor versus compact pool

The current external-translation plan selects 33 shortened mappings: 30 direct
rows and three continuation rows resolved through parent messages. That produces
31 effective string entries, but two entries share the same donor location, so
there are 30 distinct addressed strings: 26 donor strings and four derived
strings. Their exact encoded payload is 1,512 bytes including terminators.

The implemented compact MOD keeps a `0x100`-byte MWo3-compatible header/code
area, packs the 30 distinct strings in stable mapping-ID order with each start
aligned to four bytes, and rounds the final image to 16 bytes. It yields:

| Layout quantity | Bytes |
| --- | ---: |
| Current generated whole donor | `0x30E00` (200,192) |
| Current reserved TEXT envelope | `0x4C300` (312,064) |
| Compact MOD including selected-string pool | `0x720` (1,824) |
| Reclaimed versus current file bytes | `0x306E0` (198,368) |
| Reclaimed inside the TEXT envelope | `0x4BBE0` (310,240) |

At the existing `0x008F3D00` base, the compact MOD ends at `0x008F4420`.
Moving the structural boundary to that exact end recovers `0x4BCE0` bytes
(310,496 bytes, 303.219 KiB) relative to the measured two-file boundary at
`0x00940100`. The earlier `0x16C80` safety gap remains reserved between the
largest overlay and the compact MOD.

The current whole-donor layout already contains `0x32180` zero bytes
(205,184 bytes, 200.375 KiB), but they are split into `0x16C80` and `0x1B500`
runs. Compacting therefore matters first for a resident object larger than
`0x1B500`, for a project that needs a single shared contiguous code/data range,
or as the prerequisite to moving the structural boundary down and reclaiming
most of the fixed reservation for the heap.
