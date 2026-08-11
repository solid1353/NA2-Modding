# AGENTS.md

PS2 modding and reverse-engineering workspace for *Narutimate Accel v2.28*,
based on *Naruto Shippuuden: Narutimate Accel 2* / `SLPS-25837`.

## Universal rules

- Read this file first.
- `NA2-Modding`, `UN-Workshop`, maintained subrepositories such as the PCSX2
  fork, and future repositories added to this maintained project may be changed
  together when the task requires it. Cross-repository work needs no separate
  approval.
- Protect original source media and user-owned PCSX2 installations. Binary
  changes must be reproducible, guarded, and script-owned.

## Discussion and action

- During explicit discussion, design, planning, or brainstorming, later messages
  refine the proposed result. They do not authorize implementation until the
  applicable approval boundary is reached.
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

## Continuation and stopping

- “Active work” means an ongoing user request. An open task, workstream,
  uncommitted candidate, dirty files, or other repository state is not a user
  request and cannot make work active.
- Work remains executable while an in-scope next action can be performed without
  required user input or a required material decision.
- Questions, corrections, status requests, and other interruptions do not end
  active work. Answer them in commentary, then continue the authorized work.
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

## Completion reports

Before reporting completion, review the actual final diff and validation
results. For serious work, report:

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

## Agent commands

On every new task, read and follow
[`Normal mode`](docs/workflows/normal_mode.md) and every routed policy triggered
by the request before stating implementation intent, scope, approach, or
validation. Any required pre-tool commentary may state only that the applicable
context is being loaded. Exact mode-entry commands and other directly routed
commands are listed below. No other wording enters a mode; when a mode exits,
Normal mode resumes.

Exactly one workflow mode is active at a time. Only the active mode's workflow
document applies; all other mode workflow documents are inactive. Entering a
mode deactivates the previous mode. When Design mode or Interactive mode exits,
Normal mode becomes active again. Universal rules and applicable routed
policies remain active in every mode.

| Command | Read |
| --- | --- |
| `des mode`, `design mode` | [`docs/workflows/design_mode.md`](docs/workflows/design_mode.md) |
| `int mode`, `interactive mode` | [`docs/workflows/interactive_mode.md`](docs/workflows/interactive_mode.md) |
| `zxc` | [`docs/procedures/graceful_stop.md`](docs/procedures/graceful_stop.md) |
| `qwe`, `snap`, `tasks`, `task done`, `c`, `c on`, `c off`, `ver`, `mode`, `n`, `ag`, `q:`, `con`, `e2e`, `sum`, `ex`, `eff`, `sw`, `ss`, `mute`, `unmute` | [`AGENT_COMMANDS.md`](AGENT_COMMANDS.md) |

## Policy routing

Read only the routed policy whose trigger applies:

| Work | Read |
| --- | --- |
| Git, paths, work directories, elevation, cleanup, scripts, documentation layout | [`docs/policies/repository.md`](docs/policies/repository.md) |
| validation, tests, builds, PCSX2, runtime injection, E2E | [`docs/policies/testing.md`](docs/policies/testing.md) |
| profiles, builder inputs, binaries, donor data, source media, PNACH | [`docs/policies/modding.md`](docs/policies/modding.md) |
| reverse engineering, disassembly, evidence, knowledge, hypotheses | [`docs/policies/research.md`](docs/policies/research.md) |
| `TASKS.md`, workstreams, project chats, Notifications | [`docs/policies/coordination.md`](docs/policies/coordination.md) |

Read component documentation only when working on that component. Read a task's
directly linked documentation when entering or resuming that task, not before
every message. `TASKS.md`, handoffs, knowledge, research, hypothesis, and large
technical documents are not default context; load them only when the current
request requires them. For a large technical document, read only the relevant
sections unless broader context is necessary.

## Maintaining policy

Refine, consolidate, move, or restructure existing rules instead of layering
new rules on top of them. Do not duplicate policy; when touching duplicated
policy, reduce or eliminate the duplication.

Keep this file a small universal entrypoint and router. Add a rule here only
when it genuinely applies to nearly every task. Put scoped rules in their
routed policy or component document and link to the canonical owner instead of
copying it. Materially expanding this file's purpose or scope requires explicit
user approval.
