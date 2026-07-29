# Font

Canonical documentation landing page for the `Font` workstream.

## Scope

This workstream owns font appearance, measurement, fitting, positioning, and
comparison with the official NUN5 reference. Confirmed reusable findings remain
in the shared knowledge base rather than being duplicated here.

## Documents

- [Active plan and working context](plan.md)
- [Confirmed font knowledge and preserved evidence](../../knowledge/localization/font/README.md)

## Active epics

- [Layout parity batches](epics/ss2-6-layout/README.md)

## Workstream policy

- Apply the [shared epic workflow](../EPIC_WORKFLOW.md) only to Font work that
  the user explicitly declares an epic.
- For a user-declared Font epic, broad analysis is already complete. Proceed
  from the existing findings and repeat epic-wide analysis only when new
  evidence proves them insufficient or indicates that a broad fix may be
  better than separate subtask fixes.
- When a Font change reaches a runtime regression boundary, stop before
  runtime testing and tell the user the exact screens, actions, and expected
  unchanged behavior to verify. Do not perform that regression pass for them.
  In explicitly requested Continuous epic mode, this stop is waived: record
  the pending regression review and continue to the next subtask.
