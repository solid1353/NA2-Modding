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

Only `c on` or `c off` changes the persistent setting.

## Action-boundary setting

In Normal mode, add this workflow-specific setting to the universal action
boundary:

```text
Commit: <on or off>
```

`Commit` reports the persistent setting. For a one-time override, append the
override, for example:

```text
Commit: off (ver authorizes commit)
```
