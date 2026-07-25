# Epic workflow

## Modes

- **Sequential** is the default. Complete one subtask, report it, and stop.
  After the user accepts it, present the remaining epic and wait.
- **Continuous** is used only when the user explicitly requests it. Complete
  subtasks in order without further user input until none remain or a blocker
  is encountered.

## Subtask flow

For each subtask:

1. Analyze only as needed.
2. Implement.
3. Commit and push.
4. Report the result using the accepted composed-grid format.

## Epic-wide analysis and broad fixes

Epic-wide analysis is exceptional. It is allowed only when the epic is new and
has not yet received broad analysis, a concrete need cannot be resolved within
the current subtask, or specific evidence suggests one broad fix may be better
than separate subtask fixes. It must remain brief, produce an actionable
conclusion relatively quickly, reuse existing analysis, and never be repeated
routinely before subtasks.

If epic-wide analysis finds a broad fix, trial it through a task-owned test ISO
without promoting it to canonical project files. Report the trial, stop, and
ask the user to validate the approach. If accepted, promote the fix, commit and
push it, and continue. If rejected, discard the provisional trial. If the need
for a broad fix appears during subtask implementation, stop before making it
and ask the user to decide.

## Epic reporting and storage

When the user asks for the epic, present all remaining work using the accepted
composed-grid format, split under visible semantic-group headings. Keep every
grid with its group; when one group needs multiple grids, chunk it under the
same heading instead of presenting those grids as separate groups. In
sequential mode, present the remaining epic after the completed subtask is
accepted.

Commentary or tool output does not prove delivery. The final response itself
must visibly contain every semantic-group heading and every composed grid.

Preserve each epic and its report grids together under
`docs/workstreams/<workstream>/epics/<epic-id>/`. Each epic directory contains
a README describing its current subtasks and report grids, and the owning
workstream README links every active epic. Task-local source screenshots and
intermediate files remain under `work/<exact task title>/`; they are not the
canonical epic record.

A grid may contain one row, but never only one screenshot; every row shows NUN5
on the left and NA2.28 on the right.

## Savestate updates

When the user provides or identifies a new savestate pair for an epic case,
immediately:

1. Copy both reference and current states from the protected user library into
   the owning workstream's `inputs/sstates/` directory and record provenance.
2. Refresh the retained mismatch entry and its source screenshots from those
   task-owned copies.
3. Update the canonical epic README and composed report grid to show the new
   slot, status, and remaining defect.

A chat-only acknowledgment is not an update. Do not report the savestate as
recorded until the task-owned copies and canonical epic artifacts reflect it.
