# Native chakra and guard state

This document maps retail NA2 (`SLPS-25837`) fighter-side chakra and guard
state used while `BTL.BIN` is active. Values such as `5.0` and `15.0` below are
raw native `float32` units. No claim is made that one raw unit corresponds to a
particular number of pixels, icons, bars, or displayed percent.

## Research coverage

- **Assigned scope:** retail NA2 battle-time native chakra and guard resource
  state: fighter fields, current/maximum values, gain/spend/clamp and reset
  lifecycle, representative non-substitution callers, and any provable guard
  durability/break state.
- **Exploration depth:**
  - Resident `SLPS_258.37` and `PRG/BTL.BIN` instructions, raw bytes, data, and
    Ghidra exports: the resident chakra core `FUN_002254A0..FUN_002260D0`, its
    combined, lifecycle, temporary-effect, manager, and event callers, the
    guard entry/exit/input/hit routes, and the listed overlay event, debit,
    guard-setter, and attack-dispatch paths.
  - Exhaustive within stated bounds: all 138 temporary-effect definitions for
    chakra blocker bits; all 74 static configuration containers passed to
    `FUN_002151E0`; direct resident writers of fighter `+0x70` and
    `+0x95A/+0x95C`; aligned direct-JAL scans of both images for the
    add/subtract/affordability, constructor/reset, and guard-setter targets;
    the 43-entry guard-sentinel dispatcher table; all 47 aligned overlay
    `+0x95A` loads; and all 13 direct resident `+0x95C` field instructions.
  - Bounded: every direct adder site and the seven overlay subtractor sites
    to their amounts and gates; all 18 overlay and four resident affordability
    calls to their amount sources and immediate branches; guard input/stance,
    the representative resident hit router, and the two overlay dispatchers;
    representative status records `0x0B/0x0E/0x3B/0x41/0x7C/0x88` and two
    controller variants' guard record choices. Character scripts were not
    semantically reconstructed.
- **Confirmed coverage:** fighter `+0x70` is the sole proven native
  current-chakra field and raw `15.0` is its literal maximum; all 74 directly
  instantiated retail configurations author initial `15.0`; gain, affordability,
  and ordinary spend use different effect/status gates; the
  `+0x7C/+0x80/+0x82/+0x84` reservation transaction can record, release, or
  commit even when arithmetic is suppressed; the upper/lower clamps, recovery
  multipliers, temporary-effect lifecycle, and representative resident/overlay
  callers are mapped. Manager keys `2` and `5` explain the two cached fighter
  gates `+0x169/+0x168`. Guard uses temporal state `+0x95A/+0x95C`, stance
  `(0,5)`, guarded responses `(0,6)/(0,7)`, and per-hit invalidation/branch
  flags; sentinel `-1` is consumed and cleared to select reaction `(5,0x4F)`,
  and overlay dispatcher values `0x14/0x27` author timing sentinel `-2`.
  Effect `0x0B` membership vetoes the tier-debit exception even at countdown
  zero; `0x3B/0x41` bypass applies only to the commit, not ordinary signed
  deltas. Zero-exit resource deltas differ from forced removal, and per-update
  aggregation precedes expiry. Guard-response/lock branches preserve `+0x95A`
  while input age updates; effect `0x09` supplies another `-2` timing writer.
  `FUN_00249D70` debits only for polygon-contact class 1. No cumulative
  guard-durability pool was established in the traced system (a negative
  result of medium confidence; see the unresolved exceptions).
- **Unresolved or untested:** computed or split-immediate indirect-call targets;
  broader action meanings of the two recovered guard-sentinel dispatcher cases;
  player-facing names for temporary-effect IDs and attack flags `0x00400000`, `0x00800000`,
  and `0x01000000`; controller-record float `+0x24`'s displayed meaning;
  dynamic reachability of combined status states; broader semantics of the
  recovered control object at live `0x008D6A10`; descriptive labels for the
  threshold-history pair, the reservation metadata, and the two guard timing
  counters, which are medium confidence; and possible exceptions involving
  computed addresses, wider accesses, or other scripted resource state. A
  durability claim would require a field with a proven initialization,
  guarded-hit decrement, clamp, and break consumer.
- **Deliberate exclusions and overlap:**
  - Substitution mechanics and cost belong to [Substitution](../characters/substitution.md);
    hit reactions to [Hit response](hit_response.md); damage to
    [Battle damage](damage.md); temporary-effect lifecycle to
    [Battle items and status effects](../projectiles_and_items/battle_items_and_status_effects.md).
  - The support gauge at fighter `+0x74` belongs to
    [Battle support mechanics](../characters/support_mechanics.md); the chakra bar to
    [Battle HUD](../session/battle_hud.md#chakra-storage-and-display); Practice settings to
    [Practice mode](../modes/practice_mode.md); AI candidate selection to
    [Battle AI](../session/battle_ai.md); action dispatch to
    [Combat action execution](combat_action_execution.md); polygon contact
    classes to [Stage surface attributes](../stages/stage_surface_attributes.md).
  - Adventure, physical controller bindings, UI units, and player-facing
    action, effect, or stage naming are excluded.
- **Evidence limitations:** Static evidence only. Raw-byte/JAL checks mitigate
  omitted or overlapping Ghidra functions, but static analysis cannot establish
  dynamic call frequency, timing units, UI representation, or the absence of
  every indirect/scripted exception.

## Source identity and address model

Retail file identities and address conversions are defined in
[Address conventions](../../game/files/file_identities.md#address-conventions).
Resident fighter/resource routines are in `SLPS_258.37`, even though the
battle overlay calls them. Overlay tables below list the Ghidra export,
`BTL.BIN` file, and loaded EE address.

## Fighter and action-record fields

All fighter offsets are relative to the live fighter object.

| Offset | Type | Proven role | Evidence and limits | Confidence |
| ---: | --- | --- | --- | --- |
| `+0x61` | `uint8` | Fighter status flags; bit `3` enables canonical chakra gain | `FUN_00214A40` clears bit `3`; `FUN_002151E0` sets it immediately before the configured initial-chakra add. `FUN_002254A0` returns without any arithmetic or requested side effects while the bit is clear. Other bits have unrelated fighter-state roles. | High for bit `3` operation |
| `+0x62` | `uint8` | Fighter resource/action status flags | Bit `0` blocks the canonical chakra adder. Bit `1` blocks canonical and inline ordinary debits. Bit `3` selects the flat-`5.0` branch of staged-input eligibility instead of the selected tier amount. Construction clears these bits; no player-facing names are inferred. | High for these bit operations |
| `+0x70` | `float32` | Current chakra | Read, added to, subtracted from, and clamped by the native resource routines. | High |
| — | literal `float32` | Chakra maximum `15.0` | `FUN_002254A0` upper-clamps to literal `15.0`; no separate per-fighter maximum field was found. | High |
| `+0x7C` | `float32` | Pending/refundable chakra reservation claim | `FUN_00225F50` records the requested amount here even when a spend-blocking effect suppresses the corresponding debit. `FUN_002260D0` attempts to add the amount back through the canonical adder, then clears it whether or not that adder is gated. | High |
| `+0x80` | `int16` | Reservation class index | Set to `1..3` with a reservation and cleared on release. No UI meaning is inferred. | High for operation; Medium for label |
| `+0x82` | `int16` | Reservation lifetime counter | Initialized to raw `0x3C` when a reservation is created and decremented by fighter maintenance until release at zero; an active effect flag `0x40` instead triggers immediate release. No time-unit conversion is inferred. | High for operation; Medium for label |
| `+0x84` | `int16` | Post-release staged-input lockout counter | Construction clears it. `FUN_002260D0(fighter, mode)` sets raw `0x3C` when `mode != 0`; `FUN_00225B60` rejects staged input while it is nonzero; `FUN_0024C440` decrements it during fighter maintenance. No time-unit conversion is inferred. | High for operation; Medium for label |
| `+0x164` | `float32` | Base chakra-recovery multiplier | Copied by `FUN_002151E0` from character-record word `0x36` (record byte `+0xD8`); used by charge and recovery paths. | High |
| `+0x168` | `uint8` | Ultimate Jutsu setting's staged-input inhibit | Initialized to `0` by `FUN_00216440`; `FUN_00216460` sets it to `1` exactly when manager key `5` is zero, otherwise `0`. Nonzero blocks `FUN_00225B60`. | High |
| `+0x169` | `uint8` | Chakra Unlimited ordinary-debit inhibit | Initialized to `0` by `FUN_00216440`; `FUN_00216460` sets it to `1` exactly when manager key `2` is nonzero, otherwise `0`. Value `1` blocks the simple subtractors and the documented inline/combined debit branches without necessarily blocking their surrounding action logic. | High |
| `+0x18C` | `int16` | Authored chakra-cost tier selector | Initialized to `0`; `FUN_002449C0` copies a selected table entry's tier byte here. Observed values `0/1/2` select raw costs and crossing thresholds `5.0/10.0/15.0`. This is a native tier, not a UI-unit claim. | High for operation; Medium for label |
| `+0x1A0` | `float32` | Chakra threshold-history old/baseline value | `FUN_00225A40` records the old sample here when processing threshold crossings. Native spend paths overwrite it with `15.0`. It is not established as a timer. | High for behavior; Medium for label |
| `+0x1A4` | `float32` | Chakra threshold-history new value | Paired with `+0x1A0` by `FUN_00225A40`. | High for behavior; Medium for label |
| `+0x1A8` | `uint8` | Full-threshold feedback latch | Initialized/rearmed to `1` and cleared after the charge path reports a `15.0` crossing. It gates feedback, not chakra storage. | High for operation; Medium for label |
| `+0x8C4` | `int32` | Temporary-effect count | Iteration bound used by `FUN_00307230`. | High |
| `+0x8C8` | pointer | First temporary-effect entry | List head used by `FUN_00307230`; active entries contribute their `+0x94` chakra modifier. | High |
| `+0x18E` | `int16` | Major action/state class | The guard stance uses class `0`. | High |
| `+0x190` | `int16` | Action/state within the class | State pair `(0,5)` is entered from the guard input path. | High |
| `+0x338` | `uint32` | Current logical input flags | Bit `0x08000000` drives the staged-chakra eligibility/debit path and bit `0x10000000` drives the guard input updater. This does not identify physical controller bindings. | High |
| `+0x95A` | `int16` | Guard-active/eligible hold-age state | Increments while guard is held and accepted, saturates at `0x7FFF`, and clears on release/ineligibility in the guard-processing branch. Response/lock preservation branches skip those writes. Hit routing tests `<1` versus `>=1`; `FUN_00232B80` consumes and clears sentinel `-1` before selecting reaction `(5,0x4F)`. It is not durability. | High |
| `+0x95C` | `int16` | Guard-input age/timing state | The input updater increments a nonnegative value while the logical guard bit is held and clears it on release; negative values advance toward zero even after release. Its halfword increment is unsaturated. It is reused by other eligibility logic and is not durability. | High for operations; Medium for broader meaning |

The generic action-record array begins at fighter `+0xA54`; records are
`0x54` bytes. Action-record `+0x20` is a native chakra cost `float32` consumed
by `FUN_0023A9A0`. Attack/hit record `+0x14` also contains at least three
guard-sensitive flags. Two invalidate `+0x95A`; a third preserves it while
selecting a distinct overlay-processing branch. They are documented under
guard rather than assigned unproven player-facing names.

Temporary-effect entries reached through fighter `+0x8C8` expose these
additional chakra fields:

| Effect-entry offset | Type | Proven operation | Confidence |
| ---: | --- | --- | --- |
| `+0x68` | `int32` | Authored effect-definition ID copied from definition record `+0x00`. | High |
| `+0x6C` | `int32` | Lifecycle/duration state; the modifier aggregators treat nonzero as active. | High for operation |
| `+0x70` | `uint32` | Effect behavior flags. Across active entries, bit `0x10` blocks staged-input eligibility, bit `0x40` blocks chakra gain and affordability, and bit `0x80` blocks ordinary spend. Adjacent bit `0x20` has an exact scanner but no chakra role was established. | High for scans and chakra gates |
| `+0x94` | `float32` | Recovery-factor contribution used as `value - 1.0`. | High |
| `+0xA4` | `float32` | Signed chakra delta applied when `FUN_00304910` constructs/attaches the entry. | High for timing and operation |
| `+0xA8` | `float32` | Signed chakra delta applied by `FUN_00304E90` at countdown zero; ordinary removal/destruction does not itself apply it. | High for timing and operation |
| `+0xB4` | `float32` | Signed delta accumulated by the per-fighter effect update. | High |
| `+0xB8` | `float32` | Current-chakra boundary used to suppress a `+0xB4` aggregate after the current value is already beyond the authored boundary. It is not a maximum field. | High for operation; Medium for label |

## Chakra routine map

| Symbol | EE runtime | ELF file | Role |
| --- | ---: | ---: | --- |
| `FUN_002145D0` | `0x002145D0` | `0x001146D0` | Base fighter-object constructor; constructs subordinate state and calls the fighter resource/state reset. |
| `FUN_00214A40` | `0x00214A40` | `0x00114B40` | Base fighter initialization; clears current chakra and related threshold history. |
| `FUN_002151E0` | `0x002151E0` | `0x001152E0` | Applies character configuration, base recovery multiplier, and configured initial chakra. |
| `FUN_002254A0` | `0x002254A0` | `0x001255A0` | Canonical chakra adder and upper clamp. |
| `FUN_00225780` | `0x00225780` | `0x00125880` | Canonical simple subtractor and lower clamp. |
| `FUN_00225830` | `0x00225830` | `0x00125930` | Feedback-selecting direct subtractor and lower clamp. |
| `FUN_00225940` | `0x00225940` | `0x00125A40` | Chakra affordability predicate. |
| `FUN_00225A40` | `0x00225A40` | `0x00125B40` | Detects threshold crossings and maintains `+0x1A0/+0x1A4`. |
| `FUN_00225B60` | `0x00225B60` | `0x00125C60` | Eligibility and affordability predicate for staged chakra input. |
| `FUN_00225F50` | `0x00225F50` | `0x00126050` | Records a pending reservation at `+0x7C`; its corresponding debit is conditional on spend gates. |
| `FUN_002260D0` | `0x002260D0` | `0x001261D0` | Attempts a refund through the canonical adder, then clears the reservation and metadata unconditionally. |
| `FUN_00227850` | `0x00227850` | `0x00127950` | Combined action/effect helper whose second float is a conditionally applied chakra debit. |
| `FUN_00227CE0` | `0x00227CE0` | `0x00127DE0` | Combined affordability, conditional spend, feedback, and authored-effect/event helper. |
| `FUN_00227EE0` | `0x00227EE0` | `0x00127FE0` | Chakra-charge action update. |
| `FUN_002369D0` | `0x002369D0` | `0x00136AD0` | General recovery-event router; can recover chakra and/or HP. |
| `FUN_00237060` | `0x00237060` | `0x00137160` | Event/action helper that releases a reservation through the conditional refund path, emits an event/effect, then conditionally consumes a small discrete chakra amount. |
| `FUN_0023A9A0` | `0x0023A9A0` | `0x0013AAA0` | Generic action-record dispatcher; conditionally consumes record `+0x20` chakra cost. |
| `FUN_002449C0` | `0x002449C0` | `0x00144AC0` | Maintains the selected authored cost tier at `+0x18C` and the corresponding dynamic action-record cost. |
| `FUN_00244F80` | `0x00244F80` | `0x00145080` | Finalizes a matching staged action by releasing the reservation and conditionally charging the selected `5/10/15` tier. |
| `FUN_00245340` | `0x00245340` | `0x00145440` | Action-phase path that releases a reservation, then conditionally charges the active action record's `+0x20` cost. |
| `FUN_00248EC0` | `0x00248EC0` | `0x00148FC0` | Fighter input update; includes the logical `0x08000000` staged-chakra debit path. |
| `FUN_00249D70` | `0x00249D70` | `0x00149E70` | Polygon-contact classifier with a class-1, gated raw `0.008333334` chakra debit. |
| `FUN_0024C440` | `0x0024C440` | `0x0014C540` | Fighter maintenance; expires pending reservations and implements the gated Practice Chakra Unlimited refill. |
| `FUN_00304910` | `0x00304910` | `0x00204A10` | Temporary-effect construction; applies entry `+0xA4` as an immediate signed chakra delta. |
| `FUN_00304D60` | `0x00304D60` | `0x00204E60` | Temporary-effect lifetime tick; at zero, applies cleanup, invokes the entry's expiry callback, and signals removal. |
| `FUN_00304E90` | `0x00304E90` | `0x00204F90` | Temporary-effect zero-countdown exit; applies entry `+0xA8` as a signed chakra delta. |
| `FUN_00305270` | `0x00305270` | `0x00205370` | Effect-list replace/create helper; constructs a new entry and inserts it only after construction returns. |
| `FUN_003059B0` | `0x003059B0` | `0x00205AB0` | Per-fighter temporary-effect update; routes the aggregate from `FUN_00307020`. |
| `FUN_00305C30` | `0x00305C30` | `0x00205D30` | Higher-level authored-effect application path; supplies the definition lifetime and calls the list helper. |
| `FUN_00306220` | `0x00306220` | `0x00206320` | Signed chakra-delta router to the canonical adder or subtractor. |
| `FUN_00307020` | `0x00307020` | `0x00207120` | Aggregates active temporary-effect `+0xB4` deltas and applies `+0xB8` boundary gating. |
| `FUN_00307230` | `0x00307230` | `0x00207330` | Aggregates temporary chakra-recovery modifiers. |
| `FUN_003073A0` | `0x003073A0` | `0x002074A0` | Reports any active temporary-effect entry with behavior flag `0x10`; used as a staged-input blocker. |
| `FUN_00307410` | `0x00307410` | `0x00207510` | Reports any active temporary-effect entry with behavior flag `0x20`; no chakra role is assigned here. |
| `FUN_00307480` | `0x00307480` | `0x00207580` | Reports any active temporary-effect entry with behavior flag `0x40`; blocks chakra gain and affordability. |
| `FUN_003074F0` | `0x003074F0` | `0x002075F0` | Reports any active temporary-effect entry with behavior flag `0x80`; blocks ordinary spend unless a caller explicitly bypasses it. |
| `FUN_00307B20` | `0x00307B20` | `0x00207C20` | Membership-priority predicate: present ID `0x0B` returns false; otherwise `0x3B` or `0x41` returns true. It does not test `+0x6C`; staged commit uses a true result to bypass the active `0x80` scan. |
| `FUN_0035AF20` | `0x0035AF20` | `0x0025B020` | Manager callback with a positive-only, target-minus-current chakra top-up path. |
| `FUN_00374190` | `0x00374190` | `0x00274290` | Battle-event object dispatcher; event type `0x0C` adds raw `15.0`, while other recovery-class events route through `FUN_002369D0`. |

Representative direct imports from the battle overlay:

| Export bytes/function | Ghidra export | `BTL.BIN` file | Loaded EE | Chakra operation |
| --- | ---: | ---: | ---: | --- |
| `FUN_0070BBE0` | `0x0070BBE0` | `0x00057D20` | `0x0070BC20` | Event dispatcher; event byte `0x0C` adds raw `15.0`, while recovery-class events call `FUN_002369D0`. |
| `FUN_007116E0` | `0x007116E0` | `0x0005D820` | `0x00711720` | Table-driven event handler; event `0x5D` adds raw `2.5` through `FUN_002254A0`. |
| `FUN_00790830` | `0x00790830` | `0x000DC970` | `0x00790870` | Controller-object path that passes its positive raw `+0x5E8` amount to `FUN_00225780` for fighter pointer `+0x31C`. |
| `FUN_007C47A0` | `0x007C47A0` | `0x001108E0` | `0x007C47E0` | Small wrapper that requests a raw `7.5` subtraction from fighter pointer `+0x4CC`. |
| `FUN_007C6500` | `0x007C6500` | `0x00112640` | `0x007C6540` | When object `+0x550 -> +0x14` bit `0` is set, requests a raw `5.0` subtraction from fighter pointer `+0x4CC`. |
| `FUN_007F0C00` | `0x007F0C00` | `0x0013CD40` | `0x007F0C40` | Controller path that conditionally requests its raw `+0x10D8` amount from fighter pointer `+0x31C`. |
| `FUN_007FDE00` | `0x007FDE00` | `0x00149F40` | `0x007FDE40` | Larger controller update that passes a computed aggregate to the subtractor for fighter pointer `+0x4CC`. |
| `FUN_00818340` | `0x00818340` | `0x00164480` | `0x00818380` | Requests raw `5.0`, or raw `2.5` when its object gate is clear and fighter `+0x95A` is nonzero, from fighter pointer `+0x9D4`. |
| `FUN_00847030` | `0x00847030` | `0x00193170` | `0x00847070` | Controller update that requests a raw `1.25` subtraction from fighter pointer `+0x31C`. |

An aligned raw-word census over the retail overlay gives the complete direct-JAL
counts below. File offsets map unambiguously to export and loaded addresses.

| Resident target | Instruction bytes | Count | `BTL.BIN` file offsets |
| --- | --- | ---: | --- |
| `FUN_002254A0` | `28 95 08 0C` | 2 | `0x00057EF8`, `0x0005D9CC` |
| `FUN_00225780` | `E0 95 08 0C` | 7 | `0x000DCA14`, `0x001108F8`, `0x00112674`, `0x0013CE00`, `0x0014A370`, `0x00164544`, `0x001933CC` |
| `FUN_00225940` | `50 96 08 0C` | 18 | `0x0003E984`, `0x00044E20`, `0x00045850`, `0x00045950`, `0x000473C8`, `0x000474A0`, `0x000487B0`, `0x00048AB8`, `0x00048DA4`, `0x00049718`, `0x00049840`, `0x0004A720`, `0x0004B0CC`, `0x0004CBD8`, `0x0004D57C`, `0x0004E008`, `0x0004E21C`, `0x00050D4C` |

All listed words occur in decoded call contexts, not unexecuted table padding.
The raw census does not cover indirect calls.

A byte search of both mapped programs found no four-byte literal
function pointer to `0x002254A0`, `0x00225780`, `0x00225830`, `0x00225940`,
`0x00225B60`, `0x00225F50`, `0x002260D0`, `0x00228250`, or `0x00229B70`.
This excludes static absolute-pointer tables for those nine entrypoints in the
searched images. It does not exclude an address assembled from separate
immediates, calculated indirectly, or supplied by another loaded component.

The resident ELF has four aligned direct JALs to `FUN_00225780`, at file
offsets `0x0011E44C`, `0x0018F5F0`, `0x002064A4`, and `0x0025BBC8`
(runtime `0x0021E34C`, `0x0028F4F0`, `0x003063A4`, and `0x0035BAC8`). At all
four resident sites and all seven overlay sites, the call setup passes zero in
`a1`, the subtractor's effect-scan bypass argument. Thus no direct caller in
either retail image exercises a nonzero bypass. At the overlay site at file
`0x00164544`, which has no recovered Ghidra function, the raw preceding word at
`0x00164540` is `0x0000282D` (`move a1, zero`) and the JAL word itself is
`0x0C0895E0`.

The same aligned scan found no direct overlay JAL to
`FUN_00225830`, `FUN_00225B60`, `FUN_00225F50`, `FUN_002260D0`,
`FUN_00227850`, or `FUN_00227CE0`. Thus the overlay imports the
simple add/subtract/affordability surface directly, while staged-reservation
creation, release, and commit remain resident-owned in the proven paths. This
is a direct-call negative result, not a claim about every possible indirect
dispatch.

### Initialization, maximum, and reset/refill

`FUN_00214A40` clears fighter `+0x70`, reservation fields `+0x7C/+0x80/+0x82`,
threshold history `+0x1A0/+0x1A4`, and guard counters `+0x95A/+0x95C` during
base construction. `FUN_002151E0` then:

1. copies character-record word `0x36` to fighter `+0x164`;
2. calls the HP initializer with configuration word `param_2[7]`; and
3. calls `FUN_002254A0(param_2[8], fighter, 0, 0, 1)`.

Thus configuration word `param_2[8]` (container byte `+0x20`) is the native
initial-chakra input. Because construction starts at zero, the adder establishes
the initial current value while applying its normal maximum and threshold
logic. The initializer itself does not hard-code “start full.”

The direct-call lifecycle is bounded by raw-JAL censuses. The resident
ELF contains exactly one direct call to `FUN_00214A40`, at file
`0x00114910` / runtime `0x00214810`, inside base constructor
`FUN_002145D0`. It contains 74 direct calls to `FUN_002151E0`, distributed
across the specialized fighter constructors that supply their static
configuration records. The battle overlay contains no direct JAL to
either routine. Therefore the proven direct lifecycle is base zeroing followed
by configured initialization; the overlay does not directly reset or
reconfigure chakra. This is not a claim about possible indirect calls.

Those 74 direct calls supply 74 distinct static configuration containers. An
exhaustive data read found `0x41700000` (`15.0`) at container `+0x20`
for every one. Thus all directly instantiated retail fighter configurations
are authored to start at the raw maximum, even though
`FUN_002151E0` itself accepts a general value and does not hard-code “full.”
Each container's word `+0x00` points to the copied character record whose
`+0xD8` word becomes fighter recovery multiplier `+0x164`; those 74 records
have this exact distribution:

| Raw `+0x164` multiplier | IEEE-754 bits | Configuration count |
| ---: | ---: | ---: |
| `0.80` | `0x3F4CCCCD` | 4 |
| `0.85` | `0x3F59999A` | 3 |
| `0.90` | `0x3F666666` | 11 |
| `0.95` | `0x3F733333` | 2 |
| `1.00` | `0x3F800000` | 32 |
| `1.10` | `0x3F8CCCCD` | 9 |
| `1.15` | `0x3F933333` | 5 |
| `1.20` | `0x3F99999A` | 5 |
| `1.50` | `0x3FC00000` | 3 |

The counts total 74 and keep the authored recovery factor distinct from the
initial fill and maximum. They imply neither a UI scale nor a time conversion.

The proven native maximum is raw `15.0`. `FUN_002254A0` stores exactly
`15.0` when the sum is above `15.0` or within `0.001` of it. The same code uses
raw thresholds `5.0`, `10.0`, and `15.0` for threshold-crossing feedback; these
constants are not evidence for a particular UI representation.

The threshold selected by the adder is not inferred from current chakra.
`FUN_002449C0` obtains an authored byte through `FUN_00372CB0` (table byte
`0x005AEC49 + index * 0x14`) and stores it at fighter `+0x18C`. For tiers
`0/1/2`, it writes raw `5.0/10.0/15.0` to the selected dynamic action record's
`+0x20` cost. `FUN_002254A0` uses the same tier-to-value mapping when its
threshold flag is enabled. Constructor `FUN_00214A40` starts the tier at zero;
a selected-record change in `FUN_002449C0` also releases any pending
reservation before replacing the dynamic record data.

Fighter maintenance `FUN_0024C440` implements the Practice Chakra Unlimited
refill on every admitted update. Its gates are:

- manager pointer `0x00607600` is nonnull and manager `+0x0C == 3`;
- the fighter is not in major action `8`, `5`, or `6`;
- fighter `+0xB00` is zero;
- the low five bits of word `0x006073FC + 0x194` are clear;
- pending reservation `+0x7C` is zero; and
- `FUN_001F6420(manager, 2) == 1` (Practice Chakra key `2`, Unlimited).

When all pass, it calls `FUN_002254A0(15.0, fighter, 0, 0, 0)`. For a
nonnegative current value this saturates the fighter to raw `15.0` through
the standard clamp, subject to the adder's own gain gates. The reservation
gate keeps the refill out of an active staged-cost transaction. No
independent per-fighter maximum field or separate mid-round direct “reset to
max” setter was found in the traced native paths.

### Manager settings behind the fighter gates

`FUN_00216460` obtains both bytes from resident manager settings, rather than
from a character-specific chakra maximum. Its call at runtime `0x00216478`
(ELF `0x00116578`) reaches `FUN_001F6E10`, whose wrapper passes key `5` to
`FUN_001F6420`. The result is reduced to
`fighter[+0x168] = (setting == 0)`. Its call at runtime `0x002164A0`
(ELF `0x001165A0`) reaches `FUN_001F6DE0`, whose wrapper passes key `2`;
the result becomes `fighter[+0x169] = (setting != 0)`.

The getter's 19-entry jump table is at resident `0x005C0AA0`. Key `2`
targets `0x001F6528`: manager modes `2` and `3` read bit `2` of manager
`+0x9F4`, while other modes read bit `2` of `+0xA00`. Key `5` targets
`0x001F6684`: modes `2` and `3` read byte `+0x9F6`, while other modes return
literal `2`. The setting labels and retail Practice values are established in
[Practice mode](../modes/practice_mode.md#rows-local-values-and-manager-storage):
key `2` is Chakra Normal/Unlimited (`0/1`), and key `5` is Ultimate Jutsu,
with No Use at `0` and five positive modes. Thus Unlimited suppresses ordinary
debits through `+0x169`; it does not change the affordability predicate or
increase the native maximum. The separate maintenance refill still has the
gates described above. Positive Ultimate Jutsu modes all clear `+0x168`;
their later skill-play differences do not live in this one-byte gate.

Direct resident references to `FUN_00216460` are fighter configuration
`FUN_002151E0` and `FUN_001EBD90`. The latter calls it for both manager fighter
pointers `+0xDE4/+0xDE8` after its overlay-controlled result is `1`. This
establishes a later refresh of both cached fighter gates; no per-update
refresh or additional indirect caller is claimed.

### Gain and clamp behavior

`FUN_002254A0(amount, fighter, effect_flag, event_flag, threshold_flag)` is the
central gain function:

- it returns without changing chakra when any active temporary-effect entry has
  behavior flag `0x40`, fighter byte `+0x62` bit `0` is set, or fighter byte
  `+0x61` bit `3` is clear;
- otherwise it stores `fighter[+0x70] + amount` and upper-clamps to raw
  `15.0`;
- it does **not** lower-clamp. Native callers use it as a nonnegative adder;
- `threshold_flag` enables the `5/10/15` crossing test through
  `FUN_00225A40`, plus its associated sound/effect calls;
- `effect_flag` emits resource feedback through `FUN_001D87C0` and
  `FUN_0033CCD0`; and
- `event_flag` calls `FUN_002040D0(fighter, 0x19, -1, 1)`.

The flag names describe observed side effects rather than recovered original
names.

More exactly, `FUN_00225A40(old, new, threshold, fighter)` reports an upward
crossing only for `old < threshold <= new`, and a downward crossing only for
`new <= threshold < old`. It does nothing when `old == new`, when the threshold
is outside the closed old/new interval, or while the nested battle-manager
state at manager `+0x14` is nonzero. On an otherwise eligible interval it uses
`+0x1A0/+0x1A4` to suppress a repeated transition that ends at the same `new`
sample without advancing beyond the prior baseline, then stores `(old,new)`
back to that pair. Thus the pair is last-eligible-transition history, not a
second chakra value or timer. Spend paths write `15.0` only to
`+0x1A0`, biasing the next duplicate-suppression comparison while leaving
current chakra at `+0x70`.

`+0x1A8` is a separate one-byte feedback latch. Construction sets it to `1`;
`FUN_00227EE0` rearms it when the charge action's `+0x1B8` condition fires,
and clears it after the charge path accepts a raw `15.0` crossing. The adder
also consults it for the full-threshold feedback while action `(0,4)` is
active. No resource arithmetic uses this byte.

`FUN_00307230(fighter)` produces the temporary recovery factor. It starts at
`1.0`, walks `fighter[+0x8C8]` for `fighter[+0x8C4]` entries, and for each
active entry (`entry+0x6C != 0`) adds `entry[+0x94] - 1.0`. Multiple active
effects therefore stack as deviations from `1.0`, not as a product.

The retail effect definitions that carry chakra blocker bits are IDs
`0x0A`/`0x7C` (bits `0x10`, `0x20`, and `0x40`) and `0x0B`, `0x0E`, `0x0F`,
`0x21`, `0x27..0x2B`, and `0x38` (bit `0x80`); no other definition sets any
of these bits. Their routing flags, lifetimes, and signed entry/zero-exit
deltas are listed in
[Routing flags](../projectiles_and_items/battle_items_and_status_effects.md#routing-flags),
[Base countdowns](../projectiles_and_items/battle_items_and_status_effects.md#base-countdowns), and
[Entry and ordinary-expiry resource deltas](../projectiles_and_items/battle_items_and_status_effects.md#entry-and-ordinary-expiry-resource-deltas).
All of these blocker definitions author recovery modifier `+0x94` as `1.0`;
their effect on chakra therefore comes from the gates and signed deltas, not
from recovery-factor scaling. These are raw IDs, not player-facing effect
names.

Two item records carry these IDs as direct effects. Resident
`FUN_003764E0(code)` reads the signed direct-effect halfword at
`0x005B04F8 + code * 0x0C`: item `0x0C` (record runtime/file
`0x005B0580/0x004B0680`) carries effect `0x0B`, and item `0x29` (record
`0x005B06DC/0x004B07DC`, kind `3`, flags `0x0180`) carries effect `0x0A`. The
[field-item name reference](../../localization/field_item_names.md) names item
`0x0C` Energy Pills and
[qualifies the name of item `0x29`](../../localization/field_item_names.md#code-29-curse-tag-chakra-points-seal).
These establish item-to-effect associations, not a unique player-facing name
for every use of effect `0x0A` or `0x0B`. The hit-carried application path
and remaining mappings are owned by
[Battle items and status effects](../projectiles_and_items/battle_items_and_status_effects.md#direct-effect-records-carried-by-hit-objects).

Temporary effects change chakra through three signed-delta routes: entry
`+0xA4` when `FUN_00304910` constructs the entry, `+0xA8` when
`FUN_00304E90` runs at countdown zero, and the per-update `+0xB4` aggregate
that `FUN_00307020` folds against `+0xB8` boundaries. Countdown, removal,
replacement, and fold rules are owned by
[Countdown pass](../projectiles_and_items/battle_items_and_status_effects.md#countdown-pass),
[Entry and ordinary-expiry resource deltas](../projectiles_and_items/battle_items_and_status_effects.md#entry-and-ordinary-expiry-resource-deltas),
and [Signed sums and their boundaries](../projectiles_and_items/battle_items_and_status_effects.md#signed-sums-and-their-boundaries).
Their chakra consequences are:

- An effect's own `0x40/0x80` flag never suppresses its own entry or
  zero-exit delta. `FUN_00305270` inserts a new entry only after
  `FUN_00304910` has routed its `+0xA4` delta, and `FUN_00304D60` calls
  `FUN_00304E90` after countdown `+0x6C` is already zero, so the active-flag
  scanners ignore that entry. Other active entries can still block either
  delta through the canonical gain/spend gates.
- `+0xA8` is applied only at countdown zero, not by forced removal or
  same-ID replacement, so replacing a still-positive node can repeat its
  `+0xA4` delta without applying its `+0xA8`. A negative lifetime such as ID
  `0x7C`'s `-1` never reaches the zero exit, so its authored `-15.0` exit
  delta is not evidence of a debit.
- Boundary equality still forwards the whole per-update delta
  (`FUN_00307020` instructions `0x003070FC..0x00307124`). At current `15.0`,
  ID `0x88`'s approximately `+0.05` delta with boundary `15.0` still reaches
  the adder, whose clamp keeps current at `15.0`. A surviving negative delta
  with boundary zero still reaches the simple subtractor at current zero;
  with spend gates clear, current stays zero but `+0x1A0` is written to
  `15.0`. Unchanged current therefore does not prove that the resource
  routine was skipped.
- In `FUN_003059B0`, the chakra fold call at `0x00305A74` and signed-router
  call at `0x00305AA0` precede the countdown tick at `0x00305B78`, so a node
  entering with countdown `1` can contribute its per-update delta before its
  zero-exit delta on the same pass. Aggregation and countdown have separate
  gates; skipped aggregation does not establish skipped expiry, or vice versa.

All three direct calls then use
`FUN_00306220(signed_amount, -1.0, fighter)`. The router first requires fighter
byte `+0x62` bit `0` clear, `FUN_00244110() == 0`,
`FUN_00244130(fighter) == 0`, and the same predicate to be zero for the linked
fighter at `fighter+0x20`. It then sends a positive amount to
`FUN_002254A0` with flags `(0,0,0)` and the magnitude of a negative amount to
`FUN_00225780` with flag `0`. Those canonical callees still enforce effect
flags `0x40` and `0x80`, respectively. The
canonical `15.0` upper clamp and `0.0` lower floor therefore still own the
actual resource bounds. The router contains a second-argument boundary gate,
but all three static callers pass `-1.0`; even when enabled, assembly shows
that this gate only suppresses the call or passes the original amount, rather
than trimming the amount to that boundary.

Those action predicates have bounded instruction definitions. Complete
`FUN_00244130` returns one only for major state `8` with nonnull active
record `+0xA4C`, record `+0x10 & 0x000C0000`, and signed record byte
`+0x19 > 0`; applying it to both fighters can suppress the signed delta
even if the target fighter's canonical gain/spend gate would otherwise pass.
`FUN_00244110` forwards the return register from live BTL wrapper
`0x007064B0` (bytes at Ghidra `0x00706470`). The wrapper supplies absolute
live pointer `0x008D6A10` to live helper `0x007069F0` (bytes at Ghidra
`0x007069B0..0x007069CC`), which returns true exactly when object word
`+0x3C` and byte `+0x38` are both nonzero. No player-facing label is assigned to this control object. The resident
aggregation gate's `FUN_002354C0` separately recognizes state `(6,0x61)`
or `(6,0x62)`, while `FUN_00216820` reads the nested manager
`+0x08 -> +0x14` state already used by threshold feedback. These are additional
resource suppression predicates, not additional maximum or current fields.

One exact side effect follows a successful negative delta of magnitude
`15.0`: if fighter `+0x7C` is nonzero, the router clears `+0x7C` and calls
`FUN_002260D0(fighter, 0)`. Because it clears the pending reservation first,
the reset helper cannot refund it; the reservation metadata is still cleared.

Representative non-substitution gain callers are:

- `FUN_00227EE0`, dispatched by `FUN_00249640` for action `(0,4)`, performs
  one charge-action update of
  `fighter_or_linked_source[+0x164] * 0.05 * FUN_00307230(fighter)` and calls
  the adder with flags `(0,0,1)`. This is an update formula only; no per-second
  conversion is inferred.
- `FUN_002369D0(base, fighter, event)` checks the event classification and,
  for a chakra-recovery event, adds
  `base * fighter[+0x164] * FUN_00307230(fighter)` with flags `(1,1,1)`.
- Loaded `BTL.BIN` function `0x00711720` (export
  `FUN_007116E0`, file `0x0005D820`) handles table-driven event IDs. Event
  byte `0x5D` calls resident `FUN_002254A0` with literal `2.5` and flags
  `(1,1,1)`, then invokes local overlay feedback when its controller pointer
  exists. That local JAL's encoded/live target is `0x0070D5F0`; the target
  bytes are at export `FUN_0070D5B0` / file `0x000596F0`, although the
  displaced Ghidra call reference is labeled `FUN_0070D5F0`. The resident
  chakra call instruction is loaded at `0x007118CC` (export `0x0071188C`,
  file `0x0005D9CC`).
- Loaded `FUN_0070BC20` (export `FUN_0070BBE0`, file `0x00057D20`) is a
  second event entry. It passes its computed base and event byte to
  `FUN_002369D0`; when that event byte is `0x0C`, it additionally calls the
  canonical adder with raw `15.0` and flags `(1,0,1)`. That add instruction is
  at export/file/live `0x0070BDB8/0x00057EF8/0x0070BDF8`. Its call to the
  recovery router is at `0x0070BCF8/0x00057E38/0x0070BD38`.
- Resident battle-event dispatcher `FUN_00374190` handles its event type
  `0x0C` by adding raw `15.0` with adder flags `(1,0,1)`. Other event types
  classified by the adjacent recovery predicates route to
  `FUN_002369D0`; this is another non-substitution event entry into the same
  canonical recovery machinery.
- Resident manager callback `FUN_0035AF20` has a positive-only synchronization
  path. When manager `0x00607600` exists with `+0x0C != 6` and
  `FUN_00373790() == 2`, it chooses fighter pointer `manager+0xDE8` for side
  index `0` or `manager+0xDE4` otherwise. If callback-state `+0x1C` exceeds
  that fighter's current `+0x70`, it passes exactly `target - current` to the
  adder with flags `(0,0,1)`. It does nothing to chakra when the target is not
  higher, so this is a gated top-up rather than an assignment or downward
  reset.

An aligned direct-JAL census accounts for every direct canonical-adder import
in the two retail images: eight in the resident ELF and two in `BTL.BIN`. The
resident sites are configured initialization, reservation release, charge,
general recovery, Practice refill, the signed effect router's positive branch,
the manager top-up, and event type `0x0C`; the two overlay sites are the
`0x0C` and `0x5D` event paths above. No other direct adder caller is omitted
from this map. Indirect dispatch remains outside that census.

### Spend, affordability, and lower clamp

`FUN_00225940(amount, fighter)` is a pure affordability predicate in the
traced path: zero cost succeeds, while nonzero cost fails when any active
temporary-effect entry has behavior flag `0x40` or
`fighter[+0x70] < amount`.

#### Direct affordability callers

The resident image has four primary-address JALs to `FUN_00225940`:

| Call EE / ELF file | Owner and amount source | Immediate consequence |
| --- | --- | --- |
| `0x0021D704 / 0x0011D804` | `FUN_0021D380`: sum of `+0x20` costs along at most four `0x54`-byte action records, following signed next-index byte `+0x18`; absent initial record proposes raw `30.0`. | Failure rejects the queued action before staged reservation and action queue writes. The selected chain can start from a record referencing the requested action through `+0x18` and flag `+0x1C & 0x08000000`. |
| `0x0025DD48 / 0x0015DE48` | `FUN_0025DCC0`: raw `1.5`. | Successful affordability permits the feedback-selecting raw `1.5` debit; spend gates still apply. |
| `0x00284940 / 0x00184A40` | `FUN_00283A70`: `FUN_0021D270` computes the same bounded four-record cost sum for the remapped queued record. | Failure replaces fighter queued index `+0xA3E` with `0x23`; this check is action selection, not a debit. |
| `0x002B94D8 / 0x001B95D8` | `FUN_002B9400`: raw `1.5`. | Successful affordability permits the feedback-selecting raw `1.5` debit; spend gates still apply. |

For the overlay calls below, `S = slot * 0x1E0` and
`F = *(0x008D65AC + S)`. Controller-local `+0x1C` pointers in these paths
resolve to the same selected fighter. File and live call addresses identify
each of the 18 sites individually; the argument is the value actually placed
in `f12`, not an inferred action cost.

| `BTL.BIN` file / live call | Raw amount or source | Resource-gate behavior |
| --- | --- | --- |
| `0x0003E984 / 0x006F2884` | Selected action record `+0x20`, fighter `F`. | Applied for record flags `+0x10 & 0x000F0000`; failure returns zero from candidate eligibility. A zero-cost record has an additional record `+0x0E == 1` requirement. |
| `0x00044E20 / 0x006F8D20` | `float32(FUN_00372CB0(int32(record[+0x20])))`, fighter controller `+0x1C`. | Failure skips submission of the selected controller `+0x1B0` action to `FUN_0021D380`; success reaches that submission. This passes the signed tier byte directly, with no `(tier+1)*5` conversion. |
| `0x00045850 / 0x006F9750` | `FUN_00217930(fighter, controller[+0x1B0])->+0x20`. | Failure selects controller flag word `+0x10 = 8` and clears its `+0xE8` counter. Success still requires fighter state `(0,0)` before setting candidate input flags. |
| `0x00045950 / 0x006F9850` | Chosen candidate record `+0x20`, after the local candidate chooser and `FUN_00217930`. | Failure selects the same `8`/counter-clear path; success submits the chosen action to `FUN_0021D380`. |
| `0x000473C8 / 0x006FB2C8` | `FUN_00217930(fighter, controller[+0x1B0])->+0x20`. | Failure skips this candidate path; success still requires fighter state `(0,0)` before candidate input flags are set. |
| `0x000474A0 / 0x006FB3A0` | Chosen candidate record `+0x20`, after the local candidate chooser and `FUN_00217930`. | Failure skips submission; success calls `FUN_0021D380` with the chosen record index. |
| `0x000487B0 / 0x006FC6B0` | `5.0`, fighter `F`. | Success returns zero from the enclosing selector. Failure continues its candidate/event selection. |
| `0x00048AB8 / 0x006FC9B8` | `5.0`, fighter `F`. | Its physical block also returns zero when affordable, but is unreachable on the recovered enumeration path because that path already excludes the required world-record type `2`. |
| `0x00048DA4 / 0x006FCCA4` | `5.0`, fighter `F`. | Same inverse selection gate before remaining candidate-state writes. |
| `0x00049718 / 0x006FD618` | `2.5`, fighter `F`. | Reached for polygon-contact word `(F[+0xBB4] & 0x00F0F0F0) == 0x00E0E000`; failure alone reaches an additional random-selection branch. |
| `0x00049840 / 0x006FD740` | `2.5`, fighter `F`. | Under manager byte `+0x98 == 0x0C`, failure alone reaches another dispatcher-state-dependent selection branch. |
| `0x0004A720 / 0x006FE620` | `1.0`, controller `+0x1C`. | Failure skips the next chance/candidate branch; success still passes its local counter, state, and probability checks. |
| `0x0004B0CC / 0x006FEFCC` | `1.0`, controller `+0x1C`. | Same availability requirement before a chance branch; no resource mutation at this call. |
| `0x0004CBD8 / 0x00700AD8` | `1.0`, controller `+0x1C`. | Failure skips its candidate branch; success permits its later probability calculation. |
| `0x0004D57C / 0x0070147C` | `1.0`, fighter `F`. | Failure skips the branch that refreshes per-slot countdown state and performs a chance calculation. |
| `0x0004E008 / 0x00701F08` | `10.0`, fighter `F`. | Success returns zero immediately from the helper. Failure continues through effect and spatial/state gates. |
| `0x0004E21C / 0x0070211C` | `5.0`, fighter `F`, in the same helper. | Splits later selector behavior: success consults slot `0x008D666C+S`; failure uses spatial/state gates and can select dispatcher state `0x15`. |
| `0x00050D4C / 0x00704C4C` | `12.0`, controller `+0x1C`. | Under its prior candidate gates, failure and a zero controller `+0xDC` counter select controller `+0x34 = 0x15`, set `+0x90 = 1`, and refresh two counters. Success skips that low-resource branch. |

Argument setup and branches were decoded from instruction bytes, including
call delay slots. The direct tier-byte precheck at live `0x006F8D20` is
distinct from the eventual bounded-chain cost check in
`FUN_0021D380` and from committed `5/10/15` tier spending. The complete
candidate-selection logic belongs to [Battle AI](../session/battle_ai.md); these calls
establish availability decisions only. None mutates current chakra.

The physical 18-call count does not imply 18 reachable decisions. In the
radius-limited selector entered at export/live `0x006FC7B0/0x006FC7F0`,
instruction export/live/file `0x006FC860/0x006FC8A0/0x000489A0` skips a
candidate whose local world-record type byte at `sp+0x60` is `2`. The later
block at export `0x006FC8BC..0x006FC998` requires that same byte to be `2`
before reaching the call at live `0x006FC9B8`. The intervening calls do not
receive the type-byte address, so this call is unreachable on that recovered
enumeration path. Its encoded argument and branch remain part of the physical
census; no execution or unconditional reachability is inferred for it.

#### Debit and reservation behavior

The three principal gate surfaces differ:

| Operation | Temporary-effect gate | Fighter-field gates | Result when blocked |
| --- | --- | --- | --- |
| Canonical add `FUN_002254A0` | active flag `0x40` | `+0x62` bit `0` must be clear; `+0x61` bit `3` must be set | Void return before resource arithmetic and before all requested feedback/event side effects. |
| Affordability `FUN_00225940` | active flag `0x40`, except an exactly zero cost bypasses the scan | No `+0x169` or `+0x62` bit `1` test | Returns `0` for a blocked nonzero request; it does not prove that a later debit gate will pass. |
| Simple debit `FUN_00225780` | active flag `0x80` only when `bypass_flag == 0` | `+0x169 != 1`; `+0x62` bit `1` must be clear | Returns `0` without arithmetic. A nonzero bypass skips only the effect scan, never the two fighter-field gates. |

This explains why “affordable” and “debited” are not equivalent: flag `0x40`
owns availability/gain, while flag `0x80` and the two fighter status fields own
ordinary spend. Staged-input eligibility adds its own flag-`0x10`, `+0x168`,
and `+0x84` gates before either surface.

`FUN_00225780(amount, fighter, bypass_flag)` is the central simple subtractor.
Unless its resource/status gates reject the operation, it performs:

```text
fighter[+0x70] = max(fighter[+0x70] - amount, 0.0)
fighter[+0x1A0] = 15.0
```

It returns `1` on that mutation and `0` when gated. The helper itself floors an
overspend instead of rejecting it, so callers that require affordability check
before invoking it. `FUN_00227CE0` is one such combined helper: it checks the
available amount and returns `0` on failure. On acceptance it emits feedback,
but performs the subtract/floor operation and `+0x1A0 = 15.0` write only when
effect flag `0x80`, fighter `+0x169 == 1`, and fighter `+0x62` bit `1` do not
block it. It calls `FUN_00305C30` with the requested authored-effect/event
arguments and returns `1` even when one of those later spend gates suppressed
the arithmetic. A zero requested amount goes directly to that effect/event
call and successful return.

`FUN_00225830(amount, fighter, feedback_mode)` is a second direct subtractor.
Modes `0` and `1` select different pre-debit feedback; modes `2..4` return
without spending. After its status gates it subtracts, floors at zero, and
sets `+0x1A0` to `15.0`, but it does not perform its own affordability check.
Representative callers `FUN_0025DCC0` (`0x0025DCC0`, ELF `0x0015DDC0`) and
`FUN_002B9400` (`0x002B9400`, ELF `0x001B9500`) first call
`FUN_00225940(1.5, fighter)` and only then use mode `0` to request raw `1.5`.

`FUN_00227850(other_delta, chakra_delta, fighter, cadence_mode, ..., ...)`
combines chakra mutation with separate action/effect work. In mode `0` it
requires affordability for `chakra_delta`, emits failure feedback otherwise,
then reaches a conditional subtract/floor branch. In mode `1` it rejects an
exactly empty chakra field but does not require the full requested amount. In
both modes, effect flag `0x80`, fighter `+0x169 == 1`, or fighter `+0x62` bit
`1` can suppress the debit and its `+0x1A0 = 15.0` history write without
rejecting the helper: its cadence feedback, separate `+0x6C` mutation, and
successful return can still proceed. The first float is the `+0x6C` delta and
must not be mistaken for the chakra argument. Several character-action
handlers call this helper with raw authored deltas; no substitution caller is
included here.

`FUN_0023A9A0(fighter, action_index, mode)` is the representative generic
action spend path. It resolves
`record = fighter[+0xA54] + action_index * 0x54`, reads raw chakra cost from
`record+0x20`, and, for the applicable record flag classes, emits the selected
feedback before reaching the debit branch. The debit, zero floor, and
`+0x1A0 = 15.0` write occur only when effect flag `0x80`, fighter
`+0x169 == 1`, and fighter `+0x62` bit `1` do not block them. Spend suppression
alone does not abort the subsequent action-dispatch machinery, which is owned
by [Combat action execution](combat_action_execution.md#action-entry-and-state-ownership).
No substitution-specific cost path is included here.

`FUN_00225F50(amount, fighter, reservation_class)` is a distinct
reserve path used when the selected action record has one of flags
`0x00100000..0x00800000`. It accepts class values `2..4` and refuses a new
reservation when existing `+0x7C >= 15.0`. When no active effect has behavior
flag `0x80`, fighter byte `+0x169` is not `1`, and fighter byte `+0x62` bit `1`
is clear, it also subtracts and floors the requested amount and writes
`+0x1A0 = 15.0`. Crucially, failure of those spend gates does **not** fail the
reservation operation: the helper still stores the amount at `+0x7C`, stores
`class - 1` at `+0x80`, initializes `+0x82` to raw `0x3C` when that counter was
zero, emits its feedback, and returns `1`. It performs no independent
affordability test.

The ordinary input update has a second, inline staging path. When logical
input bit `0x08000000` is present and `FUN_00225B60` accepts the fighter,
`FUN_00248EC0` proposes either `(fighter[+0x18C] + 1) * 5.0` or, under its
alternate fighter-flag branch, a flat `5.0`. The predicate blocks staging when
an active effect has flag `0x10`, and its affordability portion blocks on
effect flag `0x40`; it checks the required current amount but does not check
spend-block flag `0x80`. The inline body therefore mirrors
`FUN_00225F50`: it subtracts/floors only if effect flag `0x80` and the two
fighter spend gates permit it, but still writes the staged amount to `+0x7C`,
advances/stores the class in `+0x80`, initializes `+0x82` to raw `0x3C` if
needed, and emits feedback regardless of whether those spend gates suppress
the debit. These
are raw native units and a logical input flag; no physical binding or UI scale
is inferred.

`FUN_002260D0(fighter, mode)` releases that state. ELF bytes at file
`0x001261EC` decode as `lwc1 f12, 0x7C(a0)`; when nonzero, that amount is
passed to `FUN_002254A0` with zeroed flags. This is a **refund attempt**, not a
guaranteed add: the canonical adder can reject it on active effect flag `0x40`
or its fighter gates. The release helper then clears `+0x7C` regardless and
always clears `+0x80/+0x82`; it receives no success result from the void adder.
Consequently, the reservation is a refundable transaction claim rather than a
second chakra pool, and its recorded amount is not proof that an initial debit
occurred or a later refund succeeded.

Ordinary fighter maintenance makes this asymmetry explicit. While `+0x82` is
nonzero and the applicable active action record is not in a staged flag class,
`FUN_0024C440` decrements the counter only while effect flag `0x40` is absent.
It releases at zero; if flag `0x40` is present, it releases immediately. In
that immediate path the same flag blocks the refund adder, so the metadata is
cleared without restoration. A successful temporary-effect delta of exactly
`-15.0` instead clears `+0x7C` *before* calling `FUN_002260D0`,
discarding the pending refund while still resetting its metadata.

Two action-side consumers complete the staged-reservation lifecycle.
`FUN_00244F80` recognizes a matching active record in the staged flag classes,
calls `FUN_002260D0` to release the pending claim, and then conditionally
charges the selected `+0x18C` tier (`0/1/2 -> 5.0/10.0/15.0`) with the normal
zero floor and `+0x1A0 = 15.0` history write. The charge requires the two
fighter spend gates and either no active effect flag `0x80` or the special
membership-priority predicate `FUN_00307B20 == 1`; it is skipped when those
gates do not pass even though the action transition continues. The routine also
releases the linked fighter's reservation before that transition. Separately,
`FUN_00245340` handles an active class-`8` action phase: when its phase and
animation-marker gates pass, it releases the reservation, emits feedback, and
charges the active record's raw `+0x20` cost only when effect flag `0x80` and
the fighter spend gates permit it. These paths show that the selected action
can reach its commit transition even when a refund or committed debit was
suppressed; successful arithmetic remains owned by the ordinary chakra field.

The special predicate `FUN_00307B20` tests effect-list membership without a
countdown test: a present ID `0x0B` returns `0` even when `0x3B` or `0x41` is
also present; otherwise `0x3B` or `0x41` returns `1`. Its exact branches,
sole direct caller (commit call `0x00245230`, ELF `0x00145330`), and
pending-expiry semantics are owned by
[Presence policies used by native actions](../projectiles_and_items/battle_items_and_status_effects.md#presence-policies-used-by-native-actions).
In the commit, instructions `0x00245238..0x00245268` call the
active-flag-`0x80` scan `FUN_003074F0` at `0x0024525C` only when the result is
not `1`, and both routes keep the `+0x169` and `+0x62` bit-`1` gates before the
tier subtraction at `0x00245294`:

| ID `0x0B` present | ID `0x3B` or `0x41` present | Commit's effect gate |
| --- | --- | --- |
| Yes | Either | Consult active flag `0x80`. |
| No | Yes | Skip active flag `0x80`; fighter spend gates still apply. |
| No | No | Consult active flag `0x80`. |

A zero-countdown `0x0B` still vetoes the exception but does not itself block
the debit: the active-flag scanner ignores that zero node, so another active
`0x80` node is needed to reject the ordinary effect gate.

This bypass belongs to the tier commit only. Records `0x3B/0x41` (resident
`0x0059F9B4/0x0059FC0C`) author a per-update chakra delta of approximately
`-0.008333334` (bits `0xBC088889`) with boundary zero, and that delta still
goes through `FUN_00306220` and the ordinary subtractor with bypass argument
zero. Given a list containing one of those nodes plus another active `0x80`
node, the tier commit can skip that effect blocker while the signed-delta
route remains blocked. These are conditional consequences of the native
routines, not a claim that every such list combination is dynamically
reachable.

Representative direct consumers are kept in raw
per-invocation terms:

- `FUN_00249D70` classifies the current polygon contact word `+0xBB4` into
  classes `0..3` as described in
  [Stage surface attributes](../stages/stage_surface_attributes.md#query-eligibility-and-contact-classes).
  Only class 1 can reach either inline raw `0.008333334` debit. After the preceding
  state/action gates, active flag `0x40` or current chakra below that amount
  fails the local affordability check; a nonzero reservation `+0x7C` still
  admits the counter-update branch. Both that admitted branch and its
  no-reservation/unaffordable fallback independently apply the ordinary
  active-`0x80`, `+0x169`, and `+0x62` bit-`1` spend gates, subtract, floor
  at zero, and store `15.0` to `+0x1A0`. The fallback sets return value `1`
  even if those spend gates suppress arithmetic; the admitted branch instead
  increments the bounded `+0x540/+0x542` counters when `+0x62` bit `0` is
  clear. A blocked availability check therefore does not alone prevent this
  contact path from attempting its debit or advancing contact handling.
  Class 2 returns zero before this resource section; class 3/zero return
  before the special contact section. This is an invocation formula, not a
  rate conversion.
- `FUN_00237060` first releases any pending `+0x7C` reservation through the
  conditional refund path. It selects an integer in `3..5`, proposes
  `integer * 0.375`, reduces that amount to the
  available chakra when necessary, performs its associated event/effect call,
  then conditionally subtracts, floors at zero, and stores `15.0` to `+0x1A0`.
  Effect flag `0x80`, fighter `+0x169 == 1`, or fighter `+0x62` bit `1` can
  suppress the arithmetic after the event/effect has already occurred.
- Loaded overlay `FUN_00790830` (export bytes at `0x00790830`) requests
  positive raw amount stored in its controller object at `+0x5E8`, after its
  component/state gates pass. Loaded `FUN_007C47A0` unconditionally calls the
  subtractor with raw `7.5` when that wrapper is called, while loaded
  `FUN_007C6500` requests raw `5.0` only under its object-bit gate.
- Loaded `FUN_007F0C40` (export `FUN_007F0C00`) conditionally passes raw object
  `+0x10D8` to the subtractor for fighter pointer `+0x31C`; the direct call is
  at file/live `0x0013CE00/0x007F0D00`. Loaded `FUN_007FDE40` passes a computed
  aggregate to the same subtractor for fighter pointer `+0x4CC`, at
  `0x0014A370/0x007FE270`.
- Loaded block `0x00818380` (export `FUN_00818340`) starts with raw request
  `5.0`. When object `+0x9D8` is zero and the fighter reached through object
  `+0x9D4` has nonzero `+0x95A`, it multiplies that amount by `0.5`, yielding
  raw `2.5`; it then calls the subtractor at
  `0x00164544/0x00818444`. This is a proven guard-state/chakra interaction,
  but no player-facing action name is inferred.
- Loaded `FUN_00847070` (export `FUN_00847030`) requests raw `1.25` from fighter
  pointer `+0x31C` at file/live `0x001933CC/0x008472CC`.

All seven loaded direct debit sites pass subtractor bypass flag `0`, so active
effect flag `0x80` and the canonical fighter spend gates can suppress their
arithmetic. They use the standard zero floor. No player-facing action names or
rate conversions are inferred from these controller-local paths.

For the contact consumer, instructions `0x00249D70..0x0024A300` establish the
two debit branches. The amount is loaded from immediate bits `0x3C088889` at
`0x0024A0B8..0x0024A0C0` and again at `0x0024A24C..0x0024A254`. The admitted
branch writes current/history at `0x0024A184/0x0024A1A4`; the fallback writes
them at `0x0024A260/0x0024A280` (ELF `0x0014A360/0x0014A380`) and sets the
return value at `0x0024A284`. The producer of `+0xBB4` and the other contact
effects belong to
[Stage surface attributes](../stages/stage_surface_attributes.md#attribute-data-flow).

A direct-store census of resident code, restricted to pointers
proven to be fighter objects by their surrounding fighter fields, found current
chakra writes only in constructor `FUN_00214A40`, canonical routines
`FUN_002254A0/FUN_00225780/FUN_00225830`, reserve helper `FUN_00225F50`,
combined helpers `FUN_00227850/FUN_00227CE0`, discrete consumer
`FUN_00237060`, action-record spend `FUN_0023A9A0`, commit paths
`FUN_00244F80/FUN_00245340`, input staging `FUN_00248EC0`, and the small
direct consumer `FUN_00249D70`, plus the separately excluded owner below.
Recovery, configuration, effect, maintenance-refill, and loaded-controller
paths reach this same field through those canonical/inline writers rather than
introducing another max or shadow current field. Unrelated structures also use
offset `+0x70`; they were not counted merely from the numeric offset.

The excluded substitution-specific direct debit is not folded into these
generic paths; its separate owner is `FUN_002297D0`, documented in
[Substitution](../characters/substitution.md).

The repeated write of `15.0` to `+0x1A0` is not a resource refill: current
chakra remains at `+0x70`. It resets or biases the later threshold-crossing
history. `FUN_00225A40` supplies the strongest evidence for this limited label,
because on a crossing it compares `+0x1A0/+0x1A4` with the old/new samples and
then writes those samples back to the pair.

## Guard routine map

| Symbol | EE runtime | ELF file | Role |
| --- | ---: | ---: | --- |
| `FUN_00217BD0` | `0x00217BD0` | `0x00117CD0` | Action-exit dispatcher; routes guard stance `(0,5)` to `FUN_00228130`. |
| `FUN_002209A0` | `0x002209A0` | `0x00120AA0` | Hit router that selects guarded versus ordinary response from `+0x95A`. |
| `FUN_00228130` | `0x00228130` | `0x00128230` | Guard-stance exit cleanup. |
| `FUN_00228250` | `0x00228250` | `0x00128350` | Direct setter for guard state `+0x95A`. |
| `FUN_00228260` | `0x00228260` | `0x00128360` | Guard-entry eligibility predicate. |
| `FUN_00228320` | `0x00228320` | `0x00128420` | Per-update guard input and counter state machine. |
| `FUN_00228550` | `0x00228550` | `0x00128650` | Exit cleanup for guarded-response actions `(0,6)/(0,7)`. |
| `FUN_00228760` | `0x00228760` | `0x00128860` | Guarded-hit response; enters `(0,6)` or `(0,7)` and applies response side effects. |
| `FUN_00228B50` | `0x00228B50` | `0x00128C50` | Guarded-response follow-up; calls `FUN_00238950`, which changes the linked fighter's support gauge `+0x74`. |
| `FUN_00228E90` | `0x00228E90` | `0x00128F90` | Leaves guard stance or selects a response according to current hit state. |
| `FUN_00229130` | `0x00229130` | `0x00129230` | Adjacent action-eligibility helper that clears a positive `+0x95C` when another fighter-state mask is active; its broader mechanics are outside this document. |
| `FUN_00229B70` | `0x00229B70` | `0x00129C70` | Direct setter for timing state `+0x95C`. |
| `FUN_00229B80` | `0x00229B80` | `0x00129C80` | Multi-stage action update whose terminal cleanup clears `+0x95A` before `FUN_00228E90`. |
| `FUN_00232B80` | `0x00232B80` | `0x00132C80` | Ordinary, non-guarded hit response selected when `+0x95A < 1`. |
| `FUN_00238950` | `0x00238950` | `0x00138A50` | Mutates the linked fighter's support gauge at `+0x74`; not guard durability. |
| `FUN_00248580` | `0x00248580` | `0x00148680` | Action-state maintenance; leaves guard stance through `FUN_00228E90` after `+0x95A` clears. |
| `FUN_00248EC0` | `0x00248EC0` | `0x00148FC0` | Fighter input update; passes `fighter[+0x338]` to `FUN_00228320`. |
| `FUN_00249640` | `0x00249640` | `0x00149740` | Per-action update dispatcher; `(0,5)` performs the stance's interpolation/animation update. |
| `FUN_0024DA50` | `0x0024DA50` | `0x0014DB50` | Alternate maintenance path; duplicates only the `+0x95C` guard-input timing update while normal fighter processing is suppressed. |

The battle overlay also has a guard-sensitive attack dispatcher:

| Export bytes/function | Ghidra export | `BTL.BIN` file | Loaded EE | Role |
| --- | ---: | ---: | ---: | --- |
| `FUN_006FB800` | `0x006FB800` | `0x00047940` | `0x006FB840` | 43-entry switch dispatcher; cases `0x14/0x27` call the resident `+0x95C` setter with sentinel `-2`. |
| `FUN_0072E590` | `0x0072E590` | `0x0007A6D0` | `0x0072E5D0` | Tests attack-record `+0x14` flags `0x00400000`, `0x00800000`, and `0x01000000` against fighter `+0x95A`, then conditionally invokes local attack processing. |
| `FUN_0072E700` | `0x0072E700` | `0x0007A840` | `0x0072E740` | Actual start of the local processing callee selected by the dispatcher. It consumes the guard-present selector and tests fighter `+0x95A` again. |

The local call at export `0x0072E698` / file `0x0007A7D8` executes at live
`0x0072E6D8`. Its bytes `D0 B9 1C 0C` encode the already-live target
`0x0072E740`; the corresponding callee bytes begin at export `0x0072E700`.
Ghidra's extra `FUN_0072E740` label is therefore `0x40` into that exported
function, not a second live-address mapping. The two imported setter calls at
export `0x0072E5F8` / `0x0072E624` (files `0x0007A738` / `0x0007A764`, live
`0x0072E638` / `0x0072E664`) contain `94 A0 08 0C` and directly target the
resident `FUN_00228250` at `0x00228250`.

The generated switch function has two additional indirect guard-state writes.
At export/file/live `0x006FBE40/0x00047F80/0x006FBE80` and
`0x006FC27C/0x000483BC/0x006FC2BC`, bytes `DC A6 08 0C` encode
`jal 0x00229B70`. Both sites load a fighter pointer from the per-slot table at
`0x008D65AC + slot * 0x1E0`, place raw `-2` in `a1`, and call the resident
direct setter for fighter `+0x95C`.

The parent entry is export/file/live
`0x006FB800/0x00047940/0x006FB840`. It reads dispatcher value
`0x008D65C4 + slot * 0x1E0`, bounds it to `0x00..0x2A`, and indexes 43
absolute live targets at live `0x008C3810` (export `0x008C37D0`, file
`0x0020F910`). Entry `0x14` is live `0x006FBD7C`
(export `0x006FBD3C`) and reaches the first setter after its fighter/manager
gates; entry `0x27` is live `0x006FC2A8` (export `0x006FC268`) and directly
reaches the second setter. The corresponding table entries are export/live
`0x008C3820/0x008C3860` (file `0x0020F960`) and
`0x008C386C/0x008C38AC` (file `0x0020F9AC`). These are two explicit dispatcher-controlled
timing writes, not two unidentified character methods. They set a sentinel;
neither subtracts attack strength or demonstrates durability depletion.

### Guard input and action lifecycle

`FUN_00248EC0` reads the current input word from fighter `+0x338` and calls
`FUN_00228320(fighter, input)`. In that function, bit `0x10000000` is the
logical guard input:

- while held, `+0x95C` increments; on release it becomes zero; a negative
  value increments toward zero instead;
- accepted held guard increments `+0x95A` up to `0x7FFF`; its additional
  entry gates can call `FUN_00217E40(fighter, 0, 5, 0)`;
- in the guard-processing branch, releasing guard clears `+0x95A` and
  failed eligibility also clears it; and
- action-state maintainer `FUN_00248580` checks `(0,5)` and calls
  `FUN_00228E90` when `+0x95A` is zero, leaving the stance or selecting the
  appropriate response state. `FUN_00249640` separately performs the
  stance's interpolation/animation update.

The eligibility and preservation branches must be kept distinct. Complete
instructions `0x00228320..0x00228540` update `+0x95C` first, then skip all
`+0x95A` processing while state is `(0,6)` or `(0,7)`, or fighter word
`+0x254` is nonzero. Those branches preserve the previous `+0x95A` even
on released input; they do not execute an ineligibility clear. In the
remaining branch, major states `5/6/7/8` fail eligibility; major state `0`
requires minor state `0/3/4/5`; other major states retain the initial true
result. Nonzero `+0x9F0` or `(fighter[+0x9B8] & 3) > 1` also fails it.
The latter comparison is the complete `FUN_0022D5B0` predicate, not a
chakra test. The nine-entry table at resident `0x005C2380` corroborates
the switch despite indirect case dispatch. Separate `FUN_00228260`
implements the same eligibility subset without the outer preservation
branch. Actual stance entry additionally requires held input, `+0x63`
bit `7`, major state other than `2`, and minor state other than `6/7`;
accepted held-input age can still increment when those extra entry gates
skip the transition. These are exact native predicates, without inferred
player-facing state names.

Unlike `+0x95A`, the input-age field `+0x95C` has no saturation check.
Instructions `0x00228374/0x00228378` (ELF `0x00128474/0x00128478`) increment
the register and store its low halfword. Therefore a held-input update at
`0x7FFF` stores `0x8000`, which the next signed load treats as `-32768`.
The negative branch at `0x00228350..0x00228368` advances toward zero before
testing release, so `-2 -> -1 -> 0` takes two admitted input updates even if
guard is released during them. This is the compiled field operation; no
wall-clock duration or broader action consequence is inferred.

`FUN_0024DA50` has a secondary maintenance branch requiring base byte `+0x00`
bit `1`, fighter `+0x20C >= 1`, and `(uint16(fighter[+0x60]) & 0x01E0) == 0`.
It repeats the same
negative-toward-zero, release-to-zero, held-increment update for `+0x95C`, but
does not increment `+0x95A` or enter stance `(0,5)`. This independently
separates the input-age counter from the accepted guard-state counter.

There is also a resident effect-driven timing write. In `FUN_003059B0`,
the exact-ID membership helper `FUN_00307610` is called at `0x00305AAC`
and a match calls `FUN_00229B70(fighter,-2)` at `0x00305AC4` (ELF
`0x00205BC4`; bytes `DC A6 08 0C`, preceded by `li a1,-2`). Complete
`FUN_00307610` searches for ID `0x09` without loading countdown `+0x6C`.
The write follows aggregation but precedes the separately gated countdown
pass, so it can recur while countdown is zero pending removal or while that
pass is disabled. It changes `+0x95C`, not `+0x95A`, and is an additional
source of the negative-to-zero timing state; no broader action meaning is
assigned here. The effect owner documents its
[pending-expiry behavior](../projectiles_and_items/battle_items_and_status_effects.md#countdown-pass).

The action-exit dispatcher `FUN_00217BD0` independently routes `(0,5)` to
`FUN_00228130`. That cleanup restores orientation/interpolation state when the
fighter is no longer in the guarded action. Response actions `(0,6)` and
`(0,7)` route to `FUN_00228550`.

These relationships prove that `(0,5)` is the active guard stance and that
`+0x95A/+0x95C` are temporal guard/input state. Neither field behaves like a
finite durability pool: both rise with held time rather than fall under
guarded hits.

### Guarded-hit selection and break-like flags

The resident hit router `FUN_002209A0` sends an accepted hit to ordinary
response `FUN_00232B80` when fighter `+0x95A < 1` and to guarded response
`FUN_00228760` when `+0x95A >= 1`; the guarded response enters `(0,6)` or
`(0,7)` and calls `FUN_00228B50`. Router modes, admission gates, and the
reaction outcomes are owned by
[Accepted-hit routing](hit_response.md#accepted-hit-routing) and
[Guarded-hit transitions](hit_response.md#guarded-hits).

Before that branch, two attack-record `+0x14` flags write the guard field:

- `0x00800000`, under the router's facing/state condition, changes a nonzero
  `+0x95A` to sentinel `-1`; and
- `0x00400000` clears `+0x95A` to zero.

Either result is `<1`, so that hit takes the ordinary branch even if guard
input had been active. `FUN_00232B80` consumes exactly `-1` at resident
`0x00232CCC..0x00232CE0`: it clears `+0x95A` and forces reaction `(5,0x4F)`,
which clearing to zero does not request. Thus `-1` is a one-use reaction
selector as well as a non-guarded routing value; it is not a negative
quantity of durability. No player-facing name for either attack flag is
established here.

Loaded overlay `FUN_0072E590` independently confirms both writes and exposes
a third guard-sensitive flag. Its decision order is:

- `0x00400000`: call `FUN_00228250(fighter, 0)`, then process the record;
- otherwise `0x00800000`: call `FUN_00228250(fighter, -1)`, then process it;
- otherwise `0x01000000`: process it regardless of `+0x95A`; pass selector
  `1` when `+0x95A` is nonzero and `0` when it is zero; and
- with none of those flags: process it only when `+0x95A` is zero.

The third flag does not clear, decrement, or refill `+0x95A`; it preserves the
field and tells the downstream overlay routine whether guard was present. The
dispatcher finishes by setting its owning object's `+0x20C` word to `1`.
Those are proven code effects, but they do not establish player-facing names
for any of the three flags.

The overlay has no direct `+0x95C` field access, but sets it through the
resident setter. A raw-JAL census of `BTL.BIN` found exactly two calls to the
`+0x95A` setter, at files `0x0007A738/0x0007A764`, and exactly two calls to the
`+0x95C` setter, at files `0x00047F80/0x000483BC`.

### Overlay guard-state read coverage

A whole-program byte search for `5A 09 ?? ??` found 47 aligned overlay
words; every word decodes as `lh register,0x95A(base)`. Each load's immediate
consuming branch was decoded. Their comparison classes are listed below by
Ghidra byte address (see
[Address conventions](../../game/files/file_identities.md#address-conventions)).

| Comparison class | Count | Ghidra byte addresses |
| --- | ---: | --- |
| Zero versus nonzero in shared AI and hit/result paths | 4 | `0x00703A7C`, `0x0072E648`, `0x0072E670`, `0x0072E7B8` |
| Zero versus nonzero in controller paths | 38 | `0x0077FE50`, `0x00780994`, `0x00780B34`, `0x00787A5C`, `0x00789260`, `0x007894A4`, `0x007A2EFC`, `0x007A8CC0`, `0x007AD2C4`, `0x007AD404`, `0x007AFD68`, `0x007B0958`, `0x007B7ADC`, `0x007B8F1C`, `0x007BD5CC`, `0x007F7720`, `0x007FD1BC`, `0x007FE488`, `0x00805548`, `0x0081410C`, `0x008183CC`, `0x00831F04`, `0x008360C0`, `0x0083B85C`, `0x0083B9C8`, `0x0083E8C0`, `0x0083F4A4`, `0x0083F5AC`, `0x008403D4`, `0x008444D0`, `0x008564D8`, `0x00856FE4`, `0x00857AC4`, `0x00858B20`, `0x0085DCC4`, `0x0085E448`, `0x0085E9FC`, `0x00865358` |
| Positive versus zero/negative in controller paths | 5 | `0x00780E54`, `0x007896FC`, `0x007FAB64`, `0x0080174C`, `0x00808278` |

Many controller paths first choose either the fighter `+0x95A` value or zero
according to the controller's separate fighter/component gate. The immediate
consumers select flags, record parameters, counters, feedback, candidate
branches, or the chakra amount already documented at live `0x00818444`.
They do not treat the numeric magnitude as remaining durability. In particular,
`0x00780994/0x00789260` select a record parameter on nonzero state, while
`0x00780B34/0x007894A4` increment a controller-local counter on nonzero
state; neither writes the fighter's guard field.

This also limits the descriptive label “guard active”: the 42 zero/nonzero
consumers admit a negative sentinel into their nonzero branch, whereas the
five signed consumers and resident hit router require a positive value.
For example, byte addresses `0x00780E54` and `0x007896FC` reach their
record-parameter adjustment only through `>0`, while the chakra request at
`0x008183CC` uses `!=0`. These are different native tests; replacing all of
them with one Boolean interpretation would lose proven behavior.

Two related controller variants have these bounded record adjustments,
listed by Ghidra byte window; the branches and writes were decoded from those
instruction bytes.

| Byte window | Guard test | Proven selected operation |
| --- | --- | --- |
| `0x00780974..0x007809F8` | `+0x95A != 0` | Selects record byte `+0x2C` from that record's signed halfword `+0x54`. The zero branch instead uses a controller-authored value, sets record `+0x2E = 1`, and sets `+0x30/+0x32 = 0x7FFF`. |
| `0x00789240..0x007892C8` | `+0x95A != 0` | Same record-byte and sentinel selection in the second variant, after its distinct component predicate. |
| `0x00780E30..0x00780E84` | `+0x95A > 0`, under accumulated record `+0x14 & 0x00800000` | Multiplies record raw float `+0x24` by `0.5`, retaining the guard field. |
| `0x007896BC..0x00789724` | `+0x95A > 0`, under record `+0x14 & 0x00800000` and controller byte `+0x539 != 0` | Performs the same `+0x24 *= 0.5` write in the second variant. |

Both halve operations load immediate float bits `0x3F000000`, execute
`mul.s`, and store back to record `+0x24`; neither decrements a fighter
guard field. For the positive-only half, the first variant chooses the fighter
through controller `+0x9D4` when `+0x9D8 == 0`; the second uses its separate
native component predicate and pointer `+0x4CC`. The second variant's
record-byte selection instead reads its fighter through `+0x11C`.
Negative `+0x95A` therefore qualifies for the record-byte selection but
skips either positive-only halve operation. The chakra request at bytes
`0x008183B4..0x00818408` instead changes `5.0` to `2.5` on nonzero guard
state, so a negative sentinel qualifies there too. These results establish
distinct native record/cost choices; they do not establish the record
parameter's displayed meaning or identify a character/action by name.

The census covers every occurrence of this immediate field encoding in the
mapped overlay. It does not cover pointer arithmetic that accesses the field
with another displacement or a wider access beginning at a neighboring field,
and it does not reconstruct each controller's complete action script.

### Guard-state writer coverage

A complete direct-writer census of resident code found only nine
routines touching either guard counter: constructor `FUN_00214A40`, hit router
`FUN_002209A0`, setters `FUN_00228250`/`FUN_00229B70`, input updater
`FUN_00228320`, adjacent eligibility helper `FUN_00229130`, terminal action
cleanup `FUN_00229B80`, ordinary response `FUN_00232B80`, and alternate input
updater `FUN_0024DA50`. The battle overlay has no direct assignment to either
field; it invokes the resident `+0x95A` setter with `0/-1` and the resident
`+0x95C` setter with `-2`. Apart from the arbitrary-value
setters, the resident writes are initialization/clear, `-1` sentinel, or
one-step increment (including a negative `+0x95C` moving toward zero). No
writer performs attack-strength subtraction or any other decrement toward a
break threshold. This census includes direct field syntax and the byte-pair
zero used by `FUN_0024DA50` for `+0x95C`.

An instruction-level byte search bounds `+0x95C` access. In the resident
image, `5C 09 ?? ??` occurs 29 times. Within resident
`0x00100000..0x0060737F`, 19 of these are word-aligned. Six are
three unrelated absolute-data loads, one floating instruction, and two words
whose opcode is not a memory access;
the remaining 13 encode fighter-field `lh/sh` in constructor
`FUN_00214A40` (one), input updater `FUN_00228320` (four), adjacent
eligibility helper `FUN_00229130` (three), setter `FUN_00229B70` (one),
and alternate updater `FUN_0024DA50` (four). The same search across
`BTL.BIN` found one aligned floating instruction at byte address `0x006F1218`,
with no direct `+0x95C` field access. Together with the setter imports and
the resident effect-`0x09` caller, this closes direct immediate access
coverage for both images. The adjacent eligibility owner
[Substitution](../characters/substitution.md) owns that system's action semantics;
computed-address and neighboring wider-access exceptions remain outside this
bound.

### No proven guard-durability resource

No persistent guard-durability accumulator or maximum was established in the
traced native guard paths. In particular:

- no guarded-hit path decrements `+0x95A` or `+0x95C` by attack strength;
- no clamp-to-zero or cumulative break threshold exists on those fields;
- the branch to an ordinary hit after the state-invalidating attack flags is per-hit state
  invalidation, not depletion of a meter; and
- action `(0,5)` performs stance/animation work but no resource decrement;
  overlay flag `0x01000000` likewise selects a branch without changing either
  guard counter.

This is a strong negative result for the traced guard entry, exit, and
representative hit paths, not a mathematical proof that no character-specific
or scripted exception exists anywhere in the program.

## Rejected candidates and remaining hypotheses

### `ccEffCond_AbsGuard` is an effect class, not a durability pool

The resident image contains the exact internal class string
`ccEffCond_AbsGuard` at runtime `0x005A5C20` / ELF file `0x004A5D20`, and its
vtable begins at runtime `0x005DB240` / file `0x004DB340`; raw bytes confirm
both. The class
constructor is `FUN_00345FF0` (runtime `0x00345FF0`, file `0x002460F0`), with
destructor `FUN_00346100` and virtual updates `FUN_00346210` and
`FUN_003462A0`.

This named class owns a visual/effect object at class `+0xA0` and an owner
pointer at class `+0xA8`. Its update optionally copies owner `+0x310` into the
effect object when owner byte-zero bit `2` is set, then updates effect position
and transform data. The class does not read or write fighter `+0x95A`,
`+0x95C`, or chakra; it has no decreasing counter, maximum, or break
transition. The name is useful corroboration that the game has an authored
“AbsGuard” effect concept, but it is not evidence for a persistent native
guard-durability resource.

### Fighter `+0x74` is support, not guard

Fighter `+0x74` and its recharge multiplier `+0x78` are the support gauge
described in
[Gauge state and availability](../characters/support_mechanics.md#gauge-state-and-availability);
guarded-response follow-up `FUN_00228B50` reaches `+0x74` only through
`FUN_00238950`, which adds to the linked fighter's gauge, so neither field is
a guard-durability value or maximum.

### Hypotheses requiring new evidence

- **Hypothesis:** attack-record `+0x14` flags `0x00800000` and `0x00400000`
  are two authored guard-bypass or guard-invalidation categories. Established
  here are only their writes to `+0x95A` and the overlay branch that
  `0x01000000` selects; their authored or player-facing names are not.
- **Hypothesis:** the `-2` writes to `+0x95C` (overlay dispatcher cases
  `0x14/0x27` and effect `0x09`) serve the adjacent eligibility system owned
  by [Substitution](../characters/substitution.md). The writes and the negative-to-zero
  input update are established here; their purpose is not.
- **Hypothesis:** a character-specific or scripted guard exception exists
  outside the traced native routes. A durability meter would need a
  per-fighter field that is initialized, decremented by guarded hits, clamped,
  and consumed by a break transition; none of those four links was found
  together here.
