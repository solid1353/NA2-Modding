# Script layout

`_na2.ps1` is the routine user-facing build/launch command.
`actualization/act.ps1` is the standalone user-facing actualization command.
Everything else below `scripts/` is an internal workflow helper, a focused
maintenance tool, or a preserved research utility.

Superseded implementations are removed and remain recoverable through Git
history; do not recreate an archive directory for dead scripts.

## Directories

- `lib/`: shared PowerShell bootstrap, portable run-log, and structured
  build-record helpers.
- `actualization/`: standalone dispatch, PCSX2 state actualization, PNACH-state
  parsing, and focused tests.
- `na2/`: build, promotion, ISO identity, worker-path validation, and focused
  build/run-log tests.
- `pcsx2/`: PCSX2 launch, process, configuration, CRC helpers, the user-facing
  user/development single-instance and multi-game launch commands, the
  dot-sourced source-game command set, user savestate filing, the minimal
  hidden workstream-copy launcher, and
  `patch_savestate_memory.py` for exact-byte-guarded EE-memory patches in copied
  task-owned savestates. Unsupported Zstandard ZIP members are bulk-extracted
  once through 7-Zip when available, with `tar` as the portable fallback,
  instead of rescanning the whole archive for every member.
- `media/`: ISO, AFS, and CVM inspection/extraction tools. Use
  `extract_source_iso.ps1 -IsoPath <path> -TaskTitle <exact task title>` for
  canonical recursive source extraction: it stages under
  `work/<task title>/temp/source_extraction/`, expands CVM, inner ISO, AFS, and
  nested AFS containers, verifies byte parity and timestamps, then promotes one
  `<ISO filename>.files` tree. It never uses shared top-level `work/temp/`.
  `verify_extraction.py` can recheck an existing tree. The lower-level
  `extract_iso.ps1`, `extract_afs.ps1`, and `split_cvm_rofs.ps1` remain focused
  building blocks; ISO changes belong in hash-pinned profiles, not direct
  file-replacement helpers.
- `project/`: source and completed-analysis read-only maintenance.
- `localization/`: maintained deterministic Localization generators whose
  outputs are consumed by normal profile builds.
- `research/ghidra/`: hash-pinned headless Ghidra imports into the shared
  `@analysis/disassembly/` root, MWo3 preparation, portable source-path
  normalization, C/ASCII export, verified manifests, and exact shared-binary
  game cohorts.
- `research/menu_input/`: preserved MIPS and Ghidra analysis helpers from the
  menu-input investigation.
- `research/ee_memory_map/`: PCSX2 savestate extraction, allocator-chain
  validation, overlay identification, and EE-region reporting for injection
  capacity research.
- `research/localization/`: preserved Font asset investigation, mapping
  probes, and NUN5-left/NA2-right comparison artifacts.
- `research/ui_translation/`: offline paired-savestate import and screenshot
  extraction, rendering preflight, deterministic Victory texture and layout
  generation, and user-directed runtime research for NUN5-to-NA2 UI
  comparisons.

Normal builds call `na2_patcher.build_profile` through `na2/build.ps1`.
Before that call, `na2/build.ps1` checks the deterministic successful-build
receipt through `na2_patcher.build_preflight`; an exact hit returns the normal
unchanged result without staging an ISO. `na2/test_build_preflight.ps1` covers
the cache-hit and safe full-build-fallback dispatch paths.
`na2 -t` calls the same builder in candidate-only mode: it always composes a
fresh verified `@build/NA2.28 - Candidate.iso`, bypasses Current preflight and
promotion state, and does not probe or close PCSX2.
`na2 -t work/<task title>/build/<name>.iso` instead builds an isolated
worker-owned ISO, stages beside it, and keeps both operational and structured
records under `work/<task title>/logs/`. The path is caller-supplied and
validated; worker mode cannot address shared build outputs or mutate shared
preflight, promotion, PNACH, log, or emulator state. Agents must use this form
rather than bare `na2`, `na2 -b`, or bare `na2 -t`.
Despite its historical `Test` parameter name, `na2 -t` is always an ISO-build
command and never runs tests. The unambiguous full patcher-suite command is:

```powershell
python -B -m unittest discover -s na2_patcher/tests -p 'test_*.py'
```

`na2 -b` runs the standard Current build and conditional promotion pipeline but
does not launch PCSX2. Bare `na2` keeps the build-then-launch workflow.
User-owned shared-image builds and launches run `act na2` automatically;
worker-output builds never actualize. The standalone `act` command can run all
actualization modes without building or launching.

`na` continues accepting any ordered combination of registered ISO selectors;
its existing selectors and zero-argument behavior remain unchanged. A missing
selected ISO fails before any PCSX2 process is changed.

Translation is composed directly from the pinned profile; there is no standalone
translation-export command or non-strict source-hash mode.

`actualization/input.ps1` regenerates the NA2 comparison input profile from the
canonical base profile while changing only the four configured `[Pad1]`
face-button bindings. Run it as `act input`; the legacy `na2inputs` profile
helper delegates to that mode.

`actualization/act.ps1` owns standalone actualization logging and dispatch.
Bare `act` runs `na2`, `input`, then `links`. `actualization/na2.ps1` derives
every retained role's serial and ELF CRC, maintains canonical PNACH aliases,
writes real GameSettings, keeps the template `[MemoryCards]` section only for
Current, and deduplicates shared serial/CRC identities with Current taking
precedence. It never creates or modifies memory cards.
`actualization/links.ps1` creates or verifies the configured project-to-user
hardlinks and refuses differing occupied counterparts.
Run `act help` or `act -h` for the standalone command summary.

`pcsx2/launch.ps1` is the single PCSX2 launcher. Configured launches use
`-Target stable|dev`; agent launches use `-WorkerRoot work/<task title>` and
start the existing task-owned PCSX2 copy hidden. `-IsoPath` is optional for
configured launches and mandatory and repository-relative for worker launches.
The launcher does not copy or configure PCSX2, inspect or stop processes, use
PINE, load savestates, capture output, or perform cleanup.

Profiles consume repository-owned declarative binary-patcher, translation, and
texture-patcher modules. Final output identity comes from profile `identity.json`
and is composed before the image assembler runs rather than owned by a feature.

`release/build_release.ps1` builds the self-contained Windows release EXE from
the pinned toolchain and current profile. See `docs/RELEASE_PROCESS.md`.

`release/publish_release.ps1` is the guarded publication backend for
`na2 release [version]`; it validates the production package before pushing an
annotated version tag that triggers GitHub Release publication.

When adding a script, place it beside the workflow it supports. Do not add new
files directly under `scripts/`; the root is reserved for this index and
responsibility directories.

## Retired scripts

These implementations are intentionally absent from the working tree. Recover
one into `work/<task title>/temp/` for historical inspection with its indexed
commit and former path. Review it before use, then selectively port any needed
logic into the appropriate maintained directory; never execute the recovered
file blindly or recreate `scripts/archive/`. Normal work uses the maintained
replacement.

```powershell
git show '<commit>:<former-path>' > 'work/<task title>/temp/<filename>'
```

| Former path | Recovery commit | Retirement and maintained replacement |
| --- | --- | --- |
| `scripts/pcsx2/capture_state_screenshot.ps1` | `a9938c40b3b97ab4adf072b9c577d551b620a46c` | Retired because it serialized a complete savestate solely to obtain a fresh screenshot. Extract `Screenshot.png` directly from an existing state; use PCSX2's native screenshot output for a fresh runtime frame. |
| `scripts/archive/replace_iso_file_same_size.ps1` | `ff615f410889c93dea015e5fe4ea44ec4662dbee` | Direct unverified ISO mutation was superseded by guarded, hash-pinned replacements through `na2_patcher.image_assembler`. |
| `scripts/na2/check_log_crc.ps1` | `804c2df8d16019a3b55f6acb10a023c435faaafc` | Manual log/PNACH comparison was superseded by `na2/iso_identity.ps1` and the maintained standalone actualization workflow. |
| `scripts/na2/get_elf_crc.ps1` | `ff615f410889c93dea015e5fe4ea44ec4662dbee` | The redundant command wrapper was removed; `pcsx2/pcsx2_elf_crc.ps1` remains the shared tested implementation. |
| `scripts/na2/test_memory_card.ps1` | `70a81a36ecf119b6330b19984c9c8104d54bcc61` | Retired with the later agent PCSX2 runtime framework; there is no maintained replacement. |
| `scripts/na2/test_test_memory_card.ps1` | `70a81a36ecf119b6330b19984c9c8104d54bcc61` | Retired with the later agent PCSX2 runtime framework; there is no maintained replacement. |
| `scripts/na2/pine.ps1`, `provision_test_pcsx2.ps1`, `test_operation.ps1`, `test_process_ownership.ps1`, `test_runtime.ps1`, `test_test_operation.ps1`, `test_test_pine.ps1`, `test_test_runtime.ps1`, `test_worker_pcsx2.ps1`, and `worker_pcsx2.ps1` | `4f6578e7d131fca9905aff8358371ed6eb8d9791` | The unsolicited agent PCSX2 ownership, PINE-operation, provisioning, and runtime framework was removed. Only the minimal hidden launcher remains. |
| `scripts/research/translation/check_translation_lengths.ps1` | `91a7dabbbe8ac957b4c04d3abe7aec721757b839` | Its fixed-slot `old`/`new` assumptions are obsolete; translation importer and string patcher validation now enforce encoding and capacity rules. |
| `scripts/research/translation/build_mapping_ids.ps1` | `9bb1e191a2e523f467f60c63758db2ff1df0b15b` | The temporary mapping-ID worker build was retired after visible rows were promoted; canonical `translation_importer/mappings.tsv` and ordinary profile builds are maintained. |
| `scripts/research/translation/sync_rebuild.py` | `9bb1e191a2e523f467f60c63758db2ff1df0b15b` | The parallel candidate inventory was retired; edit and validate canonical `translation_importer/mappings.tsv` directly. |
