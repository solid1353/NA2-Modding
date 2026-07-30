# PCSX2 runtime-injection workflows

Status: maintained Project workflow. Agent requirements remain authoritative in
`AGENTS.md` and `docs/policies/testing.md`.

In this document, **UW** means user workflow and **WW** means workstream
workflow.

## Boundary

- User interactive work and agent work are separate workflows.
- Runtime injection is development evidence, not release acceptance. Accepted
  behavior still needs a clean normal build and its applicable integration
  validation.
- Agents never use PNACH or cheat files to transport runtime candidates.
- The maintained compiler/linker produces transport-neutral files consumed by
  direct PINE application.
- The former top-level `injection_lab/` subsystem is assimilated into the normal
  source, script, build, and documentation trees.

## Target layout

```text
src/
  runtime.h
  hot_reload_test.c

scripts/
  injection/
    build.py
    apply.py
    test.ps1
    watch.ps1
  pcsx2/
    pine.py

build/
  injection/
    <target>/
      fragment.bin
      manifest.json
```

`build/` is already ignored. No additional ignore rule is required for
`build/injection/`.

Project-level EE C belongs under root `src/`. Feature-owned production C and
its declarations remain with the owning feature, for example under
`na228_builder/features/localization/runtime_injector/`.

Workstreams place generated candidates under
`work/<exact task title>/injection/` instead of the shared build directory.

## Generated contract

Each successful build produces exactly two persistent files:

- `fragment.bin`: compiled and fully linked EE MIPS code and initialized data.
- `manifest.json`: the fragment's addressed segments, required zero-fill
  ranges, exported symbols, resolved entrypoints, guarded data/caller writes,
  and execution-refresh requirement.

Compiler objects, linker inputs, and other intermediates are temporary and are
not retained as workflow outputs. There are no generated PNACH, linker-ASM,
installation-state, backup, or separate bank files.

## Maintained scripts

### `scripts/injection/build.py`

- Consumes canonical C, runtime declarations, Current resident symbols, and an
  optional task-owned overlay plan.
- An overlay plan may provide `resident_symbol_overrides` for verified symbols
  restored by an older supplied savestate. Overrides affect only symbols that
  the selected closure actually imports and are recorded in the manifest.
- Invokes the external EE compiler and resolves relocations and resident
  imports, using Current's exact symbol map by default.
- Produces only `fragment.bin` and `manifest.json`.
- Contains no PINE, PCSX2 process, cheat, or watcher behavior.

### `scripts/injection/apply.py`

- Consumes one generated fragment/manifest pair.
- Reads the initial PCSX2 state through PINE.
- Pauses the VM synchronously when it was running.
- Applies the fragment, zero-fill ranges, and guarded writes.
- Refreshes EE execution state.
- Resumes only when the VM was running before application.
- Contains no PNACH installation, synchronization, removal, recovery, or
  backup lifecycle.

### `scripts/injection/test.ps1`

- Standard workstream entry point for savestate-based C injection.
- Requires the independent compatible ISO under the owning task's
  `inputs/isos/`, the supplied savestate slot, and the task-owned PINE port.
- Invokes `build.py`, reloads the state and waits for completion, then invokes
  `apply.py`; agents do not run those stages separately for runtime testing.

### `scripts/injection/watch.ps1`

- User-only interactive convenience.
- Watches explicitly selected source, declaration, and overlay-plan inputs.
- Debounces saves and runs builds serially.
- Calls `build.py`, then `apply.py`.
- Exits immediately if its initial build or apply fails; after a successful
  start, a later save failure is reported and the watcher remains available
  for the next edit.
- Contains no compiler, linker, manifest, or PINE implementation.

### `scripts/pcsx2/pine.py`

- Provides the small shared PINE client and command-line operations used by
  maintained scripts and workstreams.
- Supports ordinary status, read, and write operations plus the selected
  pause, resume, execution-cache refresh, and screenshot controls.
- Remains a protocol tool rather than a complete workstream wrapper.

## PCSX2 PINE controls

The development PCSX2 fork exposes these custom parameterless controls:

1. `0x11`: queue a native screenshot;
2. `0x12`: pause the VM synchronously;
3. `0x13`: resume the VM synchronously; and
4. `0x14`: clear EE execution caches without reloading patch or cheat files.

The older `0x10` reload-patches control remains available but is independent of
the direct-memory transaction.

Synchronous pause makes live code replacement a single transaction. The new
workflow therefore uses one fixed development memory reservation and removes
the old alternating A/B banks, active-bank pointer, and bank-switching files.

## User workflow

1. Launch the visible development PCSX2 installation and navigate normally.
2. Start `watch.ps1` for the selected source and optional overlay plan.
3. Edit and save C.
4. The watcher invokes `build.py`.
5. On success, the watcher invokes `apply.py`.
6. The applier briefly pauses PCSX2, applies the candidate, refreshes execution
   state, and restores the prior running/paused state.
7. The user observes the result and repeats by saving another edit.

UW does not require PNACH generation, cheat synchronization, installation
state, a remove command, or a clean restart between ordinary rebuilds.

## Workstream workflow

1. Create or refresh only the workstream's task-owned PCSX2 clone from
   `@pcsx2_clean`; assign a unique PINE port and keep the process hidden.
2. Copy only inputs required by the task, including a user-supplied savestate
   and an independent full copy of its exact matching ISO under
   `work/<exact task title>/inputs/isos/`. Record the ISO SHA-256 and disc
   identity with the state provenance; never use a symlink or hardlink.
3. Pass only that task-owned ISO to the worker launcher and `test.ps1`. Worker
   processes never open shared Current, Previous, or Candidate.
4. Run `test.ps1` with the supplied savestate slot. It builds into
   `work/<exact task title>/injection/`, reloads that slot, waits for the load,
   applies the candidate, invalidates the JIT, and resumes.
5. Capture evidence with the shared PINE screenshot operation when needed.
6. Repeat `test.ps1` for another candidate.
7. After user acceptance, integrate the same canonical source and declarations
   through the normal builder and perform the required clean validation.
8. Delete task-owned ISO copies as soon as their compatible state batch or
   current test no longer needs them. Runtime completion leaves no worker ISO
   copies behind; only provenance remains.

WW uses the maintained `test.ps1` wrapper and no watcher. Agents do not use
PNACH, cheat directories, shared PCSX2 installations, filesystem
synchronization, or task-local injection scripts.

If the supplied state has already passed behavior that cannot be re-entered,
the workstream requests an earlier state instead of adding an input or
navigation workaround.

## Historical source and migration

The imported `NA2-C.zip` used for the original investigation has SHA-256
`8A4D94465C4F7938DCC2D49D3DAA268BDF800AD7E89112B8E09BAA6EE58D289E`.
Its exact supplied tree is preserved in commit
`9ef9dc93ec276a08b431192ca0fe798b4f834ada`; commit
`e1a0d9b604009a82afbda18bbf8423988b5e5ce3` removed that inconsistent snapshot
from the live tree. The archived VS Code task compiled C, linked it with
Armips, rewrote a CRC-named PNACH, and relied on PCSX2 reloading that file.

The maintained workflow retains the proven EE compiler/object extraction,
relocation, Current-symbol import, and exact guarded-caller logic. It removes
PNACH transport, alternating banks, dispatcher pointers, installation state,
backup/removal commands, and Lab-specific actualization handling. Historical
Lab scripts are recoverable at commit `35628bb4`.

## Validation

On 2026-07-30, an isolated hidden Project worker validated status, synchronous
pause, cache-only refresh, resume, direct fragment/caller writes, readback, and
native PINE screenshot output. Two different root C builds were applied
consecutively to the same fixed reservation without restarting PCSX2; the
second transaction found the caller already active, replaced the fragment
while paused, cleared execution caches, and resumed the VM. The test emitted no
PNACH file. The custom PCSX2 source is commit
`9cf3890b8e98bed6242d66d764732177dd78b450`; the validated Windows executable
has SHA-256
`A2101F8FC9F3ADF9C5E8A936296F8C2D2A383B67495A0425AFBC62ECDB2607F9`.
