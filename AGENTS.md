# AGENTS.md

PS2 modding/reverse-engineering workspace for Narutimate Accel v2.28, based on Naruto Shippuuden: Narutimate Accel 2 / SLPS-25837.

## Hard rules

- Use only repository-relative paths in canonical project files, scripts, configuration, logs, manifests, metadata, and generated artifacts; never persist machine-specific absolute paths there. Absolute paths are permitted only in dated `.agents/` handoffs as non-authoritative migration context, transient in-memory command arguments or diagnostic output when a tool requires them, and user-facing clickable file links. Do not persist an absolute path anywhere else unless the user explicitly authorizes that specific exception.
- The task workflow and its approval gates apply only to selected work from `TASKS.md`. Perform small, direct, low-risk changes immediately without a plan, intelligence-level recommendation, or approval gate; keep non-documentation changes uncommitted in the current changeset until the user requests or approves Git operations. Automatic commit and push applies to selected `TASKS.md` tasks and documentation-only changes.
- For a selected task, only read-only inspection is allowed before plan approval. An unambiguous use of `approved`, `qwe`, or the keyboard-layout equivalent of `qwe` produced by the same physical keys under another active input layout authorizes changes and may appear within a longer message. Agents automatically commit and push their completed changes without approval. A second unambiguous approval after result review authorizes deletion of the completed task from `TASKS.md`.
- The user may edit files or create commits while agents are working; treat this as expected concurrent activity, not an anomaly or blocker. Refresh Git status and history before staging, committing, and pushing; preserve concurrent user work and stage only the intended changes unless the user directs otherwise. Agents may push the user's existing commits together with their own. Pause when concurrent changes directly overlap or conflict with the agent's work, or materially change the requested outcome.
- Agents may work concurrently when their tasks and resources are independent. PCSX2, ISO building/promotion state, `.building` files, and any other singleton or mutable shared resource are exclusive: the task already using the resource keeps it, and a competing task must not close, replace, reconfigure, or otherwise take it over. The competing task stops its active turn and uses the existing bounded sleep/wakeup policy to check again later; it must not busy-wait, repeatedly poll, or invent unrelated substitute work while waiting. Resume only after one bounded check confirms the resource is free, and disable the wakeup after acquiring it or when the dependency no longer exists.
- Commit and push documentation-only changes automatically without `qwe` or any other approval, using the authoring agent's identity. This includes `AGENTS.md`, `TASKS.md`, plans, handoffs, and other documentation-only commits, including documentation-only selected-task results. A push may include any already-present local commits; do not exclude or rewrite them.
- When progress depends on another task, user action, or external process and no necessary in-scope work remains, stop the active turn instead of busy-waiting, repeatedly polling, or inventing unrelated work. Schedule a thread wakeup at a reasonable interval. Each wakeup performs one bounded status check; if the dependency is still unresolved, make no repository changes, stop again, and schedule the next wakeup. Disable the wakeup as soon as the dependency resolves.
- For every agent-authored Git commit, override the author for that commit only. An agent may use only the `.agents/git-authors.tsv` entry whose `agent_name` exactly matches its own normal name; if no matching entry exists, use the agent's normal name and a normalized `<agent-name>@agent.invalid` address. Never use another agent's registered identity. Do not change repository or global Git identity, rewrite commit subjects, or alter user-authored commits.
- Execute freely within an approved task, including major implementation changes. If the task becomes unclear or the whole approach is wrong, stop safely and clarify; a replacement plan requires approval.
- During an already-approved task, user questions, corrections, objections, status requests, and rhetorical questions are not stop signals. Answer or acknowledge them briefly and continue executing in the same turn. Stop only when the user explicitly says `stop`, `pause`, or `wait`, when required user input is genuinely missing, or when the task has become unsafe or materially unclear.
- Use `na2_patcher/profiles/current/` as the active reproducible build definition. Profiles must pin every enabled module input by hash and use only repository-relative paths; do not select newest packages implicitly in the normal workflow. Raw-binary profile hashes cover canonical TSV inputs and referenced blobs, not adjacent documentation.
- Use annotated Git tags for accepted reproducible checkpoints. A checkpoint tag must target a committed state whose profile pins, module inputs, and documentation agree; tags do not replace frozen binary release artifacts.
- Never change binary files manually.
- All binary changes must go through scripts.
- Prefer importing verified data or bytes from canonical NUN5 sources whenever a suitable equivalent exists and preserves the intended behavior. Raw-binary replacement bytes are also allowed when importing from NUN5 is unsuitable, unavailable, or the intended NA2 behavior deliberately differs from NUN5; document the reason and supporting evidence.
- Preserve file sizes unless explicitly instructed.
- Treat `project-paths.json` as the single source of truth for stable project directory roots and canonical project files or paths. Put static paths and named files there instead of embedding duplicate literals, and load them through the shared PowerShell or Python path loader. Use these abstractions wherever practical, but do not create manifest entries merely to eliminate transient, generated, caller-supplied, or genuinely local one-off paths. Documentation refers to configured roots as `@root/...`.
- Do not modify files under the configured `source` root (`@source/`) unless explicitly instructed.
- Keep untouched source media under `@source/`.
- Keep extractions of original media beside the source archive as `<archive filename>.files`.
- Treat everything under `@source/`, including extracted files, as read-only reference material.
- Do not create generated files, temporary files, logs, probes, manifests, or metadata under `@source/`; preserve the extracted game/archive structure exactly.
- Keep Windows read-only attributes applied to files/folders under `@source/`.
- Before changing any original-derived file, copy it outside `@source/` and modify only the copy.
- Keep only the active working ISOs under `build/`: `build/NA2.28 - Current.iso` and, when rotation history exists, at most `build/NA2.28 - Previous.iso`; do not store PNACH files, loose replacements, logs, or other working files there. During a build, `build/NA2.28 - Current.iso.building` is the only standard temporary ISO. Remove it on failure; after successful verification, discard it without rotation when its content matches `NA2.28 - Current.iso`, or atomically promote it when the content differs.
- Every build log must report `ISO result: unchanged` when the verified candidate matches `NA2.28 - Current.iso`, or `ISO result: updated` when a different candidate is promoted, together with whether rotation occurred.
- Temporary, parity-check, and hypothesis-test ISOs may remain under `build/` while they have a concrete future testing or comparison use. Permanently delete them as soon as they become useless; never leave obsolete ISOs accumulating under `build/`.
- Do not recreate a top-level `packages/` staging/history directory. Normal builds consume hash-pinned profile modules. Keep temporary imported archives under a task-specific `work/temp/` folder, normalize useful data into a module, verify it, then delete the archive or deliberately preserve an irreplaceable copy outside the repository.
- Do not recreate a top-level `milestones/` package archive directory or `na2_patcher/milestones/` snapshot tree. Keep reproducible module data as hash-pinned declarative inputs beside its module; retain retired inputs and package archives through Git history and annotated checkpoint tags.
- Translation checkpoints tag the complete committed project state, including canonical mapping data, its exact profile pin, and the integrated engine version. Do not duplicate mappings into snapshot directories. Legacy translation builder archives remain only in Git history. Generated translation TSVs are compatibility run outputs, not checkpoint inputs.
- Treat `na2_patcher/modules/translation/mappings.tsv` as the translation module's current versioned input. Profiles may reference it only with an exact content hash; changing it requires updating the profile pin as an explicit translation version change.
- The normal profile workflow invokes the translation module directly and records its generated plan and summary under the profile run log. There is no standalone translation-export command or source-hash bypass.
- Keep frozen release artifacts under the ignored root `releases/` relative link.
- Never alter, overwrite, rename, move, or delete anything under `releases/`.
- Only create new uniquely named release outputs under `releases/`.
- If a target path under `releases/` already exists, stop immediately and inspect/report manually.
- Every release PNACH must correspond to the PCSX2 CRC of the ELF inside the paired release ISO.
- Before reporting a release as valid, check the paired ISO/ELF CRC against the PNACH filename and warn if they do not match or cannot be verified.
- Keep logs, inventories, hashes, and patch records under task-specific subfolders of `logs/`; do not write files directly in the `logs/` root. Logs are disposable execution records, not the sole store of project knowledge. Before pruning a log or temporary handoff, promote reusable confirmed findings into tracked `docs/knowledge/` documentation or canonical module-local data. Follow `docs/LOGGING.md` for retention and cleanup.
- Do not recreate a project `trash/` holding area. Git history is the recovery mechanism for tracked files. Delete confirmed disposable generated files directly; before deleting an irreplaceable untracked input, preserve it deliberately outside the repository.
- Generated/intermediate files go under `@logs/` or `@work/temp/` with task-named subfolders when throwaway workspace is needed. `@scripts/` contains maintained code only. Completed working ISOs are the only outputs kept under `@build/`. Original-source extractions stay beside their source archive under `@source/` as `<archive filename>.files`.
- Treat top-level `old/` as the user's personal folder. Do not inspect, search, execute from, modify, move, delete, or otherwise touch it unless explicitly instructed.
- Treat `@utils/old/` as an untrusted tool/archive dump. Do not execute tools from it until inspected and chosen for a specific task.
- Log every binary patch: file, offset, original bytes, new bytes, reason.
- PNACH is the source of truth only for emulator settings, runtime-only memory patches, and temporary hypotheses that cannot yet be represented as file-backed module edits. Permanent file-backed changes belong in named `na2_patcher` raw-binary patch sets and must not remain enabled in PNACH. `// [Name]` is only a label/comment; a PNACH item is enabled only when its executable `patch=`/setting line is uncommented.
- Use fixed-address PNACH writes for hypothesis testing only when the target is in the boot ELF or another region proven to remain resident and stable for the entire write lifetime.
- Never apply an unguarded fixed-address PNACH write to `BTL.BIN`, `ETC.BIN`, or another module that is loaded and unloaded on demand; the same EE address may hold unrelated data while that module is absent. Test those hypotheses by patching the file through scripts, rebuilding the ISO, and recording the result.
- Runtime overlay PNACH testing is exceptional and requires a proven load-state/signature guard. Avoid fixed writes to dynamic heap objects unless their allocation, address, and lifetime are established.
- Keep active PNACH files clean: confirmed named sections only, plus temporary hypothesis patches at the very top when actively testing.
- Temporary PNACH hypothesis patches go at the top of the file as comment-only names plus disabled `// patch=` lines; uncomment them only while actively testing.
- Put confirmed subroutine roles, caller/callee relationships, state-machine behavior, address mappings, runtime observations, and useful negative results under `docs/knowledge/` or beside the canonical module data they describe. Move unresolved candidates, failed speculative addresses, and unconfirmed interpretations to `docs/HYPOTHESES.md`; do not use it as the confirmed knowledge base.
- Agents may read and manage `TASKS.md` under the task workflow below. Tasks may be added at any time by the user, or by an agent when the user orders it. Agents may move tasks between `In Progress` and `Backlog`, execute selected tasks after plan approval, and delete a completed task only after result approval.
- For string patches, always check encoded byte length before writing. `[S]`-prefixed `shorten` mappings are authorized manual fit exceptions when they retain an exact official NUN5 source reference.
- Prefer Shift-JIS / CP932-compatible text unless proven otherwise.
- The confirmed DATA.CVM password is `cc2fuku` for NA2, NUN3, and NUN5, and `Iruka` for NUN6 A35.
- Do not expand DATA.CVM, ELF, BIN, AFS, CCS, or ISO structures unless explicitly instructed.
- Do not include `ADV.bin` in release builds unless explicitly requested.
- Do not delete/rename PSS files blindly.
- Avoid GUI-only workflows when CLI/scripted alternatives exist.
- Ask before destructive actions, mass rewrites, ISO rebuilds, or modifying originals.
- If uncertain, inspect and report instead of acting.


## Task workflow and approval

Before inspecting, planning, or executing a selected task, verify that it belongs
to the current Codex task/chat's workstream and responsibility. If it belongs in
another existing workstream coordinator or dedicated task chat, route it there
immediately with the task text, status, user instructions, relevant context,
and any work already performed; tell the user where it was routed, then stop
handling it in the current chat. Do not duplicate the task across chats. If no
suitable chat exists, send one setup request to `Task coordinator` and follow
the chat-creation approval rules below instead of absorbing the work locally.

Read-only inspection for a selected task may begin immediately without plan
approval. At the start of any inspection that may take more than a brief check,
the agent must provide this status block before or with its first inspection
action:

```text
Phase: read-only inspection
Purpose: gather enough evidence for the plan
Changes: none
Recommended effort: <level>
Next response: short plan + effort recommendation + needed user inputs + approval gate
```

The initial effort recommendation is provisional and must be stated even when
inspection is still needed. If the evidence changes the recommendation, explain
the change in the plan. Progress updates during a long inspection must keep the
current phase and required next response clear.

Until a selected task is completed, every final response that hands control
back to the user must include a standalone `Recommended effort: <level>` line.
This applies after inspection, at approval gates, in execution handoffs, and at
every stop, pause, dependency, safety, or relaunch boundary. Stating the level
only in commentary or an earlier response does not satisfy this requirement; if
the recommendation changes, explain why.

Every selected-task plan must include a standalone `Needed from you: <items>`
line beside `Recommended effort`. Ask specifically for every user-supplied input
or action that is expected or may materially help execution, such as savestates
at named screens, screenshots, files, test results, tool access, or an in-game
action. Explain when each requested item is needed. If the agent needs nothing
from the user, state `Needed from you: nothing` instead of omitting the line.

1. Tasks may be added to `TASKS.md` at any time by the user, or by an agent when the user orders it.
2. Each workstream subsection is coordinated by a Codex task whose title exactly matches the subsection heading. The coordinator owns that workstream across statuses, so do not add redundant coordinator metadata to `TASKS.md`.
3. Each workstream subsection appears under exactly one status. Move the whole subsection when its status changes; never split one workstream across statuses. `In Progress` contains active workstreams, `Backlog` contains workstreams with one or more deferred tasks, and `Archive` contains persistent workstreams with no current tasks. `Testing` is always the final workstream subsection within whichever status contains it.
4. When a task is approved for active work, move its whole workstream subsection to the top of `In Progress`. Move a workstream to `Backlog` only when the user explicitly instructs it; never infer that move from task completion, inactivity, or an empty subsection.
5. When an approved completed task is deleted and that leaves its workstream subsection empty, move the whole empty subsection to `Archive` as part of the same completion update; never delete the subsection. If a task later returns, move the subsection out of `Archive`: to the top of `In Progress` when that task is approved for active work, or to `Backlog` only when the user explicitly directs it there. Keep the coordinator chat available but unpinned; do not archive the Codex chat merely because its workstream is under `Archive`.
6. When useful, a workstream subsection or individual task may have a dedicated context or plan document. Creating such a document is optional, but if one is created, it must be linked directly from the corresponding subsection heading or task entry in `TASKS.md`.
7. After a successful push—or whenever the user asks what is next—the workstream coordinator reads `TASKS.md` and reports only the choices under its matching workstream subsection across statuses, word for word without paraphrasing and in their original order. It preserves the applicable status and subsection headings so the task context remains visible, omits unrelated workstreams, and asks the user to select one.
8. After any authorized task-management edit to `TASKS.md`, commit and push that task update immediately without requesting approval. Stage only `TASKS.md` and any dedicated task context or plan document created or edited specifically as part of the same task-management update; never include concurrent implementation or unrelated work. Run the required chat actualization before this automatic commit and push when a workstream subsection changed. Deleting a completed task still requires result approval before the deletion is made.
9. The agent may perform read-only inspection, then gives a short plan, recommends an intelligence level, asks for the specific user-supplied inputs or actions needed under the policy above, and ends with **Awaiting plan approval**.
10. An unambiguous `approved`, `qwe`, or keyboard-layout equivalent of `qwe` as defined above, including within a longer message, authorizes changes.
11. The agent executes freely within the approved task, including major changes.
12. If the task becomes unclear or the whole approach is wrong, stop and clarify; a replacement plan needs approval.
13. When its work is complete, the agent refreshes Git state, stages only its intended changes, commits with its own registered identity, pushes without requesting approval, and reports the result.
14. Another unambiguous `approved`, `qwe`, or keyboard-layout equivalent of `qwe` as defined above, including within a longer message, authorizes deletion of the completed task. Commit and push that deletion automatically under rule 8.
15. The user's concurrent edits and commits are expected. The agent preserves them, refreshes Git state before Git operations, and may push the user's existing commits with its own.
16. Queued instructions remain part of the same changeset unless the user says otherwise.

### Task coordinator responsibilities

- The Codex task titled `Task coordinator` is the global coordinator for the task system, not a workstream coordinator. It maintains the relationship between `TASKS.md` workstreams and their Codex coordinator tasks; it does not select or execute workstream tasks unless the user explicitly directs it to do so.
- In the `Task coordinator` task, a user request to `actualize` or `actualize chats` means synchronize the Codex task chats with the live `AGENTS.md` and `TASKS.md`. It does not invoke `na2 act` or perform ISO/PNACH actualization. Requests that explicitly concern an ISO, PNACH, PCSX2, or the `na2 act` command follow the separate Actualize workflow below.
- Chat actualization reads the live files and inventories existing Codex tasks for this project. It derives workstreams from subsection headings across all statuses and treats matching subsection names as one workstream.
- Chat actualization reuses and renames suitable existing tasks before creating missing coordinators, maintains exactly one coordinator named for each workstream, and gives each coordinator status-independent scope limited to that workstream. A dedicated chat for an individual linked task may remain separate, but it is not the workstream coordinator.
- Chat actualization rebuilds the project's pinned-chat set and display order. It unpins every project chat, then repins only the required chats so `General` is always first, `Scripting` is always second, and `Task coordinator` is always third. After them, it follows the live `In Progress` order in `TASKS.md`: for each workstream subsection, pin its coordinator first, followed by any existing unarchived dedicated chats for its individual tasks in task order. Never unarchive or repin an archived dedicated chat during actualization. Chats that do not represent current `In Progress` work remain unpinned. Use the established pin sequence to produce this order without requesting visual confirmation; the user will intervene if the app's ordering behavior stops working as expected.
- Chat actualization does not select or begin task work. It updates existing chats only when their coordination rules or scope are stale, and it reports which coordinators were reused, renamed, created, or signaled.
- Creating, renaming, moving between statuses, or explicitly deleting a workstream subsection in `TASKS.md` automatically requires chat actualization immediately after the file change. If `Task coordinator` made the change, it actualizes directly; if another chat made the change, that chat must promptly send `Task coordinator` one concise actualization request with the changed subsection and its new status or removal state.
- Do not archive, delete, merge, or repurpose unrelated or surplus chats during actualization unless the user explicitly requests it.
- A workstream chat that needs global chat actualization or another coordination change outside its own scope must send one concise request to the Codex task titled `Task coordinator` instead of performing the global change itself. Include the requesting workstream, the needed change, and any relevant live state. Do not repeatedly message or poll the coordinator. The `Task coordinator` performs the coordination work and sends the outcome back when the requesting chat needs it to continue. If the coordinator cannot be found or contacted, report that to the user rather than taking over silently.
- When a selected task is presented in the wrong chat, route it to the existing matching workstream coordinator or dedicated task chat rather than merely recommending that the user move it. The handoff must preserve the exact task wording, status, user instructions, relevant evidence, and required next step. The receiving chat becomes responsible for inspection, planning, approval, execution, and reporting; the originating chat must not continue parallel work.
- Agents should proactively recommend a separate Codex task when the current chat is accumulating enough unrelated information, sustained digression, or distinct responsibilities that context quality or workstream focus is likely to degrade. Recommend an exact task title and a concise responsibility boundary, explain what should move there, and prefer an existing suitable task over creating a duplicate. Do not recommend a new task for a brief tangent that can be handled cleanly in the current context, and do not create one until the user explicitly asks or approves. After approval, route new-workstream or global coordination setup through `Task coordinator`.


## Cross-install Codex handoffs

- `.agents/` is intentional handoff infrastructure shared by separate Windows installations and Codex instances. Do not delete, ignore, or classify it as disposable clutter without reviewing its contents.
- `.agents/git-authors.tsv` is the shared non-secret Git author-identity registry for agents; it must never contain authentication tokens, passwords, signing keys, or other secrets.
- Handoffs are dated context snapshots, not canonical configuration. Live repository state, `AGENTS.md`, current docs, and the user override them.
- Machine-specific paths and task IDs are permitted inside dated handoffs only because they describe the originating installation; never copy them into active scripts or manifests.

## Workspace creation rules

- `docs/` contains repository-wide context, plans, hypotheses, and release documentation. Keep component-specific READMEs beside their components.
- Keep maintained scripts grouped by responsibility under `scripts/lib/`, `scripts/na2/`, `scripts/media/`, `scripts/project/`, or `scripts/research/`. `scripts/archive/` is reserved for unsupported historical reference implementations; inspect and explicitly select an archived script before using it, and never treat it as part of the normal workflow. Do not restore the former flat script dump; update `scripts/README.md` when a responsibility changes.
- Prefer cohesive files organized by responsibility. Split a file when it contains independent concerns, becomes difficult to navigate or test, or causes unrelated changes to collide. Do not split files solely because they are large; a large file is acceptable when it represents one coherent implementation and splitting would reduce clarity.
- Any Codex task/thread that works with files must own `work/<task title>/`, where the directory name exactly matches that Codex task's title, including capitalization; for example, the `Project` task uses `work/Project/` and the `QoL` task uses `work/QoL/`. Workers acting for that task use its task directory rather than creating agent-specific directories. Keep the task's copies, experiments, and intermediate artifacts inside it, with subfolders such as `base/`, `mod/`, and `temp/` when useful. A task may read another task's directory but must not modify, move, rename, or delete anything there; to make changes, copy the needed file into its own task directory and modify only that copy.
- Treat external files that may change during the task as unstable inputs. When they are reasonably small, including screenshots and savestates, copy them into the task's owned directory before relying on or modifying them. Read very large external inputs in place when copying would be unreasonable, while following all source and original-media protections.
- Use temporary subfolders inside the task's owned directory for throwaway/intermediate work. At task completion, clean the entire owned directory: delete disposable copies, probes, and generated files; promote reusable confirmed findings into canonical documentation or module data; and retain only artifacts with concrete future value. Every retained artifact must be mentioned in a nearby README, the relevant task/knowledge document, or another canonical inventory with its purpose and location so later tasks can find and assess it.
- Use `work/` for project-specific reverse-engineering and binary-mod work. Keep work separated first by exact Codex task title and then by target or activity, for example `work/Project/<target>/base/` and `work/QoL/<activity>/mod/`. Keep reusable Ghidra projects and disassembly exports shared between related repositories under `@analysis/disassembly/<target>/`.
- Do not mix source/reference files with modified files. Baseline copies, modified copies, analysis outputs, and release/build outputs must live in clearly separate folders.
- Do not repeatedly disassemble the same binary from scratch when a preserved analysis workspace is available; reuse and update the relevant `@analysis/disassembly/<target>/` materials.
- State explicitly what software/tools were used for a task. If the right tool is uncertain or missing, ask the user to provide or approve one.
- Prefer reusable, verifiable commands and scripts over long one-off command chains. Keep closely related implementation together when that is clearer than introducing additional files.

## Release and checkpoint rules

For file-level translation releases, one zip only. Zip filename gets version/postfix. Internal filenames must be exactly:

- `BTL.BIN`
- `ETC.bin`
- `SLPS_258.37`
- `translation_log.tsv`

No postfixes inside the zip. Never include `ADV.bin` unless explicitly requested.

For full project releases, place new frozen files in `releases/` with clear version/postfix names. Active working ISOs stay in `build/`.

Use annotated Git tags for accepted reproducible source checkpoints. Tags must point to committed project states and must not be used as substitutes for external ISO, ZIP, PNACH, checksum, or other frozen release artifacts.

`releases/` is append-only/frozen. Do not rewrite, rename, move, delete, or modify existing release files or folders. If the intended output name already exists, stop and inspect manually instead of choosing a workaround.

Release PNACH files are coupled to the boot ELF CRC of their paired ISO. Always verify the PNACH CRC suffix against the ISO's actual PCSX2 game CRC before treating a release as valid. If verification is unavailable or inconclusive, report that uncertainty clearly.


## Actualize workflow

The root command interface is: bare `na2` builds the current profile, conditionally rotates a changed ISO, maintains Current/Previous PNACH aliases, and launches `NA2.28 - Current.iso`; `na2 -c` launches `NA2.28 - Current.iso` without rebuilding, closing PCSX2, or changing PNACH aliases; `na2 -p` launches `NA2.28 - Previous.iso` with the same no-maintenance behavior; `na2 -un5` launches the configured canonical NUN5 source ISO with the same no-maintenance behavior; `na2 act` maintains the Current/Previous PNACH aliases without building or launching. No other public build, path-override, hash-bypass, or launch-bypass arguments are supported. `_na2.ps1` owns only public dispatch and transcript management; `scripts/na2/build.ps1` owns profile build, ISO promotion/rotation, and the corresponding PNACH alias maintenance; `na2_patcher/build_profile.py` owns profile-only ISO composition and verification; `scripts/na2/launch.ps1` only starts PCSX2 for a selected ISO. Do not recombine these responsibilities or restore direct newest-package selection.

When asked to actualize, keep the canonical file named `@pcsx2_files/SLPS-25837_C0659AD1.pnach`. Managed aliases are only matching-serial symlinks that resolve to this canonical file; preserve all real PNACH files, other games, and unrelated symlinks. If the canonical file is zero bytes, delete its managed aliases directly and skip ISO/CRC inspection. Otherwise, use the ISO in `@build/` by default, calculate the PCSX2-style ELF CRC from its boot ELF, delete obsolete managed aliases, and create the current CRC-named relative symlink targeting the canonical project PNACH if missing. Refuse an occupied target filename instead of overwriting an unmanaged file or symlink.

After a successful build, actualize the Current alias and retain the matching Previous alias when Previous exists. When the canonical PNACH is empty, remove all managed aliases. `na2 act` performs the same Current/Previous alias maintenance without building or launching. The `-c`, `-p`, and `-un5` launch selectors never change PNACH aliases.

During build-time or explicit PNACH actualization, log enabled cheat names from uncommented PNACH `patch=` or setting lines. Metadata-only lines do not count; report `none` when there are no enabled cheats. Pure launch selectors do not inspect or report PNACH state.

Before rebuilding or launching a test ISO, unconditionally issue the close command for the configured `@pcsx2/pcsx2-qt.exe`. Do not probe first to see whether PCSX2 is running; closing an absent process should be treated as a harmless no-op.

If an agent launches PCSX2 for testing, it must use `scripts/na2/test_launch.ps1`. The wrapper temporarily mutes PCSX2, starts it hidden without intentionally activating it, re-hides any exposed window, restores the previous foreground window if PCSX2 took focus, closes the test instance after the validation window, and restores the original audio setting even when testing fails. Normal user launches remain unchanged.

## Task report format

For completed `TASKS.md` tasks, report files read, files created/modified, whether originals were untouched, scripts/commands used, sizes, and uncertainties. This format does not apply to small direct changes.
