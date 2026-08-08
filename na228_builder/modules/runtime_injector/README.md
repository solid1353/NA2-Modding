# Runtime injector module

This reusable engine validates feature-owned resident code/data fragments,
their internal symbolic relocations, and guarded symbolic game-file hooks.
It contributes fragments to the shared `payload_builder`; after the builder
assigns final addresses, the composer resolves each hook template and this
engine compiles the concrete writes into an in-memory `binary_patcher`
package. A feature never chooses an offset inside `PRG/228.BIN` or owns its
loader, memory reservation, or final runtime address.

Canonical production inputs are the shared
`na228_builder/catalog/implementation/targets.tsv` registry, injection units
from `na228_builder/catalog/implementation/injections.json`, and referenced
repository sources and assets.
Catalog leaves select injection units by ID.
There is no separate runtime-injector data directory.

A `payload` declaration is either a C source or a static code/data/rodata
fragment. C sources contain their path, namespace, private imports, emitted
fragment aliases, and optional ABI metadata. Static fragments contain their
bytes or guarded blob, alignment, initialization marker, and private
relocations. Shared declarations are stored once in an injection unit
referenced by every consuming catalog leaf.

Configuration selection controls hooks. A shared payload declaration
contributes only when at least one selected leaf references its injection unit.
When every hook in a feature is disabled, the internal runtime-injector
invocation contributes no payload or target writes.

## Invokes

- `binary_patcher` for the resolved concrete guarded writes.

## Uses infrastructure

- `payload_builder` for deterministic fragment placement, relocation, and the
  one shared resident payload.
