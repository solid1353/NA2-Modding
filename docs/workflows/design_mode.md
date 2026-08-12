# Design mode

**Enter with:** `des mode` or `design mode`.

No other wording enters Design mode. Plain `des` and `design` do not enter it.

Design mode is primarily used for refactorings, project-wide changes, and other
serious structural work.

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
- Only `imp` authorizes implementation. Agreement with individual points or
  any other wording does not authorize it.
- Design mode remains active until the user approves the reviewed implementation
  with `ver` or sends `exit mode`. An instruction to stop or switch work does
  not itself exit Design mode.

## Implementation and review

1. On `imp`, finalize the design document, set its status to
   `Ready for implementation`, and commit it before implementation
   begins.
2. Start implementation of the consolidated design without leaving Design mode.
3. Implement and validate the design.
4. Add an implementation summary to the design document and set its status to
   `Pending review`.
5. Commit the implementation together with the updated design
   document.
6. Report the result in chat and request user review.

Review may remain pending indefinitely. Do not impose a deadline, restriction,
or automatic cleanup. Design mode remains active during review.

There is no standardized correction workflow after review. If the result is
wrong or incomplete, the user may ask questions or request further changes.
Questions do not authorize implementation; explicit change instructions do,
under the general interaction rules. Further corrections do not require
another `imp`. Do not choose or enter a correction workflow automatically.

When the user enters `ver` after reviewing the implementation, treat it as
implementation approval. Before deleting the individual design document,
review it against the implemented result and promote every still-useful
decision, contract, explanation, example, limitation, and validation finding
to its canonical current documentation. Verify that no useful content remains
owned only by the design document. Then delete the individual design document,
commit the promotion and deletion, and exit Design mode. Never delete
`docs/designs/`.

If the user sends `exit mode` without approving the implementation, exit to
Normal mode without deleting the individual design document. Entering another
workflow mode also exits Design mode.
