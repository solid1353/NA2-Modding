# Script layout

`_na2.ps1` is the only routine user-facing command. Everything below `scripts/`
is an internal workflow helper, a focused maintenance tool, or a preserved
research utility.

## Directories

- `lib/`: shared PowerShell bootstrap code.
- `na2/`: build, promotion, PNACH, PCSX2 launch, CRC diagnostics, and the
  agent-only hidden launch test.
- `media/`: ISO, AFS, and CVM inspection/extraction tools. `extract_cvm.ps1` is
  retained as a low-level diagnostic; `split_cvm_rofs.ps1` is the supported
  encrypted-CVM workflow.
- `project/`: repository inventory and source read-only maintenance.
- `release/`: append-only milestone creation.
- `research/menu_input/`: preserved MIPS and Ghidra analysis helpers from the
  menu-input investigation.
- `research/translation/`: preserved string-slot comparison and patch-analysis
  helpers. They are not part of normal profile builds.

Normal builds call `na2_patcher.build_profile` through `na2/build.ps1`.
Translation is composed directly from the pinned profile; there is no standalone
translation-export command or non-strict source-hash mode.

When adding a script, place it beside the workflow it supports. Do not add new
files directly under `scripts/`; the root is reserved for this index and
responsibility directories.
