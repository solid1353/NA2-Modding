# Ultimate Jutsu

How clean NA2 starts an Ultimate Jutsu, runs its cinematic and input contest,
resolves the contest, applies damage and outcome, and drives the CPU side.

## Research coverage

- **Assigned scope:** Ultimate Jutsu start after a connecting hit, the BTL
  presentation state machine, the resident contest objects for every native
  Battle Settings mode, contest resolution, cinematic damage and outcome
  application, CPU contest input, and the HP damage-trail presentation.
- **Exploration depth:** instruction-level static traces of the resident
  connection path `FUN_00244F80 -> FUN_00216EA0`, the BTL presentation state
  machine at live `0x00769790`, the skill-play constructor `FUN_0035CF00`, the
  mode dispatcher `FUN_0036B6D0`, the common contest base
  (`FUN_0035E060`, `FUN_0035E360`, base update `0x0035EA40`, base render
  `FUN_0035EAD0`, time bar `FUN_0035EBD0`, CPU tier `FUN_0035E990`, result
  `FUN_0035F610`, result displays `FUN_0035F770` and `FUN_0035FA60`, result
  flags `FUN_0035FEA0`), every class update (`FUN_00362140`, `FUN_003685E0`
  with `FUN_00369510` and `FUN_00369D00`, `FUN_00364DF0` with
  `FUN_00365AC0`, `FUN_00364170`, `FUN_003661F0`) and their initializers, the
  cinematic hit callback `FUN_0035B740`, the post-cinematic handler
  `FUN_0024ED40`, and the jutsu-slot attempt in the BTL AI helper at live
  `0x006F8810`. Direct-`jal` scans of the resident image and BTL covered the
  contest accessors named below, and a store scan covered status `+0xD8` in the
  contest code. The HP controller and parent hide/show paths were inspected
  through decompilation, disassembly, and byte views. Render routines were read
  only for their timing and result-state effects, not for layout.
- **Confirmed coverage:** the connection gates and chakra tier charge; the
  presentation timeline, its voice-stream handling, and its skill-play
  admission; all contest classes and their update/render pairs; the common
  lifecycle, time limit, render-path timer, difficulty-to-CPU tier mapping, and
  per-side controller source; input, scoring, meter scale, and CPU behavior for
  Command, Timing, Turn, Combo, and the unreachable Sign class; the shared
  result thresholds, damage multipliers, and result displays; per-hit damage,
  handicap-only scaling, chakra drain, effect application, and defeat-latch
  writes; the CPU's jutsu-slot attempt gates; and the HP trail's independent
  delay.
- **Unresolved or untested:** no producer of contest status `2` was found, so
  the presentation's status-`2` branch has no known trigger. The contents of
  the per-skill branch-frame table at `0x0060774C`, the on-screen result of the
  branch-`2` cut, the meaning of the alternate-voice table at
  BTL `0x008D2660`, the meaning of player `+0x94` in the time-limit formula,
  fighter `+0x990` in the CPU attempt, and the names of the result sprites are
  unresolved. Which action slot holds the Ultimate Jutsu is character data and
  was not decoded. No runtime capture confirms the static timings.
- **Deliberate exclusions and overlap:** Triangle staging and chakra
  reservation belong to [Chakra and guard](chakra_and_guard.md); post-Ultimate
  Jutsu transformation belongs to [Awakening](awakening.md); the Ultimate Jutsu
  record table and character lists are described there too. Practice option
  storage belongs to [Practice mode](practice_mode.md); selector routing of the
  presentation controller belongs to [Pause and replay](pause_and_replay.md).
  Feature behavior belongs to [Battle](../../features/battle.md).
- **Evidence limitations:** all conclusions are static reads of the identified
  clean resident and BTL images. Frame counts are update counts of the owning
  routine, not measured display time. The HP-trail conclusions do not establish
  behavior across every character's cinematic or end-of-round transition.

## Addresses

Binary identities and address conversions follow
[Standard game file identities](../game/files/file_identities.md). Resident
addresses are runtime addresses. BTL addresses are live addresses; the BTL
file offset is the live address minus `0x006B3F00`. Resident `gp` is
`0x0060A9F0`.

Resident globals used below:

| Address | Meaning |
| ---: | --- |
| `0x00607600` | battle manager |
| `0x00607714` | current skill-play record (`SP Skill Play` context) |
| `0x00607750` | current contest object |
| `0x00607754` | contest damage total, a fraction of maximum HP |
| `0x00604310` | post-Ultimate-Jutsu effect ID for the attacker, or `-1` |
| `0x00604314` | defeat-latch enable byte |
| `0x00607780` | cinematic control value written by the BTL presentation |

## Start

Triangle staging, the chakra reservation, and the Ultimate Jutsu Prep binding
are described in [Chakra and guard](chakra_and_guard.md). The historical lead at
ELF file `0x1492B0` is runtime `0x002491B0`, the `5.0` constant of the Triangle
staging debit `chakra -= 5.0 * (level + 1)` in `FUN_00248EC0`.

`FUN_00244F80(attacker)` is the connection path. It returns without starting
anything unless all of these hold:

- attacker `+0x62` bit `0` is clear (otherwise it releases the reservation and
  returns);
- attacker action class `+0x18E` is `8`, so the active record is
  `attacker+0xA4C`;
- attacker byte `+0xA40` is `1`;
- the record has one of flags `0x00100000`, `0x00200000`, or `0x00400000`, and
  does not have `+0x14` flag `0x00010000`;
- the record is the target's hit provenance, resolved as in
  [Damage](damage.md#native-damage-calculation) (target `+0xE54`, then
  `FUN_002179F0` on `+0xE58` and `+0xC74`), so the Ultimate Jutsu attack itself
  has hit the target.

The flag gives the jutsu level: `0x00100000` is `0`, `0x00200000` is `1`, and
`0x00400000` is `2`. The routine then releases the attacker's reservation and
charges `5.0`, `10.0`, or `15.0` chakra for tier `attacker+0x18C` `0`, `1`, or
`2`, subject to the spend gates in [Chakra and guard](chakra_and_guard.md). It
releases the target's reservation and calls `FUN_00216EA0(attacker, level)`.

The jutsu-class action slots `4..9` that carry these flags, and the Triangle
selection that reaches them, are described in
[Action commands](action_commands.md#representative-chakrajutsu-path).

`FUN_00216EA0` clears both fighters'
[update-pause block](hit_response.md#fighter-update-pause-and-action-lock)
through `FUN_00224470(fighter, 0, 1)` and sets both
[hit-rejection countdowns](hit_response.md#accepted-hit-rejection-countdown)
to `60` through `FUN_002247D0(fighter, -60, 1)`. Unless the battle coordinator
is already in state `6`, it switches the coordinator to state `6` with the
attacker at `+0x24`,
the target at `+0x28`, and the level at `+0x20`, then requests presentation
selector `13 + level` with the attacker's side. BTL collapses selectors
`13..15` to the Ultimate Jutsu presentation described next.

### CPU attempt

The AI slot layout and profile parameters are in
[Battle AI](battle_ai.md). In its state-`15` helper at BTL live `0x006F8810`,
the jutsu-slot attempt runs only when the slot's countdown `+0xB4` is zero and
the Ultimate Jutsu setting (key `5`, read at live `0x006F8BD0`) is positive.
It then requires all of these:

- a draw from `0..100` below profile parameter `16` (`+0x180`:
  `0/0/0/50/60/70` from Simple to Ultimate);
- a valid record for the cached slot `+0x1B0` (first usable slot among `4..9`);
- for slots `7..9`, planar distance `+0x0C` of at least `800.0`; for slots
  `4..6`, distance at most record `+0x34` unless that value is `10000.0` or
  `-17320.5`;
- different halfwords `+0x990` on the two fighters;
- `FUN_00225940` affordability of the tier byte of Ultimate Jutsu record
  `(int)record[+0x20]` through `FUN_00372CB0`.

When all pass it queues the slot through `FUN_0021D380`. A failed later test
skips the queue; either way `+0xB4` reloads from parameter `18` (`+0x184`). A
failed chance or missing record instead goes to the helper's other masked
action attempt (parameters `15` and `17`) described in
[Battle AI](battle_ai.md). The affordability call passes a record index derived
from the action cost rather than the cost itself; whether that is intended
cannot be established statically.

## Presentation state machine

BTL live `0x00769790` (file `0xB5890`) runs the presentation. Its object keeps
the state at `+0x00` and a countdown at `+0x04`. The side is the signed byte at
controller `+0x0C`. The Ultimate Jutsu record index is the side's manager word
`+0x60`.

| State | Behavior |
| ---: | --- |
| `0` | Loads the cut-in models and text, then sets the countdown to `100`, to `130` when the record's `+0x04` is `0x9C`, or to `150` for the alternate-voice case below. Plays voice `+0x0A` of the record on stream bank `1`, slot `0`. |
| `1` | At countdown `100` (`150` in the alternate-voice case) hides the battle HUD with `0x001F1820(-7)`. At countdown `100` sets both fighters' update-rate override `+0x1B0` to `0.05`. At countdown `85` creates the skill play and its contest. Ends at zero, or early once the voice stream has played and stopped after countdown `85`. Then sets both fighters' `+0x1B0` to `0`. |
| `2` | Waits until `FUN_001CE7F0` reports the skill play's hold point (or counts down `30` when no manager exists), then sets contest byte `+0xD4` through `0x0036C180`, which starts the contest. |
| `3` | Counts down `12`, sets both fighters' `+0x1B0` to `1.0`, stops the voice stream, and clears the skill play's hold flags through `FUN_001CE840`. |
| `4` | Polls contest status `+0xD8`. Status `2` requests skill-play branch `1` through `FUN_001CDDD0`. Status `4` writes `2` to `0x00607780` and requests branch `2` once `FUN_0035DB20(0)` accepts the current frame, then moves to state `5`. When the skill play finishes, writes `1` to `0x00607780` and exits. |
| `5`–`7` | Wait for the skill play to finish and for the flag at `0x00607778`, then exit. |

`FUN_001CDDD0(player, n)` latches `n + 1` into player bytes `+0x281` and
`+0x282`; the first request wins. A `+0x282` value of `2` or more makes the
player's entry loops jump entry index `+0x274` to entry count `+0x272`. A
`+0x281` value of `1` or `3` stops the current scene through `FUN_001A00C0`, and
any nonzero `+0x281` skips the normal entry start at `0x001CE4D8`. Branch `2`
therefore stops the running scene and jumps to the end of the entry list, and
`FUN_001CDD80` reports the player finished once both indices reach the count.
Inference: a status-`4` result cuts the rest of the cinematic, including any
hit frames it had not reached.

Fighter `+0x1B0` is the update-rate override described in
[Hit response](hit_response.md#fighter-fields-used-by-the-response-machine).
No store of status `2` exists in the contest
code range `0x0035E000..0x0036C200`; only `0`, `1`, and `4` are written.

On exit it shows the HUD with `0x001F1A20(-1)` and writes condition statuses
described in [Match outcomes](match_outcomes.md).

The presentation's calls to `FUN_001D99B0(1, 0)` at live `0x00769F94` and
`0x0076A1F0` (file `0xB6094` and `0xB62F0`) read audio state, not controller
input. `FUN_001D99B0(bank, slot)` returns byte `+0x6F4 + slot`
(bank `0`) or `+0x6F7 + slot` (bank `1`) of the stream manager at
`0x00607558`. `FUN_001D70A0` sets those bytes from the state of stream
handles `+0x08` and `+0x2C`, and the voice is started on bank `1`, slot `0` by
`FUN_001D9620(7, voice, 0) -> FUN_001D97D0 -> FUN_001D6F60`. Latch `+0x3A` is
therefore "the voice has started", and its clear-on-stop edge ends the intro.
When the alternate-voice case applies, that edge instead plays record voice
`+0x0C` once and continues the countdown.

The alternate-voice case requires record category `+0x06 == 2` and a match in
the ten-entry BTL table at `0x008D2660`, keyed by the side's manager byte
`+0x68` and a per-side presentation byte. The table's gameplay meaning is
unresolved.

### Skill-play admission

At countdown `85` the presentation calls resident `FUN_0035CF00(side, a, b,
skill, mode)` only when the record's skill value from `FUN_00372900` is
nonzero and BTL `0x00769630` returns zero. `FUN_00372900` returns record
`+0x04`, but returns `0` when `FUN_00372770` classifies the record below `2` or
as `5`. The mode is the battle-rule byte `+0x105` through BTL `0x006EE560`,
falling back to the side's cached manager word `+0x64`; see
[Practice mode](practice_mode.md#presentation-options-and-ultimate-gate).

`FUN_0035CF00` builds the `SP Skill Play` task, the skill-play record at
`0x00607714`, and a `0x2E0`-byte cinematic player with callbacks
`FUN_0035A070`, `FUN_0035B740`, `FUN_0035C110`, and `FUN_0035AF20`. Player
`+0x90` is the current cinematic frame. Unless manager mode `+0x0C` is `6` (Collection), it forwards the
mode through `FUN_0036C120` to `FUN_0036B6D0`, which creates the contest.

## Contest objects

`FUN_0036B6D0` creates one object and stores it at `0x00607750`. Random
selection is described in
[Practice mode](practice_mode.md#presentation-options-and-ultimate-gate).
Every class derives from `ccInputMatch`:

| Mode | Class | Size | Update | Render |
| ---: | --- | ---: | ---: | ---: |
| `2` Command | `ccInputMatchCmd` | `0x3E8` | `0x00362140` | `0x00363190` |
| `3` Timing | `ccInputMatchTim` | `0xFE4` | `0x003685E0` | `0x00369F70` |
| `4` Turn | `ccInputMatchRot` | `0x108` | `0x00364DF0` | `0x00365690` |
| `5` Combo | `ccInputMatchHit` | `0x100` | `0x00364170` | `0x00364A30` |
| `6` (unreachable) | `ccInputMatchSign` | `0x1D8` | `0x003661F0` | `0x00366EE0` |

Mode `0` creates no object. The manager calls update dispatcher
`FUN_0036BF10` at `0x001F0918` and render dispatcher `FUN_0036BFF0` at
`0x001F0940` (ELF file `0xF0A40`); each calls vtable slot `+0x08` or `+0x0C`.
The skill-play teardown `FUN_0035D7C0` clears `0x00607714` and then destroys
the contest through `0x0036C0F0 -> FUN_0036BC50`, which clears `0x00607750`.

### Common fields

`FUN_0035E060` and `FUN_0035E360` set these fields for every class:

| Field | Meaning |
| --- | --- |
| `+0x04` | mode |
| `+0x06` / `+0x08` | current state / pending state (`-1` when none) |
| `+0x0A` | attacker side, `0` or `1` |
| `+0x14` | CPU tier from the battle difficulty |
| `+0x16 + side*2` | CPU frame counter |
| `+0x1A + side` | side is CPU-driven, from bit `1` of manager byte `+0x48` (side `0`) or `+0x70` (side `1`) |
| `+0x62` / `+0x64` / `+0x68` | time-bar state / elapsed / limit |
| `+0x74` | contest meter, positive toward side `0` |
| `+0x78` / `+0x79` | attacker / defender result flags |
| `+0xD4` | started |
| `+0xD5` | finishing counter |
| `+0xD8` | status read by BTL through `0x0036C1A0` |

`FUN_0035E360` also clears the damage total, sets `0x00604314` to `1`, and sets
`0x00604310` to the effect ID at record `+0x0E` (record `99` when the skill is
`0x49`).

The CPU tier is `{0, 1, 2, 3, 3, 4, 4}[difficulty]`, where difficulty is
battle-setting key `0x0B` (Simple through Ultimate). That key is read from
manager `+0x9FB` in Free Battle and Practice, otherwise from `+0xA07`.

### Lifecycle and time limit

Base update `0x0035EA40` does nothing until `+0xD4` is set. It applies a
pending state and clears `+0x64`. Once `+0xD5` is nonzero it counts two more
updates, then sets state `5` and clears `+0xD4`. Every class update repeats
this logic.

`FUN_0035A070` sets the limit through `0x0036C160` to `70`, reduced to
`len - 90` when the player's `+0x94` value `len` is below `160`.

The time bar `FUN_0035EBD0` runs only in the render path, from base render
`FUN_0035EAD0`, which every class render calls. Bar state `0` slides the bar
in over `10` renders, state `1` counts `+0x64` while byte `+0x60` is set, and
state `3` marks time up once `+0x64` reaches the limit. Because the count lives
in the render path, a contest whose renders do not run never times out.

### Controller source

A human side reads the newly pressed mask `+0x68` of pad record `side` (port
`0` for side `0`, port `1` for side `1`), as described in
[Controller input](../runtime/controller_input.md). When the CPU byte is
set, the class generates the input instead.

In Practice (manager mode `3`), a CPU side generates no contest input unless
Practice Status is COM (key `0x0C == 1`) or Attack is Ultimate Jutsu
(key `0x0D == 5`).

`FUN_0035E990` gives each class its CPU interval `I` and miss chance `M`:

| CPU tier | Difficulty | `I` | `M` |
| ---: | --- | ---: | ---: |
| `0` | Simple | `10` | `35` |
| `1` | Easy | `8` | `30` |
| `2` | Normal | `6` | `25` |
| `3` | Hard, Insane | `5` | `15` |
| `4` | Ultimate | `4` | `10` |

## Command mode

State `0` generates one 256-entry sequence copied to both sides. Codes `0..3`
are Triangle, Cross, Circle, and Square; codes `4..7` are Up, Down, Right, and
Left. Each entry is a face button when a draw below `100` is less than
`75 + bias`; bias starts at `0`, returns to `0` after each face button, and
rises by `10` after each direction.

State `7` copies the time limit, resets both sides, and moves to state `9`.
State `9` waits `15` updates before starting the time bar. Each side then
advances through its own copy of the sequence:

- a matching press counts `+0x8C + side*2`, advances position
  `+0x312 + side*2`, and plays a hit sound;
- a wrong press plays a miss sound, vibrates a human side's controller when
  `FUN_001F41A0(side + 1)` allows it, and blocks that side for `6` updates.

After each correct press the meter becomes
`(count0 - count1) * 2.5`, clamped to `-10..10`. When time is up and neither
side is mid-animation, state `3` resolves the contest.

A CPU side acts once every `2I` updates. It draws `0..100`; above `M` it presses
the correct code, otherwise it presses a random code `0..7`, which can still be
correct.

## Timing mode

`FUN_00367510` and `FUN_00367890` give each side its own random face button
`+0x130 + side` (`0..3`, as in Command) and one of eleven five-entry launch
schedules at `0x005AC920`, chosen with `FUN_00180210(10)`. Each side has five
notes (`0x30` bytes each from `+0x13C + side*0xF0`). The schedules' first
entries are `0`, `5`, or `10` updates, and later gaps are `5`, `6`, `10`, `12`,
or `15` updates.

From state `9`, notes launch on schedule and each launched note advances one
step every `3` updates; the first three notes stay one update longer on step
`16`. Presses and CPU decisions count only while the time bar is counting.
Scoring is handled by `FUN_00369510`:

- a press of the side's button while any note is on step `16` hits the first
  note on step `15` or `16`, counts `+0x8C + side*2`, and vibrates a human
  side's controller when allowed;
- a press while the first such note is on step `15` and none is on step `16`
  misses that note;
- a note that passes step `16` unhit is missed;
- other buttons and presses with no note on step `15` or `16` are ignored.

The meter is `(hits0 - hits1) * 2.5`, clamped to `-10..10`. With five notes, at
most five hits count per side.

The CPU decides once per note, when it reaches step `16`
(`FUN_00369D00`). It misses when its hits already reach the tier cap
`{1, 2, 4, 4, 5}` at `0x005D4438`, or in the Practice case above; otherwise it
hits when a draw from `0..100` is above `M + 10`.

## Turn mode

A human side uses the right stick when its magnitude is at least `32`,
otherwise the left stick. Magnitude below `32` on the chosen stick is neutral.
The stick angle becomes one of eight 45-degree sectors.

`FUN_00365840` gives each side two trackers from `0x005AC840`, one for each
rotation direction. A tracker starts in any quadrant and must pass the other
three quadrants in order and return to the start. Neutral input, a sector from
the tracker's reject list, or more than `5` updates outside its current and next
quadrant resets it.
Each completed turn (`FUN_00365AC0`) counts `+0x8C + side*2`; its duration only
changes the sound pitch. Turn has no miss penalty or lockout.

The meter is `(turns0 - turns1) * 5 / 3`, clamped to `-10..10`.

A CPU side holds magnitude `0x2A` and sweeps the angle through one full turn
every `I + 4` updates.

## Combo mode

State `0` chooses one face button (`0..3`) at `+0xEE` for both sides. Each
press of it counts `+0x8C + side*2`; the update after a counted press ignores
that side's input, so at most one press counts every two updates. Another face
button is a miss: sound, vibration for a human side when allowed, and a
`6`-update lockout. Directions are ignored.

The meter is `(count0 - count1) * 5 / 3`, clamped to `-10..10`.

A CPU side presses the correct button every `I - 1` updates and never misses.

## Sign class

`ccInputMatchSign` (mode `6`) is created only by an explicit mode `6`, which the
Battle Settings and Practice selectors cannot produce. Its update
`0x003661F0` builds one shared row of `15` random face buttons. Side `0` works
from the first entry upward and side `1` from the last entry downward; a correct
press claims the entry and counts, and a wrong press locks the side for `3`
updates. A side is done when it runs off the row or reaches an entry the other
side has claimed, and the contest resolves at time-up or when both sides are
done. The meter is `(count0 - count1) * 2.5`. A CPU side presses its correct
button every `2(I - 1)` updates.

## Resolution

Every class resolves through `FUN_0035F610`. It reads the meter from the
attacker's side, `v = meter` for side `0` and `-meter` for side `1`, and the
record damage `D` from `FUN_00372BB0`, which is record `+0x10` times `0.01`.

| Attacker meter | Status `+0xD8` | Attacker / defender flags | Added damage total |
| --- | ---: | --- | --- |
| `v < -5` | `4` | `0x12` / `0x11` | `0.66 D`, then cleared |
| `-5 <= v < 0` | `1` | `0x01` / `0x41` | `0.66 D` |
| `0 <= v <= 5` | `1` | `0x01` / `0x02` | `D` |
| `v > 5` | `1` | `0x21` / `0x02` | `D + 0.08` |

Because the meter scale differs, the leads that cross these limits are:

| Mode | Defender lead for `0.66 D` | Defender lead for status `4` | Attacker lead for the bonus |
| --- | --- | --- | --- |
| Command, Timing | `1..2` | `3` or more | `3` or more |
| Turn, Combo | `1..3` | `4` or more | `4` or more |

Result state `3` sets a first result sprite per side (`1` for a side whose
flag bit `0` is set) and waits until the render path's `FUN_0035F770` has
shown it for about `21` renders. State `4` sets a second sprite through
`FUN_0035FEA0`: `3` for an attacker with flag `0x20`, `1` for a defender with
flag `0x40`, `2` for a defender with flag `0x10`, and none otherwise. It waits
until `FUN_0035FA60` has shown it for about `28` renders; that routine ends at
once when `0x00607780` is `2`, or for status `4` once `FUN_0035DB20(1)` accepts
the current frame. Both waits therefore also depend on the render path.

After the second wait, if attacker flag bit `1` is set (status `4`), the class
clears the damage total, sets the effect ID to `-1`, clears `0x00604314`, and
resets the attacker's condition slot `7` to `-1`. Otherwise it keeps
`0x00604314` at `1`. It then finishes.

`FUN_0035DB20(n)` accepts once the cinematic frame reaches entry
`skill - 1` of the halfword table pointed to by `0x0060774C`, minus `n`. That
pointer is copied from loaded-data pointer `0x00607728` at `0x00357F9C`. For status
`4`, the presentation writes `2` to `0x00607780` and requests skill-play branch
`2` at that frame. Value `2` makes `FUN_0035B3B0` skip the post-Ultimate-Jutsu
transformation; see [Awakening](awakening.md).

## Damage

HP is normalized, so `D = 0.25` is a quarter of full health. `FUN_0035B740`
runs on each cinematic frame. The skill's hit table is `0x005D3D20 + skill*8`
(count, pointer); each 8-byte hit has the frame `+0x00`, a popup flag byte
`+0x02`, a sound byte `+0x03`, a damage fraction `+0x04`, and a chakra fraction
`+0x06`, both divided by `32768`. When the cinematic frame equals the next
hit, it damages the opponent through `FUN_002252E0`. That wrapper calls the
calculator in [Damage](damage.md#calculator-formula) with flag `0x100` only, so
Ultimate Jutsu damage is scaled by the handicap factors and by nothing else,
then applies it with `FUN_00225050(damage, target, 1)`, so Practice HP stops at
`0.01` as for other damage.

- While the damage total is zero, a hit deals `D * fraction` and adds it to the
  dealt amount at skill-play record `+0x20`.
- Once the total is nonzero, the first such hit divides `1.0` by the sum of the
  remaining fractions. Each remaining hit then deals
  `(total - dealt) * fraction / sum`, so the remaining hits deliver the
  resolved total.
- After each hit, if `0x00604314` is `1` and the target's HP is `0` or less,
  the attacker's condition slot `7` becomes `1`, which blocks transformation.
- A chakra fraction of at least `0.00001` removes `fraction * 15.0` chakra from
  the target through `FUN_00225780`.

For status `4`, hits between the result and the clear share the reduced
`0.66 D` total; any hit that still plays after the clear uses the unscaled
`D * fraction` again. The branch-`2` cut described above normally ends the
cinematic near that point.

`FUN_0024ED40`, the coordinator's state-`6` handler, applies the effect ID from
`0x00604310` to the attacker through `FUN_00307690` when it is not `-1` and the
target was not defeated.

## HP damage trail and HUD transitions

In the clean BTL image, runtime `0x0071AF30` (Ghidra `0x0071AEF0`, file
`0x67030`) updates each side's HUD children before its slide transition.
The HP child pointer is parent `+0x24`; its update call at file `0x67060`
targets runtime `0x0071C000` (Ghidra `0x0071BFC0`). This call has no parent
visibility gate. The draw dispatcher at runtime `0x0071B2E0` skips its children
when parent byte `+0x54` is `1`.

The parent stores side `0` or `1` at `+0x0C` and the fighter pointer at
`+0x14`. The HP child stores its parent at `+0x00`, current normalized HP at
`+0x08`, trailing HP at `+0x0C`, and an integer delay at `+0x10`. Its constructor
at Ghidra `0x0071BF20` initializes trailing HP from fighter `+0x6C` and clears
the delay. Each native update samples that fighter field into current HP.
When current and trailing HP are equal, it sets the delay to `100`; otherwise
it decrements a positive delay. Once the delay reaches zero, trailing HP moves
toward current HP by `0.01` per update, clamped at current HP.

The HP renderer at runtime `0x0071C0E0` (entry Ghidra `0x0071C0A0`) draws a
separate segment only when trailing HP exceeds current HP. The segment covers
their difference and uses RGB `(0x4A, 0x04, 0x09)`. Current HP and the trail are
display fields; their updates do not write fighter health.

Resident `0x001F1820(-1)` requests hiding by setting each parent `+0x48` to
`0`; `0x001F1A20(-1)` requests showing with value `1`. The hide update moves
parent Y offset `+0x3C` to `-120.0`, then sets visibility byte `+0x54` to `1`.
The show update clears that byte while sliding toward Y offset `-2.0`, then
clamps there. Visibility alone therefore does not establish that the bar has
finished returning onscreen.
