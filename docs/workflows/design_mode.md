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
- Update the document at agent-determined milestones and whenever the user
  explicitly requests an update.
- Preserve accepted points, integrate corrections, remove rejected content, and
  keep unresolved decisions explicit.
- Only `qwe` authorizes implementation. Agreement with individual points or any
  other wording does not authorize it.
- An explicit instruction to stop or switch work may end Design mode without
  authorizing implementation. Normal mode resumes unless another workflow is
  entered.

## Implementation and review

1. `qwe` ends Design mode, returns to Normal mode, and starts implementation of
   the consolidated design.
2. Implement and validate the design.
3. Add an implementation summary to the design document.
4. Commit and push the implementation together with the updated design
   document.
5. Report the result in chat and request user review.

Review may remain pending indefinitely. Do not impose a deadline, restriction,
or automatic cleanup.

There is no standardized correction workflow after review. If the result is
wrong or incomplete, the user may ask questions, enter
[`Interactive mode`](interactive_mode.md), or give an ordinary implementation
order. Do not choose or enter a correction workflow automatically.

When the user approves the implementation, delete its individual design
document, commit the deletion, and push it. Never delete `docs/designs/`.
