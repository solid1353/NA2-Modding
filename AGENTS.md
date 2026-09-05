# AGENTS.md

Commit: agent-identity
Commit-Roots:
  - .
Push: auto

PS2 modding and reverse-engineering workspace for *Narutimate Accel v2.28*,
based on *Naruto Shippuuden: Narutimate Accel 2* / `SLPS-25837`.

## Project and implementation boundaries

- `NA2-Modding`, `UN-Workshop`, maintained subrepositories such as the PCSX2
  fork, and future repositories added to this maintained project may be changed
  together when the task requires it. Cross-repository work needs no separate
  approval.
- Master Mode and Shop are globally out of scope. Do not work on or document
  them.
- After replacing or removing behavior, delete its retired code and tests.
  Do not retain compatibility, detection, rejection, fallback, migration, or
  retirement checks unless explicitly requested. Verify removals with temporary
  searches or checks discarded before completion.
- Ask before changing unrequested user-visible behavior or introducing a new
  mandatory workflow, public interface, persistent mechanism, project-wide
  contract, or production/build/CI/runtime integration.

## Task sequencing

- Treat a later request as a new task unless it explicitly modifies, cancels,
  replaces, reorders, or asks about existing work, or supplies requested input.
- Treat a user-aborted turn as cancellation of its unfinished work. Resume that
  work only after a new operative command.
- Keep unfinished tasks in arrival order. Work only on the oldest task's next
  unfinished instruction; do not inspect, prepare, or start later work. A
  correction does not alter or reorder other unfinished work.
- `Immediately` temporarily moves the newest task to the front. After it
  finishes, resume the interrupted task, then continue the queue.

## Action boundary

Immediately before beginning state-changing work in any workflow, state:

```text
Changes: <what will be changed>
Validation: <how the changes will be validated>
Required user actions: <later user action or nothing>
<workflow-specific settings>
```

Include every setting defined by the active workflow.

If user input is required or would materially improve efficiency or quality,
request it before beginning or continuing work; do not substitute arbitrary
inputs. Present the action boundary only when work can begin.

## Evidence and completion

- When citing file lines, quote the relevant text and attach its clickable
  citation. Never use bare line numbers or citations without the supporting
  text.
- Treat explicit user observations and established evidence as current facts
  unless specific new evidence contradicts them.

Before reporting completion, review the actual final diff and validation results.
Report the achieved outcome, material deviations or user-visible changes, exact
validation and its result, remaining limitations or risks, and commit and push
state. Keep the report concrete and concise; omit inapplicable items.

## Context and command routing

Fresh chats start with no interaction mode active. Before stating
implementation intent or changing state, read the active
[Design](docs/interactions/design_mode.md) or
[Interactive](docs/interactions/interactive_mode.md) mode document and policies
routed by the request.

Read a routed workflow before describing its execution.

### Commands and interaction modes

Only the exact indexed commands change the active interaction mode. The active
mode's document applies alongside global, project-wide, and routed policies.
Exiting Design or Interactive mode returns to the default state with no active
mode.

Canonical project command definitions and their workflow or procedure routing
are in [`AGENT_COMMANDS.md`](AGENT_COMMANDS.md).

Command index: `des mode`, `design mode`, `int mode`, `interactive mode`,
`snap`, `ver`, `exit`, `zxc`, `mode`, `n`, `imm`, `e2e`, `ss`.

### Policy routing

Read only routed policies whose triggers apply:

| Work | Read |
| --- | --- |
| Work directories, task-owned files, external inputs, temporary files, workflow outputs, task logs | [`docs/policies/work_directories.md`](docs/policies/work_directories.md) |
| Path configuration, configured roots, manifests, path loaders | [`docs/policies/paths.md`](docs/policies/paths.md) |
| Git, protected files and directories, source media, disassembly, savestates, input recordings, PCSX2, elevation, repository cleanup, scripts, documentation layout | [`docs/policies/repository.md`](docs/policies/repository.md) |
| validation, tests, builds, PCSX2, runtime injection, E2E | [`docs/policies/testing.md`](docs/policies/testing.md) |
| profiles, builder inputs, binaries, donor data, source media, PNACH | [`docs/policies/modding.md`](docs/policies/modding.md) |
| reverse engineering, disassembly, runtime investigation, knowledge, hypotheses | [`docs/policies/research.md`](docs/policies/research.md) |

On entering a task, read its directly linked documentation and relevant
component documentation. Load other technical documents only when required,
and read only relevant sections of large documents.

Keep this file a small universal router. Add only rules that apply to nearly
every task; expanding its purpose or scope requires explicit user approval.
