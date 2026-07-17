# AGENTS.md

PS2 modding/reverse-engineering workspace for Naruto Shippuuden: Narutimate Accel 2 / SLPS-25837.

## Hard rules

- Use only repository-relative paths in canonical project files, scripts, configuration, logs, manifests, metadata, and generated artifacts; never persist machine-specific absolute paths there. Absolute paths are permitted only in dated `.agents/` handoffs as non-authoritative migration context, transient in-memory command arguments or diagnostic output when a tool requires them, and user-facing clickable file links. Do not persist an absolute path anywhere else unless the user explicitly authorizes that specific exception.
- The task workflow and its approval gates apply only to selected work from `TASKS.md`. Perform small, direct, low-risk changes immediately without a plan, intelligence-level recommendation, or approval gate; keep them in the current changeset unless the user says otherwise.
- For a selected task, only read-only inspection is allowed before plan approval. Only a standalone exact ASCII response of `approved` or `qwe` authorizes changes. A second standalone exact approval after result review authorizes task deletion, commit, and push.
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
- Keep only the active working ISO under `build/`, normally `build/Current.iso`; do not store PNACH files, loose replacements, logs, or other working files there. During a build, `build/Current.iso.building` is the only standard temporary ISO and must be removed on failure or atomically promoted on success.
- Temporary, parity-check, and hypothesis-test ISOs may remain under `build/` while they have a concrete future testing or comparison use. Permanently delete them as soon as they become useless; never leave obsolete ISOs accumulating under `build/`.
- Do not recreate a top-level `packages/` staging/history directory. Normal builds consume hash-pinned profile modules. Keep temporary imported archives under a task-specific `work/temp/` folder, normalize useful data into a module, then retire the archive to `trash/`.
- Do not recreate a top-level `milestones/` package archive directory. Keep immutable reproducible module data under `na2_patcher/milestones/` or as a hash-pinned declarative patch set beside its module; retain retired package archives only in Git history.
- New translation milestones freeze immutable canonical mapping data plus a hash-pinned profile; the integrated translation engine is versioned with the repository. Legacy translation builder archives are retained only in Git history. Generated translation TSVs are compatibility run outputs, not milestones.
- Treat `na2_patcher/modules/translation/mappings.tsv` as the translation module's current versioned input. Profiles may reference it only with an exact content hash; changing it requires updating the profile pin as an explicit translation version change.
- `na2 tr` is a compatibility/review export interface. The normal profile workflow invokes the translation module directly and records its generated plan and summary under the profile run log.
- Keep frozen milestone artifacts under the ignored root `releases/` relative link.
- Never alter, overwrite, rename, move, or delete anything under `releases/`.
- Only create new uniquely named milestone outputs under `releases/`.
- If a target path under `releases/` already exists, stop immediately and inspect/report manually.
- Every release PNACH must correspond to the PCSX2 CRC of the ELF inside the paired release ISO.
- Before reporting a release as valid, check the paired ISO/ELF CRC against the PNACH filename and warn if they do not match or cannot be verified.
- Keep logs, inventories, hashes, and patch records under task-specific subfolders of `logs/`; do not write files directly in the `logs/` root.
- Keep deleted/retired workspace items under `trash/` instead of hard-deleting when practical.
- Use `scripts/move_to_trash.ps1` for project-local removals; it must refuse `@source/`, `@releases/`, and `@trash/`.
- Generated/intermediate files go under `@logs/`, `@scripts/`, or `@work/temp/` with task-named subfolders when throwaway workspace is needed. Completed working ISOs are the only outputs kept under `@build/`. Original-source extractions stay beside their source archive under `@source/` as `<archive filename>.files`.
- Treat top-level `old/` as the user's personal folder. Do not inspect, search, execute from, modify, move, delete, or otherwise touch it unless explicitly instructed.
- Treat `@utils/old/` as an untrusted tool/archive dump. Do not execute tools from it until inspected and chosen for a specific task.
- Log every binary patch: file, offset, original bytes, new bytes, reason.
- PNACH is the source of truth only for emulator settings, runtime-only memory patches, and temporary hypotheses that cannot yet be represented as file-backed module edits. Permanent file-backed changes belong in named `na2_patcher` raw-binary patch sets and must not remain enabled in PNACH. `// [Name]` is only a label/comment; a PNACH item is enabled only when its executable `patch=`/setting line is uncommented.
- Use fixed-address PNACH writes for hypothesis testing only when the target is in the boot ELF or another region proven to remain resident and stable for the entire write lifetime.
- Never apply an unguarded fixed-address PNACH write to `BTL.BIN`, `ETC.BIN`, or another module that is loaded and unloaded on demand; the same EE address may hold unrelated data while that module is absent. Test those hypotheses by patching the file through scripts, rebuilding the ISO, and recording the result.
- Runtime overlay PNACH testing is exceptional and requires a proven load-state/signature guard. Avoid fixed writes to dynamic heap objects unless their allocation, address, and lifetime are established.
- Keep active PNACH files clean: confirmed named sections only, plus temporary hypothesis patches at the very top when actively testing.
- Temporary PNACH hypothesis patches go at the top of the file as comment-only names plus disabled `// patch=` lines; uncomment them only while actively testing.
- Move old candidates, failed experiments, and speculative addresses to `docs/HYPOTHESES.md`.
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
2. After a successful push—or whenever the user asks what is next—the agent reads `TASKS.md`, summarizes the relevant `In Progress` and `Backlog` choices, and asks the user to select one.
3. The agent may perform read-only inspection, then gives a short plan, recommends an intelligence level, and ends with **Awaiting plan approval**.
4. Only an exact standalone ASCII `approved` or `qwe` authorizes changes.
5. The agent executes freely within the approved task, including major changes.
6. If the task becomes unclear or the whole approach is wrong, stop and clarify; a replacement plan needs approval.
7. The agent reports the result.
8. Only another exact standalone ASCII `approved` or `qwe` authorizes task deletion, commit, and push.
9. The user's concurrent edits and commits are expected. The agent preserves them, refreshes Git state before Git operations, and may push the user's existing commits with its own.
10. Queued instructions remain part of the same changeset unless the user says otherwise.


## Cross-install Codex handoffs

- `.agents/` is intentional handoff infrastructure shared by separate Windows installations and Codex instances. Do not delete, ignore, or classify it as disposable clutter without reviewing its contents.
- Handoffs are dated context snapshots, not canonical configuration. Live repository state, `AGENTS.md`, current docs, and the user override them.
- Machine-specific paths and task IDs are permitted inside dated handoffs only because they describe the originating installation; never copy them into active scripts or manifests.

## Workspace creation rules

- `docs/` contains repository-wide context, plans, hypotheses, and release documentation. Keep component-specific READMEs beside their components.
- Use `work/temp/` for throwaway/intermediate work only. Clean task subfolders there after failed or finished experiments when they are no longer useful.
- Use `work/` outside `work/temp/` for persistent reverse-engineering and binary-mod work. Keep work separated by target/task, for example `work/<target>/base/`, `work/<target>/mod/`, and `work/<target>/analysis/`.
- Do not mix source/reference files with modified files. Baseline copies, modified copies, analysis outputs, and release/build outputs must live in clearly separate folders.
- Do not repeatedly disassemble the same binary from scratch when a preserved analysis workspace is available; reuse and update the relevant `work/<target>/analysis/` materials.
- State explicitly what software/tools were used for a task. If the right tool is uncertain or missing, ask the user to provide or approve one.
- Prefer short, reusable command/script chunks over long multi-stage one-off commands. Break repetitive work into scripts or small verifiable steps.

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

When asked to actualize, use the ISO in `build/` by default. Calculate the PCSX2-style ELF CRC from the boot ELF inside that ISO. Keep the base file named `cheats/SLPS-25837_C0659AD1.pnach`. Delete obsolete `cheats/SLPS-25837_<crc>.pnach` symbolic links directly, without moving them to trash, then create the current CRC-named symlink to `cheats/SLPS-25837_C0659AD1.pnach` if missing. Never delete the canonical PNACH or any real PNACH file during actualize.

Before handing off or launching any ISO, actualize the PNACH alias for that exact ISO and verify that the resulting CRC-named symlink exists. Do not skip this step unless the user explicitly requests a no-PNACH isolation run.

Before rebuilding or launching a test ISO, unconditionally issue the close command for the project-local `pcsx2/pcsx2-qt.exe`. Do not probe first to see whether PCSX2 is running; closing an absent process should be treated as a harmless no-op.

## Task report format

For completed `TASKS.md` tasks, report files read, files created/modified, whether originals were untouched, scripts/commands used, sizes, and uncertainties. This format does not apply to small direct changes.
