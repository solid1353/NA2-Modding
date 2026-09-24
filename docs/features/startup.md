# Startup

## Loading screen and automatic first-save load

The startup loading patch replaces the four splash screens with a boot-safe
loading presentation while preserving the two native startup-loader checks.
The startup runtime-injector hook replaces the splash update call at boot-ELF virtual
address `0x001E10A0` (file offset `0xE11A0`). It initializes the existing
boot-safe splash controller, holds its first draw slot active, and returns
splash completion to the unchanged startup loop.

A second guarded hook replaces the splash sprite draw call at virtual address
`0x001E10E0` (file offset `0xE11E0`). It suppresses the original logo sprite
and uses the same boot-safe solid-primitive renderer to draw a large two-digit
percentage, percent sign, and progress bar. Each rectangle is submitted as an
independent primitive so separate digit segments cannot be joined by the
renderer's triangle strip. The counter reads the EE Count register and maps
elapsed emulated time across the observed 6-7-second visible interval, rather
than treating repeated startup-poll iterations as displayed frames. It caps at
`99%`; the real loader flags, not the displayed estimate, determine when
startup may continue.

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

The `features.startup` catalog node is a plain container that owns the direct
Save/Load route. Its `faster_loading`, `skip_initial_memory_card_check`,
`auto_loading`, and `loading_screen` settings are direct children.

The `features.startup.skip_initial_memory_card_check` patch skips
only the blocking card check before the splash and startup loaders. It replaces
`jal 0x001E71B0` at boot-ELF virtual address `0x001E0FA0` (file offset
`0xE10A0`, expected bytes `6C9C070C`) with a NOP. The persistent memory-card
worker and save-data initialization remain intact. The later Continue flow
still scans the card and loads save data through its own worker session.
This Boolean is independent of `auto_loading`: disabling it restores the early
native check, while disabling `auto_loading` restores the later visible
Save/Load flow. Fresh-boot runtime validation with and without a card remains
outstanding.

With `features.startup.auto_loading` disabled, the automatic-loading injection
is absent and the full native Save/Load controller remains. With
`features.memory_card.display_only_first_save`, it shows the native record-zero
confirmation; Yes loads the save and No enters the menu without loading.
Enabling `auto_loading` selects one injection that replaces Continue's
per-frame visible-controller update with a silent generated-C driver for the
same asynchronous memory-card worker and redirects the Save/Load child draw at
file offset `0xEA0D0` to a wrapper that suppresses ordinary silent loading. It scans port zero, requests record
zero when present, internally resolves the native load confirmation as Yes,
waits through checksum-verified load completion, and then lets Continue perform
its unchanged cleanup, save-dependent setup, and main-menu loading.

Automatic loading treats no card, a wrong card type, an unformatted card, no
game directory, an empty first record, read/checksum failure, a card change, and
other non-success terminal worker results as no-load completion, except for a
supported older save awaiting upgrade consent. In those no-load cases,
the existing guarded result mapping enters the main menu without
loaded data. It does not synthesize a timeout while the native worker reports a
busy state.

For a supported version `0` save, automatic loading switches to the shared
visible Save/Load controller and enables its child draw. That controller owns
the upgrade confirmation and subsequent load flow described in
[Memory Card](memory_card.md#dedicated-save-namespace). The silent driver's
phase word marks visible-controller states with `0x100`; the marker is removed
before each native update and restored while it is pending. A successful load
publishes the ordinary loaded notification. Declining or failing the upgrade
closes through the native no-load result without a duplicate notification.

When the dedicated save has a readable but unsupported schema, automatic
loading reports `The existing save data uses version {found}. Version
{required} is required.` A native-only record reports version `0`. Other load
failures retain `Save data could not be loaded`.
The version warning uses three right-aligned lines, breaking after `data` and
after the first sentence, with 24 units between lines.
The same version result is consumed on scan, confirmation, and read failures,
including a directory-size rejection before the normal record read begins.

The main-menu notification is drawn after Mode Select's presentation, using its
prompt render context. It keeps a unit horizontal font scale for its
measurement and text draws, restores the previous scale and font context, and
remains in the menu's layer during the shared exit transition. The notification
ends when the Mode Select controller reaches its terminal state or its
ten-second display time expires.

The base configuration enables `features.startup.faster_loading`,
`skip_initial_memory_card_check`, `auto_loading`, and `loading_screen`. Disabling
`auto_loading` preserves the user-confirmed native visible Save/Load flow. The enabled sequence bypasses the
notice, Bandai Namco, Bandai, CRIWARE,
opening, interactive title, Load list, card-status messages, and load
confirmation before the main-menu loading screen. A full development build
succeeded, and user runtime validation confirmed the integrated automatic behavior before the loading-time
patch was added. The native visible Save/Load flow also remains user-confirmed.

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
Development and release inherit `faster_loading` from the base configuration.
The test and E2E configurations disable it.
The complete disassembly findings, worker layout, outcome matrix, and state
machine are recorded in
[`../knowledge/game/startup.md`](../knowledge/game/startup.md).

`features.memory_card.display_only_first_save` remains an independent setting
because it controls the visible Save/Load interface, including the upgrade
flow when automatic loading encounters a supported older save.

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
