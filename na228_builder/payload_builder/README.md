# Payload builder

`payload_builder` is mandatory build infrastructure, not a feature module.
Feature modules contribute named code, read-only-data, or writable-data
fragments plus symbolic references. External strings contribute read-only data;
the generic `runtime_injector` contributes feature-owned custom logic and
guarded hooks. The builder assigns deterministic aligned offsets, resolves
internal relocations, produces the one resident MWO3 `PRG/228.BIN`, and records
a complete symbol map.

`module_pipeline.py` gathers every contribution before invoking the builder, so
no individual feature consumer decides when the shared payload is complete.

`ee_c_fragments.py` is the shared EE source frontend used by
`runtime_injector`: it compiles ordinary PS2 EE C and preprocessed `.S`
assembly with the configured EE toolchain and
converts supported ELF sections and relocations directly into this builder's
address-independent fragment model. Object files are temporary. The builder
then lays out those fragments together with static and external-string
fragments and emits only the final shared `228.BIN`. `mips.py` provides the
small deterministic instruction/relocation encoder used only for unavoidable
native ABI shims and guarded hook templates. Both are maintained build inputs
rather than research artifacts.

Payload-fragment numeric `order` values are retained and validated while named
JSON maps are serialized canonically. Final placement remains deterministic by
fragment kind, owner, and semantic symbol, independent of source-map order.

No feature owns the file, its load address, its entrypoint, or the global loader
and memory-reservation integration. Modules never declare offsets inside
`228.BIN` or calculate final runtime addresses. The configuration composer resolves
their symbolic game-file references after linking, and `binary_patcher` applies
the resulting concrete guarded edits. `image_assembler` receives only the
finished insertion and remains unaware of the payload's internal format.

The configured `reservation_end` is the previously runtime-tested two-file
boundary `0x00940100`; `maximum_end` remains its safety ceiling. Every linked
payload serializes that complete fixed envelope and records the reservation end
in its MWO3 memory-end fields. Its actual aligned `used_end` remains available
in build metadata. Unused capacity is zero-filled, so payload growth within the
envelope changes neither loader workload nor the game heap boundary.
Contributions fail before crossing the reservation.

The shifted E2E Test build exposes a test-only aligned `payload_shift` input.
It is fingerprinted by preflight and moves every real contributed fragment
before symbolic relocations are resolved. Explicit global `na228 e2e all -s`
qualification uses the configured 32-byte shift and requires every non-ignored
normal/shifted PNG to remain byte-identical.

The configuration also declares the development-only injection reservation
`0x008F0000-0x008F3D00` immediately below the fixed payload load base. It is
inside the Current-only gap excluded from overlays and from the relocated game
heap by the payload integration. It is never emitted into `228.BIN`, never used
by release composition, and must be targeted only by an exact-identity,
guard-validated development tool. The reservation gives the direct-PINE
injection workflow one deterministic 15,616-byte range without treating
zero-filled ELF, overlay, or heap memory as an implicit code cave.
