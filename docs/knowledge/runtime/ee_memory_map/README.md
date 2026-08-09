# EE runtime memory map

This record maps NA2's 32 MiB Emotion Engine address space for injection-capacity
decisions. It combines static analysis of the resident ELF and MWo3 overlays
with matched PCSX2 savestates from clean NA2 and the integrated NA2.28 Current
image. The runtime evidence was captured on 2026-07-22.

The results are representative, not an absolute proof of every possible peak.
The eight matched states cover title, mode select, active Adventure, character
select, active battle, Shop, Collection, and Options. They do not include a
result screen, save/load activity, or long transition stress. Active Adventure
was the tightest sampled state, so the absent result capture does not affect the
reported worst-observed value.

Exact inputs and observations are preserved in:

- [`capture_inventory.tsv`](capture_inventory.tsv):
  savestate identities, sizes, and SHA-256 hashes;
- [`runtime_observations.tsv`](runtime_observations.tsv):
  validated allocator, overlay, and capacity readings for all 16 captures;
- `@work/EE Runtime Memory Map/savestates/2026-07-22/`: preserved task-owned
  copies of the 16 user captures used by the maintained analyzer.

The analyzer's larger JSON output and per-state region-hash report were
disposable derivations. They were pruned after the reusable observations and
conclusions above were promoted.

## Documents

- [Address space and fixed reservations](address_space.md): resident, overlay,
  development-injection, heap, and protected ranges.
- [Allocator and resident capacity](allocator_and_capacity.md): reservation
  decisions, allocator model, measured headroom, and compact-payload tradeoffs.
- [Runtime lifetimes](runtime_lifetimes.md): overlay, stack, mode-switch, and
  hot-reload ownership constraints.

## Safe-use constraints

- Fixed injection into the two Current zero regions is valid only while the
  structural boundary patch remains active and the shared layout explicitly
  owns the chosen subrange. The same addresses are heap memory in vanilla.
- Loaded executable code requires correct EE instruction/data cache maintenance;
  stable RAM alone is not sufficient.
- Do not use overlay slack for permanent data or unguarded fixed-address PNACH
  writes. `BTL.BIN` can overwrite the whole overlay reservation.
- Do not use allocator gaps as fixed caves. Allocate through the game allocator
  and keep the pointer for the required lifetime.
- Do not use the high `0xA000` tail. It is outside the allocator but observably
  active.
- Worst-observed headroom is not a formal maximum-use proof. Recheck results,
  save/load, repeated transitions, and any future feature that materially
  changes resource loading before treating the sampled margin as a release
  guarantee.

## Provenance and reproduction

Runtime analysis uses the maintained
`scripts/research/ee_memory_map/analyze_savestates.py` tool. It extracts the
32 MiB `eeMemory.bin` member from each PCSX2 savestate, validates the allocator,
identifies the overlay, and hashes fixed regions. Focused synthetic tests cover
identity parsing, allocator invariants, overlay interpretation, and region
reporting.

Static allocator, stack, and overlay analysis uses the maintained Ghidra 12.1.2
NA2 export under `@analysis/disassembly/NA2/exports/SLPS_258.37/`. The whole-
TEXTENG structure and used-string analysis is canonical in
[`external_string_payload.md`](../../localization/external_string_payload.md), updated by
commit `afe6ceb`. The compact-pool calculation was independently reproduced from
the active hash-pinned string-patcher plan and its 30 distinct generated
string locations.

No original source media was modified. No ISO or binary was rebuilt for this
investigation.
