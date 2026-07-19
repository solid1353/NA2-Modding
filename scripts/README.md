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
  `extract_source_iso.ps1` for canonical recursive source extraction: it stages
  an outer ISO, expands CVM, inner ISO, AFS, and nested AFS containers, verifies
  byte parity and timestamps, then promotes one `<ISO filename>.files` tree.
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
- `research/ui_translation/`: PINE identity checks, controlled savestate and
  embedded-screenshot capture, rendering preflight, and read-only runtime
  memory inspection for NUN5-to-NA2 UI comparisons.
- `research/translation/`: retained translation-table length validator. It is
  not part of normal profile builds.

Normal builds call `na2_patcher.build_profile` through `na2/build.ps1`.
Before that call, `na2/build.ps1` checks the deterministic successful-build
receipt through `na2_patcher.build_preflight`; an exact hit returns the normal
unchanged result without staging an ISO. `na2/test_build_preflight.ps1` covers
the cache-hit and safe full-build-fallback dispatch paths.
Translation is composed directly from the pinned profile; there is no standalone
translation-export command or non-strict source-hash mode.

Package and ZIP-overlay workflows are retired. Profiles consume only repository
owned declarative raw-binary, translation, UI-texture, and disc-identity modules.

When adding a script, place it beside the workflow it supports. Do not add new
files directly under `scripts/`; the root is reserved for this index and
responsibility directories.
