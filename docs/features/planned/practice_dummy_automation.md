# Practice dummy automation

This document records provisional research for guard randomness, reversal
actions, wake-up responses, and situation repetition in Practice. It does not
describe an accepted implementation. Retail facts remain owned by the linked
knowledge documents; feature choices and inferred requirements are provisional.

## Research coverage

- **Assigned scope:** Prepare provisional dummy-automation research on top of
  native AI, input, action, and reset contracts.
- **Exploration depth:** Read the neighboring owners, then inspected complete
  guard/input/scheduler, recovery entry/update/exit, queue admission/consumption,
  action entry, and resource/history reset families. Recovered all seven scripted
  Attack branches and split AI initialization through bytes. Read 18 full action
  records across three characters, five complete variant-switch bodies, one
  complete Naruto callback, and selected common prior-outcome consumers; bounded
  literal-byte-load coverage found 71 resident `+0xA41` readers.
- **Confirmed coverage:** Retained guard differs from current held input;
  maintenance precedes ordinary action selection; native success returns do not
  universally prove a new action/queue; positive-threshold simultaneous wake-up
  priority depends on cursor reset; recovery exit changes later action state;
  sample chains and live availability differ; and reset domains remain separate,
  with cross-side and RNG effects in AI initialization.
- **Unresolved or untested:** Sequence/downed/repeat episode boundaries, accepted
  action detection and retry termination, complete action/provider coverage,
  arbitrary-action cleanup and full situation restoration, identical outcomes,
  random weights, controls, storage, and lifetimes remain unresolved. No complete
  executable feature contract or accepted implementation is established.
- **Deliberate exclusions and overlap:** [Practice](../practice.md) owns implemented
  behavior. [Battle AI](../../knowledge/gameplay/session/battle_ai.md),
  [Action commands](../../knowledge/gameplay/combat/action_commands.md),
  [Hit response](../../knowledge/gameplay/combat/hit_response.md), and
  [Combat action execution](../../knowledge/gameplay/combat/combat_action_execution.md)
  own retail contracts. [Input recording](practice_input_recording.md) and
  [Position reset](practice_position_reset.md) own their provisional features.
  Full roster/callback semantics, implementation, and interface design are outside
  this provisional integration research.
- **Evidence limitations:** Static research uses unmodified retail NA2
  `SLPS_258.37` and `BTL.BIN`. GhidrAssist identifies them as `/SLPS_258.37`
  and `/BTL.BIN` in target `NA2`. The preserved BTL import omits the `0x40`-byte
  header; imported addresses are `0x40` below live addresses, while encoded
  operands contain live addresses. Missing xrefs and truncated decompilation
  cannot establish absence or a complete function contract. Source identities
  belong to [Retail game files](../../knowledge/game/files/file_identities.md).
  Static branches and source rows do not prove every combination reachable or
  assign player-facing names to raw action IDs. Random frequencies and complete
  outcome reproducibility are not established.

## Existing foundations

The [AI output boundary](../../knowledge/gameplay/session/battle_ai.md#main-tick-and-output-boundary)
and [controller ownership](../../knowledge/gameplay/session/battle_ai.md#controller-ownership-and-lifecycle)
separate dummy ownership from proposed logical input. The resident bridge can
suppress output before normal action consumers run. A requested action therefore
needs an eligibility and success contract rather than assuming that a command
mask immediately enters that action.

The [input source boundary](practice_input_recording.md#input-sampling-and-injection-boundary)
also distinguishes held input, derived edges, history matching, and gameplay
readers outside history. Reversal or wake-up commands cannot be assumed to use
one universal input representation.

The [position-reset state matrix](practice_position_reset.md#state-required-by-an-in-place-reset)
and [resource snapshot implications](practice_position_reset.md#resource-snapshot-and-reconstruction-implications)
show why restoring health or coordinates alone cannot establish a repeatable
situation. Action, phase, pending input, hit/exchange, and side-object lifetime
need their own contracts.

## Guard randomness

### Observed boundary and decision lifetime

Read-only MCP inspection recovered the complete resident guard-input updater
`0x00228320`, guard follow-up `0x00228B50`, leave helper `0x00228E90`,
action maintenance `0x00248580`, input consumer `0x00248EC0`, and fighter-list
scheduler `0x0024FD80`. The state-18 AI helper was corroborated over imported
`0x006FA550..0x006FAA0F` (live `0x006FA590..0x006FAA4F`, complete-file
`0x046690..0x046B4F`): its decompiler omits the random-departure continuations,
but the bytes contain both comparisons and the reset/facing/departure calls.
The retail algorithms belong to
[State-18 guard reaction](../../knowledge/gameplay/session/battle_ai.md#state-18-guard-reaction)
and [Guard lifecycle](../../knowledge/gameplay/combat/chakra_and_guard.md#guard-input-and-action-lifecycle).

The feature-relevant observation is that removing logical `0x10000000` does
not immediately remove accepted guard during guarded-hit states `(0,6)/(0,7)`.
The input updater skips its accepted-guard update in those states. The leave
helper consults the current held mask only when action maintenance reaches its
exit gate; a remaining action lock can re-enter a guarded-hit state instead.
Conversely, held guard is subject to native state, lock, grounded, and other
eligibility checks. A random command decision is therefore not the same as a
random hit outcome.

### Provisional behavior choices

Guard randomness needs an explicit sampling event and retention period. A
per-update coin flip can release/reaccept guard in eligible states but cannot
promise independent block decisions for hits received during a retained guarded
response. A choice retained for an attempted sequence or repeat is a stronger
candidate when the intended exercise is to distinguish guarding from taking a
hit. Defining the sequence boundary remains unresolved; opponent class `8`, a
single attack-object index, or a guard-state transition alone has not been
proven to identify a complete player-authored sequence.

The native scripted-Practice guard priority and override are unsuitable as an
assumed percentage setting. They collect threat candidates, choose state 18,
and suppress that helper's probabilistic departures under Guard Yes. Their
decision semantics are owned by
[Scripted-Practice reaction priority](../../knowledge/gameplay/session/battle_ai.md#scripted-practice-reaction-priority).
A provisional random-guard policy would need to arbitrate that producer and
the final output together, with a side-local retained choice. Selecting No on
one update is not established as cancelling a previously accepted guard.

## Reversal ordering

The inspected fighter-list scheduler executes hit routing and AI synthesis
before the ordinary pass. That pass copies logical input, runs action
maintenance, consumes input, and updates the selected action, in that order.
This corroborates the
[Resident bridge and action dispatch](../../knowledge/gameplay/combat/action_commands.md#resident-bridge-and-action-dispatch)
contract. A state exit performed by maintenance can be followed by ordinary
selection in the same eligible pass; waiting for a later update merely because
AI observed the previous state would not establish the earliest legal input.

The complete entry predicate `0x00239E50` distinguishes `(0,6)` from `(0,7)`:
with action-lock word `+0x254 == 0`, the latter is accepted by its major-0
substate gate and the former is rejected. Recovery substates also have different
cursor gates. This predicate is only one gate in ordinary selection; pending
index, selector mode, paired-state interception, contextual matching, resources,
and final candidate validation still apply. A provisional reversal must retain
its request until proved accepted, then stop submitting it. Observing only a
zero lock, leaving hit response, or publishing a mask is insufficient evidence
of acceptance.

### Native success signals are different

Complete MCP decompilation and disassembly of resident queue admission
`0x0021D380` reveal a narrower contract than the linked AI owner's statement
that return `1` always follows an installation. In its active-major-8 special
route, branches at `0x0021D960`, `0x0021D974`, `0x0021D988`, and
`0x0021D990` reach `0x0021DAAC` (`li v0,1`) without executing the queue or
pending-slot stores. These branches respectively cover no selected/current
record, selected/current signature bit `0x08000000`, selected/current category
mask `0x000C0000`, and selected/current pointer equality. The category/signature
words here belong to the already pending record when one exists, otherwise the
current record. The ordinary non-major-8 route does install its bounded chain.
This is a confirmed static distinction, not proof that every special-route
combination is reachable. A return-`1` event alone cannot prove new queue state.

The complete native consumer `0x0021DAE0` does not inspect the return from
action starter `0x0023A9A0` before installing its next pending index and setting
queue phase `2`. The starter itself performs final gates and then calls
`0x00217E40`, but does not propagate that setter's return. The setter returns
zero for an unforced same-major/same-substate request. Queue admission, queue
consumption, starter success, and a newly restarted action are therefore
distinct observations. The final feature contract would need to identify an
actual destination/action transition, including a deliberate same-action case.
The native queue and pending-slot mechanisms remain owned by
[AI action queues](../../knowledge/gameplay/session/battle_ai.md#action-record-selection-and-direct-queues)
and [Pending selection](../../knowledge/gameplay/combat/action_commands.md#pending-selection-and-priority-boundaries).

### Scripted Attack is a repeated policy, not a reversal scheduler

The seven-way native Attack helper was recovered completely from MCP bytes at
imported `0x006F9570..0x006F9877` (live `0x006F95B0..0x006F98B7`, file
`0x0456B0..0x0459B7`) and its seven live jump targets in the table at
`0x008C37F0` (import `0x008C37B0`, file `0x20F8F0`). Its decompiler merges
unrelated continuations, so those apparent cross-function cases were discarded.

Before dispatch, the helper requires expired AI countdown `+0x118`, checks a
separate predicate, reloads the countdown to `60`, and returns when the target
is major `6`. Attack value `1` emits logical `0x1000`; value `2` selects a
record, falls back to a second selector query, and submits it to
`0x0021D380`. That call's return is ignored before the common epilogue. The
remaining table branches also use different mask, affordability, current-state,
and cooldown paths. None of the seven branches establishes a retained
"execute once on my first legal response exit" request.

**Provisional inference:** Native Attack can supply candidate action families,
but its countdown/target-state scheduling and ignored admission result cannot
be reused as a promised reversal event. Command-based and record-based reversal
requests need separate definitions: native record admission can install a
multi-record chain and can stage jutsu resources, while logical commands go
through contextual matching and competing consumers. The feature has not
selected one representation or a public list of reversal actions.

Submitting to the queue during native AI synthesis also checks entry before
action maintenance has performed that pass's recovery/guard exit. Supplying a
logical request for the later selector and calling early queue admission are
therefore not interchangeable ways to reach the first eligible pass. The
retained request would need a defined observation/admission point and termination
on success, interruption, invalidated moveset, or episode end; those scheduling
choices remain provisional.

## Wake-up responses

### Selection and reversal are separate decisions

The complete resident recovery family `0x00235100` (destination setup),
`0x00235510` (downed handoff),
`0x00235690` (state maintenance), `0x00235C60` (state motion), and
`0x00235200` (exit) was inspected through MCP alongside the shared selector
gate. Their retail ownership is
[Timed downed recovery](../../knowledge/gameplay/combat/hit_response.md#timed-downed-recovery-and-get-up-choices).
The feature would need to distinguish choosing a recovery from requesting an
action during or after that recovery. Recovery `0x5F` becomes eligible for
ordinary selection at primary cursor `8`, and `0x60` at cursor `3`, subject to
all other gates; `0x5D/0x5E` fail that entry predicate. Waiting for animation
completion and using the first legal cancel window are different exercises.

State maintenance runs before ordinary input consumption. Thus an observed
`0x5E/0x60` completion can enter neutral before the same pass's input selector,
while `0x5F` completion enters `(3,0x20)`. A reversal based only on the AI's
earlier state observation can miss that pass. This establishes ordering, not a
single unconditional frame number or a character-independent valid action.

### Corrected simultaneous-input interpretation

The linked recovery owner describes binding 1 as replacing binding 2 or the
automatic choice in the same update. The instruction sequence establishes an
additional state-mutating dependency: `0x00235804` enters `0x5E`, or
`0x00235848` enters `0x5F`, through `0x00217E40`; the final test then reloads
`+0x1C4` at `0x00235850` and signed threshold `+0xB68` at `0x00235854`.
The setter resets that primary cursor to zero on this changed substate. MCP
disassembly and bytes at `0x00235740..0x002358DF` corroborate the reload and
strict threshold comparison. Complete destination dispatcher `0x00217D30` and
recovery setup `0x00235100` do not rewrite the threshold for `0x5E/0x5F/0x60`.

Consequently, for a nonnegative `+0xB68`, the final binding-1 branch cannot
override a `0x5E/0x5F` transition already made by that call. Before the
automatic threshold, simultaneous eligible `0x10000` and `0x1000` input selects
`0x5F`; at the automatic threshold, `0x5E` wins. When neither earlier branch
transitions, eligible binding 1 can select `0x60`. The standard handoff defaults
are positive (`8/40`), and the separately documented overlay overrides are
nonnegative. A negative or otherwise exceptional threshold has not been proven
reachable here. This correction concerns static control flow; it does not
assign player-facing names to the three recoveries.

### Exit-dependent action flags

Recovery exit `0x00235200` has a record-dependent special case for `0x5F`
entering major `8`: when the destination record's category lacks bit `2` and
secondary word has bit `2`, it sets fighter byte `+0xA41 = 1`. It also changes
the accepted-hit rejection channel differently for `0x5E/0x5F/0x60` when no
activation is pending. Directly replacing recovery state with a chosen action
would omit these native transition effects. The meaning and later consumer of
the `+0xA41` flag matter before treating every recovery cancel as the same
action entry.

A bounded resident search for aligned literal-offset `LB/LBU ...,0xA41(base)`
used all eight possible high opcode bytes. It found 71 distinct sites in the
ordinary resident mapping (70 signed loads and one unsigned load); the two ELF
alias mappings duplicate those sites. The initially capped signed-load search
was repeated with limit `1000`, returning all 210 matches for that opcode
pattern. Wider reads, computed offsets, and overlay readers are outside this
search. It was used to choose consumers, not to assign semantics to all 71.

Focused common consumers establish that the flag is consequential:
`0x0023EF50` can use `+0xA41 == 1` to admit its current-record/payload-driven
grounded-bit clearing branch; `0x0023F170` uses current/prior outcome bytes in
landing exits; and `0x0023F5D0` uses prior outcome in its facing, distance,
record-category, and motion-selection conditions. The complete smaller first
two bodies and the relevant branches of the large motion body were inspected.
The [Combat execution owner](../../knowledge/gameplay/combat/combat_action_execution.md#continuation-and-common-exit-decisions)
owns those algorithms; this feature implication is that bypassing native
recovery exit can change the chosen action's motion or continuation.

The Naruto definition (ID `57`, resident `0x004DAD80`) points to callback
table `0x004D56D0`; its slot `2` points to the completely inspected
`0x00299520`. Callback-local action ID `0x2A` uses `+0xA41 == 1` together
with facing and target geometry before approaching a target-relative vertical
position. This is a concrete character consumer, not a universal mapping of
callback-local `0x2A` to the selected action index or a named reversal.

### Provisional selection policy

A useful candidate is a retained recovery choice per downed episode, followed
by an independently retained reversal request. Native timer eligibility,
ground/contact conditions, side ownership, and action-lock state would remain
separate inputs. A choice made once must not be resampled merely because the
fighter spends several updates in `0x5D`; repeated input before its threshold
is not established as a queued wake-up choice. Whether the feature should use
the earliest allowed choice or delay until automatic recovery remains a product
decision, and random weights are unspecified.

The two input-driven ordinary-response recoveries (`ACT_RCV_0/1`) and the
special relocation substates `0x61/0x62` have separate native gates. They cannot
be folded into the `0x5D` choice under a generic "wake-up" name. Their contracts
remain in [Input-driven recovery](../../knowledge/gameplay/combat/hit_response.md#input-driven-recovery-actions-during-ordinary-response)
and the linked timed-recovery owner.

## Representative action variants

The completed retail census remains in
[Static action data](../../knowledge/gameplay/combat/action_commands.md#complete-static-action-data-census).
For this feature, six complete source records (slots `21..26`) were reread for
Naruto ID `57` at `0x004DA434..0x004DA62B`, Kazekage Gaara ID `59` at
`0x004E5344..0x004E553B`, and Deidara ID `64` at
`0x00501214..0x0050140B`. The queue uses each record's continuation byte
`+0x18` and category byte `+0x19`; the request signature is `+0x1C`.

| Sample | Continuation/category pairs for slots `21..26` | Feature implication |
| --- | --- | --- |
| Naruto | `-1/0, 21/1, 22/2, 23/3, 23/3, 23/3` | Requesting a later branch can identify a chain rather than one isolated action. |
| Gaara | Same six pairs as Naruto; slot `24` signature is `0x00100212`, versus Naruto `0x00100211` | Equal raw slot numbers and chain positions do not prove equal command eligibility. |
| Deidara | `-1/0, 21/1, 22/2, 22/2, 22/2, 22/2` | Branches begin one chain category earlier than in the other two samples. |

All these sampled source category words at `+0x10` are `1`. Source availability
is not live availability: complete mode helpers `0x0029C1E0` and `0x002B49C0`, and their
identified immediate callers, change the working arrays. Gaara switches
categories between slots `21..43` and `44..47`; Deidara switches them between
`21..41` and `42..45`. Gaara's three direct calls come from definition callback
`0x0029D7E0`; Deidara's two come from initializer `0x002B42D0` and transition
`0x002B4860`. Those five complete bodies were read through MCP. Their mode and
awakening ownership remains in
[Deidara and Gaara variants](../../knowledge/gameplay/characters/awakening.md#deidara-and-gaara-character-variants).

**Provisional inference:** A retained reversal action needs a live fighter,
moveset/provider, and current availability check. A raw index captured before
a mode change cannot be assumed valid afterward. Native queue continuation is
also character data; selecting an action slot is not yet a promise to perform
exactly one player-visible move. These three samples establish concrete
differences without repeating the complete roster census or claiming complete
character coverage.

## Situation repetition

### Independent native reset domains

Complete resident resource capture/restore `0x001ECC00/0x001ECDE0`, fighter
input-history reset `0x002171C0` and its sample clear `0x00217240`, and action
queue reset `0x0021D200` were inspected through MCP. Their reset domains differ:

| Native building block | Feature-relevant scope | What it does not establish |
| --- | --- | --- |
| Resource capture/restore | Selected-side HP/chakra, optional item inventory and global timer; masks belong to [Practice reset](../../knowledge/gameplay/modes/practice_mode.md#discrete-practice-controller-reset) | Restoring an action, position, input history, or RNG state |
| Fighter input-history reset | Clears fighter logical triple, 32 three-word samples, and cursor `+0x4C4` | Clearing the separately allocated `ccCommand` history or a current action/queue |
| Queue reset | Clears queue root/four category slots/phase and pending action index | Completing current action exit, clearing logical input/history, or restoring resources |
| AI initialization | Resets transient work for both static sides, then installs the selected side's profile | A side-local rewind or restoration of the same random stream |

The resident xrefs for the fighter-history and queue reset helpers identify only
constructor-reset calls at `0x00214E84` and `0x00215070`, respectively. That
bounded native xref result does not exclude overlay or indirect callers, and
does not establish a ready-made Practice repetition entrypoint. The large
constructor reset has much broader fighter initialization effects; it is not
an in-place repeat command.

The command-history constructor was inspected at imported `0x006EF5C0`
(live `0x006EF600`, file `0x03B700`). It allocates its ring and initializes
indices before binding the side and pad. Its final call targets live
`0x006EF780`, whose actual imported entry is `0x006EF740`: the complete
wrapper and `0x006EF770` loop load eight input parameters into `+0x68..+0x76`.
The misleading decompiler continuation at imported `0x006EF780` is not a
ring-reset API.

The constructor's sample callback instead reaches live `0x006EF390` (import
`0x006EF350`, file `0x03B490`). MCP cannot expose that undefined body as a
function; its bytes through import `0x006EF373` show zero stores to sample
held/press/release, both angles, and both magnitude bytes. That helper does not
touch the sample padding, owning ring indices, logical publication, or fighter
history. These are concrete building blocks, without a proven complete reset
of an already active input object. The [Input recording owner](practice_input_recording.md#reset-stop-and-object-lifetime)
owns the ring's allocation, destruction, and playback implications.

### AI and random-state consequences

The imported initializer `0x00705D30` is split into false functions by preserved
analysis. Bytes over `0x00705D30..0x00705F97` establish the initial two-side
loop and selected-side profile copy: loop counter starts at zero, its body
calls resident `0x00180210(120)` at import `0x00705DE0`, increments at
`0x00705F10`, and branches back while below two at `0x00705F18/0x00705F1C`.
The true live entry is `0x00705D70`, file `0x051E70`. Remaining profile behavior
is owned by [AI state](../../knowledge/gameplay/session/battle_ai.md#per-side-state-block).
Calling this initializer for a dummy thus consumes two shared random draws and
changes the other side's transient AI work as well. It cannot be treated as a
dummy-only rewind or a deterministic re-run of a previous AI decision.

The existing [RNG investigation](practice_input_recording.md#reproducibility-and-rng)
establishes shared state and consumers outside dummy AI. A random guard,
wake-up, reversal, or recorded-situation selector using that same generator
would add draws to gameplay's sequence. A feature-local selector is a
provisional way to separate its choices, but restoring its choice alone would
not reproduce retail randomness or call order.

### Provisional repeat contract

The strongest bounded candidate is to repeat a defined setup and input/action
request, with separate guarantees for those two things. Identical outcomes
remain a stronger, unproved requirement. Candidate setup state includes both
fighters' placement/contact/action state, resources selected for the exercise,
live moveset availability, logical and matcher history, pending queue state,
retained guard/recovery/reversal choices, and paired/side-object lifetime.
Those domains are identified by the evidence; a complete safe restoration
sequence has not been established.

The initial-position and settled-bookmark alternatives remain owned by
[Position reset](practice_position_reset.md#provisional-placement-options).
Repetition could consume a completed reset contract and an input-recording
contract, rather than interpreting a coordinate write or clip-end event as a
completed reset. Current fighter pointers cannot be retained across native
battle reconstruction, and a newly sampled live action index must be checked
against the new fighter/provider. This is a provisional composition boundary,
not an implemented scheduler or an accepted persistence mechanism.

Unresolved product choices are the setup/bookmark lifetime, termination event,
repeat count, whether a selected response is retained or resampled per attempt,
and what "repeat" promises about resources and outcomes. No control binding,
menu schema, storage format, or executable hook is selected by this document.
