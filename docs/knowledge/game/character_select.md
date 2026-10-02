# Native Character Select flow

This document records the native Character Select screen of retail NA2
(`SLPS-25837`): its fighter and support rosters, both sides' input flow, and
the setup records it hands to battle.

## Research coverage

- **Assigned scope:** Native Character Select fighter roster, both sides'
  selection and input flow, appearance choices, confirmation and cancellation,
  support and Linked Mode handoff, display resolution, and final setup records.
- **Exploration depth:** All 31 fighter-roster pairs, 15 entry and update
  descriptors, 62 recommendation records, and 96 portrait records were read.
  Both sides' input, transition, draw, restore, cancel, fixed-choice and final
  handoff paths were traced through their bounded resident and BTL consumers.
- **Confirmed coverage:** The two 31-column fighter rows, state/input routing,
  color and form fields, support/Linked Mode progression and Back paths,
  controller assignment dialog, final manager records, portrait/name
  resolution, 33-entry support roster and 40-entry capacity, compatibility,
  support identity/linked-attack relationships, and recommendation consumers.
- **Unresolved or untested:** The zero fourth byte's intended purpose, seven
  spare support slots, and reachability of the random helper's extra category
  branches remain unresolved. No complete visual matrix of all fighters,
  fixed-choice combinations, and cancellation states was observed.
- **Deliberate exclusions and overlap:** Character identity belongs to
  [Character identity](../gameplay/characters/character_ids.md), availability readers to
  [Content availability](content_availability.md), controller publication to
  [Controller input](../runtime/controller_input.md), shared UI animation to
  [UI animation](../runtime/ui_animation.md), battle asset loading to
  [Character asset tables](character_assets.md), support behavior to
  [Battle support mechanics](../gameplay/characters/support_mechanics.md), screen layout
  to [Character Select UI layout](../localization/ui/character_select.md), and
  Stage Select to [Stages](../gameplay/stages/stages.md).
- **Evidence limitations:** Findings are bounded static binary and call-site
  evidence. They establish the recorded paths and data contracts, not every
  possible caller or the visual result of every selection state. BTL function
  boundaries and startup code marked as data required instruction-byte
  corroboration; direct-reference inventories are not whole-program proofs.

## Binary identity and address conventions

The clean resident and BTL identities and their shared address conversions
follow [Retail game file identities](files/file_identities.md#address-conventions).

## Primary fighter roster and shared selector data

**Observation, high confidence:** Resident `FUN_003bb0b0` reads all 31
eight-byte pairs at `0x005D64C0..0x005D65B7` (ELF offsets
`0x4D65C0..0x4D66B7`). It reverses each source pair when placing the two
rows in screen-owned data: source word 1 becomes row 0, source word 0 row 1.
The resulting row IDs are:

```text
row 0: 39 5C 41 42 44 52 4E 50 3B 3D 47 40 3E 53 55 59
       5D 02 06 0D 0E 10 0C 28 2A 16 04 13 25 23 0B
row 1: 3A 46 43 45 51 56 4F 57 3C 4D 48 4C 3F 54 5B 5A
       01 07 03 05 0F 11 29 2E 2B 27 12 26 24 22 0A
```

Only columns `0..30` belong to the active list. Each row has capacity 50.
The producer fills columns `31..49` with ID zero and state 3 and stores the
active column count 31 at root
`+0x24`. Thus there are 62 nonzero base-fighter cells;
linked forms are resolved from those base cells rather than appended as extra
roster columns. Numeric identity and form pairs belong to
[Character identity](../gameplay/characters/character_ids.md#hard-coded-linked-form-mapping).

The data pointer in each `0xCC`-byte player selector is root `+0x24`.
This shared block ends at root `+0x477`, a total size of `0x454` bytes.
`FUN_003ba920` creates exactly two selectors, passes side indices 0 and 1 to
`FUN_003b4290`, and stores their pointers at root `+0x478` and `+0x47C`.
Both selectors therefore share roster and portrait data but own their cursors,
state, appearance, input snapshots, and support choice.

| Selector-data field (relative to root `+0x24`) | Contract |
| --- | --- |
| `+0x000` | Active fighter column count, 31 |
| `+0x004 + row*0xC8 + column*4` | Fighter ID, two rows with 50-word capacity each |
| `+0x194 + row*0x32 + column` | Fighter-cell availability state, two 50-byte rows |
| `+0x1F8` | Active support count |
| `+0x1FC` | 40-byte support-ID array |
| `+0x224` | 40-byte support-state array |
| `+0x24C + character_id*4` | Fighter portrait-object pointer |
| `+0x3CC + support_id*4` | Support portrait-object pointer |

`FUN_003b40c0` assigns state 3 to ID zero and otherwise assigns state 0 when
`FUN_003b3db0` accepts the ID or state 1 when it rejects it. Navigation
`FUN_003b60a0` visits states 0 and 1 and skips every other value; confirmation
`FUN_003b52e0` accepts only state 0. A locked cell can therefore be reached
but cannot be confirmed in the ordinary path. The save-backed gates are owned
by [Content availability](content_availability.md).

Roster construction is refreshed by `FUN_003bca90` before its root-state
dispatch on every call, independently of cursor movement. Initial selector
construction chooses ID `0x39`, support ID 0, and color index 0. If that
fighter's cell is unavailable, `FUN_003b4290` scans candidate IDs with
`FUN_003b5090` until it finds an available cell or returns to `0x39`.

## Appearance, fixed choices, and final handoff

**Observation, high confidence:** Fighter input `FUN_003b5df0` increments
selector `+0x14` on L1 (`0x04`) and wraps 2 to 0. Its three values are the
color choices, also used to select the color indicator rectangle at
`0x005D6460 + color*8` in `FUN_003b9a00`. Changing the fighter does not reset
this color field in `FUN_003b4750`. Held R1 (`0x08`) controls the independent
form flag `+0x18`, subject to the progression gate. The complete numeric
base/form rules are owned by
[Character identity](../gameplay/characters/character_ids.md#selector-id-filters);
the progression reader is in
[Content availability](content_availability.md#progress-gates).

Linked Mode is a separate byte at selector `+0x10`: choice 0 points to retail
`マニュアル` (Manual) at `0x005B4228`, choice 1 to `オート` (Auto) at
`0x00604808`. The pointer pair is `0x00604810/0x00604814`, consumed by
`FUN_003b8f40`. Construction explicitly initializes this byte to 1 through
`FUN_003b4a70`; `FUN_003bacd0` can restore it from the existing support-side
record. Color, form selection, and Linked Mode are three distinct fields.

`FUN_003b9f60(root, mode, fighter0, fighter1, support0, support1)` builds the
screen. Zero fighter arguments leave their choice editable; valid nonzero
arguments set selector `+0x04 = 1` and position its cursor. Invalid nonzero
fighter arguments are replaced with the first ID accepted by the ordinary
numeric filters. Support argument `0x24` leaves support editable. Other
arguments set selector `+0x08`: native support gives 1, `0x25` gives 2, and
`0x26` gives 3. `FUN_003b4d30` resolves the last two directly to their
sentinels. The fixed-support routes bypass support and Linked Mode input;
they do not add those sentinels to the scrollable support roster.

Without explicit fixed choices, `FUN_003bacd0` restores the two match-start
fighter choices from manager `+0xC8/+0xF0`, converts recognized forms back to
their base cells, and restores support from `+0xE4/+0x10C` and color from
`+0x54/+0x7C`. It also seeds each selector's support-memory `+0x70` with its
current resolved fighter. This restoration is gated by the byte at
`0x00604818` being zero and by the relevant choice remaining editable.

Once both selectors reach state 12, `FUN_003bbbb0` calls `FUN_003bb3a0`
before starting the root's exit transition. If all four constructor choices
are fixed, `FUN_003b9f60` calls the same handoff directly. Its output is:

| Choice | Side 0 destination | Side 1 destination |
| --- | --- | --- |
| Resolved fighter ID | manager `+0x4C` | manager `+0x74` |
| Resolved support ID | manager `+0x68` | manager `+0x90` |
| Color index | manager `+0x54` | manager `+0x7C` |
| Linked Mode byte | support-side record owner `+0x0D` | owner `+0x10` |
| Saved match-start fighter ID | manager `+0xC8` | manager `+0xF0` |
| Saved match-start color | manager `+0xD0` | manager `+0xF8` |
| Saved match-start support ID | manager `+0xE4` | manager `+0x10C` |

The manager pointer is at `0x00607600`; the support-side-record owner pointer
is at `0x00607888`. `FUN_003bb3a0` normalizes recognized form IDs to their
bases only for the color-collision comparison. If both normalized fighters
and chosen colors match, it increments side 1's color modulo three and
updates that selector before writing the manager. The selected fighter IDs
themselves retain the chosen forms. The support color consumer and its
separate collision rules belong to
[Battle support mechanics](../gameplay/characters/support_mechanics.md#setup-and-selected-support).

The immediate owner `FUN_001ed450` allocates the `0x4B4`-byte root, invokes
the constructor, then calls `FUN_003bca90` and draws through `FUN_003bcda0`
while it returns zero. Success returns 1 after the exit transition and the
root's two-call completion delay; cancellation returns -1. Fully fixed
construction enters the return state directly with no such delay. The owner
destroys the selector resources in either case and changes its own state to 9 on
success or `0x19` on cancellation. Parent `FUN_001ec960` routes state 9 to
`FUN_001ed6d0`, the Stage Select owner; Back there returns to state 7 and
reconstructs Character Select through the restoration path above. On stage
confirmation it advances to state 10. The stage-slot handoff and subsequent
loading belong to [Stages](../gameplay/stages/stages.md).

The later fighter factory at BTL live `0x00709860` reads the selected fighter
ID and color from those same manager side records, putting color into byte
`+0x11` of its constructor descriptor. Resident `FUN_002151e0` copies that
byte's low two bits into fighter `+0x60` bits 1..2 before model initialization.
The complete factory ownership is in
[Battle entities](../gameplay/session/battle_entities.md#primary-fighter-factory-and-lookup),
and the palette/material consumers are in
[Character assets](character_assets.md#model-and-appearance-name-consumers).

## Both sides' input ownership

**Observation, high confidence:** `FUN_003bb6a0` converts root `+0x08`
into controller assignments at root `+0x0C`/`+0x10`:

| Root `+0x08` | Retail label | Side 0 controller | Side 1 controller |
| ---: | --- | ---: | ---: |
| 0 | 1P vs 2P | 0 | 1 |
| 1 | 1P vs COM | 0 | -1 |
| 2 | COM vs 2P | -1 | 1 |
| 3 | COM vs COM | -1 | -1 |

Root update `FUN_003bbbb0` processes side 0 before side 1. An assigned side
normally calls `FUN_003b5c00(selector, controller_index)`. Once that selector
is finalized in state 12, the same controller can drive the other selector if
the other side has assignment -1. Assignment mode 3 at root `+0x08` processes
both sides despite their -1 assignments and checks selector `+0xC8` to identify
the controller that last drove an editable selection. Screen mode 0 at root
`+0x04` lets an unassigned side join on Start (`0x0800`) and initializes its
selector. The assignment changes are also passed to the match manager.
Outside assignment mode 3, Cross from a physical controller whose corresponding
side is unassigned calls the root cancellation handler directly. The label pointer
table is `0x005B4100`, with strings at `0x005B4050`, `0x005B4070`,
`0x005B4090`, and `0x005B40B0`, drawn by `FUN_003bc780` in that order.

Selector cancellation reaches root `FUN_003bba40`, whose independent mode
word is root `+0x04`. Mode 0 opens root state 3's assignment/exit dialog;
mode 1 opens root state 4's exit confirmation; mode 2 emits a rejection cue.
The assignment dialog combines both controllers' newly pressed masks, wraps
Up/Down over five rows, closes on Cross, and applies the chosen row on Circle
(`FUN_003bc320`). Rows `0..3` update the assignment mode; `FUN_003bb7d0`
resets only selectors whose assignments changed, returning them to their
first editable choice and clearing last-controller `+0xC8` to -1. Row 4
starts the cancel exit returning -1. The confirmation dialog returns to root
state 2 when its result is zero or starts that same cancel exit otherwise.

`FUN_003b5c00` reads the controller owner's public fields at context
`+0x84/+0x8C/+0x80` for controller 0, or `+0xFC/+0x104/+0xF8` for controller
1. It places newly pressed, delayed-repeat, and held masks at selector
`+0x50/+0x54/+0x58`. Selector `+0x5C` combines newly pressed with held input
while the byte cooldown at `+0x60` is zero; otherwise it decrements the
cooldown. Fighter/support movement sets that cooldown to 4. The controller
producer and button mapping belong to
[Controller input](../runtime/controller_input.md).

Input is dispatched only for fighter state 1, support state 5, or Linked Mode
state 9. A fixed-fighter flag at selector `+0x04` disables fighter input; a
nonzero fixed-support flag at `+0x08` disables support and Linked Mode input.
States 12 and 13 instead return status 2 (finalized) and 1 (cancelled).
Transition states receive no ordinary menu input through this dispatcher.

## Selection state machine

The state word is selector `+0x00`. It is not the root screen-state word.
`FUN_003b5670` changes this word and dispatches its entry action;
`FUN_003b9480` dispatches its update action. Both use 12-byte descriptors and
the resident dispatcher `0x00119B10`. All 15 entry descriptors originate at
`0x005B4238..0x005B4323`; all 15 update descriptors originate at
`0x005B4328..0x005B4413`. Their initializer copies them into writable tables
`0x005D65F0` and `0x005D66B0` (copy instructions
`0x005D9760..0x005D9CD4`). The runtime tables are zero in the file image;
the source records, not those zero words, establish the indirect targets.
The preserved analysis does not expose that initializer as a function, so
the copy instructions and source records were read as raw bytes.

| State | Entry action | Update action | Role and next state |
| ---: | --- | --- | --- |
| 0 | `003B56B0` | `003B7AF0` | Bring fighter panel in; transition progress reaches its endpoint, then 1 |
| 1 | `003B5710` | `003B7BC0` | Fighter input; Circle invokes `003B52E0`, Cross goes to 3 |
| 2 | `003B5780` | `003B7BD0` | Fighter accepted; ordinary support goes to 4, fixed support to 12 |
| 3 | `003B57E0` | `003B7C30` | Fighter cancellation, then 13 |
| 4 | `003B5840` | `003B7C60` | Bring support panel in; waits for panel endpoints and completion `+0x90`, then 5 |
| 5 | `003B58A0` | `003B7D60` | Support input; eligible Circle goes to 6, Cross goes to 7 or 13 |
| 6 | `003B5910` | `003B7D70` | Support accepted, then 8 |
| 7 | `003B5970` | `003B7DA0` | Back from support; waits for progress and `+0x90`, then 0 or 13 |
| 8 | `003B59D0` | `003B7E70` | Open Linked Mode window `+0xB8`; open completion goes to 9 |
| 9 | `003B5A30` | `003B7ED0` | Linked Mode input; Circle goes to 10, Cross to 11 |
| 10 | `003B5A90` | `003B7EE0` | Close accepted Linked Mode window; close completion goes to 12 |
| 11 | `003B5AC0` | `003B7F40` | Close cancelled Linked Mode window; close completion goes to 5 |
| 12 | `003B5B20` | `003B7FA0` | Finalized; root can finish or accept Back |
| 13 | `003B5B80` | `003B8040` | Cancelled; returns status 1 to root |
| 14 | `003B5BB0` | `003B8050` | Back from finalized; waits for completion `+0xA0`, then 8 or 1 |

Addresses in the table are NA2 resident addresses. Update entries
`003B7BC0`, `003B7D60`, `003B7ED0`, and `003B8040` are empty return stubs;
interactive work is owned by the separate input dispatcher. The exact
constant `0.1` per selector update drives fighter/support transition floats
`+0x2C` and `+0x3C`; completion flags also gate the transitions noted above.
This establishes per-call progress, not an independently measured frame rate.
The Linked Mode window's open/closed predicates belong to the shared panel
controller; its timing and draw-driven advancement are owned by
[UI animation](../runtime/ui_animation.md#shared-panel-openclose-controller).
In this screen the owner performs root input/update before drawing;
`FUN_003b9a00` reaches `FUN_003b8f40`, which draws that window through
`FUN_00380B60`. Window completion can therefore be observed by the selector
on the subsequent update, after the draw advanced it.

Fighter `FUN_003b5df0` prioritizes Circle over Cross, then L1 color selection,
Triangle random selection, and directional movement. `FUN_003b60a0` wraps
columns over the active count and rows over `0..1`; horizontal movement is
gated while the carousel anchor `+0x28` has magnitude greater than 1.
Vertical movement stays in the current column, toggles rows, and returns
without moving if neither row has a navigable state. Ordinary fighter
confirmation requires cell state zero before it resolves a form or advances.

Support `FUN_003b6910` has the corresponding Circle, Cross, Triangle, and
direction priority. Both ordinary and random-selection confirmation branches
apply availability/recommendation and compatibility gates before state 6.
Cross in state 5 enters state 7 for an editable fighter, or state 13 for a
fixed fighter. Linked Mode `FUN_003b79a0` uses newly pressed Circle/Cross
and repeated Up/Down to wrap its byte choice at `+0x10` over `0..1`.
It preserves that choice when backing out; the two player-local choices are
separate from fighter color at `+0x14`.

From finalized state 12, root `FUN_003bbbb0` accepts Cross. If either fighter
or support remains editable it enters state 14; that state normally reopens
Linked Mode through state 8. With fixed support it instead returns to fighter
state 1. When both selections are fixed, Back enters state 13. If the
controller was driving the other unassigned side, root first resets that
other selector's editable state and then applies Back to its own finalized
selector. Thus Back follows the selection owner rather than always undoing
the visually active side.

Triangle toggles random selection using selector `+0x40`, with counter
`+0x44` and a per-update guard at `+0x48`. While active, Circle retains the
ordinary confirmation path; Cross or Triangle stops random selection and
returns to ordinary editing. Fighter sampler `FUN_003b63d0` scans both
50-slot rows, admitting only state-zero entries whose stored fighter ID
differs from the current resolver's result. Support sampler `FUN_003b6f90`
scans all 40 support slots, excludes the current support, and admits only
available or recommended IDs that pass compatibility. Each samples a
candidate through `FUN_00180210(count - 1)` and repositions with the native
setter. The counter selects on every second eligible invocation; selector
update clears the per-update guard. With no candidates, the sampler leaves
the choice unchanged. Extra fighter category branches `2..5` exist in the
sampler, but the inspected Triangle handler sets only category 1; their
reachability is not established.

## Scrollable support roster

NA2 `FUN_003bb210` populates the scrollable support list. Its two callers are
at runtime addresses `0x003BB08C` and `0x003BCAB0`, stored at ELF offsets
`0x2BB18C` and `0x2BCBB0`.

The function reads 33 IDs from runtime `0x005D65C0`, writes them at Character
Select object offset `+0x220`, writes their availability states at `+0x248`,
and stores the count at `+0x21C`. It fills the remaining slots through index 39
with sentinel ID `0x24` and state `7`, giving the list a 40-entry capacity.

The clean 40-byte table at ELF offset `0x4D66C0` is:

```text
00 01 20 02 03 04 05 06 07 13 14 15 11 10 12 16
08 09 0A 0F 0D 0E 0B 0C 1B 1E 18 19 1A 1F 1C 1D
21 00 00 00 00 00 00 00
```

The first 33 bytes are the visible native roster. NUN5 has the same function,
bound, and list at its homologous runtime table `0x005DD710`. NA2 also uses
support ID `0x25` to represent No Support in Story Mode, but that ID is absent
from the native Character Select roster.

## Compatibility

Character Select calls the BTL compatibility helper exposed to the main ELF as
`SUB_008858C0`, whose BTL body is `FUN_00885880`. The helper begins with an
unsigned `support_id < 0x24` gate and returns zero immediately for larger IDs.
For a native support ID, it resolves the fighter through resident
`0x001F7E70` when that helper returns an identity other than `-1`, then rejects
matches in a 104-entry support/fighter exclusion table. Otherwise it returns
one. The body of `FUN_00885880` confirms that the native check
is an exclusion list, separate from the linked-attack relationship tables.

The red unavailable marker in resident `FUN_003B84D0` uses that same predicate.
The confirmation handler `FUN_003B6910` also requires a selectable fighter
(`1..0x5D`, with resident `0x001F7AA0` and `0x001F7BB0` both returning zero)
and either roster state `4` or a match among the three recommendations returned
by BTL live `0x00885C30`. Thus an otherwise locked recommended support can
still be selected if compatible.

The exclusion table is at live `0x008D1980` (Ghidra byte address `0x008D1940`).
It contains `(support, fighter)` pairs `(0x0C, 0x3F)`, `(0x0C, 0x4C)`,
`(0x1E, 0x3F)`, and `(0x1E, 0x4C)`: Hiruko and Sasori supports are both
excluded for either Sasori or Hiruko. Resident `0x001F7E70` normalizes Sasori's
puppet fighter `0x4B` to `0x3F` before that lookup. These are static code
and table observations.

The clean NA2 main ELF has six calls to this helper:

| Consumer | ELF offset |
| --- | ---: |
| Default support compatibility | `0x2B5088` |
| Initial support-selection transition | `0x2B56FC` |
| Primary confirmation | `0x2B6BEC` |
| Repeated confirmation | `0x2B6F7C` |
| Navigation | `0x2B72B0` |
| Draw eligibility | `0x2B8A38` |

Each site contains the clean call bytes `30 16 22 0C`.

## Support identities and relationships

BTL runtime table `0x008D28A0` (Ghidra byte address `0x008D2860`),
stored at complete-file offset `0x21E9A0`
in `BTL.BIN`, contains 34 three-byte rows mapping each native support ID to a
character record and display record. The character and display bytes match in
all 34 rows. Support ID `0x17` maps to character record `0x58`; the other 33
records correspond to playable characters.

Two separate BTL tables define linked attacks. The ten four-byte rows at
live `0x008D2660` (Ghidra `0x008D2620`), complete-file offset
`0x21E760`, store a support ID,
selected character ID, and little-endian linked Ultimate Jutsu ID.
`FUN_00885620` checks all ten rows:

| Selected character | Support IDs |
| --- | --- |
| Naruto (`0x39`) | Sakura (`0x01`) |
| Sakura (`0x3A`) | Naruto (`0x00`), Chiyo (`0x1B`) |
| Chiyo (`0x3E`) | Sakura (`0x01`) |
| Sasori (`0x3F`) | Deidara (`0x0B`) |
| Deidara (`0x40`) | Sasori (`0x1E`) |
| Itachi (`0x47`) | Kisame (`0x0E`) |
| Kisame (`0x48`) | Itachi (`0x0D`) |
| Orochimaru (`0x59`) | Sasuke (`0x21`) |
| Sasuke (`0x5D`) | Orochimaru (`0x1C`) |

The five six-byte rows at live `0x008D2880` (Ghidra `0x008D2840`), complete-file offset
`0x21E980`, store a support ID, selected character ID, ordinary Jutsu ID, and
little-endian linked replacement ID. `FUN_00885ec0` checks all five:

| Selected character | Support IDs |
| --- | --- |
| Naruto (`0x39`) | Gaara (`0x08`), Sai (`0x20`) |
| Shikamaru (`0x44`) | Choji (`0x13`) |
| Tsunade (`0x54`) | Jiraiya (`0x18`) |
| Sasuke (`0x5D`) | Naruto (`0x00`) |

## Support cursor and carousel

Native support-cell renderer `FUN_003b84d0`
visits carousel offsets `-6..6` and wraps each offset modulo the support-list
count. Its selector float at `+0x38` is the horizontal carousel anchor, scaled
by 36 internal pixels when drawing cells.

Resident `FUN_003B49C0(player, support_id)` resets cursor index `+0x30`, page
`+0x34`, and scroll anchor `+0x38` to zero, then scans the 40 roster slots for
the requested ID with availability state `4` or `5`. It assigns the matching
index and page. The native default
selection routine `FUN_003B4E40` uses this setter.

The support cursor persists across fighter confirmations. Selector `+0x70`
holds the fighter associated with the cursor: the constructor
`FUN_003B4290` zeroes it, `FUN_003B51A0` stores the current fighter when
`FUN_003B4E40` resets the cursor, and entry restoration `FUN_003BACD0`
also seeds it after restoring the two choices. Fighter confirmation
`FUN_003B52E0` enters support selection with state `2`, calls `FUN_003B4E40`
when `+0x70` differs from the confirmed fighter, then reads the entry under the
cursor. It keeps that entry when its state is `4` or it is one of the
fighter's three recommended supports, and it also passes the `0x008858C0`
compatibility check; otherwise it calls `FUN_003B4E40` again. Confirming the
same fighter therefore returns to the previously selected support.
`FUN_003B4E40` selects the first recommended support for an eligible fighter,
and otherwise the first support whose state is `4`.

Horizontal support navigation calls `FUN_003b7280` from two sites. Left passes
direction `2` at runtime `0x003B6C48` (ELF offset `0x2B6D48`); right passes
direction `3` at runtime `0x003B6C8C` (ELF offset `0x2B6D8C`). The native
function decrements or increments the support index and wraps across the two
ends of the list.

## Display resolution

**Observation, high confidence:** `FUN_003ba920` constructs portrait objects
for every display ID `1..95`, while root initialization leaves slot zero
null. It uses `charsel1.ccs` with `CMP_chara_ita01`/`MDL_chara_ita01`, not a
fighter body container. The complete 96-row, 12-byte portrait table is
resident `0x005D46F0..0x005D4B6F`: word `+0` is a texture-bank index,
halfwords `+4/+6` the atlas origin, and `+8/+0xA` the rectangle size.
`FUN_0037d300` returns the bank and `FUN_0037d330` normalizes the origin
against 512 by 512. Fighter portrait construction formats
`TEX_purecharsel%02d` with `bank + 1`, installs the texture into the plate
model, and stores the resulting object at root `+0x270 + display_id*4`.
Those records include locked and empty display IDs `0x5E/0x5F`.

Fighter-cell draw `FUN_003b80c0` visits 13 wrapped columns (`-6..6`) for
each row. Only its central active cell uses resolved form ID from
`FUN_003b4a90`; other cells use stored roster IDs. State 1 substitutes
display ID `0x5E`, and states 2/3 substitute `0x5F`. Selected-name draw
`FUN_003b9a00` and large-portrait draw `FUN_003b83e0` independently use the
same resolved fighter ID. The latter positions the shared portrait object
on the appropriate side before rendering it. Character-name rectangles and
footer artwork ownership are in
[Character Select UI layout](../localization/ui/character_select.md).

The support-object construction loop separately creates 34 objects at root
`+0x3F0`, resolving support IDs through the support-to-display helper. The
inspected large support portrait consumer `FUN_003b8d50` nevertheless uses
the fighter portrait array indexed by resolved display ID and positions it
from the support-panel attachment. It does not read the support-object
array. Root cleanup `FUN_003b9ce0` destroys both arrays and both selectors;
selector cleanup `FUN_003b4100` destroys its owned panels, animations, and
sprite groups. The broader use of the separate support-object array is not
inferred from its allocation.

The clean main ELF calls BTL support-to-display helper `0x008859A0` six times.
Its mapping table covers native support IDs only through `0x21`; larger IDs use
the default display record zero.

Four Character Select consumers resolve display records through that helper:

| Consumer | Runtime address | ELF offset |
| --- | ---: | ---: |
| Scrollable-list primary path | `0x003B8724` | `0x2B8824` |
| Scrollable-list available path | `0x003B8774` | `0x2B8874` |
| Selected-name record | `0x003B8B6C` | `0x2B8C6C` |
| Selected large portrait | `0x003B8DD4` | `0x2B8ED4` |

Each contains the clean call bytes `68 16 22 0C`. The selected-name renderer is
called separately at runtime `0x003B9B74`, stored at ELF offset `0x2B9C74`.

## Recommendation records

**Observation, high confidence:** The retail helper is live `0x00885C30`
(Ghidra function start `FUN_00885bf0`, complete-file offset `0x1D1D30`).
It normalizes the fighter through resident `0x001F7E70`, scans 62 eight-byte
records, and returns `record[4 + requested_index]` from the first matching
fighter-ID word. No match returns zero. The complete table is live
`0x008D2690..0x008D287F` (Ghidra `0x008D2650..0x008D283F`, complete-file
offset `0x21E790`, length `0x1F0`). Each record has a 32-bit fighter ID,
three recommended support IDs at `+4..+6`, and a zero byte at `+7`.
All 62 records were read; their fighter IDs exactly cover the 62 nonzero
base-roster cells. The last byte is zero in every row, but its intended
purpose is not established. The helper itself does not check the requested
index.

The preserved import splits this helper at `0x00885C30`, producing a
misleading partial decompilation with uninitialized registers. The prologue,
normalization, bounded scan, byte load, and return were corroborated across
the full preserved (Ghidra) byte range `0x00885BF0..0x00885C9F`, live
`0x00885C30..0x00885CDF`.

The Character Select consumers establish the first three bytes' role:
`FUN_003b51d0`, fighter confirmation, both support-confirmation branches,
random support selection, directional navigation, and support-cell rendering
compare roster IDs with recommendation indices `0..2`. They allow a locked
recommended support, while compatibility remains a separate gate. Default
support `FUN_003b4e40` uses index 0; the selected support name and large
portrait also use index 0 when resolving special support ID `0x26`.
Seven direct BTL calls likewise use index 0 for special-support resolution.
No fourth-field meaning is inferred from those calls.

Recommendations need not be distinct: fighter `0x04` has `09 0A 09`, and
fighter `0x0A` has `00 02 00`. Nor do they equal the linked-attack sets:
Naruto `0x39` recommends `01 02 18`, whereas its linked partners include
supports `08` and `20` through the separate tables above. Thus these bytes
are selection recommendations and locked-selection exceptions, not an
alternative roster or a definition of linked attacks.
