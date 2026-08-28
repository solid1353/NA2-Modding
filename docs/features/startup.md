# Startup

## Loading screen then first-save load

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

After the required startup loaders complete, the common file-backed edits write
state `3` instead of state `2` at virtual address `0x001E11CC` (file offset
`0xE12CC`) and return native title result `2` (`Continue`) at virtual address
`0x001E1240` (file offset `0xE1340`). The unchanged caller enters main state
`4`, substate `2` and constructs the shared Save/Load controller in load mode.
This route bypasses the CyberConnect2 intro and opening itself, so neither
independent skip edit is selected with a save-loading branch.

The `features.startup` catalog node is a plain container. Its independent
`faster_loading` setting is available with either startup flow. The nested
`flow` node is a union of two closed shapes: the title branch contains
`skip_cc2_intro` and `skip_opening`, which remain independent and may both be
enabled; the direct-loading branch instead contains `savedata_loading` and
`loading_screen`, so neither skip can be selected when either direct-loading
control is present.

Within the direct-loading branch, `savedata_loading: "manual"` retains the full
Save/Load controller. With
`features.memory_card.display_only_first_save`, it shows the native record-zero
confirmation; Yes loads the save and No enters the menu without loading.
`savedata_loading: "automatic"` instead replaces only Continue's per-frame
visible-controller update with a silent generated-C driver for the same
asynchronous memory-card worker. It scans port zero, requests record zero when
present, internally resolves the native load confirmation as Yes, waits through
checksum-verified load completion, and then lets Continue perform its unchanged
cleanup, save-dependent setup, and main-menu loading. Its separate guarded
no-op at file offset `0xEA0D0` prevents the Save/Load child from drawing.

The automatic branch treats no card, a wrong card type, an unformatted card, no
game directory, an empty first record, read/checksum failure, a card change, and
every other non-success terminal worker result as no-load completion. In all of
those cases the existing guarded result mapping enters the main menu without
loaded data. It does not synthesize a timeout while the native worker reports a
busy state.

The base configuration enables `features.startup.faster_loading`, then selects
`savedata_loading: "automatic"` and enables `loading_screen` inside
`features.startup.flow`;
`savedata_loading: "manual"` remains available as the confirmed visible
fallback. The sequence bypasses the notice, Bandai Namco, Bandai, CRIWARE,
opening, interactive title, Load list, card-status messages, and load
confirmation before the main-menu loading screen. Full development build
`20260811_065428_218_pid37624` succeeded, and user runtime validation on
2026-08-11 confirmed the integrated automatic behavior before the loading-time
patch was added. The manual branch also remains user-confirmed.

The `faster_loading` setting keeps the four audio archives open and the 13
general sound indexes initialized at boot, but defers all 82 RPG-voice and 93
player-voice indexes. Its two playback hooks load and cache the exact requested
bank under one semaphore before calling the unchanged native playback routine.
User runtime timing on 2026-08-11 measured the integrated startup load at about
15 seconds, 10 seconds shorter than the prior 25-second baseline. A subsequent
observation in the current launch setup measured the visible loading screen at
about 6-7 seconds. The user accepted the integrated patch and elapsed-time
counter on 2026-08-11; first-use voice delay and repeated or concurrent
first-use playback were not separately isolated during acceptance.
Development and release inherit `faster_loading` from the base configuration.
The test configuration used by Manual and E2E builds disables it.
The complete disassembly findings, worker layout, outcome matrix, and state
machine are recorded in
[`../knowledge/game/startup.md`](../knowledge/game/startup.md).

`features.memory_card.display_only_first_save` remains an independent setting because
it controls the visible Save/Load interface and is not used by the automatic
startup driver.
