# Runtime injector module

This runtime-injector pipeline validates feature-owned resident code/data fragments,
their internal symbolic relocations, and guarded symbolic game-file hooks.
It contributes fragments to the shared `payload_builder`; after the builder
assigns final addresses, the composer resolves each hook template and this
engine compiles the concrete writes into an in-memory `binary_patcher`
package. A feature never chooses an offset inside `PRG/228.BIN` or owns its
loader, memory reservation, or final runtime address.

Canonical production inputs are the shared
`@builder/catalog/targets.tsv` registry, injection units from
`@builder/catalog/injections.json`, and referenced
repository sources and assets.
Catalog settings select injection units through `i__` patch IDs.
There is no separate runtime-injector data directory or standalone TSV package
format; the catalog loader is the only declaration parser.

Each root injection identity begins with `i__`, followed by its catalog
ownership path and semantic unit identity. The root map and
unordered nested maps are serialized alphabetically. Hooks and named payload
fragments use concise local semantic identities rather than repeating their
owner's catalog prefix. Optional nonempty injection and hook descriptions hold
only definition-local purpose or provenance and never affect execution.

A `payload` declaration is either a C source, an assembly source, or a static
data/rodata fragment. C and assembly sources contain their path, namespace,
private imports, emitted fragment aliases, and optional ABI metadata. C uses
`kind: "c"` with an exact `.c` suffix; preprocessed EE assembly uses
`kind: "asm"` with an exact `.S` suffix. Static fragments contain their
bytes or guarded blob, alignment, initialization marker, and private
relocations. Shared declarations are stored once in an injection unit
referenced by every consuming catalog leaf.

Hooks and payload fragments are not one-to-one: several hooks may target one
fragment, and one hook may depend on multiple fragments. Their guards,
relocations, and symbolic references remain together in the owning injection
unit.

Configuration selection controls hooks. A shared payload declaration
contributes only when at least one selected leaf references its injection unit.
When every hook in a feature is disabled, the internal runtime-injector
invocation contributes no payload or target writes.

## Invokes

- `binary_patcher` for the resolved concrete guarded writes.

## Uses infrastructure

- `payload_builder` for deterministic fragment placement, relocation, and the
  one shared resident payload.
