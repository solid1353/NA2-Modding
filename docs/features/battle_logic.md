# Battle logic

The `battle_logic` catalog subtree selects guarded definitions through patch
IDs. The base and release configurations enable both existing battle-behavior
nodes and set `substitution_cost` to `1`.

## Substitution cost

`battle_logic.substitution_cost` is
`setting<decimal & 0..15 & step 0.25>` rather than a set of predefined
variants. `false` disables its patch; otherwise the setting accepts quarter-step
costs from `0` through `15`, inclusive.

Its referenced `replace` edit targets the boot ELF at file offset `0x1299BC`
and guards the complete little-endian `lui v0, 0x3F80` instruction bytes
`80 3F 02 3C`. The `mips_lui_float32` adapter encodes the validated integer as
IEEE-754 float32, requires an exact representation whose low 16 bits are zero,
preserves the instruction's opcode and destination register, and replaces its
high immediate. Every accepted quarter-step value has an exact single-`lui`
encoding; for example, `1.25` produces `A0 3F 02 3C` and `3` produces
`40 40 02 3C`.

The adapter and guarded selection path are covered by unit tests. The
historical cost `3` form is runtime-proven; the other configurable costs,
including zero and fractional values, have not each been runtime-tested.
