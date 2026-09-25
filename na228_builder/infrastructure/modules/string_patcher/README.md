# String patcher engine

This internal derived stage validates translation imports, chooses inline or
linked external placement, and compiles
all concrete file-backed edits into one in-memory binary-patcher package.
External strings are contributed as named read-only-data fragments with
symbolic pointer writes; `payload_builder` assigns their offsets and constructs
`PRG/228.BIN`, the composer resolves the pointers, and `binary_patcher` performs
guarded writes and conflict validation. The engine never owns the shared file,
loader, memory reservation, or final runtime addresses.

The configuration pipeline passes this engine the translation importer's
validated in-memory rows. It has no feature-owned data directory or file-backed
interface.

A sequence is placed as one complete block, inline when it fits or externally
through its validated pointer inventory. Both forms keep a NUL after every
fragment and a final empty terminator. A sequence without pointer references
must fit its source block. Structured parent families use the same complete-
message placement for callers whose mappings describe separate source slots.

Catalog-selected semantic string patches are applied after import and before
this placement decision. `replace_imported_game_title` guards the imported
title's mapping and occurrence coverage, then substitutes
`na228_builder/release_manifest.json`'s `title`. The English strings patch
selects this operation with its importer.

## Invokes

- `binary_patcher` for concrete guarded inline and resolved-pointer writes.

## Uses infrastructure

- `payload_builder` for contributed code/data fragments. It is mandatory build
  infrastructure, not a downstream module invocation.
