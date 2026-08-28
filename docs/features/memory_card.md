# Memory Card

Memory-card save presentation and identity are owned by
`features.memory_card` in `@builder/catalog/catalog.modcat`.

## Display only the first save

`features.memory_card.display_only_first_save` retains 12 guarded direct edits
for presentation and navigation. They change the shared Save/Load slot-row
renderer's loop limit from three records to one at boot-ELF virtual address
`0x001E6970` (file offset `0xE6A70`) and replace the handler's Down and Up
input-mask results with zero before either movement branch. The three-slot
occupancy scan, save data, and memory card remain unchanged; vertical input
cannot change the selected slot or play the slot-navigation sound.

The upper frame is reduced from X/Y/width/height `58/10/400/224` to
`146/90/224/96`, placing a compact one-record panel above and visibly detached
from the unchanged lower instruction panel. Within it, the date/play-time block
moves from local X `108`, Y `14` to X `45`, Y `20`. The redundant slot-number
record moves outside the viewport, the row-separator condition is disabled, and
the now-meaningless independent slot-cursor model is not drawn. The lower
instruction panel and all of its contents remain unchanged.

The controller behavior is implemented by one generated-C wrapper at virtual
`0x001E3F08` (file `0xE4008`), the sole call from `FUN_001e3f00` to the clean
visible-controller update `FUN_001e3f20`. It handles only the state-machine
branches needed to select record zero and bypass the removed list, retaining
the native scan, status UI, confirmations, load/save requests, result
resolution, and frame-counter tails. Every unaffected frame delegates exactly
once to `FUN_001e3f20`. The automatic startup hook at file `0xEA084` replaces
the outer call to `FUN_001e3f00`, so it bypasses this wrapper and remains
independent.

The native `Load this data?` confirmation remains visible. Yes continues the
record-zero load; No enters Save/Load completion state `8` instead of
reconstructing the removed record list. The startup Continue result mapping at
runtime `0x001E9FB8` (file offset `0xEA0B8`) then uses the existing success path
to enter the main menu without loaded save data.

## Dedicated save namespace

`features.memory_card.dedicated_save_namespace` selects two guarded,
equal-length boot-ELF replacements at file offsets `0x2FBAC1` and `0x2FBBF0`.
They replace the stock NA2 memory-card directory name
`BISLPS-25837NARUTO5` with the dedicated NA228 name
`BASLOP-NA228NARUTO6` without changing the ELF size.

The base configuration enables the setting. Setting it to `false` leaves the
stock directory name intact, so NA228 and NA2 address the same saved data.
Changing the setting does not copy or migrate saves between the two names.

## Memory-card title

`features.memory_card.replace_memory_card_title` selects one guarded 64-byte
replacement in the clean boot ELF at `0x2FBAE0`. The `nul_padded_text` adapter
encodes both the original Japanese title and `ＮＡ　ｖ２．２８` as CP932,
requires a terminating NUL, and pads the remainder of the fixed slot with
zeroes. Setting it to `false` leaves the original title intact.

The three settings are enabled by the base configuration and remain
independently selectable.
