# EE runtime memory map

This directory records the unmodified game's address-space, allocator, and
runtime-lifetime constraints.

## Research coverage

- **Assigned scope:** establish native EE memory ownership and capacity
  relevant to runtime analysis, safe experimentation, and asset-size planning.
- **Exploration depth:** the resident ELF and its startup code, the overlays
  and their loader, the allocator and its placement policy, the `malloc` layer,
  stacks, persistent pools, the CCS load pipeline's allocations, and sampled
  vanilla runtime states were examined.
- **Confirmed coverage:** the linked documents establish the native address
  map, allocator model and entry points, overlay loading and lifetimes,
  high-memory ownership at region level, persistent pools, CCS load costs, and
  unsafe fixed-storage regions.
- **Unresolved or untested:** result screens, active Save/Load, long transition
  stress, a retail per-asset heap breakdown in battle, and the byte-level use
  of the main-thread stack.
- **Deliberate exclusions and overlap:** NA228 payload capacity and injection
  behavior belong to [Runtime injection](../../../features/runtime_injection/implementation.md).
- **Evidence limitations:** sampled free space is not a formal maximum-use
  bound for every state.

## Safe-use constraints

- Do not use overlay slack for resident data; later overlays can overwrite it.
- Do not use allocator gaps as fixed caves; allocate through the game allocator
  and retain the returned pointer for the required lifetime.
- Do not use the high `0x01FF6000..0x02000000` tail; it holds the `malloc`
  remainder and the main-thread stack.
- Loaded executable code requires correct EE instruction and data cache
  maintenance; stable RAM alone is insufficient.

The maintained
`@scripts/research/ee_memory_map/analyze_savestates.py` tool validates allocator
links and counters, identifies overlays, and emits bounded observation tables.
Static findings use the preserved clean NA2 disassembly.
