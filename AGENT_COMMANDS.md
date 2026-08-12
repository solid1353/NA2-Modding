# Agent commands

This document is the canonical reference for commands interpreted by project
agents. It does not document the `na228` or Workshop command-line interfaces;
use `na228 help`, `workshop help`, and the owning component documentation for
those.

## Approval and task control

- `snap`: present the current consolidated implementation snapshot.
- `imp`: authorize implementation of the current consolidated proposal.
  Follow the active workflow's implementation behavior.
- `ver`: accept the current pending result and follow the active workflow's
  acceptance behavior.
- `commit`: apply the repository policy's one-time commit override to the current
  task-owned pending changes. It does not verify the result.
- `exit`: exit Design mode or Interactive mode without accepting the result
  or authorizing a commit. It has no effect in Normal mode.
- `tasks`: read and present `TASKS.md` under the
  [coordination policy](docs/policies/coordination.md).
- `task done`: apply the task-completion behavior defined by the
  [coordination policy](docs/policies/coordination.md).
- `c on`, `c off`: change the current chat's persistent Normal mode
  commit setting as defined in
  [`normal_mode.md`](docs/workflows/normal_mode.md#commit-setting).
- `c`: respond only with `Commit: on` or `Commit: off`, reporting the current
  chat's persistent Normal mode commit setting. It does not change the setting
  or grant authority.
- `zxc`: follow the
  [`graceful-stop procedure`](docs/procedures/graceful_stop.md).

## Conversation and metadata

- `n`: proceed to the next item.
- `mode`: only when the entire user message, after trimming surrounding
  whitespace, is exactly `mode`, respond with only `Normal mode`, `Design
  mode`, or `Interactive mode`, whichever is active. It does not change the
  mode or grant authority. Do not trigger it from a longer message, quoted
  text, or supplied context.
- `ag`: reread live root `AGENTS.md` and apply it immediately.
- `q:`: the request was queued earlier and may be stale. Compare it with the
  current state before acting. Perform only the still-relevant portion; do not
  repeat, undo, or conflict with work completed while it waited.
- `con`: resume the current work with scope, effort, progress, and approval
  state intact.
- `sum`: apply the
  [discussion-summary rule](AGENTS.md#discussion-and-action) to the current
  discussion topic. The boundary resets only when the discussion explicitly
  moves on.
- `ex`: explain the current subject.
- `eff`: report the currently recommended effort without changing it.
- `sw`: resume after the user changed the chat to the recommended effort;
  preserve prior approval.
- `ss`, `ss<number>`: identify a savestate or numbered savestate slot. The
  surrounding request determines the authorized action.

## Validation

- `e2e: <request>` or `e2e <suite> <captures>: <request>`: perform E2E
  validation for the current work under the normal validation policy. Suite and
  capture identifiers name expected evidence; execution remains global across
  the tracked suite set. The command authorizes E2E only, not unrelated
  validation. Follow [`e2e/AGENT_GUIDE.md`](e2e/AGENT_GUIDE.md).

## Notifications

- `mute`, `unmute`: update and commit the shared Notifications mute state.
