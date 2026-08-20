# 60 FPS timing architecture and implementation research

## Status

This document records the current evidence for implementing a real 60 FPS mode
in Narutimate Accel 2 v2.28, clean executable CRC C0659AD1. It supersedes the
earlier assumption that the Master Mode and in-engine cinematic targets were
anonymous dynamically generated code. They are stable words in the ADV and BTL
overlay files and can be guarded and patched at their file offsets.

The core conclusion is that changing the resident renderer threshold from two
VBlanks to one doubles the engine-update and task-manager wake cadence. It is
not a render-only unlock. Animation cursors, actor timers, event durations,
scene motion, camera work, effects, UI, input repeat, and sound-cue scheduling
must each remain at their original wall-clock rate. Prerecorded PSS movies are
different: the resident movie player already forces a one-VBlank presentation
path, so their encoded video and audio speed must not be halved.

“30 FPS” and “60 FPS” are nominal shorthand here. On the NTSC game path the
relevant presentation cadence is approximately 29.97 versus 59.94 Hz. Every
compensation below is derived from the exact two-VBlank-to-one-VBlank ratio,
not from assuming an exact 16.6667 ms host interval.

The static mapping is now sufficient to build guarded diagnostic patch
components. It is not sufficient to enable 60 FPS by default. In particular,
the exact six-word community battle port changes a shared producer and has a
confirmed second-consumer side effect; it is not a safe final actor-speed fix.
Clean matched runtime captures are still required to prove the remaining
candidates, find uncovered timing domains, and rule out double compensation.

The checked-in NA228 PNACH contains no enabled 60 FPS recipe. This research
therefore does not claim to reproduce the exact external or local build that
was reported broken. It establishes the clean-code failure mechanisms and the
specific evidence needed to diagnose that build.

## Research coverage

- **Assigned scope:** the architecture required for a correct 60 FPS mode in
clean *Narutimate Accel 2* v2.28: renderer/scheduler cadence, skeletal and cel
animation speed, battle and training time, Master Mode traversal, in-engine
cinematics, effects, camera, stage objects, HUD/front-end UI, input/repeat,
rumble, prerecorded PSS video, and audio/cue synchronization. The goal is to
separate physical 60 Hz presentation from every clean wall-time owner, not to
produce a renderer-only unlock or to redesign authored media.

- **Exploration depth:** deep static reverse engineering of the clean boot ELF and the
ADV, BTL, and ETC overlays, with complete-word checks for the listed patch
sites, cross-version mapping of the inherited NUN5 community candidates,
targeted clean-media inspection, and source inspection of the maintained PCSX2
input-recording path. CCS call coverage was counted in both recovered C and raw
aligned JAL scans; representative controller/projectile/stage/UI families were
traced forward through their state mutations. This is broad subsystem coverage,
but not an exhaustive classification of every unrecovered call, every virtual
class, or every dynamic +0x94/+0x278 producer.

- **Confirmed coverage:** the two-to-one-VBlank renderer gate and resulting
task cadence; CCS 8.8 playback, fractional transform evaluation, integer cel
cursors, absolute seeks, one-shot priming, and custom/odd playback increments;
the safe final battle-actor factor boundary and the failure of the inherited
shared-producer patch; independent hitstop, combo, round, support, projectile,
camera, stage, HUD, lifecycle, input-repeat, ordinal, and rumble timing; ADV
traversal/cinematic/effect candidates; nonlinear UI/controller updates; P2M2
physical-VSync semantics; and the separation of approximately 29.97 FPS PSS
video, audio sample clocks, and gameplay-owned cue timestamps.

- **Unresolved or untested:** no
complete 60 FPS build has been executed. Matched clean-30/candidate-60 captures
are still required to classify recurring versus setup CCS calls, cover dynamic
and class-specific producers, confirm battle half-frame bone matrices, identify
the smooth camera render handoff, prove event/audio/subtitle sync, validate all
modes and overlay reloads, and measure sustained EE/GS performance. The final
actor hook still needs a guarded payload location, and formula-derived easing
or camera constants remain diagnostics where nonlinear authoritative-state
interpolation is the safer design.

- **Deliberate exclusions and overlap:** unrelated gameplay/localization changes, asset
replacement, frame interpolation for prerecorded video or authored cel art,
global audio resampling, and implementation/staging/commit work. Existing
canonical task-system, controller-input, battle-camera, stage, pause/replay,
and game-file documents own their detailed contracts; this document links or
summarizes only the timing implications needed for 60 FPS. It does not claim an
in-game replay system where the separate pause/replay research found none.

- **Evidence limitations:** the Ghidra overlay imports omit the
0x40-byte MWo3 header, some functions are split or mis-prototyped, and static
control flow cannot prove live callback frequency, visible smoothness, race
behavior, audio perception, or hardware headroom. Community labels are treated
as external leads until the NA2 consumer is established. Clean-word identity
proves the mapped instruction, not the behavior of a complete unexecuted patch.

## Evidence labels

Every conclusion below uses one of these labels:

- **Proven static behavior**: established from clean NA2 instructions and
  control flow.
- **High-confidence NA2 port**: an exact or structurally equivalent NA2 site
  was matched to a known NUN5 patch and its local semantics were checked.
- **Semantic candidate**: the NA2 code clearly owns the relevant quantity, but
  the intended 60 FPS value or downstream effect still needs runtime proof.
- **External behavioral claim**: a community label or reported outcome that has
  not yet been reproduced in this workspace.

Static analysis can prove what a word does. Only matched 30/60 recordings can
prove that a complete patch preserves wall-clock behavior.

## Binary identity and address conventions

The mappings in this document are tied to these exact binaries:

| Binary | Size | SHA-256 |
| --- | ---: | --- |
| NA2 boot ELF | 5,273,256 | 20C0A40D70EA412CD431993A2E189B37ECB6054D63AE93BE545470016E1627AF |
| NA2 ADV overlay | 2,174,720 | AD60D9C9D11811CE57A4E64F35226EBB366D580010761A0FD1300DFE621BC34D |
| NA2 BTL overlay | 2,237,184 | 56FD042740221E3CC91417194F147142799D51FE70642273F4E97BD389D5D63C |
| NA2 ETC overlay | 200,448 | 8FF3C6E1ED5CE2B093B0934C898C40D1CEEA0C20778C49CDA5591AAD02375C74 |
| NUN5 boot ELF | 5,340,912 | 20A43677397731A2A20899336D1165ACE5B436906B9B89BE90FB10F4558DD19D |
| NUN5 ADV overlay | 2,049,792 | 7E2AF55362141BB1B055247CD7EF7EDAE290F3C0095701BC51467F096A2D00B8 |
| NUN5 BTL overlay | 2,253,184 | 7E8518DA7BD4957AF18CB0ABABE67F0E9B37C42C6551375201B15997F0A3DFE3 |

NUN5 overlays load at 0x006C6D00. NA2 overlays load at 0x006B3F00.
Runtime address equals overlay load base plus file offset. The existing Ghidra
overlay imports omit the 0x40-byte MWo3 header, so their displayed address is
runtime address minus 0x40.

All proposed writes are full little-endian MIPS words. An implementation must
verify the complete clean word before replacing it; matching only an opcode,
halfword, or address is not an adequate guard.

Focused clean-file validation on 2026-08-20 reread 64 resident/ADV/BTL words
listed or directly supporting the candidates in this document, including the
final actor hook and the independent +0x224 timer diagnostic. All 64 matched
their recorded 32-bit values; there were zero mismatches. This validates the
static identities and offsets, not the behavior of an unexecuted combined
patch.

## Timing-domain map

| Domain | Clean owner | Effect of a one-VBlank scheduler | Required treatment |
| --- | --- | --- | --- |
| Resident engine cycle | Renderer threshold and task-manager wake loop | System update and manager cycle run twice as often | Change threshold from 2 to 1, then compensate frame-counted consumers |
| CCS scene timeline | FUN_001BB210 and scene fields +0x94/+0xEC | The clean 8.8 increment is applied twice as often | Use a 0x80-equivalent automatic playback increment while preserving absolute seeks |
| Direct CCS frame cursors | FUN_00195810 and FUN_001956E0 | A direct one-frame step advances twice as often if its owner runs every update | Gate only periodic owners; preserve explicit seeks and setup steps |
| Battle fractional actor state | Final per-actor timing factor and accumulators | Actor animation/state advances twice as fast | Multiply the final effective factor by 0.5 after all clean modifiers |
| Battle integer state | Raw countdowns, authored-frame tests, and transform-history ring | Counts and history samples advance twice as often | Advance on a 30 Hz logical phase or add fractional state; do not rely on the actor float alone |
| Battle round timer | Timer +0x1C fixed-point delta | Remaining/elapsed counters change twice as fast | Halve both startup and per-round reset deltas |
| Support gauge | Per-fighter recharge/drain mutation | Gauge fills and drains in half the clean wall time | Gate the gauge mutation at logical 30 Hz for exactness, or halve both constants |
| Battle projectiles | Manager callback cadence, projectile +0x278 float factor, and raw +0x82/+0x84/+0x200 counters | Motion/progress and authored projectile phases run twice as fast | Halve all common +0x278 producer states and gate raw counters/modulo schedules on logical 30 Hz |
| Battle camera | Controller/object callbacks, raw phase counters, and clamped recursive tracking | Preset durations halve and tracking response changes | Advance authored camera phases on logical 30 Hz; either preserve clean tracking on that phase or decouple it and interpolate render transforms |
| Battle-stage environment | Stage-class callbacks for blends, break/rebirth timers, moving props, gravity, and effect triggers | Fades, respawns, props, and authored effect frames run twice as fast | Classify each state mutation; gate integer phases and event triggers, and compensate or interpolate continuous transforms |
| Battle HUD | CCS scene time plus controller-local slide, pulse, delay, and reverse-frame cursor | Gauge entrances, pulses, and reverse animation complete twice as fast | Use the compensated CCS clock, halve continuous HUD deltas, and keep integer delays/cursors on logical 30 Hz or convert them to fractional state |
| Master Mode traversal/encounters | ADV overlay constants | Movement and encounter animation run twice as fast | Patch the mapped ADV timing terms, then validate interactions |
| In-engine cinematics | ADV event counters and scene transforms | Durations halve and motion doubles | Double integer durations and halve per-update motion/conversion terms |
| ADV continuous effects | Paired GP-relative deltas at -0x48F0 and -0x4620 | Particle motion, fades, and float lifetimes advance twice as fast | Halve both clean deltas at every producer while preserving freeze/slow-motion ratios; separately gate raw integer delays |
| UI fades and recursive easing | Front-end/controller-local float mutations | Linear transitions and nonlinear settling complete in roughly half the wall time | Gate for exact legacy state, or halve linear deltas and convert recursive coefficients by their two-substep composition |
| PSS movies | Resident MPEG/IPU player | Movie path already owns a one-VBlank presentation rate | Do not alter video or audio speed |
| Streamed/sequence audio | Audio hardware and cue producers | Samples retain their rate; gameplay cues may fire early | Do not resample; validate cue scheduling |
| Input edges | Resident poll before the game callback | Held/pressed/released refresh at 60 Hz | Preserve unless a consumer proves otherwise |
| Input repeat | Two 15-update delay generators | Delay and sustained repeat become twice as fast | Double initial delay and pulse sustained repeat every other update |
| Rumble | Milliseconds converted to 60 Hz ticks and aged by current VBlank threshold | 2 ticks at 30 Hz becomes 1 tick at 60 Hz | No timing patch required |
| PCSX2 P2M2 input recording | Emulator VSync boundary, outside the game | Recording frames remain physical VBlanks; they do not become 60-FPS game-update frames | Replay the same records unchanged and compare by physical recording frame/wall time; preserve intervening input edges in logical game consumers |
| Renderer frame ordinal | Physical engine-cycle counter used by masks, modulo schedules, and buffer alternation | Legacy periodic effects run twice as often, while true render alternation may be correct | Keep a physical 60 Hz ordinal and route only wall-clock consumers to a logical 30 Hz ordinal |

## What an implementation needs

A credible implementation needs more than a PNACH line and an FPS counter:

1. **Exact binary identity.** Guard the full clean words against the hashes in
   this document. Refuse the feature on an unknown ELF or overlay instead of
   writing by address into a different revision.
2. **Lifetime-correct patch delivery.** Resident hooks can use the project's
   existing injection/catalog path (or a bounded confirmed PNACH diagnostic).
   ADV, BTL, and ETC share the same overlay window, so overlay edits must be
   file-backed or reapplied only after identifying the loaded overlay; a fixed
   unguarded runtime address is not sufficient.
3. **Two explicit time bases.** Keep a physical one-VBlank/60 Hz phase for
   presentation, pad polling, and real buffer alternation, plus a logical
   clean-rate phase for authored integer state. Subsystems with fractional
   clocks consume compensated deltas instead of being globally skipped.
4. **Small private timing state.** Classified CCS playback needs a per-scene
   odd-increment carry; logically gated UI needs accumulated input edges; smooth
   authoritative interpolation needs previous/current clean-rate transforms.
   That state must reset on object destruction, overlay unload, scene seek, and
   mode/reset transitions.
5. **An atomic opt-in configuration.** The final user-facing feature should
   enable the renderer gate and every required compensation together and remain
   disabled by default until validation passes. Diagnostic subpatches can exist
   for development, but are not separate supported “60 FPS” modes.
6. **Matched runtime evidence.** Use the same clean savestate or P2M2 stream for
   30/60 runs and capture clocks, counters, transforms, events, audio cues, and
   PSS A/V timestamps at identical physical-frame markers.
7. **Enough emulation and display performance.** PCSX2 must sustain 100% game
   speed with one game update per VBlank, without frame skip or cycle-rate hacks
   masking missed deadlines. A 60 Hz-or-faster display is needed to see every
   presentation. There is no defensible universal CPU/GPU model requirement;
   the acceptance test is measured EE/GS frame time on the declared renderer,
   resolution, and PCSX2 build.

No animation, video, or audio asset conversion is required to correct speed.
Existing fractional model tracks can be sampled more often; authored cel art
and approximately 29.97 FPS PSS video legitimately repeat across 60 Hz display
intervals.

## Why a gate-only unlock is broken

Changing only 0x001E11C0 removes one VBlank from the engine wait. It does not
create an independent render pass between 30 Hz simulation updates.
Consequently, it doubles every update path driven by an engine cycle:

- automatic CCS scene players apply their 8.8 fixed-point timeline increment
  twice as often;
- direct integer animation cursors can advance twice as many authored frames;
- battle actor timers, world movement, event queues, and camera transforms age
  twice as quickly unless their own accumulators or constants are compensated;
- cue-producing scripts can desynchronize from audio whose hardware sample rate
  did not change.

A single global 0.5 multiplier is also wrong. It misses integer cursor paths,
can double-compensate externally clocked state, and would incorrectly slow
subsystems such as PSS playback that already use a one-VBlank timing path.

## Resident scheduler and frame gate

### Proven control flow

The boot-time renderer threshold is the actual update gate:

- FUN_00107560(renderer, threshold) stores the one-byte threshold at renderer
  +0x01 and clears the one-byte accumulated VBlank count at +0x00.
- The GS/VBlank interrupt path FUN_00108CE0 calls
  FUN_00108D70(renderer, 1), which increments that count.
- FUN_001083A0 blocks until the accumulated count reaches the threshold.
- FUN_001081B0 clears the count, increments the renderer frame ordinal at
  +0x194, and performs system, input, display, and registered-callback work.
- FUN_001C13F0 waits at FUN_001083A0 and wakes the manager after each
  successful gate.
- Manager entry FUN_001D0590 calls FUN_001081B0, services task lifecycle,
  performs its cooperative barrier, calls FUN_00108490, and sleeps until the
  next wake.

Task records are real independent EE kernel threads. Their entry at record
+0x0C is passed to CreateThread; there is no central per-record update/draw
callback. The manager cycle controls lifecycle and cooperative progress rather
than invoking every task body exactly once. The one-VBlank change nevertheless
doubles the system update, manager cycle, registered game callback, input poll,
and the progress opportunity for task loops that yield once per manager cycle.

The clean threshold of two therefore produces one full scheduler update for
two VBlanks. Replacing it with one produces one full scheduler update per
VBlank. On a 59.94 Hz NTSC output this is the architectural 60 FPS unlock, but
it also doubles every task that assumes one scheduler call equals one authored
30 Hz frame.

### Gate candidate

| Binary | Runtime | File offset | Clean word | Candidate word | Meaning |
| --- | ---: | ---: | ---: | ---: | --- |
| Boot ELF | 0x001E11C0 | 0x000E12C0 | 0x24050002 | 0x24050001 | Initial renderer threshold 2 to 1 |

This is proven static ownership. It has not yet been executed as part of a
complete NA2 patch. The more detailed resident task contract is recorded in
[runtime/task_system.md](../runtime/task_system.md).

## CCS animation architecture

### The common 1.0 argument is not the animation clock

NA2 does not have one universal “animation speed” float. The resident CCS
render/evaluation functions expose several superficially similar paths:

- FUN_00194180(weight, container), runtime 0x00194180 / ELF offset
  0x00094280, walks child objects. Type 0xE00 dispatches to sprite/animation
  evaluation; type 0x100 dispatches to model/skinning evaluation.
- FUN_00195760(weight, animation), runtime 0x00195760 / offset 0x00095860,
  evaluates the current authored frame and stores the weight times an inherited
  multiplicative factor at animation +0xB8. It does not increment the integer
  frame cursor.
- FUN_00195810(weight, animation), runtime 0x00195810 / offset 0x00095910,
  performs the same evaluation and then increments the signed cursor at +0xF6
  by exactly one, including loop/end handling.
- FUN_001956E0(animation, frames), runtime 0x001956E0 / offset 0x000957E0,
  advances the integer cursor by an explicit integer number of frames.
- FUN_00190F40(weight, model), runtime 0x00190F40 / offset 0x00091040,
  applies the same inherited multiplicative factor to model evaluation.
- FUN_0019C6E0 resolves the inherited +0x84/+0x88 factor through the parent
  chain.

The meaning of that first argument is proven by the downstream animation
renderer, not inferred from its frequent value of 1.0. FUN_00195A90 reads
animation +0xB8, multiplies it by an authored per-frame unsigned value, shifts
the result, and clamps it to 1..255 before emitting the draw packet. The model
path similarly stores the product in render scratch +0x114 and suppresses a
path when the value is below 1/128. These are render/visibility weights, not
elapsed-time deltas.

Relevant fields are therefore:

| Offset | Static meaning |
| ---: | --- |
| +0x84 | Resolved local/inherited render factor |
| +0x88 | Parent-relative render-factor component |
| +0x8C | Parent/factor flags |
| +0x8E | Object/type selector |
| +0xB0 | Authored animation frame count/end |
| +0xB8 | Evaluated render weight used by the animation draw path |
| +0xF6 | Signed authored-frame cursor; -1 and -2 are sentinel states |

This corrects a dangerous earlier interpretation. FUN_00194180 with literal
1.0 has 24 call sites in ADV, 59 in BTL, and 24 in ETC;
FUN_00190F40 with literal 1.0 has 15 in ADV and 10 in BTL. Replacing those
literals with 0.5 would change alpha/visibility and would not fix the general
scene clock. They must remain 1.0 unless a particular effect intentionally
changes its render weight.

### The general CCS animation clock is 8.8 fixed point

FUN_001B7520 initializes a CCS scene/player object with +0x94 = 0x0100.
FUN_001BB210(scene, increment, event_context), runtime 0x001BB210 / ELF offset
0x000BB310, owns the corresponding timeline:

1. It adds the unsigned increment to the 8.8 position at scene +0xEC.
2. It clamps against `(authored_frame_count - 1) << 8`, processes the crossed
   event interval, and stores the new fixed-point position.
3. It mirrors the fractional byte at +0x96 and the integer authored frame at
   +0x98.
4. Only when the integer part changes does it call FUN_001956E0 for each type
   0xE00 child, advancing child +0xF6 by the integer-frame difference.

The ordinary automatic call shape passes the halfword at the same scene's
+0x94. Clean 0x0100 therefore means one authored frame per call. If those
owners run at 60 Hz, an automatic increment of 0x0080 advances one authored
frame over two physical updates while preserving the fixed-point remainder and
event-crossing order. FUN_001BB790 can still evaluate and draw the current
children every physical frame; its scene +0x88 argument is a render factor,
not the timeline increment.

The default clock has an exact guarded steady-state diagnostic at
FUN_001B7520:

| Runtime | ELF offset | Clean | 60 Hz candidate | Effect |
| ---: | ---: | ---: | ---: | --- |
| 0x001B7524 | 0x000B7624 | 0x24030100 | 0x24030080 | Initialize scene +0x94 to 0x0080 instead of 0x0100 |

That word covers scenes which retain the constructor default, but it is not a
safe final global patch. The same stored +0x94 value is also used for one-time
setup calls which are not doubled by the new cadence:

- ADV FUN_00702550 constructs a scene with FUN_001B7520, binds an object, and
  immediately calls FUN_001BB210 once before entering its recurring update;
- BTL FUN_00717F80 state 0 binds the battle gauge and primes it with one
  FUN_001BB210 call before switching to recurring state 1;
- BTL FUN_008341E0 binds and primes a scene using its current +0x94, then writes
  0x0200 for later playback.

Changing the constructor to 0x0080 makes those clean one-frame priming steps
half-frame steps. The candidate is therefore useful for proving steady-state
speed and fractional interpolation, but a shippable implementation must leave
one-shot priming unchanged or explicitly restore its full clean increment. It
also does not cover a later custom +0x94 write or a direct
FUN_001956E0/FUN_00195810 cursor.

The robust correction boundary is a classified *periodic consumption* of
+0x94, not the field merely existing. A wrapper can halve the increment only at
proven recurring FUN_001BB210 call sites and carry the odd low bit per scene.
Alternatively, patch each recurring producer after its setup phase. Merely
testing `increment == scene->+0x94` inside FUN_001BB210 is insufficient because
the one-shot calls above have the same shape. Explicit seeks, binding primes,
setup steps, and non-periodic positioning must remain unchanged.

BTL contains proven post-construction producers, including 2.0, approximately
0.496, 1.09375, 0.46875, 0.25, and 1.0 authored frames per call. Representative
clean words are:

| BTL owner/use | BTL file | Runtime | Clean | 60 Hz treatment |
| --- | ---: | ---: | ---: | --- |
| FUN_008341E0 state assignment, +0x94 = 0x0200 | 0x001827A0 | 0x008366A0 | `0x24030200` | `0x24030100` |
| Nested scene assignment, +0x94 = 0x007F | 0x00183F38 | 0x00837E38 | `0x2403007F` | Alternate 0x003F/0x0040 with carry; no exact single word |
| FUN_0083D1F0 early phase, +0x94 = 0x0118 | 0x0018966C | 0x0083D56C | `0x24030118` | `0x2403008C` |
| FUN_0083D1F0 later phase, +0x94 = 0x0078 | 0x001896F4 | 0x0083D5F4 | `0x24030078` | `0x2403003C` |
| FUN_008886E0 nearby-effect time factor, 0.25 | 0x001D4948 | 0x00888848 | `0x3C023E80` | `0x3C023E00` (0.125, later converted to +0x94 = 0x0020) |
| FUN_008886E0 ordinary +0x94 = 0x0100 | 0x001D49B8 | 0x008888B8 | `0x24030100` | `0x24030080` |

These are clean-file-verified producer diagnostics, not an exhaustive patch
list. A classified consumption wrapper can leave their stored clean values
unchanged and scale only recurring uses. If the producers themselves are
patched, their one-shot setup ordering must first be proven. The
FUN_008886E0 alternate branch copies another scene's +0x94; copying is already
correct if the source clock is compensated. FUN_0083D1F0 changes both scene
speed and controller-local X/Y motion according to the current authored frame,
so changing only its two +0x94 words still leaves the local trajectory fast.

More generally, dividing an even 8.8 increment is exact. An odd increment
cannot be divided exactly in the existing halfword. Rounding 0x007F to 0x0040
would make a long-running scene about 0.787% fast: two physical calls would add
0x0080 where one clean call adds 0x007F. An automatic-playback hook must retain
a one-bit remainder per scene (or equivalent higher-precision accumulator) and
alternate floor/ceiling increments. Reset that remainder when the clean owner
writes a new speed, performs an absolute seek, or resets the scene; otherwise a
stale carry can move an authored event across the reset boundary.

Fractional time is not merely stored and ignored. FUN_001BB210 calls
FUN_001B8410 on every ordinary advance, even when the integer part does not
change. That evaluator passes the 8.8 increment into the CCS track decoders:
FUN_001A67D0 linearly evaluates scalar keys, and the vector/orientation paths
including FUN_001A4250 and FUN_001A6C30 evaluate intermediate transform state.
The special +0x114 segment path similarly calls FUN_001B9480 with the absolute
8.8 position normalized over the segment. These paths update type 0x100 model
objects and transform state for type 0xE00 objects at fractional positions.

Consequently, a 0x0080 clock can yield distinct 60 Hz scene transforms using
the engine's existing interpolation; it is not inherently an every-other-frame
simulation gate. What remains integer is the type 0xE00 artwork cursor +0xF6:
the sprite/cel image advances only when the scene integer frame changes. A
sprite can therefore move or fade at half-frame positions while showing the
same authored cel twice. Static code proves fractional transform evaluation,
but not that every skeletal clip supplies a visibly distinct half-frame pose;
that needs matched pose-matrix captures.

Static call coverage makes this the principal non-battle CCS clock. The
decompiler exposes 174 resident automatic calls that pass scene +0x94, 222 in
ADV, 224 in BTL when embedded-scene equivalents are included, and 62 in ETC.
Additional direct JALs occur in unrecovered or argument-omitted blocks: an
aligned clean-binary scan for the exact `jal 0x001BB210` word finds 178 calls
in the boot ELF, 286 in ADV, 254 in BTL, and 106 in ETC. Those extra sites must
be classified from instructions or live traces before claiming complete
coverage.

There is one proven exception inside the resident CCS core. FUN_001BB5C0 takes
an absolute 8.8 target, resets state when seeking backwards, and invokes
FUN_001BB210 with `target - current`. Blindly halving every increment inside
FUN_001BB210 would therefore break absolute seeks, scripted positioning, and
setup paths. A final hook, if used instead of producer patches, must distinguish
automatic playback increments from the FUN_001BB5C0 seek path; changing every
1.0 render literal or dividing every FUN_001BB210 input is not safe.

### Direct cursor paths and visible smoothness

FUN_00195810 remains a separate whole-frame owner. Its only recovered overlay
caller is ADV FUN_00719710: the caller copies object +0x5C into the animation's
+0x84/+0x88 render-factor fields and calls FUN_00195810 with weight 1.0. The
cursor still advances by one regardless of that weight. If this owner runs on
every 60 Hz cycle, gate its periodic cursor step on the logical 30 Hz phase;
do not change the 1.0 weight.

The four recovered resident calls to FUN_001956E0 include explicit one-frame
steps and a `new_frame - old_frame` synchronization step. They are seeks or
authored-state transitions, not evidence for a global half-speed patch. Each
owner must be classified as periodic playback or explicit positioning.

Using 0x0080 in the ordinary CCS scene timeline preserves clean animation
speed and lets existing fractional transform tracks sample twice per authored
frame. Type 0xE00 child artwork selection remains integer, so each 30 Hz
authored cel is still rendered twice. Synthesizing new in-between cel artwork
would be a separate content/interpolation feature, and event-triggered state
must remain tied to the crossed authored interval. Neither is required to stop
double-speed animation.

## Battle and training actor timing

### Proven actor factor

FUN_00306D30(actor) walks active effect records referenced from actor +0x8C4
and +0x8C8. It combines each record's +0x7C modifier, clamps the result, and
forces special values in specific actor states. Its ordinary result is 1.0.

FUN_0024C440 stores that result at actor +0x1AC and feeds it to
FUN_00211D80 and FUN_00211E70. Those consumers already have a fractional
accumulator at timer +0x1C: they accumulate the float delta and advance the
integer cursor only when the total crosses 1.0. This proves that multiplying
the ordinary actor factor by 0.5 advances one original authored frame over two
60 Hz scheduler updates without inventing a new timing mechanism.

The actor's primary timer begins at actor +0x1B8. Its relevant fields are more
than an integer cursor:

| Timer offset | Primary actor offset | Meaning in FUN_00211D80/FUN_00211E70 |
| ---: | ---: | --- |
| +0x08 | +0x1C0 | Previous crossed integer frame |
| +0x0C | +0x1C4 | Current crossed integer frame |
| +0x10 | +0x1C8 | Previous fractional frame position |
| +0x14 | +0x1CC | Current `integer + remainder` position |
| +0x18 | +0x1D0 | Predicted next fractional position |
| +0x1C | +0x1D4 | Fractional remainder |

Authored-frame event tests are aware of this fractional window.
FUN_002118A0 and FUN_00211A20 compare the previous, current, and predicted
float positions when deciding whether a requested frame was crossed. A 0.5
actor delta therefore delays the integer transition to the second physical
step while retaining the crossing interval, rather than simply dropping every
other event test.

This still does not prove that every battle skeletal renderer consumes +0x1CC
as an interpolated pose coordinate. Static code proves fractional time and
fraction-aware event tests; matched bone/palette matrices must establish
whether an individual clip renders a distinct half-frame pose or repeats its
integer pose between crossings. That visual distinction does not change the
required 0.5 wall-time factor, but it determines whether the result is truly
smooth motion or correct-speed duplicated animation art.

### Exact six-word community port: diagnostic only

| Runtime | ELF offset | Clean | Replacement | Effect |
| ---: | ---: | ---: | ---: | --- |
| 0x00306D5C | 0x00206E5C | 0x00000000 | 0x3C083F00 | Load 0.5 exponent into t0 |
| 0x00306E6C | 0x00206F6C | 0xC7B40000 | 0x4488A000 | Move the 0.5 bits to f20 |
| 0x00306E70 | 0x00206F70 | 0x27BD0030 | 0x46140002 | Multiply result by f20 |
| 0x00306E74 | 0x00206F74 | 0x03E00008 | 0x27BD0030 | Restore stack |
| 0x00306E78 | 0x00206F78 | 0x00000000 | 0x03E00008 | Return |
| 0x00306E7C | 0x00206F7C | 0x00000000 | 0xC7B4FFD0 | Restore f20 in delay slot |

The words are an exact structural NA2 port, but the target is not private to the
main actor update. FUN_00306D30 has two direct callers:

- FUN_0024C440 stores its result as the actor's effective factor at +0x1AC;
- FUN_00235510 uses the same result to scale authored transition thresholds at
  +0xB66 and +0xB68, later compared against the authored-frame cursor at
  +0x1C4.

In the ordinary clean state, the shared-function patch returns 0.5 to both
callers. The main cursor then advances by 0.5 per 60 Hz update, but
FUN_00235510 also reduces a threshold T to 0.5T. Reaching 0.5T at 0.5 frame per
60 Hz update takes T / 60 seconds, while clean reaches T at one frame per 30 Hz
update in T / 30 seconds. That transition therefore still takes half the clean
wall time. This is a proven static side effect, not merely an uncovered domain.

The same port also misses some main-actor states. FUN_0024C440 calls
FUN_00306D30 only when actor +0x1B0 is exactly 1.0. Otherwise it copies +0x1B0
directly to +0x1AC, then optionally multiplies by +0x1B4. A 0.5 multiply inside
FUN_00306D30 cannot normalize that override path.

The final implementation should therefore leave FUN_00306D30's clean semantics
intact and multiply the composed +0x1AC value after the +0x1B0 selection and
+0x1B4 modifier. Runtime 0x0024C4C8 / ELF offset 0x0014C5C8 is the first common
instruction after that composition; its clean word is 0x0220202D
(`move a0,s1`). It is a viable guarded hook site if an injected stub performs
the 0.5 multiply, restores `a0 = s1`, preserves the following `a1 = 0`, and
returns to 0x0024C4D0. A concrete code-cave address must be selected and guarded
before this becomes an executable recipe.

### Proven battle paths outside the actor float

FUN_0024C440 itself contains several whole-frame operations which +0x1AC does
not scale:

- countdowns at +0x82, +0x84, +0x19A, +0x19C, +0x954, +0x9C0, and +0xB72
  decrement by exactly one per active update;
- the index at +0x8C0 advances through an eight-entry transform-history ring
  at +0x840 once per update; FUN_00224420 retrieves older entries from that
  ring, so at 60 Hz the same eight samples cover half as much wall time;
- three FUN_00211E70 countdown timers at +0x248, +0x26C, and +0x290 receive
  actor +0x1AC, but the timers at +0x224 and +0x200 receive literal 1.0;
- BTL FUN_00722E50 separately decrements a short countdown once whenever the
  renderer frame ordinal changes. At a one-VBlank gate that is once per 60 Hz
  update.

The literal timer loads have exact diagnostic candidates:

| Owner | Runtime | ELF offset | Clean | 60 Hz diagnostic | Scope |
| --- | ---: | ---: | ---: | ---: | --- |
| Combo manager FUN_0020C420 | 0x0020C4E8 | 0x0010C5E8 | 0x3C023F80 | 0x3C023F00 | Changes the independent 1.0 countdown delta to 0.5 |
| Actor timer +0x200 | 0x0024CA68 | 0x0014CB68 | 0x3C023F80 | 0x3C023F00 | Changes this actor-independent 1.0 countdown delta to 0.5 |

FUN_0020C420 arms its timer with 0x5A (90) through FUN_002117A0 and decrements
it through FUN_00211E70 while the remaining integer at timer +0x0C is nonzero.
It is the combo manager's continuation window: new activity resets the 90-frame
timer, and expiry participates in clearing the accumulated combo state. The
timer is outside the actor factor, so without the diagnostic word it expires in
about half the clean wall time at 60 Hz.

Battle lifecycle transitions have raw waits too. The resident battle-state
machine commonly resets its shared countdown word `state[1]` to 3;
FUN_001EDD10 and FUN_001EDEE0 each subtract one on every visit before resource
destruction/construction and the next state transition. At 60 visits per second
the synchronization window becomes half as long. Keep these decrements on the
logical phase (or consistently double every proven arming value); they are not
actor animation time, and shortening them can alter overlay/resource lifecycle
ordering even when the visible fight already appears correctly paced.

The +0x224 actor timer loads literal 1.0 from saved FPU register f20 at runtime
0x0024C904 / ELF offset 0x0014CA04 (clean word 0x4600A306). It has no safe
one-word 0.5 replacement at that site without a prepared register or a stub.
Routing it to actor +0x1AC would be semantically wrong because the clean code
deliberately makes this timer independent of actor-local slow/fast modifiers.

The timer at actor +0x200 is specifically the fighter-update pause channel:
its current integer count is +0x20C, accepted-hit data can raise it, and the
normal action timeline is suppressed while it is positive. It is the clean
mechanism conventionally comparable to hitstop. The +0x248 block is a separate
action-entry lock whose +0x254 count is decremented with actor +0x1AC only after
the pause expires. Consequently, the final +0x1AC factor covers the action lock
but not hitstop; the +0x200 literal-delta candidate above is required to keep
hitstop at the clean wall-clock duration.

### Round timer and support gauge

The battle round timer has another independent fixed-point delta.
FUN_001EBA80 subtracts timer +0x1C from remaining +0x04 and adds it to elapsed
+0x08 on every eligible controller update. Both startup and the new-round reset
initialize +0x1C to 0x00044444. A 60 Hz controller with that value advances
the timer twice as far per clean unit of wall time. The exact 0.5 value is
0x00022222, and both initialization paths must agree:

| Owner | Runtime | ELF offset | Clean | 60 Hz candidate |
| --- | ---: | ---: | ---: | ---: |
| New-round reset FUN_001ED110 | 0x001ED204 | 0x000ED304 | 0x3C030004 | 0x3C030002 |
| New-round reset FUN_001ED110 | 0x001ED208 | 0x000ED308 | 0x34644444 | 0x34642222 |
| Resident startup FUN_005D82F0 | 0x005D83D4 | 0x004D84D4 | 0x3C020004 | 0x3C020002 |
| Resident startup FUN_005D82F0 | 0x005D83D8 | 0x004D84D8 | 0x34434444 | 0x34432222 |

Patching only startup would be undone by the next round reset; patching only
the reset would leave the first initialized instance dependent on call order.
The timer's existing freeze and battle-state gates remain untouched.

Support availability is not a simple integer cooldown. Normal fighter update
FUN_00238540 either adds `fighter[+0x78] / 450` to gauge +0x74 when no support
object is active, or subtracts `1 / 300` while one is active, clamping to
0..1. At twice the fighter-update cadence, both recharge and active drain take
half their clean wall time. Exact half-constant diagnostics are:

| Path | Runtime | ELF offset | Clean | 60 Hz diagnostic |
| --- | ---: | ---: | ---: | ---: |
| Recharge, 1/450 to 1/900 | 0x0023861C | 0x0013871C | 0x3C033B11 | 0x3C033A91 |
| Active drain, 1/300 to 1/600 | 0x00238738 | 0x00138838 | 0x3C033B5A | 0x3C033ADA |

The following ORI words retain mantissas 0xA2B4 and 0x740E respectively; only
the exponent-bearing LUI words change. Halving gives a smoother 60 Hz gauge,
but two rounded float32 half-additions are not guaranteed to reproduce every
bit of one clean full addition. Gating only the gauge mutation on the logical
30 Hz phase instead preserves the exact clean float sequence and threshold
crossing order. The caller-supplied signed-delta helpers FUN_00238830 and
FUN_00238950 are event mutations and must not be halved without classifying
their callers.

These facts make the required architecture explicit: continuous actor and
fractional-timer deltas need a 0.5 global factor, while raw counters, history
sampling, round timing, gauge mutation, and authored integer transitions need
either a legacy 30 Hz phase or their own exact fractional treatment. Gating the
entire actor routine every other update would preserve integer state but would
also discard the 60 Hz opportunity for continuous motion and transforms. The
correction must be narrower than the whole actor update.

The six-word producer patch remains useful as a diagnostic comparison because
it reaches a broad ordinary actor path. It must not be described or shipped as
the complete battle compensation. Round timing, hitstop, support characters,
projectiles, particles, camera shake, battle UI, and scripted controllers still
require independent classification.

Training mode must be validated independently. Shared actor code does not prove
that training resets, recording playback, dummy logic, and UI clocks use the
same timing domain.

### Projectile time factor and raw frame phases

The BTL projectile manager does not inherit a complete fix automatically from
the main actor factor. Live 0x00734BA0 walks every active projectile once per
manager update, performs common pre-work, and invokes virtual update slot
+0x44. A one-VBlank scheduler therefore invokes projectile state machines at
60 Hz.

The common projectile float at +0x278 is an explicit fractional step:

- FUN_0072BF30 initializes it from the projectile manager's side-specific
  factors at manager +0xC8/+0xCC.
- FUN_00732B90 clamps motion to the smaller of projectile +0x278 and the
  current manager-side factor, then multiplies a motion vector by that result.
- Root callback FUN_0072C900 and many subclass callbacks add +0x278 to float
  progress +0x1FC; other subclasses multiply velocity, acceleration, angles,
  and fixed-point progress by +0x278.

FUN_007355AC refreshes manager +0xC8/+0xCC before the projectile walk. In the
ordinary clean path it writes 1.0 to both. Its alternate branch copies the two
actors' +0x1AC factors, but clean resident FUN_00307A60 currently returns zero
unconditionally, so that branch is not reached by the clean executable. The
ordinary default therefore needs its own 0.5 replacement even if the final
actor +0x1AC hook is installed.

Common projectile pre-work adds another required producer. FUN_0072ECD0,
entered at FUN_0072ED10 from the root update, rewrites +0x278 on every eligible
call: a nearby actor effect record with ID 0x4A selects 0.25, otherwise it
selects 1.0. This overwrites the spawn-time manager value. Both states must be
halved; changing only the default manager factor leaves the 0.25 state at
twice its clean wall-clock speed.

| Owner/state | BTL file | Runtime | Clean | 60 Hz candidate |
| --- | ---: | ---: | ---: | ---: |
| Manager ordinary +0xC8/+0xCC = 1.0 | 0x00081738 | 0x00735638 | 0x3C033F80 | 0x3C033F00 |
| Projectile effect state +0x278 = 0.25 | 0x0007AEAC | 0x0072EDAC | 0x3C033E80 | 0x3C033E00 |
| Projectile ordinary +0x278 = 1.0 | 0x0007AEBC | 0x0072EDBC | 0x3C033F80 | 0x3C033F00 |

Those guarded words cover the common factor path, not every class-specific
override. The BTL overlay contains additional projectile subclasses that
derive or replace +0x278; live traces must identify any reached write that is
not subsequently normalized by FUN_0072ECD0. Recording +0x278 at virtual-slot
entry is the fastest coverage test.

Projectile whole-frame state remains separate from +0x278:

- initial delay +0x84 decrements by one per callback;
- common state-6 expiry +0x82 decrements by one per callback;
- authored frame/phase +0x200 increments by one in the root and many subclass
  callbacks, and multiple subclasses use `+0x200 % divisor` for spawn or
  action schedules.

At 60 Hz those fields still run twice as fast after the three float
replacements. Their mutations and modulo decisions must run on the logical
30 Hz phase, or the fields must be converted to fractional state. A smooth
implementation should continue continuous vector work every physical frame
with +0x278 halved, while advancing +0x82/+0x84/+0x200 and authored spawn
decisions only on the logical phase. Gating the entire manager update would
preserve legacy projectile timing but forfeit smooth 60 Hz motion and collision
sampling.

### Battle camera phases and recursive tracking

The BTL camera controller and camera objects form another independent timing
surface; the recovered layout and state machine are documented in
[battle_camera.md](battle_camera.md). The controller's per-update commit
increments controller +0x2C when its +0x28 condition is active. This is an
integer duration counter and is not multiplied by actor +0x1AC.

The main camera-object family contains two authored transition channels:

- first-channel start/duration fields +0x228/+0x234 and phase counter +0x240;
- second-channel start/duration fields +0x22C/+0x238 and phase counter +0x244.

FUN_006D94D0 and FUN_006D95D0 increment +0x240 and +0x244 by one on every
eligible object update. Their movement envelopes select authored 0.25, 0.5,
or 1.0 weights from the integer phase and snap to the terminal vector at a
specific count. At 60 updates per second, leaving those counters physical
halves the preset delay and duration and changes the exact envelope and snap
ordering. These are logical-30 consumers. Merely halving the vector increment
does not fix when the state changes; blindly doubling only the duration fields
also changes the initializer's duration-derived step and the special edge
weights.

Separate functions FUN_006D9810 and FUN_006D99C0 track the two camera vectors.
For each coordinate they clamp target-minus-current to `[-300, 300]`, then
apply clean coefficients 0.125 and 0.25 respectively. Calling them twice as
often changes both the unsaturated exponential response and the maximum
wall-time displacement. With a stable target in the unclamped region, the
two-substep-equivalent coefficients are:

```text
first:  1 - sqrt(1 - 0.125) = 0.064585653...
second: 1 - sqrt(1 - 0.25)  = 0.133974596...
```

Those constants are not a complete patch. In the saturated region, changing
only the coefficient or only the 300-unit clamp cannot reproduce the clean
piecewise trajectory, and moving fighter targets can change between the two
physical samples. Two implementation levels are defensible:

- **Exact legacy camera:** run controller +0x2C, object +0x240/+0x244, envelope
  decisions, and the tracking state mutations only on the logical 30 Hz
  phase. Publish the resulting camera on both physical frames.
- **Smooth 60 Hz camera:** retain a clean 30 Hz authoritative camera state,
  including its clamps, counters, thresholds, and snap decisions, and
  interpolate only the render-facing eye/target transforms between adjacent
  authoritative states. This preserves clean endpoints without trying to
  retune a nonlinear state machine. It requires a confirmed render-facing
  handoff and is more invasive than constant replacement.

The formula-derived coefficients are useful diagnostic candidates for
unclamped tracking, not shippable proof. Runtime validation must cover a small
tracking correction, a displacement large enough to hit the 300-unit clamp,
a preset transition, stage-edge correction, and a camera shake or cinematic
camera path. Record +0x2C, +0x240/+0x244, the target vectors, authoritative
camera vectors, and final render transform at matched wall-clock timestamps.

### Battle-stage environment and breakables

Stage visuals and props are not passive consumers of the fighter clock. The
recovered classes in [stages.md](stages.md) have their own callback-local
state, exposing several distinct 60 Hz problems:

- `ccBgTransObject`, `ccBgTransAnm`, and `ccBgTransObject2` update proximity
  blend +0x54 toward a target with recursive coefficient 0.2, then derive a
  model frame from that blend. Unchanged at 60 Hz, the transition settles much
  faster. The stable-target two-substep coefficient is
  `1 - sqrt(0.8) = 0.105572809...`; exact legacy behavior uses a logical-phase
  mutation.
- `ccBgBreakObjectBattleAnm` and `ccBgBreakObjectRebornBattle` use raw
  greater-than-0x78 (120) rebirth waits and add 0.05 opacity per update. Their
  unchanged waits become half-duration and fades become twice as fast. A
  smooth linear fade uses 0.025, but the wait, state transition, reset, and
  repeat-count mutation must remain authored logical events.
- `ccBgBreakDollBattle` and `ccBgBreakObjectMoveBattle` own raw randomized
  cooldowns based on 60 and 30 respectively and decrement them once per class
  callback. These are logical-30 countdowns, not renderer ordinals.
- `ccBgBreakObjectFallBattle` subtracts 3.0 from vertical velocity on every
  unsupported update and propagates the transform. Halving only gravity is not
  sufficient to preserve a discrete position/velocity trajectory when both
  integration steps run twice; use authoritative-30 state plus render
  interpolation, or derive and validate a consistent half-step integrator.
- `ccHandRowShip` applies damped sinusoidal rocking and vertical bounce each
  update. It is another nonlinear integrator whose response cannot be inferred
  from the actor +0x1AC factor.
- `ccCraneTruck` emits effect 0x1017 at authored animation frames
  410/350/250/206/60/0. Its model clock can use the CCS fractional path, but
  each integer-frame effect must remain a once-only crossed-frame event.

The correction boundary is the same as for camera and projectiles: keep
authored state transitions, counters, collision/contact side effects, random
draws, and effect emission on the logical timeline; allow purely visual
transforms to update at 60 Hz only with a compensated delta or interpolation.
Gating every stage callback is an exact diagnostic, but it duplicates moving
props and may reduce collision sampling. A smoother implementation separates
authoritative stage state from render transforms and must prove that contacts
are neither missed nor applied twice.

Stage validation must include at least one proximity transition, one reborn
breakable through its 120-count wait and fade, one falling or moving prop, and
the crane's frame-triggered effects. Capture the class state, counter, opacity,
model/animation frame, transform, contact result, and emitted effect IDs at
matched wall-clock timestamps.

### Battle HUD mixed clock

The BTL `battlegauge` controller is a concrete proof that HUD animation is not
fixed by changing only the shared CCS increment. FUN_00717F80 owns the update
state and FUN_007182E0 performs the model/draw work. Its state machine combines
four different timing mechanisms:

- state 1 calls FUN_001BB210 with scene +0x94, so ordinary forward playback is
  covered by the compensated automatic CCS clock;
- state 3 calls FUN_00719020 with 30.0, adding that amount to gauge position
  +0x60 before clamping it to target +0x64;
- FUN_00718E60 advances two local 0..15 pulse phases by signed velocity fields
  initially set to 1.0, while a 15-call integer delay offsets one pulse;
- state 4 calls absolute-seek FUN_001BB5C0 with
  `(authored_end - controller_counter) * 0x100`. The counter at +0x14 is
  incremented by one in the draw-oriented FUN_007182E0 path whenever the
  controller state is active.

The last item is especially important: the 0x0080 default-clock change does not
affect an absolute seek whose target is rebuilt from an integer counter. If the
draw path is reached on every physical frame, +0x14 rewinds one complete
authored frame per 60 Hz presentation and the reverse animation finishes in
half the clean wall time. Preserve FUN_001BB5C0 itself. Either increment +0x14
only on the logical phase, or replace the counter producer with an 8.8
fractional cursor and pass its exact target. The clean increment is at BTL
Ghidra 0x007188E8, runtime 0x00718928, file 0x00064A28,
`0x24630001`; changing its immediate to zero is not compensation.

The simple continuous terms do have useful guarded diagnostic candidates. All
words below were read directly from the clean BTL.BIN:

| Purpose | BTL file | Runtime | Clean | Smooth candidate |
| --- | ---: | ---: | ---: | ---: |
| Initialize both pulse velocities, 1.0 -> 0.5 | 0x00064184 | 0x00718084 | `0x3C023F80` | `0x3C023F00` |
| Offset pulse delay, 15 -> 30 calls | 0x000641A0 | 0x007180A0 | `0x2402000F` | `0x2402001E` |
| State-3 gauge slide, 30.0 -> 15.0 | 0x00064304 | 0x00718204 | `0x3C0241F0` | `0x3C024170` |
| Pulse velocity after the zero crossing, 1.0 -> 0.5 | 0x0006508C | 0x00718F8C | `0x3C033F80` | `0x3C033F00` |

These four replacements are not a complete HUD patch: state transitions,
+0x14 reverse time, and any other reached controller-local integers remain
logical-frame work. An exact diagnostic can mutate the complete HUD controller
on logical 30 Hz while drawing its current state at 60 Hz, but must not also
halve a CCS scene that is already gated. A smooth implementation can keep CCS
and the pulse/slide terms physical with the candidates above, while advancing
the reverse cursor and authored state decisions through a separate logical or
fractional clock.

Validation must cover gauge entrance, the staggered two-channel pulse, a value
change, and the state-4 reverse/exit path. Record state +0x12, counter +0x14,
pulse phase/velocity/delay fields +0x20..+0x3C, gauge +0x60/+0x64, and scene
+0xEC at matched wall-clock timestamps. A visually plausible static HUD does
not establish correct exit timing.

## Master Mode traversal and encounter timing

The original NUN5 community patch describes four sites behaviorally as enemy
encounter speed, player encounter speed, player animation outside battle, and
movement/traversal outside battle. The community author also reported limited
testing and double speed outside Master Mode. Those labels are useful leads,
not NA2 proof. The original discussion is archived in the
[PCSX2 60 FPS codes thread](https://forums.pcsx2.net/Thread-60-fps-codes?page=29).

Cross-version structure and stable overlay offsets resolve the NA2 homologs:

| Reported NUN5 runtime | NUN5 ADV file | NA2 ADV file | NA2 runtime | Clean | Candidate |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0x007056E0 | 0x0003E9E0 | 0x0003D680 | 0x006F1580 | 0x3C033F80 | 0x3C033F00 |
| 0x007080AC | 0x000413AC | 0x0004033C | 0x006F423C | 0x3C033F80 | 0x3C033F00 |
| 0x0076C36C | 0x000A566C | 0x000A213C | 0x0075603C | 0x3C023F80 | 0x3C023F00 |
| 0x0076CE08 | 0x000A6108 | 0x000A2BA8 | 0x00756AA8 | 0x3C023F80 | 0x3C023F00 |

The last NUN5 word also exists in its BTL overlay. Its NA2 BTL homolog is file
offset 0x000A2018 / runtime 0x00755F18, with the same 1.0-to-0.5 replacement.
That shared BTL constant must not be enabled blindly together with the resident
battle actor factor: matched runtime traces must establish whether they own
different stages or would compensate the same quantity twice.

Static NA2 context gives these narrower descriptions:

- ADV +0x3D680 initializes three related fields at +0x218, +0x21C, and +0x220
  with a 1.0 term.
- ADV +0x4033C supplies the base term in a float update involving +0x220.
- ADV +0xA213C writes 1.0 to +0x274 after an authored-frame calculation.
- ADV +0xA2BA8, and the BTL homolog, supply a 1.0 term in a
  movement/placement formula.

All four are high-confidence structural ports. The exact gameplay labels and
the necessity of the BTL homolog remain runtime questions.

## In-engine cinematic timing

In-engine story and UJ scenes use ADV overlay objects, event queues, authored
animation frames, transforms, and ordinary sound cues. They are not PSS movies
and must not be treated as MPEG playback.

### Per-update vector displacement

NUN5 FUN_0080EA10 and NA2 FUN_007F3030 normalize a direction vector, multiply
it by a scalar at object +0x50, and add the result to position. The NUN5 patch
halves the scalar by decrementing its IEEE-754 exponent. The structurally
identical NA2 port is:

| NA2 ADV file | Runtime | Clean | Replacement | Meaning |
| ---: | ---: | ---: | ---: | --- |
| 0x0013F234 | 0x007F3134 | 0x4A0002FF | 0x3C09FF80 | Load exponent-decrement mask |
| 0x0013F254 | 0x007F3154 | 0x00000000 | 0x01094020 | Apply it to the scalar bits |

This is a high-confidence direct port. Runtime validation must still prove that
the scalar is finite and positive in every reached case, because the exponent
trick is not a general-purpose float multiply.

### Queue/event duration

NA2 FUN_007F2C50 compares the queue counter at object +0x18 against the current
entry duration at entry +0x08. With two scheduler calls per original frame, the
duration must be doubled. The NA2 instruction schedule differs from NUN5, so a
safe NA2-specific rewrite is:

| NA2 ADV file | Runtime | Clean | Replacement |
| ---: | ---: | ---: | ---: |
| 0x0013EDE4 | 0x007F2CE4 | 0x00000000 | 0x8E050018 |
| 0x0013EDE8 | 0x007F2CE8 | 0x8E050018 | 0x8C830008 |
| 0x0013EDEC | 0x007F2CEC | 0x8C830008 | 0x00031840 |

The following slt v1,a1,v1 instruction remains unchanged. The first load moves
into the preceding branch delay slot; that path already has a valid s0. This is
statically safe instruction packing, but its observable scene timing needs
runtime proof.

### Script-derived integer duration

NUN5 FUN_008073B0 doubles an evaluated script integer before storing it. NA2
FUN_007EC3F0 currently stores the value directly. Its epilogue has enough space
for this equivalent rewrite:

| NA2 ADV file | Runtime | Clean | Replacement |
| ---: | ---: | ---: | ---: |
| 0x0013854C | 0x007EC44C | 0xAC620010 | 0x00021040 |
| 0x00138550 | 0x007EC450 | 0x24020002 | 0xAC620010 |
| 0x00138554 | 0x007EC454 | 0xDFBF0000 | 0x24020002 |
| 0x00138558 | 0x007EC458 | 0x27BD0010 | 0xDFBF0000 |
| 0x0013855C | 0x007EC45C | 0x03E00008 | unchanged |
| 0x00138560 | 0x007EC460 | 0x00000000 | 0x27BD0010 |

The resulting order is: load the destination, double v0, store it, restore the
return value 2, restore ra, return, and pop the stack in the delay slot.
Instruction-level semantics are sound; a live trace must confirm the actual
caller ABI and cache/injection behavior.

### Animation fixed-point conversion

NUN5 FUN_008101E0 converts a scene animation position with a 307.0 scale, which
its community patch halves to 153.5. NA2 homolog FUN_007F4750 uses 256.0.
The semantic NA2 candidate is:

| NA2 ADV file | Runtime | Clean | Candidate |
| ---: | ---: | ---: | ---: |
| 0x001408A8 | 0x007F47A8 | 0x3C024380 | 0x3C024300 |

This changes 256.0 to 128.0. It is lower confidence than the direct structural
ports: a capture must correlate the producer, authored end frame, and visible
scene animation before this word is accepted.

## ADV effects and particle time

ADV contains two explicit GP-relative float deltas. Ghidra labels the words at
GP -0x48F0 and GP -0x4620 as `fGpffffb710` and `fGpffffb9e0`; those labels are
module-relative names, not stable absolute runtime addresses. All eight clean
store sequences write the same value to both words. The reached values are
0.0, 0.1, 0.3, 0.7, and 1.0, including state-dependent freeze and slow-motion
paths in FUN_006F73F0.

The recovered consumers prove elapsed-time semantics:

- FUN_0071A4D0 multiplies position, scalar, and color-rate terms by the
  -0x48F0 value and subtracts that value from float lifetime +0x38.
- FUN_0071B530, FUN_0071B680, and FUN_0071B7F0 multiply velocity and fade
  rates by -0x48F0 and subtract it from float lifetime +0x18.
- FUN_00764FE0, FUN_00765000, FUN_007654F0, FUN_00765560, and FUN_007656D0
  multiply velocity by -0x4620 and subtract it from float lifetime +0xFC.

No recovered read uses either word as render opacity or as a CCS evaluation
weight. At a 60 Hz update cadence, every nonzero clean value therefore needs
an exact 0.5 factor: 1.0 to 0.5, 0.7 to 0.35, 0.3 to 0.15, and 0.1 to 0.05;
zero remains zero. Halving a single default 1.0 would break the authored
freeze/slow-motion states.

Each nonzero producer has two independent constant loads: one supplies the
same scalar to the active scene objects through FUN_006F8B80 or the reset
dispatch, and the other supplies the paired effect globals. Both loads must be
changed. Patching only the globals would leave those scene objects at the
clean per-call factor while their particles use the compensated factor.

| Clean state | Purpose | ADV file | Runtime | Clean | 60 Hz candidate |
| ---: | --- | ---: | ---: | ---: | ---: |
| 0.3 | Object dispatch | 0x0002EEB8 | 0x006E2DB8 | 0x3C023E99 | 0x3C023E19 |
| 0.3 | Paired globals | 0x0002EEDC | 0x006E2DDC | 0x3C033E99 | 0x3C033E19 |
| 1.0 | Object dispatch | 0x0002EF48 | 0x006E2E48 | 0x3C023F80 | 0x3C023F00 |
| 1.0 | Paired globals | 0x0002EF5C | 0x006E2E5C | 0x3C033F80 | 0x3C033F00 |
| 0.7 | Object dispatch | 0x0002F384 | 0x006E3284 | 0x3C023F33 | 0x3C023EB3 |
| 0.7 | Paired globals | 0x0002F3A4 | 0x006E32A4 | 0x3C023F33 | 0x3C023EB3 |
| 1.0 | Object dispatch | 0x0002F62C | 0x006E352C | 0x3C023F80 | 0x3C023F00 |
| 1.0 | Paired globals | 0x0002F640 | 0x006E3540 | 0x3C033F80 | 0x3C033F00 |
| 0.1 | Object dispatch | 0x00043880 | 0x006F7780 | 0x3C023DCC | 0x3C023D4C |
| 0.1 | Paired globals | 0x00043898 | 0x006F7798 | 0x3C023DCC | 0x3C023D4C |
| 1.0 | Object dispatch | 0x000438B0 | 0x006F77B0 | 0x3C023F80 | 0x3C023F00 |
| 1.0 | Paired globals | 0x000438C4 | 0x006F77C4 | 0x3C023F80 | 0x3C023F00 |
| 1.0 | Reset dispatch | 0x00044C10 | 0x006F8B10 | 0x3C023F80 | 0x3C023F00 |
| 1.0 | Reset globals | 0x00044C4C | 0x006F8B4C | 0x3C033F80 | 0x3C033F00 |

The 0.0 path at runtime 0x006F7764/0x006F7768 stores `zero` directly and needs
no replacement. The table is a guarded static candidate set, not yet a claim
that all affected scene objects have been observed live.

The paired float deltas do not cover every field in their own effect classes.
FUN_0071B530, FUN_0071B680, and FUN_0071B7F0 decrement effect +0x14 by literal
1.0 once per call while that field is nonzero. This is an independent
whole-update delay/phase count. A complete implementation must gate that
mutation on the logical 30 Hz phase or convert the state to fractional time;
halving GP -0x48F0 alone leaves that phase twice as fast.

FUN_007197E0 demonstrates a second, raw particle design. It schedules spawns
with `physical_ordinal % object[+0x50]`, subtracts object +0x30 from each live
entry's lifetime +0x20, and adds the entry velocity at +0x10 directly to its
position at +0x00 on every call. There are two valid implementation targets:

- exact legacy behavior: run the spawn and particle mutation only on the
  logical 30 Hz phase, producing duplicate positions on the intervening draw;
- smoother 60 Hz behavior: keep the authored spawn schedule on the logical
  phase, but update live particles every physical frame with half lifetime and
  velocity deltas.

The smooth version requires a class-specific rewrite; redirecting only the
ordinal doubles motion and lifetime speed, while halving only the motion still
doubles spawn frequency. This is why effects cannot be fixed by one global
frame counter or by the CCS animation clock.

## UI fades, camera smoothing, and nonlinear updates

CCS timeline compensation does not slow controller-local UI state. The
resident front end contains direct per-call examples:

- FUN_003B7AF0 cross-fades two normalized fields by +0.1 and -0.1 and changes
  state when they reach 1.0 and 0.0. Ten clean calls become ten 60 Hz calls,
  so the transition takes half its clean wall time.
- FUN_003B9480 advances several visible controller fields by +/-0.2, advances
  a wrapping phase by 0.03, and also updates CCS scenes. Fixing the CCS scene
  increment leaves all of those local fields fast.
- The same FUN_003B9480 approaches a target with
  `x = x + 0.02 * (1 - x)`. This is recursive easing, not a linear elapsed-time
  addition.

Linear deltas can use a 0.5 factor for smooth 60 Hz behavior. Recursive
coefficients require composition. For a clean update
`x' = x + k(target - x)`, the 60 Hz coefficient whose two substeps equal one
clean update in real arithmetic is:

```text
k60 = 1 - sqrt(1 - k30)
```

For the observed `k30 = 0.02`, `k60` is approximately 0.010050506, not exactly
0.01. Likewise, a clean multiplicative damping `x' = d30 * x` needs
`d60 = sqrt(d30)`. This pattern applies to camera smoothing, screen fades,
particle drag, and UI springs wherever the current value feeds the next
update. Blindly halving a lerp coefficient or leaving a 0.9/0.95 damping
constant unchanged changes the response curve.

The BTL start-menu path provides a concrete mixed example. FUN_0087C6E0 state
4 updates horizontal position by its current velocity, adds 10.0 to that
velocity, adds 0.4 to opacity, and transitions after a 562.0 position
threshold. Its other states approach two target pairs using coefficients 0.2
and 0.4 while also advancing an embedded CCS scene. At 60 Hz:

- the opacity delta would be 0.2 for a smooth linear fade;
- stable-target easing coefficients are
  `1 - sqrt(0.8) = 0.105572809...` and
  `1 - sqrt(0.6) = 0.225403331...`;
- the position/velocity pair is a discrete acceleration integrator, so halving
  only velocity or acceleration changes its path and threshold-crossing time;
- local input delay +0x14, decremented by one in FUN_0087C3B0, is another
  logical-30 countdown even after the core input-repeat generator is fixed.

The safest exact treatment is to poll/accumulate input every physical frame
but mutate the menu state on the logical phase. A smooth rewrite must treat the
position and velocity together and fire the threshold action once. The
embedded scene still uses the compensated CCS clock; gating the whole menu and
also halving that scene would double-compensate it.

Battle pause is selective rather than one global frozen-update branch, as
documented in [pause_and_replay.md](pause_and_replay.md). FUN_001F03E0 applies
different masks to three virtual-update phases, while camera/controller and
other work can remain outside those masks. A 60 FPS implementation must keep
the clean pause masks and compensate each still-running timer/UI/camera owner;
installing one global alternate-frame skip around the battle dispatcher would
change pause semantics and discard input edges.

The ETC overlay has the same mixed-clock design, so title and front-end flows
cannot be certified from resident UI alone:

- FUN_006B9FC0 multiplies a local angular/motion field +0x38 by 0.7, adds 0.2
  to a local visibility field +0x34, and then advances an embedded CCS scene.
- FUN_006BD060 repeats the same 0.7 damping and 0.2 fade pattern across as many
  as six scene/model objects.
- FUN_006CFA90 advances another embedded CCS scene, recursively approaches a
  velocity/step target with coefficient 0.1, applies that result directly to
  position, decrements a randomized delay at +0x3C, and owns two integer
  counters at +0x40/+0x44 which trigger after 60 calls.

At 60 Hz, the stable two-substep damping for 0.7 is `sqrt(0.7) =
0.836660027...`; the 0.2 linear fade becomes 0.1; and the 0.1 approach
coefficient becomes `1 - sqrt(0.9) = 0.051316702...`. Those replacements do
not by themselves fix FUN_006CFA90 because its eased value is also integrated
into position and its random-delay/state transitions are integer events.
Exact treatment keeps its random draw count, countdowns, threshold decisions,
and state changes on the logical phase. Smooth treatment requires a coherent
position/velocity resampling or render interpolation, while its embedded CCS
scene independently uses the 0x0080 timeline.

These are representative proven owners rather than exhaustive ETC coverage.
Runtime write tracing should include every reached local float/counter beside
the scene +0x94 trace during title, main-menu, mode-select, options, save/load,
and transition flows.

There are two implementation standards:

- **Deterministic legacy:** mutate the controller only on the logical 30 Hz
  phase and render its current state on both physical frames. This preserves
  clean float operations, state-transition order, and threshold crossings.
- **Smooth 60 Hz:** halve linear deltas, convert recursive coefficients with
  the formulas above, and ensure threshold-triggered side effects fire once.
  Float32 rounding means this can preserve the continuous curve without being
  bit-identical to the 30 Hz trajectory.

Do not gate an entire front-end task without tracing input. Pressed/released
edges are published at 60 Hz and may exist for only one physical update. A
logical-30 UI controller needs an edge accumulator or separately ungated input
dispatch so it cannot miss a button event on the intervening phase.

### PCSX2 input-recording frame semantics

A `.p2m2` recording is an emulator-side controller stream, not an in-game
movie and not a count of NA2 gameplay updates. In the maintained PCSX2 fork at
commit `f351798d9f28b5b425231d8edaef09f3109eecf6`, `Counters.cpp::VSyncStart`
calls `VMManager::Internal::PollInputOnCPUThread` once at the emulated VSync
boundary. That function increments `g_InputRecording`'s frame counter and
selects the matching controller record; `InputRecording::updateControllerData`
reads that exact frame and overrides the current pad state.

Changing NA2's renderer threshold from two VBlanks to one does not change that
emulator VSync boundary. Therefore an existing recording must not be halved,
duplicated, resampled, or interpreted as one record per logical gameplay frame.
Its frame number remains the correct physical-time comparison key in both
clean-30 and candidate-60 runs. What changes is how often the game can consume
the held state between recording frames and which physical phase receives a
one-VSync button edge. Logical-30 consumers must accumulate those edges; simply
skipping input on alternate frames can desynchronize an otherwise valid replay.

For deterministic validation, launch the same `.p2m2` from the same boot or
savestate and compare game state at identical recording-frame markers. A
candidate that reaches an event at half the marker number is still fast even if
its own logical counter happens to match the clean numeric value.

## Prerecorded PSS video and video speed

The disc contains ten PSS files. They are MPEG program streams at approximately
29.97 encoded frames per second; their resolutions and durations are catalogued
in [game/files/README.md](../game/files/README.md#pss-video).

PSS playback has its own resident timing ownership:

- FUN_001057B0 saves the current renderer VBlank threshold through
  FUN_00105DA0.
- It unconditionally calls FUN_00107560(renderer, 1) before starting playback.
- It initializes the IPU/DMAC path, MPEG demux thread FUN_00103EE0, video decode
  thread FUN_00101AC0, and audio buffers.
- FUN_00105320 drains those resources and restores the saved threshold with
  FUN_00107560(renderer, saved_threshold).

This proves that clean 30 Hz gameplay already switches prerecorded movies to a
one-VBlank presentation path. After the global gameplay gate changes from two
to one, movie start still selects one and cleanup restores one. Consequently:

- do not apply a 0.5 speed factor to PSS video;
- do not stretch or resample PSS audio;
- do not classify an in-engine cinematic as PSS merely because it is
  noninteractive;
- do validate start, sustained playback, audio/video sync, skip, end, and
  restoration to gameplay.

The MPEG decoder is timestamp-, buffer-, and audio-hardware-driven rather than
using the CCS authored-frame cursor. A video that remains about 29.97 FPS during
60 FPS gameplay is expected behavior, not a failed 60 FPS implementation.

## Audio timing outside PSS

Changing the scheduler does not change the SPU2 sample clock. Streamed audio,
music, and voice data must not be globally played at half speed. The risk is
instead at the producer side: a gameplay event, subtitle, lip-sync marker, or
scripted cue measured in scheduler frames may fire too early or end too soon.

The media formats reinforce that separation. The ordinary AFS corpus is
predominantly 24,000 Hz AHX/ADX, while PSS carries 48,000 Hz stereo PCM. Those
rates are encoded stream contracts, not scheduler-derived values.

Resident effect wrappers such as FUN_001D83B0, FUN_001D87C0, and
FUN_001D8A30 validate IDs and immediately emit command/control packets through
FUN_00177018 and FUN_00177140 to the sound subsystem. They do not read the
renderer threshold or a gameplay delta. IDs at or above 0x1000 route through
the alternate stream path in FUN_001D7CF0, but the call still requests
playback; it does not advance audio by one gameplay frame. Static code
therefore supports unchanged pitch and sample duration after the scheduler
unlock.

What must move is the producer timestamp. A cue attached to a CCS event must
remain attached to the same crossed authored-frame interval; a cue attached to
an ADV integer queue must follow that queue's compensated duration; a battle
cue attached to an integer action frame must use the logical authored phase.
Adding a separate delay inside the sound API would desynchronize immediate
effects and double-compensate already-correct producers.

Validation must therefore separate:

- sample playback rate, which should remain unchanged;
- event/cue scheduling, which may require the same duration compensation as its
  owning gameplay or cinematic controller;
- PSS audio, which belongs to the MPEG playback pipeline;
- in-engine scene audio, which belongs to the ADV event/script pipeline.

No evidence currently supports a global audio-speed patch.

## Input and vibration timing

### Polling, edges, and repeat

FUN_001081B0 calls FUN_00113480 once per engine cycle before the registered
game callback and task consumers. It ages both vibration queues and then calls
FUN_00113710 for both ports. The poll refreshes held, newly pressed, newly
released, and repeat masks. A one-VBlank gate therefore samples and publishes
input at 60 Hz.

Pressed and released are computed from the previous raw held mask and do not
have a frame-counted delay. The core repeat generator does:

1. A new or changed nonzero held mask is published immediately and resets its
   byte counter.
2. The next 15 unchanged updates publish no repeat.
3. The 16th and every later unchanged update publish the held mask
   continuously.

Front-end analog-to-D-pad adapter FUN_001E0D20 independently recreates the
same 15-update rule with private per-port counters. It runs once at the top of
the front-end task's steady loop.

At 30 Hz the initial repeat delay is 16 / 30 seconds. At 60 Hz it becomes
16 / 60 seconds, and the post-delay continuous mask can drive direct consumers
twice as often. Resident menu code such as FUN_003832C0 -> FUN_00383340 reads
the repeat mask and changes its selected index in the same call, confirming a
real cadence-sensitive consumer.

Two exact threshold words can double the initial delay:

| Owner | Runtime | ELF offset | Clean | Diagnostic 60 Hz value |
| --- | ---: | ---: | ---: | ---: |
| Core physical-pad repeat | 0x00113AF4 | 0x00013BF4 | 0x2861000F | 0x2861001F |
| Front-end analog adapter | 0x001E0E00 | 0x000E0F00 | 0x2881000F | 0x2881001F |

Those two immediate changes are necessary but not sufficient. After the delay,
both clean paths expose repeat continuously. A complete 60 FPS implementation
must additionally suppress every other sustained-repeat update, while
preserving the immediate changed-mask event. That needs a small guarded hook or
equivalent consumer-independent filter; no safe two-word solution is claimed
yet. Globally polling only every other update would preserve repeat cadence but
would discard the intended 60 Hz edge sampling and would also interact with
rumble maintenance.

### Why rumble already compensates itself

Resident FUN_00113C70 converts vibration durations from milliseconds to
nominal 60 Hz ticks as round(ms times 60 / 1000), implemented as
(ms times 3 + 25) / 50.

FUN_00113B80 does not subtract a generic constant. It calls FUN_00105DA0,
which returns the current renderer threshold byte at renderer +0x01, and
subtracts that value from the active queue duration once per engine cycle:

- clean gameplay: subtract 2 ticks once per two VBlanks;
- 60 FPS gameplay: subtract 1 tick once per VBlank.

Both paths age the queue by approximately 60 ticks per second. This statically
establishes that ordinary rumble duration should remain wall-clock correct
after the gate change and must not receive a 0.5 compensation. Runtime
validation is still required for actuator transmission latency, override
stacking, pauses, and emulator behavior.

The full controller record and queue evidence is recorded in
[runtime/controller_input.md](../runtime/controller_input.md).

## Physical and logical frame ordinals

Renderer +0x194 is incremented by FUN_001081B0 once per successful engine
gate. It is therefore a physical engine-cycle ordinal: about 30 increments per
second with threshold two and about 60 with threshold one. Static direct-access
enumeration found two resident reads, 26 reads across 13 ADV functions, 12
reads across 11 BTL functions, and no ETC reads. These are not all the same
kind of clock consumer.

Confirmed examples show why globally replacing or halving the ordinal would be
wrong:

- Resident FUN_00300D70 schedules a trail/effect transform when
  `ordinal % divisor == 0`. Its divisor is derived from `1.0 / actor_factor`
  and clamped to 1..10. A final actor factor of 0.5 naturally selects every
  other 60 Hz update for the ordinary case; this consumer already has a local
  compensation mechanism.
- ADV FUN_007197E0 uses `ordinal % object[+0x50]` in its spawn schedule, then
  subtracts a float lifetime and adds velocity to position for every live list
  entry on each call. Both the schedule and the raw per-call particle motion
  change wall-clock behavior at 60 Hz.
- Four BTL functions at 0x006E8C10, 0x006E8C40, 0x006E8C50, and 0x006E9320 use
  `ordinal & 0x1F` to build a 32-step triangular color pulse. Leaving the mask
  unchanged halves the pulse period. A logical ordinal preserves the clean
  period with duplicated values; a 64-step physical-ordinal rewrite can
  preserve the period while producing smoother true-60-Hz values.
- BTL FUN_00722E50 stores the last ordinal and decrements a countdown once per
  new value. This is a legacy frame timer and must see a 30 Hz logical ordinal
  or an every-other-update gate.
- BTL FUN_00720F90 and FUN_00720FD0 use ordinal parity to swap two render-side
  values between passes. ADV FUN_007508C0 and four more BTL functions also use
  parity. These may be physical buffer/render alternation rather than elapsed
  gameplay time; redirecting them without a visual trace could create a fixed
  eye/pass, flicker, or every-two-frame artifact.
- Eleven ADV battle-skill functions use `ordinal & 3` before periodic calls to
  resident FUN_001D83B0. Their frequency doubles in wall time at 60 Hz, but the
  downstream effect must be identified before choosing duplicated 30 Hz work
  or a true-60-Hz rewrite.

A correct implementation therefore needs two explicit concepts even if they
are not exposed as public engine APIs:

1. **Physical ordinal:** the existing +0x194 value, advancing every displayed
   60 Hz engine cycle. Keep it for buffer selection, render alternation, and
   effects intentionally redesigned for true 60 Hz.
2. **Legacy logical ordinal:** advances once per two physical gameplay cycles,
   equivalent to `physical >> 1` for a boot-time-only 60 FPS mode. Use it for
   authored-frame masks, modulo schedules, and whole-frame countdowns whose
   clean contract is wall-clock time.

This split must be applied per consumer. A blanket shift of every +0x194 read
would damage physical alternation; leaving every read physical doubles legacy
periodic work. Runtime traces should record the ordinal, consumer call count,
and visible or stateful output to classify each ambiguous parity site.

## Implementation blueprint

A safe experimental implementation should be one opt-in rendering.60_fps
configuration with internally atomic compensation, not a menu of partial
“speed fixes.”

1. Verify the exact clean ELF and ADV/BTL/ETC overlay identities.
2. Guard every complete clean word listed above.
3. Change the resident renderer threshold from two VBlanks to one.
4. Preserve the existing physical renderer ordinal and add a private logical
   30 Hz phase for proven legacy integer consumers.
5. Keep one-shot CCS binding/priming steps at their clean increment. Halve only
   classified recurring FUN_001BB210 automatic playback, retaining a per-scene
   carry for odd increments; the FUN_001B7520 0x0080 word is a steady-state
   diagnostic, not a safe global final patch. Preserve FUN_001BB5C0 absolute
   seeks and leave CCS 1.0 render weights unchanged.
6. Leave shared FUN_00306D30 clean. Hook the common post-composition point in
   FUN_0024C440 so the final +0x1AC factor, including +0x1B0/+0x1B4 paths, is
   multiplied by 0.5 exactly once.
7. Compensate literal battle timers and gate raw countdown/history operations
   on the logical phase; do not present the six-word producer port as final.
8. Halve the three common projectile factor states, audit reached
   class-specific +0x278 writes, and gate projectile integer phases separately.
9. Keep battle camera counters and authored envelopes on the logical phase;
   for smooth camera presentation, interpolate a separately preserved clean
   authoritative transform instead of retuning the clamped state machine.
10. Gate battle-stage integer phases and one-shot events; compensate simple
    visual deltas, and interpolate nonlinear moving-prop/fall transforms from
    an authoritative clean-rate state where constant substitution is unsafe.
11. Compensate battle-HUD CCS, pulse, and slide clocks independently; keep its
    reverse-frame cursor and state decisions logical or fractional.
12. Exercise the four Master/encounter port candidates separately, correlate
    each with its live consumer, and enable only the terms not already covered
    by periodic CCS or actor compensation; compensate traversal integrators as
    complete position/velocity systems rather than isolated constants.
13. Keep in-engine cinematic queues and script-derived integer durations on
    clean wall time, halve proven per-update displacement, and route their CCS
    playback through the classified periodic clock. Preserve cue/event ordering;
    do not route these scenes through the PSS policy.
14. Halve both paired ADV effect deltas at every nonzero producer, including
    slow-motion states and their object-dispatch copies; gate uncovered integer
    effect phases separately.
15. Compensate controller-local UI/menu deltas and easing, keep their integer
    delays logical, and accumulate 60 Hz input edges across any logical-phase
    UI update gate.
16. Double both core repeat-delay thresholds and filter sustained repeat to
    logical 30 Hz while preserving immediate changed-mask and edge publication.
17. Apply only the guarded overlay mappings required by the active overlay.
18. Use the project's existing injection/patch mechanism if runtime overlay
    writes are required; do not introduce a second patch pipeline.
19. Leave PSS decode/presentation, audio sample clocks, and vibration conversion
    unchanged unless runtime evidence identifies a specific defect.
20. Keep the feature experimental and disabled by default until the complete
    validation matrix passes.

Partial combinations are useful for diagnosis but must not be presented as a
working 60 FPS mode. In particular, the gate alone is expected to produce
double-speed gameplay, and a visually correct battle does not establish
correct Master Mode, cinematics, PSS playback, or UI timing.

## Runtime validation matrix

Use matched clean-30 and candidate-60 captures from the same savestate or
deterministic input start. Compare wall-clock timestamps and state transitions,
not only the displayed FPS counter.

| Area | Required observations | Acceptance condition |
| --- | --- | --- |
| Scheduler | VBlank count, scheduler ordinal, present cadence | One scheduler update per VBlank without stalls or runaway catch-up |
| Battle | Idle, movement, attack, hitstop, projectile, support, KO, timer | Same wall-clock animation and event timing; correct end states |
| Battle camera | Tracking, large clamped displacement, preset transition, stage edge, shake | Same authoritative endpoints and transition timing; smooth mode has stable interpolated transforms |
| Battle stage | Proximity blend, break/rebirth, fade, falling/moving prop, crane effects | Same state/event timing and endpoints; no missed or doubled contacts/effects |
| Battle HUD | Gauge entrance/value change, staggered pulse, reverse/exit | Same wall-clock state and cursor timing; pulse remains smooth and reverse does not finish early |
| Training | Recording playback, resets, dummy behavior, counters | Same deterministic sequence and wall-clock duration |
| Master traversal | Run, jump, camera, NPCs, transitions | Same distance and authored animation phase at matched timestamps |
| Encounters | Player/enemy approach, prompt, engagement transition | No double speed and no duplicated compensation |
| In-engine cinematic | Event queue, camera, actor animation, subtitles, cues | Same cue order, scene duration, final transforms, and audio sync |
| CCS/UI/effects | Menus, HUD, particles, fades, looping and sentinel states | No doubled cursor, truncated effect, or every-other-frame jitter |
| Front end/ETC | Title, mode select, options, save/load, transitions | Same wall-clock states and random-event order; compensated local motion beside CCS animation |
| PSS | Start, middle, near end, skip, natural end | Encoded-rate playback, stable A/V sync, clean return to gameplay |
| Input/rumble | Poll response, buffer windows, requested vs physical duration | No latency regression; rumble duration remains wall-clock correct |
| Persistence | Overlay reloads, mode changes, reset, save/load | Guarded patch applies exactly once and restores expected state |
| Performance | EE/GS frame time and speed percentage | Sustained full speed on the declared test configuration |

For animation comparison, record at least one stable transform, authored-frame
cursor, accumulator, event counter, and relevant audio/cue timestamp. The
minimum success criterion is equal wall-clock behavior, equal event ordering,
equal terminal state, and maintained audio sync. “It says 60 FPS” is not an
acceptance test.

## Evidence still needed

The remaining evidence should come from clean original NA2 v2.28,
CRC C0659AD1:

1. A battle savestate and deterministic P2M2 input covering idle, movement,
   attack, hitstop, and a terminal transition.
2. A Master Mode traversal capture with an identifiable start and endpoint.
3. An active player/enemy encounter capture through the mode transition.
4. Start, middle, and end captures of the same in-engine UJ or story cinematic.
5. Start and near-end captures of one long PSS movie, including audio.

For each capture, record the PCSX2 build, game CRC, scene or characters,
emulation speed, EE cycle-rate/skip settings, renderer, and any active patches.
A clean 30 Hz baseline and candidate 60 Hz run from the same starting state are
ideal.

These captures are needed for runtime proof, not for the static documentation.
No new video conversion, source-media extraction, or audio processing is
required to build the first guarded experimental patch.
