# AGENTS.md

PS2 modding/reverse-engineering workspace for Naruto Shippuuden: Narutimate Accel 2 / SLPS-25837.

## Hard rules

- Never change binary files manually.
- All binary changes must go through scripts.
- Preserve file sizes unless explicitly instructed.
- Do not modify files under `source/` unless explicitly instructed.
- Keep untouched source media under `source/`.
- Keep extractions of original media beside the source archive as `<archive filename>.files`.
- Treat everything under `source/`, including extracted files, as read-only reference material.
- Do not create generated files, temporary files, logs, probes, manifests, or metadata under `source/`; preserve the extracted game/archive structure exactly.
- Keep Windows read-only attributes applied to files/folders under `source/`.
- Before changing any original-derived file, copy it outside `source/` and modify only the copy.
- Keep active working outputs under `build/`.
- Keep frozen milestone artifacts under `releases/` (`C:\Users\solid\Documents\Mods\NA2\releases`).
- Never alter, overwrite, rename, move, or delete anything under `releases/`.
- Only create new uniquely named milestone outputs under `releases/`.
- If a target path under `releases/` already exists, stop immediately and inspect/report manually.
- Every release PNACH must correspond to the PCSX2 CRC of the ELF inside the paired release ISO.
- Before reporting a release as valid, check the paired ISO/ELF CRC against the PNACH filename and warn if they do not match or cannot be verified.
- Keep logs, inventories, hashes, and patch records under `logs/`.
- Keep deleted/retired workspace items under `trash/` instead of hard-deleting when practical.
- Use `scripts/move_to_trash.ps1` for project-local removals; it must refuse `source/`, `releases/`, and `trash/`.
- Generated/intermediate files go under `build/`, `logs/`, `scripts/`, or root `temp/` with task-named subfolders when throwaway workspace is needed. Original-source extractions are the only exception and stay beside their source archive under `source/` as `<archive filename>.files`.
- Treat top-level `old/` as the user's personal folder. Do not inspect, search, execute from, modify, move, delete, or otherwise touch it unless explicitly instructed.
- Treat `utils/old/` as an untrusted tool/archive dump. Do not execute tools from it until inspected and chosen for a specific task.
- Log every binary patch: file, offset, original bytes, new bytes, reason.
- PNACH is the single source of truth for cheats. `// [Name]` is only a label/comment; a cheat is enabled only when its executable `patch=`/setting line is uncommented. Disabled proven cheats and disabled hypotheses must have their executable lines commented out.
- Keep active PNACH files clean: confirmed named sections only, plus temporary hypothesis patches at the very top when actively testing.
- Temporary PNACH hypothesis patches go at the top of the file as comment-only names plus disabled `// patch=` lines; uncomment them only while actively testing.
- Move old candidates, failed experiments, and speculative addresses to `HYPOTHESES.md`.
- Track concrete active plans and queued investigations in `TASKS.md`, not general rules or PNACH comments.
- For string patches, always check encoded byte length before writing.
- Prefer Shift-JIS / CP932-compatible text unless proven otherwise.
- DATA.CVM password is `cc2fuku`.
- Do not expand DATA.CVM, ELF, BIN, AFS, CCS, or ISO structures unless explicitly instructed.
- Do not include `ADV.bin` in release builds unless explicitly requested.
- Do not delete/rename PSS files blindly.
- Avoid GUI-only workflows when CLI/scripted alternatives exist.
- Ask before destructive actions, mass rewrites, ISO rebuilds, or modifying originals.
- If uncertain, inspect and report instead of acting.


## Workspace creation rules

- New root folders are allowed when useful, but every new root folder must be described in `AGENTS.md` and `PROJECT_CONTEXT.md` and contain a `.gitkeep` unless it is intentionally untracked/generated.
- Use root `temp/` for throwaway/intermediate work only. Clean task subfolders there after failed or finished experiments when they are no longer useful.
- Use root `work/` for persistent reverse-engineering and binary-mod work. Keep work separated by target/task, for example `work/<target>/base/`, `work/<target>/mod/`, and `work/<target>/analysis/`.
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

For full project milestones, place new frozen files in `release/` with clear version/postfix names. Active working files stay in `build/`.

`releases/` is append-only/frozen. Do not rewrite, rename, move, delete, or modify existing release files or folders. If the intended output name already exists, stop and inspect manually instead of choosing a workaround.

Release PNACH files are coupled to the boot ELF CRC of their paired ISO. Always verify the PNACH CRC suffix against the ISO's actual PCSX2 game CRC before treating a release as valid. If verification is unavailable or inconclusive, report that uncertainty clearly.


## Actualize workflow

When asked to actualize, use the ISO in `build/` by default. Calculate the PCSX2-style ELF CRC from the boot ELF inside that ISO. Keep the base file named `cheats/SLPS-25837_C0659AD1.pnach`. Create the CRC-named symlink `cheats/SLPS-25837_<crc>.pnach` to `cheats/SLPS-25837_C0659AD1.pnach` if missing. Never delete old CRC links during actualize.

## Current release file list

Keep the live release list in `RELEASE_FILES.md`. Current release contents are `BTL.BIN`, `ETC.BIN`, boot ELF `SLPS_258.37`, and the actualized PNACH. Ask for release name and confirm file list/ISO before creating a release. Then actualize and copy files into `releases/<release_name>/` without overwriting existing paths.
## Report format

Report files read, files created/modified, whether originals were untouched, scripts/commands used, hashes/sizes, and uncertainties.






