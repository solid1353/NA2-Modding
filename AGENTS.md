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
- The `General` task follows only explicit, simple commands. It must not infer
  extra actions, redesigns, routing, or repository changes.
- If uncertain, inspect and report instead of acting.

## Standing commands

- `dnf`: do not forward the attached message or its contents.
- `ag`: reread live `AGENTS.md` and apply it immediately.
- `q:`: queue the message in arrival order behind the current safe boundary.
- `con`: resume the current work without changing its scope or approval state.
- `eff`: report the current recommended effort without changing it.
- `sw`: resume after the user changed the chat to the recommended effort.
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
  applies only to workstreams that link it.
- `docs/workstreams/README.md` defines the workstream-policy storage boundary.
