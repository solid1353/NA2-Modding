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
- `research/translation/`: retained translation-table length validator. It is
  not part of normal profile builds.

Normal builds call `na2_patcher.build_profile` through `na2/build.ps1`.
Before that call, `na2/build.ps1` checks the deterministic successful-build
receipt through `na2_patcher.build_preflight`; an exact hit returns the normal
unchanged result without staging an ISO. `na2/test_build_preflight.ps1` covers
the cache-hit and safe full-build-fallback dispatch paths.
`na2 -t` calls the same builder in candidate-only mode: it always composes a
fresh verified `@build/NA2.28 - Candidate.iso`, bypasses Current preflight and
promotion state, and does not probe or close PCSX2.
`na2 -b` runs the standard Current build and conditional promotion pipeline but
does not launch PCSX2. Bare `na2` keeps the build-then-launch workflow.
Translation is composed directly from the pinned profile; there is no standalone
translation-export command or non-strict source-hash mode.

Agent runtime checks use `na2/test_launch.ps1`. It derives the PCSX2 serial and
ELF CRC through the shared `na2/iso_identity.ps1` helper, clones the game's
effective Slot 1 card into a stable agent/task-specific card on first use,
reuses that card for later launches in the same task, and restores the exact
original per-game and audio settings after PCSX2 closes. The shared ISO identity
helper is also used by PNACH actualization.

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
