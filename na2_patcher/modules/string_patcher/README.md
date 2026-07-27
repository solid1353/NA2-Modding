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

The importer supplies replacement message families only after proving complete
`<br>`-part coverage. When a family member overflows, the patcher materializes
the complete parent family once and redirects the validated parent/message
pointer rather than linking an isolated line beside unrelated payload data.
Each transformed source slot remains a separate NUL-terminated fragment in
original offset order, followed by an empty terminator; only line breaks that
belong inside one source slot remain `<br>`. This preserves NA2's multi-slot
message traversal and prevents it from falling through into the next payload
fragment.

## Invokes

- `binary_patcher` for concrete guarded inline and resolved-pointer writes.

## Uses infrastructure

- `payload_builder` for contributed code/data fragments. It is mandatory build
  infrastructure, not a downstream module invocation.
