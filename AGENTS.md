# AGENTS.md

Commit: agent-identity
Commit-Roots:
  - .
Push: auto

PS2 modding and reverse-engineering workspace for *Narutimate Accel v2.28*,
based on *Naruto Shippuuden: Narutimate Accel 2* / `SLPS-25837`.

## Project and implementation boundaries

- `NA2-Modding`, `UN-Workshop`, maintained subrepositories such as the PCSX2
  fork, and future repositories added to this maintained project may be changed
  together when the task requires it. Cross-repository work needs no separate
  approval.
- Master Mode and Shop are globally out of scope. Do not work on or document
  them.
- After replacing or removing behavior, delete its retired code and tests.
  Do not retain compatibility, detection, rejection, fallback, migration, or
  retirement checks unless explicitly requested. Verify removals with temporary
  searches or checks discarded before completion.
- Ask before changing unrequested user-visible behavior or introducing a new
  mandatory workflow, public interface, persistent mechanism, project-wide
  contract, or production/build/CI/runtime integration.

## Task control

### Task sequencing

- Treat a later request as a new task unless it explicitly modifies, cancels,
  replaces, reorders, or asks about existing work, or supplies requested input.
- Treat a user-aborted turn as cancellation of its unfinished work. Resume that
  work only after a new operative command.
- Keep unfinished tasks in arrival order. Work only on the oldest task's next
  unfinished instruction; do not inspect, prepare, or start later work. A
  correction does not alter or reorder other unfinished work.
- `Immediately` temporarily moves the newest task to the front. After it
  finishes, resume the interrupted task, then continue the queue.

### Action boundary

Immediately before beginning state-changing work in any workflow, state:

```text
Changes: <what will be changed>
Required user actions: <later user action or nothing>
<workflow-specific settings>
```

Include every setting defined by the active workflow.
No other : lines are allowed. Do not add your own stuff.

Before starting or continuing work, identify the best practical approach.
If you lack what would materially improve quality or efficiency, stop and
request it. Do not settle for an inferior approach merely because you can
make it work.
Never search for inputs or determine that existing inputs are appropriate by yourself.
Present the action boundary only when work can begin.

## Commands and interaction modes

Fresh chats start with no interaction mode active. Before stating
implementation intent or changing state, read the active
[Design](docs/interactions/design_mode.md) or
[Interactive](docs/interactions/interactive_mode.md) mode document.

Only the exact commands defined below change the active interaction mode.
The active mode's document applies alongside global and project-wide policies.
Exiting Design or Interactive mode returns to the default state with no active
mode.

Global commands are defined in `@codex-utils/AGENTS_G.md`. For the `na228` and
Workshop command-line interfaces, use `na228 help`, `workshop help`, and the
owning component documentation.

### Interaction modes

- `des mode`, `design mode`: enter
  [Design mode](docs/interactions/design_mode.md).
- `int mode`, `interactive mode`: enter
  [Interactive mode](docs/interactions/interactive_mode.md).

### Task control and validation

- `snap`: consolidate the active task's discussed work into an implementation
  proposal and include all agent-owned work required to deliver it.
  Only include work that will be done.
  Exclude completed tasks, unrelated state, and user-directed actions.
  Omit any statement that has no corresponding pending agent action.
- `ver`: accept the current result across every repository changed by the task.
  Agents may then add tests. Validate, commit, and push the accepted result. In
  Design mode, first promote useful design content and delete the design
  document, then exit after pushing.
- `exit`: exit Design mode or Interactive mode without accepting the result
  or authorizing a commit. It has no effect when no mode is active.
- `zxc`: follow the
  [graceful-stop procedure](docs/procedures/graceful_stop.md).
- `e2e: <request>` or `e2e <suite> <captures>: <request>`: follow
  [the E2E validation workflow](docs/workflows/e2e_validation.md).

### Conversation and metadata

- `n`: proceed to the next item.
- `imm`: apply the `immediately` behavior from
  [task sequencing](#task-sequencing) to the most recently added
  unfinished task.
- `mode`: only when the entire user message, after trimming surrounding
  whitespace, is exactly `mode`, respond with only `Default`, `Design mode`, or
  `Interactive mode`, whichever applies. It does not change the mode or grant
  authority. Do not trigger it from a longer message, quoted text, or supplied
  context.
- `ss`, `ss<number>`: shorthand for `savestate` / `savestate<number>`.
- `new ss<number>`: move the savestate to `@work/<exact chat title>/inputs/`
  and follow the current context on how you should inspect it.
  New savestates are stored in Workshop's `@pcsx2_savestates/`.
  The command supplies all input identification needed for the move.

## Context and workflows

Read a routed workflow before describing its execution.

On entering a task, read its directly linked documentation and relevant
component documentation. Load other technical documents only when required,
and read only relevant sections of large documents.

## Workspace

### Paths and repository boundaries

- Workshop owns shared path configuration and source-game identities. NA2
  imports that configuration and defines only project-specific paths and
  settings.
- Workshop must not depend on NA2. NA2 may override an imported entry only by
  defining the same name in its own manifest.
- Persist only repository-relative paths or configured aliases, never
  machine-specific absolute paths.
- Resolve each path from the manifest that defines it. Relative paths and alias
  references use that manifest's directory and entries, never the importing
  manifest or caller's working directory.
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
  [runtime validation](#runtime-validation).

### Git and concurrent work

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

### File and folder management

- Before using a task work root, resolve the current exact chat title from
  Codex. Use only `@work/<exact chat title>/`. Treat every other `@work` path
  as read-only except for input moves required by this policy.
  Set `NA228_TASK_WORK_ROOT` to the task root before maintained
  commands create temporary files.
- Never use a system temporary directory.
- Write authorized project changes to their canonical project paths and
  maintained workflow outputs to their configured repository paths.
- Copy changing external inputs to `@work/<exact chat title>/inputs/` before relying on them.
- Before completion, remove disposable task artifacts.
- `TASKS.md` is user-only. Agents must not read or modify it.
- Never create or use an additional Git worktree.
- `docs/designs/` is read-only outside Design mode.
- Everything under `@source/`, including extracted views, is read-only unless
  the user authorizes an exact modification. Only original archives and
  extraction views created through the
  [source-extraction runbook](docs/runbooks/source-extraction.md) belong there;
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

## Implementation

### Scripts and dependencies

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

### Builder, binary, and donor changes

- Before modifying builder composition, use the relevant sections of
  `@builder/README.md` and the affected feature document as the canonical
  contract. Do not recreate retired schemas or assumptions from historical
  notes.
- Never edit binaries manually. All binary changes go through reproducible
  scripts and guarded canonical data.
- Prefer one injection over multiple binary edits when they implement one
  behavior and a stable guarded hook can express it clearly in C or assembly.
  Keep isolated constant or instruction replacements as direct edits.
- Preserve file sizes unless the user explicitly approves expansion of the
  affected DATA.CVM, ELF, BIN, AFS, CCS, or ISO structure.
- Prefer verified canonical NUN5 data/bytes when suitable. When donor data is
  unsuitable, document the intended NA2 behavior and evidence for replacement
  bytes.

### PNACH

- Use PNACH mainly to test runtime hypotheses and adjust the runtime logic of
  other source games.
- Fixed-address writes require a region proven resident and stable for their
  lifetime. Runtime overlay tests require a proven load-state or signature
  guard; never make unguarded overlay or dynamic-heap writes.

## Validation

### Default validation

- Documentation-only changes require no validation.
- For code changes, run unit tests.
- After implementation and earlier checks are complete, build changes that can
  affect built bytes. Any later byte-affecting change requires another build.
- Agents build only through `na228 build <config>`, using `b` by default. Never
  use build-and-launch commands for validation.
- PCSX2 fork is built using its repository instructions.

### Validation behavior and tests

- After user acceptance, fix every failing maintained test discovered during
  the work before committing, unless evidence shows that a concurrent task or
  another task's uncommitted changes caused it. In that case, leave it unchanged
  and report the conflicting ownership.
- A script may fail or discard its output only when validation shows the primary
  result is invalid, unsafe, or unusable. Report other validation failures as
  warnings; making them fatal requires explicit user approval.
- Before `ver`, do not propose, plan, create, or modify tests.
  Modifying tests for PCSX2 fork is allowed.
- Unit tests must detect a meaningful regression in accepted behavior or a
  documented safety contract using the smallest practical isolated inputs. Do
  not restate source data, freeze incidental implementation details, mirror the
  implementation, or rerun the production pipeline.

### Runtime validation

- Agents must not directly launch, attach to, command, screenshot, probe, or
  close any PCSX2 process.
  Unless the user explicitly requests a specific maintained workflow below,
  runtime validation must not appear in the agent's reasoning, responses, or actions:
  [E2E](docs/workflows/e2e_validation.md),
  [input-recording with markers](docs/workflows/input_recording_with_markers.md), or
  [input-recording without markers](docs/workflows/input_recording_without_markers.md) workflow.
  Agents invoke only the requested workflow's entrypoints and inspect its
  outputs; the workflow owns emulator control. Execution is not user acceptance.

## Research and evidence

- When citing file lines, quote the relevant text and attach its clickable
  citation. Never use bare line numbers or citations without the supporting
  text.
- Treat explicit user observations and established evidence as current facts
  unless specific new evidence contradicts them.
- Use GhidrAssist MCP for substantive disassembly and decompilation. Follow the
  [shared runbook](<../UN Workshop/docs/runbooks/ghidrassistmcp.md>).
- Distinguish observations, inferences, hypotheses, contradictions, confidence,
  and experiments; never present hypotheses as facts or required implementation
  models.
- Every knowledge document must contain a `## Research coverage` section with
  these bullets:
  - **Assigned scope:** what the document investigates.
  - **Exploration depth:** how thoroughly each part was investigated.
  - **Confirmed coverage:** what the investigation established.
  - **Unresolved or untested:** what remains incomplete or unknown.
  - **Deliberate exclusions and overlap:** the document's ownership boundaries.
  - **Evidence limitations:** what the available evidence cannot establish.
- During any investigation that requires disassembly inspection record
  reverse-engineering findings and only the evidence needed to assess
  them in the relevant knowledge document. Do not record temporary file names
  or other details that do not affect the finding.
- `@tools/CCSFileExplorerMSF` is the default CCS explorer.

## Documentation layout

Give each document one job and canonical authority. Every paragraph must add
useful information owned by that document; remove it otherwise.

- `AGENTS.md` owns project-wide instructions and command definitions;
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
- Keep candidate-specific documentation provisional until acceptance; retain
  only documentation for the accepted result.
- Before completing a documentation change, review each affected document as a
  whole and remove anything that violates this section.
