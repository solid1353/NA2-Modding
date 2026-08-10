# Agent commands

This document is the canonical reference for commands interpreted by project
agents. It does not document the `na228` or Workshop command-line interfaces;
use `na228 help`, `workshop help`, and the owning component documentation for
those.

## Approval and task control

- `qwe`, or the same physical keys under another keyboard layout: follow the
  active workflow's `qwe` rule; in Normal mode, authorize the current
  serious-work implementation snapshot.
- `snap`: present the current consolidated implementation snapshot. It
  requests the snapshot only and does not authorize implementation.
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
- `ver`: apply the
  [one-time override](docs/policies/repository.md#git-and-concurrent-work) to the
  current task-owned pending Normal mode changes.
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
  [discussion-summary rule](INTERACTION.md#discussion-and-action) to the current
  discussion topic. The boundary resets only when the discussion explicitly
  moves on.
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

- `mute`, `unmute`: update, commit, and push the shared Notifications mute state.
