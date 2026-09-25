# Catalog format

`.modcat` defines the selectable feature tree and its patch references. The
builder parses this JSON-like syntax directly. Development catalogs have a
`features` root; every level accepts the same node forms.

## Nodes and configuration values

A container groups nested nodes. A bare `setting` is an on/off switch;
`setting<T>` accepts a value of type `T` and passes it to its patch adapter.

```text
{
  features: {
    example: {
      enabled: setting { patch: "example.enabled", },
      speed: setting<decimal & 0.5..2 & step 0.25> {
        patch: "example.speed",
      },
    },
  },
}
```

Matching development config:

```json
{"features": {"example": {"enabled": true, "speed": 1.25}}}
```

A container may own a shared patch, applied once with its selected object
value. A setting may omit `patch` when it selects no change or a patch-owning
ancestor consumes its value. Optional `description` text explains behavior
not already clear from the name and type; it does not inherit or fall back.

`false` disables a node and its descendants unless the setting's declared type
accepts `false`. In that case it is configured data and the setting stays
selected. A disabled node passes no value to its patch adapter.
`true` enables a bare setting but never expands a container. For `setting<T>`
where `T` accepts an empty object, `true` is shorthand for `{}` and is normalized
before reaching adapters or fragment encoders. Required object fields prevent
that shorthand.

## Types and syntax

| Form | Meaning |
| --- | --- |
| `bool`, `int`, `decimal`, `string` | Primitive types |
| `"name"`, `5`, `true` | String, number, or Boolean literal |
| `{ amount: int, label?: string }` | Closed object; `?` marks an optional field |
| `"off" \| int & 1..15` | Disjoint alternatives |
| `int & 1..15` | Inclusive range |
| `decimal & >0 & <=10` | Comparisons: `>`, `>=`, `<`, `<=` |
| `decimal & step 0.25` | Exact multiples of a positive step, anchored at zero |
| `( ... )` | Explicit grouping |

`&` binds more tightly than `|`. `int` accepts finite mathematically integral
JSON numbers, including `5.0`; `decimal` accepts all finite JSON numbers.
Every type union and node union must be pairwise disjoint: `int | decimal` is
invalid, and declaration order never resolves overlap. Object values reject
undeclared fields and require every non-optional field.

The catalog supports quoted or identifier keys, JSON strings and numbers,
`//` comments, and trailing commas. Keys must be meaningful `snake_case` names.
Empty structural containers and empty object type declarations are invalid.
Only the documented grammar is supported; there is no `number` type, `null`,
imports, variables, calculations, functions, or executable expressions. Extend
it only for an actual catalog requirement.

## Unions and object intersections

Node unions select one complete branch. Branches may be scalar settings or
named object alternatives; there is no separate choice construct or
option-to-patch map. Different implementations use complete setting branches:

```text
layout:
  setting<"compact"> { patch: "example.compact", }
  | setting<"expanded"> { patch: "example.expanded", },
```

Structural objects combine with `&` to share fields across alternatives:

```text
startup:
  { faster_loading: setting {}, }
  & ({ title_screen: setting {}, } | { auto_loading: setting {}, }),
```

This accepts an object such as `{"faster_loading": true, "auto_loading": true}`.
Each operand must resolve to a structural object or union of structural
objects. Their field names must be disjoint, and no two operands may declare
`description`. Named object alternatives use their complete object shape as
the config value; they do not add another selector field.

## Configuration and overrides

Standalone development configs contain the complete `features` object.
Repository variants contain only `overrides`, partially mirroring
`base.features`. JSONC accepts line comments, block comments, and trailing
commas. Document each non-Boolean scalar setting's allowed values and
constraints in an inline comment synchronized with the catalog. Keep trailing
`//` comments aligned; realign them when an edit changes the required width.

Overrides merge recursively through structural containers and unconditional
intersection fields. A setting or node union is replaced as a whole at any
depth. An object-valued setting therefore needs a complete valid replacement;
its fields do not merge independently.

For `shared & (branch_a | branch_b)`, shared-only overrides retain the selected
branch. Supplying a branch-specific field replaces that branch's complete
portion. Shared-only overrides cannot re-enable a disabled intersection
because no branch is selected. An override of `false` disables its node;
partially re-enabling a container leaves unspecified children disabled.

## Release configuration

The catalog defines settings independently of their release presentation.
`na228_builder/release_manifest.json` maps public configuration names and groups
to catalog paths. The generated public reference retains the mapped settings'
types, descriptions, constraints, and unions, without patch bindings.
The release loader validates public values against that reference's embedded
schema, maps edits back to internal paths, and validates the complete config.

The [release process](../runbooks/release.md#configuration-layout) owns the
mapping syntax, exported layout, and packaged defaults.

## Patch mappings and validation

Each dotted `patch` ID must resolve in
`patches/<first-segment>/<first-segment>.json` and match that file's first
segment. A patch may be referenced directly only once; shared patches belong
on the lowest common container. Internal patches may instead be reached through
`includes`. Unreachable definitions are rejected.

| Definition field | Purpose |
| --- | --- |
| `edit` or `edits` | One guarded edit or a nonempty semantic group of primitive/fixed-stride table edits; mutually exclusive |
| `hooks`, `payload` | Runtime injection |
| `string_patch` | Semantic string transformation |
| `modules` | Additional internal executors |
| `includes` | Nonempty list of reusable patch IDs |
| `startup_fast_forward_frames` | Additive or override launch-frame metadata |

A definition needs at least one implementation or metadata field. Optional
patch descriptions explain the unified behavior; component descriptions add
only distinct information. Module mappings and launch metadata belong here,
not in public catalog nodes.

Includes expand recursively and apply once per selected configuration. Missing
references, cycles, and duplicate IDs within one list are invalid. Included
patches receive no configured value; they implement static behavior or read
the complete selection through their adapter. They participate in module
selection, resource hashing, and release assets.

A declared module's input directory follows its patch ID: `localization.strings`
resolves to `patches/localization/strings/`, without a separate feature-directory
mapping. Every referenced module, target, adapter, asset, source, runtime object,
and operation must pass its owning component's validation.

[Binary patcher](../../na228_builder/infrastructure/modules/binary_patcher/README.md)
owns edit grouping, table replacement, adapters, destinations, and guards;
[runtime injector](../../na228_builder/infrastructure/modules/runtime_injector/README.md)
owns hooks and payloads; [string patcher](../../na228_builder/infrastructure/modules/string_patcher/README.md)
owns semantic string transformations. [Localization](localization.md)
describes the language-specific composition. Examples here are illustrative;
production catalogs need definitions for every referenced patch ID.
