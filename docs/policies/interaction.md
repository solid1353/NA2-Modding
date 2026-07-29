# Interaction and task policy

## Questions, discussion, and authorization

- Feasibility, possibility, preference, and design questions such as `can we`,
  `should we`, or `would this be better` request an answer only. Read-only
  inspection needed for accuracy is allowed. Execute only after an explicit
  action request such as `do it`, `implement it`, or `change it`.
- A clearly agent-directed request such as `can you add` authorizes that stated
  action only; never infer extra work.
- A question about current agent behavior asks for an exact answer, not a
  behavioral change. Angry, skeptical, or rhetorical wording does not
  authorize starting, stopping, exposing, hiding, relaunching, or otherwise
  changing the operation. Answer in commentary and continue approved work
  unchanged unless the same message explicitly orders a change.
- When an answer is wrong, give the corrected answer immediately. Explain why
  the previous answer was wrong only if the user asks why.
- During explicit discussion, design, planning, or brainstorming mode, every
  later message updates the proposed specification only, even when phrased as
  an imperative. Only the user can exit that mode through explicit execution
  authorization or applicable plan approval.
- Never guess desired action, authorization, cleanup, rollback, or final state.
  Never classify work as mistaken, obsolete, unwanted, disposable, canonical,
  or approved unless the user said so or verified evidence establishes it.
- A policy clarification changes the policy only; it does not authorize
  retroactive filesystem or implementation changes.

## Selected-task workflow

- A `TASKS.md` entry is selected only when the user explicitly chooses or
  starts that exact entry. Topical overlap, inspection depth, task mentions,
  questions, status checks, coordination, and small direct changes do not
  select it.
- Verify that a selected task belongs to the current workstream before
  inspection, planning, or execution. Follow the coordination policy when it
  belongs elsewhere.
- Read-only inspection may begin before plan approval. For a non-brief
  inspection, start with:

```text
Phase: read-only inspection
Purpose: gather enough evidence for the plan
Changes: none
Recommended effort: <level>
Next response: short plan + effort recommendation + needed user inputs + approval gate
```

- Assess effort from the current task's reasoning depth, uncertainty,
  reverse-engineering breadth, coupling, consequence of error, reversibility,
  and validation burden. Recommend the lowest reliable level and name the
  decisive factors. Reassess only when those factors materially change.
- Every selected-task plan includes `Recommended effort: <level>`,
  `Needed from you: <items>` (or `nothing`), and ends with
  **Awaiting plan approval**. Request ideal decision-quality inputs and exact
  matching conditions; use fallbacks only when necessary and state limitations.
- `approved`, `qwe`, or the same physical keys under another keyboard layout
  authorizes the plan, including inside a longer message.
- Record a result as user-verified, user-accepted, or equivalent only when the
  user explicitly confirms that exact result. Plan approval authorizes work but
  does not accept its result. Agent testing, runtime evidence, automated or
  visual comparison, implementation, commit/push, silence, moving to another
  case, or an unrelated continuation command never implies user acceptance.
  Keep agent validation and pending user acceptance as separate statuses.
- If the user orders A, then a stop for testing, review, or acceptance, then B,
  complete A and stop. Requests to finish, batch changes, or use one commit do
  not permit B. Continue to B only when the user explicitly says to skip the
  required stop.
- Execute freely within the approved scope. If the task becomes unclear or the
  whole approach is wrong, stop and clarify; a replacement plan needs approval.
- During approved work, questions, corrections, objections, status requests,
  and rhetorical questions are not stop signals. Answer in commentary and
  continue immediately; a question alone never permits a final response. A
  final response while work remains actionable is allowed only for explicit
  stop/pause/wait, missing required input, unsafe or materially unclear work,
  an unresolved dependency with nothing else in scope, or `zxc`.
- A correction or stop directed at one mistaken action cancels only that
  action. Isolate or undo the detour and continue the parent task unless the
  user stops or replaces it.
- When asked for an already-produced result or evidence, deliver the actual
  requested content immediately in commentary at the next safe boundary before
  any unrelated work. A visual report is not delivered by acknowledgment,
  description, path, link, tool output, or a statement that it exists: the
  composed grid images themselves must be visibly attached. During Continuous
  work, resume the active subtask in the same turn after delivery; never use a
  final response for this intermediate handoff.
- When completed, refresh Git, commit/push the intended work, report the result,
  and do not offer task removal. Completion ends selected-task state even if
  the entry remains in `TASKS.md`.

## Effort at handoff

- An incomplete selected-task handoff with actionable agent work includes a
  standalone `Recommended effort: <level>` line.
- Omit it when waiting solely for user review/action or an external dependency.
  If the user sends `eff` then, reply
  `Recommended effort: none while waiting`.
- Questions and small direct changes outside selected-task state do not use
  task boilerplate unless the user explicitly sends `eff`.

## Standing commands

- `dnf` means do not forward, relay, signal, quote, or summarize the attached
  message to another task. It grants no other authority.
- `ag` means reread live `AGENTS.md` completely and apply it immediately.
- `q:` queues the message in arrival order behind the current safe boundary.
  It supplements rather than replaces current work unless it says otherwise.
  Queued instructions remain in the same changeset unless the user says
  otherwise.
- `con` resumes current work with scope, effort, progress, and approval intact.
- `ep` means `epic`.
- `eff` asks for the current recommended effort and does not change it.
- `report`, `grid`, or a direct request for this chat's existing task grid is
  an immediate response command, not a request to begin producing evidence.
  The next user-visible response is either the actual composed post-change grid
  or the exact inability statement required by `AGENTS.md`. Before declaring
  it unavailable, check the current task's recorded report state and expected
  artifact locations. No other user-visible message or mutating action may
  precede it. The obligation stays with the chat where the user requested it;
  another chat cannot satisfy it. When the same message also requests a
  mistake report to `General`, deliver the task report or inability statement
  first, then send the independent mistake report.
- `sw` resumes after the user stopped only to switch to the recommended effort;
  it preserves prior approval and does not approve an unapproved plan.
- `ss` means savestate. `ss<number>` refers to that numbered savestate slot in
  the user's protected PCSX2, for example `ss7`. The shorthand identifies the
  input; the surrounding request determines what action, if any, is authorized.
- `zxc` invokes the graceful-stop procedure below.
- `task done` accepts the uniquely identifiable current task as complete and
  orders its owning workstream coordinator to remove the exact entry. When the
  command is given in that coordinator, it performs the edit itself. Never
  route task-entry removal to the task named `Task coordinator`; contact that
  task afterward only when the resulting subsection change requires chat
  actualization. Ask when the task is not uniquely identifiable.

## `zxc` graceful stop

- Stop at the next safe boundary without beginning new substantive work. Do
  not interrupt an atomic file, Git, ISO-promotion, or similar operation
  unsafely.
- Create a dated `.agents/<date>-<task-title>-resume.md` recording the objective,
  task title, phase, plan, effort, approval, completed/remaining steps,
  decisions, commands/results/tests, Git state and owned changes, files,
  retained work artifacts, processes/resources, required inputs,
  uncertainties, and exact first resume action.
- Preserve the minimum resumption artifacts and release exclusive resources
  when possible. Disable pending wakeups unless monitoring should continue. Do
  not perform normal completion cleanup.
- Commit and push only the handoff; never commit incomplete implementation
  merely because `zxc` was issued.
- On resume, validate the handoff against live rules, Git, work artifacts, and
  external resources. Delete, commit, and push the handoff before continuing
  once resumption is possible. Preserve prior approval unless drift invalidates
  the approach. A graceful-stop report identifies the handoff, restart safety,
  and any remaining live operation or hazard.
