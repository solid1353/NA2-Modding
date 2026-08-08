# Binary edit descriptions design

This document defines how useful human-readable information is moved into
isolated binary edit definitions.

## Edit contract

- Edit definitions may contain an optional `description` field.
- Add `description` only when existing documentation contains useful
  information that canonically belongs with that specific edit.
- Use concise plain language describing the edit's useful purpose, rationale,
  or provenance.
- Preserve documented meaning faithfully. Do not invent or extrapolate.
- Omit `description` when no useful qualifying information exists.
- A present `description` must be a nonempty string.
- Descriptions do not affect patch execution.
- Preserve all executable edit values and catalog references unchanged.

## Source selection

Search
`docs/workstreams/project/binary-runtime-migration-documentation.md` and other
relevant project documentation for qualifying information.

Do not transfer content merely because it exists. Exclude:

- opaque evidence IDs, legacy identifiers, and ticket-like codes;
- repetitive context, status notes, review chatter, obsolete history, and
  unrelated evidence;
- disassembly analysis, research evidence, hypotheses, detailed derivations,
  and broader feature history;
- information that belongs in its existing documentation context rather than
  with one edit.

## Move, do not copy

Moving information into an edit description must not leave a duplicate at its
source. This rule applies to every consulted document.

- If all qualifying information from source content is transferred, delete
  that source content.
- If only part is transferred, remove only the transferred portion and
  preserve the rest.
- If nothing is transferred, leave the source content unchanged.

`binary-runtime-migration-documentation.md` is expected to lose more content
because it will eventually be retired.
