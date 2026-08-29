# Input-recording validation workflow

This workflow applies when the user provides an input-recording name for the
current task.

## Baseline handoff

1. The user records and replays the baseline through `na228`:

   ```powershell
   na228 <game> -s <recording>
   ```

2. The user gives the agent the recording name. The baseline is under
   `@work/captures/<recording>/<game>/`.
3. If the baseline does not exist, ask the user to create it. If multiple game
   directories make the intended baseline genuinely ambiguous, ask which one
   applies.
4. The agent does not launch or copy an initial cached ISO and does
   not need its build identity. The baseline captures are the evidence for the
   pre-change behavior.

## Implementation and candidate validation

1. Inspect the task-relevant baseline screenshots and savestates, then
   implement the requested change.
2. Finish all earlier selected checks, then run
   `na228 build <configuration>`.
3. Replay the same recording against the ISO returned by that command:

   ```powershell
   na228 <iso-path> -s <recording> <task-owned-candidate-path>
   ```

   Use an explicit task-owned candidate path; never use default
   capture path.
4. Compare the task-relevant candidate captures with the baseline and report
   the observed result.

The candidate replay is agent validation, not user acceptance. Report the
result under the active interaction mode; the user reviews or tests it and
accepts it with `ver`.
