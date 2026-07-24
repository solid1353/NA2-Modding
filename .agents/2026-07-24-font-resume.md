# Font resume handoff — 2026-07-24

## Objective and task state

- Codex task/chat title: `Font`
- Selected `TASKS.md` entry: `Make font identical to UN5.`
- Phase: approved execution, interrupted at a safe experimental boundary by `zxc`
- Recommended effort: high
- Approval state: approved by the user's earlier `qwe`; no replacement plan is pending
- User direction that controls the next step: zoom in and compare the fonts properly until the result is genuinely better. Do not present another full-screen comparison.

## Canonical state

- Git HEAD before this handoff: `4d0b01c0a30d8e2249e66aa1b3d02d5dcbed1e20`
- Worktree was clean before adding this handoff.
- No canonical font, patcher, profile, documentation, or source file was changed during this resumed turn.
- The accepted baseline remains the tracked `font_nun5_glyphs`, `font_controls_auto_fit`, and `font_modal_alignment` implementation under `na2_patcher/features/localization/binary_patcher/`.
- Do not stage or commit anything under `work/Font/`; it is task-local experimental evidence.
- `.agents/notifications.json` has `"muted": true`, so the mandatory long-running-task notification is skipped for this stop.

## Stable findings and rejected candidates

- The accepted Slot 2 baseline measures median width `-2 px`, height `-2 px`, center Y `-2 px`, ink ratio `0.844523`, and density ratio `1.042106` relative to matched NUN5.
- The previously documented gamma `1.65` family is user-rejected and must not be treated as the best candidate.
- The v11 experiment that replaced the draw helper's stored right trim with `6 - right_metric` is rejected. Runtime measurement compressed median label width by `14 px`:
  - `accepted_semantics`: width `-14 px`, density ratio `1.335129`
  - `y120_nearest_semantics`: width `-14 px`, density ratio `1.332301`
- This proves the right-trim field was not the missing NUN5 operation. NUN5 and NA2 glyph preparation both store the same right metric.
- Enlarged native-pixel inspection of `Item Use` showed the accepted raster is already close inside each word. The repeatable structural mismatch is at the word break: accepted NA2 places the second word about six pixels farther away.
- Preserved NUN5 decompilation shows an additional horizontal `-6.0` operation in `FUN_00189640`; both games otherwise use the same leading/right metric semantics for ordinary glyph preparation. The next hypothesis is therefore the actual ASCII-space/word-transition advance, not per-letter metrics.
- This hypothesis is not yet runtime-tested and must not be documented as confirmed.

## Important implementation context

- Accepted secondary context pointer in the Slot 2 state: global `0x607470` -> context near `0x00B0AD40`; width is `14`, height is `20`, and tracking at `+0x3C` is `0.0`.
- Accepted custom draw decoder is runtime `0x00187274..0x00187330`.
- Accepted custom measurement helper is runtime `0x00187330..0x00187390`; hook is runtime `0x00187A60`.
- The active ASCII-space redirect is `font_controls_auto_fit_05`, file offset `0x88B7C`, which jumps to the local helper at runtime `0x003F86D8`.
- The helper block is the 64-byte `font_controls_auto_fit_02` edit at file offset `0x2F87C0`. Its space helper currently scales the original NA2 half-width space advance but does not subtract six.
- Do not repeat:
  - whole GF4 or GF4C swaps;
  - m01, v22, or v23 as implementation parents;
  - global tracking changes;
  - gamma thinning;
  - per-letter metric hand tuning;
  - the rejected `6 - right_metric` transform.
- Fullwidth Shift-JIS Save/Load digits remain outside the halfwidth-Latin comparison.

## Retained task-local artifacts

- Matched NUN5 reference: `work/Font/artifacts/savestate_analysis/screenshots/nun5/02.png`
- Accepted and rejected v11 captures: `work/Font/artifacts/font_match_v1/runtime_v11/`
- v11 comparison measurements: `work/Font/artifacts/font_match_v1/runtime_v11/comparison/`
- Existing enlarged native-pixel review: `work/Font/artifacts/font_match_v1/zoom_review/`
- v11 copied states: `work/Font/artifacts/font_match_v1/states_v11/`
- v11 candidate payloads: `work/Font/analysis/font_match_v1/candidates_v6/`
- Experimental scripts:
  - `work/Font/analysis/font_match_v1/build_candidates.py`
  - `work/Font/analysis/font_match_v1/prepare_states.py`
  - `work/Font/analysis/font_match_v1/capture_candidates.py`
  - `work/Font/analysis/font_match_v1/compare_candidates.py`
  - `work/Font/analysis/font_match_v1/zoom_compare.py`
  - `work/Font/analysis/font_match_v1/disassemble_decoder.py`
  - `work/Font/analysis/font_match_v1/disassemble_controls_helpers.py`

## Commands and tools used

- PowerShell, Git, `rg`, system Python, and the bundled Codex Python with Pillow/NumPy.
- PCSX2 was launched only through:
  - `scripts/na2/test_launch.ps1 -WorkerRoot work/Font -WaitSeconds 120 -AgentName Codex -TaskIdentity Font`
- The worker used PCSX2 PID `5140` and PINE port `28012`; the process had already exited before this handoff. No PCSX2 instance or exclusive build/runtime resource remains held.
- v11 comparison command:
  - bundled Python `work/Font/analysis/font_match_v1/compare_candidates.py`

## Remaining work

1. On resume, re-read live `AGENTS.md`, `TASKS.md`, `docs/workstreams/font/README.md`, this handoff, Git state, and the current notification state.
2. Delete this handoff and commit/push that deletion only after the resume state is validated.
3. Revert the task-local v11 state-injection script away from the rejected right-trim patches.
4. Build a focused copied-savestate candidate that changes only the actual ASCII-space/word-transition advance by the NUN5 `-6.0` operation. Preserve all glyph metrics and row positions.
5. Capture Slot 2 through the isolated `work/Font` PCSX2 worker, measure word breaks and complete label widths, and discard the candidate immediately if it worsens either.
6. Separately refine weight using the unchanged clean NA2 GF4C palette and exact NUN5 raster semantics. Use only small, measured alpha-coverage candidates; gamma `1.65` is rejected.
7. Generate native-pixel enlarged crops for at least `Attack`, `Item Use`, and `Linked Attack`, with NUN5 on the left/top and only the best genuinely improved NA2 candidate adjacent.
8. Do not canonicalize until the enlarged comparison is materially better and the user approves it.
9. Once stable, correct `docs/knowledge/font/README.md` and `docs/workstreams/font/plan.md` so gamma `1.65` is recorded as rejected rather than the current best candidate.

## Needed user input and uncertainty

- Needed from the user on resume: nothing before the next focused runtime experiment.
- Main uncertainty: the observed six-pixel word-break difference aligns with NUN5's `-6.0` renderer operation, but the exact scoped NA2 instruction sequence and whether it should apply to every ASCII space or only the secondary English path still require a guarded runtime test.

## Exact first action on resume

Validate live drift and resource state, then create a task-local v12 accepted-baseline savestate candidate that changes only the ASCII-space/word-transition advance by `-6.0`; capture and measure Slot 2 before doing any weight experiment.
