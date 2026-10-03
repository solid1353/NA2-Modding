# 60 FPS

Design research for a 60 FPS battle mode in Narutimate Accel v2.28: the game
runs 60 real updates per second, every displayed frame is a real game state,
and every system keeps its retail wall-clock behaviour. Nothing here is
implemented in that form. The document explains why the one-word frame-rate
unlock breaks battle speed, animation, logic and audio sync, sets out the
design, and lists every known consumer an implementation has to handle, with
its code sites.

Retail pacing, display output, frame-counter readers and clock domains are
owned by [Frame timing](../../knowledge/runtime/frame_timing.md). The failed
PNACH attempt, its runtime measurements and its patch ledger are recorded in
[the attempt record](../../../experiments/60-fps/attempt.md).

## Research coverage

- **Assigned scope:** what a correct 60 FPS battle mode must preserve; why
  changing the pacing threshold alone breaks battle; the 60 Hz simulation
  design and the decisions it requires; every known battle consumer of the
  update rate with its retail clock, code sites and treatment; audio and
  cinematic sync; input; RNG; performance and display; validation; open
  questions.
- **Exploration depth:** read-only GhidrAssist reads of the battle
  dispatcher `FUN_001F03E0` and its callers, the fighter update path
  (`FUN_0024FD80`, `FUN_0024C440`, `FUN_0024DA50`, `FUN_0024D1C0`,
  `FUN_0024D5E0`, `FUN_0024DE40`, `FUN_0024A660`, `FUN_002183D0`), the BTL AI
  tick, the input pipeline and its record windows, the jutsu clash, the
  Ultimate Jutsu playback, presentation, contest and soundtrack chain, the
  streamed play task `FUN_001A0120` and `FUN_001B4C60`, projectiles, cameras,
  HUD, stage objects, particles, recurring scene players, the end-sequence
  waits, the battle start menu and Practice menu, all direct readers of the
  frame counter, and every fighter read of `+0x1AC` found by byte scan. Each
  site in the tables below was read at instruction
  level unless marked otherwise. The knowledge documents linked in each row
  were used as the starting map.
- **Confirmed coverage:** the mechanism of every failure class reported for
  the unlocked build; the exact clean words of the sites listed; which
  consumers halving the fighter factor fixes, misses or breaks; the exact
  integrator error of half-steps; the whole-frame restriction of streamed CCS
  rates; the Ultimate Jutsu soundtrack coupling; the call sites of the battle
  dispatcher.
- **Unresolved or untested:** no part of this design has been run. A few
  second-pass callees and per-character draw callbacks are not classified,
  and some fighter-factor fixes are inferred. Frame-time headroom and the look
  of interlaced output at 60 images per second are open. See
  [Open questions](#open-questions).
- **Deliberate exclusions and overlap:** retail contracts belong to the
  linked knowledge documents; this document repeats only the facts a 60 FPS
  design depends on. `ADV.BIN` (Adventure, part of Master Mode) is out of
  scope. Front-end screens are covered only by the recommendation to keep
  them at the retail rate. Movies are excluded because retail already plays
  them on their own clock.
- **Evidence limitations:** static reads establish what each site does per
  call, not how often it is reached in a real match or how long an update
  takes. Runtime evidence comes only from the PNACH attempt, which used the
  NA228 build and one Practice recording. Sites marked inferred need runtime
  confirmation before they are relied on.

Addresses are resident ELF addresses unless marked BTL. BTL sites are given
as live addresses (Ghidra + `0x40`) unless written "Ghidra". `jal` targets and
pointers stored in BTL are live addresses. Address conventions are in
[Retail game file identities](../../knowledge/game/files/file_identities.md#address-conventions).

## Goal

1. **Real 60 Hz.** The battle simulation runs 60 updates per second. Every
   displayed frame is a game state the logic actually reached; no frame is
   synthesized between states.
2. **No added input lag.** Input is published every update, so a press can
   take effect one 60 Hz update after it happens.
3. **Retail speed.** Every gameplay, animation, camera, effect, HUD and
   cinematic element keeps its retail wall-clock rate.
4. **Retail battle logic.** Damage, windows, cooldowns, AI behaviour and
   outcomes keep their retail wall-clock values. Exact retail RNG order is not
   achievable once events can land on any 60 Hz update; per-second draw rates
   and per-event probabilities must match.
5. **Audio sync.** Battle music, the Ultimate Jutsu soundtrack, voices and
   sound cues stay aligned with what is on screen.

## Why the one-word unlock breaks battle

`MOTHER` sets the pacing threshold to 2 with `li a1,2` at `0x001E11C0`
(word `0x24050002`) before the mode loop. Changing it to 1 makes the root
release one engine update per VBlank instead of one per two
([threshold writers](../../knowledge/runtime/frame_timing.md#threshold-writers)).
That doubles everything that advances once per update or once per task wake,
which is nearly every clock in the game
([clock domains](../../knowledge/runtime/frame_timing.md#clock-domains)).
Only vibration (aged by the threshold itself) and movies (own clock) are
unaffected.

| Symptom in the unlocked build | Cause |
| --- | --- |
| Battle runs at double speed: movement, animation, hitstop, combo window, round clock | Fighter animation advances `speed * factor` per update; timers subtract a per-call delta; the round clock adds `0x00044444` per eligible update. |
| Animations look wrong, not just fast | Fighter scenes, stage props, HUD players and effects each own a separate per-call clock; there is no single animation speed. |
| Ultimate Jutsu visuals run twice as fast as its music | The cinematic advances one frame per play-task wake; its soundtrack is one real-time stream unpaused at cinematic frame 1 and never re-synced ([coupling](../../knowledge/runtime/frame_timing.md#couplings-between-clock-domains)). |
| Ultimate Jutsu intro voice and HUD timing drift | The presentation state machine counts engine updates (150/130/100/85/30/12). |
| Inputs feel wrong, combos and specials fail | Every battle input window is counted in history records or updates and halves in wall time; repeat speed doubles; mash contests change balance. |
| AI behaves differently | AI timers and per-tick probability rolls run twice as often. |
| Different random outcomes | Per-update RNG draws double. |

The attempt record measured this directly: with only the threshold changed,
recorded actions occur early and the match diverges
([gate-only failure](../../../experiments/60-fps/attempt.md#gate-only-failure)).

## Design

Run every battle update at 60 Hz and make each consumer advance, per update,
half of what it advanced per retail update. Each consumer gets exactly one of
two treatments:

- **Convert.** Change its per-call amount so that two updates equal one retail
  update: halve float deltas and rates, double integer durations and
  thresholds, convert recursive coefficients. Continuous motion, animation and
  fades become genuinely 60 Hz. This is the default.
- **Half rate.** Run the consumer on every other update only, with its retail
  amounts. Use this only where conversion is impossible or changes the result:
  integer schedules tested by equality, streamed playback that cannot take a
  half rate, recursive systems with clamps, and per-tick random rolls. A
  half-rate owner still draws on every update.

The [catalogue](#compensation-catalogue) assigns a treatment to each consumer.
A consumer must never get both: halving a fighter-factor clock and also
running its owner at half rate makes it run at quarter speed, as the PNACH
attempt found.

### Rejected: 30 Hz logic with interpolated frames

Running the game logic on every other update and drawing positions, poses and
cameras halfway between the last two states would keep retail logic for free,
but it is unsuitable for a fighting game. It needs the next state before it can
draw the in-between frame, so everything appears one retail update (about
33 ms) late. The in-between frames show positions that hit detection never
used. The game would still decide everything at 30 Hz. Half-rate running is
therefore kept only as a per-owner tool, not as the frame-rate design.

### Decisions the design requires

| Problem | Decision |
| --- | --- |
| Gravity with half steps lands jumps lower by `K*n/4` after `n` retail frames ([movement](#movement-and-physics)) | Apply gravity on every other update with its retail amount, so position and velocity match retail at every retail-frame boundary and the in-between position is a true midpoint |
| Consumers that already use the fighter factor break when it is 0.5 ([list](#consumers-broken-by-halving-the-factor)) | Fix each site to use the unhalved rate or a doubled count, as listed |
| Proportional approaches with a factor-scaled gain converge slightly slower when halved | Convert the gain to `1 - sqrt(1 - min(1, 2k))` at each call site |
| Odd animation rates lose 1/256 frame per retail frame when halved ([animation](#animation-increments)) | Keep a one-bit carry per scene |
| Per-update random rolls double ([RNG](#rng)) | Run each per-tick roller at half rate, keeping the per-second draw rate and probabilities |
| Input windows halve ([input windows](#input-windows)) | Keep publication at 60 Hz and double every record and update window |
| The Ultimate Jutsu cinematic cannot take a half rate ([Ultimate Jutsu](#ultimate-jutsu-and-audio-sync)) | Advance it at half rate; draw it every update |

## Shared mechanics

### Scoping the threshold change

Two scopes are possible:

- **Battle only (recommended).** Write threshold 1 through the live setter
  `FUN_00107560` when a battle starts and restore 2 when it ends, the way the
  movie path saves and restores it. Front-end screens keep retail timing with
  no further work. The attempt found that patching the initializer word after
  boot has no effect; a runtime switch must call the setter.
- **Boot-wide.** Patch `0x001E11C0`. Every front-end task, ETC overlay screen
  and transition then needs the same treatment as battle.

The battle scope is the session's lifetime: session global `0x00607604` is
published by `FUN_001EC3B0` in outer state 14 and cleared after
`FUN_001EECD0` in state `0x10` (or `0x17`/`0x18` for continuations)
([Battle lifecycle](../../knowledge/gameplay/session/battle_lifecycle.md#session-construction)).
A check at the start of every engine update can set threshold 1 while the
session exists and 2 otherwise, through the live setter. Continuations
rebuild the session and need no separate case. Everything that runs while the
session exists needs compensation, including the intro, KO and result
sequences ([end sequence](#end-sequence-and-transitions)).

The battle `ccCommand` constructor sizes its history as `300 / threshold`
records (BTL Ghidra `0x006EF5C0`, `li v0,0x12C` at Ghidra `0x006EF61C`). It
runs inside the same call that publishes the session, before a per-update
check can see the session, so the threshold is still 2 there. Changing the
constant to `0x258` gives 300 records, the retail five-second span at 60 Hz.
Matcher windows reach at most 31 retail records (62 doubled), so capacity
never limits matching.

### Half-rate phase

Half-rate owners need one phase bit, toggled once per engine update and
stored in the resident payload. It is the same for every owner, so half-rate
owners keep their retail order relative to each other. The attempt used
`context+0x194 & 1`; a private bit avoids depending on the counter's parity at
battle start. A half-rate owner is reached through a gate stub that checks the
bit and either calls the native target or returns.

### Input

`FUN_00113710` publishes held, pressed, released and repeat once per update
([Controller input](../../knowledge/runtime/controller_input.md#held-edges-and-repeat)).
At 60 updates per second a press exists for exactly one publication, and the
battle input history gains one record per update. Publication stays at 60 Hz;
every window, repeat delay and mash counter downstream is doubled
([input windows](#input-windows)).

Readers of the shared pad words bypass battle history: the start-menu detector
`FUN_001EBC50`, the BTL start menu, the Practice settings input, the generic
list `FUN_003832C0 -> FUN_00383340`, the three binding-1 predicates (BTL live
`0x00796A50`, `0x007FF520`, `0x00806680`), the Ultimate Jutsu contests, and
the jutsu clash. The clash driver reads the core pressed word directly (BTL
Ghidra `0x0077C498..0x0077C4D0`: `lw ctx,-0x35F4(gp)`, `+side*0x78`,
`lw +0x84`, mask `+0xB50`, then `+0xA7A[side]++`), not the ccCommand history.

Vibration needs no change: it ages by the threshold value per update
([Controller input](../../knowledge/runtime/controller_input.md#vibration-and-actuator-scheduling)).

### RNG

Per-update draws from the shared generator in battle:

- `FUN_0024C440` stores one raw MT word to fighter `+0x88` on every update,
  unconditionally (`jal FUN_001801E0` at `0x0024CA0C`, store at
  `0x0024CA14`); substitution later uses it.
- The BTL AI tick and the clash AI (BTL live `0x006FFD50`) draw per tick.
- `FUN_00224660` hitstop jitter makes two draws per update while hitstop is
  active.
- Combo-digit shake makes two draws per call (BTL live `0x006B6E90`).
- Particle spawns, stage cooldown re-arms, grass sway (`FUN_00397BC0`) and the
  per-element angular jitter `FUN_00393BD0` draw per spawn or per call.

Each is run at half rate, which keeps per-second draw counts and per-tick
probabilities. Event draws (hits, spawns, choices) happen when their event
does. A visual that should become truly 60 Hz and needs randomness must use a
private generator, or it moves gameplay RNG. The seed read at `0x001E11A4`
happens before the threshold write and is unaffected
([Randomness](../../knowledge/runtime/randomness.md#coordinated-initialization-and-reseeding)).

### Frame-time budget

There is no catch-up: an update that overruns its VBlank delays the next one
and the game slows down
([update cadence](../../knowledge/runtime/frame_timing.md#update-cadence)).
Every update now carries a full retail update's work in 16.7 ms instead of
33.4 ms. This is a hard prerequisite. Measure it with the per-update RCNT0
snapshot at context `+0x04` (horizontal blanks, about 262 per NTSC field). On
PCSX2 the EE cycle rate setting can hide an overrun; an overrun must not be
mistaken for a timing bug.

### Display

Retail requests interlaced NTSC field output from a 448-line buffer and flips
once per update, so each image is shown in both fields
([display output](../../knowledge/runtime/frame_timing.md#display-output-and-buffer-flip)).
At one flip per VBlank each field shows alternate lines of a different image.
**Inference:** fast motion will show interlace combing unless the emulator
deinterlaces or the output is changed to frame mode. The visual result has not
been checked.

## Compensation catalogue

"Half rate" in the tables means running that owner on every other update. The
conversion rule for float constants: subtract `0x00800000` from the bits, so
for a `lui`/`ori` pair only the `lui` immediate changes by `-0x80`. A recursive
approach `x += (t - x) * k` needs `k' = 1 - sqrt(1 - k)` for two steps to equal
one, and is exact only for a fixed target and no clamp. A multiplicative decay
`x *= d` needs `d' = sqrt(d)`. A linear slide `offset += v; v -= a` from `v0`
matches at every other step with `a' = a/4` and `v0' = (v0 + a/4)/2`.

| `k` | `k'` | Float bits |
| ---: | ---: | --- |
| 0.1 | 0.0513167 | `0x3D523176` |
| 0.125 | 0.0645857 | `0x3D84457C` |
| 0.2 | 0.1055728 | `0x3DD8368F` |
| 0.25 | 0.1339746 | `0x3E0930A3` |
| 0.3 | 0.1633400 | `0x3E274298` |
| 0.4 | 0.2254033 | `0x3E66D021` |

### Fighter factor

`FUN_0024C440` composes fighter factor `+0x1AC` from override `+0x1B0` or
`FUN_00306D30`, times `+0x1B4`
([Hit response](../../knowledge/gameplay/combat/hit_response.md#timed-downed-recovery)).
Halving it in the composition window `0x0024C4A0..0x0024C4CC` is the correct
place: it covers every override path and leaves `FUN_00306D30` (shared with
`FUN_00235510`) unchanged. The attempt's seven-word rewrite is in its
[actor-factor section](../../../experiments/60-fps/attempt.md#exact-six-word-community-port-diagnostic-only)
and was runtime-verified for all composition branches. Do not use the six-word
`FUN_00306D30` port: it also halves `FUN_00235510`'s downed thresholds.

Halving the factor converts the fighter animation increment (`FUN_0024D1C0`),
the primary and secondary action clocks `+0x1B8/+0x1DC`, the action lock and
timers `+0x248/+0x26C/+0x290`, displacement, x-dash and throw phases, puppet
steps and cue timing. Gravity needs the half-rate rule under
[movement](#movement-and-physics). Nothing below is covered by the factor.

### Fighter maintenance

All sites in `FUN_0024C440` unless noted.

| Field or work | Site | Retail per call | Treatment |
| --- | --- | --- | --- |
| Chakra reservation window `+0x82` | `0x0024C5B0..0x0024C5B8`, conditional, releases through `FUN_002260D0` | −1 | Half rate |
| Position ring `+0x8C0`/`+0x840` | `0x0024C5DC..0x0024C608` | One sample, 8 entries | Half rate. Both recovered readers of `FUN_00224420` use the latest sample only |
| Hold/release synthesis `FUN_0024CDA0` | `0x0024C610` | `+0xB40` ±1, `+0xB44`, `+0xB48`, `+0xB4E` +1 | Double the per-character constants loaded by `FUN_00247DC0`, or half rate |
| Multi-press counter `FUN_0024CCD0` | `0x0024C61C` | `+0xB54` +1; window `+0xB52` | See [input windows](#input-windows) |
| KO recovery timer | `FUN_00225330` arms `+0x230 = 60` | literal | Double |
| X-dash cooldown `+0x9C0`, lockout `+0x84`, voice cooldown `+0x19A`, chakra-shortage sound `+0x19C`, `+0x954` (unknown), item cooldown `+0xB72` | `0x0024C740..0x0024C7B4` | −1 each | Half rate |
| Hit-rejection countdown `+0x224` | `0x0024C904`, `mov.s f12,f20` (clean `0x4600A306`); `f20 = 1.0` is also compared at `0x0024C47C` | 1.0 | 0.5 through a stub; no one-word change |
| Hitstop `+0x200` (count `+0x20C`) | `0x0024CA68` (clean `0x3C023F80`) | 1.0 | `0x3C023F00`; **inferred** to resume 1/60 s early, because activation consumes one call |
| Fighter RNG word `+0x88` | `0x0024CA0C` | One MT draw | Half rate |
| Grounded count `+0xB9A` | `FUN_0024A660` | +1 | Half rate; `FUN_00224970` tests `> 4` |
| Practice refill | `0x0024CBD4` | `+0x194 & 0x1F` | See [frame-counter consumers](#frame-counter-consumers) |
| Combo window | `FUN_0020C420`, `0x0020C4E8` (clean `0x3C023F80`) | 1.0, armed 90 | `0x3C023F00` |
| Sustained chakra charge | `FUN_00227EE0`, `0x00228084` (clean `0x3C023D4C`) | `+0x164 * 0.05 * rate` | `0x3C023CCC` (0.025, keeps `ori 0x3442CCCD`) |
| Input-duration `+0x98A`, guard age `+0x95C` | `FUN_002173D0`; `0x0024DB30..0x0024DB64` | +1 | Double thresholds, or half rate |
| Grounded-count statistic `+0x548` | `FUN_0024D5E0`, `0x0024D6F8..0x0024D80C` | +1, cap 9999 | Half rate |
| Late input ring `+0x4C4`/`+0x344` | `FUN_0024DE40`, `0x0024E020..0x0024E064` | One record, 32 entries | Keep at 60 Hz and double the window: recovery inputs check the last 5 records (10) |
| Visual timers `FUN_00226370` | second pass, `0x0024DD94` | literal | Half rate (attempt runtime-verified) |
| Scale envelope `FUN_0024D3C0` | first pass | literal | Halve the deltas, or half rate |
| Auxiliary scene `+0xB30` | `FUN_0024DA50`, `jal FUN_001BB210` at `0x0024DC74` | scene `+0x94` | Halve the increment with carry; its lifetime `+0x1C` in `FUN_002091B0` at half rate |
| Flight acceleration `FUN_0020EAE0` | first pass | table literal | Halve |
| Support gauge `FUN_00238340`, `FUN_00238540` | first pass | `recharge/450`, `1/300` | Halve (support is off in Practice) |
| Overlap push `FUN_002222F0`, `FUN_00221600` | first pass | Added unscaled through `+0x4E0` | Halve |
| Status-effect countdown `FUN_00304D60` | `0x00304D9C` via `FUN_003059B0` at `0x0024C4E8` | −1, plus `floor(3n/2)` for mashing | Half rate |
| Item lanes `FUN_00306090`, `FUN_00306220` | via `FUN_003059B0` | literal per update | Halve |

### Consumers broken by halving the factor

These already multiply by `+0x1AC` or compare against it, and give a wrong
result when it is 0.5:

| Site | Retail | At factor 0.5 | Fix |
| --- | --- | --- | --- |
| Attack-window registration `FUN_0021FC70` (`0x0024DFD0`) | Branches on scene rate `trunc(+0xB90 * f)`: above `0x100` uses a `1.9` crossing test, below uses integer frame bounds | Rates `0x101..0x200` drop to the other branch; `0x100` becomes `0x80` and changes test | Branch on the unhalved rate |
| Extra Hit window `FUN_00239250` (`0x00239394`) | `+0xB0A * rate / 256` frames | Window lasts half as long | Double the window |
| Extra Hit wait `FUN_00241A50` (`0x00241C64`) | Opponent `+0x1C4 >= 7 * opponent +0x1AC` | Reached in 7 calls instead of 14 | Use the unhalved factor |
| Rejection staging `FUN_002346B0` (`0x00234B78/94/A4`) | `+0x230 = base * (2 - r)` when `r != 1` | 1.5× base | Use the unhalved factor |
| Boosted-state tests `FUN_002B7D10`, `FUN_00221600` | `+0x1AC > 1` | Lose the branch | Compare against 0.5 |
| AI reach predictors `FUN_002185C0`, `FUN_00218810`, `FUN_002189D0` | Sum speed per simulated step without the factor, gravity with it | Predicted jump reach about doubles | Use the unhalved factor in the prediction |
| Hitstop jitter `FUN_00224660` | Amplitude scaled only when `f < 1` | Amplitude halves (visual only) | Use the unhalved factor |

The complete scan of fighter `+0x1AC` reads is summarized in
[Combat action execution](../../knowledge/gameplay/combat/combat_action_execution.md#readers-and-writers-of-the-update-delta).
Its non-rate readers need these changes. A one-shot amount computed from the
factor must use twice the halved factor, which restores the retail amount
exactly, slow-motion overrides included.

| Site | Use | Change |
| --- | --- | --- |
| `0x0022A400` | One approach, `k = 0.5 * f` | `3C023F00` → `3C023F80` |
| `0x0022A64C` | `k = min(1, 1.25 * f)` snap | `3C023FA0` → `3C024020` (exact at factor 1; slow motion converges slightly fast) |
| `0x0023B854` | One approach, `k = 0.5 * f` | `3C023F00` → `3C023F80` |
| `0x0023DC90`, `0x0023DD2C` | One approach each, `k = 0.75 * f` | `3C023F40` → `3C023FC0` |
| `0x0024641C` | One approach, `k = 0.5 * f` | `3C023F00` → `3C023F80` |
| `0x00246BF0` | One approach, `k = +0xF4 * c * f` | `nop` → `add.s f21,f21,f21` (`4615AD40`); the following clamp keeps `k <= 1` |
| `0x0026EBB4` | ID 22 repeat count by `f == 1` / `> 1` | `3C033F80` → `3C033F00` (**inferred** that its hits follow the action clock) |
| `0x002870F8` | ID 51 scene advance skipped while `f <= 0.1` | `3C023DCC` → `3C023D4C` |
| `0x0029720C`, `0x002972E0` | ID 57 selections by `f > 1` | `3C023F80` → `3C023F00` |
| `0x002CB594`, `0x002CB5B8` (delay slots) | ID 71 copies the opponent's speed times the opponent's factor | `add.s f12,f12,f12` (`460C6300`) (**inferred**) |
| `0x002DD4F8` | ID 78 pull term multiplied by `f` twice | Double the `0.7` gain and the `30.0` clamp (`lui 0x41F0` at `0x002DD490`); the gain's register source is not located |
| `0x002E7D48` | ID 80 one-shot `+0x994 += 25 * f` | `3C0241C8` → `3C024248` |
| `0x00603D20`, `0x00603D24` | ID 80 thresholds for `u16(+0xB90) * f` | `01000080` → `00800040`, `00000120` → `00000090` |
| `0x002FF19C`, `0x002FF530` | ID 92 test `u16(+0xB90) * f < 128` | `3C024300` → `3C024280` |
| `0x002FF5A0`, `0x002FF5C8`, `0x002FF5F0` (delay slots) | ID 92 one-shot receiver values times `f` | `4616B580`, `4615AD40`, `4614A500` (`add.s` doubling; **inferred**) |
| `0x00604148`, `0x0060414C` | ID 93 thresholds for `u16(+0xB90) * f` | `01000080` → `00800040`, `00000120` → `00000090` |
| `0x003032BC` | ID 93 `min(2f - 1, 1)` | `nop` → `add.s f0,f0,f0` (`46000000`) |
| BTL D `0x008099C0`, `0x0080999C` | Counter compared with `30 * f`, fallback 1.0 | `30.0` → `120.0` (`lui 0x42F0`); fallback `0x3F00` |
| BTL D `0x0081BCB0`/`0x0081BC88`, `0x0081C2A0`/`0x0081C278`, `0x0081C57C`/`0x0081C554` | `FUN_0081BB70` steps by `1 / f`, fallback 1.0 | Numerator `lui 0x3E80` (0.25); fallback `lui 0x3F00` |

The BTL owner-absent fallbacks of 1.0 at D `0x007AC618`, `0x0080B3B8`,
`0x0080DAE0`, `0x00824680`, `0x00826E88` and `0x008274D8`, and the literal 1.0
at D `0x00811AE4`, become 0.5.

Writers of a literal 1.0 to `+0x1AC` restore double speed until the next
composition. They must write 0.5: `0x00243850` and `0x00243E48`
(`3C023F80` → `3C023F00`), `0x002466A8` (`3C033F80` → `3C033F00`), and BTL
D `0x007B96B0` (`3C023F80` → `3C023F00`). The store at `0x00214CF8` is not
inspected.

Proportional approaches (about 140 sites, including `FUN_00218250`) stay
roughly right with a halved factor, converging 2–6% slower per retail frame
for typical gains; a gain whose retail value reaches 1 turns from a snap into
lag. The exact form is `k' = 1 - sqrt(1 - min(1, 2k))` with `k` the halved
gain: apply it inside `FUN_00218250`, and retarget each direct
`jal 0x00180CE0` (`0x0C060338`) that passes a factor-scaled gain to a helper
that does the same. `FUN_00180CE0` itself must stay unchanged, because other
callers pass unscaled gains.

Counters and steps on fighter paths that ignore the factor run at half rate:
`+0x968`, `+0x9C2/+0x9C4`, `+0xB14`, `+0x194/+0x196`, statistics
`+0x518`, `+0x52C`, `+0x544` and `+0x548`. The override `+0x1B0` approaches
(0.0125, 0.25, 0.02), the halving decays in `FUN_0021A8D0` and the
`+0xA9C` step in `FUN_00251230` are converted with the recursive or linear
rules above.

### Movement and physics

`FUN_0024A660` and `FUN_002183D0` integrate `x += f * v` then
`v = max(v - K * f, T)`, with `K = 3 * record+0x6C * multiplier`
([Movement and physics](../../knowledge/gameplay/stages/movement_and_physics.md#gravity-and-input-smoothing)).
With `f = 0.5` and gravity on every update, velocity matches retail at every
retail-frame boundary, but position after `n` retail frames is lower by
`K * n / 4`. For launch speed 20 and `K = 3` the apex is 71.75 instead of 77,
and landing comes about half a frame early. Applying the full retail gravity
`K` on every other update instead (and none on the update between) gives
`x += v/2; x += v/2; v -= K`, which matches retail position and velocity at
every retail-frame boundary, with the in-between position on the retail path.
Horizontal motion at constant speed is exact; terminal speed is unchanged.
Gravity multiplier `+0x9B4` resets to 1 after every pass, so a one-pass request
must persist until the gravity update.

### Animation increments

`FUN_0024D1C0` stores `trunc(+0xB90 * f)` as the fighter scene's 8.8
increment (`cvt.w.s` at `0x0024D28C..0x0024D2E0`), then advances at
`0x0024D32C`. At `f = 0.5` an odd `+0xB90` loses 1/256 frame per retail frame
(0x7F: 0.79% slow), while the secondary clock `+0x1DC` uses the exact float,
so animation end and loop events drift against it. A per-scene carry of the
dropped bit fixes this.

Fighter-scene events: each advance clears the previous event list, and
`FUN_001BB190` delivers it after the advance
([Animation runtime](../../knowledge/runtime/animation_runtime.md#packed-command-crossing-and-event-delivery)).
Two half advances deliver the same crossings as one full advance as long as
delivery follows every advance, which the fighter path does.

Recurring scene players outside the fighter, each advancing by its own `+0x94`:

| Return address | Owner | Increment | Treatment |
| --- | --- | --- | --- |
| `0x003962B8` | `ccBgDrawAnm` update `FUN_00396220` | `u16(+0x2C * +0x30 * scene+8)`, written each call | Halve with carry; 153 → 76 drifts 0.33% |
| BTL `0x006C4F58` | `ccBgBreakObjectBattle` update | `256 * scene+8` | Halve |
| BTL `0x00712DA8` | Item auxiliary model draw | `+0x94` | Halve; draw path |
| BTL `0x0071DA34` | Chakra gauge player `+0x48` | `+0x94`, default `0x100` | Halve |
| BTL `0x0071DBFC` | Chakra gauge player `+0x44` | `+0x94` | Halve |
| BTL `0x006B85A8` | HUD icon bundle callback `0x006B8570` | `+0x94` | Halve |

For a call site whose delay slot is `nop`, `srl a1,a1,1` (`0x00052842`) in the
slot halves that one call. All six slots above are `nop`. Odd increments
truncate. The fighter scene (return `0x0024D334`) and the doll player (BTL
`0x006C6EC0`) must not be halved again when the factor or their owner is
already compensated. Other recurring players exist but were not reached in the
attempt's recording: gauge player `+0x4C` (BTL `0x0071DE34`), combo hit
animation (BTL `0x006B6E48`), break, doll, transition, chandelier and crash
objects, the crane, battlegauge state 1 and the shared owner BTL `0x00855080`
([BTL scene owners](../../knowledge/runtime/scene_playback_owners_btl.md)).

Do not change the scene constructor default `FUN_001B7520` (`+0x94 = 0x100`):
it also halves one-shot priming steps and misses later rate writes. Do not
halve every `FUN_001BB210` call: absolute seeks pass `target - current`
through it ([Animation runtime](../../knowledge/runtime/animation_runtime.md#absolute-seeks-and-evaluator-reset)).

### AI

The BTL AI tick (live `0x00704D40`, called through fighter vtable `+0x1C` at
`0x00250094`) decrements `+0x38`, the 31-word bank `+0x94..+0x10C`, `+0x114`,
`+0x118` and `+0x128` once per tick, and makes per-tick RNG rolls
([Battle AI](../../knowledge/gameplay/session/battle_ai.md)). Run the whole
tick at half rate. Its reach predictors are also factor-sensitive (above).

### Input windows

At 60 history records per second each window below halves in wall time.

| Window | Site | Retail | Doubled |
| --- | --- | --- | --- |
| Double-tap trials | `+0x0A` of four records at BTL Ghidra `0x0089814A`, `0x00898156`, `0x0089816A`, `0x00898176` | `0x10` | `0x20` |
| Binding-2 same-press ages 1..7 | BTL Ghidra `0x006F0468`, `li a3,6` | 6 | 13 |
| Multi-press distance `+0xB52` | default `li v1,0xC` at `0x00248568`; per-character via `FUN_00247DC0` | 12/16/30 | 25/33/61 |
| Synthesis cooldown, hold threshold, progress cap `+0xB42/+0xB46/+0xB4A` | `FUN_00247DC0` loads at `0x00247DC8`, `0x00247DD8`, `0x00247DE8` | per character | ×2 |
| Substitution guard window | `0x00229610`/`0x0022961C` (`slti at,s0,4` / `li s0,3`), distances at `0x00229658`, `0x00229694` | 0..3 records | Needs a hook |
| Guard-held age | `0x00229620`, `slti v0,v0,0x10` | 16 | 32 |
| Recovery input | `FUN_0022A890` via `FUN_00217260` | Last 5 records | 10 |

Mash contests: the jutsu clash counts updates with any pressed button in its
mask; its timer `+0xA76` enters phase 1 at 5 and resolves at 150 (BTL Ghidra
`0x0077C2B0`, `0x0077C620`). At 60 updates human presses per second stay the
same while the window halves, and the AI side counts per update, so the
contest shifts toward the AI. Double its timers and run its AI side at half
rate. The Ultimate Jutsu contests have the same shape.

Repeat: the core threshold `slti at,v1,0xF` at `0x00113AF4` (clean
`0x2861000F`) and the front-end adapter at `0x001E0E00` delay repeat by 15
updates, after which repeat is published on every update. Doubling the delay
to `0x1F` is not enough; the continuous phase must also pulse every other
update, which needs a cave. The battle start menu reloads its countdown with
`li v1,4` at BTL Ghidra `0x0087C668` and `0x0087C6B0` (use 9); the Practice
menu navigates on held input with reloads of 4 at BTL Ghidra `0x008817A8`
and `0x008817E4` (use 9).

### Round clock

`FUN_001EBA80` adds `0x00044444` per eligible call
([Timer primitives](../../knowledge/runtime/timer_primitives.md#fixed-point-remainingelapsed-block)).
Change all four writers together:

| Site | Clean | 60 Hz |
| --- | --- | --- |
| `0x001ED204` (round reset) | `0x3C030004` | `0x3C030002` |
| `0x001ED208` | `0x34644444` | `0x34642222` |
| `0x005D83D4` (startup) | `0x3C020004` | `0x3C020002` |
| `0x005D83D8` | `0x34434444` | `0x34432222` |

`0x22222 * 120 = 0x44444 * 60 = 0xFFFFF0`, so every whole-unit boundary,
including the below-31 and below-61 outcome conditions, falls on the same wall
time.

### Projectiles

| Owner | Site (BTL live) | Clean → 60 Hz | Notes |
| --- | --- | --- | --- |
| Side factors `+0xC8/+0xCC` refresh `0x007355A0` | `0x00735638` | `0x3C033F80` → `0x3C033F00` | A fighter with `+0x186 == 0x8D` keeps the old values; also halve the reset at `0x007344B0` (`0x3C053F80` → `0x3C053F00`) |
| Pre-work `0x0072ED10`, `+0x278 = 0.25` | `0x0072EDAC` | `0x3C033E80` → `0x3C033E00` | Only when `+0x27C != 0` and effect `0x4A` within 400 |
| `+0x278 = 1.0` | `0x0072EDBC` | `0x3C033F80` → `0x3C033F00` | |
| Root delay `+0x84` | `0x0072C95C` | −1 | Half rate |
| Root phase `+0x200` | `0x0072CB30` | +1 | Half rate; equality tests at 17, 19, 90 break if halved |
| State 4/5/6 `+0x82` | `0x0072E0A0`, `0x0072E0E0`, `0x0072E180` | −1 | Half rate; state 5 also adds `+0x1C0` to position unscaled, halve that addition |
| Trail decay `0x0072FB80` | per node | literal | Half rate |

Class-specific unscaled terms (sound wave, paper bomb, kunai bomb, homing
delay, chase, boomerang, explosions, launchers) are listed in
[Projectile motion](../../knowledge/gameplay/projectiles_and_items/projectile_motion.md).
Motion terms are halved; integer schedules and equality tests run at half
rate.

### Camera

| Owner | Site (BTL live) | Retail | Treatment |
| --- | --- | --- | --- |
| Controller counter `+0x2C` | `0x006DC428` | +1 | Half rate |
| Preset phase counters `+0x240`/`+0x244` | `0x006D95F4`, `0x006D96F4` | +1 | Half rate; doubling durations changes the initializer's `(duration-4)` step |
| Eye tracking 0.125, clamp 300 | `0x006D9854` | `0x3C033E00` | `0x3C033D84` approximates; saturated region differs (37.5 vs 38.75 per frame) |
| Target tracking 0.25 | `0x006D9A04` | `0x3C033E80` | `0x3C033E09`; same caveat |
| Main camera gains `k = 1/8` | `0x006D8908`, `0x006D8958`, `0x006D898C`, `0x006D8A44`, `0x006D8A78`, `0x006D8B70`, `0x006D6DB8` | `0x3C023E00` | `0x3C023D84` |
| Main camera stage gains from table `0x00891510` | `FUN_006D8EB0` call sites `0x006D8ACC`, `0x006D8AE8`, `0x006D8B04`, `0x006D8E4C`, `0x006D8E68`, `0x006D8E84` | 0.03–0.8 | Convert in a wrapper |
| Shake mixer `0x006D6150` | angle `0x006D62E0`, phase `0x006D637C`, duration `0x006D6488`; adds offsets into eye `+0x30` and target `+0x80` every call | per call | Half rate |

Converted tracking matches retail only below the 300 clamp; the attempt found
that a recursive half-step also drifts in float rounding. A camera that must
match retail exactly near the clamp needs its tracking movers at half rate,
which makes camera motion 30 Hz.

### HUD

Top panels (BTL live; clean → 60 Hz):

- **Frame discs** `0x0071B5B0`: targets 8 and 1 at `0x0071B604`, `0x0071B62C`; steps 0.4 and 0.1 at `0x0071B60C`, `0x0071B634`. Halve the targets and quarter the steps.
- **HP child** `0x0071C000`: delay arm 100 at `0x0071C048` (`0x24030064` → `0x240300C8`); trail 0.01 at `0x0071C070` and `0x0071C0A8` (`0x3C033C23` → `0x3C033BA3`).
- **Chakra child** `0x0071E070`:
  - rate ease 0.1 at `0x0071D848/4C`;
  - reservation +0.5 at `0x0071D894` (`0x3C033F00` → `0x3C033E80`);
  - blink limit 2 at `0x0071D908` (→ 4);
  - pulse `pi/60` at `0x0071D984`;
  - marker counter at `0x0071D9C0` (half rate);
  - fades at `0x0071DCB8` and `0x0071DE8C`;
  - icon rate/90 at `0x0071E0A4`.

  The second helper is `0x0071D880` (its `jal` is at Ghidra `0x0071E04C`).
- **Top hide/show** `0x0071AD80`/`0x0071AE50`: velocities and accelerations at `0x0071ADAC`, `0x0071ADD8`, `0x0071AE7C`, `0x0071AEA8`, `0x0071AEC8`.
- **Top-panel shake** `0x0071B020`: sample count plus one RNG draw per request. Half rate.

Other HUD:

- **Lower item panel** `0x00711B40`: slide `k = 0.3` at `0x00711BA8/AC` and `0x00711C04/08`; wheel step 0.2 at `0x007123E8`; badge ±0.1 at `0x007126A0`, `0x007126C4`.
- **Battlegauge** (vtable `0x005DDF80`, update `0x00717FC0`, draw `0x00718320`): pulse velocity 1.0 at `0x00718084` and `0x00718F8C`, stagger 15 at `0x007180A0`, slide 30.0 at `0x00718244`, and the draw-path counter at `0x00718928`.
- **Combo digits** `0x006B6D10`:
  - hold limit 30 at `0x006B6D60` (`0x2862001E` → `0x2862003C`);
  - opacity −0.05 at `0x006B6D70`;
  - overlay +0.1 at `0x006B6DC0`;
  - scale +0.15 at `0x006B6DFC`;
  - shake countdown with two RNG draws at `0x006B6E90` (half rate).
- **Prompts** `0x006B53F0`: counters at `0x006B5458`, `0x006B54B0`, `0x006B551C`; alpha −0.15 at `0x006B5534`.
- **Clock** `0x0087EB40`:
  - below-ten scale ramp at `0x0087EC6C` (`0x3C023C75` → `0x3C023BF5`);
  - hide slide at `0x0087E6F4`, `0x0087E720/24`;
  - show slide at `0x0087E7BC`, `0x0087E7F0`, `0x0087E808`.

  Digits follow the round clock.

Rates and owners are documented in
[Battle HUD](../../knowledge/gameplay/session/battle_hud.md). Running a whole
HUD element at half rate is a valid shortcut where 30 Hz HUD motion is
acceptable.

### Draw-path consumers

These advance state from drawing code, once per draw. They need the same
treatment as update-path consumers.

| Owner | What advances | Site | Treatment |
| --- | --- | --- | --- |
| Fighter second-pass slot `+0x14`, `FUN_0024DD70` | `FUN_00226370` visual fade, ramp, pulse and tint timers, all literal per call | `jal FUN_00226370` at `0x0024DD94` (clean `0x0C0898DC`) | Half rate |
| Same slot, other calls | `FUN_00226900` only applies the display values to the renderer ([Section transfers](../../knowledge/gameplay/stages/section_transfers.md#visible-placement-and-presentation-amounts)); `FUN_00308FD0` returns immediately; channel 7 of `FUN_00217670` runs per-character draw callbacks that select render environments, and slot `+0x28` draws auxiliary scenes ([Character action callbacks](../../knowledge/gameplay/characters/character_action_callbacks.md)) | | Unchanged, except per-character channel-7 and `+0x28` bodies that advance state, which are not all inspected |
| ccPlayerCtrl second pass `FUN_00250690` | `FUN_002091B0` decrements an owned object's `+0x1C` | `jal FUN_002091B0` at `0x002507B0` | Half rate |
| Same pass, `FUN_00305C00` | Status-effect secondary callbacks; effect `4A`'s callback `FUN_002C8900` recomputes node state ([Battle items and status effects](../../knowledge/gameplay/projectiles_and_items/battle_items_and_status_effects.md#update-expiry-and-removal)) | `0x00250758` | Per callback; not all classified |
| Same pass, `FUN_002070D0` | Draws the container's `+0x30` auxiliary object while fighter 1P `+0xB10` is nonzero; its helpers `FUN_00207490`, `FUN_00207790`, `FUN_00207B10` and `FUN_00207DC0` are not classified | | Not classified |
| Battlegauge draw `FUN_007182E0` (live `0x00718320`) | Counter `+0x14` +1 whenever state `+0x12 > 0`; it feeds the reverse seek `(end - +0x14) * 0x100` | `addiu v1,v1,1` at live `0x00718928` (clean `0x24630001`) | Half rate |
| Item auxiliary model draw (live `0x00712C20`, codes `0x51..0x73`) | Advances its scene by `+0x94`; `+0x0C += 1.0`, wrapping at 12 | `jal FUN_001BB210` returning to live `0x00712DA8` | Halve both |
| Particle history draw | `FUN_0034B070 -> FUN_0034AB30` advances the visual's sprite frame or scene ([Particle runtime](../../knowledge/runtime/rendering/particle_runtime.md#concrete-visual-update-and-draw)) | `jal FUN_0034AB30` at `0x0034B08C` | Half rate |
| Track renderer, BTL Ghidra `0x00720F90` | Swaps pass weights by `+0x194 & 1` | See [frame-counter consumers](#frame-counter-consumers) | |
| Ultimate Jutsu contest render | Time bar and result-display counters count renders | `FUN_0035EBD0` at `0x0035EC60`, `0x0035ED60`, `0x0035EDEC`; `FUN_0035F770` at `0x0035F7A8`; `FUN_0035FA60` at `0x0035FAF8` | Half rate, or double their limits |
| Ultimate Jutsu presentation state 5 | Calls `FUN_001D8050(0x39, 0x3E)` on every render | Render function at BTL live `0x0076A8E0` | Half rate |
| UI pulse `FUN_0037E7C0` and other draw-counted UI | Counts draw-wrapper calls ([UI animation](../../knowledge/runtime/ui_animation.md#counter-driven-squashstretch-pulse)) | | Half rate |
| BTL camera publication `FUN_006B4CC0`/`FUN_006B4D60` | Advances its player when player `+0xFC` is nonzero ([Renderer coordinates](../../knowledge/runtime/rendering/renderer_coordinates.md#lazy-camera-publication-into-existing-environments)) | | Halve |
| RGBA transition pool `FUN_00183650` | Cursor +1 per draw call, from `FUN_00186000` in the engine tail ([UI animation](../../knowledge/runtime/ui_animation.md#draw-before-advance-order)) | | Half rate |

### Unmasked dispatcher work

`FUN_001F03E0` calls these on every update regardless of its masks
([Pause and replay](../../knowledge/gameplay/session/pause_and_replay.md#selective-update-gating)):

| Call | What it does | Treatment |
| --- | --- | --- |
| `0x0076EF90` | Pause controller pre-update: runs the active presentation (battle-gauge intro, end demo, Ultimate Jutsu) and its countdowns ([Pause and replay](../../knowledge/gameplay/session/pause_and_replay.md#shared-ownership-and-controller-lifecycle)) | Half rate |
| `0x0076F020` | Pause controller post-update: draws the active presentation child | Every update; its draw-path counters are listed under [draw-path consumers](#draw-path-consumers) |
| `0x006DC3B0` | Camera controller | See [camera](#camera) |
| `0x00706420`, `0x00706450`, `0x00706480` | Reapply the fighter override bank | Unchanged (idempotent) |
| `0x00778D90` | Starts or resets the two-side helper at `0x00607844 + 0x210` | Half rate, paired with its update |
| `0x00778FF0` | Updates that helper: call counter, 12- and 5-call state counters, decaying sine offset, recursive approaches, child updates, pending input capture, `+0xA50` release | Half rate |
| `0x00870230` ×2 | Moves a pending command word into the fighter command node | Unchanged (event) |
| `FUN_001DE1C0` | Collision separation pass ([Collision](../../knowledge/gameplay/combat/collision.md#resident-pair-processor)); draws RNG only when two centres coincide | Unchanged; separation is resolved per pass |

### Stage objects

Live BTL sites unless noted:

- **Proximity blends:**
  - `ccBgTransObject` `0x006C7900`: `k = 0.2` at `0x006C7A44/48` and `0x006C7A6C/70` (`0x3C023E4C/0x3442CCCD` → `0x3C023DD8/0x3442368F`).
  - `ccBgTransAnm` (`0x006C8294`, `0x006C82BC`) and `ccBgTransObject2` (`0x006CE378`, `0x006CE3A0`): the same, but their register and `ori` words were not dumped.
- **Rebirth waits:** wait `> 0x78` and fade 0.05 per update in `ccBgBreakObjectBattleAnm` (`0x006C60C4`, `0x006C60CC`, `0x006C6160`), the reborn object (`0x006CDDE0`, `0x006CDDE8`, `0x006CDE7C`) and the chandelier (`0x006D3068`, `0x006D3070`, `0x006D3104`). Double the waits (`0x28410079` → `0x284100F1`) and halve the fades.
- **Cooldowns:** doll (byte `+0x190` −1 at `0x006C6978`, re-armed with RNG) and mover (`+0x230` at `0x006CEB74`, armed at `0x006CEB58/64` with RNG). Half rate.
- **Falling prop** `0x006CE5E0`: `vz -= 3.0` at `0x006CE6B4`. Apply it at half rate, as for fighter gravity.
- **Animated backgrounds:**
  - `ccBgDrawAnm` `FUN_00396220`: step `+0x2C * +0x30 * scene+8`.
  - `ccBgUVAnm` `FUN_0039B910`: UV += `speed * scene+8`.
  - `ccBgRotateSky` `FUN_00398510`: angle += `+0x50`, no scale.
  - `ccBgSwingGrass` helper `FUN_00397BC0`: per-call angle, countdown `+0xD0` and RNG (half rate).

Scene float `+8`, initialized to 1.0 by `0x003AD510`, multiplies several of
these. It is tempting as a single lever, but its writer set is not established
and its initializer also seeds other fields. Owners and rates are in
[Stages](../../knowledge/gameplay/stages/stages.md).

### Particles

The default manager is stepped from the engine tail and the battle manager
from dispatcher bit 7
([Particle runtime](../../knowledge/runtime/rendering/particle_runtime.md#caller-scheduling-and-suppression)).
In `FUN_0034CE00` emission adds `rate / 30.0` per call (`lui v1,0x41F0` at
`0x0034CE6C` → `0x3C034270` for 60.0), and delay `+0x30` counts calls. In
`FUN_0034FAF0`, fades divide by 2048 (`0x0034FBF0`, `0x0034FCE8`: `0x3C034500`
→ `0x3C034580`) and hold `+0x80` counts calls. Ages, lifetimes, force-field
ages and history shifts are integer per call, and every spawn draws from the
shared generator. Running the whole controller `FUN_0034C610` per emitter at
half rate was runtime-exact in the attempt but makes effect motion 30 Hz;
converting the constants and doubling the integer ages makes it 60 Hz.

### End sequence and transitions

`FUN_001EF9C0` runs every update through `FUN_001EF8F0`. Its delays are armed
with `li v0,N`:

| Site | Value | Doubled word |
| --- | ---: | --- |
| `0x001EFCA0`, `0x001EFCB0`, `0x001EFD70`, `0x001EFDAC`, `0x001EFDBC`, `0x001F00B4`, `0x001F01C8` | `0x5A` | `0x240200B4` |
| `0x001EFCC0` | `0x1E` | `0x2402003C` |
| `0x001F0140` | `0x3C` | `0x24020078` |

They are decremented at `0x001EFCDC`, `0x001EFDD8`, `0x001F015C`,
`0x001F0194` and `0x001F01B8`. The outer battle state's `state[1]` delays of 3
(arms at `0x001EADF8`, `0x001EB274`, `0x001EB528`, `0x001ED820`,
`0x001EDBEC`, `0x001EDEAC`) order overlay and resource lifetime; run them at
half rate rather than retuning them.

### Battle start menu and Practice menu

BTL Ghidra sites:

- **Start menu state 4:**
  - initial velocity −30 at `0x0087C534`;
  - acceleration +10 at `0x0087C7A0`;
  - opacity +0.4 at `0x0087C7B8/BC`.

  The velocity and acceleration form a discrete slide; `−16.25` (`0xC1820000`) and `2.5` (`0x40200000`) reproduce every retail position at every other update. Use opacity `0x3E4CCCCD`.
- **Start menu easing:** 0.2 at `0x0087CA24/28` and 0.4 at `0x0087CA60/64`, converted with the table above.
- **Practice child update** (Ghidra `0x00881A70`): phase steps 0.05, 0.04 and 0.01 at `0x00881AB8`, `0x00881AF4`, `0x00881B30`.

The whole start-menu updater can instead run at half rate from `0x001EBF48`.

### Ultimate Jutsu and audio sync

The Ultimate Jutsu cinematic cannot be converted:

- the cinematic is a streamed container whose rate must be a whole multiple of
  `0x100` ([streamed rate](../../knowledge/runtime/frame_timing.md#streamed-ccs-rate-is-whole-frame-only));
  `0x80` freezes it;
- raw `+0x9C` is also the generator pass count, so changing the rate changes
  effect timing;
- the soundtrack is a real-time stream that only starts on frame 1.

It is therefore a half-rate owner that still draws every update:

- **Play task.** `FUN_001A0120` steps the stream (`jal FUN_001B4C60` at
  `0x001A05C8`), runs `FUN_001ABC70` with the raw rate, calls frame callback
  `FUN_0035B740` (`jalr s3` at `0x001A065C`), runs the `+0x7C` loop, submits
  the scene through `FUN_001A0A40` (draw callback `FUN_0035C110`), and yields
  once. On the off update run only the frame callback and the submission. The
  frame callback must run every update, because `FUN_001F03E0` resets the
  pointers it reinstates; repeated calls on the same frame do not refire hits,
  since rows fire on frame equality and the index steps once. Hook:
  `0x001A0578` (clean `0x8E820078`) becomes a jump to a cave and `0x001A057C`
  (clean `0x8C420004`) a `nop`; on the stepping update the cave replays the
  two loads and returns to `0x001A0580`; on the off update it calls the frame
  callback and jumps to the submission at `0x001A06A8`.
- **Per-call work inside the callbacks.** `FUN_00370120` (called at
  `0x0035BD60`) advances the skill-play object's child by `0x100` per call,
  and `FUN_003572E0` (called at `0x0035C038`) negates a matrix row per call.
  Both run at half rate. The hit popups advance their scenes at `0x0035C634`
  and `0x0035C7E0`; halve those increments.
- **Presentation state machine** BTL `0x00769790`, called from live
  `0x0076FCF0` (`jal`, clean `0x0C1DA5E4`): run at half rate, or
  - double its countdowns (150, 130, 100, 85, 81, 30, 15, 12, 6, at BTL Ghidra
    `0x00769E7C`, `0x00769EA4`, `0x00769EB4`, `0x00769F9C`, `0x0076A0F4`,
    `0x0076A334`, `0x0076A340`, `0x0076A3D8`, `0x0076A3E4`);
  - convert its lerps (0.5 → `0x3E95F61A`, 0.07 → `0x3D11F5ED`, 0.65 →
    `0x3ED118C2`);
  - set cut-in scene rates to `0x80` and `0x60`.
- **Contest.** The contest update `FUN_0036BF10` (call at `0x001F0918`) and
  its render counters ([draw-path consumers](#draw-path-consumers)) run at half
  rate, or their limits double: time limit `li a1,70` at `0x0035ACAC` and its
  `last - 90` shortcut at `0x0035ACB4..0x0035ACC8`.
- **Screen-break task** `FUN_00373240` (`ZgBreakScreen`) yields per wake:
  step `0x200` at `0x00373158` (→ `0x24030100`) and waits 15, 60, 90 at
  `0x00373490`, `0x00373504`, `0x00373508` (double). Where else it runs is not
  established; its edits are correct only while the threshold is 1.

With these, the cinematic advances at retail rate and stays in sync with the
real-time soundtrack without any audio change.

Elsewhere in battle, audio follows its owner's clock:

- Fighter cues use the action cursor and are converted by the factor ([Battle audio](../../knowledge/gameplay/session/battle_audio.md#fighter-action-cue-production)).
- The voice cooldown `+0x19A` counts updates (half rate, under fighter maintenance).
- The guide voice re-arms with `150 + rand(90)` updates; double it.
- Countdown-timed voice waits in other presentations can cut voices short.

Battle music is a stream and needs nothing.

## Frame-counter consumers

Direct readers of `+0x194` are listed in
[Frame timing](../../knowledge/runtime/frame_timing.md#engine-update-counter-readers).
The counter advances 60 times per second.

| Reader | Treatment |
| --- | --- |
| Master-chain template `FUN_001079C0` | Unchanged (it alternates buffers per update) |
| RNG seed `0x001E11A4` | Unchanged |
| Practice refill `0x0024CBD4` | Test `(+0x194 & 0x3F) == 0` |
| `ccPl93Track` trail `FUN_00300D70` | Halving the factor doubles its divisor, which keeps retail spacing for factors up to 1. A boosted retail factor (above 1) clamps the divisor to 1 at 60 Hz and doubles the trail rate; clamp the divisor to at least 2 |
| Ranking-screen highlight pulse (BTL Ghidra `0x006E8CC4/C8`, `0x006E8EE8/EC`, `0x006E93D4/D8`) | `andi 0x3F; sll 7` at the listed pairs |
| Track renderer weights, BTL Ghidra `0x00721004` | Unchanged; the weights alternate per update instead of per retail update |
| Once-per-update counter helper, BTL live `0x00722D90` (characters 78, 80, 82, 91, 92, 93) | Count once per retail update: read a half-rate counter |
| ID 93 effect countdown `FUN_00722E50` | Read a half-rate counter |
| `ccSkillKIW001` afterimages (BTL Ghidra `0x0081F950`, `0x008626A0`) | `(+0x194 & 3) == 1`; its `20.0` per-update travel threshold becomes `10.0` |

## The PNACH attempt

[The attempt record](../../../experiments/60-fps/attempt.md) and its ledger
`experiments/60-fps/NA228_60_fps.pnach` halved the fighter factor and literal
timers and, as each first divergence was found in a Practice replay, ran that
divergence's owner on every other update.

What it established at runtime on the NA228 build:

- Retail runs one complete update every two VBlanks; the threshold word alone
  doubles everything.
- The composed fighter factor at 0.5 is exact in every composition branch.
- The combo and hitstop timers at 0.5 are exact.
- Running fighter logic, per-element jitter, the CCS manager passes, the
  camera and camera effects, particles, emitter scheduling, the doll cooldown,
  controller publication and `FUN_00226370` at half rate restores byte-exact
  battle, fighter, camera, CCS, RNG and controller state through frame 2642.

Why it did not produce a working mode:

- It had no rule for which consumer is converted and which runs at half rate,
  so each fix was found only after the previous divergence. A factor of 0.5
  combined with half-rate fighter logic double-compensates.
- 17 scene advances at six call sites (listed under
  [Animation increments](#animation-increments)) were still uncompensated, so
  every image differed from retail from the first input.
- A runtime switch of the threshold requires the live setter; patching the
  boot initializer after boot has no effect.
- It never reached the Ultimate Jutsu with its fixes on, so the soundtrack
  desync and the whole-frame-only streamed rate were not found.

The catalogue above supplies the missing rule: each consumer has one assigned
treatment.

## Effect on other mod features

- [Substitution](../substitution.md#once-per-battle-recovery-clock-seam)'s
  recovery clock runs from the round-clock call, which runs every update at
  60 Hz. It currently fails closed for any threshold other than 2, so it would
  freeze. At threshold 1 it must add one count per call, not two, or stocks
  recover twice as fast.
- Practice features that count updates (frame data, input recording) count
  60 Hz updates; their displayed units need the same doubling.
- Mod code that reads pressed input (for example the rematch prompt) is
  edge-based and works unchanged.

## Validation

Use the [E2E validation workflow](../../workflows/e2e_validation.md) with
matched retail and 60 FPS runs from the same recording. A P2M2 recording
stores one record per physical VSync, so the same recording drives both runs
and recording frame numbers are the common time base
([PCSX2 input-recording frame semantics](../../../experiments/60-fps/attempt.md#pcsx2-input-recording-frame-semantics)).

- **State.** At every retail update boundary, fighter positions, velocities,
  animation cursors, timers and HUD values equal retail within float tolerance
  for converted consumers and exactly for half-rate owners. Events (hits,
  state changes, spawns) happen within one 60 Hz update of retail.
- **Input.** A press appears in the published pad state on the first update
  after its VSync.
- **Ultimate Jutsu.** The cinematic's last frame and the soundtrack's end fall
  on the same recording frame as in retail.
- **Performance.** Context `+0x04` stays below one field on every update in the
  heaviest stage and Ultimate Jutsu tested.

## Open questions

- **Unclassified per-update work.** The helpers of `FUN_002070D0`, the
  status-effect secondary callbacks reached through `FUN_00305C00`, and the
  per-character channel-7 and `+0x28` draw callbacks.
- **Task wakes.** Which tasks besides `MOTHER` and the play task yield once per
  wake in battle and count wakes (sound RPC tasks, loaders, the screen-break
  task).
- **Display.** Whether 60 images per second in interlaced field mode looks
  acceptable, or the output should change to frame mode.
- **Frame time.** Whether battle work fits in one VBlank on the target emulator
  settings.
- **Fighter factor sites.** Reads through rebased pointers, the store at
  `0x00214CF8`, other callers of the one-shot entry routines, the consumers of
  the ID 92 and ID 93 outputs, the exact words for the ID 78 pull term, and
  whether data-driven gains ever reach 1 at retail rate.
- **Camera near the clamp.** Whether converted tracking is close enough, or the
  tracking movers must run at half rate.
- **Ultimate Jutsu factor writes.** The presentation writes override `+0x1B0`
  as 0, then 0.05 at countdown 100, then 0, then 1.0. The attempt's runtime
  observation of the composed factor as "0, then 0.05" fits this order, but its
  link to these sites is not established.
- **Fighter `+0x954` and `+0x186 == 0x8D`.** Their meanings.
