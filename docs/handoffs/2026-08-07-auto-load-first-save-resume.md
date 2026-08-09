# Resume: automatic first-save loading

## Outcome

Make NA2.28 silently load the first memory-card save during startup, wait for
the load to finish, and then enter the main menu without restoring the removed
title or Load-list screens. Preserve a deliberate way to enter the menu without
loading a save.

## Recovery

- Stash: `stash@{0}: On master: General: automatic first-save loading paused
  before silent-startup redesign`
- Stash object: `6d038f12dc2743a94c28093e8249342fea4b24e2`.
- Restore with `git stash apply 'stash@{0}'`.
- The stash contains only these four task-owned files:
  - `docs/knowledge/game/startup.md`
  - `na228_builder/features/qol/README.md` (when recovering the stash, reconcile
    this historical path into the current `docs/features/qol.md`)
  - `na228_builder/features/qol/binary_patcher/edits.tsv`
  - `na228_builder/features/qol/binary_patcher/patches.tsv`
- Verify all four files and the exact recovered diff before dropping the stash.

The previous stash object
`31d6f19d730c830a491a79bee02d300723b3529f` was explicitly deleted when this
replacement stash was created.

## Preserved inputs and analysis

- Base NA2 states copied from
  `@pcsx2_dev/sstates/SLPS-25837 (C0659AD1).01-04.p2s` are under
  `work/General/inputs/load-first-current/base-na2/`; extracted EE memory is
  under `work/General/analysis/load-first-current/base-na2/`.
- Current NA2.28 states copied from
  `@pcsx2_dev/sstates/SLOP-NA228 (6E79CD2E).01-02.p2s` are under
  `work/General/inputs/load-first-current/sstates/`; extracted EE memory is
  under `work/General/analysis/load-first-current/states/`.
- The earlier tested Latest ISO's extracted boot ELF is
  `work/General/analysis/load-first-current/SLOP_NA2.28`.
- The current candidate ELF is
  `work/General/temp/auto-load-first-save-candidate-v1/SLPS_258.37` with SHA-256
  `8265FB9A2B244E80CD485191C1A15F31DB748EDEBD7AD16132243A2F199D4C93`.
- Reusable startup and Save/Load-controller findings are in
  [`../knowledge/game/startup.md`](../knowledge/game/startup.md).

## Current candidate

- The rejected `ELF-Q010-23` candidate was removed. The replacement candidate
  changes `ELF-Q009-03` at file offset `0xE1340` to return native title result
  `2` (`Continue`).
- Continue constructs the shared Save/Load controller in load mode. The guarded
  `ELF-Q010-14` replacement at file offset `0xE5108` fixes the selected record
  at zero, calls the native load operation in mode `1`, retains the unchanged
  save body for other modes, and rejoins the controller's native post-operation
  states. It ends before the existing guarded edit at `0xE5140`.
- Binary-patcher validation passed: one target, four groups, ten patches, and
  32 edits; the selected dry-run plan contained two atomic patches and 24 edits.
- Integrated build `20260807_111358_863_pid17324` succeeded and promoted
  `build/NA v2.28 - Latest.iso`, SHA-256
  `80471C65AF0B8B15A30BF8459C621E9FA3D8850C6182C159DB668F322179527B`.
- Independent ISO inspection verified the embedded ELF contains the candidate
  bytes at `0xE1340` and `0xE5108` and the existing `ELF-Q010-16` bytes at
  `0xE5140` without overlap corruption.
- No E2E or runtime validation was run. No runtime behavior has been confirmed.
  The candidate remains uncommitted and is not accepted.

## Design state

- The user selected silent, blocking loading rather than asynchronous loading:
  startup may wait for the memory-card operation, but it must not ask a question
  or display the Load list.
- Entering the menu without loading a save is also a valid deliberate startup
  choice. Unconditional silent loading would incorrectly remove that choice.
- The smallest proposed preservation mechanism is a held-button startup
  override that skips loading and enters the menu unsaved. No button or exact
  input point has been selected.
- This user-visible behavior change has not received a consolidated serious-work
  snapshot or `approved`/`qwe` authorization. Do not implement the redesign
  until that boundary is completed.

## Remaining work

1. Apply the new stash and verify recovery of all four task-owned files.
2. Finish the design of the deliberate no-save override, then present the
   consolidated implementation snapshot and obtain `approved` or `qwe`.
3. Trace or adapt the lower-level native first-record load so startup waits for
   it without constructing or displaying the Continue/Load-list UI.
4. Replace the current candidate with a guarded, script-owned silent-startup
   candidate while preserving the explicit no-save path.
5. Do not run E2E. Use user runtime testing, and keep the patch uncommitted until
   the user confirms the result.
6. After acceptance, finalize canonical documentation, commit and push the
   feature, remove this handoff/task link, and drop the recovered stash.
