# EE address space and fixed reservations

Static and runtime evidence for the EE address-space map, development injection reservation, and fixed widescreen heap target.

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
| `0x008F3D00-0x008F8550` | `0x4850` | Current compact `228.BIN`; the exact end changes as linked resident fragments change. | Occupied resident code/data. |
| `0x008F8550-0x00940100` | `0x47BB0` | Unused portion of the stable resident-payload envelope for the current 18,512-byte build. | Reserved for future linked payload growth; never use as heap or an independent fixed cave. |
| `0x00940100-0x00940110` | `0x10` | Alignment before the Current heap base sentinel. Vanilla has the analogous padding at `0x008DD080-0x008DD090`. | Reserve for allocator/system alignment; do not use. |
| `0x00940110-0x01FF6000` | `0x16B5EF0` | Current game allocator arena including its two sentinels. Vanilla starts at `0x008DD090` and spans `0x1718F70`. | Dynamic allocation only; fixed addresses are unsafe. |
| `0x01FF6000-0x02000000` | `0xA000` | High-memory system/stack working tail outside the game allocator. It was nonzero and changed across states. | Protected; not an injection cave. |

The final Current heap user base is `0x00940120`; the end sentinel begins at
`0x01FF5FF0`. The clean/vanilla user base is `0x008DD0A0`, so the heap-start
movement is exactly the `0x63080` fixed reservation.

### Development injection reservation

`payload_builder/config.tsv` reserves `0x008F0000-0x008F3D00` (15,616 bytes)
inside the proven Current-only safety gap for temporary C/PNACH development.
The range is below the fixed `228.BIN` load base, above the maximum overlay end,
and below the relocated heap boundary. It is not part of `228.BIN` and is never
included in a release image. A development tool must still verify the exact
Current ISO identity, its resident-payload header, and every hook's clean bytes
before emitting a CRC-named PNACH.

The first imported NUN5 injection experiment instead used
`0x003E4410`, which contains active clean-NA2 data. Its hook executed and
printed successfully, but the overwritten data caused an invalid
`F005FC1D` instruction and a TLB miss at `0x06E42F68` during startup. The same
experiment also demonstrated that ordinary `patch=1` PNACH data writes are
reapplied continuously: a writable `print_pending` initializer was restored
every frame and the message repeated. Mutable injected state must therefore
live in the reserved range without a recurring PNACH initializer; code may use
a source-derived build signature to recognize a newly reloaded build.

The imported `NA2-C.zip` source reviewed for the maintained lab has SHA-256
`8A4D94465C4F7938DCC2D49D3DAA268BDF800AD7E89112B8E09BAA6EE58D289E`.
The exact `NA2-C/` tree supplied on 2026-07-28 is recoverable from commit
`9ef9dc93ec276a08b431192ca0fe798b4f834ada`; commit
`e1a0d9b604009a82afbda18bbf8423988b5e5ce3` removes it from the live checkout.
It is an internally mixed snapshot: its root wrappers and generator constants
still name the earlier MC3/SLES build, its compact linker and C example target
NUN5 `SLPS_258.37`, and its checked-in generated linker outputs came from a
different, larger input set. It is preserved as evidence, not as a runnable
dependency.

The compact NUN5 linker does not replace `WakeupThread`: it inserts a C call
into the function epilogue beginning at runtime `0x001D0578`, then moves the
displaced return sequence into the following words.

Archived NUN5 and clean Current contain the identical five-word window
`DFBF0000 27BD0010 03E00008 00000000 00000000` at
`0x001D0578-0x001D058C`. The historical Lab therefore emitted
`jal injectionLabTick`, `nop`, `ld ra,0(sp)`, `jr ra`, and
`addiu sp,sp,0x10` across that exact guarded window. The native
`jal WakeupThread` at `0x001D0570` remains unchanged. Confidence is **high**
for the source mechanism, byte identity, and file/runtime mapping; runtime
acceptance of each injected C build remains separate.

An earlier isolated PCSX2 2.6.3 startup test of Current identity
`SLOP-NA228 / 7036AA4A` loaded the generated 31-write PNACH and remained
running with the former one-word `0x001D0570` adapter. Read-only PINE
verification observed hook word `0x0C23C000`, compiled code at `0x008F0000`,
read-only data at `0x008F0050`, and the C function's source-derived `.bss`
build ID `0x4B0F31A2` at `0x008F0048`; that final value proves the hooked C
function executed rather than merely being copied into memory. A second source
build with ID `0x58F7CCC7` initialized identically after a clean restart. This
historical test validates the reservation and compiled-code path, but not the
new source-faithful epilogue hook.

The imported VS Code task merely runs `gen_pnach.sh`, which adds PS2DEV tools
to `PATH` and invokes `gen_pnach.py`. The generator compiles imported C objects,
uses Armips to resolve their sections and hook blocks, serializes the resolved
words as `patch=1` entries, and opens its CRC-named PNACH in truncating write
mode. It sends no command to PCSX2. User-observed PCSX2 behavior confirms that
the in-place rewrite itself triggers the emulator's file watcher and automatic
cheat reparse. An earlier bounded clone check used a replacement-style update
and did not reload, so it does not contradict the in-place watcher path. The
now-retired Lab installer preserved the filesystem object and performed the
same truncate/write/flush sequence. The
project's PCSX2 fork adds parameterless PINE opcode `0x10`, which synchronously
dispatches `VMManager::ReloadPatches(true, false, true, true)` on the CPU
thread. The retired Lab sent that opcode after each install and required the
five-byte `OK` reply before returning. Stock PCSX2 rejects the unknown opcode;
the extension does not change PNACH parsing or patch application semantics.

A later Current `SLOP-NA228 / 1236AA28` run separated PNACH reload from
executed-code refresh. `emulog.txt` recorded successful cheat reparses at
runtime timestamps `470.5826` and `492.3710`, but the newly compiled C message
did not execute again after the first message at `437.9280`. The installed and
generated PNACH hashes matched, so the watcher and file update had succeeded.
The remaining failure is consistent with PCSX2 continuing to execute an
already translated host block for the overwritten EE code. This is a useful
negative result: the data-table update demonstrated by the source video does
not prove that overwriting previously executed code is hot-reload safe.

The historical Lab therefore kept a fixed four-instruction dispatcher at
`0x008F0000-0x008F0010`, stores its active C entry pointer at `0x008F0010`,
and alternates compiled C between `0x008F0100-0x008F1F00` and
`0x008F1F00-0x008F3D00`. The already translated dispatcher reloads the pointer
from EE memory on every call, while each changed build enters the other code
bank and receives a fresh translation. Confidence is **high** for the observed
reload-without-code-refresh failure and the alternating-bank JIT-cache
mechanism. On 2026-07-29 the user ran the reload-enabled PCSX2 build and the
Lab end to end and confirmed that the explicit PINE reload path
worked in the running game.

The historical production-aware adapter kept this dispatcher and
alternating-bank mechanism but did not use the imported proof's
ordinary-section linker. It compiled one selected canonical runtime-injector C source through
`ee_c_fragments.py`, applies the source's declared fragment aliases and
relocations, and resolves its external imports against the symbol map belonging
to the exact on-disc Current `228.BIN` hash. It verifies the recorded bytes and
fragment hashes before emitting a PNACH. One ABI-allowlisted resident entry is
replaced by an eight-byte `j 0x008F0000; nop` tail redirect; existing
file-backed caller hooks remain unchanged. The selected C closure is linked
wholly into one bank and overflow is rejected.

On 2026-07-29 the current `font_v2_core` closure occupied `0x1180` bytes and
resolved 15 resident imports. All seven declared top-level Font entries passed
build-only linking against Current `SLOP-NA228 / 092FEF8A` and `228.BIN`
SHA-256
`81DED6B73DAB6B2B72B52FC158FD7F3C9C4A05CE8654EB1A273C81779AAF6E2D`.
Confidence is **high for static identity, relocation, bank-bound, and
entry-guard validation**, but there is no runtime acceptance yet. A lab result
is valid only with the same Current payload and compatible resident writable
state. It does not prove cold initialization, file-backed integration, overlay
lifetime, release-payload placement, or callers not exercised through the
selected entry.

On 2026-07-30, the maintained workflow replaced PNACH transport and alternating
banks with `scripts/injection/build.py` and
`scripts/injection/apply.py`. The builder emits one addressed `fragment.bin`
and `manifest.json`; the applier synchronously pauses the VM, writes one fixed
development reservation and exact-guarded callers through PINE, invokes the
custom cache-only opcode `0x14`, and restores the prior running/paused state.
Two different root C builds were applied consecutively to the same reservation
in an isolated worker without restarting PCSX2. Confidence is **high** for this
direct-memory transaction and readback; its development evidence remains
narrower than a clean integrated build. That validation used custom PCSX2
source commit `9cf3890b8e98bed6242d66d764732177dd78b450`; the tested Windows
executable had SHA-256
`A2101F8FC9F3ADF9C5E8A936296F8C2D2A383B67495A0425AFBC62ECDB2607F9`.
The user flow `na228 c && na228 w` was subsequently validated from a stopped
VM. Waiting for both the loaded root hook and resident `MWo3` marker prevented
the initial direct-memory application from being cleared later during boot;
delayed readback confirmed that the immutable fragment bytes and guarded
caller remained active.

### Widescreen heap target

The official clean-NA2 widescreen write targets `0x00AF3694`, the first
`1.0f` field in the stable structure context
`0000BF01 00000000 00000045 FFFFFF44 0000803F 0000803F 00008043 00004043`.
This structure is allocated at a fixed offset from the game heap boundary, so
its absolute address moves when the resident-payload reservation changes.

The earlier two-file Current captures moved the boundary by `0x63080` and
contained the exact structure at `0x00B56714` in every checked paired state.
The compact `SLOP-NA228` build with ELF CRC `F9FF71C8` ends its resident
reservation at `0x008F43F0`, `0x17370` bytes above vanilla's `0x008DD080`.
Accordingly, the working target is `0x00B0AA04`; three current savestates
(slots 01, 09, and 10) contained the exact structure there with the target
field still equal to `1.0f`, while the old address was empty.

Confidence is **high for this exact build identity**. The address is not a
fixed game constant: recalculate and validate it whenever the linked
resident-payload end changes.

Rendering patch `ELF-R001` replaces the shared rendering-state writer at
boot-ELF offset `0xEDC0`. It forces `0.75f` at object offset `0x274` through
the live object pointer while preserving the caller-provided vertical scale at
`0x278`. This is the verified good-enough file-backed implementation and
affects every call through that writer.

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
