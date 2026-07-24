# Script layout

`_na2.ps1` is the only routine user-facing command. Everything below `scripts/`
is an internal workflow helper, a focused maintenance tool, or a preserved
research utility.

## Directories

- `lib/`: shared PowerShell bootstrap, portable run-log, and structured
  build-record helpers.
- `archive/`: unsupported reference-only implementations. Read the directory
  warning before considering one for a task.
- `na2/`: build, promotion, PNACH, PCSX2 launch, CRC diagnostics, and isolated
  agent tests for hidden launch and run logging.
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
- `research/ui_translation/`: selectable multi-game PCSX2 launch and tiling,
  PINE identity checks, controlled savestate and embedded-screenshot capture,
  rendering preflight, and read-only runtime memory inspection for NUN5-to-NA2
  UI comparisons.
- `research/translation/`: retained translation-table length validator and the
  worker-only mapping-ID diagnostic builder used to identify visible strings.
  Neither changes normal profile behavior.

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
`na2 -b` runs the standard Current build and conditional promotion pipeline but
does not launch PCSX2. Bare `na2` keeps the build-then-launch workflow. Every
user-owned Current, Previous, or Candidate build/launch path runs the unified
PCSX2 actualizer; isolated worker builds never do.
Translation is composed directly from the pinned profile; there is no standalone
translation-export command or non-strict source-hash mode.

`na2/sync_input_profiles.ps1` regenerates the NA2 comparison input profile from
the canonical base profile while changing only the four configured `[Pad1]`
face-button bindings. The shared PowerShell profile exposes it as `na2inputs`.

`na2/actualize.ps1` derives every retained role's serial and ELF CRC, maintains
the canonical PNACH and GameSettings aliases, and creates each role's memory
card from the copy-only base only when absent. Existing role cards are preserved.

Agent runtime checks use `na2/test_launch.ps1 -WorkerRoot
work/<task title>`. A short named lock protects shared configuration while the
wrapper redirects writable folders, copies/reuses the game's effective Slot 1
card under the worker, chooses a free PINE port, and launches hidden/muted and
running by default. Pass `-StartPaused` only when the test requires a paused
initial state; it is part of the same guarded settings snapshot rather than a
separate shared-INI edit.
After PINE reports the expected serial/CRC, shared settings are restored
immediately and the lock is released. The wrapper records and validates the
specific PID, start time, top-level window handle, and PINE endpoint, then
closes only that process. Runtime logs are unique per launch; savestates,
screenshots, recordings, cards, cache, and dump paths remain task-owned.
`na2/test_test_runtime.ps1` covers path injection/restoration and guards against
overwriting unrelated settings; `na2/test_test_memory_card.ps1` covers private
card reuse. The shared ISO identity helper is also used by PNACH actualization.

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
