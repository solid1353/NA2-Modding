# Agent workflow for local NA2.28 visual fixes

Use this workflow when the user gives you an existing E2E difference and asks
for a local NA2.28 rendering fix. The E2E suite owns the build, replay,
capture, and comparison mechanics; do not reproduce those steps manually.

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
