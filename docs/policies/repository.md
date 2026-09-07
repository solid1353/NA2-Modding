# Repository and workspace policy

## Paths and repository boundaries

- Workshop owns shared path configuration and source-game identities. NA2
  imports that configuration and defines only project-specific paths and
  settings.
- Workshop must not depend on NA2. NA2 may override an imported entry only by
  defining the same name in its own manifest.
- Persist only repository-relative paths or configured aliases, never
  machine-specific absolute paths.
- Resolve each manifest relative to its own directory, never the caller's
  working directory.
- Loaders inject `repository`; manifests do not define it.
- Define parent roots before entries derived from them and keep related entries
  together.
- `existence_deferred_roots` contains only generated roots that may be absent
  while loading the manifest.
- Runtime consumers resolve configured paths through a maintained loader; do
  not hard-code their backing paths.
- Each registered game's alias-owned PCSX2 bundle must exist in exactly one
  configured `pcsx2_files` root.
- For a requested `from <source> to <destination>` link, preserve the source and
  create the link at the destination. Do not redesign ownership unless asked.
- `@pcsx2_fork` is build output, not a runnable installation. Runtime
  procedures are in
  [runtime validation](modding.md#runtime-validation).

## Git and concurrent work

- After successful validation of task-owned PCSX2 repository changes,
  automatically stage, commit, push, and deploy the validated build to
  `@pcsx2_dev`. This standing authorization applies only to PCSX2 repository
  changes.
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
- When a remote exists, immediately push each task-owned commit.
- Never modify persistent Git identity configuration. The shared Git policy
  guard owns per-command identity and subject validation.
- Git history is the recovery mechanism for tracked files. Preserve
  irreplaceable untracked inputs deliberately before deleting them.

## File and folder management

- Before using a task work root, resolve the current exact chat title from
  Codex. Use only `@work/<exact chat title>/`. Treat every other `@work` path
  as read-only except for input moves required by this policy.
  Set `NA228_TASK_WORK_ROOT` to the task root before maintained
  commands create temporary files.
- Never use a system temporary directory or write outside repositories
  configured for the current task.
- Write authorized project changes to their canonical project paths and
  maintained workflow outputs to their configured repository paths.
- Write task-owned generated records below `@work/<exact chat title>/logs/`.
- Copy changing external inputs to `@work/<exact chat title>/inputs/` before relying on them.
- New savestates are stored in Workshop's `@pcsx2_savestates/`.
  Before inspecting a savestate supplied for the task, move it to
  `@work/<exact chat title>/inputs/` instead of copying it.
- Before inspecting an input-recording baseline, move it from
  `@work/captures/<recording>/<game>/` to
  `@work/<exact chat title>/inputs/captures/<recording>/<game>/`.
  Treat its contents as read-only.
- Before completion, remove disposable task artifacts.
- `TASKS.md` is user-only. Agents must not read or modify it.
- Never create or use an additional Git worktree.
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
- Savestates are read-only diagnostic evidence: do not modify them
  or use them for validation.
- Before deleting anything, preserve any useful information it contains in the
  appropriate project file.
- After moving or deleting files, inspect affected parent directories with
  hidden and ignored entries included. Remove unintended empty parents and
  inspect them again; Git status cannot prove directory cleanup.
- Do not create or preserve a directory containing only one file unless it has a
  clear structural, ownership, namespace, tooling, or future-extension purpose.
  Otherwise move the file to the nearest appropriate existing directory and
  remove the unnecessary folder.

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

Give each document one job and canonical authority. Every paragraph must add
useful information owned by that document; remove it otherwise.

- `AGENT_COMMANDS.md` owns project-specific command definitions;
  `docs/interactions/` owns interaction modes, `docs/procedures/` owns command
  procedures, `docs/workflows/` owns multi-step task workflows, and runbooks own
  exact operational procedures.
- Feature docs own all information about this mod or any other mod, including
  reference behavior, configuration, and implementation.
- Knowledge docs contain only facts and research about unmodified retail games.
  They must not describe any mod and must remain valid if the project mod is
  removed or redesigned.
- Link between feature and knowledge docs instead of copying content. If a
  document contains both kinds of information, move each part to the document
  where it belongs and preserve all useful evidence.
- Current operational docs describe the current system; historical docs retain
  only non-current material with concrete continuing value. Delete superseded
  policy, stale incident explanations, and obsolete retirement notes; Git
  preserves history.
- Substantial supporting documentation belongs under `docs/`. A local
  `README.md` must own a local contract that cannot be inferred from the
  directory or found in canonical documentation.
- Before completing a documentation change, review each affected document as a
  whole and remove anything that violates this section.
