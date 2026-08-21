# Input-recording validation workflow

This workflow applies when the user provides an input-recording name for the
current task.

## Baseline handoff

1. The user records and replays the baseline through Workshop's default path:

   ```powershell
   ws <game> -s <recording>
   ```

2. The user gives the agent the recording name. The baseline is under
   `@work/captures/<recording>/<game>/`.
3. The agent treats that baseline as read-only. If it does not exist, ask the
   user to create it. If multiple game directories make the intended baseline
   genuinely ambiguous, ask which one applies.
4. The agent does not launch or copy the initial Latest or Manual ISO and does
   not need its build identity. The baseline captures are the evidence for the
   pre-change behavior.

## Implementation and candidate validation

1. Inspect the task-relevant baseline screenshots and savestates, then
   implement the requested change.
2. If game logic changed, finish all earlier selected static and unit checks,
   then build or reuse the canonical cached ISO.
3. Replay the same recording against the cached ISO into a task-owned
   candidate capture path through the exact command in the
   [runtime-testing runbook](../runbooks/runtime-testing.md#input-recording-candidate-replay).
4. Compare the task-relevant candidate captures with the baseline and report
   the observed result.
5. If game logic did not change, do not build a cached ISO or replay a candidate
   merely because the recording was provided.

The candidate replay is agent validation, not user acceptance. Report the
result under the active interaction mode; the user reviews or tests it and
accepts it with `ver`.
