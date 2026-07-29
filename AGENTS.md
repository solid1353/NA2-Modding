# AGENTS.md

PS2 modding/reverse-engineering workspace for Narutimate Accel v2.28, based on
Naruto Shippuuden: Narutimate Accel 2 / SLPS-25837.

## Core authority

- Read this file first, then read only the shared policies routed below that
  apply to the current work. A routed policy is mandatory when its trigger
  applies.
- Agents communicate with the user in English only.
- The task workflow and plan-approval gate apply only to explicitly selected
  `TASKS.md` work. Perform small, direct, low-risk changes immediately.
- Feasibility, preference, and design questions request discussion only.
  Read-only inspection is allowed; mutation requires an explicit action request.
- A question about current behavior, including angry or rhetorical wording,
  requests an explanation only. Never convert it into an instruction to start,
  stop, expose, hide, relaunch, or otherwise change the work. Answer it and
  continue approved work unchanged unless the user explicitly orders a change.
- When an answer is wrong, give the corrected answer immediately. Explain why
  the previous answer was wrong only if the user asks why.
- While approved work remains actionable, answer every question in commentary
  and resume the work immediately. A question never permits ending the turn
  with a final response.
- When the user declares discussion, design, planning, or brainstorming mode,
  later requirements remain discussion until the user explicitly authorizes
  execution. If authorization is ambiguous, ask.
- Never infer the user's desired action, authorization, classification,
  cleanup, rollback, or final state from complaints, context, or agent
  proposals. Perform only the requested change and unavoidable prerequisites.
- Keep disposable development tools to the simplest workflow that performs the
  requested function. Add only validation required to make that function work;
  optional guards, backups, recovery state, identity/hash enforcement, cleanup
  commands, restart requirements, or other workflow-blocking safeguards require
  explicit user authorization. If an unsolicited safeguard causes a failure,
  remove or simplify it; never repair it by adding another safeguard layer.
- For a selected task, only read-only inspection is allowed before plan
  approval. `approved`, `qwe`, or its same-key keyboard-layout equivalent
  approves the current plan, including when used in a longer message.
- Execute freely within approved scope. Stop and clarify if the task becomes
  materially unclear or the whole approach is wrong; a replacement plan needs
  approval.
- If the user says to do A, stop for testing/review/acceptance, and then do B,
  stop after A. Later requests to finish, batch work, or use one commit do not
  authorize B. Continue only when the user explicitly says to skip that
  required stop and proceed.
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
- `report` or `grid`: immediately preempt everything. The next user-visible
  response must be exactly one of: (1) the actual composed post-change
  report-grid images, or (2) `Cannot produce report grid: <exact reason>.
  Missing: <exact post-change input>.` No status, promise, findings, tool
  narration, implementation, final answer, or relay to another task may appear
  first. If post-change imagery is absent, use outcome (2) immediately; do not
  build, launch, investigate, or substitute source, donor, baseline, pre-fix,
  savestate-preview, or other input imagery. If the same message also orders a
  mistake report to `General`, satisfy this task-report response first and send
  the separate mistake report afterward; neither replaces the other.
- `sw`: resume after the user changed the chat to the recommended effort.
- `ss`: savestate; `ss<number>`: that numbered savestate slot in the user's
  PCSX2, for example `ss7`.
- `zxc`: checkpoint and stop gracefully for restart or reboot.
- `task done`: the owning workstream coordinator removes the uniquely
  identifiable current task and pushes the task-management update. This never
  means the task named `Task coordinator`.

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
- Treat `@source/` as protected read-only unless the user explicitly authorizes
  a specific source change. Treat both `@pcsx2_dev` and `@pcsx2_stable` as
  protected read-only user installations. Only an ISO launch explicitly
  requested by the user permits executing either installation; it never
  authorizes modifying it or otherwise controlling the user PCSX2 process.
- Never change binary files manually; all binary changes go through scripts.
- Run every shell, filesystem, script, and Git command elevated from the first
  attempt. On permission failure, retry the exact operation elevated.
- File-working tasks own `work/<exact task title>/` and have standing authority
  to create, modify, move, or delete anything inside that exact directory
  without separate destructive-action approval. This authority never extends
  outside the owned directory. Keep inputs, experiments, builds, logs, and
  runtime files there; reusable scripts belong under `scripts/`. At completion,
  promote useful findings and remove disposable artifacts, logs, and every
  empty directory.
- Agent PCSX2 uses only a task-owned clone of `@pcsx2_clean` with a unique PINE
  port. Agent-only runs use PCSX2 no-GUI mode, suppress any render window, and
  count as hidden only after a read-back check finds no visible top-level
  windows owned by the launched process; flags, `-WindowStyle Hidden`, and
  launch intent are not proof. If the worker process cannot remain hidden,
  terminate that newly launched process and fail. Never navigate emulator or
  game menus through PINE or injected input. If a required savestate was not
  supplied, stop and ask the user for that exact state.
- Never centrally migrate, replace, or clean another task's PCSX2 copy. Before
  reusing an existing copy for new work, its owning task audits it, promotes
  anything still needed, then replaces the whole copy from `@pcsx2_clean`.
  This audit includes PINE configuration, hot-reload PNACH state, savestates,
  screenshots, logs, memory cards, cheats, GameSettings, and input files. After
  that audit and promotion, the owner has standing authority to delete and
  recreate its complete `work/<exact task title>/pcsx2/` copy without another
  destructive-action approval. This authority never extends to another task's
  copy, `@pcsx2_clean`, `@pcsx2_dev`, or `@pcsx2_stable`.
- `na228 -t` and `_na228.ps1 -t` build ISOs; `-t` never means tests. The full
  builder test suite is
  `python -B -m unittest discover -s na228_builder/tests -p 'test_*.py'`.
  Never infer command semantics from a flag name; verify the documented exact
  command before execution.
- Keep hypothesis/candidate checks outside the permanent tracked suite and
  normal builds. Permanent coverage begins only after explicit user acceptance
  of the exact behavior; static-only coverage requires explicit user approval.
  TDD is allowed only when declared in an approved task plan against an
  independently established contract. Permanent tests protect approved
  behavior or documented safety requirements, never an unverified
  implementation merely because it currently exists.
- Only the user may change profile `bypass_check`; agents preserve it exactly.
- Preserve substantive disassembly, decompilation, and live-memory findings in
  canonical knowledge with identities, ranges, reconstructed behavior,
  evidence, useful negative results, and confidence. Never commit an
  implementation derived from such findings unless the canonical knowledge
  update is included in the same commit; never clean up its analysis artifacts
  before verifying that promotion.
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
- Profiles, builder architecture, binary edits, PNACH, source media, and text
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
