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

An explicit `mapping_ids` diagnostic display mode consumes the importer's
adjacent rebuild inventory and replaces every candidate with its complete
permanent `T#` identifier before placement. Sequence fragments use `.1`, `.2`,
and so on. IDs are never shortened by dropping the `T` prefix. It exists only
for verified worker builds used to identify visible source rows; normal builds
continue consuming the accepted `mappings.tsv` donor/override text. The
diagnostic mode never rewrites either table or the active profile.

An explicit `replacement` worker mode consumes only enabled rows from adjacent
`replacement.tsv` and applies ordinary translation placement without importing
accepted `mappings.tsv`. It skips the accepted table's fixed-coverage game-title
policy because the replacement is deliberately partial while passes accumulate.
Profile identity still applies the disc and memory-card identity independently.
Normal and mapping-ID builds remain unchanged.

The importer supplies replacement message families only after proving complete
`<br>`-part coverage. When a family member overflows, the patcher materializes
the complete parent template once and redirects the validated parent/message
pointer rather than linking an isolated line beside unrelated payload data.

## Invokes

- `binary_patcher` for concrete guarded inline and resolved-pointer writes.

## Uses infrastructure

- `payload_builder` for contributed code/data fragments. It is mandatory build
  infrastructure, not a downstream module invocation.
