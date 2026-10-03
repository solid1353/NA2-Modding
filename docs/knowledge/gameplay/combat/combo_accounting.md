# Combo accounting

Live combo accumulation, interruption, reset and display publication in
unmodified retail NA2 (`SLPS-25837`).

## Research coverage

- **Assigned scope:** fighter-owned live combo counters, accepted-hit producers,
  consumption and reset conditions, interruption, and publication to combo
  presentation; the auxiliary per-side contribution route and its mask
  selection; the `ccSkillHNW001` contribution gate; and selected projectile
  attribution arguments.
- **Exploration depth:**
  - Complete resident count/update helper family and its direct caller.
  - Twelve resident result-publication sites and four direct BTL pending-byte
    producers.
  - The `ccSkillHNW001` contribution helper, its gate-field producers and the
    shared input producer.
  - Complete auxiliary maintenance/flush branches, request-mask setters and
    the concrete mask owners listed below.
  - Presentation increment and reset entries.
  - One concrete projectile contact caller for its attribution argument.
- **Confirmed coverage:** side-keyed ownership, signed accumulation, 90-unit
  rearming, update order, exact reset/retention predicates, independent
  pending-byte clearing, accepted-result attribution, repeated-event gates,
  full-count versus single-result auxiliary routing, paired mask acquisition
  and release, and a separate clamped running display count that retains its
  digits after a gameplay reset.
- **Unresolved or untested:** exhaustive indirect callback/writer coverage,
  every collision admission route into the `ccSkillHNW001` accepted-event
  callback, complete projectile attribution callers, auxiliary bank UI
  meanings and all selection paths, later mutations through borrowed record
  aliases, and exhaustive state reachability.
- **Deliberate exclusions and overlap:**
  - [Damage](damage.md) owns HP arithmetic and scaling;
    [Match outcomes](../session/match_outcomes.md) owns result metrics;
    [Hit response](hit_response.md) owns response-state behavior.
  - [Battle HUD](../session/battle_hud.md#combo-digit-presentation) owns combo digit
    binding, fade and draw; [Battle lifecycle](../session/battle_lifecycle.md#fighter-overrides-at-phase-boundaries)
    owns the override bank's layout and application.
  - [Battle entities](../session/battle_entities.md#ccskillhnw001-skill-actor) owns the
    `ccSkillHNW001` actor's identity, creation, state machine and cleanup;
    [Collision](collision.md#ccskillhnw001-interaction-records-and-accepted-event-route)
    owns its borrowed interaction records and accepted-event route;
    [Character assets](../../game/character_assets.md#action-records) owns
    character and action record contracts.
  - [Ultimate Jutsu](../characters/ultimate_jutsu.md) owns its interaction controller.
- **Evidence limitations:** static code and imported data establish operations
  and ordering. They do not establish measured cadence, visible timing or
  exhaustive player-facing reachability. Immediate and direct-JAL scans do
  not exclude indexed stores, retained-pointer aliases or indirect calls.

## Evidence convention

Resident addresses are ELF virtual addresses. For BTL, `L` denotes the live
EE address and `D` the preserved Ghidra address: `L = D + 0x40`, as described
in [Address conventions](../../game/files/file_identities.md#address-conventions).

## Resident owner and update order

Observation: resident `0x0020C270` allocates `0x3C` bytes, constructs through
`0x0020C320`, and stores the result at `0x006076B8 + 4*(fighter[+0x60]&1)`.
This creates two side-keyed owner slots, rather than a per-projectile counter.
The direct construction caller is fighter initializer `0x00214A40`, at
`0x00215624`. Initializer `0x0020C3D0` stores the fighter pointer and clears
the child pointers, both counts, notification phase and timer.

| Owner offset | Stored value or role |
| --- | --- |
| `+0x00` | Owning fighter pointer. |
| `+0x04` | Side's combo presentation child. |
| `+0x08/+0x0C` | Other root presentation children, resolved independently. |
| `+0x10..+0x33` | Resident timer, with current integer at owner `+0x1C`. |
| `+0x34` | Signed-halfword current count. |
| `+0x36` | Signed-halfword largest completed count. |
| `+0x38` | Independent presentation/action notification phase. |

Fighter cleanup `0x00215720` resolves the same side slot and frees its
non-null owner, then clears the slot (`0x00215818..0x00215860`). Its local
timer teardown resets the timer vtable at owner `+0x30` before freeing the
owner; it does not free the three borrowed presentation children here.
Session/root teardown remains owned by
[Battle lifecycle](../session/battle_lifecycle.md#teardown-order).

`0x0020C420` obtains each missing child in order and returns immediately after
each lookup, including a successful lookup. Its lookup calls are live BTL
`0x006B3FB0/0x006B4050/0x006B4000`. Count processing therefore waits until
all three pointers were present on entry; a first lookup does not proceed
straight into accumulation.

The only named resident direct caller is `0x0024DE40` at `0x0024DEB0`.
Instruction range `0x0024DE58..0x0024DEC8` loops over both owner slots only
when the callback fighter has byte `+0x63` bit `0` clear, side bit `+0x60&1`
zero, and byte `+0x00` bit `1` set. The calls precede that callback's
`+0x61` bit-`4` early return and positive hit-stop `+0x20C` gate. Thus those
two later gates do not themselves suppress the combo update. This is local
ordering evidence, not a measured invocation rate.

Once all children are available, the manager performs this sequence:

1. If timer current `+0x1C` is nonzero, call `0x00211E70` with literal float
   `1.0` and owner `+0x10` (`0x0020C4DC..0x0020C4F8`).
2. Consume signed pending byte `fighter+0xA45` when nonzero and fighter
   `+0x62` bit `0` is clear. Send the signed delta to the presentation child,
   add it to signed current `+0x34`, arm timer for `90`, and clear the pending
   byte (`0x0020C4FC..0x0020C578`). No saturating count check occurs here.
3. If the resulting current is greater than one, publish the related event;
   then evaluate reset/retention (`0x0020C57C..0x0020C6B8`).
4. Publish a changed high-water statistic for a remaining nonzero count, then
   run the independent presentation/action notifications in the function tail.
   [Match outcomes](../session/battle_statistics.md#accepted-ninjutsu-and-combo-flushing)
   owns the statistic banks and their uses.

The apparent zero-delta fallback at `0x0020C528..0x0020C544` is unreachable
through this straight-line entry: signed byte `+0xA45` was already checked
nonzero and sign-extended into `a1` before the second comparison. The actual
nonzero route at `0x0020C54C` retains that signed delta as the second argument
to live BTL `0x006B6C30`; the decompiler omits it from the displayed call.

## Retention and reset

Observation: let `owner` be the combo object, `attacker = owner[+0x00]`, and
`defender = attacker[+0x20]`. The complete disassembly
`0x0020C5A0..0x0020C6B8` establishes:

```text
keep = (action_getter(attacker) == 1 or action_getter(attacker) == 3)
       and defender byte +0x61 has bit 7
free = defender (major, substate) is neither (0,6) nor (0,7)
       and defender word +0x254 == 0
       and eligibility_00228260(defender) != 0
reset = not keep and ((current != 0 and timer_current == 0) or free)
```

`eligibility_00228260` allows major `0` only for substates `0/3/4/5`, rejects
majors `5..8`, and retains its initial nonzero value for other majors. Either
defender halfword `+0x9F0 != 0` or global query `0x0022D5B0() != 0` rejects
eligibility. These are exact code predicates; state names and every possible
gameplay route into them are not established.

The retained-action getter is resident `0x00217860`, not an unconditional
read of `+0xA3C`. Outside major `8` it returns `-1`. In major `8`, selected
indices outside `0..3` pass through; indices `0/1` use selector `+0x184`,
indices `2/3` use `+0x186`. Selector value exactly `1` returns `-1` for
either pair. Otherwise, an odd `+0x184` maps `0/1` to `2/3`, while an even
`+0x186` maps `2/3` to `0/1`. The `keep` predicate therefore follows the
resolved configured slot, not merely the raw selected index.

A reset calls live BTL `0x006B6BF0`, raises owner record `+0x36` only if
current is larger, and clears current `+0x34`. It leaves pending byte and
timer untouched. `free` can therefore clear a newly consumed count during
the same manager call, and can invoke presentation reset while current is
already zero. Conversely `keep` prevents both timeout and `free` resets.

## Explicit and pending updates

Resident `0x00239230(fighter, delta)` performs byte-width addition into
`fighter+0xA45`, without a cap or positivity check. The manager later reads
that byte with `lb`. `0x002391D0(fighter, result, flag)` calls it with `1`
only when `result == 1` and `flag != 0`; it also writes distinct result bytes
`+0xA40/+0xA42/+0xA43/+0xA44`, which are not the combo count.

Resident `0x0020C2E0(side, delta)` resolves the side slot and, if non-null,
calls `0x0020CD40(owner, current+delta)`. The setter truncates to a halfword
and acts only with a resolved `+0x04` child, non-null owner fighter, and
fighter `+0x62` bit `0` clear. It sends display increment `1`, stores the
supplied current count, and rearms/publishes the high-water path only when
that supplied halfword is nonzero. The display input is therefore **not**
the supplied current or delta on this explicit path. A zero setter does not
rearm the timer or archive `+0x36`.

### Pending-byte lifetime and accepted-result attribution

The pending byte is temporary event accounting. Besides constructor clear
`0x00214FE8` and manager consumption clear `0x0020C578`, the common fighter
update `0x0024C440` clears it at `0x0024CB30`. The complete decompilation
and instruction tail place this clear outside the node-bit-`1` update block
and after the hit-stop block. It is not conditioned on the manager having
consumed the byte. Therefore a byte skipped under the manager's
`+0x62` gate or unresolved-child gate is not established as durable queued
work: a later eligible call to that fighter callback clears it independently.
[Battle lifecycle](../session/battle_lifecycle.md#phase-3-and-the-final-collision-boundary)
owns the broader phase ordering.

An exact-immediate scan for displacement `0xA45` in resident code finds seven
aligned direct field sites: manager reads/clear
`0x0020C4FC/0x0020C558/0x0020C578`, construction clear `0x00214FE8`, helper
read/store `0x00239230/0x00239238`, and callback clear `0x0024CB30`. This
bound does not exclude indexed or aliased writes.

Pair resolver `0x0021F610` reports its result to the **initiating** fighter
through `0x002391D0(initiator,result,1)` at `0x0021F94C`. Its ordinary
accepted route assigns result `1`; guarded route assigns `-1`; its successful
substitution branches replace that result with `-2`. Earlier rejected
branches return before publication. The manager's pending producer therefore
does not equate every collision or every damage event with a combo hit.
The resolver also has a branch assigning `1` when `0x00240990` returns zero;
its full eligibility and response meaning belong to
[Hit response](hit_response.md), rather than being inferred here as a newly
named damage category.

The eleven other named resident direct callsites to `0x002391D0` all pass
`(fighter,1,0)`, so they publish the separate outcome byte without incrementing
the pending count. Their instructions immediately preceding the calls
establish this distinction across character callback variants:

| Containing function | Callsite |
| --- | --- |
| `0x00258340` | `0x0025891C` |
| `0x0025B1E0` | `0x0025B5B0` |
| `0x0025DEF0` | `0x0025E4DC` |
| `0x00264E20` | `0x00265A74` |
| `0x00275600` | `0x00275FAC` |
| `0x00289AC0` | `0x00289CD4` |
| `0x002B5250` | `0x002B6650` |
| `0x002C0A30` | `0x002C0D30` |
| `0x002E5730` | `0x002E5810`, `0x002E5FB4` |
| `0x002F0520` | `0x002F0ABC` |

No character/move name is assigned solely from these numeric callback
addresses. [Character action callbacks](../characters/character_action_callbacks.md) owns
character callback bodies and their identities.

### Other direct byte producers

A direct-JAL scan of BTL for resident `0x00239230` finds exactly four calls,
all passing delta `1`:

| Imported callsite / live callsite | Established path |
| --- | --- |
| `D0x00730598 / L0x007305D8` | Common projectile virtual slot `+0x34`, entry `D0x00730560 / L0x007305A0`: skip when object byte `+0x28C == 1`; otherwise sign-extend the incoming second argument to 16 bits, resolve resident primary-fighter getter `0x003769C0`, and add one if it returns non-null. |
| `D0x0079FEE8 / L0x0079FF28` | Actor path resolves side through object `+0x350`, then uses battle primary slot `+0xDE4+4*side`. |
| `D0x007D4598 / L0x007D45D8` | Same primary-side attribution as the preceding actor path. |
| `D0x0085EA78 / L0x0085EAB8` | Conditional multi-event `ccSkillHNW001` contribution, described below. |

Resident getter `0x003769C0` returns battle manager `+0xDE4` for argument
`0`, `+0xDE8` for `1`, and zero otherwise. Projectile byte `+0x28C` is an
independent skip flag, not the getter's side argument. Instructions
`D0x00730578/0x0073057C` are `dsll32 a0,a1,0x10` and
`dsra32 a0,a0,0x10`, preserving the signed-halfword incoming side.
The common initializer clears the skip byte at `D0x0072B7A4`; the
common state-machine's child-spawn continuation writes it to `1` on the new
child at `D0x0072DCB4`, corroborated with bytes
`D0x0072DCA0..0x0072DCEF`. This suppresses that child's future common
pending-count publication through this slot. Complete callback-invocation
and indirect-writer coverage remains unresolved.
[Projectile motion](../projectiles_and_items/projectile_motion.md#representative-callback-composition)
owns the projectile root slot table, including slot `+0x34`.

One concrete caller supplies the side without reading projectile `+0x8A`.
The true entry is `D0x0072E700 / L0x0072E740`; its prologue retains
`a0` as projectile and `a1` as contacted fighter. Complete instruction
continuation `D0x0072E740..0x0072EBD8` reaches the projectile table at
`+0x50`, slot `+0x34`, at `D0x0072E7E4` only when contacted fighter
signed halfword `+0x95A` is zero. It passes the projectile as `a0` and
the signed-halfword form of `(fighter[+0x60]&1)^1` as `a1`.
Consequently this caller credits the primary fighter opposite the contacted
fighter. Optional direct damage joins before this gate, so taking that
damage branch is not required for this publication. Later affiliation and
callback-`+0x40` gates in the same body do not guard the earlier `+0x34`
call. [Projectile contact](../projectiles_and_items/projectiles.md#hit-and-despawn-evidence) and
[Damage](damage.md#shared-wrapper-and-combo-call-contracts) own the broader
contact and HP contracts. Other callers remain outside this concrete join.

The two actor calls occur after their optional accumulated-count flush and
optional direct damage, regardless of whether the direct-damage branch was
taken. Instruction bytes `D0x0079FE84..0x0079FEEF` and
`D0x007D4534..0x007D459F` corroborate the continuation across resident
`0x003083A0`, which Ghidra incorrectly treats as nonreturning.
[Damage](damage.md#all-fifteen-btl-source-retaining-calls) owns the source
records, class joins and HP path; the byte producer is outside that wrapper.

The separate resident producer `0x00233540(fighter,flag)` resolves
`paired=fighter[+0x20]` and adds one to **paired** pending byte when `flag`
is nonzero and paired signed byte `+0xB58` is neither `0`, `-1`, nor `-2`.
It first notifies the opposite-side BTL child at live `0x00889360`.
This receiver-side attribution differs from ordinary pair-resolver publication.

The three named direct callers of `0x00233540` are in hit router
`0x002209A0`. Call `0x00220C98` passes zero and cannot produce a count.
Successful substitution writes paired `+0xB58=-2` before call
`0x00220D04(flag=1)`, so the helper's signed-result gate prevents its count.
The ordinary branch writes paired `+0xB58=1`, calls receiver hit handling,
then reaches `0x00220E20(flag=1)`; a guarded branch reaches the same helper
join after guarded-hit handling. These are direct call-order observations;
the shared router and response predicates are owned by
[Hit response](hit_response.md#accepted-hit-routing).

### Repeated-event contribution in `ccSkillHNW001`

`ccSkillHNW001` (resident table header `0x005E2020`) is the skill actor
created for Hinata's (character ID `80`) action **守護八卦六十四掌**:
selector `161` maps to resource `165` (`2hnwcha1.ccs`), and an authored
animation event creates it through factory index `0xA5`.
[Battle entities](../session/battle_entities.md#ccskillhnw001-skill-actor) owns that
identity join, creation, local state machine and cleanup;
[Collision](collision.md#ccskillhnw001-interaction-records-and-accepted-event-route)
owns its borrowed interaction records and the accepted-event route into its
receiver.

The producer is imported `0x0085E9C0` / live `0x0085EA00`. It permits
work when no valid linked target with nonzero target halfword `+0x95A` is
present; the link uses object flag `+0x539`, pointer `+0x4CC`, and resident
predicate `0x003083A0`. It then requires both bytes `+0x1176/+0x1177` zero
and event latch `+0x1175` nonzero. For signed old halfword `+0x1170 < 8`,
it adds one to that halfword only. At old value `>=8`, it adds two to that
halfword and publishes **one** pending hit to the primary fighter selected
by side `+0x350`. It clears event latch `+0x1175` after either accepted
branch. An early gate return does not clear that latch. Its only direct BTL
call is at `D0x0085E520`, within a direct-JAL scan bound.

The gate fields have these producers (imported byte ranges):

| Imported evidence | Established contribution lifetime |
| --- | --- |
| `0x0085CE10..0x0085CEA3` | Returning initializer clears halfwords `+0x1170/+0x1172` and bytes `+0x1174..+0x1177`. |
| `0x0085D090..0x0085D123` | Activation/resource setup separately clears those same fields. |
| `0x0085D970..0x0085DD9F` | Event receiver sets `+0x1176=1` and returns when `+0x1177==1`; old count `>=32` also returns. The continuing linked-target route writes either target statistic `3` for no guard or statistic `9` for guard, then sets latch `+0x1175=1`. It can set `+0x1174=1` from its descriptor-field comparison. |
| `0x0085E400..0x0085E58B` | Update state-`2` branch increments `+0x1172`, requires `+0x1174==1`, no valid guarded target, and positive `+0x14A` before clearing `+0x14A` and invoking the producer. It clears `+0x1174/+0x1172` before that call. |
| `0x0085E9C0..0x0085EA97` | Entire contribution helper, including the skipped linked-target continuation and real returning epilogue. |

Local state `4` stores `+0x1177=1`; a later receiver invocation then sets
`+0x1176=1` and returns before producing the counting latch. Thus `+0x1177`
is a locally selected later-phase gate and `+0x1176` its receipt
acknowledgement; neither is an independent pending-hit producer. The state
sequence that reaches the counting branch is described in
[Battle entities](../session/battle_entities.md#ccskillhnw001-skill-actor).

The same activation/setup function has a separate display reset at
`D0x0085D910 / L0x0085D950`. Bytes
`D0x0085D8F8..0x0085D927` show it obtaining the side's presentation child,
clearing its running count when non-null, and then selecting local state
`0`. It does not call resident current-count reset/setter at this site.

### Shared input producer of the contribution gate

Observation: common helper `D0x00796840 / L0x00796880` is the producer
of halfword `+0x14A` consumed by HNW state `2`. Complete bytes through
`D0x0079690F` require actor input object `+0x144` nonnull and byte
`+0x150` nonzero. When predicate `L0x00796A50 / D0x00796A10`
succeeds, the helper increments both unsigned halfwords `+0x148/+0x14A`
with halfword stores and clears age halfword `+0x14C`. A separate aging
branch operates only when both `+0x14E` and `+0x14A` are nonzero:
it increments `+0x14C` while below `+0x14E`, otherwise clears `+0x14A`.

HNW activation clears all four halfwords and initializes the `0x14`-byte
input object. Therefore its `+0x14E=0` leaves that age-based clearing
disabled until another writer changes it. Update state `0` enables byte
`+0x150` and the input object's byte `+0x00` when local counter `+0x04`
equals `5` (`D0x0085E340..0x0085E384`). State `1` consumes positive
`+0x14A` by clearing it and local halfword `+0x1172`; state `5` disables
the input object and `+0x150` (`D0x0085E264..0x0085E280`). Thus a
counting-state event latch alone is insufficient: the producer also waits for
this independently accumulated input gate.

Predicate bytes `D0x00796A10..0x00796ACF` distinguish a valid linked
fighter's alternate control branch, which returns actor `+0x13C&1`, from
the ordinary side-input branch. The latter obtains a side-specific record
through resident `0x001F3F10(side+1)` and intersects that record's signed
halfword `+0x02` with the logical input word at input-manager
`+0x84+side*0x78`; a missing record returns false.
[Action commands](action_commands.md#logical-mask) owns that
input domain. The intersection does not identify a fixed physical button.

The inherited primary callback at table slot `+0x124`, resident
`0x005E2144`, points to `L0x007950D0 / D0x00795090`.
Its complete returning body calls the input helper at `D0x00795120`
after its ordinary virtual work; nonzero actor byte `+0x1C0` selects another
virtual branch and skips that ordinary route. This supplies a concrete
indirect invocation route without claiming one increment per frame or a
measured order between every HNW update and input callback.

## Per-side accumulated contribution route

The auxiliary context has another pending **word** at `+0x3268+4*side`
and countdown word at `+0x3270+4*side`, distinct from the fighter byte.
[Match outcomes](../session/battle_statistics.md#accepted-ninjutsu-and-combo-flushing)
owns the completed 19-site flush inventory and metric publication, including
the accepted-event writers. That inventory is not repeated here.

The maintenance entry `L0x00777DD0 / D0x00777D90` was inspected through its
entire returning byte range `D0x00777D90..0x00777F4B`. Ghidra's early
nonreturning call is live `0x007063E0`, actually a returning getter at
`D0x007063A0..0x007063AF` that returns the override bank pointer, live BTL
BSS `0x008D6A10`. The bank's three two-side channels, trailing record and
phase application belong to
[Battle lifecycle](../session/battle_lifecycle.md#fighter-overrides-at-phase-boundaries).
The maintenance routine loops over exactly two sides and obtains the side's
combo display through live `0x006B3FB0`; a null display skips that side.

Let `bank` be that getter's result. Live `0x00706CA0` is imported returning
leaf `0x00706C60..0x00706C97`; it validates side `0..1` and returns whether
`bank+0x0C+8*side` is nonzero. The two branches are:

- With that gate **nonzero**, obtain an auxiliary actor through the manager
  at global `0x00607844` when available, otherwise use action identifier
  `-1`. Live predicate `0x007069F0` (imported
  `0x007069B0..0x007069CB`) returns `bank[+0x38]!=0` only while
  `bank[+0x3C]!=0`; otherwise zero. When this predicate is zero and the
  resolved actor identifier is not `0x20`, decrement a nonzero context
  countdown; if it is already zero, reset the side's presentation running
  count. Otherwise call the full-count flush entry.
- With the gate **zero**, a positive context pending word resolves the
  corresponding primary fighter, calls `0x002391D0(fighter,1,1)` when the
  fighter exists, and clears the context word. This publishes exactly one
  pending-byte increment, rather than forwarding the word's magnitude. It
  does not decrement the countdown in this branch.

The full-count flush is `L0x00778000 / D0x00777FC0`. Complete bytes through
`D0x0077806B` show that a positive word calls resident
`0x0020C2E0(side,word)` and then publishes its result metrics before clearing
the word. A nonpositive word is also cleared. The explicit setter's
presentation increment remains `1` even when the accumulated word is larger.
The reset call in the other maintenance branch changes presentation only;
it does not directly clear resident manager current `+0x34`.

Direct-JAL scans find the resident display increment calls at
`0x0020C530/0x0020C550/0x0020CD94` and no BTL calls to that increment entry.
Display reset has resident call `0x0020C698` and BTL calls
`D0x00777E7C/0x0085D910`. This confirms all direct callers within that scan
bound, rather than excluding indirect publication or reset.

These are numeric predicates and routing operations. The UI meanings of the
bank fields and every path selecting them are not established here.

### Request-mask producers and retained values

Observation: `bank+0x08+8*side` is a requested byte paired with request
mask word `bank+0x0C+8*side`. Its role as a phase-applied fighter override
and the session reset belong to
[Battle lifecycle](../session/battle_lifecycle.md#fighter-overrides-at-phase-boundaries).
For the combo maintenance consumer, a nonzero mask selects the full-count
route regardless of the byte's value.

Setter `D0x00706B10 / L0x00706B50` takes `(bank,side,value,mask)`.
For side `0..1`, it accepts an empty record or one whose stored byte equals
the new value, writes the byte, and ORs the supplied mask into the word.
It leaves an occupied record with a different byte unchanged. Release
`D0x00706BB0 / L0x00706BF0` removes only intersecting supplied mask
bits; when the resulting mask is zero it clears both fields. It then
reapplies the bank through live `0x007065E0`. Bytes
`D0x00706B10..0x00706C97` corroborate the complete setters, returning
epilogues and gate leaf. A release does not decrement a reference count:
ownership is represented by the mask's bits.

The trailing pair similarly consists of requested byte `+0x38` and mask
word `+0x3C`. Leaves `D0x00706960..0x007069CB` establish that
live `0x007069A0(bank,mask)` ORs the mask and stores byte `1`, while
live `0x007069C0(bank,mask)` clears the supplied bits and clears the byte
only when no bits remain. The maintenance query returns false whenever
the mask is zero; otherwise it returns whether the byte is nonzero.
These operations explain retention across multiple owners without assigning
a player-facing name to this pair.

`ccSkillHNW001` supplies a concrete producer of the side masks. Complete
bytes `D0x0085EAA0..0x0085EE67` show local helper
`L0x0085EAE0(actor,flag)` obtaining the shared bank through
`L0x007063E0`. With nonzero `flag`, it requests byte value `0` for the
actor's side with mask `side+1`, and for stored opposite side `+0x500`
with mask `actor_side+1`. With zero `flag`, it releases those same mask
bits. Both branches also alter the linked fighters' flag bit `+0x00:1`
directly when their pointers are nonnull. Local state `3` acquires these
requests; state `4` releases them. Consequently even the request with byte
`0` can select the maintenance full-count branch while its mask survives.
The helper pauses/restores the admitted child animations separately; those
resource operations do not write a combo count.

### Trailing-mask owners and inherited callbacks

Observation: primary table callbacks `+0x210/+0x214`, which `ccSkillHNW001`
inherits at resident `0x005E2230/0x005E2234`, point to acquire
`D0x00794370 / L0x007943B0` and release
`D0x00794480 / L0x007944C0`. Acquire requires the battle manager and
bank to exist, adds mask `actor_side+1` to trailing word `+0x3C` through
`L0x007069A0`, and sets actor byte `+0x592=1`. Release requires that
latch as well as the battle manager, removes the same mask through
`L0x007069C0`, and clears the latch. Complete returning byte bodies
`D0x00794370..0x0079447F` and `D0x00794480..0x00794597`
corroborate the branches omitted by Ghidra.

The pair also acquires/releases value `1` in the bank's third per-side
channel for the actor's side and stored opposite side, using the same
actor-side mask. It sets linked fighter `+0x61` bit `7` on acquisition and
uses the low bit returned by resident predicate `0x003083A0` for that bit
on release. Bytes `0x003083A0..0x003083CB` show that predicate returning
only `0` or `1` from pointer/global eligibility, without reading the
fighter's `+0x00`. The release's guarded continuing path therefore also
sets bit `7`; it does not restore a saved fighter flag here. These are
control requests at an inherited callback interface; they do not establish
the player-facing meaning of the trailing byte or every higher-level caller
selecting those slots.

For `ccSkillHNW001`, common binding supplies a concrete selection path.
Primary slot `+0x204` points to returning leaf `D0x00793F00 / L0x00793F40`:
it returns whether the first fixed definition's byte `+0x04` is nonzero.
HNW's byte is zero (`D0x008ACAD4`), so binding takes its zero-result
branch and invokes slot `+0x208` with flags `-1` at
`D0x0078E8D4`. The inherited target
`D0x00793F60 / L0x00793FA0` records the flags at auxiliary owner
`+0x32D0` when available and dispatches slot `+0x210` for flags bit
`0`; thus this binding acquires the actor-side trailing request. Other
flag bits select separate control callbacks, whose broader behavior is
outside the combo interface. It also sets actor byte `+0x591=1`.

Paired inherited cleanup slot `+0x20C` points to
`D0x00794110 / L0x00794150`. Its complete bytes through
`D0x00794363` clear owner `+0x32D0`, perform linked descriptor cleanup
when eligible, and invoke slot `+0x214` at `D0x007942DC` before clearing
`+0x591`. The release callback's own `+0x592` gate remains independent
of that dispatcher. This proves a concrete acquisition/cleanup interface;
every caller and simultaneous owner combination remain unresolved.

Exact direct-JAL searches for the trailing acquire/release leaves each find
two BTL sites: acquire at `D0x007943B0/0x007BAA80`, release at
`D0x007944CC/0x007BAD6C`. The second actor family has no assigned
player-facing identity. Separate bank-wide wrapper
`D0x007067A0 / L0x007067E0` ORs mask `0x1000` into trailing `+0x3C`,
sets byte `+0x38=1`, and requests first-channel value `0` and
third-channel value `1` for both sides under that same mask. Its paired
release at `D0x00706830 / L0x00706870` removes those mask bits.
These distinct request owners show why a local release need not clear the
maintenance gate while another mask survives. The bank-wide acquire has one
direct BTL call, `D0x0077A988`, in the pair-controller body beginning
`D0x0077A870`. Its local continuation obtains the bank, calls only when
nonnull, and then changes both primary fighters' flag bytes. This
establishes one caller without assigning the controller an unproved UI name
or completing its earlier admission gates.

## Separate presentation count

Observation: live BTL increment `L0x006B6C30` is imported function
`D0x006B6BF0`. It adds its signed integer delta into presentation word
`+0x08`, then clamps that word to `0..255`. Only a result greater than one
copies it to display latch `+0x0C`, sets active byte `+0x01`, restarts the
appearance values, writes hold countdown `+0x20 = 10`, and resets the
associated render child. A one-hit count alone does not start this branch.

Live BTL reset `L0x006B6BF0` is absent as a named imported function.
Bytes `D0x006B6BB0..D0x006B6BE7` show a complete returning leaf:
`sw zero,8(a0)`, set comparison register zero, range-check/clamp that zero,
and `jr ra`. It clears presentation running count `+0x08` while leaving
display latch `+0x0C` and active byte `+0x01` intact. Presentation can retain
the completed digits after the gameplay current becomes zero.

The side lookup that supplies manager `+0x04`, the fade and shake update,
and the draw's latched-count color/scale rows and positions are described in
[Battle HUD](../session/battle_hud.md#combo-digit-presentation). The draw reads latched
word `+0x0C`, so resetting only `+0x08` does not erase the shown result, and
the fade does not inspect owner current `+0x34` or the 90-unit timer.

## Remaining static leads

- The complete invocation and second-argument sources for projectile virtual
  slot `+0x34` remain to be mapped beyond the concrete common contact join.
  An exact instruction search for `lw t9,0x34(t9)` finds seven BTL sites;
  some use a primary actor table at `+0x110`, rather than the projectile
  table at `+0x50`. That count is not a projectile callback census and
  excludes other register encodings and computed slots.
- Complete collision admission into the `ccSkillHNW001` accepted-event
  callback, all state-`2` entries, later borrowed-record mutation and
  simultaneous reuse remain open. The authored marker and local call
  counters do not establish visible cadence.
- Auxiliary masks have concrete setters, HNW selection, inherited paired
  callbacks and a bank-wide request caller. Every indirect owner, alternative
  selection path and UI meaning remains unresolved; mask retention alone
  does not assign a player-facing name to the bank fields.
