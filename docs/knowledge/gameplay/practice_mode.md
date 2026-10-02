# Practice-mode architecture

This document owns the established architecture of the Battle and Practice
Settings children in retail NA2 (`SLPS-25837`), Practice starting-HP selection,
and the battle-side policies that consume Practice settings. Localized layout
measurements, strings, and presentation geometry are owned by
[`practice.md`](../localization/font/screen_layouts/practice.md) and
[`settings_presentation.md`](../localization/ui/battle/settings_presentation.md).

The controller, object, table, and transaction findings below are static unless
a runtime observation is stated explicitly.

## Research coverage

- **Assigned scope:** Retail NA2 BTL Battle and Practice Settings children:
  menu and controller ownership, the option records, state and input
  transitions, Confirm/Cancel/Defaults and restart paths, dummy behavior
  settings, starting-HP selection, resource and gauge semantics, and the
  controller/render split.
- **Exploration depth:** Bounded but deep. The 17-row Practice schema and the
  six-row Battle schema were recovered from their label, help, value-pointer,
  count, snapshot, Defaults, enabled-row, and setter paths. The Practice child
  family (BTL live `0x008809E0..0x00882670`) was followed end to end, with
  ownership through the generic parent/UI-owner path, the standalone
  wrapper/selector-host path, and the resident outer controller's preparation,
  running, admission, and teardown states. Manager storage and defaults were
  bounded to the resident settings helpers and the dynamic-support manager that
  stores Linked Mode. Dummy behavior was traced far enough to establish each
  Practice row's setting-specific gate or effect, without reconstructing the
  complete general-AI state machine. Reset work covered the outer Practice
  controller, both snapshot directions and their direct callers, and the BTL
  item-cache entries. The Ultimate row was followed to the resident
  mode-controller dispatcher.
- **Confirmed coverage:** Both ownership chains and their resident scheduling
  gates; the standalone callback registration and selected-command route;
  parent and child states; controller selection and input masks;
  transactional menu behavior; Battle and Practice local-value tables; manager
  and per-side record layouts; dummy Status/Attack/Guard/Move routing;
  Practice Strength profile copy and hot reload; linked, extra-hit, item,
  substitution, and Ultimate branches; discrete snapshot masks; starting-HP
  selection and consumption; continuous HP, chakra, and Link Gauge policies;
  resource lifetime, host module replacement, and later fighter setting
  refresh; the update/draw gates and backdrop variant; and the font renderer's
  allocation-failure behavior.
- **Unresolved or untested:** Visible scheduling and unrestricted indirect
  reachability between the main and standalone owners beyond the recovered
  registration and selection chain; full timing and naming of the general
  AI/controller graph; transitions beyond the selected linked-handshake
  consumer and engine names for several linked-work fields; and physical-PS2
  reproduction of the render-packet exhaustion.
- **Deliberate exclusions and overlap:** Localized text, layout, and
  presentation geometry belong to
  [Practice screen layout](../localization/font/screen_layouts/practice.md) and
  [Battle and Practice settings presentation](../localization/ui/battle/settings_presentation.md).
  General AI state, profile tables, and parameter consumers belong to
  [Battle AI](battle_ai.md); the shared start-menu transaction to
  [Pause and replay](pause_and_replay.md); the Guide Ninja Sound scheduler to
  [Battle audio](battle_audio.md#guide-ninja-sound); item-cache layout and
  inventory routines to [Battle item inventory](battle_item_inventory.md#item-cache);
  the support manager to [Support mechanics](support_mechanics.md); chakra
  arithmetic to [Chakra and guard](chakra_and_guard.md); substitution
  eligibility to [Substitution](substitution.md); PRNG behavior to
  [Resident randomness](../runtime/randomness.md); and slot-`0x6A`
  acquisition to [Content availability](../game/content_availability.md#recovered-difficulty-word-producer).
- **Evidence limitations:** Findings are static, from the identified retail
  `BTL.BIN` and `SLPS_258.37`, with tables and call sites checked against the
  complete raw overlay. Runtime evidence is limited to six starting-HP states
  and the observed retail text loss, which has no input recording, hardware
  run, or breakpoint trace. Exact static effects remain distinct from inferred
  names.

Binary identities and the live/file/preserved-export address relationship used
below are defined in
[Standard game file identities](../game/files/file_identities.md#address-conventions).

## Starting-HP selector

Practice Settings stores its native HP selection as an integer enum: `0` is
Normal/full, `1` is Half, and `2` is Almost/critical.

Paired runtime states before and after selection show that battle setup
consumes the enum for both fighters. Their `float32` HP at fighter `+0x6C` is
respectively `1.0`, `0.5`, and the float32 representation of `0.1`; both sides
held identical values in each state.

Retail `SLPS_258.37` function `FUN_001E7A80` initializes three Practice settings
blocks and is reused by native reset paths. At runtime `0x001E7AE8` (ELF
offset `0xE7BE8`) it executes `sb zero,1(a0)` followed by `li t1,2`; the next
instruction stores `t1` to settings byte `+2`. Settings byte `+1` is therefore
the native starting-HP enum. The evidence combines static tracing and six
runtime states covering all three selections before and after battle setup.

The static construction consumer is resident `FUN_002151E0`. It first applies
the configuration holder's HP/chakra inputs, initializes Link Gauge, and calls
`FUN_00216460` for the setting-derived fighter flags and factors. When manager
mode is `3`, it then calls Health helper `FUN_002165C0` before completing the
fighter's command and child-object initialization. Starting HP is therefore
consumed during native actor construction as well as by the continuous policy
below. A later reconstruction snapshot restore can still write the HP word
directly; those are separate operations.

Representative constructor bodies `FUN_002CE5A0`, `FUN_002DAEF0`, and
`FUN_003000E0` all call this common initializer with their own descriptor
holders. Each also performs character-specific initialization outside the common
call; no additional Practice branch appears in those three constructor bodies. This is a bounded
three-constructor sample, not an audit of every downstream character helper.
The factory census and character identities remain owned by
[Battle entities](battle_entities.md).

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
single `+0x38` slot. The resident paths below further separate the normal
preparation and running-session owners; they do not measure visible overlap or
establish every possible indirect entry route.

### Resident scheduling and controller lifetime

**Observed static path.** The resident outer controller at `0x00607620`
dispatches through `FUN_001EC960`. Its `+0x14` value, returned by
`FUN_001EC240`, is a controller variant, distinct from battle-manager mode
`+0x0C`: variant `2` is the branch which adds the standalone Practice module.
The dispatcher calls `FUN_001EBD90` before its numeric-state switch, so the
start-menu owner is polled even on outer states which do not run the battle
session. Its admission conditions, rather than that top-level call alone,
determine whether it constructs and advances a menu. The shared start-menu
transaction is owned by [Pause and replay](pause_and_replay.md#resident-ownership-and-top-level-result-routing).

The preparation owner is stored at outer-controller `+0x38` and exists in
outer state `9`, handled by resident `FUN_001ED6D0`. When the pointer is null,
that function allocates `0x16C` bytes, calls BTL live `0x00713A50` and
`0x00713DC0`, and initializes its selected stage through live `0x007147C0`.
Variant `2` supplies stage value `6` to this initialization; that numeric
argument does not identify a player-facing stage name. Each invocation then
calls owner update live `0x00715830`. Its eight-entry state table at live
`0x008C3C90` routes owner state `4` to the parent-update wrapper at live
`0x00714CB0`; owner draw live `0x00715CC0` likewise draws the generic parent
only in owner state `4`.

While owner update returns neither `1` nor `-1`, `FUN_001ED6D0` invokes that
draw entry and retains the owner. On either completion value it calls live
`0x00713B20`, frees the `0x16C`-byte owner, and clears outer `+0x38`. Result
`1` also copies the selected stage to manager `+0x98`, sets outer state `10`,
and seeds the outer countdown to `3`; result `-1` enters outer state `7`.
Thus successful preparation destroys this owner before the resource-loading
states `11..14` and running state `15`. The owner's destructor reaches its
generic parent at `+0xA8`; ordinary parent/child menu closure, in contrast,
retains those objects as described below.

The start-menu admission word is resident `0x0060765C`, named
`uGpffffcc6c`/`cGpffffcc6c` in the resident analysis. `FUN_001ED000` clears it
on the state-`2` initialization route. Session controller `FUN_001EF9C0`
sets it to `1` when session halfword `+0x0A` advances from `3` to `4` and
clears it on the inspected departure from active phase `4` into its subsequent
result phases. `FUN_001EDB70`, the outer state-`15` handler, also clears it
when the session reports completion. `FUN_001EBD90` admits a new start menu
only when this word is `1`, its local menu state is zero, manager `+0x14` is
zero, its other blockers are clear, and the input-side predicate returns a
nonzero side. This explains the phase distinction on the traced route without
assigning an elapsed time to either controller.

The `gp`-relative accesses to the admission word are at `0x001EBE38`,
`0x001ED0A0`, `0x001EDBBC`, `0x001EFAA8`, and `0x001EFC28`; the aligned byte
match at `0x00367C40` is an `lwc1` from register `v0`, not an access to this
word. This bounds the word and the direct resident phase chain, not every other
admission blocker, callback, or overlay route.

### Registered standalone Practice selection

**Observation, high confidence:** the type-`5` factory branch installs a
resident callback table at `0x005FBB00` in wrapper `+0x08`. Its four method
slots are:

| Table slot | Encoded live BTL target | Established operation |
| ---: | ---: | --- |
| `+0x08` | `0x0087E4F0` | destroy the wrapper and its Practice child; optionally free the wrapper |
| `+0x0C` | `0x00875AB0` | construct the Practice child |
| `+0x10` | `0x00875B20` | update the Practice child and return Boolean completion |
| `+0x14` | `0x00875B50` | draw the Practice child |

The table's first word is the type descriptor at live `0x008D17D0`. Its
leading string pointer is live `0x008BDAF0`, whose exact bytes spell
`ccStartMenuPractice`. The factory table's type-`5` entry points to live
`0x0087BC1C`, whose bytes (preserved `0x0087BBDC..0x0087BC13`) perform
the `0x10`-byte allocation, the base-table assignment `0x005FBA20`, the
replacement assignment `0x005FBB00`, and zero initialization of child pointer
`+0x0C`. These pointers supply the virtual calls above. No direct code reference to
wrapper update `0x00875B20` was found; its literal address appears in this
resident table.

At the factory join, host `+0x04` is copied to wrapper `+0x00`, and host
`+0x0C` to wrapper `+0x04`, before table slot `+0x0C` is invoked with the
wrapper in `a0`. The host retains only the wrapper pointer at `+0x38`; it
does not copy a second Practice callback table into another module slot.
The module's table pointer is resident, but its methods and type/name data
belong to BTL. A resident table address alone does not establish that these
targets remain usable after BTL replacement; the shared image contract belongs
to [Overlay ABI](../runtime/overlay_abi.md#indirect-dispatch-is-application-abi-not-loader-binding).

**Observation, high confidence:** the host selector reaches this factory
through a stored command ID, not by invoking the Practice update pointer
directly. The shared command-list builder, host UI states, child-result poller,
and result routing are owned by
[Pause and replay](pause_and_replay.md#resident-ownership-and-top-level-result-routing);
its outer-variant-`2` list places Practice command ID `5` at index `4`. The
list's word count is host `+0x18`, its entries start at `+0x1C`, and its
selected index is `+0x10`. Builder helper live `0x0087C190` (bytes at preserved
`0x0087C150..0x0087C19F`) replaces the first entry equal to its second argument
with its third argument and returns immediately. On this variant the list's one
ID `4` therefore becomes ID `2` when the active side is zero, or ID `3` when it
is nonzero, while Practice ID `5` remains at index `4`. No player-facing name is
assigned here to the other command IDs.

Host input live `0x0087C3F0` uses host `+0x04` as its input source. On this
variant's constructed host that value is `0` or `1`, matching manager
`+0x18`; the source-`2` OR-both-input branch is separate. The handler first
requires resident `0x00381FA0(host+0x44)` to report ready. Edge mask `0x20`
then changes host state `3 -> 4`. Edge mask `0x40` instead changes it to
state `2` and requests the closing transition through `0x00381930`.
Directional masks `0x4000`/`0x1000` increment/decrement selected index
`+0x10`, wrap by count `+0x18`, and reload repeat word `+0x14` to `4`
(preserved `0x0087C590..0x0087C6B7`).

State `4` subsequently advances its stored transition fields. Only when
float `host+0x64` reaches at least `562.0` (gate at preserved
`0x0087C8E4..0x0087C903`) does it load `host[+0x1C + 4*selected_index]` and
call the factory at live `0x0087BB10` (preserved `0x0087C904..0x0087C91F`).
Selecting index `4` therefore reaches the registered Practice construction
callback through command ID `5`, and only the subsequent state-`5` host
dispatch reaches its update/draw callbacks. This is an invocation-counted
transition, not evidence of an elapsed duration.

The resident admission helper `FUN_001EBC50` further limits opening this host.
It considers sides `1/2`, requires that side's COM bit (`0x02`) to be clear
unless manager control mode `+0x1C` is `3`, then, for outer variant `2`,
rejects any zero-based side unequal to manager `+0x18`. It reports a side
only when that side's edge-input mask contains `0x800`. This admission check
and the later host-source selection agree on the controlling side; changing
host command selection does not choose a new Practice input owner.

Before that input helper runs, `FUN_001EBD90` applies these additional
admission gates. A non-null session pointer at `0x00607604` combined with a
nonzero battle-route word `0x00607670` blocks opening. The graph query
`FUN_00250820` must return zero: it reads the fighter coordinator's state
selector at `graph->+0x08->+0x14` from graph global `0x00607654`, returning
`-1` when either pointer is null. A nonzero selector and the missing-pointer
`-1` both block admission. Coordinator construction initializes this selector
to `1` through `FUN_0024E380`; graph existence alone therefore does not admit
Practice. The coordinator's fields and state writer are owned by
[Battle entities](battle_entities.md#derived-fighter-registrycoordinator).
Loading predicate `FUN_00200640` must report inactive, and timeout marker
`0x00607674` must be zero. These supplement admission byte `0x0060765C == 1`,
menu-local state `0x00607660 == 0`, and manager `+0x14 == 0`; the flag alone
is insufficient. Graph ownership belongs to
[Battle lifecycle](battle_lifecycle.md#session-construction), and loading
predicate ownership to [Startup](../game/startup.md#controller-construction-resources-and-phases).
The timeout-marker producer and reset belong to
[Match outcomes](match_outcomes.md#terminal-detector-and-classifier). The
coordinator's complete transition graph is unresolved.

These are opening conditions. Once manager `+0x14` is nonzero and menu-local
state is `1`, the other branch allocates/polls the existing host without
rechecking those opening gates; the two branches are distinct in resident
`0x001EBDBC..0x001EBF60`. The outer Practice callback's later indirect call
does not add another Practice update or draw: its installed target at
`0x001ECBF0` is the return-zero stub
`2D 10 00 00 08 00 E0 03 00 00 00 00` documented by
[Mode flow](../game/mode_flow.md#btl-handoff-and-return).

Session destruction supplies a second host retirement route even if ordinary
host completion has not already cleared it. `FUN_001EEFD0` reads the host
pointer at `0x00607668`, calls live `0x0087B160`, releases host member
`+0x8C`, frees the host, and clears the global before deleting the battle
graph (resident `0x001EF1DC..0x001EF21B`); its installed Practice module
consequently follows the same virtual destructor chain above. Session
initialization `FUN_001EED40` clears the global without calling that
destructor, so that clear is not a retirement path. The surrounding session
teardown is owned by [Battle lifecycle](battle_lifecycle.md#teardown-order).

Wrapper destruction (preserved `0x0087E4B0..0x0087E55F`) restores its class
table, destroys and frees child `+0x0C`, clears that pointer, restores the base
table, and frees the wrapper when the deleting-destructor argument is positive.
These static findings do not prove unrestricted indirect reachability, exclude
every register-built interior target, or measure overlap with preparation
drawing.

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
presentation state and starts the parent's transition resource. The two direct
BTL calls are live `0x00714744` (file `0x60844`) in owner initialization and
live `0x007159B8` (file `0x61AB8`) when the stage-confirm transition completes.
Both pass `owner+0xA8`. The latter enters owner state `4` before resetting the
parent. A complete-file aligned `jal` scan finds no other direct BTL callers.

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

The close transition does not check whether the parent result is Confirm or
Cancel before applying that controller mode. `FUN_001F48F0` writes
`manager+0x1C` and updates bit `0x02` in both side records (`+0x48` and
`+0x70`): mode `0` clears both COM bits, mode `1` sets only Player 2's COM
bit, and mode `2` sets only Player 1's. Manual therefore applies mode `0`
even on preparation cancellation. This changes controller assignment without
changing the saved Practice Status option.

The battle UI owner's update wrapper is live `0x00714CB0` (preserved prologue
`0x00714C70`). It forwards `owner+0xA8` to the parent update. Parent result
`1` is propagated to the wrapper's caller. On result `-1`, an owner with
`owner+0x0C >= 0` enters owner state `5`; an owner with a negative `+0x0C`
instead calls the owner reinitializer at live `0x00714700`. This is the first
consumer of the parent's delayed result and keeps child completion, parent
closure, and owner transition as three distinct state boundaries.

## Battle Settings child

This section owns the mode-2 Battle Settings child's local values and
transaction; its row and Handicap geometry belong to
[Battle and Practice settings presentation](../localization/ui/battle/settings_presentation.md#battle-rows-and-handicap).
The child is `0x68` bytes. Native snapshot live
`0x0087F870` reads the manager values into six local words:

| Row | Local | Values | Manager key | Native default |
| ---: | ---: | --- | ---: | ---: |
| `0` | `+0x30` | Time: `10` through `90`, `99`, Unlimited (stored as `100`) | `6` | index `9` / value `99` |
| `1` | `+0x34` | Difficulty: Simple, Easy, Normal, Hard, Insane, Ultimate | `0xB` | `2` |
| `2` | `+0x38` | Items: None, Less, Normal, More | `7` | `2` |
| `3` | `+0x3C` | Chakra: Normal, Unlimited | `2` | `0` |
| `4` | `+0x40` | Ultimate Jutsu: No Use, Random, Command, Timing, Turn, Combo | `5` | `2` |
| `5` | `+0x44` | Handicap: `0-10` through `10-0` | `8` | `5` |

The time values are the 11 words at live `0x008D1850`; the six row counts
`{11, 6, 4, 2, 6, 11}` are at live `0x008D1880`. Snapshot converts the
manager's stored numeric time to its table index, then clamps all six local
values by those counts. The sixth Difficulty option is limited by profile flag
slot `0x6A`; without that flag the maximum index is `4`.

The native Battle value-pointer table at live `0x008BE5C0` confirms exact
resource reuse rather than merely similar labels: Difficulty points to the
same `0x008BDBA0` table as Practice Strength, Items to the same `0x008BDBC0`
table as Practice Items, Chakra to the same `0x00605A90` table as Practice
Chakra, and Ultimate Jutsu to the same `0x008BDC10` table as its Practice row.
The Chakra table contains live string pointers `0x00605A80` for Normal and
`0x00605A88` for Unlimited.

The local Defaults action at live `0x0087FC08..0x0087FC78` finds the first time
entry at least `99`, then writes `{9, 2, 2, 0, 2, 5}` to the six local words.
Those values remain local until the ordinary Confirm transaction. This is
separate from the manager-level reset described below.
After these writes, live `0x0087FC74` plays sound `0x33`, and
`0x0087FC7C..0x0087FCA0` resets the help object and queues the native Defaults
notice through `FUN_0037F760`. The notice pointer is loaded from
`-0x4E18(gp)` at `0x0087FC94`.

The native controller stores its selected row as a halfword at `+0x48`, its
directional-repeat countdown at `+0x4A`, its phase at `+0x58`, newly pressed
input at `+0x60`, and effective directional input at `+0x64`; the help-text
object is at `+0x18`. The snapshot call site is live `0x0087FA04`. The Confirm
arm at live `0x0087FB24` writes phase
`1`, plays its sound, and starts the native apply transaction at live
`0x0087FB38`. The Cancel arm at live `0x0087FBE0` performs the same phase write
for closing. Both paths can return through the common epilogue at live
`0x0087FDBC`.

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

The native menu has 17 rows. The values below are the retail table contents and
help-text meanings. “Default” is what the menu's local Defaults action writes.

| Row | Local | Label and values | Count | Manager key/storage | Default |
| ---: | ---: | --- | ---: | --- | ---: |
| `0` | `+0x6C` | Health: Normal, Half, Almost | 3 | key `4`, `+0x9F5` | `0` |
| `1` | `+0x70` | Chakra: Normal, Unlimited | 2 | key `2`, `+0x9F4` bit 2 | `0` |
| `2` | `+0x74` | Linked Attack: Normal, Unlimited | 2 | key `3`, `+0x9F4` bit 3 | `0` |
| `3` | `+0x78` | Ultimate Jutsu: No Use, Random, Command, Timing, Turn, Combo | 6 | key `5`, `+0x9F6` | `2` |
| `4` | `+0x7C` | Linked Mode: Manual, Auto | 2 | support-manager side record byte `+1` | `1` |
| `5` | `+0x80` | Items: None, Less, Normal, More | 4 | key `7`, `+0x9F8` | `2` |
| `6` | `+0x84` | Commands: OFF, ON | 2 | key `1`, `+0x9F4` bit 0 | `1` |
| `7` | `+0x88` | Damage: OFF, ON | 2 | key `9`, `+0x9F4` bit 4 | `1` |
| `8` | `+0x8C` | Guide Ninja Sound: OFF, ON | 2 | key `0xA`, `+0x9F4` bit 5 | `1` |
| `9` | `+0x90` | Status: Manual, COM, Stand, Jump, Double-jump | 5 | key `0xC`, `+0x9FA` | `2` |
| `10` | `+0x94` | Strength: Simple, Easy, Normal, Hard, Insane, Ultimate | 6 | key `0xB`, `+0x9FB` | `2` |
| `11` | `+0x98` | Attack: No, Single, Combo, Projectile, High Speed Move, Ultimate Jutsu, Jutsu | 7 | key `0xD`, `+0x9FC` | `0` |
| `12` | `+0x9C` | Guard: No, Yes | 2 | key `0xE`, `+0x9FD` | `0` |
| `13` | `+0xA0` | Move: Stay, Follow | 2 | key `0xF`, `+0x9FE` | `0` |
| `14` | `+0xA4` | Substitution Jutsu: Normal, No | 2 | key `0x11`, `+0x9F4` bit 7 | `0` |
| `15` | `+0xA8` | Linked Attack: Don't use, Normal, frequent/random (`乱発`) | 3 | key `0x12`, `+0x9FF` | `1` |
| `16` | `+0xAC` | Extra Hit Counter: Normal, Return | 2 | key `0x10`, `+0x9F4` bit 6 | `0` |

Rows `2` and `15` share an English-facing label but are different controls.
The row-2 help describes how the player's Link Gauge charges; row 15 controls
the non-manual dummy's linked-attack use.

The Status/Strength key order is non-obvious and confirmed in both snapshot
and apply code: Status is key `0xC` at `+0x9FA`, while Strength is key `0xB`
at `+0x9FB`. Resident `FUN_001F6D30` mirrors only key `0xB` (Strength) to
manager `+0xA13`.

**Linked Mode storage.** Practice row `4`, Linked Mode, is stored as byte `+1`
of the controlling side's three-byte record in the dynamic-support manager:
Manual is `0` and Auto is `1`. It is not part of the manager's 12-byte settings
pack. Live `0x00882630` reads, and live `0x00882670` writes, that byte in the
record selected by `manager+0x18`; the effective record is
`*(gp-0x3168) + 0x0C + side*3`. The manager constructor initializes both side
records to `{0, 1, 0}`, so the setting starts as Auto whenever the manager is
recreated. The manager's construction, side-record layout, and other record
bytes are owned by [Support mechanics](support_mechanics.md#ownership-model)
and [Battle entities](battle_entities.md#separate-owner-and-exact-side-slots).

The setting helpers do not make manager absence safe: a null singleton selects
a zero record pointer before the final signed-byte read or byte write at record
`+1` (preserved `0x008825F0..0x00882663`). In the traced construction order,
the manager is created before either settings owner's Linked Mode snapshot. The
setter writes only that byte; it does not rebuild the manager, replace an
active support object, or write the AI handshake.

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
sixth/Ultimate difficulty tier. Its established finite-Survival result
producer and acquisition conditions are owned by
[Content availability](../game/content_availability.md#recovered-difficulty-word-producer);
the Practice consumers do not establish a separate acquisition event.

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
`-28 * +0xB0` on the upper half or `-270 - 28 * +0xB4` on the lower half, by
at most `20.0` per update. Selection therefore changes controller-owned
geometry without reconstructing any render object; the resulting row,
heading, backing, and cursor geometry is owned by
[Battle and Practice settings presentation](../localization/ui/battle/settings_presentation.md#practice-content-and-contexts).

The interactive actions are transactional:

| New-press bit | Action |
| ---: | --- |
| `0x20` | Confirm: call live `0x008811A0` immediately, enter fade-out phase `1`, play `0x34` |
| `0x40` | Cancel: do not apply, enter fade-out phase `1`, play `0x33` |
| `0x100` | Defaults: replace only the 17 local values with the defaults in the table, update help state, play `0x33` |

Defaults remain local until Confirm. Cancel therefore discards both ordinary
edits and a local Defaults action; reopening calls live `0x00880FB0` and
snapshots the manager again.

The native section-heading branch at live `0x008823B8` compares the drawn row
with the section boundary, advances the row origin by `18.0`, loads the heading
text at live `0x008823E0`, and calls its renderer at live `0x008823E8` with
style `0x0F`.

## Confirm/apply side effects

Live `0x008811A0` writes all 16 manager-backed local values through resident
`FUN_001F59F0(manager, key, value)` and writes Linked Mode through live
`0x00882670`. Resident `FUN_001F59F0` checks the battle mode, updates the
packed bits/bytes above, then calls `FUN_001F6D30`; that final helper only
mirrors Strength. It does not perform a general fighter or resource reset.

The exact setter order is Commands, Items, Health, Ultimate Jutsu,
Linked Attack (gauge), Chakra, Damage, Guide Ninja Sound, Linked Mode, Status,
Strength, Attack, Guard, Move, Extra Hit, Substitution, and Linked Attack. The
dummy-status bridge runs only after that sequence. This ordering is material
to the post-write Strength comparison below; there is no staged manager-side
transaction or rollback layer.

### Completion boundaries and fighter setting refresh

The two owners retain different objects when the Practice child finishes its
fade-out. The generic parent returns to its selector state `2` and retains
the child at `+0x3C`. The standalone wrapper at live `0x00875B20` converts
any nonzero child result into Boolean `1`; the host poller at live
`0x0087CB20` then enters host state `1` and starts reopening its list. That
branch does not destroy or clear host `+0x38`. In the same top-level host
invocation, live `0x0087D940` first updates the host and then calls its draw
entry at live `0x0087D460`; the draw's ten-entry table at live `0x008D1700`
dispatches the module's virtual draw only in host state `5`. Once the poller
changes state to `1`, that invocation no longer draws the completed Practice
child. Child Confirm and child Cancel take the same owner-completion route;
their distinction is the earlier apply-versus-discard transaction.

Selecting another module reaches the factory join at live
`0x0087C0F8..0x0087C154`: it destroys the previous `+0x38` module, installs
the newly allocated module, calls its construction callback, and enters host
state `5`. Therefore reopening Practice through this factory constructs a new
child and snapshots the then-current manager values. It does not reuse the
old wrapper's closed child. Whole-host destruction at live `0x0087B160`
also destroys the installed module through its virtual destructor. The
Practice wrapper destructor calls child teardown at live `0x0087E538`, frees
the child, and clears wrapper `+0x0C`; the generic parent's corresponding
sequence is live `0x006BFF88..0x006BFF98` for parent `+0x3C`.

**Observed setting refresh.** Returning from the child to the command list
does not finish the resident start-menu transaction. Manager `+0x14` remains
in the active-menu state until the host's overall updater returns nonzero.
For overall result `1`, resident `FUN_001EBD90` destroys the host, restores
manager `+0x14` to zero, and calls `FUN_00216460` on both live fighters. That
refresh has exactly these setting-derived writes:

| Getter | Fighter fields written by `FUN_00216460` |
| --- | --- |
| Ultimate key `5`, through `FUN_001F6E10` | byte `+0x168 = (value == 0)` |
| Chakra key `2`, through `FUN_001F6DE0` | byte `+0x169 = (value != 0)` |
| Handicap key `8`, through `FUN_001F6E70` | floats `+0x16C` and `+0x170`; both become `1.0` in Practice because this getter returns neutral `5` outside manager mode `2` |

It does not write current HP `+0x6C`, chakra `+0x70`, Link Gauge `+0x74`,
the item cache, or the BTL AI work records. The manager setter's immediate
side cache, the dummy-status bridge, this later fighter-field refresh, and
the continuously polled resource settings are consequently distinct
consumers. `FUN_00216460`'s other direct resident caller is native fighter
construction `FUN_002151E0`; indirect overlay calls were not inventoried.
The mode-`2` Handicap factors are owned by
[Damage](damage.md#handicap-factors); Practice does not acquire a Handicap
control through this refresh.

The wrapper constructor bytes (preserved `0x00875A70..0x00875B6F`) contain
both initialization calls, variant `0`, child storage, and the Boolean result.
These static calls establish object and setting boundaries, not their visible
duration.

The resident order also separates menu work from setting consumption. Within
one `FUN_001EC960` invocation, the start-menu transaction runs before the
outer-state handler. In state `15`, `FUN_001EDB70` then calls session wrapper
`FUN_001EF8F0`. When its session-state updater returns zero, that wrapper
constructs the subsystem masks through `FUN_001F0290` and dispatches them
through `FUN_001F03E0`. An active start menu makes the first allowed mask
zero through manager `+0x14 == 1`; the independent second mask and the
documented exceptions still apply. Thus Confirm's immediate manager writes
precede the later session dispatch in this call chain, but a setting consumer
need not run merely because the menu accepted the edit. The shared mask
contract is owned by [Pause and replay](pause_and_replay.md#selective-update-gating),
and the common AI-to-command order by
[Battle AI](battle_ai.md#controller-ownership-and-lifecycle). This is static
invocation order, not a measured frame boundary.

### Dummy-status bridge

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

The manager-side COM-bit write occurs even when that side has no live fighter.
The bridge checks the resolved fighter pointer before either fighter-field
branch, so a missing fighter skips the nibble write and AI initialization.
This distinguishes setting preparation from updating an existing actor.

The comparison flag is formed by comparing local Strength `+0x94` with getter
key `0xB` **after** the key has been written. In Practice mode the setter
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
  key `0xE` and uses Guard == Yes in non-COM scripted decisions;
- preserved export `FUN_006FAA10` (live `0x006FAA50`) reads Status and Move
  key `0xF` and requires Move == Follow for the scripted movement path;
- preserved export `FUN_006FB090` (live `0x006FB0D0`) reads Status and Attack
  key `0xD`. For non-COM status, Attack `0` exits without an attack, `3` sets
  a projectile-related request, `4` sets a high-speed-move request, and
  `5/6` resolve and execute Ultimate-Jutsu/Jutsu action objects. Values `1/2`
  continue through the ordinary timing/attack-selection paths.

The setting-specific state lives in each `0x1E0`-byte BTL AI work record at
live `0x008D6590 + side*0x1E0`, whose general layout is owned by
[Battle AI](battle_ai.md#per-side-state-block). The fields used below are
`+0x10` request flags, `+0x34` dispatcher state (controller code), `+0x90`
request latch, `+0x94` request countdown, `+0x160` effective Strength profile,
and `+0x1B0` selected Ultimate action slot, plus these Practice-relevant roles:

| Work offset | Live side-0 address | Practice role |
| ---: | ---: | --- |
| `+0xF4` | `0x008D6684` | linked-action timer |
| `+0x114` | `0x008D66A4` | scripted Status timer |
| `+0x118` | `0x008D66A8` | Attack retry/cooldown timer |
| `+0x14E` | `0x008D66DE` | cached linked-partner selector/type byte |
| `+0x150` | `0x008D66E0` | linked-action handshake halfword |

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
It returns when Status is COM and otherwise integrates the three scripted rows
rather than treating them as independent toggles: Guard Yes can select
controller code `0x12` (state 18) with countdown `30`, Move Follow maintains
code `5`, Jump and Double-jump converge on code `0x24` (state 36) through the
`+0x114` timer, and Stand with a nonzero Attack value can select code `0x25`
(state 37), after which the seven-way dispatcher above determines the attack
family. Their priority order and exact gates are owned by
[Battle AI](battle_ai.md#scripted-practice-reaction-priority); for ordinary
modes and Practice COM, the reactions that run before this tail are in
[Battle AI](battle_ai.md#main-reaction-stage-and-later-rewrites). These are
controller requests, not immediate fighter-state assignments.

### Strength profiles

Strength is not a scalar damage multiplier. Resident `FUN_001F6EA0` is the
key-`0xB` getter used by BTL AI. The selected value indexes six `0x50`-byte
profiles of 40 signed 16-bit AI parameters at live `0x008C3230`; the effective
per-side copy begins at BSS live `0x008D66F0 + side*0x1E0`. The profile table,
its per-field consumers, and the initializer's input layers are owned by
[Battle AI](battle_ai.md#configuration-and-behavior-profiles) and
[its parameter ledger](battle_ai.md#direct-profile-parameter-consumers).

Live `0x00705D70` caches the selected level in `iGpffffce10`, copies the
profile for the passed fighter's side, and in Practice skips the secondary
percentage modifier used by other modes. It then applies three
character-descriptor modifiers: descriptor bit `1`, `4`, or `8` multiplies
profile field `16`, `8`, or `24`, respectively, by `1.2` with integer
truncation.

The main AI update at live `0x00704D40` also compares the getter against
`iGpffffce10` in Practice. On a change it updates the cache and copies the new
`0x50` bytes into the current side's BSS profile. That hot-reload copy does not
repeat the three character-specific `1.2` adjustments.

The fields used by the Practice paths below are `12` (Extra Hit cooldown),
`11` and `39` (Extra Hit response threshold and retry delay), `38` (linked-action
retry timer), and `21` (linked-action request threshold). Their bounded-RNG
draws use resident `FUN_00180210(N)`, an inclusive `0..N` modulo reduction
documented in [Resident randomness](../runtime/randomness.md#mt-wrappers).

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
  dummy Status, Linked Mode, and partner availability to initialize the same
  per-side timer. COM Status writes `30 + RNG(0..60)` and retains a separate
  threshold from Strength-profile field `21`; non-COM Normal writes `30` when
  Linked Mode is Manual and no partner is available, otherwise `90`, with
  threshold `100`. Value `2`
  (`乱発`, frequent/random) writes `5` with threshold `100`. A final
  `RNG(0..100) < threshold` sets bit `0x00200000` in the side work flags.
  Another no-current-request branch initializes the timer to
  `90 + RNG(0..30)` under its Linked Mode/partner conditions.

The retail field-`21` values from Simple through Ultimate Strength are
`0, 0, 0, 0, 30, 50`. Because `FUN_00180210(100)` is inclusive and the test
is strict `<`, an unmodified field accepts `0`, `30`, or `50` of the `101`
result values, not `0%`, `30%`, and `50%`; threshold `100` accepts `100` of
them. These are nominal ratios, since the helper keeps modulo bias. The
boosted formula produces `1350` or `3750` for the two nonzero retail fields and
therefore accepts every `0..100` draw; a zero field remains zero.

After live `0x006FE720` selects code `0x26`, Linked Mode controls the handshake
at work `+0x150`. Auto writes `2`. Manual writes `1` when no partner object is
available, writes `2` when the available partner's byte `+0xE6` is `1`, and
leaves other partner states unchanged. Handshake value `1` shortens the same
linked timer to `5`. Work byte `+0x14E` caches the partner selector/type used
by these tests.

One later consumer of this setting-derived handshake is established exactly.
When AI controller code is `0x26` (decimal 38), the dispatch body at live
`0x006FC260` (table word at preserved `0x008C3868`) stores request mask
`0x20000000` in work `+0x10`. It reads the signed handshake halfword at
`+0x150` and clears request latch byte `+0x90` only when that value is `2`;
other values leave the latch unchanged in this body. This handler does not
reread the menu's Linked Mode byte or change the handshake halfword, and the
menu setter does not directly perform this request. Dispatcher ownership and
later output arbitration remain in
[Battle AI](battle_ai.md#action-state-dispatcher); the full linked-action graph
and original field names remain unresolved.

This establishes why rows 4 and 15 interact without conflating them: Linked Mode
participates in scheduling and the partner handshake for an enabled linked
attack, while row 15 can prevent that request family or select its
short-countdown policy. Some partner-state and controller-code semantics remain
unnamed, but the setting-selected timers, thresholds, draws, and written fields
are exact.

Extra Hit key `0x10` is consumed by the Extra Hit Counter response selector at
live `0x006FF650`. Return (`1`) clears the relevant cooldown and commits the
candidate response immediately (code `0x0D` for hit-response flags
`0x0400`/`0x1000`, code `0x13` for `0x0100`); Normal (`0`) keeps the ordinary
cooldown, Strength-profile, and phase-gate path. The selector's states, phase
gate, and profile fields are owned by
[Battle AI](battle_ai.md#direct-state-constructors),
[its RNG section](battle_ai.md#rng-ownership-and-confirmed-uses), and
[its parameter ledger](battle_ai.md#direct-profile-parameter-consumers).

### Item amount

Resident `FUN_003AEAF0` is a concrete Items key-`7` consumer in the item-spawn
path:

- None (`0`) rejects the spawn request entirely;
- Less (`1`) retains the base spawn but sets the extra-spawn count to zero;
- Normal (`2`) retains the caller's extra-spawn count;
- More (`3`) changes an extra count below one to `2`, otherwise doubles it,
  and adds another base-style spawn when a `0..100` inclusive random draw is
  below `80` (80 of 101 result values, nominally `79.21%`; the helper's
  modulo bias is documented in
  [Resident randomness](../runtime/randomness.md#mt-wrappers)).

Position randomization and the caller-provided spawn kind still affect the
result; these setting branches do not themselves choose the item identity.
The identity selector, its authored general and recovery pools, native
weights, and its separation from spawn amount are documented
in [Random field-item selection](battle_item_inventory.md#random-field-item-selection).

### Substitution Jutsu

At live `0x006FBDC4..0x006FBE88`, a branch in the per-side behavior
dispatcher first verifies Practice mode (`manager+0x0C == 3`) and calls the
resident setting getter for key `0x11` at live call site `0x006FBE18`.

The two setting outcomes are concrete:

- Don't use (`1`) writes dispatcher code `0x12` to live
  `0x008D65C4 + side*0x1E0` and exits this decision path;
- Normal (`0`) calls resident `FUN_00229B70(current_fighter, -2)`, which writes
  signed halfword `current_fighter+0x95C = -2`, then exits the same path.

The negative `+0x95C` value is the guard-age sentinel that lets substitution
eligibility routine `FUN_00229130` take its early path; its maintenance and
shortcut are owned by
[Substitution](substitution.md#negative-guard-age-sentinel-and-temporary-effect-id-9).
The dispatcher branch is state `20` in
[Battle AI](battle_ai.md#action-state-dispatcher).

### Presentation options and Ultimate gate

The three presentation settings are consumed outside the Practice menu rather
than by its draw routine:

- live `0x006BB590` begins the Damage renderer by reading key `9`.
  OFF returns before building/drawing the damage object. ON still requires the
  object's `+0x4C` bit 0 and its side short `+0x0C` to match
  `manager+0x18`;
- live `0x00728B00` updates the Commands HUD and explicitly calls its
  clear/hide helper at live `0x00728A80` when key `1` is OFF. The companion
  path at live `0x00728BF0` skips the command-display drawing work when OFF,
  and live `0x00729130` forces that HUD's internal byte `+3` into its closed
  state when OFF;
- live `0x00728EA0` (event trigger) and live `0x00728F80` (scheduler) both
  gate the Guide Ninja Sound subsystem on key `0xA`; ON does not force a sound
  because the subsystem's own event and audio-busy tests still apply. The
  scheduler is owned by [Battle audio](battle_audio.md#guide-ninja-sound).

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
single draw. Treating each inclusive `0..100` draw as uniform, the nominal
probabilities are `418241/1030301` for Timing (`3`), `339360/1030301` for
Command (`2`), `137700/1030301` for Turn (`4`), and `135000/1030301` for
Combo (`5`); `FUN_00180210` keeps modulo bias, so these are not exact
([Resident randomness](../runtime/randomness.md#mt-wrappers)). The final
`<= 100` test always accepts, so the encoded fallback
which chooses `2` or `3` is unreachable under this helper contract. The
dispatcher also contains a mode-`6` class, but the retail Practice row count and
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

In that block, the Simple Display default is written by the `or v1,v1,a2` at
live `0x001E7AAC` after masking byte `0` with `0xFFFFFFFD`, so the setting is
bit `0x02` of byte `0`. Its menu and getter/setter are owned by
[Pause and replay](pause_and_replay.md#simple-display-selection).

Resident `FUN_001F5960` has one established caller, the Practice controller's
state-`2` initialization path at live `0x001ED0E4`. It resets `+0x9F4` and
`+0xA00`, then in modes `2/3` re-applies Strength key `0xB` from mirror byte
`manager+0xA13`. This is a manager-level default operation; it is separate from
the pause menu's local Defaults action. No Battle-mode caller of
`FUN_001F5960` is established; the mode selector's case-2 branch at live
`0x001EA7B4..0x001EA7C0` assigns `manager+0x0C = 2`, and the common selector
flow rejoins at live `0x001EA818`.

### Discrete Practice-controller reset

Resident `FUN_001EC960` dispatches the outer Practice controller. In state `2`,
`FUN_001ED000` waits for the preceding asynchronous transition, clears several
controller globals, calls `FUN_001F5960`, and advances to state `3`. State `3`
calls `FUN_001ED110`, which:

- seeds the resident per-side snapshot words to normalized HP `1.0` and chakra
  `15.0` for sides `1` and `2`;
- calls encoded BTL target/live `0x0070F1E0`;
- clears its own transition globals and advances to state `4`.

Live `0x0070F1E0` only clears the two sides' three-entry
[item cache](battle_item_inventory.md#item-cache) at live `0x008D6A60`; it does
not touch HP, chakra, or gauge state. That document owns the cache layout, its
category-6 exclusion, and the build (`0x007109F0`) and restore (`0x00710B00`)
routines, including restore-time normalization of item IDs `0x51..0x73`.

Item state is mask bit `0x20` in the resident snapshot API:

- `FUN_001ECC00(..., side, mask)` captures HP for bit `1`, chakra for bit `2`,
  and, for bit `0x20`, calls `FUN_00375FD0` to build the selected side's item
  cache. A side argument of `1` or `2` first seeds both resource snapshots and
  calls live `0x0070F1E0`, so stale caches for both sides are cleared before
  the requested side is captured;
- `FUN_001ECDE0(..., side, mask)` restores the same resources. For bit `0x20`
  it calls resident `FUN_00376050`, which dispatches live `0x00710B00` for the
  requested side mask; category-6 inventory entries are left intact.

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

### Reconstruction entry and retained setting owners

The resident controller distinguishes re-entry at state `3` from the
state-`2` manager-default operation. For outer variant `2`, the inspected
state-`18` route with battle-route value `6` enters state `22`; its handler
`FUN_001EEAC0` waits for the resource fence and writes state `3`. That resumes
`FUN_001ED110`, which seeds both HP/chakra snapshots and clears both item
caches. It does not invoke `FUN_001F5960`. Later state `9` constructs a new
preparation owner because the old `+0x38` owner was freed on completion.
This path therefore resets snapshot storage and reconstructs the UI while
bypassing the earlier settings-pack default call. It is not the child-local
Defaults action or a restore from the previous menu's local values. The
shared teardown and route selection are documented in
[Pause and replay](pause_and_replay.md#start-menu-result-paths-through-teardown).

The route-`8` reconstruction branches have different capture masks. Resident
`FUN_001EE1C0` captures both sides with side `-2` and mask `-1` before
destroying the session owner. Resident `FUN_001EE500` instead chooses one
side from manager `+0x50`. Its outer-variant-`2` branch captures that side
with mask `0x20`; the `...FFEF` capture belongs to the variant-`4` branch
only. Selecting one side first
seeds **both** HP snapshots to `1.0`, both chakra snapshots to `15.0`, and
clears both item caches in `FUN_001ECC00`, then captures the selected side's
items. Consequently the mask-`0x20` branch retains that side's eligible items,
not its previous HP/chakra snapshot values. The other side's item cache is
left empty by the preparatory clear.

Both branches set reconstruction condition `0x00607678` to `2` and re-enter
at outer state `13`. Graph creation `FUN_001EF330` restores side `-2` with
mask `-1` or `...FFEF`, according to reconstruction-mode word
`0x0060767C` (operands at resident `0x001EF4E0..0x001EF54F`). The restored
HP/chakra words are therefore whatever the preceding capture left in the
outer controller; these restore masks do not establish that the preceding
capture preserved both resources. Neither capture nor restore includes Link
Gauge. The source of route `8` and its shared graph ownership belong to
[Pause and replay](pause_and_replay.md#battle-teardown-and-reconstruction);
this conditional variant analysis does not establish that an ordinary Practice
menu choice produces that route.

Linked Mode has a longer ownership boundary than either settings UI. Outer
construction `FUN_001EC7A0` recreates the support manager, establishing Auto in
both side records, and outer destruction `FUN_001EC890` destroys it. The
state-`14` battle-entry reset (`FUN_001EDB00`) and state-`16` cleanup
(`FUN_001EDD10`) retain the manager and its selector bytes `+0x0D/+0x10`, so a
Linked Mode choice survives those graph-entry and graph-cleanup paths until the
outer controller is rebuilt. The manager phases are owned by
[Support mechanics](support_mechanics.md#scheduled-lifecycle-and-teardown).

A whole-file aligned `jal` scan of the identified ELF and BTL finds three
resident snapshot-capture sites (`0x001EE1EC`, `0x001EE56C`, `0x001EE588`),
two restore sites (`0x001EF528`, `0x001EF54C`), and no direct BTL call to
either resident snapshot entry; other overlays and indirect calls were not
scanned.

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
3. Under the same eligibility gate, Chakra key `2` == Unlimited refills chakra
   through `FUN_002254A0(15.0, fighter, 0, 0, 0)` when no chakra reservation is
   pending at fighter `+0x7C`. The refill's gates, the reservation lifecycle,
   and the adder's clamp are owned by
   [Chakra and guard](chakra_and_guard.md#initialization-maximum-and-resetrefill).
4. Independently of that narrower action-state gate, Link Gauge key `3` ==
   Unlimited increments fighter `+0x74` by `1.0` and clamps it to `[0,1]`
   during the Practice fighter update.

Consequences:

- Confirm does not directly write fighter HP, chakra, or Link Gauge; it writes
  settings, and the relevant fighter update later consumes them.
- Health Normal actively refills to full on eligible updates. Chakra Normal
  does not refill, and Link Gauge Normal does not increment.
- Chakra Unlimited is not an unconditional per-update assignment to `15.0`; it
  keeps the reservation and adder gates.
- No static evidence shows the menu's Confirm or local Defaults action directly
  resetting items, Link Gauge, or the item-slot cache at `0x008D6A60`.

## Rendering and control split

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
passes `0`. In draw, only nonzero `+0x48` submits the full-frame Practice
Settings backdrop rectangle. Its RGB is `0x86A8BE` and its opacity comes from
child alpha `+0x54`, which live `0x00881AB0` advances for the open and close
phases. The backdrop is independent of the backing animation at child `+0x2C`,
the row renderer, and the input owner.

Opening Practice from parent state `2` calls only live `0x00880F30`. That reset
does not replace or free any pointer at `+0x04..+0x34`; it clears presentation,
input, and page state, re-snapshots manager values, and resets the help
animation. The destructor is called from parent/wrapper teardown sites, not
from the ordinary state `2 <-> 5` open/close transaction. Ordinary open/close
therefore reuses the constructed resources.

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

The reveal delay at child `+0x56` is draw-call-counted. Reset clears it; once
alpha is full, each call to live `0x00882250` increments it until `3` and
returns without drawing rows. Raw `jal` enumeration finds exactly two direct
caller families:

| Caller family | Update call site -> target | Draw call site -> target |
| --- | --- | --- |
| main generic parent | `0x006C1014 -> 0x00881AB0` | `0x006C1250 -> 0x00882250` |
| standalone wrapper | `0x00875B2C -> 0x00881AB0` | `0x00875B5C -> 0x00882250` |

### Render-packet allocation failure

The Practice draw routine submits all 17 rows after the reveal delay, including
rows outside the visible window. Its label and value helpers ultimately reach
resident `FUN_00188140`. For each glyph, resident `FUN_00187CC0` requests
transient GS-packet storage through `FUN_00182E60`; a null allocation skips that
glyph. `FUN_00182E60` obtains the storage from the render pool through
`FUN_001104A0`, which returns null when no suitable free block remains. The pool
occupies `0x00951480..0x00B51480`, exactly 2 MiB. `FUN_001104A0` links each
allocation into the list passed in `$a1` and records that list address in the
allocation header at `+0x04`.

This establishes that render-pool exhaustion can selectively remove Practice
text. Static analysis alone does not establish which runtime state exhausts the
pool first.

**Runtime observation:** text loss of this kind also occurs in unmodified
retail NA2. **Inference:** because the failure path is in the game's EE-side
packet construction, before the GS stream reaches the renderer, a physical PS2
should reproduce it when the pool exhausts; this has not been confirmed on
hardware.

### Native Practice Settings presentation geometry

Row windows, backing animation records, the title model, atlas and color data,
resource construction, and cursor and arrow geometry are owned by
[Battle and Practice settings presentation](../localization/ui/battle/settings_presentation.md#practice-content-and-contexts)
and its [cursor and arrows](../localization/ui/battle/settings_presentation.md#cursor-and-arrows)
section.

### Negative findings

- live `0x006C0CC0` is a VS/Practice prompt renderer, not the Practice
  Settings controller;
- live `0x00881E50` is a draw helper, not an input owner;
- the Practice draw loop does not reset or apply manager option values.

## Address index

### BTL code

| Role | Live entry/target | Complete file | Preserved-export prologue |
| --- | ---: | ---: | ---: |
| generic parent zero/init | `0x006BFD30` | `0x0000BE30` | `0x006BFCF0` |
| generic parent constructor | `0x006BFFF0` | `0x0000C0F0` | `0x006BFFB0` |
| generic parent destructor | `0x006BFDB0` | `0x0000BEB0` | `0x006BFD70` |
| generic parent reset | `0x006C0380` | `0x0000C480` | `0x006C0340` |
| generic outer-selector update | `0x006BE810` | `0x0000A910` | `0x006BE7D0` |
| generic parent close-transition completion | `0x006C06F0` | `0x0000C7F0` | `0x006C06B0` |
| generic parent selector/open update | `0x006C07C0` | `0x0000C8C0` | `0x006C0780` |
| generic parent update | `0x006C0F60` | `0x0000D060` | `0x006C0F20` |
| generic parent renderer | `0x006C1120` | `0x0000D220` | `0x006C10E0` |
| Practice row-offset easing helper | `0x006C12A0` | `0x0000D3A0` | `0x006C1260` |
| Damage renderer/settings gate | `0x006BB590` | `0x00007690` | `0x006BB550` |
| Ultimate raw battle-rule-mode accessor | `0x006EE560` | `0x0003A660` | `0x006EE520` |
| Ultimate Jutsu setting getter call site (inside general AI) | `0x006F8BD0` | `0x00044CD0` | `0x006F8B90` |
| seven-way scripted Attack dispatcher | `0x006F95B0` | `0x000456B0` | `0x006F9570` |
| scripted Guard consumer | `0x006FA590` | `0x00046690` | `0x006FA550` |
| scripted Move consumer | `0x006FAA50` | `0x00046B50` | `0x006FAA10` |
| broad scripted Attack decision path | `0x006FB0D0` | `0x000471D0` | `0x006FB090` |
| linked-action enable/profile gate | `0x006FE720` | `0x0004A820` | `0x006FE6E0` |
| linked-action frequency/countdown policy | `0x006FF410` | `0x0004B510` | `0x006FF3D0` |
| Extra Hit response policy | `0x006FF650` | `0x0004B750` | `0x006FF610` |
| Substitution setting getter call site (inside behavior dispatcher) | `0x006FBE18` | `0x00047F18` | `0x006FBDD8` |
| Practice Strength-profile hot reload in main AI update | `0x00704D40` | `0x00050E40` | `0x00704D00` |
| clear six two-byte BTL records | `0x0070F1E0` | `0x0005B2E0` | `0x0070F1A0` |
| reset common AI work and initialize selected-side Strength profile | `0x00705D70` | `0x00051E70` | `0x00705D30` |
| central scripted Status/Guard/Move controller | `0x007024A0` | `0x0004E5A0` | `0x00702460` |
| build one side's three-slot item cache | `0x007109F0` | `0x0005CAF0` | `0x007109B0` |
| restore one side's three-slot item cache into inventory | `0x00710B00` | `0x0005CC00` | `0x00710AC0` |
| preparation UI owner destructor | `0x00713B20` | `0x0005FC20` | `0x00713AE0` |
| preparation UI owner constructor | `0x00713DC0` | `0x0005FEC0` | `0x00713D80` |
| battle UI owner reinitializer | `0x00714700` | `0x00060800` | `0x007146C0` |
| battle UI owner parent-update wrapper | `0x00714CB0` | `0x00060DB0` | `0x00714C70` |
| preparation UI owner state dispatcher | `0x00715830` | `0x00061930` | `0x007157F0` |
| battle UI owner parent-draw wrapper | `0x00715CC0` | `0x00061DC0` | `0x00715C80` |
| ultimate skill-play creation function containing the raw-mode consumer | `0x00769790` | `0x000B5890` | `0x00769750` |
| Ultimate raw-mode consumer call site | `0x0076A0CC` | `0x000B61CC` | `0x0076A08C` |
| Commands update/settings gate | `0x00728B00` | `0x00074C00` | `0x00728AC0` |
| Commands draw/settings gate | `0x00728BF0` | `0x00074CF0` | `0x00728BB0` |
| Guide Ninja Sound event/settings gate | `0x00728EA0` | `0x00074FA0` | `0x00728E60` |
| Guide Ninja Sound scheduler/settings gate | `0x00728F80` | `0x00075080` | `0x00728F40` |
| standalone Practice update wrapper | `0x00875B20` | `0x001C1C20` | `0x00875AE0` |
| standalone Practice draw wrapper | `0x00875B50` | `0x001C1C50` | `0x00875B10` |
| standalone Practice wrapper construction callback | `0x00875AB0` | `0x001C1BB0` | `0x00875A70` |
| standalone host module-list builder | `0x0087B3B0` | `0x001C74B0` | `0x0087B370` |
| screen-selector module factory (Practice is case `5`) | `0x0087BB10` | `0x001C7C10` | `0x0087BAD0` |
| standalone host module update | `0x0087CB20` | `0x001C8C20` | `0x0087CAE0` |
| standalone host draw | `0x0087D460` | `0x001C9560` | `0x0087D420` |
| standalone host update/draw wrapper | `0x0087D940` | `0x001C9A40` | `0x0087D900` |
| standalone wrapper child-destructor call site | `0x0087E538` | `0x001CA638` | `0x0087E4F8` |
| Battle snapshot manager values | `0x0087F870` | `0x001CB970` | `0x0087F830` |
| Battle child reset/snapshot | `0x0087F9D0` | `0x001CBAD0` | `0x0087F990` |
| Battle snapshot call site | `0x0087FA04` | `0x001CBB04` | `0x0087F9C4` |
| Battle Confirm phase-write site | `0x0087FB24` | `0x001CBC24` | `0x0087FAE4` |
| Battle Cancel phase-write site | `0x0087FBE0` | `0x001CBCE0` | `0x0087FBA0` |
| Battle local Defaults block | `0x0087FC08..0x0087FC78` | `0x001CBD08..0x001CBD78` | `0x0087FBC8..0x0087FC38` |
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
| Linked Mode getter | `0x00882630` | `0x001CE730` | `0x008825F0` |
| Linked Mode setter | `0x00882670` | `0x001CE770` | `0x00882630` |
| Linked Mode backing-object rebuild | `0x00885210` | `0x001D1310` | `0x008851D0` |
| Linked Mode backing-object teardown | `0x00885290` | `0x001D1390` | `0x00885250` |
| support manager battle-phase entry | `0x008852E0` | `0x001D13E0` | `0x008852A0` |
| support active-object cleanup | `0x008853D0` | `0x001D14D0` | `0x00885390` |
| Linked Mode backing-object constructor | `0x00886CB0` | `0x001D2DB0` | `0x00886C70` |

### BTL data

| Role | Live address | Complete file | Preserved-export byte location |
| --- | ---: | ---: | ---: |
| 17 label pointers | `0x008BE6C0` | `0x0020A7C0` | `0x008BE680` |
| normal help pointers | `0x008BEF70` | `0x0020B070` | `0x008BEF30` |
| status-specific help pointers | `0x008BF350` | `0x0020B450` | `0x008BF310` |
| 17 value-array pointers | `0x008BF380` | `0x0020B480` | `0x008BF340` |
| six Strength source profiles (`6 x 0x50`) | `0x008C3230` | `0x0020F330` | `0x008C31F0` |
| eight-entry preparation-owner state table | `0x008C3C90` | `0x0020FD90` | `0x008C3C50` |
| 15-entry screen-selector module jump table | `0x008D1690` | `0x0021D790` | `0x008D1650` |
| ten-entry standalone-host draw table | `0x008D1700` | `0x0021D800` | `0x008D16C0` |
| 11 Battle time values | `0x008D1850` | `0x0021D950` | `0x008D1810` |
| six Battle value counts | `0x008D1880` | `0x0021D980` | `0x008D1840` |
| 17 value counts | `0x008D18C0` | `0x0021D9C0` | `0x008D1880` |
| per-side AI work record | `0x008D6590 + side*0x1E0` | BSS; nominal `0x00222690` is past EOF | `0x008D6550 + side*0x1E0` (nominal baseline) |
| per-side effective Strength profile | `0x008D66F0 + side*0x1E0` | BSS; nominal `0x002227F0` is past EOF | `0x008D66B0 + side*0x1E0` (nominal baseline) |
| two three-slot item cache records | `0x008D6A60` | BSS; nominal `0x00222B60` is past EOF | `0x008D6A20` (BSS) |

Absolute table pointers embedded in BTL point to the live addresses in the
second column. BSS rows intentionally have no complete-file byte location.
