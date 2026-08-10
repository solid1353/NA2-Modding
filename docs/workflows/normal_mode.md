# Normal mode

Normal mode is active by default whenever no other workflow mode is active.
Follow the shared discussion, authorization, sequencing, and completion rules
in [`INTERACTION.md`](../../INTERACTION.md).

## Small, direct work

Small, direct work does not require a separate design phase.

## Serious work

Work is serious when it requires decisions about architecture, user-visible
behavior, compatibility, or coordinated changes across multiple components.

- Design serious work through normal responsive dialogue. Read-only inspection
  is allowed; canonical implementation changes are not.
- Design mode is optional and is not required merely because work is serious.
- Natural-language agreement such as `yes`, `good`, or `do that` approves the
  current design point only. Once settled, present one concise implementation
  snapshot containing the intended outcome, scope, important architecture or
  behavior, proposed persistent mechanisms, and planned validation.
- Begin implementation of serious work only after `qwe`. If implementation
  requires a material change to the snapshot, stop and request user direction
  rather than extending the authorization.

## Task sequencing

- If a later item is serious, finish already-authorized small items in order and
  queue the serious item for design unless the user makes it immediate.

## Commit setting

Each chat has its own Normal mode commit setting and starts with `c off`.
The setting persists across tasks, messages, context compaction, and temporary
entry into another workflow mode. It is not shared with other chats or stored
in the repository.

- `c on` makes completed Normal mode work commit and push automatically.
- `c off` leaves completed Normal mode work uncommitted and unpushed.
- `ver` is a one-time override for the current task-owned pending Normal mode
  changes.

One-time override behavior is defined in the
[repository policy](../policies/repository.md#git-and-concurrent-work). Only
`c on` or `c off` changes the persistent setting. Design mode and Interactive
mode retain their own commit behavior.

Game/runtime patches remain uncommitted until `ver`, regardless of the
persistent setting. Starting a patch does not change that setting.

## Action boundary

Questions, discussion, design, planning, and brainstorming do not require a
work announcement. Immediately before beginning implementation or another
requested state-changing operation, state:

```text
Changes: <what will be changed>
Needed from you: <required input or nothing>
Commit: <on or off>
```

`Commit` reports the persistent setting. For a one-time override, append the
override to the reported setting, for example
`Commit: off (ver authorizes commit and push)`.

If `Needed from you` is not `nothing`, do not begin the operation. Ask for any
savestate, screenshot, dump, file, reproduction, access, decision, or other
input that is required or would noticeably improve efficiency or quality. The
ability to continue through a substantially slower or more speculative route
is not a reason to avoid asking. Resume automatically after the input is
provided.

Exact mode-entry commands in root [`AGENTS.md`](../../AGENTS.md) enter other
workflow modes. When one of those modes exits, Normal mode resumes.
