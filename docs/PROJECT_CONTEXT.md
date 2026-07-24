# Project Context

The modified project game is named *Narutimate Accel v2.28*. It is based on
*Naruto Shippuuden: Narutimate Accel 2*, whose clean source identity remains
`SLPS-25837`.

## Stable Local References

Original source ISOs are the `na2_iso`, `nun3_iso`, `nun5_iso`, and `nun6_iso`
project files. NUN6 A35 is a Brazilian mod of NUN5, not an official successor.
It is retained as a feature donor because it contains many modifications that
may later be ported to NA2.

Current PCSX2 actualization:

- Canonical editable inputs are `@pcsx2_files/cheats.pnach` and
  `@pcsx2_files/gamesettings.ini`.
- The actualizer derives each retained Current, Previous, and Candidate
  identity from its ISO and maintains the matching CRC-named PNACH and
  GameSettings symlinks under `@pcsx2/`.
- Former PNACH sections preserved as binary-patcher patch sets are `QoL` and `Battle logic`. Binary-patcher schema v2 organizes each package as groups, atomic patches, and exact edits; `default_enabled` preserves historical state. The old `Testing` substitution edits were retired after their negative runtime results were promoted to `docs/knowledge/substitution.md`. Rendering is currently an empty feature folder omitted from the active profile.
- Actualization runs after every user-owned build and before every user-owned
  Current, Previous, or Candidate launch. Isolated worker builds never mutate
  shared PCSX2 state. `na2 act` refreshes the same state without building or
  launching.
- A zero-byte canonical PNACH removes its managed PCSX2 CRC aliases. Managed
  aliases are symlinks targeting the canonical project files or the
  actualizer's generated role settings; other games, real files, and unrelated
  symlinks are preserved.
- `Mcd001_NA228.ps2` is a copy-only base. Current, Previous, and Candidate each
  receive a separately named copy when absent, and later actualizations never
  overwrite those working cards.
- `@pcsx2_files/` contains the Git-tracked canonical PNACH, GameSettings
  template, input profiles, project input recordings, and ignored local
  screenshots.
- `na2 act` reports enabled named cheats from uncommented `patch=` or setting lines, or `none` when no cheats are enabled.
- PNACH labels such as `// [Skip CC2 intro]` are comments only. A cheat is enabled only when its executable `patch=`/setting line is uncommented. Disabled proven cheats and disabled hypotheses must keep their executable lines commented out. Temporary PNACH hypothesis patches go at the top as comment-only names plus disabled `// patch=` lines; uncomment them only while actively testing.
- Fixed-address PNACH hypotheses are safe by default only for the boot ELF or another region proven to remain resident and stable for the entire write lifetime.
- `BTL.BIN`, `ETC.BIN`, and other on-demand modules are loaded and unloaded into reusable EE memory. Never test them with unguarded fixed-address PNACH writes: patch the file through the binary-patcher module, rebuild the ISO, and test that build instead.
- A runtime overlay PNACH write is permitted only with a proven load-state/signature guard. Dynamic heap targets require a proven allocation, address, and lifetime.

## Working Layout

Directory roots are configured once in `project-paths.json`; see
`docs/PROJECT_PATHS.md`. The `@root/...` notation below is logical and must not be
replaced with a copied machine-specific absolute path.

- `@source/`: untouched source media. Do not modify unless explicitly instructed. No generated logs, temp files, probes, manifests, or metadata belong here.
- `@source/*.files/`: extracted views of original source archives. Treat as read-only reference.
- `build/`: normally contains `build/NA2.28 - Current.iso`, may retain at most `build/NA2.28 - Previous.iso` as rotation history, and may retain `build/NA2.28 - Candidate.iso` while concurrent refactoring/testing needs it. Standard builds use `NA2.28 - Current.iso.building`, then discard an identical candidate or promote and rotate a changed one. `na2 -t` instead uses `NA2.28 - Candidate.iso.building`, atomically updates only Candidate, leaves PCSX2 running, and never changes Current, Previous, their build mapping, or Current's preflight receipt. Staging files are removed on failure.
- `work/<task title>/build/`: isolated agent ISOs produced by `na2 -t work/<task title>/build/<name>.iso`. Staging remains beside the requested output, build records remain under that task's `logs/`, and the mode never touches shared build, preflight, promotion, PNACH, or PCSX2 state.
- Temporary imported archives live under the active task's `work/<task title>/temp/` folder until normalized or retired. Reproducible data lives as hash-pinned inputs beside its module; complete accepted states are preserved by annotated Git tags, and retired inputs remain available through Git history.
- `na2_patcher/features/localization/translation_importer/mappings.tsv` is the Localization feature's current hash-pinned importer input and folds the verified pointer inventory into each applicable mapping row. `source_ref` and `source` retain the guarded NA2 origin; `donor_ref` and `donor` retain the official translation and make it executable by default. A nonempty user-authored `replacement` overrides the donor, and `prefix` is prepended to the selected text. Profile `identity.json` owns the imported/output game titles, and the generic `string_patcher` applies that output policy before deriving inline or linked placement from encoded fit and available references. `payload_builder` constructs `PRG/228.BIN` and owns its loader/memory integration; the composer resolves symbols and `binary_patcher` applies concrete guarded writes. No standalone export or source-hash bypass exists.
- `@logs/`: disposable shared-workflow records; no files should be written directly in the root. `na2` keeps bounded Current/Previous/Candidate provenance under `@logs/na2/`, and shared generated workstream evidence belongs under `@workstream_logs/<exact task title>/`. Agent ISO and PCSX2 records instead stay under `work/<task title>/logs/`. See `docs/LOGGING.md`.
- `scripts/`: repeatable tooling.
- `@pcsx2_files/`: project-owned PCSX2 artifacts. The canonical PNACH and input recordings are tracked; screenshots remain local and ignored.
- `@pcsx2/`: portable PCSX2 installation and user-owned emulator state. Agent launches share its read-only executable, BIOS, resources, profiles, and replacement textures, but temporarily redirect mutable folders into their own `work/<task title>/` tree. Its game-list media paths may point to `@build/` and `@source/`; its CRC-named cheat symlinks target the canonical PNACH under `@pcsx2_files/`.
- `na2_patcher/modules/binary_patcher/`: repository-owned schema v2 and reusable CLI validator/patcher for canonical group/patch/edit packages owned by features. The schema has no relations table; default-enabled edits are simulated in deterministic order so compatible overlaps and already-satisfied replacements are retained while real guard conflicts fail before ISO staging. It never applies `pending`, `runtime_failed`, or `deprecated` patches and writes only new same-size outputs with complete logs.
- `na2_patcher/modules/translation_importer/`: the reusable official-string importer engine. Localization-owned mappings and their pointer-reference inventory live under `na2_patcher/features/localization/translation_importer/`.
- `na2_patcher/modules/string_patcher/`: the reusable semantic string-placement engine. Localization has no feature-owned string-patcher directory or local declarations; its importer artifact invokes the engine as a derived consumer. The engine compiles inline imports and contributes external fragments/symbolic pointers without owning `228.BIN` layout. The memory-card title belongs to profile `identity.json`, not Localization.
- `na2_patcher/modules/texture_patcher/`: the reusable fixed-size texture derivation engine. The Localization feature owns its 34 source-derived NUN5 UI recipes under `na2_patcher/features/localization/texture_patcher/`; no replacement blobs are stored.
- `na2_patcher/`: manifest-free profiles, reusable aggregate-hash-pinned feature packages, folder-derived module orchestration, artifact dependency composition, and reusable transformation engines. `na2_patcher/profiles/current/` contains source-root bindings, enabled feature IDs/pins, and final image identity. Feature rows define stable peer order; module directories define ownership and engine type; the composer resolves declared artifacts and closes typed operations. `payload_builder/` links shared resident code/data and global integration; `image_assembler/` alone performs ISO9660/UDF mutation and complete staged-image verification. Binary packages apply their default-enabled patches and contain four canonical control tables plus referenced blobs. Adjacent READMEs, engine code, and non-input helpers are excluded from feature pins.
- `.agents/`: dated human-readable handoffs exchanged between separate Windows installations and Codex instances. They may contain machine-specific paths as historical context, are non-authoritative, and must be reviewed rather than deleted as clutter.
- `docs/`: repository-wide context, confirmed knowledge, active plans, hypotheses, and release documentation. Component-specific READMEs remain beside their components.
- `docs/knowledge/`: confirmed findings, reusable negative results, and supporting evidence promoted out of disposable logs. Module-owned structured evidence remains beside its module.
- `docs/LOGGING.md`: log contents, bounded retention, cleanup, and knowledge-promotion policy.
- `docs/HYPOTHESES.md`: archived patch candidates, failed experiments, unverified addresses, and speculative leads.
- `TASKS.md`: concrete active tasks, test plans, and queued investigations only; no general workflow rules.
- `@user_savestates/`: ignored, user-managed, read-only library of savestates, screenshots, and related task inputs. Its subject folders may be linked from `TASKS.md`; agents inspect them only to choose inputs, copy selected files into their own `work/<task title>/inputs/sstates/` tree with provenance, and never modify or clean the library itself.
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

All tasks must read `AGENTS.md`, `docs/PROJECT_CONTEXT.md`, `TASKS.md`, and `docs/HYPOTHESES.md` before acting. Binary outputs and experiments remain shared, so each task must re-check Git status and current profile/build state before modifying files.

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

Use `scripts/media/extract_source_iso.ps1 -IsoPath <path> -TaskTitle <exact task
title>` for a new canonical extraction. It stages under the invoking task's
owned `work/<task title>/temp/source_extraction/` folder and never recreates
top-level `work/temp/`. It recursively expands CVM, inner ISO, AFS,
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

- `@source_na2/DATA/DATA.CVM.files/DATA.CVM.iso`
- `@source_na2/DATA/DATA.CVM.files/DATA.CVM.hdr`
- `@source_na2/DATA/DATA.CVM.files/DATA.CVM.iso.files/`

Use `scripts/media/split_cvm_rofs.ps1` to split the encrypted CVM safely without running `@utils/old/CVM Parser/cvm_tool.exe`.

## Current Scripts

- Root `_na2.ps1` is the only routine user-facing entrypoint. Bare `na2`, `na2 -b`, bare `na2 -t`, `na2 -c`, `na2 -p`, and `na2 act` retain their Current/Previous/Candidate behavior. A standard bare `na2` launch clears a stale shared `StartPaused` setting after closing PCSX2 so the game starts running; pure `-c`/`-p` selectors do not rewrite settings around existing instances. `na2 -t work/<task title>/build/<name>.iso` adds a full verified worker-output mode with task-owned staging/logs and no shared-state mutation; agents must use that form for builds.
- `scripts/na2/` contains build/promotion, PCSX2 actualization, ISO identity,
  worker-path validation, PCSX2 launch/process control, PINE identity checks,
  and agent runtime isolation. `test_launch.ps1` briefly injects worker
  folders/card/PINE settings, waits for the expected ELF identity, restores
  shared settings immediately, and thereafter controls only its recorded
  PID/window/port. Live two-instance validation on PCSX2 2.6.3 confirmed
  independent ports, windows, cards, settings restoration, and targeted
  shutdown.
- `na2_patcher/module_pipeline.py` prepares one explicit hash-pinned profile's artifacts, derived consumers, and shared payload contributions. `na2_patcher/build_profile.py` applies that prepared pipeline and writes its run log. `na2_patcher/composer.py` resolves module artifacts and closes typed image operations. `na2_patcher/image_assembler/` alone stages, mutates, and verifies the caller-selected `.building` image for standard promotion, shared Candidate, or worker-owned output.
- `scripts/media/` contains the recursive source extractor, its byte-parity
  verifier, and focused ISO, AFS, and CVM building blocks. Direct same-size ISO
  replacement survives only as an unsupported reference under
  `scripts/archive/`.
- `scripts/project/` contains configured-source read-only maintenance. There is currently no maintained release-creation script; the release workflow will be redesigned before new automation is added.
- `scripts/archive/` contains unsupported historical reference implementations. Inspect and explicitly select one before use; archived scripts are never part of the normal workflow.
- `scripts/research/menu_input/` and `scripts/research/translation/` retain useful one-off analysis tools outside the normal build path. Their lack of runtime callers does not make them disposable.
- See `scripts/README.md` for the maintained directory contract and individual responsibilities.

## Utils Dump

`@utils/old/` is an untrusted historical tool/archive dump. It may contain useful tools or source references, but nothing there should be treated as current workflow or executed blindly.

Observed examples include AFS tools, CCS tools, Ghidra/EmotionEngine material, Kuriimu, PS2Dis, PSS tools, StudioCCS variants, and many unknown `.bin` files. Inspect and select a tool for a specific task before using it.

## CRC / PNACH Notes

PCSX2 cheat filenames include the game CRC, for example:

`SLOP-NA228_<crc>.pnach`

If the boot ELF inside an ISO changes, PCSX2 may report a different CRC.
Actualize derives the alphanumeric serial from the ISO boot path and creates a
matching `@pcsx2/cheats/<serial>_<crc>.pnach` link to
`@pcsx2_files/cheats.pnach`.

PCSX2 uses its internal `@pcsx2/cheats/` folder. Only the canonical PNACH is tracked in the project; actualized CRC aliases are relative symlinks in the portable installation.

Known PCSX2 paths from prior notes:

- Log: `@pcsx2/logs/emulog.txt`
- Cheats: CRC aliases in `@pcsx2/cheats/`, targeting
  `@pcsx2_files/cheats.pnach`

Known log pattern:

Original-source historical pattern:

`ELF Loading: cdrom0:\SLPS_258.37;1, Game CRC = 870F8722, EntryPoint = 0x00100008`

Modified-project pattern after the profile identity is assembled:

`ELF Loading: cdrom0:\SLOP_NA2.28;1, Game CRC = <crc>, EntryPoint = 0x00100008`

## Prior GPT Handoff Notes

The following are transferred notes/hypotheses from earlier ChatGPT work. Treat them as leads, not verified facts, unless re-confirmed locally.

Original observed PCSX2 CRC from prior notes: `C0659AD1`

The former file-role handoff notes have been researched and consolidated into
the canonical [`knowledge/game_files.md`](knowledge/game_files.md) reference.
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

## Actualize Workflow

`scripts/na2/actualize.ps1` owns this workflow. It derives identities for every
retained Current, Previous, and Candidate ISO, deletes stale managed symlinks,
and creates relative PNACH and GameSettings aliases. It generates role
GameSettings from `@pcsx2_files/gamesettings.ini`, changing only the memory-card
filename, and copies the configured base card only when a role card is absent.
An active role wins if two retained ISOs share one PCSX2 identity. The
actualizer refuses occupied unmanaged alias paths instead of overwriting them.

## Release Workflow

The maintained release builder is `scripts/release/build_release.ps1`; it produces a self-contained development or production candidate from the current embedded profile. The exact end-user contract, validation evidence, and GitHub publication sequence are canonical in `docs/RELEASE_PROCESS.md`.
