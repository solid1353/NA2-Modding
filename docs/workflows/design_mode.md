# Design mode

**Enter with:** `des mode` or `design mode`.

No other wording enters Design mode. Plain `des` and `design` do not enter it.

## Draft creation

1. Infer the design topic from the conversation. Ask only when genuinely unclear.
2. Resume the existing draft for that topic, or create
   `docs/designs/<topic>.md`.
3. A new draft contains its title, `Status: Draft`, and only points explicitly
   stated or approved by the user.
4. Do not add inferred requirements, proposals, decisions, questions,
   alternatives, implementation details, or validation plans.
5. Present agent-generated proposals in chat first. Add them only after explicit
   user approval.
6. If no design points are approved, leave the draft otherwise empty.
7. Open the draft in VS Code and report its path.
8. Removing discussed content does not authorize deleting the draft. Delete the
   draft only on an explicit instruction to delete the draft.

## Discussion

- Discuss the design freely. The document is a consolidated design, not a
  conversation transcript.
- After each user approval of a design point, propose the next unresolved
  design question if one remains.
- Update the document only at milestones or when the user explicitly requests
  an update.
- A milestone occurs when a coherent part of the design has stabilized enough
  to be recorded as a consolidated result, normally when discussion moves to
  another part or the complete design is ready for implementation. Individual
  messages, approvals, corrections, and wording changes are not milestones.
- Preserve accepted points, integrate corrections, remove rejected content, and
  keep unresolved decisions explicit.
- Only `qwe` authorizes implementation. Agreement with individual points or any
  other wording does not authorize it.
- An explicit instruction to stop or switch work may end Design mode without
  authorizing implementation. Normal mode resumes unless another workflow is
  entered.

## Implementation and review

1. On `qwe`, finalize the design document, set its status to
   `Ready for implementation`, and commit and push it before implementation
   begins.
2. `qwe` then ends Design mode, returns to Normal mode, and starts
   implementation of the consolidated design.
3. Implement and validate the design.
4. Add an implementation summary to the design document.
5. Commit and push the implementation together with the updated design
   document.
6. Report the result in chat and request user review.

Review may remain pending indefinitely. Do not impose a deadline, restriction,
or automatic cleanup.

There is no standardized correction workflow after review. If the result is
wrong or incomplete, the user may ask questions, enter
[`Interactive mode`](interactive_mode.md), or give an ordinary implementation
order. Do not choose or enter a correction workflow automatically.

When the user approves the implementation, delete its individual design
document, commit the deletion, and push it. Never delete `docs/designs/`.
