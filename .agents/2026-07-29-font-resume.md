# Font resume handoff — 2026-07-29

## Objective and task

- Task title: `Font`
- Selected work: user-declared Layout/autofit epic, Continuous mode.
- Objective: process the refreshed NA2.28/NUN5 ss1–ss10 comparison cases one
  caller family at a time through the maintained C/runtime-injector pipeline.
- Current recommended effort: high.
- Approval: the epic plan and Continuous execution are approved. The user
  explicitly ordered one subtask at a time, automatic prioritization, and C
  pipeline use. The Continuous override waives intermediate regression-review
  stops but does not manufacture user acceptance.
- User instruction at this boundary: `zxc`.

## Completed

- Command Chart ss1/ss2 relationship rows were implemented, validated against
  both supplied states, committed, and pushed in
  `e4a9abda5622f56ca590c2d874ec962970d7fe87`
  (`[Font] Align Command Chart relationship rows`).
- Its composed comparison is retained at
  `work/Font/artifacts/command_relationships/command-chart-ss1-ss2-agent-validated-grid.png`.
- General's speculative-wakeup correction is live at
  `c01f974c181335a5881edc1b0230d186f71ad555`.

## Critical correction at stop

- The refreshed NA2 ss3 is
  `work/Font/inputs/sstates/batches/2026-07-29-c-pipeline-na228-ss1-10/ss03_NA228.p2s`,
  SHA-256
  `CB1F907C16213EAF0E88B70564A028DD08E3963E43D1773045D17E633B408C91`.
- The agent previously claimed that this state inherently transitions to the
  Customize Jutsu detail page. The user directly verified that it does not.
  That claim is retracted. The worker-run behavior must be diagnosed as a
  runtime/setup issue and must not be reused as savestate evidence.
- `work/Font/checkpoints/ss3-jutsu-title-blocked.md` has been corrected to mark
  ss3 active again and records the retained C design and prior no-draw evidence.
- ss3 is the exact NUN5 visual target. ss4 has different content and only needs
  no-overflow regression coverage.

## Current plan and remaining work

1. Resume ss3 before later cases. Validate the actual post-load screen in the
   task-owned hidden worker before starting any watcher or changing canonical
   C. Compare the supplied original state with its exact-Current converted copy
   if needed to isolate conversion/runtime behavior.
2. If ss3 redraws through the existing guarded title caller, reapply the
   retained generated-C practice-title design from the checkpoint, tune it
   against the NUN5 ss3 screenshot, validate ss4 no-overflow, then promote
   knowledge, commit, push, and report that subtask.
3. If it still does not redraw, diagnose that exact caller/cache fact before
   requesting any new state. Do not claim the state transitions without direct
   proof.
4. Continue the next independent family only after the ss3/ss4 boundary:
   Character Select ss5–ss7. Existing binary Character Select list alignment
   likely already covers ss5 and ss6; ss7's footer body remains the probable
   implementation target.

## Retained task-owned artifacts

- Corrected ss3 checkpoint:
  `work/Font/checkpoints/ss3-jutsu-title-blocked.md`
- Refreshed state and screenshot batch:
  `work/Font/inputs/sstates/batches/2026-07-29-c-pipeline-na228-ss1-10/`
  and
  `work/Font/inputs/screenshots/batches/2026-07-29-c-pipeline-na228-ss1-10/`
- Exact-Current ss3/ss4 conversions and manifest:
  `work/Font/temp/jutsu_titles/converted/`
- Prepared but untested ss5–ss7 conversions:
  `work/Font/temp/character_select/converted/`
- Prepared but untested ss7 overlay plan:
  `work/Font/operations/character_select_confirmation_overlay.json`
- Hidden worker helper:
  `work/Font/temp/command_relationships_runtime.ps1`

## Character Select findings already established

- NA2 confirmation body function is `FUN_003bc950`.
- Its ordinary body draw is runtime `0x003BCA54`, ELF file `0x2BCA54`,
  guarded by `C4080E0C00000000` (`jal 0x00382310` plus NOP).
- NUN5 homolog `FUN_003cf580` uses its boxed renderer instead of the ordinary
  NA2 renderer.
- Existing `localization.font.v2.quit_body_adapter` is an allowlisted C entry
  and is a plausible task-owned ss7 trial, but no runtime trial has occurred.
- The ss5–ss7 conversion completed with 34 file-backed patches and 8,992
  resident bytes; no ISO build occurred.

## Git and owned changes

- Live HEAD at checkpoint preparation:
  `c01f974c181335a5881edc1b0230d186f71ad555`
  (`[General] Restrict speculative wakeups`).
- `master` matched `origin/master`.
- No tracked canonical Font implementation changes were present.
- The only tracked change created for `zxc` is this handoff.
- Work artifacts listed above are ignored task-owned state and intentionally
  retained.

## Processes, resources, and wakeups

- No Font runtime session descriptor exists at
  `work/Font/temp/command_relationships_runtime.json`.
- No Font worker PCSX2 or watcher is intentionally retained.
- No ISO build or Git transaction is running.
- The speculative ss3 replacement-state wakeup was deleted and must not be
  recreated unless the user explicitly agrees to a detectable future action.

## Exact first resume action

1. Re-read live `AGENTS.md`, the Font workstream README, linked epic workflow,
   and this handoff; refresh Git and task-owned artifacts.
2. Once resumption is valid, delete this handoff, commit, and push that deletion
   before substantive work as required by the graceful-stop policy.
3. Launch only the task-owned hidden/muted worker with supplied ss3, capture the
   actual post-load screen before any watcher, stop it, then repeat with the
   exact-Current converted ss3 if needed. Do not navigate menus and do not build
   an ISO.
