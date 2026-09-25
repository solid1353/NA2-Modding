# Startup

## Loading screen and startup route

The startup loading patch replaces the four splash screens with the NA2.28
artwork and a boot-safe loading presentation while preserving the two native
startup-loader checks.
The artwork is derived from `assets/artwork/splash.png` into
`@builder/patches/startup/loading_screen/228SPL.ccs.gz` by
`@builder/patches/startup/loading_screen/generate_splash.py`. The builder verifies the asset's
hash and inserts it as `PRG/228SPL.CCS` without changing `DATA.CVM` or the
original `LOGO.CCS`. The 4:3 source is sampled at 1024×768 and packed into
the three existing 512×512, 256-color texture slots as twelve 256×256 tiles.
The decompressed CCS size stays unchanged.

At boot, the patch loads that inserted file through the native CCS loader. Its
internal resource name remains `logo`, so the native splash controller can find
it without changing the original logo path. A resident metadata hook supplies
its decompressed size; all other CCS requests keep native metadata lookup. The
resident draw hook submits the twelve tiles first, then resets the renderer
and draws a dark track with a white loading fill and rounded ends below the
NA2.28 title.
The startup runtime-injector hook replaces the splash update call at boot-ELF virtual
address `0x001E10A0` (file offset `0xE11A0`). It initializes the existing
boot-safe splash controller, holds its first draw slot active, and returns
splash completion to the unchanged startup loop.

A guarded hook replaces the splash sprite draw call at virtual address
`0x001E10E0` (file offset `0xE11E0`). It draws the inserted artwork with
boot-safe textured primitives and the loading bar with solid primitives.
The bar reads the EE Count register and maps elapsed emulated time across the
observed 6-7-second visible interval, rather than treating repeated
startup-poll iterations as displayed frames. Its fill caps at 99%; the real
loader flags, not the displayed estimate, determine when startup may continue.

After the required startup loaders complete, the common file-backed edit writes
state `3` instead of state `2` at virtual address `0x001E11CC` (file offset
`0xE12CC`). The title-call hook at virtual address `0x001E1240` (file offset
`0xE1340`) normally returns native title result `2` (`Continue`). The unchanged
caller enters main state `4`, substate `2` and constructs the shared Save/Load
controller in load mode. This route bypasses the CyberConnect2 intro and
opening directly.

After Mode Select completes its native back-exit cleanup, the same `startup`
patch preserves the front-end manager's native return-to-title result `1` and
arms a hidden title-to-opening handoff. The confirmation prompt reads `View the
movie?`. The title-call hook constructs the native title controller, starts it
directly in the idle-return transition before its first update, and masks title
input while the handoff is active. Skipping the controller's state-0 title
presentation setup prevents title-screen audio from starting.
When that controller returns `-1`, the unchanged outer loop enters its opening
state and the patch initializes the post-splash sequence directly at
`OPENING.PSS`.
Natural movie completion resets that sequence to the opening again. The native
movie-input update remains responsible for its accepted buttons and decoder
termination; the patch only records its stop request. After an input-driven
termination completes the native opening cleanup, the existing title-result
replacement selects Continue and returns through the same Save/Load path to
Mode Select.

Four guarded call hooks implement this route. File offset `0xE13D0` wraps the
front-end manager update, `0xE1340` selects Continue or drives the hidden native
title handoff, `0xDC1F8` wraps the native movie-input update, and `0xE1318`
wraps the opening-sequence update. Three resident words distinguish an active
Mode Select replay from ordinary startup, track the hidden title handoff, and
distinguish an input-driven stop from natural movie completion.

The `features.startup` catalog node owns the direct Save/Load route. Its
`faster_loading` and `loading_screen` settings are direct children. Automatic
loading and the initial card check are configured under
[`features.memory_card`](memory_card.md#automatic-loading).

The `faster_loading` setting keeps the four audio archives open and the 13
general sound indexes initialized at boot, but defers all 82 RPG-voice and 93
player-voice indexes. Its two playback hooks load and cache the exact requested
bank under one semaphore before calling the unchanged native playback routine.
User runtime timing measured the integrated startup load at about
15 seconds, 10 seconds shorter than the prior 25-second baseline. A subsequent
observation in the current launch setup measured the visible loading screen at
about 6-7 seconds. Runtime validation confirmed the integrated patch and elapsed-time
counter; first-use voice delay and repeated or concurrent
first-use playback were not separately isolated during acceptance.
The build configurations inherit `faster_loading` from the base configuration.
The complete disassembly findings, worker layout, outcome matrix, and state
machine are recorded in
[`../knowledge/game/startup.md`](../knowledge/game/startup.md).

## NUN5 E2E PNACH

The NUN5 E2E port targets `SLES-55605`, CRC `C071D4C1`. It preserves NUN5's
native localization initialization by making the sole English-language selector
return language index zero, then uses the homologous startup and Continue paths
for silent first-save loading.

| Runtime | ELF offset | Effect |
| ---: | ---: | --- |
| `0x001E6620` | `0xE67A0` | Skip logo playback after normal text loading and logo construction. |
| `0x001E6DB4` | `0xE6F34` | Enter title state after required loaders. |
| `0x001E6E28` | `0xE6FA8` | Select Continue without title input. |
| `0x001EFEDC` | `0xF005C` | Call the silent driver. |
| `0x001EFEFC` | `0xF007C` | Map no-load to normal menu continuation. |
| `0x001F0174` | `0xF02F4` | Suppress the visible Save/Load child. |
| `0x003D0C60` | `0x2D0DE0` | Replace the English-selector entry; the driver begins at `0x003D0C80`. |

The driver occupies `0x003D0C80..0x003D0E3F`, inside the now-unreachable tail
of the selector function whose only native caller is `0x001E65D0`. It uses the
same four native worker phases as NA2: scan `1/0`, confirmation `0x10/3`, read
progress `0x11/4` or `0x12/4`, and verified completion `0x13/1`. Busy status
`4` retains the native unbounded wait; every other terminal outcome enters the
menu without loaded data.

This port deliberately omits NA228's loading presentation, savedata
notification, and resident-payload system. Runtime validation confirmed the
PNACH startup path; the exact memory-card case used in that check was not
recorded.

## NUN5 faster-loading PNACH

`pcsx2_files/games/NUN5/NUN5.pnach` ports the NA228 lazy voice-index behavior
to NUN5. The Practice launch profile layers its game-specific PNACH on top of
this normal file, so `-l practice` inherits the payload without duplicating it.
The payload keeps all four audio archives and the 13 ordinary sound indexes
initialized at boot, temporarily hides the RPG and player counts from the
native eager initializer, and loads each requested voice-bank index once under
a semaphore before native playback.

| Runtime hook | Clean call | Replacement |
| ---: | --- | --- |
| `0x001DEF50` | NUN5 eager audio initialization | Initialize archives and ordinary sound indexes only. |
| `0x001D8070` | Category-3 player playback | Ensure the requested player index, then call native playback. |
| `0x001DB60C` | Category-2 RPG playback | Ensure the requested RPG index, then call native playback. |

The compiled code and 28-byte mutable state occupy
`0x01FF53E0..0x01FF57B3` inside the PNACH's existing guarded
`0x01FF4000..0x01FF5FFF` allocator-tail reservation. A missing manager or
semaphore-creation failure retains native eager loading; an invalid first-use
request fails without starting native playback. Static hook, relocation, and
placement validation passed. NUN5 runtime timing and first-use playback
validation remain outstanding.
