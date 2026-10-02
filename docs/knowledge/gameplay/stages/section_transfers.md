# Section transfers

This document records fighter stage-section transfers in unmodified retail
NA2 (`SLPS-25837`).

## Research coverage

- **Assigned scope:** Section-transfer requests, destination selection, facing,
  input and presentation choreography, interruption, cleanup and return paths.
- **Exploration depth:**
  - Complete bodies of request helper `FUN_0022E760`, motion handler
    `FUN_0022E950`, interruption `FUN_0022F0B0`, cleanup `FUN_0022F110`,
    their state dispatchers, both transfer descriptor arrays and the shared
    phase-condition consumer.
  - Direct-call scans of the resident and BTL images for request, motion,
    interruption and cleanup, with every resulting caller family read.
  - Presentation setup/update/model paths, paired-relative placement, four
    representative character dimension records, selected animation/effect
    bindings, effect playback/retirement and Chiyo's additional-scene callback.
  - Bounded reads of four retail CCS containers for the selected animation
    records and authored frame counts.
- **Confirmed coverage:** Request admission and its three return classes,
  section-delta/destination storage, origin snapshot, request ordering, all
  three motion stages, partner/input-dependent branch, descriptor completion,
  conditional restoration, cleanup stores, visual/physical position
  separation, presentation-countdown ownership, interaction-registration
  disable/enable interval, representative paired-character variation,
  alternative contact handoff and endpoint correction, the alternative's
  outcome-byte write, selected resource names/frame counts, and distinct
  primary/additional-scene placement sources.
- **Unresolved or untested:** Observed animation/effect/sound presentation,
  audible sample identity, behavior over every stage's geometry, every derived
  character model callback, and indirect/tail-call entry paths. Exact visual
  durations are not established.
- **Deliberate exclusions and overlap:** Geometry queries belong to
  [Collision](../combat/collision.md) and stage data to [Stages](stages.md). Ordinary
  movement algorithms belong to [Movement and physics](movement_and_physics.md),
  input infrastructure to [Action commands](../combat/action_commands.md), the main
  camera's transfer branch and smoothing to
  [Battle camera](../session/battle_camera.md#tracking-target), and the general lifetime
  of outcome byte `+0xA41` to
  [Combat action execution](../combat/combat_action_execution.md#prior-outcome-byte-lifetime).
  This document owns their section-transfer consumers.
- **Evidence limitations:** Static branches and data establish dispatch and
  field operations, not observed presentation, wall-clock timing or the absence
  of indirect callers. Numeric states are not assigned player-facing names
  without independent evidence.

## Evidence and address conventions

Resident addresses are EE addresses. BTL addresses are labeled **live**;
preserved import addresses and complete-file offsets follow
[Retail game file identities](../../game/files/file_identities.md#address-conventions).

## Request admission and retained destination

**Observed:** `FUN_0022E760(fighter, signed_delta)` rejects with `0` unless
fighter byte `+0x63` has grounded bit `0x80`, transfer delta `+0x9F0` is zero,
word `+0xB00` is zero and `byte +0x9B8 & 3 <= 1`. Allowed action states are
neutral `(0,0)`, running `(1,0x0E..0x11)`, jump preparation `(2,0x17)` and
major `4`; this helper does not constrain major `4`'s substate.

After those gates, a missing field/controller pointer `+0x28` or nonzero
field predicate live `0x00708BC0(field,2)` produces `-1`. Otherwise it stores
the supplied signed halfword at `+0x9F0` and calls field service live
`0x007090D0(field,current_section,current_section+delta,&position,&destination)`.
Current section is signed `+0x9F6`; output destination is vec4 `+0xA20`.
Success snapshots current position `+0x30` into `+0xA10` and returns `1`;
instructions `0x0022E8C8..0x0022E910` establish these stores and arguments.
Resolution failure clears the delta and returns `-1`. Thus `0` and `-1`
are distinct rejection classes; the helper itself does not enter a new action.

**Observed service boundary:** field service live `0x007090D0` rejects only
a negative target or a target `>= field[+0x7C]` in its complete wrapper.
For an admitted target it copies the input vector, optionally passes that
copy to background line service live `0x006C1E90` when field `+0x70` exists,
copies it to the output and returns `1`. The wrapper does not propagate a
separate geometry-failure return. The restriction predicate at live
`0x00708BC0` returns whether a shared GP-relative mask intersects its argument
when field `+0x70` exists, or zero otherwise. These are established from the
instruction bytes at import `0x00708B80..0x00708BAB` and
`0x00709090..0x0070910B`. Background line algorithms and their authored data remain with
[Collision](../combat/collision.md) and [Stages](stages.md).

### Input order and selected action

**Observed:** `FUN_00248EC0` processes ordinary jump logical bit `0x10000`
through `FUN_0022F200` before trying a section transfer. Bit `0x80000` takes
priority and requests delta `+1`. Only when it is absent does bit `0x100000`
try fast descent through `FUN_002302C0`; if descent is unavailable it requests
delta `-1`. The input translator's binding/sector contract is owned by
[Action commands](../combat/action_commands.md#logical-mask-translation): these are
the Up/Down modifiers of a press on binding 2, default Cross.

Return `1` enters major `1`, substate `0x15` for `+1` or `0x16` for `-1`
through `FUN_00217E40`. Return `-1` calls `FUN_0022F3D0(fighter,0)`, whose
ordinary path enters jump preparation `(2,0x17)`; return `0` leaves the
transfer request without that action change. The request dispatcher first
requires byte `+0x63 & 1 == 0` and `FUN_00226FA0` to return zero. These outer
gates are distinct from the transfer helper's grounded/action gates.

## Motion stages and relocation

Halfwords `+0x9F2/+0x9F4` are a transfer-local stage and update counter,
separate from action-descriptor phase `+0x192`. `FUN_00249640` dispatches
both transfer substates to `FUN_0022E950`. The latter tests primary-timeline
event `0` to reset both transfer-local halfwords. Its constants below count
handler calls; no wall-clock duration is established.

| Local stage | Observed work in `FUN_0022E950` |
| --- | --- |
| `0` | Copies origin `+0xA10` to auxiliary vec4 `+0x2C0`. On old counter zero, copies origin to `+0xA00`, saves section to `+0x9F8`, and calls `FUN_00226B00(fighter,0,0x100,8,4)`. Increments the counter; new value `>=4` installs float `80` at `+0x9FC`, stage `1`, counter `0`. Directional speed `+0x994` is snapped to zero. |
| `1` | Keeps auxiliary vec4 at origin. Subtracts `18` from `+0x9FC`, clamps a negative result to zero, and otherwise adds the new value to `+0xA08`. Eases orientation `+0x48` toward direction-table entry 2 for delta `-1`, entry 3 for `+1`, with coefficient `0.1`; snaps directional speed to zero. Increments counter and decides relocation only when the **old** value is `>=12`. |
| `2` | Eases the three components of auxiliary `+0x2C0` toward destination `+0xA20` with coefficient `0.2`. On old counter zero calls `FUN_00226CE0(fighter,0,0x100,8,7)`. Copies current position into both `+0xA10/+0xA00` each call. Airborne orientation approaches paired-target angle `+0x328` with coefficient `0.3`; grounded orientation approaches the `+0x990 & 1` table direction with coefficient `0.1`. |

The four floats at resident direction table `0x005C16B0` are approximately
`pi/2`, `-pi/2`, `0`, and `-pi`; these are orientation values, without an
assigned screen direction.

The normal relocation branch applies when current section `+0x9F6` equals
cached paired section `+0x324`, or input history contains no bit `0x1000` in
its newest 12 records. `FUN_00217260` counts matching records in the 32-entry
ring; this is any matching record, not a requirement that the bit be held
throughout. Logical `0x1000` is produced by the configured attack binding,
default Circle, and can also be reinserted by action-chain input processing
as documented in [Action commands](../combat/action_commands.md).

**Observed normal relocation:** copies destination `+0xA20` to position and
`+0xA00`, with `300` added to component `+8`; sets byte `+0x61` bit `0x40`;
adds signed delta to section `+0x9F6`; copies position to history snapshot
`+0x970`; refreshes paired geometry for both fighters via
`FUN_002174A0(fighter,0)`; synchronizes `+0x98C/+0x98E/+0x990` from paired
facing `+0x326`; snaps orientation to that direction; and explicitly selects
descriptor phase `2` through BTL live `0x0071EEF0`. It enters local stage `2`
with counter zero. If cursor flags at `+0x226` do not already contain bit
`4`, it initializes the `+0x224` cursor block's integer and float positions
to `-4`, sets its mode bits and latches bit `4`.

**Observed alternative:** differing sections plus at least one recent
`0x1000` record instead call `FUN_0021D0C0` with offset scale
`partner[+0xE8] * partner[+0x2F0] * 0.75`, selector `4`, mode `4`, mask
`0xFF`. That service selects cached paired section `+0x324`, resolves a
paired-relative position, sets the relocation bit, and refreshes paired
geometry. The handler saves that position to destination `+0xA20`, then adds
`partner[+0xE4] * partner[+0x2F0]` to its vertical component, reduced to
`0.75` of that addition when transferred contact byte `+0xB9D` is nonzero.
It synchronizes the direction/facing halfwords from `+0x326`, initializes
the same cursor block to `-6` when its bit `4` is clear, enters ordinary fall
`(3,0x1E)`, then sets byte `+0xA41` to `1`. It does not enter local stage `2`
or perform the normal branch's section-plus-delta store.

**Inference:** the alternative selects the paired fighter's section and a
relative placement rather than the initially resolved destination. No
player-facing move name is assigned to this branch.

### Alternative placement correction and contact handoff

**Observed:** `FUN_0021D0C0` stores cached paired section `+0x324` into
current section `+0x9F6` before correcting the relative candidate. Selector 4
uses vector `(0,1,0,0)` at resident `0x00407DB0`; mode 4 selects the paired
fighter's saved facing `+0x984` and position `+0x970`.

`FUN_0021CC00` first calls `FUN_0021C550`. With paired contact byte `+0xB9D`
nonzero, that helper compares the candidate's direction with paired halfword
`+0x986`; on its matching side it places candidate component 0 at paired
`+0x970` plus or minus 10 and returns 1. `FUN_0021CC00` returns whether this
specific adjustment occurred, while also applying segment/environment
corrections selected by mask `0xFF`. Its return is not a general geometry
admission result; the corrected candidate is installed in either case.

When that result is true and the paired contact byte remains nonzero,
`FUN_0021D0C0` moves paired `+0xB9D` into the transferring fighter, clears
the paired byte, copies paired `+0xB9F`, sets the transferring fighter's
`+0xBA0` to `0.1`, and writes sentinel bits `0xC6875104` to paired `+0xBA0`.
The transfer handler subsequently tests this acquired contact byte when
choosing its full or three-quarter height addition.

The mask-`0x10` branch of `FUN_0021C9A0` calls field endpoint service BTL live
`0x00708AF0`. With a background present, its leaf live `0x006C23A0` compares
candidate component 0 against the section's two endpoint records at
`background + 0xA40/0xA50 + section*0x20`. An out-of-interval candidate is
replaced by the corresponding endpoint vec4 and returns 0; inside or exactly
on an endpoint returns 1. The caller restores the candidate's component 2
after correction and sets fighter byte `+0xB04` to 1. The leaf's instruction
bytes at import `0x006C2360..0x006C23BF` establish the lower `c.le.s` and
upper `c.lt.s` comparisons. The mask-`0x20` path also uses the
floor-profile service. Endpoint construction and general query algorithms
remain with [Stages](stages.md#boundary-and-floor-profile-data) and
[Collision](../combat/collision.md#stage-query-functions).

Finally, `FUN_0021D0C0` sets relocation bit `+0x61 & 0x40`, installs the
candidate at physical `+0x30`, and, when field service live `0x007090D0`
succeeds for the selected section to itself, copies only returned component
`+4` to physical `+0x34`. It refreshes paired geometry through
`FUN_002174A0(fighter,1)` before returning to the handler's height addition.
These operations establish the correction sequence, not the resulting
separation on every authored stage.

## Descriptor phases and normal return

The eight-byte substate table at BTL live `0x0089AEB0` gives `0x15` retail
name `ACT_LIN_0` and phase pointer `0x0089A0C0`; `0x16` is `ACT_LIN_1`
with pointer `0x0089A0F0`. Both arrays have identical contents:

| Phase | Animation slot | Condition | Start | Rate / `256` |
| --- | ---: | ---: | ---: | ---: |
| `0` | `0x35` | `-0x10` | `0` | `1.5` |
| `1` | `0x36` | `0` | `0` | `2` |
| `2` | `0x39` | `-0x11` | `0` | `1` |
| `3` | `0x3B` | `-0x10` | `0` | `1` |
| `4` | `-1` | `0` | `0` | `0` |

The complete phase-condition consumer BTL live `0x0071F160` (imported
`FUN_0071F120`) advances `-0x10` on animation-completion word `+0xB88`,
`-0x11` on grounded bit `+0x63 & 0x80`, and leaves condition `0` unchanged.
Each advance resets secondary timeline `+0x1DC`. A selected animation slot
`-1` reports completion. `FUN_00248580` then returns transfer substates
`0x15/0x16` to neutral `(0,0)` through `FUN_00217E40`. Explicit relocation
selection of phase `2` bypasses the phase-1 wait; local stage `2` itself has
no fixed elapsed-update completion check.

The descriptor bytes are at import `0x0089AF18..0x0089AF27`, names at
`0x0089A970..0x0089A98F` and phase records at `0x0089A080..0x0089A0DF`.
Instructions `0x0022EB04..0x0022F080` establish the relocation, alternative
branch and exact old/new counter comparisons.

## Interruption and cleanup

**Observed:** `FUN_0022F0B0` restores vec4 position from `+0xA10` and section
from saved halfword `+0x9F8` only when transfer stage `+0x9F2 < 2`, setting
byte `+0x61` bit `0x40`. It then calls `FUN_0022F110` in either case.

`FUN_0022F110` clears transfer delta `+0x9F0`, halfwords `+0x30A`,
`+0x31A/+0x31C/+0x31E`, words `+0x30C/+0x320`, and sets floats
`+0x310/+0x314` to `1.0`. It derives facing halfword `+0x990` from the sign
of orientation component `+0x48` and snaps that component to the corresponding
direction-table value at resident `0x005C16B0`. It resolves registrations
`1` and `2` through `FUN_001DDD80(fighter+0xDD0,index)` and applies
`FUN_001DCCC0`, which activates an inactive registration in the global DD
chain. This cleanup does not itself restore position or section, clear local
stage/counter `+0x9F2/+0x9F4`, clear presentation lock `+0x318`, or directly
clear mode flags `+0x308`. Presentation update `FUN_00226370` clears the
active mode bits when their duration fields are zero.

### Direct cleanup paths

State setter `FUN_00217E40` first calls old-state exit dispatcher
`FUN_00217BD0`; major `1`, substate `0x15/0x16` goes through
`FUN_0022E740` to cleanup `FUN_0022F110`. This occurs before the setter's
same-state early return as well as on an actual state change. New-state setup
`FUN_00217D30` contains no transfer-specific entry callback. Transfer-local
initialization instead happens through event `0` in the motion handler.

| Direct caller | Established section-transfer consequence |
| --- | --- |
| `FUN_00216A60` | Under `+0x62 & 1 == 0`, interrupts an active transfer, then enters neutral if grounded or ordinary fall otherwise. Its other response/exchange cleanup belongs to [Hit response](../combat/hit_response.md). |
| `FUN_0021E0C0` | Interrupts whenever delta is nonzero, then handles surface-axis exit independently. This wrapper does not select a new action itself. |
| `FUN_002209A0` | All four accepted-response source-mode paths interrupt an active transfer after their acceptance gates and before ordinary/guarded response dispatch. Rejected/intercepted paths can return earlier. |
| `FUN_00225330` | Its response-entry branch interrupts before forcibly entering `(5,0x37)`. Its major-state and response gates remain separate from transfer state. |
| `FUN_00226FA0` | When `FUN_00306A60` finds list effect ID `0` or `1`, interrupts an active transfer and calls `FUN_00227200`, entering `(0,2)` and setting `+0x61 & 0x80` and `+0x62 & 0x10`. Its return suppresses ordinary request processing when it first installs the `+0x62` bit; an already-set bit does not produce that return. Effect identity belongs to [Battle items and status effects](../projectiles_and_items/battle_items_and_status_effects.md). |
| `FUN_00216D00` | When its coordinator exists and `+0x62 & 1 == 0`, calls cleanup directly for both paired fighters before selecting coordinator participants. It does not use the origin-restoration helper. |

Direct `jal` encodings in the resident and BTL images reach request helper
`0x0022E760` from two physical resident callsites, motion `0x0022E950` from
one, interruption `0x0022F0B0` from eight and cleanup `0x0022F110` from four;
none are in BTL. Every caller family above was read. This covers those exact
direct calls, not computed function pointers or tail jumps. Immediate `sh`
stores to offset `0x9F0` occur only in initialization `FUN_00214A40`, which
clears it, request `FUN_0022E760` and cleanup `FUN_0022F110`, and none in BTL. Wider stores and
rebased aliases were not exhaustively scanned.

## Presentation, interaction and camera consumers

### Alternative outcome byte

**Observed:** the alternative branch writes `+0xA41 = 1` at resident
`0x0022EE90`, after the state setter has exited the transfer and installed
fall `(3,0x1E)`, so transfer cleanup runs before that write. The byte is
shared action history rather than a transfer-local flag; its resets, readers
and other producers are documented in
[Combat action execution](../combat/combat_action_execution.md#prior-outcome-byte-lifetime).

### Visible placement and presentation amounts

**Observed:** while transfer delta is nonzero, shared model-transform update
`FUN_0024D3C0` passes visual position `+0xA00` to `FUN_0019CB70`, with
orientation `+0x40` and model scale `+0x2E0`. Without a transfer it selects
the ordinary position/pause path. Consequently the stage-1 additions to
`+0xA08` affect model placement without being writes to physical position
`+0x38`. No observed arc duration or screen direction is inferred.

Entry presentation helper `FUN_00226B00(...,8,4)` requests mode `2` in
`+0x308`'s low nibble, target factor `+0x314 = 0`, duration `+0x30A = 8`,
and mode `0x20`, duration `+0x31A = 4`, in the high nibble. Arrival helper
`FUN_00226CE0(...,8,7)` requests the complementary modes `1/0x10`, factor
target `1`, durations `8/7`. Both install these requests only when
lock/countdown `+0x318` is zero, then set that countdown to the larger supplied
duration.

`FUN_00226370` advances factor `+0x310` toward the target by the reciprocal
duration, advances signed presentation amount `+0x31E` toward `100` on entry
or toward `0` on arrival, and decrements lock `+0x318`. Integer conversion
occurs on every `+0x31E` step, so the `7` divisor does not justify assuming
exactly seven updates to zero. The mode bits clear after passing their bounds.
`FUN_00226900` supplies `+0x310` to model `+0x88` (subject to a separate
status branch), stores a factor-derived renderer byte `+0xE4`, and passes
`+0x31E/+0x320` to renderer setter `FUN_0010D220`, which clamps the amount
to `0..100`. These prove presentation control fields, not a particular visual
effect's appearance.

`FUN_001BB790` forwards model `+0x88` to its object-render functions.
For ordinary model objects, `FUN_00190F40` multiplies that factor by the
object's inherited factor and requires the product to be at least `1/128`
for its ordinary geometry submission. `FUN_001982B0` stores the product in
render context `+0x114`. **Inference:** this is the transfer's fade-out and
fade-in factor. The complete material/shader alpha mapping beyond that
submission contract is not established.

These two presentation functions run from shared phase-2 fighter callback
`FUN_0024DD70` when node flag bit `2` is set, separately from the motion
handler's phase-1 update. The shared scheduling and concrete-table coverage
are owned by [Battle lifecycle](../session/battle_lifecycle.md#what-phase-2-guarantees).
Handler counters, action timelines, and presentation-update counts therefore
must not be treated as one timer.

### Authored animation, effect and sound bindings

**Observed selected variants:** the descriptor slots resolve through each
fighter's animation-name array, rather than naming one universal animation.
The sampled pointers are Naruto record `0x004DAD80`, array `0x004D5E30`,
and Hiruko record `0x005403A0`, array `0x0053C1C0`:

| Descriptor slot | Naruto ID 57: name / authored frames | Hiruko ID 76: name / authored frames |
| --- | --- | --- |
| `0x35` | `ANM_pnrwnxj0` / 7 | `ANM_pschnxj0` / 11 |
| `0x36` | `ANM_pnrwjmp0` / 17 | `ANM_pschjmp0` / 17 |
| `0x37` (alternative fall) | `ANM_pnrwdow0` / 16 | `ANM_pschdow0` / 16 |
| `0x39` | `ANM_pnrwdow1` / 16 | `ANM_pschdow0` / 16 |
| `0x3B` | `ANM_pnrwlan0` / 10 | `ANM_pschlan0` / 13 |

The alternative installs ordinary-fall descriptor live `0x0089A190`, whose
first row uses slot `0x37`, condition 0, start 0 and rate 1. This establishes
a different descriptor route from the normal phase-2/phase-3 return. Provider
selection and lookup ownership remain with
[Character asset tables](../../game/character_assets.md#animation-name-and-0x4c-stride-tables).

The frame counts above come from the named local `0x0700` records in retail
`PL/2NRWBOD1.CCS` and `PL/2SCHBOD1.CCS`; this covers only the selected
records, not a complete container census. Parser `FUN_001B1470` establishes
that the field after record ID is the authored frame count, as documented in
[CCS runtime](../../game/files/ccs_runtime.md#animation-track-parsing).
The different `nxj0` and `lan0` lengths coexist with the handler's fixed
counter boundaries. Playback rate, timeline events, grounding and scheduling
remain separate, so these counts do not establish total transfer duration.

Both branches share the local-stage-0 entry call
`FUN_00226B00(fighter,0,0x100,8,4)`. Its mode argument 0 requests effect
resource `0x11` and resource 9 through `FUN_003350E0`, then common SFX event
`0x0F`. Resource `0x11`'s row at `0x005A3E90` names container `effect0x`
and `ANM_e0x_line_00`, kind 4. Resource 9's row at `0x005A3E10` names
`ANM_e0x_smok_01` in the same container, kind 1. `FUN_0030D3B0` resolves
both during its `0..0x6A` lookup loop into array `0x006B3780`; the transfer
uses those resolved pointers through `FUN_0030F610/FUN_0030F290`.
Resource 9 also sets mask `0x2000` on its two named objects
`OBJ_e0xsmok01a/b`. No observed appearance is assigned to these authored names.
Retail `CMN/EFFECT0X.CCS` authors 13 frames for
`ANM_e0x_line_00` and 41 for `ANM_e0x_smok_01` in `CMN/EFFECT0X.CCS`.

Normal local-stage-2 arrival calls `FUN_00226CE0(fighter,0,0x100,8,7)`;
mode 0 invokes `FUN_00338330`, which binds resource `0x11` at physical
position `+0x30` and resets its player to frame zero. The arrival helper also
requests SFX `0x0F`. Entry's resource-`0x11` placement instead adds 75 to the
supplied position's vertical component; resource 9 uses the unshifted position
and rate `0x100`.
These effect anchors use physical position, independently of visual `+0xA00`.
The alternative exits before local stage 2 and therefore does not reach this
arrival helper. Other fall/action cue producers are separate.

The helpers' presentation lock suppresses their mode-field setup, not the
subsequent effect/audio requests. Effect allocation uses the shared manager's
`+0x41C` controller; `FUN_0030E130` can recycle an existing element when its
pool is full. The helpers do not retain a fighter-owned effect handle.

**Observed effect lifetime:** element reset `FUN_0030E8D0` enables retirement
byte `+0x1AD`, clears completion `+0x1AF`, and clears loop byte `+0x1AC`.
The inspected transfer bindings leave these effects nonlooping. Concrete
element table `0x005DC830` selects update `FUN_003108A0`: for kinds 1/4,
with playback gate `+0x1EC` clear and a bound player resource present, it
advances the player and publishes completion in `+0x1AF`. On a later eligible
update, completed/nonlooping playback with retirement enabled invokes slot
`+0x18`, resident `0x0028BF30`, an eight-instruction setter of the low bit
of node byte `+0x24`. Controller `FUN_0030E020` then releases/unlinks
flagged elements through `FUN_0030EBC0`. Transfer cleanup does not retire them
directly. This establishes a playback-driven retirement path, not guaranteed
resource availability or observed visibility/timing. Shared scheduling remains
with [Battle auxiliary services](../session/battle_auxiliary_services.md#resident-effect-manager-callbacks-and-ownership).

The common SFX selector at `0x00406FEE` maps transfer selector `0x0F` to
event `0x0F`; its eight-byte control row at `0x003FCA18` is
`0F 00 00 3C 7F 7F 00 01`. This identifies the shared event/control request,
not its audible sample. Bank resolution and command fields remain with
[Battle audio](../session/battle_audio.md#sfx-selectors-and-loaded-sound-banks).

### Interaction-registration interval

At primary-timeline event `8`, `FUN_0022E950` deactivates registrations `1/2`
from fighter list `+0xDD0` through `FUN_001DCD10`. On the first local-stage-2
update, provided event `8` is not crossing on that same call, it activates
them through `FUN_001DCCC0`. Cleanup also activates them. Their DD chain
operations and generation-safe lookup belong to [Collision](../combat/collision.md).
This establishes a temporary interaction-registration interval; it does not
prove immunity to every attack source or every independent query family.

The shared movement pass also explicitly avoids grounding on polygon
attribute `0x10000` while delta is nonzero and local stage is `2`, in the
relevant downward-contact branch; ordinary geometry and contact ownership
remain in [Movement and physics](movement_and_physics.md#floor-side-surfaces-and-limits).
Other polygons can still supply grounding for descriptor phase `2`.

### Camera positions

Resident position service `FUN_00216320` returns auxiliary vec4 `+0x2C0`
while the delta is nonzero. That easing does not establish what the main
camera follows: it selects between physical position `+0x30` and origin
snapshot `+0xA10`
through its own transfer branch, and the delta and destination component also
select its eye/target smoothing coefficients. Both are documented in
[Battle camera](../session/battle_camera.md#tracking-target) and
[Battle camera smoothing](../session/battle_camera.md#smoothing).

## Representative character-dependent placement

The shared handler's `4` and old-counter-`12` boundaries, visual increment
constants `80/18`, normal relocation height addition `300`, and both phase
arrays are fixed. Its alternative placement depends on the **paired**
fighter's copied contact dimensions and scale. Record-copy ownership and the
completed dimension census remain in
[Movement and physics](movement_and_physics.md#character-movement-parameters).
Four representative IDs supply these record `+0x58/+0x5C` values:

| Paired ID / record | Height `+0xE4` | Width `+0xE8` | Requested offset scale at unit `+0x2F0` | Added height if contact byte is zero / nonzero |
| --- | ---: | ---: | ---: | ---: |
| Naruto `57`, `0x004DAD80` | `150` | `110` | `82.5` | `150 / 112.5` |
| Sakura `58`, `0x004E01B0` | `150` | `110` | `82.5` | `150 / 112.5` |
| Nine-Tailed Fourth Awakened State `73`, `0x00535D50` | `145` | `130` | `97.5` | `145 / 108.75` |
| Sasori (Hiruko) `76`, `0x005403A0` | `170` | `160` | `120` | `170 / 127.5` |

These are arithmetic inputs before environment correction, not guaranteed
world-space separations. Offset selector `4` is resident vec4 `(0,1,0,0)` at
`0x00407DB0`; `FUN_0021CC00` rotates the scaled offset by the paired fighter's
saved facing `+0x984`, adds it to paired position snapshot `+0x970`, and
passes the candidate to geometry correction. Character labels follow
[Character identity](../characters/character_ids.md) and its linked retail reference.
A sampled extra-model path, ID `47`'s `FUN_0027ECB0`, also explicitly uses
visual `+0xA00` during transfer and copies the presentation factor to its
additional model. Its callback is final concrete table `0x005DAB20` slot
`+0x28`. Other derived model callbacks were not exhaustively inspected.

### Chiyo's additional scenes use a different position source

**Observed:** ID 62's constructor `FUN_002A8E40` installs concrete table
`0x005DA830`, whose `+0x28` selects `FUN_002ADA80`. The shared phase-2
callback invokes this slot after submitting the primary scene. With node
flags `& 2` nonzero, fighter `+0x61 & 0x10` clear and `FUN_00224650() != 1`,
the derived callback updates both additional players at `+0x5C68/+0x5CE8`.
It copies the primary player rate, attempts to select their matching animation
through `FUN_002AD430`, positions them through `FUN_002AD570`, and copies primary
model factor `+0x88` into each. Additional submission through
`FUN_002A97A0` separately requires `+0x56B4 & 2`.

For the inspected transfer/fall slots, the source names are the two columns
of interleaved table `0x005C3810`, read at `0x005C39B8..0x005C39EF`.
Their named local `0x0700` records in retail `PL/2CHYBOD1.CCS` establish:

| Primary slot | First additional scene / authored frames | Second additional scene / authored frames |
| --- | --- | --- |
| `0x35` | `ANM_pfatnxj0` / 9 | `ANM_pmotnxj0` / 9 |
| `0x36` | `ANM_pfatjmp0` / 17 | `ANM_pmotjmp0` / 17 |
| `0x37`, `0x39` | `ANM_pfatdow0` / 16 | `ANM_pmotdow0` / 16 |
| `0x3B` | `ANM_pfatlan0` / 13 | `ANM_pmotlan0` / 13 |

`FUN_002AD430` binds the selected lookup, records primary slot `+0xB8C`,
resets the additional timeline, and seeks the primary start frame `+0xB94`
when nonzero and the resource is bound. A missing lookup keeps an unfinished
additional animation; after its completion it instead binds slot `0x29`.
`FUN_002ADA80` advances an additional player only while its own completion
word is zero and its resource is bound. These scenes therefore do not acquire
a universal duration from the shared transfer counters.

`FUN_002AD570`'s special bone/offset path requires its recorded animation slot
below `0x23` and different from `0x1C`. All four transfer slots and fall
slot `0x37` fail that gate. When one of those slots is installed, it passes
fighter physical position `+0x30`, orientation `+0x40` and scale `+0x2E0`
directly to the additional scene transform. It does not select transfer visual
`+0xA00`.
Thus primary and additional scenes can receive different placement sources
while sharing the presentation factor. This is a static placement distinction;
the draw gate and model-factor gate prevent inferring what is simultaneously
visible. Auxiliary animation providers and puppet ownership remain with
[Character asset tables](../../game/character_assets.md#auxiliary-model-animation-providers)
and [Puppet control](../characters/puppet_control.md).

## Confidence and remaining leads

**High static confidence:** request return classes and ordering, transfer-local
stages, fixed counter comparisons, all stores in normal/alternative relocation,
phase arrays, direct interruption callers and presentation/control lifetimes.
The alternative's contact handoff and outcome-byte write, selected authored
resources and inspected effect-retirement path are also established statically
from complete instruction bodies, including the request, motion, cleanup and
renderer-field consumer.

**Bounded findings:** direct `jal` and immediate-store scans use the concrete
targets above. They do not establish absence of wider stores, rebased field
aliases, indirect calls, tail calls or replacement character callbacks. The
four sampled dimensions establish arithmetic variation, not a new complete
character census. Naruto/Hiruko primary records, Chiyo's additional scenes and
the two common effects are selected resource samples, not a complete
character/container census.

The strongest remaining static leads are remaining character-specific
extra-model presentation callbacks, the shared SFX event's audible sample
identity, and the section resolver's behavior on the complete authored
stage-line set. These leads do not change the confirmed
request/relocation/return contract above.
