# Runtime injector module

This reusable engine validates feature-owned resident code/data fragments,
their internal symbolic relocations, and guarded symbolic game-file hooks.
It contributes fragments to the shared `payload_builder`; after the builder
assigns final addresses, the composer resolves each hook template and this
engine compiles the concrete writes into an in-memory `binary_patcher`
package. A feature never chooses an offset inside `PRG/228.BIN` or owns its
loader, memory reservation, or final runtime address.

Canonical production inputs are the shared
`na228_builder/features/targets.tsv` registry and the owning catalog nodes'
`hooks` and `payload` objects, plus referenced repository sources and assets.
There is no feature-local runtime-injector directory.

A `payload` declaration is either a C source or a static code/data/rodata
fragment. C sources contain their path, namespace, private imports, emitted
fragment aliases, and optional ABI metadata. Static fragments contain their
bytes or guarded blob, alignment, initialization marker, and private
relocations. Shared declarations are stored only at the nearest common
selectable owner of their consumers.

Configuration selection controls hooks. A parent payload declaration
contributes only when at least one selected descendant consumes that owner.
When every hook in a feature is disabled, the internal runtime-injector
invocation contributes no payload or target writes.

## Invokes

- `binary_patcher` for the resolved concrete guarded writes.

## Uses infrastructure

- `payload_builder` for deterministic fragment placement, relocation, and the
  one shared resident payload.
