# Design mode

**Enter with:** `des mode` or `design mode`.

No other wording enters Design mode. Plain `des` and `design` do not enter it.

## Draft creation

1. Infer the design topic from the conversation. Ask only when it is genuinely
   unclear.
2. Resume an existing draft for the same design, or create
   `docs/designs/<topic>.md` when none exists.
3. Give a new document the status `Draft` and write an initial proposal into it.
4. Open the design document in VS Code.
5. Report the draft path and begin grooming the proposal with the user.

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
  authorizing implementation.

## Implementation and review

1. `qwe` ends Design mode and starts implementation of the consolidated design.
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
