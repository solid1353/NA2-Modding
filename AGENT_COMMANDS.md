# Agent commands

This document is the canonical reference for project-specific agent commands.
Global commands are defined in `@codex-utils/AGENT_COMMANDS.md`. This document
does not document the `na228` or Workshop command-line interfaces; use
`na228 help`, `workshop help`, and the owning component documentation for those.

## Interaction modes

- `des mode`, `design mode`: enter
  [Design mode](docs/interactions/design_mode.md).
- `int mode`, `interactive mode`: enter
  [Interactive mode](docs/interactions/interactive_mode.md).

## Approval and task control

- `snap`: present the current consolidated implementation snapshot.
- `ver`: accept the current pending result and follow the active interaction mode's
  acceptance behavior.
- `exit`: exit Design mode or Interactive mode without accepting the result
  or authorizing a commit. It has no effect in Normal mode.
- `zxc`: follow the
  [graceful-stop procedure](docs/procedures/graceful_stop.md).
- `c on`, `c off`: change the current chat's persistent Normal mode
  commit setting as defined in
  [`normal_mode.md`](docs/interactions/normal_mode.md#commit-setting).
- `c`: respond only with `Commit: on` or `Commit: off`, reporting the current
  chat's persistent Normal mode commit setting. It does not change the setting
  or grant authority.

## Conversation and metadata

- `n`: proceed to the next item.
- `imm`: apply the `immediately` behavior from
  [task sequencing](AGENTS.md#task-sequencing) to the most recently added
  unfinished task.
- `mode`: only when the entire user message, after trimming surrounding
  whitespace, is exactly `mode`, respond with only `Normal mode`, `Design
  mode`, or `Interactive mode`, whichever is active. It does not change the
  mode or grant authority. Do not trigger it from a longer message, quoted
  text, or supplied context.
- `sum`: apply the
  [discussion-summary rule](AGENTS.md#discussion-and-action) to the current
  discussion topic. The boundary resets only when the discussion explicitly
  moves on.
- `ss`, `ss<number>`: identify a savestate or numbered savestate slot. The
  surrounding request determines the authorized action.

## Validation

- `e2e: <request>` or `e2e <suite> <captures>: <request>`: follow
  [the E2E validation workflow](docs/workflows/e2e_validation.md).

## Notifications

- `mute`, `unmute`: update and commit the shared Notifications mute state.
