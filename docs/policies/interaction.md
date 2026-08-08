# Interaction and task policy

**Applies when:** discussing work, deciding authorization, sequencing tasks,
requesting user inputs, troubleshooting an observable result, or reporting
completion.

## Discussion and action

- During explicit discussion, design, planning, or brainstorming, later messages
  refine the proposed result. They do not authorize implementation until the
  applicable approval boundary is reached.
- A user correction changes the named point only. Preserve unaffected approved
  work and continue it unless the user explicitly stops, pauses, cancels, or
  replaces it.
- A discussion summary preserves every accepted point, integrates corrections,
  excludes rejected wording, and adds nothing new.

## Work announcement and user inputs

Before starting changes, state:

```text
Changes: <what will be changed>
Needed from you: <required input or nothing>
```

If `Needed from you` is not `nothing`, do not start. Ask early for any
savestate, screenshot, dump, file, reproduction, access, decision, or other
user input that is required or would noticeably improve efficiency or quality.
The ability to continue through a substantially slower or more speculative
route is not a reason to avoid asking. Resume automatically after the input is
provided.

## Task sequencing

- The user may add any number of tasks. Keep them in order and work through them
  in that order.
- A new task does not interrupt current work unless the user says to do it
  immediately. `Immediately` changes priority, not cancellation; afterward,
  resume the interrupted work automatically.
- If a later item is serious, finish already-authorized small items in order and
  queue the serious item for design unless the user makes it immediate.

## Small and serious work

- Small, direct work does not require a separate design phase.
- Work is serious when it requires decisions about architecture, user-visible
  behavior, compatibility, or coordinated changes across multiple components.
- Design serious work through normal responsive dialogue. Read-only inspection
  is allowed; canonical implementation changes are not.
- Natural-language agreement such as `yes`, `good`, or `do that` approves the
  current design point only. Once settled, present one concise implementation
  snapshot containing the intended outcome, scope, important architecture or
  behavior, proposed persistent mechanisms, and planned validation.
- Begin implementation only after `approved`, `qwe`, or its same-key
  keyboard-layout equivalent. If implementation requires a material change to
  the snapshot, present that changed part and wait for the same approval.

## Implementation boundaries

- Choose ordinary code-level implementation details inside the approved outcome
  and scope.
- Ask before expanding the requested outcome or scope, changing unrequested
  user-visible behavior, or introducing a new long-lived project mechanism or
  project-wide contract.
- A new mandatory workflow, pipeline stage, public wrapper/command, canonical
  generator output, manifest, schema, configuration contract, required
  persistent state, or production/build/CI/runtime integration requires
  approval.
- Dependencies use the existing dependency mechanism of the affected component
  and need no separate approval. A new package-management mechanism does.
- A command, recipe, selector, profile, or other interface presented for a
  requested scope must actually cover that scope. State a limitation instead of
  presenting a narrower case as the full solution.

## Continuation and stopping

- “Active work” means an ongoing user request. An open task, workstream,
  uncommitted candidate, dirty files, or other repository state is not a user
  request and cannot make work active.
- Stop only for an explicit stop/pause/cancel, required user input, or a required
  user decision such as a material change to an approved serious-work design.

## Evidence and troubleshooting

- Treat explicit user observations and established evidence as current facts
  unless specific new evidence contradicts them.
- When the task concerns a state currently visible or running, inspect that
  state or ask for the exact missing input; historical artifacts are context,
  not a substitute.
- If a proven execution path produces no requested observable change, trace
  forward from the last proven point to the first unproven consumer rather than
  restarting earlier layers or reviving rejected theories.
- Do not claim observable success from configuration, compilation, an applied
  write, or an intended code path alone.

## Completion report

Before reporting completion, review the actual final diff and validation
results. For serious work, report:

- the achieved outcome and how it matches the approved snapshot;
- deviations, omitted items, or additional changes;
- important implementation changes grouped by purpose;
- user-visible behavior changes;
- every new persistent mechanism or contract, or explicitly that none were
  introduced;
- exact validation and its result;
- remaining limitations, uncertainty, risks, or unverified areas;
- commit and push state.

Use enough concrete detail that the user can understand the result without
reviewing the source. Do not add empty template sections or repeat information
merely to satisfy a format.
