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

- Mode: Continuous.
- Current subtask: Priority 3 — ss3–ss6 Jutsu selector.
- Pending grid:
  `docs/workstreams/font/epics/ss2-6-layout/3-jutsu-selector.png`.
- Next action: validate, commit and push the one-caller Jutsu fix, visibly
  deliver the pending result grid, then continue Priority 4.

## Scope and evidence

- Declared: 2026-07-27.
- Inputs: `work/Font/inputs/sstates/batches/2026-07-30-ss1-10/`.
- Extracted source screenshots:
  `work/Font/inputs/screenshots/batches/2026-07-30-ss1-10/`.
- State provenance and hashes:
  `work/Font/inputs/sstates/batches/2026-07-30-ss1-10/provenance.tsv`.
- Compatible independent worker ISO provenance:
  `work/Font/inputs/sstates/batches/2026-07-30-ss1-10/iso_provenance.tsv`.
- Protected `@pcsx2_dev` sources remain untouched.
- Exact grouping: ss1 Character Select return confirmation; ss2 Linked Mode
  center modal; ss3–ss6 one Jutsu-selector defect, with ss3/ss4 supplied as
  precursors and ss5/ss6 showing the defect; ss7 Collection confirmation; ss8
  Movie list; ss9–ss10 character move lists.
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
  committed, pushed, agent-validated, and visibly delivered; user acceptance
  remains pending.
- Result: the scoped top Yes/No list has the same offsets from its modal origin
  as NUN5 while the accepted lower body remains unchanged.

![Priority 1 Character Select confirmation baseline](1-character-select-confirmation.png)

### Priority 2 — ss2: Linked Mode center modal

- State: isolated three-instruction fix is committed, pushed,
  agent-validated, and visibly delivered; user acceptance remains pending.
- Result: the center-modal `Linked Mode`, `Manual`, and `Auto` labels now
  match the NUN5 vertical geometry without changing another modal or renderer.

![Priority 2 Linked Mode baseline](2-linked-mode-modal.png)

## Battle Settings / Jutsu selector

### Priority 3 — ss3–ss6: One Jutsu-selector defect

- State: implemented and agent-validated on supplied ss5 and ss6; user
  acceptance remains pending. The exact native row draw at live BTL
  `0x006BCFDC` is isolated behind one guarded C caller. Both long selected
  names wrap inside the NUN5 186-by-32 two-line box. A session-scoped
  20-unit glyph bottom edge and explicit 16-unit row advance match the NUN5
  normalized top, bottom, height, and line spacing without changing another
  renderer session.
- ss3 and ss4 are supplied precursors for this one caller family.
- ss5 and ss6 visibly prove that Current keeps long Jutsu names on one line
  and overflows, while NUN5 wraps them inside the selector bounds.
- Runtime validation used direct supplied ss5 and ss6 loads; no game input or
  menu navigation was required.

![Priority 3 Jutsu-selector baselines](3-jutsu-selector.png)

## Collection

### Priority 4 — ss7: Exit confirmation

- State: matched baseline captured; not implemented.
- Remaining defect: confirmation body and choice geometry remain to match.

![Priority 4 Collection confirmation baseline](4-collection-confirmation.png)

### Priority 5 — ss8: Movie list

- State: matched baseline captured; not implemented.
- Remaining defect: Current movie titles remain single-line and overflow,
  while NUN5 uses variable-height wrapped rows.

![Priority 5 Movie-list baseline](5-movie-list.png)

### Priority 6 — ss9–ss10: Character move lists

- State: two matched baselines captured; not implemented.
- Remaining defect: Current keeps long move and relationship titles on one
  line and overflows, while NUN5 wraps them within the move-list column.

![Priority 6 Character move-list baselines](6-character-move-list.png)

## Current priorities

Priority is determined by the most efficient implementation order.

1. **ss1 — Character Select return confirmation.** Finish the already-isolated
   top selector while preserving the accepted lower body.
2. **ss2 — Linked Mode center modal.** Correct the shared three-label vertical
   geometry as one bounded caller.
3. **ss3–ss6 — one Jutsu-selector defect.** Use ss5/ss6 as visible targets and
   retain ss3/ss4 only as the supplied precursor states.
4. **ss7 — Collection exit confirmation.** Match its body and choice geometry
   without affecting the Character Select modal family.
5. **ss8 — Movie list.** Implement caller-specific variable-height wrapped
   rows.
6. **ss9–ss10 — Character move lists.** Reuse one bounded wrapping primitive
   for both long-title cases where the caller family is shared.

Shared primitives are implemented only once. Each prioritized caller family
receives one guarded implementation and commit/push boundary; every case keeps
its own result evidence and explicit acceptance.
