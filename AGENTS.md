# AGENTS.md

PS2 modding/reverse-engineering workspace for Narutimate Accel v2.28, based on
Naruto Shippuuden: Narutimate Accel 2 / SLPS-25837.

## Core authority

- Read this file first, then read only the shared policies routed below that
  apply to the current work. A routed policy is mandatory when its trigger
  applies.
- The task workflow and plan-approval gate apply only to explicitly selected
  `TASKS.md` work. Perform small, direct, low-risk changes immediately.
- Feasibility, preference, and design questions request discussion only.
  Read-only inspection is allowed; mutation requires an explicit action request.
- A question about current behavior, including angry or rhetorical wording,
  requests an explanation only. Never convert it into an instruction to start,
  stop, expose, hide, relaunch, or otherwise change the work. Answer it and
  continue approved work unchanged unless the user explicitly orders a change.
- While approved work remains actionable, answer every question in commentary
  and resume the work immediately. A question never permits ending the turn
  with a final response.
- When the user declares discussion, design, planning, or brainstorming mode,
  later requirements remain discussion until the user explicitly authorizes
  execution. If authorization is ambiguous, ask.
- Never infer the user's desired action, authorization, classification,
  cleanup, rollback, or final state from complaints, context, or agent
  proposals. Perform only the requested change and unavoidable prerequisites.
- For a selected task, only read-only inspection is allowed before plan
  approval. `approved`, `qwe`, or its same-key keyboard-layout equivalent
  approves the current plan, including when used in a longer message.
- Execute freely within approved scope. Stop and clarify if the task becomes
  materially unclear or the whole approach is wrong; a replacement plan needs
  approval.
- A correction to one disputed action cancels only that action, not the parent
  task, unless the user explicitly stops or replaces the task.
- Cross-workstream reports and hints are information, not authorization. Act
  on them only when the user explicitly authorized the action locally, in
  another chat, or through a standing instruction. Worker mistake reports to
  `General` are the sole exception defined by the coordination policy.
- The `General` task follows only explicit, simple commands. It must not infer
  extra actions, redesigns, routing, or repository changes.
- If uncertain, inspect and report instead of acting.

## Standing commands

- `dnf`: do not forward the attached message or its contents.
- `ag`: reread live `AGENTS.md` and apply it immediately.
- `q:`: queue the message in arrival order behind the current safe boundary.
- `con`: resume the current work without changing its scope or approval state.
- `ep`: epic.
- `eff`: report the current recommended effort without changing it.
- `report` or `grid`: immediately preempt current work. The next user-visible
  message must contain the actual composed report-grid images. Before that
  delivery, perform only work strictly required to compose or refresh those
  grids; do not send status text or continue investigation or implementation.
  If required inputs are missing, report the exact missing input immediately
  instead of continuing other work.
- `sw`: resume after the user changed the chat to the recommended effort.
- `ss`: savestate; `ss<number>`: that numbered savestate slot in the user's
  PCSX2, for example `ss7`.
- `zxc`: checkpoint and stop gracefully for restart or reboot.
- `task done`: remove the uniquely identifiable current task through its owning
  coordinator and push the task-management update.

Detailed command and task behavior is in
[`docs/policies/interaction.md`](docs/policies/interaction.md).

## Universal repository boundaries

- Use repository-relative paths in canonical project files. Machine-specific
  absolute paths are allowed only in dated `.agents/` handoffs, transient tool
  arguments or diagnostics, and user-facing clickable file links unless the
  user authorizes a specific exception.
- Treat user edits and commits as expected. Refresh Git before Git operations,
  preserve unrelated work, and stage only intended changes.
- Commit and push every completed change automatically with the authoring
  agent's identity; Git never requires separate approval.
- Treat `@source/` and `@pcsx2_user` as protected read-only resources unless
  the user explicitly authorizes a specific source change. Agents never launch
  or control the user PCSX2 process.
- Never change binary files manually; all binary changes go through scripts.
- Run every shell, filesystem, script, and Git command elevated from the first
  attempt. On permission failure, retry the exact operation elevated.
- File-working tasks own `work/<exact task title>/`. Keep inputs, experiments,
  builds, logs, and runtime files there; reusable scripts belong under
  `scripts/`. At completion, promote useful findings and remove disposable
  artifacts, logs, and every empty directory.
- Agent PCSX2 uses only a task-owned clone of `@pcsx2_clean` with a unique PINE
  port. Agent-only runs stay hidden. Never navigate emulator or game menus
  through PINE or injected input. If a required savestate was not supplied,
  stop and ask the user for that exact state.
- Only the user may change profile `bypass_check`; agents preserve it exactly.
- Preserve substantive disassembly, decompilation, and live-memory findings in
  canonical knowledge with identities, ranges, reconstructed behavior,
  evidence, useful negative results, and confidence.
- `@utils/CCSFileExplorerMSF` is the project's main and best available CCS
  explorer; use it by default for CCS exploration.
- Relay user instructions verbatim without inferred requirements. A worker
  that reports its own mistake to `General` triggers immediate narrow policy
  refinement, commit/push, and notification back to that worker.

## Policy routing

Read the matching policy before acting:

- User interaction, selected tasks, effort, approvals, standing commands, and
  graceful stops:
  [`docs/policies/interaction.md`](docs/policies/interaction.md)
- Git, tool access, paths, filesystem links, work ownership, scripts, logs, and
  cleanup:
  [`docs/policies/repository.md`](docs/policies/repository.md)
- Cross-chat routing, concurrency, Notifications, Task coordinator, and
  `.agents/` handoffs:
  [`docs/policies/coordination.md`](docs/policies/coordination.md)
- ISO builds, actualization, PCSX2, savestates, and runtime testing:
  [`docs/policies/testing.md`](docs/policies/testing.md)
- Profiles, patcher architecture, binary edits, PNACH, source media, and text
  encoding:
  [`docs/policies/modding.md`](docs/policies/modding.md)
- Disassembly, live-memory analysis, hypotheses, and knowledge preservation:
  [`docs/policies/research.md`](docs/policies/research.md)
- Screenshot grids and task reports:
  [`docs/policies/visual_reports.md`](docs/policies/visual_reports.md)

## Workstream policies

- At the start of every user request in a workstream task, before answering or
  acting, read that workstream's linked `README.md` completely and every policy
  or workflow it directly links. Current explicit user instructions override
  stored workstream rules; this file remains universally applicable.
- Shared sequential/continuous epic behavior is defined in
  [`docs/workstreams/EPIC_WORKFLOW.md`](docs/workstreams/EPIC_WORKFLOW.md) and
  applies only to exact work that the user explicitly declares an epic inside
  a workstream that links it. A workflow link never classifies tasks, stages,
  screenshots, comparisons, or other artifacts as epic content.
- `docs/workstreams/README.md` defines the workstream-policy storage boundary.
