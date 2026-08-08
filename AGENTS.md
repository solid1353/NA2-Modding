# AGENTS.md

PS2 modding and reverse-engineering workspace for *Narutimate Accel v2.28*,
based on *Naruto Shippuuden: Narutimate Accel 2* / `SLPS-25837`.

## Universal rules

- Read this file first. Communicate with the user in English.
- The user may override any repository instruction. The scope and duration of an
  override follow the user's wording; unrelated rules remain active.
- Do not alter or extend the requested contract. If you believe a different
  contract would be better, ask the user before changing it.
- `NA2-Modding`, `UN-Workshop`, maintained subrepositories such as the PCSX2
  fork, and future repositories added to this maintained project may be changed
  together when the task requires it. Cross-repository work needs no separate
  approval.
- Before making changes, state `Changes:` and `Needed from you:`. If useful user
  input is required, ask for it and wait instead of pursuing a materially less
  efficient substitute. This applies throughout the work, not only at startup.
- Run every shell, filesystem, script, and Git operation elevated from the first
  attempt. If the elevated operation still fails, report the exact failure; do
  not invent alternate workflows or helper machinery to evade it.
- Preserve unrelated work. Protect original source media and user-owned PCSX2
  installations. Binary changes must be reproducible, guarded, and script-owned.
- Do not introduce a new long-lived project mechanism or project-wide contract
  without explicit approval. Ordinary code-level implementation choices inside
  approved scope do not need separate approval.
- Never claim validation, runtime behavior, user acceptance, or completion that
  has not actually occurred.

## Task authorization

- Small, direct tasks do not require a separate design phase.
- Work is serious when it requires design decisions about architecture,
  user-visible behavior, compatibility, or coordinated changes across multiple
  components. Design serious work interactively; do not
  implement it until the user approves the consolidated implementation snapshot
  with `approved`, `qwe`, or the same physical keys under another keyboard
  layout.
- A serious-work snapshot states the outcome, scope, important architecture or
  behavior, proposed persistent mechanisms, and planned validation.
- When the user asks a question, the agent MUST answer it and MUST NOT perform,
  start, authorize, infer, schedule, or resume any action based on that
  question. The agent also MUST NOT stop, pause, abandon, replace, or end active
  authorized work because the question was asked. After answering, the agent
  MUST continue only the work already authorized before the question. A
  question never grants approval and never satisfies a requested decision.

Detailed interaction and authorization rules are in
[`docs/policies/interaction.md`](docs/policies/interaction.md).

## Agent commands

Canonical command semantics are in
[`docs/AGENT_COMMANDS.md`](docs/AGENT_COMMANDS.md). The command index is:

`approved`, `qwe`, `tasks`, `task done`, `dnf`, `ag`, `q:`, `con`, `e2e`,
`sum`, `eff`, `report`, `sw`, `ss`, `zxc`, `mute`, `unmute`.

## Policy routing

Read only the routed policy whose trigger applies:

| Work | Read |
| --- | --- |
| conversation, authorization, sequencing, user inputs, completion reports | [`docs/policies/interaction.md`](docs/policies/interaction.md) |
| Git, paths, work directories, elevation, cleanup, scripts, documentation layout | [`docs/policies/repository.md`](docs/policies/repository.md) |
| validation, tests, builds, PCSX2, runtime injection, E2E | [`docs/policies/testing.md`](docs/policies/testing.md) |
| profiles, builder inputs, binaries, donor data, source media, PNACH | [`docs/policies/modding.md`](docs/policies/modding.md) |
| reverse engineering, disassembly, evidence, knowledge, hypotheses | [`docs/policies/research.md`](docs/policies/research.md) |
| `TASKS.md`, workstreams, project chats, Notifications | [`docs/policies/coordination.md`](docs/policies/coordination.md) |

Read component documentation only when working on that component. Read durable
workstream-specific documentation when entering or resuming that workstream,
not before every message. `TASKS.md`, knowledge, research, hypothesis, and large
technical documents are not default context; load them only when the current
request requires them. For a large technical document, read only the relevant
sections unless broader context is necessary.

## Maintaining this file

Keep this file a small universal entrypoint and router. Add a rule here only
when it genuinely applies to nearly every task. Put scoped rules in their
routed policy or component document, link to the canonical owner instead of
copying it, and consolidate existing wording rather than appending an overlap.
Materially expanding this file's purpose or scope requires explicit user
approval.
