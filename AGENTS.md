# AGENTS.md

PS2 modding and reverse-engineering workspace for *Narutimate Accel v2.28*,
based on *Naruto Shippuuden: Narutimate Accel 2* / `SLPS-25837`.

## Project scope

- `NA2-Modding`, `UN-Workshop`, maintained subrepositories such as the PCSX2
  fork, and future repositories added to this maintained project may be changed
  together when the task requires it. Cross-repository work needs no separate
  approval.

## Discussion and action

- During explicit discussion, design, planning, or brainstorming, later messages
  refine the proposed result.
- A discussion summary contains only the intended changes, integrates accepted
  corrections, excludes rejected or withdrawn changes, and adds no new changes.

## Task sequencing

- The user may add any number of tasks. Keep them in order and work through them
  in that order.
- A new task does not interrupt current work unless the user says to do it
  immediately. `Immediately` changes priority, not cancellation; afterward,
  resume the interrupted work automatically.

## Implementation boundaries

- Choose ordinary code-level implementation details inside the approved outcome
  and scope.
- Ask before changing unrequested user-visible behavior or introducing a new
  long-lived project mechanism or project-wide contract.
- A new mandatory workflow, pipeline stage, public wrapper/command, canonical
  generator output, manifest, schema, configuration contract, required
  persistent state, or production/build/CI/runtime integration requires
  approval.
- Dependencies use the existing dependency mechanism of the affected component
  and need no separate approval. A new package-management mechanism does.
- A command, recipe, selector, profile, or other interface presented for a
  requested scope must actually cover that scope. State a limitation instead of
  presenting a narrower case as the full solution.

## Action boundary

Immediately before any state-changing operation in any workflow, state:

```text
Changes: <what will be changed>
Mode: <Normal mode, Design mode, or Interactive mode>
<workflow-specific settings>
Will need from you: <later user action or nothing>
```

Always include `Changes`, `Mode`, and `Will need from you`. Include every setting
defined by the active workflow.

If user input is required before or during the operation, or would noticeably
improve its efficiency or quality, request it and do not begin or continue the
operation. Present the action boundary only when the operation can begin.

## Evidence and troubleshooting

- When citing file lines, quote the relevant text and attach its clickable
  citation. Never use bare line numbers or citations without the supporting
  text.
- Treat explicit user observations and established evidence as current facts
  unless specific new evidence contradicts them.
- When the task concerns a state currently visible or running, inspect that
  state or ask for the exact missing input; historical artifacts are context,
  not a substitute.
- If a proven execution path produces no requested observable change, trace
  forward from the last proven point to the first unproven consumer rather than
  restarting earlier layers or reviving rejected theories.

## Completion reports

Before reporting completion, review the actual final diff and validation
results. Report the applicable items below:

- the achieved outcome and how it matches the approved snapshot;
- deviations, omitted items, or additional changes;
- important implementation changes grouped by purpose;
- user-visible behavior changes;
- every new persistent mechanism or contract, or explicitly that none were
  introduced;
- for work routed through the research policy, the canonical knowledge files
  updated and the disposition of supporting analysis;
- exact validation and its result;
- remaining limitations, uncertainty, risks, or unverified areas;
- commit and push state.

Use enough concrete detail that the user can understand the result without
reviewing the source. Do not add empty template sections or repeat information
merely to satisfy a format.

## Context and command routing

On every new task, read and follow
[`Normal mode`](docs/workflows/normal_mode.md) and every routed policy triggered
by the request before stating implementation intent, scope, approach, or
validation. Any required pre-tool commentary may state only that the applicable
context is being loaded.

### Workflow modes

Exactly one workflow mode is active at a time. Only the active mode's workflow
document applies; all other mode workflow documents are inactive. Entering a
mode deactivates the previous mode. Global and project-wide rules and applicable
routed policies remain active in every mode. No wording other than the exact
commands below enters a mode; when a mode exits, Normal mode resumes.

### Command index

Canonical command definitions and their workflow or procedure routing are in
[`AGENT_COMMANDS.md`](AGENT_COMMANDS.md).

Command index: `des mode`, `design mode`, `int mode`, `interactive mode`,
`snap`, `imp`, `ver`, `commit`, `exit`, `zxc`, `tasks`, `task done`, `c`,
`c on`, `c off`, `mode`, `n`, `ag`, `q:`, `con`, `e2e`, `sum`, `diff`, `ex`,
`eff`, `sw`, `ss`, `mute`, `unmute`.

### Policy routing

Read only the routed policy whose trigger applies:

| Work | Read |
| --- | --- |
| Git, paths, work directories, elevation, cleanup, scripts, documentation layout | [`docs/policies/repository.md`](docs/policies/repository.md) |
| validation, tests, builds, PCSX2, runtime injection, E2E | [`docs/policies/testing.md`](docs/policies/testing.md) |
| profiles, builder inputs, binaries, donor data, source media, PNACH | [`docs/policies/modding.md`](docs/policies/modding.md) |
| reverse engineering, disassembly, evidence, knowledge, hypotheses | [`docs/policies/research.md`](docs/policies/research.md) |
| `TASKS.md`, concurrent work, project chats, Notifications | [`docs/policies/coordination.md`](docs/policies/coordination.md) |

Read component documentation only when working on that component. Read a task's
directly linked documentation when entering or resuming that task, not before
every message. `TASKS.md`, handoffs, knowledge, research, hypothesis, and large
technical documents are not default context; load them only when the current
request requires them. For a large technical document, read only the relevant
sections unless broader context is necessary.

## Maintaining policy

- Keep this file a small universal entrypoint and router. Add a rule here only
  when it genuinely applies to nearly every task. Put scoped rules in their
  routed policy or component document and link to the canonical owner instead
  of copying it. Materially expanding this file's purpose or scope requires
  explicit user approval.
