# Practice-mode architecture

This document owns the established architecture of clean NA2 Practice Settings
and the battle-side policies that consume those settings. It deliberately does
not duplicate the starting-HP savestate evidence and direct-Practice bootstrap
owned by [`battle.md`](battle.md), or the localized layout measurements and
string work owned by
[`practice.md`](../localization/font/screen_layouts/practice.md) and
[`settings_and_results.md`](../localization/ui/battle/settings_and_results.md).

The controller, object, table, and transaction findings below are static unless
a runtime observation is stated explicitly. In particular, they do **not**
establish the cause of the currently reported Practice Settings flicker.

## Research coverage

- **Assigned scope:** clean-NA2 BTL Practice Settings architecture beyond the
already-owned starting-HP work: menu/controller ownership, the option record,
state and input transitions, Confirm/Cancel/Defaults and restart paths, dummy
behavior settings, resource/gauge semantics, and the controller/render split
needed for a later flicker trace. This document is the sole output of that
lane.

- **Exploration depth:** coverage was bounded but deep, with exhaustive treatment only inside the
following explicit boundaries:

- the complete 17-row menu schema was exhaustively recovered from the clean
  label, help, value-pointer, count, snapshot, Defaults, enabled-row, and setter
  tables/paths. All 17 local offsets, value bounds, local defaults, manager
  keys/storage, availability predicates, and the menu's setter order were
  checked;
- the Practice child family was followed end to end through BTL live
  `0x008809E0..0x00882670`: allocation/resource construction, reset/snapshot,
  apply/defaults, input and repeat handling, phase update, row/window geometry,
  drawing, destruction, and Link Mode access. Direct raw-`jal` enumeration of
  the update and draw entries found the two documented caller families;
- ownership was followed through the generic parent/UI-owner path at live
  `0x006BE810..0x006C12A0` and `0x00714164..0x00715D08`, and through the
  standalone wrapper/selector-host path at live
  `0x00875AB0..0x0087E538`. The type-`5` factory entry and 15-entry module jump
  table were inspected. This is exhaustive for the direct static caller and
  single-module-slot relationships, but not for runtime scheduling between the
  two top-level owners;
- manager storage/default/getter/setter behavior was bounded to resident
  `FUN_001E7A80`, `FUN_001F5910`, `FUN_001F5960`, `FUN_001F59F0`,
  `FUN_001F6420`, and `FUN_001F6D30/FUN_001F6D50`, plus the separately owned
  dynamic-support manager whose side records also store Link Mode, including
  its BTL setup/teardown and constructor at live `0x00885210`, `0x00885290`,
  and `0x00886CB0`;
- dummy behavior was traced only far enough to establish every Practice row's
  setting-specific gate or effect. The bounded BTL set includes live
  `0x006F5410`, `0x006F95B0`, `0x006FA590`, `0x006FAA50`, `0x006FB0D0`,
  `0x006FE720`, `0x006FF410`, `0x006FF650`, `0x007024A0`, `0x00704D40`, and
  `0x00705D70`. The complete general-AI state machine, every downstream action
  object, and every field in the 40-short Strength profile were not
  exhaustively reconstructed;
- reset/resource work covered the resident outer Practice controller through
  `FUN_001EC960..FUN_001ED110`, both snapshot directions
  `FUN_001ECC00/FUN_001ECDE0`, and the BTL item-cache entries at live
  `0x0070F1E0`, `0x007109F0`, and `0x00710B00`. All mask bits consumed by those
  two snapshot functions were enumerated; unrelated save/replay systems were
  not surveyed;
- the Ultimate row was followed from its zero/positive AI gate through BTL live
  `0x006EE560`, the sole raw caller at `0x0076A0CC` in live function
  `0x00769790`, and the resident mode-controller dispatcher. The four-pair
  Random table at resident `0x005ACD70` was evaluated exactly. This did not
  expand into general Ultimate-Jutsu gameplay mechanics.

- **Confirmed coverage:** the live/file/preserved-export
address convention, both ownership chains, parent and child states, controller
selection and input masks, transactional menu behavior, manager and per-side
record layouts, dummy Status/Attack/Guard/Move routing, Strength profile copy
and hot reload, linked/extra-hit/item/substitution branches, Ultimate mode
dispatch, discrete snapshot masks, continuous HP/chakra/Link Gauge policies,
resource lifetime, and the exact update/draw gates useful as watchpoints.

- **Unresolved or untested:** the runtime cause of the
reported flicker; whether the main and standalone owners coexist in a failing
frame; full timing and naming of the general AI/controller graph; later
transitions and engine names for several linked-work fields; semantics of every
Strength-profile field; and the producer/unlock event for manager slot `0x6A`.
- **Deliberate exclusions and overlap:** starting-HP/bootstrap evidence stays in `battle.md`; localization and layout
stay in their existing Practice/UI documents. Adventure, damage-scaling
formula work, broad substitution mechanics, 60-FPS work, widescreen,
localization, and PCSX2 infrastructure were intentionally excluded to avoid
the other scoped lanes.

- **Evidence limitations:** validation was static against the identified clean `BTL.BIN` and
`SLPS_258.37`: raw bytes/disassembly were used to correct the preserved
Ghidra overlay's omitted-header coordinates, and tables/call sites were checked
against the complete raw overlay. No controller-input run, breakpoint trace,
live ownership trace, or failing-flicker capture was performed. Consequently,
the document distinguishes exact static effects from inferred names and does
not assign a runtime flicker cause.

## Evidence identity and address conventions

The battle overlay is the clean `PRG/BTL.BIN` with:

- size `2,237,184` bytes;
- SHA-256
  `56FD042740221E3CC91417194F147142799D51FE70642273F4E97BD389D5D63C`;
- `MWo3` header base/live load address `0x006B3F00`.

The resident executable is clean `SLPS_258.37`, SHA-256
`20C0A40D70EA412CD431993A2E189B37ECB6054D63AE93BE545470016E1627AF`.
Resident addresses such as `FUN_001F59F0` are ordinary EE runtime addresses
and are not subject to the overlay-header correction.

The complete BTL file and live memory both retain the `0x40`-byte `MWo3`
header. The preserved Ghidra baseline omitted that header from its mapped
payload. Therefore, for an overlay-local instruction or datum:

~~~text
complete file offset = live address - 0x006B3F00
preserved export address = live address - 0x40
live address = preserved export address + 0x40
~~~

The complete-file formula identifies a byte only when the result is below the
file size `0x222300`. Higher nominal offsets are overlay BSS: they exist in
live memory and in the preserved export's extended address space, but not as
stored bytes in `BTL.BIN`.

An absolute pointer or `jal` target encoded in the raw overlay is already a
live address. It must **not** receive another `+0x40`. The preserved export can
consequently create a misleading symbol at that numeric target, forty bytes
into the actual function; the real prologue appears at `target - 0x40` in the
export. This is why the tables below state live target, complete-file offset,
and preserved-export prologue separately.

The same warning applies to absolute data operands. For example, the Strength
copy encodes source `0x008C3230` and destination `0x008D66F0`; those are the
live addresses. Ghidra names symbols at those encoded numbers even though the
preserved byte displayed at export `0x008C3230` is the complete-file byte that
actually lives at `0x008C3270`. Static table contents must therefore be read
at `complete offset = encoded live - 0x006B3F00`, not from the misleading
same-number export symbol.

## Ownership chain

The main battle manager is reached through the resident pointer at
`0x00607600`, named `iGpffffcc10` in the BTL export. Confirmed fields used by
this subsystem are:

| Manager offset | Meaning |
| ---: | --- |
| `+0x0C` | mode; `3` is Practice |
| `+0x18` | active/controller side, `0` or `1` |
| `+0x9F4..+0x9FF` | active Practice settings pack |
| `+0xA00..+0xA0B` | alternate settings pack used outside modes `2/3` |
| `+0xA0C..+0xA17` | third default-initialized pack; established Practice use is the persistent Strength mirror at `+0xA13` |
| `+0xDE4` | Player 1 live-fighter pointer |
| `+0xDE8` | Player 2 live-fighter pointer |

The battle UI owner stores a pointer at `+0xA8` to a generic `0x54`-byte
settings parent. The raw constructor sequence at live `0x00714164..0x00714194`
allocates it, calls live `0x006BFD30` and `0x006BFFF0`, and stores it at
`owner+0xA8`. The generic constructor checks `manager+0x0C`:

- mode `3` allocates the `0xB8`-byte Practice child, initializes it through
  live targets `0x008809E0` and `0x00880BE0`, and stores it at parent `+0x3C`;
- mode `2` instead allocates a `0x68`-byte Battle Settings child and stores it
  at parent `+0x38`;
- other modes allocate neither settings child.

The parent controller and renderer are separate calls:

~~~text
BTL UI owner +0xA8
  -> generic parent +0x3C
     -> Practice child

preserved export FUN_00714C70 (live entry 0x00714CB0)
  -> parent update, live 0x006C0F60
     -> Practice update, live 0x00881AB0, while parent state is 5

preserved export FUN_00715C80 (live entry 0x00715CC0)
  -> parent renderer, live 0x006C1120
     -> Practice draw, live 0x00882250, while parent state is 5
~~~

There is also a smaller wrapper path whose preserved-export update and draw
functions are `FUN_00875AE0` and `FUN_00875B10` (live entries `0x00875B20`
and `0x00875B50`). It owns a Practice child at wrapper `+0x0C` and invokes the
same live update and draw targets. It is a second caller, not a second settings
implementation.

That wrapper is module type `5` in a separate screen-selector host. The live
factory at `0x0087BB10` indexes the 15-entry jump table at live `0x008D1690`;
case `5` allocates the `0x10`-byte wrapper and installs its class table. At the
factory join, the host destroys any previous module at host `+0x38` through
its virtual destructor, stores the new wrapper there, copies host context into
wrapper `+0x00/+0x04`, invokes the wrapper construction callback, and enters
host state `5`. The wrapper construction callback at live `0x00875AB0`
allocates the same `0xB8`-byte Practice child, initializes it through live
`0x008809E0`, and constructs its resources through live `0x00880BE0` with
variant `0`. Wrapper destruction reaches the child destructor at live
`0x00880A20` from live call site `0x0087E538`, then frees the child.

The host's module-list builder at live `0x0087B3B0` calls resident
`FUN_001EC240()`. Only return value `2` appends module type `5` to that list;
the same branch derives the controlling side from `manager+0x18`. Once type
`5` is selected, host update live `0x0087CB20` invokes virtual slot `+0x10` on
the sole `host+0x38` module, reaching wrapper update live `0x00875B20`. Host
draw live `0x0087D460` dispatches host state `5` to virtual slot `+0x14`,
reaching wrapper draw live `0x00875B50`. Each host path makes one such virtual
call per invocation.

Thus the selector host itself cannot retain two Practice modules in its
single `+0x38` slot. This does not establish whether that host and the main
battle UI owner can be active simultaneously; that remains a runtime ownership
question.

### Generic parent states

Live `0x006C0F60` dispatches on parent `+0x00`:

| State | Behavior |
| ---: | --- |
| `0` | poll resource handle `+0x48` through resident `0x00183FD0`; advance to `2` when ready |
| `1` | call live `0x006C06F0` |
| `2` | call live `0x006C07C0` |
| `3` | increment `+0x50`; after two ticks return result `+0x4C` |
| `4` | update Battle Settings child `+0x38` through live `0x0087FF60`; return to `2` when the child completes |
| `5` | update Practice child `+0x3C` through live `0x00881AB0`; return to `2` when the child completes |

The parent reset entry is live `0x006C0380`. It resets shared parent/child
presentation state and starts the parent's transition resource. UI-owner paths
whose preserved-export prologues are `0x007146C0` and `0x00714700` (live
entries `0x00714700` and `0x00714740`) call this entry on `owner+0xA8`.

Live `0x006C07C0` owns the parent state's selector/open transaction. It updates
two selector children at parent `+0x30` and `+0x34` through live
`0x006BE810`, skips entries whose corresponding parent availability word
`+0x04`/`+0x08` is negative, and interprets the child return codes as follows:

- return `2` cancels the whole settings parent: it records result `-1` in
  parent `+0x4C`, enters state `1`, clears timer `+0x50`, starts the transition
  handle at `+0x48`, and plays sound `0x33`;
- return `3` opens the available settings child: it enters state `4` and calls
  the Battle child reset at live `0x0087F9D0`, or enters state `5` and calls
  the Practice reset/snapshot at live `0x00880F30`; sound `0x34` accompanies
either open;
- when both selector updates have reported completion, it closes the parent
  with result `1`, starts the same state-`1` transition, and plays `0x34`.

Controller selection is resolved at this outer selector layer. When
`manager+0x1C == 3`, the parent passes source `2` to both selectors; otherwise
it passes source `0` to the first and `1` to the second. Live `0x006BE810`
stores that source at selector `+0x1C`; source `0` samples the first input
record, source `1` the second, and source `2` ORs both records. It snapshots
new, secondary, and held masks into selector `+0x20`, `+0x24`, and `+0x28`
before dispatching the selector's own phase at `+0x00`. After Practice opens,
the Practice child does not reuse these cached masks: live `0x00881660`
resamples the active side selected by `manager+0x18`.

Live `0x006C06F0` polls that transition handle. On completion it enters parent
state `3`, clears `+0x50`, and, in Practice mode, calls resident
`FUN_001F48F0` to select the manager control-side mode: argument `0` when
Status is Manual, otherwise argument `1` when `manager+0x18 == 0` or argument
`2` when `manager+0x18 != 0`. State `3` then delays for two parent updates and
returns the recorded `+0x4C` result. This manager-side update belongs to
closing the overall settings parent, not to the Practice child's Confirm
apply routine.

The battle UI owner's update wrapper is live `0x00714CB0` (preserved prologue
`0x00714C70`). It forwards `owner+0xA8` to the parent update. Parent result
`1` is propagated to the wrapper's caller. On result `-1`, an owner with
`owner+0x0C >= 0` enters owner state `5`; an owner with a negative `+0x0C`
instead calls the owner reinitializer at live `0x00714700`. This is the first
consumer of the parent's delayed result and keeps child completion, parent
closure, and owner transition as three distinct state boundaries.

## Practice child record

The child is `0xB8` bytes. The following layout is established from its
constructor, reset, update, input, and draw consumers:

| Offset | Size | Established role |
| ---: | ---: | --- |
| `+0x04` | 4 | loaded archive/resource handle |
| `+0x08..+0x14` | 4 each | four owned `0x40`-byte backing/render objects |
| `+0x18..+0x24` | 4 each | prompt/panel render objects |
| `+0x28..+0x30` | 4 each | owned sprite/draw objects |
| `+0x34` | 4 | help/selector text object |
| `+0x38` | 4 | child phase: `0` fade in, `2` interactive, `1` fade out |
| `+0x3C` | 4 | selected row, `0..16` |
| `+0x40` | 4 | directional-repeat arbitration countdown |
| `+0x44` | 4 | floating-point vertical row offset, eased toward the selected page |
| `+0x48` | 1 | backdrop variant: main parent passes `1`, standalone wrapper passes `0` |
| `+0x4C`, `+0x50`, `+0x58` | 4 each | cyclic floating-point presentation phases, advanced by `0.05`, `0.01`, and `0.04` per update |
| `+0x54` | 2 | alpha/transition value, clamped to `0..0xC0` in `0x32` steps |
| `+0x56` | 2 | post-fade render delay, advanced to `3` |
| `+0x5C` | 2 | draw-transform/presentation state |
| `+0x60` | 4 | newly pressed input mask |
| `+0x64` | 4 | held/repeat input mask |
| `+0x68` | 4 | effective directional mask for the current update |
| `+0x6C..+0xAC` | 17 x 4 | local option values for rows `0..16` |
| `+0xB0` | 4 | upper-window start index (`0..2`) for rows `0..8` |
| `+0xB4` | 4 | lower-window start index (`0..2`) for rows `9..16` |

The exact engine class names behind the resource pointers and several
presentation accumulators remain unknown. Their ownership and consumers are
established; more specific semantic names would currently be guesses.

Live `0x00880F30` resets the phase, selection, animation, sampled input, and
page fields and calls live `0x00880FB0` to snapshot the current manager
settings into the 17 local values. Each value is clamped into the range
declared by the live count table at `0x008D18C0`. As detailed in the input
section, this reset does not write directional-repeat countdown `+0x40`.

## Rows, local values, and manager storage

The native menu has 17 rows. The values below are the clean table contents and
help-text meanings. “Default” is what the menu's local Defaults action writes.

| Row | Local | Label and values | Count | Manager key/storage | Default |
| ---: | ---: | --- | ---: | --- | ---: |
| `0` | `+0x6C` | Health: Normal, Half, Almost | 3 | key `4`, `+0x9F5` | `0` |
| `1` | `+0x70` | Chakra: Normal, Unlimited | 2 | key `2`, `+0x9F4` bit 2 | `0` |
| `2` | `+0x74` | Linked Attack / Link Gauge: Normal, Unlimited | 2 | key `3`, `+0x9F4` bit 3 | `0` |
| `3` | `+0x78` | Ultimate Jutsu: No Use, Random, Command, Timing, Turn, Combo | 6 | key `5`, `+0x9F6` | `2` |
| `4` | `+0x7C` | Link Mode: Manual, Auto | 2 | separate per-side configuration | `1` |
| `5` | `+0x80` | Items: None, Less, Normal, More | 4 | key `7`, `+0x9F8` | `2` |
| `6` | `+0x84` | Command Display: OFF, ON | 2 | key `1`, `+0x9F4` bit 0 | `1` |
| `7` | `+0x88` | Damage Display: OFF, ON | 2 | key `9`, `+0x9F4` bit 4 | `1` |
| `8` | `+0x8C` | Guide Ninja Sound: OFF, ON | 2 | key `0xA`, `+0x9F4` bit 5 | `1` |
| `9` | `+0x90` | Status: Manual, COM, Stand, Jump, Double-jump | 5 | key `0xC`, `+0x9FA` | `2` |
| `10` | `+0x94` | Strength: Easiest, Easy, Normal, Hard, Very hard, Ultimate | 6 | key `0xB`, `+0x9FB` | `2` |
| `11` | `+0x98` | Attack: No, Single, Combo, Projectile, High Speed Move, Ultimate Jutsu, Jutsu | 7 | key `0xD`, `+0x9FC` | `0` |
| `12` | `+0x9C` | Guard: No, Use | 2 | key `0xE`, `+0x9FD` | `0` |
| `13` | `+0xA0` | Move: Stay, Follow | 2 | key `0xF`, `+0x9FE` | `0` |
| `14` | `+0xA4` | Substitution Jutsu: Normal, Don't use | 2 | key `0x11`, `+0x9F4` bit 7 | `0` |
| `15` | `+0xA8` | Linked Attack: Don't use, Normal, frequent/random (`乱発`) | 3 | key `0x12`, `+0x9FF` | `1` |
| `16` | `+0xAC` | Extra Hit Counter: Normal, Always return | 2 | key `0x10`, `+0x9F4` bit 6 | `0` |

Rows `2` and `15` share an English-facing label but are different controls.
The row-2 help describes how the player's Link Gauge charges; row 15 controls
the non-manual dummy's linked-attack use.

The Status/Strength key order is non-obvious and confirmed in both snapshot
and apply code: Status is key `0xC` at `+0x9FA`, while Strength is key `0xB`
at `+0x9FB`. Resident `FUN_001F6D30` mirrors only key `0xB` (Strength) to
manager `+0xA13`.

Link Mode is not part of the manager's 12-byte settings pack. Live
`0x00882630` reads, and live `0x00882670` writes, a byte in a per-side global
record selected by `manager+0x18`. The effective record is
`gp-0x3168 + side*3 + 0x0C` and the setting is its byte `+1`.

That global points to the separate `0x24`-byte dynamic-support manager
described in [Support mechanics](support_mechanics.md). BTL setup live
`0x00885210`, called by resident outer-controller construction
`FUN_001EC7A0`, destroys any previous object, allocates a replacement, and
constructs it through live `0x00886CB0`. The constructor lays out two
three-byte side records at object `+0x0C` and `+0x0F`, initializing each as
`{0, 1, 0}`; the middle byte is therefore the established Link Mode field and
starts as Auto. Resident outer-controller teardown reaches BTL live
`0x00885290`, which destroys the object and clears the global. The roles of the
other two bytes in each three-byte record are outside the established Practice
setting path.

### Row availability

Live `0x008814F0` is used by both input and drawing:

| Rows | Enabled condition |
| --- | --- |
| `0..9` | always |
| `10` Strength | Status == COM (`1`) |
| `11..13` Attack/Guard/Move | Status is Stand, Jump, or Double-jump (`2..4`) |
| `14` Substitution | Status == COM (`1`) |
| `15..16` Linked Attack/Extra Hit | Status != Manual (`0`) |

Disabled rows are drawn grey and cannot be changed. The sixth Strength value
is additionally unavailable when resident
`FUN_001F7780(manager, 0x6A) == 0`; in that case row 10's maximum is reduced
from `5` to `4`. `FUN_001F7780` reads a 32-bit indexed slot in the
manager-owned profile/progress record (the underlying `FUN_001E3D40` indexes
`base+0xE60`). Resident difficulty-selector input and draw routine
`FUN_0038BAC0` use the same slot `0x6A` to reduce a six-value selector's
maximum in exactly the same way. Slot `0x6A` is therefore the gate for the
sixth/Ultimate difficulty tier; the event which sets that slot remains
unknown.

## Input and child state transitions

Live `0x00881660` owns input. It selects a `0x78`-stride side record under
`iGpffffca0c` using `manager+0x18`, copies new presses from input `+0x84` to
child `+0x60`, and copies held/repeat input from input `+0x80` to child
`+0x64`. If the repeat countdown `+0x40` is positive, new presses drive
`+0x68` and the countdown is decremented; otherwise held/repeat input drives
`+0x68`. Releasing all four directions clears the countdown. Every accepted
row navigation or value change reloads the countdown to `4`; Confirm, Cancel,
and Defaults bypass the directional path.

Live `0x00881910` changes rows:

- `0x1000` selects the preceding row and wraps `0 -> 16`;
- `0x4000` selects the following row and wraps `16 -> 0`.

Live `0x00881990` changes the current enabled value:

- `0x2000` increments while below the row maximum;
- `0x8000` decrements while above zero.

Navigation and accepted value changes play sound `0x35`.

The ordinary child reset at live `0x00880F30` clears the sampled/effective
masks `+0x60/+0x64/+0x68`, but does not write repeat countdown `+0x40`.
Consequently the countdown can survive a close/reopen until four directional
updates elapse or an update observes no held direction and clears it. It only
selects which directional mask reaches navigation/value handling; it does not
write a resource pointer, phase, or draw gate.

Live `0x00881AB0` owns the child phase:

- phase `0` raises alpha `+0x54` by `0x32` per update to `0xC0`, then enters
  interactive phase `2`;
- phase `2` samples input, navigates, changes values, and handles actions;
- phase `1` lowers alpha by `0x32` per update and returns completion only once
  it reaches zero. The parent then changes state `5 -> 2`.

Before dispatching that phase, every child update advances the three cyclic
presentation phases and updates the row window. Rows `0..8` use resident
`FUN_0037D9C0(selection, +0xB0, 7, 2, 9)`; rows `9..16` use
`FUN_0037D9C0(selection-9, +0xB4, 6, 2, 8)`. Both window starts are bounded to
`0..2`. Live `0x006C12A0` then moves the floating-point offset `+0x44` toward
`-30 * +0xB0` on the upper half or `-270 - 30 * +0xB4` on the lower half, by
at most `20.0` per update. The draw loop begins its first row at `+0x44 + 14`
and adds the separate `18`-pixel gap before row `9`. Selection therefore
changes controller-owned geometry without reconstructing any render object.

The interactive actions are transactional:

| New-press bit | Action |
| ---: | --- |
| `0x20` | Confirm: call live `0x008811A0` immediately, enter fade-out phase `1`, play `0x34` |
| `0x40` | Cancel: do not apply, enter fade-out phase `1`, play `0x33` |
| `0x100` | Defaults: replace only the 17 local values with the defaults in the table, update help state, play `0x33` |

Defaults remain local until Confirm. Cancel therefore discards both ordinary
edits and a local Defaults action; reopening calls live `0x00880FB0` and
snapshots the manager again.

## Confirm/apply side effects

Live `0x008811A0` writes all 16 manager-backed local values through resident
`FUN_001F59F0(manager, key, value)` and writes Link Mode through live
`0x00882670`. Resident `FUN_001F59F0` checks the battle mode, updates the
packed bits/bytes above, then calls `FUN_001F6D30`; that final helper only
mirrors Strength. It does not perform a general fighter or resource reset.

The exact setter order is Command Display, Items, Health, Ultimate Jutsu,
Link Gauge, Chakra, Damage Display, Guide Ninja Sound, Link Mode, Status,
Strength, Attack, Guard, Move, Extra Hit, Substitution, and Linked Attack. The
dummy-status bridge runs only after that sequence. This ordering is material
to the post-write Strength comparison below; there is no staged manager-side
transaction or rollback layer.

After writing all values, the apply function calls the dummy-status bridge at
live `0x008813F0`. It selects the side opposite `manager+0x18`:

~~~text
active side 0 -> dummy side index 2 -> fighter manager+0xDE8
active side 1 -> dummy side index 1 -> fighter manager+0xDE4
~~~

For that side it:

1. stores `Status != Manual` in bit 1 of
   `manager + side*0x28 + 0x20`;
2. resolves the fighter from `manager + 0xDE0 + side*4`;
3. on Manual, clears the fighter `+0x60` behavior subfield in bits `5..8`;
4. on non-Manual, sets that subfield to `1` when it is zero or a comparison
   flag requests reinitialization, then calls live `0x00705D70` to rebuild the
   BTL AI-controller state and Strength profile.

The comparison flag is formed by comparing local Strength `+0x94` with getter
key `0xB` **after** the key has been written. In clean Practice mode the setter
succeeds, so this comparison is false even when Strength changed. Consequently
an already-nonzero fighter behavior subfield does not take the reset branch for
an ordinary Strength edit; the continuous AI update's profile-change path,
described below, handles the new level instead. There is not enough evidence to
assign a broader “status changed” meaning to this comparison.

Live `0x00705D70` is the entry whose real prologue is at preserved-export
`0x00705D30`. It first loops over both `0x1E0`-stride BTL AI work records,
restoring common action, countdown, sentinel, and 31-word work fields. It then
selects the side from the passed fighter's `+0x60` flags, loads that side's
Strength parameter profile, applies character-specific modifiers, and performs
the remaining per-side AI initialization. It does **not** reset fighter HP,
chakra, or Link Gauge.

## Dummy behavior routing

The help tables and BTL consumers agree on the high-level routing:

- Manual (`Status 0`) permits control by another controller.
- COM (`1`) routes the dummy through the general AI and enables Strength and
  Substitution controls.
- Stand, Jump, and Double-jump (`2..4`) route through scripted dummy behavior
  and enable Attack, Guard, and Move.
- Linked Attack and Extra Hit controls are available for every non-Manual
  status.

Confirmed BTL consumers include:

- preserved export `FUN_006F53D0` (live entry `0x006F5410`) tests
  `Status == COM` before taking COM-specific branches;
- preserved export `FUN_006FA550` (live `0x006FA590`) reads Status and Guard
  key `0xE` and uses Guard == Use in non-COM scripted decisions;
- preserved export `FUN_006FAA10` (live `0x006FAA50`) reads Status and Move
  key `0xF` and requires Move == Follow for the scripted movement path;
- preserved export `FUN_006FB090` (live `0x006FB0D0`) reads Status and Attack
  key `0xD`. For non-COM status, Attack `0` exits without an attack, `3` sets
  a projectile-related request, `4` sets a high-speed-move request, and
  `5/6` resolve and execute Ultimate-Jutsu/Jutsu action objects. Values `1/2`
  continue through the ordinary timing/attack-selection paths.

The setting-specific state lives in each `0x1E0`-byte BTL AI work record at
live `0x008D6590 + side*0x1E0`. Established fields used below are:

| Work offset | Live side-0 address | Established role |
| ---: | ---: | --- |
| `+0x10` | `0x008D65A0` | request/work flags |
| `+0x34` | `0x008D65C4` | current scripted controller code |
| `+0x90` | `0x008D6620` | request-active byte |
| `+0x94` | `0x008D6624` | request countdown |
| `+0xF4` | `0x008D6684` | linked-action timer |
| `+0x114` | `0x008D66A4` | scripted Status timer |
| `+0x118` | `0x008D66A8` | Attack retry/cooldown timer |
| `+0x14E` | `0x008D66DE` | cached linked-partner selector/type byte |
| `+0x150` | `0x008D66E0` | linked-action handshake halfword |
| `+0x160` | `0x008D66F0` | effective 40-short Strength profile |
| `+0x1B0` | `0x008D6740` | selected Ultimate action identifier |

Live `0x006F95B0` is a direct seven-way dispatcher for Attack key `0xD`.
When the `+0x118` timer is zero and its shared eligibility checks pass, it
initializes that timer to `60` and dispatches through the raw-value table:

| Attack | Concrete dispatcher effect |
| --- | --- |
| No (`0`) | emits no request; the `60`-tick retry timer remains |
| Single (`1`) | ORs request bit `0x00001000` into work `+0x10` |
| Combo (`2`) | selects an ordinary action through live `0x006F2B80` and passes its identifier to resident `FUN_0021D380` |
| Projectile (`3`) | ORs request bit `0x01000000` |
| High Speed Move (`4`) | ORs request bits `0x00030000` |
| Ultimate Jutsu (`5`) | validates work `+0x1B0`; on success ORs `0x08001000` and changes the retry timer to `240` |
| Jutsu (`6`) | searches action classes `0x000F0000`, then `0x00080000`, and passes a valid identifier to `FUN_0021D380` |

The failed-action branches for values `5/6` write work flags `8` and clear the
retry timer. Fighter action-state and action-object validation can still stop a
listed effect; the table is the setting-specific result after those checks,
not a promise that every dispatcher call produces an action.

Live `0x007024A0` is the complementary controller for scripted Status values.
It returns in Practice when Status is COM and otherwise integrates the three
scripted rows rather than treating them as independent toggles:

- Guard == Use builds three reaction predicates from range, action objects,
  and target state. A qualifying predicate can reset the current work, select
  controller code `0x12`, set `+0x90`, and write countdown `30` to `+0x94`;
- Move == Follow maintains controller code `5` through its target/distance
  checks. Under Status Stand, selecting Stay can cancel that code, while Follow
  permits it to remain or be re-entered;
- Status Jump (`3`) and Double-jump (`4`) converge on controller code `0x24`.
  The usual timer at `+0x114` is `90`; Double-jump has a shorter `18`-tick case
  when fighter action state `+0x18E` is zero and waits for specific substates
  when that action state is `2`;
- under Status Stand (`2`), any nonzero Attack value can select controller code
  `0x25` when the `+0x118` Attack timer is zero and the fighter-state gates
  accept it. The seven-way dispatcher above then determines the concrete
  attack family.

These are controller requests, not immediate fighter-state assignments. The
subsequent controller and action-object checks remain authoritative.

### Strength profiles

Strength is not a scalar damage multiplier. Resident `FUN_001F6EA0` is the
key-`0xB` getter used by BTL AI. The selected value indexes six `0x50`-byte
profiles at live `0x008C3230`; each profile contains 40 signed 16-bit AI
parameters. The effective per-side copy begins at BSS live `0x008D66F0 +
side*0x1E0`.

Live `0x00705D70` caches the selected level in `iGpffffce10`, copies the
profile for the passed fighter's side, and in Practice skips the rank/progress
scaling used by other modes. It then applies three character-descriptor
modifiers: descriptor bit `1`, `4`, or `8` multiplies profile field `16`, `8`,
or `24`, respectively, by `1.2` with integer truncation.

The main AI update at live `0x00704D40` also compares the getter against
`iGpffffce10` in Practice. On a change it updates the cache and copies the new
`0x50` bytes into the current side's BSS profile. That hot-reload copy does not
repeat the three character-specific `1.2` adjustments; this is a static path
difference, not a claim about a currently observed symptom.

The clean source profiles, split into groups of ten field indices, are:

~~~text
fields 00..09
Easiest:    50  0  0 240  0 20  0  0 60 10
Easy:       45  0  0 210  0 30 25  0 40 15
Normal:     30  0  0 180  0 35 35 25 40 30
Hard:       20 10 20 150 25 40 35 35 40 40
Very hard:  15 15 20 120 45 50 45 40 40 50
Ultimate:   15 20 30  90 60 60 55 50 50 60

fields 10..19
Easiest:    60  0  0  0 10  0  0 180 180  0
Easy:       60  0 30  0 30 35  0 150 150 30
Normal:     70 40 40  0 65 45  0 120 100 40
Hard:       70 50 60 45 60 55 50  90 100 50
Very hard:  70 60 70 55 70 60 60  80  80 50
Ultimate:   80 70 70 60 80 70 70  70  80 70

fields 20..29
Easiest:     0  0  0 50 0  0  0  0 20 40
Easy:        0  0  0 15 0  0  0  0 35 55
Normal:      0  0  0 50 0 35  0 30 40 60
Hard:       10  0  0 50 0 35 40 40 40 60
Very hard:  25 30 50 50 0 40 45 45 45 65
Ultimate:   40 50 70 50 0 50 45 45 50 70

fields 30..39
Easiest:    0 380 60 240 40 8 0 1 200 30
Easy:       0 360 45 180 35 6 0 2 170 25
Normal:     0 300 60 150 35 6 0 3 150 20
Hard:       3 300 50 120 35 5 0 3 120 15
Very hard:  2 240 40  90 30 5 0 3 110 10
Ultimate:   1 180 35  75 20 4 0 3  85  5
~~~

Not all 40 field meanings are decoded. Concrete consumers include profile
field `12` in the normal Extra-Hit cooldown as `100 - field[12]`; field `11`
as a `0..100` response threshold in the other Extra-Hit flag family; field
`39` as both the base and inclusive PRNG bound for that family's retry delay;
field `38` as both the base and inclusive PRNG bound for a linked-action retry
timer; and field `21` as that path's initial `0..100` request threshold.
Resident `FUN_00180210(N)` returns a pseudorandom integer modulo `N+1`.

### Linked Attack and Extra Hit

Linked Attack key `0x12` is consumed at multiple gates:

- live `0x006FE720` returns immediately in Practice when the value is `0`
  (Don't use). When enabled and its current-action gate is clear, it writes
  `StrengthProfile[38] + RNG(0..StrengthProfile[38])` to the per-side timer at
  live `0x008D6684 + side*0x1E0`. After the partner/action tests pass it uses
  Strength-profile field `21` as the initial request threshold. With an
  available partner whose type is not `4`, fighter action state `5` replaces
  it with `field[21] * trunc(1.5 * field[21])`; other accepting branches retain
  the original field. It then requires `RNG(0..100) < threshold` before setting
  controller code `0x26`;
- live `0x006FF410` likewise blocks value `0`. Value `1` (Normal) uses the
  dummy Status, Link Mode, and partner availability to initialize the same
  per-side timer. COM Status writes `30 + RNG(0..60)` and retains a separate
  threshold from Strength-profile field `21`; non-COM Normal writes `30` when
  Link Mode is Manual and no partner is available, otherwise `90`, with
  threshold `100`. Value `2`
  (`乱発`, frequent/random) writes `5` with threshold `100`. A final
  `RNG(0..100) < threshold` sets bit `0x00200000` in the side work flags.
  Another no-current-request branch initializes the timer to
  `90 + RNG(0..30)` under its Link Mode/partner conditions.

The clean field-`21` values from Easiest through Ultimate Strength are
`0, 0, 0, 0, 30, 50`. Because `FUN_00180210(100)` is inclusive and the test
is strict `<`, an unmodified field gives acceptance counts of `0/101`,
`30/101`, or `50/101`, not `0%`, `30%`, and `50%` under a 100-outcome model.
Threshold `100` accepts `100/101` draws. The boosted formula produces `1350`
or `3750` for the two nonzero clean fields and therefore accepts every
`0..100` draw; a zero field remains zero.

After live `0x006FE720` selects code `0x26`, Link Mode controls the handshake
at work `+0x150`. Auto writes `2`. Manual writes `1` when no partner object is
available, writes `2` when the available partner's byte `+0xE6` is `1`, and
leaves other partner states unchanged. Handshake value `1` shortens the same
linked timer to `5`. Work byte `+0x14E` caches the partner selector/type used
by these tests.

This establishes why rows 4 and 15 interact without conflating them: Link Mode
participates in scheduling and the partner handshake for an enabled linked
attack, while row 15 can prevent that request family or select its
short-countdown policy. Some partner-state and controller-code semantics remain
unnamed, but the setting-selected timers, thresholds, draws, and written fields
are exact.

Extra Hit key `0x10` is consumed by live `0x006FF650`. For hit-response flags
`fighter+0xB00 & 0xFF00` equal to `0x0400`/`0x1000`, Always return (`1`)
clears the normal cooldown and immediately selects response code `0x0D`; for
flag `0x0100` it clears the corresponding cooldown and selects code `0x13`.
It then commits that response and marks its per-side request active. Normal
(`0`) retains the ordinary cooldown/probability path, including the
`100 - StrengthProfile[12]` counter.

### Item amount

Resident `FUN_003AEAF0` is a concrete Items key-`7` consumer in the item-spawn
path:

- None (`0`) rejects the spawn request entirely;
- Less (`1`) retains the base spawn but sets the extra-spawn count to zero;
- Normal (`2`) retains the caller's extra-spawn count;
- More (`3`) changes an extra count below one to `2`, otherwise doubles it,
  and adds another base-style spawn when a `0..100` inclusive random draw is
  below `80`.

Position randomization and the caller-provided spawn kind still affect the
result; these setting branches do not themselves choose the item identity.

### Substitution Jutsu

The non-menu Substitution consumer survives in raw BTL bytes even though the
preserved Ghidra export marks most of export `0x006FBD84..0x006FBE8F` as
undefined. At live `0x006FBDC4..0x006FBE88`, a branch in the per-side behavior
dispatcher first verifies Practice mode (`manager+0x0C == 3`) and calls the
resident setting getter for key `0x11` at live call site `0x006FBE18`.

The two setting outcomes are concrete:

- Don't use (`1`) writes dispatcher code `0x12` to live
  `0x008D65C4 + side*0x1E0` and exits this decision path;
- Normal (`0`) calls resident `FUN_00229B70(current_fighter, -2)`, which writes
  signed halfword `current_fighter+0x95C = -2`, then exits the same path.

Resident `FUN_00228320` advances a negative `fighter+0x95C` toward zero on
successive updates. Resident `FUN_00229130`, the relevant substitution-action
eligibility routine, tests this field: a negative value can take its early
eligibility path under the routine's fighter/action conditions, while a
positive value above `15` blocks its later attempt. This establishes the
setting's control mechanism without assigning a complete name to every
dispatcher code or reconstructing general substitution mechanics.

### Presentation options and Ultimate gate

The three presentation settings are consumed outside the Practice menu rather
than by its draw routine:

- live `0x006BB590` begins the Damage Display renderer by reading key `9`.
  OFF returns before building/drawing the damage object. ON still requires the
  object's `+0x4C` bit 0 and its side short `+0x0C` to match
  `manager+0x18`;
- live `0x00728B00` updates the Command Display HUD and explicitly calls its
  clear/hide helper at live `0x00728A80` when key `1` is OFF. The companion
  path at live `0x00728BF0` skips the command-display drawing work when OFF,
  and live `0x00729130` forces that HUD's internal byte `+3` into its closed
  state when OFF;
- live `0x00728EA0` and live `0x00728F80` both gate the Guide Ninja Sound
  subsystem on key `0xA`. OFF prevents its event-state trigger and scheduled
  countdown/selection path; ON does not force a sound immediately because the
  subsystem's own event and audio-busy tests still apply.

The direct non-menu BTL getter call for Ultimate Jutsu key `5` is at live
`0x006F8BD0`, inside the general AI path entered at live `0x006F8810`. Value
`0` (No Use) skips the optional ultimate-action selection branch. Any positive
value permits that branch to continue through its own chance, target/action,
and distance tests. This AI call site tests only zero versus positive.

Resident setup exposes the same first-stage gate. Setter `FUN_001F59F0` case
`5` stores the raw byte and refreshes `manager + side*0x28 + 0x3C` for both
sides. That word is a per-side cache of the raw setting: `FUN_001F4F70` and the
setter both fill it with the result of `FUN_00372C70`, which in turn returns
key `5` through `FUN_001F6E10`. Fighter setup `FUN_00216460` reduces the
current setting to `fighter+0x168 = (value == 0)`. Ultimate-eligibility routine
`FUN_00225B60` and related resident action predicates reject while that byte is
nonzero. The raw value is also copied to the active battle-rule record at
`+0x105`.

The positive values are distinguished later, in the ultimate skill-play
creation path rather than in the AI decision above:

1. BTL live `0x006EE560` (preserved prologue `0x006EE520`) returns
   `battle_rule+0x105`, or `-1` when the battle-rule object is unavailable.
2. Its only raw `jal` caller is live `0x0076A0CC`, inside the function whose
   live entry is `0x00769790`. A `-1` result falls back to the current side's
   cached manager value at `manager + zero_based_side*0x28 + 0x64`, equivalent
   to field `+0x3C` in the corresponding one-based side record. The selected
   raw mode is passed as the fifth argument to resident `FUN_0035CF00`.
3. `FUN_0035CF00` constructs the `SP_Skill_Play` object and, outside manager
   mode `6`, forwards the mode through `FUN_0036C120` to `FUN_0036B6D0`.
   The latter is the concrete mode dispatcher:

| Raw value | Menu meaning | Resident dispatch |
| ---: | --- | --- |
| `0` | No Use | creates no mode-controller object |
| `1` | Random | selects one of modes `2..5`, then uses that mode's branch |
| `2` | Command | allocates `0x3E8` bytes; initializes through `FUN_003619A0` / `FUN_00361BB0` |
| `3` | Timing | allocates `0xFE4` bytes; initializes through `FUN_00367510` / `FUN_00367890` |
| `4` | Turn | allocates `0x108` bytes; initializes through `FUN_00364C80` |
| `5` | Combo | allocates `0x100` bytes and its associated helper objects |

Random copies four resident short pairs from `0x005ACD70`:
`(3,40), (2,55), (4,50), (5,100)`. It tests them in that order with a fresh
`FUN_00180210(100)` draw for each pair and selects the first whose draw is at
most the paired threshold. Thus these are sequential tests, not weights for a
single draw. With the helper's inclusive `0..100` range, the resulting exact
probabilities are `418241/1030301` for Timing (`3`), `339360/1030301` for
Command (`2`), `137700/1030301` for Turn (`4`), and `135000/1030301` for
Combo (`5`). The final `<= 100` test always accepts, so the encoded fallback
which chooses `2` or `3` is unreachable under this helper contract. The
dispatcher also contains a mode-`6` class, but the clean Practice row count and
clamp only allow values `0..5`; mode `6` is not reachable through this menu.

This establishes both layers without conflating them: the AI-selection gate
only asks whether ultimate use is enabled, while the later skill-play creation
chooses the Command/Timing/Turn/Combo interaction controller.

## Defaults, restart, and resource semantics

There are three related operations which must not be conflated.

### Manager defaults

Resident `FUN_001E7A80` initializes one 12-byte settings block. Manager
construction (`FUN_001F4200` / `FUN_001F5910`) applies it to
`manager+0x9F4`, `+0xA00`, and `+0xA0C`. The visible Practice defaults match
the local Defaults row values above.

The Practice Settings rework hooks the initializer tail at live
`0x001E7B7C`, replacing the native `sb a1,11(a0); jr ra` pair with a tail jump
to an owned leaf. The leaf reproduces byte `11 = 1`, then optionally overrides
Health byte `1`, Commands bit `0`, and Guide Ninja Sound bit `5` in byte `0`,
plus Linked Attack byte `11`. The resident schema uses `0xFF` per field to
preserve the native value; configured enum values are stored directly as
`0..2`.

Simple Display is independent of the Practice Settings rework. Its native
initializer write is the `or v1,v1,a2` at live `0x001E7AAC` after masking byte
`0` with `0xFFFFFFFD`, confirming that its native mask is `0x02`.
`features.battle.simple_display` owns that guarded instruction directly:
`"on"` retains it and `"off"` replaces it with a no-op.

Resident `FUN_001F5960` is used by the Practice-controller startup/restart
path. It resets `+0x9F4` and `+0xA00`, then in modes `2/3` re-applies Strength
key `0xB` from mirror byte `manager+0xA13`. This is a manager-level default
operation; it is separate from the pause menu's local Defaults action.

### Discrete Practice-controller reset

Resident `FUN_001EC960` dispatches the outer Practice controller. In state `2`,
`FUN_001ED000` waits for the preceding asynchronous transition, clears several
controller globals, calls `FUN_001F5960`, and advances to state `3`. State `3`
calls `FUN_001ED110`, which:

- seeds the resident per-side snapshot words to normalized HP `1.0` and chakra
  `15.0` for sides `1` and `2`;
- calls encoded BTL target/live `0x0070F1E0`;
- clears its own transition globals and advances to state `4`.

Live `0x0070F1E0` only clears six two-byte BTL records at live
`0x008D6A60` (two sides by three entries). These are per-side item-slot cache
records, not HP/chakra/gauge state. Each two-byte entry is an item identifier
followed by a one-byte amount. Live `0x007109F0` clears and rebuilds one side's
three-entry cache from an inventory object, omitting identifiers for which
resident `FUN_00376480` reports the special category `6`; resident
`FUN_00375FD0` invokes that builder for caller-selected side masks.

The restore half is also established. Item state is mask bit `0x20` in the
resident snapshot API:

- `FUN_001ECC00(..., side, mask)` captures HP for bit `1`, chakra for bit `2`,
  and, for bit `0x20`, calls `FUN_00375FD0` to build the selected side's item
  cache. A side argument of `1` or `2` first seeds both resource snapshots and
  calls live `0x0070F1E0`, so stale caches for both sides are cleared before
  the requested side is captured;
- `FUN_001ECDE0(..., side, mask)` restores the same resources. For bit `0x20`
  it calls resident `FUN_00376050`, which dispatches live `0x00710B00` for the
  requested side mask;
- live `0x00710B00` clears the inventory object's three non-category-6 slots,
  iterates the three cached `(identifier, amount)` pairs, normalizes IDs in
  `0x51..0x73` through resident `FUN_00373980`, and re-adds each nonempty pair
  through live `0x00710040`. Category-6 inventory entries are deliberately
  left intact, matching their exclusion from capture.

The complete mask behavior in these two resident functions is:

| Mask bit | Capture / restore target |
| ---: | --- |
| `0x01` | fighter HP `+0x6C` and per-side snapshot word |
| `0x02` | fighter chakra `+0x70` and per-side snapshot word |
| `0x10` | global round-timer remaining/elapsed words at `0x006B28D4` / `0x006B28D8`, copied to/from `0x006B28DC` / `0x006B28E0` |
| `0x20` | the three-slot non-category-6 item cache |

No other bit is consumed by `FUN_001ECC00` or `FUN_001ECDE0`. In particular,
neither function reads or writes fighter Link Gauge `+0x74`; there is no
discrete Link-Gauge snapshot bit in this API. Timer bit `0x10` is global, so a
side loop merely records that it was requested and performs one two-word copy
after the loop.

Resident battle reconstruction `FUN_001EF330` calls `FUN_001ECDE0` for both
sides when its saved-battle condition `iGpffffcc88 == 2` holds. Both masks
used there include bit `0x20` (the `...FFEF` variant excludes bit `0x10`, not
item state). The cache is therefore a real restart/reconstruction snapshot,
not an unused scratch buffer. The outer Practice initialization at
`FUN_001ED110` explicitly forgets it; subsequent snapshot capture repopulates
it when the controlling transition requests item state.

Resident `FUN_001ECC00` and `FUN_001ECDE0` separately capture and restore live
fighter HP `+0x6C` and chakra `+0x70` under caller-supplied bit masks. This
proves that the outer controller owns a discrete resource-snapshot path in
addition to the continuously enforced Practice policies, while Link Gauge is
absent from that path.

### Continuous fighter policy

During an eligible fighter update in mode `3`, resident code performs these
checks and effects:

1. When fighter action-state short `+0x18E` is not `8`, `5`, or `6`,
   fighter `+0xB00 == 0`, and
   `(*(uint *)(0x006073FC + 0x194) & 0x1F) == 0`, it calls
   `FUN_002165C0(fighter)`.
2. `FUN_002165C0` reads Health key `4`:
   - Almost adds `0.1 - current_HP`;
   - Half adds `0.5 - current_HP`;
   - Normal adds `1.0` and the helper clamps at `1.0`.
   Subject to the health helper's own fighter-state flags, this makes the
   selected target persistent rather than a one-time menu reset.
3. Under the same eligibility gate, if the active/pending chakra-expenditure
   amount at fighter `+0x7C` is zero and Chakra key `2` is Unlimited, it calls
   `FUN_002254A0(15.0, fighter, 0, 0, 0)`. That helper adds to actual chakra
   at fighter `+0x70` and caps it at `15.0`.
4. Independently of that narrower action-state gate, Link Gauge key `3` ==
   Unlimited increments fighter `+0x74` by `1.0` and clamps it to `[0,1]`
   during the Practice fighter update.

Consequences:

- Confirm does not directly write fighter HP, chakra, or Link Gauge; it writes
  settings, and the relevant fighter update later consumes them.
- Health Normal actively refills to full on eligible updates. Chakra Normal
  does not refill, and Link Gauge Normal does not increment.
- Chakra Unlimited is not implemented as an unconditional per-frame assignment
  to `15.0`; it has the additional `fighter+0x7C == 0` and helper-state gates.
- `FUN_00225F50` sets `fighter+0x7C` to the chakra cost selected for a
  technique while subtracting it from actual chakra, and `FUN_002260D0`
  reconciles/refunds that amount and clears the field when the transaction is
  abandoned or completed. The Unlimited gate therefore avoids injecting
  chakra during an active cost transaction.
- No static evidence shows the menu's Confirm or local Defaults action directly
  resetting items, Link Gauge, or the item-slot cache at `0x008D6A60`.

## Rendering/control split and flicker boundary

### Resource lifetime

Live `0x008809E0` is the child's zero-initializer and live `0x00880A20` is its
destructor. Live `0x00880BE0` performs the one-time construction:

- it stores the loaded archive/resource handle at `+0x04`;
- it allocates the four `0x40`-byte render objects at `+0x08..+0x14` and
  initializes them with resource IDs `0xE0`, `0xE1`, `0xE8`, and `0xE9`;
- live `0x00880DB0` creates the prompt/panel and sprite objects at
  `+0x18..+0x30`;
- live `0x00880E90` creates/configures the help object at `+0x34`;
- it finishes by calling live `0x00880F30`, the same state reset used on later
  opens.

The main parent passes constructor variant `1`; the smaller standalone wrapper
passes `0`. In draw, only nonzero `+0x48` emits the full-screen backdrop whose
opacity is derived from child alpha `+0x54`.

Opening Practice from parent state `2` calls only live `0x00880F30`. That reset
does not replace or free any pointer at `+0x04..+0x34`; it clears presentation,
input, and page state, re-snapshots manager values, and resets the help
animation. The destructor is called from parent/wrapper teardown sites, not
from the ordinary state `2 <-> 5` open/close transaction. Therefore a future
flicker trace should distinguish pointer churn from content/draw gating rather
than assuming resources are reloaded every time the child opens.

The generic parent makes update and rendering distinct:

- live `0x006C0F60` advances the parent and child controllers;
- live `0x006C1120` renders the parent and, only in parent state `5`, calls the
  Practice child draw at live `0x00882250`;
- the parent renderer returns without drawing anything while parent state is
  `3`.

The Practice draw routine also has child-local gates:

- while child alpha `+0x54 < 0xC0`, it skips the 17 option rows;
- once alpha reaches `0xC0`, it advances post-fade delay `+0x56` to `3`;
- only after that delay does it loop through all 17 rows, with the native
  vertical gap before row `9`;
- it calls live `0x008814F0` for enabled/grey state and live
  `0x00881E50` for selection/arrows.

The renderer is therefore not completely read-only: it advances presentation
delay `+0x56`. It does not write the manager settings pack or apply local
values. Input ownership remains in live `0x00881660` and phase ownership in
live `0x00881AB0`.

### Compact-schema presentation alignment

User-supplied, timestamp-matched NUN5 and NA228 savestate slots `1..3` from
2026-08-27 preserve two distinct presentation faults in the compact Practice
Settings implementation. Their extracted screenshots and source-state hashes
are retained under
`work/Battle mechanics/inputs/practice_settings_nun5_na228_ss1-3/`.

The NA228 controller is at `0x00EB1120` in all three captured EE-memory
snapshots. The preserved states contain:

| Slot | Selected compact row | Scroll `+0x44` | Upper/lower starts |
| --- | ---: | ---: | ---: |
| `1` | `0` (Health) | `0.0` | `0 / 0` |
| `2` | `13` (Substitution Jutsu) | `-242.0` | `0 / 0` |
| `3` | `8` (Status) | `-242.0` | `0 / 0` |

The matching NUN5 controller is at `0x00DE4FA0`; slot `3` preserves native
Status selection `9`, scroll `-270.0`, and starts `0 / 0`. Static disassembly
explains the numeric difference: the native window update uses a `28.0` row
step and computes the opponent target as `-18 - 28*9 - 28*lower_start`.
The compact target generalizes that expression to
`-18 - 28*player_count - 28*lower_start`. A separate `30.0` step has no native
basis and is incorrect for any nonzero window start.

The SS1 up-arrow fault is a control-flow error, not a bad window value. Native
live `0x00882078` skips the up-arrow draw body at `0x00882080` when its flag is
zero. The first compact bridge returned directly to `0x00882080`, bypassing
that branch and drawing the arrow unconditionally even though the captured
upper start is zero. The corrected bridge returns to `0x008820FC` when no rows
exist above the current window and to `0x00882080` only when the flag is set.

SS2/SS3 preserve a second, independent split: the row text loop inserts the
Opponent Settings heading at the compact player count, but the native
`ANM_setting01` row backing retains its fixed nine-player/eight-opponent row
topology. The first candidate added `28 * (9 - player_count)` to the backing
translation. Its section phase was correct, but the first unused backing row
still left a thin edge after the final compact row in both sections.

A later candidate incorrectly divided that delta by the backing transform's
`0.96` multiplier and used `29.166666` per omitted row. Current user-supplied
states `SLOP-NA228 (0C8A0D9B).01.p2s` and `.02.p2s`, captured on 2026-08-28,
reject that compensation. Slot 1 ends the seven-row player section at Guide
Ninja Sound; slot 2 ends the six-row opponent section at Substitution Jutsu.
Both retain the unused-row edge, while slot 2 and the supplied old/current
comparison show that the compensated backing is `2.24` game units too far from
the text. The correct section delta remains the native `28.0` units per omitted
player row; the transform applies the same raster phase used by the untouched
row renderer.

The same states expose the backing object's exact draw inventory. Object
`controller+0x2C` points at an 18-record animation whose record list is at
`object+0xFC`. Resident `FUN_001BB790` iterates the resource count and draws a
record only when byte `record+0x0A` has bit `0x04` set. Record `0` is the
Opponent Settings heading. Player rows use record `1` followed by records
`10..17`; opponent rows use records `2..9`. Their settled transforms differ by
the native row pitch. In the supplied seven/six-row schema, player records
`16..17` and opponent records `8..9` are therefore unused; their first visible
edges are the reported terminal lines.

The selection-dependent global backing correction was invalid: selection
changes immediately while controller scroll `+0x44` approaches its new target
by `20.0` per update. Applying the complete compact-section correction as soon
as selection crosses the boundary therefore jumps every backing while text,
values, and cursor continue along the native eased path.

Slot 2 also confirms the record-to-transform link needed to compact the
animation locally. Each record's word at `+0x00` points to its render object.
That object stores world Y at `+0x38` and authored local Y at `+0x78`; the
native object draw composes the latter with the backing object's global
translation to produce the former. In this state, player records `15` and `17`
have local Y values `-66.612` and `-119.454`, while the heading and first
opponent records have `-165.931` and `-192.744`. Anchoring the heading and
opponent records to record `15` while preserving their native deltas from
record `17` therefore removes exactly the two omitted player slots without a
global phase correction.

The subsequent draw-time candidate was also rejected by user runtime evidence.
The supplied current slots `1..2`, retained with provenance under
`work/Battle mechanics/inputs/practice_settings_current_ss1-2_20260828/`, show
that unused terminal lines were suppressed but the compact backing geometry did
not follow the text. Static control flow explains the split. Live
`0x00881AE0` advances `controller+0x2C` through resident `0x001BB210`, and live
`0x00881AEC` immediately composes its hierarchy through resident `0x001BB6F0`.
The rejected hook changed record-local Y only later, at the draw-time scroll
load at live `0x00882368`. Resident `0x001BB790` reads the record draw bits
directly, so suppression worked, but it drew the already-composed world
transforms. Changing authored local Y at that point could not move them.

The replacement source candidate removes that draw-time hook and leaves the
native `lwc1 controller+0x44` / `neg.s` scroll pair intact. Its layout wrapper
replaces only the compose call at live `0x00881AEC`: after native animation
advance, it anchors the heading and opponent records to the compact section's
actual last player row, applies active record bits, and then calls the displaced
native hierarchy composer. The draw call at live `0x008823D0` remains native
except for a wrapper that draws one additional copy of the native final player
backing when all ten possible player rows are present; the animation owns only
nine player backings. Native controller slots remain authoritative for all 17
native values. The compact list stores only resolved label/value-table pointers,
and the custom Substitution value alone has staged state for Confirm/Cancel.
Runtime confirmation of this replacement candidate is pending.

The `+0x56` delay is draw-call-counted, not update-counted. Reset sets it to
zero; once alpha is full, each invocation of live `0x00882250` increments it
until `3` and returns without drawing rows. If rendering is skipped, the delay
does not advance; multiple draw invocations advance it correspondingly. This
is an intentional three-draw row reveal gate and a concrete counter to log in
any frame-by-frame diagnosis.

Raw `jal` enumeration finds exactly two direct BTL callers of each Practice
child entry:

| Caller family | Update call site -> target | Draw call site -> target |
| --- | --- | --- |
| main generic parent | `0x006C1014 -> 0x00881AB0` | `0x006C1250 -> 0x00882250` |
| standalone wrapper | `0x00875B2C -> 0x00881AB0` | `0x00875B5C -> 0x00882250` |

The main owner calls its parent update at live `0x00714CC4`; its draw wrapper
calls the parent renderer at live `0x00715D08`. This establishes the complete
static call split but does not establish that the main and standalone owners
are simultaneously active. A runtime breakpoint should retain the caller
address rather than treating every child-draw hit as the same source.

Within the standalone family, host factory live `0x0087BB10` replaces the
single module pointer at host `+0x38` before the wrapper begins updating or
drawing. Logging that host pointer and module slot alongside the main battle UI
owner's `owner+0xA8` distinguishes cross-owner overlap from accidental
duplication inside one owner.

Static analysis exposes the following useful runtime watchpoints for a future
flicker trace:

- UI-owner state and `owner+0xA8`;
- standalone host state, `host+0x38`, and update/draw entry counts at
  `0x0087CB20` / `0x0087D460`;
- parent `+0x00`, `+0x3C`, `+0x48`, and update/draw entry counts at
  `0x006C0F60` / `0x006C1120`;
- child `+0x38`, `+0x54`, `+0x56`, selection `+0x3C`, resource pointers
  `+0x04..+0x34`, and update/draw entry counts at
  `0x00881AB0` / `0x00882250`.

No runtime trace currently establishes which, if any, of those gates or
pointers oscillates during the reported flicker. A cause must not be assigned
until such a trace identifies the first divergent state.

Useful negative results:

- live `0x006C0CC0` is a VS/Practice prompt renderer, not the Practice
  Settings controller;
- live `0x00881E50` is a draw helper, not an input owner;
- the Practice draw loop does not reset or apply manager option values;
- misleading preserved-export symbols at encoded live call targets are an
  artifact of the omitted-header baseline, not evidence of a second function.

## Address index

### BTL code

| Role | Live entry/target | Complete file | Preserved-export prologue |
| --- | ---: | ---: | ---: |
| generic parent zero/init | `0x006BFD30` | `0x0000BE30` | `0x006BFCF0` |
| generic parent constructor | `0x006BFFF0` | `0x0000C0F0` | `0x006BFFB0` |
| generic parent reset | `0x006C0380` | `0x0000C480` | `0x006C0340` |
| generic outer-selector update | `0x006BE810` | `0x0000A910` | `0x006BE7D0` |
| generic parent close-transition completion | `0x006C06F0` | `0x0000C7F0` | `0x006C06B0` |
| generic parent selector/open update | `0x006C07C0` | `0x0000C8C0` | `0x006C0780` |
| generic parent update | `0x006C0F60` | `0x0000D060` | `0x006C0F20` |
| generic parent renderer | `0x006C1120` | `0x0000D220` | `0x006C10E0` |
| Practice row-offset easing helper | `0x006C12A0` | `0x0000D3A0` | `0x006C1260` |
| Damage Display renderer/settings gate | `0x006BB590` | `0x00007690` | `0x006BB550` |
| Ultimate raw battle-rule-mode accessor | `0x006EE560` | `0x0003A660` | `0x006EE520` |
| Ultimate Jutsu setting getter call site (inside general AI) | `0x006F8BD0` | `0x00044CD0` | `0x006F8B90` |
| seven-way scripted Attack dispatcher | `0x006F95B0` | `0x000456B0` | `0x006F9570` |
| scripted Guard consumer | `0x006FA590` | `0x00046690` | `0x006FA550` |
| scripted Move consumer | `0x006FAA50` | `0x00046B50` | `0x006FAA10` |
| broad scripted Attack decision path | `0x006FB0D0` | `0x000471D0` | `0x006FB090` |
| linked-action enable/profile gate | `0x006FE720` | `0x0004A820` | `0x006FE6E0` |
| linked-action frequency/countdown policy | `0x006FF410` | `0x0004B510` | `0x006FF3D0` |
| Extra Hit response policy | `0x006FF650` | `0x0004B750` | `0x006FF610` |
| Substitution setting getter call site (inside behavior dispatcher) | `0x006FBE18` | `0x00047F18` | `0x006FBDD8` (inside Ghidra-undefined range) |
| Practice Strength-profile hot reload in main AI update | `0x00704D40` | `0x00050E40` | `0x00704D00` |
| clear six two-byte BTL records | `0x0070F1E0` | `0x0005B2E0` | `0x0070F1A0` |
| reset common AI work and initialize selected-side Strength profile | `0x00705D70` | `0x00051E70` | `0x00705D30` |
| central scripted Status/Guard/Move controller | `0x007024A0` | `0x0004E5A0` | `0x00702460` |
| build one side's three-slot item cache | `0x007109F0` | `0x0005CAF0` | `0x007109B0` |
| restore one side's three-slot item cache into inventory | `0x00710B00` | `0x0005CC00` | `0x00710AC0` |
| battle UI owner reinitializer | `0x00714700` | `0x00060800` | `0x007146C0` |
| battle UI owner parent-update wrapper | `0x00714CB0` | `0x00060DB0` | `0x00714C70` |
| battle UI owner parent-draw wrapper | `0x00715CC0` | `0x00061DC0` | `0x00715C80` |
| ultimate skill-play creation function containing the raw-mode consumer | `0x00769790` | `0x000B5890` | `0x00769750` |
| Ultimate raw-mode consumer call site | `0x0076A0CC` | `0x000B61CC` | `0x0076A08C` |
| Command Display update/settings gate | `0x00728B00` | `0x00074C00` | `0x00728AC0` |
| Command Display draw/settings gate | `0x00728BF0` | `0x00074CF0` | `0x00728BB0` |
| Guide Ninja Sound event/settings gate | `0x00728EA0` | `0x00074FA0` | `0x00728E60` |
| Guide Ninja Sound scheduler/settings gate | `0x00728F80` | `0x00075080` | `0x00728F40` |
| standalone Practice update wrapper | `0x00875B20` | `0x001C1C20` | `0x00875AE0` |
| standalone Practice draw wrapper | `0x00875B50` | `0x001C1C50` | `0x00875B10` |
| standalone Practice wrapper construction callback | `0x00875AB0` | `0x001C1BB0` | `0x00875A70` |
| standalone host module-list builder | `0x0087B3B0` | `0x001C74B0` | `0x0087B370` |
| screen-selector module factory (Practice is case `5`) | `0x0087BB10` | `0x001C7C10` | `0x0087BAD0` |
| standalone host module update | `0x0087CB20` | `0x001C8C20` | `0x0087CAE0` |
| standalone host draw | `0x0087D460` | `0x001C9560` | `0x0087D420` |
| standalone wrapper child-destructor call site | `0x0087E538` | `0x001CA638` | `0x0087E4F8` |
| Practice child zero-initializer | `0x008809E0` | `0x001CCAE0` | `0x008809A0` |
| Practice child destructor | `0x00880A20` | `0x001CCB20` | `0x008809E0` |
| Practice child resource constructor | `0x00880BE0` | `0x001CCCE0` | `0x00880BA0` |
| build Practice prompt/panel/sprite objects | `0x00880DB0` | `0x001CCEB0` | `0x00880D70` |
| build Practice help object | `0x00880E90` | `0x001CCF90` | `0x00880E50` |
| reset/snapshot child | `0x00880F30` | `0x001CD030` | `0x00880EF0` |
| snapshot manager values | `0x00880FB0` | `0x001CD0B0` | `0x00880F70` |
| apply local values | `0x008811A0` | `0x001CD2A0` | `0x00881160` |
| local Defaults | `0x00881390` | `0x001CD490` | `0x00881350` |
| dummy-status bridge | `0x008813F0` | `0x001CD4F0` | `0x008813B0` |
| row-enabled predicate | `0x008814F0` | `0x001CD5F0` | `0x008814B0` |
| input/action handler | `0x00881660` | `0x001CD760` | `0x00881620` |
| row navigation | `0x00881910` | `0x001CDA10` | `0x008818D0` |
| value change | `0x00881990` | `0x001CDA90` | `0x00881950` |
| Practice child update | `0x00881AB0` | `0x001CDBB0` | `0x00881A70` |
| Practice row draw helper | `0x00881E50` | `0x001CDF50` | `0x00881E10` |
| Practice child draw | `0x00882250` | `0x001CE350` | `0x00882210` |
| Link Mode getter | `0x00882630` | `0x001CE730` | `0x008825F0` |
| Link Mode setter | `0x00882670` | `0x001CE770` | `0x00882630` |
| Link Mode backing-object rebuild | `0x00885210` | `0x001D1310` | `0x008851D0` |
| Link Mode backing-object teardown | `0x00885290` | `0x001D1390` | `0x00885250` |
| Link Mode backing-object constructor | `0x00886CB0` | `0x001D2DB0` | `0x00886C70` |

The last two entries demonstrate the symbol trap directly: the preserved
export's `FUN_00882630` label is at the setter prologue, while a raw call to
encoded target `0x00882630` reaches the getter in live memory.

### BTL data

| Role | Live address | Complete file | Preserved-export byte location |
| --- | ---: | ---: | ---: |
| 17 label pointers | `0x008BE6C0` | `0x0020A7C0` | `0x008BE680` |
| normal help pointers | `0x008BEF70` | `0x0020B070` | `0x008BEF30` |
| status-specific help pointers | `0x008BF350` | `0x0020B450` | `0x008BF310` |
| 17 value-array pointers | `0x008BF380` | `0x0020B480` | `0x008BF340` |
| six Strength source profiles (`6 x 0x50`) | `0x008C3230` | `0x0020F330` | `0x008C31F0` |
| 15-entry screen-selector module jump table | `0x008D1690` | `0x0021D790` | `0x008D1650` |
| 17 value counts | `0x008D18C0` | `0x0021D9C0` | `0x008D1880` |
| per-side AI work record | `0x008D6590 + side*0x1E0` | BSS; nominal `0x00222690` is past EOF | `0x008D6550 + side*0x1E0` (nominal baseline) |
| per-side effective Strength profile | `0x008D66F0 + side*0x1E0` | BSS; nominal `0x002227F0` is past EOF | `0x008D66B0 + side*0x1E0` (nominal baseline; Ghidra also creates same-number raw-reference symbols) |
| two three-slot item cache records | `0x008D6A60` | BSS; nominal `0x00222B60` is past EOF | `0x008D6A20` (BSS) |

Absolute table pointers embedded in BTL point to the live addresses in the
second column. BSS rows intentionally have no complete-file byte location.

## Confidence and open questions

High confidence:

- address mapping and every live/file/export coordinate in the index;
- ownership, allocations, parent/child state dispatch, input masks, and
  Confirm/Cancel/Defaults transaction;
- all 17 local offsets, manager keys/storage, counts, defaults, and
  availability conditions;
- dummy-status apply side effects, Strength-profile selection/hot reload, and
  the concrete Items/Extra-Hit/Substitution setting branches;
- discrete resident reset/snapshot calls and continuous HP/chakra/Link Gauge
  consumers;
- the role of fighter `+0x7C` and the complete capture/clear/restore lifecycle
  of the two three-slot item-cache records.

Medium confidence:

- descriptive names for child presentation fields `+0x40..+0x5C`;
- the high-level grouping of complex Attack/Guard/Move AI branches, whose key
  gates are clear but whose complete timing behavior is not reconstructed;
- the precise semantics of every field in the 40-short Strength profile and
  every linked-action work/countdown field;
- the manager-owned slot `0x6A` as the sixth/Ultimate-tier gate; its two
  consumers are exact, but its producer/unlock condition is not known.

Open:

- the current flicker's runtime cause;
- the engine-level names and later transitions for several linked-partner work
  fields and controller codes;
- the producer for difficulty-tier slot `0x6A`.
