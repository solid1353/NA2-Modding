# Font

Canonical documentation landing page for the `Font` workstream.

## Scope

This workstream owns font appearance, measurement, fitting, positioning, and
comparison with the official NUN5 reference. Confirmed reusable findings remain
in the shared knowledge base rather than being duplicated here.

## Documents

- [Architecture, implementation history, and deferred work](context.md)
- [Confirmed font knowledge and preserved evidence](../../knowledge/localization/font/README.md)

## Workstream policy

- Broad Font layout analysis is already complete. Proceed from the existing
  findings and repeat broad analysis only when new
  evidence proves them insufficient or indicates that a broad fix may be
  better than separate subtask fixes.
- When a Font change reaches a runtime regression boundary, stop before
  runtime testing and tell the user the exact screens, actions, and expected
  unchanged behavior to verify. Do not perform that regression pass for them.
- During Font live editing, never attribute unchanged visible output to
  caching. If a requested coordinate or metric change does not visibly move,
  the implementation is wrong: retain the user's current screen, trace forward
  from the proven live entry to the first incorrect value or consumer, and fix
  that path. Do not ask the user to reopen or reconstruct the same screen.
