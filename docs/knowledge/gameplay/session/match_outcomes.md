# Match termination and outcome flow

This document describes how a retail NA2 (`SLPS-25837`) battle ends: HP and
timer termination, the latched result code, the inner and outer end-of-battle
state machines, session outcome counters, the result-`8` continuation, and
cleanup boundaries. Battle statistics and scoring belong to
[Battle statistics](battle_statistics.md); `FUN_*` and `SUB_*` names are
analysis labels, not original symbols.

## Research coverage

- **Assigned scope:** KO and timeout decisions, result/draw state,
  configured-condition outcomes, session counters, end/result transitions,
  result-`8` continuation producers, and teardown boundaries, in the resident
  executable where it owns battle flow and in BTL where it consumes results.
- **Exploration depth:**
  - Exhaustive within bounded dispatchers: every case in the active inner
    end-sequence dispatcher and resident outer-controller states `1..0x19`,
    plus the wrapper-owned post-result sentinels `0x1D..0x20` in
    `FUN_001F2E70` (resident families `FUN_001EC300..FUN_001EEB10`,
    `FUN_001EEC80..FUN_001F12B0`, and `FUN_001F1E80..FUN_001F2E70`).
  - Exhaustive within explicit reference scans: direct BTL calls to the four
    session outcome/streak accessors, the sole resident caller of result-`8`
    producer `FUN_001EC5E0`, and direct stores/callers of the result field.
  - Bounded traces: the KO/life gate, timer/end-reason path, terminal
    classifier, condition scan (`FUN_001FCCD0..FUN_001FDBB0` and its scoped
    callers), pause results, result-`8` readiness and rebuild routes, session
    counter updater/accessors and their cleanup callees, and the selection
    return boundary in states `3..10`.
- **Confirmed coverage:** the exact classifier for ordinary KO/time results
  `1..4`, condition-derived result `5`, pause-derived results `6/7`, both
  synthetic result-`8` routes, the absence of a proven result-`9` producer,
  timer fields and freeze/end flags, score-route qualification, session
  tally/streak semantics, the separate type-`5` encounter limit, and inner,
  result, and outer cleanup ownership. BTL consumes the result through getter
  `FUN_001EC280` but has no direct call to setter `FUN_001EC270` or to Victory
  request `FUN_00201E90`; result latching and the Victory handoff are
  resident.
- **Unresolved or untested:**
  - Player-facing names for results `5/8/9` and the higher-wrapper signed
    returns; condition menu strings.
  - A latched result-`9` producer: result `9` has consumers but no scoped
    producer, and no literal pointer to the setter exists in either image; a
    computed indirect call or out-of-scope overlay remains possible.
  - A generic best-of-N round counter: none was proven. The six-word block is
    an outcome tally/streak block, and the higher-level encounter index/limit
    shows no round-win threshold.
  - The three other `FUN_001EC300` callers and the screens behind the other
    `FUN_001F48F0` callers. Invocation frequency and presentation timing.
- **Deliberate exclusions and overlap:**
  - Statistics, conditions read from statistics, and scoring belong to
    [Battle statistics](battle_statistics.md).
  - Session construction, teardown order, archive lifetime, and continuation
    rebuilds belong to [Battle lifecycle](battle_lifecycle.md); pause-menu
    construction to [Pause and replay](pause_and_replay.md).
  - Damage calculation belongs to [Damage](../combat/damage.md); timer arithmetic to
    [Timer primitives](../../runtime/timer_primitives.md); Victory rendering and
    layout are an interface boundary only.
- **Evidence limitations:** static evidence only; no PCSX2 runtime trace was
  made, and dynamic confirmation is outstanding. BTL xrefs and function
  boundaries omit significant bodies, so negative conclusions are limited to
  the stated byte/reference scans. Static calls establish per-invocation
  arithmetic and ordering, not scheduler frequency or wall-clock duration.

## Game binary address conventions

Address conventions follow
[Retail game file identities](../../game/files/file_identities.md#address-conventions);
the BTL header fields are listed in
[Overlay ABI](../../runtime/overlay_abi.md#exact-clean-layouts). The result-code
logic itself is resident. The BTL result-object entries consumed by the outer
controller (import live `0x00719580`, dispatcher `0x00719D80`, clear
`0x00719500`, internals `0x00719140/0x00719290`) are tabulated in
[Battle statistics](battle_statistics.md#address-convention).

## Outcome state and decisive fields

The central objects and fields are:

| Address / object offset | Meaning established by use |
| --- | --- |
| `0x00607600` | Battle manager pointer |
| manager `+0x0C` | Battle mode; value `3` activates the nonlethal Practice HP floor |
| manager `+0x18` | Side/configuration selector used by several mode-specific branches |
| manager `+0x1C` | Control assignment written by `FUN_001F48F0`; see [Control assignment](#control-assignment-and-com-sides) |
| manager side-record byte `+0x48` / `+0x70`, bit `0x02` | Side 1 / side 2 COM-controlled bit |
| manager `+0xDE4`, `+0xDE8` | Side 1 and side 2 live fighter pointers |
| `0x00607604` | Active `0x38`-byte inner battle/end-sequence object for the current cycle |
| `0x00607620` | Active `0x44`-byte outer controller; owns state `1..0x19` and the reusable BTL result object |
| `0x00607658` | Transient end-presentation object destroyed by outer state `0x10` |
| `0x00607660` | Pause-flow active flag |
| `0x00607664` | Pause-flow auxiliary pointer/handle |
| `0x00607668` | Pause/menu object pointer |
| `0x00607670` | Latched outcome/result code (`0` while unresolved) |
| `0x00607674` | Timeout/end-reason marker; exposed by `FUN_001EC290` and consumed by the BTL metric importer |
| `0x00607678` | Continuation phase (`1` request, `2` preserve-on-rebuild, `3` consumed) |
| `0x0060767C` | Result-`8` rebuild route (`1` or `2`) |
| `0x00607680` | Inner result-`8` readiness-handshake byte |
| fighter `+0x61`, bit `0x08` | Active/not-KO gate used by the terminal detector |
| fighter `+0x6C` | Current HP as a float; normal full value is `1.0` |
| fighter `+0xB00` | Transient gate that must be zero before countdown advancement |
| `0x006B28D0` | Timer flags byte |
| timer `+0x04` (`0x006B28D4`) | Remaining counter, with whole units in the high byte |
| timer `+0x08` (`0x006B28D8`) | Elapsed counter, same representation |
| timer `+0x14` (`0x006B28E4`) | Configured whole-unit limit |
| timer `+0x1C` (`0x006B28EC`) | Per-update counter delta |
| `0x006B2900..0x006B2917` | Six-word session outcome/streak block |

The outcome API consists of:

- `FUN_001EC270(value)` writes `0x00607670` without validation.
- `FUN_001EC280()` returns it.
- `FUN_001EC290()` returns whether `0x00607674` is nonzero.
- `FUN_001EEE30()` clears the outcome to zero during battle initialization.

The ordinary classifier itself only latches a value when the global is still
zero, so the first ordinary classification is stable. The scripted-condition
branch described below is an exception in the same update.

Raw gp-relative stores give this producer inventory:

| Resident store | Function / value written |
| ---: | --- |
| `0x001EC270` | Generic setter `FUN_001EC270(value)` |
| `0x001EC5F0` | `FUN_001EC5E0`: synthetic result `8` |
| `0x001EEEE4` | `FUN_001EEE30`: initialization value `0` |
| `0x001F0F0C` | `FUN_001F0B10`: condition result `5` |
| `0x001F129C` | `FUN_001F11E0`: ordinary classified result `1..4`, only if still zero |
| `0x001F3370` | `FUN_001F2E70`: synthetic result `8` |

The only direct resident calls to the generic setter are at `0x001EC044` and
`0x001EC058`, both in the pause handler and passing `7` and `6`, respectively.
Clean BTL has two direct outcome-getter calls (live `0x00719604` and
`0x00719F14`) and no call to the setter. This inventory accounts for every
direct gp-relative outcome store and direct setter call in the scoped images;
none writes `9`.

### Outer-controller types

The outer controller's type at `+0x14` is the argument of `FUN_001EC300`.
The Mode Select callback dispatcher documented in
[High-level mode callback dispatcher](../../game/mode_flow.md#high-level-mode-callback-dispatcher)
creates it as type `1` from the Free Battle callback `FUN_001EA8C0` and as type
`2` from the Practice callback `FUN_001EA940`. The routing tables below
therefore describe Free Battle (type `1`) and Practice (type `2`). Three other
resident functions (`FUN_001FEA70`, `FUN_001FED10`, `FUN_001FEF50`) also call
`FUN_001EC300`; they belong to the higher-level flow and were not traced here.

### Control assignment and COM sides

`FUN_001F48F0(manager, mode)` stores `mode` at manager `+0x1C` and rewrites
bit `0x02` of both side-record bytes:

| Manager `+0x1C` | Side 1 bit (`+0x48`) | Side 2 bit (`+0x70`) |
| ---: | :---: | :---: |
| `0` | clear | clear |
| `1` | clear | set |
| `2` | set | clear |
| `3` | set | set |

[Practice Mode](../modes/practice_mode.md) establishes this bit as the per-side COM
bit: Practice's Manual status applies mode `0`, and its other statuses make
the side opposite the human player COM. Outer state `2` (`FUN_001ED000`),
the same handler that zeroes the six-word session block, calls
`FUN_001F48F0(manager, 1)` when manager `+0x18` is zero and
`FUN_001F48F0(manager, 2)` otherwise, so each Free Battle or Practice
controller starts with one human side and one COM side. Manager initialization
`FUN_001F4360` also applies mode `1`. Other resident callers exist
(`FUN_003B9F60`, `FUN_003BB720`, `FUN_003BB7D0`, `FUN_003BBBB0`) but their
triggering screens were not traced here.

The outcome consumers below read this bit for the winning side. Where they
require it to be clear, they require the winner to be human-controlled.

## KO and time termination

### Fighter life gate

`FUN_002151E0` sets fighter life bit `+0x61 & 0x08` at initialization, and
`FUN_00225050` clears it when an accepted HP change leaves HP at or below zero
(in Practice, manager `+0x0C == 3`, HP instead stops at `0.01` with the bit
kept); see [Damage](../combat/damage.md#damage-application).

### Timer path

`FUN_001EEE30` obtains configuration selector `6` through
`FUN_001F6420(manager, 6)`, stores it at timer `+0x14`, copies it to the high
byte of timer `+0x04`, clears elapsed `+0x08`, and clears the result code. A
zero initial counter sets timer expiry bit `0x04` immediately; these functions
do not contain a special zero-as-unlimited interpretation.

`FUN_001EBA80(timer)` is the timer accumulator. If expiry bit `0x04` is already
set it returns `1`. Flag bit `0x01` returns without accumulating; bit `0x02`
skips the subtraction/addition but still permits the final negative-remainder
check. With both gates clear, the helper subtracts `+0x1C` from remaining
`+0x04` and adds the same value to elapsed `+0x08`, capping elapsed at
`0x63000000` (99 whole units). A negative remainder is clamped to zero, elapsed
is normalized to configured limit `+0x14 << 24`, expiry bit `0x04` is set, and
the helper returns `1`.

`FUN_001F10F0(controller)` is the outer countdown gate. It calls
`FUN_001EBA80(0x006B28D0)` only while all of the following hold:

- both live fighter pointers exist;
- both fighter `+0xB00` values are zero;
- both fighter life bits `+0x61 & 0x08` remain set;
- `FUN_00250820()` and BTL `0x007064B0` both report zero;
- the outcome is still zero; and
- controller byte `+0x00` has bit `0x02` set.

Small resident accessors decoded from the raw instructions are
`FUN_001EBBA0` (write timer freeze bit `0x02`), `FUN_001EBBD0` (read that bit),
`FUN_001EBBF0` (rounded-up remaining whole units), `FUN_001EBC10` (elapsed
whole units, clamped nonnegative), and `FUN_001EBC30` (configured limit).

### Terminal detector and classifier

While `0x00607670 == 0`, `FUN_001F0B10` reads both fighters and treats the
battle as terminal when either:

- either fighter life bit `+0x61 & 0x08` is clear; or
- timer flag `0x04` is set.

For either terminal trigger, the detector first calls
`FUN_00216C60(side1_fighter, 1)`. This fixed side-1 call is independent of
which life bit cleared and is distinct from the later result-dependent
`FUN_001F12B0` side selection.

Timeout also sets resident marker `0x00607674` / analysis global
`uGpffffCC84` to `1`; later presentation logic uses this to take a different
end sequence from a non-timeout termination. The detector then calls
`FUN_001F11E0`, which compares current HP only:

```text
if side1_hp > side2_hp: result = 1
else if side2_hp > side1_hp: result = 2
else if side1_hp == 0.0 and side2_hp == 0.0: result = 4
else: result = 3
```

Consequences worth keeping explicit:

- A timeout is not a separate ordinary result code. Unequal remaining HP yields
  side `1` or `2`; equal nonzero HP yields `3`.
- `4` specifically requires both compared HP values to be zero.
- The trigger and classification are separate. The life bit or timer ends the
  battle; HP ordering determines ordinary result `1..4`.
- If the manager pointer is absent, `FUN_001F11E0` returns `9` but does not
  latch it. The normal caller is manager-guarded, so this is not an observed
  producer of latched result `9`.

Later in the same update, `FUN_001F0B10` services an optional manager-`+0xDDC`
condition subsystem whether or not KO/time just triggered. The relevant layout
and globals are:

| Address / field | Proven use |
| --- | --- |
| manager `+0xDDC` | Optional condition-definition object pointer |
| condition object `+0x18` | Signed byte count of configured conditions |
| condition object `+0x1A + index*2` | Signed-16 condition IDs, scanned in stored order |
| condition object `+0x24 + index*4` | Per-condition payload used by the status-change presentation path |
| `0x0060768C` | Condition-flow enable byte, read by `FUN_001FDB80` |
| `0x00607690` | Condition-flow phase/control word, accessed by `FUN_001FDB90` / `FUN_001FDBB0` |
| `0x006B2B40 + side*0x174 + id*4` | Signed 32-bit status for a side/condition pair |

The status area has three banks of `0x5D` entries; this outcome path uses side
banks `1` and `2`. `FUN_001FD7D0` initializes every bank entry to `-1`,
`FUN_001FDB40(side, condition_id)` reads one entry, and
`FUN_001FD850(side, condition_id, value)` changes it. Both writing and scanning
treat a side as active only when bit `0x02` is clear in manager side-record byte
`+0x48` (side 1) or `+0x70` (side 2). The enable byte is set at resident
`0x001FE340` and cleared at `0x001FE3A4` by the enclosing condition flow.

`FUN_001FCF00(manager+0xDDC)` is not a generic “completion” predicate. It
scans the configured condition IDs at subsystem `+0x1A`, and for each active
side returns the first side number whose status is exactly zero. It returns
zero when none qualify. Scan priority is configuration-list order first, then
side 1 before side 2 for each ID. When this scan returns a side,
`FUN_001F0B10` changes phase `0x00607690` from `1` to `3` when applicable and
calls `FUN_00216C60(selected_side_fighter, 1)` on that phase transition. It then
sets outcome `5` unconditionally. Result `5` can therefore arise without a
simultaneous KO/time and can replace a just-computed ordinary `1..4` in the
same update.

At an ordinary KO/time boundary, the same function resolves several condition
statuses before that scan:

- condition ID `1` receives status `1` for the ordinary winner side and status
  `0` for the other configured active side after unresolved-status completion;
- timeout sets condition ID `2` to status `1` for both sides;
- on a KO with ordinary result `1` or `2`, the winning side receives status
  `1` for condition ID `3` when elapsed whole units are below `31`, and for ID
  `4` when below `61`;
- condition IDs `0x18` and `0x1A` are changed from `-1` to `1` for both sides;
  and
- `FUN_001FCE30` then changes every configured condition that is still `-1`
  for an active side to status `0`.

The final zero-status scan occurs after those writes. Result `5` is therefore
best described as the configured-condition/unsatisfied-condition outcome path,
while preserving the exact numeric status semantics for conditions that can
also change during live gameplay.

Condition status has an explicit continuation lifetime. Near the end of
`FUN_001EEE30`, `FUN_001FD7D0` normally resets the table, but the reset is
skipped precisely when continuation phase `0x00607678 == 2` and it is not the
special combination of inner type halfword `+0x0C` equal to `4` or `5` with
route `0x0060767C != 1`. That special combination forces a reset even in phase
`2`; raw branches `0x001EEF64..0x001EEF94` establish the polarity. Outcome
`0x00607670` and timeout marker `0x00607674` are still cleared earlier in the
same initializer. These are separate lifetimes: most continued encounters can
begin with no result marker while retaining condition progress, but the stated
type/route exception cannot.

BTL also writes condition statuses directly through `FUN_001FD850`; its ten
direct writer calls are listed in
[Battle statistics](battle_statistics.md#direct-btl-condition-status-writers).
Three of them, inside live function `0x00769790`, write value `0` for IDs
`0x18` and `0x1A`; that value is directly eligible for `FUN_001FCF00`'s
outcome-`5` scan when the ID is configured and the target side is active.

## Result-code table

| Code | Proven producer/consumer meaning | Confidence |
| ---: | --- | --- |
| `0` | Battle unresolved/active. Required by timer and ordinary classifier. | High |
| `1` | Side 1 has greater current HP at terminal classification. | High |
| `2` | Side 2 has greater current HP at terminal classification. | High |
| `3` | Equal nonzero current HP, normally a time draw. | High for condition; medium for UI wording |
| `4` | Both current HP values are zero. | High |
| `5` | Optional condition subsystem found an active side with an unsatisfied/configured status of zero; this can override an ordinary result. | High for mechanism; medium for original mode name |
| `6` | Pause/control-flow termination selected when the pause object returns `3`: return to Character Select without scoring. | High for source and route; medium for menu wording (prompt text, not traced input) |
| `7` | Pause/control-flow termination selected when the pause object returns `2`: leave the mode for Mode Select. | High for source and route; medium for menu wording (prompt text, not traced input) |
| `8` | Synthetic higher-level continuation/sequence result. `FUN_001EC5E0` and `FUN_001F2E70` are resident producers; outer state `0x10` routes it without normal score initialization. | High for flow; low for original name |
| `9` | Recognized by end-state consumers, but no latched producer was found in the scoped resident direct assignments or clean BTL calls. | High negative result |

Codes `6` and `7` are written through `FUN_001EC270` by pause handler
`FUN_001EBD90`; code `8` is written directly. Ordinary KO/time logic emits only
`1..4`. Giving `6..9` winner/loser names would exceed the evidence.

The pause path also establishes its own cleanup boundary. `FUN_001EBD90` will
not open the pause object while its eligibility checks reject pausing, an
outcome/timeout is already active, or another blocking service is active. It
creates the `0xCC`-byte object kept at `0x00607668`, marks pause-flow global
`0x00607660`, and pauses battle control. Once the object's update returns a
nonzero selection, the handler unpauses first, clears the pause globals,
destroys the object, and clears `0x00607668`. Return `1` then resumes both live
fighters through `FUN_00216460` without setting an outcome; return `2` sets
result `7`; return `3` sets result `6`. Thus results `6` and `7` are latched
only after the menu object that selected them has been torn down.

## End-of-battle state machines

### Inner end sequence

`FUN_001EF8F0` wraps inner state machine `FUN_001EF9C0`. While the inner
machine reports its active state, the wrapper advances input/battle services,
then `FUN_001F10F0` (timer), then `FUN_001F0B10` (terminal detection). This
ordering allows expiry raised by the timer helper to be classified in the same
outer update.

The wrapper's return contract is exact. With no inner object it reports
completion `1`. Inner return `0` runs the services above and remains active;
inner return `2` remains active but skips those services for that update; and
inner returns `1` or `3` report completion to outer state `0x0F`. The
result-`8` readiness helper is the proven source of the `2`/`3` pair.

`FUN_001EF9C0` stores its substate as a halfword at inner object `+0x0A` and a
delay/handle at `+0x10`. Relevant verified branches are:

- Substate `3` clears an overlay-object flag, requests resident battle event
  `8` while the result is still zero, sets substate `4`, and enables the pause
  gate used during the end sequence.
- Substate `4` sends results `6`, `7`, or `9` directly to event `0x17` and
  reports completion. Otherwise, when timeout marker `0x00607674` is set, it
  emits event `0x0A`, emits event/sound `0x32`, calls
  `FUN_001D2D20(0)`, and enters substate `0x0A`. With no timeout marker, a
  nonzero result emits event `9` and enters substate `5`; result zero stays in
  substate `4`.
- Substate `5` chooses the first wait: `0x1E` for `1`, `2`, or `4`; `0x5A`
  for `3`; and, for result `5`, calls `FUN_001D7E20(0x39)`,
  `FUN_001D2D20(3)`, and seeds `0x5A`.
- Substate `6` follows `1`, `2`, and `4` with another `0x5A` wait. Result `5`
  seeds `0x5A`, calls `FUN_001D2D20(4)`, and emits event IDs `0x13`,
  `0x3D`, and `0x46`. The argument `4` is carried in `a0` from the comparison
  at `0x001EFD2C` to raw call site `0x001EFD78`.
- Substate `7` sends winner results `1` or `2` either to substate `8` or
  directly toward fade. Substate `8` is chosen exactly when the manager exists,
  manager field `+0x1C != 3`, and bit `0x02` is clear in the winning side's
  record byte (`+0x48` for result `1`, `+0x70` for result `2`); otherwise it
  goes to fade substate `0x0F`. Draws and special results do not select a
  winner-side record here. By the control-assignment table above, substate `8`
  requires that the match is not COM versus COM and that the winner is
  human-controlled.
- Substate `8` maps result `1` to side index `1`, result `2` to side index `2`,
  calls live BTL `0x0076EDA0(winner_hp, ..., remaining_whole_units)`, then live
  BTL `0x0076EF60(..., winner_side_record, winner_index - 1, 1)`. It also
  clears byte `+0xB0` through the optional inner-object pointer at `+0x20`,
  then enters substate `9`.
- Substates `9` and `0x0F..0x11` wait for the overlay object and fade, then
  report completion.

The timeout-marked route through substates `0x0A..0x0E` is also outcome-aware.
After its BTL overlay gate reports ready:

- results `3` and `4` call `FUN_001D2D20(2)`, seed a `0x5A` wait, and use
  substate `0x0C` before rejoining substate `7`;
- result `5` calls `FUN_001F12B0`, then `FUN_001D2D20(4)`, emits IDs `0x13`,
  `0x3D`, and `0x46`, and passes through substate `0x0E`; and
- the remaining ordinary results (`1` and `2`) call `FUN_001F12B0`, then
  `FUN_001D2D20(1)`, seed a `0x3C` wait, and pass through substate `0x0D`
  toward the fade path.

`FUN_001F12B0`, called during this sequence, also maps result codes to a
fighter-side object before calling `FUN_00216C60(fighter, 0)`: result `1`
selects side 2, result `2` selects side 1, results `3` and `4` select side 1,
and result `5` re-runs `FUN_001FCF00` when the condition object exists. With no
condition object, result `5` instead uses manager selector `+0x18 + 1`. This is
a proven mechanical side effect, but it is not safe to label the selected
object a loser for draw or scripted-condition outcomes.

The `0x1E`, `0x5A`, and other constants above are state-machine wait/event
arguments, not a claim about real-world duration.

### Outer controller

`FUN_001EC300(type)` allocates the `0x44`-byte outer controller at
`0x00607620`; `FUN_001EC690` constructs it, and `FUN_001EC7A0` stores its
battle type at `+0x14`, creates the BTL result object at `+0x3C`, clears that
object through live `0x00719500`, and enters outer state `1`.
`FUN_001EC960` dispatches outer states `1..0x19` and runs the pause handler on
every update.

The outer and inner objects are distinct. Outer state `0x0E` handler
`FUN_001EDB00` waits for its readiness gates, then calls `FUN_001EC3B0(type)`.
That function allocates the `0x38`-byte inner object at `0x00607604`, initializes
it through `FUN_001EEC80` / `FUN_001EEE30`, and calls `FUN_001EF330` to create
its battle-owned subsystems before entering outer state `0x0F`. State `0x0F`
is therefore both the active inner-battle driver and the end-sequence wait; it
does not begin only after a result has already been latched.

The result/cleanup tail is:

| Outer state | Resident handler | Proven work |
| ---: | --- | --- |
| `0x0F` | `FUN_001EDB70` | Drives `FUN_001EF8F0` while the current inner battle is active, including timer/outcome detection and the end sequence. On inner completion it clears an end-sequence gate, performs related teardown, enters `0x10`, and seeds a three-count delay. |
| `0x10` | `FUN_001EDD10` | After the delay, clears the resident Victory request, destroys the transient end-presentation object at `0x00607658`, and handles result `8` specially. Results other than `6`, `7`, and `9` wait for resource readiness and call live BTL metric importer `0x00719580(controller+0x3C)`. Then enters `0x11`. |
| `0x11` | `FUN_001EDEE0` | Releases battle archives (see [Battle lifecycle](battle_lifecycle.md#archive-lifetime-is-separate-from-session-lifetime)), updates the session outcome block, and enters `0x12`. |
| `0x12` | `FUN_001EE060` | For controller type `1`, qualifying winner results enter score setup `0x13`; otherwise it emits event `0x17` and sends result `7` to `0x19`, other results to `0x16`. Type `2` likewise sends only result `7` to `0x19`, all others to `0x16`. |
| `0x13` | `FUN_001EE880` | Waits for resource readiness, creates/loads the BTL result presentation and its fade, then enters `0x14`. |
| `0x14` | `FUN_001EE9C0` | Runs live BTL result dispatcher `0x00719D80`. On its completion return, clears the metric state, destroys the current presentation internals, unloads the presentation resource, and enters `0x15`; the allocation at controller `+0x3C` remains for reuse. |
| `0x15` | `FUN_001EEA80` | Emits event `0x0E` and loops to state `3`. |
| `0x16` | `FUN_001EEAC0` | Waits for resource readiness, then loops to state `3` without the BTL score presentation. |
| `0x17` | `FUN_001EE1C0` | Result-`8` continuation route `1`; queues resident Victory data when a side is selected. The rebuild is described in [Battle lifecycle](battle_lifecycle.md#continuation-encounters-rebuild-the-session). |
| `0x18` | `FUN_001EE500` | Result-`8` continuation route `2`; updates the session outcome block on this alternative completion path before the rebuild. |
| `0x19` | `FUN_001EEB10` | Performs its final resource transition, clears timer freeze bit `0x02`, sets manager mode `+0x0C` to `1`, and makes the outer dispatcher report terminal status `3`. |

Normal state `0x11` and continuation state `0x18` are alternative places where
the outcome counter is committed. Result `8` can skip the ordinary
metric/state-`0x11` route and reach the continuation states directly.

Composing states `0x10` and `0x12` gives the following exact route matrix for
the two handled controller types:

| Result | BTL metric import | Type `1` (Free Battle) after cleanup | Type `2` (Practice) after cleanup |
| ---: | --- | --- | --- |
| `1`, `2` | Yes | `0x13` score route only when the winning side is not COM; otherwise `0x16` | `0x16` |
| `3`, `4`, `5` | Yes | `0x16` | `0x16` |
| `6` | No | `0x16` | `0x16` |
| `7` | No | `0x19` terminal route | `0x19` terminal route |
| `8` | No | Directly `0x17` or `0x18` according to `0x0060767C` | Same special handling |
| `9` | No | `0x16` | `0x16` |

State `0x16` rejoins state `3`, so pause-selected result `6` is mechanically a
no-score restart while pause-selected result `7` is a terminal exit from this
outer controller. These routes match the pause-menu confirmation prompts
decoded in [Pause, start-menu, and battle-restart control](pause_and_replay.md):
the command that returns to character selection produces pause result `3` and
therefore result `6`, whose route reaches Character Select through states `3`
to `7`; the command that returns to game-mode selection produces pause result
`2` and therefore result `7`, whose state `0x19` writes manager mode `1`
(Mode Select). A second command with the generic "end the battle?" prompt also
produces result `6`. A hypothetical latched result `9` would use the same restart
route as `6`; recognizing the code does not establish a producer.

The type-`1` score qualification in state `0x12` is exact rather than a generic
winner test. Result `1` enters state `0x13` only when manager side-record byte
`+0x48` has bit `0x02` clear. Result `2` enters it only when side-record byte
`+0x70` has bit `0x02` clear. Every other type-`1` result takes the non-score
branch described in the table. Raw instructions `0x001EE0DC..0x001EE124`
extract the same bit for each winner and route both zero-bit cases to state
`0x13`. That bit is the side's COM bit, so the result screen and point commit
run only in Free Battle and only when a human-controlled side wins. A COM win,
any Practice result, and every draw or special result skip it.

State `3` handler `FUN_001ED110` resets the timer flags, remaining, elapsed,
configured-limit placeholder, and delta before advancing to state `4` for the
next battle cycle. Consequently, states `0x15` and `0x16` are proven restart
routes, while `0x19` is the terminal route. The higher-level controller still
decides what that terminal return means for the enclosing mode.

Resident Victory request function `FUN_00201E90` stores its six parameters in
the idle object at global `piGpffffCCC0` and sets request byte `+0x2C`.
`FUN_00201ED0` clears that request; `FUN_00201EF0` tests idleness. This is an
interface boundary only. The rendering/layout behavior belongs to the Victory
UI documentation.

### Selection reset and battle-load boundary

The native post-results loop is not an immediate repeat of the same matchup.
State 3 also calls `FUN_001F4D70(manager)`, which clears the three selection
records and stage bytes at manager `+0x20..+0x9A` through `FUN_001F4B60`.
It resets the outer controller's side resource snapshots and calls live BTL
`0x0070F1E0`. The six-word session outcome block is separate and is not cleared.

State 4 (`FUN_001ED230`) queues selection resources when controller `+0x18`
is zero. State 5 (`FUN_001ED300`) waits for the resource fence, adopts the
Character Select, Stage Select, and Settings archives, and enters state 6.
State 6 (`FUN_001ED400`) waits for `FUN_00200670()` before entering Character
Select state 7. That readiness function returns `1` only when the transition
object at `0x006076A0` exists and its first word is zero. Successful Stage
Select state 9 stores the selected stage,
calls `FUN_002005B0(1,0)`, sets the three-count delay, and enters state 10.

State 10 (`FUN_001ED880`) releases those selection archives after the delay,
calls `FUN_001F4DD0(manager)`, requests battle loading with `FUN_001E9520(1)`,
and enters state 11. `FUN_001F4DD0` normalizes the configured jutsu/support
records, resolves equal-character costume conflicts, and saves the three
`0x28`-byte records from `+0x20..+0x97` to `+0x9C..+0x113`, followed by the
three stage bytes at `+0x114..+0x116`. The state-3 clear does not overwrite this
saved block. These paths establish distinct selection-reset, saved-setup,
session-score, and fresh-battle initialization boundaries.

### Results resource loading

In the score-qualified state-`0x12` branch, `FUN_001EE060` queues `xninka.ccs`
through `FUN_001CF9E0` when it is absent, then starts the queue through
`FUN_001CFCD0(0)` at resident `0x001EE160`. State `0x13` waits for
`FUN_001CFD70`, constructs the result presentation, and only then starts its
entrance transition and enters state `0x14`. Result initialization at live
`0x00719ED0` runs inside the subsequent presentation dispatcher.

The resident archive helper `FUN_0037E1A0` first checks `FUN_001AA450`. A cache
miss calls `FUN_00116DE0` and enters the synchronous loader `FUN_001CF3F0`,
which yields to the scheduler until its read/decode flags complete.

## Session outcome and streak counters

`FUN_001ED000` zeroes all six words at `0x006B2900..0x006B2914` once during
outer-controller startup. `FUN_001EC090(block, result)` updates them:

| Block offset | Update |
| ---: | --- |
| `+0x00` | Increment for result `1` |
| `+0x04` | Increment for result `2` |
| `+0x08` | Increment for result `3` or `4` |
| `+0x0C` | Increment for every other result |
| `+0x10` | Consecutive same-winner count; reset to zero by `3` or `4` |
| `+0x14` | Consecutive winner code (`1` or `2`); reset to zero by `3` or `4` |

For a winner code, `+0x10` increments when `+0x14` already matches; otherwise
the type changes and the count becomes one. Results outside `1..4` increment
the other-result bucket and leave streak fields unchanged. The resident update
does not saturate any of the six 32-bit counters; only the BTL presentation
consumers described below clamp displayed values.

The update occurs during completed teardown (`FUN_001EDEE0`) or its alternative
continuation route (`FUN_001EE500`), not when HP first reaches zero. The
resident raw code also supplies four accessors:

| Function | Return value |
| --- | --- |
| `FUN_001EC180()` | `+0x00 + +0x04 + +0x08`: total ordinary outcomes (`1..4`) |
| `FUN_001EC1B0(side)` | Side-1 count `+0x00` or side-2 count `+0x04`; zero for other inputs |
| `FUN_001EC200()` | Draw/double-zero bucket `+0x08` |
| `FUN_001EC210(side)` | Streak count `+0x10` only when `side == +0x14`, otherwise zero |

Clean BTL is a direct presentation consumer of these accessors:

- live `0x006BE248` and `0x006BE26C` query the selected and opposite side's
  current streak and choose one of three internal presentation variants;
- live `0x006BF0D8..0x006BF11C` obtains selected-side count, ordinary total,
  draw/double-zero count, and selected-side streak. Its arithmetic derives the
  other-side ordinary count as `ordinary_total - selected_side_count -
  draw_count`; numeric presentation values are clamped to `0..99`; and
- live `0x006C0AE0` reads `ordinary_total + 1`, also clamped to `0..99`, for a
  separate counter presentation.

These are encoded calls to resident addresses, so the BTL `+0x40` function
mapping does not alter their targets. The access pattern confirms the block's
session-outcome and streak interpretation. It is not itself evidence of a
best-of-N rule; the separate sequence counter is described below.

An exhaustive direct-call scan found no resident caller of any of the four
accessors. The BTL sites listed above are all direct calls in clean BTL, and
they test streak only for zero/nonzero or format clamped numeric values; none
compares a win/draw count with a termination threshold. This strengthens the
negative result: the six-word block is not the scoped match-limit mechanism.

## Higher-level sequence counter and result-8 continuation

A separate resident flow object created by `FUN_001F1E80`, cleared by
`FUN_001F1F30`, and initialized by `FUN_001F1F70(object, type)` provides the
counter that the six-word outcome block does not. Its relevant fields are:

| Object offset | Proven use |
| ---: | --- |
| `+0x00` | Higher-level flow state |
| `+0x04` | One-based current encounter counter after higher-flow state `4` initializes it |
| `+0x08` | Type-`5` encounter limit; `99` sentinel in the other initialized flows |
| `+0x0C` | Cumulative elapsed whole units |
| `+0x14` | Flow/battle type |
| `+0x18` | Snapshot of the manager condition-subsystem pointer |
| `+0x1C` | Pointer to resident data at `0x006B2990` |
| `+0x30` | Optional type-`5` sequence-definition pointer |
| `+0x34` | Optional randomized selection table created for type `4` |

When the higher flow reaches state `4`, it initializes counter `+0x04` to
`1`. For a valid type-`5` sequence-definition pointer it reads the signed-16
limit from definition `+0x08`; otherwise it uses `99`. Type `5` also indexes
three-byte per-encounter records through definition pointer `+0x04`. These
uses make `+0x04` an encounter ordinal and `+0x08` a real type-`5` sequence
limit, not a win count.

The continuation comparison is signed `current_counter < limit`. Because the
counter starts at `1`, a positive type-`5` limit `N` permits at most `N` total
encounters: the continuation after encounter `N` is suppressed. A limit of
`1` or less suppresses the first continuation; no positive-range validation is
visible here. The `99` value does not impose a limit on non-type-`5` flows,
because their type check bypasses the counter comparison.

`FUN_001F2E70` watches the active outer controller while it remains in state
`0x0F`. When the inner end sequence has reached substate `8`, it adds current
timer elapsed whole units (`timer + 0x08`, high byte, clamped nonnegative) to
object `+0x0C`. Unless flow type is `5` and counter `+0x04` has reached limit
`+0x08`, it then:

1. increments counter `+0x04`;
2. chooses selection index `2` for result `1`, otherwise index `1`;
3. writes resident flow globals `0x00607678 = 1` and `0x0060767C = 2`;
4. writes synthetic outcome `8`;
5. sets byte `1` at `manager + selection_index * 0x28 + 0x28`; and
6. resets inner substate `+0x0A` to `4`.

For type `5`, reaching the configured limit suppresses this result-`8`
continuation and allows the ordinary completion path to proceed. This proves
an encounter index, an optional limit, and elapsed accumulation at the
higher-level sequence boundary. It does not by itself establish round-win
counting, a best-of-N rule, or the player-facing name of flow type `5`.

The inner-to-outer result-`8` handoff has an explicit readiness barrier.
`FUN_001F0F40`, called by inner substate `4`, is inactive unless continuation
phase `0x00607678 == 1`. On the first active pass it clears field `+0x48` in
each present inner side object at `inner+0x24/+0x28` and sets handshake byte
`0x00607680 = 1`. Subsequent passes service each present object through live
BTL `0x0071AF30` and `0x0071B2E0`, and return inner-machine wait code `2`
until every present object's byte `+0x54` is nonzero. Once all present objects
are ready, the helper clears `0x00607680` and returns code `3`; the
`FUN_001EF8F0` wrapper then reports completion to outer state `0x0F`. This is
why resetting the inner substate to `4` does not immediately tear down the old
encounter: result `8` crosses into outer state `0x10` only after this barrier.

Both result-`8` rebuild handlers set continuation phase `2`, which preserves
the BTL result bank and, outside the inner type `4`/`5` with route-other-than-`1`
exception, the condition statuses; the outcome and timeout marker are still
cleared for the new encounter. The rebuild itself and the retained values are
described in
[Battle lifecycle](battle_lifecycle.md#continuation-encounters-rebuild-the-session).

The two resident producers select different rebuild routes:

- `FUN_001EC5E0(side, value)` writes `0x00607678 = 1`,
  `0x0060767C = 1`, result `8`, and the supplied value into the selected
  manager side record. Outer state `0x10` therefore routes it to
  `FUN_001EE1C0` / outer state `0x17`.
- `FUN_001F2E70` writes `0x0060767C = 2`, so its synthetic result `8` routes
  to `FUN_001EE500` / outer state `0x18`. This route commits result `8` to the
  six-word outcome block's “other” bucket before rebuilding.

Neither route runs the ordinary BTL metric importer for result `8`. Route `1`
also does not call the session-counter updater; route `2` does, at resident
call site `0x001EE848`.

The route-`1` producer has one direct resident caller, at `0x0035B704` in
`FUN_0035B3B0(side_zero_based)`. That site passes side
`side_zero_based + 1` and a nonzero value returned by
`FUN_00372D00(manager + side_zero_based*0x28 + 0x60)`, and calls the producer
only while that side's condition ID `7` status is not `1`. The producer stores
the value at manager `+0x50` for side `1` or `+0x78` for side `2`. State
`0x17` later selects side `1` when `+0x50` is nonzero, otherwise side `2` when
`+0x78` is nonzero, with no selection if both are zero. These mechanics close
the direct route-`1` chain but do not establish a player-facing name for the
source value or condition.

Route `2` (state `0x18`) rebuilds side `2` when manager `+0x50` is zero and
side `1` otherwise, and commits result `8` to the session block's
other-result bucket.

The enclosing `FUN_001F2E70` wrapper owns an additional post-result tail that
is not part of the `FUN_001EC960` state-`1..0x19` dispatcher. It snapshots the
outer state before calling that dispatcher and snapshots it again immediately
afterward. If the pre-dispatch state was `0x12`, the wrapper writes outer state
`0x1D` and resets its own mini-state at higher-flow object `+0x00` to zero.
The already-sampled post-dispatch state is still used for the rest of that
update: in particular, a post-dispatch state `0x19` takes its separate path to
outer sentinel `0x20`, so that terminal choice is not left at `0x1D`.

On a later update that begins with outer state `0x1D`, `FUN_001F2E70` drives
`FUN_001F2920(higher_flow)`:

1. mini-state `0` creates a transition/fade and the helper at object `+0x2C`,
   then enters mini-state `1`;
2. mini-state `1` updates that helper through resident/live entries
   `0x006EE380` and `0x006EE4E0`; readiness advances it to mini-state `2`; and
3. mini-state `2` calls `FUN_001FD000(object+0x18)`, destroys helpers at
   `+0x24` and `+0x2C`, and returns sentinel `0x1F` when the scan is nonzero or
   `0x1E` when it is zero.

`FUN_001FD000` is the Boolean wrapper around `FUN_001FCF00`. The latter walks
the configured condition IDs in the snapshot at higher-flow `+0x18`, tests
both sides whose manager side-record bit `0x02` is clear, and returns the first
side for which a configured condition status is still `0`. Thus `0x1F` means
that at least one eligible side still has an unfinished configured condition;
`0x1E` means the scan found none. `FUN_001F2E70` emits event `0x14` for the
`0x1F` choice, stores the selected sentinel in the outer state, and resets its
mini-state. On the following update outer sentinel `0x1E` makes the wrapper
return `+1`, while `0x1F` makes it return `-1`. These are wrapper return
sentinels, not additional cases in the outer dispatcher's `1..0x19` switch.
The raw evidence is resident `0x001F2F10..0x001F3118`,
`0x001F33B0..0x001F3488`, `0x001F2920`, and
`0x001FCF00..0x001FD024`. Confidence is high for the mechanics and low for any player-facing meaning of the two signed returns.

## Battle statistics and scoring

The 28-slot result bank, its producers, statistic-derived conditions, and the
BTL metric import, tier, and ryo commit are described in
[Battle statistics](battle_statistics.md). Outer state `0x10` runs the
importer for results `1..5` before inner destruction, and state `0x14` runs
the result dispatcher on the score route described above.

## Cleanup boundaries

There are several distinct cleanup levels:

1. **End-presentation cleanup.** `FUN_001EDD10` clears the Victory request and
   destroys the transient overlay presentation object at `0x00607658` before
   BTL metric initialization.
2. **Inner battle-cycle destruction.** For imported results `1..5`, state
   `0x10` runs the BTL metric importer first and then calls `FUN_001EECD0` on the inner
   object at `0x00607604`. That wrapper invokes `FUN_001EEFD0`, which destroys
   battle-owned subsystems in the order given in
   [Battle lifecycle](battle_lifecycle.md#teardown-order), frees the
   `0x38`-byte allocation, and returns; state `0x10` then clears the global. Results `6`, `7`, and `9`
   skip import but use the same teardown. Result-`8` states `0x17` and `0x18`
   perform the corresponding teardown and global clear on their alternative
   routes. `FUN_001EC540`
   is a broader helper that destroys this inner object plus transient object
   `0x00607658`; it is not the outer-controller destructor.
3. **Completed-cycle resource and counter cleanup.** After normal inner
   destruction, state `0x11` handler `FUN_001EDEE0` releases the battle
   archives
   ([Battle lifecycle](battle_lifecycle.md#archive-lifetime-is-separate-from-session-lifetime))
   and commits the latched result to the session outcome block.
4. **Result-presentation internals.** State `0x14` clears the metric object and
   destroys its current owned presentation internals, but retains the result
   allocation at outer controller `+0x3C` for another cycle.
5. **Outer-controller destruction.** `FUN_001EC370` destroys the object at
   `0x00607620` through `FUN_001EC700`; `FUN_001EC890` releases its objects at
   `+0x34`, `+0x38`, and `+0x3C`, including finally freeing the reusable result
   allocation. Higher-level `FUN_001F2020` performs the equivalent remaining
   selection/result teardown when it owns this boundary.

Only the BTL metric import must precede destruction of the live fighter
pointers it consumes. The session counter update occurs afterward
and consumes the still-latched result plus the six-word block, not fighter
pointers. This ordering separates the data handoff from resource lifetime.

Outcome state survives the state-`0x10` metric import and
state-`0x11` counter/resource teardown because both are consumers. The next
battle initialization in `FUN_001EEE30` clears both the outcome at
`0x00607670` and timeout marker at `0x00607674`. The timeout marker has exactly
one scoped direct resident set (`0x001F0BC4`) and one direct clear
(`0x001EEE6C`); clean BTL only reads it through `FUN_001EC290`.

## Call graph summary

```text
FUN_001EF8F0
  -> FUN_001EF9C0                 inner end presentation
  -> FUN_001F10F0
       -> FUN_001EBA80            timer accumulation/expiry
  -> FUN_001F0B10
       -> FUN_001F11E0            HP comparison, latch 1..4
       -> condition-status scan   optional overwrite to 5

FUN_001EC960                     outer dispatcher
  state 0x0F -> FUN_001EDB70     wait for inner completion
  state 0x10 -> FUN_001EDD10
                 -> BTL live 0x00719580  metric import
  state 0x11 -> FUN_001EDEE0
                 -> FUN_001EC090        outcome/streak commit
  state 0x12 -> FUN_001EE060     exit/continuation decision
  state 0x14 -> FUN_001EE9C0
                 -> BTL live 0x00719D80 result dispatcher
                      -> live 0x00719ED0 total/tier init
                           -> live 0x00719C00 contribution sum
                      -> live 0x0071A2C0 accepted point commit
```
