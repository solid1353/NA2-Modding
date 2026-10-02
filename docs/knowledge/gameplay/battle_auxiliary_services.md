# Battle auxiliary services

This document records the two auxiliary battle services that retail NA2
(`SLPS-25837`) creates for every battle session: the resident effect manager
`ccEffectManager` and the BTL skill service `ccSkillCtrl`. It covers their
construction and RTTI identities, embedded controllers, record banks and
handles, per-phase callbacks, and deferred and immediate deletion. Their
position in the session's construction, per-update dispatch, and teardown
belongs to [Battle lifecycle](battle_lifecycle.md).

## Research coverage

- **Assigned scope:** `ccEffectManager` and `ccSkillCtrl` construction,
  RTTI/vtable joins, pooled and individually registered effect records,
  skill primary/subordinate/cut-in records and handles, their phase-1/2/3
  callbacks, and their retirement and deletion interfaces.
- **Exploration depth:** constructors, RTTI and vtables for both services, the
  three pooled effect controllers and `ccEffDrawObj`, the `ccEffDrawObj`
  record handle, binding, and retirement paths, the individual-record
  registration and handle checks, the `ccSkill`/`ccSkillComboBase` primary
  tables, the `ccSkillObj`/`ccSkillDmyPlayer` subordinate tables, two concrete
  subordinate samples (`ccSkillPlayerBlowWatch`, `ccSkillHKG001Wall`), the
  cut-in controller's handle validation and child bank, and the deletion paths
  of all three skill groups.
- **Confirmed coverage:** pool versus individual-record ownership in
  `ccEffectManager`; `ccEffDrawObj` generation-checked handles, pool-pressure
  reuse, and its two retirement mechanisms; the pooled controllers' update,
  draw, and delay-word gates and phase-3 resource retirement;
  `ccSkillCtrl` primary/subordinate/cut-in interfaces and handle validation;
  deferred bank-level deletion of subordinates and primaries; and the distinct
  destructor interfaces of each group.
- **Unresolved or untested:** every individually registered effect class and
  producer; the full concrete skill callback and producer set; the embedded
  offset-gauge callback semantics; cut-in bank child identities and any
  producer of the cut-in insertion helper; the downstream meaning of the
  primary slot-`+0x138` helper; every producer-side writer of the pooled
  delay word `+0x28`; and every writer of the `ccEffDrawObj` ownership and
  completion bytes.
- **Deliberate exclusions and overlap:**
  - Session construction, dispatch order, and teardown belong to
    [Battle lifecycle](battle_lifecycle.md).
  - Resource submission belongs to
    [Render submission](../runtime/render_submission.md); playback child
    contracts to [Scene playback owners](../runtime/scene_playback_owners.md);
    particle-generator actions to
    [Effect-generator commands](../runtime/effect_generator_commands.md).
  - Skill contribution and flush semantics belong to
    [Combo accounting](combo_accounting.md); skill outcomes to
    [Match outcomes](match_outcomes.md) and
    [Ultimate Jutsu](ultimate_jutsu.md).
  - The cut-in flag's effect on update masks belongs to
    [Pause and replay](pause_and_replay.md#auxiliary-btl-global-and-the-0xa50-override).
- **Evidence limitations:** conclusions are static. The auxiliary class samples
  and registration searches are bounded; direct-call and literal-address
  searches do not exclude indirect or computed callers, and RTTI names are
  internal class identifiers, not player-facing move names.

## Address convention

Resident addresses are ELF virtual addresses; BTL addresses are live unless
labelled Ghidra. Conversions follow
[Retail game file identities](../game/files/file_identities.md#address-conventions).

## Resident effect-manager callbacks and ownership

The resident auxiliary global `0x006076F0` is `ccEffectManager`.
`FUN_00309090` allocates `0x31C0`
bytes and calls `FUN_00309DF0`; that constructor installs vtable
`0x005DC9E8` at object `+0x31BC`. Its RTTI pointer `0x005C8C70` resolves
to the literal `ccEffectManager` at `0x005A6580`. The constructor and
`FUN_0030C710` register three embedded controllers in the list at
manager `+0x3F4`, counted by `+0x414`:

| Embedded field | Retail RTTI name | Final vtable | Initialization slot `+0x0C` |
| ---: | --- | ---: | ---: |
| `+0x41C` | `ccEffDrawObjWorkCtrl` | `0x005DC8C0` at child `+0x14` | `FUN_0030DDD0`, allocating `0x200` elements |
| `+0x434` | `ccEffHitMarkWorkCtrl` | `0x005DC890` at child `+0x14` | `FUN_0030E380`, allocating `0x34` elements in seven groups |
| `+0x484` | `ccEffIllustCharWorkCtrl` | `0x005DC860` at child `+0x14` | `FUN_0030E560`, allocating groups selected by 21 count/resource rows |

All three pools use `0x210`-byte elements constructed by
`FUN_0030E770` and destroyed by `FUN_0030E830`. The subtype names are
retail identifiers; they do not by themselves classify every resource or
caller using a pool. RTTI/data bytes at resident
`0x005C8C00..0x005C8C80`, `0x005A64F0..0x005A65B3`, and vtables
`0x005DC860..0x005DC8E0` establish these names and targets.

The three controllers share their service callbacks: slot `+0x14` is
`FUN_0030DEE0`, slot `+0x18` is `FUN_0030DF80`, and slot `+0x1C` is
`FUN_0030E020`. These map to the registered-list portions of the manager's
phase-1/2/3 passes, respectively. They walk the active list at child `+4`
using element next `+0x1B8`. The element delay is the signed word `+0x28`
(`lw/sw 0x28` at `0x0030DF04..0x0030DF38`; reset `FUN_0030E8D0` stores
`sw zero, 0x28` at `0x0030E920`). Phase 1 requires update byte `+0x38`;
a negative delay is replaced by its absolute value through `FUN_001771A0`
and the callback is skipped for that pass, a positive delay is decremented,
and element slot `+0x0C` runs when the word is zero after that step.
The "delay predicate" in phases 2 and 3 is `FUN_001771A0(+0x28) == 0`
(`0x0030DFB8..0x0030DFC4`, `0x0030E050..0x0030E05C`).
Phase 2 checks draw byte `+0x39` and the delay predicate, chooses the
manager-owned view indexed by element `+0x1C`, and calls element slot
`+0x10`. Phase 3 checks update
byte `+0x38` and the delay predicate before element slot `+0x14`; afterward
retirement flag `element+0x24 & 1` causes `FUN_0030EBC0` resource cleanup,
clears element byte `+0x1B1`, and unlinks its previous/next pointers
`+0x1B4/+0x1B8`. It does not free the pooled element there. Controller
cleanup slot `+0x10` is `FUN_0030A830`, which deletes the entire array,
clears its pointer, active-list head and capacity. The shared controller
phase 3 is therefore a resource-retirement boundary as well as a callback
pass, distinct from the graph's non-removing generic phase-3 walk.

Separately, the `0x300` records at manager `+0x544` have stride `0x0C`
and own individually registered effect objects. `FUN_0030CAE0` searches
for an empty record from either end, stores its pointer and a nonzero serial,
sets the object's manager/index/serial fields, and optionally returns a
three-word handle `(index, serial, pointer)`. `FUN_0030C2E0` checks all
three against the live record and the object's serial at `+0x10`. This is
direct evidence that retaining only a pointer is insufficient for that
handle's validity; it does not establish all producer lifetimes.
`FUN_0030BB40` destroys flagged records through object slot `+0x20`
with delete argument `1` and clears each record. `FUN_0030C950` performs
the same destruction over every nonnull record during manager teardown.
Registered pooled controllers have separate array ownership and are cleaned
after those individual records by `FUN_0030A9F0`.

The individual-record third-phase callback has different eligibility from
the pooled-list callback: `FUN_0030BE30` requires update byte `+0x38`
nonzero and retirement flag `+0x24 & 1` clear, then invokes object slot
`+0x14` without its own delay test. The pooled element is `ccEffDrawObj`:
final vtable `0x005DC830` points through RTTI `0x005C81E8` to that literal
at `0x005A5BC0`. Its update/draw/third-phase targets are
`FUN_003108A0`, `FUN_00311C60`, and `FUN_00310A90`.
The last requires a nonnull payload at element `+0x1A0` and advances
configured fade, scale, texture-frame, rotation and translation state. It
can invoke element slot `+0x18` when a countdown or nonlooping sequence
finishes. The first-phase callback binds transforms and advances the
model/animation path; the second submits the selected model or sprite form.
This concrete effect therefore splits animation/resource state across both
update phases. Resource submission details belong to
[Render submission](../runtime/render_submission.md). Other individually
registered effect classes and every producer are not exhaustively recovered.

## BTL skill-service callbacks and ownership

The BTL auxiliary global `0x00607844` is `ccSkillCtrl`. Live
`0x00776AD0` allocates `0x3330` bytes and calls constructor
`0x00777130`, which installs resident vtable `0x005FB9B8` at
object `+0x3320`. That table's RTTI points to live BTL `0x008D02F0`,
whose name pointer is live `0x008BC5D8`, the literal `ccSkillCtrl`.
The constructor also initializes embedded `ccSkillCutInCtrl` at `+0x210`
and `ccSklOfstGauge` with its vtable at service `+0x32CC`.
Their final resident tables are `0x005E08D0` at cut-in child `+0x830`
and `0x005FB9D0`, respectively. The name joins are at Ghidra `0x008CE820`, `0x008BB400`, `0x008D02B0..0x008D02C0`,
and `0x008BC598..0x008BC5B7`. These are retail class identifiers;
they do not supply player-facing names for every skill variant.

The controller has two primary `(pointer, serial)` records at `+0/+8`,
and two banks of 32 subordinate records at `+0x10`, with stride `8`
within a bank and `0x100` between sides. Live `0x00778790` registers a
primary only when its selected record is empty, stores a serial, and writes
the object's handle fields `+0x120/+0x124/+0x128` as
`(side index, serial, self pointer)` plus controller pointer `+0x0C`.
Live `0x00778630/0x007786E0` search subordinate records from the back/front,
respectively, taking the side from subordinate `+0x958`. They store the
subordinate's slot/serial/self fields at `+0x78/+0x7C/+0x80` and can
return the same three-word handle. The instruction ranges at Ghidra
`0x007785F0..0x007787E4` establish both registration paths, including their
separate serial counters. This does not establish an exhaustive producer
set or the lifetime of every copied handle.

The primary base is `ccSkill`: constructor live `0x00785410` installs
vtable `0x005FB4D0` at object `+0x110`; its RTTI resolves to the resident
literal `ccSkill` at `0x006059C0`. The service's primary phase slots have
these concrete base targets, preserved in resident table bytes
`0x005FB5F0..0x005FB60F`:

| Primary slot | Service use | Base target, live BTL |
| ---: | --- | ---: |
| `+0x124` | Phase 1, primary `+0x14 & 3 == 0` | `0x007950D0` |
| `+0x128` | Phase 2, same primary flag gate | `0x007956E0` |
| `+0x12C` | Phase 3, same primary flag gate | `0x00795990` |
| `+0x138` | Additional call after the phase-3 subordinate pass, for each nonnull primary | `0x0077EB40` |
| `+0x120` | Final wrapper pass, for each nonnull primary | `0x00794FA0`, empty |

The base slot-`+0x138` thunk calls live `0x00770490` (Ghidra
`0x0077EB00..0x0077EB1F`). That helper starts with
the resident nonnull/session predicate `0x003083A0` on the primary's
fighter pointer `+0x31C`. Its full downstream meaning and the embedded
offset-gauge callback semantics remain unclassified.

Base phase 3 requires byte `+0x1C0` zero before calling slot `+0x134`
(live `0x00795DE0`). That hook invokes slot `+0x10C`; with byte
`+0xF06 & 1` set it also invokes slot `+0x1E8` and increments halfword
`+0xF08`. Later base work conditionally addresses the fighter-override bank.
The derived `ccSkillComboBase` constructor live `0x00797250` replaces the
table with `0x005FB240`; its phase-3 slot is live `0x0079B4F0`. That
override checks the authored descriptor, dispatches selected slots
`+0x274/+0x230`, consumes latch byte `+0x10B8` through slot `+0x24C`,
then calls the base phase-3 method. Thus neither a shared controller nor
the empty base final callback makes all concrete skill tails empty.
The final wrapper still marks
primary/subordinate flag states and performs the separately owned combo
maintenance even when the selected slot `+0x120` is empty.

The subordinate base is `ccSkillObj`: constructor live `0x0077ED00`
installs table `0x005FB920` at node `+0x50`; the RTTI name is at live
BTL `0x008AE638`. Live `0x00781F20` derives `ccSkillDmyPlayer` with
table `0x005FB7D0` (table writes at Ghidra `0x0077ECC0..0x0077ED6F` and
`0x00781EE0..0x00781FAF`). Two concrete registered samples are
`ccSkillPlayerBlowWatch` (`0x005FAF10`, allocation `0xBA0`) and
`ccSkillHKG001Wall` (`0x005F84C0`, allocation `0xDF0`). Their allocation,
table installation and registration are joined by bytes at Ghidra
`0x0079F650..0x0079F720` and `0x007B5480..0x007B5588`; their literal
names resolve through RTTI at Ghidra `0x008D0220/0x008CFF98` to
`0x008BC520/0x008BC380`. These joins identify internal classes without
assigning an unproved move name.

Both samples retain the base service wrappers at slots `+0x5C/+0x60/+0x64`:
live `0x00781090/0x007812B0/0x00781320`. Their ordinary phase-1 path
uses node update bit `+0 & 2`, updates two binding records at
`+0x900/+0x990`, and can set byte `+0xAE4 & 1` to suppress the ordinary
late pass while a fractional step or local delay remains. Phase 2 requires
node draw bit `+0 & 4` and calls slot `+0x68`, or `+0x70` for the
alternative state selected by byte `+0xA20 & 1`. The ordinary phase-3 path
requires the update bit and `+0xAE4 & 1` clear, calls slot `+0x48` on
both binding records, invokes class-specific node slot `+0x18`, handles and
clears pending fields `+0x1D4/+0x1DC`, decrements nonzero countdown
`+0xAD0` with slot `+0x80` on reaching zero, and increments `+0xAD4`.
The alternative late path calls slot `+0x74` and increments halfword
`+0xA22`. Thus the service's slot `+0x64` is a wrapper around class work,
not the class's own generic node slot `+0x18`.

The selected late targets differ: `ccSkillPlayerBlowWatch` uses live
`0x0079D9A0`, which checks retained actor `+0xB40` and local flags before
its calls and retirement request through slot `+0x80`; that shared request
live `0x0077F230` sets subordinate `+0x8B0` bit 0.
`ccSkillHKG001Wall` uses live `0x007B44B0`, with a counter-`0x3C`
retirement request, node slot `+0x90`, and local queue/binding maintenance.
The BlowWatch late target continues past its call to the resident
nonnull/session predicate `0x003083A0` (Ghidra `0x0079D960..0x0079DA04`);
its destructor (Ghidra `0x0079D180..0x0079D383`) likewise continues to
conditional writes to retained actor flags, base destruction, and heap
deletion.

The shared slot-`+0x80` retirement request reaches deletion in two stages.
The service's final phase-3 wrapper
turns any nonzero subordinate `+0x8B0` into a bit-1-marked value. The
next eligible phase-1 wrapper calls live `0x00778960` before the ordinary
primary/subordinate dispatch; that routine reaches live `0x0077CE90`,
which destroys bit-1-marked primaries and subordinates and clears their
pointer/serial records. Primaries use `+0x14 & 2`; subordinates use
`+0x8B0 & 2`. This is a bank-level deferred deletion contract, separate
from the pooled effect manager's phase-3 unlinking and from immediate
whole-controller teardown. The selected concrete callbacks do not establish
every bank member's targets, resource ownership or indirect producer set.

The cut-in controller is a separate ownership boundary. Live
`0x0086FCD0` accepts a primary handle only if its side index is `0..1`
and both serial and pointer match the service's primary record. It copies
that triple to child `+0x5F0/+0x5F4/+0x5F8` in a side record of stride
`0x1C0`, selected through the primary's fighter pointer at `+0x31C` and
fighter byte `+0x60 & 1`. The first cut-in phase, live `0x00870270`,
rechecks that handle and resets selected side state when it is no longer
valid. Its separate two-by-four child bank at `+0x7D0` uses virtual
`+0x0C/+0x10/+0x14` for phase 1/2/3; phase 1 destroys a child marked
by `child+0x24 & 1` through slot `+0x20(1)` and clears its bank pointer.
Live `0x00870FD0` inserts into the first empty entry of a selected
four-entry side bank. No concrete producer of that insertion helper was
established by the BTL direct-`jal`/literal-address scans; the children's original
class names and all derived targets remain unresolved.

Live `0x007783A0` destroys service primaries through slot `+0x228(1)`
after slot `+0x18C`, destroys the 32-entry subordinate banks through
vtable-at-object `+0x50` slot `+8(1)`, and clears pointer/serial records.
Cut-in destructor live `0x0086F020` first resets its side state, destroys
every nonnull `+0x7D0` child through `+0x20(1)`, releases its two sprite
objects at `+0x3F0/+0x424`, and tears down its embedded arrays and contexts.
These are distinct deletion interfaces for the primary, subordinate and
cut-in-child groups. General skill outcomes, authored events and contribution
semantics remain with [Match outcomes](match_outcomes.md),
[Ultimate Jutsu](ultimate_jutsu.md), and [Combo accounting](combo_accounting.md).

## Indexed effect pool (ccEffDrawObj)

The `ccEffDrawObjWorkCtrl` pool embedded at `ccEffectManager + 0x41C` hands
out `ccEffDrawObj` records through generation-checked handles. The manager,
its three controllers and their phase callbacks are described in
[Resident effect-manager callbacks and ownership](#resident-effect-manager-callbacks-and-ownership);
this section describes the record handle, binding and retirement contract. Battle
support objects are one traced consumer, described in
[Support mechanics](support_mechanics.md#specialized-descendants-and-release-order).
**Inference:** the BTL export names the owner `iGpffffcd00`, which is
`gp - 0x3300` = `0x006076F0` with the gp value implied by
`0x00607888 = gp - 0x3168`; the offset `+0x41C`, `0x210`-byte records,
constructor `FUN_0030E770` and phase-3 consumer `FUN_0030E020` match that
controller.

**Handles and acquisition.** A record is `0x210` bytes; its index and
generation are `+4/+8`, its occupied byte is `+0x1B1`, and its list links are
`+0x1B4/+0x1B8`. `FUN_0030E130(pool, handle_out)` resets an unused record
through `FUN_0030E8D0`, links it into pool `+4`, assigns a nonzero generation,
and publishes a three-word handle `(index, generation, pointer)`. When the
searched part of the pool has no unused record, the same function can release
and reuse the current list head, replacing its generation, so a held handle
can become invalid while its holder still exists. Traced consumers treat a
handle as valid only when the index is nonnegative and below owner `+0x424`,
the saved generation is nonzero and equals record `+8`, and record `+0x1B1` is
nonzero. Resident leaf `0x003092D0..0x003092E7` resets a handle to
`(-1, 0, 0)`. These checks protect the cached record only; they do not
validate other retained pointers.

**Record callbacks.** Constructor `FUN_0030E770` installs table
`0x005DC830`: `+0x0C -> FUN_003108A0`, `+0x10 -> FUN_00311C60`,
`+0x14 -> FUN_00310A90`. Slot `+0x18` is an unrecognized leaf at
`0x0028BF30..0x0028BF4F` that sets pending-removal mask `0x01` in record
byte `+0x24`; it neither destroys record contents nor clears `+0x1B1`. Slot
`+0x1C -> FUN_00308050` clears that bit during reset. The phase wrappers
`FUN_0030DEE0` and `FUN_0030E020` require record byte `+0x38` nonzero and
`FUN_0030DF80` requires `+0x39`; the nonzero signed delay word `+0x28`
described above can additionally suppress the callback. These gates belong
to the pool, independently of any consumer's own update flags.

`FUN_0030F290(record, descriptor, 1, 0, 0, 0)` allocates and binds a type-`1`
animation player at record `+0x1A0` (type byte `+0x19C`). `FUN_0030F080`
writes a supplied halfword step to the bound player's `+0x94`;
`FUN_0030ED40` seeks the record's animation; render callback `FUN_00311C60`
publishes record scalar `+0x34` to player `+0x88` before `FUN_001BB790`.

**Retirement.** A consumer requests retirement through two concurrent
mechanisms, not one timer:

| Record field | Request and consumer |
| --- | --- |
| Signed halfwords `+0xCA/+0xCC/+0xCE`, byte `+0xC8 & 3` | `FUN_0030F160(record,0,0,N)` writes `(0,0,N)` and selects local phase `2`. With record mask `+0xC4 & 4` set, `FUN_00310A90` subtracts `float(+0x204)/N` from `float(+0x34)` while it is at or below `+0x204`, clamps at `+0x200`, and changes phase to `3` when the lower bound is reached. Phase `3` itself makes no pending-removal call in this block. |
| Byte `+0x1AE`, word `+0x1BC` | The consumer separately writes `(1,N)`. `FUN_00310A90` requires a nonnull record payload at `+0x1A0`, then decrements a positive `+0x1BC` while `+0x1AE` is nonzero. The decrement that reaches zero invokes slot `+0x18`, setting the pending-removal bit. This precedes the local phase calculation. |
| Byte `+0x24 & 1` | After the slot-`+0x14` callback, `FUN_0030E020` tests this bit, calls `FUN_0030EBC0`, unlinks the record and clears both list links. `FUN_0030EBC0` runs the content handler `FUN_0030EC30` and clears occupied byte `+0x1B1`. The pool record allocation remains available for reuse. |

The countdown and phase instructions at `0x00310A90..0x00310C7C` fall through
after the indirect pending-removal call, so `N` is both the local phase
divisor and the initial retirement countdown. For an unchanged nonnull payload
and an otherwise eligible third callback, the `N`th decrement requests owner
removal. These are callback counts, not displayed-frame counts or seconds, and
do not establish a minimum visible survival time.

Earlier removal is possible within the same interface. For payload type
`+0x19C == 1/4`, `FUN_003108A0` advances the bound animation while completion
byte `+0x1AF` is zero. On a later eligible invocation with completion set,
repeat byte `+0x1AC` zero and completion-removal byte `+0x1AD` nonzero, it
sets the same pending-removal bit; a repeated animation instead takes the
seek/restart path. Pool pressure can also recycle the record as above. Reset
`FUN_0030E8D0` initializes `+0x1AD = 1`, clears `+0x1AE/+0x1AF/+0x1BC`, and
selects local phase `3`; resource or other writers of those fields have not
all been audited.

Content retirement has an ownership gate. With record byte `+0x1B0` nonzero
and type `+0x19C == 1/4`, `FUN_0030EC30` destroys the `+0x1A0` player through
`FUN_001B7570(...,1)` and any `+0x1A8` composition through
`FUN_001951A0(...,1)`, clearing both pointers. With `+0x1B0 == 0` it instead
calls seek helper `FUN_0030ED40` and retains those allocations. Constructor
`FUN_0030E770` initializes `+0x1B0` to `1`; acquisition reset and the type-`1`
binding call do not rewrite it. Other writers of that ownership mode have not
all been audited, so clearing occupied byte `+0x1B1` alone does not prove
payload destruction.

Whole-pool destruction `FUN_0030A830` invokes record destructor
`FUN_0030E830` for the allocated records and clears pool base/head/count. That
destructor sets `+0x1B0 = 1` before `FUN_0030EC30`, forcing the
content-destruction path. This route does not wait for any retirement
countdown. The broader playback child contracts belong to
[Scene playback owners](../runtime/scene_playback_owners.md). This indexed
scene-effect pool is distinct from the particle-generator actions owned by
[Effect-generator commands](../runtime/effect_generator_commands.md#removal-and-reset-lifetime).
