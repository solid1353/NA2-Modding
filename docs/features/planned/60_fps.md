# 60 FPS research

Research into how unmodified *Narutimate Accel 2* (`SLPS-25837`) paces engine
cycles and advances subsystem time. The proposed 60 FPS choices below are
provisional static design research; no change described here is implemented.

This is the single 60 FPS research record. Earlier framerate notes and PNACH
ideas are not evidence for a timing change. The pre-existing instruction-scan
inventories are retained below with their limits; the current pass uses
read-only GhidrAssist decompilation and instruction/byte corroboration.

The failed PNACH attempt and its live recording measurements are recorded in
[the attempt record](../../../experiments/60-fps/attempt.md).

## Research coverage

- **Assigned scope:** a static timing/dependency model for resident ELF,
  `BTL.BIN`, and `ETC.BIN`, distinguishing simulation, presentation, integer
  events, fractional playback, input publication, and reset/lifetime contracts.
- **Exploration depth:** complete pacing/manager, fighter pre/late timing,
  fractional-timer input expressions, countdown and scene advance/seek paths;
  current resident/BTL/ETC opcode inventories; selected presentation and
  generator consumers; integration of the linked subsystem owners' findings.
  This is a completed bounded pass, not every caller's semantic classification.
- **Confirmed coverage:** separate pacing/publication/simulation/presentation
  domains; literal, factor, scene-derived and maximum-rate timers; histories,
  countdown, event lifetime, emitter/UI/camera gates and the design dependencies
  tabulated below. The previous blanket doubling claim is not supported.
- **Unresolved or untested:** indirect timing readers, complete scene-owner
  classification, other subsystem consumers, actual cadence, and the proposed
  design choices remain incomplete or unestablished.
- **Deliberate exclusions and overlap:** `ADV.BIN` is the Adventure overlay and
  is out of scope. The task framework is owned by
  [task_system.md](../../knowledge/runtime/task_system.md) and the battle
  input history by
  [action_commands.md](../../knowledge/gameplay/combat/action_commands.md); this
  document repeats only what frame pacing needs from them.
- **Evidence limitations:** static MCP instructions/bytes establish the scoped
  operations; incomplete xrefs and false import boundaries limit completeness.
  Opcode counts are not caller-semantic counts. Actual invocation frequency,
  distinct presented motion samples and a complete 60 FPS design are unproven.

## Binaries and address conventions

The clean binaries are identified in
[file_identities.md](../../knowledge/game/files/file_identities.md).

| Binary | Address rule |
| --- | --- |
| `SLPS_258.37` | file offset = address - `0x100000` + `0x100` |
| `PRG/BTL.BIN`, `PRG/ETC.BIN` | live address = file offset + `0x6B3F00`; Ghidra address = live address - `0x40` |

Overlay addresses in this document are live addresses unless a Ghidra function
name is given. `jal` targets and pointers stored in an overlay are live
addresses.

## Terms

- **System context:** the resident object whose pointer is stored at
  `0x006073FC` (small-data slot `gp - 0x35F4`, Ghidra `iGpffffca0c`).
- **VBlank count:** context byte `+0x00`.
- **Step:** context byte `+0x01`, the number of VBlanks one engine update
  waits for. Retail gameplay uses 2.
- **Frame ordinal:** context word `+0x194`, incremented once per engine update.
- **Update:** one pass of the engine loop, from the end of one VBlank wait to
  the next.

## Frame pacing

### Observations

| Address | Function | Role |
| ---: | --- | --- |
| `0x00108CE0` | `FUN_00108ce0` | VBlank interrupt handler. Calls `FUN_00108d70(context, 1)`; the normal branch wakes the main thread only when its queried kernel state is 4. |
| `0x00108D70` | `FUN_00108d70` | Adds its argument to the VBlank count: `lbu a2,0(a0)`, `addu`, `sb v1,0(a0)`. |
| `0x001065A0` | `FUN_001065a0` | Display setup. Registers the handler with `FUN_00150578(0x108ce0)`. |
| `0x00107560` | `FUN_00107560` | Step setter: `context[1] = value`, `context[0] = 0`. The ABI receives context in `a0` and value in `a1`. |
| `0x00105DA0` | `FUN_00105da0` | Step getter: `lbu v0,1(a0)`. |
| `0x001083A0` | `FUN_001083a0` | VBlank wait. Loops while VBlank count < step. |
| `0x001C13F0` | `FUN_001c13f0` | Main thread. Its final loop is `FUN_001083a0(context)` then `FUN_001d0560()` forever. |
| `0x001D0560` | `FUN_001d0560` | Wakes the task manager thread. |
| `0x001D0590` | `FUN_001d0590` | Task manager. Calls `FUN_001081b0`, services the tasks, calls `FUN_00108490`, sleeps. |
| `0x001081B0` | `FUN_001081b0` | Start of update. Clears the VBlank count, increments the frame ordinal, performs display/packet bookkeeping, reads the pads through `FUN_00113480`, and conditionally calls the registered callback at context `+0x520`. |
| `0x00108490` | `FUN_00108490` | End of update. Flushes the draw lists. |

The wait in `FUN_001083a0` has two forms chosen by context byte `+0x02`:

- nonzero: call `FUN_0012f3f8` and `FUN_0012f540`, then repeat while
  VBlank count < step (`0x001083D4..0x00108400`);
- zero: spin on the same comparison (`0x00108410..0x0010842C`).

It returns at once when context byte `+0x2AD` is nonzero.

`FUN_00107f80` sets byte `+0x02` to 1 and byte `+0x2AD` to 1 during boot.

### Step writers

The current MCP byte scan for `58 1D 04 0C` reproduces four distinct resident
`jal 0x00107560` sites and zero matches in BTL/ETC. The ELF import exposes
mirrors at `+0x20000000` and `+0x30100000`; they repeat the same sites and
are not additional callers. Direct literal/call scans cannot exclude an
indirect call, an aliased context pointer, or a store outside a tracked
register window. `ADV.BIN` remains excluded.

| Call | Caller | Value | When |
| ---: | --- | --- | --- |
| `0x001080C0` | `FUN_00107f80` | 1 | Boot, while the context is initialised. |
| `0x001E11C4` | `FUN_001e0ee0` (`MOTHER` task) | 2 | After boot loading, immediately before the mode loop. The value is loaded by `li a1,2` at `0x001E11C0` (word `0x24050002`). |
| `0x00105A88` | `FUN_001057b0` (movie start) | 1 | Saves the current step through `FUN_00105da0` at `0x00105A70` first. |
| `0x001054E8` | `FUN_00105320` (movie end) | saved value | Restores the step saved by movie start. |

### Step readers

The prior scans identified these readers. This is a bounded inventory of
recognized accesses, not proof that all readers have been found. Overlay
addresses are live.

| Read | Binary | Function | Use of the step |
| ---: | --- | --- | --- |
| `0x001083E8`, `0x00108414` | ELF | `FUN_001083a0` | The VBlank wait itself. |
| `0x00105A70` (call) | ELF | `FUN_001057b0` | Saved before a movie forces 1. |
| `0x00113C20` (call) | ELF | `FUN_00113b80` | Subtracted from the active rumble duration once per update. |
| `0x0019B518` | ELF | `FUN_0019b4d0` | Multiplies pad-driven rotation and movement speed; added to a hold counter. |
| `0x0019BB80` | ELF | `FUN_0019bb00` | Same, second control scheme. |
| `0x006EF628` | BTL | `ccCommand` history constructor (Ghidra `FUN_006ef5c0`) | Copied to `ccCommand +0x7C`; history capacity = `300 / step`. |

The recovered direct caller of `FUN_0019b4d0` and `FUN_0019bb00` is `FUN_0019b490`
(`0x0019B4BC` and `0x0019B4AC`). Both convert the step to a float and use it as
elapsed time: acceleration terms grow by `step * 0.0625` and `step * 0.05`,
and the hold counter at object `+0x98` grows by `step`.

The current MCP caller trace resolves `FUN_0019b490` to the streamed play
worker `FUN_001a0120`: its argument is `play_context+0x40`. The branch needs
request flags `&0x60 != 0`, `&0x100 == 0`, and container `+0xA4 &1 != 0`.
It is optional playback control, not evidence of a fighter movement clock.
Request reachability and the full worker contract belong to
[scene playback owners](../../knowledge/runtime/scene_playback_owners.md#streamed-worker-scheduling).

The prior scan found no recognized direct reader in `ETC.BIN`; indirect or
aliased access remains outside that negative result.

### Inferences

- The step is a VBlank wait threshold. It is not a universal elapsed-time
  argument: fighter timers and CCS playback accept independent values.
- Active rumble durations subtract the current step on each publication cycle
  (`FUN_00113b80`). Their nominal rate stays constant when both cycle cadence
  and step change proportionately, subject to endpoint rounding and queue order.
- `ccCommand` sizes its ring as `300 / step` only at construction. A nominal
  five-second span at a 60 Hz VBlank rate follows only if its gated input phase
  advances once per paced cycle. Changing step after construction does not
  resize it. Matcher windows still count records; sizing is not general input
  timing compensation. See [action commands](../../knowledge/gameplay/combat/action_commands.md#battle-input-object-and-circular-history).
- A consumer's lack of a direct step read does not establish its rate. It may
  receive a factor, be called on a separate cadence, evaluate an absolute cursor,
  or only submit a draw. Doubling is a conditional prediction for a consumer
  whose calls double while its per-call increment and gates stay unchanged.

### Unresolved

- Which in-scope retail requests enable the optional `FUN_0019b490` branch.
- Readers that receive the context pointer through a saved register or a
  stack slot outside the scan window.

## What one update runs

### Engine services, every mode

`FUN_001081b0` and `FUN_00108490` bracket every update in every mode.

| Address | Function | Work per update |
| ---: | --- | --- |
| `0x00113480` | `FUN_00113480` | Ages both rumble queues (`FUN_00113b80`), then publishes both pads (`FUN_00113710`). |
| `0x00113710` | `FUN_00113710` | Publishes held, pressed, released, and repeat masks. The repeat counter at pad `+0x44` counts unchanged updates up to `0x0F`. |
| context `+0x520` | registered callback | Called when the low three bits of context `+0x192` are clear and the pointer is nonzero. The prior scan recorded a writer at `0x001086A8`; indirect writes are not excluded. |
| `0x0034FEA0` | `FUN_0034fea0` | Emitter pass. Calls `FUN_0034c610` for every live emitter. Reached from `FUN_00108490` directly and through `FUN_00352f60`. |
| `0x0034FFD0` | `FUN_0034ffd0` | Emitter draw pass. |

### Battle dispatcher

`FUN_001ef8f0` runs one battle update. When the inner state machine
`FUN_001ef9c0` returns 0 it calls `FUN_001f0290` (build the two masks),
`FUN_001f03e0` (dispatch), `FUN_001f10f0`, and `FUN_001f0b10`.

`FUN_001f03e0` makes three passes. The first and third use the mask at session
`+0x02`; the second uses the mask at session `+0x04`. The four list owners come
from the array at session `+0x18`, and each pass calls one slot of the owner's
table at owner `+0x0C`.

| Pass | Mask | Owner slot | Child slot | Role |
| --- | --- | ---: | ---: | --- |
| First | `+0x02` | `+0x0C` | `+0x10` | update |
| Second | `+0x04` | `+0x10` | `+0x14` | draw |
| Third | `+0x02` | `+0x14` | `+0x18` | late update |

For `ccPlayerCtrl` the three owner slots are `FUN_002504b0`, `FUN_00250690`,
and `FUN_00250800`. The first runs the fighter logic `FUN_0024fd80` and the
fighters' own update slot; the second sets the camera for drawing and draws
the fighters; the third runs the fighters' late slot.

The subsystems and their mask bits are tabulated in
[pause_and_replay.md](../../knowledge/gameplay/session/pause_and_replay.md#selective-update-gating).
The decompilation of `FUN_001f03e0` read for this research matches that table.

### Inference

The player owner has separate first, drawing, and late callbacks. That does
not prove that every second-phase callee is a pure draw. The complete masks
also have exceptions and operations outside them. Alternating selected mask
bits is therefore not evidence of preserved timing for the whole battle.
Without an additional presentation state, drawing a fighter twice between
simulation changes cannot produce another motion sample.

## Clock primitives

These are established timing mechanisms, not an exhaustive taxonomy. Counts
retained from the prior aligned-instruction scans need caller/owner
classification before they can become compensation counts.

### Fighter time factor

Fighter float `+0x1AC` is a time factor, with base 1.0. In the active-bit-1
branch, `FUN_0024c440` writes it before the other fighter work:

1. if fighter `+0x1B0` is exactly 1.0, the factor is the result of
   `FUN_00306d30`; otherwise it is `+0x1B0`;
2. if fighter `+0x1B4` is not exactly 1.0, the factor is multiplied by it.

The prior scan recorded float loads at offset `+0x1AC` at 218 ELF sites between
`0x00218288` and `0x003032B0`, and 26 BTL sites. Offset matches alone do not
establish the base object's identity or the consumer's timing unit. The sampled readers
(`FUN_00218250`, `FUN_0021a140`, `FUN_0024d1c0`, `FUN_0024d5e0`) multiply a
rate, a coefficient, or an animation increment by it.

### Fractional timers

A timer block holds an integer count at `+0x0C` and a fraction at `+0x1C`.
`FUN_002117a0` arms it, `FUN_00211d80` counts up, `FUN_00211e70` counts down,
and `FUN_002118a0` tests whether a frame was crossed. Both advance functions
take the elapsed time in `f12`.

The prior direct-call inventory is below. Every listed input expression was
rechecked through MCP in this pass; character-specific semantic names are
not established merely by these offsets. All four scene-derived quotient
callers and the `+0x6168` caller advance only when `FUN_00224650` returns
zero; otherwise `FUN_00211f70` clears flags bit 1 without resetting the
cursor or remainder. Other event predicates have separate paths. The helper
ABI and event predicates belong to
[timer primitives](../../knowledge/runtime/timer_primitives.md).

| Call | Direction | Timer | Elapsed time |
| ---: | --- | --- | --- |
| `0x0020C4F4` | down | combo manager timer | literal 1.0 |
| `0x0024C7DC` | down | fighter `+0x248` | fighter factor |
| `0x0024C838` | down | fighter `+0x26C` | fighter factor |
| `0x0024C8AC` | down | fighter `+0x290` | fighter factor |
| `0x0024C908` | down | fighter `+0x224` | `f20`, loaded with 1.0 |
| `0x0024CA74` | down | fighter `+0x200` | literal 1.0 |
| `0x0024D608` | up | fighter `+0x1B8` | fighter factor |
| `0x0024D6D8` | up | fighter `+0x1DC` | fighter factor x (`+0xB90` / 256) |
| `0x0024D6F0` | up | fighter `+0x1DC` | fighter factor |
| `0x002663DC` | up | fighter `+0x5084` | `u16(scene at fighter+0x5114, +0x94) / 256.0` |
| `0x0029F5A0` | up | two blocks at fighter `+0x5528 + i*0x80` | `u16(scene at fighter+0x5598+i*0x80, +0x94) / 256.0` |
| `0x002A9C08` | up | two blocks at fighter `+0x5BF8 + i*0x80` | `u16(scene at fighter+0x5C68+i*0x80, +0x94) / 256.0` |
| `0x002AF4E4` | up | fighter `+0x4E68` | `u16(scene at fighter+0x4EF4, +0x94) / 256.0` |
| `0x002DCA6C` | up | fighter `+0x6168` | fighter factor |
| `0x00724748` (BTL; Ghidra `0x00724708`) | up | action-selected timer in Ghidra `FUN_007243a0` | `max(action record+0x5C, owning fighter+0x1AC)` |

**Inference:** the quotient timers already follow their auxiliary scene's
rate; independently halving both that rate and the derived timer argument
would apply two scales. The BTL maximum instead means a record rate can
prevent a reduced fighter factor from slowing the timer. Its selected record
and timer lifetime need the combat-action owner's contract before proposing
a compensation. Neither family supports a blanket non-step-reader rule.

### CCS animation clock

`FUN_001bb210(scene, increment, context)` accepts an unsigned delta in
1/256-frame units. `FUN_001bb5c0` requests a position in the same units;
its active-blend exception is described below.

| Binary | `jal FUN_001bb210` | Increment is a 16-bit load from `scene + 0x94` | Other | `jal FUN_001bb5c0` |
| --- | ---: | ---: | --- | ---: |
| ELF | 178 | 177 | 1 computed, inside the seek at `0x001BB6C4` | 35 |
| `BTL.BIN` | 254 | 254 (25 of them through an embedded scene at a larger offset) | 0 | 214 |
| `ETC.BIN` | 106 | 106 | 0 | 3 |

The current MCP JAL-encoding scan reproduces the advance/seek counts
`178/35`, `254/214`, and `106/3` after resident mirrors are collapsed.
Some sites remain unmarked as code. This rechecks opcode inventory, not every
caller boundary or the prior increment-source classification.

The prior scan classified the ordinary playback calls as loading the scene's
increment field. This does not establish their cadence or every writer of the
field. `FUN_001b7520` initializes it to `0x0100` at `0x001B7524`, rechecked
through MCP in this pass.

The fighter model scene at fighter `+0xE70` is driven by `FUN_0024d1c0`. Each
update it writes `increment = speed(+0xB90) x factor(+0x1AC)` to the scene and
calls `FUN_001bb210` at `0x0024D32C`.

## Mixed fighter clocks: concrete uncompensated consumers

**Observed, high static confidence:** the complete resident ranges
`FUN_0024c440` (`0x0024C440..0x0024CCC4`), `FUN_0024d5e0`
(`0x0024D5E0..0x0024D820`), and `FUN_0024de40`
(`0x0024DE40..0x0024E09C`) mix factor-based and call-based time. Relevant
loads, arithmetic, calls, and delay slots were corroborated in MCP disassembly.

| Consumer | Per-call advancement and gate | 60-cycle consequence if the same gate stays open |
| --- | --- | --- |
| Fighter `+0x248/+0x26C/+0x290` | Down timers take `f12 = fighter+0x1AC`; active bit 1 and `+0x20C < 1`, with each timer's local gate | A factor of 0.5 can preserve their nominal accumulation rate. |
| Fighter `+0x224` | Down timer at `0x0024C908` takes `f20 = 1.0`, loaded at `0x0024C470..474`; active bit 1, `+0x20C < 1`, and timer-specific flags | Halving `+0x1AC` does not slow it. |
| Fighter `+0x200` | Down timer at `0x0024CA74` takes literal 1.0; this tail is outside the active-bit-1 block, with its own timer flags | Halving `+0x1AC` does not slow it; disabling only active fighter work does not cover this tail. |
| Fighter `+0x9C0/+0x84/+0x19A/+0x19C/+0x954/+0xB72` | Each nonzero signed halfword decrements by one in `0x0024C740..0x0024C7B4`, under active bit 1 | Twice as many eligible calls consume these counters twice as quickly. Their meanings are not inferred here. |
| Fighter `+0x82` | Decrements by one at `0x0024C5B0..0x0024C5B8`, after its nonzero, state/action, and `FUN_00307480` gates | Same call-rate dependency, conditional on those additional gates. |
| Position ring `+0x8C0`, records `+0x840` | Index increments and wraps at 8; copies position `+0x30..+0x3C` once per active first-phase call at `0x0024C5DC..0x0024C608` | The ring covers half the elapsed span if calls double; this is a sampling/lifetime change, not a scalar speed. |
| Fighter `+0x1B8/+0x1DC` | Late routine advances by factor, or factor times `u16(+0xB90)/256`; `+0x20C < 1`; animation-wrap flag `+0xB98` can instead reset `+0x1DC` | Fractional accumulation exists, but reset and event order must remain consistent with scene playback. |
| Fighter `+0x548` | In `FUN_0024d5e0`, increments by one and saturates at 9999 under several additional state/flag gates; maintains maximum `+0x54A` | This count is not slowed by the factor. Its producer/metric semantics belong to match-outcome research. |
| Late ring `+0x4C4`, records `+0x344` | `0x0024E020..0x0024E064` increments/wraps at 32 and copies `+0x338..+0x340`, after late callback and timer advancement | Its history span follows eligible late calls, independently of fractional clocks. |
| Combo object's timer at `object+0x10` | `FUN_0020c420`, call `0x0020C4F4`, subtracts literal 1.0 when its integer count at object `+0x1C` is nonzero; a hit-related path rearms it to `0x5A` | A fractional timer implementation alone does not compensate a caller that keeps supplying 1.0. |

`FUN_002504b0` calls `FUN_0024fd80` before the child first-phase list. That
routine first applies `FUN_0024c440` to every list member, then makes further
passes over fighter state and event gates. The late routine
`FUN_0024de40` calls `FUN_0024d5e0` only after its active, flag, and
`+0x20C` conditions. Thus moving timer calls or applying half-speed at a
single later point can change what earlier consumers observe.

`FUN_00306d30` is not the pacing-byte getter. It starts at 1.0 and adds
`child+0x7C - 1.0` for eligible objects in fighter `+0x8C4/+0x8C8`, caps the
result at 1.25, and forces 1.0 in specified fighter states. Writing only the
result `+0x1AC` before `FUN_0024c440` is consequently unstable: that routine
recomputes it. A proposed global time scale must be applied at an established
factor-production point while retaining these retail modifiers.

## Input publication, history, and lifetime

**Observed:** `FUN_001081b0` calls `FUN_00113480` before task servicing.
The latter ages both rumble queues, then calls `FUN_00113710` for each pad.
The publication method replaces `held`, `pressed = ~previous & held`, and
`released = previous & ~held` on every call. An unchanged nonzero mask
increments byte `+0x44` to 15 while output `+0x70` is zero; the following
unchanged call publishes the held mask as repeat. Mask change or zero resets
the counter. The detailed port/packet contract is owned by
[controller input](../../knowledge/runtime/controller_input.md#held-edges-and-repeat).

**Inference:** if pad publication runs on both 60 Hz presentation cycles but
simulation consumes only alternate cycles, a press that existed only on the
skipped cycle can disappear from resident `+0x68` before simulation reads it.
A held input does not have that edge-persistence property. A split design
therefore needs an explicit decision about sampling, edge accumulation, and
repeat ownership; changing only the battle masks does not provide one.

**Observed:** BTL Ghidra `FUN_006ef5c0` is live `0x006EF600`. It copies
context byte `+1` into `ccCommand+0x7C`, allocates `(300/step)*0x18+0x10`
bytes, constructs records, and clears ring indices. Ghidra
`FUN_006f09c0` (live `0x006F0A00`) advances exactly one record per call;
Ghidra `FUN_006f0e60` (live `0x006F0EA0`) invokes that physical routine,
copies pad state, normalizes edges, and translates commands. Encoded overlay
targets are live, so its decompiler label `FUN_006f0a00` must not be used as
the physical byte entry. The resident first-phase `ccCommandCtrl` gate and
its `+0xA50 == 1` exception are documented in
[action commands](../../knowledge/gameplay/combat/action_commands.md#battle-input-object-and-circular-history).

The normalized battle edges compare consumed history samples. A button still
held at the next sample can therefore produce a battle press even after its
resident core press expired; a press and release entirely between samples
is absent from both held snapshots. Resident repeat is not copied into the
ring. These distinct boundaries are documented in
[publication lifetime](../../knowledge/runtime/controller_input.md#publication-lifetime-and-consumer-snapshots).

**Design dependency:** ring capacity must follow the intended simulation
sampling rate, not merely the presentation pacing byte. At step 1, a
300-record ring sampled only 30 times per second nominally retains ten
seconds; at 60 samples per second its span is five seconds but the retail
record-count matcher windows halve in elapsed duration. Reconstructing an
input object resizes/clears its ring; changing the pacing byte on a live object
does neither. These are distinct lifetime choices, not automatic compensation.

## Fractional animation is coupled to integer events

**Observed:** complete MCP disassembly of `FUN_001bb210`
(`0x001BB210..0x001BB4E4`) and `FUN_001bb5c0`
(`0x001BB5C0..0x001BB6E4`) supports fractional curve evaluation, but the
advance API also owns packed commands, attached generator actions, and event
list lifetime. [Animation runtime](../../knowledge/runtime/animation_runtime.md#advance-and-end-behavior)
owns the full contracts; the consequences for 60 FPS are:

- An increment `0x80` represents half an animation frame. Curves receive that
  fractional delta, while command/effect advancement is gated by a change of
  `cursor >> 8`. The fighter caller converts `speed*factor` to an integer and
  stores a halfword; odd rates can lose fractional precision when halved.
- Terminal clamp, loop reset and blend residuals make “two half calls equal
  one full call” conditional. Loop handling discards overshoot; a blend consumes
  its whole duration and forwards only the remaining delta.
- Each advance clears the previous event list, including zero/fractional calls.
  Event delivery is a separate API, `FUN_001bb190`, used by the fighter after
  advance and attachment work. An added presentation advance must not clear
  undelivered events or cause the same retained list to be delivered twice.
- Seek is not a pure visual sampler. Without an active blend, a backward seek
  resets evaluator and command-reader state then advances from zero; commands
  and events can be reconstructed. An equal seek clears the event list without
  reevaluation. Active-blend cancellation sets the comparison origin to zero
  but retains the published cursor: target zero takes that equal return, while
  a positive target is passed as a delta added to the retained cursor before
  end/loop handling. See the [seek contract](../../knowledge/runtime/animation_runtime.md#absolute-seeks-and-evaluator-reset).

**Design dependency:** halving a scene's rate preserves its nominal cursor
rate only when its calls double and its rate writer, binding, seek, looping,
blend and command consumers follow the same intended time domain. A single
initializer change to scene `+0x94` does not cover the fighter's per-update
writer or the independent streamed-container family. Caller ownership is
tracked in [scene playback owners](../../knowledge/runtime/scene_playback_owners.md).

## Countdown and presentation-owned timing

**Observed:** resident `FUN_001ed110` clears the battle countdown fields
and writes step `0x00044444` to `0x006B28EC` at
`0x001ED204..0x001ED210`. Initial session setup `FUN_001eee30` puts the
selected duration into `0x006B28D4` by shifting it left 24. This setup is
distinct from generic `FUN_001eba10`, which zeros the supplied timer block,
including its step. `FUN_001eba80` (`0x001EBA80..0x001EBB64`) subtracts
that stored step from remaining `+4`, adds it to elapsed `+8`, and has no
fighter-factor or pacing-byte read. Its flag bits 0/1 inhibit the arithmetic;
bit 2 reports completion, with expiration set when the remaining value becomes
negative. The call at `0x001F11B8` also needs two fighters, both `+0xB00 == 0`,
both flag `+0x61 &8`, two zero-return subsystem predicates, global
`0x00607670 == 0`, and session active bit 1.

Countdown digit presentation uses a ceiling in 24-fraction-bit units, as
documented in [pause and replay](../../knowledge/gameplay/session/pause_and_replay.md#battle-countdown-gate-and-presentation).
**Inference:** `0x44444 / 2^24` is approximately `1/60` displayed unit per
eligible call. That arithmetic does not independently prove a second of
wall time: at 30 eligible calls/s it advances about 0.5 displayed unit/s.
Doubling eligible calls with the same step doubles this arithmetic rate;
halving the fighter factor does not affect it. A 60 FPS choice must preserve
the retail rate intended here, rather than assume that a digit equals one
second or rewrite its value on that assumption.

**Observed presentation exceptions:**

| Owner | Clock and gate | Timing dependency |
| --- | --- | --- |
| Four-slot RGBA pool, `FUN_00183650` | When pool `+0 == 0`, samples color at the current cursor, then increments each active slot's signed-halfword cursor by one. It advances even without packet storage. | Increasing draw-function calls increases transition rate; a nominally separate draw path contains timing mutation. Arming, endpoint and phase rules are owned by [UI animation](../../knowledge/runtime/ui_animation.md#draw-before-advance-order). |
| Mode Select scalar, `FUN_00387400` | Caller supplies target and fixed step; sampled Mode Select call uses 0.1 and gates selected-resource advance near zero. | No external time argument; caller rate controls convergence. See [fixed-step approach](../../knowledge/runtime/ui_animation.md#fixed-step-scalar-approach). |
| ETC Ghidra `FUN_006b51a0`, live `0x006B51E0` | Stable-selection path advances scene at owner `+0x28` using scene `+0x94`, then increments independent owner counter `+0x10` and resets it at 21. Call bytes at Ghidra `0x006B5314`, counter at `0x006B5328..0x006B5334`. | Slowing only scene playback does not slow the independent counter. The owner is left unnamed here; no screen identity follows from those fields alone. |
| Global and detached emitter managers | Engine tail `FUN_00108490` steps resident manager `0x0061AF80` and detached managers while context `+0x192 &7 == 0`; each manager additionally requires byte `+0x51 != 0`. | Fighter mask/factor changes do not cover this engine-tail scheduling. Age, emission and fade have call-based contracts in [particle runtime](../../knowledge/runtime/rendering/particle_runtime.md#manager-gates-and-call-sequence). |
| Battle HUD | Chakra display reservation increases by 0.5 per child update; blink/marker and clock-feedback cursors also count presentation updates. Children can update while parent draw-hidden. | Gameplay resource/countdown scaling does not scale these display clocks. Rates and owner masks are documented in [battle HUD](../../knowledge/gameplay/session/battle_hud.md#chakra-storage-and-display). |
| Presentation camera | Eye/target offset counters increment once per eligible compute; final component approach uses coefficients 0.125/0.25 with a pre-scale difference cap of 300. | Delay, duration, smoothing and the manager gate are separate dependencies; 37.5/75 are per-call displacement caps, not velocities in seconds. See [battle camera](../../knowledge/gameplay/session/battle_camera.md#presentation-camera-smoothing). |
| Background rotation/UV owners | `FUN_00398510` increments angle only after nonzero culling result; `FUN_0039b910` likewise advances UV by speed times parent `+8` after that result. | Their eligible-call counts depend on classification and, for UV, a supplied factor. Do not classify all draw readers as uncompensated or all rejected draws as pure submission skips. See [visibility](../../knowledge/runtime/rendering/visibility.md#bounded-resident-caller-inventory). |

`FUN_001abc70` also advances generator managers once per requested iteration.
Animation playback requests whole-frame crossings; the streamed worker instead
passes the raw signed `container+0x9C` at `0x001A05D0..0x001A05F4` to its
unsigned iteration loop. Those are different contracts: a raw `0x100` requests
256 iterations there. This pass corroborated both caller instructions and the
loop; [effect-generator commands](../../knowledge/runtime/effect_generator_commands.md#scheduling-and-owner-gates)
owns the detailed evidence. Rate scaling across both families cannot assume
that every manager count uses the same fixed-point conversion or the same gate.

Composition attachments introduce another per-call domain: `FUN_00189d10`
has no delta-time argument or frame-count loop and integrates/corrects its
chains once per invocation. Additional fractional scene evaluation therefore
does not by itself preserve attached motion. The integration, rebase and
teardown contracts belong to [attachment execution](../../knowledge/runtime/rendering/composition_attachment_dynamics.md#attachment-step-rebase-and-destruction).

## Why rate scaling alone does not preserve every trajectory

[Movement and physics](../../knowledge/gameplay/stages/movement_and_physics.md#shared-movement-fields-and-ordering)
establishes that ordinary displacement uses current speed times the fighter
factor before gravity updates the next speed. **Mathematical inference** for
constant gravity, factor 1, no contact/clamp/transient contributions and ordinary
gravity multiplier 1: one full update moves by `v` and leaves speed `v-g`;
two half updates move by `v/2 + (v-g/2)/2 = v-g/4` and leave the same speed.
Thus halving both gravity and displacement preserves their nominal rates but
does not reproduce the retail sampled path. Contacts and state transitions can
make that difference consequential; their complete effects are not established
by this arithmetic example. Gravity multiplier `+0x9B4` also resets to 1
after each pass, so a one-pass request is not automatically a two-pass request.

Recursive approach has a different issue. For an unchanged target and no clamp
or snap, `value += (target-value)*k` leaves residual error multiplied by `1-k`.
Two calls with coefficient `k/2` leave `(1-k/2)^2`, not `1-k`. The coefficient
`1-sqrt(1-k)` used twice would match one old call's residual only under those
conditions; it does not settle camera caps, changing targets, endpoint snapshots or state
gates. [UI animation](../../knowledge/runtime/ui_animation.md) and
[battle camera](../../knowledge/gameplay/session/battle_camera.md#presentation-camera-smoothing)
own the relevant retail consumers. Panel duration additionally participates
in geometry, so doubling an arming duration is not a generally safe timing-only
change; see [panel open/close](../../knowledge/runtime/ui_animation.md#shared-panel-openclose-controller).

## Static timing and dependency model

The order below is established within the inspected functions; task workers
are separate kernel threads. A manager wake/barrier is not a generic atomic
gameplay callback or proof of actual display cadence.

```text
VBlank callback -> count byte +0
main: wait for threshold +1 -> wake manager
manager top: clear count -> ordinal++ -> display bookkeeping -> publish pads
  -> registered callback under context +0x192 gate
  -> task wake/lifecycle service and cooperative barrier
    MOTHER task, active battle path:
      start-menu input -> battle state gate -> build masks
      -> first phase (command history precedes players)
      -> second phase -> late phase -> countdown gate -> outcome work
manager tail: gated emitter steps/draws -> submission/flush -> sleep
```

The wait counts arrivals and resets the byte at the next manager top. It does
not measure a float elapsed interval or perform a shown catch-up loop to advance
each gameplay consumer once for every missed VBlank. Nominal 60/30-cycle
reasoning assumes a 60 Hz display, timely service, the ordinary wait gate,
and no additional consumer suppression. “Step 1” alone is not proof of
60 distinct simulation or motion samples per second.

EE packet-list rotation, master-chain parity and GS environment selection
are separate state. The worker's end-of-frame wait bounds DMA packet lifetime;
it does not independently prove complete GS rasterization or capacity for
60 presentation samples per second. A presentation design must respect that
rotation/completion contract, owned by [render submission](../../knowledge/runtime/rendering/render_submission.md#completion-and-packet-lifetime).

| Time domain | Proven owners | Reset/lifetime dependency |
| --- | --- | --- |
| VBlank threshold | System context `+0/+1`, current-step rumble subtraction | Setter clears count; movie path saves/restores the threshold. |
| Engine-cycle ordinal | System context `+0x194`; pad repeat | Ordinal advances regardless of battle masks; repeat resets on mask change/zero. A parity gate using this ordinal would therefore run during suppressed battle work too. |
| Gated simulation invocations | Integer fighter counters, history/rings, literal timers, countdown | Owner creation, timer arming, history clearing and pause gates must share the chosen simulation cadence. |
| Fractional time | Fighter factor and 0x24-byte timer block | Arming/reset sets integer event flags and clears remainder; consumers observe previous/current/predicted positions. |
| Animation cursor | 1/256-frame scene delta, auxiliary derived clocks | Binding, blend end, seek, loop and event-list clearing mutate more than the cursor. |
| Presentation invocation | RGBA transition draw, scalar approach, selected draw/culling-gated owners | Drawing cannot be assumed side-effect free; slot rearming and retained histories have independent lifetime. |

## Provisional design choices

No option below is an implemented patch or an accepted implementation design.
The static evidence rules out a complete solution made only from pacing step 1,
a fighter factor of 0.5, or a scene-default increment of `0x80`.

| Choice | What can be preserved by construction | Conditions and remaining cost |
| --- | --- | --- |
| 30 Hz simulation with 60 Hz presentation | Retail integer event, command and history units if every simulation owner retains its cadence/order | Separate presentation transforms/poses from mutating advance/seek/event APIs; cover emitters and draw-owned fades; define input sampling and edge handling; initialize/reset presentation phase and snapshots with owner lifetime. Repeated state alone adds no motion sample. |
| 60 Hz simulation with half-duration steps | Fractional curves, factor-based motion and accumulator rates in the inspected paths | Convert or gate literal/integer consumers, countdown, repeat/matcher windows, rings, record-rate maxima and independent owners. Preserve per-owner retail modifiers. Two smaller updates need not reproduce one larger physics/collision/easing step. |
| Separate discrete events from fractional visual advancement | Keep commands/history at retail tick units while creating intermediate pose samples | The present advance APIs couple curves to commands, attachments and event lifetime. A safe presentation evaluator needs a proven ownership boundary and cannot simply call normal seek twice. |

**Inference:** the first choice has the smallest demonstrated semantic change
to discrete simulation. It is a preferred research direction, conditional on
finding a presentation evaluation boundary that does not mutate simulation-owned state.
The third describes one way to satisfy that condition; it is not established
as available merely because scene curves accept fractional increments.

## Bounded pass result and remaining dependencies

This pass establishes why none of the three single-value changes above covers
the inspected retail owners. It supplies a timing model and concrete consumer
inventory sufficient to distinguish the provisional choices; it does not
establish a complete patch list or a finished presentation evaluator.

Remaining research is specifically:

- An evaluation/submission boundary for intermediate model, camera and
  attachment presentation that leaves gameplay and command-event lifetime
  intact; dependent on [animation evaluation](../../knowledge/runtime/animation_runtime.md),
  [model transforms](../../knowledge/runtime/rendering/model_runtime.md),
  [render submission](../../knowledge/runtime/rendering/render_submission.md) and
  [scene ownership](../../knowledge/runtime/scene_playback_owners.md).
- Full semantic classification of the scene-call inventory, factor writers,
  action-record maximum rates and other camera/UI/stage owners. The retained
  218/26 field-load inventory cannot supply that classification by itself.
- Complete collision, random-event and ordering consequences of 60 Hz
  simulation; audio and other independently scheduled consumers are not
  classified by this pass. Event counts require event semantics, not automatic
  halving because an update loop runs more often.
- Presentation-phase reset and snapshot lifetime across binding, teardown,
  reconstruction and suppression, plus sampling rules for consumers outside
  `ccCommand`. The start menu reads shared core pressed/repeat before battle
  masks, and other gameplay readers bypass history, as documented in
  [controller input](../../knowledge/runtime/controller_input.md#consumers-in-the-front-end-task).

These are limits of the current bounded evidence and design readiness. They
are not claims of observed failures or executable implementation instructions.
