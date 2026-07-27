# ss1–ss6 layout parity

User-declared Font epic covering the matched NUN5/NA2.28 savestate pairs in
slots 1 through 6. Slots 2–6 formed the original declaration; the user added
the remade Special Controls slot 1 pair on 2026-07-27. The epic runs in an
efficiency-prioritized sequential mode: implement one slot, commit and push it, present its
NUN5-left/Current-NA2-right result, then wait for explicit user acceptance
before beginning the next slot.

## Scope and evidence

- Declared: 2026-07-27.
- Inputs:
  `work/Font/inputs/sstates/epics/ss2-6/`.
- Additional remade ss1 inputs:
  `work/Font/inputs/sstates/special-controls-on-off/remade-ss1-20260727/`.
- Extracted source screenshots:
  `work/Font/inputs/screenshots/epics/ss2-6/`.
- Provenance:
  `work/Font/inputs/sstates/epics/ss2-6/provenance.tsv` and
  `work/Font/inputs/sstates/special-controls-on-off/remade-ss1-20260727/provenance.tsv`.
- Protected `@pcsx2_user` sources remain untouched.
- Status: the remade ss2 and ss3 pair records the same Pause Controls modal in
  normal and selected states. Both are user-verified and removed from the
  remaining report. The shared quit-confirmation case is also user-verified
  and removed; three epic cases remain.
- Existing accepted Font and resident-renderer behavior remains the regression
  baseline. The previously retained Command Chart ss2 image was superseded by
  the remade Pause Controls ss2 state and is no longer an epic input.
- Text-content differences are normally routed to the translation workstreams.
  By explicit user instruction, this Font subtask also owns the two exact
  modal-specific ss1 mappings that replace fullwidth Shift-JIS `Ｏ　Ｎ`/`ＯＦＦ`
  with official NUN5 ASCII `ON`/`OFF`.

## Battle

### ss1 — Special Controls final selector

- State: mapping and bounded renderer positioning implemented; agent-validated
  against the remade pair and awaiting user acceptance.
- Baseline defect: Current draws fullwidth Shift-JIS `Ｏ　Ｎ`/`ＯＦＦ`, producing
  physically larger glyphs and wide internal advances, while NUN5 draws compact
  ASCII `ON`/`OFF`. Exact telemetry locates the NA2 slots at SLPS files
  `0x505AF0`/`0x505AF8`; mappings T2203/T2204 use the official NUN5 SLES donors
  at `0x513E68`/`0x513E6C`. The paired states prove identical modal list
  geometry, so the existing selected/unselected shared adapters use exact
  string-pointer guards and measured local targets `(66,31)` / `(59,49)`.
  Every unrelated list remains native. The remaining one- to two-pixel ink
  height difference is the separately tracked small raster mismatch.

![ss1 Special Controls final selector baseline](battle-special-controls-ss1.png)

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

## Efficiency-prioritized sequential plan

1. **ss1 — Special Controls final selector.** Commit the two guarded
   modal-specific ASCII mappings and remove the unrelated provisional Control
   Settings hook. Apply the exact mapping bytes to the task-owned state, compare
   placement against NUN5, and add a bounded position correction only if needed.
2. **ss5 — Character model move list.** Add bounded wrapping and positioning
   for the right-side move-name column.
3. **ss6 — Movie list.** Implement variable-height wrapped rows last because
   this case has the greatest caller-specific row-advance and layout burden.

Shared primitives are implemented only once. Each slot still receives its own
guarded caller, commit/push boundary, result grid, and explicit acceptance; a
shared implementation does not merge the six review decisions.
