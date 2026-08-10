# AGENTS.md

PS2 modding and reverse-engineering workspace for *Narutimate Accel v2.28*,
based on *Naruto Shippuuden: Narutimate Accel 2* / `SLPS-25837`.

## Universal rules

- Read this file first. Communicate with the user in English.
- The user may override any repository instruction. The scope and duration of an
  override follow the user's wording; unrelated rules remain active.
- For implementation work, do not alter or extend the requested outcome or
  scope; ask before implementing a different contract. This does not govern
  policy wording or documentation structure.
- `NA2-Modding`, `UN-Workshop`, maintained subrepositories such as the PCSX2
  fork, and future repositories added to this maintained project may be changed
  together when the task requires it. Cross-repository work needs no separate
  approval.
- Preserve unrelated work. Protect original source media and user-owned PCSX2
  installations. Binary changes must be reproducible, guarded, and script-owned.
- Do not introduce a new long-lived project mechanism or project-wide contract
  without explicit approval. Ordinary code-level implementation choices inside
  approved scope do not need separate approval.
- Never claim validation, runtime behavior, user acceptance, or completion that
  has not actually occurred.

## Task authorization

- **NEVER send a final response while authorized work remains unfinished and
  executable. Answer interruptions in commentary and continue working until
  completion, explicit cancellation, or a hard blocker.**
- When the user asks a question, the agent MUST answer it. If an accurate answer
  depends on information that has not already been verified, the agent may
  perform any necessary non-mutating inspection or research—including
  repository inspection, current-state checks, and web searches—before
  answering. The agent MUST NOT treat a question as authorization to modify
  state, implement work, schedule work, or perform any other state-changing
  action. A question is not approval and does not satisfy a requested decision.

Detailed interaction and authorization rules are in
[`docs/INTERACTION.md`](docs/INTERACTION.md).

## Agent commands

Read and follow [`Normal mode`](docs/workflows/normal_mode.md) by default. Exact
mode-entry commands and other directly routed commands are listed below. No
other wording enters a mode; when a mode exits, Normal mode resumes.

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
| `qwe`, `snapshot`, `tasks`, `task done`, `c`, `c on`, `c off`, `ver`, `mode`, `n`, `ag`, `q:`, `con`, `e2e`, `sum`, `eff`, `sw`, `ss`, `mute`, `unmute` | [`docs/AGENT_COMMANDS.md`](docs/AGENT_COMMANDS.md) |

## Policy routing

Read only the routed policy whose trigger applies:

| Work | Read |
| --- | --- |
| conversation, authorization, sequencing, user inputs, completion reports | [`docs/INTERACTION.md`](docs/INTERACTION.md) |
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
