# Startup sequence

Native NA2 startup, Save/Load, loading-controller, and audio-initialization
findings.

## Research coverage

- **Assigned scope:** establish the retail ELF bootstrap, resident startup state
  machine, initial managers and tasks, readiness barriers, Continue and
  Save/Load path, loading presentation, and handoff into the main menu.
- **Exploration depth:** the ELF entry and first resident bootstrap layer have
  direct static coverage. Deeper resident call paths were traced and sampled
  across card check, splash, title, Save/Load, loading, and main-menu states.
- **Confirmed coverage:** the ELF identity and entry-point side effects, initial
  task handoff, blocking card check, splash ownership, the two asynchronous
  readiness gates, Continue's shared Save/Load controller, record metadata, the
  native main-menu loading controller, and the eager audio bottleneck are
  established.
- **Unresolved or untested:** semantic roles and manager ownership below several
  early bootstrap calls, scheduler timing between the initial tasks, every
  physical memory-card failure case, indirect voice consumers, and exact
  player-character-to-voice-bank mapping.
- **Deliberate exclusions and overlap:** NA228 startup behavior belongs to
  [Startup](../../features/startup.md); visible one-record presentation and save
  identity belong to [Memory Card](../../features/memory_card.md).
- **Evidence limitations:** sampled timing establishes ordering and observed
  bottlenecks, not a fixed duration on every host or storage device. Read-only
  static analysis cannot establish asynchronous completion timing or exact
  visible-frame boundaries; all frame and duration interpretation uses 30 FPS.

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
3. It sets `gp` to `0x0060A9F0`, invokes raw EE syscalls `0x3C` and `0x3D`,
   and takes the stack pointer returned by syscall `0x3C`. Syscall `0x3D`
   receives `0x008DD080` and `-1`; their higher-level roles are unresolved.
4. It calls `FUN_00168058`, whose observed call order is
   `FUN_00167E08`, `FUN_00167F48`, `FUN_00168538`,
   `FUN_001686B0(2)`, `FUN_001688F0`, `FUN_0015EAB8`,
   `FUN_00168180`, `FUN_00167670`, and `FUN_00169D70`.
5. It calls `FlushCache(0)`, enables interrupts, loads two startup arguments
   from `0x00607A00` and `0x00607A04`, and passes them to `FUN_001C13F0`.
6. If that function returns, `entry` tail-calls `FUN_001787B0` with its return
   value. `FUN_001787B0` walks registered callback lists, invokes the callback
   at context offset `+0x3C` when present, and calls
   `thunk_FUN_00168458`. The ordinary path instead remains in
   `FUN_001C13F0`'s permanent loop.

`FUN_001C13F0` calls the following first-layer initializers before creating the
initial tasks. Their semantic names remain unresolved, so the original symbols
and exact order are retained:

| Order | Original symbol/address | Observed side effect |
| ---: | --- | --- |
| 1 | `FUN_00118730` at `0x00118730` | No explicit argument. |
| 2 | `FUN_00100230` at `0x00100230` | No explicit argument. |
| 3 | `FUN_001BD2B0` at `0x001BD2B0` | No explicit argument. |
| 4 | `FUN_00105FC0` at `0x00105FC0` | No explicit argument. |
| 5 | `FUN_001DA0F0` at `0x001DA0F0` | No explicit argument. |
| 6 | `FUN_001DA130` at `0x001DA130` | No explicit argument. |
| 7 | `FUN_001C14F0` at `0x001C14F0` | No explicit argument. |
| 8 | `GetThreadId` / `ChangeThreadPriority` | Stores the current thread ID at `gp-0x351C` and changes its priority to `0x78`. |
| 9 | `FUN_001BD380` at `0x001BD380` | No explicit argument. |
| 10 | `FUN_001D04F0` at `0x001D04F0` | No explicit argument. |

It then creates a descriptor through
`FUN_001D0090(0x00113530, 0x19, 0x800)`, sets bit `0x8` in its halfword at
`+0x12`, and submits it through `FUN_001CFF00(descriptor, 0)`. It creates a
second descriptor through `FUN_001D0090(0x001E0EE0, 0x23, 0xC000)`, copies the
two arguments from `entry` to descriptor offsets `+0x28` and `+0x2C`, and
submits it the same way. It thereafter loops over `FUN_001083A0` on the pointer
at `gp-0x35F4` followed by `FUN_001D0560`.

The descriptor interpretation is an inference with medium confidence:
`FUN_001D0090` appears to create scheduler-owned task records from an entry
address, priority-like value, and stack-size-like value, while
`FUN_001CFF00` makes them runnable. Exact field meanings remain unresolved.
The `0x001E0EE0` task is the startup game task with high confidence because its
downstream flow constructs the persistent memory-card and save objects and
reaches the splash/title state machine below.

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

The boot-ELF identity and address conversion follow
[Standard game file identities](files/file_identities.md).

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

Calling that dispatcher from the state-0 loader loop was experimentally
rejected: it reset its sequence state and restarted the opening on the next
iteration. Invoking it before audio and streaming prerequisites were ready also
produced first-playback stutter and noise. This establishes that the dispatcher
cannot safely replace the native readiness barrier.

## Startup readiness barrier

The startup loop requires three simultaneous completion values:

- the splash controller result;
- the ROFS/data-ready byte at `0x006074A0`;
- byte `+0x1C` of the startup-resource object referenced at `0x0060755C`.

Bypassing the splash alone exposes the remaining asynchronous loading as a black
screen. Startup mounts `DATA.CVM` as `VOL`, loads its root synchronously, and
creates the `Load ROFS_Data` worker at `FUN_001BD970`. The worker recursively
loads the 20 directories described by `GZLIST.TXT` and sets `0x006074A0` only
after their metadata is ready; it does not preload the 2,310 CCS payloads.

After all three values are ready, native code writes state `2` at `0x001E11CC`.
The title dispatcher at `0x001E1240` calls `FUN_001DE840`; result `1` selects New
Game and result `2` selects Continue. The caller then enters main state `4` with
the corresponding substate.

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

Each record descriptor contains occupancy at `+0x00`, native class at `+0x01`,
checksum at `+0x02`, play time in 30 Hz ticks at `+0x04`, and the memory-card
timestamp at `+0x08..+0x0F`. The timestamp fields are reserved byte, second,
minute, hour, day, month, and little-endian year. `FUN_001C2C80` copies those
bytes from the native directory entry. `FUN_001E6370` renders the date and
converts play time using 108,000 ticks per hour, 1,800 per minute, and 30 per
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
turns status `0x10` into operation `6`, which reads `0x2400` bytes, verifies the
stored checksum, and copies the profile before reporting success.

## Native main-menu loading presentation

`FUN_001E9C00` is the main-menu-load subcontroller. It prepares resources,
opens a `loadingXX.ccs` resource through `FUN_001FFC30`, begins the loading
screen through `FUN_002005B0`, waits for completion, and hands control to the
usable menu. `FUN_00203B50` initializes loading systems, `FUN_00203C50` updates
and draws them, `FUN_002006C0` stores progress, and `FUN_001CFAE0` queries
progress.

Calling those functions during startup state `0` produced only black output,
establishing that the menu loading presentation depends on resources or state
unavailable before the startup loaders complete. The boot splash path is the
only presentation path proven usable during that earlier wait.

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
voice ranges, with final readiness only after player-voice index 242. Removing
polling yields would not shorten the underlying I/O, and publishing readiness
early would expose uninitialized buffers.

`FUN_001D6010` is the resident RPG-voice playback wrapper and forwards with
archive category `2`. An exhaustive direct-call search found 24 callers in
`ADV.BIN`, none in `ETC.BIN`, and one in `BTL.BIN`; the battle caller requests
bank `0x4E`. Player voices use category `3` through `FUN_001D2C20`. Its 93-entry
table matches character IDs `1..0x5D`, suggesting one bank per identity, but
that mapping remains unconfirmed.

Feature use of these clean hook and data boundaries is documented in
[Startup](../../features/startup.md).
