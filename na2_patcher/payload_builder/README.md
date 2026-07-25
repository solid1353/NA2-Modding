# Payload builder

`payload_builder` is mandatory build infrastructure, not a feature module.
Feature modules contribute named code, read-only-data, or writable-data
fragments plus symbolic references. External strings contribute read-only data;
the generic `resident_patcher` contributes feature-owned custom logic and
guarded hooks. The builder assigns deterministic aligned offsets, resolves
internal relocations, produces the one resident MWO3 `PRG/228.BIN`, and records
a complete symbol map.

`module_pipeline.py` gathers every contribution before invoking the builder, so
no individual feature consumer decides when the shared payload is complete.

No feature owns the file, its load address, its entrypoint, or the global loader
and memory-reservation integration. Modules never declare offsets inside
`228.BIN` or calculate final runtime addresses. The profile composer resolves
their symbolic game-file references after linking, and `binary_patcher` applies
the resulting concrete guarded edits. `image_assembler` receives only the
finished insertion and remains unaware of the payload's internal format.

The configured maximum end is the previously runtime-tested two-file
reservation boundary. The actual heap boundary follows the linked payload's
aligned end, so the current compact build returns unused capacity to the game
while future contributions fail before exceeding the proven envelope.
