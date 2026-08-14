# Coordination and task tracking

## Concurrent and cross-chat work

- Concurrent work is allowed only when tasks and mutable resources are
  independent. A shared Git transaction, overlapping canonical edit, physical
  game input, shared ISO promotion state, artifact, decision, or other
  unisolated mutable resource has one owner at a time.
- Use tracked canonical files as shared context. When the user explicitly asks
  for a cross-chat handoff, relay the instruction faithfully and separate
  verified facts from interpretation. Link to canonical evidence instead of
  copying logs, history, or analysis between chats.

## Notifications

- `Notifications` remains the one-way notification channel for long-running
  task completion, blockers, errors, or required user action.
- Send a concise notification immediately before handing control back and
  include the source title, result/problem, and exact requested user action.
- Respect the shared muted state in
  `@codex-utils/settings/notifications.json`. `mute` and
  `unmute` behavior is defined in [`AGENT_COMMANDS.md`](../../AGENT_COMMANDS.md).

## `TASKS.md`

- `TASKS.md` is the user's selective coordination and decision tracker. Read or
  modify it only when the user explicitly asks to inspect, present, select,
  take, add, update, complete, or remove tracked tasks, or when `tasks` or
  `task done` requires it.
- Each named subsection appears under exactly one of `In Progress`, `Backlog`,
  or `Archive`. `Bugs` remains under `Backlog`; labels on its entries refer to
  the relevant named subsection without moving those entries. Keep `Testing`
  last within its current status.
- Approved active work may move its subsection to `In Progress`; move it to
  `Backlog` only on explicit user instruction.
- `task done` removes the exact task from its subsection. If the subsection
  becomes empty, move it to `Archive` without deleting it.
- Requested task-list edits are a one-time override across every interaction
  mode.
- Link a task's temporary handoff or other task-specific document directly from
  its task entry. Keep durable knowledge, component contracts, procedures, and
  policy in their canonical domain documents.
