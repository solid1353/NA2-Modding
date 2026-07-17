# AGENTS.md

PS2 modding/reverse-engineering workspace for Naruto Shippuuden: Narutimate Accel 2 / SLPS-25837.

## Hard rules

- Use only repository-relative paths in canonical project files, scripts, configuration, logs, manifests, metadata, and generated artifacts; never persist machine-specific absolute paths there. Absolute paths are permitted only in dated `.agents/` handoffs as non-authoritative migration context, transient in-memory command arguments or diagnostic output when a tool requires them, and user-facing clickable file links. Do not persist an absolute path anywhere else unless the user explicitly authorizes that specific exception.
- The task workflow and its approval gates apply only to selected work from `TASKS.md`. Perform small, direct, low-risk changes immediately without a plan, intelligence-level recommendation, or approval gate; keep them in the current changeset unless the user says otherwise.
- For a selected task, only read-only inspection is allowed before plan approval. An unambiguous ASCII use of `approved` or `qwe` authorizes changes and may appear within a longer message. A second unambiguous approval after result review authorizes task deletion, commit, and push.
- The user may edit files or create commits while agents are working; treat this as expected concurrent activity, not an anomaly or blocker. Refresh Git status and history before staging, committing, and pushing; preserve concurrent user work and stage only the intended changes unless the user directs otherwise. Agents may push the user's existing commits together with their own. Pause when concurrent changes directly overlap or conflict with the agent's work, or materially change the requested outcome.
- Execute freely within an approved task, including major implementation changes. If the task becomes unclear or the whole approach is wrong, stop safely and clarify; a replacement plan requires approval.
- Use `na2_patcher/profiles/current/` as the active reproducible build definition. Profiles must pin every enabled module input by hash and use only repository-relative paths; do not select newest packages implicitly in the normal workflow. Raw-binary profile hashes cover canonical TSV inputs and referenced blobs, not adjacent documentation.
- Treat `na2_patcher/milestones/` mapping snapshots as immutable module data. New translation work gets a new uniquely named snapshot/profile; never rewrite an existing snapshot.
- Never change binary files manually.
- All binary changes must go through scripts.
- Preserve file sizes unless explicitly instructed.
- Treat `project-paths.json` as the single source of truth for directory roots. Every script must load it through the shared PowerShell or Python path loader; do not duplicate configured root locations in scripts or profiles. Documentation refers to configured roots as `@root/...`.
- Do not modify files under the configured `source` root (`@source/`) unless explicitly instructed.
- Keep untouched source media under `@source/`.
- Keep extractions of original media beside the source archive as `<archive filename>.files`.
- Treat everything under `@source/`, including extracted files, as read-only reference material.
- Do not create generated files, temporary files, logs, probes, manifests, or metadata under `@source/`; preserve the extracted game/archive structure exactly.
- Keep Windows read-only attributes applied to files/folders under `@source/`.
- Before changing any original-derived file, copy it outside `@source/` and modify only the copy.
- Keep only the active working ISOs under `build/`: `build/Current.iso` and, when rotation history exists, at most `build/Previous.iso`; do not store PNACH files, loose replacements, logs, or other working files there. During a build, `build/Current.iso.building` is the only standard temporary ISO. Remove it on failure; after successful verification, discard it without rotation when its content matches `Current.iso`, or atomically promote it when the content differs.
- Every build log must report `ISO result: unchanged` when the verified candidate matches `Current.iso`, or `ISO result: updated` when a different candidate is promoted, together with whether rotation occurred.
- Temporary, parity-check, and hypothesis-test ISOs may remain under `build/` while they have a concrete future testing or comparison use. Permanently delete them as soon as they become useless; never leave obsolete ISOs accumulating under `build/`.
- Do not recreate a top-level `packages/` staging/history directory. Normal builds consume hash-pinned profile modules. Keep temporary imported archives under a task-specific `work/temp/` folder, normalize useful data into a module, verify it, then delete the archive or deliberately preserve an irreplaceable copy outside the repository.
- Do not recreate a top-level `milestones/` package archive directory. Keep immutable reproducible module data under `na2_patcher/milestones/` or as a hash-pinned declarative patch set beside its module; retain retired package archives only in Git history.
- New translation milestones freeze immutable canonical mapping data plus a hash-pinned profile; the integrated translation engine is versioned with the repository. Legacy translation builder archives are retained only in Git history. Generated translation TSVs are compatibility run outputs, not milestones.
- Treat `na2_patcher/modules/translation/mappings.tsv` as the translation module's current versioned input. Profiles may reference it only with an exact content hash; changing it requires updating the profile pin as an explicit translation version change.
- The normal profile workflow invokes the translation module directly and records its generated plan and summary under the profile run log. There is no standalone translation-export command or source-hash bypass.
- Keep frozen milestone artifacts under the ignored root `releases/` relative link.
- Never alter, overwrite, rename, move, or delete anything under `releases/`.
- Only create new uniquely named milestone outputs under `releases/`.
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
- For string patches, always check encoded byte length before writing. `[S]`-prefixed `shorten` mappings are authorized manual fit exceptions when they retain an exact official UN5 source reference.
- Prefer Shift-JIS / CP932-compatible text unless proven otherwise.
- DATA.CVM password is `cc2fuku`.
- Do not expand DATA.CVM, ELF, BIN, AFS, CCS, or ISO structures unless explicitly instructed.
- Do not include `ADV.bin` in release builds unless explicitly requested.
- Do not delete/rename PSS files blindly.
- Avoid GUI-only workflows when CLI/scripted alternatives exist.
- Ask before destructive actions, mass rewrites, ISO rebuilds, or modifying originals.
- If uncertain, inspect and report instead of acting.


## Task workflow and approval

1. Tasks may be added to `TASKS.md` at any time by the user, or by an agent when the user orders it.
2. After a successful push—or whenever the user asks what is next—the agent reads `TASKS.md`, reports several relevant `In Progress` choices and any closely related `Backlog` choices word for word without paraphrasing and in their original order, preserves their original section and subsection headings so the task context remains visible, avoids dumping the whole file, and asks the user to select one.
3. The agent may perform read-only inspection, then gives a short plan, recommends an intelligence level, and ends with **Awaiting plan approval**.
4. An unambiguous ASCII `approved` or `qwe`, including within a longer message, authorizes changes.
5. The agent executes freely within the approved task, including major changes.
6. If the task becomes unclear or the whole approach is wrong, stop and clarify; a replacement plan needs approval.
7. The agent reports the result.
8. Another unambiguous ASCII `approved` or `qwe`, including within a longer message, authorizes task deletion, commit, and push.
9. The user's concurrent edits and commits are expected. The agent preserves them, refreshes Git state before Git operations, and may push the user's existing commits with its own.
10. Queued instructions remain part of the same changeset unless the user says otherwise.


## Cross-install Codex handoffs

- `.agents/` is intentional handoff infrastructure shared by separate Windows installations and Codex instances. Do not delete, ignore, or classify it as disposable clutter without reviewing its contents.
- Handoffs are dated context snapshots, not canonical configuration. Live repository state, `AGENTS.md`, current docs, and the user override them.
- Machine-specific paths and task IDs are permitted inside dated handoffs only because they describe the originating installation; never copy them into active scripts or manifests.

## Workspace creation rules

- `docs/` contains repository-wide context, plans, hypotheses, and release documentation. Keep component-specific READMEs beside their components.
- Keep maintained scripts grouped by responsibility under `scripts/lib/`, `scripts/na2/`, `scripts/media/`, `scripts/project/`, or `scripts/research/`. `scripts/archive/` is reserved for unsupported historical reference implementations; inspect and explicitly select an archived script before using it, and never treat it as part of the normal workflow. Do not restore the former flat script dump; update `scripts/README.md` when a responsibility changes.
- Prefer cohesive files organized by responsibility. Split a file when it contains independent concerns, becomes difficult to navigate or test, or causes unrelated changes to collide. Do not split files solely because they are large; a large file is acceptable when it represents one coherent implementation and splitting would reduce clarity.
- Use `work/temp/` for throwaway/intermediate work only. Clean task subfolders there after failed or finished experiments when they are no longer useful.
- Use `work/` outside `work/temp/` for persistent reverse-engineering and binary-mod work. Keep work separated by target/task, for example `work/<target>/base/`, `work/<target>/mod/`, and `work/<target>/analysis/`.
- Do not mix source/reference files with modified files. Baseline copies, modified copies, analysis outputs, and release/build outputs must live in clearly separate folders.
- Do not repeatedly disassemble the same binary from scratch when a preserved analysis workspace is available; reuse and update the relevant `work/<target>/analysis/` materials.
- State explicitly what software/tools were used for a task. If the right tool is uncertain or missing, ask the user to provide or approve one.
- Prefer reusable, verifiable commands and scripts over long one-off command chains. Keep closely related implementation together when that is clearer than introducing additional files.

## Release / milestone rules

For file-level translation releases, one zip only. Zip filename gets version/postfix. Internal filenames must be exactly:

- `BTL.BIN`
- `ETC.bin`
- `SLPS_258.37`
- `translation_log.tsv`

No postfixes inside the zip. Never include `ADV.bin` unless explicitly requested.

For full project milestones, place new frozen files in `releases/` with clear version/postfix names. Active working ISOs stay in `build/`.

`releases/` is append-only/frozen. Do not rewrite, rename, move, delete, or modify existing release files or folders. If the intended output name already exists, stop and inspect manually instead of choosing a workaround.

Release PNACH files are coupled to the boot ELF CRC of their paired ISO. Always verify the PNACH CRC suffix against the ISO's actual PCSX2 game CRC before treating a release as valid. If verification is unavailable or inconclusive, report that uncertainty clearly.


## Actualize workflow

The root command interface is: bare `na2` builds the current profile, conditionally rotates a changed ISO, and launches `Current.iso`; `na2 -c` launches `Current.iso` without rebuilding; `na2 -p` launches `Previous.iso` without rebuilding; `na2 act` actualizes `Current.iso` without launching. No other public build, path-override, hash-bypass, or launch-bypass arguments are supported. `_na2.ps1` owns only public dispatch and transcript management; `scripts/na2/build.ps1` owns profile build and ISO promotion/rotation; `na2_patcher/build_profile.py` owns profile-only ISO composition and verification; `scripts/na2/launch.ps1` owns mandatory PNACH actualization, enabled-cheat logging, and PCSX2 launch. Do not recombine these responsibilities or restore direct newest-package selection.

When asked to actualize, keep the canonical file named `@pcsx2_files/SLPS-25837_C0659AD1.pnach`. Managed aliases are only matching-serial symlinks that resolve to this canonical file; preserve all real PNACH files, other games, and unrelated symlinks. If the canonical file is zero bytes, delete its managed aliases directly and skip ISO/CRC inspection. Otherwise, use the ISO in `@build/` by default, calculate the PCSX2-style ELF CRC from its boot ELF, delete obsolete managed aliases, and create the current CRC-named relative symlink targeting the canonical project PNACH if missing. Refuse an occupied target filename instead of overwriting an unmanaged file or symlink.

Before handing off or launching any ISO, run actualization for that exact ISO. For a non-empty canonical PNACH, verify that the resulting CRC-named symlink exists; for a zero-byte canonical PNACH, verify that its managed aliases are absent. Do not skip this step unless the user explicitly requests a no-PNACH isolation run.

Before launching PCSX2, log enabled cheat names from uncommented PNACH `patch=` or setting lines. Metadata-only lines do not count; report `none` when there are no enabled cheats.

Before rebuilding or launching a test ISO, unconditionally issue the close command for the configured `@pcsx2/pcsx2-qt.exe`. Do not probe first to see whether PCSX2 is running; closing an absent process should be treated as a harmless no-op.

If an agent launches PCSX2 for testing, it must use `scripts/na2/test_launch.ps1`. The wrapper temporarily mutes PCSX2, starts it hidden without intentionally activating it, re-hides any exposed window, restores the previous foreground window if PCSX2 took focus, closes the test instance after the validation window, and restores the original audio setting even when testing fails. Normal user launches remain unchanged.

## Task report format

For completed `TASKS.md` tasks, report files read, files created/modified, whether originals were untouched, scripts/commands used, sizes, and uncertainties. This format does not apply to small direct changes.
