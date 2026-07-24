# Font resume handoff — 2026-07-25

## Objective and state

- Task/chat title: `Font`
- Selected `TASKS.md` entry: `[Investigate](work/__sstates/translation/font) → Implement proper autofit/positions everywhere.`
- Current phase: approved execution, stopped safely by the user's `zxc`.
- Approved plan: fix one screen/caller family at a time, reuse shared wrappers,
  compare against matched NUN5 captures, and commit/push each finished fix
  before starting the next.
- Recommended effort: `max`.
- Approval state: approved by the user's earlier `qwe`; approval remains valid.
- Recurring user preference: prefer a broad renderer-logic port over selective
  per-screen patching when the behavior is genuinely shared.

## Completed at this boundary

- Commit `3d52a14` (`[Font] Port shared NUN5 text fitting and layout`) is pushed
  to `origin/master`.
- The committed Localization package now has five Font patches and 33 Font
  edits:
  - `font_nun5_glyphs`
  - `font_renderer_metrics`
  - `font_controls_auto_fit`
  - `font_modal_alignment`
  - `font_layout_wrappers`
- Shared NUN5 logic now supplies ordinary-space advance, newline advance,
  secondary tracking, logical measurement, Controls shrink-only fitting,
  selected/unselected confirmation-choice placement, Practice pause-list
  fitting, confirmation-body placement, and the character-return body box.
- Final Controls measurement for `Ultimate Jutsu Prep` is 157 pixels wide with
  center X 154 in both NUN5 and current NA2. The latest paired crop is
  `work/Font/artifacts/autofit_everywhere/modal_prototype_v1/pairs/02_control_settings_shared_fit_zoom.png`.
- Every new helper was relocated into the compact settled-boot block at EE
  runtime `0x003D3E00..0x003D4388` / ELF file
  `0x002D3F00..0x002D4488`. Clean ELF plus 16 saved states were zero there, and
  a five-second marker audit proved the start/middle/end sentinels survive.
  Immediate PINE readiness is not sufficient evidence because the boot ELF may
  still be copying at that moment.
- The current Localization feature pin is
  `1C6115C20D99BD053CCF44E7C2C4605AA826BEBE3A0079443EDE22EEA43206EF`
  with `bypass_check=0`.

## Validation completed

- Deterministic Font asset verification passed for all eight blobs.
- Binary package validation passed: 7 targets, 9 groups, 91 patches, 314 edits.
- Focused Font plan passed: 5 atomic patches, 33 edits.
- Profile load confirmed the declared and actual Localization hashes match.
- Focused unit tests passed: 26/26
  (`na2_patcher.tests.test_binary_patcher` and
  `na2_patcher.tests.test_profile`).
- The final isolated worker build passed:
  - ISO: `work/Font/build/font-test.iso`
  - SHA-256:
    `45253A4B4C89573C20081EFA7B68EC4C218C60E53BD1263AA29FDB60C373B37E`
  - Build record:
    `work/Font/logs/builds/20260725_021057_424_pid48600/`
  - Result: worker ISO updated; Current/Previous remained unchanged; no
    rotation.

## Incomplete runtime boundary

- The final post-relocation guarded runtime readback and ten-state capture were
  not started because the user issued `zxc`.
- The operation plan is ready at
  `work/Font/operations/autofit_modal_prototype_v1.json`.
- It has 42 actions: a five-second settled-boot wait, eleven exact guarded
  readbacks of the final hooks/helpers, then ten load/wait/capture triplets.
- The corresponding patched task-owned states are under
  `work/Font/artifacts/autofit_everywhere/modal_prototype_v1/states/`.
- Expected paired outputs are under
  `work/Font/artifacts/autofit_everywhere/modal_prototype_v1/pairs/`.

## Remaining caller families

After the pushed shared-fit checkpoint passes final runtime regression, continue
one family at a time in this order:

1. Practice command-explanation overflow/positioning.
2. Collection movie-list overflow/positioning.
3. No-memory-card prompt overflow/positioning.

Do not start the next family before the current family is visually accepted and
committed/pushed. Reuse a shared wrapper when static and runtime evidence proves
the callers share it.

## Retained task-owned artifacts

The whole `work/Font/` directory is deliberately retained; no graceful-stop
cleanup was performed.

- `work/Font/README.md`: task-owned artifact inventory and provenance.
- `work/Font/inputs/`: copied user savestates and other read-only inputs.
- `work/Font/reference/`: matched NUN5 reference material.
- `work/Font/analysis/autofit_everywhere/`: state preparation, paired-capture,
  metric analysis, and the settled-cave probe scripts/results.
- `work/Font/artifacts/autofit_everywhere/modal_prototype_v1/`: patched states,
  screenshots, pairs, and operation result location.
- `work/Font/operations/`: maintained guarded operation plans, including the
  ready final plan.
- `work/Font/build/font-test.iso`: final worker ISO for immediate resume.
- `work/Font/build/font-cave-probe.iso`: disposable only after the settled-cave
  conclusion and runtime result are fully assimilated; it was not removed
  during graceful stop.
- `work/Font/logs/`: worker-build and guarded-runtime records, including the
  final build record named above.
- `work/Font/appearance_parity/`, `experiments/`, `verification/`, `workers/`,
  and `temp/`: earlier Font evidence and intermediate material retained to
  avoid destructive cleanup during `zxc`.

Canonical reusable findings are committed in
`docs/knowledge/localization/font/README.md`; active execution context is in
`docs/workstreams/font/plan.md`.

## Git and resource state

- HEAD: `3d52a14` (`[Font] Port shared NUN5 text fitting and layout`)
- Remote: `origin/master` is at the same commit.
- Tracked Git status before this handoff: clean.
- Owned staged canonical paths: none.
- Owned unstaged canonical paths: none.
- Ignored task-local change:
  `work/Font/operations/autofit_modal_prototype_v1.json` contains the new
  settled-boot readback prefix and must be retained.
- No Font-owned PCSX2 instance was launched after the final build, so there is
  no process to close and no ownership descriptor/capability to retain.
- No Current/Previous/Candidate promotion state, physical input, memory card,
  Git transaction, build transaction, PCSX2 instance, or other exclusive
  resource is held.
- No pending wakeup exists.
- `.agents/notifications.json` has `muted: true`, so no Notifications-task
  message is sent for this stop.

## Resume procedure

1. Read live `AGENTS.md`, `TASKS.md`, the Font workstream policy, this handoff,
   Git state, and the retained `work/Font/` state.
2. If drift validation succeeds, delete this handoff and commit/push that
   deletion before resuming, as required by the graceful-resume rule.
3. Do not rebuild unless drift invalidates the retained worker ISO. Run the
   maintained guarded launcher:

   ```powershell
   & .\scripts\na2\test_launch.ps1 `
     -WorkerRoot 'work/Font' `
     -IsoPath 'work/Font/build/font-test.iso' `
     -OperationPlan 'work/Font/operations/autofit_modal_prototype_v1.json'
   ```

4. Confirm every settled-boot readback and all ten captures complete. Regenerate
   the paired grids with
   `work/Font/analysis/autofit_everywhere/make_modal_prototype_pairs.py`.
5. Inspect Controls plus the already accepted Practice pause-list, Practice
   quit, character-return, and Collection-quit families for regression.
6. If the pushed shared-fit checkpoint passes, begin only the Practice
   command-explanation family. If it fails, correct the pushed checkpoint in a
   new Font commit before proceeding.

Required user input: none before resuming.

Uncertainty: static validation and the final isolated build are complete, but
the final runtime readback/capture after compact helper relocation remains
pending.
