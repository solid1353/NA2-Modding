# Multi-option patch behavior

Status: Implemented

## Repository-wide changes

- Selectable feature definitions use a custom declarative catalog format whose
  object syntax resembles JSON and whose value types resemble TypeScript.
- The existing Python builder parses the catalog source directly. The format
  requires no compiler, generated schema, or CUE, Go, Node, or TypeScript
  runtime.
- User configurations remain JSON and retain the existing `features` and
  `overrides` hierarchy.
- `setting<T>` defines one supplied-value setting. `T` describes the accepted
  JSON value with literal unions, object types, and numeric constraints.
- Bare `setting { ... }` defines a static patch setting. Its JSON value is
  `true` to apply its patches or `false` to apply nothing, and it supplies no
  value to a patch adapter.
- A typed setting cannot have a top-level boolean domain: `setting<bool>`,
  `setting<true>`, and `setting<false>` are invalid. The `bool` type remains
  valid inside object types, allowing an object-valued setting to supply a
  boolean without conflicting with the node-level control values.
- Every bare or typed setting branch requires a nonempty, non-whitespace
  `description`. Plain grouping containers may optionally have descriptions;
  descriptions do not inherit and have no fallback behavior.
- Catalog-node expressions compose with `|`. A union may combine
  `setting<T>`, closed objects containing named settings, and other node
  expressions, allowing one JSON configuration path to accept values such as
  either a bare integer or one of several distinctly shaped setting objects.
- There is no dedicated construct for named alternatives. A union of closed
  object branches expresses them directly, and each branch remains concretely
  present so release packaging can enumerate it.
- Union branches must be pairwise disjoint. Catalog loading rejects any union
  for which a configuration value could match more than one branch; branch
  order never provides selection precedence.
- The parser normalizes each union branch into its accepted value domain and
  requires every pairwise intersection to be empty. It performs this analysis
  for the approved primitive types, literals, numeric constraints, closed
  object types, optional fields, and catalog-node expressions. If it
  cannot prove that two branches are disjoint, catalog loading fails.
- Scalar setting unions and closed-object unions are distinct authoring forms
  because they represent distinct configuration shapes. The parser normalizes
  both to the same internal selection model rather than maintaining separate
  execution pipelines.
- Patch configuration supports typed values beyond boolean flags.
- Every setting branch uses a single `patches` array of patch IDs instead of
  separate `edits` and `injections` arrays.
- Alternatives with different behavior are represented as a union of complete
  `setting<literal>` branches. Each branch owns its accepted literal,
  description, and patch array; there is no option-to-patches map.
- Bare `setting` is the single-option static-patch form. A configured
  `true` selects its patches and supplies no parameter.
- Structural parents are configured as explicit objects or `false`. `true`
  selects only a bare setting branch; it does not expand a parent or provide a
  default. There is no first-child default or order-based branch selection.
- Overrides merge recursively only through plain catalog containers. When an
  override reaches a `setting<T>` or node-union declaration, it replaces that
  node's complete configured value regardless of depth. An
  object-valued setting must therefore receive a complete valid object rather
  than inheriting omitted fields from its previous value.
- The configuration value `false` disables any catalog node. It is intercepted
  before type validation or union-branch matching, excluded from every branch's
  accepted-value domain, and never reaches a patch adapter. Disabling a
  structural parent disables its complete subtree; disabling a setting or node
  union applies no patches from that node.
- The strings `"false"`, `"enabled"`, `"disabled"`, and `""` are ordinary string
  data whenever the declared `T` accepts them. `null` is not an approved catalog
  type or configuration value.
- A parameterized setting declares its configuration-value validation in its
  `setting<T>` type expression. Disabled values skip its patches before type
  validation.
- After validation, the builder passes the configuration value to the value
  adapter declared by each referenced patch definition. The adapter produces
  the concrete patch value; normal guarded patch validation and composition
  then apply.
- A parameterized edit retains the `replace` operation, target, offset, and
  destination guard. Instead of a static `replacement_hex`, its declared
  adapter produces the concrete replacement from the validated configuration
  value. No `replace_int` or separate adapter operation is introduced.
- The currently required adapters belong to `binary_patcher` and are stored in
  `na228_builder/modules/binary_patcher/adapters.py`; no separate shared
  adapter module is introduced.
- Every edit and injection ID is renamed: edit IDs use the lowercase `e__`
  prefix, and injection IDs use the lowercase `i__` prefix.
- Catalog loading requires every `e__` patch ID to identify exactly one edit
  definition and every `i__` patch ID to identify exactly one injection
  definition. Any other patch-ID prefix is invalid.
- Multiple setting branches may reference the same patch. Every edit and
  injection definition must be referenced by at least one catalog branch;
  orphaned definitions are invalid.
- Every target, adapter, asset, source, and runtime object referenced through a
  catalog-reachable patch definition must exist and pass its owning
  component's normal validation.
- Catalog-node descriptions move from `catalog/__reference.json` into their
  corresponding feature catalog files as reserved non-executable metadata.
- Release packaging reads catalog-node descriptions directly from the feature
  catalog files.
- After every description is migrated, `catalog/__reference.json` and its
  loader, validation, fingerprint, documentation, and test handling are
  removed.

The approved catalog shape is:

```text
{
  features: {
    battle_logic: {
      substitution_cost: setting<int & 1..15> {
        description: "Substitution-bar cost.",
        patches: ["e__battle_logic__substitution_cost"],
      },
    },

    qol: {
      startup: {
        skip_opening: setting {
          description: "Skip the opening sequence.",
          patches: ["e__qol__startup__skip_opening"],
        },
        save_loading:
          setting<"manual"> {
            description: "Use the current confirmed startup save-loading flow.",
            patches: ["e__qol__startup__save_loading__manual"],
          },
      },
    },

    example: {
      boolean_parameter: setting<{
        value: bool,
      }> {
        description: "Synthetic supplied-boolean setting.",
        patches: ["e__example__boolean_parameter"],
      },

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
    },
  },
}
```

The corresponding JSON configuration is:

```json
{
  "features": {
    "battle_logic": {
      "substitution_cost": 5
    },
    "qol": {
      "startup": {
        "skip_opening": true,
        "save_loading": "manual"
      }
    },
    "example": {
      "boolean_parameter": {
        "value": false
      },
      "value_or_named_setting": {
        "ratio_cost": {
          "numerator": 3,
          "denominator": 2
        }
      }
    }
  },
  "overrides": {}
}
```

### Catalog grammar

The parser implements the complete approved minimal grammar below and rejects
every other construct. The grammar supports:

- JSON-style objects, arrays, strings, numbers, booleans, and keys;
- unquoted identifier keys and quoted keys where necessary;
- bare `setting` declarations, typed `setting<T>` declarations, plain catalog
  containers, closed objects containing named settings, and catalog-node
  unions using `|`;
- the type names `bool`, `int`, `decimal`, and `string`;
- the node-level boolean controls `true` and `false`, with direct boolean typed
  settings forbidden and `bool` permitted inside object types;
- disjoint numeric types: `int` accepts mathematically integral JSON numbers,
  including forms such as `5.0`, while `decimal` accepts only finite
  non-integral JSON numbers;
- required object fields by default and TypeScript-style `?` for optional
  fields;
- closed object types, making undeclared fields invalid;
- disjoint unions using `|`;
- compatible constraints using `&`;
- parentheses for explicit grouping;
- numeric constraints including `int & 1..15`, `int & >0`, and
  `decimal & >=0`;
- `&` binding more tightly than `|`;
- `//` line comments; and
- trailing commas.

The grammar does not support imports, variables, functions, calculations,
executable expressions, or any other unlisted syntax. New syntax is added only
when an actual catalog requirement needs it.

Catalog source files use the game-neutral `.modcat` extension. Project catalogs
remain split by feature, such as `catalog/battle_logic.modcat` and
`catalog/qol.modcat`; release packaging consolidates their user-facing contract
into `catalog.modcat`.

## Release packaging

The release contains:

- the packaged builder executable;
- one editable `config.json`;
- one consolidated `catalog.modcat` reference file; and
- one `README.md` containing general information and explaining the builder,
  configuration, and catalog in simple terms.

The release catalog reference has exactly the same user-facing selectable
hierarchy, node types, constraints, unions, and descriptions as the complete
catalog embedded in the executable. It contains no implementation
details of any kind, including patch mappings, adapter names, target IDs,
offsets, module ownership, source paths, assets, proof metadata, or build data.
It also contains no configured selections, enabled values, or overrides and is
not a configuration.

Release packaging derives the reference from the canonical project catalog by
consolidating the feature definitions and retaining only their user-facing
configuration contract. It is not maintained as a second source.

The release catalog is an inert reference. The executable never reads it for
validation, selection, or patching, so modifying or deleting it cannot affect
builder behavior. The user is responsible for any damage to that reference
copy.

The executable embeds the complete catalog, parser, and validator plus all
patch mappings, guarded definitions, adapters, assets, and runtime objects. It
validates `config.json` against its embedded catalog, then resolves the selected
semantic paths and values through the embedded implementation data.

`README.md` explains at least:

- what the builder does;
- which user-supplied game inputs it requires;
- how to run it and edit `config.json`;
- how disabled values, scalar settings, named structured alternatives, and
  unions appear in the
  configuration; and
- that the consolidated catalog is a readable reference which the executable
  does not consume, not a file users normally need to edit.

## Startup behavior patch

- `qol.startup.save_loading` is currently `setting<"manual">` and owns the
  confirmed loading-screen-then-main-menu behavior.
- The base configuration uses `manual`; there is no separate default.
- Automatic background first-save loading is not implemented and is not added
  by this change. If implemented later, it can become a disjoint second branch
  without changing the catalog model.
- `qol.save_load.display_only_first_save` remains independent because it owns
  Save/Load presentation rather than startup behavior.

## Substitution-cost patch

- `battle_logic.substitution_cost` accepts a configuration integer from `1`
  through `15`; it does not select from predefined cost variants.
- Its catalog type is `setting<int & 1..15>`.
- Its referenced edit uses `replace`, retains ELF offset `0x1299BC`, expands
  the destination guard to the complete `lui v0, 0x3F80` instruction bytes
  `803F023C`, and declares the generic `mips_lui_float32` adapter.
- `mips_lui_float32` validates that the guarded bytes are a complete MIPS
  `lui` instruction, encodes the validated number as IEEE-754 float32, requires
  an exact encoding with zero low 16 bits, preserves the opcode and destination
  register, and replaces the immediate with the float32 high 16 bits.
- Every integer from `1` through `15` has an exact single-`lui` encoding. For
  example, `3` produces complete replacement instruction bytes `4040023C`.
- The historical `5` to `0x40A0` immediate is structurally confirmed as
  float32 `5.0`; its gameplay behavior remains runtime-unvalidated.
