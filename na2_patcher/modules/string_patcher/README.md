# String patcher engine

This reusable engine validates feature-owned semantic string declarations and
translation imports, chooses inline or linked external placement, and compiles
all concrete file-backed edits into one in-memory binary-patcher package.
External strings are contributed as named read-only-data fragments with
symbolic pointer writes; `payload_builder` assigns their offsets and constructs
`PRG/228.BIN`, the composer resolves the pointers, and `binary_patcher` performs
guarded writes and conflict validation. The engine never owns the shared file,
loader, memory reservation, or final runtime addresses.

Localization owns no `string_patcher/` feature directory because it currently
has no local string declarations. Its importer artifact invokes this generic
consumer as a derived stage. A feature creates `string_patcher/strings.tsv` only
when it owns actual local declarations.

## Invokes

- `binary_patcher` for concrete guarded inline and resolved-pointer writes.

## Uses infrastructure

- `payload_builder` for contributed code/data fragments. It is mandatory build
  infrastructure, not a downstream module invocation.
