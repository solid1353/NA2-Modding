# Normal mode

## Commit setting

Each chat has its own Normal mode commit setting and starts with `c off`.
The setting persists across tasks, messages, context compaction, and temporary
entry into another workflow mode. It is not shared with other chats or stored
in the repository.

- `c on` makes completed Normal mode work commit automatically.
- `c off` leaves completed Normal mode work uncommitted.
- `ver` is a one-time override for the current task-owned pending Normal mode
  changes.

One-time override behavior is defined in the
[repository policy](../policies/repository.md#git-and-concurrent-work). Only
`c on` or `c off` changes the persistent setting. Design mode and Interactive
mode retain their own commit behavior.

Game/runtime patches remain uncommitted until `ver`, regardless of the
persistent setting. Starting a patch does not change that setting.

## Action boundary

Immediately before beginning implementation or another requested state-changing
operation, state:

```text
Changes: <what will be changed>
Needed from you: <required input or nothing>
Commit: <on or off>
```

`Commit` reports the persistent setting. For a one-time override, append the
override to the reported setting, for example
`Commit: off (ver authorizes commit)`.

If `Needed from you` is not `nothing`, do not begin the operation. Ask for any
savestate, screenshot, dump, file, reproduction, access, decision, or other
input that is required or would noticeably improve efficiency or quality. The
ability to continue through a substantially slower or more speculative route
is not a reason to avoid asking. Resume automatically after the input is
provided.
