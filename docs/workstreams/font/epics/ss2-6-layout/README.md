# ss2–ss6 layout parity

User-declared Font epic covering only the matched NUN5/NA2.28 savestate pairs
in slots 2 through 6. The epic runs in the default sequential mode: implement
one slot, commit and push it, present its NUN5-left/Current-NA2-right result,
then wait for explicit user acceptance before beginning the next slot.

## Scope and evidence

- Declared: 2026-07-27.
- Inputs:
  `work/Font/inputs/sstates/epics/ss2-6/`.
- Extracted source screenshots:
  `work/Font/inputs/screenshots/epics/ss2-6/`.
- Provenance:
  `work/Font/inputs/sstates/epics/ss2-6/provenance.tsv`.
- Protected `@pcsx2_user` sources remain untouched.
- Status: all five baselines are captured; implementation has not started.
- Existing accepted Font and resident-renderer behavior remains the regression
  baseline. The accepted Command Chart title is not reopened by ss2; ss2 owns
  only the remaining command-body layout.
- Text-content differences are routed to the translation workstreams. This
  epic owns measurement, wrapping, fitting, positioning, and clipping only.

## Battle

### ss2 — Command Chart body

- State: baseline captured; not implemented.
- Remaining defect: the third Current description remains on one clipped line,
  while NUN5 wraps it into two lines inside the command panel.

![ss2 Command Chart body baseline](battle-command-chart-ss2.png)

### ss3 — Pause Controls list

- State: baseline captured; not implemented.
- Remaining defect: Current long menu rows run beyond the panel edge, while
  NUN5 fits them within the list.

![ss3 Pause Controls list baseline](battle-controls-list-ss3.png)

### ss4 — Quit confirmation

- State: baseline captured; not implemented.
- Remaining defect: Current keeps the confirmation body on one overflowing
  line, while NUN5 wraps it into two lines; the Yes/No row placement also
  differs.

![ss4 Quit confirmation baseline](battle-quit-confirmation-ss4.png)

## Collection

### ss5 — Character model move list

- State: baseline captured; not implemented.
- Remaining defect: Current overflows the long move name, while NUN5 wraps it
  inside the right-side column.

![ss5 Character model baseline](collection-character-model-ss5.png)

### ss6 — Movie list

- State: baseline captured; not implemented.
- Remaining defect: Current movie titles remain single-line and overflow,
  while NUN5 uses variable-height wrapped rows.

![ss6 Movie list baseline](collection-movie-list-ss6.png)

## Sequential order

1. ss2 — Command Chart body.
2. ss3 — Pause Controls list.
3. ss4 — Quit confirmation.
4. ss5 — Character model move list.
5. ss6 — Movie list.

Before adding a separate wrapper, inspect whether the active case shares the
same NUN5/NA2 caller family with a later epic case. Reuse proven shared behavior
without treating acceptance of one slot as acceptance of another.
