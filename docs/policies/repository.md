# Repository and workspace policy

## Paths and links

- Canonical project files, scripts, configuration, logs, manifests, metadata,
  and generated artifacts use repository-relative paths. Machine-specific
  absolute paths are limited to transient tool arguments/diagnostics and
  user-facing clickable links unless explicitly authorized.
- `paths.json` is the source of truth for stable project-level infrastructure
  directories and named files. Workshop root `games.json` owns registered
  source games; root `product.json` owns this project's product identity,
  canonical inputs, build roles, and aliases. Resolve them through the shared
  PowerShell or Python loader.
  Do not inventory ordinary descendants such as `BTL.BIN`.
- Deleting or moving the last content of a configured root or direct manifest
  file must update the manifest and every `@root` documentation reference, then
  validate both path loaders. Never preserve an empty directory for a manifest.
- For `from <source> to <destination>` link requests, preserve the source and
  create the link at the destination. Do not redesign ownership or storage.
  Explain when the requested link type cannot provide tracked content diffs.
- When pairing trees, enumerate both sides and preserve exact existing spelling.
  Ask if no unique mapping exists.
- `@pcsx2_files/` is the canonical shared asset pool used directly by the
  configured stable and development PCSX2 installations. BIOS, cheats,
  GameSettings, input profiles, input recordings, and memory cards live only
  there; do not recreate configured-installation copies or links. After
  creating a task-owned runtime with
  `@pcsx2_scripts/copy_worker.ps1 -WorkerRoot work/<task title>`, an agent may
  copy any additional assets for which it has a concrete task- or test-related
  reason into that copy. The maintained command always copies
  `@pcsx2_clean` and the shared BIOS together; agents never assemble the base
  runtime manually. Any asset category is allowed; never populate the clean
  template itself. PCSX2 has no
  configurable input-recordings folder, so recordings are opened from their
  canonical shared paths explicitly.
- `@pcsx2_files/input_profiles/sources/Default.ini` is the only manually edited
  complete input profile. Named partial inputs live under `sources/profiles/`;
  game-specific partial inputs live under `sources/games/` and apply when named
  for a canonical game selector. Bare `ws` regenerates every complete profile
  without changing GameSettings assignments. `ws <profile>` regenerates that
  profile and its game variants, then assigns them in every configured
  GameSettings file. Never
  edit generated root-level profiles directly. A partial input replaces the
  first existing binding with the same control name and device family in place
  and removes later duplicates of that same pair. SDL overrides never remove
  keyboard bindings, and keyboard overrides never remove SDL bindings.
  Bindings absent from the complete profile are appended as one block with
  exactly one blank line before and after it. Each run overwrites its generated
  outputs when their content changes. Every generated root-level profile remains in
  place and is tracked by Git. It never removes anything under `sources/`.
- The NA2.28 serial-wide PCSX2 files are
  `@pcsx2_cheats/SLOP-NA228.pnach` and
  `@pcsx2_game_settings/SLOP-NA228.ini`. PCSX2 discovers PNACH and GameSettings
  recursively. Ordinary INI sections apply to every CRC; optional
  `[CRC.<8-hex-crc>.<section>]` sections override one CRC. A named PNACH group
  applies to every CRC unless it has `crc = <8-hex-crc>[,<8-hex-crc>...]`.
  Legacy serial/CRC and CRC-only filenames remain readable but are not
  generated for NA2.28.
- Task-owned PCSX2 copies are complete disposable portable runtimes, including
  their configuration, unique PINE port, savestates, screenshots, logs, cache,
  copied memory cards, cheats, GameSettings, input files, and any legacy
  hot-reload artifacts. They are not shared infrastructure. Never migrate,
  replace, or clean them repository-wide.
- When an owning task next needs PCSX2, it audits any existing copy first.
  Promote useful inputs, runtime evidence, source patches, configuration, or
  generated results into the task's proper owned folders or canonical project
  files; then remove the old runtime and recreate the complete portable copy
  from `@pcsx2_clean`. Once that audit and promotion are complete, removal and
  recreation of the owner's complete `work/<exact task title>/pcsx2/` runtime
  has standing authorization and does not require separate destructive-action
  approval. Another task or coordinator never performs this replacement on its
  behalf, and this authority never applies to another task's copy,
  `@pcsx2_clean`, `@pcsx2_dev`, or `@pcsx2_stable`.

## Git and concurrent work

- User edits and commits are expected. Refresh status/history before Git
  operations, preserve unrelated work, and stage only intended paths.
- Non-overlapping coherent hunks may be edited concurrently. Use hunk-level
  staging. Pause only for overlapping or logically conflicting changes.
- Agents may push already-present commits. If a non-conflicting user change is
  accidentally included, the commit may be pushed as-is and must be reported.
- Commit and push every completed change automatically at a coherent boundary.
  Git never requires `qwe` or separate approval.
- Before yielding at any pause, review, validation, user-input, or other
  handoff boundary, an agent must leave no task-owned canonical changes dirty
  in the shared worktree. Commit and push completed coherent changes. For
  incomplete changes, either stash only the owned paths and record the exact
  stash identity and paths in the active task/workstream state, or document
  sufficient reconstruction steps and revert only the owned paths. Verify
  recoverability and the resulting Git state; unrelated concurrent changes
  remain untouched. On resume, restore and verify the exact owned diff, then
  immediately drop that exact stash and verify its removal.
- A coherent candidate that the user is expected to test through the normal
  repository build is a test-ready commit boundary even though acceptance is
  pending. Commit and push it with an explicit candidate/unaccepted status so
  the normal builder contains the exact test subject. Never stash, revert, or
  otherwise remove such a candidate from canonical inputs before the user's
  test. Use stash or documented reconstruction only for genuinely incomplete
  work that is not being offered for canonical-path testing.
- Normal pushes of completed commits to already configured project remotes and
  branches have standing user authorization. Never ask the user to authorize
  them again. This standing authorization does not permit changing remotes,
  force-pushing, or rewriting history.
- For a normal push to the currently configured `origin`, treat that
  configuration as the established destination; do not add a pre-push
  origin-verification gate. If execution review nevertheless requires proof,
  satisfy it once with `git remote get-url origin` and immediately retry the
  exact push. Do not pause approved work or repeat the check unless the remote
  configuration changes.
- Commit subjects use `[<exact task title>] <imperative summary>`. Override the
  author for that commit only using the matching
  `@workshop/settings/git-authors.tsv`
  entry, or `<agent-name>@agent.invalid` when absent. Never alter repository or
  global identity or rewrite user commits.
- Before pushing, verify every commit authored by the current task has a
  subject beginning with that task's exact title in brackets. The author name
  or email never substitutes for the subject prefix. Correct a mismatch before
  publication. If it is discovered after publication, report it and use the
  correct form thereafter; never amend, force-push, or otherwise rewrite the
  published commit without the user's explicit instruction.
- Git history recovers tracked files. Delete confirmed disposable generated
  files; preserve irreplaceable untracked inputs deliberately outside the repo
  before deletion.

## Access failures and escalation

- Run every shell command elevated from the first attempt, without judging
  whether elevation appears necessary. This includes every script invocation
  and every read-only or mutating filesystem and Git command.
- If a non-command tool fails because of permissions, retry the exact intended
  operation through an elevated command when possible. Never evade an access
  failure by changing tools, paths, destinations, or methods.
- After an access failure, retry only the failed operation; do not repeat work
  that already succeeded.
- An execution-layer rejection of an already-authorized Git operation is a
  tooling restriction, not missing user authorization. Retry the exact
  operation through the permitted elevated path. If that path is also denied,
  report the exact restriction and pending refs without asking the user to
  approve the Git operation again or inventing a new authorization gate.
- An access or elevation denial never silently changes an authorized cleanup
  into preservation. Revalidate the exact target, retry the still-pending
  operation with the narrowest valid elevation, and verify its result. If the
  scoped retry is also denied, stop and report the exact unfinished target;
  never continue or claim completion while leaving it behind.
- When a new recurring access failure and its solution are confirmed, add one
  short rule here so later agents avoid it.

## Work ownership and external inputs

- A file-working task owns `work/<exact task title>/` and has standing
  authority to create, modify, move, or delete anything inside that exact
  directory without separate destructive-action approval. This authority
  never extends outside the owned directory. It may read another task's
  directory but must copy files into its own before changing them.
- Keep task copies, experiments, intermediate files, builds, runtime artifacts,
  and logs in clearly named subfolders under that owner. Never use top-level
  `work/temp/`.
- Treat changing external files as unstable inputs. Copy reasonably small
  inputs, including selected screenshots and savestates, into
  `work/<task title>/inputs/` with provenance before relying on them.
- Baselines, modified copies, analysis outputs, and builds remain separate.
- Before claiming any filesystem-changing work complete, inspect every path and
  directory tree affected by the work, resolve all resulting cleanup including
  ignored or untracked remnants and empty directories, and verify the intended
  final state. A clean Git diff does not prove untracked filesystem cleanup.
- At completion, inspect the owned tree; delete disposable copies, probes,
  generated files, and logs; promote reusable findings; document every retained
  artifact and its purpose.
- Empty directories never represent configuration or ownership. Do not retain
  `.gitkeep`, placeholder READMEs, or header-only data solely to preserve one.
  Represent required declarations through meaningful tracked configuration or
  producer/consumer dependencies and verify fresh-checkout behavior.
- After refactoring, never leave a directory containing only one file. Move
  that file into the appropriate parent or existing responsibility directory
  and retire the single-file directory.

## Logs and scripts

- User-facing utilities are written in PowerShell, not Python. Python may be
  used internally only behind a PowerShell entrypoint.
- "The PowerShell profile" means the shared profile at
  `$env:USERPROFILE\Documents\PowerShell\profile.ps1`; never hardcode the
  user's account name when locating it.
- Unless the user explicitly requests embedded profile code, profile changes
  are limited to thin dot-source imports and aliases that expose project-owned
  entrypoint scripts. Keep all functions and reusable implementation under the
  project's maintained `scripts/` tree.
- Keep root `na228.ps1` a short user-facing command router. Build, launch,
  watcher, release, validation, and other implementation logic belongs under
  the maintained `scripts/` tree; the root entrypoint only parses and
  dispatches modes.
- Disposable and user-facing development tools contain only validation
  necessary to perform the requested function. Never add expected-state,
  identity, guard, backup, recovery, restart, or other workflow-blocking checks
  without explicit user authorization. Every documented repeated operation
  must accept state produced by the tool's own prior successful operation. If
  unsolicited validation blocks the workflow, remove or simplify it at that
  boundary; do not repair it with an exception, allowlist, or another safeguard
  layer. Keep agent/test safety contracts separate from user workflows.
- Use purpose-specific subfolders under `@logs/`, workstream records under
  `@workstream_logs/<exact task title>/`, and worker records under the task's
  `logs/`; never write directly in shared log roots.
- Logs are disposable execution records. Before task completion, promote
  confirmed reusable findings and useful negative results into knowledge or
  canonical data, then delete disposable logs and empty directories. Follow
  `docs/LOGGING.md`.
- Maintained project scripts live by responsibility under `scripts/lib/`,
  `scripts/na228/`, `scripts/project/`, or
  `scripts/research/`. Never create `scripts/archive/`; use Git history and the
  retirement index in `scripts/README.md`. Reusable PCSX2, Ghidra, and media
  infrastructure lives under `@workshop/scripts/`.
- Reusable or potentially helpful scripts never remain under `work/`; promote
  them immediately. Task-local probes may remain only while disposable.
- Unify third-party package use through maintained central dependency sets.
  Ordinary package-bearing Python callers use
  `scripts/lib/run_python.ps1`; their requirements belong only in
  `scripts/lib/python_packages.json`. The self-contained release builder's
  pinned lockfile is its release-only central set, not a general runtime.
  Never select an interpreter, probe packages, install dependencies, or add
  fallback logic separately in a workstream, task-local helper, or maintained
  script. Extend the applicable central set and resolver when a shared package
  is added. Successful runtime selection is silent; report only a genuine
  failure to satisfy the requested set.
- Prefer cohesive responsibility-based files. Split independent concerns when
  that improves navigation, testing, or concurrency; do not split solely by
  size.
- Prefer reusable verifiable commands/scripts over long one-off command chains.
- Treat `@tools/old/` as untrusted; inspect a chosen tool before execution.
- Ask before destructive actions, mass rewrites, or modifying originals,
  except for actions contained within the acting task's owned
  `work/<exact task title>/` directory.

## Documentation layout

- `docs/` contains repository context, plans, hypotheses, policies, and release
  documentation.
- Each feature has exactly one `na228_builder/features/<feature>/README.md`;
  feature-module details are sections there, not nested or sibling feature
  Markdown files. Reusable engine documentation belongs in the corresponding
  `na228_builder/modules/<module>/README.md`.
- When retiring a script, promote reusable logic/knowledge and record the old
  path, recovery commit, retirement reason, and maintained replacement in the
  retirement index in `scripts/README.md`. Recover historical code only into
  task-owned temporary space for inspection; never execute it blindly.
