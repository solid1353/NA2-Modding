# Catalog format

The builder's selectable feature contract is authored in `.modcat`, a custom
declarative format with JSON-like objects and TypeScript-like value types. The
Python builder parses it directly; there is no compiler, generated schema, or
CUE, Go, Node, or TypeScript runtime.

Each `catalog/<feature>.modcat` file defines one direct child of the logical
`features` root. Project catalog files contain both the user-facing contract and
their `patches` mappings. Release packaging consolidates them into an inert
`catalog.modcat` reference and removes the mappings and every other
implementation detail. The packaged executable uses its embedded complete
catalog and never reads the external reference.

User selections remain JSON with two root fields: `features` contains the
complete selected tree, while `overrides` contains an optional partial overlay.
A complete synthetic configuration appears below.

## Nodes and configuration values

A plain object is a structural container. Its fields are catalog nodes and may
nest to any depth. `description` is reserved non-executable metadata: it is
optional on a container and must be nonempty when present.

A bare `setting` is the static-patch form:

```text
skip_opening: setting {
  description: "Skip the opening sequence.",
  patches: ["e__qol__startup__skip_opening__skip_opening"],
},
```

Its configuration value is `true` to select its patches or `false` to select
nothing. `true` applies only to a bare setting; it never expands a container,
selects a child, or chooses a default branch.

`setting<T>` accepts one supplied JSON value described by `T`:

```text
substitution_cost: setting<int & 1..15> {
  description: "Substitution cost setting.",
  patches: ["e__battle_logic__substitution_cost"],
},
```

The selected value is validated against `T` and passed to any adapter declared
by the referenced patch definition. A typed setting has no option-to-patches
map; alternatives with different patches are complete setting branches.

Every setting requires a nonempty `description` and a nonempty `patches` array.
Patch IDs within one setting must be unique. Descriptions do not inherit and
have no fallback behavior.

The node-level value `false` disables any setting, union, or structural
container before typed-value validation or union matching. It never reaches a
patch adapter. Disabling a container disables its entire subtree. Strings such
as `"false"`, `"enabled"`, `"disabled"`, and `""` remain ordinary data when
accepted by the declared type.

Direct boolean typed settings are forbidden: `setting<bool>`, `setting<true>`,
and `setting<false>` are invalid because they overlap the node-level controls.
Boolean data is supplied inside an object instead:

```text
boolean_parameter: setting<{
  value: bool,
}> {
  description: "Synthetic supplied-boolean setting.",
  patches: ["e__example__boolean_parameter"],
},
```

## Types

The complete approved type grammar consists of:

- `bool`, `int`, `decimal`, and `string`;
- string, number, and boolean literals;
- closed object types, with required fields by default and `?` for optional
  fields;
- pairwise-disjoint unions using `|`;
- numeric constraints using `&` with inclusive ranges (`1..15`) or comparisons
  (`>`, `>=`, `<`, and `<=`); and
- parentheses for explicit grouping.

`&` binds more tightly than `|`. `int` accepts mathematically integral finite
JSON numbers, including `5.0`. `decimal` accepts only finite non-integral JSON
numbers. There is no `number` type. Object types are closed: undeclared fields
are invalid, and every non-optional field is required.

The source syntax also supports quoted or identifier keys, JSON strings and
numbers, `//` line comments, and trailing commas. Catalog keys and feature
filenames must be meaningful `snake_case` identifiers. Empty objects and empty
object types are invalid.

`null`, imports, variables, functions, calculations, executable expressions,
and every other unlisted construct are unsupported. The grammar is extended
only for an actual catalog requirement.

## Unions

Catalog-node expressions compose with `|`. There is no separate `choice`
construct. Named alternatives are closed-object branches:

```text
value_or_named_setting:
  setting<int> {
    description: "Synthetic direct integer setting.",
    patches: ["e__example__direct_integer"],
  }
  |
  {
    fixed_cost: setting<int & 1..15> {
      description: "Synthetic fixed-cost setting.",
      patches: ["e__example__fixed_cost"],
    },
  }
  |
  {
    ratio_cost: setting<{
      numerator: int & >0,
      denominator: int & >0,
    }> {
      description: "Synthetic ratio-cost setting.",
      patches: ["e__example__ratio_cost"],
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
    patches: ["e__example__layout__compact"],
  }
  |
  setting<"expanded"> {
    description: "Use the expanded layout.",
    patches: ["e__example__layout__expanded"],
  },
```

If the synthetic nodes above belong to `example.modcat` alongside this simple
bare setting:

```text
simple_patch: setting {
  description: "Synthetic static patch.",
  patches: ["e__example__simple_patch"],
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
  },
  "overrides": {}
}
```

Every type union and catalog-node union must be pairwise disjoint. Catalog
loading rejects overlapping branches; declaration order never supplies
precedence. Scalar setting branches and named object branches use the same
internal selection model.

## Release projection

The consolidated release `catalog.modcat` retains the complete public feature
hierarchy, descriptions, node forms, value types, constraints, and unions. It
contains no configured selections or `overrides` and is not a configuration.
It also removes patch IDs, adapters, targets, offsets, module ownership, source
paths, assets, proof metadata, build data, and every other implementation
detail.

The executable embeds the parser, validator, complete project catalog, patch
definitions, adapters, assets, and runtime objects. It validates `config.json`
against that embedded data. Editing, damaging, or deleting the external
catalog reference cannot change validation or patching behavior.

## Overrides

The base configuration contains the complete `features` object. An `overrides`
object may partially mirror that hierarchy. Overrides merge recursively only
through plain structural containers. When an override reaches a setting or a
catalog-node union, it replaces that node's complete configured value at any
depth. An object-valued setting therefore requires a complete valid object; its
fields never merge independently with the previous value.

An override value of `false` disables the addressed node. When a disabled
container is partially re-enabled by a later object override, its unspecified
children remain disabled.

## Patch mappings and validation

Every setting has one `patches` array. Edit IDs use the `e__` prefix and must
resolve to exactly one guarded definition in
`catalog/implementation/edits.json`. Injection IDs use `i__` and must resolve
to exactly one unit in `catalog/implementation/injections.json`. Every other
prefix is invalid.

Multiple setting branches may share a patch ID. Every edit and injection must
be referenced by at least one catalog branch; orphan definitions are rejected.
Every target, adapter, asset, source, runtime object, and operation reachable
through a referenced definition must also pass its owning component's normal
validation.

A parameterized edit retains the ordinary `replace` operation, target, offset,
and destination guard. It declares an adapter instead of `replacement_hex`;
the adapter turns the validated setting value into concrete replacement bytes
before normal guarded composition. Adapters are owned by
`modules/binary_patcher/adapters.py`; there is no separate adapter operation.

The examples in this document are illustrative authoring fragments. A real
catalog must provide implementation definitions for every shown patch ID.
