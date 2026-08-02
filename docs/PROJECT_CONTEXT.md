# Project Context

The modified project game is named *Narutimate Accel v2.28*. It is based on
*Naruto Shippuuden: Narutimate Accel 2*, whose clean source identity remains
`SLPS-25837`.

## Stable Local References

Original source ISOs are the `na2_iso`, `nun3_iso`, `nun5_iso`, and `nun6_iso`
project files. NUN6 A35 is a Brazilian mod of NUN5, not an official successor.
It is retained as a feature donor because it contains many modifications that
may later be ported to NA2.

NA2.28 PCSX2 configuration:

- Canonical serial-wide files are `@pcsx2_cheats/SLOP-NA228.pnach` and
  `@pcsx2_game_settings/SLOP-NA228.ini`. PCSX2 finds PNACH and GameSettings
  recursively. No CRC aliases are generated.
- Ordinary GameSettings sections apply to every CRC. Sections named
  `[CRC.<8-hex-crc>.<section>]` override the ordinary section for one CRC.
  Named PNACH groups apply to every CRC unless they contain
  `crc = <8-hex-crc>[,<8-hex-crc>...]`.
- Runtime C candidates bypass cheat files and are applied directly to
  task-owned PCSX2 memory through PINE.
- Former PNACH sections preserved as binary-patcher patch sets are `QoL` and `Battle logic`. Binary-patcher schema v4 organizes each package as groups, atomic patches, and exact edits; independent group and patch `enabled` switches control normal composition. The old `Testing` substitution edits were retired after their negative runtime results were promoted to `docs/knowledge/localization/substitution.md`.
- Builds and launches never synchronize PCSX2 identities. `workshop input`
  regenerates every Workshop input profile without changing GameSettings
  assignments; `workshop input <profile>` regenerates and assigns one profile.
- The serial-wide GameSettings fallback uses `NA v2.28.ps2`. CRC override
  sections preserve the current Latest, Previous, Manual Test, and Screenshot
  Test assignments to
  their existing role-specific memory cards.
- `@pcsx2_files/` contains the canonical BIOS, cheats, GameSettings, input
  profiles, input recordings, and memory cards used directly by stable and
  development PCSX2.
- PNACH labels such as `// [Skip CC2 intro]` are comments only. A cheat is enabled only when its executable `patch=`/setting line is uncommented. Disabled proven cheats and disabled hypotheses must keep their executable lines commented out. Temporary PNACH hypothesis patches go at the top as comment-only names plus disabled `// patch=` lines; uncomment them only while actively testing.
- Fixed-address PNACH hypotheses are safe by default only for the boot ELF or another region proven to remain resident and stable for the entire write lifetime.
- `BTL.BIN`, `ETC.BIN`, and other on-demand modules are loaded and unloaded into reusable EE memory. Never test them with unguarded fixed-address PNACH writes: patch the file through the binary-patcher module, rebuild the ISO, and test that build instead.
- A runtime overlay PNACH write is permitted only with a proven load-state/signature guard. Dynamic heap targets require a proven allocation, address, and lifetime.

## Working Layout

Directory roots are configured once in `paths.json`; see
`docs/PATHS.md`. The `@root/...` notation below is logical and must not be
replaced with a copied machine-specific absolute path.

- `@source/`: untouched source media. Do not modify unless explicitly instructed. No generated logs, temp files, probes, manifests, or metadata belong here.
- `@source/*.files/`: extracted views of original source archives. Treat as read-only reference.
- `build/`: normally contains `build/NA v2.28 - Latest.iso`, may retain at most `build/NA v2.28 - Previous.iso` as rotation history, and may retain `build/NA v2.28 - Manual Test.iso` and `build/NA v2.28 - Screenshot Test.iso` for isolated manual and visual testing. These names are derived from root `product.json`. Standard builds use `NA v2.28 - Latest.iso.building`, then discard an identical staged image or promote and rotate a changed one. Isolated builds atomically update only their named output, leave PCSX2 running, and never change Latest, Previous, their build mapping, or Latest's preflight receipt. Staging files are removed on failure.
- `work/<task title>/build/`: isolated agent ISOs produced by `na228 worker work/<task title>/build/<name>.iso`. Staging remains beside the requested output, build records remain under that task's `logs/`, and the mode never touches shared build, preflight, promotion, PNACH, or PCSX2 state.
- Temporary imported archives live under the active task's `work/<task title>/temp/` folder until normalized or retired. Reproducible data lives as hash-pinned inputs beside its module; complete accepted states are preserved by annotated Git tags, and retired inputs remain available through Git history.
- `na228_builder/features/localization/translation_importer/mappings.tsv` is the Localization feature's current hash-pinned importer input and folds the verified pointer inventory into each applicable mapping row. `source_ref` and `source` retain the guarded NA2 origin; `donor_ref` and `donor` retain the official translation and make it executable by default. A nonempty user-authored `replacement` overrides the donor, and `prefix` is prepended to the selected text. Root `product.json` owns the imported/output game titles, and the generic `string_patcher` applies that output policy before deriving inline or linked placement from encoded fit and available references. Feature-owned custom resident functions and guarded hooks are declared through `runtime_injector`; `payload_builder` links those fragments together with external strings into `PRG/228.BIN` and owns its loader/memory integration. The composer resolves symbols and `binary_patcher` applies concrete guarded writes. No standalone export or source-hash bypass exists.
- `@logs/`: disposable shared-workflow records; no files should be written directly in the root. `na228` keeps bounded Latest/Previous/Test provenance under `@logs/na228/`, and shared generated workstream evidence belongs under `@workstream_logs/<exact task title>/`. Agent ISO records instead stay under `work/<task title>/logs/`. See `docs/LOGGING.md`.
- `scripts/`: repeatable tooling.
- `@pcsx2_files/`: shared PCSX2 artifacts under
  `@workshop/pcsx2_shared/`.
- `@pcsx2_dev/`: the default user-facing PCSX2 runtime. Routine `na228`,
  multi-game launch, and savestate-filing commands use it unless `stable` is
  selected explicitly.
- `@pcsx2_stable/`: protected user-owned portable stable PCSX2 installation
  and state, retained for explicit compatibility and release checks. Agents
  never inspect, launch, or modify it without direct authorization.
- `@pcsx2_clean/`: protected immutable compiled worker template at the external
  PCSX2 checkout's `bin/` output. Agents copy it to
  `work/<task title>/pcsx2/` and may copy any assets for which they have a
  concrete task- or test-related reason from `@pcsx2_files` into the task-owned
  runtime. The source template is never populated, launched, or mutated.
- `work/<task title>/pcsx2/`: the exact workstream's private PCSX2 copy. The minimal hidden launcher starts only this copy; other PCSX2 processes are off-limits.
- `na228_builder/modules/binary_patcher/`: repository-owned schema v4 and reusable CLI validator/patcher for canonical group/patch/edit packages owned by features. The schema has no relations table; a patch is normally selected only when both its group and patch `enabled` switches are `1`. Selected edits are simulated in deterministic order so compatible overlaps and already-satisfied replacements are retained while real guard conflicts fail before ISO staging. It never applies `pending`, `runtime_failed`, or `deprecated` patches and writes only new same-size outputs with complete logs.
- `na228_builder/modules/runtime_injector/`: reusable declarative bridge for feature-owned code/data fragments, internal relocations, and guarded symbolic hooks. It contributes to the shared payload builder and compiles linked hooks into an in-memory binary-patcher package; it never chooses offsets or final addresses inside `PRG/228.BIN`.
- `na228_builder/modules/translation_importer/`: the reusable official-string importer engine. Localization-owned mappings and their pointer-reference inventory live under `na228_builder/features/localization/translation_importer/`.
- `na228_builder/modules/string_patcher/`: the reusable semantic string-placement engine. Localization has no feature-owned string-patcher directory or local declarations; its importer artifact invokes the engine as a derived consumer. The engine compiles inline imports and contributes external fragments/symbolic pointers without owning `228.BIN` layout. The memory-card title belongs to root `product.json`, not Localization.
- `na228_builder/modules/texture_patcher/`: the reusable fixed-size texture derivation engine. The Localization feature owns its 34 source-derived NUN5 UI recipes under `na228_builder/features/localization/texture_patcher/`; no replacement blobs are stored.
- `na228_builder/`: single-file profiles, reusable aggregate-hash-pinned feature packages, folder-derived module orchestration, artifact dependency composition, and reusable transformation engines. `na228_builder/profiles/default.tsv` explicitly lists every feature, its enabled state, pin, and bypass setting. Root `product.json` owns source inputs and final output identity. Feature rows define stable peer order; module directories define ownership and engine type; the composer resolves declared artifacts and closes typed operations. `payload_builder/` links shared resident code/data and global integration; `image_assembler/` alone performs ISO9660/UDF mutation and complete staged-image verification. Binary packages apply patches enabled by both group and patch switches and contain four canonical control tables plus referenced blobs. Adjacent READMEs, engine code, and non-input helpers are excluded from feature pins.
- Root `product.json` contains NA2 product identity, inputs, and build roles.
  Shared source games live in Workshop root `games.json`; non-secret commit
  identities and Notifications state live in Workshop `settings/`. Resumable
  agent state belongs to the owning
  `docs/workstreams/<workstream>/` tree.
- `docs/`: repository-wide context, confirmed knowledge, active plans, hypotheses, and release documentation. Component-specific READMEs remain beside their components.
- `docs/knowledge/`: confirmed findings, reusable negative results, and supporting evidence promoted out of disposable logs. Module-owned structured evidence remains beside its module.
- `docs/LOGGING.md`: log contents, bounded retention, cleanup, and knowledge-promotion policy.
- `docs/HYPOTHESES.md`: archived patch candidates, failed experiments, unverified addresses, and speculative leads.
- `TASKS.md`: concrete active tasks, test plans, and queued investigations only; no general workflow rules.
- `@ss/`: ignored NA2-local `work/__sstates/` library of user-managed savestates, screenshots,
  and related task inputs. Agents inspect it only to choose inputs, copy
  selected files into their own `work/<task title>/inputs/sstates/` tree with
  provenance, and never modify or clean the library itself.
- `work/<task title>/`: ignored workspace owned by that exact Codex task. `build/` and `logs/` contain isolated agent build/runtime records, supplied savestates are copied into `inputs/sstates/`, created savestates and captures belong under `artifacts/`, and `temp/` holds disposable caches. The shared top-level `work/temp/` directory is forbidden.

Scratch/intermediate folders should be created only when needed under the active task's `work/<task title>/temp/` folder. Extractions of original source archives stay beside the source archive under `@source/`.
For binary modding, prefer persistent target folders under `work/` over repeated fresh disassembly. State the tools/software used for each change, and keep command chunks short and reusable.
See non-tracked folders in gitignore, need to be recreated if starting anew.

## Codex Task Separation

Use separate Codex tasks against the same real project root:

- Coordination / build workflow: repository structure, `na2`, profiles, actualize, releases, and cross-task integration.
- GF4 font rendering: GF4/GF4C assets, NA2/NUN5 renderer comparison, metrics, positioning, and auto-fit logic.
- Translation: maintain mappings, validate module/profile compatibility, and investigate translation issues without bypassing the hash-pinned profile workflow.
- Logic / PNACH: gameplay patches and reverse engineering unrelated to font or translation work.

All tasks must read `AGENTS.md`, `docs/PROJECT_CONTEXT.md`, `TASKS.md`, and `docs/HYPOTHESES.md` before acting. Binary outputs and experiments remain shared, so each task must re-check Git status and default-profile/build state before modifying files.

## Extraction Layout

All extracted original files stay under `@source/`, beside the archive they came from.

Canonical ISO extraction layout:

- project file `na2_iso`
- `@source_na2/`
- project file `nun3_iso`
- `@source_nun3/`
- project file `nun5_iso`
- `@source_nun5/`
- project file `nun6_iso`
- `@source_nun6/`

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

For edited/build versions, do not edit anything under `@source/` in place. Copy the needed file or archive into a task/build folder first, then patch that copy through scripts and log the source path and output path. If extraction or inspection needs shared metadata, write it under the owning `@workstream_logs/<exact task title>/` folder using source-relative paths instead of placing files in `@source/`.

Use `scripts/project/extract_source_iso.ps1 -IsoPath <path> -TaskTitle <exact task
title>` for a new canonical extraction. It stages under the invoking task's
owned `work/<task title>/temp/source_extraction/` folder and never recreates
top-level `work/temp/`. It recursively expands CVM, inner ISO, AFS,
and nested AFS containers, verifies file sets and byte contents, normalizes
timestamps from archive metadata or deterministic container fallbacks, then
promotes exactly one `<ISO filename>.files` tree. It refuses to merge into an
existing tree. Use `scripts/project/verify_source_extraction.py` to recheck an existing
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

- `@source_na2/DATA/DATA.CVM.files/DATA.CVM.iso`
- `@source_na2/DATA/DATA.CVM.files/DATA.CVM.hdr`
- `@source_na2/DATA/DATA.CVM.files/DATA.CVM.iso.files/`

Use `@media_scripts/split_cvm_rofs.ps1` to split the encrypted CVM safely
without running `@tools/old/CVM Parser/cvm_tool.exe`.

## Current Scripts

- Root `na228.ps1` is the routine build/launch entrypoint. Bare `na228` builds and launches Latest. Compact invocations contain one or two positional game tokens whose order defines window placement: `l`, `p`, or `mt` runs Latest, Previous, or Manual Test; `bl` or `bmt` builds and runs Latest or Manual Test; and suffix `w` watches that token's game. The optional value after a watched token is a registered C file/folder or a task-owned overlay-plan path; with no value, the watcher attaches every registered source under `src/`. Trailing launch arguments are forwarded unchanged to Workshop, which alone parses shared launch options such as input-recording playback, recording, and regression capture. Explicit `build l|mt`, standalone `w [C path|plan]`, `worker`, `release`, and `help` remain available. Use `workshop input` to regenerate all shared input profiles without reassigning them, or `workshop input <profile>` to regenerate and assign one profile. Single-game configured launches preserve existing PCSX2 instances; two-game launches close configured user instances first, then select unused PINE ports and tile only their newly started windows. `na228 worker work/<task title>/build/<name>.iso` adds a full verified worker-output mode with task-owned staging/logs and no shared-state mutation; agents must use that form for builds.
- `scripts/na228/` contains build/launch execution, promotion, ISO identity,
  worker-path validation, and focused tests. Root `na228.ps1` owns argument
  parsing and dispatches substantive execution to `scripts/na228/run.ps1`.
- `@pcsx2_scripts/` contains PCSX2 launch, worker-runtime copying,
  configuration, and CRC helpers. `copy_worker.ps1` is the mandatory
  task-runtime creator and copies the clean template plus shared BIOS together.
  `launch.ps1` is the single configured and worker-PCSX2 launcher;
  configured launches default to `dev` and may select `stable` explicitly,
  while worker launches select an already-existing task-owned runtime with
  `-WorkerRoot`, use PCSX2 no-GUI mode, suppress process-owned render windows,
  and verify that the launched process owns no visible top-level windows.
  `-IsoPath` is optional for configured launches and mandatory for
  worker launches; `-PassThru` exposes the started process to higher-level
  orchestration. It performs no cloning, configuration, process inspection, or
  termination beyond the newly launched worker's hidden-state check, and
  configured multi-game orchestration passes the custom process-local
  `-pine-port` override so each process keeps an independent PINE endpoint
  without rewriting the persistent INI.
  performs no PINE operation, savestate handling, capture, or cleanup.
  Workshop is the public shared-launch parser used by direct `na228` game
  selectors; it forwards one or two ordered source/build selectors and shared
  launch options to `@pcsx2_scripts/launch_games.ps1`; and
  `savestates.ps1 move <game-or-alias> <subpath>` files only that selected
  game's development savestates by default, or stable savestates with
  `-Target stable`, under `@ss`; and
  `workshop ss extract <paths...>` extracts embedded `Screenshot.png`
  members into the source folder's `screenshots/` directory. One folder
  selects every direct `.p2s` and replaces that output directory; one or more
  explicit files from the same folder preserve unrelated outputs.
- The custom development PCSX2 PINE interface retains reload-patches opcode
  `0x10` and adds native screenshot `0x11`, synchronous pause `0x12`,
  synchronous resume `0x13`, and EE execution-cache refresh `0x14`. Direct
  injection uses pause/write/cache-refresh/resume and does not reload or
  transport candidates through patch or cheat files.
- `na228_builder/module_pipeline.py` prepares one explicit hash-pinned profile's artifacts, derived consumers, and shared payload contributions. `na228_builder/build_profile.py` applies that prepared pipeline and writes its run log. `na228_builder/composer.py` resolves module artifacts and closes typed image operations. `na228_builder/image_assembler/` alone stages, mutates, and verifies the caller-selected `.building` image for standard promotion, shared Test, or worker-owned output.
- `@media_scripts/` contains reusable ISO, AFS, and CVM extractors in Workshop.
  `scripts/project/` contains NA2 source-extraction orchestration, byte-parity
  verification, and configured-source read-only maintenance. Direct same-size
  ISO replacement is retired; guarded replacements belong to the hash-pinned
  `na228_builder.image_assembler` workflow.
- `scripts/research/menu_input/` and `scripts/research/translation/` retain useful one-off analysis tools outside the normal build path. Their lack of runtime callers does not make them disposable.
- See `scripts/README.md` for the maintained directory contract and individual responsibilities.

## Utils Dump

`@tools/old/` is an untrusted historical tool/archive dump. It may contain useful tools or source references, but nothing there should be treated as current workflow or executed blindly.

Observed examples include AFS tools, CCS tools, Ghidra/EmotionEngine material, Kuriimu, PS2Dis, PSS tools, StudioCCS variants, and many unknown `.bin` files. Inspect and select a tool for a specific task before using it.

## CRC / PNACH Notes

PCSX2 still reports the boot ELF CRC, but the NA2.28 cheat file is named only
`SLOP-NA228.pnach` and therefore survives CRC changes. Use group-level `crc =`
metadata only when a cheat is valid for specific CRCs.

Known PCSX2 paths from prior notes:

- Routine log: `@pcsx2_dev/logs/emulog.txt`
- Explicit stable-check log: `@pcsx2_stable/logs/emulog.txt`
- Cheats: `@pcsx2_cheats/SLOP-NA228.pnach`

Known log pattern:

Original-source historical pattern:

`ELF Loading: cdrom0:\SLPS_258.37;1, Game CRC = 870F8722, EntryPoint = 0x00100008`

Modified-project pattern after the profile identity is assembled:

`ELF Loading: cdrom0:\SLOP_NA2.28;1, Game CRC = <crc>, EntryPoint = 0x00100008`

## Prior GPT Handoff Notes

The following are transferred notes/hypotheses from earlier ChatGPT work. Treat them as leads, not verified facts, unless re-confirmed locally.

Original observed PCSX2 CRC from prior notes: `C0659AD1`

The former file-role handoff notes have been researched and consolidated into
the canonical [`knowledge/game/files/README.md`](knowledge/game/files/README.md) reference.
Use its evidence labels instead of reviving these older unqualified guesses.

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

## Input-profile Workflow

`workshop input` generates every complete profile from
`input_profiles/sources/Default.ini`, named partial inputs under
`sources/overrides/`, and game-specific partial inputs under
`sources/overrides/games/`,
without changing GameSettings assignments. `workshop input <profile>`
regenerates only the selected profile and its game-specific variants, then
assigns those profiles through GameSettings. Generated root-level profiles
remain tracked by Git.

## Release Workflow

The maintained release builder is `scripts/release/build_release.ps1`; it produces a self-contained development or production candidate from the current embedded profile. The exact end-user contract, validation evidence, and GitHub publication sequence are canonical in `docs/RELEASE_PROCESS.md`.
