# Ultimate Jutsu

How retail NA2 (`SLPS-25837`) starts an Ultimate Jutsu, runs its presentation
and input contest, resolves the contest, applies damage and outcome, and
drives the CPU side.

## Research coverage

- **Assigned scope:** Ultimate Jutsu start after a connecting hit, the BTL
  presentation state machine, the resident contest objects for every native
  Battle Settings mode, contest resolution, cinematic damage and outcome
  application, CPU contest input, and the interruption-animation task.
- **Exploration depth:**
  - Instruction-level traces of the connection path
    `FUN_00244F80 -> FUN_00216EA0`, the BTL presentation state machine at live
    `0x00769790`, the skill-play constructor `FUN_0035CF00`, and the mode
    dispatcher `FUN_0036B6D0`.
  - The common contest base (constructors, base update/render, time bar, CPU
    tier, result, result displays, result flags), every class update and its
    initializers, the cinematic hit callback `FUN_0035B740`, the
    post-cinematic handler `FUN_0024ED40`, and the jutsu-slot attempt in the
    BTL AI helper at live `0x006F8810`.
  - Direct-`jal` scans of the resident image and BTL for the contest
    accessors; a store scan for status `+0xD8` in the contest code.
  - The CCS tag-5 endpoint parser, facing helpers
    `FUN_0021B8D0..FUN_0021B9A0`, the ten-row support-dependent voice lookup,
    all 183 branch-frame entries in `STRMCMN.CCS`, the dynamic action selector
    `FUN_002449C0`, the result atlases in `OUGI.CCS`, the interruption task
    `FUN_00373690 -> FUN_00373240`, every nested `ANM_strbreak` command and
    all 72 piece bindings.
  - Render routines only for their timing and result-state effects, not
    layout.
- **Confirmed coverage:** the connection gates and chakra tier charge; the
  presentation timeline and its skill-play admission; all contest classes and
  their update/render pairs; the common lifecycle, time limit, render-path
  timer, difficulty-to-CPU tier mapping, and per-side controller source;
  input, scoring, meter scale, and CPU behavior for Command, Timing, Turn,
  Combo, and the unreachable Sign class; the shared result thresholds, damage
  multipliers, and result displays; per-hit damage, handicap-only scaling,
  chakra drain, effect application, and defeat-latch writes; the CPU's
  jutsu-slot attempt gates and facing requirement; the cinematic endpoint used
  by the time limit; the support/primary identity pairs controlling the
  additional intro voice; the common branch frame `126`; the action slot
  selected for each tier and class; the Japanese result labels; the grayscale
  interruption path and its release flag; Command/Combo retention through
  lockout and Combo rearm; and the 72 interruption pieces' authored
  transforms, shared alpha keys, texture binding, and two-frame advance step.
- **Unresolved or untested:** no producer of contest status `2` was found, so
  the presentation's status-`2` branch has no known trigger; a writer outside
  the inspected paths remains unexcluded (see
  [Status-2 producer boundary](#status-2-producer-boundary)).
  `ANM_strbreak`'s exact projected appearance remains unestablished. Static
  instruction and asset reads do not establish measured display timings.
- **Deliberate exclusions and overlap:**
  - Triangle staging and chakra reservation belong to
    [Chakra and guard](../combat/chakra_and_guard.md); post-Ultimate Jutsu
    transformation, the Ultimate Jutsu record table, and character lists to
    [Awakening](awakening.md).
  - Cinematic selection and authored per-participant substitutions belong to
    [Ultimate Jutsu cinematics](ultimate_jutsu_cinematics.md).
  - Practice option storage belongs to [Practice mode](../modes/practice_mode.md);
    selector routing of the presentation controller to
    [Pause and replay](../session/pause_and_replay.md).
  - HUD hiding, the HP damage trail, and shake belong to
    [Battle HUD](../session/battle_hud.md); stream activity and cinematic cue rows to
    [Battle audio](../session/battle_audio.md).
  - Shared-pad publication belongs to
    [Controller input](../../runtime/controller_input.md); general CCS transport
    and resource lookup to [CCS runtime](../../game/files/ccs_runtime.md);
    record-type identities to
    [CCS object types](../../game/files/ccs_object_types.md); curve evaluation and
    target application to [Animation runtime](../../runtime/animation_runtime.md).
- **Evidence limitations:** conclusions come from static reads of the clean
  resident and BTL images and the named clean CCS resources. Cinematic
  playback frames, update counts, and render counts are distinguished where
  used; none is a measured display duration. Direct-call scans do not exclude
  indirect callers, and the status scans do not prove whole-game
  unreachability of status `2`.

## Addresses

Binary identities and address conversions follow
[Retail game file identities](../../game/files/file_identities.md#address-conventions).
Resident addresses are runtime addresses; BTL addresses are live addresses.
Resident `gp` is `0x0060A9F0`.

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
are described in [Chakra and guard](../combat/chakra_and_guard.md). The Triangle staging
debit `chakra -= 5.0 * (level + 1)` in `FUN_00248EC0` takes its `5.0`
constant from runtime `0x002491B0` (ELF file `0x1492B0`).

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
  [Damage](../combat/damage.md#native-damage-calculation) (target `+0xE54`, then
  `FUN_002179F0` on `+0xE58` and `+0xC74`), so the Ultimate Jutsu attack itself
  has hit the target.

The flag gives the jutsu level: `0x00100000` is `0`, `0x00200000` is `1`, and
`0x00400000` is `2`. The routine then releases the attacker's reservation and
charges `5.0`, `10.0`, or `15.0` chakra for tier `attacker+0x18C` `0`, `1`, or
`2`, subject to the spend gates in [Chakra and guard](../combat/chakra_and_guard.md). It
releases the target's reservation and calls `FUN_00216EA0(attacker, level)`.

The jutsu-class action slots `4..9` that carry these flags, and the Triangle
selection that reaches them, are described in
[Action commands](../combat/action_commands.md#representative-chakrajutsu-path).

`FUN_002449C0` selects the currently usable Ultimate Jutsu action rather than
leaving its slot entirely to the character's original action table. The tier
and category selection is described in
[Awakening](awakening.md#effect-to-form-mapping-and-resource-replacement).
After that selection, it uses this mapping:

| Selected tier | Category flag | Ordinary record slot | Class-7 record slot |
| ---: | ---: | ---: | ---: |
| `0` | `0x00100000` | `4` | `7` |
| `1` | `0x00200000` | `5` | `8` |
| `2` | `0x00400000` | `6` | `9` |

The class comes from record `+0x08` through `FUN_00372C40`; class `7` also
copies the record effect to fighter `+0x18A`. Tier `0` can replace its record
through the support/primary lookup documented below. The record's own tier
byte `+0x09`, read by `FUN_00372CB0`, supplies fighter `+0x18C` and the `5/10/15`
chakra cost; that byte is distinct from the slot-selection tier. The selector
writes the chosen slot's category, name, and cost at action-record
`+0x10/+0x08/+0x20`, clears those three fields in the other five slots, and
stores the selected Ultimate Jutsu record in manager
`+0x60 + side*0x28`. A tier-remap result of `-1` clears all six slots. With an
unchanged tier and a nonnegative remap result, the function returns before
rewriting them. The write loop is `0x00244D14..0x00244DBC`.

`FUN_00216EA0` clears both fighters'
[update-pause block](../combat/hit_response.md#fighter-update-pause-and-action-lock)
through `FUN_00224470(fighter, 0, 1)` and sets both
[hit-rejection countdowns](../combat/hit_response.md#accepted-hit-rejection-countdown)
to `60` through `FUN_002247D0(fighter, -60, 1)`. Unless the battle coordinator
is already in state `6`, it switches the coordinator to state `6` with the
attacker at `+0x24`,
the target at `+0x28`, and the level at `+0x20`, then requests presentation
selector `13 + level` with the attacker's side. BTL collapses selectors
`13..15` to the Ultimate Jutsu presentation described next.

### CPU attempt

The AI slot layout and profile parameters are in
[Battle AI](../session/battle_ai.md). In its state-`15` helper at BTL live `0x006F8810`,
the jutsu-slot attempt runs only when the slot's countdown `+0xB4` is zero and
the Ultimate Jutsu setting (key `5`, read at live `0x006F8BD0`) is positive.
It then requires all of these:

- a draw from `0..100` below profile parameter `16` (`+0x180`:
  `0/0/0/50/60/70` from Simple to Ultimate);
- a valid record for the cached slot `+0x1B0` (first usable slot among `4..9`);
- for slots `7..9`, planar distance `+0x0C` of at least `800.0`; for slots
  `4..6`, distance at most record `+0x34` unless that value is `10000.0` or
  `-17320.5`;
- different facing-direction halfwords `+0x990` on the two fighters;
- `FUN_00225940` affordability of the tier byte of Ultimate Jutsu record
  `(int)record[+0x20]` through `FUN_00372CB0`.

When all pass it queues the slot through `FUN_0021D380`. A failed later test
skips the queue; either way `+0xB4` reloads from parameter `18` (`+0x184`). A
failed chance or missing record instead goes to the helper's other masked
action attempt (parameters `15` and `17`) described in
[Battle AI](../session/battle_ai.md). The affordability call passes a record index derived
from the action cost rather than the cost itself; whether that is intended
cannot be established statically.

The facing interpretation is established by resident `FUN_0021B8D0`, which
accepts only `0` or `1` and can write that value to `+0x990`, and
`FUN_0021B930`, which derives it as `!(fighter[+0x48] > 0.0)`.
`FUN_0021B9A0` copies direction halfword `+0x326` into the selected direction
fields and uses `+0x990 & 1` to select `+pi/2` or `-pi/2` from
`0x005C16B0` for orientation vector `+0x48`. Its exact write/read pair is
`0x0021B9D8..0x0021BA04`. Thus the CPU inequality requires opposite binary
facing directions; it does not by itself prove that either fighter is looking
toward the opponent's current position.

## Presentation state machine

BTL live `0x00769790` (file `0xB5890`) runs the presentation. Its object keeps
the state at `+0x00` and a countdown at `+0x04`. The side is the signed byte at
controller `+0x0C`. The Ultimate Jutsu record index is the side's manager word
`+0x60`.

| State | Behavior |
| ---: | --- |
| `0` | Loads the cut-in models and text, then sets the countdown to `100`, to `130` when the record's `+0x04` is `0x9C`, or to `150` for the alternate-voice case below. Plays voice `+0x0A` of the record on stream bank `1`, slot `0`. |
| `1` | At countdown `100` (`150` in the alternate-voice case) hides the clock and both lower HUD panels with `0x001F1820(-7)`; the top panels stay visible (see [Battle HUD](../session/battle_hud.md#visibility-and-shared-transforms)). At countdown `100` sets both fighters' update-rate override `+0x1B0` to `0.05`. At countdown `85` creates the skill play and its contest. Ends at zero, or early once the voice stream has played and stopped after countdown `85`. Then sets both fighters' `+0x1B0` to `0`. |
| `2` | Waits until `FUN_001CE7F0` reports the skill play's hold point (or counts down `30` when no manager exists), then sets contest byte `+0xD4` through `0x0036C180`, which starts the contest. |
| `3` | Counts down `12`, sets both fighters' `+0x1B0` to `1.0`, stops the voice stream, and clears the skill play's hold flags through `FUN_001CE840`. |
| `4` | Polls contest status `+0xD8`. Status `2` requests skill-play branch `1` through `FUN_001CDDD0`. Status `4` writes `2` to `0x00607780` and requests branch `2` once `FUN_0035DB20(0)` accepts the current frame, then moves to state `5`. When the skill play finishes, writes `1` to `0x00607780` and exits. |
| `5`–`7` | Wait for the skill play to finish and for the flag at `0x00607778`, then exit. |

`FUN_001CDDD0(player, n)` independently latches `n + 1` into player bytes
`+0x281` and `+0x282` only while the respective byte is zero. `PlayDecode`
clears `+0x281` when advancing normally to another request; a value of `2`
or more instead ends the request list without that clear. The current-scene
latch can accept another request after an ordinary advance, while `+0x282`
retains its first request for the player lifetime. The distinct advance and
skip paths are corroborated by bytes `0x001CE778..0x001CE7A4`.
The general controls belong to [CCS runtime](../../game/files/ccs_runtime.md#player-controls).
A `+0x282` value of `2` or more makes the
player's entry loops jump entry index `+0x274` to entry count `+0x272`. A
`+0x281` value of `1` or `3` stops the current scene through `FUN_001A00C0`, and
any nonzero `+0x281` skips the normal entry start at `0x001CE4D8`. Branch `2`
therefore stops the running scene and jumps to the end of the entry list, and
`FUN_001CDD80` reports the player finished once both indices reach the count.
Inference: a status-`4` result cuts the rest of the cinematic, including any
hit frames it had not reached.

The cut has a separate presentation task. The BTL render entry at live
`0x0076A8E0` calls `FUN_00373690(attacker_side)` whenever presentation state
is `5`; the callsite is live `0x0076A9F4` (Ghidra `0x0076A9B4`). That helper
creates `ZgBreakScreen` only while its task handle is zero. `FUN_00372DF0`
prepares `BLT_strbreak`, `TEX_strbreak`, and `ANM_strbreak` from the common
`strmcmn` container; their literals are at `0x005AFE70..0x005AFEA0`.
Its image-copy path is `FUN_00109860 -> FUN_00109430`, followed by the
texture readback `FUN_0010F790` in task body `FUN_00373240`.

The task converts each captured pixel to grayscale with
`g = (77*R + 151*G + 28*B) >> 8`, preserving alpha. It holds the break
animation near its start through `FUN_003730C0(1)`, yields for a countdown
of `15`, and may play a defender voice on bank `1`, slot `0`, using
`FUN_001D9620(8, defender_id - 1, 0)`. The voice is omitted when
`FUN_001F7AA0(defender_id)` is nonzero or the defender is `0x27`.
The subsequent wait has a `60` countdown before a voice start is observed
and a total `90` countdown. It then advances the break animation without
the hold, sets byte `0x00607778` to `1`, and continues until the animation
ends before freeing its owned resources.

The byte is therefore a release flag after the voice wait, not proof that
the break animation has finished. BTL's state-`7` read calls resident
`0x00373770`, whose bytes load exactly that byte. The task can still be
finishing when the presentation proceeds to restore the HUD. The common
archive contains `ANM_strbreak` as record `147` at decompressed `0x4170`
(block size `0xC630`), and `TEX_strbreak` as record `233` at `0x27D38`
(block size `0x40024`). The captured image and grayscale conversion are
established statically; the animation's exact visible motion is not.
The state transitions above are established from the instructions at Ghidra
`0x0076A4A0..0x0076A5EC`.

Fighter `+0x1B0` is the update-rate override described in
[Hit response](../combat/hit_response.md#fighter-fields-used-by-the-response-machine).
The [status-producer investigation](#status-2-producer-boundary)
has not recovered a producer for the presentation's status-`2` branch.

On exit it shows the HUD with `0x001F1A20(-1)` and writes condition statuses
described in [Match outcomes](../session/match_outcomes.md).

The presentation's calls to `FUN_001D99B0(1, 0)` at live `0x00769F94` and
`0x0076A1F0` (file `0xB6094` and `0xB62F0`) read the cached activity of mono
voice slot `0`, not controller input; the cache is described in
[Battle audio](../session/battle_audio.md#cached-stream-activity-and-replacement). The
voice is started on bank `1`, slot `0` by
`FUN_001D9620(7, voice, 0) -> FUN_001D97D0 -> FUN_001D6F60`. Latch `+0x3A` is
therefore "the voice has started", and its clear-on-stop edge ends the intro.
When the alternate-voice case applies, that edge instead plays record voice
`+0x0C` once and continues the countdown.

The alternate-voice case requires record category `+0x06 == 2` and a match in
the ten-entry BTL table at live `0x008D2660` (Ghidra `0x008D2620`, complete
file `0x21E760`). Each four-byte row is `[support-list ID, primary fighter
ID, s16 replacement skill ID]`:

| Support-list ID | Primary fighter ID | Replacement skill ID | Resolved record index |
| ---: | ---: | ---: | ---: |
| `0x00` | `0x3A` | `0x54` | `117` |
| `0x01` | `0x39` | `0x4F` | `112` |
| `0x01` | `0x3E` | `0x61` | `130` |
| `0x0B` | `0x3F` | `0x65` | `134` |
| `0x0D` | `0x48` | `0x88` | `164` |
| `0x0E` | `0x47` | `0x84` | `160` |
| `0x1B` | `0x3A` | `0x53` | `116` |
| `0x1C` | `0x5D` | `0xB5` | `222` |
| `0x1E` | `0x40` | `0x6B` | `138` |
| `0x21` | `0x59` | `0xA7` | `209` |

At the tier-0 callsite in `FUN_002449C0`, the returned halfword is passed
to `FUN_00372990`, which scans record `+0x04` for that skill ID and returns
the matching record index. A bounded read of the full 223-record table at
`0x005AEC40` establishes every resolved index above. All ten selected records
have category `2`, class `3`, and record tier `0`.

Lookup live `0x00883A30` starts at Ghidra `0x008839F0`; its loop runs exactly
ten rows and returns `-1` without a match. The first argument is the selected
support ID from `manager+0x68+side*0x28`, documented in
[Support mechanics](support_mechanics.md#setup-and-selected-support).
The second is presentation byte `+0x04+side`, initialized from the current
primary IDs `manager+0x4C/+0x74` by
`FUN_001EF330 -> BTL 0x0076E9D0`. The row's primary byte may be `0xFF` as a
wildcard in the lookup, but no clean row uses it. The presentation tests only
whether this lookup matched; the returned replacement skill ID is not
itself the voice ID. It extends the intro to `150` and plays the selected
record's second voice `+0x0C` after the first finishes.

This is a support-dependent cinematic case, not an alternate costume voice.
The same pair lookup is used by `FUN_0035A070`, which calls `FUN_00359BB0`
to substitute named cinematic material/model resources when the selected UJ
category is `2`. That establishes a shared voice/resource dependency without
assigning an unverified player-facing name to these ten combinations.

### Authored interruption animation

**Clean-file observation:** The `ANM_strbreak` record described above declares
`101` frames. A complete walk of its nested command lengths from decompressed
`0x4184` to `0x107A0` recovers 72 `0x0102` object tracks for odd directory IDs
`1..143`, named `OBJ_strbrk00..OBJ_strbrk71`. Every track has flags `0x0412`:
keyed position, keyed Euler rotation, no scale channel, and keyed alpha.
The channel readers `FUN_001A8000`, `FUN_001A4D30`, `FUN_001A30C0`, and
`FUN_001A6520` account for each track's complete declared payload. Every
piece changes both position and rotation; every alpha curve is exactly
`{frame 0: 1.0, frame 35: 1.0, frame 50: 0.0}`. The same animation contains
camera track `0x0503` for record `145`, light track `0x0603` for record `146`,
and frame markers `0..100` followed by end marker `-1`; no loop marker `-2`
appears in this record.

Representative authored vectors, rounded here to five decimal places:

| Piece | Position at frame 0 | Position at frame 50 | Euler rotation at frame 50 |
| --- | --- | --- | --- |
| `strbrk00` | `(76.97718, -84.22642, 0.00005)` | `(70.95950, -98.40812, -3.49707)` | `(79.85712, -39.16872, 103.46084)` |
| `strbrk01` | `(112.67823, -68.93830, 0.00005)` | `(51.20626, -60.39729, -14.38771)` | `(114.00680, 43.25048, 74.84045)` |
| `strbrk71` | `(78.39194, -84.17529, 0.00005)` | `(72.04525, -95.62317, -10.59493)` | `(-174.79240, -19.90574, 57.43475)` |

All three sampled rotations start at `(0, 0, 0)`. The `00` and `71` position
and rotation curves have 17 keys at frames
`0,8,10,12,14,17,20,23,26,29,32,35,38,41,44,47,50`; `01` has 20, also
including `2,4,6`. These are stored transform values, not measured screen
coordinates. Euler curve evaluation and transform application belong to
[Animation runtime](../../runtime/animation_runtime.md#typed-curve-evaluation).

`FUN_00372DF0 -> FUN_001B9930 -> FUN_001B99B0` binds this descriptor to its
animation player and named object records. Sampled external-wrapper blocks
at `0x33D4/0x33E8/0x3960` link track IDs `1/3/143` to same-named model-instance
IDs `2/4/144`, respectively; each stored parent is zero. Their `0x0100`
model-instance blocks select `MDL_strbrk00/01/71` records `230/234/374`.
The external-wrapper and model-instance meanings belong to
[CCS object types](../../game/files/ccs_object_types.md#confirmed-identities), and
the binding/application path belongs to
[Animation runtime](../../runtime/animation_runtime.md#target-binding-and-transform-application).

A bounded read of all 72 wrapper/model-instance pairs and their selected
model headers establishes zero stored parents, one mesh part per model, and
material record `232` for every part. That material's block at `0x1211C`
selects texture record `233`, `TEX_strbreak`. Thus all 72 moving pieces bind
the texture populated by the capture/grayscale path. The texture's
`BLT_strbreak` transfer-group ownership belongs to
[CCS object types](../../game/files/ccs_object_types.md#runtime-tag-0x1000-from-texture-and-clut-construction-image-transfer-group).

`FUN_003730C0` writes the animation step `0x200`, or two frames, before each
advance through `FUN_001BB210` and evaluator call `FUN_001BB6F0`. With hold
argument `1`, it advances only while the current integer frame is at most
`1`; argument `-1` removes that condition. Drawing continues through the
helper in either case. Thus the task holds the beginning of a moving,
rotating, fading piece animation and later releases its authored playback.
The stored curves and bindings establish those transforms, but do not by
themselves establish their exact projected appearance or a display duration.

### Skill-play admission

At countdown `85` the presentation calls resident `FUN_0035CF00(side, a, b,
skill, mode)` only when the record's skill value from `FUN_00372900` is
nonzero and BTL `0x00769630` returns zero. `FUN_00372900` returns record
`+0x04`, but returns `0` when `FUN_00372770` classifies the record below `2` or
as `5`. The mode is the battle-rule byte `+0x105` through BTL `0x006EE560`,
falling back to the side's cached manager word `+0x64`; see
[Practice mode](../modes/practice_mode.md#presentation-options-and-ultimate-gate).

`FUN_0035CF00` builds the `SP Skill Play` task, the skill-play record at
`0x00607714`, and a `0x2E0`-byte cinematic player with callbacks
`FUN_0035A070`, `FUN_0035B740`, `FUN_0035C110`, and `FUN_0035AF20`. The current
CCS container is stored at skill-play record `+0x04`; its `+0x90` is the
current cinematic frame. Unless manager mode `+0x0C` is `6` (Collection), it forwards the
mode through `FUN_0036C120` to `FUN_0036B6D0`, which creates the contest.

Before constructing the player, `FUN_0035CF00` lets `FUN_0035CA80` replace the
requested skill for specific attacker/defender pairs. That selection, the
request setup and draw callbacks, and the authored appearance, draw-state,
placement, and geometry substitutions are described in
[Ultimate Jutsu cinematics](ultimate_jutsu_cinematics.md).

## Contest objects

`FUN_0036B6D0` creates one object and stores it at `0x00607750`. Random
selection is described in
[Practice mode](../modes/practice_mode.md#presentation-options-and-ultimate-gate).
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

### Status-2 producer boundary

Direct stores to contest `+0xD8` in the resident contest region
`[0x0035E000,0x0036C240)` write only status `0`, `1`, and `4`. The base
constructor clears status with `sb zero,0xD8(s0)` at `0x0035E194`; the `1`
and `2` bit values written immediately afterward belong to the distinct byte
`+0xD9`. `FUN_0036B6D0` allocates fresh storage for every class and passes it
through that constructor, as does Command's separate constructor
`FUN_003619A0`; no contest-state template copy occurs in these paths.

No wider integer, floating-point, quadword, or vector store in that region
overlaps `+0xD8` on contest storage, and its two non-stack `addiu` rebases in
`+0xC0..+0xE0` (`0x003613F0`, `0x00361414`) address the per-side
`+0xC0/+0xC4` sprite state and counter. The region's ten `jalr` instructions
belong to dispatchers `FUN_0036BF10/FUN_0036BFF0`, whose six 16-byte
descriptors at `[0x005DCB60,0x005DCBC0)` name only the five class pairs and
the common base pair. Raw-pointer accessor `FUN_0036B6C0` has only the two
manager callers `0x001F0904/0x001F092C`, the factory wrapper `FUN_0036C120`
does not retain the pointer, and the global slot `0x00607750` is addressed
only in the destructor path.

No producer of status `2` was found. This bounds the listed paths; it does not
exclude multi-step address arithmetic, an escaped alias, or an external
writer.

### Lifecycle and time limit

Base update `0x0035EA40` does nothing until `+0xD4` is set. It applies a
pending state and clears `+0x64`. Once `+0xD5` is nonzero it counts two more
updates, then sets state `5` and clears `+0xD4`. Every class update repeats
this logic.

`FUN_0035A070` sets the limit through `0x0036C160` to `70`, reduced to
`last_frame - 90` when the current cinematic CCS container's `+0x94` value
`last_frame` is below `160`. This is an inclusive last frame index, not a
frame count or a field of the `0x2E0`-byte entry-list player. The CCS tag-5
parser `FUN_001B5290` reads one dword `n` and writes `n - 1` to container
`+0x94`; container `+0x90` is the playback cursor used by `FUN_0035DB20`.
The container layout belongs to
[Resident CCS runtime](../../game/files/ccs_runtime.md#container-fields).
The time-limit calculation itself has no lower clamp.

The time bar `FUN_0035EBD0` runs only in the render path, from base render
`FUN_0035EAD0`, which every class render calls. Bar state `0` slides the bar
in over `10` renders, state `1` counts `+0x64` while byte `+0x60` is set, and
state `3` marks time up once `+0x64` reaches the limit. Because the count lives
in the render path, a contest whose renders do not run never times out.

### Controller source

A human side reads the newly pressed mask `+0x68` of pad record `side` (port
`0` for side `0`, port `1` for side `1`), as described in
[Controller input](../../runtime/controller_input.md). When the CPU byte is
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
- a wrong decoded command plays a miss sound, vibrates a human side's
  controller when `FUN_001F41A0(side + 1)` allows it, and blocks that side for
  `6` updates.

Each side retains one pending code at `+0x10E + side*2`. A newly recognized
press overwrites it; no recognized press leaves it unchanged. The lockout
decrements before sampling, and a still-positive value skips consumption
without clearing that code. Processing either a correct or wrong code clears
it to `-1`; a time-bar state other than `1` also clears it. Thus a command
sampled during lockout can be processed when the lockout expires. The matching
instruction gates are `0x00362894..0x003628B0`, with the processing clear at
`0x00362BC0..0x00362BC4`. Shared-pad publication and bit priority belong to
[Controller input](../../runtime/controller_input.md#gameplay-readers-outside-command-history).

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
consumed matching code counts `+0x8C + side*2`; the update after a counted
code rearms that side without processing another code, so at most one counts
every two updates. Sampling still precedes the rearm check: a press in that
update can remain pending at `+0xF8 + side*2` and count on a later eligible
update. Another recognized face button overwrites the pending code and is a
miss when consumed: sound, vibration for a human side when allowed, and a
`6`-update lockout. Directions are ignored.

As in Command, sampling with no recognized press preserves the pending code,
and sampling continues during lockout. A positive lockout skips consumption;
processing or a time-bar state other than `1` clears the code to `-1`.
The rearm skip is `0x003645F0..0x0036460C`, the lockout gate is
`0x00364610..0x0036462C`, and the processing clear is
`0x00364860..0x00364864`. These are one-code latches, not queues: a newer
recognized press can replace an older unconsumed one. They cannot recover
shared-pad publications missed while the outer contest update does not run.

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

The sprite frames have these labels in clean `OUGI.CCS`:

| Atlas | Frame | Label | Meaning |
| --- | ---: | --- | --- |
| `TEX_ougi_spgau1` | `0` | 失敗 | Failure |
| `TEX_ougi_spgau1` | `1` | 成功 | Success |
| `TEX_ougi_spgau2` | `1` | ダメージ軽減 | Damage reduced |
| `TEX_ougi_spgau2` | `2` | 中断成功 | Interruption successful |
| `TEX_ougi_spgau2` | `3` | 大ダメージ | Heavy damage |

`FUN_0035E360` loads the two resources and constructs the sprites with frame
rectangles at `0x005AC1A0` and `0x005AC1D0`. The first atlas is `64x64`; its
failure and success frames occupy `(32,0,32,64)` and `(0,0,32,64)`.
The second is `128x128`; its three label rectangles are `(0,0,32,50)`,
`(32,0,16,60)`, and `(0,64,16,64)`. These are pixel `(x,y,width,height)`
coordinates before normalization. BTL live `0x00766290` normalizes the
vertical coordinates as `1-y/height`, so the decoded file image must be
flipped vertically to read the selected regions in their displayed orientation.
The label identities come from an in-memory decode of those exact atlas
regions, paired with the resident frame-selection code. Atlas 2 frame `0` is
the white backing; frames `4/5` are black/red exclamation marks.

Thus status `4` gives the attacker Failure and the defender Success, followed
by the defender's Interruption successful label. The reduced-damage result
gives both sides Success before the defender's Damage reduced label; the
positive bonus gives the attacker Heavy damage after Success.

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

The clean branch table comes from `STRMCMN.CCS`. Loader `FUN_00357B10` resolves
`strmcmn.ccs` and its `BIN_strtbln4` resource (strings at
`0x005AB678/0x005AB688`). That resource is CCS record `405`, with block header
at decompressed offset `0x68E70` and binary payload at `0x68E7C`, length
`0x5874`. The runtime blob ABI is established by `FUN_001B4BC0`: its `+0x08`
points at the file payload, without an additional length word in that payload.
The payload's `+0x14` word is `0x1980`; the loader adds it to the payload base
and stores the result at `0x00607728`, subsequently copied to `0x0060774C`.
Thus the branch table occupies decompressed
`[0x6A7FC,0x6A96A)`: 183 signed halfwords indexed by skills `1..183`.
Every entry is `126`; the following nine halfwords are zero padding before
the next data table at payload `+0x1B00`.

Consequently `FUN_0035DB20(1)` permits the result display to end at cinematic
frame `125`, and `FUN_0035DB20(0)` permits the presentation's status-`4`
branch at frame `126`, for every clean skill entry. These are comparisons
against the current CCS playback cursor, not contest elapsed time. The table
contents come from decompressing clean `STRMCMN.CCS`; the resident globals
that receive them are uninitialized in the static image.

## Damage

HP is normalized, so `D = 0.25` is a quarter of full health. `FUN_0035B740`
runs on each cinematic frame. The skill's hit table is `0x005D3D20 + skill*8`
(count, pointer); each 8-byte hit has the frame `+0x00`, a popup flag byte
`+0x02`, a sound byte `+0x03`, a damage fraction `+0x04`, and a chakra fraction
`+0x06`, both divided by `32768`. The sound byte is the cue described in
[Battle audio](../session/battle_audio.md#authored-cinematic-frame-rows). When the
cinematic frame equals the next hit, it damages the opponent through `FUN_002252E0`. That wrapper calls the
calculator in [Damage](../combat/damage.md#calculator-formula) with flag `0x100` only, so
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
