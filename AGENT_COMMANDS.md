# Agent commands

This document is the canonical reference for project-specific agent commands.
Global commands are defined in `@codex-utils/AGENTS_COMMANDS_G.md`. This document
does not document the `na228` or Workshop command-line interfaces; use
`na228 help`, `workshop help`, and the owning component documentation for those.

## Interaction modes

- `des mode`, `design mode`: enter
  [Design mode](docs/interactions/design_mode.md).
- `int mode`, `interactive mode`: enter
  [Interactive mode](docs/interactions/interactive_mode.md).

## Task control and validation

- `snap`: present the current consolidated implementation snapshot.
- `ver`: accept the current result across every repository changed by the task.
  Agents may then add tests. Validate, commit, and push the accepted result. In
  Design mode, first promote useful design content and delete the design
  document, then exit after pushing.
- `exit`: exit Design mode or Interactive mode without accepting the result
  or authorizing a commit. It has no effect when no mode is active.
- `zxc`: follow the
  [graceful-stop procedure](docs/procedures/graceful_stop.md).
- `e2e: <request>` or `e2e <suite> <captures>: <request>`: follow
  [the E2E validation workflow](docs/workflows/e2e_validation.md).

## Conversation and metadata

- `n`: proceed to the next item.
- `imm`: apply the `immediately` behavior from
  [task sequencing](AGENTS.md#task-sequencing) to the most recently added
  unfinished task.
- `mode`: only when the entire user message, after trimming surrounding
  whitespace, is exactly `mode`, respond with only `Default`, `Design mode`, or
  `Interactive mode`, whichever applies. It does not change the mode or grant
  authority. Do not trigger it from a longer message, quoted text, or supplied
  context.
- `ss`, `ss<number>`: identify a savestate or numbered savestate slot. The
  surrounding request determines the authorized action.
