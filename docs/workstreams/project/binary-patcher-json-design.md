# Builder catalog and configuration redesign
Status: approved and implemented.
This document records the accepted builder catalog and configuration design. It is not a JSON schema.
## Scope
- Use repository-wide `catalog.json`, `edits.json`, and `injections.json` files
  as the canonical selectable and executable definitions.
- `catalog.json` owns the complete feature hierarchy and leaf references;
  `edits.json` owns binary-patcher definitions; `injections.json` owns
  runtime-injector units.
- Keep texture-patcher, translation-importer, targets, and operation definitions in TSV for now.
- Represent retained translation and texture behavior as selectable catalog leaves; their executable TSV data remains outside the catalog and is invoked internally when the corresponding leaf is enabled.
- Do not represent modules in the catalog or configurations. Builder engines remain internal implementation details.
- Do not introduce schemas, schema versions, or migrations while this design is changing.
## Catalog hierarchy
- `catalog.json` has one top-level `features` parent whose children are the actual feature keys.
- Eliminate groups as a concept.
- Catalog nodes may nest directly to any depth; there is no fixed feature/group/patch hierarchy and no `children` wrapper.
- Use meaningful, stable `snake_case` keys. Do not retain opaque IDs, generated sequence IDs, or separate ID/name fields.
- Preserve every existing `description`. The field is optional at any catalog level and ignored by the parser.
- Keep enablement out of the catalog.
- The reserved catalog fields are `description`, `proven`, `edits`, and
  `injections`. Every other key is a directly nested selectable node.
- A selectable patch is an ordinary meaningful node in the hierarchy. There is no `patches` wrapper, separate `patch_id`, or patch-name field.
- Catalog leaves contain ordered arrays of edit and injection IDs. Definitions
  do not appear inline in the feature tree.
## Ownership and extraction
- Keep every edit and injection definition in its owning root map.
- Reference a shared injection unit from every consuming catalog leaf; store the
  unit only once in `injections.json`.
- Keep a source's private imports, emitted fragments, relocations, and other private declarations inside that source or its owning patch.
- Keep patch-specific hooks and payload declarations together in one injection
  unit when they share a catalog owner.
## Executable fields
- Remove `enabled`, `confidence`, and `status` from executable definitions.
- Migrated executable patches may temporarily contain `"proven": false`. Presence means the patch still needs proof. Remove the field when the patch is proven; never set it to `true`; never add it to new patches. Remove the concept after the migrated set is proven.
- Move useful `evidence_id`, `review_notes`, and `reason` content to the appropriate documentation, discard stale or duplicated content, and remove those fields from executable data.
## Configurations
- Use configurations named `test`, `release`, and `development`.
- Configurations are the sole owners of enablement and contain no canonical definitions, patch data, or module information.
- Configurations have exactly two top-level fields: `features` and `overrides`.
- The base `features` setting is `true`, `false`, or a complete object matching the catalog's `features` children. The maintained configurations use `true`.
- `overrides` is an object. It may be empty or partially mirror the configuration structure under `features`; unspecified descendants retain their base value.
- Build and release loading recursively merge `overrides` over the base `features` setting before deriving module invocations.
- A configuration value corresponding to a catalog node is `true`, `false`, or an object.
- `true` enables the node's complete selectable catalog subtree.
- `false` disables the node's complete selectable catalog subtree.
- An object configures that node's direct selectable children individually.
- An object is forbidden for a lowest-level selectable catalog node; leaves must be `true` or `false`.
- Whenever a configuration descends with an object, its keys must match that catalog node's direct selectable child keys exactly. Missing and extra keys are invalid.
- Configurations contain no `enabled` or `description` fields.
```json
{
  "features": true,
  "overrides": {
    "features": {
      "localization": false
    }
  }
}
```
## Targets
- Keep shared target definitions outside the three JSON definition files in one
  flat `targets.tsv` registry. Edits and injection hooks reference targets by
  ID.
- The registry path is `na228_builder/targets.tsv`.
## Binary edits
- Store binary edits in the direct root map of `edits.json`.
- Catalog leaf `edits` arrays reference meaningful edit IDs. Do not retain a
  separate `edit_id` field inside a definition.
- Remove edit `order`; it changes no current binary-patcher or runtime-injector output.
- Preserve an explicit `operation` discriminator. The parser reads it directly and never infers an operation from object shape.
- Preserve `destination_target_id` on each edit.
- Every edit stores exactly one destination guard. Compact replace/copy ranges use `expected_hex`; existing large replace/copy ranges and blob replacements use `expected_sha256` so the original range is not duplicated inline.
- Remove copy-source `source_expected_hex` and `source_expected_sha256`; the complete source target is already verified by size and SHA-256.
- Preserve `fill` and its single-byte fill value.
- Remove `blob_offset`; each blob contains exactly one edit's replacement payload.
- Preserve `blob_sha256` as an independent guard that guarantees the asset has not changed.
- Retain `length` for copy and fill edits. Derive replace length from its replacement bytes and blob length from the exact blob file size.
## Binary operation contracts
- Define runtime manifests named `replace.tsv`, `copy.tsv`, `blob.tsv`, and `fill.tsv` under the binary-patcher engine's `operations/` directory.
- The filename defines the operation name. Every manifest is independently complete and lists the operation's full allowed field set, including common edit fields, using `field`, `required`, and `type` columns.
- Use the manifests for generic required-field, unknown-field, and basic-type validation.
- Keep operation execution and behavioral checks such as target existence and range bounds in code handlers.
- Do not introduce manifest inheritance or schema versions.
## Injected code and hooks
- Runtime-injection target changes are hooks, not generic edits.
- Store hooks and payload declarations together in direct-root injection units
  under `injections.json`.
- Catalog leaf `injections` arrays reference injection-unit IDs. Multiple leaves
  may reference the same unit.
- Represent hook identity with a meaningful JSON key. Do not retain a separate hook or edit ID field.
- Hooks have no `operation` field because the containing structure already defines them as hooks.
- Preserve hook encoding because current hooks use both non-linking `j26` and linking `jal26` encodings.
- The runtime-injection engine continues resolving payload symbols after final payload placement and turning resolved hooks into guarded concrete binary replacements for application.
- Each injection unit contains `hooks`, `payload`, or both. `payload` maps
  meaningful payload IDs to declarations. A C source declaration contains
  `kind: "c"`, its repository-relative `path`, `namespace`, private `imports`,
  and emitted `fragments`. A static fragment declaration contains its fragment
  kind, order, alignment, inline value or guarded blob, optional relocations,
  and optional initialization marker.
- C-fragment ABI and purpose metadata lives on the specific emitted fragment. Static adapter ABI metadata lives on that adapter declaration; it names its source only when ownership cannot be inferred from nesting.
- Static-fragment relocations remain inside the fragment that owns them. Source imports remain inside the source that owns them.
## Validation
- The loader rejects duplicate JSON keys, invalid selectable keys, non-leaf
  implementation references, missing edit/injection IDs,
  configuration/catalog structural mismatches, objects at configuration leaves,
  non-false `proven` values, unknown binary-operation fields, missing required
  fields, malformed types, invalid targets, bad ranges, and bad asset hashes.
- Migration equivalence covers all binary edits, enabled selections, runtime fragments, runtime hooks, the linked resident payload, exported symbols, and resolved hook writes before removal of the superseded TSV inputs.
