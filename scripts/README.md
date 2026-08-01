# Script layout

`na228.ps1` is the routine NA2 user-facing build/launch command. Shared
input-profile and savestate utilities are exposed by Workshop `workshop.ps1`.
Everything else below `scripts/` is an internal workflow helper, a focused
maintenance tool, or a preserved research utility.

Use the Workshop savestate interface for filing and screenshot extraction:

```powershell
workshop ss move <game> <subpath> [-Target dev|stable] [-Cleanup|-c]
workshop ss extract <paths...>
```

Folder extraction recreates the single `screenshots/` output directory;
explicit same-folder files preserve unrelated outputs. The focused move and
extract scripts are internal implementations behind this entry point.

Superseded implementations are removed and remain recoverable through Git
history; do not recreate an archive directory for dead scripts.

## Directories

- `lib/`: shared PowerShell bootstrap, portable run-log, structured
  build-record helpers, and unified Python runtime/package-set resolution.
- `injection/`: compile/link canonical EE C into `fragment.bin` plus
  `manifest.json`, apply that candidate transactionally through PINE, the
  operational `inject_candidate.ps1` workstream command, and the user-only save
  watcher.
- `na228/`: build/launch execution, promotion, and worker-path
  validation. Root `na228.ps1` owns argument
  parsing and dispatches substantive execution to `na228/run.ps1`.
- `@pcsx2_scripts/`: Workshop-owned PCSX2 launch, worker copying, PINE,
  input-profile, savestate, disc-identity, and CRC utilities.
- `@media_scripts/`: Workshop-owned reusable ISO, AFS, and CVM extractors.
- `project/`: NA2 source extraction and maintenance. Use
  `extract_source_iso.ps1 -IsoPath <path> -TaskTitle <exact task title>` for
  canonical recursive source extraction: it stages under
  `work/<task title>/temp/source_extraction/`, expands CVM, inner ISO, AFS, and
  nested AFS containers, verifies byte parity and timestamps, then promotes one
  `<ISO filename>.files` tree. It never uses shared top-level `work/temp/`.
  `verify_source_extraction.py` can recheck an existing tree. Workshop
  `extract_iso.ps1`, `extract_afs.ps1`, and `split_cvm_rofs.ps1` remain focused
  building blocks; ISO changes belong in hash-pinned profiles, not direct
  file-replacement helpers.
- `research/ghidra/`: NA2 target manifests, cohorts, import/export wrappers,
  and portable source-path normalization. Reusable Java scripts and runtime
  setup live under `@workshop/scripts/ghidra/`.
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
unchanged result without staging an ISO. `tests/na228/test_build_preflight.ps1` covers
the cache-hit and safe full-build-fallback dispatch paths.
`na228 build t` calls the same builder in Test-only mode: it always composes a
fresh verified catalog-derived Test ISO, bypasses Latest preflight and
promotion state, and does not probe or close PCSX2.
`na228 worker work/<task title>/build/<name>.iso` instead builds an isolated
worker-owned ISO, stages beside it, and keeps both operational and structured
records under `work/<task title>/logs/`. The path is caller-supplied and
validated; worker mode cannot address shared build outputs or mutate shared
preflight, promotion, PNACH, log, or emulator state. Agents must use this form
rather than bare `na228`, compact build recipes, or `na228 build l|t`.
The complete project test command is:

```powershell
.\tests\run.ps1
```

Bare `na228` builds and runs Latest. Compact invocations contain one or two
positional game tokens whose order defines window placement. `l`, `p`, or `t`
runs Latest, Previous, or Test; `bl` and `bt` build and run Latest or Test; and
suffix `w` watches that token's game. `b` remains shorthand for `bl`. For
example, `na228 nun5 btw` builds Test, launches NUN5 and Test side by side, then
watches Test. A registered C file/folder or task-owned overlay-plan path may
follow the watched token: `na228 nun5 blw src/localization` or
`na228 nun5 btw work/Font/operations/jutsu_names_overlay.json`.
`na228 build l|t` provides the uncommon build-only forms.
Build and launch commands never generate CRC-specific PCSX2 files. NA2.28 uses
serial-wide PNACH and GameSettings files directly.
Configured launches preserve existing PCSX2 instances and tile only the newly
started windows. `workshop input [profile]` regenerates input profiles without
building or launching.

Passing one or more registered ISO selectors directly to `na228` launches them
in the requested order. A missing selected ISO fails before any PCSX2 process
is changed.

Translation is composed directly from the pinned profile; there is no standalone
translation-export command or non-strict source-hash mode.

Workshop `scripts/pcsx2/input.ps1` regenerates input profiles
from `input_profiles/sources/Default.ini`, named partial inputs under
`sources/overrides/`, and game-specific partial inputs under
`sources/overrides/games/`.
A partial input replaces existing bindings with the same action name and input
type, then removes other actions using the same binding unless the override
deliberately assigns that binding to multiple actions. `workshop input`
regenerates every profile without changing assignments; `workshop input
<profile>` regenerates and assigns only the selected profile and its game
variants. Generated root-level profiles remain tracked by Git.

Create a fresh task-owned worker runtime with:

```powershell
@pcsx2_scripts/copy_worker.ps1 -WorkerRoot work/<task title>
```

This mandatory command copies the protected `@pcsx2_clean` template and the
shared BIOS together. It refuses an existing destination; the owning task must
first audit and remove its obsolete runtime under the normal work cleanup
policy. Other task-specific shared assets are copied only when needed.

`@pcsx2_scripts/launch.ps1` is the single PCSX2 launcher. Configured launches default to
`dev` and start it in unlimited-speed mode; pass `-Target stable` for an
explicit capped stable check. Agent launches use
`-WorkerRoot work/<task title>` and start the existing task-owned PCSX2 copy in
no-GUI mode. The launcher suppresses process-owned render windows for the
worker startup interval, reads back top-level-window visibility, and terminates
only the newly launched worker if it cannot remain hidden. `-IsoPath` is
optional for configured launches and mandatory and repository-relative for
worker launches; worker paths must be independent copies under
`work/<task title>/inputs/isos/`.
`-PassThru` returns the started process for higher-level orchestration such as
multi-game launch. `scripts/na228/launch_games.ps1` assigns successive
process-local PINE ports beginning at the configured development `PINESlot`
and passes each as `-pine-port`; a compact token ending in `w` sends that
launch's returned port to the watcher.
window tiling. The launcher does not copy or configure PCSX2, inspect or stop
unrelated processes, use PINE, load savestates, capture output, or perform
cleanup.
The unified multi-game launcher inherits the `dev` default. Savestate filing
also defaults to `dev`; pass `-Target stable` to file states from the stable
installation.

Each injection build retains exactly two transport-neutral outputs:
`fragment.bin`, containing the addressed linked EE MIPS code/data, and
`manifest.json`, containing segments, zero-fill ranges, exported symbols,
entrypoints, guarded writes, and execution-refresh requirements. User builds
default to ignored `build/injection/<source>/`; workstreams build under
`work/<exact task title>/injection/`. Compiler objects and linker inputs are
temporary. The maintained pipeline emits no PNACH, installation state,
backup, dispatcher, or alternating-bank files.

Build the project smoke-message candidate into the ignored default output:

```powershell
& .\scripts\lib\run_python.ps1 `
  -PackageSet builder `
  -Script scripts/injection/build.py `
  -NoBytecode `
  -ArgumentList @(
    '--source-id', 'hot_reload_message',
    '--entry', 'project.hot_reload_message'
  )
```

After each successful direct-PINE apply, this message draws the watcher-generated
`HOT RELOAD HH:mm:ss` label at the top-left of the game for 300 rendered frames.
Its zero-filled frame counter is reset by every apply, so the visible marker
replaces log watching as the reload confirmation.

Production entries are declared in the owning feature's
`runtime_injector/entries.tsv`; task-owned overlay plans may select multiple
declared roots and guarded callers. A plan may also supply
`resident_symbol_overrides` when a verified supplied savestate restores an
older resident-symbol layout. Those explicit overrides are also sufficient
when the compatible ISO's shared build record has already rotated out: the
linker bank-links the selected new closure and imports only the named verified
resident symbols. Without overrides, the exact retained build record and its
byte-verified symbol map remain mandatory. Workstreams use the maintained
operational command that builds into their owned tree, reloads the supplied
state, and applies it to their isolated PCSX2:

```powershell
.\scripts\injection\inject_candidate.ps1 `
  -SourceId <source> `
  -Entry <symbol> `
  -OverlayPlan work/<task>/<plan>.json `
  -IsoPath work/<task>/inputs/isos/<matching>.iso `
  -StateSlot <slot> `
  -PinePort <task-port>
```

The applier preserves the VM's prior running/paused state, writes the fragment
and guarded callers while paused, clears execution caches, and uses no PNACH or
cheat-folder state. `scripts/injection/watch.ps1` is the user-only equivalent.
The user-facing `na228 w` command attaches every registered C source under
`src/`; `na228 w injection_test` selects only the root smoke-message source.
A registered C file/folder narrows the attachment, while a direct task-owned
overlay-plan path remains valid for exceptional caller writes. Every watch
also rebuilds the smoke-message source because the visible reload confirmation
is linked into every candidate. The compact `w` suffix chooses the PCSX2
instance, while the following optional C path or plan chooses what is rebuilt.
Standalone `na228 w [C path|plan]` uses the configured development PINE port.
Both forms wait up to 60 seconds for a live
VM with the resident payload and injection target loaded. Agents invoke
`test.ps1` and never run the watcher or its build/apply stages separately.

Profiles consume repository-owned declarative binary-patcher, translation, and
texture-patcher modules. Final output identity comes from root `product.json`
and is composed before the image assembler runs rather than owned by a feature.

`release/build_release.ps1` builds the self-contained Windows release EXE from
the pinned toolchain and default profile. See `docs/RELEASE_PROCESS.md`.

`release/publish_release.ps1` is the guarded publication backend for
`na228 release [version]`; it validates the production package before pushing an
annotated version tag that triggers GitHub Release publication.

When adding a script, place it beside the workflow it supports. Do not add new
files directly under `scripts/`; the root is reserved for this index and
responsibility directories.

## Python package sets

Third-party Python packages are declared once in
`lib/python_packages.json`. Invoke package-bearing scripts through
`lib/run_python.ps1`; do not call a guessed interpreter or probe/install a
package locally. For example:

```powershell
.\scripts\lib\run_python.ps1 `
  -PackageSet imaging `
  -Script scripts/research/localization/compose_font_report_grid.py `
  -ArgumentList @('--help')
```

`NA228_PYTHON` may identify an explicit compatible runtime. Otherwise the
resolver silently selects an available runtime that satisfies the complete
named set.

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
| `scripts/injection/test.ps1` | `9a4ddb5b` | Renamed to `scripts/injection/inject_candidate.ps1` because it is an operational compile/reload/apply command, not a test. |
| `scripts/pcsx2/extract_savestate_screenshots.py` | `a7a19d9e` | Replaced by the user-facing PowerShell implementation `@pcsx2_scripts/extract_savestate_screenshots.ps1`, which accepts either one folder or explicit same-folder savestates. |
| `scripts/pcsx2/move_na228_savestates.ps1` | `82444b3a` | Renamed and generalized as `@pcsx2_scripts/move_savestates.ps1`; pass a configured game or alias before the destination subpath. |
| `scripts/pcsx2/game_commands.ps1` and `launch_pair.ps1` | `dae022c8` | Separate source-game functions and the pair/multi-game alias were consolidated into `na228.ps1` command routing and `scripts/na228/launch_games.ps1`. Pass game selectors directly to `na228`. |
| `scripts/pcsx2/capture_state_screenshot.ps1` | `ec4b8276193bc214b526d5ab4f4f85b240ef7949` | Retired because it serialized a complete savestate solely to obtain a fresh screenshot. Extract `Screenshot.png` directly from an existing state; use `@pcsx2_scripts/pine.py screenshot` for a fresh runtime frame. |
| `injection_lab/gen_pnach.py`, `linker.asm`, `overlay_writer.py`, `production_adapter.py`, `screenshot.ps1`, `test.ps1`, and `watch.ps1` | `35628bb4` | The PNACH transport, alternating banks, install/restore state, standalone screenshot helper, and Lab wrapper were retired after the direct-PINE workflow was proven. Workstreams use the unrelated maintained `scripts/injection/inject_candidate.ps1`; user live editing uses `scripts/injection/watch.ps1`. |
| `scripts/archive/replace_iso_file_same_size.ps1` | `858da62aacc5d9571bdef072e36b484efddc15e9` | Direct unverified ISO mutation was superseded by guarded, hash-pinned replacements through `na228_builder.image_assembler`. |
| `scripts/na2/check_log_crc.ps1` | `ce4b06c57a7e1a28124c7a8efffd38169723d915` | Manual log/PNACH comparison was superseded by `@pcsx2_scripts/iso_identity.ps1`. |
| `scripts/na2/get_elf_crc.ps1` | `858da62aacc5d9571bdef072e36b484efddc15e9` | The redundant command wrapper was removed; `@pcsx2_scripts/pcsx2_elf_crc.ps1` remains the shared tested implementation. |
| `scripts/actualization/links.ps1` and `test_links.ps1` | `a972fc1` | Retired when stable and development PCSX2 were configured to consume `@pcsx2_files/` directly; no copy or link synchronization step remains. |
| `scripts/na2/test_memory_card.ps1` | `5e2f7a49723ad6b1ae0262880588bb7926e880c3` | Retired with the later agent PCSX2 runtime framework; there is no maintained replacement. |
| `scripts/na2/test_test_memory_card.ps1` | `5e2f7a49723ad6b1ae0262880588bb7926e880c3` | Retired with the later agent PCSX2 runtime framework; there is no maintained replacement. |
| `scripts/na2/pine.ps1`, `provision_test_pcsx2.ps1`, `test_operation.ps1`, `test_process_ownership.ps1`, `test_runtime.ps1`, `test_test_operation.ps1`, `test_test_pine.ps1`, `test_test_runtime.ps1`, `test_worker_pcsx2.ps1`, and `worker_pcsx2.ps1` | `4fe8bc3b0c77633b83de519a1913f2e8776a6770` | The unsolicited agent PCSX2 ownership, PINE-operation, provisioning, and runtime framework was removed. Only the minimal hidden launcher remains. |
| `scripts/research/translation/check_translation_lengths.ps1` | `819c0999f6adf5686ce5f75ea82157e697469ee8` | Its fixed-slot `old`/`new` assumptions are obsolete; translation importer and string patcher validation now enforce encoding and capacity rules. |
| `scripts/research/translation/build_mapping_ids.ps1` | `4687470b31db4ff8a2a46071808a35f9282745cf` | The temporary mapping-ID worker build was retired after visible rows were promoted; canonical `translation_importer/mappings.tsv` and ordinary profile builds are maintained. |
| `scripts/research/translation/sync_rebuild.py` | `4687470b31db4ff8a2a46071808a35f9282745cf` | The parallel candidate inventory was retired; edit and validate canonical `translation_importer/mappings.tsv` directly. |
