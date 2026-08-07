# Resume: automatic first-save loading

## Outcome

Make NA2.28 load the first memory-card save during startup, then enter the main
menu without restoring the removed title or Load-list screens.

## Recovery

- Stash: `stash@{0}: On master: General: auto-load first save pending user validation`
- Stash object: `31d6f19d730c830a491a79bee02d300723b3529f`.
- Restore with `git stash apply 'stash@{0}'`.
- The stash was created on commit `090b83e4`, before the policy/documentation
  refactor. Reconcile its documentation hunks with current canonical files; do
  not restore deleted or superseded documentation structure.
- Verify all four task-owned files were recovered before dropping the stash.

The stash contains changes to:

- `docs/knowledge/runtime/menu_input.md`
- `na228_builder/features/qol/README.md`
- `na228_builder/features/qol/binary_patcher/edits.tsv`
- `na228_builder/features/qol/binary_patcher/patches.tsv`

Its `ELF-Q010-23` implementation is a rejected candidate, not resumable final
code. After applying the stash for recovery, remove or replace that edit and
correct its pending documentation before producing another candidate.

## Preserved inputs and analysis

- Base NA2 states copied from
  `@pcsx2_dev/sstates/SLPS-25837 (C0659AD1).01-04.p2s` are under
  `work/General/inputs/load-first-current/base-na2/`; extracted EE memory is
  under `work/General/analysis/load-first-current/base-na2/`.
- Current NA2.28 states copied from
  `@pcsx2_dev/sstates/SLOP-NA228 (6E79CD2E).01-02.p2s` are under
  `work/General/inputs/load-first-current/sstates/`; extracted EE memory is
  under `work/General/analysis/load-first-current/states/`.
- The tested Latest ISO's extracted boot ELF is
  `work/General/analysis/load-first-current/SLOP_NA2.28`.
- Reusable state evidence and the rejected-controller boundary are preserved in
  [`../../knowledge/game/startup.md`](../../knowledge/game/startup.md).

## Current state

- The tested Latest ISO contains the rejected candidate bytes at runtime
  `0x001E5008`, proving build integration. The user confirmed that it produces
  no automatic load.
- That address belongs to the shared Save/Load controller. Current startup
  states reach the main menu without allocating that controller.
- Bare `na228` builds and launches Latest through the low-level PCSX2 launcher
  without a `-memory-card` argument, so it uses `SLOP-NA228.ini`'s configured
  `Slot1_Filename` (`NA v2.28.ps2`). Workshop game-selector launches separately
  derive build-postfixed card names; do not assume bare `na228` does.
- No implementation commit exists. The earlier candidate commit was removed
  from local and remote branch history; only the named stash retains it.

## Remaining work

1. Apply the stash and retain it until recovery is verified.
2. Remove the rejected `ELF-Q010-23` candidate and its incorrect behavioral
   claims.
3. Trace the native first-save operation inside the title/startup sequence that
   current `ELF-Q009` bypasses at runtime `0x001E1340`.
4. Implement a guarded, script-owned candidate that performs that native load
   before entering main state `4 / 1`, without displaying the removed screens.
5. Do not run E2E for this task. The user explicitly rejected E2E because the
   startup screenshots are expected to change. Use user runtime testing.
6. Keep the patch uncommitted until the user confirms the runtime result. After
   acceptance, finalize canonical documentation, commit, push, remove this
   handoff/task link, and drop the recovered stash.
