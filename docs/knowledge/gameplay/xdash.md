# X-dash

Native X-dash action states, cancellation boundary, movement transition, and
chakra behavior.

## Research coverage

- **Assigned scope:** establish the native X-dash action record, phase and
  substate transitions, cancellation boundary, and chakra-cost behavior.
- **Exploration depth:** the action selector, cost path, all centralized phase
  writers, and three completed or cancelled attempts were traced.
- **Confirmed coverage:** action index `0x13`, its native zero cost, cancellable
  preparation, committed movement, hit transition, and the first persistent
  post-cancellation state are established.
- **Unresolved or untested:** whether any character-specific X-dash variant
  bypasses the shared state machine.
- **Deliberate exclusions and overlap:** NA228's configurable cost and hook
  belong to [Battle](../../features/battle.md).
- **Evidence limitations:** the runtime trace covered one Kakashi-versus-Sai
  Practice sequence and bounded instrumentation of the known phase writers.

## Native action and cost

X-dash uses major action state `8`, action index `0x13`, and phases `0`, `1`,
and `2`. Its action record is `fighter[+0xA54] + 0x13 * 0x54`; field `+0x10` is
type `2`, field `+0x1C` is `0x02000011`, and native float cost `+0x20` is
`0.0`. The unmodified action therefore consumes no chakra.

`FUN_00239530` selects action index `0x13`. After acceptance,
`FUN_0023A9A0` loads the record cost at `0x0023AAF0`, subtracts and clamps it at
`0x0023AC00..0x0023AC20`, and calls `FUN_00217E40` to enter the action.
Because record type `2` returns before the ordinary affordability check, the
native action has no minimum-chakra requirement.

## State transitions

Phase `0` is cancellable preparation. Phase `1` represents dash movement, and
phase `2` is the hit transition. A phase write alone is not a safe commitment
boundary: phases `1` and `2` can both be written transiently during an update
that ultimately cancels the action.

The internal state at fighter `+0x9BA` distinguishes the transition.
`FUN_0023C230` sees state `1` during preparation. When the animation crosses
its start threshold, `FUN_0023C0F0` changes that field to `2`, writes phase `1`,
and installs movement physics. The state-2 branch later handles contact and
calls `FUN_0023D980`, which changes the internal state to `3` and phase to `2`.
`FUN_0023D980` is hit-response processing, not dash-start processing.

Bounded tracing of the direct setter, generic increment, and seven centralized
event stores produced these ordered paths:

- completed dash: phase `0`/substate `1`, then persistent phase `1`/substate
  `2`, then phase `2`/substate `3`;
- early cancellation: phase `0`/substate `1` directly to another major action;
- final-frame cancellation: a transient phase-1 write followed by direct exit
  from preparation to another major action.

The first fighter-update boundary entered with phase `1` and substate `2` is
therefore the first persistent state after the final cancellation opportunity.
The configurable NA228 consumer of that boundary is documented in
[Battle](../../features/battle.md).
