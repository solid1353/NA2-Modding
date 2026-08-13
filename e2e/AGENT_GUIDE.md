# Agent E2E validation workflow

Use this runbook after E2E has been selected for the current work under
[`../docs/policies/testing.md`](../docs/policies/testing.md). The command and
infrastructure own build, replay, capture, transaction retention, and report
generation; do not reproduce those steps manually.

## Coverage discovery

Before proposing E2E for a visual change, inspect only suite names, definitions,
and scenario descriptions. Do not scan the screenshot corpus merely to decide
whether coverage probably exists. When E2E cannot exercise or meaningfully
prove the behavior, propose user runtime validation instead.

An agent request may identify expected evidence using the existing syntax:

```text
e2e font/main 25: <requested result>
e2e font/main 25, 27-30: <requested result>
```

Those identifiers name evidence to inspect; execution remains global across the
tracked suite set so unintended changes elsewhere can surface.

## Evidence

For suite `<suite>` and capture `<slot>`, accepted visual history is in the
nested Git repository under `captures/<suite>/`:

- `base-screenshots/<slot>_a_reference.png`: optional reference-game image.
- `base-screenshots/<slot>_b_current.png`: accepted NA2 image.
- `base-blends/<slot>_c_blend.png`: 50% reference/current blend.
- `base-diffs/<slot>_d_diff.png`: amplified reference/current difference.
- `base-pairs/<slot>_e_pair.png`: side-by-side reference/current image.
- `grid-screenshots/`: separate `page_<n>_a_reference.png` and
  `page_<n>_b_current.png` grid series.
- `grid-pairs/`: paged grids of side-by-side pairs.
- `grid-blends/`: paged 50% blend grids.
- `grid-diffs/`: paged amplified-difference grids.
- `base-all/` and `grid-all/`: ignored regenerated hardlink aggregates that
  intentionally exclude pairs.
- `sstates/current/<slot>.p2s`: retained state when the capture changed.

For text, inspect relevant images at sufficient zoom to judge glyph pixels,
spacing, baselines, and alignment.

## Run and review

1. Inspect any explicitly requested existing evidence.
2. Make only the implementation/asset changes authorized for the task.
3. Run the current global E2E entrypoint documented in
   [`README.md`](README.md).
4. Inspect the complete Git diff in the nested `e2e/captures/` repository.
5. Inspect every changed capture or artifact itself. Unchanged artifacts need no
   manual review unless there is a concrete reason.
6. Treat an expected visual change with no corresponding diff as evidence that
   the candidate was ineffective.
7. Explain every changed artifact or continue investigating it; do not dismiss a
   difference as unrelated or volatile without evidence.
8. Iterate until the intended result is achieved or a concrete blocker remains.

Do not manually edit generated current images, reports, recordings, or
references unless the user explicitly requests that exact change. Do not
regenerate references without explicit authorization.

## Acceptance and delivery

Keep the implementation and generated capture-history changes uncommitted while
iterating. Agent review and a successful E2E run do not replace user acceptance.
Present the regenerated evidence and wait for `ver`, which accepts the pending
result and authorizes its complete delivery.

When `ver` is received:

1. Finalize accepted patch-specific tests and documentation.
2. Refresh both repositories and confirm every pending change under
   `e2e/captures/` and `e2e/suites/` belongs to the accepted result. If
   unaccepted concurrent E2E changes are present, wait until only accepted state
   would be committed.
3. Run `na228 e2e commit` before helper-managed main-repository staging. This
   command exclusively owns delivery of the capture and suite paths; do not
   substitute manual Git or the staging helper. Use `-p` only when the user
   explicitly requests preserved capture history.
4. Stage and commit the accepted implementation changes in the main repository
   so both repositories form one coherent delivery.
5. Include regenerated tracked reports, then verify and report both
   repositories' commit, push, and dirty states.

If the capture repository has no remote, commit it locally before pushing the
main implementation and report that exact exception.
