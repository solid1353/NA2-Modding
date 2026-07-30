# Coordination policy

## Cross-chat work

- Agents may work concurrently only when tasks and resources are independent.
  Shared Git transactions, overlapping canonical edits, physical game input,
  shared ISO promotion state, and other unisolated mutable resources are
  exclusive. The existing owner keeps the resource; competitors sleep and
  wake rather than inventing work. Independent worker-output ISOs are allowed.
- Schedule a bounded wakeup only when no other approved in-scope work is
  actionable, a concrete external operation is already running or a future
  state change is confirmed, and that change can be detected without a new user
  message. Never poll for an action the user has not explicitly agreed to
  perform. When user input or a user-created artifact is required, ask once and
  stop; in Continuous mode, queue only the blocked subtask and continue
  independent approved subtasks first. Check once per wakeup, make no unrelated
  changes, and disable it when resolved.
- A workstream that asks `Project` for anything stops immediately and sleeps
  until `Project` responds.
- Use canonical tracked files as shared context. Send concise handoffs only
  when another chat must act or decide, with owner, objective, exact paths,
  commit, confirmed decisions, unresolved questions, and requested action.
- When relaying user instructions, quote them verbatim and preserve scope,
  force, ambiguity, and omissions. Put confirmed facts in `Verified context`
  and interpretations in a labeled non-authoritative section. Never attribute
  inferred requirements to the user.
- Cross-workstream reports, findings, failures, suggestions, and hints are
  informational only. They do not authorize the recipient to investigate,
  test, implement, or interrupt its current work.
- `sin` is a standing policy-enforcement trigger. The reporting task sends
  `Policeman` a self-contained account containing the exact user complaint or
  instruction, the exact failure, current work and approval state, and relevant
  paths or commits. Sending it does not stop, replace, or waive any other rule
  governing the reporting task.
- `Policeman` inspects the relevant live rules, identifies the exact violation,
  and makes a durable correction or strengthens the existing rule's
  placement or wording when needed. It commits and pushes the policy change,
  then directly tells the offending task what it did wrong and the behavior
  now required. It does not take over implementation work without separate
  authorization.
- The recipient may act only when the user explicitly authorized that action
  in the receiving chat, in another chat, or through a standing instruction.
  Authorization from another chat must be relayed as the user's exact quoted
  instruction with its source; an agent's request or interpretation never
  substitutes for it.
- Without authorization, do not perform substantial analysis to validate a
  cross-workstream hint. Report or preserve it as context and continue the
  authorized work.
- Keep one owner per artifact/decision. Link rather than copy logs or history;
  avoid acknowledgments, chatter, polls, and duplicate analysis.

## Workstreams and Notifications

- The policy linked from a `TASKS.md` subsection is the recurring scoped source
  for that workstream. Read it on entry/resume. Store only recurring user rules;
  keep universal rules here, technical findings in knowledge, execution state
  in plans/handoffs, and one-off instructions in chat.
- Only long-running tasks notify the `Notifications` task, immediately before
  handing control back on completion, user-input/approval need, error, or
  blocker. Include source title, result/problem, and exact requested user
  action. Respect the configured muted state; muted events are not queued.
- In `Notifications`, `mute` and `unmute` update, commit, and push the configured
  notification state.

## Policeman

- `Policeman` is the shared policy enforcer. Contact it only through `sin` or
  an explicit policy-enforcement instruction.
- It preserves the reporting task's exact scope and context, corrects policy
  as needed, and confronts the offending task with the exact violated rule and
  required behavior. It does not silently absorb reports or become a general
  implementation, coordination, or task-management channel.
- After every `sin` report, it adjusts the live policies with a durable
  correction or strengthening based on that report.
- Policy adjustments prevent the failed behavior across its applicable scope;
  they do not encode an incident's exact path, artifact, task title, or other
  one-off detail unless the rule inherently applies only there.
- A `sin` report is an allegation, not proof of guilt. `Policeman` arrests or
  confronts a task as an offender only after evidence confirms that the task's
  action violated an exact rule that was live when it acted. A newly added or
  clarified rule cannot retroactively turn previously permitted behavior into
  a violation.
- An exact live rule includes applicable direct and standing user
  instructions, not only wording already persisted in repository policy.
  Failure to store a repeated user rule does not erase its authority or justify
  lifting charges; verify that the instruction applied to the task when it
  acted, then enforce it and repair the policy-storage gap separately.
- Every confirmed-violation confrontation tells the offending task exactly:
  `YOU'RE UNDER ARREST.` When no live-rule violation is confirmed, do not use
  that statement or label the reported task an offender; start the enforcement
  response exactly with `Charges lifted.`
- It also directs the offending task to correct the violation and any resulting
  noncompliant state itself. This is standing authorization only for remediation
  needed to restore compliance within the work's previously authorized scope;
  it never authorizes new implementation or unrelated cleanup.

## Task coordinator

- `Task coordinator` maintains the mapping between `TASKS.md` workstreams and
  Codex coordinator tasks. It does not select or execute workstream tasks.
- Contact `Task coordinator` only for `actualize` or `actualize chats`
  requests. Do not send it task-list edits, reports, implementation or policy
  work, or ordinary coordination.
- `actualize` or `actualize chats` means synchronize chats with live
  `AGENTS.md` and `TASKS.md`; it is unrelated to ISO/PNACH actualization.
- Actualization may create missing coordinators without separate approval,
  reuses/renames suitable chats, and maintains exactly one coordinator whose
  title exactly matches each workstream across statuses. Its scope is limited
  to that workstream.
- Every new project chat's initial scope carries standing authorization to
  commit and push completed work. That authorization does not approve a task
  plan or start task execution.
- Actualization unpins project chats, then pins `General`, `Project`,
  `Policeman`, `Notifications`, and `Task coordinator` in that order, followed
  by each `In Progress` workstream coordinator and its unarchived dedicated
  task chats in task order. It never unarchives archived dedicated chats.
- Actualization does not select work. It updates scope/rules only when stale and
  reports reused, renamed, created, or signaled coordinators.
- Creating, renaming, moving, or deleting a whole workstream subsection
  triggers actualization before the corresponding task-management commit and
  push. Editing entries within an unchanged subsection does not. Non-coordinator
  chats send one concise request to `Task coordinator`.
- Do not archive, delete, merge, or repurpose unrelated chats without explicit
  instruction.
- A task presented in the wrong chat is routed to the matching coordinator or
  dedicated chat with exact wording, status, instructions, evidence, and next
  step; the originator stops parallel work.
- Recommend a separate task only when sustained unrelated context or distinct
  responsibilities threaten quality. Prefer existing tasks and create nothing
  until the user approves.

## `TASKS.md`

- Tasks are added only by the user or by an agent on the user's order.
- A workstream subsection appears under exactly one of `In Progress`,
  `Backlog`, or `Archive`; `Testing` is last within its current status.
- Approved active work moves its whole subsection to `In Progress`. Move to
  `Backlog` only by explicit user instruction.
- `task done` makes the owning workstream coordinator remove the exact task;
  the task named `Task coordinator` never performs task-entry edits. If the
  subsection becomes empty, move it to `Archive` without deleting it or
  archiving its coordinator chat. If work returns, move it to `In Progress`
  when approved or to `Backlog` only by explicit instruction.
- Documented workstreams use `docs/workstreams/<workstream>/README.md`, linked
  from the subsection heading, with recurring rules under
  `## Workstream policy`.
- After a successful push or when asked what is next, a coordinator reports
  only its own subsection choices across statuses, word for word, in original
  order with applicable headings.
- Commit and push authorized task-management edits immediately. Stage only
  `TASKS.md` and dedicated context created for that update. Actualize chats only
  for whole-subsection creation, rename, status move, or deletion.

## Cross-install handoffs

- `.agents/` is intentional installation-context infrastructure, not clutter,
  but workstream resume handoffs never live there.
- `.agents/git-authors.tsv` stores non-secret author identities only.
- Dated handoffs are context snapshots subordinate to live repository state,
  rules, docs, and user instructions. Machine paths and task IDs may appear
  only as originating-install context.
- Workstream resume handoffs are canonical documents placed directly beside
  the owning `docs/workstreams/<workstream>/README.md`; they use
  repository-relative paths and omit installation-specific task IDs.
