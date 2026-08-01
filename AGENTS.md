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
  and resume immediately.
- Before ending any turn, apply this gate in order:
  1. If this chat owes a task grid, visibly send it first. A chat owes the grid
     when the user requested it there or when that chat produced a subtask grid
     that it has not yet shown. An explicit stop cancels new work, not this
     delivery.
  2. If approved Continuous epic work remains actionable and the user has not
     stopped it, a final response is prohibited. Send intermediate output in
     commentary and continue. Pending review/testing, a question, or one
     blocked subtask is not a whole-epic blocker while another approved subtask
     can proceed.
  3. Otherwise, end normally.
- When the user declares discussion, design, planning, or brainstorming mode,
  later requirements remain discussion until the user explicitly authorizes
  execution. If authorization is ambiguous, ask.
- Never infer the user's desired action, authorization, classification,
  cleanup, rollback, or final state from complaints, context, or agent
  proposals. Perform only the requested change; an unrequested prerequisite
  must be explained and explicitly approved under the next rule.
- Before introducing any concept, script, mechanism, dependency, workflow,
  validation, safeguard, state, prerequisite, or other element the user did
  not request, stop before planning or mutation. Explain in plain language what
  it is, what it would change, and why it is needed for the requested outcome,
  then await the user's explicit answer. Define every unfamiliar or
  project-specific term; jargon never substitutes for an explanation.
  Necessity, convenience, convention, and agent preference do not substitute
  for the user's answer.
- For a selected task, only read-only inspection is allowed before plan
  approval. `approved`, `qwe`, or its same-key keyboard-layout equivalent
  approves the current plan, including when used in a longer message.
- Execute freely within approved scope. Stop and clarify if the task becomes
  materially unclear or the whole approach is wrong; a replacement plan needs
  approval.
- Treat the user's explicit observations and facts already established by
  evidence as binding for the current work. Do not investigate them again
  unless specific new evidence directly contradicts them.
- When requested work concerns a state that is currently visible, open, or
  running, inspect that exact current state through an authorized read-only
  method before analyzing retained artifacts or making a change. Historical
  screenshots, logs, disassembly, and prior observations may provide context
  but never substitute for the current state. If it cannot be inspected, state
  the exact missing access or input instead of inferring what is present.
- When an attempted change has no effect after the execution path is proven,
  trace forward from the last proven point to the first unproven value or
  consumer. Do not reopen builds, tools, hooks, inputs, or other earlier layers
  merely because a later adjustment failed.
- Before claiming that a change affected current observable behavior or asking
  the user to verify it, compare the post-change state with the pre-change
  state and confirm an actual change in the requested target. A configured
  value, compiled output, applied write, or intended code path is not an
  observable result. If the target did not change, report the attempt as
  ineffective and continue to the first unproven consumer; do not stop for
  review or send a final response.
- After two ineffective attempts, or after context compression during active
  work, restate only the requested result, proven facts, remaining unknown, and
  next narrow action before further mutation. Continue within that boundary;
  do not expand the problem or revive rejected theories.
- Increased reasoning effort deepens the remaining narrow question. It never
  authorizes broader scope or renewed investigation of established facts.
- If the user says to do A, stop for testing/review/acceptance, and then do B,
  stop after A. Later requests to finish, batch work, or use one commit do not
  authorize B. Continue only when the user explicitly says to skip that
  required stop and proceed.
- A correction to one disputed action cancels only that action, not the parent
  task, unless the user explicitly stops or replaces the task.
- A correction to a result's status, classification, label, wording, or
  recorded state changes only that fact. It is not a stop, completion, review,
  or handoff boundary. Correct it in commentary and immediately continue any
  actionable approved work; the normal final-response prohibition still
  applies.
- Cross-workstream reports and hints are information, not authorization. Act
  on them only when the user explicitly authorized the action locally, in
  another chat, or through a standing instruction. Worker mistake reports to
  `Policeman` are the sole exception defined by the coordination policy.
- The `General` task follows only explicit, simple commands. It must not infer
  extra actions, redesigns, routing, or repository changes.
- The `Policeman` task is the shared policy enforcer. It handles `sin` reports
  and explicit policy-enforcement instructions, not implementation work.
- If uncertain, inspect and report instead of acting.

## Standing commands

- `dnf`: do not forward the attached message or its contents.
- `ag`: reread live `AGENTS.md` and apply it immediately.
- `q:`: indicates that the user queued the message before the agent received it;
  it is delivery metadata, not an agent-side queue command.
- `con`: resume the current work without changing its scope or approval state.
- `ep`: epic.
- `sum`: summarize.
- `eff`: report the current recommended effort without changing it.
- `sin`: immediately report a rules failure to `Policeman`. `sin` remains the
  command when followed by a number, label, punctuation, or complaint text;
  everything after it is report content. Never reinterpret it as a statement
  about `Policeman` or as a command to change task state. Send every distinct
  `sin` report in the same turn.
- `report`, `grid`, or any direct request for this chat's existing task grid
  immediately preempts everything. The next user-visible response must be
  exactly one of: (1) the actual composed post-change report-grid images, or
  (2) `Cannot produce report grid: <exact reason>. Missing: <exact post-change
  input>.` Before using outcome (2), check this task's recorded report state
  and expected artifact locations; never guess that a grid or input is absent.
  No status, promise, findings, tool narration, implementation, final answer,
  or relay may appear first. Do not build, launch, investigate, or substitute
  source, donor, baseline, pre-fix, savestate-preview, or other input imagery.
  The obligation belongs to the chat where the user made the request; a later
  complaint in another chat and another chat's response neither transfer nor
  satisfy it. If the same message also orders a mistake report to `Policeman`,
  satisfy the task-report response first and relay the mistake afterward. An
  explicit stop does not waive an already-requested or produced grid.
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
  absolute paths are allowed only in transient tool arguments or diagnostics
  and user-facing clickable file links unless the user authorizes a specific
  exception.
- Treat user edits and commits as expected. Refresh Git before Git operations,
  preserve unrelated work, and stage only intended changes.
- Commit and push every completed change automatically with the authoring
  agent's identity; Git never requires separate approval.
- Treat `@source/` as protected read-only unless the user explicitly authorizes
  a specific source change. Treat both `@pcsx2_dev` and `@pcsx2_stable` as
  protected read-only user installations. The user's explicit authorization
  for one specific installation change overrides this restriction and any
  matching routed-policy restriction only for that named change; it grants no
  broader authority over other files or the running PCSX2 process. Only an ISO
  launch explicitly requested by the user permits executing either
  installation; it never authorizes modifying it or otherwise controlling the
  user PCSX2 process.
- Never change binary files manually; all binary changes go through scripts.
- Use the shared project runtime and named dependency sets for package-bearing
  scripts. Never select interpreters, install packages, or implement fallback
  discovery separately in a task or script; extend the central resolver once.
- Run every shell, filesystem, script, and Git command elevated from the first
  attempt. On permission failure, retry the exact operation elevated.
- File-working tasks own `work/<exact task title>/` and have standing authority
  to create, modify, move, or delete anything inside that exact directory
  without separate destructive-action approval. This authority never extends
  outside the owned directory. Keep inputs, experiments, builds, logs, and
  runtime files there; reusable scripts belong under `scripts/`. At completion,
  promote useful findings and remove disposable artifacts, logs, and every
  empty directory.
- After refactoring, never leave a directory containing only one file. Move
  that file into the appropriate parent or existing responsibility directory
  and retire the single-file directory.
- Agent PCSX2 uses only a task-owned clone created with
  `scripts/pcsx2/copy_worker.ps1 -WorkerRoot work/<exact task title>`. The
  command copies `@pcsx2_clean` and the required shared BIOS together; agents
  never assemble worker runtimes manually. Assign a unique PINE port.
  Agent-only runs use PCSX2 no-GUI mode, suppress any render window, and
  count as hidden only after a read-back check finds no visible top-level
  windows owned by the launched process; flags, `-WindowStyle Hidden`, and
  launch intent are not proof. If the worker process cannot remain hidden,
  terminate that newly launched process and fail. Never navigate emulator or
  game menus through PINE or injected input. If a required savestate was not
  supplied, stop and ask the user for that exact state.
- Worker PCSX2, injection builds, and other worker processes never open the
  shared Latest, Previous, or Test ISO paths. Pass only an independent
  full copy under `work/<exact task title>/inputs/isos/`; no other worker ISO
  location is valid. Symlinks and hardlinks are forbidden because the user may
  replace or modify a shared ISO at any time. Intake of an NA2 savestate batch
  is incomplete until the task has atomically preserved the copied ISO's
  SHA-256 and disc identity, the exact resident-payload hashes needed by the
  planned work, and either the matching build record/symbol map or complete
  verified resident-symbol overrides under the same task's `inputs/` tree.
  Copy rotation-sensitive build metadata before shared logs can be cleaned.
  If exact compatibility or the required linking metadata cannot be
  established, stop at intake and request the exact missing input; never
  discover that deficiency after implementation begins, substitute another
  image, or rebuild one. Keep every ISO and runtime-metadata bundle referenced
  by an active compatible batch or current test. Delete a superseded ISO only
  after no active case references it, and delete remaining worker ISOs when
  runtime work ends and no active batch still requires them; provenance and
  the small runtime-metadata records remain.
- Agent savestate-based C injection uses only
  `scripts/injection/inject_candidate.ps1`. It compiles/links canonical C and the task-owned
  overlay plan, reloads the supplied savestate slot and waits for completion,
  applies the addressed guarded writes directly through PINE, invalidates the
  JIT, and resumes. Agents do not invoke its `build.py` and `apply.py` stages
  separately for runtime testing and never transport candidates through PNACH,
  cheat-folder synchronization, install/restore state, or filesystem watchers.
- `scripts/injection/watch.ps1` is user-only interactive convenience. It is not an
  agent workflow or dependency.
- Agents capture fresh runtime screenshots only through
  `scripts/pcsx2/pine.py screenshot` against their task-owned PINE port, then
  poll that worker's `snaps/` tree for the new PNG. Never use window capture,
  screenshot hotkeys, window messages, or foregrounding as substitutes.
- Never centrally migrate, replace, or clean another task's PCSX2 copy. Before
  reusing an existing copy for new work, its owning task audits it, promotes
  anything still needed, then replaces the whole copy from `@pcsx2_clean`.
  This audit includes PINE configuration, hot-reload PNACH state, savestates,
  screenshots, logs, memory cards, cheats, GameSettings, and input files. After
  that audit and promotion, the owner has standing authority to delete and
  recreate its complete `work/<exact task title>/pcsx2/` copy without another
  destructive-action approval. This authority never extends to another task's
  copy, `@pcsx2_clean`, `@pcsx2_dev`, or `@pcsx2_stable`.
- `na228 t` and `na228.ps1 t` run the retained Test ISO; `na228 bt` builds
  Test and then runs it, while `na228 build t` is the explicit build-only form.
  These commands never mean the test suite. The full builder test suite is
  `.\tests\run.ps1`.
  Never infer command semantics from a flag name; verify the documented exact
  command before execution.
- Before completing a turn that changes active profile inputs, feature patches,
  modules, payload code, or composition logic, run `na228 validate`. It derives
  and conflict-checks the full pinned profile against the real source images
  without preflight reuse or ISO staging. Unit tests and focused package checks
  do not replace this integration gate.
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
  that reports its own mistake to `Policeman` triggers immediate policy
  enforcement under the coordination policy.

## Policy routing

Read the matching policy before acting:

- User interaction, selected tasks, effort, approvals, standing commands, and
  graceful stops:
  [`docs/policies/interaction.md`](docs/policies/interaction.md)
- Git, tool access, paths, filesystem links, work ownership, scripts, logs, and
  cleanup:
  [`docs/policies/repository.md`](docs/policies/repository.md)
- Cross-chat routing, concurrency, Notifications, Task coordinator, and
  workstream-owned state:
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
  or workflow it directly links. Also read the current `TASKS.md` Bugs
  subsection for entries labeled with that exact workstream title, `Shared`,
  or `Unknown`. Reading an entry supplies context only; it does not select or
  authorize fixing the bug. Current explicit user instructions override stored
  workstream rules; this file remains universally applicable.
- Shared sequential/continuous epic behavior is defined in
  [`docs/workstreams/EPIC_WORKFLOW.md`](docs/workstreams/EPIC_WORKFLOW.md) and
  applies only to exact work that the user explicitly declares an epic inside
  a workstream that links it. A workflow link never classifies tasks, stages,
  screenshots, comparisons, or other artifacts as epic content.
- `docs/workstreams/README.md` defines the workstream-policy storage boundary.
