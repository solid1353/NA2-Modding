# Narutimate Accel v2.28

This builder creates `Narutimate Accel v2.28.iso` from supported clean copies
of *Naruto Shippuuden: Narutimate Accel 2* and *Naruto Shippuden: Ultimate
Ninja 5*.

## Use it

1. Extract all five release files into one directory.
2. Put one supported clean NA2 ISO and one supported clean Ultimate Ninja 5 ISO
   in that directory. Their filenames do not matter.
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

- Write the `base` row's `substitution_cost` as a literal value such as `2.5`.
- In a character row, write an unsigned value such as `3` for a literal cost,
  `+0.5` to add to the base cost, or `-0.5` to subtract from it.
- Leave a value empty to inherit the packaged value and its literal-or-delta
  mode. If neither the character nor `base` supplies a value, the game keeps
  its native behavior.
- `0` is literal zero; `+0.0` is a zero delta; an empty cell inherits.
- A form row applies when that form is selected at match start. Transforming
  during a match keeps the originally selected base character's row.

For example, these rows make the base cost `2.5`, add `2.0` for Naruto, and use
literal cost `3` for Sakura:

```tsv
id	base_id	character	tier	substitution_cost	hp	damage_multiplier	health_recovery_multiplier	chakra_recovery_multiplier
base		Base		2.5
57		Naruto Uzumaki	S	+2.0
58		Sakura Haruno	A	3
```

Save the file as UTF-8 TSV and run the builder normally. The runtime implements
`substitution_cost`; the other columns are reserved for later per-character
battle hooks and may be left empty.

## `catalog.modcat`

`catalog.modcat` is a readable reference for the available configuration. It
shows descriptions, setting types, ranges, object shapes, and unions. It has no
patch addresses or other implementation details.

The EXE contains and uses its own complete catalog. It never reads the external
`catalog.modcat`, so editing or deleting that reference file cannot change how
the builder validates or patches the game.
