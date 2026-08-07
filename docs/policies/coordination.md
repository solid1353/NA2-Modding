# Coordination, workstreams, and task tracking

**Applies when:** using `TASKS.md`, workstreams, project chats, actualization,
Notifications, or an explicit cross-chat handoff.

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
  invoked `tasks`, `task done`, or `actualize` operation requires it.
- Selecting an entry identifies work; it does not authorize implementation or
  change the normal small/serious-work rules.
- Tasks are added only by the user or on the user's instruction.
- A workstream subsection appears under exactly one of `In Progress`, `Backlog`,
  or `Archive`. `Bugs` remains under `Backlog`; it is not a workstream and has
  no coordinator. Labeled bugs belong to the named workstream without becoming
  workstreams themselves. Keep `Testing` last within its current status.
- Approved active work may move its subsection to `In Progress`; move it to
  `Backlog` only on explicit user instruction.
- `task done` removes the exact task through its owning workstream. If the
  subsection becomes empty, move it to `Archive` without deleting it.
- Commit and push requested task-list edits automatically. Structural workstream
  changes are followed by `actualize`; ordinary entry edits are not.

## Workstreams

- A workstream is a named tracked area represented by a `TASKS.md` subsection.
- Workstream documentation is optional. Create
  `docs/workstreams/<workstream>/` only for durable workstream-specific context
  that has no better canonical owner. Do not require a landing README,
  `context.md`, or fixed section structure.
- Link useful durable workstream documents directly from `TASKS.md` when they
  exist. Keep reusable technical knowledge, component contracts, procedures,
  and policy in their canonical topic/component documents.
- When entering or resuming a workstream, read its applicable durable documents
  once; do not reread them before every message.

## Actualization and Task coordinator

- Both the user and agents may invoke `actualize` / `actualize chats` when
  needed. The command reconciles project chats/coordinators with live
  `AGENTS.md` and `TASKS.md`; it does not select work.
- `Task coordinator` performs actualization only. It does not execute workstream
  tasks or make ordinary task-list edits.
- `Bugs` is excluded. Maintain exactly one coordinator per workstream across
  statuses, reusing or renaming suitable chats and creating missing ones.
- `General` is an ordinary workstream/chat; it has no special behavioral or pin
  priority.
- Actualization unpins project chats, then pins `Project`, `Notifications`, and
  `Task coordinator` in that order, followed by each `In Progress` workstream
  coordinator and its unarchived dedicated task chats in task order. It never
  unarchives archived dedicated task chats.
- Do not archive, delete, merge, or repurpose unrelated chats without explicit
  instruction.
