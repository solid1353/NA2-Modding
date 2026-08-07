# Repository and workspace policy

**Applies when:** changing files, paths, Git state, scripts, dependencies, logs,
work directories, or documentation layout.

## Paths and repository boundaries

- Canonical project files, scripts, configuration, logs, metadata, and generated
  artifacts use repository-relative paths or configured `@root/...` references.
  Machine-specific absolute paths are limited to transient tool arguments,
  diagnostics, and user-facing clickable links unless explicitly authorized.
- Workshop root `paths.json` owns shared roots and named files. Workshop
  `games.json` owns source-game identity. NA2 root `paths.json` imports Workshop
  and adds NA2-local paths; `product.json` owns NA2 inputs, output identity,
  build roles, and aliases. Use the maintained loaders rather than duplicating
  derivation logic.
- When moving a configured root or direct manifest file, update its canonical
  owner and every affected reference, then validate the existing loaders.
- For a requested `from <source> to <destination>` link, preserve the source and
  create the link at the destination. Do not redesign ownership unless asked.
- Treat `@source/`, `@pcsx2_dev`, `@pcsx2_stable`, and the clean PCSX2 worker
  template as protected. Runtime-specific handling is in
  [`../runbooks/runtime-testing.md`](../runbooks/runtime-testing.md).

## Git and concurrent work

- User edits and commits are expected. Refresh status/history before Git
  operations, preserve unrelated work, and stage only task-owned paths or hunks.
- Independent changes may proceed concurrently. Pause only for overlapping or
  logically conflicting changes or exclusive mutable resources.
- Completed refactors and other completed non-patch changes are committed after
  their selected validation, then pushed automatically. Game/runtime patches
  follow the proof and commit boundary in [`testing.md`](testing.md).
- Ordinary pauses, questions, reviews, and requests for user input do not require
  a clean working tree. If work is blocked or incomplete, do not create a WIP
  commit merely to clean the tree; report the exact task-owned dirty state.
  `zxc` is the explicit recoverable graceful-stop exception.
- Every created task-owned commit is pushed automatically. Normal pushes to the
  configured current branch/origin have standing authorization; do not ask for
  it again. Changing remotes, force-pushing, or rewriting published history
  still requires explicit instruction.
- A coherent delivery spanning maintained repositories has one completion
  boundary: create every intended commit before pushing any participating
  repository, then report each repository's commit, push, and dirty state.
- Use the matching identity from `@workshop/settings/git-authors.tsv`, or
  `<agent-name>@agent.invalid` when it has no entry. Do not use the user's
  personal identity. Use the concise task-authored subject
  `[<workstream/category>] <imperative summary>`, with the owning workstream or
  category as the prefix. When no meaningful owner or category applies, use
  `[Other] <imperative summary>`. Do not use the full task title or invent
  another prefix taxonomy. Verify the subject before pushing.
- Git history is the recovery mechanism for tracked files. Preserve
  irreplaceable untracked inputs deliberately before deleting them.

## Access and elevation

- Run every shell, filesystem, script, and Git operation elevated from the first
  attempt.
- If an elevated operation still fails, report the exact failure. Do not switch
  tools, paths, destinations, workspaces, or methods and do not invent a helper
  workflow to bypass the access problem.
- Retry only the failed operation; do not repeat work that already succeeded.

## Work ownership and external inputs

- A file-working task owns `work/<exact task title>/` and may manage that tree
  without separate destructive-action approval. It may read another task's tree
  but copies anything it needs into its own tree before changing it.
- Agents do not use the operating-system `TEMP`/`TMP` directory as a workspace
  or artifact root. Set `NA228_TASK_WORK_ROOT` to the acting task's
  `work/<exact task title>/` before maintained commands that create temporary
  files.
- The permanent-test runner uses `work/General/` as its technical default when
  `NA228_TASK_WORK_ROOT` is unset. This path has no special chat-role meaning.
- Keep inputs, experiments, intermediates, outputs, builds, runtime artifacts,
  and logs in clearly named subdirectories. Do not use top-level `work/temp/`.
- Copy changing external inputs such as selected savestates or screenshots into
  `work/<task>/inputs/` with provenance before relying on them. Keep baselines,
  modified copies, analysis outputs, and builds separate.
- After moving or deleting files, enumerate every affected parent directory on
  disk with hidden and ignored entries included. Remove an unintended empty
  parent, then inspect it again. Do not report cleanup or completion from Git
  status alone because Git does not represent empty directories.
- A task that moves or deletes files is incomplete until its affected parent
  directories have been inspected on disk and every unintended empty directory
  has been removed.
- Do not create or preserve a directory containing only one file unless it has a
  clear structural, ownership, namespace, tooling, or future-extension purpose.
  Otherwise move the file to the nearest appropriate existing directory and
  remove the unnecessary folder.
- Before completion, remove disposable task artifacts and promote reusable
  findings or tools to their canonical owner. Document every intentionally
  retained task artifact and its future use.

## Scripts, dependencies, and logs

- User-facing utilities are PowerShell. Python may be used internally behind a
  maintained PowerShell entrypoint.
- Keep root `na228.ps1` a short parser/router; substantive implementation belongs
  under `scripts/` by responsibility. Shared PCSX2, media, and Ghidra tooling
  belongs in Workshop.
- When a task changes the shared PowerShell profile, locate it through
  `$env:USERPROFILE`; keep the profile change to a thin alias or dot-source and
  keep reusable implementation in the project `scripts/` tree.
- Optional reusable analysis/research tools belong in an existing tooling area;
  task-local scratch tools remain under the task and are deleted when no longer
  useful. See the implementation boundary in [`interaction.md`](interaction.md).
- Third-party packages use the affected component's existing central dependency
  set and runtime resolver. Do not select interpreters, install packages, or add
  fallback discovery independently in a task or script.
- On Windows, do not execute a `.py` path directly through the shell. Use the
  maintained Python wrapper or an explicitly resolved compatible interpreter.
- User-facing repeated operations must accept state produced by their own prior
  successful run. Do not add workflow-blocking identity, expected-state, guard,
  backup, recovery, or restart validation unless it is explicitly authorized by
  the applicable validation plan.
- Write logs only to the configured purpose-specific log/work roots. Promote
  reusable findings before deleting disposable logs; follow
  [`../LOGGING.md`](../LOGGING.md).
- Prefer cohesive responsibility-based files. Split independent concerns when
  it improves ownership, navigation, testing, or concurrency, not merely by
  size.
- Treat `@tools/old/` as untrusted historical material; inspect a chosen tool
  before execution. Deliberately retained shared tools under `@tools/` are not
  task-temporary artifacts.

## Documentation layout

Give each document one job and canonical authority:

- root `AGENTS.md` owns universal rules and scoped-document routing;
- routed policies own scoped normative rules;
- runbooks own exact operational procedures;
- `docs/AGENT_COMMANDS.md` owns commands interpreted by agents;
- the implementing repository or component owns user-facing CLI help;
- component docs own current architecture, contracts, inputs, and outputs;
- knowledge/research docs own evidence, findings, hypotheses, and negative
  results;
- historical docs contain only non-current material with concrete continuing
  value.

Link to the canonical owner instead of copying its content. Substantial
supporting documentation belongs under the repository root `docs/` hierarchy.
- A code area may retain one concise local `README.md` when nearby orientation
  or a component contract is useful. Link to substantial documentation instead
  of accumulating multiple Markdown files beside code.
- The builder currently requires one root `README.md` in each feature for
  structural discovery. That requirement does not make the file the mandatory
  home for all feature/module documentation.
- Current operational documentation describes the current system. Delete
  superseded policy, stale incident explanations, and obsolete retirement notes
  when they no longer provide concrete current value; Git preserves history.
