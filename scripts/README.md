# Script layout

`_na2.ps1` is the only routine user-facing command. Everything below `scripts/`
is an internal workflow helper, a focused maintenance tool, or a preserved
research utility.

Superseded implementations are removed and remain recoverable through Git
history; do not recreate an archive directory for dead scripts.

## Directories

- `lib/`: shared PowerShell bootstrap, portable run-log, and structured
  build-record helpers.
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
  offline paired-savestate import and screenshot extraction, rendering
  preflight, and user-directed runtime research for NUN5-to-NA2 UI comparisons.
  Agent-owned runtime control uses `na2/test_launch.ps1 -OperationPlan`.
- `research/translation/`: the worker-only mapping-ID diagnostic builder used
  to identify visible strings. It does not change normal profile behavior.

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
specific PID, start time, top-level window handle, and PINE endpoint. Process
control additionally requires the unchanged live descriptor and its
launch-local ownership capability; identity checks alone never authorize a
stop. Descriptor or capability loss leaves the process and potentially live
runtime files untouched and reports lost ownership. Runtime logs are unique per
launch; savestates, screenshots, recordings, cards, cache, and dump paths remain
task-owned.
`na2/test_test_runtime.ps1` covers path injection/restoration and guards against
overwriting unrelated settings; `na2/test_test_memory_card.ps1` covers private
card reuse; `na2/test_process_ownership.ps1` proves missing, mismatched, and
modified ownership records cannot terminate a process;
`na2/test_test_pine.ps1` covers exact-byte guarded reads/writes; and
`na2/test_test_operation.ps1` covers task-root confinement plus state/screenshot
handling. The shared ISO identity helper is also used by PNACH actualization.

Tasks that need runtime control pass a repository-relative JSON plan below their
own worker root with `-OperationPlan`; the launcher interprets it after PINE
identity is ready and shared settings are restored, but before guarded cleanup:

```powershell
& .\scripts\na2\test_launch.ps1 `
  -WorkerRoot 'work/Font' `
  -IsoPath 'work/Font/build/font-test.iso' `
  -OperationPlan 'work/Font/runtime-operation.json'
```

`work/Font/runtime-operation.json`:

```json
{
  "schema_version": 1,
  "result_path": "work/Font/artifacts/runtime/font-case.json",
  "actions": [
    {
      "action": "load_state",
      "state_path": "work/Font/inputs/sstates/font-case.p2s",
      "slot": 0
    },
    {
      "action": "read_memory",
      "address": "0x00123450",
      "expected_hex": "00112233"
    },
    {
      "action": "wait",
      "milliseconds": 500
    },
    {
      "action": "capture_state",
      "slot": 1,
      "screenshot_path": "work/Font/artifacts/screenshots/font-case.png",
      "timeout_seconds": 30
    }
  ]
}
```

Supported action objects are `identity`; `load_state` with `state_path` and
optional `slot`; exact-byte `read_memory` with `address` and `expected_hex`;
exact-byte guarded `patch_memory` with `address`, `expected_hex`, and
`replacement_hex`; `save_state`; `capture_state` with a task-owned
`screenshot_path`; and bounded `wait` with `milliseconds`. State inputs, plans,
result files, and screenshot outputs must stay below the same
`work/<task title>/` root. Addresses accept JSON integers or `0x` strings;
byte strings are non-empty, even-length hexadecimal.

Every PINE action revalidates the authenticated live descriptor and verifies
the recorded serial/CRC over the same private PINE connection used for that
action. The plan interpreter exposes and persists no PINE port, descriptor, or
ownership capability. `capture_state` records both task-owned state and
screenshot paths, optional `result_path` receives the complete portable JSON
result, and `WaitSeconds` starts only after all plan actions finish.

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
| `scripts/archive/replace_iso_file_same_size.ps1` | `ff615f410889c93dea015e5fe4ea44ec4662dbee` | Direct unverified ISO mutation was superseded by guarded, hash-pinned replacements through `na2_patcher.image_assembler`. |
| `scripts/na2/check_log_crc.ps1` | `804c2df8d16019a3b55f6acb10a023c435faaafc` | Manual log/PNACH comparison was superseded by `na2/iso_identity.ps1` and automatic `na2/actualize.ps1`. |
| `scripts/na2/get_elf_crc.ps1` | `ff615f410889c93dea015e5fe4ea44ec4662dbee` | The redundant command wrapper was removed; `na2/pcsx2_elf_crc.ps1` remains the shared tested implementation. |
| `scripts/research/translation/check_translation_lengths.ps1` | `91a7dabbbe8ac957b4c04d3abe7aec721757b839` | Its fixed-slot `old`/`new` assumptions are obsolete; translation importer and string patcher validation now enforce encoding and capacity rules. |
