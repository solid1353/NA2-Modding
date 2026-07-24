# UI Translation resume handoff — 2026-07-24

## Objective and state

- Task/chat title: `UI Translation`
- Selected `TASKS.md` entry: `[Investigate](work/__sstates/translation/UI) → Deal with remaining issues (items, awakenings, etc.).`
- Current phase: approved execution, stopped safely by the user's `zxc`.
- Approved plan: fix remaining item/status layouts one class at a time, using official NUN5 donors plus the minimum NA2 ABI port; validate each finished class and commit/push it separately.
- Recommended effort: `ultra`.
- Approval state: approved by the user's earlier `qwe`; approval remains valid.
- Current user corrections: fix classes one by one; do not redo a fix that can be shared; use PCSX2 for direct visual evidence; do not touch later classes while the current class is unfinished.

## Completed

- Paired item-status labels are complete in commit `646192a` (`[UI Translation] Localize paired item-status labels`) and pushed to `origin/master`.
- The patch uses three exact NUN5 donor ranges plus the runtime-proven NA2 ABI-safe renderer/layout port.
- Focused tests passed:
  - `UiTextureTests.test_paired_item_status_layout_uses_exact_nun5_donors`
  - `UiTextureTests.test_binary_patch_provenance_is_donor_first`
  - `ProfileTests.test_current_profile_and_feature_layout`
- Binary package validation passed: 7 targets, 9 groups, 89 patches, 303 edits.
- Isolated worker ISO build passed at `work/UI translation/build/items-pair.iso`; Current/Previous and PCSX2 were untouched.
- The Localization feature pin in the committed state is `25E7339B3DBAAE7812E589667A537B58FA445887B22C8127AF4AF3163C869445`; the user-owned `bypass_check=1` was preserved.

## Current incomplete class

Numeric item-status layout only (paired is complete; single and fixed are not started).

Confirmed numeric target evidence:

- NUN5 uses 1.25 horizontal bubble scale, neutral vertical scale, quarter-turn background rotation, common origin `(-33,-33)`, and the imported rank offsets.
- Official donor records required by this class are Health `0x81`, Chakra `0x82`, and Recovery `0x8D`; bubble `0x80` and observed digit records are already byte-identical.
- Exact NUN5 digit offsets are `-36/-27/-18`, `-32/-22`, and `-26`.
- The latest generated lower-label helper uses Y bias `0x11` (17), correcting the earlier experimental `0x13`.

## PCSX2 attempts and safe state

All three launches used the maintained hidden, muted, ownership-guarded launcher and closed only their owned process:

1. Running launch rejected the first guard at `0x00377074` because the savestate had not settled.
2. Adding a post-load wait reached the saved object migration, then rejected `0x00E57A94` because the running frame had already advanced/reused the object.
3. `-StartPaused` kept all exact guards stable, but `capture_state` timed out because paused PCSX2 did not produce a stable `Screenshot.png`.

No PCSX2 process is running or owned by this task. No shared configuration, Current/Previous/Candidate ISO, memory card, or exclusive resource is held. Notifications are muted in `.agents/notifications.json`, so no stop notification was sent.

## Retained restart artifacts

- Accepted paired evidence:
  - `work/UI translation/artifacts/sstates/items-v20-slot07.p2s`
  - `work/UI translation/artifacts/screenshots/items-v20b-slot07.png`
  - `work/UI translation/inputs/sstates/library/Character Items/SLES-55605 (C071D4C1).07.png`
- Numeric/reference inputs:
  - `work/UI translation/inputs/sstates/library/Character Items/SLPS-22228 (6D94D520).03.p2s`
  - `work/UI translation/inputs/sstates/library/Character Items/SLES-55605 (C071D4C1).03.p2s`
  - corresponding `.03.png` files in the same directory
- Pair regression inputs:
  - `work/UI translation/inputs/sstates/library/Character Items/SLPS-22228 (6D94D520).07.p2s`
  - `work/UI translation/inputs/sstates/library/Character Items/SLES-55605 (C071D4C1).07.p2s`
- Worker build and record:
  - `work/UI translation/build/items-pair.iso`
  - `work/UI translation/logs/builds/20260724_233946_884_pid46492/`
- Runtime-plan sources and partial outputs:
  - `work/UI translation/temp/build_item_runtime_plan.py`
  - `work/UI translation/temp/build_numeric_checkpoint_plan.py`
  - `work/UI translation/temp/patch_item_state.py`
  - `work/UI translation/temp/items-v26-raw-slot03.json`
  - `work/UI translation/temp/items-v26-raw-slot07.json`
  - `work/UI translation/runtime-items-v26-numeric.json`
- Earlier numeric evidence retained for comparison, not acceptance:
  - `work/UI translation/artifacts/sstates/items-v25-slot03.p2s`
  - `work/UI translation/artifacts/screenshots/items-v25-slot03.png`
  - `work/UI translation/artifacts/sstates/items-v25-slot07.p2s`

The rest of `work/UI translation/` predates this stop and was not cleaned or changed as part of `zxc`.

## Git and files

- HEAD: `646192a7377c2cbfa60de51eeb3f6378b5b205e2`
- Git status before this handoff: clean.
- Owned staged paths: none.
- Owned unstaged canonical paths: none.
- Canonical files changed and committed for the completed paired class:
  - `docs/knowledge/localization/ui/battle.md`
  - `na2_patcher/features/localization/README.md`
  - `na2_patcher/features/localization/binary_patcher/edits.tsv`
  - `na2_patcher/features/localization/binary_patcher/patches.tsv`
  - `na2_patcher/profiles/current/features.tsv`
  - `na2_patcher/tests/test_texture_patcher.py`
- Incomplete work exists only under the ignored task-owned `work/UI translation/` paths listed above.

## Resume procedure

1. Read live `AGENTS.md`, `TASKS.md`, the UI Translation workstream policy, this handoff, Git state, and the retained files.
2. If drift validation succeeds, delete this handoff and commit/push that deletion before resuming.
3. Regenerate `runtime-items-v26-numeric.json`; the updated generator now also emits filtered Slot 03 numeric and Slot 07 pair-regression patch plans.
4. Use `patch_item_state.py` offline to create patched task-owned Slot 03 and Slot 07 savestates. This avoids unstable live heap writes.
5. Launch once, running and hidden/muted, with a capture-only operation plan that loads the two already-patched savestates. Inspect one paired NUN5/current numeric checkpoint and one paired-label regression checkpoint.
6. Only after both match, canonicalize the numeric class as its own patch, validate/build, and commit/push that single finished class.

Required user input: none before resuming.

Uncertainty: the numeric code/data is evidence-derived, but the final fresh rendered frame has not yet been captured; `items-v25-slot03.png` is not acceptance evidence because its saved sprite cache retained pre-patch geometry.
