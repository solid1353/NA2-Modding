# EE runtime memory map

This directory records the unmodified game's address-space, allocator, and
runtime-lifetime constraints.

## Research coverage

- **Assigned scope:** establish native EE memory ownership relevant to runtime
  analysis and safe experimentation.
- **Exploration depth:** the resident ELF, overlays, allocator, stacks, and
  sampled vanilla runtime states were examined.
- **Confirmed coverage:** the linked documents establish the native address
  map, allocator model, overlay lifetimes, and unsafe fixed-storage regions.
- **Unresolved or untested:** result screens, active Save/Load, long transition
  stress, and complete high-memory ownership.
- **Deliberate exclusions and overlap:** NA228 payload capacity and injection
  behavior belong to [Runtime injection](../../../features/runtime_injection/implementation.md).
- **Evidence limitations:** sampled free space is not a formal maximum-use
  bound for every state.

## Safe-use constraints

- Do not use overlay slack for resident data; later overlays can overwrite it.
- Do not use allocator gaps as fixed caves; allocate through the game allocator
  and retain the returned pointer for the required lifetime.
- Do not use the high `0x01FF6000..0x02000000` tail; it is outside the allocator
  but observably active.
- Loaded executable code requires correct EE instruction and data cache
  maintenance; stable RAM alone is insufficient.

The maintained
`@scripts/research/ee_memory_map/analyze_savestates.py` tool validates allocator
links and counters, identifies overlays, and emits bounded observation tables.
Static findings use the preserved clean NA2 disassembly.
