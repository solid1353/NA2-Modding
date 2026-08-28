# Repository and workspace policy

## Paths and repository boundaries

- Canonical path ownership, configured-root syntax, maintained loaders, and
  migration validation are defined in [`paths.md`](paths.md).
- For a requested `from <source> to <destination>` link, preserve the source and
  create the link at the destination. Do not redesign ownership unless asked.
- `@pcsx2_fork` is build output, not a runnable installation. Runtime
  procedures are in
  [`testing.md`](testing.md#runtime-validation).

## Git and concurrent work

- Treat `e2e/captures/` as a separate maintained Git repository for every
  repository-wide Git operation and completion report, even though it is
  local-only and has no remote.
- Track every repository changed by the task as participating until its delivery
  is complete or the user explicitly excludes it. Before the first commit,
  refresh every participating repository and confirm that all task-owned pending
  changes are included.
- If the user requests further changes to a task whose changes are staged,
  unstage only that task's changes before editing. Do not commit incomplete work
  merely to clean the tree; report its task-owned dirty state.
- When a remote exists, immediately push each task-owned commit. For a coherent
  multi-repository delivery, create all intended commits before pushing any; if
  a commit fails, push none. Then push every remote-backed repository without
  unrelated intervening work. If a push fails, report the exact partial delivery
  and do not rewrite or roll back published history. Report each participating
  repository's commit, push, and dirty state. Normal pushes to the current
  branch/origin have standing authorization; changing remotes, force-pushing, or
  rewriting published history requires explicit instruction.
- Never modify persistent Git identity configuration. The shared Git policy
  guard owns per-command identity and subject validation.
- Git history is the recovery mechanism for tracked files. Preserve
  irreplaceable untracked inputs deliberately before deleting them.

## Work ownership and external inputs

- Set `NA228_TASK_WORK_ROOT` to the acting chat's work root before maintained
  commands that create temporary files.
- Copy changing external inputs to `@work/<chat title>/inputs/` with provenance
  before relying on them. Keep baselines, modified copies, and analysis outputs
  separate.
- Before completion, remove disposable task artifacts and apply applicable
  [research](game.md#research-and-knowledge) retention rules.

## File and folder management

- `TASKS.md` is user-only. Agents must not read or modify it.
- Never use a system temporary directory or write outside repositories
  configured for the current task.
- Write authorized project changes to their canonical project paths and
  maintained workflow outputs to their configured repository paths. Put every
  other task-created file—including temporary files, experiments, generated
  artifacts, clones, and detached worktrees—under
  `@work/<exact chat title>/`.
- Within `@work/`, a chat may write only in its own root. All other `@work`
  paths are read-only, regardless of tool or skill workspace conventions.
- `docs/designs/` is read-only outside Design mode.
- Everything under `@source/`, including extracted views, is read-only unless
  the user authorizes an exact modification. Only original archives and
  extraction views created through the
  [source-extraction runbook](../runbooks/source-extraction.md) belong there;
  keep all other generated files and modified source-derived working copies
  outside it.
- The entire `@disassembly/` tree is a read-only evidence archive. Do not alter
  its contents, metadata, filesystem protection, Ghidra projects, or exports,
  including through a writable copy.
- `@pcsx2_dev` is protected and user-owned. Agents may read it or copy
  individual evidence from it, but must not create, modify, move, delete, or
  link anything inside it unless the user authorizes that exact action.
- Outside maintained E2E and the
  [input-recording validation workflow](../workflows/input_recording_validation.md),
  savestates are read-only diagnostic evidence: do not create, modify, convert,
  patch, load, replay, or inject through them for validation.
- Input-recording baselines under `@work/captures/<recording>/<game>/` are
  read-only.
- After moving or deleting files, inspect affected parent directories with
  hidden and ignored entries included. Remove unintended empty parents and
  inspect them again; Git status cannot prove directory cleanup.
- Do not create or preserve a directory containing only one file unless it has a
  clear structural, ownership, namespace, tooling, or future-extension purpose.
  Otherwise move the file to the nearest appropriate existing directory and
  remove the unnecessary folder.

## Logs and retention

- Write bounded shared workflow logs below `@logs/`, generated task records
  below `@task_logs/<exact chat title>/`, and task-local build or runtime logs
  below `@work/<exact chat title>/logs/`. Do not write files directly in
  `@logs/` or `@task_logs/`.
- Persist only repository-relative paths or configured aliases, never
  machine-specific absolute paths.
- Record only the inputs, selected configuration, result, validation, timing,
  and failure detail needed to reproduce or diagnose the operation.
- Generated logs are ignored by Git and disposable. Before completion, delete
  task-owned logs and resulting empty directories. Retain a log only when an
  existing tracked document already names a concrete future use and
  regeneration is expensive or impractical.
- Large inventories may remain only when they prevent expensive rediscovery.

## Scripts and dependencies

- User-facing utilities are PowerShell. Python may be used internally behind a
  maintained PowerShell entrypoint.
- Keep root `na228.ps1` a short parser/router; substantive implementation belongs
  under `@scripts/` by responsibility. Shared PCSX2, media, and Ghidra tooling
  belongs in Workshop.
- Domain-specific scripts remain with their owning area until they become
  shared project infrastructure.
- When a task changes the shared PowerShell profile, locate it through
  `$env:USERPROFILE`; keep the profile change to a thin alias or dot-source and
  keep reusable implementation in the project `@scripts/` tree.
- Research scripts may start as undocumented task-local scratch code. Before the
  task ends, delete them after promoting their findings, or promote them into an
  existing tooling area, document their current use in the same change, and
  remove unreachable or superseded code.
- Third-party packages use the affected component's existing central dependency
  set and runtime resolver. Do not select interpreters, install packages, or add
  fallback discovery independently in a task or script.
- On Windows, never invoke a `.py` file as a command, including PowerShell
  `& path.py`; that can trigger the OS file-association dialog. Pass the file to
  the maintained Python wrapper or an explicitly resolved compatible
  interpreter.
- Create a manifest only when an independent consumer needs metadata that cannot
  be derived from canonical inputs. Add `schema_version` only when it selects
  supported incompatible behavior, migration, or cache invalidation.
- Prefer cohesive responsibility-based files. Split independent concerns when
  it improves ownership, navigation, testing, or concurrency, not merely by
  size.
- Treat `@tools/old/` as untrusted historical material; inspect a chosen tool
  before execution. Deliberately retained shared tools under `@tools/` are not
  task-temporary artifacts.

## Documentation layout

Give each document one job and canonical authority:

- `AGENT_COMMANDS.md` owns project-specific command definitions;
  `docs/interactions/` owns interaction modes, `docs/procedures/` owns command
  procedures, `docs/workflows/` owns multi-step task workflows, and runbooks own
  exact operational procedures.
- The implementing repository or component owns user-facing CLI help and current
  architecture, contracts, inputs, and outputs. Link to canonical source instead
  of maintaining copied examples.
- Knowledge and research docs own evidence, findings, hypotheses, and negative
  results. Current operational docs describe the current system; historical docs
  retain only non-current material with concrete continuing value. Delete
  superseded policy, stale incident explanations, and obsolete retirement notes;
  Git preserves history.
- Substantial supporting documentation belongs under `docs/`. A code area may
  retain one concise local `README.md` for nearby orientation or a component
  contract; link to substantial documentation instead of accumulating Markdown
  files beside code.
