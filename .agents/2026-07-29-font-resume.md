# Font resume handoff — 2026-07-29

## Objective and task

- Workstream/task title: `Font`.
- Selected work: the user-declared Continuous `Layout parity batches` epic.
- Current subtask: Priority 2, refreshed ss3–ss4 Customize Jutsu name list.
- Objective: reproduce NUN5 wrapping and positioning for the shared selected/list
  title caller, using ss3 as the exact visual target and ss4 as no-overflow
  coverage, without regressing the previously working Practice-title family.

## Phase, approval, and effort

- Phase: implementation candidate prepared; runtime validation not started.
- Approval: the epic, Continuous mode, self-prioritization, and one-subtask
  commit/push/report flow were explicitly approved. Existing approval remains
  valid on resume unless live drift invalidates the approach.
- Current requested effort: max.
- The user issued `zxc`; stop here without committing the incomplete
  implementation.

## Completed

- Priority 1 Command Chart implementation was committed as `9808766f`.
- Its actual post-change grid was visibly delivered:
  `work/Font/artifacts/command_relationships_v2/command-chart-ss1-ss2-row-aware-grid.png`.
- Stale Pending-grid state was cleared and pushed in `7f6e6ebb`
  (`[Font] Record Command Chart grid delivery`).
- Reconfirmed the Priority 2 shared caller:
  - NA2 BTL function `FUN_00878820`.
  - NUN5 homolog `FUN_00894F60`.
  - BTL file hook `0x1C4B98`.
  - live hook `0x00878A98`.
- Reconfirmed NUN5 behavior: X `24`, right edge `376` (width `352`),
  caller Y minus `14`, line height `20`, and wrapped output. The source string
  contains no newline; the renderer performs wrapping.
- Canonical runtime-injector package compile/load passed with the current C
  candidate: 63 fragments, 80-byte Practice-title fragment, 3 relocations,
  33 active edits.
- Focused permanent verifier run produced 4 passes and 1 unrelated known error:
  its expected-export set still omits the already-committed
  `font_v2_command_icon_offset`.

## Recoverable stashed implementation

The incomplete candidate is preserved in Git stash commit:

`9d1f6b9296a9646ac0fbbe214a60837746388068`

Stash subject:

`On master: [Font] zxc Priority 2 Jutsu title candidate`

It contains changes to exactly one owned canonical Font path:

`na228_builder/features/localization/runtime_injector/sources/font_v2_core.c`

The candidate:

- changes the shared Practice/Jutsu title X from `31.2` to `24`;
- changes the Y offset from `-6.8` to `-14`;
- adds a 40-unit box and two-line limit;
- routes `font_v2_practice_title_entry` through
  `font_v2_wrapped_body_common`;
- uses the existing `font_v2_title_callback`.

The stash was verified against its first parent: one file changed, 24
insertions, 6 deletions, and `git diff --check` passed. The canonical worktree
was clean afterward. Do not drop this stash before recovering the candidate on
resume. It is not runtime-proven and must not be committed yet.

## Important corrected finding

`work/Font/checkpoints/ss3-jutsu-title-blocked.md` is partly stale. Its claim
that a new dedicated callback is required is contradicted by the retained
callback bytes:

`4800ECC44C00EDC4C4080E0800000000`

They decode as loads of the prepared session draw X/Y followed by a tail jump
to the native boxed renderer, so the existing `font_v2_title_callback` is the
current correct candidate. Correct or supersede that task-owned checkpoint
before relying on it.

## Runtime pipeline state

- No Font worker, watcher, ISO build, or runtime injection was started after
  the current candidate was prepared.
- Project corrected its earlier explanation: the intended candidate flow is
  compile/link canonical C plus the task-owned plan into addressed writes,
  load the supplied task-owned state while stopped, apply the bank/dispatcher/
  caller writes directly over PINE, invoke opcode `0x10` for patch reload/JIT
  invalidation, then resume and capture.
- No watcher, PNACH transport, cheat synchronization, install state, new
  wrapper, or new generic CLI is required by that corrected design.
- Live `AGENTS.md` at stop still contains the contradictory earlier rule saying
  to wait for a maintained generic direct-PINE command. Project was asked to
  remove only that admitted erroneous policy text. Do not perform runtime
  writes until live policy is reconciled.
- Notifications are muted in `.agents/notifications.json`; no stop
  notification was queued.

## Inputs and retained evidence

- Active states:
  `work/Font/inputs/sstates/batches/2026-07-29-c-pipeline-na228-ss1-10/`.
- Active screenshots:
  `work/Font/inputs/screenshots/batches/2026-07-29-c-pipeline-na228-ss1-10/`.
- ss3 NA2.28 SHA-256:
  `CB1F907C16213EAF0E88B70564A028DD08E3963E43D1773045D17E633B408C91`.
- ss4 NA2.28 SHA-256:
  `F0A7339BD927B367BF3C0BA393FEB4416FDB3206E756D186E8122D0AB32AE777`.
- Priority 2 baseline grid:
  `docs/workstreams/font/epics/ss2-6-layout/2-jutsu-name-list.png`.
- Earlier accepted/agent-validated Practice-title evidence:
  `work/Font/artifacts/autofit_v2/titles/title-family-v2-grid-01.png`
  and `title-family-v2-grid-02.png`.
- Task-owned overlay draft:
  `work/Font/operations/jutsu_titles_overlay.json`.

## Remaining work and uncertainties

1. Refresh live Git and mandatory policies; confirm the erroneous generic-CLI
   prohibition has been corrected.
2. Compare the retained Practice-title result against the current shared
   candidate. Determine whether the NUN5 shared geometry is safe globally or a
   reliable context split is required.
3. Correct/supersede the stale task-owned ss3 checkpoint.
4. Run the task-specific direct-PINE candidate only after policy reconciliation:
   load supplied ss3 while stopped, apply addressed writes, invalidate JIT,
   resume, and capture. Do not navigate menus.
5. Tune ss3 to NUN5; validate ss4 only for overflow as instructed.
6. Update canonical Font knowledge in the same commit as the disassembly-derived
   implementation.
7. Validate, commit/push only Font-owned files, compose and visibly deliver the
   NUN5-left/Current-right post-change grid, then continue Priority 3 under
   Continuous mode.

Main uncertainty: the existing hook is shared with previously working Practice
titles. Static NUN5 evidence favors the new broad geometry, but retained runtime
evidence must be checked before committing.

## Git state at stop

- Branch: `master`.
- HEAD/origin at checkpoint start: `7f6e6ebb`.
- Remediation HEAD/origin before this handoff update: `a5906fc8`.
- Owned incomplete change: recoverable stash commit
  `9d1f6b9296a9646ac0fbbe214a60837746388068`, containing only
  `na228_builder/features/localization/runtime_injector/sources/font_v2_core.c`.
- Canonical working tree: clean after the stash.
- This handoff update must be committed and pushed by itself; the C candidate
  remains outside the canonical working tree.

## Exact first resume action

Read this handoff and the live Font/epic policies, refresh Git, verify stash
commit `9d1f6b9296a9646ac0fbbe214a60837746388068` still contains only the recorded
Font path, then remove/commit/push this handoff as required by the live resume
rule. Apply that exact stash to recover the C candidate, verify the resulting
single-path diff, and only then inspect whether Project removed the
contradictory generic-direct-PINE rule. Resume the Practice-versus-Jutsu
isolation before any runtime operation.
