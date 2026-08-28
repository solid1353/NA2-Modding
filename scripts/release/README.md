# Narutimate Accel v2.28

This builder creates `Narutimate Accel v2.28.iso` from supported clean copies
of *Naruto Shippuuden: Narutimate Accel 2* and *Naruto Shippuden: Ultimate
Ninja 5*.

## Use it

1. Extract all five release files into one directory.
2. Put one supported clean NA2 ISO in that directory. If
   `features.localization.ui` is enabled in `config.json`, also put one
   supported clean Ultimate Ninja 5 ISO there. English UI textures and their
   matching layout/runtime patches are selected together. Their filenames do
   not matter. A build with UI disabled needs only NA2.
3. Edit `config.json` if you want to change the selected features. Edit
   `character_overrides.tsv` if you want to change per-character battle values.
4. Double-click the EXE.

The builder identifies both source ISOs by size and SHA-256, applies the
selected changes, verifies the complete result, and then creates or replaces
`Narutimate Accel v2.28.iso`. If the build fails, it preserves an existing
output and removes only its temporary `.building` file.

## `config.json`

`features` has the same hierarchy shown in `catalog.modcat`:

- `true` enables a plain on/off setting.
- `false` disables any setting or complete branch.
- A scalar setting uses its value directly, such as `"manual"` or an integer.
- A named structured alternative is an object containing its selected named
  field. Object shapes and unions must match the catalog exactly.

`config.json` contains the complete `features` tree; edit values in that tree
directly. It has no separate overrides layer.

Invalid keys, values, ranges, or ambiguous union values are rejected before
the builder modifies an ISO. The error names the invalid configuration path,
shows the supplied value, and states the expected type or shape.

After a failure, the builder creates or replaces `builder-error.log`. The
window shows a concise error and points to that file; full technical exception
details and stack traces appear only in the log. Successful runs create no log.

## `character_overrides.tsv`

This tab-separated file controls per-character battle values. Every supported
character's `id`, `base_id`, name, and balance `tier` are already listed. Keep
the identity columns unchanged.

- `base` and `step` are metadata, not characters. Keep their `base_id`,
  `character`, and `tier` cells empty. Write `base` as a literal percentage
  from `0` through `100` and `step` as an explicitly positive, signed tier
  increment; the packaged values are `20` and `+5`.
- Leave a character cost empty to infer it from tier as
  `base + tier_index * step`: D `0`, C `1`, B `2`, A `3`, S `4`, S+ `5`,
  S++ `6`, and S+++ `7`.
- In a character row, write an unsigned value such as `30` for a literal
  `30/100` override, or write `+5`/`-5` to adjust the tier-derived cost. The
  resolved result must remain in `0..100`.
- Leave a value empty to inherit the packaged value and its literal-or-signed
  mode. `0` is literal zero; `+0.0` is a zero adjustment.
- A form row applies when that form is selected at match start. Transforming
  during a match keeps the originally selected base character's row.

For example, these rows make Naruto inherit tier S (`40/100`) and give Sakura
a literal `25/100` override:

```tsv
id	base_id	character	tier	substitution_cost	hp	damage_multiplier	health_recovery_multiplier	chakra_recovery_multiplier
base				20
step				+5
57		Naruto Uzumaki	S
58		Sakura Haruno	A	25
```

Save the file as UTF-8 TSV and run the builder normally. With the gauge feature
disabled, or with its shared runtime setting on `Chakra`, the runtime charges
`substitution_cost / 100` of NA2's 15-point chakra capacity. `Gauge` charges
the same fraction of the independent resource and places the red marker at the
exact rounded executable cost. `Free` charges neither resource. The Gauge mode
requires Character Overrides. Battle Support Disabled independently
controls whether field support and its native lower gauge remain available. The other columns
are reserved for later per-character battle hooks and may be left empty.

## `catalog.modcat`

`catalog.modcat` is a readable reference for the available configuration. It
shows descriptions, setting types, ranges, object shapes, and unions. It has no
patch addresses or other implementation details.

The EXE contains and uses its own complete catalog. It never reads the external
`catalog.modcat`, so editing or deleting that reference file cannot change how
the builder validates or patches the game.
