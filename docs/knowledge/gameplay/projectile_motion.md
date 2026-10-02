# Projectile motion and local timing

This document describes the derived motion callbacks of retail NA2
(`SLPS-25837`) `BTL.BIN` projectile classes: the common candidate-position and
commitment order, per-class velocity and direct-position updates, record
inputs, contact-driven phases, emission schedules, Clay/Ink guide producers,
character-carrier command rows, and the local clocks and counters that drive
them. Configuration, class identity, spawn, manager ownership, transitions,
and removal are in [Projectile lifecycle](projectiles.md). Addresses are live
EE addresses unless labelled otherwise; see
[Address conventions](../game/files/file_identities.md#address-conventions).

## Research coverage

- **Assigned scope:** the motion/state callbacks of the factory projectile
  classes reached through slot `+0x1C` and the related extended slots, their
  record inputs, contact transitions, event schedules, and local timing
  inputs; selected Clay/Ink Bird guide producers and lifetimes,
  launcher-supplied record blocks, and character-carrier command publication,
  movement admission, and cleanup.
- **Exploration depth:**
  - All 60 distinct factory slot-`+0x1C` bodies were traced through their raw
    return paths, including literal no-ops. Selected setup, movement, contact,
    and emission helpers were expanded. The complete Parabola launch solver,
    nine-row Kibakufuda schedule, three-entry Kagebunshin schedule, and
    six-way BakutiBall decision were recovered.
  - Guide construction, borrowed binding, writable key copies, Bird S's
    launcher-supplied block, and N/S/Ink Bird cleanup were traced for the
    selected producers.
  - All five carrier constructors' command publications, the shared `+0x60`
    command/movement consumer, its two row widths, cursor crossing gates, and
    selected class `+0x64` format switches were traced.
  - Callback composition was compared against the root vtable for seven
    representative selectors.
- **Confirmed coverage:**
  - The shared candidate/commitment order and, for all 60 motion-entry bodies,
    the per-family velocity and direct-position updates, class-specific record
    inputs, contact-driven phases, emission schedules, and distinct local
    clock/counter inputs.
  - Homing's live fighter-position lookup and HomingDelay's delayed position
    snapshot; neither retains a fighter pointer.
  - Selected guide channel construction, borrowed versus copied key bindings
    and release, source sentinel/count checks, and the Bird S launcher block
    and guide retiming.
  - All five carriers' table/array publications, command-row selection,
    movement crossing gates, resource cursor inputs, movement-gate lifetime,
    and embedded-registration lookup/cleanup.
- **Unresolved or untested:**
  - Nested services and callbacks beyond the traced motion-entry bodies, and
    every class's complete state machine.
  - Guide producers and carrier commands beyond the selected publications and
    routes: unrestricted aliases of the guide and command-table interfaces,
    every authored key's contents, all class-local choices of `+0x430/+0x434`,
    the remaining full-row payload consumers, the producer of the selected
    carrier registration under every route, and the source-container lifetime
    under every external teardown.
  - A complete curve-interpolation audit of the guide sampler.
  - Several class-local predicates and lookup objects whose broader meaning
    is noted as open in the body, including resident predicate
    `0x00306420(fighter, 0x4A)`.
  - COP1 conversion rounding mode.
  - Negative result: the selected guide blocks' key tail floats are zero and
    unused by the selected linear flags; other flags and blocks are not
    covered.
- **Deliberate exclusions and overlap:** configuration, class identity, spawn,
  manager callbacks, transitions, and removal belong to
  [Projectile lifecycle](projectiles.md); random wrappers to
  [Randomness](../runtime/randomness.md#mt-wrappers); fighter motion events
  and movement to
  [Combat action execution](combat_action_execution.md#authored-motion-events-and-phase-payload)
  and [Movement and physics](movement_and_physics.md); resource containers
  and resource-loop execution to [CCS runtime](../game/files/ccs_runtime.md)
  and [Animation runtime](../runtime/animation_runtime.md); collision query
  internals and contact classes to
  [Collision](collision.md#resident-segmentenvironment-broad-and-narrow-phases)
  and [Stage surface attributes](stage_surface_attributes.md#authored-word-and-geometric-class);
  damage to [Damage](damage.md).
- **Evidence limitations:** static analysis of retail `BTL.BIN` raw
  instructions and data, with resident code read only for called services.
  Local clocks, accumulators, countdowns, resource cursors, and equality
  schedules are callback counters; they do not establish live callback
  cadence, frame or real-time duration, or animation rate. Dynamic target
  outcomes and collision-shape semantics are outside this evidence.

## Continuing state-2 motion and position commitment

The continuing path in common state-2 handler live
`0x0072DF7C..0x0072E018` calls virtual slot `+0x1C`, then candidate-position
helper `0x00732BD0`. For response modes other than `3/4`, byte `+0x81 == 1`
also admits virtual contact slot `+0x3C(self, candidate, 1)`. It then calls
slot `+0x38(self, candidate)`. Earlier response branches in that state handler
can take other paths; this order is not an unconditional invocation promise.

Helper live `0x00732BD0..0x00732C7C` computes:

```text
step = min(object float +0x278, manager float [+0xC8 + 4*inverse-side])
candidate.xyz = current.xyz + (object vector +0x1C0 + vector +0x1D0).xyz * step
candidate.w = 1.0
```

The inverse-side service is `0x00734130`. The helper returns the candidate in
caller storage; it does not write object position `+0x30`. Root slot `+0x38`,
live `0x00730120..0x00730138`, copies all four candidate words into `+0x30`
only when byte `+0x27D` is nonzero. A derived contact or commitment callback
can therefore affect the result after the movement callback has run.

The common record setup at live `0x0072BF70` copies record float `+0x1C`
into speed `+0x1E0` only when that instance scalar is `-1.0f`. That branch
also copies the inverse-side manager scalar into `+0x278` and sets
byte `+0x27C = 1`. Manager reset live `0x00734470..0x00734538` initializes
both `+0xC8/+0xCC` entries to `1.0f`.

Root update calls step helper live `0x0072ED10..0x0072EDD8` after its positive
delay and inactive gates. With byte `+0x27C == 0`, that helper preserves the
instance scalar. Otherwise it selects the same-tag fighter from battle global
`+0xDE4 + 4*tag`. If resident predicate `0x00306420(fighter, 0x4A)` is nonzero
and Euclidean position distance is at most `400.0f`, it writes `+0x278 = 0.25f`;
otherwise it writes `1.0f`. Distance service `0x001806F0` computes the square
root of the sum of squared xyz differences. The broader meaning of predicate
`0x4A` is not established by this consumer.

At the end of an admitted root update, accumulator `+0x1FC` increases by
`+0x278`, while signed halfword counter `+0x200` increases by one. These are
different time inputs: position uses the minimum with the manager scalar;
some derived countdowns decrement by one and others subtract `+0x278`.
No conversion of any of them to frames or seconds follows from this local
evidence.

In the motion contracts below, `q` means float `+0x278`, and `int(x)` denotes
the observed COP1 `cvt.w.s` conversion rather than an assumed truncation rule.
`bounded_draw(n)` uses resident `0x00180210`, returning the unsigned remainder
modulo `abs(n)+1`; ordinary nonnegative input therefore includes both `0` and
`n`. Signed scaled draws use `0x001802B0`. The wrapper contracts belong to
[Randomness](../runtime/randomness.md#mt-wrappers).

## Straight and distance-scaled launch vectors

`ccProjectileStraight` motion live `0x00738E40..0x00739060` initializes only
when byte `+0x87 == 1`: it enables `+0x206`, signals handle `+0x6C`, normalizes
`+0xA0 - current position +0x30` into direction `+0xF0`, and writes
`+0x1C0 = direction * speed +0x1E0`. It clears `+0x87` and performs the
position-associated resident call `0x003363F0(0.5f, object+0x30)`. Later calls
to this body leave that launch velocity unchanged. Movement and contact then
use the common candidate/commitment path above.

Config `0x31` has a preliminary aim adjustment: it compares the sign of
`(+0xA0 - +0x90).x` with the opposite-tag fighter's float `+0x48`, and reverses
that x difference if their signs disagree. With byte `+0x1F0 == 0`, it instead
resets the aim to `+0x90` and offsets x by `+100` or `-100` according to that
fighter scalar. These are config-specific branches, not a general Straight
target acquisition policy.

`ccProjDist2Speed` and `ccProjKNWbuddy` share motion live
`0x007392E0..0x00739628`. Their first-call direction starts from
`+0xA0 - current position`; signed halfword `+0x268 == 0` adds vector `+0xB0`
before normalization. The distance used to choose speed is separately measured
between `+0xA0` and `+0x90`, without that vector addition. If signed record
word `+0x38 != -1`, instructions live `0x00739508..0x0073956C` replace
`+0x1E0` with:

```text
clamp(distance / float(record word +0x38),
      float(record word +0x40), float(record word +0x3C))
```

The three inputs are signed words converted numerically to floats, not float
bit patterns. The body stores normalized direction in `+0xF0`, scales it into
`+0x1C0`, and clears `+0x87`. The ratio is a launch-time speed selection;
this body does not recompute it on subsequent motion calls.

## Parabola vertical update

`ccProjectileParabola` and `ccProjectileNumbnessBall` share motion live
`0x00744820..0x007449DC`. First activation enables `+0x206`, clears
`+0x88/+0x87`, and signals `+0x6C`. If scalar `+0x1E4 == -1.0f`, it calls
automatic launch solver `0x00744A30`; otherwise it normalizes
`+0xA0 - +0x90` and scales it by speed `+0x1E0` into `+0x1C0`.

That initial branch falls through into helper live
`0x007449E0..0x00744A24` on the same invocation. Raw COP1 instructions prove
the following update, including a negate rather than an absolute-value operation:

```text
velocity.z (+0x1C8) -= scalar +0x1E4 * step +0x278
velocity.z = max(velocity.z, -60.0f)
```

Each continuing call applies this helper and normalizes the resulting velocity
into `+0xF0`. Config `0x36` additionally increments angle `+0xE4` by the float
bits `0x3E80ADFD` (approximately `0.25132743`) and wraps it around the pi
boundary. That angular increment has no `+0x278` multiplier in this body.

The automatic solver live `0x00744A30` writes acceleration `+0x1E4 = 3.0f`.
It can revise the aim for configs `0x30/0x9A` using the same-tag fighter's
position and a resident height result; it also compares opposite-tag direction
and the two fighters' halfword `+0x9F6` in config-specific branches. The bounded
solver at `0x00744A30..0x00745384` uses horizontal difference `X`, vertical
difference `Z`, speed `s = +0x1E0`, and `g = 3`:

```text
a = g * X * X / (2 * s * s)
b = -abs(X)
c = Z + a
D = b*b - 4*a*c
angles = atan((-b + sqrt(D))/(2*a)), atan((-b - sqrt(D))/(2*a))
```

For configs `0x36/0x3B` when the fighters' `+0x9F6` values differ, `X` is
the length of the aim-minus-spawn xy vector and the resulting velocity is
rotated back by its xy bearing. Otherwise `X` is the x difference. The reference
angle is `atan(abs(Z/X))`, or zero for zero x difference.

Raw branches `0x00744EB0..0x00745230` sort the two roots as low/high and
first try the low root. For each root they calculate
`t = abs(X)/(s*cos(angle))` and height
`spawn.z + t*s*sin(angle) - 0.5*g*t*t`. Low is kept when its height plus
`150` reaches the target height; otherwise high is tried. If neither reaches
that comparison, the result is high when the reference angle exceeds low,
otherwise `max(low, *(float*)0x008C4D88)`. The retail word at that live constant
address is zero. These are the instruction comparisons, without assuming
that continuous trajectory predictions exactly match the discrete updater.

For negative `D` or zero `X`, the fallback compares `abs(X)` with double
`5.0` through resident predicate `0x001003E0`. Its true branch selects either
sign of pi/2 according to target height. Its other branch wraps
`reference-angle + 0.55` around pi and takes the minimum with the float at
live `0x008C4D90`, also a zero word in retail. A negative x difference reflects
the selected angle as `pi - angle` and wraps it again. The final stores are
`velocity.x = s*cos(angle)` and `velocity.z = s*sin(angle)`; the motion
callback then applies the first gravity update described above.

Parabola contact slot live `0x00745390..0x007458C4` first calls root contact
response `0x00731F80(self, candidate, 1)`. Only configs `0x30/0x9A` then run
its extra emission path. It admits object flag `+0x23C` bit `4`, or bit `5`
(also remembering bit `3`), or contact-query result bit `4` from
`0x007319D0`. Raw doubleword shifts establish those bit numbers.

- Config `0x30` emits one config `0x44` at the candidate position.
- Config `0x9A` normally emits two config `0x9B` children, reduced to one
  when object flag bit `5` admitted the path. Each starts from the projectile
  position, with a direction-dependent x offset of `200 * child-index`; the
  code probes a vertical segment with `150`-unit endpoints using resident
  `0x001BF100`. A failed probe preserves the attempted position; a successful
  probe uses the returned point with a `10`-unit adjustment.
- Successful children get delay `+0x84 = 10 + 2*child-index` and the observed
  parent lineage copy. Bit `5` clears child byte `+0x295`; with that branch
  and remembered bit `3`, it also sets child halfword `+0x292 = 3`.

After the loop it signals the parent handle and writes common `+0x82 = 1`,
`+0x7E = 6` at live `0x0074579C..0x007457A8`. This does not call the common
[state-6 helper](projectiles.md#state-6-transition-helper). The direct spawn calls are `0x007456A4` for config `0x9B`
and `0x00745704` for config `0x44`.

## Homing target data and the delayed strategy

`ccProjectileHoming` activation slot `+0x50`, live `0x0073F610` (Ghidra
`0x0073F5D0`, file `0x08B710`), initializes a direction from spawn vector 2
minus spawn vector 1 and sets collision participation `+0x206 = 1`. Unless
byte `+0x2A3` is set, it copies record signed words `+0x3C/+0x40` into object
`+0x290/+0x294`, clears `+0x298`, and copies record float `+0x48` into
`+0x29C`. Here `+0x290/+0x294/+0x298/+0x29C` are class-specific storage,
not pointers. Setter live `0x0073FC90` copies a supplied 16-byte vector into
that block and sets `+0x2A3 = 1`; activation then preserves it.

The complete motion body at live `0x0073F6C0..0x0073FC88` resolves the
same-tag fighter (`+0x8A = 0` selects battle global `+0xDE4`; tag `1` selects
`+0xDE8`) whenever its steering path runs. It copies the fighter's position
into temporary storage, optionally adds a resident-service height result, and
adds the object's `+0x290` vector before deriving the desired direction.
The steering window uses signed **words** `+0x290/+0x294`, byte
`+0x2A2 == 1`, and `t = s16(int(+0x1FC))`: it admits
`+0x290 <= t < +0x294`. The turn contribution is float `+0x29C * +0x278`,
otherwise zero. Raw loads at `0x0073F84C..0x0073F8B0` establish the word
width and the turn field; `+0x298` is not the turn scalar. The same 16-byte
block is subsequently added as a vector bias, so a caller-supplied vector and
record-produced timing words must not be assigned one universal field meaning.

It normalizes desired and current directions, snaps to the desired direction
when their dot product exceeds the cosine of the admitted turn amount, and
otherwise rotates about their normalized cross-product axis. It copies the
result to `+0xF0` and scales it by speed into `+0x1C0`. A fighter condition
`+0x18E == 1` with `+0x190 == 21/22`, and the manager x-bound check, clear
float `+0x29C`; an already computed turn contribution remains available to
that invocation. It retains direction vectors and scaled displacement, not the resolved fighter
pointer. For config `0x10`, reaching signed threshold `+0x2A0` enters state
`6`, clears `+0x82`, signals `+0x6C`, detaches `+0x70`, and clears `+0x216`;
this is a direct transition rather than a call to `0x00730950`.

`ccProjectileHomingDelay` has a different, fully bounded internal strategy at
live `0x00743A00..0x00743F0C` (Ghidra `0x007439C0..0x00743ECC`, file
`0x08FB00..0x09000C`). Its word `+0x290` is a three-phase internal state
independent of common state `+0x7E`.

Post-spawn setup live `0x00743770..0x007437C4` converts record signed words
`+0x38/+0x3C/+0x40` into float speed `+0x1E0` and steering-window bounds
`+0x298/+0x29C`. Record float `+0x48` supplies turn amount `+0x2A0`.
It sets wait word `+0x2A8 = -1`; config `0x1B` also sets byte `+0x26D`.
The phase behavior is:

- First activation enables `+0x206`, clears `+0x87`, normalizes vector
  `+0xA0 - +0x90` into direction `+0x1D0`, and selects phase `0`, except
  `+0x2A8 == -1` starts phase `1`.
- Phase `0` decreases scalar `+0x1E0` by `8.0f * +0x278`; the constant is at
  live `0x008C4D78`. At zero or below it clamps to zero, sets phase `1`, and
  clears phase counter `+0x294`.
- Phase `1` decrements signed word `+0x2A8`. Once nonpositive, it sets phase
  `2`, clears `+0x294/+0x1FC`, sets `+0x1E0 = 50.0f` from live `0x008C4D80`, and
  snapshots the same-tag fighter's position into `+0xA0`, with the observed
  height-service exception and vector `+0xB0` addition. It does not keep the
  fighter pointer and does not reacquire the fighter in phase `2`.
- Phase `2` uses `+0x298 <= +0x1FC < +0x29C` to enable steering amount
  `+0x2A4 = +0x2A0 * +0x278`, otherwise zero. It steers direction `+0x1D0`
  toward the stored `+0xA0` point. Outside manager coordinate bounds
  `+0x28..+0x24`, it clears steering scalar `+0x2A0`.
- Every continuing phase copies direction to `+0xF0`, writes scaled
  displacement `+0x1C0 = +0x1D0 * +0x1E0`, clears its fourth word, and
  increments phase counter `+0x294`.

Activation falls through to the selected phase in the same invocation. Phase-1
wait and phase counter increments are unscaled integer operations, unlike
deceleration, steering amount, and the root accumulator. With setup's `-1`
wait, first activation enters phase `1` and immediately proceeds to phase `2`;
other writers of `+0x2A8` can produce the longer strategy described above.

These consumers prove a live fighter-position lookup for Homing and a delayed
position snapshot for HomingDelay. They do not support calling the common side
tag an owner field. The exact inversion and lookup contract remains the
portable description; direct owner/target pointer storage in the common
object remains unproven.

## SoundWave phases and repeated events

`ccProjSoundWave` motion live `0x00740230..0x00740544` calls Homing
`0x0073F6C0` before its private phase byte `+0x2B6`. Constructor initialization
clears that byte and event threshold `+0x2B0`. Activation at `0x0073FF50`
loads signed countdown halfword `+0x2B4` from record word `+0x38`; its
Homing steering inputs retain the record `+0x3C/+0x40/+0x48` contract.

In phase `0`, a single `+0x2B0 < +0x1FC` check emits a resident-service event
and adds `5.0f` to the threshold. It does not loop to catch up missed thresholds.
The same phase subtracts `1.5f` from speed `+0x1E0` and clamps at zero, without
a step multiplier. It decrements `+0x2B4` by one. Once the new signed value is
negative, it emits another event, ends the three private effect references via
`0x007405A0`, resets the countdown to `20`, and increments phase to `1`.
Phase `1` decrements that countdown by one; a negative result writes common
state `6` and clears `+0x82`. Contact slot `0x00740550` also ends those three
references when root response sets `+0x23C` bit `0`. The resident events are
recorded as scheduling operations without assigning damage or audio meaning.

## Kibakukunai contact and private countdown

`ccProjectileKibakukunai` motion live `0x00741180..0x0074155C` first builds a
normalized launch vector from `(+0xA0 - current position) + +0xB0`, with the
observed 42-vector random selection scaled by `7.5f` and its y word cleared.
It scales direction by speed, enables collision, clears `+0x87`, sets private
word `+0x2D4 = 1`, and initializes float countdown `+0x2DC = 17.0f`.

Phase `1` copies velocity into `+0xF0`, subtracts `+0x278` from the countdown,
and writes its integer conversion into halfword `+0x1F8`. Phase `2` likewise
subtracts the step. A negative countdown in either phase invokes live
`0x00741560`: clear common counter `+0x200`, signal the handle, set private
phase `3`, and set `+0x1F8 = -1`. Phase `3` calls `0x00730F00` rather than
continuing the launch countdown. Byte `+0x2D8` additionally admits a repeated
resident event when signed `+0x200 % 5 == 1`.

Contact slot live `0x00741650..0x007417FC` skips its query in phase `3`.
Otherwise query result bit `1` routes to `0x007307A0`. Bits `2/3` stop speed
and velocity and signal the handle. Bit `3` immediately performs the phase-3
transition; bit `2` instead sets phase `2`, clears byte `+0x207`, and calls
`0x00740D70`. This is a private phase change, not a common state-6 write.

## Kibakufuda contact, countdown, and nine-row emission schedule

`ccProjectileKibakufuda` motion live `0x00741FF0..0x0074293C` uses private
phase byte `+0x2A0`. Initial motion clears velocity and speed, sets acceleration
increment `+0x2B0 = 0.5f`, and sets angular rate `+0x2A8` to `+10` or `-10`
according to opposite-tag fighter float `+0x48`.

Phase `0` adds the quantized rate times `+0x278 * pi/32768` to angle `+0x2A4`
and wraps around pi. It increases speed by `+0x2B0` without a step multiplier,
caps it at `10`, writes vertical velocity `-speed`, and horizontal velocity
`20 * sin(angle)`. Accumulator `+0x1FC > 300.0f` writes common state `6`
and countdown `+0x82 = 10` at `0x00742860..0x0074286C`.

Contact slot live `0x00742BA0..0x00742E7C` uses two resident segment queries.
The first uses mask `0x20000001`, adjusts the returned vertical coordinate by
`5`, and sets attachment byte `+0x2A1 = 1`. The second uses mask `0x40000002`,
stops x velocity on a hit, and, when result flags include `0x200`, sets angle
`+0xE8` to either sign of pi/2 and attachment byte `2`. Either admitted
attachment, while private phase is not `2`, clears speed/acceleration/velocity,
clears common counter `+0x200`, sets float countdown `+0x2B4 = 29.0f`, and
sets phase `1`. Without that admission it does not advance the phase.

When resident predicate `0x003737A0` returns zero, phase `1` subtracts
`+0x278` from `+0x2B4` and exposes its integer conversion in `+0x1F8`.
A negative result, or positive registration count `+0x318` tested by helper
`0x00743110`, sets phase `2`, clears `+0x82`, and writes `+0x1F8 = -1`.
Phase `0` can also enter phase `2` through that registration-count predicate.

Phase `2` disables collision byte `+0x206`. Except for config `0xA0`'s separate
child-emission route, it scans exactly nine rows at live `0x008A2290`, stride
`0x30`, when resident predicate `0x003737A0` is zero. A row runs only when
its word `+0x00` equals signed counter `+0x82`. The row's xyz vector at
`+0x10` is added to the current position, and word `+0x24` is the child config;
byte `+0x20` can write common state `6`. The complete bounded schedule is:

| Row | Counter | Position offset x/z | Child config | State-6 byte |
| ---: | ---: | --- | ---: | ---: |
| 0 | 0 | `0 / +50` | `0x29` | 0 |
| 1 | 0 | `+50 / -120` | `0x2A` | 0 |
| 2 | 0 | `-50 / -120` | `0x2A` | 0 |
| 3 | 0 | `+100 / -120` | `0x2A` | 0 |
| 4 | 0 | `-100 / -120` | `0x2A` | 0 |
| 5 | 4 | `+250 / +50` | `0x28` | 0 |
| 6 | 8 | `+500 / +50` | `0x28` | 0 |
| 7 | 4 | `-250 / +50` | `0x28` | 0 |
| 8 | 8 | `-500 / +50` | `0x28` | 1 |

Every row's y offset is zero. Matching rows all run on the same invocation;
this includes the five counter-zero emissions. Phase `2` increments `+0x82`
by one even when the resident predicate suppresses the table scan, so skipped
equalities are not retried by this body. Config `0xA0` calls child helper
`0x00742940(self, 2)` and writes state `6`, then follows the same counter
increment. These schedule values are callback counters, not frame durations.

## Chase's local phases

`ccProjectileChase` and `ccProjectileNrwCombo` share motion live
`0x0073B060..0x0073BD14` and activation `0x0073C220..0x0073C6C4`.
Here common halfword `+0x82` also selects the local movement phase; it must
not be treated as a universal countdown. Activation selects `3` for config
`0x51`, otherwise `2`, and initializes float clock `+0x2B0 = -1`. Unless
record float `+0x48` is `-1`, it supplies turn amount `+0x2B8`; byte
`+0x1F0 == 0` clears that amount. Unset float `+0x2D0` becomes `8`.

The motion body uses the same-tag fighter's position, with the observed
height exception, unless byte `+0x25F == 1` or sticky flag `+0x2C2` bit `0`
selects stored point `+0xA0`. That flag becomes sticky when stored byte
`+0x202` differs from the fighter's signed halfword `+0x9F6`. The body
increments `+0x2B0` by `+0x278` only on paths reaching its final tail.

- Phase `2` waits for `+0x1FC >= +0x2D0`, then selects phase `3`, resets
  `+0x2B0 = -1`, and initializes normalized target-minus-position velocity
  scaled by speed. Byte `+0x2CE` chooses the resolved point or stored `+0xA0`.
- Phase `3` admits steering only with byte `+0x2CC != 0` and
  `+0x2B0 < +0x2C8`. It uses float `+0x2B8` directly as the angle limit,
  without multiplying it by the step in this body. Configs `0x56/0x57`
  additionally have fighter-state/direction branches that choose an x point
  `5000` units away instead of the normal steering route.
- Phase `1` can clear velocity and auxiliary vector on `+0x2C2` bit `1`.
  When predicate `0x0072F460(self, 0)` returns `2`, it can directly move
  position by a normalized `20`-unit step toward the fighter if distance
  exceeds `50`. Its early return branches signal the handle and do not reach
  the local clock increment.

Contact live `0x0073AB70..0x0073AFD0` skips its query in phase `1`.
Query result bit `1`, or bits `2/3`, cause config-specific completion for
`0x51/0x57`; `0x51` clears velocity, speed, and collision and writes state
`6`, countdown `10`, while `0x57` writes state `6`, countdown `0`.
For other configs those routes call `0x007307A0` or `0x00732C80` instead.
Config `0x57` also terminates on bits `4/5`, with the observed signed
`100`-unit x adjustment to the candidate. Its angle/transform callbacks are
described in [callback composition](#representative-callback-composition).

## Clay motion clocks and guide sampling

The class-local multiplier in the Clay callbacks below is distinct from both
`q` and the manager scalar used by the later common candidate step.

| Class / live motion body | Local clock and multiplier | Motion and completion |
| --- | --- | --- |
| `ccProjClayBrdN`, `0x00752280..0x00752C48` | `dt = +0x2C4*q`; guide clock `+0x294` | Phase `100` advances the guide clock by `dt`, samples owned guide `+0x290`, and steers toward sampled position `+0x2A0`. At clock `>= guide.+0x0C - 1`, calls `0x00731330(self, 0)`. Phase `200/300`, if byte `+0x273` is zero, calls `0x00731600/0x00731670`, emitting child config `0x66/0x67` before their state-6 work. |
| `ccProjClayBrdS`, `0x007536E0..0x00753A68` | `dt = +0x2C4*q`; clock `+0x294 += dt` | Uses the same guide sampling and angular steering pattern. Completes through `0x00731330(self, 0)` at `clock >= guide.+0x0C - 1 - +0x298`. |
| `ccProjClayBrdU`, `0x007546A0..0x00754968` | `dt = +0x2B0*q`; clock `+0x290 += dt` | Continually steers toward normalized `+0xA0 - +0x90`, with angle limit `+0x298*dt`. Scales the chosen direction by speed and then by `+0x2B0`. At clock `>= +0x294`, calls `0x00731330(self, 0)`. |
| `ccProjClaySpd`, `0x00755A40..0x00755DF4` | `dt = +0x324*q`; clock `+0x294` advances only with byte `+0x290 != 0` | Private vertical speed `+0x310 -= g*q`, with `g` from float bits `0x3FFAE148`; writes x velocity `+0x318*speed`, z velocity `+0x310`, then scales the vector by `+0x324`. Contact controls recovery, described below. Clock `>= +0x298` enters a state-6 helper. |
| `ccProjClaySpd2`, `0x00755FD0..0x00756428` | Same `dt`, conditional clock, gravity, and vector scaling | On admitted contact in phase `0`, same/opposite fighters must have equal `+0x9F6`, `abs(dx) < +0x330`, and `abs(dz) < 100` to set phase `1`, choose horizontal direction toward the fighter, and restore speed from `+0x314`. Phase `1` contact clears vertical speed. The same deadline completes it. |

Bird N/S call guide setter `0x00752D00(guide, clock)`, which clamps guide
float `+0x08` to `0..guide.+0x0C`, then sampler `0x00768200` returns a
position, angles, and a further vector of parameters. Their steering limit is
the latter vector's x float times `dt`. Raw Bird N instructions
`0x00752A20..0x00752AE8` and corresponding S instructions derive speed as
`(length(new sampled position - old sampled position) + parameter-vector.y)
/ dt`, copy direction to `+0xF0`, then scale velocity by that speed and the
class multiplier. Thus speed is not simply guide-point distance divided by
time: the sampled y parameter is an additional input. The selected guide
producers and their binding ownership are established in
[guide construction and binding](#guide-construction-and-binding). A complete
curve-interpolation audit is outside this projectile-facing contract.

Bird N private phase halfword `+0x268` selects its route. Phase `0` adds `q`
to clock `+0x294` and derives an oscillating velocity around spawn `+0x90`;
clock `> 90` selects its completion route. Phases `10/20/40` install guides
from live `0x008C4DC0/0x008C5180/0x008C55C0`, with channel strides of
`8/9/9` key records, clear the clock, and select `100`; phases `20/40`
multiply `+0x2C4` by `1.1`.
Phase `30` selects `300` directly and, when byte `+0x273` is zero, calls
child/completion helper `0x00731670` on that same invocation.
The guide pointers are route data, not newly emitted projectile configs.

Activation inputs are class-specific; `r` below is resident `0x00180260`'s
`float(int32(random word)) / 4294967296.0f`, whose shared contract is in
[randomness](../runtime/randomness.md#mt-wrappers).

| Setup / live entry | Direct record or supplied-block inputs |
| --- | --- |
| Bird N, `0x00752150` | Signed record word `+0x40 / 100` supplies `+0x2C4`. The record-tail/helper consumers remain in [tail-field consumers](projectiles.md#tail-field-consumers-and-mutable-records). |
| Bird S, `0x007530B0` | Without supplied block `+0x2C0`, cutoff adjustment `+0x298 = 5*(r+1)` and multiplier `+0x2C4 = 1`. With that block: signed words `+0x00/+0x04` give adjustment `word0 + word4*(r+1)/2`, and signed word `+0x08 / 100` supplies the multiplier. |
| Bird U, `0x00754520` | Record signed words `+0x38/+0x3C` give deadline `+0x294 = word38 + word3C*(r+1)/2`; word `+0x40 / 100` supplies `+0x2B0`, and float `+0x48` supplies turn scalar `+0x298`. A supplied block `+0x2AC` uses the corresponding words `+0/+4/+8` and float `+0x10`. |
| Clay Spd, `0x00755870` | Record words `+0x38/+0x3C` produce the same deadline form in `+0x298`; word `+0x44` produces recovery threshold `+0x29C = word44*(r+1)/2`; word `+0x40 / 100` supplies `+0x324`. Float `+0x1C` and a signed draw with range float `+0x48` produce stored speed `+0x314`. Byte `+0x26A != 0` instead sets deadline `9999`, recovery threshold zero, and stored speed zero. |
| Clay Spd2, `0x00755E70` | Multiplies existing deadline `+0x298` by signed record word `+0x38`; word `+0x40 / 100` supplies `+0x324`. Word `+0x3C` gives proximity `+0x330 = word3C*0.6 + word3C*(r+1)*k`, with `k` from float bits `0x3E4CCCCC`. Speed uses the same `+0x1C/+0x48` inputs. |

Clay Spd contact helper `0x00738560` returns a word of flags. On flag
`0x20000000`, byte `+0x26A` chooses whether to zero the deadline or to
start its clock and clear vertical speed. If clock exceeds recovery threshold
`+0x29C`, it increments word `+0x31C` and restores stored speed; otherwise
resident `0x00180CE0` approaches speed toward zero. Without that flag it also
approaches zero, with rate `0.1*q` unless byte `+0x26A` selects zero rate.
Flag `0x40000000` sets the clock to its deadline. On expiry, byte `+0x26A`
can select between helpers `0x00731330/0x00731420` using a bounded draw;
both clear motion and write state `6`, countdown `10` on the cited calls.
Clay Spd2's phase-0 slowing uses `0.2*q` before its proximity check; this
differs from Spd's ordinary `0.1*q` route.

## Guide construction and binding

The shared guide is a `0x20`-byte object, not a retained fighter pointer.
Constructor live `0x00767A00` calls reset `0x00767B40`, which clears flags
`+0x00`, channel count `+0x02`, channel-array pointer `+0x04`, sample cursor
`+0x08`, endpoint `+0x0C`, and the 16-byte position bias at `+0x10`.
Channel builder `0x00767B60` uses only input mask bits `0..2` to choose
channels, so at most three channel descriptors are created. It allocates and
clears `count * 0x14` bytes; each descriptor's halfword `+0x00` combines its
individual channel bit with the supplied interpolation bits `0x78`. The
Bird callers supply mask `0x27`, producing descriptor flags `0x21`, `0x22`,
and `0x24`. Sampler `0x00768200` routes their values to the parameter,
position, and angle outputs, respectively. This limit belongs to guide
channels, not the number of active projectiles.

Live `0x00767CC0` binds an authored block without copying its keys. It writes
each channel's key pointer from the supplied address, advances that address
by `supplied stride * 0x28` for the next channel, counts `0x28`-byte keys
until a word with bit `0x80000000` is reached, and sets guide endpoint
`+0x0C` to the maximum final non-sentinel key time. Before rebinding, it frees
old key arrays only if guide flag bit `0` says they were allocated; it then
clears that flag. The guide owns its descriptor array while these authored
key pointers remain borrowed. No deep copy or reference count is added by
this binder. A channel with no non-sentinel key is not given a safe empty
endpoint path: its final-time load addresses one key before the supplied
pointer. The selected authored routes must therefore supply keys before
their sentinel.

The separate producer pair `0x00767EE0` and `0x00768010` creates writable
copies. The first sets guide flag bit `0`, allocates `(requested count + 1)
* 0x28` bytes for each selected channel (`a1 = -1` selects all channels),
and clears the allocations. The second copies all ten words of every
non-sentinel key into those arrays, writes sentinel word `0x80000000` and
nine zero words after the copied keys, recomputes counts, and extends the
endpoint from the source's last key time. Its source advances by the supplied
channel stride. Neither this copier nor the borrowed binder bounds the
sentinel scan by that stride; the stride is the next-channel displacement,
not an independently enforced admission length. The copier does not check
its destination allocation length before writing each copied key.

Bird N activation live `0x00752150..0x00752238` allocates the guide at
projectile `+0x290`, builds mask `0x27`, and borrows block `0x008C4DC0`
with stride `8`. It mirrors x via guide flag `2` on the spawn/aim direction
branch and copies the spawn position into guide bias `+0x10`. The route
changes already listed above bind their replacement blocks through the same
borrowed interface. Bird S activation creates its guide at the same instance
offset but allocates and copies all three channels: selection word `+0x29C`
chooses one of blocks `0x008A3580`, `0x008A38D0`, `0x008A3C20`,
`0x008A3F70`, and `0x008A42C0`, each with stride/count `7`. Its following
setup edits those copied position keys. Thus calling both N and S guides
"owned" describes the guide allocation but conceals a meaningful difference
in ownership of their keys.

Ink Bird's non-`40/41/42` activation creates guide `+0x294` and initially
borrows `0x008C5A00` with stride `8`. Routes `10/11`, `20..24`, and
`30..33` then replace that binding with allocated copies through the same
producer pair, using stride/count `8`; default routes retain the borrowed
block. Their copied blocks run from `0x008C5A00` through `0x008C7F80`
in `0x3C0`-byte increments. Routes `40/41/42` take the stored-target phase
`100` path before guide allocation, so phase `100` does not imply guide
sampling. These branches are raw instructions at live
`0x00761FCC..0x00762430`.

The selected source blocks corroborate the stride/count distinction:

| Authored block, live | Channel stride | Non-sentinel key counts: parameter / position / angles | Final times | Initial guide endpoint |
| ---: | ---: | --- | --- | ---: |
| `0x008C4DC0`, Bird N | 8 | `2 / 7 / 6` | `56 / 56 / 56` | 56 |
| `0x008A3580`, Bird S selection 0 | 7 | `2 / 6 / 4` | `51 / 51 / 51` | 51 |
| `0x008C5A00`, Ink Bird | 8 | `2 / 6 / 2` | `25 / 25 / 25` | 25 |

All three inspected channels in each block contain sentinel `0x80000000`
inside their stride. The six tail floats at key `+0x10..+0x24` are zero in
these selected non-sentinel keys. The producer copies those bytes, but the
selected linear flags `0x20` do not use them as tangent inputs. Other flags
and other blocks are not covered by that negative result.

Bird S's supplied-block lifetime is proven through its launcher. The emission
continuation at live `0x00753F00..0x00753F10` passes `parent record +0x38`
to child setter `0x00753FE0`, which stores the pointer verbatim at child
`+0x2C0`. Activation reads it later; neither setter nor constructor copies the
block or owns a separate allocation for it. In this chain the pointer stays
inside the shared global record, so the parent projectile can retire without
freeing that storage. The launcher copies no parent-object address into this
field. This proves these selected parent-record meanings:

| Parent record field | Child setup use through supplied block |
| ---: | --- |
| `+0x38` / block `+0x00` | Base cutoff adjustment. |
| `+0x3C` / block `+0x04` | Random cutoff-adjustment range in the already documented formula. |
| `+0x40` / block `+0x08` | Percentage multiplier divided by 100. |
| `+0x48` / block `+0x10` | Range passed to signed random service `0x001802B0` when selecting the copied guide's initial segment speed. |

For the last field, setup `0x00753394..0x007533F0` measures the first
position-key segment's xyz distance and divides by its authored time
difference, then multiplies by `1 + signed_draw(block.+0x10)`. Without a
supplied block the range is `0.1f`. It stores that result as speed `+0x1E0`.
The later copy-adaptation loop can add signed draws ranged by `10` to key x
and `20` to key z when selection `+0x29C < 3`, clamps key z so spawn z plus
that key is at least `20`, and replaces each later position-key time with
the prior time plus its x/z segment distance divided by the selected speed.
It then publishes the final retimed endpoint and aligns the other copied
channels' last key times to it. This is guide-data production before sampling,
not a retained target or a universal record-`+0x48` turn meaning.

Guide deleting helper `0x00767A30` frees channel key arrays only with guide
flag bit `0` set, always frees a non-null channel-descriptor array, and frees
the guide itself only for a positive deleting argument. This proves the
borrowed/copied distinction at destruction as well as binding. Bird N/S
deleting destructors `0x007520B0/0x00753010` call that helper with argument
`1` for non-null `+0x290`, clear the field, and continue into root destruction.
Ink Bird cleanup `0x00761C60`, reached from its deleting destructor
`0x007636B0`, similarly deletes non-null guide `+0x294`, then separately
releases owned reference `+0x290`. Guide lifetime and the Ink auxiliary
reference lifetime therefore have distinct storage and release interfaces.
Every authored key's contents, repeated setup outside these traced paths,
and unrestricted aliases of these interfaces remain separate leads.
The scalar sample cursor and key times establish inputs to the documented
motion bodies; they do not establish visible cadence or numerical rounding.

## Ink motion and completion

| Class / live motion body | Local timing inputs | Motion and completion |
| --- | --- | --- |
| `ccProjInkSnakeN`, `0x00761370..0x0076195C` | `dt = +0x2C4*q`; clock `+0x294 += dt`; bias countdown `+0x2C0 -= dt` | Speed is `35` through clock `5`, then `13`. In phase `20`, clock `5..20` can adjust stored aim toward the selected fighter. Expired bias countdown regenerates vector `+0x2B0` and flips flag `+0x2C8` bit `1`. Query flag `0x40000000`, or clock `>= signed halfword +0x298`, ends owned reference `+0x290` with `0x00721FB0` and calls `0x00731820(self, 0, 0)`. |
| `ccProjInkBrdN`, `0x00762640..0x00762A68` | `dt = +0x2E8*q`; clock `+0x29C += dt` | Phase `100` steers toward stored target `+0x2B0`; other guide-bearing routes sample owned guide `+0x294`. At clock `>= signed halfword +0x2A0`, uses the same reference-end/state-6 pair. |
| `ccProjInkMouseN`, `0x00763160..0x00763438` | `dt = +0x320*q`; clock `+0x294 += dt` | Vertical scalar `+0x1E4 -= 8*dt`, clamped to `-20`. Builds x/z velocity from signed direction `+0x318`, speed, and that scalar, then scales it by `dt`. At clock `>= signed halfword +0x298`, calls `0x00731820(self, 0, 0)`. |

Snake helper live `0x007619D0..0x00761B44` decreases vertical scalar
`+0x1E4` by `4*dt`, clamps it at `-40`, and advances anchor `+0x2A0`
by normalized `+0xA0 - +0x90` times `speed*dt`, with that vertical scalar
added to z. It steers current velocity toward `anchor + bias +0x2B0`
with angle limit `0.2*dt`, writes direction `+0xF0`, and scales velocity by
`speed*dt`. Its query using mask `0x60000001` also uses flag
`0x20000000` to set anchor z to returned z plus `20`; the other flag ends
the object as shown above. These are two different query responses.

Ink Bird helper `0x00762A70..0x00762B84` uses angle limit `0.15*dt`
and velocity magnitude `speed*dt` for phase `100`. Setup `0x00761DA0`
initializes multiplier `+0x2E8 = 1`; its routes `40/41/42` select phase
`100`, speed `40`, deadline `30`, stored target, and a retarget window
`3..10` in floats `+0x2E0/+0x2E4`. Flag `+0x2EC` bit `1` admits
retargeting during that window; the selected fighter comes from halfword
`+0x2A2`, and predicate `0x0072AF50` can clear the flag. The guide route
has the same sampled-parameter speed addition as Clay Bird N/S, scales its
turn by `dt`, and scales the final velocity by `+0x2E8`. Helper
`0x00761960` stores `dt` into owned reference `+0x0C`; it is not a local
elapsed-time increment.

Mouse setup `0x00762F90` reads signed record words `+0x38/+0x3C` for
its deadline, combining `+0x38` with the magnitude of a signed random draw
ranged by `+0x3C`, then converting to halfword `+0x298`. Word
`+0x40 / 100` supplies `+0x320`; float `+0x1C` and a signed draw
ranged by float `+0x48` supply stored speed `+0x314`. Query flag
`0x20000000` clears the vertical scalar and restores that speed; without
it, speed approaches zero with rate `0.1*q`. Flag `0x40000000` assigns
the deadline to the clock, causing the same-call expiry check to admit
completion. No other class's record field interpretation is implied.

Clay Bird N/S and Ink Snake/Bird additionally set their optional helper's
halfword `+0x94` to the low half of `int(256*q)`. They do not add that
quantity to an existing helper counter at those stores. Their object clocks,
helper input, root accumulator, and position step therefore remain separate
observed quantities.

## Other flight phases

The following contracts cover the other distinct flight bodies reached from
the factory classes' common motion interface. All addresses in these motion
tables are live addresses; `q` continues to mean instance float `+0x278`.
Local phase values are identified by their actual storage, not equated with
common state `+0x7E`.

| Class / live body | Verified movement, phase, and timing inputs |
| --- | --- |
| `ccProjectileTenten1`, `0x0073CD40..0x0073CF74` | Common `+0x82 == 0` initializes via `0x0073CA70`: quantized angle `30/150` according to opposite-tag direction, launch direction `+0x2B0`, vertical accumulator `+0x2C4 = -20`, increment `+0x1E4 = 4`, phase `1`, word `+0x2C0 = 0`. Phases `1/2` add `5` to speed, cap at `45`, and scale `+0x2B0` into velocity. Every call adds `+0x1E4` to `+0x2C4`, writes it into auxiliary z `+0x1D8`, normalizes velocity-plus-auxiliary into `+0xF0`, and increments word `+0x2C0`. Phase `2` writes state `6` once the old word is at least `6`. These increments are unscaled. |
| `ccProjectileMakibishi`, `0x0073E0A0..0x0073E31C` | First call uses the 42-vector draw scaled by `7.5`, clears its y, and sets velocity to unnormalized `aim - position + +0xB0`; speed starts at zero and decrement `+0x29C = 6`. While private byte `+0x290 == 0`, speed decreases by that amount, floors at `-5`, and the resulting z value is added to existing velocity each call. It normalizes velocity into `+0xF0`. Common counter `+0x200 > 300` signals the handle and writes state `6`, countdown `10`. |
| `ccProjBoomerang`, `0x0074B780..0x0074BC8C` | Setup `0x0074B740` numerically converts record word `+0x38` to speed, takes low halves of `+0x3C/+0x40` into `+0x290/+0x292`, and float `+0x48` into turn scalar `+0x294`. The motion body uses angle limit `+0x298 = +0x294*q`. Before clock `+0x29C` reaches `30` it resolves the same-tag fighter with the observed height exception; thereafter it resolves the opposite-tag fighter. It adds bias `+0xB0`, normalizes and angle-limits the direction, and scales by speed. Manager x-bound failure clears turn scalar. Clock increases by `q`; `> 120` writes state `6`, countdown `1`. |
| `ccProjSandPellet`, `0x0074CC80..0x0074D458` | Private byte `+0x290` selects phases `0/1/2`. Phase `0` subtracts `speed*q` from distance `+0x2D0`; a negative value stops speed and selects `1`, with halfword `+0x292 = bounded_draw(5)+1`. Phase `1` steers toward a fighter position or stored snapshot using angle `0.2`, then decrements the halfword by one; new value below zero selects `2`. Phase `2` adds `6*q` to speed, caps at `60`, and scales direction into velocity. Phases `0/2` subtract `speed*q` from remaining distance `+0x2D4`; negative distance clears collision, speed and velocity, writes state `6`, countdown `10`, and signals the handle. |
| `ccProjIronRain`, `0x00750E40..0x00751354` | Private byte `+0x290` selects four phases. Phase `0` post-decrements signed halfword `+0x292`; old value `<= 0` sets phase `1`, zero speed, and a new bounded draw with argument `2`. Phase `1` increases scale `+0x1E8` by `0.15` per call, caps at `+0x2F0`, and selects `2`. Phase `2` decrements the halfword; new negative value selects `3`, signals the handle, resolves direction, and measures collision distance along a `5000`-unit ray, using `5000` for sentinel `-1`. Phase `3` adds `24` to speed, capped at `240`, without a `q` factor. Phases `0/3` subtract `speed*q` from distance `+0x2D4`; only phase `0` directly calls completion helper `0x00731130` when it becomes negative. Every phase writes velocity `speed*direction`. |
| `ccProjCHYSkillKunai`, `0x007582A0..0x007589E8` | Private halfword `+0x268` selects four routes. Phase `0` approaches a fighter-relative anchor, subtracting a speed clamped to `2..20` times `q` from distance `+0x2D0`. Completion selects phase `1` when byte `+0x26A` is set, otherwise `2`, and initializes sinusoidal inputs. Phase `1` directly positions the object around the same-tag fighter with stored offsets and z oscillation; angular input increments without `q`. Fighter distance `<= 550` admits phase `2` and a bounded delay with argument `15`. Phase `2` decrements delay `+0x2E0` by one, floors at `-1`, and at zero initializes normalized launch velocity with speed `65` and enables collision. Phase `3` applies an unscaled `3.5` gravity decrement and direct z positioning; query bits `2/3/4` enter common state `4` and use returned z plus `10`, while bit `1` calls `0x007307A0`. |
| `ccProjExcORWSnake`, `0x0075BC90..0x0075C108` | Private halfword `+0x268 == 0` directly advances position using speed `+0x2A0` and vertical scalar `+0x2AC`, then adds `+0x2B0` to the latter. Segment hit from `0x0075C640` places z at hit plus `2`, selects phase `1`, clears vertical scalar, and sets flag `+0x2B8` bit `0`. Phase `1` adds `+0x2A4` to speed up to `+0x2A8`, and adds `+0x2B0` to vertical scalar up to `+0x2B4` unless that flag suppresses it; its horizontal displacement uses `q`. Accumulator `+0x1FC >= 200`, or a hit through query mask `0x40000001`, selects phase `2` and calls `0x00730600(self, 0)`. |
| `ccProjNWVGen`, `0x007600E0..0x0076020C` | Floors speed at zero and writes velocity `speed*+0xF0`. Phase halfword `+0x268 == 0` calls position-associated helper `0x0072B060` while counter `+0x294 < 15`; speed `<= 35` selects phase `1` through `0x007600D0`, which resets the counter. Phase `1` writes scale `+0x1EC = lerp(counter/5, 1, 0)`; a nonpositive result writes state `6` and signals the handle. Counter increments by one per call. |

Makibishi contact `0x0073E320..0x0073E470` runs only while its private byte
is zero. Query bit `1` calls `0x007307A0`; bits `2/3/4` clear speed,
decrement and velocity, place the candidate at the returned point plus `10`
in z, and set byte `+0x290 = 1`. Bit `5` has the separate horizontal-stop
path. This explains why the continuing motion body stops accumulating gravity
after the first admitted contact, without assigning a collision shape.

SandPellet setup live `0x0074CA80` snapshots the opposite-tag fighter into
`+0x2C0`, stores its direction scalar in `+0x2B0`, and initializes negative
distance `+0x2D0` from Euclidean aim-to-position distance. The motion body
can choose the same-tag fighter instead while steering. The stored snapshot
and the later resolved fighter are separate inputs.

## Bound and character-carrier motion

`ccProjBakutiBall` motion live `0x00746770..0x0074694C` snapshots current
position into `+0x320`. Its first-call setup enables collision, clears
`+0x88/+0x87`, and initializes its private state and resources, then falls
through to extended slot `+0x5C`, followed by `+0x64`, on that same call.
Its signed halfword `+0x290` increments by one after those callbacks.

The `+0x5C` target live `0x00746950..0x00746CC8` applies unscaled gravity
`velocity.z -= +0x294`, floored at `-+0x2A0`, and passes the moving point
and velocity to contact helper `0x00738560`. Its flag responses are exact:

- `0x20000000`: z velocity below `-10` becomes `-vz * +0x29C`, otherwise
  zero; x velocity is multiplied by `+0x298`. Additional small-speed and
  height comparisons can settle horizontal motion.
- `0x40000000`: x velocity becomes `-vx * +0x29C`.
- `0x80000000`: a positive z velocity is negated.

It stores the returned flags in `+0x310` and calls extended slot `+0x60`.
That target, live `0x00746CD0..0x00746D60`, updates angle `+0xE4` from
the x difference against snapshot `+0x320` and scalar `+0x2D8`, then wraps
around pi. These contact responses precede the emission decision.

Extended `+0x64`, live `0x007473D0..0x0074765C`, admits its six-way
choice at accumulator `+0x1FC >= 60`, contact flag `0x20000000`, and
resident predicate `0x003737A0 == 0`. It copies six bytes from resident
live `0x00604DF0`, draws inclusively from `0..100`, and chooses the first byte
whose unsigned cumulative sum is **at least** the draw. Retail bytes are
`18, 18, 10, 18, 18, 18`; the exact inclusive comparison is retained rather
than interpreting these as six exact percentage probabilities. The complete
jump table is live `0x008C4DA0`, with these outcomes:

| Index | Live target / called helper | Bounded emitted result |
| ---: | --- | --- |
| 0 | `0x00747538` → `0x00747660(self, 4)` | One config `0x29` and four config `0x28`, with the helper's alternating x offsets and delays. |
| 1 | `0x00747550` → `0x00747BB0(self, 2)` | One config `0x1E` plus two further config `0x1E`. |
| 2 | `0x00747568` → `0x00747DD0(self)` | Resident allocations/services; no call to projectile spawn in the complete helper. |
| 3 | `0x0074757C` → `0x00747660(self, 0)` | One config `0x29`. |
| 4 | `0x00747594` → `0x00747BB0(self, 0)` | One config `0x1E`. |
| 5 | `0x007475AC` → `0x00747960(self, 2)` | Three config `0x28`, with delays `0/2/4`. |

After an admitted choice it writes common state `6`, countdown `0`.
The same callback also has an independent accumulator `> 180` completion
and an earlier flag-tuple route to `0x007307A0`. The weighted decision is
therefore not its only completion route.

The five factory classes using character-carrier motion live
`0x0074D8B0..0x0074D970` are `ccProjTest`, `ccProjCharNRW`,
`ccProjCharNRWOtherSelf`, `ccProjCharSZWBuddyTonTon`, and
`ccProjSZWExcItemTonton`. First activation clears `+0x87/+0x88`, enables
collision, signals the handle, and selects word `+0x2CC = 2/3` according
to the spawn/aim x comparison. With collision byte enabled it calls extended
`+0x60` before `+0x5C`, then resolves binding `+0x2D4` through
`0x0074F0A0`. This differs from BakutiBall's callback order.

Their shared `+0x5C` body, live `0x0074DF50..0x0074E460`, combines
horizontal scalar `+0x450`, vertical scalar `+0x454`, direction `+0x2CC`,
and mode `+0x2B0` into velocity, with `q` multipliers. It moves the object's
position through one or two stored contact contexts `+0x350/+0x3B0`,
stores the union of flags in `+0x2D0`, clears vertical scalar on flag
`0x20000000`, and ends its horizontal mode on `0x40000000/0x80000000`.
At the tail it subtracts `+0x458 * +0x2C8 * q * 3` from the vertical
scalar and resets `+0x458 = 1`. The shared `+0x60` entry
`0x0074E5F0` dispatches the class-specific `+0x64` callback, consumes
movement-parameter records through `0x0074EA80`, updates its local command
cursor through `0x0074E680`, and increments word `+0x438` by
`int(256*q)`. Its selected producers, row formats, and admission gates are
established below; the concrete Tonton completion branches remain
in [hit and despawn evidence](projectiles.md#hit-and-despawn-evidence).

## Carrier command publication and retained references

The carrier constructors publish two distinct borrowed tables and allocate an
array of resolved resource pointers at `+0x298`. Each `+0x44C` entry is eight
bytes: a resource-name pointer at `+0x00`, plus a second word later retained at
carrier `+0x440` when that resource is selected. The constructor resolves the
name with live wrapper `0x0074F260`, which calls resident `0x001A8F00` with
the carrier's resource source `+0x290` and final argument zero. That resident
lookup returns an existing record's word `+0x2C`; it neither allocates a
descriptor copy nor increments a reference count in the inspected body.
Missing lookup takes an explicit null-address store in this argument-zero
path. Construction therefore relies on the named records being present.

| Exact carrier | Constructor, live | `+0x44C` resource table | `+0x448` command table | Resolved-pointer array entries |
| --- | ---: | --- | --- | ---: |
| `ccProjTest` | `0x0074F410` | `0x008A2EE0` | `0x008A2F20` | 8 |
| `ccProjCharNRW` | `0x00751A70` | `0x008A3090` | `gp - 0x5BF0` | 2 |
| `ccProjCharNRWOtherSelf` | `0x0075E640` | `0x008A32A0` | `0x008A32C0` | 4 |
| `ccProjCharSZWBuddyTonTon` | `0x0075F080` | `gp - 0x5BE8` | `gp - 0x5BE0` | 1 |
| `ccProjSZWExcItemTonton` | `0x007605E0` | `gp - 0x5BD8` | `gp - 0x5BD0` | 1 |

These counts are the constructor loop/allocation bounds, not a command-row
count. The shared [`ccProjChar` resource cleanup](projectiles.md#ccprojchar) frees
the `+0x298` array itself, then detaches the embedded registration through
`0x0074D820`. It does not individually free those resolved descriptor pointers
or the two borrowed tables in that path. The broader source-container lifetime
and animation-player ownership remain in
[CCS runtime](../game/files/ccs_runtime.md) and
[Animation runtime](../runtime/animation_runtime.md).

That registration has its own lifetime. Live `0x0074F0A0` searches embedded
handle `+0x2D4` for a registration node whose word `+0x24` equals the address
of carrier member `+0x300`, using `0x00729300` and resident ordinal-list
reader `0x001DDD80`. Only a found node admits copying current position into
that member's `+0x20` vector. Cleanup `0x0074D820` searches the same pair,
deactivates a found node with `0x001DCD10`, unlinks/deletes it through
`0x001DDCC0`, and signals the embedded handle. The resident unlink removes
the node from the handle list, repairs its `+0x1C/+0x20` links, decrements
handle count `+0x0C`, and invokes node destructor `0x001DCC20(node, 1)`.
Thus the carrier's binding check concerns a registered embedded member; it
does not resolve the resource ID used by command rows or retain a fighter
pointer. The producer of that selected registration under every carrier route
remains open.

Command publication live `0x0074DA20` accepts `a1` as the class callback
command and `a2` as a command-table index. It rejects publication while carrier
flag `+0x2AC & 1` is nonzero. An admitted publication clears flag `8`, stores
`a1` at `+0x430`, stores `a2` at `+0x434`, resets the fixed-point command
clock `+0x438 = -256`, selects header `+0x43C = +0x448 + 8*a2`, and clears
row index `+0x444`. It retains the selected header; it does not copy its rows.
No table-index bound is enforced by this setter. Test activation calls it with
`(command, index) = (0,0)` at `0x0074F654`; both Tonton activations do the
same at `0x0075F2FC/0x00760908`. Test's command-zero callback can publish
`(1,1)` after contact flag `0x20000000`; the later command-one callback sets
carrier flag `8`, selecting full rows. NRW and both Tonton command-zero
callbacks also set flag `8` on their admitted branches. These are concrete
format publishers, not a guessed interpretation of class names.

Readers live `0x0074DC10/0x0074DC80` use selected header word `+0x04`
as the borrowed row base. With carrier flag `8` set, current row address is
`base + 0x4C*+0x444`, and the first reader exposes that full row to movement.
Without flag `8`, the movement reader returns null and the command reader
uses stride `8`. Neither reader bounds `+0x444` or checks a null row base.
The first eight row bytes have these proven consumers in both formats:

| Row offset | Width | Carrier consumer |
| ---: | --- | --- |
| `+0x00` | `s16` | Index into resolved-pointer array `+0x298`; `-1` suppresses resource selection in the cursor updater. |
| `+0x02` | `s16` | Zero prevents row advancement at the endpoint; nonzero permits one row increment. Value `-16` additionally holds carrier flag `1` until that endpoint. |
| `+0x04` | `s16` | Written into helper `+0x98` on resource selection; also subtracted when deriving a full-row movement-event threshold. |
| `+0x06` | `s16` | Multiplied by `q`, converted with COP1 `cvt.w.s`, and stored in helper halfword `+0x94`. |

No general design name is assigned to `+0x02`: the updater does not count it
down as a duration. For a concrete source example, Test command-zero's first
eight-byte row at live `0x008A2AC0` is `(0,0,0,256)`, followed by row
`(-1,0,0,0)`. Test command-one starts full rows at `0x008A2B10`; its first
prefix is `(1,-16,0,256)`, and its movement block has flags `0x0202` and
disabled event `0x7FFF`. These bytes corroborate the dual format without
claiming all authored commands are reachable or enumerated.

## Carrier movement-event gates and cursor order

The shared slot-`+0x60` body `0x0074E5F0` first calls class `+0x64` with
command `+0x430`, then reads the full movement row through `0x0074DC10`,
calls `0x0074EA80`, updates command/resource state through `0x0074E680`,
and finally increments `+0x438` by `int(256*q)`. A class callback can thus
change the table, row format, or common state before the shared movement and
cursor work. This body has no second state/collision gate after that callback.
Its caller's collision-byte admission is documented above; the record does
not promise that a class callback always keeps collision enabled.

Movement admission `0x0074E960` requires a non-null selected header, full-row
flag `8`, and row event halfword `+0x0A != 0x7FFF`. It computes the following
threshold for every enabled event, not only negative event values:

```text
threshold = max(0, s16(row.+0x0A)
                   + helper.[+0x90]->word(+0x0C) - 1 - s16(row.+0x04))
```

Row flags `+0x08 & 2` choose the resource cursor; otherwise the carrier's
independent fixed-point clock is used. For a nonzero threshold `t`, the exact
crossing checks are:

```text
carrier clock: C - int(256*q) < (t << 8) <= C, C = word(+0x438)
resource cursor: A - (u16(helper.+0x94) - 1) < (t << 8) <= A
                A = (word(helper.+0x98) << 8) | u16(helper.+0x96)
```

Threshold zero takes a different path. Carrier-clock helper `0x0074DDB0`
uses the numeric inequalities directly, while resource helper `0x0074DE10`
returns carrier flag `2`, the transient resource-change flag. It does not
evaluate the resource inequality for zero. The resource helper rejects a
null helper; the carrier-clock helper does not access it. The threshold
producer and command updater themselves dereference helper storage without
such a null guard. Static evidence establishes those invariants, not a
recoverable missing-resource path.

On admission, movement flag group `0xFF00` determines how authored row floats
`+0x0C/+0x10` replace or add to carrier speeds `+0x450/+0x454`: `0x0100`
replaces both, `0x0200` adds to both, `0x0400` adds to horizontal and
replaces vertical, and `0x0800` replaces horizontal and adds to vertical.
Other groups preserve both old values. The updater writes the pair and sets
carrier flag `4` even for that preserve branch. Independently of crossing
admission, a non-null full
row with float `+0x18 != 1` replaces gravity multiplier `+0x458`. The
subsequent `+0x5C` motion consumes that multiplier and resets it to `1`, as
already documented. Row `+0x14` is instead consumed by the following shared
`+0x5C` body as horizontal approach-to-zero rate `row.+0x14 * q` while
carrier flag `4` is set. That body clears flag `4` only on its admitted
low-speed comparison with contact flag `0x20000000` at
`0x0074E040..0x0074E060`; it also zeroes the horizontal scalar on the
low-speed branch. These stores bound the admitted movement event's lifetime
beyond its initial speed publication. The analogous fighter-row publication
and movement ownership belong to
[Combat action execution](combat_action_execution.md#authored-motion-events-and-phase-payload)
and [Movement and physics](movement_and_physics.md); their gates must not be
substituted for these carrier-specific comparisons.

Command updater `0x0074E680` clears transient carrier flag `2` before its
resource decision. It obtains endpoint from helper `+0x90 -> +0x0C` and uses
`endpoint - 2` when descriptor halfword `+0x28 & 2` is set, otherwise
`endpoint - 1`. Carrier flag `4` makes this updater set flag `1` and skip
its row advancement, resource replacement, and step write; shared `+0x5C`
can subsequently clear that movement gate as described above. Its integer
cursor comparison uses `u32(helper.+0xEC) >> 8`, distinct from the crossing
cursor above. On the continuing ungated path, when current resource ID `+0x2A8`
equals row `+0x00`, that cursor has reached the endpoint, and row `+0x02`
is nonzero, it increments row index exactly once and reads the next row.
It contains no loop to consume multiple rows in one invocation.

For a new row resource ID other than `-1` that differs from `+0x2A8`, the
updater sets flag `2`, passes the resolved array pointer to resident
`0x001B99B0(helper, pointer, 0)`, writes the authored start to helper `+0x98`,
stores the new ID at `+0x2A8`, and retains that resource entry's second word
at `+0x440`. It then writes the step halfword described above. This completes
the producer-to-retained-reference-to-cursor chain without calling it a
fighter-owner pointer. Resource-loop behavior and descriptor execution remain
owned by [Animation runtime](../runtime/animation_runtime.md).

The selected constructors' pointer counts do not become checked admission
limits in these consumers: an out-of-range row resource ID is used directly
to index `+0x298` and `+0x44C`. Remaining leads include unrestricted aliases
of command/table publication, all class-local choices of `+0x430/+0x434`,
the remaining full-row payload consumers, and the source-container lifetime
under every external teardown. Numerical conversion rounding and visible
cadence remain unestablished.

## Emitter callbacks and their local schedules

These bodies occupy the same motion interface but perform scheduled child
emission or phase management. That interface placement alone does not imply
that the body continuously integrates the parent's position.

| Class / live body | Trigger and verified emitted/state result |
| --- | --- |
| `ccProjectileKagebunshinLauncher`, `0x007432C0..0x00743620` | Initializes normalized launch velocity. At common counter `+0x200 == 1`, renormalizes it and scales to `10`. Three equality thresholds at live `0x008C4D50` are exactly `2/6/10`; each calls `0x0073E890` with record child config `+0x06`, the selected angle input, and explicit speed/offset inputs. Counter `13` writes state `6`. The equality scan is bounded to three entries. |
| `ccProjFloatLauncher`, `0x007489D0..0x00748E68` | Private byte `+0x290 == 0` waits for `+0x1FC > +0x2A8`; helper `0x00749300(self, 1)` clears `+0x82/+0x1FC`. Phase `1` writes x velocity `+0x298*+0x2A4`, increments `+0x298` by `+0x29C` and caps toward `+0x2A0`, writes z velocity `1.5*sin(+0x294)`, and adds float bits `0x3D00ADFD` to its angle without `q`. At `+0x1FC > +0x2AC` it selects phase `2`. Predicate `0x003737A0 == 0` admits phase-2 emission of signed record byte `+0x08` children using config `+0x06`, plus five children when byte `+0x26A` is set. The child value `+0x258` is parent `+0x258` divided by the original record count, including on the extra-five path. Phase `2` writes state `6`, countdown `1` even when the predicate suppresses emission. |
| `ccProjKunaiBomb`, `0x0074AA50..0x0074B064` | Setup `0x0074A8D0` sets x velocity `-5/+5` from aim direction, z velocity `-1`, gravity scalar `+0x290 = 3`, and enables collision. Private phase halfword `+0x298 == 0` subtracts gravity from z velocity per call, floors at `-100`, and normalizes velocity. Phase `1` adds `q` to clock `+0x294`; clock `> 30` with resident predicate zero emits record `+0x08` children of config `+0x06`, applies bounded child delay with argument `10`, and distributes parent `+0x258` over that count. The completion route writes state `6`, countdown `1`. |
| `ccProjLunFan`, `0x0074C0B0..0x0074C438` | Emits signed halfword count `+0x294` in one invocation. Uses normalized aim-minus-spawn, fan angle from `-0.5*+0x2B0` with increment `+0x2B0/(count-1)`; count `1` selects the unrotated direction. Child config is word `+0x290`; every child gets bounded delay with signed halfword range `+0x296`, parent `+0x258/count`, and speed `+0x298*+0x2A0 + signed_draw(+0x29C*+0x2A4)`. Writes state `6`, countdown `0` after the loop. |
| `ccProjLunLinear`, `0x0074C5E0..0x0074C950` | Same count/config/delay/speed/value inputs and same-call completion as Fan. Uses parallel normalized direction, with positions distributed from `spawn - 0.5*width` along a step `width/count`; count `1` uses spawn itself. Width is `+0x2B0`. |
| `ccProjTripleChase`, `0x0075C770..0x0075CAC0` | Emits signed record count `+0x08` using config `+0x06`. Child float `+0x2D0 = float(record word +0x38) + 3*index`; child `+0x2B8/+0x2C8` receive numerically converted record words `+0x3C/+0x40`, and byte `+0x2CE = 0`. Direction geometry can use fighter byte `+0x63` bit `7`. Writes parent state `6` after the bounded loop. |
| `ccProjLauncherTewAnki`, `0x00759640..0x007596D0` | Private phase `+0x268 == 0` changes to `1` only when common counter `+0x200` equals signed halfword `+0x290`; it does not execute phase `1` on that same call. Phase `1` calls `0x00730950`, emission helper `0x007597F0`, and sets private phase `2`. |
| `ccProjTewSkillAnki`, `0x00759A70..0x00759B18` | Calls Parabola motion first. With signed halfword `+0x290 != 0` and `+0x1FC >= that threshold`, calls `0x0075A0B0`, whose full loop emits 15 config `0x77` children, three aimed through the fighter-service route and twelve using random spatial inputs. It signals the parent handle; neither this call site nor the helper clears the threshold, so this body alone does not establish a one-shot trigger. Angular `+0xE4` also uses `+0xD0*q` and wrapping. |
| `ccProjSNWCmbULauncher`, `0x0075B8B0..0x0075B980` | At `s16(int(+0x1FC)) >= signed halfword +0x2B4`, config other than `0x97` emits config `0x0F`, copies byte `+0x2A2`, signed halfword `+0x2A0`, and 16-byte Homing control block `+0x290` through their exact setters. Then calls `0x007306A0`, also for config `0x97` and failed child spawn. |
| `ccProjDDRExcItemLauncher`, `0x0075CBF0..0x0075CE64` | Uses record count/config `+0x08/+0x06`, bounded speed/amplitude inputs, and child delay `2*index`. Child-local floats are set through `0x0075CE70..0x0075CEB0`. Writes parent state `6` only on the body path with a resolved same-tag fighter; the null-fighter route skips that write. |
| `ccProjDDRBuddyLauncher`, `0x0075D540..0x0075D714` | Uses record count/config `+0x08/+0x06`, indexed vectors at live `0x008A49D8`, direction-dependent rotation, and child `+0x258 = parent.+0x258/count`. Writes parent state `6`. |
| `ccProjTEWExcItemKagura`, `0x0075F5E0..0x0075F80C` | Clears first-call byte, signals handle, disables collision, and emits record count/config `+0x08/+0x06` with interpolated angles; odd child indices get delay `5`. Writes parent state `6`. |
| `ccProjSIWExcItemRakushiki`, `0x0075F810..0x0075FA78` | Same first-call/handle/collision setup and record count/config interface; its loop assigns child parameters through `0x0075FA80..0x0075FAB0` using random inputs. Writes parent state `6`. |
| `ccProjSCHExcItemSenbon`, `0x0075FD30..0x0075FF68` | Emits record count/config children with random xyz offsets. Fighter distance `<= 350` chooses the alternate base x displaced `350` from spawn according to direction. Child delay is integer `index/2`. Writes parent state `6`. |

Kagebunshin's three schedule arrays are live `0x008C4D40` (angle inputs),
`0x008C4D50` (counter equalities), and `0x008C4D60` (wait bases). The wait
range is converted from float `5` at live `0x008C4D70` and supplied to the
inclusive bounded wrapper:

| Common counter | Angle input | Supplied wait input |
| ---: | ---: | --- |
| 2 | 10 | `8 + bounded_draw(5)`, range `8..13` |
| 6 | -10 | `4 + bounded_draw(5)`, range `4..9` |
| 10 | 0 | `bounded_draw(5)`, range `0..5` |

The helper live `0x0073E890..0x0073ECC0` receives fan words
`5, 20, 20, 40` from live `0x008C4D20`: count, angle-spread input,
speed-draw bound, and base speed. Its complete loop makes five spawn attempts
per admitted equality, using the parent's record child config `+0x06`;
successful children get speed `40 + bounded_draw(20)`, range `40..60`.
For child records whose selector byte is `0x14` (`HomingDelay`), it copies
the supplied block from live `0x008C4D30` through setter `0x007437D0`
and stores the converted wait input into child `+0x2A8`. Thus the three
equalities supply 15 child attempts if all are visited; this body does not
catch up a missed equality or guarantee successful allocation.

KunaiBomb contact live `0x0074B070..0x0074B148` first calls root response.
Flag `+0x23C` bit `1` calls `0x007307A0`; bit `2` selects private phase
`1`, clears velocity, and performs its effect/service work. Bit `5` additionally
sets byte `+0x29A` bit `1`. A phase transition is therefore contact-driven,
while the later emission clock is step-scaled.

Lun's record-to-instance fields and retail child remap are established in
[post-spawn initialization](projectiles.md#complete-post-spawn-initialization-inventory).
In the motion bodies, speed sentinel `+0x298 == -1` is replaced from the
chosen child's record float `+0x1C` before emission.

## Direct positioning, attachments, and auxiliary movement

| Class / live body | Verified local movement contract |
| --- | --- |
| `ccProjSCOGen`, `0x0075A890..0x0075A938`; `ccProjINWFlower`, `0x0075BB70..0x0075BC2C` | First-call launch normalizes `aim - current position`, copies direction to `+0xF0`, scales it by speed into `+0x1C0`, clears `+0x87`, and enables collision. Later motion calls do not reconstruct the launch vector. |
| `ccProjDDRGen`, `0x0075AA20..0x0075ABBC` | First call normalizes aim-minus-spawn and sets its oscillation/anchor inputs. Continuing calls directly derive position from anchor `+0x2A0` plus a z sine offset, increase angle `+0x290` by rate `+0x294` without `q`, and wrap it. They write velocity from direction and `speed*q`, then advance the anchor by that vector. |
| `ccProjDDRExcItemBullet`, `0x0075CF80..0x0075D08C` | Similar direct sine-offset position and anchor movement, with amplitude `+0x29C`, angle `+0x294`, and unscaled rate `+0x298`. Accumulator `+0x1FC > float +0x290` calls transition helper `0x00731510(self, 1)`. |
| `ccProjSCVGen`, `0x0075AE10..0x0075AE8C` | Calculates `position + direction*speed`; admitted auxiliary pointer `+0x290` receives that point through `0x00750500`. This body does not directly commit object position or write a common state. |
| `ccProjSCVExcItemFire`, `0x0075D870..0x0075D980` | Same auxiliary-point route with `direction*speed*4`. Common counter `+0x200 % 4 == 0` additionally runs its resident-service event chain. The event counter and spatial multiplier are different inputs. |
| `ccProjSSWGoukakyu`, `0x0075DDF0..0x0075DE40` | Calls Dist2Speed motion, then admitted auxiliary `+0x290` receives the current position. Its launch-time speed contract is inherited from the explicitly called body. |
| `ccProjYMTSkillYari`, `0x0075DB90..0x0075DC5C` | Direct x displacement uses speed signed by scalar `+0x48`; direct z displacement uses float `+0x290`. It normalizes new-minus-old position into `+0xF0`, adds float `+0x294` to the vertical scalar without `q`, and services its handle when that scalar becomes negative. |
| `ccProjSCVSkillPupBullet`, `0x0075E090..0x0075E1A8` | With byte `+0x81 == 0`, subtracts the length of velocity from remaining distance `+0x2A0`. At nonpositive distance it zeroes velocity/speed, restores position from `+0x290`, runs child helper `0x0075E240` with word `+0x2A4`, and calls `0x00730600(self, 0)`. This counter uses vector length, without a local `q` multiplier. |
| `ccProjStickKibakuFuda`, `0x00748120..0x00748368` | Float countdown `+0x290 -= q`. On a continuing countdown, helper `0x00748540` copies the same-tag fighter's position, adds its height-service result, and performs position work. Negative countdown either suppresses emission when resident predicate returns `1` or emits config `0x28` at the fighter position, copying parent `+0x258` and setting child byte `+0x244`; both routes write state `6`, countdown `0`. Fighter `+0x18E == 6` with `+0x190 == 0x61` supplies a separate completion store. |
| `ccProjectileNumbness`, `0x0075B060..0x0075B254` | First call disables collision, clears velocity/speed, and creates two auxiliary references. Continuing calls position admitted references from fighter-resource/bone-service results. Integer `int(+0x1FC) >= 80` writes state `6`; it has no continuing launch-velocity integration of its own. |
| `ccProjDDRBuddy`, `0x0075D420..0x0075D424` | Exact body is `jr ra` with a no-op delay slot. The no-op motion entry says nothing about its separately documented manager-update behavior. |

Direct stores in these callbacks are local facts. A later shared candidate
commit or a derived commitment gate may affect the final object position;
the common call order is retained in
[position commitment](#continuing-state-2-motion-and-position-commitment).

## Stationary and resource-controlled phase timing

`ccProjFixedFire` live `0x0074A220..0x0074A5E8` uses signed halfwords
`+0x290/+0x292` as startup and active countdowns, each decremented by one
on its admitted route. Setup `0x00749F10` copies record word `+0x38`
into the active countdown when its sentinel is `-1`, chooses startup as
`record word +0x3C + bounded_draw(word40-word3C)`, clears velocity, and
sets byte `+0x81 = 0`. Startup completion activates its references; active
completion writes state `6`, countdown `1`, signals the handle and clears its
references. Their follow-position service calls do not introduce a projectile
flight integrator in this body.

`ccProjExplodeS/L`, live `0x00756E00..0x00756F08` and
`0x007571C0..0x007572C8`, likewise have startup halfword `+0x290` and
optional active halfword `+0x292`. Startup decrements by one and at new
value `<= 0` clamps to zero and activates the handle. Once startup is zero,
an active countdown other than `-1` decrements; reaching zero signals the
handle and changes that field to `-1`. Independently, reference predicate
`0x00756F30(+0x298, 0) == 0` calls setters `0x00756F20(self, 6)` and
`0x00756F10(self, 1)` and signals the handle. Thus countdown zero is not
alone the direct state-completion test.

`ccProjDDRFire` live `0x00757470..0x00757588` needs optional helper
`+0x64`. It sets that helper's halfword `+0x94 = low16(int(256*q))`;
reference cursor `0x0074DDA0` returns `helper.+0xEC >> 8`, and endpoint
`0x0074E920` returns the word at `helper.+0x90 + 0x0C`. Once cursor is
at least endpoint minus one, it writes state `6`, countdown `1`, and signals
the handle. This is resource-cursor timing rather than its own float clock.

`ccProjSIWTrap` live `0x00757BB0..0x00757C58` uses phase halfword
`+0x268` and unscaled counter `+0x290`. Phase `0` runs helper
`0x00757E00` when counter is divisible by `30`, snapshots the selected
fighter's state into `+0x292`, and increments the counter by one. Old counter
`>= 250` selects phase `1`; a later phase-1 call enters `0x007580B0`,
which disables collision and signals the handle. Its separately documented
manager update supplies the removal decision.

`ccProjExplode3` live `0x0075D0B0..0x0075D118` waits for float
accumulator `+0x1FC > 8`, then signals the handle and calls the same exact
state/countdown setters with `6/1`. The root motion entry at
`0x0072E020` is another literal no-op; classes inheriting it can still have
their own manager-update schedules in
[update contracts](projectiles.md#complete-factory-class-update-contracts).

## Representative callback composition

Comparing resident vtables against root `ccProjectile` vtable `0x005E0810`
shows that motion/state strategies replace selected callbacks rather than a
single universal "motion" slot. The following are every non-root target in
slots `+0x1C` through `+0x58` for seven representative retail selectors; all
unlisted slots in that range retain the root target:

| Root slot | Root live target |
| ---: | ---: |
| `+0x1C` | `0x0072E020` |
| `+0x20` | `0x0072E240` |
| `+0x24` | `0x0072D200` |
| `+0x28` | `0x00733080` |
| `+0x2C` | `0x00732FD0` |
| `+0x30` | `0x00730140` |
| `+0x34` | `0x007305A0` |
| `+0x38` | `0x00730120` |
| `+0x3C` | `0x00731F80` |
| `+0x40` | `0x00734280` |
| `+0x44` | `0x0072C940` |
| `+0x48` | `0x0072CDA0` |
| `+0x4C` | `0x0072C2A0` |
| `+0x50` | `0x0072B480` |
| `+0x54` | `0x0072B490` |
| `+0x58` | `0x007305F0` |

| Selector / exact class | Non-root slot → live target |
| --- | --- |
| `0x00` / `ccProjectileStraight` | `+0x1C` → `0x00738E40` |
| `0x03` / `ccProjDist2Speed` | `+0x1C` → `0x007392E0`; `+0x30` → `0x00739170`; `+0x54` → `0x00739260`; `+0x58` → `0x00739630` |
| `0x01` / `ccProjectileChase` | `+0x1C` → `0x0073B060`; `+0x20` → `0x0073BD20`; `+0x30` → `0x0073AA30`; `+0x3C` → `0x0073AB70`; `+0x40` → `0x0073C6D0`; `+0x48` → `0x0073C060`; `+0x4C` → `0x0073BF60`; `+0x50` → `0x0073C220` |
| `0x09` / `ccProjectileHoming` | `+0x1C` → `0x0073F6C0`; `+0x30` → `0x0073FCC0`; `+0x50` → `0x0073F610` |
| `0x14` / `ccProjectileHomingDelay` | `+0x1C` → `0x00743A00`; `+0x30` → `0x00743800`; `+0x48` → `0x007438E0`; `+0x54` → `0x00743770` |
| `0x15` / `ccProjectileParabola` | `+0x1C` → `0x00744820`; `+0x3C` → `0x00745390`; `+0x54` → `0x007458D0` |
| `0x0F` / `ccProjectileExplosion` | `+0x44` → `0x00741970` |

The invocation points that are proven globally are narrower than the class
names: spawn calls `+0x54`; the manager calls `+0x44`; the collision pass calls
`+0x48`; root active update calls `+0x20` and `+0x4C`; and common state `2`
dispatch calls `+0x24`. Its continuing branch also reaches motion `+0x1C`,
the admitted contact `+0x3C`, and commitment `+0x38`, as established in
[position commitment](#continuing-state-2-motion-and-position-commitment).
Other slots above retain their exact interface addresses without a universal
semantic label.

The root `+0x20` target at live `0x0072E240` dispatches record `+0x09` values
`0..7` to orientation/transform helpers; its default branch builds matrix
storage at `+0x140..+0x170` from angles at `+0xE0`. This is why calling every
`+0x20` implementation simply a position integrator would be incorrect.
`ccProjectileChase` replaces it with live `0x0073BD20`: in common states `2`
and `5`, that body sets `+0x216 = 1` and updates angle `+0xE8` using signed
halfword `+0x204`, scalar `+0x278`, and explicit pi/32768 quantization. The body
does not directly write position `+0x30`; Chase's own slot-`+0x4C` target at
live `0x0073BF60` consumes `+0xE8` while building matrix storage at `+0x100`
and anchors that transform to position `+0x30`. In contrast, common state `5` is a proven
direct integrator because its handler adds vector `+0x1C0` to position `+0x30`
on each invocation. No invocation is equated to a frame or real-time duration.

`ccProjectileExplosion` demonstrates a real class-specific state contract. Its
live `+0x44` body returns `0` immediately for state `7`; for state `6` it writes
state `7` and returns `1`. Thus an explosion already placed in state `6`
transitions on that callback and is removed on a later manager callback, without
using common state-6 handler `0x0072E180`. When common counter `+0x200` is zero,
the same body also calls its virtual `+0x2C` entry and resident
`SUB_001D87C0(0x1000, object+0x30)`. No cadence or damage meaning is assigned.
