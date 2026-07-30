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

- Mode: Continuous, limited by the user's current authorization to the
  explicitly selected Priority 4 correction.
- Current subtask: Priority 4 — ss7 Collection exit confirmation.
- Pending grid: missing: exact post-change Priority 4 capture from a newly
  constructed Collection exit prompt.
- Next action: obtain one NA2.28 savestate on the Collection menu immediately
  before the action that opens `Quit Collection?`, then run the already-enabled
  body and choice hooks and capture the first newly constructed prompt. The
  retained visible-prompt ss7 resumes after both owner calls and cannot prove
  this result.

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

### Priority 2 — supplemental ss1–ss2: Character Select option lists

- State: implemented, canonically validated, agent-validated, visibly
  delivered, and user-accepted on 2026-07-30.
- ss1: the highlighted first player-mode row remains unchanged. The ordinary
  rows already had exact NUN5 Y bounds, but bypassed the selected row's
  NUN5-metric session, making them eight or nine pixels too wide and six pixels
  too far left. Their dedicated ordinary callback now enters the same bounded
  240-unit session and five-local-unit X correction while retaining native Y.
  All three visible ordinary rows now match NUN5 bounds exactly.
- ss2: the title stays at local Y `8`; one shared `46 + 20*i` choice formula,
  with no selected-only compensation, gives exact NUN5 Y bounds for selected
  `Manual` and ordinary `Auto`.
- The verified return-confirmation family and every unrelated caller remain
  unchanged.

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

![Priority 3 Jutsu-selector regression](awaiting_approval/3-jutsu-selector.png)

## Collection

### Priority 4 — ss7: Exit confirmation

- State: selected again by the user on 2026-07-30. The bounded C/file-backed
  implementation remains enabled from commit `76e5023f`; its exact guards,
  compilation, relocation, fragment reconstruction, and current full-profile
  composition are agent-validated. Clean-construction runtime output and user
  acceptance remain pending.
- Result design: route only ETC body object `+4` through the existing wrapped
  body primitive at local `(24,12)` in a 400-by-60 box, and scope only choice
  object `+8` through the accepted Yes/No mapper. Native Collection inputs
  `(50,24)` and `(50,56)` already match that mapper's source keys.
- Validation limitation: the supplied visible-prompt ss7 state resumes after
  both owner calls. Its baseline frame is retained below, but it cannot produce
  the required post-change result or validate clean modal construction.
- Remaining action: supply one NA2.28 savestate on the Collection menu
  immediately before opening the exit prompt. The existing enabled patch can
  then be exercised without an ISO build or agent menu navigation.

![Priority 4 Collection confirmation baseline](pending/4-collection-confirmation.png)

### Priority 5 — ss8: Movie list

- State: corrected in canonical C, compose-validated, and exercised as a
  runtime-injected candidate on the supplied ss8 state. The user then verified
  the exact integrated-ISO result on 2026-07-30. The previous
  nonrepresentative grid remains removed, and no accepted grid is retained.
- Implemented result: one-line Movie rows bypass the wrapper completely. Only
  titles that actually wrap use the 192-unit two-line layout and 16-unit line
  interval; those wrapped rows retain native glyph geometry instead of
  receiving the 20-unit glyph-height override. Selection style, source strings,
  fixed caller cadence, character-detail branches, and every non-Movie caller
  remain unchanged.
- Evidence: development injection established the candidate appearance; the
  user's subsequent integrated-ISO verification establishes the accepted
  shipped result.

### Priority 6 — ss9–ss10: Character move lists

- State: corrected in canonical C/static core and agent-validated as a
  runtime-injected candidate. The user explicitly accepted the exact ss9 target
  appearance on 2026-07-30. Exact integrated-ISO confirmation remains pending,
  and the previous nonrepresentative grid remains removed.
- Root cause: the compatible development ISO retained the older right-edge
  session shim, which ignored the character branch's `0x40` glyph-quad flag.
  The integrated payload used the newer flag-aware shim, whose conditional
  branch loaded `session.glyph_height` from its MIPS delay slot even when the
  flag was clear. Development therefore appeared correct while the integrated
  rows were squeezed.
- Implemented result: the shared hook now uses a NOP delay slot and loads
  `glyph_height` only on its flagged path. Character rows retain
  `glyph_height = 20` solely for two-line box centering but no longer set the
  glyph-quad flag. Their accepted 152- or 192-unit boxes, native X, Y minus 10,
  required line breaks, and 16-unit line interval are unchanged.
- Candidate evidence: fresh ss9 and ss10 captures through the corrected modern
  hook reproduce every retained target text group's native-resolution bounds
  and glyph-pixel counts exactly. A supplied ss8 regression reproduces the
  accepted Movie right panel pixel-for-pixel. Non-text animation pixels are not
  part of that identity claim.
- Evidence requirement: the canonical result grid still requires untouched
  NUN5 and exact integrated-ISO ss9/ss10 captures at native resolution.

## Current priorities

Priority is determined by the most efficient implementation order.

1. **ss1 — Character Select return confirmation.** User-verified.
2. **supplemental ss1–ss2 — Character Select option lists.** User-accepted.
3. **ss3–ss6 — one Jutsu-selector defect.** Implemented, agent-validated, and
   visibly delivered; explicit user acceptance is pending.
4. **ss7 — Collection exit confirmation.** Implementation is ready, but the
   supplied visible-prompt state resumes after both owner calls; final runtime
   construction evidence remains queued.
5. **ss8 — Movie list.** Corrected, compose-validated, and user-verified on the
   integrated ISO on 2026-07-30. One-line rows and fitting wrapped rows retain
   native glyph height; the previous nonrepresentative grid remains removed.
6. **ss9–ss10 — Character move lists.** Corrected and candidate-validated
   against the user-accepted target. The previous nonrepresentative grid is
   removed; exact integrated-ISO ss9/ss10 evidence is pending.

Shared primitives are implemented only once. Each prioritized caller family
receives one guarded implementation and commit/push boundary; every case keeps
its own result evidence and explicit acceptance.
