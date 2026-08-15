# QoL

File-backed and resident quality-of-life behavior. Selectable nodes, guarded
binary edits, runtime hooks, and payload declarations are selected by
`na228_builder/catalog/qol.modcat`.

## Practice bootstrap

`qol.practice.bootstrap` enters Practice directly after startup with three
configured inputs: Player 1 character ID `p1`, Player 1 support ID `support`,
and `awakening`, which is `none` or one of the selected character's native IDs
from the `awakening_ids` column in `resources/character_data.tsv`. That column
unites the native fighter-controller associations, Ultimate-Jutsu post-effects,
and hard-coded transformed-form initialization effects; it defines attainable
active states, not their normal entry routes. Configuration JSON keeps `p1` as
a decimal integer, while `support` and a non-`none` `awakening` are hexadecimal
strings such as `"0x18"` and `"0x57"`. The builder rejects decimal forms,
unknown Player 1 IDs, and awakenings that are valid globally but do not belong
to that character. Player 2 is fixed to Naruto with Sakura support and the
Practice stage remains the native fixed stage. Starting HP is deliberately not
duplicated in this object:
`qol.practice.starting_hp` continues to select `full`, `half`, or `critical`.

The base, development, and release configurations disable the bootstrap. The
test configuration enables Tsunade (`84`) with Jiraiya support (`"0x18"`),
awakening `"0x57"`, and the existing half-HP Practice setting. The builder
converts the typed bootstrap object into a 16-byte read-only resident
configuration. This is a scoped generated fragment, not a new general catalog
payload schema.

A guarded file edit changes only successful Continue startup from main-menu
substate `1` to Practice substate `3`. The native Practice controller still
runs its resource states `1` through `6`. Its state-`7` Character Select call
is replaced by a resident wrapper that writes both current and match-start
character/support fields, fixes the stage, and enters the native state-`10`
battle-loading transition. Character Select and the final Practice Settings
screen are never constructed. A second wrapper retains the native active-
battle update and, when requested, applies the configured awakening once after
Player 1's live fighter exists.

The clean guards are ELF `0xE9BF8` for the post-Continue route, `0xECB2C` for
the state-`7` Character Select call, and `0xECBCC` for the state-`15` battle
update call. The reverse-engineering evidence and native field contract are in
[`../knowledge/gameplay/battle.md`](../knowledge/gameplay/battle.md).

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
forward and backward flow. Replay of `pcsx2_files/input_recordings/supports.p2m2`
confirmed that Naruto's four recorded menu markers remain unchanged while the
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

`qol.ultimate_jutsu.disable_input_contest` blocks Player 1 input during the
Ultimate Jutsu contest and suppresses its bottom meter, button prompts, and
result messages. The ordinary top battle HUD remains visible. The base
configuration enables the setting, so the development configuration inherits
it.

One guarded BTL edit passes native contest type `0` to the resident Ultimate
Jutsu factory. That disabled type creates no contest object, which removes the
interface and its later result message at their common owner. Two independent
guarded edits replace the contest controller's press-latch and release-poll
reads with zero so the recorded input cannot affect the controller even though
no interface object exists.

Development replay of `pcsx2_files/input_recordings/uj.p2m2` confirmed that
checkpoints 3 through 5 contain no bottom contest interface, checkpoints 6 and
7 contain no contest result messages, and the input latch remains zero. The
user accepted the replayed result on 2026-08-15. Clean offsets, live addresses,
NUN6 homologs, and replay evidence are recorded in
[`../knowledge/gameplay/battle.md`](../knowledge/gameplay/battle.md).

## Unlock all content without loading a save

`qol.content.unlock_all` selects the resident injection
`i__qol__content__unlock_all__availability`. Six guarded hooks replace only the
save-backed reads for characters, the Character Select R1-form gate, secondary
content, the 32-entry small table, the six grouped tables, and metadata-valid
jutsu. The injected helpers reproduce bounded fully unlocked values and the
native stable state for Collection figures; native wrappers, metadata checks,
and callers remain intact.

The feature performs no save-data writes. It therefore exposes characters and
their R1 forms, supports, stages, jutsu, Shop items, and Collection entries
without importing the reference save's settings, progress, currency,
inventory, statistics, or availability bytes. Disabling the setting restores
the native save-dependent readers.

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

## ELF-Q010: Use only first save

`ELF-Q010` changes the shared Save/Load slot-row renderer's loop limit from
three records to one at boot-ELF virtual address `0x001E6970` (file offset
`0xE6A70`). The three-slot occupancy scan, save data, and memory card remain
unchanged. Any fallback slot display therefore contains only its first record.
Two additional guarded edits replace the handler's Down and Up input-mask
results with zero before either movement branch, so vertical input cannot
change the selected slot or play the slot-navigation sound.

The upper frame is reduced from X/Y/width/height `58/10/400/224` to
`146/90/224/96`, placing a compact one-record panel above and visibly detached
from the unchanged lower instruction panel. Within it, the date/play-time block
moves from local X `108`, Y `14` to X `45`, Y `20`. The redundant slot-number
record moves outside the viewport, the row-separator condition is disabled, and
the now-meaningless independent slot-cursor model is not drawn. The lower
instruction panel and all of its contents remain unchanged.

The normal record-selection path is bypassed before its list update. The
guarded edit at runtime `0x001E5008` sets the child selection to record zero,
calls the existing `FUN_001e1e10` load operation when the controller mode is
`1`, and branches to the unchanged `FUN_001e1e50` save body for every other
mode. It then uses the controller's unchanged post-operation states.

The native `Load this data?` confirmation remains visible. Yes continues the
record-zero load. The guarded correction changes the No branch at
runtime `0x001E5474` (file offset `0xE5574`) from Save/Load state `4` to its
native completion state `8`, avoiding reconstruction of the removed record
list. The startup Continue result mapping at runtime `0x001E9FB8` (file offset
`0xEA0B8`) then maps that no-load completion to the existing success path, which
enters the main menu without loaded save data. The clean
instructions, replacement branch targets, and immediates are statically
verified, and user runtime validation confirmed the integrated behavior.

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
The test configuration disables `faster_loading`, so Manual, worker, and E2E
outputs retain native eager voice-index loading; development and release
outputs keep the faster-loading selection from the base configuration.
The complete disassembly findings, worker layout, outcome matrix, and state
machine are recorded in
[`../knowledge/game/startup.md`](../knowledge/game/startup.md).

`qol.save_load.display_only_first_save` remains an independent setting because
it controls the visible Save/Load interface and is not used by the automatic
startup driver.

## ELF-Q004: Remove Adventure mode

NUN6 A35 removes Adventure from the Mode Select carousel by storing the signed
sentinel `-1` in entry 0 of the boot ELF's seven-entry mode table. The menu setup
loop skips entries whose table value is negative, so the item is omitted rather
than displayed and blocked after selection.

The corresponding tables are:

- NA2: virtual address `0x005D51D0`, ELF offset `0x4D52D0`, values
  `(4, 2, 3, -1, 5, 6, 7)`.
- NUN5: virtual address `0x005DC300`, ELF offset `0x4DC480`, values
  `(4, 2, 3, -1, 5, 6, 7)`.
- NUN6 A35: the NUN5 address and offset, values
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
