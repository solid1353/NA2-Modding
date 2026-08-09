# Coordination, workstreams, and task tracking

**Applies when:** using `TASKS.md`, workstreams, project chats, Notifications,
or an explicit cross-chat handoff.

## Concurrent and cross-chat work

- Concurrent work is allowed only when tasks and mutable resources are
  independent. A shared Git transaction, overlapping canonical edit, physical
  game input, shared ISO promotion state, or other unisolated mutable resource
  has one owner at a time.
- Use tracked canonical files as shared context. When the user explicitly asks
  for a cross-chat handoff, relay the instruction faithfully and separate
  verified facts from interpretation. A handoff does not broaden authorization.
- Keep one owner per artifact and decision. Link to canonical evidence instead
  of copying logs, history, or analysis between chats.

## Notifications

- `Notifications` remains the one-way notification channel for long-running
  task completion, blockers, errors, or required user action.
- Send a concise notification immediately before handing control back and
  include the source title, result/problem, and exact requested user action.
- Respect the shared muted state. `mute` and `unmute` behavior is defined in
  [`../AGENT_COMMANDS.md`](../AGENT_COMMANDS.md).

## `TASKS.md`

- `TASKS.md` is the user's selective coordination and decision tracker. Do not
  read it by default.
- Read or modify it only when the user explicitly asks to inspect, present,
  select, take, add, update, complete, or remove tracked tasks, or when an
  invoked `tasks` or `task done` operation requires it.
- Selecting an entry identifies work; it does not authorize implementation or
  change the normal small/serious-work rules.
- Tasks are added only by the user or on the user's instruction.
- A workstream subsection appears under exactly one of `In Progress`, `Backlog`,
  or `Archive`. `Bugs` remains under `Backlog`; it is not a workstream. Labeled
  bugs belong to the named workstream without becoming workstreams themselves.
  Keep `Testing` last within its current status.
- Approved active work may move its subsection to `In Progress`; move it to
  `Backlog` only on explicit user instruction.
- `task done` removes the exact task through its owning workstream. If the
  subsection becomes empty, move it to `Archive` without deleting it.
- Requested task-list edits are a one-time override across every workflow mode.

## Workstreams

- A workstream is only a named task grouping represented by a `TASKS.md`
  subsection. It does not own chats, documentation, commits, implementation, or
  a repository directory.
- Link a task's temporary handoff or other task-specific document directly from
  its task entry. Keep durable knowledge, component contracts, procedures, and
  policy in their canonical domain documents.
- When entering or resuming a task, read its directly linked documents once; do
  not reread them before every message.

## Project chats

- `TASKS.md` is the sole durable definition of workstreams. Chats hold active
  conversations and do not mirror the workstream structure.
- A workstream may have zero, one, or multiple chats. Create a dedicated chat
  for a concrete active task only when useful and explicitly requested by the
  user.
- Changes to `TASKS.md` do not cause chats to be created, renamed, pinned,
  unpinned, archived, or unarchived.
- Chat organization and pinning are manual and user-directed. Do not archive,
  delete, merge, or repurpose unrelated chats without explicit instruction.
