# Layout parity batches

User-declared Font epic covering matched NUN5/NA2.28 layout cases. Slots 2–6
formed the original declaration; the user later added and accepted the remade
Special Controls slot 1 pair. On 2026-07-27 the user added a distinct matched
batch in slots 1–10, then supplied one additional Command Chart ss1 pair. On
2026-07-29 the user recreated every current NA2.28 state after the C-pipeline
cutover; retained NUN5 references were matched to the refreshed slots by screen
semantics. The epic now runs in efficiency-prioritized Continuous mode:
implement one case or proven shared caller family, commit and push it, present
its NUN5-left/Current-NA2-right result, then proceed unless a required
regression boundary or blocker requires user input.

## Scope and evidence

- Declared: 2026-07-27.
- Inputs:
  `work/Font/inputs/sstates/epics/ss2-6/` and
  `work/Font/inputs/sstates/batches/2026-07-27-ss1-10/`, plus
  `work/Font/inputs/sstates/batches/2026-07-27-additional-ss1/`. The active
  refreshed batch is
  `work/Font/inputs/sstates/batches/2026-07-29-c-pipeline-na228-ss1-10/`.
- Extracted source screenshots:
  `work/Font/inputs/screenshots/epics/ss2-6/` and
  `work/Font/inputs/screenshots/batches/2026-07-27-ss1-10/`, plus
  `work/Font/inputs/screenshots/batches/2026-07-27-additional-ss1/`. The active
  refreshed screenshots are under
  `work/Font/inputs/screenshots/batches/2026-07-29-c-pipeline-na228-ss1-10/`.
- Provenance:
  `work/Font/inputs/sstates/epics/ss2-6/provenance.tsv` and
  `work/Font/inputs/sstates/batches/2026-07-27-ss1-10/provenance.tsv`, plus
  `work/Font/inputs/sstates/batches/2026-07-27-additional-ss1/provenance.tsv`.
  The active refreshed mapping and hashes are recorded in
  `work/Font/inputs/sstates/batches/2026-07-29-c-pipeline-na228-ss1-10/provenance.tsv`.
- Protected `@pcsx2_dev` sources remain untouched.
- Status: the remade ss2 and ss3 pair records the same Pause Controls modal in
  normal and selected states. Both are user-verified and removed from the
  remaining report. The shared quit-confirmation and ss1 Special Controls cases
  are also user-verified and removed. The original batch retains two cases and
  the new batch contributes nine remaining cases. The additional Command Chart
  ss1 raises the remaining total to twelve cases. The accepted 2026-07-29
  remade ss1 superseded the old ss10 Mode Select evidence and has been removed
  from this remaining-work report. The refreshed batch retains the same ten
  remaining semantic cases with new numbering: Command Chart ss1–2, Jutsu
  ss3–4, Character Select ss5–7, Collection ss8, and Practice Settings ss9–10.
- Existing accepted Font and resident-renderer behavior remains the regression
  baseline. The previously retained Command Chart ss2 image was superseded by
  the remade Pause Controls ss2 state and is no longer an epic input.
- Text-content differences are normally routed to the translation workstreams.

## Collection

### Priority 6 — Original ss5: Character model move list

- State: baseline captured; not implemented.
- Remaining defect: Current overflows the long move name, while NUN5 wraps it
  inside the right-side column.

![Priority 6 character model baseline](6-character-model-move-list.png)

### Priority 7 — Original ss6: Movie list

- State: baseline captured; not implemented.
- Remaining defect: Current movie titles remain single-line and overflow,
  while NUN5 uses variable-height wrapped rows.

![Priority 7 movie list baseline](7-movie-list.png)

### Priority 4 — Refreshed ss8: Quit Collection confirmation

- State: baseline captured; not implemented.
- Review target: shared modal selector and body geometry.

![Priority 4 Collection confirmation baseline](4-collection-confirmation.png)

## Battle / Practice Settings

### Priority 5 — Refreshed ss9–ss10: Settings rows and explanations

- State: two matched baselines captured; not implemented.
- Review targets: row-value geometry, selection alignment, and lower
  explanatory-text flow. Content differences remain translation-owned.

![Priority 5 Practice Settings baselines](5-practice-settings.png)

## Battle / Command Chart

### Priority 1 — Refreshed ss1–ss2: Command details

- State: two matched baselines captured; not implemented.
- ss1: Current keeps the relationship explanation on one line and overflows;
  NUN5 wraps it within the command-details panel.
- ss2: Current's blue explanation and controller-icon rows sit
  roughly 8–14 pixels lower than NUN5 within each command entry.

![Priority 1 Command Chart baselines](1-command-chart.png)

## Character Select

### Priority 3 — Refreshed ss5–ss7: Shared selection/modal family

- State: three matched baselines captured; not implemented.
- ss5: Current's final `Back to Game Mode Screen` option overflows the modal.
- ss6: Linked Mode is retained as a regression case for shared selector
  geometry.
- ss7: Current's return-confirmation body overflows while NUN5 fits it inside
  the footer box.

![Priority 3 Character Select baselines](3-character-select-modals.png)

## Battle Settings / Customize Jutsu

### Priority 2 — Refreshed ss3–ss4: Jutsu-name list

- State: two matched baselines captured; not implemented.
- Remaining defect: Current selected and expanded-list titles overflow
  horizontally; NUN5 wraps them inside the left-side list bounds.

![Priority 2 Jutsu-name list baselines](2-jutsu-name-list.png)

## Current priorities

Priority is determined by the most efficient implementation order.

1. **Refreshed ss1–ss2 — Command Chart details.** Reuse the
   established command/practice text-flow primitives for the bounded
   relationship explanation, and correct the shared per-entry explanation/icon
   vertical geometry once for both states.
2. **Refreshed ss3–ss4 — Jutsu-name list.** Resolve the shared selected/list title
   family once, then validate both states.
3. **Refreshed ss5 and ss7 — Character Select modal text.** Address the
   overflowing list entry and confirmation body while keeping refreshed ss6 as
   regression proof.
4. **Refreshed ss8 — Quit Collection confirmation.** Treat its modal selector
   and body geometry as a separate unfinished layout case.
5. **Refreshed ss9–ss10 — Practice Settings review.** Separate translation-owned
   content differences from remaining Font geometry before patching.
6. **Original ss5 — Character model move list.** Add bounded wrapping and
   positioning for the right-side move-name column.
7. **Original ss6 — Movie list.** Implement variable-height wrapped rows last
   because this case has the greatest caller-specific row-advance burden.

Shared primitives are implemented only once. Each prioritized caller family
receives one guarded implementation and commit/push boundary; every case keeps
its own result evidence and explicit acceptance, so shared code does not merge
the twelve remaining review decisions.
