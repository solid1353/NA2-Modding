# Agent commands

This document is the canonical reference for commands interpreted by project
agents. It does not document the `na228` or Workshop command-line interfaces;
use `na228 help`, `workshop help`, and the owning component documentation for
those.

## Approval and task control

- `qwe`, or the same physical keys under another keyboard layout: follow the
  active workflow's `qwe` rule; outside a workflow mode, authorize the current
  serious-work implementation snapshot.
- `snapshot`: present the current consolidated implementation snapshot. It
  requests the snapshot only and does not authorize implementation.
- `tasks`: read and present `TASKS.md`.
- `task done`: remove the uniquely identifiable current task from `TASKS.md`.
  If its workstream becomes empty, move the workstream to `Archive`. Ask when
  the task is not uniquely identifiable.

## Conversation and metadata

- `dnf`: do not forward, relay, quote, or summarize the attached message to
  another task. It grants no other authority.
- `ag`: reread live root `AGENTS.md` and apply it immediately.
- `q:`: the request was queued earlier and may be stale. Compare it with the
  current state before acting. Perform only the still-relevant portion; do not
  repeat, undo, or conflict with work completed while it waited.
- `con`: resume the current work with scope, effort, progress, and approval
  state intact.
- `sum`: summarize the complete current discussion topic with accepted
  corrections integrated. Exclude rejected or withdrawn wording and add no new
  points. The boundary resets only when the discussion explicitly moves on.
- `eff`: report the currently recommended effort without changing it.
- `report`: provide the factual textual account requested by the user.
- `sw`: resume after the user changed the chat to the recommended effort;
  preserve prior approval.
- `ss`, `ss<number>`: identify a savestate or numbered savestate slot. The
  surrounding request determines the authorized action.

## Validation

- `e2e: <request>` or `e2e <suite> <captures>: <request>`: perform E2E
  validation for the current work under the normal validation policy. Suite and
  capture identifiers name expected evidence; execution remains global across
  the tracked suite set. The command authorizes E2E only, not unrelated
  validation. Follow [`../e2e/AGENT_GUIDE.md`](../e2e/AGENT_GUIDE.md).

## Notifications

- `mute`, `unmute`: update, commit, and push the shared Notifications mute state.

## `zxc` graceful stop

`zxc` pauses unfinished work safely:

1. Stop at the next safe boundary.
2. Create a named stash containing only the current task-owned uncommitted work;
   include the workstream and task in the stash name.
3. Write a temporary resume handoff under
   `docs/workstreams/<workstream>/<date>-<task>-resume.md`.
4. Create or update the corresponding `TASKS.md` entry and link it to the
   handoff.
5. Commit and push only the handoff and `TASKS.md` update. Never commit the
   unfinished implementation.
6. Stop.

The handoff records the exact stash name/reference, what it contains, current
state, completed and remaining work, blockers, validation state, and restore
command.

On resume, follow the task link, apply the recorded stash, resolve ordinary Git
conflicts using the stash and handoff, and verify that the paused work was
recovered correctly before dropping the stash. Then delete the temporary
handoff, remove its task link, commit and push that cleanup, keep the task entry
until the work itself is complete, and continue normally.
