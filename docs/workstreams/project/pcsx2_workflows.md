# PCSX2 workflows draft

Status: tracked discussion draft. This records the selected design but is not
yet canonical policy or an implementation contract.

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
- The current `injection_lab/` top-level subsystem will be assimilated into the
  normal source, script, build, and documentation trees.

## Target layout

```text
src/
  runtime.h
  hot_reload_test.c

scripts/
  injection/
    build.py
    apply.py
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
- Invokes the external EE compiler and resolves relocations and Current
  imports.
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

### `scripts/injection/watch.ps1`

- User-only interactive convenience.
- Watches explicitly selected source, declaration, and overlay-plan inputs.
- Debounces saves and runs builds serially.
- Calls `build.py`, then `apply.py`.
- Contains no compiler, linker, manifest, or PINE implementation.

### `scripts/pcsx2/pine.py`

- Provides the small shared PINE client and command-line operations used by
  maintained scripts and workstreams.
- Supports ordinary status, read, and write operations plus the selected
  pause, resume, execution-cache refresh, and screenshot controls.
- Remains a protocol tool rather than a complete workstream wrapper.

## PCSX2 PINE controls

The development PCSX2 fork will expose three additional synchronous controls:

1. pause the VM;
2. resume the VM; and
3. clear EE execution caches without reloading patch or cheat files.

The existing screenshot control remains available. The existing
reload-patches control is independent of the new direct-memory transaction.

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
   when runtime positioning is required.
3. Load the supplied state before applying the candidate.
4. Run `build.py` once into `work/<exact task title>/injection/`.
5. Run `apply.py` once against that folder and the task-owned PINE port.
6. Capture evidence with the shared PINE screenshot operation when needed.
7. Repeat the build/apply commands manually for another candidate.
8. After user acceptance, integrate the same canonical source and declarations
   through the normal builder and perform the required clean validation.

WW has no watcher and no higher-level workflow wrapper. Agents do not use
PNACH, cheat directories, shared PCSX2 installations, filesystem
synchronization, or task-local injection scripts.

If the supplied state has already passed behavior that cannot be re-entered,
the workstream requests an earlier state instead of adding an input or
navigation workaround.

## Structural migration

- Refactor useful compile/link logic from
  `injection_lab/production_adapter.py` into
  `scripts/injection/build.py`.
- Refactor direct-memory application from
  `injection_lab/overlay_writer.py` into
  `scripts/injection/apply.py` and the shared PINE client.
- Move and simplify `injection_lab/watch.ps1`.
- Replace the standalone screenshot script with the shared PINE screenshot
  command.
- Move the project-level C example from `injection_lab/src/` to root `src/`
  with meaningful names.
- Move production entry declarations beside their owning runtime-injector
  feature.
- Remove `gen_pnach.py`, `linker.asm`, `test.ps1`, Lab PNACH transport,
  install-state handling, and the nested Lab ignore file.
- Preserve useful imported-source provenance and runtime-injection findings in
  maintained project documentation before removing the Lab README.
- Remove the empty `injection_lab/` directory after migration.

## Implementation order

1. Update this tracked design before code changes.
2. Add and validate the three PINE controls in the development PCSX2 fork.
3. Refactor compile/link into the two-file builder contract.
4. Implement the transactional direct-PINE applier.
5. Reduce the watcher to build/apply orchestration.
6. Move retained source/declarations and remove the PNACH-era Lab files.
7. Validate consecutive UW saves without restarting PCSX2.
8. Validate WW against an established candidate in a task-owned hidden clone.
9. Confirm that neither workflow transports candidates through cheat files.
10. Update canonical policy and operational documentation only after the
    implementation contract is proven.

No additional proof of concept is required: existing Font work has already
proven the C compiler/linker path, and prior workstream testing has already
proven direct PINE EE-memory writes.

Recommended implementation effort: High.
