# Agent workflow for local NA2.28 visual fixes

Use this workflow when the user gives you an existing E2E difference and asks
for a local NA2.28 rendering fix. The E2E suite owns the build, replay,
capture, and comparison mechanics; do not reproduce those steps manually.

## Invocation

The root standing command may identify the suite and captures directly:

```text
e2e font 25: <requested fix>
e2e font 25, 27-30: <requested fix>
```

A capture expression accepts one slot, comma-separated slots, and inclusive
ranges. This command authorizes immediate implementation and repeated execution
of the affected E2E suite. Begin with the named prepared differences and keep
implementing, running `na228 test <suite> -b`, and inspecting the regenerated
differences until every named capture has the requested result or a concrete
blocker remains. Do not stop for separate plan approval.

## Read the evidence

For suite `<suite>` and capture `<slot>`:

- `captures/<suite>/approved/<slot>.png` is the accepted NA2.28 rendering.
- `captures/<suite>/pending/<slot>.png` is the current NA2.28 rendering.
- `captures/<suite>/references/<slot>.png` is the reference-game rendering.
- `captures/<suite>/reports/approved-vs-pending/` contains the prepared pairs,
  diffs, blends, and grids for the current NA2.28 change.
- `captures/<suite>/sstates/pending/<slot>.p2s` is available when the visible
  difference requires runtime investigation.

The approved-versus-pending comparison is authoritative for a local NA2.28
regression. A reference image provides design context; different games or
video modes do not necessarily produce pixel-identical frames.

When the target is plain text, an agent using ordinary capture PNGs or grid
pages must zoom them until individual glyph pixels, spacing, baselines, and
alignment are clearly legible. A thumbnail, fitted whole screenshot, or fitted
grid page alone is not sufficient evidence for a text-rendering conclusion.
Inspect the relevant pair, diff, or blend at that readable zoom before deciding
what to change and again before deciding that the result is correct.

## Evidence gate

- Open and inspect every capture named by the command. Evidence from one slot
  never establishes the state of another slot.
- A relational claim such as "aligned with", "matches", "same bounds", or
  "consistent across" requires an actual comparison of every named side at a
  readable zoom. Observing that one capture moved is not evidence that it now
  aligns with another capture.
- When the request distinguishes selected, highlighted, ordinary, disabled, or
  other states, inspect the exact state named for each capture. Do not
  substitute a visually similar state.
- After each `na228 test <suite> -b` run, reopen the regenerated evidence for
  every named capture. Pre-run images and observations cannot establish the
  post-run result.
- Do not claim that a result is correct, aligned, or complete until every
  property named by the request has been directly checked in every applicable
  capture.
- Do not say that comparison, testing, or inspection is happening "now" and
  then yield or end the turn. Perform that action in the same turn and report
  only the evidence actually obtained. Stop only for a concrete blocker that
  prevents the required inspection or test.

## Fix and verify

1. Inspect the supplied difference and identify the exact requested visual
   result.
2. Change only the NA2.28 code or asset responsible for that result.
3. Run the affected suite with a fresh Screenshot Test build. For the current
   font suite:

   ```powershell
   na228 test font -b
   ```

4. Inspect the regenerated approved-versus-pending report.
5. Repeat the change, command, and inspection until the requested local result
   is correct.

The command builds or reuses Screenshot Test, replays the suite recording,
captures its markers and savestates, removes pixel-identical and suite-ignored
pending screenshots, and regenerates the comparisons transactionally.

## Boundaries

- Do not navigate PCSX2 manually or construct comparison images yourself.
- Do not edit `approved/`, `pending/`, `references/`, reports, recordings,
  `screens.tsv`, or `ignore.txt` unless the user explicitly requests that
  exact change.
- Do not approve captures or regenerate references. Acceptance belongs to the
  user.
- Do not treat a NUN5 reference as accepted NA2.28 output.
- Preserve unrelated pending differences.
- Do not expand a local visual fix into release work, broad cleanup, or
  unrelated validation.

At handoff, name the implementation files changed, the capture slots affected,
the `na228 test <suite> -b` result, and any remaining visible difference. Keep
agent validation separate from user acceptance.
