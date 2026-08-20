# Match termination and outcome flow

## Scope and evidence

This document describes the clean NA2 v2.28 battle outcome path: HP and timer
termination, the latched result code, the end-of-battle state machines, session
outcome counters, the `BTL.BIN` score/rank handoff, and cleanup boundaries. It
does not assign story-mode names to generic controller modes and does not cover
damage calculation, substitution, frame-rate behavior, localization, or the
layout/artwork of the Victory screen.

The static inputs are:

| Binary | Size | SHA-256 |
| --- | ---: | --- |
| `SLPS_258.37` | `5,273,256` (`0x5076A8`) | `20C0A40D70EA412CD431993A2E189B37ECB6054D63AE93BE545470016E1627AF` |
| `PRG/BTL.BIN` | `2,237,184` (`0x222300`) | `56FD042740221E3CC91417194F147142799D51FE70642273F4E97BD389D5D63C` |

Both executables are stripped. `FUN_*`, `SUB_*`, and `func_0x*` names below are
analysis labels, not original symbols. Findings were checked against the raw
instructions and data where the preserved decompiler split functions or
attached a label to the wrong overlay bytes.

This is static evidence. The ordinary KO/time classifier, result latching,
counter updates, and score accumulator writes are high confidence. Human-facing
names for controller modes, results `5` through `9`, and the point accumulator
remain deliberately limited to what their callers prove.

## Research coverage

- **Assigned scope:** clean `BTL.BIN` match termination and outcome handling:
KO and timeout decisions, result/draw state, round-or-session counters,
end/result transitions, proven score/rank/reward handoffs, and teardown
boundaries. Work covered the resident executable where it owns battle flow and
the BTL overlay where it owns metric import and result presentation.
- **Exploration depth:** the following coverage levels are intentionally distinguished:

  **Exhaustive within bounded dispatchers:** every case in the active inner
  end-sequence dispatcher and resident outer-controller states `1..0x19` was
  traced far enough to classify its outcome, restart, continuation, score, or
  terminal behavior. The wrapper-owned post-result sentinels `0x1D..0x20` in
  `FUN_001F2E70` were also followed through their signed returns. Relevant
  resident families were `FUN_001EC300..FUN_001EEB10`,
  `FUN_001EEC80..FUN_001F12B0`, and `FUN_001F1E80..FUN_001F2E70`.
  **Exhaustive within explicit reference scans:** all ten clean-BTL direct
  calls to resident condition-status writer `FUN_001FD850` were inventoried;
  all clean-BTL direct calls to the four session outcome/streak accessors were
  accounted for; the sole resident direct caller of result-`8` producer
  `FUN_001EC5E0` was followed; and direct result stores/callers found for the
  scoped result field were classified. These claims do not include indirect
  calls or code outside the two hashed executables.
  **Bounded deep traces:** the KO/life gate, timer/end-reason path, terminal
  classifier, condition scan/status table, pause results, result-`8` readiness
  and rebuild routes, session counter updater/accessors, and their cleanup
  callees were followed through their decisive branches and side effects. The
  relevant condition subsystem was bounded to `FUN_001FCCD0..FUN_001FDBB0` and
  its scoped callers.
  **Bounded overlay analysis:** raw `BTL.BIN` was checked for its `MWo3` header
  and address mapping; the two-side 28-slot metric bank and wrappers around raw
  `0x062060..0x062150`; and the result-object/import/helper/dispatcher/commit
  region at raw `0x0651D0..0x066480`. The importer descriptors, bucket tables,
  tier thresholds, accumulator writes, and resident handoff calls used by that
  region were decoded. This was not a whole-overlay audit.

- **Confirmed coverage:** the exact result-code classifier for
ordinary KO/time states `1..4`, the condition-derived result `5`, pause-derived
results `6/7`, both synthetic result-`8` routes, the absence of a proven result-
`9` producer, timer fields and freeze/end flags, score-route qualification,
session tally/streak semantics, the separate type-`5` encounter limit, metric
import and tier/point mechanics, and inner/result/outer cleanup ownership.
Addresses are given in resident, raw-overlay, live-overlay, and preserved-export
conventions where applicable, including the proven `+0x40` overlay correction.

- **Unresolved or untested:** no
original names were recovered for generic controller types, condition IDs, or
results `5..9`; no player-facing semantic name is proven for the point
accumulator or the higher-wrapper signed returns; indirect-call reachability
was not exhaustively reconstructed; and no producer was established for result
`9`. The wider origins and meanings of every one of the 28 metric slots and all
condition IDs were outside the bounded outcome trace. Runtime frequency,
ordering under unusual engine states, presentation timing, and externally
visible rewards remain unverified.

- **Deliberate exclusions and overlap:** Adventure/story flow, damage scaling and
formulas, substitution, timing/60-FPS work, widescreen/UI layout, localization,
and media. Victory rendering/layout was treated only as an interface boundary;
fighter mechanics were read only where they directly supplied HP or terminal
state; and score/rank/reward logic was followed only through the proven BTL
handoff.
- **Evidence limitations:** validation was static: preserved decompiler output was cross-checked
against raw little-endian MIPS instructions, file bytes, encoded call targets,
table contents, hashes, and address arithmetic. No PCSX2 runtime trace,
breakpoint session, savestate experiment, or gameplay replay was performed for
this document, so dynamic confirmation is still outstanding.

## BTL address convention

`BTL.BIN` is an `MWo3` image whose complete raw file, including the header, is
loaded at EE `0x006B3F00`. Its header records:

| Header field | Value |
| --- | ---: |
| Kind (`+0x04`) | `1` |
| Full-file load base (`+0x08`) | `0x006B3F00` |
| Text bytes (`+0x0C`) | `0x001DB6C0` |
| Initialized-data bytes (`+0x10`) | `0x00046C00` |
| BSS bytes (`+0x14`) | `0x00006E80` |
| Constructor interval (`+0x18..+0x1C`) | `[0x008D6180, 0x008D61A4)` |
| Product label (`+0x20`) | `BTL_product.bin` |

The authoritative mapping is therefore:

```text
live EE address = 0x006B3F00 + raw BTL file offset
```

The preserved Ghidra baseline omitted raw header bytes `0x00..0x3F` and is
`0x40` low:

```text
live EE address = preserved Ghidra/export address + 0x40
```

Encoded absolute pointers and `j`/`jal` targets in the raw overlay are already
live addresses and must not be shifted. This matters for intra-overlay calls:
Ghidra can attach an encoded live target to bytes `0x40` later than the bytes
that execute at that target. The mapping is independently documented in
[the MWo3 overlay ABI](../runtime/overlay_abi.md).

The result-code logic itself is resident and has no overlay adjustment. Useful
BTL entries in this flow are:

| Role | Raw file | Live EE | Preserved export | Address note |
| --- | ---: | ---: | ---: | --- |
| Construct result object | `0x0651D0` | `0x007190D0` | bytes at `0x00719090` | Initializes the `0x188`-byte object and its descriptor records |
| Destroy result object internals | `0x065240` | `0x00719140` | bytes at `0x00719100` | Releases the fade, render object, and both result subobjects |
| Create result presentation internals | `0x065390` | `0x00719290` | bytes at `0x00719250` | Called by resident score-setup state `0x13` |
| Clear result-metric object | `0x065600` | `0x00719500` | `FUN_007194C0` | Called directly by resident controller setup and result teardown |
| Import battle metrics | `0x065680` | `0x00719580` | `FUN_00719540` | Called by resident state `0x10` |
| Capped/weighted metric helper | `0x065B60` | `0x00719A60` | bytes at `0x00719A20` | Stores a capped value and descriptor weight times value |
| Threshold-boolean metric helper | `0x065BC0` | `0x00719AC0` | bytes at `0x00719A80` | Stores raw value and a fixed contribution when threshold is met |
| Floor-bucket metric helper | `0x065C00` | `0x00719B00` | bytes at `0x00719AC0` | Selects the last table row whose threshold is not above the value |
| Ceiling-bucket metric helper | `0x065C70` | `0x00719B70` | bytes at `0x00719B30` | Selects the first table row whose threshold is not below the value |
| Read metric contribution | `0x065CE0` | `0x00719BE0` | bytes at `0x00719BA0` | Returns the selected entry's contribution word |
| Finalize 28 contribution values | `0x065D00` | `0x00719C00` | `FUN_00719BC0` | Encoded target is live `0x00719C00` |
| Result-object dispatcher | `0x065E80` | `0x00719D80` | `FUN_00719D40` | Called by resident state `0x14` |
| Initialize total/tier view | `0x065FD0` | `0x00719ED0` | `FUN_00719E90` | Called at raw `0x065F2C` by encoded `jal 0x00719ED0` |
| Accept/commit result points | `0x0663C0` | `0x0071A2C0` | physical export `FUN_0071A280` | Ghidra incorrectly splits its commit block as `FUN_0071A2C0` |
| Commit basic block | `0x066400` | `0x0071A300` | displayed `0x0071A2C0` | Part of the live `0x0071A2C0` function, not a separate live entry |
| Commit-input predicate | `0x066480` | `0x0071A380` | displayed `0x0071A340` | Tests selected-side record bit `0x20` |

For example, resident `jal 0x00719500` lands on the prologue at raw
`0x065600`; the preserved export instead labels that prologue
`FUN_007194C0`. Treating the export label as live would land inside the wrong
function.

## Outcome state and decisive fields

The central objects and fields are:

| Address / object offset | Meaning established by use |
| --- | --- |
| `0x00607600` | Battle manager pointer |
| manager `+0x0C` | Battle mode; value `3` activates the nonlethal Practice HP floor |
| manager `+0x18` | Side/configuration selector used by several mode-specific branches |
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

The outcome API is intentionally small:

- `FUN_001EC270(value)` writes `0x00607670` without validation.
- `FUN_001EC280()` returns it.
- `FUN_001EC290()` returns whether `0x00607674` is nonzero.
- `FUN_001EEE30()` clears the outcome to zero during battle initialization.

The ordinary classifier itself only latches a value when the global is still
zero, so the first ordinary classification is stable. The scripted-condition
branch described below is a deliberate exception in the same update.

Raw gp-relative stores provide a compact producer inventory independent of the
decompiler:

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

## KO and time termination

### Fighter life gate

`FUN_002151E0` sets fighter `+0x61 & 0x08` during fighter initialization.
`FUN_00225050` clamps HP to `0.0` and clears that bit when an accepted HP change
leaves HP at or below zero. Its return value is `1` for that lethal transition
and `0` otherwise.

When manager `+0x0C == 3`, the same function instead clamps HP to the float
`0.01` and does not clear the life bit. Thus Practice mode prevents this
ordinary KO trigger at the HP-update boundary. This statement concerns only
the terminal clamp, not how an incoming HP change was calculated.

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

One BTL producer family is exact. Live `0x006C3250` (raw `0x00F350`, preserved
bytes at `0x006C3210`), called at live `0x006C1868`, checks configured IDs
`0x2C`, `0x2D`, and `0x2E`. It reads the manager-selected side's BTL metric
bank index `19` and writes condition status `1` when the count has reached
`3`, `5`, or `7`, respectively. This proves a BTL-stat-to-condition handoff;
it does not establish the player-facing names of those conditions or imply
that status zero always means the same thing for every condition ID.

A full direct-call scan of clean BTL finds ten `jal 0x001FD850` status-writer
sites in executable functions. The first three are the threshold family above;
the other seven close these additional mechanical producer paths:

| Live call (raw offset) | Status write and proven trigger |
| ---: | --- |
| `0x006C3308` (`0x00F408`) | Selected side, ID `0x2C`, value `1` when metric `19 >= 3` |
| `0x006C3340` (`0x00F440`) | Selected side, ID `0x2D`, value `1` when metric `19 >= 5` |
| `0x006C3378` (`0x00F478`) | Selected side, ID `0x2E`, value `1` when metric `19 >= 7` |
| `0x00713744` (`0x05F844`) | Side argument plus one, ID `0x2A`, value `1` when live helper `0x00713680` inserts a previously unseen nonzero token and its counter at object `+0x74` becomes exactly `3` |
| `0x00713854`, `0x00713924` (`0x05F954`, `0x05FA24`) | Side `1` or `2`, ID `0x2B`, value `1` when each of three side-specific entries has both its active byte and object pointer set; live helper `0x00713770` checks this once per object, guarded by byte `+0x7D` |
| `0x0072F304` (`0x07B404`) | Side returned by live `0x00734130` plus one, configured ID `9` or `0x0B`, value `1`; ID `9` requires object signed halfword `+0x24A != -1`, while ID `0x0B` requires byte `+0x284 == 1` |
| `0x0076A720` (`0x0B6820`) | Object's zero-based side index plus one, ID `0x18`, value `0`, when that index equals manager selector `+0x18` |
| `0x0076A744`, `0x0076A760` (`0x0B6844`, `0x0B6860`) | Opposite side, ID `0x1A`, value `0`, when the same zero-based index differs from manager selector `+0x18` |

The last three calls are inside live function `0x00769790`; its side index is
the signed byte at `*(object+0x08)+0x0C`. Unlike the value-`1` satisfaction
writes, their value `0` is directly eligible for `FUN_001FCF00`'s outcome-`5`
scan when the corresponding ID is configured and the target side is active.
No other direct condition-status-writer call occurs in clean BTL. This is a
direct-call result; it does not exclude an indirect call or resident producer.

## Result-code table

| Code | Proven producer/consumer meaning | Confidence |
| ---: | --- | --- |
| `0` | Battle unresolved/active. Required by timer and ordinary classifier. | High |
| `1` | Side 1 has greater current HP at terminal classification. | High |
| `2` | Side 2 has greater current HP at terminal classification. | High |
| `3` | Equal nonzero current HP, normally a time draw. | High for condition; medium for UI wording |
| `4` | Both current HP values are zero. | High |
| `5` | Optional condition subsystem found an active side with an unsatisfied/configured status of zero; this can override an ordinary result. | High for mechanism; medium for original mode name |
| `6` | Pause/control-flow termination selected when the pause object returns `3`. | High for source; low for menu wording |
| `7` | Pause/control-flow termination selected when the pause object returns `2`. | High for source; low for menu wording |
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
  at `0x001EFD2C`; raw call site `0x001EFD78` proves it even though the
  decompiler renders this call without an argument.
- Substate `7` sends winner results `1` or `2` either to substate `8` or
  directly toward fade. Substate `8` is chosen exactly when the manager exists,
  manager field `+0x1C != 3`, and bit `0x02` is clear in the winning side's
  record byte (`+0x48` for result `1`, `+0x70` for result `2`); otherwise it
  goes to fade substate `0x0F`. Draws and special results do not select a
  winner-side record here.
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
| `0x11` | `FUN_001EDEE0` | Unloads common battle resources, calls live BTL cleanup `0x007691A0` and `0x006C3160`, unloads both fighter resource sets, releases the stage-selected resource, updates the session outcome block, and enters `0x12`. |
| `0x12` | `FUN_001EE060` | For controller type `1`, qualifying winner results enter score setup `0x13`; otherwise it emits event `0x17` and sends result `7` to `0x19`, other results to `0x16`. Type `2` likewise sends only result `7` to `0x19`, all others to `0x16`. |
| `0x13` | `FUN_001EE880` | Waits for resource readiness, creates/loads the BTL result presentation and its fade, then enters `0x14`. |
| `0x14` | `FUN_001EE9C0` | Runs live BTL result dispatcher `0x00719D80`. On its completion return, clears the metric state, destroys the current presentation internals, unloads the presentation resource, and enters `0x15`; the allocation at controller `+0x3C` remains for reuse. |
| `0x15` | `FUN_001EEA80` | Emits event `0x0E` and loops to state `3`. |
| `0x16` | `FUN_001EEAC0` | Waits for resource readiness, then loops to state `3` without the BTL score presentation. |
| `0x17` | `FUN_001EE1C0` | Rebuilds a selected side for one continuation route and queues resident Victory data when a side is selected. |
| `0x18` | `FUN_001EE500` | Rebuilds/swaps fighter selection for another continuation route and updates the session outcome block on this alternative completion path. |
| `0x19` | `FUN_001EEB10` | Performs its final resource transition, clears timer freeze bit `0x02`, sets manager mode `+0x0C` to `1`, and makes the outer dispatcher report terminal status `3`. |

Normal state `0x11` and continuation state `0x18` are alternative places where
the outcome counter is committed. Result `8` can skip the ordinary
metric/state-`0x11` route and reach the continuation states directly.

Composing states `0x10` and `0x12` gives the following exact route matrix for
the two handled controller types:

| Result | BTL metric import | Type `1` after cleanup | Type `2` after cleanup |
| ---: | --- | --- | --- |
| `1`, `2` | Yes | `0x13` score route only when the winning side-record bit qualifies; otherwise `0x16` | `0x16` |
| `3`, `4`, `5` | Yes | `0x16` | `0x16` |
| `6` | No | `0x16` | `0x16` |
| `7` | No | `0x19` terminal route | `0x19` terminal route |
| `8` | No | Directly `0x17` or `0x18` according to `0x0060767C` | Same special handling |
| `9` | No | `0x16` | `0x16` |

State `0x16` rejoins state `3`, so pause-selected result `6` is mechanically a
no-score restart while pause-selected result `7` is a terminal exit from this
outer controller. A hypothetical latched result `9` would use the same restart
route as `6`; recognizing the code does not establish a producer.

The type-`1` score qualification in state `0x12` is exact rather than a generic
winner test. Result `1` enters state `0x13` only when manager side-record byte
`+0x48` has bit `0x02` clear. Result `2` enters it only when side-record byte
`+0x70` has bit `0x02` clear. Every other type-`1` result takes the non-score
branch described in the table. Raw instructions `0x001EE0DC..0x001EE124`
extract the same bit for each winner and route both zero-bit cases to state
`0x13`; no player/CPU meaning is assigned to that bit without evidence from
its owner.

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

Both result-`8` rebuild handlers `FUN_001EE1C0` and `FUN_001EE500` change
`0x00607678` from phase `1` to phase `2`. On the next battle startup,
`FUN_001EC3B0` recognizes phase `2`, deliberately skips the BTL metric-bank
reset, and advances the phase to `3`. `FUN_001EEE30` independently skips the
condition-status reset for phase `2`, except that inner type `4`/`5` combined
with route other than `1` forces a condition reset. Thus both result-`8` routes
preserve BTL statistics, while condition progress is preserved by the general
phase-`2` path but not by that explicit type/route exception. A startup outside
these preservation cases resets the corresponding structure. The outcome and
timeout marker are nevertheless cleared for the new encounter.

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

Route `2` uses an explicit ordered side pair in state `0x18`: when manager
`+0x50` is zero, `FUN_001EE500` snapshots/services side `1` and rebuilds side
`2`; when `+0x50` is nonzero it snapshots/services side `2` and rebuilds side
`1`. It then changes continuation phase to `2`, moves the outer controller to
state `0x0D`, and commits result `8` to the session block's other-result bucket.

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
`0x001FCF00..0x001FD024`. Confidence is high for the mechanics and deliberately
low for any player-facing meaning of the two signed returns.

## BTL score, tier, and point-accumulator handoff

The two-side source bank at BTL BSS `0x008D6A80` is managed by these live
overlay wrappers:

| Live entry | Raw file | Operation |
| ---: | ---: | --- |
| `0x00715F60` | `0x062060` | Clear both sides' 28 signed-16 metric slots |
| `0x00715F90` | `0x062090` | Add a signed-16 delta to `(side, metric)` |
| `0x00715FD0` | `0x0620D0` | Set `(side, metric)` |
| `0x00716010` | `0x062110` | Replace `(side, metric)` only when the new signed value is greater |
| `0x00716050` | `0x062150` | Read `(side, metric)` as signed-16 |

Each wrapper converts one-based side `1..2` to a zero-based record and uses a
`0x38`-byte side stride. `FUN_001EC3B0` is the resident caller of the clear
wrapper while creating a new inner battle-cycle object. Clean BTL itself has no
direct call to either clear or set. Resident code does call set at
`0x00223428` for metric `17` and at `0x00374894` for metric `18`; the remaining
scoped producers use add or max-update. The result-`8` phase exception described
above is the verified new-inner-cycle reset exception.

The underlying storage operations are unsaturated signed-16 arithmetic. Add
sign-extends its input to 16 bits, adds it to the signed-16 slot, and stores the
low halfword; set stores the supplied low halfword; max compares the current
sign-extended halfword with the supplied integer before storing the latter's
low halfword. The wrappers do not validate side or metric ranges, so their
documented `1..2` / `0..27` domains are caller contracts rather than enforced
bounds.

The score bank is not wholesale-cleared by the state-`3` timer reset,
state-`0x10` metric import, or state-`0x11` resource teardown. A state-`0x15`
or `0x16` restart initially remains in the same outer controller, but it later
passes through state `0x0E`; `FUN_001EC3B0` then clears the bank before creating
the next inner battle-cycle object unless continuation phase is `2`. The bank
therefore has an ordinary inner-cycle/sample lifetime, with an explicit
result-`8` preservation exception, rather than an unconditional outer-controller
lifetime. The importer has one proven bank side effect before that boundary:
on its normal non-timeout/non-special-time path it writes computed remaining
whole units to metric slot `7` in both side records at live `0x008D6A8E` and
`0x008D6AC6`.

The six-word session outcome block has the longer lifetime: it resets only in
initial outer state `2` and is updated after each completed cycle. The reusable
BTL result object has the outer controller's allocation lifetime, but its
metric values and presentation internals are cleared/rebuilt per result
presentation; it is a transformation of the source bank rather than its owner.

The outer controller calls live `0x00719580` after the end presentation but
before state-`0x11` resource teardown. The BTL result object contains a
28-entry metric-record array beginning at `+0x14`, with `0x0C` bytes per
record: descriptor pointer at `+0x00`, value at `+0x04`, and contribution at
`+0x08`. Thus metric values begin at object `+0x18` and contributions at
object `+0x1C`. The importer clears every value/contribution pair, obtains the
latched result with resident `FUN_001EC280`, and chooses a side record as
follows:

```text
selected_side = (result == 1) ? 1 : 2
```

This exact condition means draws and special result `5` select the side-2
record. It is not evidence that side 2 “won”; it is simply the importer branch
used by flows that reach it. Outer state `0x10` imports results `1..5`, but
state `0x12` only permits its field-qualified result `1` or `2` paths to create
the score presentation. Therefore an imported draw, double-zero, or result-`5`
sample is not subsequently committed through this result screen in the proven
outer flow.

The source records are two `0x38`-byte runtime records beginning at BTL BSS
`0x008D6A80`. Twenty-eight initial metric values are copied for the selected
side and then several are recomputed/bucketed. The generic weighted helper at
live `0x00719A60` uses descriptor byte `+0x04` to select a signed-16 cap from
live `0x008C3CB0`, applies that cap only as an upper bound (there is no lower
floor in the helper), and stores
`descriptor_signed_i16[0] * capped_value` as its contribution. The beginning
of that cap/rank table is `999, 99, 100, 0, 0, 300, 450, 550, 700`.

The 28 descriptors themselves begin at live `0x008C3DE0` (raw
`0x20FEE0`), stride `0x0C`. The coefficient and cap-selector bytes used by the
weighted helper are:

| Metric indices | `(coefficient, cap selector -> maximum)` |
| --- | --- |
| `0` | `(5, 0 -> 999)` |
| `1` | `(100, 1 -> 99)` |
| `2` | `(10, 0 -> 999)` |
| `3` | `(5, 0 -> 999)` |
| `4` | `(10, 0 -> 999)` |
| `5` | `(1, 0 -> 999)` |
| `6` | `(5, 0 -> 999)` |
| `7` | `(1, 1 -> 99)` |
| `8` | `(1, 2 -> 100)` |
| `9` | `(50, 0 -> 999)` |
| `10` | `(100, 1 -> 99)` |
| `11` | `(5, 0 -> 999)` |
| `12` | `(5, 0 -> 999)` |
| `13` | `(0, 0 -> 999)` |
| `14`, `15` | `(100, 1 -> 99)` |
| `16` | `(10, 1 -> 99)` |
| `17..24` | `(0, 0 -> 999)`; their relevant custom helpers replace the generic contribution |
| `25` | `(20, 0 -> 999)` |
| `26` | `(100, 0 -> 999)` |
| `27` | `(400, 1 -> 99)` |

The importer then performs these verified overrides:

- metric index `7`: configured limit minus elapsed whole units, clamped to
  zero; auxiliary flag `0x00607674` and one mode/configuration combination
  force it to zero;
- metric index `8`: selected fighter HP multiplied by `100` and converted to a
  word with MIPS `cvt.w.s` (there is no explicit `trunc.w.s`); HP below `0.05`
  receives an additional one after that conversion;
- metric index `5`: selected-side record signed-16 value at `+0x22`;
- metric index `17`: the same `+0x22` source through floor table
  `0x008C3CD0`;
- metric index `18`: selected-side record `+0x24` through floor table
  `0x008C3D10`;
- metric index `19`: selected-side record `+0x26`, contributing `50` when at
  least one;
- metric index `20`: selected-side record `+0x28`, contributing `20` when at
  least one;
- metric index `21`: forced to zero;
- metric index `22`: elapsed whole units through ceiling table
  `0x008C3D30`; timeout marker `0x00607674`, or the conjunction of manager
  mode `2` and configuration selector `6 == 100`, forces it to zero;
- metric index `23`: selected HP integer, contributing `500` when at least
  `100`;
- if selected-side record `+0x30` is nonzero, metric `25` receives record
  `+0x04` and metric `2` is forced to zero; and
- metric index `24` contributes `100` when any of metrics `25`, `26`, or `27`
  has a positive contribution, otherwise zero.

The encoded bucket rows are exact pairs of `(threshold, contribution)`:

| Live table | Selection rule | Rows |
| ---: | --- | --- |
| `0x008C3CD0` | Last threshold `<=` input | `(30,50)`, `(40,100)`, `(50,200)`, `(60,300)`, `(70,400)`, `(80,500)`, `(90,1000)` |
| `0x008C3D10` | Last threshold `<=` input | `(2,10)`, `(3,20)`, `(4,30)`, `(5,50)` |
| `0x008C3D30` | First threshold `>=` input | `(10,400)`, `(20,200)`, `(30,100)` |

These numeric transformations are proven; their player-facing metric labels
are not.

Live `0x00719C00` finishes special component caps, sets result object `+0x04`
to zero, and sums the 28 contribution words at
`object + 0x1C + index*0x0C` into that total. Before summing, it sets metric
`9` to `3` when manager `+0x1C == 0`; otherwise it uses
`FUN_001F6EA0(manager) + 1`, where that resident wrapper reads configuration
selector `0x0B`. The value is upper-capped through metric `9`'s descriptor and
weighted by its coefficient `50`. It also sums the contributions of metrics
`14`, `15`, and `16`, writes that sum as metric `13`'s value, and gives metric
`13` no additional contribution because its coefficient is zero. Live
`0x00719ED0` then:

1. initializes the result/tier view;
2. copies resident manager accumulator `FUN_001F6F60(manager)` to object
   `+0x08`;
3. records side `1` only for result `2`, otherwise side `0`, for presentation;
4. invokes the contribution finalizer;
5. clamps object `+0x04` to `9,999`; and
6. computes tier byte `+0x0C` from four signed-16 thresholds.

The encoded live tier table is `0x008C3CBA` (raw `0x20FDBA`), containing
`300, 450, 550, 700`. The resulting tier is:

| Total | Tier byte |
| ---: | ---: |
| `< 300` | `0` |
| `300..449` | `1` |
| `450..549` | `2` |
| `550..699` | `3` |
| `>= 700` | `4` |

No letter/rank names are assigned because this code stores only numeric tier
`0..4`.

Live `0x0071A2C0` is the acceptance/commit function. Its predicate at live
`0x0071A380` checks bit `0x20` in the selected side's runtime input/status
record. Once accepted, it plays event/sound `0x34` and returns `1`. With a live
manager it advances the result-object to state `3` and computes:

```text
new_accumulator = object[+0x08] + object[+0x04]
new_accumulator = min(new_accumulator, FUN_001F7870())
FUN_001F6F00(manager, new_accumulator)
```

`FUN_001F7870()` returns `9,999,999`. `FUN_001F6F60` reads and
`FUN_001F6F00` writes the field at `*(manager + 4) + 0x34`; the writer also
enforces the same maximum. Neither the result-total clamp nor accumulator
writer applies a lower floor. If the manager is absent at acceptance, the
object instead moves directly to state `4` and skips the accumulator write.
The normal routed score path has a live manager, but this distinction is part
of the function's exact contract. The code proves a capped manager point
accumulator and its result-screen commit. It does not prove that the value is
currency, an item unlock, or a persistent reward. No direct item/reward grant
was found in this handoff.

The surrounding result object has halfword state at `+0x00`, selected-side
halfword at `+0x02`, total at `+0x04`, pre-result accumulator at `+0x08`, tier
byte at `+0x0C`, and fade handle at `+0x10`. Live dispatcher `0x00719D80`
implements states `0..5`: state `0` runs total/tier initialization and enters
`1`; states `1` and `2` update the two result subobjects and can invoke the
accept/commit function; state `3` waits for a fade and enters `4`; dispatcher
state `4` returns completion value `1`; and state `5` returns value `2`.

Resident `FUN_001EE9C0` accepts only dispatcher return `1`. After resource
readiness, it clears the metric object through live `0x00719500`, destroys it
current presentation internals through live `0x00719140`, unloads the
associated result resource, and moves the outer controller from state `0x14`
to `0x15`. It does not free or clear the `0x188`-byte allocation stored at
controller `+0x3C`; later cycles reuse it. Controller teardown
`FUN_001EC890` calls `0x00719140` again, then frees the allocation through
`FUN_00117000` and clears `+0x3C`. Thus the accumulator write occurs before
presentation teardown, and the result object is not the persistent owner of
the committed total.

Dispatcher state `5` returns `2`, but the resident owner does not treat `2` as
completion and remains in outer state `0x14`. No direct write of `5` to result
object halfword `+0x00` was found in the constructor, clear/import functions,
dispatcher state handlers, or resident owner: the verified writes are states
`0..4`. Consequently state `5` and return `2` are a recognized interface branch
whose scoped reachability is unproven, not a second proven cleanup route.

## Cleanup boundaries

There are several distinct cleanup levels:

1. **End-presentation cleanup.** `FUN_001EDD10` clears the Victory request and
   destroys the transient overlay presentation object at `0x00607658` before
   BTL metric initialization.
2. **Inner battle-cycle destruction.** For imported results `1..5`, state
   `0x10` runs the BTL metric importer first and then calls `FUN_001EECD0` on the inner
   object at `0x00607604`. That wrapper invokes `FUN_001EEFD0`, which destroys
   battle-owned subsystems and clears manager live pointers `+0xDE0..+0xDE8`
   and `+0xDEC..`, clears the inner object, frees its `0x38`-byte allocation,
   and returns; state `0x10` then clears the global. Results `6`, `7`, and `9`
   skip import but use the same teardown. Result-`8` states `0x17` and `0x18`
   perform the corresponding teardown and global clear on their alternative
   routes. `FUN_001EC540`
   is a broader helper that destroys this inner object plus transient object
   `0x00607658`; it is not the outer-controller destructor.
3. **Completed-cycle resource and counter cleanup.** After normal inner
   destruction, state `0x11` handler `FUN_001EDEE0` unloads common,
   per-fighter, and selected-stage resources, calls the BTL-side cleanup
   functions, and commits the latched result to the session outcome block.
4. **Result-presentation internals.** State `0x14` clears the metric object and
   destroys its current owned presentation internals, but retains the result
   allocation at outer controller `+0x3C` for another cycle.
5. **Outer-controller destruction.** `FUN_001EC370` destroys the object at
   `0x00607620` through `FUN_001EC700`; `FUN_001EC890` releases its objects at
   `+0x34`, `+0x38`, and `+0x3C`, including finally freeing the reusable result
   allocation. Higher-level `FUN_001F2020` performs the equivalent remaining
   selection/result teardown when it owns this boundary.

Only the BTL metric import must precede destruction of the live fighter
pointers it consumes. The session counter update deliberately occurs afterward
and consumes the still-latched result plus the six-word block, not fighter
pointers. This ordering separates the data handoff from resource lifetime.

Outcome state deliberately survives the state-`0x10` metric import and
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

## Negative results and unresolved questions

- Clean `BTL.BIN` calls resident outcome getter `FUN_001EC280` but contains no
  identified direct call to setter `FUN_001EC270`. KO/time classification and
  result latching are resident responsibilities; BTL consumes the result.
- No direct BTL call to resident Victory request `FUN_00201E90` was found. The
  outer resident controller owns that handoff; BTL owns other result
  presentation/score objects.
- No generic best-of-N round counter or round-win threshold was proven. The
  six-word block is an outcome tally/streak block. A distinct higher-level
  object does have an encounter index/limit and synthesizes result `8`, but no
  round-win threshold is visible in that mechanism.
- Result `9` has consumers but no scoped latched producer. Codes `6`, `7`, and
  `8` have exact flow producers but their menu/mode-facing names remain
  unresolved. The direct-store/direct-call audit also found no literal pointer
  to the setter in either scoped image; a dynamically computed indirect call or
  an out-of-scope overlay remains outside this negative result.
- Tier `0..4` and the capped manager accumulator are proven. Currency, unlock,
  inventory, persistence, and human-readable rank labels are not.
- The exact player-facing labels of all 28 score metrics remain unresolved.
  Their record layout, selected source fields, all three bucket tables, total,
  tier thresholds, and final accumulator write are established.
- No runtime trace was added for this research. Mode-specific routing and
  presentation wording should be confirmed dynamically before giving the
  unresolved codes user-facing names.
