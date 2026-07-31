# Runtime injector module

This reusable engine validates feature-owned resident code/data fragments,
their internal symbolic relocations, and guarded symbolic game-file hooks.
It contributes fragments to the shared `payload_builder`; after the builder
assigns final addresses, the composer resolves each hook template and this
engine compiles the concrete writes into an in-memory `binary_patcher`
package. A feature never chooses an offset inside `PRG/228.BIN` or owns its
loader, memory reservation, or final runtime address.

Canonical inputs are `targets.tsv`, `groups.tsv`, `patches.tsv`,
`fragments.tsv`, `c_sources.tsv`, `c_imports.tsv`, `c_fragments.tsv`,
`relocations.tsv`, and `edits.tsv`, plus only the source files and blobs
referenced by those tables. Static fragments may contain their bytes inline or
select a guarded range from a referenced blob. Canonical project C sources live
under root `src/`; feature `c_sources.tsv` rows reference those repository paths,
and their contents remain covered by the owning feature hash. Declared C
sources are compiled with the pinned EE toolchain during normal package loading; the
generic object extractor converts their sections and relocations directly into
the same address-independent fragment model. Compiler objects and aggregate
payload blobs are temporary and are not canonical feature inputs.

Fragment IDs are exported payload symbols. `c_fragments.tsv` aliases extracted
object-section symbols to those stable IDs and assigns their global order.
Relocations may target any exported symbol in the complete linked payload.
Symbolic edit templates preserve surrounding instructions such as branch or
jump delay slots while replacing only the declared relocation field.

Runtime-injection patches use the same hierarchical `enabled` selection contract as
ordinary binary patches. A disabled group masks every member patch without
changing the member switches. Disabled rows, their symbolic edits, and all
fragment/blob declarations remain validated and hash-covered, but they
contribute no hooks. When every runtime-injection patch in a feature is effectively
disabled, that feature contributes no resident fragments and composes as a
no-op `runtime_injector` module without deleting its retained implementation.

## Invokes

- `binary_patcher` for the resolved concrete guarded writes.

## Uses infrastructure

- `payload_builder` for deterministic fragment placement, relocation, and the
  one shared resident payload.
