# Catalog format

The builder's selectable feature contract is authored in `.modcat`, a custom
declarative format with JSON-like objects and TypeScript-like value types. The
Python builder parses it directly; there is no compiler, generated schema, or
CUE, Go, Node, or TypeScript runtime.

`catalog.modcat` defines the logical `features` root and all of its direct
feature children. The project catalog contains the user-facing contract and one
singular `patch` reference wherever implementation is selected. Release
packaging writes an inert `catalog.modcat` reference with patch references and
every other implementation detail removed. The packaged executable uses its
embedded complete catalog and never reads the external reference.

A complete standalone or released `.jsonc` configuration has one root field:
`features` contains the complete selected tree. Repository build variants use
an internal `overrides` root to customize `base.features`. Line comments,
block comments, and trailing commas are accepted. A complete synthetic
configuration appears below.

## Nodes and configuration values

A plain object is a structural container. Its fields are catalog nodes and may
nest to any depth. A container may own one patch shared by its nested tree. The
patch receives the selected object value and is applied once whenever that
container is selected.

A bare `setting` is the static-patch form:

```text
replace_imported_game_title: setting {
  patch: "general.replace_imported_game_title",
},
```

Its configuration value is `true` to select its patch or `false` to select
nothing. `true` never expands a structural container or recursively selects its
children.

`setting<T>` accepts one supplied JSON value described by `T`:

```text
camera_distance: setting<decimal & 0.5..2 & step 0.25> {
  description: "Camera distance setting.",
  patch: "example.camera_distance",
},
```

The selected value is validated against `T` and passed to any adapter declared
by the referenced patch definition. A typed setting has no option-to-patch map;
alternatives with different patches are complete setting branches.
When `T` accepts an empty object, `true` is shorthand for `{}` and the selected
value exposed to adapters and resident-fragment encoders is normalized to `{}`.
Typed settings with any required object field reject that shorthand.

Structural blocks and settings may omit `description`; include one only when it
adds behavior or semantics that the name and type do not already make clear. A
setting may also omit `patch` when a patch-owning structural ancestor consumes
its value as part of the nested tree. Each patch ID appears only once in the
entire catalog; a patch shared by nested settings belongs on their lowest common
structural ancestor. Descriptions do not inherit and have no fallback behavior.
Module mappings and launch metadata belong to patch definitions and are omitted
from the public release catalog.

The node-level value `false` disables a node only when its declared type does
not accept `false`. It never reaches a patch adapter in that case. Disabling a
container disables its entire subtree. A boolean typed setting treats `false`
as its configured data and remains selected:

```text
boolean_parameter: setting<bool> {
  description: "Synthetic supplied-boolean setting.",
  patch: "example.boolean_parameter",
},
```

## Types

The complete approved type grammar consists of:

- `bool`, `int`, `decimal`, and `string`;
- string, number, and boolean literals;
- closed object types, with required fields by default and `?` for optional
  fields;
- pairwise-disjoint unions using `|`;
- numeric constraints using `&` with inclusive ranges (`1..15`), comparisons
  (`>`, `>=`, `<`, and `<=`), or a positive zero-anchored multiple constraint
  (`step 0.25`); and
- parentheses for explicit grouping.

`&` binds more tightly than `|`. `int` accepts mathematically integral finite
JSON numbers, including `5.0`. `decimal` accepts every finite JSON number,
including integers, so `int` is its narrower subset. A union containing
overlapping `int` and `decimal` branches is invalid. There is no `number` type.
Object types are closed: undeclared fields are invalid, and every non-optional
field is required.

`step N` accepts exact multiples of the positive number `N`, anchored at zero.
For example, `decimal & 0..15 & step 0.25` accepts `0`, `1`, `1.25`, and `15`,
but rejects `0.1`, `1.1`, and values outside the inclusive range.

The source syntax also supports quoted or identifier keys, JSON strings and
numbers, `//` line comments, and trailing commas. Catalog keys and feature
filenames must be meaningful `snake_case` identifiers. Empty objects and empty
object types are invalid.

`null`, imports, variables, functions, calculations, executable expressions,
and every other unlisted construct are unsupported. The grammar is extended
only for an actual catalog requirement.

## Unions and object intersections

Catalog-node expressions compose with `|`. There is no separate `choice`
construct. Named alternatives are closed-object branches:

```text
value_or_named_setting:
  setting<int> {
    description: "Synthetic direct integer setting.",
    patch: "example.direct_integer",
  }
  |
  {
    fixed_cost: setting<int & 1..15> {
      description: "Synthetic fixed-cost setting.",
      patch: "example.fixed_cost",
    },
  }
  |
  {
    ratio_cost: setting<{
      numerator: int & >0,
      denominator: int & >0,
    }> {
      description: "Synthetic ratio-cost setting.",
      patch: "example.ratio_cost",
    },
  },
```

The corresponding configuration value can be a direct integer or exactly one
of the named object shapes:

```json
{
  "value_or_named_setting": {
    "ratio_cost": {
      "numerator": 3,
      "denominator": 2
    }
  }
}
```

Alternatives with different patches are unions of complete literal-setting
branches:

```text
layout_mode:
  setting<"compact"> {
    description: "Use the compact layout.",
    patch: "example.layout.compact",
  }
  |
  setting<"expanded"> {
    description: "Use the expanded layout.",
    patch: "example.layout.expanded",
  },
```

If the synthetic nodes above belong to `features.example` alongside this
simple bare setting:

```text
simple_patch: setting {
  description: "Synthetic static patch.",
  patch: "example.simple_patch",
},
```

their JSON configuration values look like this:

```json
{
  "features": {
    "example": {
      "simple_patch": true,
      "boolean_parameter": {
        "value": false
      },
      "value_or_named_setting": {
        "ratio_cost": {
          "numerator": 3,
          "denominator": 2
        }
      },
      "layout_mode": "compact"
    }
  }
}
```

Every type union and catalog-node union must be pairwise disjoint. Catalog
loading rejects overlapping branches; declaration order never supplies
precedence. Scalar setting branches and named object branches use the same
internal selection model.

Catalog structural objects compose with `&` when several union alternatives
share the same fields:

```text
startup:
  {
    faster_loading: setting {
      description: "Defer voice indexes until first use.",
      patch: "example.faster_loading",
    },
  }
  &
  (
    {
      title_screen: setting {
        description: "Show the title screen.",
        patch: "example.title_screen",
      },
    }
    |
    {
      auto_loading: setting {
        description: "Load saved data automatically.",
        patch: "example.auto_loading",
      },
    }
  ),
```

This is equivalent for matching to the union of both complete merged object
shapes, but keeps `faster_loading` declared once and leaves the JSON flat:

```json
{
  "startup": {
    "faster_loading": true,
    "auto_loading": true
  }
}
```

`&` binds more tightly than `|`; parentheses make the intended distribution
explicit. Every operand must resolve to a structural object or a union of
structural objects. Intersected objects must have disjoint selectable field
names, and no two operands may both declare `description`. Fields declared by
unconditional object operands remain recursive merge points in configuration
overrides. If an override supplies any field belonging to a union operand, it
must supply one complete branch of that union-specific portion.

## Release projection

The consolidated release `catalog.modcat` retains the complete public feature
hierarchy, descriptions, node forms, value types, constraints, and unions. It
contains no configured selections or `overrides` and is not a configuration.
It also removes patch IDs, adapters, targets, offsets, module ownership, source
paths, assets, proof metadata, build data, and every other implementation
detail.

The executable embeds the parser, validator, complete project catalog, patch
definitions, adapters, assets, and runtime objects. It validates `config.jsonc`
against that embedded data. Editing, damaging, or deleting the external
catalog reference cannot change validation or patching behavior.

## Overrides

The base and standalone configurations contain only the complete `features`
object. Repository development, test, and release variants contain an
`overrides` object that may partially mirror that hierarchy. Overrides merge
recursively through plain structural containers and unconditional object fields
of an intersection. When an override reaches a setting or a catalog-node union,
it replaces that node's complete configured value at any depth. An object-valued
setting therefore requires a complete valid object; its fields never merge
independently with the previous value.

For `shared & (branch_a | branch_b)`, an override may contain only shared
fields; those fields merge while the selected branch is preserved. Supplying
any branch-specific field replaces the branch-specific portion atomically and
therefore requires one complete branch. A shared-only override cannot re-enable
an intersection whose previous value is `false`, because no branch is selected.

An override value of `false` disables the addressed node. When a disabled
container is partially re-enabled by a later object override, its unspecified
children remain disabled.

## Patch mappings and validation

A setting or structural block may own one singular dotted `patch` ID. Each ID
must resolve to one definition in `patches/<first-segment>.json`, must appear
exactly once in the catalog, and must match that file's first dotted segment.
Orphan definitions are rejected.

A unified patch may contain any compatible combination of these fields:

- `edit` for one primitive guarded edit, or `edits` for one nonempty semantic
  group of primitive and fixed-stride table edits;
- `hooks` and `payload` for runtime injection;
- `string_patch` for one supported semantic string transformation;
- `modules` for additional internal executors required by the patch; and
- `startup_fast_forward_frames` for launch-frame `additive` or `override`
  metadata.

A declared module reads its canonical input directory from the patch ID under
`patches/`: `localization.strings` resolves to
`patches/localization/strings/`. Module input ownership therefore lives with
the patch instead of a separate feature-to-directory mapping.

`edit` and `edits` are mutually exclusive. At least one implementation or
metadata field is required. The optional patch `description` labels the unified
behavior; component-local descriptions are retained only when they add distinct
information. Every module, target, adapter, asset, source, runtime object, and
operation reachable through a patch must also pass its owning component's
normal validation.

A grouped edit has only an optional `description` and its `edits` map. Child
keys are stable snake-case semantic identities, not destination addresses.
Each child retains its explicit `operation` and complete operation contract.
Groups are one level only and may contain different operations or targets. The
loader expands children by semantic key before ordinary operation validation
and guarded composition. Existing single-operation roots remain primitive
definitions; grouping adds no binary operation and does not change the binary
patcher engine contract. Destination ranges belonging to different children
in one group must not overlap; an ordered same-range chain remains separate
primitive roots.

`replace_table` is a catalog authoring operation for guarded fields repeated in
one fixed-stride game table. It declares one `destination_target_id`,
`table_offset`, positive `record_stride`, `field_offset`, and nonempty
`record_patches` map. Each semantic record patch contains exactly one
`record_index` or nonempty unique `record_indices` list, plus `expected_hex`
and `replacement_hex`. All record patches in one table have the same nonzero
byte length, both hex values have equal length, and the patched field must fit
inside the stride. A record index resolves to:

```text
table_offset + record_index * record_stride + field_offset
```

Record indices must be unique across the table. The loader expands every
semantic record patch into one ordinary `replace` definition with the resolved
destination offsets before operation-manifest validation. The binary patcher
therefore receives no table-specific operation, and its exact guards, conflict
handling, logging, and output behavior remain unchanged. Tables may be dense
or sparse; `record_indices` exists only to share identical guarded bytes across
several records.

A parameterized edit retains the ordinary `replace` operation, target, offset,
and destination guard. It declares an adapter instead of `replacement_hex`;
the adapter turns the validated setting value into concrete replacement bytes
before normal guarded composition. Adapters are owned by
`modules/binary_patcher/adapters.py`; there is no separate adapter operation.

A bare setting may select a fixed-value adapter edit. For example,
`ascii_fixed` accepts readable `expected_value` and `replacement_value` fields
in the implementation definition, requires equal-length nonempty ASCII, and
encodes both values before the same guarded composition. These fixed values are
implementation details and do not appear in the release catalog reference.

`nul_padded_text` additionally accepts an `encoding` and fixed byte `length`.
It encodes each nonempty value, requires room for a terminating NUL, and pads
the remaining bytes with zeroes. This keeps fixed text slots readable without
weakening their exact byte guard.

The currently supported semantic string operation is
`replace_imported_game_title`. Its definition guards the imported text plus
the expected mapping and occurrence counts; when selected, the string patcher
replaces that text with root `settings.title` before choosing inline or linked
external placement. Disabling its catalog setting leaves the imported text
unchanged.

Every primitive binary edit declares exactly one destination form:
`destination_offset` for one integer address, or `destination_offsets` for a
unique list of at least two addresses. The loader normalizes the singular form
to its internal one-element list before operation-manifest validation. When the
same guarded operation applies at multiple known locations in one target, one
definition lists all of them. The loader expands the normalized list into
independently guarded and logged concrete edits; it never searches the target
or derives an occurrence count.

The examples in this document are illustrative authoring fragments. A real
catalog must provide implementation definitions for every shown patch ID.
