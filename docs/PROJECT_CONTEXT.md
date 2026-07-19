# Project Context

The modified project game is named *Narutimate Accel v2.28*. It is based on
*Naruto Shippuuden: Narutimate Accel 2*, whose clean source identity remains
`SLPS-25837`.

## Stable Local References

Original source ISOs are `@source/NA2.iso`, `@source/NUN3.iso`,
`@source/NUN5.iso`, and `@source/NUN6 A35.iso`. NUN6 A35 is a Brazilian mod of
NUN5, not an official successor. It is retained as a feature donor because it
contains many modifications that may later be ported to NA2.

Current PNACH:

- Canonical editable PNACH base: `@pcsx2_files/SLPS-25837_C0659AD1.pnach`
- The modified project image uses `SLPS-22228`; its actualized PNACH symlinks live in `@pcsx2/cheats/SLPS-22228_<crc>.pnach` and point to `@pcsx2_files/SLPS-25837_C0659AD1.pnach`. The canonical PNACH keeps its historical source-game name.
- Former PNACH sections preserved as raw-binary patch sets are `Testing`, `Rendering`, `QoL`, and `Battle logic`. Patches are cheats, edits are subcheats, and `default_enabled` preserves state. Rendering is currently an empty disabled module in the active profile.
- PNACH actualization is mandatory before every ISO handoff or launch unless the user explicitly requests a no-PNACH isolation run.
- A zero-byte canonical PNACH removes its managed PCSX2 CRC aliases and skips ISO/CRC inspection. Managed aliases are matching-serial symlinks that resolve to this canonical file; other games, real PNACH files, and unrelated symlinks are preserved.
- `@pcsx2_files/` contains the Git-tracked canonical PNACH, project input recordings, and ignored local screenshots. The actualizer manages CRC-named relative symlinks under `@pcsx2/cheats/`.
- Every normal PCSX2 launch logs enabled named cheats from uncommented `patch=` or setting lines, or `none` when no cheats are enabled.
- PNACH labels such as `// [Skip CC2 intro]` are comments only. A cheat is enabled only when its executable `patch=`/setting line is uncommented. Disabled proven cheats and disabled hypotheses must keep their executable lines commented out. Temporary PNACH hypothesis patches go at the top as comment-only names plus disabled `// patch=` lines; uncomment them only while actively testing.
- Fixed-address PNACH hypotheses are safe by default only for the boot ELF or another region proven to remain resident and stable for the entire write lifetime.
- `BTL.BIN`, `ETC.BIN`, and other on-demand modules are loaded and unloaded into reusable EE memory. Never test them with unguarded fixed-address PNACH writes: patch the file through the raw-binary module, rebuild the ISO, and test that build instead.
- A runtime overlay PNACH write is permitted only with a proven load-state/signature guard. Dynamic heap targets require a proven allocation, address, and lifetime.

## Working Layout

Directory roots are configured once in `project-paths.json`; see
`docs/PROJECT_PATHS.md`. The `@root/...` notation below is logical and must not be
replaced with a copied machine-specific absolute path.

- `@source/`: untouched source media. Do not modify unless explicitly instructed. No generated logs, temp files, probes, manifests, or metadata belong here.
- `@source/*.files/`: extracted views of original source archives. Treat as read-only reference.
- `build/`: normally contains `build/NA2.28 - Current.iso` and may retain at most `build/NA2.28 - Previous.iso` as rotation history. Standard builds use `build/NA2.28 - Current.iso.building` in the same directory and delete it on caught failure. After verification and log creation, a byte-identical candidate is discarded without changing the current or previous ISO; a changed candidate rotates the current ISO to the configured previous path and becomes the new current ISO. Other temporary, parity-check, and hypothesis-test ISOs may remain while they have a concrete future testing or comparison use, but are permanently deleted as soon as they become useless.
- There are no top-level `packages/` or `milestones/` archive directories and no `na2_patcher/milestones/` snapshot tree. Temporary imported archives live under task-specific `work/temp/` folders until normalized or retired. Reproducible data lives as hash-pinned inputs beside its module; complete accepted states are preserved by annotated Git tags, and retired archives remain available through Git history.
- `na2_patcher/modules/translation/mappings.tsv` is the translation module's current hash-pinned v34 input. The current profile invokes the translation engine directly and records its plan under the profile run log; no standalone export or source-hash bypass exists. All legacy translation builder archives have been retired from the workspace after exact profile parity and remain available through Git history.
- `releases/`: ignored relative link to the frozen release archive outside the repository. It contains binary release artifacts only; never alter existing contents.
- `logs/`: disposable execution records grouped into task-specific subfolders; no files should be written directly in the `logs/` root. `na2` keeps `logs/na2/latest.log` plus one `rolling.log` capped at the newest 20 completed operational invocations. Structured profile records under `logs/na2/builds/` are retained only for the configured current and previous ISO files; one atomically replaced `logs/na2/builds.tsv` maps both ISO names to their records. See `docs/LOGGING.md`.
- `scripts/`: repeatable tooling.
- `@pcsx2_files/`: project-owned PCSX2 artifacts. The canonical PNACH and input recordings are tracked; screenshots remain local and ignored.
- `@pcsx2/`: portable, self-contained PCSX2 installation. BIOS, memory cards, logs, saves, settings, and other support data stay inside this root. Its game-list media paths may point to `@build/` and `@source/`; its CRC-named cheat symlinks target the canonical PNACH under `@pcsx2_files/`.
- `na2_patcher/modules/raw_binary/`: repository-owned schema v1, CLI validator/patcher, the exact font m01 reconstruction, canonical menu-input mappings and runtime classifications, the UI translation's paired OUGI code edit, and verified historical font ELF patch groups. It never applies `pending`, `runtime_failed`, or `deprecated` patches and writes only new same-size outputs with complete logs. The main ISO compositor applies all modules in explicit profile order with staged-byte conflict checks.
- `na2_patcher/modules/ui_textures/`: hash-pinned, source-derived fixed-size CCS container imports from the official NUN5 donor. It stores no replacement blobs: 32 whole strategies derive complete donor payloads, while mapped `MAPSEL1.CCS` preserves NA2's stage-picture structure and mapped `MODE2KDV.CCS` preserves its portrait/palette/lower rows. Profile hashes cover the three canonical TSV recipes, not generated replacements, parser code, or documentation.
- `na2_patcher/`: profile schemas, ordered module orchestration, hash-pinned module data, and the translation/raw-binary/UI-texture/disc-identity implementations. `na2_patcher/profiles/current/` enables the font, menu-input, QoL, battle-logic, string-replacement, text translation, UI-texture, paired UI-code, and disc-identity modules by exact executable-input hashes. Raw-binary and UI-texture hashes exclude adjacent READMEs and engine code; the complete committed checkpoint pins the integrated implementation. The disc-identity module runs last and performs the declared equal-length `SLPS_258.37` to `SLPS_222.28` boot-path rename.
- `.agents/`: dated human-readable handoffs exchanged between separate Windows installations and Codex instances. They may contain machine-specific paths as historical context, are non-authoritative, and must be reviewed rather than deleted as clutter.
- `docs/`: repository-wide context, confirmed knowledge, active plans, hypotheses, and release documentation. Component-specific READMEs remain beside their components.
- `docs/knowledge/`: confirmed findings, reusable negative results, and supporting evidence promoted out of disposable logs. Module-owned structured evidence remains beside its module.
- `docs/LOGGING.md`: log contents, bounded retention, cleanup, and knowledge-promotion policy.
- `docs/HYPOTHESES.md`: archived patch candidates, failed experiments, unverified addresses, and speculative leads.
- `TASKS.md`: concrete active tasks, test plans, and queued investigations only; no general workflow rules.
- `work/temp/`: ignored throwaway/intermediate workspace, organized into task-named subfolders and cleaned when no longer useful.
- `old/`: user's personal folder. Off-limits unless explicitly instructed.

Scratch/intermediate folders should be created only when needed under `@work/temp/`, with names tied to the task. Extractions of original source archives stay beside the source archive under `@source/`.
For binary modding, prefer persistent target folders under `work/` over repeated fresh disassembly. State the tools/software used for each change, and keep command chunks short and reusable.
See non-tracked folders in gitignore, need to be recreated if starting anew.

## Codex Task Separation

Use separate Codex tasks against the same real project root:

- Coordination / build workflow: repository structure, `na2`, profiles, actualize, releases, and cross-task integration.
- GF4 font rendering: GF4/GF4C assets, NA2/NUN5 renderer comparison, metrics, positioning, and auto-fit logic.
- Translation: maintain mappings, validate module/profile compatibility, and investigate translation issues without bypassing the hash-pinned profile workflow.
- Logic / PNACH: gameplay patches and reverse engineering unrelated to font or translation work.

All tasks must read `AGENTS.md`, `docs/PROJECT_CONTEXT.md`, `TASKS.md`, and `docs/HYPOTHESES.md` before acting. Binary outputs and experiments remain shared, so each task must re-check Git status and current package/build state before modifying files.

## Extraction Layout

All extracted original files stay under `@source/`, beside the archive they came from.

Canonical ISO extraction layout:

- `@source/NA2.iso`
- `@source/NA2.iso.files/`
- `@source/NUN3.iso`
- `@source/NUN3.iso.files/`
- `@source/NUN5.iso`
- `@source/NUN5.iso.files/`
- `@source/NUN6 A35.iso`
- `@source/NUN6 A35.iso.files/`

Nested archive convention:

- Keep the archive file at its natural path in the extracted tree.
- Put that archive's extracted contents beside it in a sibling folder named `<archive filename>.files`.
- Repeat the same rule for archives inside archives.

Example:

```text
original/
  NA2.iso
  NA2.iso.files/
    SYSTEM.CNF
    SLPS_258.37
    DATA/
      DATA.CVM
      DATA.CVM.files/
        ...
      SOUND.AFS
      SOUND.AFS.files/
        ...
    PRG/
      BTL.BIN
      ETC.BIN
```

For edited/build versions, do not edit anything under `@source/` in place. Copy the needed file or archive into a task/build folder first, then patch that copy through scripts and log the source path and output path. If extraction or inspection needs metadata, write it under `@logs/` using source-relative paths instead of placing files in `@source/`.

Use `scripts/media/extract_source_iso.ps1` for a new canonical extraction. It
stages the work under `@work/temp/`, recursively expands CVM, inner ISO, AFS,
and nested AFS containers, verifies file sets and byte contents, normalizes
timestamps from archive metadata or deterministic container fallbacks, then
promotes exactly one `<ISO filename>.files` tree. It refuses to merge into an
existing tree. Use `scripts/media/verify_extraction.py` to recheck an existing
tree.

The active `@source/` ISOs and extraction trees have Windows read-only
attributes applied. Use `scripts/project/set_source_readonly.ps1 -SourceDir`
with one explicit active ISO extraction tree after adding new original-source
content or when attributes need to be restored. The script refuses the whole
source root and anything under `@source/__old/`.

## DATA.CVM Extraction

Confirmed ROFS/CVM passwords:

- NA2, NUN3, and NUN5: `cc2fuku`
- NUN6 A35: `Iruka`

Current split/extraction outputs:

- `@source/NA2.iso.files/DATA/DATA.CVM.files/DATA.CVM.iso`
- `@source/NA2.iso.files/DATA/DATA.CVM.files/DATA.CVM.hdr`
- `@source/NA2.iso.files/DATA/DATA.CVM.files/DATA.CVM.iso.files/`

Use `scripts/media/split_cvm_rofs.ps1` to split the encrypted CVM safely without running `@utils/old/CVM Parser/cvm_tool.exe`.

## Current Scripts

- Root `_na2.ps1` is the only routine user-facing entrypoint. Bare `na2` builds the pinned current profile, rotates only when the verified candidate differs, actualizes the Current PNACH alias while retaining the Previous alias, and launches `NA2.28 - Current.iso`. `na2 -c`, `na2 -p`, and `na2 -un5` are pure launch selectors: they do not rebuild, terminate an existing PCSX2 instance, or change PNACH aliases. `na2 act` performs the same Current/Previous alias maintenance without building or launching.
- `scripts/na2/` contains build/promotion, mandatory PNACH actualization, PCSX2 process/launch handling, CRC diagnostics, and the agent-only hidden/muted launch test. Build transcripts explicitly report `ISO result: unchanged` or `ISO result: updated` and the rotation result.
- `na2_patcher/build_profile.py` is the profile-only ISO compositor. It applies one explicit hash-pinned profile, rejects all file-size changes, verifies the complete staged ISO, writes the profile log, and leaves `NA2.28 - Current.iso.building` for PowerShell promotion.
- `scripts/media/` contains the recursive source extractor, its byte-parity
  verifier, and focused ISO, AFS, and CVM building blocks. Direct same-size ISO
  replacement survives only as an unsupported reference under
  `scripts/archive/`.
- `scripts/project/` contains configured-source read-only maintenance. There is currently no maintained release-creation script; the release workflow will be redesigned before new automation is added.
- `scripts/archive/` contains unsupported historical reference implementations. Inspect and explicitly select one before use; archived scripts are never part of the normal workflow.
- `scripts/research/menu_input/` and `scripts/research/translation/` retain useful one-off analysis tools outside the normal build path. Their lack of runtime callers does not make them disposable.
- See `scripts/README.md` for the maintained directory contract and individual responsibilities.

## Utils Dump

Top-level `old/` is personal user space and should not be inspected, searched, executed from, modified, moved, deleted, or otherwise touched unless the user explicitly asks for it.

`@utils/old/` is an untrusted historical tool/archive dump. It may contain useful tools or source references, but nothing there should be treated as current workflow or executed blindly.

Observed examples include AFS tools, CCS tools, Ghidra/EmotionEngine material, Kuriimu, PS2Dis, PSS tools, StudioCCS variants, and many unknown `.bin` files. Inspect and select a tool for a specific task before using it.

## Release Folder Rule

`releases/` is for release artifacts only. Existing contents are frozen.

Allowed:

- Create a new uniquely named release file/folder.

Not allowed:

- Modify an existing release file.
- Overwrite an existing release file.
- Rename, move, or delete anything under `releases/`.
- Auto-pick a different name after a collision.

If an intended `releases/` output path already exists, stop immediately and inspect/report manually.

Every release PNACH must match the PCSX2 CRC for the boot ELF inside the paired release ISO. Before calling a release valid, check the ISO/ELF CRC against the PNACH filename suffix. If the CRC does not match, warn. If it cannot be verified, say so explicitly.

## CRC / PNACH Notes

PCSX2 cheat filenames include the game CRC, for example:

`SLPS-22228_BCB73695.pnach`

If the boot ELF inside the ISO changes, PCSX2 may report a different CRC. Actualize derives the serial from the ISO boot path and creates a matching `@pcsx2/cheats/SLPS-22228_<crc>.pnach` link to `@pcsx2_files/SLPS-25837_C0659AD1.pnach` for the modified project image.

PCSX2 uses its internal `@pcsx2/cheats/` folder. Only the canonical PNACH is tracked in the project; actualized CRC aliases are relative symlinks in the portable installation.

Known PCSX2 paths from prior notes:

- Log: `@pcsx2/logs/emulog.txt`
- Cheats: CRC aliases in `@pcsx2/cheats/`, targeting the canonical `@pcsx2_files/SLPS-25837_C0659AD1.pnach`

Known log pattern:

Original-source historical pattern:

`ELF Loading: cdrom0:\SLPS_258.37;1, Game CRC = 870F8722, EntryPoint = 0x00100008`

Modified-project pattern after the disc-identity module:

`ELF Loading: cdrom0:\SLPS_222.28;1, Game CRC = <crc>, EntryPoint = 0x00100008`

## Prior GPT Handoff Notes

The following are transferred notes/hypotheses from earlier ChatGPT work. Treat them as leads, not verified facts, unless re-confirmed locally.

Original observed PCSX2 CRC from prior notes: `C0659AD1`

File role hypotheses:

- `SLPS_258.37`: main PS2 ELF/executable. May contain code and embedded strings. Replacing it can change PCSX2 Game CRC.
- `BTL.BIN`: battle/practice data. Claimed to contain battle UI/practice/settings strings.
- `ETC.bin`: misc/extras/collection/shop-ish data. Claimed to contain collection/shop/extras strings, item names, some jutsu/location/name/title strings.
- `ADV.bin`: adventure/master/story-ish data. Prior translated ADV reportedly crashed; do not include or modify unless explicitly requested.
- `GF4.BIN`, `GF4C.BIN`, `GRF4.BIN`, `SF1.BIN`, `SF1C.BIN`: likely graphics/font/resource containers; not confirmed safe string targets.
- `logo.ccs`: likely startup/logo texture/animation data, not normal string translation.
- PSS files: movie/video files. Do not delete/rename blindly.
- AFS files: archives, not directly playable audio streams. Extract first, then inspect contained files.

Prior package mentioned:

- `narutimate_translation_latest_all_v6_substantial.zip`
- Claimed contents: `BTL.BIN`, `ETC.bin`, `SLPS_258.37`, `translation_v6_log.tsv`
- Claimed stats: 238 exact replacements, 14 offset-based replacements, 17 already-present strings.

Prior known PNACH patch notes:

- RPS Disable / Consume Circle
- Intro/logo PSS skip
- Opening skip

Prior warnings:

- Do not continue blind startup/logo PNACH guessing; prior static guesses reportedly caused black screens/hangs.
- Do not include `ADV.bin` unless explicitly requested.

## Translation Strategy

- Preserve byte budgets unless a pointer relocation/free-space strategy is explicitly developed.
- Use exact replacements where possible.
- Use offset-based replacements only when logged and justified.
- For string patches, check CP932/Shift-JIS byte length before writing.
- Some visible Japanese may be textures/CCS, not text.

## CVM Notes

DATA.CVM passwords: `cc2fuku` for NA2, NUN3, and NUN5; `Iruka` for NUN6 A35.

## Actualize Workflow

When asked to actualize, keep the canonical file named `@pcsx2_files/SLPS-25837_C0659AD1.pnach`. Managed aliases use the serial derived from the selected ISO boot path: normally `SLPS-22228` for the modified project image, or legacy `SLPS-25837` for an older/source-identity image. Preserve other games, real PNACH files, and unrelated symlinks. If the canonical file is zero bytes, delete managed aliases for both project serials directly and skip ISO/CRC inspection. Otherwise, use the ISO in `@build/` by default, calculate the PCSX2-style ELF CRC from its boot ELF, delete obsolete managed aliases, and create the current relative `@pcsx2/cheats/<serial>_<crc>.pnach` symlink targeting the canonical PNACH if missing. Refuse an occupied target filename instead of overwriting it.

## Release Workflow

Existing output under the root `releases/` link remains frozen and append-only. The former release-creation script and stale file-list document have been retired; release composition and verification will be redesigned before another automated release is created. Until then, stop and agree on a new release plan rather than reconstructing the retired workflow ad hoc.
