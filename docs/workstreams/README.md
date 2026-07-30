# Workstream policies

Workstream policies preserve recurring user instructions whose scope is one
`TASKS.md` workstream. They are identified by the exact workstream heading and
discovered through that heading's document link; a Codex chat or thread ID is
not a durable identity.

## Location

When a workstream needs durable documentation, create
`docs/workstreams/<workstream>/README.md` as its short canonical landing page
and link it from the workstream heading in `TASKS.md`. Put explicit recurring
rules in a `## Workstream policy` section. Keep larger plans, working context,
and other workstream-owned documents beside it and link them from the landing
page. Place resumable execution state directly in this owning directory; there
is no separate OS-migration handoff location. Do not create empty files or
directories in anticipation of future rules, and do not maintain a second
index beside `TASKS.md`.

## Content boundary

Record only explicit recurring decisions such as workstream-specific defaults,
scope and ownership boundaries, required inputs, tool or validation conventions,
preferred or prohibited approaches, and cleanup or artifact-retention rules.
Preserve the user's scope and omissions; do not turn agent interpretations into
policy.

Keep universal rules in `AGENTS.md` and the shared policies it routes under
`docs/policies/`, confirmed technical findings in `docs/knowledge/` or
canonical module data, current execution status in plans or handoffs, and
one-off instructions in the active conversation only. Avoid duplicating those
sources in a workstream policy.

## Maintenance and authority

The owning coordinator reads its linked policy whenever it enters or resumes
the workstream. When the user clearly establishes, changes, or retires a
recurring scoped rule, update the policy promptly and commit/push the narrow
documentation change. A current explicit user instruction overrides stored
policy; update the stored rule when the override is intended to persist.
