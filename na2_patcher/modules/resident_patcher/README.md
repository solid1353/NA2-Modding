# Resident patcher engine

This reusable engine validates feature-owned resident code/data fragments,
their internal symbolic relocations, and guarded symbolic game-file hooks.
It contributes fragments to the shared `payload_builder`; after the builder
assigns final addresses, the composer resolves each hook template and this
engine compiles the concrete writes into an in-memory `binary_patcher`
package. A feature never chooses an offset inside `PRG/228.BIN` or owns its
loader, memory reservation, or final runtime address.

Canonical inputs are `targets.tsv`, `groups.tsv`, `patches.tsv`,
`fragments.tsv`, `relocations.tsv`, and `edits.tsv`, plus only the blobs
referenced by fragment rows. Fragment IDs are exported payload symbols.
Relocations may target any exported symbol in the complete linked payload.
Symbolic edit templates preserve surrounding instructions such as branch or
jump delay slots while replacing only the declared relocation field.

Resident patches use the same `default_enabled` selection contract as ordinary
binary patches. Disabled rows, their symbolic edits, and all fragment/blob
declarations remain validated and hash-covered, but they contribute no hooks.
When every resident patch in a feature is disabled, that feature contributes
no resident fragments and composes as a no-op resident module without deleting
its retained implementation.

## Invokes

- `binary_patcher` for the resolved concrete guarded writes.

## Uses infrastructure

- `payload_builder` for deterministic fragment placement, relocation, and the
  one shared resident payload.
