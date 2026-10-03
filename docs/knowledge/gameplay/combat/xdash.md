# X-dash

Native X-dash action states, cancellation boundary, movement transition, and
chakra behavior in retail NA2 (`SLPS-25837`).

## Evidence basis and address conventions

Binary identities and address conversions follow
[Retail game file identities](../../game/files/file_identities.md#address-conventions).
Resident addresses below are EE addresses; encoded BTL calls retain live
addresses.

## Research coverage

- **Assigned scope:** establish the native X-dash action record, character
  variants, authored thresholds, entry/exit gates, cancellation boundary, and
  chakra-cost behavior.
- **Exploration depth:** traced the action selector, cost path, centralized
  phase writers, category-2 entry, transition, motion, contact-latch and
  old-action cleanup consumers, and three completed or cancelled attempts.
  Read slot `0x13` in all 74 distinct definitions containing it, their
  authored startup/duration fields, and definition 14's relevant phase rows.
- **Confirmed coverage:** action index `0x13`, its native zero cost,
  cancellable preparation, committed movement, hit transition, shared
  category-2 dispatch, authored threshold producers, definition 14's distinct
  contact-limit record, delayed contact, and old-action cleanup are
  established. The first persistent post-cancellation state is established
  for the one traced sequence.
- **Unresolved or untested:** whether an unrestricted character callback or
  indirect route bypasses the shared state machine; simultaneous cancellation
  reachability, post-setup overrides, unsampled callback descendants, exact
  reason-3/4 phase arguments, cooldown lifetime, and visible timing remain
  open.
- **Deliberate exclusions and overlap:** [Movement and physics](../stages/movement_and_physics.md)
  owns ordinary movement and the shared physics pass; [Combat action execution](combat_action_execution.md)
  owns general action/phase dispatch; [Character action callbacks](../characters/character_action_callbacks.md)
  owns its wider callback census.
- **Evidence limitations:** runtime observations covered one
  Kakashi-versus-Sai Practice sequence and bounded instrumentation of known
  phase writers. The remaining findings are static retail evidence; they do
  not extend those observations to every character or establish visible
  timing.

## Native action and cost

X-dash uses major action state `8`, action index `0x13`, and phases `0`, `1`,
and `2`. Its action record is `fighter[+0xA54] + 0x13 * 0x54`; field `+0x10` is
type `2`, field `+0x1C` is `0x02000011`, and native float cost `+0x20` is
`0.0`. The unmodified action therefore consumes no chakra.

`FUN_00239530` selects action index `0x13`. After acceptance,
`FUN_0023A9A0` loads the record cost at `0x0023AAF0`, subtracts and clamps it at
`0x0023AC00..0x0023AC20`, and calls `FUN_00217E40` to enter the action.
Because record type `2` returns before the ordinary affordability check, the
native action has no minimum-chakra requirement.

## State transitions

Phase `0` is cancellable preparation. Phase `1` represents dash movement, and
phase `2` is the hit transition. A phase write alone is not a safe commitment
boundary: phases `1` and `2` can both be written transiently during an update
that ultimately cancels the action.

The internal state at fighter `+0x9BA` distinguishes the transition.
`FUN_0023C230` sees state `1` during preparation. When the primary action cursor
reaches the authored start threshold, `FUN_0023C0F0` changes that field to `2`
and writes phase `1`, selecting the committed movement branch. The state-2
branch later handles contact through `FUN_0023D980`; its ordinary reason-2
continuation changes the internal state to `3` and phase to `2`.
`FUN_0023D980` handles contact, movement completion, and interruption recovery,
rather than dash-start processing. Its delayed-contact branch can retain
substate `2`, as detailed below.

Bounded tracing of the direct setter, generic increment, and seven centralized
event stores produced these ordered paths:

- completed dash: phase `0`/substate `1`, then persistent phase `1`/substate
  `2`, then phase `2`/substate `3`;
- early cancellation: phase `0`/substate `1` directly to another major action;
- final-frame cancellation: a transient phase-1 write followed by direct exit
  from preparation to another major action.

The first fighter-update boundary entered with phase `1` and substate `2` is
therefore the first persistent state after the final cancellation opportunity
in that traced sequence. Static evidence does not establish the same
cancellation reachability for every character callback or variant.

## Character-authored records and threshold producers

**Confirmed observation:** The slot is reached through the character table
at `0x005A2900`, definition pointer at table `+4`, default action array at
definition `+0x2C`, and action `0x13` at array `+0x63C`. Every one of the
74 distinct definitions whose count includes that slot stores category
`+0x10 = 2`, behavior word `+0x14 = 0`, request signature
`+0x1C = 0x02000011`, and float cost `+0x20 = 0.0`. Four auxiliary
four-record definitions do not contain the slot; repeated filler references
do not add distinct definitions. The wider definition/table census belongs
to [Character identity](../characters/character_ids.md#character-definition-table) and
[Action commands](action_commands.md#static-action-data).

All those slot records have empty strings at pointers `+0/+4/+8`, which
point to resident `0x006031F0`, whose bytes begin with zero. Consequently
this table does not provide a named character-specific X-dash move. No move
name is inferred from an animation slot, character ID, or code address.

`FUN_002151E0` copies definition word `+0x8C` to fighter `+0x118` and
word `+0x90` to fighter `+0x11C`. These are the signed startup and movement
duration thresholds consumed by `FUN_0023C230`. Across the 74 definitions,
authored startup is `6..12` and duration `8..18`. Those values are action
cursor thresholds, not established visible frames or elapsed seconds.
The loader also copies definition float `+0x98` to fighter `+0x124`;
`FUN_00218D30` resolves the X-dash records' sentinel `+0x34/+0x38` to that
field. Motion target construction uses it independently of the timing sum.

| Definition ID | Definition address | Slot `0x13` address | Startup / duration | Contact limit `+0x2E` | Authored maximum distance `definition +0x98` |
| ---: | --- | --- | --- | ---: | ---: |
| 14 | `0x004474A0` | `0x00446D3C` | `12 / 18` | 4 | 700 |
| 39 | `0x004877D0` | `0x00486D7C` | `9 / 15` | 1 | 850 |
| 51 | `0x004BC530` | `0x004BBC7C` | `9 / 18` | 1 | 900 |
| 70 | `0x00525BC0` | `0x0052522C` | `8 / 12` | 1 | 700 |
| 76 | `0x005403A0` | `0x0053FCAC` | `8 / 8` | 1 | 400 |
| 92 | `0x00595B60` | `0x0059531C` | `8 / 12` | 1 | 700 |

Definition 14 is the only inspected static slot with contact limit `4`;
the other 73 store `1`. Its row index is `0x55`, selecting source rows at
`0x00444D2C` from definition row-array pointer `0x004433F0`. The six headers
are `(animation, condition, start, rate)`:

```text
phase 0: (0x00, 0, 0, 0x0C0)
phase 1: (0x66, 0, 0, 0x200)
phase 2: (0x39, 0, 0, 0x100)
phase 3: (0x45, 0, 0, 0x100)
phase 4: (0x44, 0, 0, 0x100)
phase 5: (-1,   0, 0, 0)
```

The condition-zero rows alone do not progress on an authored positive
count. Explicit phase selection and the shared X-dash state machine remain
relevant; the common row/header contract belongs to
[Combat action execution](combat_action_execution.md#shared-phase-progression).
This data difference selects the delayed-contact branch described below,
without changing category-2 dispatch.

**Limits:** `FUN_002151E0` can select a constructor-installed writable array
through definition `+0x30`; `FUN_00219620` copies default slots 4 through
the action count into it, and `FUN_00218FE0` replaces slot `+0x50` with a
pointer into the fighter's copied phase rows. Their complete setup is owned
by [Action commands](action_commands.md#working-action-arrays).
It is not established that every constructor, later callback, or indirect
writer preserves slot `0x13` and copied thresholds for their full lifetime.
Definition 14's factory `FUN_0025EF70` calls constructor `FUN_0025EFC0`;
its callback vector at `0x00442800` names `0x0025F170`, `0x0025F410`,
`0x0025FDA0`, and `0x00260260`, whose descendants were not followed.

## Static entry and dispatch gates

**Confirmed observation:** The logical request bit `0x02000000` branch of
resident `FUN_00239530` considers only index `0x13`, requires action category
`+0x10 & 2`, and calls `FUN_0023BEE0`. That predicate requires zero signed
cooldown `+0x9C0`, zero exchange word `+0xB00`, and either cleared
`byte +0x63 & 0x0C` or unequal tier halfwords `+0x9F6/+0x324`. If already in
major `8`, its current payload `+0xA50` must exist and its first word must be
exactly `0x20`. This is the native selector gate; input recognition is
owned by [Action commands](action_commands.md), and the exchange word by
[Extra Hit](extra_hit.md#exchange-state-at-fighter-0xb00).

Accepted entry through `FUN_0023A9A0` and `FUN_00217E40` reaches
`FUN_00238A70`, which selects `+0xA54 + index*0x54` into `+0xA4C`.
Category bit `2` calls `FUN_0023C000`: it writes `+0x9BA = 1`, clears
`+0x9C2`, saves direction into `+0x9BE`, and saves the starting position at
`+0x9D0`. The common phase/timeline reset remains owned by
[Combat action execution](combat_action_execution.md#action-entry-and-state-ownership).

Category bit `2` routes the common major-8 transition dispatcher
`FUN_0023B280` to `FUN_0023C230`, and the motion dispatcher `FUN_0023BAC0`
to `FUN_0023CD80`, after their exchange and paired-state branches
([Combat action execution](combat_action_execution.md#continuation-and-common-exit-decisions));
different character-authored records alone do not prove a bypass of this
shared path.

For current slot `0x13`, callback dispatcher `FUN_00217670` does not take
the configured-provider remapping reserved for indices below 4 and uses
fighter callback table `+0xA8`
([dispatcher contract](../../game/character_assets.md#per-character-code)).
Channels 2 and 3 run before the later motion dispatcher in `FUN_00249640`.
The broader callback routes belong to
[Character action callbacks](../characters/character_action_callbacks.md#evidence-convention-and-ownership).
This establishes where a selected character callback can run; it does not
prove that all such bodies leave X-dash unchanged.

## Committed motion and counter lifetime

**Confirmed observation:** `FUN_0023C0F0` stores substate `2`, clears
signed counter `+0x9C2` and float movement accumulator `+0x9C8`, writes
cooldown `+0x9C0 = 0x14`, then selects phase `1`. In the later
`FUN_0023CD80` motion consumer, substate `1` zeros directional and vertical
speed; substate `2` constructs movement from the saved start `+0x9D0` and
target `+0x9E0`. It advances `+0x9C8` by
`(pi/2 / duration[+0x11C]) * fighter_delta[+0x1AC]`, then scales the
start-to-target vector by
`FUN_0016EFB8(accumulator - pi/10) * 0.11`. The helper's mathematical
implementation was not separately inspected. The consumer
writes resulting directional/vertical speed at `+0x994/+0x998`; integration
belongs to [Movement and physics](../stages/movement_and_physics.md).

The target is not universally fixed at entry. In the ordinary matching-tier
route, absent the opponent `(6,0x61/0x62)` exclusion, `FUN_0023CD80` calls
`FUN_0023C6D0` to recompute it; other inspected branches call
`FUN_0023C840` only while `+0x9C2 == 0`. `FUN_0023C6D0` clamps the
opponent distance between fighter bounds `+0x120/+0x124`, both multiplied
by `FUN_00306E80`'s result, and uses it to construct `+0x9E0`.
`FUN_0023C840` instead constructs a directional target and adjusts it through
the stage-query service. The multiplier's producer and every target-adjustment
variant were not followed here; collision services remain owned by
[Collision](collision.md).

The same motion consumer increments `+0x9C2` once at its common tail,
including its preparation and recovery branches. Entry, commitment and
ordinary recovery initialization reset it, so this counter is distinct from
the primary action cursor used for startup/duration. Its increment counts
consumer calls, while the motion accumulator uses fighter delta. Neither
quantity alone establishes player-visible elapsed timing. The complete
cooldown decrement/writer lifetime remains an unresolved lead.

## Contact latch and recovery continuations

**Confirmed observation:** In `FUN_0023C230`, preparation waits for signed
primary cursor `+0x1C4 >= +0x118`. Committed movement compares that cursor
against `+0x118 + +0x11C`. If action halfword `+0x2E != 1` and byte
`+0xA41 == 1`, it waits until that sum, then calls `FUN_0023D980(fighter,2,0)`
and returns. Otherwise the timeout calls reason `0`, fighter byte
`+0x64 & 1` also calls reason `0`, and byte `+0x63 & 0x40` calls reason `4`.
These latter checks are sequential, so more than one call is structurally
possible in one update; simultaneous reachable conditions are not established.

`FUN_0023D980` has an early reason-2 branch when record `+0x2E != 1` and
the cursor is below the same sum. It sets `+0xA41 = 1`, adds `5.0` to the
fighter's vertical position, prepares the opponent through `FUN_0021A8D0`,
and conditionally calls `FUN_00224510`. It does not write phase `2` or
substate `3` on this branch. Thus a contact invocation does not always end
committed movement. General hit effects belong to [Hit response](hit_response.md).

The other reason-2 branch sets phase `2`, substate `3`, and recovery limit
`+0x9C4 = 0x14`. Reason `0` also enters phase `2` and substate `3`, with
limit `0x10`; reason `1` uses limit `0x24`; reasons `3/4` enter substate `3`
with limit `0x0C` through a separate phase-selection branch whose exact
argument needs instruction corroboration. Reasons `5/6` clear `+0x9BA` to
zero. These are reason codes established by their callers and stores, not a
complete naming of every contact outcome.

In substate `3`, `FUN_0023C230` combines recovery count
`+0x9C2 >= +0x9C4`, tier/opponent-state gates, groundedness, and reason
`+0x9BC`. Instructions `0x0023C4B4..0x0023C5BC` establish that
groundedness can admit exit independently of the recovery count. With
matching tiers and an opponent outside `(6,0x61/0x62)`, the count-based
airborne exit is suppressed; otherwise it is admitted except for reason 1
while airborne. No caller-supplied terminal argument gates this exit: the
branch assigns register `a3` itself before an admitted exit. It clears
`+0x9BA` and enters landing `(4,0x26)` when grounded; airborne reasons
`1/3/4` enter `(3,0x25)` and reasons `0/2` enter `(3,0x23)`. Substate zero
instead exits to neutral `(0,0)` or ordinary fall `(3,0x1E)` after
`FUN_0023EF30`. [Movement and physics](../stages/movement_and_physics.md#ordinary-state-dispatch)
describes those destination states.

Old major-8 cleanup `FUN_00238D00`, reached from `FUN_00217BD0` before a
new state is installed, calls `FUN_0023D980(fighter,6,0)` whenever
`+0x9BA != 0`. This clears the native X-dash substate during an external
action change. It does not imply that every external action request is allowed
at every X-dash point; those requests have independent eligibility gates.
