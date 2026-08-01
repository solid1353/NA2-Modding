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

- Mode: Continuous; implemented cases remain recorded below.
- Current subtask: none; Priority 6 still requires exact integrated-ISO
  confirmation.
- Pending grid: none.
- Next action: obtain exact integrated-ISO ss9/ss10 confirmation when this epic
  resumes. Practice Settings column alignment and broad Collection-family work
  were removed from this epic for later work and preserved in `../../plan.md`.

## Scope and evidence

- Declared: 2026-07-27.
- Inputs: `work/Font/inputs/sstates/batches/2026-07-30-ss1-10/`.
- Extracted source screenshots:
  `work/Font/inputs/screenshots/batches/2026-07-30-ss1-10/`.
- State provenance and hashes:
  `work/Font/inputs/sstates/batches/2026-07-30-ss1-10/provenance.tsv`.
- Priority 3 replacement inputs:
  `work/Font/inputs/sstates/batches/2026-07-31-priority3-ss1-2/`.
- Priority 3 replacement source screenshots:
  `work/Font/inputs/screenshots/batches/2026-07-31-priority3-ss1-2/`.
- Priority 3 replacement provenance and hashes:
  `work/Font/inputs/sstates/batches/2026-07-31-priority3-ss1-2/provenance.tsv`.
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
- The 2026-07-31 paired ss1–ss2 batch supersedes the older Priority 3
  presentation evidence. Its ss1 is the collapsed Jutsu list and its ss2 is
  the expanded list. Older ss3–ss6 states remain only as regression evidence
  for the same caller family.
- Every slot is loaded directly. The user supplied the exact Priority 3
  constructor sequence ss3 -> Cross -> ss4 -> Circle -> ss5 -> Cross -> ss6,
  but the final draw-time caller executes after direct ss5 and ss6 reloads, so
  no agent navigation was required.
- Existing accepted Font and resident-renderer behavior remains the regression
  baseline.
- Text-content differences are normally routed to the translation workstreams.

## Character Select

### Priority 1 — ss1: Return confirmation

- State: the isolated top-selector and reopened lower-body fixes are
  user-verified. The complete Mode Select confirmation is runtime-proven.
- Result: the dedicated body caller uses the NUN5 tracking and
  plain-space renderer state, moves local Y from `16` to `12`, and applies no
  glyph scaling. Fresh native-resolution captures give identical NUN5 and
  NA2.28 ink bounds X `194..909`, Y `1042..1078`; the previously verified
  top Yes/No selector remains unchanged.
- Acceptance: the user verified the exact live lower-body result on
  2026-07-31. Its accepted candidate grid was removed.

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

### Priority 3 — replacement ss1–ss2: One Jutsu-selector defect

- State: implemented in canonical C, fragment-verified, and user-verified
  through whole-Font hot reload on the replacement ss1–ss2 case on
  2026-07-31. This establishes acceptance of the displayed result; it does not
  claim a separate integrated-ISO runtime pass.
- ss1: fitting one-line rows are shifted right in NA2.28.
- ss2: the effective text box is too narrow. NUN5 wraps `Explosive Destruction
  Formation` after `Destruction`, while NA2.28 wraps after `Explosive`.
- ss2: the wrapped text is also too narrow vertically in NA2.28.
- Implemented result: fitting one-line and wrapped two-line rows share the
  measured NUN5-width correction while retaining separate vertical behavior.
  One-line rows receive no glyph-height or multiline-line-spacing override.
  Two-line rows keep the 186-unit break policy, 16-unit line interval,
  22-unit glyph height, and corrected centered Y. Both branches retain the
  established left/right origins.
- Older ss3–ss6 states remain regression inputs for the same caller family;
  they do not override the replacement pair.

## Collection

### Priority 4 — ss7: Exit confirmation

- State: corrected through the actual ETC render-state body consumer,
  compose-validated, and user-verified live on 2026-07-31.
- Implemented result: both guarded body-draw paths use one native-scale C
  adapter at local `(24.8,12)`, preserving the colored-word separator. The
  bounded choice call uses Collection-local Yes/No coordinates.
- Evidence: at native capture resolution, NA2.28 matches the scaled NUN5 black
  ink bounds exactly and the red ink bounds within one pixel. The prior
  unresolved grid is removed because accepted grids are not retained.

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

1. **ss1 — Character Select return confirmation.** Top selector and reopened
   lower body are user-verified; the body has exact NUN5 ink bounds.
2. **supplemental ss1–ss2 — Character Select option lists.** User-accepted.
3. **replacement ss1–ss2 — one Jutsu-selector defect.** Implemented,
   fragment-verified, visibly reviewed through whole-Font hot reload, and
   user-verified on 2026-07-31. The verified result preserves one-line vertical
   geometry while matching the two-line break, width, height, and placement.
4. **ss7 — Collection exit confirmation.** Corrected through the actual ETC
   render-state body consumer and user-verified live on 2026-07-31.
5. **ss8 — Movie list.** Corrected, compose-validated, and user-verified on the
   integrated ISO on 2026-07-30. One-line rows and fitting wrapped rows retain
   native glyph height; the previous nonrepresentative grid remains removed.
6. **ss9–ss10 — Character move lists.** Corrected and candidate-validated
   against the user-accepted target. The previous nonrepresentative grid is
   removed; exact integrated-ISO ss9/ss10 evidence is pending.
Shared primitives are implemented only once. Each prioritized caller family
receives one guarded implementation and commit/push boundary; every case keeps
its own result evidence and explicit acceptance.
