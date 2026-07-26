# Repository and workspace policy

## Paths and links

- Canonical project files, scripts, configuration, logs, manifests, metadata,
  and generated artifacts use repository-relative paths. Machine-specific
  absolute paths are limited to dated `.agents/` handoffs, transient tool
  arguments/diagnostics, and user-facing clickable links unless explicitly
  authorized.
- `project-paths.json` is the single source of truth for stable project-level
  directories and named files. Resolve them through the shared PowerShell or
  Python loader. Do not inventory ordinary descendants such as `BTL.BIN`.
- Deleting or moving the last content of a configured root or direct manifest
  file must update the manifest and every `@root` documentation reference, then
  validate both path loaders. Never preserve an empty directory for a manifest.
- For `from <source> to <destination>` link requests, preserve the source and
  create the link at the destination. Do not redesign ownership or storage.
  Explain when the requested link type cannot provide tracked content diffs.
- When pairing trees, enumerate both sides and preserve exact existing spelling.
  Ask if no unique mapping exists.
- Maintain file hardlinks from project files under
  `@pcsx2_files/game_settings/`, `@pcsx2_files/input_profiles/`, and
  `@pcsx2_files/input_recordings/` to same-relative-path counterparts under
  `@pcsx2_user/gamesettings/`, `@pcsx2_user/inputprofiles/`, and
  `@pcsx2_user/inputrecordings/`. Directories are never linked. Extra PCSX2
  files remain untouched. After authorized operations or Git actions that may
  replace project files, verify and restore the hardlinks. Refuse a differing
  occupied counterpart. This invariant does not independently authorize
  protected-tree access.

## Git and concurrent work

- User edits and commits are expected. Refresh status/history before Git
  operations, preserve unrelated work, and stage only intended paths.
- Non-overlapping coherent hunks may be edited concurrently. Use hunk-level
  staging. Pause only for overlapping or logically conflicting changes.
- Agents may push already-present commits. If a non-conflicting user change is
  accidentally included, the commit may be pushed as-is and must be reported.
- Commit and push every completed change automatically at a coherent boundary.
  Git never requires `qwe` or separate approval.
- Commit subjects use `[<exact task title>] <imperative summary>`. Override the
  author for that commit only using the matching `.agents/git-authors.tsv`
  entry, or `<agent-name>@agent.invalid` when absent. Never alter repository or
  global identity or rewrite user commits.
- Git history recovers tracked files. Delete confirmed disposable generated
  files; preserve irreplaceable untracked inputs deliberately outside the repo
  before deletion.

## Access failures and escalation

- Use scoped elevation from the first attempt for every filesystem operation,
  including reads, listings, searches, hashes, link checks, and mutations.
- After an access failure, retry only the failed operation; do not repeat work
  that already succeeded.
- An access or elevation denial never silently changes an authorized cleanup
  into preservation. Revalidate the exact target, retry the still-pending
  operation with the narrowest valid elevation, and verify its result. If the
  scoped retry is also denied, stop and report the exact unfinished target;
  never continue or claim completion while leaving it behind.
- When a new recurring access failure and its solution are confirmed, add one
  short rule here so later agents avoid it.

## Work ownership and external inputs

- A file-working task owns `work/<exact task title>/`. It may read another
  task's directory but must copy files into its own before changing them.
- Keep task copies, experiments, intermediate files, builds, runtime artifacts,
  and logs in clearly named subfolders under that owner. Never use top-level
  `work/temp/`.
- Treat changing external files as unstable inputs. Copy reasonably small
  inputs, including selected screenshots and savestates, into
  `work/<task title>/inputs/` with provenance before relying on them.
- Baselines, modified copies, analysis outputs, and builds remain separate.
- At completion, inspect the owned tree; delete disposable copies, probes,
  generated files, and logs; promote reusable findings; document every retained
  artifact and its purpose; and scan every changed directory tree to remove
  every empty directory, including ignored and untracked ones.
- Empty directories never represent configuration or ownership. Do not retain
  `.gitkeep`, placeholder READMEs, or header-only data solely to preserve one.
  Represent required declarations through meaningful tracked configuration or
  producer/consumer dependencies and verify fresh-checkout behavior.

## Logs and scripts

- "The PowerShell profile" means the shared profile at
  `$env:USERPROFILE\Documents\PowerShell\profile.ps1`; never hardcode the
  user's account name when locating it.
- Unless the user explicitly requests embedded profile code, profile changes
  are limited to thin dot-source imports and aliases that expose project-owned
  entrypoint scripts. Keep all functions and reusable implementation under the
  project's maintained `scripts/` tree.
- Use purpose-specific subfolders under `@logs/`, workstream records under
  `@workstream_logs/<exact task title>/`, and worker records under the task's
  `logs/`; never write directly in shared log roots.
- Logs are disposable execution records. Before task completion, promote
  confirmed reusable findings and useful negative results into knowledge or
  canonical data, then delete disposable logs and empty directories. Follow
  `docs/LOGGING.md`.
- Maintained scripts live by responsibility under `scripts/lib/`,
  `scripts/na2/`, `scripts/pcsx2/`, `scripts/media/`, `scripts/project/`, or
  `scripts/research/`. Never create `scripts/archive/`; use Git history and the
  retirement index in `scripts/README.md`.
- Reusable or potentially helpful scripts never remain under `work/`; promote
  them immediately. Task-local probes may remain only while disposable.
- Prefer cohesive responsibility-based files. Split independent concerns when
  that improves navigation, testing, or concurrency; do not split solely by
  size.
- Prefer reusable verifiable commands/scripts over long one-off command chains.
- Treat `@utils/old/` as untrusted; inspect a chosen tool before execution.
- Ask before destructive actions, mass rewrites, or modifying originals.

## Documentation layout

- `docs/` contains repository context, plans, hypotheses, policies, and release
  documentation.
- Each feature has exactly one `na2_patcher/features/<feature>/README.md`;
  feature-module details are sections there, not nested or sibling feature
  Markdown files. Reusable engine documentation belongs in the corresponding
  `na2_patcher/modules/<module>/README.md`.
- When retiring a script, promote reusable logic/knowledge and record the old
  path, recovery commit, retirement reason, and maintained replacement in the
  retirement index in `scripts/README.md`. Recover historical code only into
  task-owned temporary space for inspection; never execute it blindly.
