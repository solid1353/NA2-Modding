# Remaining UI Translation epic

Current report snapshot: 2026-07-26.

Every grid shows the official NUN5 reference on the left and Current NA2.28 on
the right.

## Remaining subtasks

1. Battle Results screen 2: labels, title, footer, and moving clouds are fixed.
   The red rank correction is implemented as one exact five-record NUN5 donor
   table and awaits normal-pipeline runtime verification. Matched ss2-ss6
   preserve the pre-fix baseline for all five values with the prior renderer
   replacement and whole-column atlas shift disabled while retaining the
   unmodified official NUN5 container:
   ss2 `Outstanding!`, ss3 `Try harder!`, ss4 `Keep trying`, ss5 `Good job!`,
   and ss6 `Nicely done!`. Current ss3-ss5 sample mixed neighboring atlas
   cells; ss2 and ss6 retain the correct identity as untouched placement
   baselines. The shared selector is proven to use indices `4,0,1,2,3` across
   those five pairs; `UI-BTL-016-11` replaces the incompatible NA2 64x56
   records with NUN5's 96x44 records without changing renderer code. The
   task-owned states and extracted screenshots are under
   `@work/UI translation/inputs/sstates/battle_results_rank_baseline_ss02_06_20260726/`
   and
   `@work/UI translation/inputs/screenshots/battle_results_rank_baseline_ss02_06_20260726/`.
## User-accepted completed cases

- Cross/Triangle labels: every preserved pair (original slots 1-5 and newer
  slots 1-3) was explicitly confirmed fixed by the user on 2026-07-26.
- Character Items transition: the user explicitly confirmed all five paired
  phases fixed on 2026-07-26.
- Victory winner character names: the user explicitly confirmed the expanded
  all-character donor coverage fixed on 2026-07-26.
- Ninja Song details footer: the user explicitly confirmed the corrected
  X/Next and Triangle/Back placement on 2026-07-26.

## Report grids

### Battle results

![Battle Results screen 2](02-battle-results-2.png)
