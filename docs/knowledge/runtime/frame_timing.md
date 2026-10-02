# Frame timing and clock domains

This document records how retail NA2 (`SLPS-25837`) relates engine updates to
display interrupts and output, which code reads or writes the pacing state,
and which independent clock each subsystem uses. The root wait, manager pass
and per-update order are owned by
[Task system](task_system.md#root-pacing-and-the-engine-gate) and
[Controller input](controller_input.md#ownership-initialization-and-update-order);
this document does not repeat them. Resident addresses are ELF runtime
addresses. BTL addresses are given as Ghidra address with the live address
(Ghidra + `0x40`) where it matters; conventions follow
[Retail game file identities](../game/files/file_identities.md#address-conventions).

## Research coverage

- **Assigned scope:** the relation between display interrupts, the pacing
  threshold and engine updates; display output mode and buffer flip cadence;
  every recovered writer and reader of the pacing threshold; direct readers of
  the engine update counter `+0x194`; a map of the game's independent clock
  domains with their owning documents; and presentation that starts on one
  clock and continues on another.
- **Exploration depth:** read-only GhidrAssist decompilation and instruction
  checks of `FUN_00107F80`, `FUN_00107340`, `FUN_001065A0`, `FUN_0014E808`,
  `FUN_00107590`, `FUN_001081B0`, `FUN_001083A0`, `FUN_00108490`,
  `FUN_00108CE0`, `FUN_001C13F0`, `FUN_001D0590`, `FUN_001057B0`,
  `FUN_0019B490`, `FUN_0019B4D0`, `FUN_001A0120`, `FUN_001B4C60`,
  `FUN_00300D70` and the counter readers listed below, plus the Ultimate Jutsu
  playback and soundtrack chain (`FUN_0035CF00`, `FUN_001CE8A0`,
  `FUN_001D5BE0`, `FUN_001D5D80`, `FUN_0035B740`). Byte scans covered the
  `jal FUN_00107560` encoding and every `lw rt,0x194(rs)` in the ELF, BTL and
  ETC.
- **Confirmed coverage:** four threshold writers and their values; the
  threshold readers; the absence of an update catch-up path; the per-update
  RCNT0 work-time snapshot; the boot display mode request and its
  `SetGsCrt` arguments; one buffer flip per engine update; the direct-load
  inventory of `+0x194` readers; whole-frame-only streamed CCS rates; the
  start and continuation clocks of the Ultimate Jutsu soundtrack.
- **Unresolved or untested:** `+0x194` reads through `lq`/`ld` or computed
  addresses; any reader of the RCNT0 snapshot at `+0x04`; the CRI-side meaning
  of the stream pause call `FUN_001363E0`; measured cadence on hardware.
- **Deliberate exclusions and overlap:** the wait loop, interrupt callback,
  manager traversal and engine gate `+0x192` belong to
  [Task system](task_system.md#manager-pass-and-ordering-boundary). Pad
  publication order belongs to [Controller input](controller_input.md).
  Packet rotation and GS environments belong to
  [Render submission](rendering/render_submission.md#display-and-draw-environments).
  Every subsystem clock in the domain map is owned by the linked document.
  `ADV.BIN` is excluded.
- **Evidence limitations:** static evidence only. Hardware meaning of the GS
  and timer register values is stated as an inference from the PS2 register
  layout. Static code shows the maximum update rate a threshold permits; it
  cannot show whether every update finishes within that budget.

## Update cadence

`FUN_00108CE0` is registered on EE interrupt channel 2
([Task system](task_system.md#root-pacing-and-the-engine-gate)).
**Inference, hardware convention:** channel 2 is the EE INTC VBLANK-start
cause, so the counter at context `+0x00` counts VBlank starts. On an NTSC
output that is about 59.94 per second.

The root releases one manager pass each time the counter reaches the
threshold at context `+0x01`, and `FUN_001081B0` clears the counter at the
start of that pass. With the retail threshold 2 the engine runs at most one
update per two VBlanks, nominally 29.97 updates per second.

**Observed: there is no catch-up.** The wait tests `count >= threshold` and the
next pass resets the count to zero. If an update takes longer than its budget,
the extra VBlanks are discarded: the following wait returns at once, and no
code runs additional updates or passes a larger elapsed time to consumers. A
slow update therefore slows the game rather than skipping simulation.

**Observed: per-update work time.** `FUN_001081B0` writes zero to RCNT0's
count register at its start, and `FUN_00108490` stores RCNT0's count to
halfword context `+0x04` when the engine gate `+0x192 & 7` is clear.
`FUN_00105FC0` configures counter 0 with `MODE=0x83`
([Startup](../game/startup.md#sdk-prelude)). **Inference:** mode `0x83`
counts horizontal blanks, so `+0x04` holds roughly the number of scan lines
spent between the start of an update and the end of its tail. No reader of
`+0x04` was found.

### Threshold writers

`FUN_00107560(context, value)` writes `+0x01` and clears `+0x00`. The scan for
`jal 0x00107560` finds exactly four resident sites and none in BTL or ETC.

| Call | Caller | Value | When |
| ---: | --- | --- | --- |
| `0x001080C0` | `FUN_00107F80` | 1 | Context initialization at boot. |
| `0x001E11C4` | `FUN_001E0EE0` (`MOTHER`) | 2, loaded by `li a1,2` at `0x001E11C0` (word `0x24050002`) | After the startup readiness barrier, before the outer mode loop. Every later front-end, battle and result screen runs at this value. |
| `0x00105A88` | `FUN_001057B0` (movie start) | 1 | After saving the current value through `FUN_00105DA0`. |
| `0x001054E8` | `FUN_00105320` (movie end) | saved value | Restores the value saved at movie start. |

The movie path is described in
[Disc files](../game/files/disc_files.md#pss-full-motion-video).

### Threshold readers

`FUN_00105DA0` returns context `+0x01`. Its two direct callers and the other
recovered readers are:

| Reader | Use |
| --- | --- |
| `FUN_001083A0` | The root wait comparison. |
| `FUN_001057B0` | Saves the value before forcing 1 for a movie. |
| `FUN_00113B80` | Subtracts it from each active vibration duration once per update, so vibration ages in VBlank units at any threshold ([Controller input](controller_input.md#vibration-and-actuator-scheduling)). |
| BTL `ccCommand` constructor, Ghidra `FUN_006EF5C0` | Sizes the input history as `300 / threshold` records when the object is constructed ([Action commands](../gameplay/combat/action_commands.md#battle-input-object-and-circular-history)). |
| `FUN_0019B4D0`, `FUN_0019BB00` | Multiply pad-driven rotation and movement and a hold counter by the threshold. Their only caller, `FUN_0019B490`, runs inside streamed play worker `FUN_001A0120` when the request flags have `0x60` set and `0x100` clear and the container has `+0xA4 & 1`. The same branch reads raw pad words at context `+0x80/+0x84/+0xF8/+0xFC` and lets pad input change container rate `+0x9C` in steps of `0x40`. It is a pad-controlled scene viewer, not a battle or front-end consumer; which retail requests enable it is unresolved. |

## Display output and buffer flip

**Observed.** `FUN_00107F80` calls `FUN_00107340(context, 0x200, 0x1C0, 0)`,
requesting a 512 by 448 display with mode byte `+0x2AC = 0`. `FUN_001065A0`
then sets byte `+0x03 = 1` because the height is above `0x100`, sets
`+0x2AE = 0` because `+0x2AC` is zero, and calls
`FUN_0014E808(0, +0x03, 2, +0x2AE)`. That routine resets the GS and calls
`SetGsCrt(+0x03 & 1, 2, +0x2AE & 1)`, so retail requests
`SetGsCrt(1, 2, 0)`. The movie path calls `FUN_00107340` with the movie's own
dimensions before playback.

**Inference, GS register convention:** the arguments select interlaced NTSC
output in field mode, where each field displays alternate lines of one
448-line frame buffer.

Each engine update flips once: `FUN_001081B0` calls
`FUN_00107590(context, selector ^ 1)`, which writes `DISPFB1`/`DISPLAY1` for
the other buffer and records GS CSR field bit 13 at `+0x1B8`
([Render submission](rendering/render_submission.md#display-and-draw-environments)).
**Inference:** at threshold 2 every rendered image stays on screen for two
consecutive fields, so both its even and odd lines are shown. At threshold 1
each field would come from a different update.

## Engine update counter readers

Context word `+0x194` is incremented once per update by `FUN_001081B0`. A
byte scan for every `lw rt,0x194(rs)` in the ELF, BTL and ETC, with each hit
checked for the system-context base, finds the readers below. Reads through
`lq`/`ld` or a computed address are not covered. BTL hits at Ghidra
`0x006D6990`, `0x006D9778`, `0x006D97A0`, `0x006DDED0` and `0x006DDEE0`
belong to other objects.

| Binary | Site | Function | Use |
| --- | ---: | --- | --- |
| ELF | `0x001079D0` | `FUN_001079C0` | Selects the master-chain template by `+0x194 & 1` ([Render submission](rendering/render_submission.md#frame-chain-and-vif1-submission)). |
| ELF | `0x001E11A4` | `FUN_001E0EE0` | Seeds random state ([Randomness](randomness.md#coordinated-initialization-and-reseeding)). The read precedes the threshold write at `0x001E11C4`. |
| ELF | `0x0024CBD4` | `FUN_0024C440` | Practice refill runs only when `+0x194 & 0x1F == 0` ([Practice mode](../gameplay/modes/practice_mode.md#continuous-fighter-policy)). |
| ELF | `0x00300E0C` | `FUN_00300D70`, the `ccPl93Track` trail of character ID 93 | Emits a trail sample when `+0x194 % d == 0`, where `d = int(1 / fighter+0x1AC)` clamped to `1..10` (`d = 1` when the factor is below `0.01`). |
| BTL | Ghidra `0x006E8CBC`, `0x006E8EE0`, `0x006E93CC` | Row draws Ghidra `0x006E8C10`/`FUN_006E9320` and list draw Ghidra `0x006E8E90`, on the `spbattle` ranking and record screens | Triangular highlight pulse: `u = (+0x194 & 0x1F) * 0x100`, folded to `0x2000 - u` above `0x1000`; one cycle every 32 updates. |
| BTL | Ghidra `0x00721004` | Track renderer Ghidra `0x00720F90` | Uses `+0x194 & 1` to swap two pass weights (`0.98` and `0.02`) between the two passes of one draw. |
| BTL | Ghidra `0x00722D50` (live `0x00722D90`) | Counter helper called from resident character callbacks at `0x002DF314`, `0x002E2414` (ID 78), `0x002E807C` (80), `0x002EBC04` (82), `0x002FCB44` (91), `0x002FEFB4` (92) and `0x003030CC` (93) | Adds its second argument to a signed halfword counter only when the stored update value differs from `+0x194`, then stores `+0x194`; repeated calls in one update count once. This is the guard used by [Kiba's response-count exit](../gameplay/characters/character_action_callbacks.md#kibas-response-count-exit). |
| BTL | Ghidra `0x00722E88` (`FUN_00722E50`, live `0x00722E90`) | Called from `FUN_003005A0` at `0x0030060C` for timers at fighter `+0x61C8 + 0xC*i` (character ID 93) | Decrements a signed halfword counter once per new `+0x194` value; below zero it releases an attached effect. Value `-999` disables the countdown. |
| BTL | Ghidra `0x0081F950`, `0x008626A0` | Skill actor Ghidra `0x0081F650` and `FUN_00862360` (`ccSkillKIW001`) | When per-update travel is below `20.0`, spawn an afterimage effect only on odd `+0x194`; otherwise spawn by distance travelled. |
| ETC | none | | |

## Clock domains

Each row is an independent unit of time. Converting between rows requires the
owner's contract; none of them reads elapsed wall time except the kernel delay
and the media decoders.

| Domain | Unit and advance | Owner |
| --- | --- | --- |
| VBlank count | Context `+0x00`, one per VBlank start | [Task system](task_system.md#root-pacing-and-the-engine-gate) |
| Engine update | Context `+0x194`, one per manager pass | [Task system](task_system.md#manager-pass-and-ordering-boundary) |
| Task wait | `FUN_001D0000`/`FUN_001D0340` counts of manager wakes | [Task system](task_system.md#wait-and-wake-semantics) |
| Pad publication and repeat | One publication per update; repeat after 15 unchanged updates | [Controller input](controller_input.md#held-edges-and-repeat) |
| Vibration | 60 Hz ticks, aged by the threshold per update | [Controller input](controller_input.md#vibration-and-actuator-scheduling) |
| Fractional timer block | Caller-supplied float delta per call | [Timer primitives](timer_primitives.md#fractional-integer-cursor-block) |
| Fixed-point countdown | `0x00044444` (2^24/60) per eligible call | [Timer primitives](timer_primitives.md#fixed-point-remainingelapsed-block) |
| Scene playback | 8.8 increment per advance, 256 = one authored frame | [Animation runtime](animation_runtime.md#advance-and-end-behavior) |
| Streamed CCS playback | Signed 8.8 container rate `+0x9C` per worker cycle | [CCS runtime](../game/files/ccs_runtime.md#the-play-task), [Scene playback owners](scene_playback_owners.md#streamed-worker-scheduling) |
| Effect generator | Whole list passes per requested iteration | [Effect generator commands](effect_generator_commands.md#scheduling-and-owner-gates) |
| Particle emission | `rate / 30.0` accumulated per manager update | [Particle runtime](rendering/particle_runtime.md#emission-particle-lifetime-and-update-ordering) |
| Kernel delay | RCNT2 alarm, wall-clock units | [Kernel threads and synchronization](kernel_threads_and_sync.md#alarm-backed-delay-semaphore) |
| Movies | MPEG timestamps and audio hardware | [Disc files](../game/files/disc_files.md#pss-full-motion-video) |
| Audio samples | SPU2 sample rate of each stream; commands sent from tasks | [Audio and video replacement](../game/files/audio_video_replacement.md#observed-stream-contract), [Battle audio](../gameplay/session/battle_audio.md#transport-and-stream-poll-scheduling) |

Gameplay and presentation code built on the per-call domains (fractional
timers, fixed-point countdowns, scene playback, generator passes, particle
emission, integer counters and recursive approaches) advances once per call.
Its wall-clock rate is the call rate times the per-call amount. Audio sample
playback and movie decoding do not follow the call rate.

### Streamed CCS rate is whole-frame only

**Observed.** `FUN_001B4C60` advances a streamed container by adding signed
halfword rate `+0x9C` to accumulator `+0x9E`. It takes the whole-frame step as
`sign_extend16(sum) >> 8`, then stores the remainder as a sign-extended low
byte (`dsll32/dsra32 ...,0x18` at `0x001B4D70/0x001B4D74`). The fraction is
therefore not carried as an unsigned 1/256 remainder:

| Rate | Successive whole-frame steps |
| ---: | --- |
| `0x100` | 1, 1, 1, ... |
| `0x80` | 0, 0, 0, ... (remainder alternates `-0x80` and `0`) |
| `0x40` | 0, 0, -1, 0, ... |

Only whole multiples of `0x100` advance as a frame rate. The default `0x100`
is written by container initialization `FUN_001AA7C0` at `0x001AA7E4`.
Whenever `+0x9C` is not exactly `0x100`, each frame parse first calls
`FUN_001A1F40(0.0, ...)` (`0x001B4CC0`, `0x001B4E14`, `0x001B4F20`), which
clears the inherited alpha of the container's `0x0E00` and `0x0100` objects.
The play worker also passes raw `+0x9C` to `FUN_001ABC70`, so `0x100` means
256 generator passes per step
([Effect generator commands](effect_generator_commands.md#scheduling-and-owner-gates)).

## Couplings between clock domains

Some presentation is started on one clock and continues on another. These
couplings hold only while the starting clock keeps its retail rate.

| Coupling | Start | Continuation |
| --- | --- | --- |
| Ultimate Jutsu soundtrack | `FUN_001CE8A0` calls `FUN_001D94F0(skill)`, which opens the skill's stereo stream on slot 1 paused (`FUN_001D6CF0(..., paused=1)` via jump-table case `0x001D3C08`). Task `SND_RPC` unpauses it through `FUN_001D5D80` when the play container's frame `+0x90` (`FUN_0035DA70`) equals 1. | The stream plays in real time on the sound side. No later code compares stream position with the cinematic frame. When the stream ends, `FUN_001D5F10` stops slot 1 and restarts the battle music. |
| Ultimate Jutsu cinematic frames | Streamed play task `FUN_001A0120`, one step per manager wake through `FUN_001D0000(task, 1)` at `0x001A070C`. | Damage, sound-effect cues and camera rows fire on equality with frame `+0x90` in `FUN_0035B740`, so they follow the cinematic frame, not the stream. |
| Ultimate Jutsu intro voice | Presentation state 0 (BTL live `0x00769F30`) starts a mono voice and stops the battle music. | The presentation's countdowns, counted in engine updates, decide when later states start and when state 3 stops the voice. |
| Movies | Movie start forces threshold 1 ([threshold writers](#threshold-writers)). | Video and audio follow MPEG timestamps and the audio hardware ([Disc files](../game/files/disc_files.md#pss-full-motion-video)). |

The same play path is used by the ETC Collection viewer (`FUN_006C0AB0` calls
`FUN_0035CF00`).
