# Startup sequence

Startup, Continue Save/Load, main-menu loading presentation, and audio
initialization in retail NA2 (`SLPS-25837`).

## Research coverage

- **Assigned scope:** establish the retail ELF bootstrap, resident startup state
  machine, initial managers and tasks, readiness barriers, Continue and
  Save/Load path, loading presentation, and handoff into the main menu.
- **Exploration depth:** the ELF entry, nine-call SDK prelude, first resident
  bootstrap layer, sound readiness/command handoff, post-splash cleanup, and
  complete loading-presentation service family have direct static coverage.
  Call paths across card check, splash, title, Save/Load, loading, and
  main-menu states were traced and sampled at runtime.
- **Confirmed coverage:** the ELF identity and entry-point side effects, initial
  task handoff, blocking card check, splash ownership, the two asynchronous
  readiness gates, Continue's shared Save/Load controller, record metadata, the
  native main-menu loading controller, its resource ownership and completion
  phases, initial service allocation order, and the eager audio bottleneck are
  established. Entry arguments distinguish a loaded word from a passed pointer.
- **Unresolved or untested:** stripped SDK command/handler names, meanings of
  most sound RPC commands and descriptor fields, scheduling/timing between
  independent tasks, lower-initializer failure reachability, every physical
  memory-card failure case, and indirect voice consumers. Static ignored error
  returns do not establish a normal-play failure.
- **Deliberate exclusions and overlap:** The save record, descriptor table and
  load worker belong to [Save data](save_data.md); player-voice descriptors to
  [Character asset tables](character_assets.md#voice-descriptors-and-filename-number-lists).
  General [task mechanics](../runtime/task_system.md),
  [render submission](../runtime/render_submission.md),
  [UI transitions](../runtime/ui_animation.md),
  [file services](files/runtime_services.md), and
  [front-end navigation](mode_flow.md) retain their separate ownership.
- **Evidence limitations:** sampled timing establishes ordering and observed
  bottlenecks, not a fixed duration on every host or storage device. Read-only
  static analysis cannot establish asynchronous completion timing or exact
  visible-frame boundaries; frame and duration interpretations use 30 FPS.
  Claims about absent teardown are limited to the named boot/front-end paths
  and recovered direct callers, not arbitrary indirect calls or a whole-game
  absence proof. Game-function addresses refer to the resident ELF; kernel
  copy destinations are identified separately.

## Retail ELF entry and resident bootstrap

The clean resident identity and address conversion follow
[Retail game file identities](files/file_identities.md). Static analysis
identifies its sole declared entry as `entry` at `0x00100008` and its loaded
`SECTION4` as `0x00100000..0x0060737F`.

`entry` performs these observed operations in order:

1. It clears the integer, accumulator, and floating-point registers, executes
   `sync 0x10`, and clears `FCSR`.
2. It zeroes the upper-exclusive range
   `0x00607380..0x008DD080`, beginning immediately after the loaded ELF block.
3. It sets `gp` to `0x0060A9F0` and invokes `InitMainThread` (`0x3C`) with
   stack `-1`, stack size `0x8000`, startup-argument storage `0x00607A00`, and
   exit entry `0x00100220`. It takes the returned stack pointer, then invokes
   `InitHeap` (`0x3D`) with `0x008DD080` and `-1`. The memory-layer interpretation
   is owned by [EE allocator](../runtime/ee_memory_map/allocator_and_capacity.md).
4. It calls `FUN_00168058`, whose observed call order is
   `FUN_00167E08`, `FUN_00167F48`, `FUN_00168538`,
   `FUN_001686B0(2)`, `FUN_001688F0`, `FUN_0015EAB8`,
   `FUN_00168180`, `FUN_00167670`, and `FUN_00169D70`.
5. It calls `FlushCache(0)`, enables interrupts, loads the word at
   `0x00607A00` into `a0`, and passes the address `0x00607A04` in `a1` to
   `FUN_001C13F0`. It does not load the word at `0x00607A04` as a second scalar.
   Bytes `00 00 44 8C` at `0x00100204` are `lw a0, 0(v0)`; bytes
   `04 00 45 24` in the call's delay slot at `0x0010020C` are
   `addiu a1, v0, 4`.
6. If that function returns, `entry` tail-calls `FUN_001787B0` with its return
   value. `FUN_001787B0` walks registered callback lists, invokes the callback
   at context offset `+0x3C` when present, and calls
   `thunk_FUN_00168458`, which performs the memory-size-selected TLB setup
   through `FUN_001677F8` and calls `_Exit`. This is library-exit handling;
   the ordinary path remains in `FUN_001C13F0`'s permanent loop and never
   reaches it.

### SDK prelude

The nine-call `FUN_00168058` sequence precedes both the game arena and the game
task list. Directly observed responsibilities are:

| Call | Observed work |
| --- | --- |
| `FUN_00167E08` | Creates the semaphores named `SceKernelLibc` and `SceKernelLibcEh`, storing their IDs at `0x003F8030/0x003F8034`. |
| `FUN_00167F48` | Installs local handlers for syscall selectors `0x83/0x5A`, invokes the selector-`0x83` wrapper with start/end arguments `0x80000000/0x80080000` and two pattern-address arguments, and stores the resulting shared address at `0x003F8018`. The handler's wider semantics are unresolved. |
| `FUN_00168538` | Under counter-3 MODE bit `0x100 == 0`, copies resident payloads to `0x80076000` (`0x740` bytes) and `0x00082000` (`0x28` bytes), flushes caches 0/2, and installs syscall-table entries. These are writes performed by retail code, not bytes read from a live kernel during this research. |
| `FUN_001686B0(2)` | Initializes 128 `0x40`-byte records in `0x00613380..0x0061537F`, installs INTC handler `0x00168C50` for source `0xB`, configures counter 2, and enables that interrupt source. |
| `FUN_001688F0` | Starts counter-2 timing if MODE bit `0x80` is clear, initializes its time state through `FUN_00168EF8/FUN_00168A00`, and returns 1 if already active. |
| `FUN_0015EAB8` | Creates the independent `SceKerneltopThread` dispatch service and changes the root caller's priority to 1; its queue and lifetime belong to [EE kernel threads and synchronization](../runtime/kernel_threads_and_sync.md#separate-kernel-dispatch-queue-and-semaphore). |
| `FUN_00168180` | Calls `FUN_00168118`, which temporarily changes OSD configuration version bits, rereads them, and restores the original word. A reread version field of zero selects a `0x7A8`-byte copy to `0x80074000`, cache flushes, and syscall installation. |
| `FUN_00167670` | Copies `0x330` bytes to `0x80075000`, flushes caches 0/2, installs another syscall family, and stores selector-3's returned address at `0x003F7D40`. |
| `FUN_00169D70` | Clears words `0x003F8FC8/0x003F8FCC` and a `0x200`-byte state area at `0x00615788`. It is a tail call after the prelude restores its stack. |

The prelude ignores its initializers' returned error values. The static
inspection establishes its calls, conditions, address ranges, and stores;
neither the installed kernel payloads' full behavior nor a live kernel image
was investigated. Their stripped source names remain unresolved.

`FUN_001C13F0` calls the following first-layer initializers before creating the
initial tasks. The roles below describe observed work; the stripped original
source names remain unknown:

| Order | Original symbol/address | Observed side effect |
| ---: | --- | --- |
| 1 | `FUN_00118730` at `0x00118730` | Acquires an arena through `FUN_00179850`, reducing the initial `0x01718F70` request by `0x100` until it succeeds; installs 16-byte-aligned heap boundaries and initializes allocator records at `0x00607B50` and `0x00608360`. |
| 2 | `FUN_00100230` at `0x00100230` | Calls `FUN_00119A90`, which invokes all 20 function pointers in upper-exclusive `0x005D9CF0..0x005D9D40`, then calls the empty `FUN_0011B0B0`. This is a static-initializer walk, not a task dispatcher. |
| 3 | `FUN_001BD2B0` at `0x001BD2B0` | Resets the IOP from `cdrom0:\MODULES\IOPRP300.IMG;1`, waits for reset/synchronization, reinitializes services, and loads the nine module images in `MODULES.BIN` through `FUN_001BD0B0`. |
| 4 | `FUN_00105FC0` at `0x00105FC0` | Constructs the `0x530`-byte system/input context at `0x006073FC`, configures counter 0 (`MODE=0x83`, `COUNT=0`), prepares display/render state, and constructs the `0x140`-byte renderer at `0x006073D0`. |
| 5 | `FUN_001DA0F0` at `0x001DA0F0` | Loads `sndbase.irx` through the shared module-path loader `FUN_001BCFF0`. |
| 6 | `FUN_001DA130` at `0x001DA130` | Binds two RPC clients using IDs `0x12346/0x12347`, sends the initial sound-service commands, and clears `0x00607594`. The sound-service role follows the module/call sequence; command meanings beyond numeric arguments are unresolved. |
| 7 | `FUN_001C14F0` at `0x001C14F0` | Calls the memory-card library initializer `FUN_001756B0`; only a zero result constructs the `0x438`-byte lower card context at `0x006074D8` and sets its `+0x434` field to `0x67`. |
| 8 | `GetThreadId` / `ChangeThreadPriority` | Stores the current thread ID at `gp-0x351C` and changes its priority to `0x78`. |
| 9 | `FUN_001BD380` at `0x001BD380` | Loads `cri_adxi.irx`, initializes the FLIST cache and ADX services, mounts `DATA.CVM`, and loads its ROFS root; detailed ownership is in [Resident file and archive services](files/runtime_services.md). |
| 10 | `FUN_001D04F0` at `0x001D04F0` | Constructs the scheduler/list-head task at `0x001D0590`, priority `0x18`, requested stack `0x1000`; starts it immediately and publishes head/tail slots `0x00607504/0x00607508`. |

The nine-module bootstrap allocates temporary `0x4D000`-byte buffers in EE and
IOP memory, reads the complete fixed-size `MODULES.BIN`, transfers it by SIF
DMA, and invokes the module loader at the nine offsets in `0x003FB890`.
After those calls, it frees both buffers through `FUN_00117C40/FUN_00166180`.
Those allocations are not the persistent file-cache, card, sound, or renderer
contexts. Module-path loads later append the configured suffix to the selected
IRX name and retry a negative loader result indefinitely.

It then creates a descriptor through
`FUN_001D0090(0x00113530, 0x19, 0x800)`, sets bit `0x8` in its halfword at
`+0x12`, and submits it through `FUN_001CFF00(descriptor, 0)`. It creates a
second descriptor through `FUN_001D0090(0x001E0EE0, 0x23, 0xC000)`, copies the
two arguments from `entry` to descriptor offsets `+0x28` and `+0x2C`, and
submits it the same way. It thereafter loops over `FUN_001083A0` on the pointer
at `gp-0x35F4` followed by `FUN_001D0560`.

The task interpretation is directly established by `CreateThread`,
`StartThread`, `ReferThreadStatus`, and the linked scheduler family.
The `0x001E0EE0` task is the startup game task with high confidence because its
downstream flow constructs the persistent memory-card and save objects and
reaches the splash/title state machine below.

### Initial task handoff

[Resident task system](../runtime/task_system.md) owns the task record layout,
start/defer rules, scheduler barriers, wait/wake APIs, and destruction. Raw
instructions establish `FUN_001D0090`'s pointer return, which the decompiler
omits.

The initial list is the priority-`0x18` scheduler/head followed by `PAD` at
`0x00113530` and `MOTHER` at `0x001E0EE0`. Their requested stacks
`0x1000/0x800/0xC000` become `0x1400/0xC00/0xC400` under the task allocator.
Submission flag zero queues both ordinary entries because their numeric
priorities `0x19/0x23` are smaller than the root thread's `0x78`; the scheduler
starts them. This establishes list/start-call order, not measured interleaving
of their first instructions. The root continues pacing through `FUN_001083A0`
and awakening the scheduler through `FUN_001D0560`.

The PAD entry adds policy mask `7` to the creator's mask `8`, opens the two
controller records at system-context `+0x1C/+0x94`, and services both until byte
`0x006073B0` becomes `2`. It closes both ports and ends the pad library before
publishing value `3`; its ready publication is value `1`. `MOTHER` installs a
no-op cleanup callback at `0x001E0ED0` and runs the permanent outer front-end
loop. Neither initial task supplies a central update/draw callback. Their
service lifetime differs from the temporary card-check, splash, title, and
menu-loading controllers below.

## Initial memory-card check

Before constructing the splash and starting the resource loaders,
`FUN_001E0EE0` constructs the persistent memory-card worker and save-data
object, then calls `FUN_001E71B0` at `0x001E0FA0` (ELF file offset `0xE10A0`).
The call bytes are `6C9C070C`; its delay slot is a NOP.

`FUN_001E71B0` creates a temporary controller and runs `FUN_001E72E0`.
That routine starts the card worker in mode zero and waits one frame per loop.
Worker statuses `0x24..0x27` display an initial confirmation through
`FUN_001E74E0`; choosing Yes permits the loop to finish. Worker status `1`
also completes it. The routine stops the worker before returning, and the
temporary controller is destroyed. Continue later starts a separate worker
session for loading through the same persistent worker object.

A sampled no-card confirmation had worker status `0x24`, result class `3`,
and mode zero, with no main-menu object constructed. This establishes that the
initial blocking check is separate from the later Continue Save/Load screen.

## Splash controller

`FUN_001E7E30` loads `logo.ccs` through `FUN_00116DE0` before the
splash loop. `FUN_001E7EB0` retrieves that loaded container through
`FUN_001AA450`. The filename pointer is at `0x00603060` and points to
`0x004049F0`. The root `LOGO.CCS` member occupies 53,973 compressed bytes
and expands to 921,452 bytes. It contains four 512×512 indexed textures:
the notice uses 16 colors, while the Bandai, Bandai Namco, and CRIWARE
textures each use 256 colors.

The resource loader opens the name through `FUN_001BE450` and obtains its
decompressed size through `FUN_001BE9B0`. The former accepts device paths
through `FUN_001BE1F0`; the latter looks up size metadata in the mounted
ROFS tree through `FUN_001BCA00`. **Inference:** the native CCS decode path
therefore has a decompressed size only for files inside the mounted ROFS tree.

`FUN_001E00E0` draws the selected splash object's texture pointer at `+0x1C`
through the resident renderer. It covers coordinates `(0, 0)` to
`(512, 384)` with vertically reversed texture coordinates spanning
`1..512`; the object's float at `+0x18` controls opacity. State `7` skips
drawing. This path does not require the later main-menu resources.
The routine binds the texture at render-manager offset `+0x128`, enables
texturing through `FUN_0010CAA0(manager, 1)` and
`FUN_0010C9E0(manager, 0)`, and submits a type-5 quad. The draw context
stores texture coordinates at `+0x130` and `+0x134`, marks them active with
flag `0x80000` at `+0x170`, and submits each vertex through `FUN_001822B0`.

The native solid-rectangle path in `FUN_001DC1A0` calls `FUN_0010D6A0`
before setting up primitive type `5`. With argument zero, that renderer reset
clears the manager's bound texture pointer at `+0x128`, so a native solid
rectangle does not inherit the texture bound by `FUN_001E00E0`.

`FUN_001E0390` constructs four splash objects using, in order,
`TEX_logo_notice_pss`, `TEX_logo_bn_pss`, `TEX_logo_b_pss`, and
`TEX_logo_adx_pss`. `FUN_001E0980` advances them. Its caller at `0x001E10A0`
treats return value `1` as completion, destroys the controller normally, and
continues toward the title animation.

| Visible phase | Main state | Splash index |
| --- | ---: | ---: |
| Notice | 0 | 0 |
| Bandai Namco | 0 | 1 |
| Bandai | 0 | 2 |
| CRIWARE | 0 | 3 |
| Title animation | 3 | absent |
| Interactive title | 3 | absent |

The main-state pointer is at `0x006075C0`; the splash-pointer slot is at
`0x006075DC`. `FUN_001DE6F0` is the post-splash sequence dispatcher.

## Startup readiness barrier

The startup loop requires three simultaneous completion values:

- the splash controller result;
- the ROFS/data-ready byte at `0x006074A0`;
- byte `+0x1C` of the startup-resource object referenced at `0x0060755C`.

Startup mounts `DATA.CVM` as `VOL`, loads its root synchronously, and
creates the `Load ROFS_Data` worker at `FUN_001BD970`. The worker recursively
loads the 20 directories described by `GZLIST.TXT` and sets `0x006074A0` only
after their metadata is ready; it does not preload the 2,310 CCS payloads.

After all three values are ready, native code writes state `2` at `0x001E11CC`.
The title dispatcher at `0x001E1240` calls `FUN_001DE840`; result `1` selects New
Game and result `2` selects Continue. The caller then enters main state `4` with
the corresponding substate.

### Sound-service setup before readiness

The pointer at `0x0060755C` is specifically the `0x18C`-byte sound-control/RPC
object constructed by `FUN_001D9E70`, not the archive/stream manager. The latter
is a separate `0x718`-byte allocation at adjacent slot `0x00607558`. Their
initialization order in `FUN_001D2570` is:

1. Construct the control object and a separate `0x78`-byte request/state object
   at `0x0060753C`; name this task `SOUND` and set task policy mask `3`.
2. Send the initial RPC commands through `FUN_001DA620`, retaining the returned
   destinations from commands `0x8010`, `0x8100/1`, and `0x8100/2`.
3. Publish the path strings `cdrom0:\DATA\` and `snddata.bin` through commands
   `0x1340/0x1350`, then run `FUN_001DA3C0`.
4. Construct/configure the archive/stream manager through `FUN_001D7A30` and
   perform eager archive/index initialization through `FUN_001D6550`.
5. Set control byte `+0x1C` to `1`, submit `SND_RPC` at `0x001D28C0` with
   priority `0x71`/requested stack `0x1000`, and submit `SND_RPC2` at
   `0x001D29F0` with priority `0x72`/requested stack `0x800`.
6. Set the control value through `FUN_001D7A90(0x100)`, then continually yield
   and transfer each nonempty command buffer through `FUN_001D27C0`.

`FUN_001DA3C0` allocates `0x2F40` IOP bytes and builds the `SNDDATA.BIN`
descriptor at `0x006B23C0`. It sends command `0x9210`, sets control byte
`+0x1D`, and yields until returned word `0x006B2300` equals descriptor word
`+0x0C` (`0x0007CAC0`). It clears `+0x1D`, registers the command-buffer chain
through `FUN_001DABC0`, and sends `0x9050`, `0xA0`, and `0xB0`. This handshake
precedes the index loads; archive completion alone is not the entire sound
startup dependency. An IOP allocation failure returns `-1`, which
`FUN_001D2570` ignores. Readiness is therefore a completed-sequence flag, not a
checked success aggregate for every lower initializer.

`FUN_001DA620` refuses commands while `+0x1D` is set or while its RPC busy byte
`+0x4C` is already `1`; otherwise it holds `+0x4C` during the call. Numeric
commands `0xB0`, `0x9200`, `0x9210`, and `0x9400` additionally poll the selected
RPC client until it is idle. The two fixed clients are selected through
`0x003FE2F0`, not through an overlay-local object. `FUN_001D27C0` transfers
three `0x100`-byte command buffers, then clears each buffer's pending word.
`FUN_001DA560` flushes cache and starts SIF DMA; its status polling is bounded
at 10,001 iterations and records a timeout flag rather than withholding the
startup ready byte.

`SND_RPC` updates sound-control requests and status once per scheduler yield;
both it and `SOUND` are permanent loops. `SND_RPC2` first waits for control
`+0x1C`, then yields, checks control byte `+0x21`, and calls `FUN_001D9930` only
when that byte is nonzero. That routine visits all three channels in each of
the two stream families through `FUN_001D70A0`. Ghidra has no function at
`0x001D29F0`; the complete `0x80`-byte task body was read as raw instructions.
Its decisive call bytes are `EC 68 07 0C` at `0x001D2A30`
(`FUN_001DA3B0`, readiness getter) and `4C 66 07 0C` at `0x001D2A60`
(`FUN_001D9930`), with the byte-`+0x21` load at `0x001D2A54`. All backedges
are within that body.

Archive and codec/player initialization allocate their backing before the
barrier: `FUN_001D6AA0 -> FUN_001D6190` derives the four archive/index buffer
sets from their sentinel tables; `FUN_001D6810` creates three type-2 players
with `0x1C1E4` backing each and three type-1 players with `0x11924` backing and
`0x3000` supplementary backing each. Its failure result is also ignored by
`FUN_001D7A30`. `FUN_001D6980/FUN_001D6A30` reset individual players; their
bodies neither free the manager nor close the archive buffers. No sound-task
termination or whole-manager destruction occurs in the covered boot-to-title
path. Stream completion and codec/AFS details belong to
[Audio and video replacement](files/audio_video_replacement.md).

### Post-splash cleanup and front-end services

Barrier completion is followed by additional work before the permanent
opening/title/front-end loop. `FUN_001E0EE0` executes this sequence at
`0x001E1138..0x001E11D4`:

1. `FUN_001E0CB0` destroys the splash controller. `FUN_001E0870` visits its
   children in reverse order, resets and destroys each child, frees it, sets
   the child count to zero, and calls `FUN_001E7EE0` to release `logo.ccs`.
   The outer destructor frees the vector's backing, then the `0x14`-byte root,
   and clears pointer slot `0x006075DC`. The decompiler omits the vector-free
   argument: bytes `08 00 24 8E` at `0x001E0C60` load it from vector `+0x08`;
   the vector is embedded at controller `+0x04`. Passing destructor argument
   `-1` prevents freeing that embedded vector object separately.
2. `FUN_001E7F50` synchronously loads each missing member of the five common
   provider paths. Their exact inventory and resource-dependency edges belong
   to [Common providers](files/asset_dependencies.md#common-providers-and-battle-preparation).
   These payload loads occur after the directory-metadata/audio/splash barrier;
   that barrier does not certify their completion.
3. Clear the system context's packed value through `FUN_001074D0(context, 0)`,
   reset the renderer through `FUN_0010D6A0(renderer, 0)`, and yield through
   `FUN_001D0000(MOTHER, 2)`.
4. Bind the font manager at `0x00607470` to its default renderer at
   `0x00607474`, set its alpha through `FUN_00186B90(manager, 0x80)`, and
   clear the second global four-slot transition pool at `0x00607464` through
   `FUN_00183610`. Clearing slots does not free that pool.
5. Pass system-context counter `+0x194` to `FUN_001801A0`, initialize random
   state through `FUN_00180060`, reset the root pacing threshold through
   `FUN_00107560(context, 2)`, and finally write outer state `2`.

The draw services used here were already installed by `FUN_00105FC0` before
the scheduler and game task. `FUN_00185F50` creates the font manager, its
default/alternate render contexts, and both `0x98`-byte transition pools.
`FUN_00107F80` creates the display packet pool; `FUN_00106240(0x400)` creates
the ordering-node pool. [Render submission](../runtime/render_submission.md)
and [UI animation](../runtime/ui_animation.md) own those allocators and slot
contracts. Startup binds/resets them rather than reconstructing them after
each title return.

The outer state object, `0x60`-byte card worker, and `0x2400`-byte live save
object are allocated once by `MOTHER` before the initial card check. The lower
card context already came from the earlier root bootstrap. The covered outer
loop never frees those persistent objects, the sound-control/stream manager,
or the system/render contexts. In contrast, splash, title, front-end manager,
and loading-presentation allocations have their own finite lifetimes.
[Resident front-end and mode flow](mode_flow.md#allocation-lifetimes) owns the
title/manager/callback lifetime split; returning from that manager to title is
not a second native bootstrap or a teardown of the persistent services above.

## Continue and shared Save/Load controller

Continue allocates a `0x28`-byte parent through `FUN_001E3DB0`. The constructor
resets it through `FUN_001E3EC0`, starts the global memory-card worker through
`FUN_001E1CA0(worker, 2)`, and allocates a `0x44`-byte UI child at parent
offset `+0x24`. `FUN_001E3F00(parent, 1)` updates it once per frame.

| Result | Native Continue behavior |
| ---: | --- |
| `0` | Continue updating and draw the Save/Load child. |
| `1` | Record load success, destroy the controller, and start the main-menu loader. |
| `2` | Record no-load completion and destroy the controller. |

`FUN_001E3E20` stops the worker, frees the child, resets the parent, and frees
it. A successful load retains the native save-dependent setup through
`FUN_001076C0`, `FUN_001E36C0`, and `FUN_001F4030`.

The global worker pointer is at `0x006075F4`. Its relevant `0x60`-byte layout is:

| Offset | Meaning |
| ---: | --- |
| `+0x00..+0x3F` | Four `0x10`-byte record descriptors. |
| `+0x40` | Memory-card port. |
| `+0x44` | Record index. |
| `+0x48` | Requested operation. |
| `+0x4C` | Detailed status. |
| `+0x50` | Result class. |
| `+0x54` | Mode hint; `1` is load. |
| `+0x58` | Latest lower-level card classification. |
| `+0x5C` | Worker thread handle. |

The four record descriptors follow
[Descriptor table](save_data.md#descriptor-table); their play time is in
30 Hz ticks. `FUN_001E6370` renders the date and converts play time using 108,000 ticks per hour, 1,800 per minute, and 30 per
second, capped visually at `999:59:59`.

The timestamp uses the PS2 clock's fixed JST representation. PS2SDK conversion
applies `configured timezone - 540 minutes` plus the configured daylight-saving
hour. `GetOsdConfigParam` is linked at `0x0015DD90`; timezone is the signed
11-bit field at bits `21..31`, and configuration version is bits `13..15`.
Version zero is the early-Japanese fallback. Syscall `0x6F` exposes daylight
saving through bit `4` of parameter byte one for later configurations.

The load path writes mode `1`, calls `FUN_001E1D80`, performs
`FUN_001D9600(0)`, scans through `FUN_001E1DA0`, requests a record through
`FUN_001E1E10`, and resolves confirmation through `FUN_001E3120`. A Yes decision
turns status `0x10` into operation `6`, the record read, validation and copy
described under [Load path](save_data.md#load-path), before reporting success.

## Native main-menu loading presentation

`FUN_001E9C00` is the main-menu-load subcontroller. Its shared `0x14`-byte
transient at `0x0060760C` advances through these phases:

| Phase | Observed work and completion gate |
| ---: | --- |
| `0` | Enter phase 1. |
| `1` | Run `FUN_001E7940`: create `MC_CHECKDIR`, yield until its `+0x28` completion, read its `+0x2C` result, and request task termination. Zero result selects phase 3; nonzero selects phase 2. The scan's save-directory contract remains with [Save data](save_data.md). |
| `2` | Update optional controller `FUN_001F3B60` until it returns 1. |
| `3` | Request random loading artwork through `FUN_001FFC30(-1, 1)` and enter phase 4. |
| `4` | Wait for `FUN_001CFD70` to report an inactive background queue, free its transport nodes, and resolve the loaded artwork through `FUN_001FFD30`. Request presentation `(0, 1)`, queue each missing `modesel1.ccs`, `option.ccs`, `charsel1.ccs`, `mapsel1.ccs`, and `setting.ccs` resource, then start the background queue with size pre-scan enabled and enter phase 5. Character/stage requests instead use their resident pointer slots as the absence gate. |
| `5` | Wait for the second background queue to become inactive, free its transport nodes, clear the presentation request through `FUN_00200620`, and enter phase 6. |
| `6` | Wait for the presentation controller to return to idle through `FUN_00200670`; release the loading artwork through `FUN_001FFD80`, free/clear the transient, and return 1. |

The [background queue](files/runtime_services.md#loadbg-queue) owns file reads,
pre-scan totals, transport cleanup, and downstream publication. The initial
artwork request uses pre-scan flag zero; the menu-resource request uses flag
one. File-queue completion and presentation completion are separate gates.

### Controller construction, resources, and phases

`FUN_00203B50`, directly called at `0x001F4388` during front-end manager
construction, creates the `0x1C`-byte loading controller at `0x006076A0` plus
two other front-end presentation services. `FUN_00203C50` services the loading
controller through `FUN_00200230` and then those other services. Its
decompilation omits the first argument, but bytes `B0 CC 84 8F` at
`0x00203C58` load the controller from `gp-0x3350` into `a0` before the call.
The boot loop does not construct this controller before entering the front-end
manager; `FUN_002005B0` does nothing if that pointer is null or already active.

| Controller offset | Established use |
| ---: | --- |
| `+0x00` | Presentation phase, initially zero/idle. |
| `+0x04` | Initial-delay counter. |
| `+0x08` | Exit-transition handle, initially `-1`. |
| `+0x0C/+0x10` | Entry/exit transition selectors, initially `-1`. |
| `+0x14` | Request byte; start sets it to 1, `FUN_00200620` clears it. |
| `+0x15` | Artwork was acquired by this controller and should be released by its cleanup. |
| `+0x18` | Finite `0x14`-byte presentation child, initially null. |

`FUN_001FFC30(-1, ...)` chooses a nonnegative random value modulo 7. The first
seven table entries are `loading00`, `loading01`, `loading02`, `loading04`,
`loading05`, `loading08`, and `loading09`, all with `.ccs` suffix. They are not
the numerically contiguous `00..06` filenames. The complete 13-pointer table
at `0x005C1470` also contains `03`, `06`, `10`, `11`, `12`, and `13`, but
those are outside this caller's random selection. Absent artwork is loaded as
`loading/<filename>`; argument zero loads synchronously, while nonzero uses the
background queue. `FUN_001FFD30` resolves the selected published container;
`FUN_001FFD80` destroys it and clears slot `0x00607698`.

`FUN_001FFDC0` constructs the finite presentation child: a priority-`0xE0`
renderer, two `0x120`-byte animation objects named `ANM_xload_ba` and
`ANM_xload_fa` from `cmn/gauge.ccs`, and a third `0x120`-byte object named
`ANM_xloada` from the selected loading container. If the selected container is
absent, a flag skips only that third object. The two gauge objects are still
used by `FUN_00200060`, so an available drawing service alone is not the full
resource prerequisite. The child also creates the `0x208`-byte progress display
through `FUN_00200DB0`, using `TEX_xnum` from `gauge.ccs`.

The complete `FUN_00200230` presentation switch behaves as follows:

| Phase | Observed behavior |
| ---: | --- |
| `0` | No request returns immediately; a request enters phase 1 in the same call. |
| `1` | If no artwork is already supplied, load it synchronously and set local-ownership byte `+0x15`; otherwise clear that byte. Enter phase 2 with counter zero. |
| `2` | Increment the counter; a value above 5 permits phase 3. A cleared request takes phase 6 before creating the child. This is six service calls, not a proven six-frame duration. |
| `3` | Unless entry selector is `-1`, clear transition slots and start a `0x14`-count transition. Create the presentation child; success enters phase 4, null child enters phase 6. |
| `4` | Update/draw the child through `FUN_00200060`. A cleared request permits phase 5 and starts the selected exit transition; selector `-1` supplies handle zero. |
| `5` | Continue drawing until `FUN_00183FD0` says the exit transition is no longer active, then enter phase 6. |
| `6` | Destroy all non-null animation objects, unregister/free the renderer, destroy the progress display, free the child, and release artwork only when local-ownership byte `+0x15` is set. Return to phase 0. |

The normal menu loader supplied its artwork before requesting presentation, so
presentation phase 1 borrows it and phase 6 leaves its release to the outer
`FUN_001E9C00 -> FUN_001FFD80` path. `FUN_00200640` reports active phase;
`FUN_00200670` reports a non-null controller with idle phase. A null controller
does not report completion through that latter predicate. Manager cleanup
`FUN_00203CB0`, called at `0x001F4764`, additionally releases any loaded artwork,
remaining presentation child and progress display, and the loading controller,
then clears their global slots. The wider manager teardown remains owned by
[Mode flow](mode_flow.md).

### Progress value and exit

`FUN_001CFAE0` returns floating-point `completed * 100 / total` in `f0`, or
`-1.0` when the queue total is zero. `FUN_00200060` passes that float directly
to `FUN_002006C0`; bytes `06 03 00 46` at `0x002001C0` are
`mov.s f12, f0`. It does not pass an integer percentage despite the incomplete
decompiler signatures.

`FUN_002006A0` clears valid byte `0x006076A4` and stores `-1.0` at
`0x006076A8`. A known value makes the cache valid; values above 99 become
100. A later `-1.0` changes an already-valid cache to 100, while an initially
unknown value leaves it invalid. `FUN_00200730` returns `-1.0` until valid.
Consequently, the presentation can retain 100 after queue exit resets its raw
total to zero. Only the display path converts the cached float to an integer
with `cvt.w.s/mfc1` at `0x002001EC..0x002001F0`. The completion gate remains
the inactive file queue plus idle presentation controller, independent of that
displayed percentage.

## Audio initialization bottleneck

The startup-resource task `FUN_001D2570` does not set completion byte `+0x1C`
until `FUN_001D9650` returns. That function constructs the sound manager through
`FUN_001D7A30` and calls eager initialization `FUN_001D6550`:

1. `FUN_001D6B60` opens `sound.afs`, `stream.afs`, `rpgvoice.afs`, and
   `plvoice.afs`.
2. `FUN_001D6C70` loads 13 sound indexes, 82 RPG-voice indexes, and 93
   player-voice indexes.
3. Each helper starts one ADXF operation and yields until it reaches state `3`
   before beginning the next operation.

The path therefore performs 188 serialized index loads. The global ADXF record
at `0x003D3BC4` and `0x003D3BC8` permits only one current operation. The sound
manager allocates all destination buffers before eager loading begins.

Runtime samples show ROFS becoming ready while audio continues through both
voice ranges, with final readiness only after player-voice index 242.

`FUN_001D6010` is the resident RPG-voice playback wrapper and forwards with
archive category `2`. An exhaustive direct-call search found 24 callers in
`ADV.BIN`, none in `ETC.BIN`, and one in `BTL.BIN`; the battle caller requests
bank `0x4E`. Player voices use category `3` through `FUN_001D2C20`. Its 93
descriptors are indexed by character ID minus one; see [Voice descriptors and filename-number lists](character_assets.md#voice-descriptors-and-filename-number-lists).

NUN5 retains the same manager layout and eager-loading sequence. Its audio
manager pointer is at `0x00617C58`; `FUN_001DBB50` opens the four archives and
walks the same count and buffer-pointer fields, while `FUN_001DC270` performs
one blocking index load. The RPG and player index tables are at `0x00415BD0`
and `0x00415E70`, and their archive handles are at `0x006101A4` and
`0x006101A6`. The shared clip routine is `FUN_001DF0C0`. The category-3 player
call is at `0x001D8070`, the category-2 RPG call is at `0x001DB60C`, and the
startup caller invokes the eager initializer at `0x001DEF50`.
