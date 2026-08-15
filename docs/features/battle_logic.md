# Battle logic

The `battle_logic` catalog subtree selects guarded definitions through patch
IDs. Its character-override node loads layered TSV data and emits one resident
table shared by current and future per-character battle hooks.

## Substitution cost

`configurations/overrides/base.character_overrides.tsv` supplies the shared
base and character rows. The selected profile's matching TSV in that directory
layers nonempty cells over it. Character IDs and names are validated against
`resources/character_data.tsv`. `base_id` records form relationships as
human-readable configuration metadata. `tier` records the balancing tier and
is serialized as fixed-width table metadata. Empty cells inherit, while zero
remains an explicit value.

The `base` row's `substitution_cost` is a literal value. In a character row, an
unsigned value such as `3` is also literal, while an explicitly signed value
such as `+0.5` or `-0.5` is a delta from the resolved base cost. Profile layers
inherit both the number and its literal-or-delta mode when the cell is empty.
Other numeric fields remain nonnegative literal float32 values.

The builder serializes four-byte tier labels, presence and delta flags, and
float32 values into a dense ID-indexed resident table. The
substitution hook at ELF offset `0x1299C0` maps the incoming fighter to its
player slot and reads that slot's match-start character ID. A directly selected
form therefore uses its form row, while a base character transformed during
the match keeps its base row. The clean instruction at `0x1299BC` is no longer
edited. The current TSV selects base cost `2.5` and tier deltas from D `+0.0`
through S+++ `+3.5` in `0.5` steps.

`hp`, damage, and recovery columns are present for later hooks; only
`substitution_cost` currently has a runtime consumer.
