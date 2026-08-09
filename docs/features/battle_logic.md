# Battle logic

The `battle_logic` catalog subtree selects guarded definitions through patch
IDs. The base and release configurations enable both existing battle-behavior
nodes and set `substitution_cost` to `1`.

## Substitution cost

`battle_logic.substitution_cost` is a `setting<int & 1..15>` rather than a set
of predefined variants. `false` disables its patch; an integer from `1` through
`15` supplies the requested cost.

Its referenced `replace` edit targets the boot ELF at file offset `0x1299BC`
and guards the complete little-endian `lui v0, 0x3F80` instruction bytes
`80 3F 02 3C`. The `mips_lui_float32` adapter encodes the validated integer as
IEEE-754 float32, requires an exact representation whose low 16 bits are zero,
preserves the instruction's opcode and destination register, and replaces its
high immediate. Every accepted integer has an exact single-`lui` encoding; for
example, `3` produces `40 40 02 3C`.

The adapter and guarded selection path are covered by permanent tests. The
historical cost `3` form is runtime-proven; the other non-default configurable
costs have not each been runtime-tested.
