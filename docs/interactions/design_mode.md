# Design mode

Design mode is primarily used for refactorings, project-wide changes, and other
serious structural work.

## Draft creation

1. Infer the design topic from the conversation. Ask only when genuinely unclear.
2. Resume the existing draft for that topic, or create
   `docs/designs/<topic>.md`.
3. A new draft contains its title, `Status: Draft`, and only user-stated or
   explicitly approved points. Keep inferred proposals, questions, alternatives,
   implementation details, and validation plans in chat until approved.
4. If no design points are stated or approved, leave the draft otherwise empty.
5. Open the draft in VS Code and report its path.
6. Removing discussed content does not authorize deleting the draft. Delete the
   draft only on an explicit instruction to delete the draft.

## Discussion

- After each user approval of a design point, propose the next unresolved
  design question if one remains.
- Update the document only at milestones or when the user explicitly requests
  an update.
- A milestone occurs when a coherent part of the design has stabilized enough
  to be recorded as a consolidated result, normally when discussion moves to
  another part or the complete design is ready for implementation. Individual
  messages, approvals, corrections, and wording changes are not milestones.
- Keep unresolved decisions explicit.
- `imp` is the only implementation command in Design mode.
- Design mode remains active until the user approves the reviewed implementation
  with `ver` or sends `exit`. An instruction to stop or switch work does
  not itself exit Design mode.

## Implementation and review

1. On `imp`, finalize the design document, set its status to
   `Ready for implementation`, and commit it before implementation
   begins.
2. Implement and validate the design.
3. Add an implementation summary to the design document and set its status to
   `Pending review`.
4. Commit the implementation together with the updated design
   document.
5. Report the result in chat and request user review.

Review may remain pending indefinitely. Do not impose a deadline, restriction,
or automatic cleanup.

If the result is wrong or incomplete, further requested corrections do not
require another `imp`. Do not choose a correction workflow automatically.

When the user enters `ver` after reviewing the implementation, treat it as
implementation approval. Before deleting the individual design document,
review it against the implemented result and promote every still-useful
decision, contract, explanation, example, limitation, and validation finding
to its canonical current documentation, then delete the individual design
document, commit the promotion and deletion, and exit Design mode.

`exit` leaves the individual design document intact.
