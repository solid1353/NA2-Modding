# EE runtime memory map

This record maps NA2's 32 MiB Emotion Engine address space for injection-capacity
decisions. It combines static analysis of the resident ELF and MWo3 overlays
with matched PCSX2 savestates from clean NA2 and the integrated NA2.28 Current
image. The runtime evidence was captured on 2026-07-22.

The results are representative, not an absolute proof of every possible peak.
The eight matched states cover title, mode select, active Adventure, character
select, active battle, Shop, Collection, and Options. They do not include a
result screen, save/load activity, or long transition stress. Active Adventure
was the tightest sampled state, so the absent result capture does not affect the
reported worst-observed value.

Exact inputs and observations are preserved in:

- [`capture_inventory.tsv`](ee_runtime_memory_map/capture_inventory.tsv):
  savestate identities, sizes, and SHA-256 hashes;
- [`runtime_observations.tsv`](ee_runtime_memory_map/runtime_observations.tsv):
  validated allocator, overlay, and capacity readings for all 16 captures;
- `@work/EE Runtime Memory Map/savestates/2026-07-22/`: preserved task-owned
  copies of the 16 user captures used by the maintained analyzer.

The analyzer's larger JSON output and per-state region-hash report were
disposable derivations. They were pruned after the reusable observations and
conclusions above were promoted.

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
[`external_string_payload.md`](external_string_payload.md) for the
decompilation and integration evidence.

The implemented compact architecture therefore:

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

Direct inline patching alone is not an equivalent full-string alternative.
The selected inline NA2 slots are the reason shortening fallbacks exist; the
full official strings do not all fit. Full strings therefore still require
repointing to a pool or another shared resident data area.

## EE address-space map

Addresses use the EE physical RAM view saved as `eeMemory.bin`; every range is
end-exclusive.

| Address range | Size | Lifetime and owner | Injection classification |
| --- | ---: | --- | --- |
| `0x00000000-0x00100000` | `0x100000` | Low system/runtime region outside the NA2 ELF image. Every capture contained changing nonzero data. | Protected; not free. |
| `0x00100000-0x00607380` | `0x507380` | File-backed resident NA2 ELF code and static data. The single resident load segment is RWX and also contains the six static thread stacks. | Resident and occupied. Use only individually proven caves. |
| `0x00607380-0x006B3F00` | `0xACB80` | Zero-filled tail of the resident ELF load segment: BSS, allocator globals, and other mutable/static runtime storage. | Resident and occupied; zero at load does not mean free. |
| `0x006B3F00-0x008DD080` | `0x229180` | Reused MWo3 overlay window for `BTL.BIN`, `ADV.BIN`, and `ETC.BIN`. Contents change with phase. | Never a global fixed injection range. Phase-only use requires a proven overlay/state guard. |
| `0x008DD080-0x008F3D00` | `0x16C80` | Current-only safety gap above the maximum overlay end. Zero and hash-stable in all eight Current captures. | 93,312-byte persistent fixed candidate while the structural reservation remains active. |
| `0x008F3D00-0x00924B00` | `0x30E00` | Current generated `TEXTENG.BIN`; hash-stable in all Current captures. | Occupied resident data. |
| `0x00924B00-0x00940000` | `0x1B500` | Unused portion of the current TEXT envelope. Zero and hash-stable in all Current captures. | 111,872-byte persistent fixed candidate only if a shared layout prevents later TEXT growth. |
| `0x00940000-0x00940100` | `0x100` | Current generated `MOD.BIN`; hash-stable in all Current captures. | Occupied resident code/data. |
| `0x00940100-0x00940110` | `0x10` | Alignment before the Current heap base sentinel. Vanilla has the analogous padding at `0x008DD080-0x008DD090`. | Reserve for allocator/system alignment; do not use. |
| `0x00940110-0x01FF6000` | `0x16B5EF0` | Current game allocator arena including its two sentinels. Vanilla starts at `0x008DD090` and spans `0x1718F70`. | Dynamic allocation only; fixed addresses are unsafe. |
| `0x01FF6000-0x02000000` | `0xA000` | High-memory system/stack working tail outside the game allocator. It was nonzero and changed across states. | Protected; not an injection cave. |

The final Current heap user base is `0x00940120`; the end sentinel begins at
`0x01FF5FF0`. The clean/vanilla user base is `0x008DD0A0`, so the heap-start
movement is exactly the `0x63080` fixed reservation.

The clean ELF's first `PT_LOAD` begins at file offset `0x100`, maps at
`0x00100000`, has file size `0x507380`, and has memory size `0x5B3F00`.
Consequently the file-backed resident image ends exactly at `0x00607380` and
the following `0xACB80` bytes are its loader-cleared memory tail. Three further
program headers declare the mutually exclusive BTL, ADV, and ETC memory spans
from their shared `0x006B3F00` base.

Disc files under `MODULES/` are IOP executables and do not occupy this EE
address space. Their EE-side command structures, buffers, and static CRI thread
stacks are represented here through the resident image and game heap instead.

The resident ELF contains a previously proven 108-byte zero cave at
`0x00607314-0x00607380`. The Current bootstrap owns that whole range and its
hash was stable in all eight Current captures; residual zero bytes inside it
must not be treated as unassigned capacity. The allocator globals begin
immediately afterward at `0x00607380`.

## Overlay lifetimes and phase-only space

Each loaded overlay begins with `MWo3` at `0x006B3F00`; header word 1 identifies
the kind. The effective ends below come from the binary layout and were matched
against the savestate headers.

| State at overlay base | Kind | Effective end | Temporarily unused before `0x008DD080` |
| --- | ---: | ---: | ---: |
| No overlay | 0 | `0x006B3F00` | `0x229180` (2,265,472 bytes) |
| `BTL.BIN` | 1 | `0x008DD080` | `0x0` |
| `ADV.BIN` | 2 | `0x008C7200` | `0x15E80` (89,728 bytes) |
| `ETC.BIN` | 3 | `0x006E4E00` | `0x1F8280` (2,065,024 bytes) |

This slack is not persistent free memory. A later overlay transition can
overwrite it, and `BTL.BIN` consumes the entire reserved window. It is unsuitable
for unguarded PNACH writes or resident code/data. A phase-local experiment may
use it only when overlay identity, load state, and lifetime are explicitly
guarded.

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
| Shop | ETC | `0x1042B10` | `0x0FDFA50` | `0x0AFD1A0` | `0x0A95A40` | `0x54A010` |
| Collection | ETC | `0x0C89CB0` | `0x0C26C60` | `0x0A7EB80` | `0x0A3A3A0` | `0x1EC8C0` |
| Options | BTL | `0x0B09660` | `0x0AA7340` | `0x0A96680` | `0x09D0350` | `0xD6FF0` |

Current's peak-tracked global reached `0xFC95E0`; vanilla's reached `0xFCE500`.
Individual paired free-space differences do not always equal
`0x63080` because capture timing, live allocation sets, and fragmentation differ
slightly between instances. The structural heap-start difference is the correct
fixed cost of the reservation.

## Stacks and thread-owned memory

Six resident CRI/ADX thread stacks are statically allocated inside the main ELF:

| Range | Size |
| --- | ---: |
| `0x003D6B20-0x003D7320` | `0x800` |
| `0x003D7320-0x003D8320` | `0x1000` |
| `0x003D8320-0x003D9320` | `0x1000` |
| `0x003D9320-0x003DA320` | `0x1000` |
| `0x003DA320-0x003DC320` | `0x2000` |
| `0x003DC320-0x003DE320` | `0x2000` |

The corresponding creation paths are `FUN_0012E6B0` through
`FUN_0012E9B8`. Separately, `FUN_001CFE50` enforces a requested dynamic-thread
stack minimum of `0x800`, adds `0x400`, and obtains the backing memory through
the game allocator before `CreateThread`. These stacks therefore contribute to
ordinary heap occupancy and have thread-specific lifetimes.

The `0x01FF6000-0x02000000` tail is outside that allocator and changed across
the captures. Register-level ownership of every byte was not established, but
its observed use and position make the conservative classification clear:
leave it to the system/stack runtime.

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

## Safe-use constraints

- Fixed injection into the two Current zero regions is valid only while the
  structural boundary patch remains active and the shared layout explicitly
  owns the chosen subrange. The same addresses are heap memory in vanilla.
- Loaded executable code requires correct EE instruction/data cache maintenance;
  stable RAM alone is not sufficient.
- Do not use overlay slack for permanent data or unguarded fixed-address PNACH
  writes. `BTL.BIN` can overwrite the whole overlay reservation.
- Do not use allocator gaps as fixed caves. Allocate through the game allocator
  and keep the pointer for the required lifetime.
- Do not use the high `0xA000` tail. It is outside the allocator but observably
  active.
- Worst-observed headroom is not a formal maximum-use proof. Recheck results,
  save/load, repeated transitions, and any future feature that materially
  changes resource loading before treating the sampled margin as a release
  guarantee.

## Provenance and reproduction

Runtime analysis uses the maintained
`scripts/research/ee_memory_map/analyze_savestates.py` tool. It extracts the
32 MiB `eeMemory.bin` member from each PCSX2 savestate, validates the allocator,
identifies the overlay, and hashes fixed regions. Focused synthetic tests cover
identity parsing, allocator invariants, overlay interpretation, and region
reporting.

Static allocator, stack, and overlay analysis uses the maintained Ghidra 12.1.2
NA2 export under `@analysis/disassembly/NA2/exports/SLPS_258.37/`. The whole-
TEXTENG structure and used-string analysis is canonical in
[`external_string_payload.md`](external_string_payload.md), updated by
commit `cb7d1d7`. The compact-pool calculation was independently reproduced from
the active hash-pinned string-patcher plan and its 30 distinct generated
string locations.

No original source media was modified. No ISO or binary was rebuilt for this
investigation.
