# Script layout

`_na228.ps1` is the routine user-facing build/launch command.
`pcsx2/actualization/act.ps1` is the standalone user-facing actualization
command.
Everything else below `scripts/` is an internal workflow helper, a focused
maintenance tool, or a preserved research utility.

Superseded implementations are removed and remain recoverable through Git
history; do not recreate an archive directory for dead scripts.

## Directories

- `lib/`: shared PowerShell bootstrap, portable run-log, and structured
  build-record helpers.
- `na228/`: build, promotion, ISO identity, worker-path validation, and focused
  build/run-log tests.
- `pcsx2/`: PCSX2 launch, process, configuration, CRC helpers, the user-facing
  user/development single-instance and multi-game launch commands, the
  dot-sourced source-game command set, stable/development savestate filing,
  actualization dispatch/state/input-profile generation and focused tests, the
  minimal hidden workstream-copy launcher, and
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
- `research/ghidra/`: hash-pinned headless Ghidra imports into the shared
  `@analysis/disassembly/` root, MWo3 preparation, portable source-path
  normalization, C/ASCII export, verified manifests, and exact shared-binary
  game cohorts.
- `research/menu_input/`: preserved MIPS and Ghidra analysis helpers from the
  menu-input investigation.
- `research/ee_memory_map/`: PCSX2 savestate extraction, allocator-chain
  validation, overlay identification, and EE-region reporting for injection
  capacity research.
- `research/localization/`: preserved Font asset investigation, independent
  renderer-fragment verification, mapping probes, and NUN5-left/NA2-right
  comparison artifacts.
- `research/ui_translation/`: offline paired-savestate import and screenshot
  extraction, rendering preflight, deterministic Victory texture and layout
  generation, and user-directed runtime research for NUN5-to-NA2 UI
  comparisons.

Normal builds call `na228_builder.build_profile` through `na228/build.ps1`.
Before that call, `na228/build.ps1` checks the deterministic successful-build
receipt through `na228_builder.build_preflight`; an exact hit returns the normal
unchanged result without staging an ISO. `na228/test_build_preflight.ps1` covers
the cache-hit and safe full-build-fallback dispatch paths.
`na228 -t` calls the same builder in candidate-only mode: it always composes a
fresh verified `@build/NA2.28 - Candidate.iso`, bypasses Current preflight and
promotion state, and does not probe or close PCSX2.
`na228 -t work/<task title>/build/<name>.iso` instead builds an isolated
worker-owned ISO, stages beside it, and keeps both operational and structured
records under `work/<task title>/logs/`. The path is caller-supplied and
validated; worker mode cannot address shared build outputs or mutate shared
preflight, promotion, PNACH, log, or emulator state. Agents must use this form
rather than bare `na228`, `na228 -b`, or bare `na228 -t`.
Despite its historical `Test` parameter name, `na228 -t` is always an ISO-build
command and never runs tests. The unambiguous full builder-suite command is:

```powershell
python -B -m unittest discover -s na228_builder/tests -p 'test_*.py'
```

`na228 -b` runs the standard Current build and conditional promotion pipeline but
does not launch PCSX2. Bare `na228` keeps the build-then-launch workflow.
User-owned shared-image builds and launches run `act na228` automatically;
worker-output builds never actualize. The standalone `act` command can run all
actualization modes without building or launching.

`na` continues accepting any ordered combination of registered ISO selectors;
its existing selectors and zero-argument behavior remain unchanged. A missing
selected ISO fails before any PCSX2 process is changed.

Translation is composed directly from the pinned profile; there is no standalone
translation-export command or non-strict source-hash mode.

`pcsx2/actualization/sync_input.ps1` regenerates the NA2 comparison input profile
from the canonical base profile while changing only the four configured
`[Pad1]` face-button bindings. Run it as `act input`; the legacy `na2inputs`
profile helper delegates to that mode.

`pcsx2/actualization/act.ps1` owns standalone actualization logging and
dispatch. Bare `act` runs `na2`, then `input`.
`pcsx2/actualization/sync_game_files.ps1` derives every retained role's serial
and ELF CRC, links the stable cheat template to generated CRC aliases, writes
real GameSettings that select the configured existing Current, Previous, or
Candidate card, and deduplicates shared serial/CRC identities with Current
taking precedence. It never creates or modifies templates or memory cards.
Run `act help` or `act -h` for the standalone command summary.

`pcsx2/launch.ps1` is the single PCSX2 launcher. Configured launches default to
`dev`; pass `-Target stable` for an explicit stable check. Agent launches use
`-WorkerRoot work/<task title>` and start the existing task-owned PCSX2 copy in
no-GUI mode. The launcher suppresses process-owned render windows for the
worker startup interval, reads back top-level-window visibility, and terminates
only the newly launched worker if it cannot remain hidden. `-IsoPath` is
optional for configured launches and mandatory and repository-relative for
worker launches.
`-PassThru` returns the started process for higher-level orchestration such as
window tiling. The launcher does not copy or configure PCSX2, inspect or stop
unrelated processes, use PINE, load savestates, capture output, or perform
cleanup.
Source-game and pair-launch commands inherit the `dev` default. Savestate
filing also defaults to `dev`; pass `-Target stable` to file states from the
stable installation.

Profiles consume repository-owned declarative binary-patcher, translation, and
texture-patcher modules. Final output identity comes from profile `identity.json`
and is composed before the image assembler runs rather than owned by a feature.

`release/build_release.ps1` builds the self-contained Windows release EXE from
the pinned toolchain and current profile. See `docs/RELEASE_PROCESS.md`.

`release/publish_release.ps1` is the guarded publication backend for
`na228 release [version]`; it validates the production package before pushing an
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
| `scripts/pcsx2/capture_state_screenshot.ps1` | `ec4b8276193bc214b526d5ab4f4f85b240ef7949` | Retired because it serialized a complete savestate solely to obtain a fresh screenshot. Extract `Screenshot.png` directly from an existing state; use PCSX2's native screenshot output for a fresh runtime frame. |
| `scripts/archive/replace_iso_file_same_size.ps1` | `858da62aacc5d9571bdef072e36b484efddc15e9` | Direct unverified ISO mutation was superseded by guarded, hash-pinned replacements through `na228_builder.image_assembler`. |
| `scripts/na2/check_log_crc.ps1` | `ce4b06c57a7e1a28124c7a8efffd38169723d915` | Manual log/PNACH comparison was superseded by `na228/iso_identity.ps1` and the maintained standalone actualization workflow. |
| `scripts/na2/get_elf_crc.ps1` | `858da62aacc5d9571bdef072e36b484efddc15e9` | The redundant command wrapper was removed; `pcsx2/pcsx2_elf_crc.ps1` remains the shared tested implementation. |
| `scripts/actualization/links.ps1` and `test_links.ps1` | `a972fc1` | Retired when stable and development PCSX2 were configured to consume `@pcsx2_files/` directly; no copy or link synchronization step remains. |
| `scripts/na2/test_memory_card.ps1` | `5e2f7a49723ad6b1ae0262880588bb7926e880c3` | Retired with the later agent PCSX2 runtime framework; there is no maintained replacement. |
| `scripts/na2/test_test_memory_card.ps1` | `5e2f7a49723ad6b1ae0262880588bb7926e880c3` | Retired with the later agent PCSX2 runtime framework; there is no maintained replacement. |
| `scripts/na2/pine.ps1`, `provision_test_pcsx2.ps1`, `test_operation.ps1`, `test_process_ownership.ps1`, `test_runtime.ps1`, `test_test_operation.ps1`, `test_test_pine.ps1`, `test_test_runtime.ps1`, `test_worker_pcsx2.ps1`, and `worker_pcsx2.ps1` | `4fe8bc3b0c77633b83de519a1913f2e8776a6770` | The unsolicited agent PCSX2 ownership, PINE-operation, provisioning, and runtime framework was removed. Only the minimal hidden launcher remains. |
| `scripts/research/translation/check_translation_lengths.ps1` | `819c0999f6adf5686ce5f75ea82157e697469ee8` | Its fixed-slot `old`/`new` assumptions are obsolete; translation importer and string patcher validation now enforce encoding and capacity rules. |
| `scripts/research/translation/build_mapping_ids.ps1` | `4687470b31db4ff8a2a46071808a35f9282745cf` | The temporary mapping-ID worker build was retired after visible rows were promoted; canonical `translation_importer/mappings.tsv` and ordinary profile builds are maintained. |
| `scripts/research/translation/sync_rebuild.py` | `4687470b31db4ff8a2a46071808a35f9282745cf` | The parallel candidate inventory was retired; edit and validate canonical `translation_importer/mappings.tsv` directly. |
