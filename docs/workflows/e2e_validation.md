# Agent E2E validation workflow

Use this workflow after E2E has been selected for the current work under
[`../policies/testing.md`](../policies/testing.md). The command and
infrastructure own build, replay, capture, transaction retention, and report
generation; do not reproduce those steps manually.

## Requested evidence

An agent request may identify expected evidence using the existing syntax:

```text
e2e font/main 25: <requested result>
e2e font/main 25, 27-30: <requested result>
```

Those identifiers name evidence to inspect; execution remains global across the
tracked suite set so unintended changes elsewhere can surface.

## Evidence

For suite `<suite>` and capture `<slot>`, accepted visual history is in the
nested Git repository under `e2e/captures/<suite>/`:

- `screenshots/`: separate `page_<n>_a_reference.png` and
  `page_<n>_b_current.png` grid series.
- `pairs/`: paged grids of side-by-side pairs.
- `blends/`: paged 50% blend grids.
- `diffs/`: paged amplified-difference grids.
- `all/`: ignored regenerated hardlink aggregate that intentionally excludes
  pairs.

Screenshot, blend, and diff grids use six fixed cells in a horizontal 3×2
layout, with missing slots left black. Pair grids retain their existing layout
and side-by-side cells. Pair, blend, and diff cells contain no embedded headers.

For text, inspect relevant images at sufficient zoom to judge glyph pixels,
spacing, baselines, and alignment.

## Selective diagnostic savestates

If investigating one or more concrete E2E pictures requires savestates, rerun
only their corresponding recording marker numbers through PCSX2 using
`-input-recording-capture-mode savestates` and
`-input-recording-capture-markers <markers>`.

Write the diagnostic savestates only within the acting task's
`@work/<exact chat title>/` directory. Confirm each state's embedded screenshot
corresponds to the requested picture. Use savestates only to inspect runtime
state: their embedded screenshots cannot establish visual parity or replace
screenshot-mode E2E evidence. Never publish diagnostic savestates as E2E
capture history. Delete them before completing the task.

## Run and review

1. Inspect any explicitly requested existing evidence.
2. Make only the implementation/asset changes authorized for the task.
3. Run the current global E2E entrypoint documented in
   [`e2e/README.md`](../../e2e/README.md).
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
   `e2e/captures/` belongs to the accepted result. If
   unaccepted concurrent E2E changes are present, wait until only accepted state
   would be committed.
3. Run `na228 e2e commit` before committing the main repository. This command
   exclusively owns delivery of the capture repository. Use `-p` only when the
   user explicitly requests
   preserved capture history.
4. Commit the accepted implementation changes in the main repository so both
   repositories form one coherent delivery.
5. Include regenerated tracked reports, then verify and report both
   repositories' commit, push, and dirty states.

If the capture repository has no remote, commit it locally before pushing the
main implementation and report that exact exception.
