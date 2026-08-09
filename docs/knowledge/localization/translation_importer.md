# Translation importer knowledge

This document owns durable evidence and negative results behind the current
translation-importer contract. The current schema, inputs, output, and failure
behavior remain in the [feature document](../../features/localization/translation_importer.md).

## Mapping admission and evidence

Executable mappings are admitted only when their clean NA2 source, official
NUN5 donor, and display ownership are established. `display_context` identifies
the concrete screen and field. `display_basis` distinguishes directly seen
rows, hidden members inferred from a proven shared table, and character-family
rows established through matching structures.

An evidence-scoped rebuild removed unvisited alternate-mode, inventory,
generic-choice, and unmatched voice-title rows instead of treating historical
coverage as proof. Clean Japanese bytes remain authoritative when no verified
official source or display location exists.

## Structural mapping families

Character Command Chart names are selected through 74 matching executable
record arrays. Each record is `0x54` bytes and stores its displayed-name pointer
at `+0x08`; a row is mapped only when the corresponding NA2 and NUN5 record
indices both identify nonblank text.

Ultimate and character-specific Jutsu names use a separate `0x14`-byte record.
Its first word is the localized-name pointer and the remaining four metadata
words identify homologous records across NA2 and NUN5. Matching those metadata
words is the evidence boundary; string order alone is insufficient. When a
record-selected NUN5 name contains decorative color tags but a separate plain
official copy exists, the plain copy is used for a plain NA2 slot.

## Packed message blocks

Some dialogs contain consecutive NUL-terminated fragments inside one fixed
region. Treating each fragment as an independent slot zero-filled the remainder
of the Japanese fragment and could insert an early empty string that hid later
parts. `sequence` mappings therefore write the selected official parts
consecutively, terminate each part, add one final NUL, and zero-fill only the
unused tail of the verified whole block. They never resize the target or write
outside that block.

## Placement and semantic guards

- A fitting slot is written inline.
- An overflowing slot is linked externally only when that same mapping owns
  validated pointer references; otherwise compilation fails.
- Sequence mappings must fit their declared block.
- Placeholder donor text such as `unknown`, `placeholder`, or `dummy` cannot
  overwrite identifier-like NA2 data.
- Source, donor, references, transforms, override, and prefix stay on the same
  stable mapping row. Generated logs derive their reasons from its stable ID.
- The official donor is executable by default. A replacement is present only
  for an intentional user-owned override.
- The project-title policy is hash- and coverage-pinned and replaces only its
  declared official donor token with `Narutimate Accel v2.28`.

## Content and layout boundary

Canonical mappings preserve official wording. They do not insert authored line
breaks or shorten correct text merely to compensate for a renderer defect.
Collection Movie line breaks added to four exact NUN5 titles were rejected and
removed; wrapping belongs to the Font caller path. Likewise, the correct
`Flying Thunder God Jutsu` mapping remains unchanged even if a particular
Collection panel needs wrapping.

Generic modal labels remain exact official `No` and `Yes`. A global uppercase
transform was rejected because those slots are shared and did not own the
startup-specific presentation that motivated the experiment. Graphical labels,
controller prompts, emulator chrome, placement, and atlas behavior remain
outside the translation importer.

## Durable resolved mappings

- Collection's confirmed selector label uses official `Opponent`; its paired
  screen established that the missing mapping, not layout, caused the Japanese
  label.
- The Mode Select return confirmation uses official
  `Return to Title Screen?`; it is distinct from Save/Load and Character Select
  prompts with different sources and capitalization.
- Temari's Collection voice title maps to official `Silent Confidence`, proven
  by the matching NUN5 screen and `TEXTENG.BIN` source.
- Plain Kankuro maps to `Kankuro`, not `Kankuro (Classic)`; structurally matched
  character families must not collapse distinct variants.
- Memory-card notices use packed sequence mappings so every official fragment
  remains reachable without changing file size.

Version-by-version counts, generated hashes, old runtime checklists, and
superseded issue logs remain in Git history rather than canonical
documentation.
