# Agent workflow for local NA2.28 visual fixes

Use this workflow when the user gives an existing E2E difference and requests a
local NA2.28 rendering fix. The E2E command owns building, replay, capture,
state retention, and report generation; do not reproduce those steps manually.

## Invocation

```text
e2e font/main 25: <requested fix>
e2e font/main 25, 27-30: <requested fix>
```

A capture expression accepts one slot, comma-separated slots, and inclusive
ranges. The command authorizes immediate implementation and repeated execution
of the affected suite without separate plan approval.

## Evidence

For suite `<suite>` and capture `<slot>`:

- `captures/<suite>/reference/<slot>.png` is the optional reference-game image.
- `captures/<suite>/current/<slot>.png` is the latest NA2.28 image.
- `captures/<suite>/report/` contains generated reference/current pairs,
  pixel diffs, blends, and grids when the suite has a reference.
- `captures/<suite>/sstates/current/<slot>.p2s` is available when the visible
  difference requires runtime investigation.
- Git history in the capture repository records accepted prior versions of the
  current images, savestates, and generated report.

When the target is plain text, ordinary capture PNGs or grid pages must be
zoomed until individual glyph pixels, spacing, baselines, and alignment are
clearly legible. A thumbnail or fitted whole image is insufficient. Inspect the
relevant pair, diff, or blend at readable zoom before deciding what to change
and again before deciding that the result is correct.

## Evidence gate

- Open and inspect every capture named by the command. Evidence from one slot
  never establishes the state of another slot.
- A claim such as "aligned with", "matches", "same bounds", or "consistent
  across" requires an actual comparison of every named side at readable zoom.
- Inspect the exact selected, highlighted, ordinary, disabled, or other state
  named by the request; never substitute a visually similar state.
- After every `na228 test <suite> -b` run, reopen the regenerated evidence for
  every named capture. Pre-run evidence cannot establish the post-run result.
- Inspect every regenerated capture that differs from its tracked predecessor,
  including captures not named by the request. Never call a difference
  pre-existing, unrelated, volatile, nondeterministic, or outside the changed
  code path merely because that classification seems likely. Compare the
  actual before/after evidence and establish its cause; if the cause remains
  unknown, report it as unknown and continue investigating. A run is not clean
  while any regenerated capture difference remains unexplained.
- Do not claim correctness or completion until every requested property has
  been checked directly in every applicable capture.
- Do not say comparison, testing, or inspection is happening "now" and then
  yield. Perform it in the same turn. Stop only for a concrete blocker.

## Fix and verify

1. Inspect the named current images and reference/current evidence.
2. Change only the NA2.28 code or asset responsible for the requested result.
3. Run the affected suite; for the current font suite:

   ```powershell
   na228 test font/main -b
   ```

4. Inspect the regenerated current images and report.
5. Repeat until every named capture has the requested result or a concrete
   blocker remains.

The run atomically publishes `current/`, `sstates/current/`, and `report/`.
When a freshly captured PNG is pixel-identical to the existing current PNG,
the existing savestate is retained instead of replacing it. A changed or new
PNG publishes its matching fresh savestate. Files listed in the suite's
`ignore.txt` keep both their previous current screenshot and previous current
savestate; a newly ignored slot without existing evidence publishes neither.

## Verification and delivery gate

Keep implementation, current screenshots, current savestates, and the report
uncommitted while iterating. Agent inspection and a successful command do not
establish user acceptance. Present the regenerated evidence and wait for
explicit user verification and approval.

After approval, commit the accepted capture-history changes in the nested
`e2e/captures/` repository and the implementation changes in the main
repository as one coordinated delivery. Include the regenerated tracked report
changes. If the capture repository has no remote, commit it locally before
pushing the main implementation and report that it was not pushed.
This boundary is indivisible: never commit or push the main-repository half
while accepted capture-history changes remain uncommitted in the nested
repository. Before reporting delivery, verify and report both repositories'
commit, push, and dirty states.

## Boundaries

- Do not navigate PCSX2 manually or construct comparison images yourself.
- Do not manually edit current images, references, the report, recordings, or
  `ignore.txt` unless the user explicitly requests that exact change.
- Do not regenerate references without explicit user authorization.
- Do not treat a NUN5 reference as accepted NA2.28 output.
- Preserve unrelated current/report changes.
- Do not expand a local visual fix into release work or broad cleanup.

Before acceptance, report the implementation files changed, capture slots, test
result, and remaining visible differences. After delivery, report both
repository commits and whether each was pushed.
