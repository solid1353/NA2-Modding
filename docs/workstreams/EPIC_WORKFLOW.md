# Epic workflow

## Activation and ownership

- This workflow applies only after the user explicitly declares the exact work
  an epic. A workstream linking this file does not classify all of its tasks,
  stages, screenshots, comparisons, or other artifacts as epic content.
- Only the user chooses what belongs in an epic and what is promoted into
  `docs/workstreams/<workstream>/epics/<epic-id>/`. Never create an epic
  directory, epic README, epic entry, or epic report artifact without that
  explicit choice.
- Ordinary screenshots, comparison grids, and runtime outputs remain under
  `work/<exact task title>/artifacts/`. Confirmed reusable findings belong in
  existing knowledge files, and active execution state belongs in the existing
  workstream plan, unless the user explicitly promotes them into an epic.

## Modes

- **Sequential** is the default. Complete one subtask, report it, and stop.
  After the user accepts it, present the remaining epic and wait.
- **Continuous** is used only when the user explicitly requests it. Complete
  subtasks in order without further user input until none remain or a blocker
  is encountered. If the user ordered a stop between two steps for testing,
  review, or acceptance, Continuous mode stops there unless the user explicitly
  says to skip that stop.
- Pending review or acceptance of a completed subtask is not a blocker in
  Continuous mode. Record the pending state and continue the next actionable
  approved subtask. Do not hand control back, wait, or schedule a wakeup unless
  the user explicitly required that boundary or a real dependency blocks the
  remaining independent epic work.

## Subtask flow

For each subtask:

1. Analyze only as needed.
2. Implement.
3. Commit and push.
4. Visibly send the result in the accepted composed-grid format from the
   owning chat. In Continuous mode, send it in commentary and continue the next
   independent approved subtask.

Existing code, enabled hooks, compilation, and successful composition do not
make a selected subtask implemented when accurate current-result evidence still
shows its requested defect. Keep that case unresolved under `pending/` and use
the existing accurate grid as failure evidence; do not replace it with a
missing-input claim or ask the user to reproduce the same result. Changing only
execution text or status cannot substitute for changing the result.

A later nonvisual integration, build, metadata, or documentation repair to an
already-reported subtask does not create a new grid obligation when it neither
changes the visible result nor makes the delivered grid's imagery or metadata
stale. If the repair changes visible output or invalidates the delivered
evidence, treat the corrected result as due and update `Pending grid`.

Every active epic README records `Mode`, `Current subtask`, and `Pending grid`.
`Pending grid` is `none`, a repository-relative path to the composed
post-change grid under that epic's `awaiting_approval/` directory, or
`missing: <exact post-change input>`. Set it as soon as a subtask result becomes
due and clear it only after the owning chat visibly sends that grid or exact
inability response. Consult these fields before every final response.

Track implementation, agent validation, delivery to the user, and explicit
user acceptance as separate states in epic READMEs and reports. Only an
explicit user confirmation referring to the exact result may set
`user-verified`, `accepted`, `confirmed complete`, or an equivalent final
status. Tests, runtime proof, a matching grid, commit/push, silence, beginning
the next subtask, or unrelated continuation instructions cannot do so.
Continuous mode permits progress without acceptance; it does not manufacture
acceptance for earlier subtasks.

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

Internal tool output, paths, links, or claims of delivery do not prove
delivery. Follow the universal turn-end gate in `AGENTS.md` after each epic
report.

Preserve each epic and its report grids together under
`docs/workstreams/<workstream>/epics/<epic-id>/`. Each epic directory contains
a README describing its current subtasks and report grids, and the owning
workstream README links every active epic. Task-local source screenshots and
intermediate files remain under `work/<exact task title>/`; they are not the
canonical epic record.

Canonical epic grids are split by acceptance state:

- `pending/` contains baselines and unresolved cases that still require
  implementation or valid post-change evidence;
- `awaiting_approval/` contains implemented post-change result grids whose
  exact displayed result has not yet received explicit user acceptance.

When an unresolved epic case produces and shows a new runtime-injected
candidate, immediately preserve that exact evidence in a truthfully
candidate-labeled grid under `awaiting_approval/` and update the README state,
image reference, and `Pending grid` atomically. This obligation applies while
the candidate implementation remains uncommitted and integrated validation is
still pending; do not leave the older baseline as the sole canonical record.
`Uncommitted` describes eligibility for Git history, not permission to leave
canonical paths dirty; preserve the candidate through the repository's clean
handoff-boundary rule.

Accepted grids are not retained in the epic. When the user accepts or verifies
an exact result, delete its grid and remove its README image reference in the
same commit. When a pending case gains valid post-change evidence, move or
regenerate its grid under `awaiting_approval/` and update its README status and
image reference atomically. If an awaiting-approval result is rejected or
reopened, move its current grid back to `pending/` while recording the remaining
defect.

No canonical grid remains at the epic root, and no `done/` directory exists.
Create either allowed state directory only when it contains at least one real
grid; never add placeholders to retain an empty directory.

Before committing, enumerate the epic directory and verify that every report
image is referenced by the README, every README image reference resolves, and
each grid's folder agrees with its recorded acceptance state; do not leave
stale, missing, or root-level report artifacts.

A grid may contain one row, but never only one screenshot; every row shows NUN5
on the left and NA2.28 on the right.

## Savestate updates

Replacing, renumbering, or semantically regrouping an active epic input batch
is one atomic canonical-update boundary. Before further implementation or
runtime testing, update the epic README's input/provenance paths, slot meanings,
priorities, case states, remaining defects, `Current subtask`, and `Pending
grid`; regenerate every affected canonical baseline/report grid from the new
task-owned evidence; remove superseded grid artifacts; and verify every README
image reference. Continuous mode resumes immediately after this canonical
update and does not permit implementation to outrun stale epic documentation
or pictures.

When the user provides or identifies a new savestate pair for a
user-declared epic case, immediately:

1. Copy both reference and current states from the protected user library into
   the owning workstream's `inputs/sstates/` directory and record provenance.
2. Refresh the retained mismatch entry and its source screenshots from those
   task-owned copies.
3. Update the canonical epic README and composed report grid to show the new
   slot, status, and remaining defect.

A worker may not reclassify user-identified epic-case inputs as deferred,
plan-only, or outside the active epic to omit this canonical update.
Deferring their implementation changes only the recorded case state; it does
not waive the README and baseline-grid boundary.

A chat-only acknowledgment is not an update. Do not report the savestate as
recorded until the task-owned copies and canonical epic artifacts reflect it.
If replacement evidence reopens an accepted case, create its regenerated grid
under `pending/` until a new implementation produces a result for
`awaiting_approval/`.
