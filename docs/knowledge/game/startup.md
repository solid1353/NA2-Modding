# Startup sequence

Native NA2 startup, Save/Load, loading-controller, and audio-initialization
findings.

## Research coverage

- **Assigned scope:** establish the clean startup state machine, readiness
  barriers, Continue and Save/Load path, loading presentation, and serialized
  audio initialization.
- **Exploration depth:** the relevant resident call paths were traced and
  sampled across splash, title, Save/Load, loading, and main-menu states.
- **Confirmed coverage:** splash ownership, the two asynchronous readiness
  gates, Continue's shared Save/Load controller, record metadata, the native
  main-menu loading controller, and the eager audio bottleneck are established.
- **Unresolved or untested:** every physical memory-card failure case, indirect
  voice consumers, and exact player-character-to-voice-bank mapping.
- **Deliberate exclusions and overlap:** NA228 startup behavior belongs to
  [Startup](../../features/startup.md); visible one-record presentation and save
  identity belong to [Memory Card](../../features/memory_card.md).
- **Evidence limitations:** sampled timing establishes ordering and observed
  bottlenecks, not a fixed duration on every host or storage device.

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
