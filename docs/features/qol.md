# QoL

File-backed and resident quality-of-life behavior. Selectable nodes, guarded
binary edits, runtime hooks, and payload declarations are selected by
`features.qol` in `@builder/catalog/catalog.modcat`.

## Practice bootstrap PNACH

Practice bootstrap is runtime-only and has no builder catalog node, builder
configuration field, resident fragment, or ISO rebuild input. The launch
profile invocation is `na228 <game> [game] -l practice <row>`; `practice`
selects a physical row from `@resources/movesets.tsv`, starting at row 2 after
the header. It works with NUN5,
NA2.28 build selectors, build-and-launch tokens, and input playback. It reads
only that row; it neither reads
`character_data.tsv` nor expands character, support, or awakening combinations.
Exactly one of `linked_j_id` or `linked_uj_id` may select a support; when
both cells are empty, the profile selects No Support `0x25`. An empty
`awakening_id` cell writes the `FFFFFFFF` no-effect sentinel. A `Y` in the
`reversal` column adds a fourth, game-specific inline PNACH line that selects
the native Half starting-HP mode; an empty cell leaves starting HP unchanged.
The `uniqueness` column is metadata.

`@repository/launch_profiles/practice/NA228.pnach` and
`@repository/launch_profiles/practice/NUN5.pnach` contain the
complete game-specific bootstraps. Each selected game receives its own file and
three ordinary inline PNACH lines at that game's character, support, and
awakening configuration addresses. Those process-local lines are the sole case
values and do not modify or regenerate either file. The normal
PNACHs at `@pcsx2_files/games/NA228/NA228.pnach` and
`@pcsx2_files/games/NUN5/NUN5.pnach` contain no Practice bootstrap.
Clean NA2 is not supported yet.

The bootstrap writes both current and match-start Player 1 fields, fixes Player
2 to Naruto with Sakura support and the Practice stage to `6`, skips Character
Select and Practice Settings, and retains the native battle-loading states.
Its battle wrapper first runs the native update, then applies the requested
awakening once after Player 1 exists. Every non-`none` awakening ID reaches the
native awakening function's exact-effect transition, so the requested effect,
awakened controller state, transition actions, and sound are applied together.
Deidara `0x41` retains the complete native entry. Taijutsu Chiyo `0x4E` first
enters her separate native moveset state, then uses the complete native entry to
remove her constructor-owned `0x4D` effect and apply `0x4E`. Gaara's regular
`0x3B` first enters his separate native moveset state, then reaches the shared
transition; his item awakening `0x3C` deliberately does not enter that moveset
state. There is no raw-effect fallback.

The NA2 guards are runtime `0x001E9AF8` for the post-Continue route,
`0x001ECA2C` for the unchanged state-`7` call into the replaced native
`FUN_001ED450` range, and `0x001ECACC` for the state-`15` battle-update call.
The reverse-engineering evidence, PNACH layout, and native field contract are
in [`../knowledge/gameplay/battle.md`](../knowledge/gameplay/battle.md).

## Practice starting HP

`qol.practice.starting_hp` selects `full`, `half`, or `critical` as the native
Practice starting-HP mode for both fighters. The base configuration selects
`half`; every value changes only the initializer for the existing Practice
settings field, with `full` retaining the clean instruction sequence. The game
then carries that field through its normal battle setup, producing normalized
live HP of `1.0`, `0.5`, or `0.1`.

The patch is an eight-byte guarded replacement in clean `SLPS_258.37` at ELF
offset `0xE7BE8` (runtime `0x001E7AE8`). It reuses constants already present in
the initializer and preserves the immediately following settings field. Static
binary and savestate comparison are complete; patched-build runtime validation
remains pending. The reverse-engineering record is in
[`../knowledge/gameplay/battle.md`](../knowledge/gameplay/battle.md).

Practice reversal rows override the initializer process-locally with
`0x001E7AE8 = 0xA0850001` for NA228 or
`0x001ED8D8 = 0xA0850001` for NUN5. Ordinary rows do not add either write.

## Select No Support on Character Select

`qol.character_select.no_support` is an accepted runtime patch that builds one
compact support roster per player. Every roster begins with **No Support**;
native supports are retained only for the declared directional relationships:
Naruto-Sakura, Sakura-Chiyo, Itachi-Kisame, Sasori-Deidara, and
Sasuke-Orochimaru in both directions, plus Naruto to Sai, Naruto to Gaara,
Sasuke to Naruto, Tsunade to Jiraiya, and Shikamaru to Choji. A fighter with no
declared relationship therefore receives No Support as the sole selectable
entry.

Both native population call sites are routed through one C injection. It
copies the complete `0x454`-byte selector-data block for each player, preserving
the fighter and support portrait-object tables while allowing simultaneous
different rosters. It retains each permitted native ID and availability state,
prepends the entries declared in `ADDITIONAL_SUPPORT_ENTRIES`, and clears the
unused list slots. The current special declaration adds native no-support ID
`0x25` as an available entry, maps it to display record `0x5F`, and supplies
the name `NO SUPPORT`.

The first runtime test proved that the inserted icon rendered and that the
cursor could reach it, but pressing OK did not accept it. NA2's separate BTL
compatibility helper rejects every support ID at or above `0x24`; NUN6 extends
that gate through `0x25`. The implementation routes all six Character
Select consumers of the helper through a second table-aware C entry point.
IDs declared in `ADDITIONAL_SUPPORT_ENTRIES` are accepted globally, while
native IDs are accepted only for the same directional roster table. This keeps
confirmation, navigation, and draw eligibility aligned with the compact lists
instead of showing rejected cells with red-X overlays.

Runtime testing then confirmed that OK accepts the new entry, but established
that NA2's unextended support-to-display map resolves ID `0x25` to record zero,
visibly reusing Classic Naruto. The localization pipeline's imported official
NUN5 `CHARSEL1.CCS` already contains a Leaf sprite at display record `0x5F`;
the patch routes Character Select's list and selected-portrait lookups
through the table-defined record. NUN6 artwork is not imported or reused.

The NUN5 character-name atlas has no suitable No Support label. For the added
entry only, the selected-name path therefore skips the unrelated character
sprite and draws `NO SUPPORT` with the resident font, centered in the existing
nameplate. Every native support delegates to the complete original name path.
Runtime testing confirmed the Leaf and label both render, while the initial
full-width label intruded beneath the **Linked Character** badge. Two rejected
candidates wrote `0.80` to the shared scale word without activating Font v2's
geometry hooks; runtime pixels proved that the label remained full-width and
offsetting it merely moved the problem. The accepted implementation uses the
existing Font v2 adapter to fit the measured 112-unit label into the row's
84-unit maximum width and center its actually scaled glyph geometry in the
nameplate. There is no manual draw offset. The injection remains table-driven
so later special entries can supply their own display record, name, and maximum
label width without editing the executable list. The native renderer always
visits 13 carousel positions and wraps them modulo the roster count; an
additional guarded draw hook suppresses those wrapped repetitions so every
compact entry is rendered once at its native position. A one-entry roster thus
shows one centered, highlighted Leaf cell, and left or right navigation wraps
to that same entry. Clean call sites, both native list producers, all six
compatibility consumers, and all six render hooks are statically guarded. The
user accepted the fitted-and-centered label in runtime on 2026-08-14 and the
compact per-character roster behavior on 2026-08-15.

For a fighter whose compact roster contains only No Support, both native
fighter-confirmation calls now retain the native confirmation work and then
advance directly from fighter selection to the finalized state with support
index zero and Linked Mode disabled. The support-selection and Linked Mode
screens are never rendered. Back from that finalized state returns directly to
fighter selection; rosters with selectable partners retain the complete native
forward and backward flow. A retained replay confirmed that Naruto's four
recorded menu markers remain unchanged while the
No-Support-only fighter moves directly from marker 5 to marker 8. A derivative
replay confirmed the reverse marker-8-to-marker-5 transition. The user accepted
both directions on 2026-08-15.

The No Support battle hooks keep the selected native support intact through
battle transition and linked Jutsu. A guarded main-ELF hook replaces the sole
per-fighter support-button acceptance call with a no-op, preventing its
linked-fighter field-call signal without changing selected support data. A
second guarded hook replaces only the dedicated BTL `TEX_xgauge` draw call
with a no-op, keeping the support gauge hidden for both players while leaving
the rest of the battle HUD native. Blocking unrelated fighter inputs during
Ultimate Jutsu remains outside this patch. The Character Select record is in
[`../knowledge/game/character_select.md`](../knowledge/game/character_select.md),
and the battle-path evidence is in
[`../knowledge/gameplay/battle.md`](../knowledge/gameplay/battle.md).

## Disable the Ultimate Jutsu input contest

`qol.ultimate_jutsu.disable_input_contest` blocks both players' inputs during
the Ultimate Jutsu contest and suppresses its bottom meter, button prompts,
and result messages. The ordinary top battle HUD remains visible. The base
configuration enables the setting, so the development configuration inherits
it.

Two guarded BTL edits replace the contest controller's press-latch and
release-poll reads with zero so neither player's input can affect the
controller. A guarded resident-ELF edit suppresses the contest object's common
render dispatch while preserving its native allocation, update, result, and
completion lifecycle.

The earlier implementation selected native contest type `0`, which prevented
the entire contest object from being allocated. Its development replay proved
that the interface was hidden and the recorded input latch remained zero, but
it did not cover post-Ultimate-Jutsu awakening. The user subsequently reported
that enabling the setting prevented that awakening. Static investigation
confirmed that type `0` removes the object's nonvisual update lifecycle as well
as its interface, so the accepted correction restores native object creation
and suppresses only its common render call. User runtime testing on 2026-08-21
confirmed that post-Ultimate-Jutsu awakening occurs, the meter, prompts, and
result messages remain invisible, and both players' inputs remain blocked.
Clean offsets, live addresses, dispatcher ownership, and the earlier replay
evidence are recorded in
[`../knowledge/gameplay/battle.md`](../knowledge/gameplay/battle.md).

## Unlock all content without loading a save

`qol.content.unlock_all` selects the resident injection
`i__qol__content__unlock_all__availability`. Seven guarded hooks replace only the
save-backed reads for characters, the Character Select R1-form gate, secondary
content, the 32-entry small table, the six grouped tables, and metadata-valid
jutsu, plus progress slot `0x6A`, which gates Ultimate difficulty. The injected
helpers reproduce bounded fully unlocked values and the native stable state for
Collection figures; the progress helper returns available only for slot `0x6A`
and preserves every other native progress read. Native wrappers, metadata
checks, and callers remain intact.

The feature performs no save-data writes. It therefore exposes characters and
their R1 forms, supports, stages, jutsu, Shop items, and Collection entries
plus Ultimate difficulty without importing the reference save's settings,
progress, currency, inventory, statistics, or availability bytes. Disabling
the setting restores the native save-dependent readers.

The first character candidate used an invalid mask derived through the wrong
global and produced an incorrect, displaced roster. The corrected helper makes
all 94 stored character IDs available and leaves native roster filtering to
the existing callers. User runtime testing on 2026-08-10 confirmed the
correction. The reader contracts, stored values, hook seams, evidence, and
rejected-mask failure are recorded in
[`../knowledge/game/content_availability.md`](../knowledge/game/content_availability.md).

User runtime testing on 2026-08-11 confirmed that R1 forms remain accessible
without a loaded save and that Collection figure pedestals render when
`unlock_all` is enabled. The R1 hook supplies only the gate's fully unlocked
progress value `0x66`; grouped Collection reads return their native stable
viewed-and-unlocked state `3`.

User runtime testing on 2026-08-21 confirmed that Ultimate difficulty remains
selectable with `unlock_all` in NA2 and with the regular NUN5 PNACH port.

## ELF-Q010: Use only first save

`ELF-Q010` retains 12 guarded direct edits for presentation and navigation.
They change the shared Save/Load slot-row renderer's loop limit from three
records to one at boot-ELF virtual address `0x001E6970` (file offset
`0xE6A70`) and replace the handler's Down and Up input-mask results with zero
before either movement branch. The three-slot occupancy scan, save data, and
memory card remain unchanged; vertical input cannot change the selected slot
or play the slot-navigation sound.

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
to enter the main menu without loaded save data. This is the previously
accepted runtime behavior; the refactor changes its storage and hook shape, not
its intended result.

## ELF-Q009: Loading screen then first-save load

`ELF-Q009` replaces the four splash screens with a boot-safe loading
presentation while preserving the two native startup-loader checks. The QoL
runtime-injector hook replaces the splash update call at boot-ELF virtual
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

The `qol.startup` catalog node is a plain container. Its independent
`faster_loading` setting is available with either startup flow. The nested
`flow` node is a union of two closed shapes: the title branch contains
`skip_cc2_intro` and `skip_opening`, which remain independent and may both be
enabled; the direct-loading branch instead contains `savedata_loading` and
`loading_screen`, so neither skip can be selected when either direct-loading
control is present.

Within the direct-loading branch, `savedata_loading: "manual"` retains the full
Save/Load controller. With
`qol.save_load.display_only_first_save`, it shows the native record-zero
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

The base configuration enables `qol.startup.faster_loading`, then selects
`savedata_loading: "automatic"` and enables `loading_screen` inside
`qol.startup.flow`;
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

`qol.save_load.display_only_first_save` remains an independent setting because
it controls the visible Save/Load interface and is not used by the automatic
startup driver.

## ELF-Q004: Remove Adventure mode

NUN6 removes Adventure from the Mode Select carousel by storing the signed
sentinel `-1` in entry 0 of the boot ELF's seven-entry mode table. The menu setup
loop skips entries whose table value is negative, so the item is omitted rather
than displayed and blocked after selection.

The corresponding tables are:

- NA2: virtual address `0x005D51D0`, ELF offset `0x4D52D0`, values
  `(4, 2, 3, -1, 5, 6, 7)`.
- NUN5: virtual address `0x005DC300`, ELF offset `0x4DC480`, values
  `(4, 2, 3, -1, 5, 6, 7)`.
- NUN6: the NUN5 address and offset, values
  `(-1, 2, 3, -1, -1, -1, 7)`.

`ELF-Q004` changes only NA2 entry 0 from `04 00 00 00` to `FF FF FF FF`.
NUN6's changes to entries 4 and 5 are unrelated and are intentionally not
ported. NUN5 is not a suitable byte donor because its entry 0 matches NA2; the
raw replacement is used because the desired behavior deliberately follows the
NUN6 variant. The source ELF remains untouched and the output size is preserved.

Runtime testing of the integrated Current ISO confirmed that Adventure is absent
and the remaining Mode Select entries work normally. `ELF-Q004` is therefore
enabled in the release configuration; its runtime proof is retained in documentation.

## ELF-Q008: Remove Shop

`ELF-Q008` applies the same filtered-carousel mechanism to Shop. Shop is entry
4 of the same seven-entry boot-ELF table, at virtual address `0x005D51E0` and
ELF offset `0x4D52E0`, where its clean value is `5`.

The patch changes only that entry from `05 00 00 00` to `FF FF FF FF`. The
menu setup loop therefore omits Shop while leaving Adventure, Free Battle,
Practice, Collection, Options, and the existing unused entry unchanged. The
source ELF remains untouched and the output size is preserved.

The canonical `Restore Shop` cheat writes value `5` back to `0x005D51E0`,
re-enabling Shop without changing the file-backed default. The table mapping
and patch guards are statically verified; integrated runtime validation remains
pending.
