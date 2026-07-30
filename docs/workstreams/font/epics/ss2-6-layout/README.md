# Layout parity batches

User-declared Font epic covering matched NUN5/NA2.28 layout cases. On
2026-07-30 the user replaced every prior active savestate with one new paired
ss1–10 batch and ordered the work to continue from it. The active evidence,
slot meanings, priorities, and grids below refer only to that replacement
batch. Work runs in efficiency-prioritized Continuous mode: implement one
case or proven shared caller family, commit and push it, visibly present its
NUN5-left/Current-NA2.28-right result, then proceed to the next actionable
case.

## Execution state

- Mode: Continuous, stopped after Priority 6 by explicit user instruction.
- Current subtask: none. Priority 4 remains queued because supplied ss7 resumes
  after its two owner calls.
- Pending grid: none.
- Next action: wait for explicit continuation; Priority 4 still needs a
  post-construction Collection confirmation state or screenshot.

## Scope and evidence

- Declared: 2026-07-27.
- Inputs: `work/Font/inputs/sstates/batches/2026-07-30-ss1-10/`.
- Extracted source screenshots:
  `work/Font/inputs/screenshots/batches/2026-07-30-ss1-10/`.
- State provenance and hashes:
  `work/Font/inputs/sstates/batches/2026-07-30-ss1-10/provenance.tsv`.
- Supplemental regression inputs:
  `work/Font/inputs/sstates/batches/2026-07-30-regressions/`.
- Supplemental extracted screenshots:
  `work/Font/inputs/screenshots/batches/2026-07-30-regressions/`.
- Supplemental provenance and hashes:
  `work/Font/inputs/sstates/batches/2026-07-30-regressions/provenance.tsv`.
- Original-batch compatible independent worker ISO provenance:
  `work/Font/inputs/sstates/batches/2026-07-30-ss1-10/iso_provenance.tsv`.
- Supplemental-batch compatible independent worker ISO provenance:
  `work/Font/inputs/sstates/batches/2026-07-30-regressions/iso_provenance.tsv`.
- Protected `@pcsx2_dev` sources remain untouched.
- Exact grouping: ss1 Character Select return confirmation; ss2 Linked Mode
  center modal; ss3–ss6 one Jutsu-selector defect, with ss3/ss4 supplied as
  precursors and ss5/ss6 showing the defect; ss7 Collection confirmation; ss8
  Movie list; ss9–ss10 character move lists.
- The supplemental pair reuses ss1 for the Character Select player-mode option
  list and ss2 for Linked Mode with `Manual` highlighted. It supplements rather
  than replaces the original batch: the original ss1 remains the accepted
  return-confirmation evidence.
- Supplemental ss3 is the current collapsed Jutsu-selector regression: the
  long selected title remains unwrapped, while native short one-line rows are
  the behavior that must be preserved.
- Every slot is loaded directly. The user supplied the exact Priority 3
  constructor sequence ss3 -> Cross -> ss4 -> Circle -> ss5 -> Cross -> ss6,
  but the final draw-time caller executes after direct ss5 and ss6 reloads, so
  no agent navigation was required.
- Existing accepted Font and resident-renderer behavior remains the regression
  baseline.
- Text-content differences are normally routed to the translation workstreams.

## Character Select

### Priority 1 — ss1: Return confirmation

- State: accepted lower-body fix retained; isolated top-selector fix is
  committed, pushed, agent-validated, visibly delivered, and user-verified on
  2026-07-30.
- Result: the scoped top Yes/No list has the same offsets from its modal origin
  as NUN5 while the accepted lower body remains unchanged.

![Priority 1 Character Select confirmation baseline](1-character-select-confirmation.png)

### Priority 2 — supplemental ss1–ss2: Character Select option lists

- State: implemented, canonically validated, agent-validated, and visibly
  delivered on 2026-07-30; explicit user acceptance remains pending.
- ss1: the highlighted first player-mode row remains unchanged. The ordinary
  rows already had exact NUN5 Y bounds, but bypassed the selected row's
  NUN5-metric session, making them eight or nine pixels too wide and six pixels
  too far left. Their dedicated ordinary callback now enters the same bounded
  240-unit session and five-local-unit X correction while retaining native Y.
  All three visible ordinary rows now match NUN5 bounds exactly.
- ss2: the title stays at local Y `8`; one shared `46 + 20*i` choice formula,
  with no selected-only compensation, gives exact NUN5 Y bounds for selected
  `Manual` and ordinary `Auto`.
- Remaining action: explicit user review only. The verified return-confirmation
  family and every unrelated caller remain unchanged.

![Priority 2 Linked Mode baseline](2-linked-mode-modal.png)

## Battle Settings / Jutsu selector

### Priority 3 — ss3–ss6: One Jutsu-selector defect

- State: implemented, canonically validated, agent-validated on supplemental
  ss3, and visibly delivered; explicit user acceptance remains pending.
- The enabled hook uses corrected BTL file offset `0x90DC`.
- The C entry preserves native one-line rows exactly and invokes the
  NUN5-matched 186-by-32 session only when measurement actually produces a
  line break.
- Supplemental ss3 gives exact NUN5 bounds for the wrapped selected title and
  exact untouched-Current bounds for short `Great Ball Rasengan`. Original
  ss5/ss6 remain retained evidence for the same long-title compositor in its
  other visible state.

![Priority 3 Jutsu-selector regression](3-jutsu-selector.png)

## Collection

### Priority 4 — ss7: Exit confirmation

- State: bounded C/file-backed implementation is ready and its exact guards,
  compilation, relocation, and fragment reconstruction are agent-validated;
  clean-construction runtime output and user acceptance remain pending.
- Result design: route only ETC body object `+4` through the existing wrapped
  body primitive at local `(24,12)` in a 400-by-60 box, and scope only choice
  object `+8` through the accepted Yes/No mapper. Native Collection inputs
  `(50,24)` and `(50,56)` already match that mapper's source keys.
- Validation limitation: the supplied visible-prompt ss7 state resumes after
  both owner calls. Its baseline frame is retained below, but it cannot produce
  the required post-change result or validate clean modal construction.
- Remaining action: build the patch, enter the Collection exit prompt normally,
  and supply one fresh screenshot or savestate for the final result grid.

![Priority 4 Collection confirmation baseline](4-collection-confirmation.png)

### Priority 5 — ss8: Movie list

- State: implemented, canonically validated, agent-validated, and visibly
  delivered; explicit user acceptance remains pending.
- Result: one guarded ETC caller routes only Movie-table pointers through a
  192-by-32, two-line C wrapper at native X and native Y minus 10. The four
  long titles now use NUN5's exact breaks and 16-unit line interval while the
  list keeps fixed row cadence. Short titles, selection style, source strings,
  and every non-Movie caller remain native.

![Priority 5 Movie-list result](5-movie-list.png)

### Priority 6 — ss9–ss10: Character move lists

- State: implemented, canonically validated, agent-validated on both supplied
  states, and visibly delivered on 2026-07-30; explicit user acceptance remains
  pending.
- Result: the shared ETC row entry recognizes only the two exact
  character-detail pointer families. ss9 uses NUN5's 152-by-32 box and ss10
  uses its 192-by-32 box; both retain native X, move Y up 10 units, and use the
  accepted 16-unit two-line compositor. Short rows and every unrelated ETC row
  remain native. The broadened entry also preserves the accepted ss8 Movie-list
  output.

![Priority 6 Character move-list result](6-character-move-list.png)

## Current priorities

Priority is determined by the most efficient implementation order.

1. **ss1 — Character Select return confirmation.** User-verified.
2. **supplemental ss1–ss2 — Character Select option lists.** Implemented,
   agent-validated, and visibly delivered; explicit user acceptance is pending.
3. **ss3–ss6 — one Jutsu-selector defect.** Implemented, agent-validated, and
   visibly delivered; explicit user acceptance is pending.
4. **ss7 — Collection exit confirmation.** Implementation is ready, but the
   supplied visible-prompt state resumes after both owner calls; final runtime
   construction evidence remains queued.
5. **ss8 — Movie list.** Implemented, agent-validated, and visibly delivered
   with fixed-cadence two-line wrapping; explicit user acceptance is pending.
6. **ss9–ss10 — Character move lists.** Implemented, agent-validated on both
   supplied states through one pointer-bounded shared entry, and visibly
   delivered; explicit user acceptance remains pending.

Shared primitives are implemented only once. Each prioritized caller family
receives one guarded implementation and commit/push boundary; every case keeps
its own result evidence and explicit acceptance.
