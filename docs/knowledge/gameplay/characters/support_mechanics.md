# Battle support mechanics

This note reconstructs the resident/BTL boundary for ordinary battle support
characters in retail NA2 (`SLPS-25837`). It covers request gates, the support
gauge, per-side selection state, lifecycle variants, support-hit bookkeeping,
and teardown. Support-object allocation, side slots, the common object prefix
and the factory's class table belong to
[Battle entities](../session/battle_entities.md#dynamic-support-object-owner). The two
support-owned indexed-effect handles are described here; the generic pool they
borrow from belongs to
[Battle lifecycle](../session/battle_auxiliary_services.md#indexed-effect-pool-cceffdrawobj).

## Research coverage

- **Assigned scope:** ordinary battle support-character behavior in the
  resident ELF and BTL overlay: pre-battle support selection, the per-side
  selector byte whose UI is Practice's Linked Mode row, manual summon and
  re-request gates, gauge-backed availability, support-object state
  transitions, notification bookkeeping, scheduled manager passes, and
  teardown. The selected code-`0x0A/0x3F` resource scripts and indexed-effect
  handles are covered through their support-owner interfaces.
- **Exploration depth:** static analysis of the retail images. The resident
  request/update chain (`FUN_002151E0`, `FUN_00238340..FUN_00238950`,
  `FUN_0024DA50`) and subsystem entry, transition and dispatch functions were
  traced completely. Every BTL reference to the manager singleton, every row of
  the selection, object-code and recharge tables, every direct call of the
  candidate resolver, and all 14 final factory vtables with their shared and
  overriding state slots were audited. Teardown, gauge-delta writers, BSS
  counters, the direct-hit notification route, specialized destructors, the
  contact-exit predicate, and the selected `BIN_new1scr_atk` /
  `BIN_ymt1scr_atk` scripts were followed through raw instructions where
  decompilation was incomplete.
- **Confirmed coverage:** a two-side manager with one active object per side;
  deterministic setup-time selection with candidate `0` used for the actual
  `0x26` replacement; one resolved object code and recharge class per side;
  exact resident input, gauge and coordinator-state request gates;
  recharge/drain arithmetic and ordering; the object-local active re-request
  latch; all request return states; the three scheduled manager passes; the
  common zero-gauge-to-terminal chain; the animation result and state
  transitions shared by every factory class; automatic requests selected by
  Linked Mode Auto; the two damage-related gauge recipients; attack-entry and
  deduplicated notification counters; the resident direct-hit notification
  route; the temporary paired-transition reset/disable; the contact-list
  activation countdown; specialized descendant cleanup; the two indexed-effect
  handle release policies; the selected scripts' command routes and borrowed
  scene-name bindings; and both natural and enclosing-subsystem teardown.
  Useful negative results include no runtime rotation among three candidate
  members, no second ordinary-support slot, and no independent resident
  cooldown counter in the audited path.
- **Unresolved or untested:** every support subclass's attack payload, emitted
  effects and resource-script events; the battle meanings of the pass-1 global
  predicates; the runtime frequency of direct-hit notifications and the
  lifetime safety of retained hit-source pointers; character names for
  support-list and object-code IDs; resource-specific animation lengths; and
  the indexed effects' complete outer scheduling and authored animation event
  streams.
- **Deliberate exclusions and overlap:** support-object allocation, side slots,
  the common prefix, the factory class table and the identifier allocator
  belong to [Battle entities](../session/battle_entities.md#dynamic-support-object-owner);
  the Linked Mode row and its snapshot/restore belong to
  [Practice mode](../modes/practice_mode.md#rows-local-values-and-manager-storage); the
  support-gauge display belongs to [Battle HUD](../session/battle_hud.md#support-gauge);
  the generic indexed effect pool belongs to
  [Battle lifecycle](../session/battle_auxiliary_services.md#indexed-effect-pool-cceffdrawobj);
  hit routing to [Hit response](../combat/hit_response.md); retained hit sources to
  [Target selection](../combat/target_selection.md); projectile contact to
  [Projectiles](../projectiles_and_items/projectiles.md); damage calculation to
  [Battle damage](../combat/damage.md); the Extra Hit transition caller to
  [Combat action execution](../combat/combat_action_execution.md#continuation-and-common-exit-decisions).
  Battle AI, statuses, outcomes and Adventure were not used.
- **Evidence limitations:** no live-memory capture or runtime request trace
  was used, so update ordering and invocation counts are static facts, while
  wall-clock durations, visible animation timing, scheduler frequency, and the
  runtime behavior of unreachable or extreme allocator states remain
  unvalidated.

## Evidence identity and address conventions

Address forms follow
[Standard game file identities](../../game/files/file_identities.md#address-conventions);
"export" below means the preserved Ghidra address (live minus `0x40`). `FUN_`
names are synthetic labels; RTTI names explicitly identified below are retail
strings. Timing is stated in update calls rather than seconds.

## Ownership model

Support state is split across three owners:

1. The resident global pointer slot at live `0x00607600` holds the battle setup
   object that supplies the selected-side records. The resident fighter object
   owns the gauge and request input.
2. A BTL-owned `0x24`-byte two-side manager is heap allocated. Its pointer is
   held in the resident/global slot at live `0x00607888` (`gp - 0x3168`; the
   export calls it `iGpffffce98`).
3. The manager owns at most one active support object per side. Those two
   pointers are manager `+0x04` and `+0x08`.

The manager's retail class name is `ccBuddyAtkCtrl` (string at live
`0x008BFD70`, raw `0x20BE70`); its embedded identifier allocator is
`ccBdySerialNo`. Its RTTI chain, field layout, constructor defaults and
identifier allocator belong to
[Battle entities](../session/battle_entities.md#separate-owner-and-exact-side-slots); the
table and destructor ABI belong to [Overlay ABI](../../runtime/overlay_abi.md).
Behaviorally relevant here: both side records start as `{0, 1, 0}`, and
manager byte `+0x20` is a one-shot pass-1 flag that starts at `1`.

This is a direct two-side owner, not a scan through the game's generic entity
population. A raw-store audit of the manager region, cross-checked against
every BTL reference to the singleton, found only four active-slot mutation
paths: constructor clear (the loop store is live `0x00886D0C`, raw
`0x1D2E0C`), a successful request store (live `0x008876C8`, raw `0x1D37C8`),
pass-1 terminal clear (live `0x00887160`, raw `0x1D3260`), and the shared
explicit delete/clear routine. Other singleton references read a slot or side
metadata; they do not install or replace an active object.

The side record fields currently established are:

| Side-record byte | Proven use |
| --- | --- |
| `+0` | Support color variant `0..2`. Battle setup derives it from the two selected support identities, the two primary-fighter identities, and the primary fighters' color indices. A support object's resource path reads this byte; nonzero variants `1` and `2` request an alternate resource through virtual `+0x68`. |
| `+1` | Linked Mode: Manual (`0`) / Auto (`1`), the Practice row-4 setting described in [Practice mode](../modes/practice_mode.md#rows-local-values-and-manager-storage). It is initialized to `1` (Auto), read by BTL live `0x00882630`, and written by live `0x00882670`. Value `1` also enables automatic attack requests in common object state `1`. When an active support object exists and the fighter's packed role is zero, the resident request handler uses value `1` to select input mask `0x40000000`; every other value selects `0x20000000`. Other packed roles use `0x20000000` without reading this selector. |
| `+2` | Recharge-rate class. Fighter construction maps values `0..4` to `0.8, 0.9, 1.0, 1.1, 1.2`; any other value falls back to `1.0`. |

The byte getter at live `0x00882630` (raw BTL `0x1CE730`, export
`0x008825F0`, an undefined gap) returns `manager[0x0D + side * 3]`. The writer
at live `0x00882670` (raw `0x1CE770`, export `FUN_00882630`) stores the
supplied byte to that same field. Neither helper is null-safe: when the
singleton is absent, each forms a zero record pointer and then reads or writes
byte address `1`. Their traced callers therefore rely on manager creation
order; manager absence is not represented by a harmless selector value.

The selector is also round-tripped by a paired BTL parameter snapshot/restore
path. At live `0x00881070` (raw `0x1CD170`, export `0x00881030`), the reader
takes the side index from setup-object word `+0x18` and saves the selector in
local-record byte `+0x7C`, Practice's row-4 local value. The sole direct call
to the writer is at live `0x0088126C` (raw `0x1CD36C`, export `0x0088122C`);
it restores that local byte for the same setup-derived side.

## Setup and selected support

Resident `FUN_001F4DD0` finalizes the two player records and calls BTL live
`0x00886250` (raw `0x1D2350`, export `FUN_00886210` at `0x00886210`). That BTL
routine consumes the two `0x28`-byte side records rooted in the resident battle
setup object. The selected support-list ID is the word at side-relative
`+0x68`; the resolved support code later consumed by the support-object factory
is the byte at side-relative `+0x6C`. Side-0/1 selected support IDs are
therefore battle-setup words `+0x68/+0x90`.

Two resident configuration paths also write those IDs. `FUN_001FE540` copies
the two primary IDs and two support IDs from a setup record, swapping the two
source pairs together when its side-order byte is nonzero. A separate setup
path, `FUN_001F2AC0`, writes a selected primary ID at battle-setup `+0x74` and
`0x26` at the side-1 support field `+0x90`. Values `0x24`
and `0x25` also receive special-case treatment elsewhere; no domain names are
established for the three sentinel values.

The setup routine resolves the special selection value `0x26`, derives the two
side-record `+0` color variants, and maps each side's selected support data into
side-record `+2`. This proves that the manager's per-side metadata is chosen
before fighter construction and that the fighter's recharge multiplier is
selection-derived.

Special value `0x26` is resolved deterministically, not by a random-number
call. BTL live `0x00885C30` (raw `0x1D1D30`, export `FUN_00885BF0` at
`0x00885BF0`) first canonicalizes the primary-fighter identity with resident
`FUN_001F7E70`, then scans 62 unique eight-byte records at encoded live
`0x008D2690`, raw `0x21E790` (length `0x1F0`, slice SHA-256
`6BAF266E15ECBF6F95B17DDFBE8A65AF3C1900C4153404F5936F1EC9C9CF4977`).
Each record is `[s32 primary identity, candidate 0, candidate 1, candidate 2,
zero pad]`. Known callers supply candidate indices `0..2`; battle setup uses
index `0`. The helper returns `0` if the primary identity has no row.

The complete direct-call set makes the distinction sharper. All seven
BTL calls and three of fourteen resident calls pass constant index `0`. Each
of the other eleven resident calls is inside a loop bounded by `index < 3` and
uses candidates `0..2` only in equality tests against another selection. No
BTL caller requests candidate `1` or `2`, and neither the request handler nor
the manager calls this resolver at all. Thus candidates `1` and `2` participate
in resident selection validation/comparison, while the battle setup's actual
`0x26` replacement is candidate `0`; they are not three runtime summon slots.

All candidate bytes in the retail table are support-list IDs `0..33`, so the
setup branch that calls the helper again if its first result is still `0x26`
cannot be reached from this table.

The concrete support-object code is selected through 66 three-byte records at
encoded live `0x008D1A50`, raw `0x21DB50` (length `0xC6`, slice SHA-256
`25D4DC03376390ED930A47CF1611DBD990CAFAAD38AD6EFF02963793EB9A247C`).
Each record is `[support-list ID, primary-fighter ID or 0xFF, object code]`.
There is one wildcard-primary record for each support-list ID `0..33`; 32 later
primary-specific records override their earlier wildcard because the scan does
not stop at the first match. The input pairs are unique and object codes span
`0..65` exactly once each.

The resulting object code is written to side-relative `+0x6C`, except that
code `49` is normalized to `0`. Two independent raw paths establish this rule.
The resolver passes its result through BTL live `0x00885880` (raw `0x1D1980`,
corresponding preserved-export address `0x00885840`, where no function was
recognized). That helper accepts only codes `0..65` and dispatches through 66
encoded-live pointers at `0x008D2B30`, raw `0x21EC30`: indices other than `49`
target live `0x008858B0` and return zero, while index `49` targets live
`0x008858B4` and returns one. Its callers replace a nonzero-tested code with
zero. Independently, the setup routine's jump table at encoded live
`0x008D2D50`, raw `0x21EE50`, points code `49` to live `0x00886410` and all
other codes `0..65` to live `0x00886400`, again selecting a zero result only
for code `49`. A missing resolver match reaches an explicit store through
address zero rather than a graceful unavailable result.

The sole mapping row that produces code `49` is numeric record
`[support-list ID 23, primary 0xFF, code 49]`, and ID `23` has no
primary-specific override. It therefore always normalizes to object code `0`
in the retail table; support-list ID `0` independently maps directly to code
`0`. No character names are inferred from these numeric IDs.

Recharge class uses a separate 912-record table at encoded live `0x008D1BB0`,
raw `0x21DCB0` (length `0xAB0`, slice SHA-256
`FDD36E924D53D38C035A33624AFE88661C243F02B173C0A0AF67C7BB2B421875`).
Each unique record is `[support-list ID, primary-fighter ID, class]`; there are
no wildcard IDs or duplicate input pairs. Lookup begins at class `2` and an
exact pair overrides it. The table contains only class `0` (475 records),
class `1` (46), class `3` (293), and class `4` (98), so `2` is exclusively the
default for pairs absent from the table.

The color resolver is one continuous raw function at BTL live `0x00885CE0`
(raw `0x1D1DE0`, export start `FUN_00885CA0` at `0x00885CA0`). With sides `0` and `1`, it first sets
both support variants to zero, then applies these rules in order:

```text
if support_identity[0] == primary_identity[1]:
    support_variant[0] = (primary_color[1] + 1) % 3
if support_identity[1] == primary_identity[0]:
    support_variant[1] = (primary_color[0] + 1) % 3
if support_identity[1] == support_identity[0]:
    support_variant[1] = (support_variant[0] + 1) % 3
```

Primary identities first pass through resident `FUN_001F7E70` when that
resolver returns a value other than `-1`. The source color words are the battle
setup side fields `+0x54` and `+0x7C`. Their meaning is independently fixed by
the character-select path: it copies each selector object's color field into
those words and increments the second modulo three when both sides select the
same resolved primary identity and color. The selected support IDs likewise
pass through the BTL support-identity resolver before the comparisons above.
Thus side-record `+0` is a collision-resolved support color, not another active
object slot or a cooldown field.

Only the resolved byte at side-relative `+0x6C` selects the support-object
implementation during a field request. The factory rejects values `>= 0x44`.
Because the retail mapping above produces each code `0..65` exactly once, this
range rejection is not an ordinary selection availability gate; it
requires noncanonical or corrupted resolved state.
For accepted values it chooses one of several specialized object sizes and
constructors; no speculative character or class names are assigned here.
The common initialization interface receives `(object, resolved code, side)`.
Its implementation at BTL live `0x00887FD0` (raw `0x1D40D0`, export
`FUN_00887F90` at `0x00887F90`) stores the side byte at object `+0xE4` and the
resolved code byte at object `+0x60`. Subsequent owner-fighter lookups use that
stored side, rather than reselecting a team member from a global registry.

### Request-time side and member selection

The support choice is fixed before fighter construction. At request time the
resident handler derives only a side index from `fighter[+0x60] & 1`; the BTL
manager then addresses exactly `active[side]` and battle-setup
`resolved_code[side]`. If that slot is populated, it calls the existing
object's virtual `+0x24` query. It neither rotates through candidate slots
`0..2` nor replaces the object with another candidate.

The packed fighter role `((u16 fighter[+0x60] & 0x1FF) >> 5)` affects the input
mask for an occupied slot, as detailed below. Linked Mode (side-record `+1`)
selects Circle versus R1 only for packed role zero; it does not select a support-list
ID, object code, color variant, or second manager slot. No request-time scan of
multiple support team members exists in this ownership path.

The complete native side-lookup and retained-point boundary is owned by
[Target selection](../combat/target_selection.md#support-side-selection-and-point-retention),
including its [nine attack-slot bodies](../combat/target_selection.md#complete-native-attack-slot-boundary).
Primary-fighter auxiliary playback and attack-origin selection retain their
separate owner in
[Puppet control](puppet_control.md#attack-results-remain-primary-owned).

## Gauge state and availability

The resident fighter owns these support fields:

| Fighter offset | Meaning | Evidence |
| --- | --- | --- |
| `+0x74` | Gauge, clamped to `[0.0, 1.0]` | Initialized to `1.0`; read by the request gate; updated by `FUN_00238600`, `FUN_00238720`, `FUN_00238830`, and `FUN_00238950`. |
| `+0x78` | Recharge multiplier | Initialized once from manager side-record `+2` by `FUN_002380C0`; a missing manager or unrecognized class yields `1.0`. |
| `+0x338` | Current input-bit field | Tested by the request handler. |

The HUD copies gauge `+0x74` into its per-side support-gauge controller; the
display is described in [Battle HUD](../session/battle_hud.md#support-gauge).

Fighter setup `FUN_002151E0` supplies `1.0` to the clamped gauge setter at
live call `0x00215530`, then calls the recharge-class resolver at live
`0x0021553C` and stores its result to `+0x78`. A resident direct-call scan
finds no other callers of either initialization helper. Later gauge
changes use the update/delta writers below rather than rerunning selection.

Resident `FUN_00238540` runs immediately after the support request handler in
the normal fighter update. The enclosing update reaches both calls only while
fighter byte `+0x00` has flag `0x02` set. Within that outer invocation,
`FUN_00238540` updates the gauge only while fighter `+0xB00` is zero, fighter
`+0xB10` is zero, and the derived fighter registry's coordinator state
(`0x00607654 -> +0x08 -> +0x14`) is zero; that state belongs to
[Battle entities](../session/battle_entities.md#derived-fighter-registrycoordinator).

The update rule is exact per invocation:

```text
if manager.active[side] == null:
    gauge = clamp(gauge + recharge_multiplier / 450.0, 0.0, 1.0)
else:
    gauge = clamp(gauge - 1.0 / 300.0, 0.0, 1.0)
```

Crossing upward to full in the no-active-object path can emit resident event
`0x2D`, subject to the fighter-role and global gates in `FUN_00238600`.
The two additional writers use the same clamp and add a supplied signed delta
only when the recipient side has no active support object:

| Writer / recipient | Complete resident direct-call set | Supplied delta |
| --- | --- | --- |
| `FUN_00238830(delta, fighter)` / that fighter | `FUN_00225050`, call `0x00225130` (file `0x125230`) | The same normalized amount that the HP writer subsequently subtracts. The support-gauge call is after its byte-`+0x62` bit-0 exclusion and before the HP subtraction. |
| `FUN_00238950(delta, fighter)` / fighter at argument `+0x20` | `FUN_00217AE0`, call `0x00217B28`; `FUN_00228B50`, call `0x00228CB4`; `FUN_002346B0`, call `0x00234A14` | Attack-record float `+0x24`, divided by signed halfword `+0x2E` when that halfword is nonzero. This is the value before the native damage calculator's factors. |

Thus the receiving fighter can gain support gauge from applied damage while
the paired fighter can gain from raw attack-record damage. The second writer
targets the supplied fighter's `+0x20` link, not an inferred support-object
owner; its recipient follows each caller's argument. The guarded and ordinary
record consumers pass the defender. Caller state gates, attack-record fallback,
and the calculation of applied HP damage belong to [Battle damage](../combat/damage.md).

No separate resident cooldown counter was found in this traced path. For an
empty slot, availability uses the normalized fighter gauge and `0.5` is an
entry threshold. An active re-request bypasses that threshold but has the
object-local `+0xE6/+0xE8` latch documented below. Drain versus recharge still
depends only on slot presence, even while that active-request latch is closed.
The request does not directly subtract `0.5` or reset the gauge: an active
object drains it on subsequent updater calls. When a request creates an object
in the normal fighter update, the immediately following updater sees the
populated slot and applies the first `1.0 / 300.0` drain in that same outer
invocation if its gates still pass. Conversely, an object notification or
terminal-state byte does not by itself select recharge: the updater continues
to choose drain until the owning manager slot is actually cleared. This is a
static fact about these writers, not a claim about the visible duration of
every specialized support object.

The following counts are a derived IEEE-754 single-precision reproduction of
the retail operations, starting from exactly `0.0` for recharge or exactly
`1.0` for drain. They are not runtime timing measurements:

| Class | Multiplier | Recharge invocations to `>= 0.5` | Recharge invocations to clamped `1.0` |
| ---: | ---: | ---: | ---: |
| `0` | `0.8` | 282 | 563 |
| `1` | `0.9` | 250 | 501 |
| `2` | `1.0` | 226 | 450 |
| `3` | `1.1` | 205 | 410 |
| `4` | `1.2` | 188 | 376 |

Starting from `1.0`, the active drain reaches clamped `0.0` on invocation 301.
The one-invocation differences from ideal real-number division are float32
accumulation effects. In the normal fighter update the request handler runs
before the gauge updater, so crossing `0.5` in an updater call can only satisfy
a later request-handler call. Any frame in which the outer gates suppress the
updater does not advance these counts.

Gauge exhaustion is a notification, not an immediate owner-side free. The
resident gauge getter at live `0x00238070` (file `0x138170`) is a three-
instruction leaf that returns fighter `float +0x74`. One support-object state
routine at BTL live `0x00889C10` (raw `0x1D5D10`, export `FUN_00889BD0` at
`0x00889BD0`) calls it for the owning side; when the result is exactly `0.0`,
the routine invokes that object's virtual `+0x48` with argument `3`. It does
not clear the manager slot.

The request factory can leave 14 distinct final object vtables (listed in
[Battle entities](../session/battle_entities.md#request-class-creation-and-repeated-calls)).
All 14 put the
state routine above in slot `+0x50`. Nine map virtual `+0x48` directly to BTL
live `0x00889540` (raw `0x1D5640`, export `FUN_00889500` at `0x00889500`);
the five specialized overrides call that same common handler first. It records
the supplied reason at object `+0xE6` and resets its internal state, but does
not write terminal byte `+0xF2` or the manager slot. Thus zero gauge reaches
the common reason-`3` handler for every factory class.

The later route is also common. The scheduled update dispatches state byte
`+0xE6 == 1` through virtual `+0x50`, where the zero-gauge test occurs; after
reason `3` is recorded, a later enabled update dispatches `+0xE6 == 3` through
virtual `+0x58`. All 14 final vtables map `+0x58` to BTL live `0x0088A890`
(raw `0x1D6990`, export `FUN_0088A850` at `0x0088A850`). When object halfword
`+0xE8` is zero and byte `+0xF1` is nonzero, that handler invokes virtual
`+0x40`, the common terminal setter below. If either condition is false, that
invocation does not request terminal state.

All 14 vtables map virtual `+0x40` to the terminal setter at BTL live
`0x008890A0` (raw `0x1D51A0`, export `FUN_00889060` at `0x00889060`), which
writes object byte `+0xF2 = 1`. Twelve map scheduled virtual `+0x10` directly
to BTL live `0x00888720` (raw `0x1D4820`, export `FUN_008886E0` at
`0x008886E0`); the two overrides call that common update first. With
`+0xF2 == 1`, it advances the byte to `2`, after which the manager's pass-1
owner logic deletes the object and clears its slot. When the reason-`3` state
handler calls `+0x40` from inside the current `+0x10` update, the update has
already entered its `+0xF2 == 0` branch; the new value `1` therefore advances
to `2` on the next enabled pass, not the same call.

## Manual request gates and return states

Resident `FUN_00238340` at live `0x00238340` (resident file `0x138440`) is the
per-fighter manual support request handler. Its only direct caller is the normal
fighter update `FUN_0024DA50`; the call is live `0x0024DCA4`, resident file
`0x14DDA4`. That caller reaches the request handler and immediately following
gauge updater only while `fighter[+0x00] & 0x02` is nonzero.

The request path is:

1. Determine whether this side already has an active support object through
   BTL live `0x008854D0` (raw `0x1D15D0`, export `FUN_00885490` at
   `0x00885490`). Its manager callee at live `0x00887810` (raw `0x1D3910`,
   corresponding export address `0x008877D0`) is a five-instruction predicate:
   it returns whether `manager.active[side]` is non-null.
2. With no active object, require input bit `0x20000000`. With an active object,
   most fighters still use `0x20000000`; fighters whose packed `+0x60` role
   field `((value & 0x1FF) >> 5)` is zero instead use `0x40000000` when the
   side's Linked Mode is Auto (`1`) and `0x20000000` otherwise. Under the
   default binding map those logical bits are Circle and R1, respectively.
3. With no active object, require `gauge >= 0.5`. An existing active object
   bypasses this threshold. A failed low-gauge attempt can emit resident event
   `0x2C` for packed role zero.
4. Require fighter `+0xB00 == 0`, fighter `+0xB10 == 0`, and the same
   coordinator state `0x00607654 -> +0x08 -> +0x14` to be zero.
5. Call BTL live `0x00885490` (raw `0x1D1590`, export `FUN_00885450` at
   `0x00885450`), which forwards to the manager request at live `0x008872E0`
   (raw `0x1D33E0`, export `FUN_008872A0` at `0x008872A0`).

The manager request returns a compact state:

| Return | Proven path |
| ---: | --- |
| `0` | Resolved support code is out of range, or an existing object's virtual `+0x24` query returns zero. |
| `1` | The side slot was empty; the factory allocated and initialized a support object, stored it in that side slot, and enabled object-flag masks `0x02` and `0x04`. |
| `2` | The side slot was already populated and its virtual `+0x24` query returned nonzero. |

All 14 final factory vtables use the same virtual `+0x24` implementation at
BTL live `0x00888FE0` (raw `0x1D50E0`, export `FUN_00888FA0` at
`0x00888FA0`). Its raw predicate at live `0x008890D0` (raw `0x1D51D0`,
corresponding unrecognized export address `0x00889090`) returns true exactly
when object byte `+0xE6 == 1` and signed halfword `+0xE8 == 0`. On true, the
common query calls BTL live `0x0088A7C0` (raw `0x1D68C0`, export
`FUN_0088A780` at `0x0088A780`) with argument zero; that writes object
`+0xE8 = 3`, and the manager maps the true query to return `2`. On false it
leaves the object in place and the manager returns `0`.

This is an object-local active-request latch, not a fixed resident cooldown.
The common state routine branches on halfword states `0..3`; it does not
decrement `+0xE8` once per update. After a successful active request, another
request remains unavailable while the state pair differs from
`(+0xE6, +0xE8) = (1, 0)`. It can reopen only if later lifecycle returns to
that exact pair; no fixed update count is established.

While this latch is closed, slot presence still selects the active-object input
mask and bypasses the half-gauge threshold. The manager nevertheless returns
`0`; the resident handler leaves fighter byte `+0xB58` unchanged but still
returns its outer `1` once the resident gates have passed. An open latch yields
manager return `2` and clears `+0xB58`.

Creation does not begin in the queryable state. The common base constructor
leaves object `+0xE6 = 0` and `+0xE8 = 0`. Every final factory class uses the
common virtual `+0x1C` initializer at live `0x00887FD0`, directly or through
one of two overrides that call it first; none changes those two state fields.
Consequently manager return `1` makes the slot immediately active for gauge
drain, but an active re-request initially returns `0`. Reaching `+0xE6 = 1`
is necessary but insufficient: the reason-1 tail can immediately latch
`+0xE8 = 3`, as established below.

The resident handler clears fighter byte `+0xB58` only for manager return `1`
or `2`. Once all resident gates above have passed, however, it returns `1` even
if the manager returned `0`. Callers must not treat the resident boolean as
proof that a support object was created.

Manager absence is one concrete instance of that mismatch. Both null-safe BTL
wrappers report no active object / request return `0`, so the normal handler
does not enter its selector-read branch and the gauge updater selects recharge.
If input, gauge, and the other resident gates pass, the resident handler can
still return `1` without creating an object.

### Animation result and common state transitions

The five borrowed animation payloads at object `+0x80..+0x90` have lookup
suffixes `ent`, `nut`, `run`, `act`, and `ext`, in that order. Their lookup and
ownership evidence belongs to
[Battle entities](../session/battle_entities.md#support-object-common-prefix-and-removal).
The lifecycle below describes how support state consumes those payloads.

Object byte `+0xF1` records the resident animation advance result, rather than
a separate support availability flag. In the common scheduled update at BTL
live `0x00888720`, the instructions at live `0x00888BF8..0x00888C10`
(raw `0x1D4CF8..0x1D4D10`) call
resident `FUN_001BB210(animation, animation[+0x94], 0)` and store its result
to `+0xF1`. A null animation object-list pointer `animation[+0xFC]` instead
produces zero. Object byte `+0xF0` suppresses this advance for one update and
is then cleared; that branch preserves the previous `+0xF1` value.

Resident `FUN_001BB210` (file `0x0BB310`) advances fixed-point position
`animation[+0xEC]` by the supplied step. It compares the result with
`(animation_descriptor[+0x0C] - 1) * 0x100`, clamps at that limit, and initially
returns whether the limit was reached. Descriptor flag `+0x28 & 2` restarts
the animation and forces a zero result when that end is crossed; otherwise,
animation flag `+0xF7 & 0x10` can substitute the result of resident
`FUN_001BB4F0`, which consults the associated animation stream. Thus nonzero
`+0xF1` is the animation system's completion result, not merely an elapsed
support update count. The support state handler executes before this advance,
so it normally consumes the preceding update's result.

The common reason handler at BTL live `0x00889540` (raw `0x1D5640`) changes
the animation, clears `+0xF1`, and sets `+0xF0 = 1` when it installs a
replacement animation; the stores are at live `0x008896DC..0x008896E4`,
`0x008897CC..0x008897D8`, and `0x008898D4..0x008898E0`. The completion result
therefore is not latched across a state change.

All factory classes use common entry slot `+0x4C`, BTL live `0x008899B0`
(raw `0x1D5AB0`, export `FUN_00889970`). Entry starts at `(E6,E8) = (0,0)`,
installs the animation stored at object `+0x80`, and advances `E8` to `1`.
While `(0,1)`, a nonzero animation result invokes virtual `+0x48` with reason
`1`, which resets `E8` to zero but immediately sets it to `3` when Linked Mode
is Auto (`1`). The completed entry therefore leaves `(1,3)` for Auto and
`(1,0)` for Manual. The initial transition also reads Linked Mode: under Auto
it faces the opponent and can invoke virtual `+0x70` before entry completes.
This behavior is additional to that byte's resident input-mask use.

**Reason-1 tail:** after its animation-bind call, the common reason handler
at live `0x008896E4..0x00889737` (raw `0x1D57E4..0x1D5837`; decompilation
omits this tail) loads the side record's `+1`, compares it with `1`, and
calls live `0x0088A7C0(support,0)` when equal. That helper stores halfword
`E8 = 3` at live `0x0088A7FC` and clears movement through live
`0x0088B000`; with argument
zero it does not recursively dispatch another reason. All five reason
overrides call the common handler and leave its `E6/E8` results intact.
The manager's actual query requires exactly `(1,0)`; reason-1 completion alone
does not establish that pair under Auto.

The shared state-`1` routine, BTL live `0x00889C10` (raw `0x1D5D10`), gives
the re-request latch these concrete transitions:

| `E8` | Common behavior while `E6 == 1` |
| ---: | --- |
| `0` | Linked Mode Auto (`1`) calls the same request helper that writes `E8 = 3`, without another manual input. The routine also follows or pauses beside the owning fighter and may instead enter state `1` through its positioning predicates. |
| `1` | A nonzero `F1` changes `E8` to `2` and installs object animation `+0x80`. |
| `2` | A nonzero `F1` changes `E8` to `0` and installs object animation `+0x84`, reopening the common query pair. |
| `3` | Compare the opponent's horizontal distance with object float `+0x130`. When distance exceeds that value and bytes `+0x118/+0x119` are both zero, approach the opponent; otherwise invoke virtual `+0x48` with reason `2` to start the attack state. |

Linked Mode Auto therefore also enables automatic attack requests in the
common state routine. The table records branches within one invocation: after writing
`E8 = 3` in the state-`0` branch, that invocation continues its positioning
work rather than immediately executing the state-`3` branch. The state-`1`
and state-`2` animation transitions return early, so their gauge-exhaustion
notification is deferred to another invocation. These are static ordering
facts; visible animation lengths and character-specific positioning are not
established here.

### Contact-triggered exit and contact-list activation

**Observation:** Common scheduled update tests live `0x0088B150` before
dispatching the state byte. A true result invokes reason `4`; that same update
then dispatches the newly selected state-4 exit routine. Thus a contact exit
can replace a pending state-1 approach or state-2 attack before its native
callback runs. Gauge exhaustion is checked later in state 1, so it cannot be
treated as the only native departure trigger.

The predicate requires support flag `+0x50C & 0x04` clear, a positive result
count at `+0x494`, and state byte `E6` equal to `1` or `2`. It reads the
embedded lists at `+0x48C/+0x368`; their registration, result count and
object-resolution APIs belong to
[Collision](../combat/collision.md#resident-list-and-registration-layouts). Within that
boundary, the exit decision has two forms:

| Result count at support `+0x370` | Contact predicate |
| --- | --- |
| Positive | Every `+0x48C` result must resolve to a kind-1 object, have signed byte `+0x208` in `0..3` (`0..5` when support `+0x50C & 2`), and also occur among the `+0x368` results. A null object, another kind, an out-of-range byte, or a missing membership match requests exit. |
| Zero/nonpositive | A null object or a kind other than `0/5` requests exit. A kind-5 object requests exit unless its word `+0x90` equals one of the three table values below. The first kind-0 result takes the separate paired-fighter gate below. |

The shared kind-5 helper is live `0x0088B480` (raw `0x1D7580..0x1D7607`). It
returns false for null/non-kind-5 inputs or a matching ID, and true only for
kind `5` with an unmatched word `+0x90`. Its three signed halfwords are `9`,
`0x57`, and `0x8B` at live `0x008D2AD0` (raw `0x21EBD0`).
These are native numeric exclusions; no effect or player-facing names are
assigned to them.

For the kind-0 branch, the function resolves the opposite primary fighter
from the support side and tests resident `0x003083A0(opponent)`. That
unrecognized leaf's bytes establish only a nonnull argument and nonnull
resident hub global `0x00607654`; it does not inspect a fighter action.
The support predicate additionally requires opponent `+0xA4C` nonnull and
that record's `+0x14 & 0x4000` clear before returning true. The first kind-0
contact returns this gate's result rather than continuing the contact loop.
The current-record flag check is established from the predicate's raw
instructions (export `0x0088B110..0x0088B437`); decompilation omits it. This
is a bounded support exit predicate, not a whole-game hurtbox or
target-eligibility rule.

**Observation:** Signed support halfword `+0x114` has four direct-`sh` stores
in BTL: constructor clear at live `0x00887C04`, initializer value `90` at
`0x00888688`, common-update decrement at `0x00888978`, and reason-2 clear at
`0x00889804`. The same encoding search also matched a word at export
`0x008D47B0`, outside this function family; it is not an established
support-field writer. This scan excludes
stores through adjusted base pointers, bulk copies and other widths.

The initializer registers then deactivates the contact list at `+0x48C`
before setting `+0x114 = 90`. While terminal byte `F2` is zero, each enabled
common update decrements a positive value; reaching zero calls resident
`FUN_001DD9D0(support+0x48C)` to activate it, and the same update then falls
through into the contact predicate (raw block at export
`0x00888924..0x00888967`). Reason-2 attack entry instead clears the countdown and activates that list
immediately, so the initializer's 90 eligible decrements are not a required
wait before attack. Neither the manager query nor resident gauge/request
gates reads `+0x114`. This timer controls contact-list activation, not summon
recharge or the `E6/E8` re-request latch.

### Factory variants and attack completion

The resolved object codes, the 14 final resident tables they select, and each
table's attack slot `+0x54` and reason slot `+0x48` are listed in
[Battle entities](../session/battle_entities.md#request-class-creation-and-repeated-calls).
The default bodies are live `0x0088A820` (attack) and `0x00889540` (reason);
codes `0x0A`, `0x0C`, `0x11`, `0x19`, `0x1E`, `0x21`, `0x2B` and `0x3F`
override the attack slot, and `0x0A`, `0x19`, `0x21`, `0x2B` and `0x3F` the
reason slot.

All nine distinct attack bodies retain the common completion condition:
`E8 == 0 && F1 != 0` invokes virtual `+0x44`, then virtual `+0x48` with reason
`3`. Their extra work uses animation-index events and class fields, but none
returns to reason `1`. All five reason-handler overrides call the common
handler first and do not replace its `E6/E8` writes. The specialized body at
live `0x0088E0A0` can take an earlier branch when its moving effect collides;
the raw branch at live `0x0088E290` targets live `0x0088E2DC` and continues
to the same completion tail, not the early return that decompilation reports
after the collection-clear call.

The two final tables `0x005FBFC0/0x005FC040` share update override live
`0x0088CE10` (raw `0x1D8F10`, export `FUN_0088CDD0`). It calls the common
scheduled update before iterating child objects and does not change the
support's `E6/E8/F1` fields. Every final table also shares state-4 slot
`+0x5C`, live `0x0088A930` (raw `0x1D6A30`, export `FUN_0088A8F0`): substate
zero performs its exit positioning/effect work and sets `E8 = 1`; animation
completion in substate one invokes reason `3`. The collision-collection
predicate at live `0x0088B150` can request reason `4` while the object is in
state `1` or `2`; its support-specific decision is described in
[Contact-triggered exit and contact-list activation](#contact-triggered-exit-and-contact-list-activation).

The bounded factory lifecycle therefore establishes entry `0 -> 1`, attack
`1 -> 2 -> 3`, and the separate `1/2 -> 4 -> 3` exit. The shared
`E8 = 1 -> 2 -> 0` transitions in the preceding table reopen the request pair
only while `E6` remains `1`. Attack completion itself does not reopen it: it enters the
departure path. Resource animation lengths, emitted payloads, and status or
damage effects cannot be inferred from these transitions. Jutsu-resource
selector tables are separately documented in
[Character assets](../../game/character_assets.md#selector-to-resource-mapping);
their auxiliary record IDs do not identify these factory behavior classes.

### Request preconditions and identifiers

These return states assume the ownership preconditions used by the resident
caller. The side is always reduced to `fighter[+0x60] & 1`; the manager does
not defensively convert another index to an unavailable return. The empty-slot
factory also assumes its heap allocation succeeds. A null allocation reaches
the common slot store at live `0x008876C8` and then dereferences object
`+0x50`; it is not converted to return `0`.

For a new object the manager stores an identifier at object `+0x120` from
its embedded `ccBdySerialNo` allocator, whose contract belongs to
[Battle entities](../session/battle_entities.md#request-class-creation-and-repeated-calls).
After wrap an identifier collision yields zero but does not reject or postpone
object creation. No request, gauge, terminal-state, or slot gate reads object
`+0x120` in the audited paths; it matters to support behavior only as the
notification identity below.

### Support counters and notification suppression

Successful empty-slot creation increments the first of three per-side
halfwords at live `0x008DCE90 + side * 6`. This storage is in BTL BSS, not in the raw file: the
header establishes file-backed end `0x008D6200` and BSS span
`0x008D6200..0x008DD080`. The constructor and BTL live `0x00886BB0` (raw
`0x1D2CB0`, corresponding export address `0x00886B70`) zero all three
halfwords for both sides. The request and gauge gates read none of these six
halfwords, so the creation counter is bookkeeping rather than availability or
cooldown state.

An exhaustive raw-address and direct-call audit bounds the remaining uses. The
first-halfword getter is BTL live `0x00886C20` (raw `0x1D2D20`); its sole
direct caller is resident live `0x00224280`, outside the request and gauge
chains. The second halfword has one inline increment, at BTL live
`0x00889850` (raw `0x1D5950`). The third is changed through the signed-add
helper at BTL live `0x00886C60` (raw `0x1D2D60`), whose sole direct caller is
BTL live `0x00886B3C` (raw `0x1D2C3C`). None of the six fields feeds the
request gates, drain/recharge selection, pass-1 terminal test, or explicit
teardown.

The latter two producers establish distinct meanings:

| BSS halfword, per-side stride `6` | Proven producer and interpretation |
| --- | --- |
| `0x008DCE90` | Successful empty-slot creation; number of published support objects since reset. Slot destruction does not decrement it, so it is not current occupancy. |
| `0x008DCE92` | The common reason-2 handler increments it at live `0x00889850`, after selecting the attack animation, using support side byte `+0xE4`; an invalid side reaches an explicit zero-address assertion. It counts attack-state entries, not completed animations or hits. The five overrides retain this producer. |
| `0x008DCE94` | The signed-add helper receives `+1` from live `0x00886A40` only after its duplicate checks pass. It counts accepted support notifications, not damage magnitude or every projectile contact. |

Notification live `0x00886A40` (raw `0x1D2B40`, export `FUN_00886A00`)
receives `(side, identifier)`. For identifier zero it requires an active object
and object flag `+0x50C & 1` clear. For a nonzero identifier it compares against
four words at live `0x008DCFF0 + side * 0x14`; a match returns without an event
or increment. A new identifier replaces the word selected by ring index
`0x008DD000 + side * 0x14`, which advances modulo four. The accepted path emits
`(side + 1, 2, 1)`, adds one to the third halfword, and sets the active object's
`+0x50C` bit 0 if an object exists. Common reason-2 entry clears that bit.

There are exactly two BTL direct calls to the notification body. Live
`0x0072EBB8` (raw `0x7ACB8`) is in the common projectile contact path and is
gated by projectile byte `+0x284 == 1`; it resolves the side through live
`0x00734130` and supplies projectile identifier `+0x288`. Support emitters at
live `0x0088B040` and `0x0088D880` establish that tag and copy support object
identifier `+0x120` to the projectile (stores at live `0x0088B0AC` and
`0x0088DA18`). When the transient-actor manager (live `0x00736080`) creates an
actor from a nonnull source actor, it copies `+0x284/+0x288`, so the tag
follows descendant actors; the transient base reset clears both. Therefore
several tagged projectiles from the same summon can share one notification
identity. The notification never dereferences the originating support; it
affects only the currently slotted object's `+0x50C` bit. The other call, live `0x008893D0` (raw `0x1D54D0`), supplies the
object's side and identifier zero from body live `0x00889360`, reached by the
resident route below. Projectile acceptance and response decisions belong to
[Projectiles](../projectiles_and_items/projectiles.md).

Battle-phase reset live `0x008852E0` always clears all five words of each
notification ring, independently of the conditional six-halfword reset. The
ring can remember only the four most recently accepted nonzero identifiers;
the duplicate rule is not a permanent record of every summon identifier.

### Resident direct-hit notification route

**Observation:** The sole resident direct call `jal 0x00889360` is at
`0x002335BC` (file `0x1336BC`) in `FUN_00233540`; no encoded direct call to it
exists in BTL.

`FUN_00233540(receiver, enabled)` returns immediately when the low byte of
`enabled` is zero. Otherwise it follows receiver `+0x20`, reads that linked
fighter's signed byte `+0xB58`, and proceeds for every value except
`0`, `-1`, and `-2`. It loads the support slot for the side opposite
`receiver[+0x60] & 1`, calls live `0x00889360` on that object, then adds one
to the linked fighter's byte `+0xA45` through `FUN_00239230`. This is a direct
slot dereference; neither the manager nor the object is checked for null.
Its precondition is therefore stronger than the null-safe manual-request
wrappers.

All three direct calls to `FUN_00233540` are in hit-router
`FUN_002209A0`, mode `2`. That branch retains receiver hit source `+0xE58`
separately from linked fighter `+0x20`, as documented in
[Target selection](../combat/target_selection.md#accepted-hit-source-boundary).
[Hit response](../combat/hit_response.md#accepted-hit-routing) owns the complete
router gates and the ordinary, guarded and intercepted marker values.
Among those three produced values, only ordinary marker `1` passes this
support notification helper; its other calls either disable the helper or
leave an excluded marker. This establishes the support-side consequence
without equating every overlap, animation event or guarded contact with an
accepted notification.

**Observation:** The BTL body at live `0x00889360..0x008893F7` (raw
`0x1D5460..0x1D54F7`; decompilation stops before its notification tail)
copies `0x54` bytes from side record `0x008DCEA0 + side * 0xA8` to the immediately following record at
`0x008DCEF4 + side * 0xA8`, deactivates the support's collection at `+0x148`,
calls notification `(side, 0)`, then increments support byte `+0x116`.
Resident `FUN_0017A420` confirms the first argument is the copy destination.
The local `+0x116` increment and linked-fighter `+0xA45` increment occur
regardless of whether notification deduplication accepts identifier zero.
The common scheduled update resets `+0x116` before state work, so that byte
is not the cumulative BSS notification count. These records and increments
do not alter the gauge, request latch, or owner slot in the inspected bodies.

### Support-record borrowing and retained-source lifetime

**Observation:** The kind-2 branch of resident `FUN_002179F0(receiver,source)`
uses the source only to establish nonnull pointer, magic `0x474F`, and kind
`+0x0C == 2`. It then calls BTL live `0x00886850` with
`(opposite receiver side, 1, 1)`. It does not use the source object's side,
support identifier `+0x120`, or indexed-effect generation to select a record.
The getter (export `0x00886810..0x008868AC`) returns
`0x008DCEA0 + side*0xA8 + selector*0x54`. For selector `1` and nonzero
third argument it first calls live `0x008868F0` to copy the current `0x54`
bytes into the following side-owned record: the refresh helper's raw
instructions (export `0x008868F0..0x0088690F`) pass destination
`current+0x54` and length `0x54` to resident `FUN_0017A420`.
This is the same record pair copied by the direct-hit notification above.
The returned address is a fixed per-side storage location, not a new
allocation for that hit. A later refresh or notification can replace its
contents. State-script command `6`, live `0x00882E40`, also writes the
current side record, which is distinct from the support object allocation.

**Lifetime limit:** Returning a side-owned record does not keep the supplied
support object alive: `FUN_002179F0` must dereference that object's header
before reaching the copy, and this kind-2 lookup has none of the
index/generation checks that protect the indexed-effect handles below. The
retained-pointer writers, the copied source prefix and the pointer-lifetime
limits belong to
[Target selection](../combat/target_selection.md#copied-provenance-and-pointer-lifetime-limits).
The inspected support deletion and record consumers establish neither a
stale-pointer failure nor a schedule that prevents later use of an expired
hit-source alias.

## Scheduled lifecycle and teardown

The resident battle dispatcher `FUN_001F03E0` gives support manager bit
`0x0008` in its subsystem masks. In its three ordered passes it calls these BTL
wrappers:

| Pass | BTL live / raw / export wrapper | Manager work reached |
| --- | --- | --- |
| 1 | `0x00885400` / `0x1D1500` / `FUN_008853C0` at `0x008853C0` | live `0x00886ED0`, export `FUN_00886E90` at `0x00886E90` |
| 2 | `0x00885430` / `0x1D1530` / `FUN_008853F0` at `0x008853F0` | live `0x008871A0`, export `FUN_00887160` at `0x00887160` |
| 3 | `0x00885460` / `0x1D1560` / `FUN_00885420` at `0x00885420` | live `0x00887250`, export `FUN_00887210` at `0x00887210` |

Pass 1 refreshes object-flag masks `0x02` and `0x04` from current battle state.
It begins with both enabled. If the fighter pointer held at battle-setup
`+0xDE4` has nonzero `+0xB00` or `+0xB10`, it disables both; a separate
global-predicate chain described below can disable `0x02` alone. These scheduled
object flags are distinct from the fighter byte-`+0x00` outer-update flag
described above. For an object with `0x02` enabled, pass 1 invokes virtual
`+0x10` and then checks object byte `+0xF2`. When that byte equals `2`, it
invokes virtual destructor slot `+0x08` with deleting flag `1` and clears the
owning manager slot. Pass 2 invokes virtual `+0x14` for objects with `0x04`
enabled. It temporarily writes pointer value `0x00609160` to the shared global
pointer slot at live `0x006073F4`, then restores that slot's prior value. Pass
3 invokes virtual `+0x18` for objects with `0x02` enabled.

These flags are callback-enable gates, not slot membership. The presence
query (live `0x008854D0`) and the slot-pointer getter (live `0x00886750`) test
neither flag nor `+0xF2`, so a support remains discoverable until its owner
destroys it and clears the slot. Because `+0xF2 == 2` is checked only inside
the `0x02`-enabled pass-1 dispatch, a disabled object is not deleted by pass 1,
while the unconditional owner teardown below ignores both flags.

Pass 1 has two additional manager-level actions before the virtual `+0x10`
loop. If manager byte `+0x20` is set, it checks each side's resolved code with
the raw code-table predicate at live `0x00885B70` (raw `0x1D1C70`,
corresponding export address `0x00885B30`) and may emit event
`(side + 1, 0x18, 1)`, then clears `+0x20`. Under a BTL
global-predicate chain it can also broadcast virtual `+0x40` to both active
objects through manager live `0x008878F0` (raw `0x1D39F0`, export
`FUN_008878B0` at `0x008878B0`). The vtable audit above proves this is a
terminal request for every factory class. Because the broadcast precedes the
per-object `+0x10` loop, an object can advance `+0xF2` from `1` to `2` and be
deleted in that same pass when flag `0x02` remains enabled. If `0x02` is
disabled, the terminal byte remains `1` until a later enabled pass. The global
predicate's battle meaning remains unresolved, but its exact conditions are
established:

| Predicate | Exact expression | Evidence |
| --- | --- | --- |
| `A` | Fixed BTL object at `0x008D6A10` has word `+0x3C != 0` and byte `+0x38 != 0`. | Wrapper live `0x007064B0` (raw `0x525B0`) calls leaf live `0x007069F0` (raw `0x52AF0`, export undefined gap `0x007069B0`). |
| `B` | Resident global `0x00607844` is non-null and its word `+0x32D0` has neither bit `0x04` nor bit `0x10` set. | Leaf live `0x00777DB0` (raw `0xC3EB0`, export undefined gap `0x00777D70`). |
| `C` | Global `0x00607654` is non-null, its pointer `+0x08` is non-null, and that registry's coordinator state `+0x14 == 3` (see [Battle entities](../session/battle_entities.md#derived-fighter-registrycoordinator)). | Leaf live `0x00772BD0` (raw `0xBECD0`, export undefined gap `0x00772B90`). |

The terminal broadcast runs for `A && !B`. Object update flag `0x02` is
additionally disabled for `(A && B) || (C && !(fighter0[+0x00] & 0x02))`.
Flag `0x04` does not have those additional gates. Here `fighter0` is the
pointer at battle-setup `+0xDE4`; the same result is applied to both sides'
objects. These predicates are structural facts, not inferred menu or cinematic
names. The independently established lifetime of the `0x00607844` object
belongs to [Pause and replay](../session/pause_and_replay.md#auxiliary-btl-global-and-the-0xa50-override).

Resident `FUN_001EC7A0` initializes the subsystem through BTL live
`0x00885210` (raw `0x1D1310`, export `FUN_008851D0` at `0x008851D0`), which
resets the support-side global counters, deletes any prior manager, and
creates and publishes a new one (allocation details in
[Battle entities](../session/battle_entities.md#separate-owner-and-exact-side-slots)).
Resident `FUN_001EC890` and resident cleanup call sites at live `0x001F20F0`
and `0x001F360C` call BTL live `0x00885290` (raw `0x1D1390`, export
`FUN_00885250` at `0x00885250`), which invokes the manager's deleting
destructor and clears `0x00607888`. Those are the only three resident direct
calls to this destroy wrapper.

Later battle-phase entry `FUN_001EDB00` calls BTL live `0x008852E0` (raw
`0x1D13E0`, export `FUN_008852A0` at `0x008852A0`). If the manager exists, this
resets its embedded allocator through manager live `0x00886EB0` (raw
`0x1D2FB0`, export `FUN_00886E70` at `0x00886E70`), writing manager
`+0x18 = 1` and `+0x1C = 0`. The wrapper can also reset the six BSS halfwords
above under its resident-mode predicates. This is initialization/bookkeeping;
it is not a per-request cooldown reset.

The manager deleting destructor at BTL live `0x00886DE0` (raw `0x1D2EE0`,
export `FUN_00886DA0` at `0x00886DA0`) deletes each non-null per-side support
object through virtual slot `+0x08` and clears both slots. Therefore both
natural object completion and enclosing battle-subsystem teardown have
explicit ownership paths; overlay replacement is not relied upon as object
cleanup.

There is also a clear-without-manager-destruction path. Resident
`FUN_001EDD10` calls BTL live `0x008853D0` (raw `0x1D14D0`, export
`FUN_00885390` at `0x00885390`). Its manager callee at live `0x00886E70`
(raw `0x1D2F70`, export `FUN_00886E30` at `0x00886E30`) calls the all-sides
delete routine at live `0x00887990` (raw `0x1D3A90`, export `FUN_00887950` at
`0x00887950`). That routine deletes both non-null objects through virtual
`+0x08` with flag `1`, clears both slots, and leaves the `0x24`-byte manager
allocated. The manager callee then sets manager byte `+0x20 = 1`; pass 1
performs and clears the one-shot resolved-code checks described above.

### Paired-participant transitions and temporary callback disable

**Observation:** Manager live `0x00887830` calls each occupied support's
virtual `+0x28`, then clears that object's callback flag masks `0x02/0x04`.
Every final factory table maps `+0x28` to live `0x00889040`, a wrapper which
dispatches virtual `+0x48` with reason `1`. The operation resets support
action/animation state before disabling callbacks; it neither writes terminal
byte `+0xF2` nor clears the owning slot. Under Linked Mode Auto, the common
reason-1 tail described above leaves `E8 = 3` rather than an open request.

The two resident direct calls are at `0x0023B620` in `FUN_0023B280` and
`0x00245988` in `FUN_002455B0`. The first precedes `FUN_00241F10` on accepted
Extra Hit entry; `FUN_0023B280` is the common major-8 transition described in
[Combat action execution](../combat/combat_action_execution.md#continuation-and-common-exit-decisions). The second follows writes of
`+0xB10 = -1` to both linked fighters on its paired transition.
[Extra Hit](../combat/extra_hit.md#eligibility-and-action-exit) owns
the participant-state contracts and admission conditions. These callsites
establish support reset/disable at those boundaries, without assigning a
player-facing name to the `+0xB10` sequence.

Reason `1` also clears the common embedded contact/attack collection state
through live `0x0088C6B0/0x0088C740`, resets the per-state positions and
movement, and binds the waiting animation. This does not destroy the object.
Later manager pass 1 derives and rewrites `0x02/0x04` again; a disable is
not a permanent cancellation. The resident request and gauge gates continue
to use participant `+0xB00/+0xB10`, while slot presence remains true until
explicit owner deletion. Consequently no recharge or new empty-slot summon
is implied by this temporary callback-disable operation.

### Specialized descendants and release order

**Observation:** The deleting destructors of all 14 final resident vtables
fall into three cleanup families. Ten specialized tables
have small wrappers which restore their own table, call the common destructor
with deleting flag zero, then free the complete support allocation only when
the original signed halfword flag is positive. The default table calls the
common destructor directly. Common child, handle, collection and borrowed
resource ownership remains with
[Battle entities](../session/battle_entities.md#support-object-common-prefix-and-removal).
The remaining three tables add the work below before that common teardown.

| Resolved codes / final table | Additional lifetime path |
| --- | --- |
| `0x15..0x17` / `0x005FC040` | Initializer live `0x0088CF40` owns a `0x20`-byte list header at support `+0x510` and appends four presentation nodes. Deleting destructor live `0x0088F390` releases the nodes and header before the common support destructor. |
| `0x38` / `0x005FBFC0` | Initializer live `0x0088D100` uses the same header/node mechanism with three nodes. Deleting destructor live `0x0088F220` releases the same ownership family. |
| `0x3F` / `0x005FBB40` | Constructor live `0x0088E5F0` initializes a three-word indexed effect handle at `+0x510/+0x514/+0x518`. Destructor live `0x0088ED10` validates that handle and requests effect retirement before the common support destructor; it does not free the indexed effect record itself. |

The list initializers' publication tails are at export
`0x0088CF00..0x0088CFEF` and `0x0088D0C0..0x0088D1AF`. The shared builder is
live `0x008850E0..0x0088520C` (export `0x008850A0`, raw `0x1D11E0`). It walks the existing header count/head at
`+0/+4`, allocates `0xF0` bytes per new node, constructs each from one
`0x88`-byte definition and the support's playback `+0x70`, appends through
node `+0xE0`, and increments the header count after each successful node.
A failed node allocation is skipped; the stored count describes accepted
nodes rather than the requested three or four.

The node constructor at live `0x00883AC0` (export `0x00883A80`) borrows
definition `+0` and playback `+4`, owns its sample buffer `+0x24`, and
constructs embedded records at `+0xB8/+0xCC`. Support update override live
`0x0088CE10` calls the common support update first, then advances each node;
presentation override live `0x0088CEB0` likewise calls the common
presentation pass before visiting the list. These support-local nodes are
distinct from the primary-fighter auxiliary playback records and helper
owners in [Puppet control](puppet_control.md#linked-presentation-helpers).
No additional primary fighter or support-manager side slot is installed by
the inspected node builder.

The two list destructors (export `0x0088F1E0..0x0088F347` and
`0x0088F350..0x0088F4B7`) loop over every node, not only the first one that
decompilation shows. Each nonnull node's next pointer is saved before
releasing its sample buffer, destroying both embedded records through resident
`FUN_00208520(...,-1)`, and freeing the node. The loop continues through the
header count, frees the header, nulls support `+0x510`, then calls the common
support destructor.

The code-`0x3F` handle has a different contract. Its index must be nonnegative
and below the resident effect owner's `+0x424`, its saved generation must be
nonzero and match the indexed `0x210`-byte record's `+8`, and that record's
byte `+0x1B1` must be nonzero. The reason override at live `0x0088E640`
first calls the common reason handler, then release helper live `0x0088EBA0`
on every reason.
For reason `2` it can acquire a fresh record through resident
`FUN_0030E130(effect_owner+0x41C, support+0x510)`. The attack and attachment
callbacks repeat the same index/generation checks before using cached pointer
`+0x518`. This generation is separate from support lineage `+0x120`.

On a valid handle, both the release helper and deleting destructor call
`FUN_0030F160(record,0,0,10)`, write record `+0x1BC = 10` and byte
`+0x1AE = 1`, then reset the support handle to
`(index,generation,pointer) = (-1,0,0)` through resident leaf
`0x003092D0..0x003092E7`. An invalid handle skips those effect writes and the
handle reset. On the valid branch, support deletion requests retirement of the
separately managed record and resets its local handle; the inspected
destructor does not synchronously destroy that record. How the pool consumes
these writes is summarized in
[Indexed-effect retirement consumers](#indexed-effect-retirement-consumers);
visible survival is not established by these static paths.

**Observation:** Code `0x0A` also uses an indexed effect handle at
`+0x510/+0x514/+0x518`, but its release policy differs. Attack body live
`0x0088DC70` acquires a record at animation event index `2`, then repeats the
index/generation validity checks before updating it. Reason override live
`0x0088DB00` calls the common handler first. For reason `4`, a valid handle
receives the same retirement writes with value `5` instead of `10` before
the local handle is reset. Every other reason resets the local handle
without those record writes. Its deleting destructor is the small common
wrapper at live `0x0088EFF0`; it adds no code-`0x3F`-style release request.
This proves different support-local release contracts, not a leak or a
claim that the separately managed effect necessarily survives its own
lifetime rules.

### Selected resource commands and callback routes

**Observation, high confidence:** State scripts and streamed animation events
have separate dispatch paths. Script builder live `0x0088C1D0` selects a
five-byte row at live `0x008BF460` using the resolved object code. Code
`0x0A` selects token `new`, variant `1`; code `0x3F` selects `ymt`, variant
`1`. It formats `BIN_%s%dscr_%s` with suffixes `ent/wit/atk/ext` for states
`0/1/2/3`; the fifth suffix is null. For each populated state it replaces
the owned `0x10`-byte wrapper at `support+0x134+state*4` and stores a
borrowed pointer to the command bytes at wrapper `+0x0C` (loop and
allocation tail at export `0x0088C190..0x0088C307`). Wrapper destruction and the resource bundle lifetime belong to
[Battle entities](../session/battle_entities.md#support-object-common-prefix-and-removal).

Caller live `0x0088C350` selects the current state wrapper, then invokes
runner live `0x0088C3A0`. The runner requires the integer-position-change
byte `+0x100`; it takes the position from `support[+0xF8] >> 8` and walks
from the wrapper's start pointer on each eligible call. Each command begins
with position/opcode words, and its native handler returns the next command
pointer. In the complete loop (export `0x0088C3A0..0x0088C447`) the
wrapper's start pointer is not advanced persistently, and opcode
`0` terminates the walk without testing its position word. Matching commands
compare equality with the sampled integer position; the runner does not
iterate all positions crossed by a playback step. A seek which revisits a
position can therefore make its command eligible again. Playback bookkeeping
and descriptor replacement remain with
[Scene playback owners](../../runtime/scene_playback_owners_btl.md#btl-buddy-resource-descriptor-changes).

The following native commands establish the selected scripts' support-owner
interfaces; this is not a full opcode inventory:

| Opcode / BTL live handler | Command bytes and support-side operation |
| --- | --- |
| `4` / `0x00882BF0` | `0x2C` bytes: positive radius at command `+8` binds attack entry `1` to the two side-record pointers and borrows the 32-byte inline scene name at command `+0x0C` into support `+0x350`. Nonpositive radius clears that binding. |
| `14` / `0x00882CC0` | `0x30` bytes: explicit index at `+8`, radius at `+0x0C`, and 32-byte name at `+0x10` bind the selected attack entry; the name pointer goes to `+0x350+index*4`, and the radius to `+0x188+index*0x50`. |
| `15` / `0x00883660` | `0x30` bytes: the analogous index/radius/name binding for the secondary contact collection `+0x368`, radii `+0x3A8+index*0x50`, and names `+0x480+index*4`. |
| `5` / `0x00882DE0` | `0x0C` bytes: a nonzero argument calls `FUN_001DD9D0` on attack collection `+0x148`; zero calls `FUN_001DDA50`. |
| `16` / `0x00883780` | `0x0C` bytes: the same activation/deactivation calls for contact collection `+0x368`. |
| `18` / `0x008838B0` | `0x0C` bytes: a nonzero argument sets support `+0x50C & 4`, suppressing the contact-triggered exit described above. Zero replaces that bit with `(byte(+0x50C) & 1) << 2`; it does not unconditionally clear suppression. The complete leaf is export `0x00883870..0x008838CF`. |

**Resource observations:** In the decompressed retail `BUDDY/2NEWBDY1.CCS`
and `BUDDY/2YMTBDY1.CCS`, the named type-`0x2400` blobs follow the directory
and chunk framing owned by
[CCS runtime](../../game/files/ccs_runtime.md#parsing-type-dispatch-and-publication).
The attack-blob chunk headers are at decoded offsets `0x272F0` and
`0x12374`; their blob lengths are `396` and `172` bytes, respectively.
Each blob starts with word `0x101`; commands start at blob `+4`.
The native widths walk each selected attack blob exactly to its end,
including the two-word terminal marker. These are bounded named-blob reads,
not an exhaustive typed walk of either CCS container.

| Selected script | Authored support-interface commands |
| --- | --- |
| `BIN_new1scr_atk` | Position `3`: opcode `18(1)`; opcode `4` binds radius `150.0` and `OBJ_2cmn00t0 pelvis`; opcode `15` binds contact index `0`, radius `180.0`, and the same name. Attack activation `5(1)` appears at positions `7,17,27,37,47,57,67,77`; contact activation `16(1)` is at `7`. Position `85` contains `5(0)`, `16(0)`, and `18(0)`. Terminal opcode `0` has position word `90`. |
| `BIN_ymt1scr_atk` | Position `1`: opcode `14` binds attack index `0`, radius `100.0`, and `OBJ_hit_dmy01`. Attack activation `5(1)` appears at `21,24,27`, and deactivation `5(0)` at `30`. Terminal opcode `0` has position word `33`. |

Both selected containers' `ent/ext/wit` scripts contain only leading
`0x101` and terminal words `(1,0)`. The attack blobs also contain opcodes
`1/6`; their widths were included in the complete walk, but their audio and
attack-payload semantics are outside this selected interface trace.
The position words above are authored animation positions, not seconds,
guaranteed dispatched events, or measured animation lengths. In particular,
terminal position words `90/33` do not schedule support departure.

The inline scene names are borrowed from resource bytes, not copied into
the support allocation and not retained scene-object pointers. Common reason
reset helpers live `0x0088C6B0/0x0088C740` clear all six attack bindings and
three contact bindings, respectively, including their radii, side-record
pointers, and name pointers, then deactivate the corresponding collection.

**Separate streamed-event route:** Support playback callback resident
`FUN_00308DC0` forwards type-`0x8002` events to BTL live `0x008866D0`.
That wrapper accepts event codes `2000..3000`, uses the supplied primary
fighter's side to load the active support slot, and invokes support virtual
`+0x20` if the slot is nonnull. Tables `0x005FBD40` and `0x005FBB40`
both put live `0x00888FD0` (export `0x00888F90`) in this slot; it is only
`jr ra; nop`. Thus neither selected subclass implements its
indexed effect or state-script commands in this virtual streamed-event slot.
The callback's other resident/BTL event consumers are separate interfaces;
their complete resource event streams were not decoded here.

### Indexed animation binding and attachment sampling

**Observation:** Code `0x0A` attack body live `0x0088DC70` requires
request latch `+0xE8 == 0` and sampled changed position `2` to acquire its
indexed record. It resolves `ANM_enewact1` from support bundle `+0x6C`,
then calls `FUN_0030F290(record,descriptor,1,0,0,0)` to bind a type-`1`
animation player. Its initialization tail (export
`0x0088DCC8..0x0088DD5F`) seeks with `FUN_0030ED40(record,1)`,
sets the record's transform from the support position, writes record
`+0x1C = 1`, and sets scalar `+0x34 = 0.3`. The seek is not a repeat-mode
write. The later valid-handle path refreshes the transform and copies the
support player's halfword step `+0x94` through `FUN_0030F080`.

Code `0x3F` instead binds `ANM_pymtact1e` on reason `2`, after releasing
its previous valid handle. It uses the same type-`1` binding call, computes
an origin retained at support `+0x520`, installs that origin in the record's
transform, sets record `+0x1C = 2`, and transfers the support playback step
(export `0x0088E690..0x0088E72F`). Its attack body live `0x0088E790`, at changed position `14` with request
latch zero, additionally resolves `CMP_2ymtgim_a0/a1/a2/a3` and calls
resident `FUN_003F9010` for each with the retained origin. These four
descriptor calls are distinct from the indexed animation handle; their
internal effect ownership is outside this interface trace.

The code-`0x3F` attachment override, virtual `+0x3C` at live
`0x0088E9B0`, validates the indexed handle and requires record type
`+0x19C == 1`. It reads that record's player at `+0x1A0`, then visits
all six borrowed attack names at `support+0x350+i*4`. Each nonnull name is
resolved anew through `FUN_001BAB40(player,name,1)`. A found scene object
has its transform refreshed, and its vector at `+0x30` is copied into
the attack sample at `support+0x190+i*0x50`. The raw sample store and
six-entry loop (export `0x0088EA60..0x0088EB47`) visit every entry, not only
the first one that decompilation suggests. This is the native consumer of
`OBJ_hit_dmy01` supplied by the selected state script. No scene-object pointer is cached by this callback.

The record-side binding (`FUN_0030F290`), step write (`FUN_0030F080`) and
scalar publication (`FUN_00311C60`) belong to the pool described in
[Battle lifecycle](../session/battle_auxiliary_services.md#indexed-effect-pool-cceffdrawobj).
They are concrete step/scalar interfaces, not a measurement of visual
opacity, animation speed, or event frequency.

### Indexed-effect retirement consumers

Both support handles acquire a record through resident
`FUN_0030E130(effect_owner+0x41C, support+0x510)` from the `ccEffDrawObj`
pool, which is separate from the `0x24`-byte two-side support manager. The
pool's handle, callback and retirement contract is described in
[Battle lifecycle](../session/battle_auxiliary_services.md#indexed-effect-pool-cceffdrawobj).
Applied to the support writes above:

- Code `0x3F` (release helper and deleting destructor) requests retirement
  with `N = 10`; code `0x0A` (reason `4` only) uses `N = 5`. In both cases
  `N` is the local fade divisor and the initial retirement countdown, so the
  tenth or fifth eligible third-phase pool callback requests owner removal.
  These are callback counts, not frames or seconds.
- The record can leave earlier: animation completion with completion-removal
  enabled, or pool pressure recycling the record, also retire it. A support
  handle can therefore become invalid before support destruction; the
  repeated index/occupied/generation checks protect only this cached record
  and do not validate fighter hit-source pointers.
- Support deletion does not destroy the record synchronously. Whole-pool
  destruction is a separate route that does not wait for either support
  countdown.

## Limits and useful negative results

- The analysis proves one manager-owned active object per side. It found no
  second simultaneous ordinary-support slot in this path.
- No independent resident cooldown timer was found beside fighter `+0x74` and
  `+0x78`; the active-object pointer itself selects drain versus recharge.
  Active re-request has a separate object-state latch, not a decrementing
  timer.
- Zero gauge is passed to an object as virtual reason `3`; it is not itself the
  manager's deletion condition. The manager frees only terminal byte
  `+0xF2 == 2` while pass-1 flag `0x02` is enabled.
- Side-record `+1` is Practice's Linked Mode (Manual `0`, Auto `1`). It
  selects the active-object request input, entry facing, and automatic attack
  requests; it does not select a support, object code or slot.
- All final factory classes retain the shared request pair and attack-to-exit
  transition. Their detailed attack payloads remain outside this document;
  animation completion must not be equated with landed damage.
- Reason `1` resets state before any temporary callback disable, but under
  Linked Mode Auto it immediately sets the attack-request latch again. Entry
  completion or callback disable therefore does not imply an available active
  re-request.
- Object halfword `+0x114` schedules contact-list activation; it is separate
  from gauge availability and the request latch. Reason `2` can activate the
  list before that initial countdown expires.
- Static code establishes update counts and ordering, not wall-clock duration.
  Any conversion to seconds requires the actual scheduler rate.

## Function map

| Image | Live address | File/raw offset | Preserved export | Established role |
| --- | ---: | ---: | --- | --- |
| Resident | `0x001BB210` | `0x0BB310` | `FUN_001bb210` | Advance animation position and return the completion result stored in support `+0xF1`. |
| Resident | `0x001EC7A0` | `0x0EC8A0` | `FUN_001ec7a0` | Initialize battle subsystem and create/reset BTL support manager. |
| Resident | `0x001EC890` | `0x0EC990` | `FUN_001ec890` | Enclosing cleanup that destroys the BTL support manager. |
| Resident | `0x001EDD10` | `0x0EDE10` | `FUN_001edd10` | Transition path that clears both active slots but retains the manager. |
| Resident | `0x001F03E0` | `0x0F04E0` | `FUN_001f03e0` | Three-pass battle subsystem dispatcher. |
| Resident | `0x002179F0` | `0x117AF0` | `FUN_002179f0` | Classify a supplied source header; kind 2 requests a refreshed opposite-receiver-side support record. |
| Resident | `0x00233540` | `0x133640` | `FUN_00233540` | Consume the paired ordinary-response marker and notify the opposite side's support object. |
| Resident | `0x00238070` | `0x138170` | unrecognized three-instruction leaf | Return fighter support gauge `+0x74`. |
| Resident | `0x002380C0` | `0x1381C0` | `FUN_002380c0` | Map selected support's manager class byte to fighter recharge multiplier. |
| Resident | `0x00238340` | `0x138440` | `FUN_00238340` | Manual support input and request gates. |
| Resident | `0x00238540` | `0x138640` | `FUN_00238540` | Select recharge or active drain. |
| Resident | `0x00238600` | `0x138700` | `FUN_00238600` | Recharge and clamp. |
| Resident | `0x00238720` | `0x138820` | `FUN_00238720` | Active-object drain and clamp. |
| Resident | `0x00238830` | `0x138930` | `FUN_00238830` | Add signed gauge delta to the supplied fighter while its support slot is empty. |
| Resident | `0x00238950` | `0x138A50` | `FUN_00238950` | Add signed gauge delta to the fighter at the supplied fighter's `+0x20` link while the recipient's support slot is empty. |
| Resident | `0x0030E130` | `0x20E230` | `FUN_0030e130` | Acquire/recycle an indexed record and publish its generation handle. |
| Resident | `0x0030F290` | `0x20F390` | `FUN_0030f290` | Bind the selected animation descriptor as a type-1 player. |
| BTL | `0x00885210` | `0x1D1310` | `FUN_008851D0` / `0x008851D0` | Recreate two-side manager. |
| BTL | `0x008852E0` | `0x1D13E0` | `FUN_008852A0` / `0x008852A0` | Reset manager identifiers and notification rings; conditionally reset BSS counters. |
| BTL | `0x00885490` | `0x1D1590` | `FUN_00885450` / `0x00885450` | Null-safe global wrapper for manager request. |
| BTL | `0x008854D0` | `0x1D15D0` | `FUN_00885490` / `0x00885490` | Null-safe global wrapper for active-object predicate. |
| BTL | `0x00885880` | `0x1D1980` | unrecognized start / `0x00885840` | Validate an object code and identify code `49` for normalization to zero. |
| BTL | `0x00885C30` | `0x1D1D30` | `FUN_00885BF0` / `0x00885BF0` | Resolve a canonical primary identity to one of three support-list candidates. |
| BTL | `0x00885CE0` | `0x1D1DE0` | `FUN_00885CA0` / `0x00885CA0` | Resolve per-side support color variants without identity/color collisions. |
| BTL | `0x00886250` | `0x1D2350` | `FUN_00886210` / `0x00886210` | Normalize selected support data and initialize per-side metadata. |
| BTL | `0x008866D0` | `0x1D27D0` | `FUN_00886690` / `0x00886690`, truncated | Forward selected streamed-event codes to the active support's virtual `+0x20`. |
| BTL | `0x00886850` | `0x1D2950` | `FUN_00886810` / `0x00886810` | Return a side-owned support record, optionally refreshing its copied half. |
| BTL | `0x008868F0` | `0x1D29F0` | `FUN_008868B0` / `0x008868B0`, truncated | Copy the current side record into its adjacent `0x54`-byte record. |
| BTL | `0x00886950` | `0x1D2A50` | unrecognized start / `0x00886910` | Allocate object `+0x120` identifier from manager `+0x18`, with post-wrap active-ID collision fallback. |
| BTL | `0x00886A40` | `0x1D2B40` | `FUN_00886A00` / `0x00886A00` | Suppress duplicate support notifications, emit the accepted event, and increment the third counter. |
| BTL | `0x00886BB0` | `0x1D2CB0` | unrecognized start / `0x00886B70` | Reset three BSS bookkeeping halfwords for each side. |
| BTL | `0x00886C60` | `0x1D2D60` | unrecognized start / `0x00886C20` | Add a signed value to the third per-side BSS halfword. |
| BTL | `0x00886CB0` | `0x1D2DB0` | unrecognized start / `0x00886C70` | Construct `0x24`-byte two-side manager. |
| BTL | `0x00886DE0` | `0x1D2EE0` | `FUN_00886DA0` / `0x00886DA0` | Delete active objects and, for a deleting call, free the manager. |
| BTL | `0x00886E70` | `0x1D2F70` | `FUN_00886E30` / `0x00886E30` | Delete both active objects, retain manager, and arm one-shot setup. |
| BTL | `0x00886EB0` | `0x1D2FB0` | `FUN_00886E70` / `0x00886E70` | Reset the embedded identifier allocator to its initial state. |
| BTL | `0x008872E0` | `0x1D33E0` | `FUN_008872A0` / `0x008872A0` | Validate resolved code; create or query the side's support object. |
| BTL | `0x00887810` | `0x1D3910` | unrecognized start / `0x008877D0` | Return whether a side has an active support object. |
| BTL | `0x00887990` | `0x1D3A90` | `FUN_00887950` / `0x00887950` | Delete and clear one side or both sides; reset path supplies `-1`. |
| BTL | `0x00887FD0` | `0x1D40D0` | `FUN_00887F90` / `0x00887F90` | Initialize common object identity fields, including resolved code and owning side. |
| BTL | `0x00888720` | `0x1D4820` | `FUN_008886E0` / `0x008886E0` | Common scheduled object update; advance terminal byte `1` to `2`. |
| BTL | `0x00888FE0` | `0x1D50E0` | `FUN_00888FA0` / `0x00888FA0` | Common active-object request query; test and latch object state. |
| BTL | `0x008890A0` | `0x1D51A0` | `FUN_00889060` / `0x00889060` | Common virtual `+0x40` terminal setter; write object `+0xF2 = 1`. |
| BTL | `0x008890D0` | `0x1D51D0` | unrecognized start / `0x00889090` | Return whether object `+0xE6 == 1` and `+0xE8 == 0`. |
| BTL | `0x00889540` | `0x1D5640` | `FUN_00889500` / `0x00889500` | Common virtual `+0x48` reason/state-reset handler. |
| BTL | `0x008899B0` | `0x1D5AB0` | `FUN_00889970` / `0x00889970` | Common entry state; completion selects reason `1`, leaving `(1,3)` for Linked Mode Auto or `(1,0)` for Manual. |
| BTL | `0x00889C10` | `0x1D5D10` | `FUN_00889BD0` / `0x00889BD0` | Common object state routine; notify virtual `+0x48` with reason `3` at zero gauge. |
| BTL | `0x0088A7C0` | `0x1D68C0` | `FUN_0088A780` / `0x0088A780` | Set active-request latch halfword `+0xE8 = 3`. |
| BTL | `0x0088A890` | `0x1D6990` | `FUN_0088A850` / `0x0088A850` | Common reason-`3` state handler; conditionally invoke terminal setter. |
| BTL | `0x0088A930` | `0x1D6A30` | `FUN_0088A8F0` / `0x0088A8F0` | Common state-4 exit; animation completion requests reason `3`. |
| BTL | `0x00889360` | `0x1D5460` | `FUN_00889320` / `0x00889320`, truncated | Copy the side's support record, deactivate the attack list, notify identifier zero, and increment local `+0x116`. |
| BTL | `0x0088B150` | `0x1D7250` | `FUN_0088B110` / `0x0088B110`, split | Contact-result predicate which can replace state `1/2` with reason `4`. |
| BTL | `0x00887830` | `0x1D3930` | `FUN_008877F0` / `0x008877F0` | Reset occupied supports through reason `1`, then disable their two callback masks. |
| BTL | `0x008850E0` | `0x1D11E0` | `FUN_008850A0` / `0x008850A0`, truncated | Build and append support-local presentation nodes. |
| BTL | `0x0088F220` / `0x0088F390` | `0x1DB320` / `0x1DB490` | `FUN_0088F1E0` / `FUN_0088F350` | Release specialized linked-node lists before common support destruction. |
| BTL | `0x0088ED10` | `0x1DAE10` | `FUN_0088ECD0` / `0x0088ECD0` | Code-`0x3F` destructor; request valid indexed-effect retirement before common support destruction. |
| BTL | `0x0088C1D0` | `0x1D82D0` | `FUN_0088C190` / `0x0088C190`, truncated | Bind named state-script command bytes through owned wrappers. |
| BTL | `0x0088C3A0` | `0x1D84A0` | `FUN_0088C360` / `0x0088C360`, truncated | Walk the current state script and dispatch matching authored positions. |
| BTL | `0x0088E9B0` | `0x1DAAB0` | `FUN_0088E970` / `0x0088E970`, truncated | Resolve six attack names against the valid indexed player and copy found scene vectors into attack samples. |
