# Repository and workspace policy

## Paths and repository boundaries

- Canonical path ownership, configured-root syntax, maintained loaders, and
  migration validation are defined in [`paths.md`](paths.md).
- For a requested `from <source> to <destination>` link, preserve the source and
  create the link at the destination. Do not redesign ownership unless asked.
- Treat `@pcsx2_dev` and the PCSX2 fork worker template as
  protected. Runtime-specific handling is in
  [`../runbooks/runtime-testing.md`](../runbooks/runtime-testing.md).

## Git and concurrent work

- Treat `e2e/captures/` as a separate maintained Git repository for every
  repository-wide Git operation, including identity configuration, status
  checks, commits, and completion reporting, even though it is local-only and
  has no remote.
- Refresh Git status and history before operations.
- If the user requests further changes to a task whose changes are staged,
  unstage only that task's changes before editing.
- Do not commit incomplete work merely to clean the working tree. Report its
  task-owned dirty state.
- When a remote exists, immediately push each task-owned commit unless it
  belongs to a coherent multi-repository delivery. For such a delivery, create
  every intended commit before pushing any repository; if any commit fails,
  push none. Once all commits exist, push every remote-backed participating
  repository without unrelated intervening work. If a push fails partway,
  report the exact partial delivery; do not rewrite or roll back published
  history automatically. Report every participating repository's commit, push,
  and dirty state.
  Normal pushes to the configured current branch/origin have standing
  authorization; do not ask for it again. Changing remotes, force-pushing, or
  rewriting published history
  still requires explicit instruction.
- Never modify persistent Git identity configuration. The shared Git policy
  guard owns per-command identity and subject validation.
- Git history is the recovery mechanism for tracked files. Preserve
  irreplaceable untracked inputs deliberately before deleting them.

## Work ownership and external inputs

- `work/<exact chat title>/` is exclusively the workspace of that chat. Only
  that chat may create, change, move, or delete content there. Another chat may
  read it but copies anything it needs into its own tree before changing it.
  Project-wide, release, build, test, script, and other non-chat workflows use
  their own configured roots outside every chat directory. Generic skill
  workspace conventions do not override this rule; remap paths such as
  `tmp/pdfs/` into the acting chat's directory.
- Agents do not use the operating-system `TEMP`/`TMP` directory as a workspace
  or artifact root. Set `NA228_TASK_WORK_ROOT` to the acting chat's
  `work/<exact chat title>/` before maintained commands that create temporary
  files.
- When `NA228_TASK_WORK_ROOT` is unset, the unit-test runner uses the ignored
  `work/temp/tests/` technical root instead of impersonating a chat.
- Reserve top-level `work/temp/` for unit-test scratch. Keep inputs,
  experiments, intermediates, outputs, builds, runtime artifacts, and logs in
  clearly named subdirectories outside that technical root.
- Copy changing external inputs such as selected savestates or screenshots into
  `work/<chat title>/inputs/` with provenance before relying on them. Keep baselines,
  modified copies, analysis outputs, and builds separate.
- After moving or deleting files, inspect every affected parent directory on
  disk with hidden and ignored entries included. Remove unintended empty
  parents and inspect them again; the task remains incomplete until this is
  done. Git status cannot prove directory cleanup.
- `docs/designs/` is exclusively owned by Design mode. Do not create or modify
  files there in any other mode.
- Do not create or preserve a directory containing only one file unless it has a
  clear structural, ownership, namespace, tooling, or future-extension purpose.
  Otherwise move the file to the nearest appropriate existing directory and
  remove the unnecessary folder.
- Before completion, apply the applicable
  [logging](logging.md#retention) and [research](research.md) retention rules,
  remove other disposable task artifacts, and document every retained artifact
  and its future use.

## Scripts, dependencies, and logs

- User-facing utilities are PowerShell. Python may be used internally behind a
  maintained PowerShell entrypoint.
- Keep root `na228.ps1` a short parser/router; substantive implementation belongs
  under `scripts/` by responsibility. Shared PCSX2, media, and Ghidra tooling
  belongs in Workshop.
- Domain-specific scripts remain with their owning area until they become
  shared project infrastructure.
- When a task changes the shared PowerShell profile, locate it through
  `$env:USERPROFILE`; keep the profile change to a thin alias or dot-source and
  keep reusable implementation in the project `scripts/` tree.
- Optional reusable analysis/research tools belong in an existing tooling area;
  task-local scratch tools remain under the task and are deleted when no longer
  useful. See the implementation boundary in root
  [`AGENTS.md`](../../AGENTS.md#implementation-boundaries).
- Third-party packages use the affected component's existing central dependency
  set and runtime resolver. Do not select interpreters, install packages, or add
  fallback discovery independently in a task or script.
- On Windows, never invoke a `.py` file as a command, including PowerShell
  `& path.py`; that can trigger the OS file-association dialog. Pass the file to
  the maintained Python wrapper or an explicitly resolved compatible
  interpreter.
- User-facing repeated operations must accept state produced by their own prior
  successful run. Do not add workflow-blocking identity, expected-state, guard,
  backup, recovery, or restart validation unless it is explicitly authorized by
  the applicable validation plan.
- Follow [`logging.md`](logging.md) for log roots, retention, and
  knowledge promotion.
- Prefer cohesive responsibility-based files. Split independent concerns when
  it improves ownership, navigation, testing, or concurrency, not merely by
  size.
- Treat `@tools/old/` as untrusted historical material; inspect a chosen tool
  before execution. Deliberately retained shared tools under `@tools/` are not
  task-temporary artifacts.

## Documentation layout

Give each document one job and canonical authority:

- interaction documents under `docs/interactions/` own interaction modes;
- workflow documents under `docs/workflows/` own multi-step task workflows;
- procedure documents under `docs/procedures/` own non-mode agent procedures;
- runbooks own exact operational procedures;
- the implementing repository or component owns user-facing CLI help;
- component docs own current architecture, contracts, inputs, and outputs;
  never duplicate canonical source as a documentation example;
- knowledge/research docs own evidence, findings, hypotheses, and negative
  results;
- historical docs contain only non-current material with concrete continuing
  value.

Substantial supporting documentation belongs under the repository root `docs/`
hierarchy.
- A code area may retain one concise local `README.md` when nearby orientation
  or a component contract is useful. Link to substantial documentation instead
  of accumulating multiple Markdown files beside code.
- The builder has no physical `features/` directory. Selectable structure lives
  in `na228_builder/catalog/catalog.modcat`; guarded edits, runtime injection
  units, and targets live beside it under `na228_builder/catalog/`. Non-inline
  executable inputs and
  assets live under their concrete builder data area, and feature documentation
  belongs under `docs/features/`. Catalog-only features require no directory.
- Current operational documentation describes the current system. Delete
  superseded policy, stale incident explanations, and obsolete retirement notes
  when they no longer provide concrete current value; Git preserves history.
